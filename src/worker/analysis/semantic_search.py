"""
Graph-RAG v2: 시맨틱 코드 검색

AWS Bedrock 또는 OpenAI 임베딩 생성 및
OpenSearch/Qdrant 벡터 인덱싱

Features:
- 코드 청킹 (함수 단위/토큰 단위)
- 임베딩 생성 (Bedrock Titan, OpenAI)
- OpenSearch k-NN 인덱싱
- S3 기반 임베딩 캐싱

PDD v4.0 업데이트:
- 환경변수 기반 자동 provider 선택
- config.py 통합
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

import numpy as np
from config import EmbeddingConfig
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from opensearchpy import OpenSearch, RequestsHttpConnection


class SemanticSearch:
    """
    시맨틱 코드 검색 및 임베딩 관리

    Supported Embedding Models:
    - AWS Bedrock: amazon.titan-embed-text-v1 (1024 dim)
    - OpenAI: text-embedding-3-large (1536 dim)
    """

    def __init__(
        self,
        opensearch_endpoint: str,
        opensearch_user: str,
        opensearch_password: str,
        embedding_provider: Optional[str] = None,  # None = 환경변수 기반 자동 선택
        embedding_model: Optional[str] = None,
        aws_region: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        s3_cache_bucket: Optional[str] = None
    ):
        """
        Args:
            opensearch_endpoint: OpenSearch 엔드포인트
            opensearch_user: OpenSearch 사용자명
            opensearch_password: OpenSearch 비밀번호
            embedding_provider: "bedrock" 또는 "openai" (None이면 환경변수 USE_BEDROCK 기반 자동 선택)
            embedding_model: 모델 ID (None이면 환경변수 기반 자동 선택)
            aws_region: AWS 리전 (None이면 환경변수 기반 자동 선택)
            openai_api_key: OpenAI API 키 (provider="openai" 시 필수, None이면 환경변수 사용)
            s3_cache_bucket: S3 캐시 버킷 (선택사항)
        """
        if not TIKTOKEN_AVAILABLE:
            raise RuntimeError("tiktoken not installed. Install with: pip install tiktoken")

        # 환경변수 기반 자동 설정 (PDD v4.0)
        if embedding_provider is None:
            config = EmbeddingConfig.get_provider()
            embedding_provider = config['provider']

            if embedding_provider == 'bedrock':
                embedding_model = embedding_model or config['model_id']
                aws_region = aws_region or config['region']
                s3_cache_bucket = s3_cache_bucket or config.get('s3_cache_bucket')
            else:  # openai
                openai_api_key = openai_api_key or config.get('api_key')
                embedding_model = embedding_model or config['model']

        # OpenSearch 클라이언트
        self.opensearch = OpenSearch(
            hosts=[opensearch_endpoint],
            http_auth=(opensearch_user, opensearch_password),
            use_ssl=True,
            verify_certs=False,  # 로컬 개발용, 프로덕션에서는 True
            connection_class=RequestsHttpConnection
        )

        # 임베딩 설정
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.aws_region = aws_region
        self.s3_cache_bucket = s3_cache_bucket

        # Bedrock 클라이언트
        if embedding_provider == "bedrock":
            if not BOTO3_AVAILABLE:
                raise RuntimeError("boto3 not installed. Install with: pip install boto3")
            self.bedrock = boto3.client('bedrock-runtime', region_name=aws_region)

        # OpenAI 클라이언트
        elif embedding_provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("openai not installed. Install with: pip install openai")
            if not openai_api_key:
                raise ValueError("OpenAI API key required for provider='openai'")
            openai.api_key = openai_api_key
            self.openai_client = openai.OpenAI(api_key=openai_api_key)

        # Tokenizer (GPT-4 기준)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # S3 클라이언트 (캐싱용)
        if s3_cache_bucket and BOTO3_AVAILABLE:
            self.s3 = boto3.client('s3', region_name=aws_region)
        else:
            self.s3 = None

        print(f"✅ SemanticSearch initialized: {embedding_provider}/{embedding_model}")

    def chunk_code(
        self,
        file_content: str,
        file_path: str,
        chunk_size: int = 200,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        코드 청킹 (토큰 기반 슬라이딩 윈도우)

        Args:
            file_content: 파일 전체 내용
            file_path: 파일 경로 (메타데이터용)
            chunk_size: 청크 크기 (토큰 수)
            overlap: 오버랩 크기 (토큰 수)

        Returns:
            chunks: [{"text": "...", "metadata": {...}}, ...]
        """
        tokens = self.tokenizer.encode(file_content)
        chunks = []

        start = 0
        chunk_idx = 0

        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "file_path": file_path,
                    "chunk_index": chunk_idx,
                    "token_count": len(chunk_tokens),
                    "start_token": start,
                    "end_token": end
                }
            })

            chunk_idx += 1
            start += (chunk_size - overlap)

        print(f"  📄 Chunked {file_path}: {len(chunks)} chunks ({len(tokens)} tokens)")
        return chunks

    def generate_embeddings(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[np.ndarray]:
        """
        텍스트 리스트를 임베딩 벡터로 변환

        Args:
            texts: 텍스트 리스트
            use_cache: S3 캐시 사용 여부

        Returns:
            embeddings: [np.ndarray, ...] (각 1024 or 1536 차원)
        """
        embeddings = []

        for i, text in enumerate(texts):
            # 캐시 확인
            if use_cache and self.s3 and self.s3_cache_bucket:
                cached_embedding = self._get_cached_embedding(text)
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                    continue

            # 임베딩 생성
            if self.embedding_provider == "bedrock":
                embedding = self._generate_bedrock_embedding(text)
            elif self.embedding_provider == "openai":
                embedding = self._generate_openai_embedding(text)
            else:
                raise ValueError(f"Unknown embedding provider: {self.embedding_provider}")

            embeddings.append(embedding)

            # 캐시 저장
            if use_cache and self.s3 and self.s3_cache_bucket:
                self._save_embedding_to_cache(text, embedding)

            if (i + 1) % 10 == 0:
                print(f"  🔢 Generated {i + 1}/{len(texts)} embeddings...")

        print(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings

    def _generate_bedrock_embedding(self, text: str) -> np.ndarray:
        """Bedrock Titan으로 임베딩 생성"""
        try:
            response = self.bedrock.invoke_model(
                modelId=self.embedding_model,
                body=json.dumps({"inputText": text})
            )

            response_body = json.loads(response['body'].read())
            embedding = np.array(response_body['embedding'], dtype=np.float32)
            return embedding

        except ClientError as e:
            print(f"❌ Bedrock error: {e}")
            # Fallback: 제로 벡터 반환
            return np.zeros(1024, dtype=np.float32)

    def _generate_openai_embedding(self, text: str) -> np.ndarray:
        """OpenAI로 임베딩 생성"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding

        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            # Fallback: 제로 벡터 반환
            return np.zeros(1536, dtype=np.float32)

    def _get_cache_key(self, text: str) -> str:
        """텍스트의 캐시 키 생성 (SHA256 해시)"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """S3에서 캐시된 임베딩 가져오기"""
        cache_key = self._get_cache_key(text)
        s3_key = f"embeddings/{self.embedding_model}/{cache_key}.npy"

        try:
            obj = self.s3.get_object(Bucket=self.s3_cache_bucket, Key=s3_key)
            embedding_bytes = obj['Body'].read()
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            return embedding

        except self.s3.exceptions.NoSuchKey:
            return None
        except Exception as e:
            print(f"⚠️  Cache read error: {e}")
            return None

    def _save_embedding_to_cache(self, text: str, embedding: np.ndarray):
        """임베딩을 S3에 캐싱"""
        cache_key = self._get_cache_key(text)
        s3_key = f"embeddings/{self.embedding_model}/{cache_key}.npy"

        try:
            self.s3.put_object(
                Bucket=self.s3_cache_bucket,
                Key=s3_key,
                Body=embedding.tobytes()
            )
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")

    def index_to_opensearch(
        self,
        embeddings: List[np.ndarray],
        metadata: List[Dict[str, Any]],
        index_name: str = "code_embeddings"
    ) -> int:
        """
        OpenSearch에 벡터 인덱싱

        Args:
            embeddings: 임베딩 벡터 리스트
            metadata: 각 임베딩의 메타데이터
            index_name: 인덱스 이름

        Returns:
            indexed_count: 인덱싱된 문서 수
        """
        if len(embeddings) != len(metadata):
            raise ValueError("embeddings와 metadata 길이 불일치")

        # 인덱스 존재 확인 및 생성
        if not self.opensearch.indices.exists(index=index_name):
            self._create_index(index_name, dimension=len(embeddings[0]))

        # 벌크 인덱싱
        bulk_actions = []
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            doc_id = meta.get('id', f"{meta['file_path']}_{i}")

            bulk_actions.append({"index": {"_index": index_name, "_id": doc_id}})
            bulk_actions.append({
                "vector": embedding.tolist(),
                "metadata": meta
            })

        # 벌크 요청 실행
        response = self.opensearch.bulk(body=bulk_actions)

        # 성공 카운트
        indexed_count = sum(
            1 for item in response['items']
            if item['index']['status'] in [200, 201]
        )

        print(f"✅ Indexed {indexed_count}/{len(embeddings)} documents to '{index_name}'")
        return indexed_count

    def _create_index(self, index_name: str, dimension: int):
        """OpenSearch k-NN 인덱스 생성"""
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
                            "space_type": "cosinesimil",
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

        self.opensearch.indices.create(index=index_name, body=index_body)
        print(f"✅ Created OpenSearch index: {index_name} ({dimension} dim)")

    def query(
        self,
        natural_language_query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: str = "code_embeddings"
    ) -> List[Dict[str, Any]]:
        """
        자연어 쿼리로 유사 코드 검색

        Args:
            natural_language_query: 자연어 질문
            k: 반환할 결과 수
            filter_dict: 메타데이터 필터 (예: {"analysis_id": "..."})
            index_name: 검색할 인덱스

        Returns:
            results: [{"score": ..., "metadata": {...}, "text": "..."}, ...]
        """
        # 쿼리 임베딩 생성
        query_embedding = self.generate_embeddings([natural_language_query])[0]

        # k-NN 검색 쿼리 구성
        search_body = {
            "size": k,
            "query": {
                "knn": {
                    "vector": {
                        "vector": query_embedding.tolist(),
                        "k": k
                    }
                }
            }
        }

        # 필터 추가
        if filter_dict:
            search_body["query"] = {
                "bool": {
                    "must": [
                        {"knn": {"vector": {"vector": query_embedding.tolist(), "k": k}}}
                    ],
                    "filter": [
                        {"term": {f"metadata.{key}": value}}
                        for key, value in filter_dict.items()
                    ]
                }
            }

        # 검색 실행
        response = self.opensearch.search(index=index_name, body=search_body)

        # 결과 변환
        results = []
        for hit in response['hits']['hits']:
            results.append({
                "score": hit['_score'],
                "metadata": hit['_source']['metadata'],
                "text": hit['_source']['metadata'].get('chunk_text', '')
            })

        print(f"✅ Query returned {len(results)} results")
        return results
