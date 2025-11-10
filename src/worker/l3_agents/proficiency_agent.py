"""
Proficiency Agent: 코드 숙련도 평가 (PDD v4.0 핵심)

Graph-RAG + Vector-RAG + LLM을 통합하여
개발자의 코드 작성 수준을 심층 분석합니다.
"""
from typing import Dict, Any
from pathlib import Path

from .base_agent import IL3Agent, AgentExecutionError


class ProficiencyAgent(IL3Agent):
    """
    코드 숙련도 평가 에이전트

    평가 기준:
    1. 구조적 수준 (Graph-RAG):
       - 아키텍처적 중요도 (핵심 모듈인가?)
       - 의존성 복잡도 (몇 개 모듈과 연결되었나?)
       - 계층 위치 (인프라/비즈니스 로직/UI 중 어디인가?)

    2. 의미적 효율성 (Vector-RAG):
       - 알고리즘 패턴 (유사 코드와 비교)
       - 코드 재사용성
       - 업계 베스트 프랙티스 준수 여부

    3. 정성적 판단 (LLM):
       - 1+2의 컨텍스트를 바탕으로 최종 수준 결정
       - Junior/Mid/Senior/Expert 분류
       - 근거 및 개선 제안
    """

    def __init__(self, graph_service, vector_service, llm_client):
        super().__init__(
            agent_name="PROFICIENCY_AGENT",
            graph_service=graph_service,
            vector_service=vector_service,
            llm_client=llm_client
        )

    def analyze(self, file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        코드 숙련도 평가 수행

        Args:
            file_path: 분석 대상 파일
            context: L3-Tool 결과 (pylint, sonarqube 등)

        Returns:
            {
                "level": str,              # "Junior" | "Mid" | "Senior" | "Expert"
                "confidence": float,       # 0.0 ~ 1.0
                "reasoning": str,          # LLM의 판단 근거
                "graph_insights": dict,    # Neo4j 분석 결과
                "vector_insights": dict,   # OpenSearch 분석 결과
                "suggestions": list,       # 개선 제안
                "tokens_used": int         # LLM 토큰 사용량
            }
        """
        try:
            # 1️⃣ Graph-RAG: 구조적 수준 분석
            graph_insights = self._analyze_structural_level(file_path)

            # 2️⃣ Vector-RAG: 의미적 효율성 분석
            vector_insights = self._analyze_semantic_efficiency(file_path)

            # 3️⃣ LLM: 최종 판단
            llm_assessment = self._llm_final_assessment(
                file_path=file_path,
                context=context,
                graph_insights=graph_insights,
                vector_insights=vector_insights
            )

            return {
                "level": llm_assessment["level"],
                "confidence": llm_assessment["confidence"],
                "reasoning": llm_assessment["reasoning"],
                "graph_insights": graph_insights,
                "vector_insights": vector_insights,
                "suggestions": llm_assessment.get("suggestions", []),
                "tokens_used": llm_assessment["tokens_used"]
            }

        except Exception as e:
            raise AgentExecutionError(f"Proficiency 분석 실패: {e}")

    def _analyze_structural_level(self, file_path: str) -> Dict[str, Any]:
        """
        Graph-RAG를 사용하여 구조적 수준 분석

        Neo4j Cypher 쿼리로 다음을 분석:
        - 아키텍처적 중요도 (PageRank, Betweenness Centrality)
        - 의존성 복잡도 (in/out degree)
        - 계층 위치 (깊이, 패턴)
        """
        file_name = Path(file_path).name

        # Cypher 쿼리: 파일의 구조적 위치 분석
        cypher_query = """
        MATCH (f:File {path: $file_path})
        OPTIONAL MATCH (f)-[r_out:CALLS|IMPORTS]->(target)
        OPTIONAL MATCH (source)-[r_in:CALLS|IMPORTS]->(f)
        RETURN
            f.path AS file_path,
            COUNT(DISTINCT r_out) AS outgoing_dependencies,
            COUNT(DISTINCT r_in) AS incoming_dependencies,
            f.loc AS lines_of_code,
            f.complexity AS cyclomatic_complexity,
            labels(f) AS labels
        """

        try:
            result = self.query_graph(cypher_query, {"file_path": file_path})

            if not result or len(result) == 0:
                return {
                    "importance_score": 0.0,
                    "dependency_complexity": "low",
                    "layer": "unknown",
                    "note": "Graph에서 파일을 찾을 수 없음"
                }

            record = result[0]

            # 의존성 복잡도 계산
            total_deps = record["outgoing_dependencies"] + record["incoming_dependencies"]
            dependency_level = "low" if total_deps < 5 else ("medium" if total_deps < 15 else "high")

            # 중요도 점수 (간단한 휴리스틱)
            importance_score = min(1.0, (record["incoming_dependencies"] * 0.7 + record["outgoing_dependencies"] * 0.3) / 20.0)

            # 계층 추론 (파일 경로 기반)
            layer = self._infer_layer(file_path)

            return {
                "importance_score": round(importance_score, 2),
                "dependency_complexity": dependency_level,
                "layer": layer,
                "outgoing_deps": record["outgoing_dependencies"],
                "incoming_deps": record["incoming_dependencies"],
                "lines_of_code": record.get("loc", 0),
                "cyclomatic_complexity": record.get("cyclomatic_complexity", 0)
            }

        except Exception as e:
            return {
                "importance_score": 0.0,
                "dependency_complexity": "unknown",
                "layer": "unknown",
                "error": str(e)
            }

    def _infer_layer(self, file_path: str) -> str:
        """파일 경로로부터 아키텍처 계층 추론"""
        path_lower = file_path.lower()

        if any(keyword in path_lower for keyword in ['database', 'db', 'repository', 'dao']):
            return "infrastructure"
        elif any(keyword in path_lower for keyword in ['service', 'business', 'logic', 'usecase']):
            return "business_logic"
        elif any(keyword in path_lower for keyword in ['api', 'controller', 'router', 'endpoint']):
            return "api"
        elif any(keyword in path_lower for keyword in ['ui', 'view', 'component', 'frontend']):
            return "presentation"
        else:
            return "unknown"

    def _analyze_semantic_efficiency(self, file_path: str) -> Dict[str, Any]:
        """
        Vector-RAG를 사용하여 의미적 효율성 분석

        OpenSearch k-NN 검색으로:
        - 유사 코드 패턴 찾기
        - 알고리즘 효율성 비교
        - 베스트 프랙티스 참조
        """
        file_name = Path(file_path).name

        # 자연어 쿼리: "이 파일과 유사한 알고리즘 패턴"
        query_text = f"Similar code patterns and algorithms for {file_name}"

        try:
            # Vector 검색 (상위 5개)
            similar_codes = self.query_vector(query_text, k=5)

            if not similar_codes or len(similar_codes) == 0:
                return {
                    "similarity_score": 0.0,
                    "pattern_reuse": "unknown",
                    "note": "Vector Index에서 유사 코드를 찾을 수 없음"
                }

            # 유사도 점수 (첫 번째 결과 기준)
            top_similarity = similar_codes[0].get("score", 0.0)

            # 패턴 재사용성 판단
            pattern_reuse = "high" if top_similarity > 0.8 else ("medium" if top_similarity > 0.6 else "low")

            return {
                "similarity_score": round(top_similarity, 2),
                "pattern_reuse": pattern_reuse,
                "similar_files_count": len(similar_codes),
                "top_similar_file": similar_codes[0].get("metadata", {}).get("file_path", "unknown") if similar_codes else None
            }

        except Exception as e:
            return {
                "similarity_score": 0.0,
                "pattern_reuse": "unknown",
                "error": str(e)
            }

    def _llm_final_assessment(
        self,
        file_path: str,
        context: Dict[str, Any],
        graph_insights: Dict[str, Any],
        vector_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        LLM을 사용한 최종 수준 판단

        Graph/Vector 컨텍스트와 L3-Tool 결과를 종합하여
        개발자의 숙련도를 평가합니다.
        """
        # 시스템 프롬프트
        system_prompt = """당신은 코드 리뷰 전문가입니다.
주어진 코드의 구조적 수준(Graph-RAG)과 의미적 효율성(Vector-RAG)을 바탕으로
개발자의 숙련도를 평가하세요.

평가 기준:
- Junior: 기본 문법은 알지만 아키텍처 이해 부족
- Mid: 구조를 이해하고 적절한 패턴 사용
- Senior: 복잡한 의존성 관리, 최적화된 알고리즘
- Expert: 아키텍처 설계 주도, 혁신적 패턴 도입

응답 형식 (JSON):
{
    "level": "Junior" | "Mid" | "Senior" | "Expert",
    "confidence": 0.0 ~ 1.0,
    "reasoning": "판단 근거 (1-2문장)",
    "suggestions": ["개선 제안 1", "개선 제안 2"]
}
"""

        # 사용자 프롬프트
        user_prompt = f"""파일: {file_path}

구조적 분석 (Graph-RAG):
- 중요도: {graph_insights.get('importance_score', 0)}
- 의존성 복잡도: {graph_insights.get('dependency_complexity', 'unknown')}
- 계층: {graph_insights.get('layer', 'unknown')}
- 외부 의존성: {graph_insights.get('outgoing_deps', 0)}개
- 내부 의존성: {graph_insights.get('incoming_deps', 0)}개

의미적 분석 (Vector-RAG):
- 유사도: {vector_insights.get('similarity_score', 0)}
- 패턴 재사용성: {vector_insights.get('pattern_reuse', 'unknown')}

정적 분석 (Pylint):
- 점수: {context.get('PYLINT_TOOL', {}).get('payload', {}).get('score', 'N/A')}
- 에러 수: {len(context.get('PYLINT_TOOL', {}).get('payload', {}).get('errors', []))}

위 정보를 바탕으로 개발자의 숙련도를 평가하고 JSON으로 반환하세요.
"""

        try:
            llm_response = self.invoke_llm(user_prompt, system_prompt)
            content = llm_response["content"]

            # JSON 파싱 (LLM이 JSON을 반환한다고 가정)
            import json
            assessment = json.loads(content)

            assessment["tokens_used"] = llm_response.get("tokens_used", 0)

            return assessment

        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값
            return {
                "level": "Mid",
                "confidence": 0.5,
                "reasoning": "LLM 응답 파싱 실패, 기본값 반환",
                "suggestions": [],
                "tokens_used": llm_response.get("tokens_used", 0)
            }

        except Exception as e:
            raise AgentExecutionError(f"LLM 평가 실패: {e}")

    def get_version(self) -> str:
        """에이전트 버전"""
        return "1.0.0"
