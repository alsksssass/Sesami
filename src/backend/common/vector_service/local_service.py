from typing import Dict, List, Any, Optional
import numpy as np
from opensearchpy import AsyncOpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError, RequestError

from .base import IVectorService


class LocalVectorService(IVectorService):
    """로컬 OpenSearch 벡터 서비스"""

    def __init__(
        self,
        endpoint: str,
        user: str,
        password: str,
        default_index: str = "code_embeddings"
    ):
        """
        Args:
            endpoint: OpenSearch 엔드포인트 (예: "https://opensearch:9200")
            user: OpenSearch 사용자명
            password: OpenSearch 비밀번호
            default_index: 기본 인덱스 이름
        """
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.default_index = default_index
        self._client = None

    def _get_client(self):
        """OpenSearch 클라이언트 Lazy 초기화"""
        if self._client is None:
            self._client = AsyncOpenSearch(
                hosts=[self.endpoint],
                http_auth=(self.user, self.password),
                use_ssl=True,
                verify_certs=False,  # 로컬 개발용, 프로덕션에서는 True로 변경
                connection_class=RequestsHttpConnection
            )
        return self._client

    async def index_embeddings(
        self,
        embeddings: List[np.ndarray],
        metadata: List[Dict[str, Any]],
        index_name: Optional[str] = None
    ) -> int:
        """임베딩 벡터를 벌크 인덱싱"""
        if not embeddings or len(embeddings) != len(metadata):
            raise ValueError("embeddings와 metadata 길이가 일치해야 합니다")

        index = index_name or self.default_index
        client = self._get_client()

        # 벌크 인덱싱을 위한 액션 생성
        actions = []
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            actions.append({
                "index": {
                    "_index": index,
                    "_id": meta.get("id", f"{meta.get('analysis_id')}_{i}")
                }
            })
            actions.append({
                "vector": embedding.tolist(),
                "metadata": meta
            })

        # 벌크 요청 실행
        response = await client.bulk(body=actions)

        # 성공한 인덱싱 수 계산
        indexed_count = sum(1 for item in response["items"] if item["index"]["status"] == 201)
        return indexed_count

    async def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """k-NN 벡터 검색"""
        index = index_name or self.default_index
        client = self._get_client()

        # k-NN 쿼리 구성
        query_body = {
            "size": k,
            "query": {
                "knn": {
                    "vector": {
                        "vector": query_vector.tolist(),
                        "k": k
                    }
                }
            }
        }

        # 필터 추가
        if filter_dict:
            query_body["query"] = {
                "bool": {
                    "must": [
                        {"knn": {"vector": {"vector": query_vector.tolist(), "k": k}}}
                    ],
                    "filter": [
                        {"term": {f"metadata.{key}": value}}
                        for key, value in filter_dict.items()
                    ]
                }
            }

        response = await client.search(index=index, body=query_body)

        # 결과 변환
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "score": hit["_score"],
                "metadata": hit["_source"]["metadata"],
                "vector": hit["_source"]["vector"]
            })

        return results

    async def delete_by_analysis_id(
        self,
        analysis_id: str,
        index_name: Optional[str] = None
    ) -> int:
        """특정 분석 ID의 모든 문서 삭제"""
        index = index_name or self.default_index
        client = self._get_client()

        query_body = {
            "query": {
                "term": {
                    "metadata.analysis_id": analysis_id
                }
            }
        }

        response = await client.delete_by_query(index=index, body=query_body)
        return response.get("deleted", 0)

    async def create_index(
        self,
        index_name: str,
        dimension: int,
        metric: str = "cosine"
    ) -> bool:
        """벡터 인덱스 생성"""
        client = self._get_client()

        # OpenSearch k-NN 인덱스 매핑
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "vector": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": metric,
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "metadata": {
                        "type": "object"
                    }
                }
            }
        }

        try:
            await client.indices.create(index=index_name, body=index_body)
            return True
        except RequestError as e:
            if "resource_already_exists_exception" in str(e):
                return True  # 이미 존재하는 경우 성공으로 처리
            raise

    async def check_health(self) -> bool:
        """OpenSearch 클러스터 상태 확인"""
        try:
            client = self._get_client()
            health = await client.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception:
            return False

    async def close(self):
        """클라이언트 연결 종료"""
        if self._client:
            await self._client.close()
            self._client = None
