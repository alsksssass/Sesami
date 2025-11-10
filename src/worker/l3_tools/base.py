"""
L3-Tools Base Interface

모든 L3 분석 도구의 공통 인터페이스를 정의합니다.
PDD v4.0의 "저비용 도구" 계층입니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
import time

from shared.schemas.event_envelope import L3ToolOutput


class IL3Tool(ABC):
    """L3-Tool 인터페이스

    모든 분석 도구(pylint, SonarQube, Semgrep 등)는 이 인터페이스를 구현합니다.

    특징:
    - 저비용: CPU 기반, Graviton + Spot 인스턴스에서 실행
    - 100% 실행: 모든 파일에 대해 실행 (L2-Filter 이전)
    - 결정론적: 같은 입력 → 같은 출력
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    @abstractmethod
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        파일 분석을 수행합니다.

        Args:
            file_path: 분석 대상 파일 경로

        Returns:
            분석 결과 딕셔너리 (payload)

        Raises:
            ToolExecutionError: 도구 실행 실패 시
        """
        pass

    def execute(self, file_path: str) -> L3ToolOutput:
        """
        분석을 실행하고 표준 Event Envelope 형식으로 반환합니다.

        이 메서드는 모든 L3-Tool에서 공통으로 사용됩니다.
        실제 분석 로직은 analyze() 메서드에서 구현합니다.

        Args:
            file_path: 분석 대상 파일 경로

        Returns:
            L3ToolOutput: 표준 이벤트 봉투
        """
        start_time = time.time()

        try:
            # 실제 분석 수행
            payload = self.analyze(file_path)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Event Envelope 생성
            return L3ToolOutput(
                tool_name=self.tool_name,
                tool_type="L3_TOOL",
                file_path=file_path,
                execution_time_ms=execution_time_ms,
                payload=payload,
                metadata={
                    "tool_version": self.get_version(),
                    "success": True
                }
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 실패 시에도 Event Envelope 반환 (L2가 처리 가능하도록)
            return L3ToolOutput(
                tool_name=self.tool_name,
                tool_type="L3_TOOL",
                file_path=file_path,
                execution_time_ms=execution_time_ms,
                payload={
                    "error": str(e),
                    "success": False
                },
                metadata={
                    "tool_version": self.get_version(),
                    "success": False,
                    "error_type": type(e).__name__
                }
            )

    @abstractmethod
    def get_version(self) -> str:
        """도구 버전 반환"""
        pass

    def is_applicable(self, file_path: str) -> bool:
        """
        이 도구가 해당 파일에 적용 가능한지 확인합니다.

        Args:
            file_path: 파일 경로

        Returns:
            적용 가능 여부
        """
        # 기본 구현: 모든 파일에 적용 가능
        return True


class ToolExecutionError(Exception):
    """도구 실행 중 발생한 에러"""
    pass


class ToolNotApplicableError(Exception):
    """도구가 해당 파일에 적용 불가능한 경우"""
    pass
