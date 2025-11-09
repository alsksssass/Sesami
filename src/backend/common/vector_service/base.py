from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class IVectorService(ABC):
    """Vector Database 서비스 인터페이스

    로컬 환경(OpenSearch)과 AWS 환경(OpenSearch Serverless 또는 Qdrant)을 추상화하는 인터페이스
    """

    @abstractmethod
    async def index_embeddings(
        self,
        embeddings: List[np.ndarray],
        metadata: List[Dict[str, Any]],
        index_name: Optional[str] = None
    ) -> int:
        """임베딩 벡터를 인덱스에 저장

        Args:
            embeddings: 임베딩 벡터 리스트 (각 벡터는 numpy array)
            metadata: 각 임베딩에 대한 메타데이터 (file_path, chunk_text, graph_node_id 등)
            index_name: 인덱스 이름 (기본값은 설정값 사용)

        Returns:
            인덱싱된 벡터 수
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """벡터 유사도 검색 (k-NN)

        Args:
            query_vector: 쿼리 벡터 (numpy array)
            k: 반환할 결과 수
            filter_dict: 메타데이터 필터 (예: {"file_path": "src/main.py"})
            index_name: 검색할 인덱스 이름

        Returns:
            검색 결과 리스트 (각 결과는 score, metadata 포함)
        """
        pass

    @abstractmethod
    async def delete_by_analysis_id(
        self,
        analysis_id: str,
        index_name: Optional[str] = None
    ) -> int:
        """특정 분석 ID의 모든 벡터 삭제

        Args:
            analysis_id: 분석 작업 ID
            index_name: 인덱스 이름

        Returns:
            삭제된 벡터 수
        """
        pass

    @abstractmethod
    async def create_index(
        self,
        index_name: str,
        dimension: int,
        metric: str = "cosine"
    ) -> bool:
        """새로운 벡터 인덱스 생성

        Args:
            index_name: 인덱스 이름
            dimension: 벡터 차원 (예: 1536 for OpenAI, 1024 for Bedrock Titan)
            metric: 거리 메트릭 ("cosine", "euclidean", "dot_product")

        Returns:
            생성 성공 여부
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """벡터 데이터베이스 연결 상태 확인

        Returns:
            연결 성공 여부
        """
        pass

    @abstractmethod
    async def close(self):
        """연결 종료"""
        pass
