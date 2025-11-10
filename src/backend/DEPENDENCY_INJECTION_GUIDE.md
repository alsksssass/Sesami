# Graph-RAG Dependency Injection 가이드

## 개요

Neo4j와 OpenSearch 서비스는 `TASK_SERVICE_IMPL` 환경변수에 따라 자동으로 로컬/AWS 구현체로 전환됩니다.

## 아키텍처

### 서비스 계층 구조

```
common/
├── graph_service/
│   ├── __init__.py
│   ├── base.py              # IGraphService 인터페이스
│   ├── local_service.py     # LocalGraphService (Neo4j Community)
│   └── aws_service.py       # AwsGraphService (Phase 3 구현 예정)
├── vector_service/
│   ├── __init__.py
│   ├── base.py              # IVectorService 인터페이스
│   ├── local_service.py     # LocalVectorService (OpenSearch)
│   └── aws_service.py       # AwsVectorService (Phase 3 구현 예정)
└── dependencies.py          # 의존성 주입 팩토리 함수
```

## 환경 전환 로직

### LOCAL 환경 (개발)
```bash
# .env
TASK_SERVICE_IMPL=LOCAL
NEO4J_URI=bolt://neo4j:7687
OPENSEARCH_ENDPOINT=https://opensearch:9200
```

```python
# 자동으로 로컬 구현체 사용
graph_service = get_graph_service()  # → LocalGraphService
vector_service = get_vector_service()  # → LocalVectorService
```

### AWS_BATCH 환경 (프로덕션)
```bash
# .env
TASK_SERVICE_IMPL=AWS_BATCH
NEO4J_URI=bolt://your-auradb-instance.databases.neo4j.io:7687
OPENSEARCH_ENDPOINT=https://your-opensearch-serverless-endpoint.amazonaws.com
```

```python
# 자동으로 AWS 구현체 사용 (Phase 3에서 구현)
graph_service = get_graph_service()  # → AwsGraphService
vector_service = get_vector_service()  # → AwsVectorService
```

## 사용 예시

### FastAPI 엔드포인트에서 사용

```python
from fastapi import APIRouter, Depends
from common.dependencies import get_graph_service, get_vector_service
from common.graph_service import IGraphService
from common.vector_service import IVectorService

router = APIRouter()

@router.get("/insights/{analysis_id}")
async def get_insights(
    analysis_id: str,
    graph_service: IGraphService = Depends(get_graph_service),
    vector_service: IVectorService = Depends(get_vector_service)
):
    # Neo4j 쿼리 실행
    query = """
    MATCH (f:File)-[:CALLS]->(target:Function)
    WHERE f.analysis_id = $analysis_id
    RETURN f.path, count(target) as call_count
    ORDER BY call_count DESC
    LIMIT 10
    """
    results = await graph_service.execute_query(query, {"analysis_id": analysis_id})

    # 시맨틱 검색
    query_vector = np.array([...])  # 임베딩 벡터
    similar_code = await vector_service.search(
        query_vector=query_vector,
        k=5,
        filter_dict={"analysis_id": analysis_id}
    )

    return {
        "hotspot_files": results,
        "similar_code": similar_code
    }
```

### Worker에서 사용

```python
# src/worker/analysis/graph_loader.py
from common.dependencies import get_graph_service

async def load_graph_data(analysis_id: str, nodes: List[Dict], edges: List[Dict]):
    graph_service = get_graph_service()

    # 노드 일괄 생성
    await graph_service.create_nodes(nodes, label="File")
    await graph_service.create_nodes(functions, label="Function")

    # 관계 일괄 생성
    await graph_service.create_relationships(edges, rel_type="CALLS")

    print(f"✅ Graph loaded for {analysis_id}")
```

## IGraphService 인터페이스

### 주요 메서드

| 메서드 | 설명 | 반환값 |
|--------|------|--------|
| `execute_query(query, parameters)` | Cypher 쿼리 실행 | `List[Dict[str, Any]]` |
| `create_nodes(nodes, label)` | 노드 일괄 생성 (UNWIND) | `int` (생성된 노드 수) |
| `create_relationships(relationships, rel_type)` | 관계 일괄 생성 | `int` (생성된 관계 수) |
| `get_graph_snapshot(analysis_id)` | 그래프 스냅샷 조회 | `Optional[Dict]` |
| `check_health()` | 연결 상태 확인 | `bool` |
| `close()` | 연결 종료 | `None` |

### 사용 예시

```python
# 노드 생성
nodes = [
    {"id": "file1", "path": "src/main.py", "language": "python"},
    {"id": "file2", "path": "src/utils.py", "language": "python"}
]
count = await graph_service.create_nodes(nodes, label="File")

# 관계 생성
relationships = [
    {
        "from_id": "file1",
        "to_id": "file2",
        "properties": {"import_count": 5}
    }
]
count = await graph_service.create_relationships(relationships, rel_type="IMPORTS")

# Cypher 쿼리
results = await graph_service.execute_query(
    "MATCH (f:File) WHERE f.language = $lang RETURN f.path",
    {"lang": "python"}
)
```

## IVectorService 인터페이스

### 주요 메서드

| 메서드 | 설명 | 반환값 |
|--------|------|--------|
| `index_embeddings(embeddings, metadata, index_name)` | 벡터 인덱싱 | `int` (인덱싱된 수) |
| `search(query_vector, k, filter_dict, index_name)` | k-NN 검색 | `List[Dict]` |
| `delete_by_analysis_id(analysis_id, index_name)` | 분석 ID로 삭제 | `int` (삭제된 수) |
| `create_index(index_name, dimension, metric)` | 인덱스 생성 | `bool` |
| `check_health()` | 연결 상태 확인 | `bool` |
| `close()` | 연결 종료 | `None` |

### 사용 예시

```python
import numpy as np

# 임베딩 인덱싱
embeddings = [
    np.array([0.1, 0.2, ..., 0.5]),  # 1536차원
    np.array([0.3, 0.4, ..., 0.6])
]
metadata = [
    {
        "id": "chunk1",
        "analysis_id": "abc-123",
        "file_path": "src/main.py",
        "chunk_text": "def main(): ..."
    },
    {
        "id": "chunk2",
        "analysis_id": "abc-123",
        "file_path": "src/utils.py",
        "chunk_text": "def helper(): ..."
    }
]
count = await vector_service.index_embeddings(embeddings, metadata)

# 시맨틱 검색
query_vector = np.array([0.15, 0.25, ..., 0.55])
results = await vector_service.search(
    query_vector=query_vector,
    k=5,
    filter_dict={"analysis_id": "abc-123"}
)

for result in results:
    print(f"Score: {result['score']}, File: {result['metadata']['file_path']}")
```

## 헬스체크

### 엔드포인트: `/health`

```bash
curl http://localhost:8000/health
```

**응답 예시 (정상)**:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "neo4j": "connected",
    "opensearch": "connected"
  }
}
```

**응답 예시 (일부 장애)**:
```json
{
  "status": "degraded",
  "services": {
    "database": "connected",
    "neo4j": "disconnected",
    "opensearch": "connected"
  }
}
```

## 싱글톤 패턴

GraphService와 VectorService는 애플리케이션 생명주기 동안 **싱글톤**으로 관리됩니다:

```python
# dependencies.py
_graph_service: IGraphService = None
_vector_service: IVectorService = None

def get_graph_service() -> IGraphService:
    global _graph_service
    if _graph_service is None:
        # 환경에 따라 구현체 생성 (한 번만)
        _graph_service = LocalGraphService(...) or AwsGraphService(...)
    return _graph_service
```

**장점**:
- 연결 풀 재사용
- 메모리 효율성
- 일관된 상태 관리

## Phase 3 (AWS 구현) 준비사항

### AwsGraphService 구현 계획

```python
# common/graph_service/aws_service.py
from .base import IGraphService

class AwsGraphService(IGraphService):
    """AWS Neo4j AuraDB 또는 Amazon Neptune 서비스"""

    def __init__(self, uri: str, user: str, password: str):
        # Neo4j AuraDB 연결
        # 또는 Neptune Gremlin 연결
        pass

    async def execute_query(self, query, parameters):
        # Cypher 쿼리 실행 (AuraDB)
        # 또는 Gremlin 쿼리 변환 (Neptune)
        pass
```

### AwsVectorService 구현 계획

```python
# common/vector_service/aws_service.py
from .base import IVectorService
import boto3

class AwsVectorService(IVectorService):
    """AWS OpenSearch Serverless 서비스"""

    def __init__(self, endpoint: str, region: str):
        self.endpoint = endpoint
        self.region = region
        self.client = boto3.client('opensearchserverless', region_name=region)

    async def index_embeddings(self, embeddings, metadata, index_name):
        # OpenSearch Serverless 벡터 인덱싱
        pass

    async def search(self, query_vector, k, filter_dict, index_name):
        # k-NN 검색 (Serverless)
        pass
```

## 테스트

### 로컬 연결 테스트

```bash
# Docker Compose 시작
docker-compose up -d neo4j opensearch

# 백엔드 시작
docker-compose up backend

# 헬스체크 확인
curl http://localhost:8000/health
```

### 의존성 주입 테스트

```python
# tests/test_graph_service.py
import pytest
from common.dependencies import get_graph_service

@pytest.mark.asyncio
async def test_graph_service_local():
    service = get_graph_service()
    assert service is not None

    # 헬스체크
    healthy = await service.check_health()
    assert healthy is True

    # 간단한 쿼리
    results = await service.execute_query("RETURN 1 as test")
    assert results[0]["test"] == 1
```

## 문제 해결

### Neo4j 연결 실패
```bash
# 로그 확인
docker-compose logs neo4j

# Cypher Shell 직접 연결 테스트
docker-compose exec neo4j cypher-shell -u neo4j -p sesami_graph_2025

# 헬스체크
curl http://localhost:8000/health
```

### OpenSearch 연결 실패
```bash
# 클러스터 상태 확인
curl -k -u admin:Sesami@OpenSearch2025! https://localhost:9200/_cluster/health

# 로그 확인
docker-compose logs opensearch

# 인덱스 목록
curl -k -u admin:Sesami@OpenSearch2025! https://localhost:9200/_cat/indices?v
```

## 참고 문서

- [TaskService 패턴](./task_service/README.md)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [OpenSearch Python Client](https://opensearch.org/docs/latest/clients/python/)
- [Graph-RAG 전체 계획](../../docs/design/v2/PROJECT_PLAN_V2.md)
