import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ContributionStats:
    """기여도 분석 결과"""
    total_lines: int
    added_lines: int
    deleted_lines: int
    commits: int
    files_changed: int


class GitAnalyzer:
    """Git 저장소 분석 클래스

    Celery/AWS Batch 환경과 독립적인 순수 분석 로직
    """

    def __init__(self, work_dir: Optional[Path] = None):
        """
        Args:
            work_dir: 작업 디렉토리 (None이면 임시 디렉토리 생성)
        """
        self.work_dir = work_dir or Path(tempfile.mkdtemp())

    def clone_repository(self, repo_url: str, branch: str = "main") -> Path:
        """저장소 클론

        Args:
            repo_url: GitHub 저장소 URL
            branch: 클론할 브랜치

        Returns:
            클론된 저장소 경로

        Raises:
            RuntimeError: Git clone 실패 시
        """
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        repo_path = self.work_dir / repo_name

        try:
            # 이미 존재하면 삭제
            if repo_path.exists():
                shutil.rmtree(repo_path)

            # Git clone 실행
            subprocess.run(
                ["git", "clone", "--branch", branch, "--single-branch", repo_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True
            )
            return repo_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")

    def analyze_contributions(self, repo_path: Path, target_user: str) -> ContributionStats:
        """특정 사용자의 기여도 분석

        Args:
            repo_path: Git 저장소 경로
            target_user: 분석할 GitHub 사용자명

        Returns:
            ContributionStats: 기여도 통계

        Raises:
            RuntimeError: Git 명령 실패 시
        """
        try:
            # 커밋 수 계산
            commits_result = subprocess.run(
                ["git", "log", f"--author={target_user}", "--oneline"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commits = len(commits_result.stdout.strip().split('\n')) if commits_result.stdout.strip() else 0

            # 변경된 파일 수 계산
            files_result = subprocess.run(
                ["git", "log", f"--author={target_user}", "--name-only", "--pretty=format:"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            files_changed = len(set(filter(None, files_result.stdout.strip().split('\n'))))

            # 추가/삭제된 라인 수 계산
            stats_result = subprocess.run(
                ["git", "log", f"--author={target_user}", "--numstat", "--pretty=format:"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            added_lines = 0
            deleted_lines = 0

            for line in stats_result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        added_lines += int(parts[0])
                        deleted_lines += int(parts[1])
                    except ValueError:
                        # Binary 파일 등은 숫자가 아닐 수 있음
                        continue

            # git blame으로 현재 코드베이스에서 해당 사용자가 작성한 라인 수 계산
            total_lines = self._count_blame_lines(repo_path, target_user)

            return ContributionStats(
                total_lines=total_lines,
                added_lines=added_lines,
                deleted_lines=deleted_lines,
                commits=commits,
                files_changed=files_changed
            )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to analyze contributions: {e.stderr}")

    def _count_blame_lines(self, repo_path: Path, target_user: str) -> int:
        """git blame을 사용하여 현재 코드베이스에서 해당 사용자가 작성한 라인 수 계산

        Args:
            repo_path: Git 저장소 경로
            target_user: 분석할 사용자명

        Returns:
            해당 사용자가 작성한 라인 수
        """
        try:
            # 모든 추적되는 파일 목록 가져오기
            files_result = subprocess.run(
                ["git", "ls-files"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            total_lines = 0
            for file_path in files_result.stdout.strip().split('\n'):
                if not file_path:
                    continue

                try:
                    # git blame으로 각 파일 분석
                    blame_result = subprocess.run(
                        ["git", "blame", "--line-porcelain", file_path],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    # author로 시작하는 라인에서 사용자명 확인
                    for line in blame_result.stdout.split('\n'):
                        if line.startswith('author '):
                            author = line.replace('author ', '').strip()
                            if author == target_user:
                                total_lines += 1

                except subprocess.CalledProcessError:
                    # Binary 파일이나 권한 문제 등은 건너뛰기
                    continue

            return total_lines

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to count blame lines: {e.stderr}")

    def cleanup(self):
        """작업 디렉토리 정리"""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
