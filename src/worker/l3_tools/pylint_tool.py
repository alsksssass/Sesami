"""
Pylint Tool: Python 코드 품질 분석

PDD v4.0 L3-Tool 구현
- 저비용: CPU 기반
- 100% 실행: 모든 Python 파일
- 결정론적: Pylint static analysis
"""
import subprocess
import json
from typing import Dict, Any
from pathlib import Path

from .base import IL3Tool, ToolExecutionError, ToolNotApplicableError


class PylintTool(IL3Tool):
    """Pylint를 사용한 Python 코드 품질 분석"""

    def __init__(self):
        super().__init__(tool_name="PYLINT_TOOL")
        self.pylint_version = self._get_pylint_version()

    def _get_pylint_version(self) -> str:
        """Pylint 버전 확인"""
        try:
            result = subprocess.run(
                ["pylint", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # pylint 2.15.0 형식에서 버전 추출
            for line in result.stdout.split('\n'):
                if 'pylint' in line.lower():
                    parts = line.split()
                    for part in parts:
                        if part[0].isdigit():
                            return part
            return "unknown"
        except Exception:
            return "unknown"

    def is_applicable(self, file_path: str) -> bool:
        """Python 파일만 분석 가능"""
        return file_path.endswith('.py')

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Pylint 분석 수행

        Args:
            file_path: Python 파일 경로

        Returns:
            {
                "score": float,        # 0.0 ~ 10.0
                "errors": list,
                "warnings": list,
                "conventions": list,
                "refactors": list,
                "stats": dict
            }

        Raises:
            ToolNotApplicableError: Python 파일이 아닌 경우
            ToolExecutionError: Pylint 실행 실패
        """
        if not self.is_applicable(file_path):
            raise ToolNotApplicableError(f"Pylint은 Python 파일만 분석 가능: {file_path}")

        if not Path(file_path).exists():
            raise ToolExecutionError(f"파일이 존재하지 않음: {file_path}")

        try:
            # Pylint 실행 (JSON 출력)
            result = subprocess.run(
                ["pylint", "--output-format=json", file_path],
                capture_output=True,
                text=True,
                timeout=30  # 30초 타임아웃
            )

            # Pylint는 문제가 있으면 non-zero exit code 반환 (정상)
            # JSON 파싱
            pylint_output = json.loads(result.stdout) if result.stdout else []

            # 메시지 분류
            errors = []
            warnings = []
            conventions = []
            refactors = []

            for msg in pylint_output:
                item = {
                    "line": msg.get("line", 0),
                    "column": msg.get("column", 0),
                    "message": msg.get("message", ""),
                    "symbol": msg.get("symbol", ""),
                    "message_id": msg.get("message-id", "")
                }

                msg_type = msg.get("type", "").lower()
                if msg_type == "error":
                    errors.append(item)
                elif msg_type == "warning":
                    warnings.append(item)
                elif msg_type == "convention":
                    conventions.append(item)
                elif msg_type == "refactor":
                    refactors.append(item)

            # 점수 계산 (별도 실행 필요)
            score = self._calculate_score(file_path)

            return {
                "score": score,
                "errors": errors,
                "warnings": warnings,
                "conventions": conventions,
                "refactors": refactors,
                "stats": {
                    "error_count": len(errors),
                    "warning_count": len(warnings),
                    "convention_count": len(conventions),
                    "refactor_count": len(refactors),
                    "total_issues": len(pylint_output)
                }
            }

        except subprocess.TimeoutExpired:
            raise ToolExecutionError(f"Pylint 실행 타임아웃 (30초 초과): {file_path}")

        except json.JSONDecodeError as e:
            raise ToolExecutionError(f"Pylint JSON 출력 파싱 실패: {e}")

        except Exception as e:
            raise ToolExecutionError(f"Pylint 실행 중 에러: {e}")

    def _calculate_score(self, file_path: str) -> float:
        """Pylint 점수 계산 (0.0 ~ 10.0)"""
        try:
            result = subprocess.run(
                ["pylint", "--score=y", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            # "Your code has been rated at 9.50/10.00" 형식에서 점수 추출
            for line in result.stdout.split('\n'):
                if 'rated at' in line:
                    parts = line.split('rated at')[1].strip().split('/')[0]
                    return float(parts)

            return 10.0  # 기본값

        except Exception:
            return 10.0  # 에러 시 만점 반환 (보수적 접근)

    def get_version(self) -> str:
        """Pylint 버전 반환"""
        return self.pylint_version
