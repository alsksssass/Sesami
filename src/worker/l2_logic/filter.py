"""
L2 Filter: 비용 최적화를 위한 파일 선별

PDD v4.0의 "L2-Filter" 계층
- L3-Tool 결과를 기반으로 "유의미한" 파일만 선별
- L3-Agent (고비용 LLM)는 선별된 10%만 실행
"""
from typing import List, Dict, Any
import os


class L2Filter:
    """
    CPU 기반 필터링 로직

    필터링 기준:
    1. 복잡도 (Cyclomatic Complexity) > 임계값
    2. 코드 라인 수 > 임계값
    3. 품질 점수 (Pylint) < 임계값 (문제가 많은 파일)
    4. 보안 이슈 존재 (Semgrep)
    """

    def __init__(
        self,
        min_complexity: int = None,
        min_lines: int = None,
        max_quality_score: float = None
    ):
        """
        Args:
            min_complexity: 최소 복잡도 임계값 (환경변수 우선)
            min_lines: 최소 라인 수 임계값
            max_quality_score: 최대 품질 점수 (이하면 문제가 있는 파일)
        """
        self.min_complexity = min_complexity or int(os.getenv("L2_FILTER_MIN_COMPLEXITY", "10"))
        self.min_lines = min_lines or int(os.getenv("L2_FILTER_MIN_LINES", "100"))
        self.max_quality_score = max_quality_score or float(os.getenv("L2_FILTER_MAX_QUALITY_SCORE", "8.0"))

    def filter_significant_files(self, tool_results: List[Dict[str, Any]]) -> List[str]:
        """
        L3-Tool 결과를 기반으로 유의미한 파일 선별

        Args:
            tool_results: L3-Tool의 Event Envelope 리스트

        Returns:
            선별된 파일 경로 리스트 (L3-Agent 실행 대상)
        """
        significant_files = set()

        for tool_result in tool_results:
            file_path = tool_result.get("file_path")
            tool_name = tool_result.get("tool_name")
            payload = tool_result.get("payload", {})

            if not file_path:
                continue

            # 1️⃣ Pylint 기준: 낮은 점수 또는 많은 에러
            if tool_name == "PYLINT_TOOL":
                score = payload.get("score", 10.0)
                error_count = len(payload.get("errors", []))

                if score < self.max_quality_score or error_count > 5:
                    significant_files.add(file_path)

            # 2️⃣ SonarQube 기준: 버그/취약점 존재
            elif tool_name == "SONARQUBE_TOOL":
                bugs = payload.get("bugs", 0)
                vulnerabilities = payload.get("vulnerabilities", 0)

                if bugs > 0 or vulnerabilities > 0:
                    significant_files.add(file_path)

            # 3️⃣ Semgrep 기준: 보안 이슈 존재
            elif tool_name == "SEMGREP_TOOL":
                findings = payload.get("findings", [])

                if len(findings) > 0:
                    significant_files.add(file_path)

            # 4️⃣ DORA 기준: 높은 변경 빈도 (Churn Rate)
            elif tool_name == "DORA_CALCULATOR":
                churn_rate = payload.get("churn_rate", 0.0)

                if churn_rate > 0.5:  # 50% 이상 변경
                    significant_files.add(file_path)

        return list(significant_files)

    def calculate_threshold_percentage(self, total_files: int, selected_files: int) -> float:
        """
        선별 비율 계산

        Args:
            total_files: 전체 파일 수
            selected_files: 선별된 파일 수

        Returns:
            선별 비율 (0.0 ~ 1.0)
        """
        if total_files == 0:
            return 0.0

        return selected_files / total_files

    def validate_threshold(self, total_files: int, selected_files: int, max_threshold: float = 0.2) -> bool:
        """
        선별 비율이 임계값을 초과하는지 검증

        Args:
            total_files: 전체 파일 수
            selected_files: 선별된 파일 수
            max_threshold: 최대 허용 비율 (기본 20%)

        Returns:
            임계값 이하 여부 (True = 통과)
        """
        percentage = self.calculate_threshold_percentage(total_files, selected_files)
        return percentage <= max_threshold


# 사용 예시
if __name__ == "__main__":
    # 테스트 데이터
    tool_results = [
        {
            "tool_name": "PYLINT_TOOL",
            "file_path": "src/backend/main.py",
            "payload": {"score": 9.5, "errors": []}
        },
        {
            "tool_name": "PYLINT_TOOL",
            "file_path": "src/backend/auth.py",
            "payload": {"score": 7.2, "errors": ["E1101", "W0612"]}
        },
        {
            "tool_name": "SEMGREP_TOOL",
            "file_path": "src/backend/config.py",
            "payload": {"findings": [{"rule": "hardcoded-secret"}]}
        }
    ]

    filter_obj = L2Filter()
    significant = filter_obj.filter_significant_files(tool_results)

    print("선별된 파일:", significant)
    # 출력: ['src/backend/auth.py', 'src/backend/config.py']
