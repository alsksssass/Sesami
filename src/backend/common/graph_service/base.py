from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from uuid import UUID


class IGraphService(ABC):
    """Graph Database 서비스 인터페이스

    로컬 환경(Neo4j Community)과 AWS 환경(Neo4j AuraDB 또는 Neptune)을 추상화하는 인터페이스
    """

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Cypher 쿼리 실행

        Args:
            query: Cypher 쿼리 문자열
            parameters: 쿼리 파라미터

        Returns:
            쿼리 결과 리스트
        """
        pass

    @abstractmethod
    async def create_nodes(
        self,
        nodes: List[Dict[str, Any]],
        label: str
    ) -> int:
        """노드 일괄 생성

        Args:
            nodes: 노드 데이터 리스트
            label: 노드 레이블 (예: "File", "Function", "Class")

        Returns:
            생성된 노드 수
        """
        pass

    @abstractmethod
    async def create_relationships(
        self,
        relationships: List[Dict[str, Any]],
        rel_type: str
    ) -> int:
        """관계 일괄 생성

        Args:
            relationships: 관계 데이터 리스트 (from_id, to_id, properties)
            rel_type: 관계 타입 (예: "CALLS", "IMPORTS", "CONTAINS")

        Returns:
            생성된 관계 수
        """
        pass

    @abstractmethod
    async def get_graph_snapshot(
        self,
        analysis_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """분석 ID로 그래프 스냅샷 조회

        Args:
            analysis_id: 분석 작업 ID

        Returns:
            스냅샷 메타데이터 또는 None
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """그래프 데이터베이스 연결 상태 확인

        Returns:
            연결 성공 여부
        """
        pass

    @abstractmethod
    async def close(self):
        """연결 종료"""
        pass
