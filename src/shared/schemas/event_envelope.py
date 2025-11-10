"""
Event Envelope: 모든 L3 작업자의 표준 출력 형식

PDD v4.0의 "동적 확장" 패턴을 구현합니다.
L3 작업자가 10개에서 50개로 늘어날 때 L1/L2 코드 수정 없이
자동으로 새 데이터를 집계하고 LLM에게 전달합니다.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID


class EventEnvelope(BaseModel):
    """
    표준 이벤트 봉투 구조

    모든 L3 작업자(Tool/Builder/Agent)는 이 형식으로 결과를 EFS에 저장합니다.
    """

    tool_name: str = Field(..., description="도구/에이전트 이름 (예: PYLINT_TOOL, PROFICIENCY_AGENT)")
    tool_type: Literal["L3_TOOL", "L3_BUILDER", "L3_AGENT"] = Field(..., description="작업자 타입")
    file_path: Optional[str] = Field(None, description="분석 대상 파일 경로")
    execution_time_ms: int = Field(..., description="실행 시간 (밀리초)")

    payload: Dict[str, Any] = Field(..., description="실제 결과 데이터 (도구마다 다름)")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")

    class Config:
        schema_extra = {
            "example": {
                "tool_name": "PYLINT_TOOL",
                "tool_type": "L3_TOOL",
                "file_path": "src/backend/main.py",
                "execution_time_ms": 1234,
                "payload": {
                    "score": 9.5,
                    "errors": [],
                    "warnings": ["Line too long (120/100)"]
                },
                "metadata": {
                    "worker_id": "batch-job-12345",
                    "timestamp": "2025-01-10T12:34:56Z"
                }
            }
        }


class L3ToolOutput(EventEnvelope):
    """L3-Tool 출력 스키마 (저비용 분석 도구)"""

    tool_type: Literal["L3_TOOL"] = "L3_TOOL"

    # Payload 구조 (각 Tool마다 다를 수 있음)
    # pylint: {"score": float, "errors": list, "warnings": list}
    # sonarqube: {"bugs": int, "vulnerabilities": int, "code_smells": int}
    # semgrep: {"findings": list}


class L3BuilderOutput(EventEnvelope):
    """L3-Builder 출력 스키마 (Graph/Vector DB 구축)"""

    tool_type: Literal["L3_BUILDER"] = "L3_BUILDER"
    file_path: Optional[str] = None  # Builder는 파일별이 아님

    # Payload 구조
    # graph_builder: {"nodes_created": int, "edges_created": int, "snapshot_id": str}
    # vector_builder: {"chunks_indexed": int, "embedding_dimension": int, "index_name": str}


class L3AgentOutput(EventEnvelope):
    """L3-Agent 출력 스키마 (LLM 기반 분석)"""

    tool_type: Literal["L3_AGENT"] = "L3_AGENT"

    # Payload 구조 (각 Agent마다 다를 수 있음)
    # proficiency_agent: {"level": str, "confidence": float, "reasoning": str}
    # architecture_agent: {"quality_score": float, "patterns": list, "suggestions": list}


class L2Summary(BaseModel):
    """
    L2 Reducer가 생성하는 중간 요약본

    L2는 담당 그룹(파일들)의 L3 결과물들을 집계하여
    EFS에 l2_summary_{group_id}.json 형식으로 저장합니다.
    """

    group_id: str = Field(..., description="L2 그룹 ID")
    file_count: int = Field(..., description="처리한 파일 수")

    # tool_name을 Key로 하는 동적 딕셔너리
    tools_summary: Dict[str, list] = Field(default_factory=dict, description="도구별 결과 집계")
    agents_summary: Dict[str, list] = Field(default_factory=dict, description="에이전트별 결과 집계")

    execution_time_ms: int = Field(..., description="L2 총 실행 시간")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "group_id": "group_0001",
                "file_count": 50,
                "tools_summary": {
                    "PYLINT_TOOL": [
                        {"file": "main.py", "score": 9.5},
                        {"file": "auth.py", "score": 8.7}
                    ],
                    "SONARQUBE_TOOL": [
                        {"file": "main.py", "bugs": 0, "vulnerabilities": 1}
                    ]
                },
                "agents_summary": {
                    "PROFICIENCY_AGENT": [
                        {"file": "auth.py", "level": "Senior", "confidence": 0.92}
                    ]
                },
                "execution_time_ms": 12340,
                "timestamp": "2025-01-10T12:34:56Z"
            }
        }


class L1FinalReport(BaseModel):
    """
    L1-Finalize Agent가 생성하는 최종 리포트

    모든 L2 요약본을 통합하고 Graph-RAG + 최종 LLM 호출로
    다차원 역량 리포트를 생성합니다.
    """

    analysis_id: UUID = Field(..., description="분석 작업 ID")

    # 모든 L2 요약본을 통합한 전체 요약
    overall_summary: Dict[str, Any] = Field(..., description="전체 요약")

    # Graph-RAG 인사이트
    graph_insights: Dict[str, Any] = Field(default_factory=dict, description="Neo4j Graph-RAG 분석")

    # Vector-RAG 인사이트
    vector_insights: Dict[str, Any] = Field(default_factory=dict, description="OpenSearch Vector-RAG 분석")

    # 최종 LLM 종합 판단
    final_assessment: Dict[str, Any] = Field(..., description="최종 LLM 평가")

    execution_time_ms: int = Field(..., description="L1 총 실행 시간")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "overall_summary": {
                    "total_files": 500,
                    "total_lines": 12000,
                    "average_complexity": 7.5
                },
                "graph_insights": {
                    "architecture_quality": 8.5,
                    "key_modules": ["auth", "api", "database"]
                },
                "vector_insights": {
                    "code_similarity": 0.85,
                    "duplicate_patterns": 3
                },
                "final_assessment": {
                    "overall_level": "Senior",
                    "confidence": 0.92,
                    "strengths": ["Clean architecture", "Good test coverage"],
                    "improvements": ["Reduce complexity in auth module"]
                },
                "execution_time_ms": 123400,
                "timestamp": "2025-01-10T12:34:56Z"
            }
        }
