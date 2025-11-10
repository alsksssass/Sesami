"""
L3-Agents Base Interface

모든 L3 LLM 에이전트의 공통 인터페이스를 정의합니다.
PDD v4.0의 "고비용 에이전트" 계층입니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

from shared.schemas.event_envelope import L3AgentOutput


class IL3Agent(ABC):
    """L3-Agent 인터페이스

    모든 LLM 기반 에이전트는 이 인터페이스를 구현합니다.

    특징:
    - 고비용: LLM 호출 (Bedrock Claude 3.5 Sonnet)
    - 10% 선별 실행: L2-Filter를 통과한 "유의미한" 파일만
    - 도구 사용: Neo4j (Graph-RAG), OpenSearch (Vector-RAG)
    - 추론 기반: 구조적/의미적 인사이트 도출
    """

    def __init__(
        self,
        agent_name: str,
        graph_service: Optional[Any] = None,
        vector_service: Optional[Any] = None,
        llm_client: Optional[Any] = None
    ):
        self.agent_name = agent_name
        self.graph_service = graph_service
        self.vector_service = vector_service
        self.llm_client = llm_client

    @abstractmethod
    def analyze(self, file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM 기반 분석을 수행합니다.

        Args:
            file_path: 분석 대상 파일 경로
            context: L3-Tool 결과물 등 컨텍스트 정보

        Returns:
            분석 결과 딕셔너리 (payload)

        Raises:
            AgentExecutionError: 에이전트 실행 실패 시
        """
        pass

    def execute(self, file_path: str, context: Dict[str, Any] = None) -> L3AgentOutput:
        """
        분석을 실행하고 표준 Event Envelope 형식으로 반환합니다.

        이 메서드는 모든 L3-Agent에서 공통으로 사용됩니다.
        실제 분석 로직은 analyze() 메서드에서 구현합니다.

        Args:
            file_path: 분석 대상 파일 경로
            context: L3-Tool 결과물 등 컨텍스트 정보

        Returns:
            L3AgentOutput: 표준 이벤트 봉투
        """
        start_time = time.time()
        context = context or {}

        try:
            # 실제 분석 수행
            payload = self.analyze(file_path, context)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Event Envelope 생성
            return L3AgentOutput(
                tool_name=self.agent_name,
                tool_type="L3_AGENT",
                file_path=file_path,
                execution_time_ms=execution_time_ms,
                payload=payload,
                metadata={
                    "agent_version": self.get_version(),
                    "llm_model": self.get_llm_model(),
                    "success": True,
                    "tokens_used": payload.get("tokens_used", 0)
                }
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 실패 시에도 Event Envelope 반환
            return L3AgentOutput(
                tool_name=self.agent_name,
                tool_type="L3_AGENT",
                file_path=file_path,
                execution_time_ms=execution_time_ms,
                payload={
                    "error": str(e),
                    "success": False
                },
                metadata={
                    "agent_version": self.get_version(),
                    "llm_model": self.get_llm_model(),
                    "success": False,
                    "error_type": type(e).__name__
                }
            )

    @abstractmethod
    def get_version(self) -> str:
        """에이전트 버전 반환"""
        pass

    def get_llm_model(self) -> str:
        """사용 중인 LLM 모델 반환"""
        if self.llm_client:
            return getattr(self.llm_client, 'model_id', 'unknown')
        return "unknown"

    def query_graph(self, cypher_query: str, params: Dict = None) -> Any:
        """
        Neo4j Graph-RAG 쿼리 (도구로 사용)

        Args:
            cypher_query: Cypher 쿼리
            params: 쿼리 파라미터

        Returns:
            쿼리 결과
        """
        if not self.graph_service:
            raise AgentExecutionError("Graph service가 주입되지 않음")

        try:
            return self.graph_service.query(cypher_query, params or {})
        except Exception as e:
            raise AgentExecutionError(f"Graph 쿼리 실패: {e}")

    def query_vector(self, query_text: str, k: int = 5, filters: Dict = None) -> Any:
        """
        OpenSearch Vector-RAG 쿼리 (도구로 사용)

        Args:
            query_text: 자연어 쿼리
            k: 반환할 결과 수
            filters: 메타데이터 필터

        Returns:
            유사 코드 블록 검색 결과
        """
        if not self.vector_service:
            raise AgentExecutionError("Vector service가 주입되지 않음")

        try:
            return self.vector_service.query(query_text, k=k, filter_dict=filters)
        except Exception as e:
            raise AgentExecutionError(f"Vector 쿼리 실패: {e}")

    def invoke_llm(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        LLM 호출 (Bedrock Claude)

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트

        Returns:
            {
                "content": str,
                "tokens_used": int,
                "model": str
            }
        """
        if not self.llm_client:
            raise AgentExecutionError("LLM client가 주입되지 않음")

        try:
            # Bedrock Claude 호출 (의사코드 - 실제 구현 필요)
            response = self.llm_client.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt
            )

            return {
                "content": response.get("content", ""),
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "model": self.get_llm_model()
            }

        except Exception as e:
            raise AgentExecutionError(f"LLM 호출 실패: {e}")


class AgentExecutionError(Exception):
    """에이전트 실행 중 발생한 에러"""
    pass
