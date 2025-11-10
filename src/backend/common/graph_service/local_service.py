from typing import Dict, List, Any, Optional
from uuid import UUID
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from .base import IGraphService


class LocalGraphService(IGraphService):
    """로컬 Neo4j Community 그래프 서비스"""

    def __init__(self, uri: str, user: str, password: str):
        """
        Args:
            uri: Neo4j 연결 URI (예: "bolt://neo4j:7687")
            user: Neo4j 사용자명
            password: Neo4j 비밀번호
        """
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    def _get_driver(self):
        """Neo4j 드라이버 Lazy 초기화"""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        return self._driver

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Cypher 쿼리 실행"""
        driver = self._get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def create_nodes(
        self,
        nodes: List[Dict[str, Any]],
        label: str
    ) -> int:
        """노드 일괄 생성 (UNWIND 사용)"""
        if not nodes:
            return 0

        query = f"""
        UNWIND $nodes AS node
        CREATE (n:{label})
        SET n = node
        RETURN count(n) as created_count
        """

        result = await self.execute_query(query, {"nodes": nodes})
        return result[0]["created_count"] if result else 0

    async def create_relationships(
        self,
        relationships: List[Dict[str, Any]],
        rel_type: str
    ) -> int:
        """관계 일괄 생성

        relationships 구조:
        [
            {
                "from_id": "node_id_1",
                "to_id": "node_id_2",
                "properties": {"weight": 1.0}
            }
        ]
        """
        if not relationships:
            return 0

        query = f"""
        UNWIND $rels AS rel
        MATCH (a {{id: rel.from_id}})
        MATCH (b {{id: rel.to_id}})
        CREATE (a)-[r:{rel_type}]->(b)
        SET r = rel.properties
        RETURN count(r) as created_count
        """

        result = await self.execute_query(query, {"rels": relationships})
        return result[0]["created_count"] if result else 0

    async def get_graph_snapshot(
        self,
        analysis_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """분석 ID로 그래프 스냅샷 조회

        Note: 실제로는 PostgreSQL graph_snapshot 테이블에서 조회하지만,
        여기서는 그래프 메타데이터만 반환
        """
        query = """
        MATCH (n)
        WHERE n.analysis_id = $analysis_id
        RETURN
            count(n) as node_count,
            count(distinct labels(n)) as label_count
        LIMIT 1
        """

        result = await self.execute_query(query, {"analysis_id": str(analysis_id)})
        return result[0] if result else None

    async def check_health(self) -> bool:
        """Neo4j 연결 상태 확인"""
        try:
            driver = self._get_driver()
            await driver.verify_connectivity()
            return True
        except (ServiceUnavailable, AuthError):
            return False

    async def close(self):
        """드라이버 연결 종료"""
        if self._driver:
            await self._driver.close()
            self._driver = None
