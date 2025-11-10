"""
Graph-RAG v2: Neo4j 그래프 빌더

Tree-sitter 파서를 사용하여 코드를 AST로 파싱하고
Neo4j 그래프 데이터베이스에 적재

Features:
- Tree-sitter 기반 AST 파싱 (Python, JavaScript, TypeScript, Java, Go)
- JSONL 스테이징 (EFS/로컬 저장소)
- Neo4j 대량 적재 (Cypher UNWIND)
- 커밋 해시 기반 스냅샷 캐싱
"""
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from uuid import UUID

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from neo4j import GraphDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Shared 모델 import
from shared.graph_models import GraphSnapshot


class GraphLoader:
    """
    Neo4j 그래프 적재 및 버전 관리

    Workflow:
    1. parse_with_tree_sitter() - AST 추출
    2. stage_to_jsonl() - EFS/로컬에 JSONL 저장
    3. bulk_load_to_neo4j() - Neo4j에 대량 적재
    4. create_snapshot() - PostgreSQL에 스냅샷 기록
    """

    # 지원 언어 매핑
    LANGUAGE_PARSERS = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
    }

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        postgres_url: str,
        staging_dir: str = "/tmp/graph_staging"
    ):
        """
        Args:
            neo4j_uri: Neo4j 연결 URI (bolt://...)
            neo4j_user: Neo4j 사용자명
            neo4j_password: Neo4j 비밀번호
            postgres_url: PostgreSQL 연결 URL (스냅샷 저장용)
            staging_dir: JSONL 스테이징 디렉토리
        """
        if not TREE_SITTER_AVAILABLE:
            raise RuntimeError(
                "Tree-sitter not installed. "
                "Install with: pip install tree-sitter tree-sitter-languages"
            )

        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

        # PostgreSQL 세션 (스냅샷 관리)
        engine = create_engine(postgres_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        # Tree-sitter 파서 초기화
        self._init_parsers()

    def _init_parsers(self):
        """Tree-sitter 언어 파서 초기화"""
        self.parsers = {}

        # Python 파서
        PY_LANGUAGE = Language(tspython.language())
        py_parser = Parser(PY_LANGUAGE)
        self.parsers['python'] = py_parser

        # JavaScript/TypeScript 파서
        JS_LANGUAGE = Language(tsjavascript.language())
        js_parser = Parser(JS_LANGUAGE)
        self.parsers['javascript'] = js_parser
        self.parsers['typescript'] = js_parser  # 동일 파서 사용

        print("✅ Tree-sitter parsers initialized: python, javascript, typescript")

    def parse_with_tree_sitter(
        self,
        repo_path: str,
        file_extensions: Optional[List[str]] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Tree-sitter로 저장소의 모든 파일 파싱

        Args:
            repo_path: Git 저장소 경로
            file_extensions: 파싱할 파일 확장자 (None이면 모든 지원 언어)

        Returns:
            (nodes, edges): 노드 리스트, 엣지 리스트
        """
        if file_extensions is None:
            file_extensions = list(self.LANGUAGE_PARSERS.keys())

        nodes = []
        edges = []
        file_count = 0

        repo_root = Path(repo_path)
        print(f"🔍 Parsing repository: {repo_root}")

        for ext in file_extensions:
            if ext not in self.LANGUAGE_PARSERS:
                print(f"⚠️  Unsupported extension: {ext}")
                continue

            language = self.LANGUAGE_PARSERS[ext]
            parser = self.parsers.get(language)

            if not parser:
                print(f"⚠️  No parser for language: {language}")
                continue

            # 해당 확장자 파일 찾기
            pattern = f"**/*{ext}"
            for file_path in repo_root.glob(pattern):
                if self._should_skip_file(file_path):
                    continue

                file_nodes, file_edges = self._parse_file(file_path, parser, language, repo_root)
                nodes.extend(file_nodes)
                edges.extend(file_edges)
                file_count += 1

                if file_count % 50 == 0:
                    print(f"  📄 Parsed {file_count} files ({len(nodes)} nodes, {len(edges)} edges)...")

        print(f"✅ Parsing complete: {file_count} files → {len(nodes)} nodes, {len(edges)} edges")
        return nodes, edges

    def _should_skip_file(self, file_path: Path) -> bool:
        """파일 스킵 여부 결정"""
        skip_dirs = {'node_modules', '.git', '__pycache__', 'venv', 'dist', 'build'}
        return any(part in skip_dirs for part in file_path.parts)

    def _parse_file(
        self,
        file_path: Path,
        parser: Parser,
        language: str,
        repo_root: Path
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        단일 파일 파싱 (Tree-sitter)

        Returns:
            (file_nodes, file_edges)
        """
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()

            tree = parser.parse(source_code)
            root_node = tree.root_node

            # 파일 노드 생성
            rel_path = str(file_path.relative_to(repo_root))
            file_node = {
                "id": f"file:{rel_path}",
                "type": "File",
                "path": rel_path,
                "language": language,
                "loc": source_code.count(b'\n') + 1
            }

            nodes = [file_node]
            edges = []

            # 함수/클래스 노드 추출
            if language == 'python':
                func_nodes, class_nodes, func_edges = self._extract_python_symbols(
                    root_node, source_code, rel_path
                )
                nodes.extend(func_nodes)
                nodes.extend(class_nodes)
                edges.extend(func_edges)

            elif language in ['javascript', 'typescript']:
                func_nodes, class_nodes, func_edges = self._extract_js_symbols(
                    root_node, source_code, rel_path
                )
                nodes.extend(func_nodes)
                nodes.extend(class_nodes)
                edges.extend(func_edges)

            return nodes, edges

        except Exception as e:
            print(f"⚠️  Failed to parse {file_path}: {e}")
            return [], []

    def _extract_python_symbols(
        self,
        root_node,
        source_code: bytes,
        file_path: str
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Python AST에서 함수/클래스 추출"""
        functions = []
        classes = []
        edges = []

        # 재귀적으로 AST 탐색
        def traverse(node):
            if node.type == 'function_definition':
                func_name_node = node.child_by_field_name('name')
                if func_name_node:
                    func_name = source_code[func_name_node.start_byte:func_name_node.end_byte].decode('utf-8')
                    func_id = f"func:{file_path}:{func_name}"

                    functions.append({
                        "id": func_id,
                        "type": "Function",
                        "name": func_name,
                        "file_path": file_path,
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1
                    })

                    # File → Function 엣지
                    edges.append({
                        "from_id": f"file:{file_path}",
                        "to_id": func_id,
                        "type": "CONTAINS"
                    })

            elif node.type == 'class_definition':
                class_name_node = node.child_by_field_name('name')
                if class_name_node:
                    class_name = source_code[class_name_node.start_byte:class_name_node.end_byte].decode('utf-8')
                    class_id = f"class:{file_path}:{class_name}"

                    classes.append({
                        "id": class_id,
                        "type": "Class",
                        "name": class_name,
                        "file_path": file_path,
                        "start_line": node.start_point[0] + 1
                    })

                    # File → Class 엣지
                    edges.append({
                        "from_id": f"file:{file_path}",
                        "to_id": class_id,
                        "type": "CONTAINS"
                    })

            # 자식 노드 탐색
            for child in node.children:
                traverse(child)

        traverse(root_node)
        return functions, classes, edges

    def _extract_js_symbols(
        self,
        root_node,
        source_code: bytes,
        file_path: str
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """JavaScript/TypeScript AST에서 함수/클래스 추출"""
        # Python과 유사한 로직 (간략화)
        # 실제로는 'function_declaration', 'arrow_function', 'class_declaration' 등 처리
        functions = []
        classes = []
        edges = []

        # TODO: JS/TS 전용 파싱 로직 구현
        # 현재는 기본 구조만 제공

        return functions, classes, edges

    def stage_to_jsonl(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        analysis_id: str
    ) -> Tuple[str, str]:
        """
        JSONL 파일로 스테이징

        Args:
            nodes: 노드 리스트
            edges: 엣지 리스트
            analysis_id: 분석 작업 ID

        Returns:
            (nodes_file, edges_file): JSONL 파일 경로
        """
        analysis_dir = self.staging_dir / analysis_id
        analysis_dir.mkdir(parents=True, exist_ok=True)

        nodes_file = analysis_dir / "graph_nodes.jsonl"
        edges_file = analysis_dir / "graph_edges.jsonl"

        # 노드 JSONL 저장
        with open(nodes_file, 'w') as f:
            for node in nodes:
                f.write(json.dumps(node) + '\n')

        # 엣지 JSONL 저장
        with open(edges_file, 'w') as f:
            for edge in edges:
                f.write(json.dumps(edge) + '\n')

        print(f"✅ JSONL staged: {nodes_file} ({len(nodes)} nodes)")
        print(f"✅ JSONL staged: {edges_file} ({len(edges)} edges)")

        return str(nodes_file), str(edges_file)

    def bulk_load_to_neo4j(
        self,
        nodes_file: str,
        edges_file: str,
        batch_size: int = 1000
    ) -> Tuple[int, int]:
        """
        Neo4j에 대량 적재 (Cypher UNWIND)

        Args:
            nodes_file: 노드 JSONL 파일 경로
            edges_file: 엣지 JSONL 파일 경로
            batch_size: 배치 크기

        Returns:
            (nodes_created, edges_created)
        """
        start_time = time.time()

        # 노드 적재
        with open(nodes_file, 'r') as f:
            nodes = [json.loads(line) for line in f]

        nodes_created = self._create_nodes_batch(nodes, batch_size)

        # 엣지 적재
        with open(edges_file, 'r') as f:
            edges = [json.loads(line) for line in f]

        edges_created = self._create_edges_batch(edges, batch_size)

        elapsed = time.time() - start_time
        print(f"✅ Neo4j bulk load complete: {nodes_created} nodes, {edges_created} edges ({elapsed:.2f}s)")

        return nodes_created, edges_created

    def _create_nodes_batch(self, nodes: List[Dict], batch_size: int) -> int:
        """노드 배치 생성 (Cypher UNWIND)"""
        total_created = 0

        with self.neo4j_driver.session() as session:
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]

                # 타입별로 그룹화
                nodes_by_type = {}
                for node in batch:
                    node_type = node.get('type', 'Unknown')
                    if node_type not in nodes_by_type:
                        nodes_by_type[node_type] = []
                    nodes_by_type[node_type].append(node)

                # 타입별 UNWIND 쿼리 실행
                for node_type, typed_nodes in nodes_by_type.items():
                    query = f"""
                    UNWIND $nodes AS node
                    CREATE (n:{node_type})
                    SET n = node
                    """
                    result = session.run(query, nodes=typed_nodes)
                    total_created += len(typed_nodes)

                if (i + batch_size) % 5000 == 0:
                    print(f"  📊 Created {total_created}/{len(nodes)} nodes...")

        return total_created

    def _create_edges_batch(self, edges: List[Dict], batch_size: int) -> int:
        """엣지 배치 생성 (Cypher UNWIND)"""
        total_created = 0

        with self.neo4j_driver.session() as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i + batch_size]

                # 관계 타입별로 그룹화
                edges_by_type = {}
                for edge in batch:
                    edge_type = edge.get('type', 'RELATED_TO')
                    if edge_type not in edges_by_type:
                        edges_by_type[edge_type] = []
                    edges_by_type[edge_type].append(edge)

                # 타입별 UNWIND 쿼리 실행
                for edge_type, typed_edges in edges_by_type.items():
                    query = f"""
                    UNWIND $edges AS edge
                    MATCH (from {{id: edge.from_id}})
                    MATCH (to {{id: edge.to_id}})
                    CREATE (from)-[r:{edge_type}]->(to)
                    SET r.properties = COALESCE(edge.properties, {{}})
                    """
                    result = session.run(query, edges=typed_edges)
                    total_created += len(typed_edges)

                if (i + batch_size) % 5000 == 0:
                    print(f"  📊 Created {total_created}/{len(edges)} edges...")

        return total_created

    def create_snapshot(
        self,
        analysis_id: UUID,
        commit_hash: str,
        repo_url: str,
        node_count: int,
        edge_count: int,
        node_types: Dict[str, int],
        build_duration: int,
        branch: str = "main"
    ) -> str:
        """
        PostgreSQL에 그래프 스냅샷 기록

        Returns:
            snapshot_id (str)
        """
        snapshot = GraphSnapshot(
            analysis_id=analysis_id,
            commit_hash=commit_hash,
            repo_url=repo_url,
            branch=branch,
            node_count=node_count,
            edge_count=edge_count,
            node_types=node_types,
            build_duration_seconds=build_duration,
            is_valid=True
        )

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        print(f"✅ Snapshot created: {snapshot.id} (commit: {commit_hash[:8]})")
        return str(snapshot.id)

    def reuse_snapshot(self, commit_hash: str) -> Optional[str]:
        """
        커밋 해시 기반 스냅샷 재사용 가능 여부 확인

        Returns:
            snapshot_id (str) 또는 None
        """
        snapshot = self.db.query(GraphSnapshot).filter(
            GraphSnapshot.commit_hash == commit_hash,
            GraphSnapshot.is_valid == True
        ).first()

        if snapshot:
            print(f"✅ Reusing existing snapshot: {snapshot.id} (commit: {commit_hash[:8]})")
            return str(snapshot.id)

        print(f"ℹ️  No snapshot found for commit: {commit_hash[:8]}")
        return None

    def close(self):
        """리소스 정리"""
        self.neo4j_driver.close()
        self.db.close()
