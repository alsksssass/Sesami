"""
Graph-RAG v2 데이터베이스 모델
Neo4j 그래프 스냅샷 및 벡터 인덱스 메타데이터 관리
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from common.database import Base


def utc_now():
    """UTC aware datetime factory for SQLAlchemy default"""
    return datetime.now(timezone.utc)


class GraphSnapshot(Base):
    """
    Neo4j 그래프 스냅샷 버전 관리 테이블

    Purpose:
    - 커밋 해시 기반 그래프 캐싱
    - 그래프 빌드 이력 추적
    - 증분 업데이트 지원
    """
    __tablename__ = "graph_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    analysis_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Git 메타데이터
    commit_hash = Column(String(40), nullable=False, index=True, unique=True)
    repo_url = Column(String, nullable=False)
    branch = Column(String, default="main")

    # 그래프 통계
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)

    # 그래프 타입별 노드 수 (JSON)
    # {"File": 120, "Function": 450, "Class": 80, "Module": 30}
    node_types = Column(JSON, nullable=True)

    # Neo4j 스냅샷 메타데이터
    neo4j_database = Column(String, default="neo4j")
    neo4j_snapshot_id = Column(String, nullable=True)  # Neo4j 내부 스냅샷 ID

    # 상태 관리
    is_valid = Column(Boolean, default=True)  # 스냅샷 유효 여부
    build_duration_seconds = Column(Integer, nullable=True)  # 빌드 소요 시간

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 캐시 만료 시각

    def __repr__(self):
        return f"<GraphSnapshot(commit={self.commit_hash[:8]}, nodes={self.node_count}, edges={self.edge_count})>"


class VectorIndex(Base):
    """
    OpenSearch 벡터 인덱스 메타데이터 관리

    Purpose:
    - 임베딩 인덱스 추적
    - 시맨틱 검색 성능 모니터링
    - 인덱스 재생성 관리
    """
    __tablename__ = "vector_indices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    analysis_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # 인덱스 메타데이터
    index_name = Column(String, nullable=False, index=True)
    commit_hash = Column(String(40), nullable=False, index=True)

    # 임베딩 통계
    chunk_count = Column(Integer, default=0)
    embedding_dimension = Column(Integer, default=1536)  # OpenAI: 1536, Titan: 1024
    embedding_model = Column(String, nullable=False)  # "openai/text-embedding-3-large"

    # OpenSearch 설정
    opensearch_endpoint = Column(String, nullable=True)
    index_settings = Column(JSON, nullable=True)  # k-NN 파라미터 등

    # 상태 관리
    is_valid = Column(Boolean, default=True)
    indexing_duration_seconds = Column(Integer, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<VectorIndex(name={self.index_name}, chunks={self.chunk_count}, model={self.embedding_model})>"
