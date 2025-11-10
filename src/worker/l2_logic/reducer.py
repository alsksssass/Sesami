"""
L2 Reducer: 중간 집계 (Map-Reduce의 Reduce)

PDD v4.0의 "L2-Reducer" 계층
- L3 결과물들을 tool_name 기준으로 동적 집계
- EFS에 l2_summary_{group_id}.json 저장
- L1이 이 요약본을 읽어서 최종 LLM 호출
"""
from typing import List, Dict, Any
from pathlib import Path
import json
import time

from shared.schemas.event_envelope import L2Summary


class L2Reducer:
    """
    L3 결과물 집계 로직

    집계 방식:
    - tool_name을 Key로 하는 동적 딕셔너리
    - 새로운 L3-Tool/Agent 추가 시 코드 수정 불필요
    """

    def __init__(self, efs_mount_path: str = "/mnt/efs"):
        self.efs_mount_path = Path(efs_mount_path)
        self.results_dir = self.efs_mount_path / "results"

    def aggregate_results(
        self,
        group_id: str,
        tool_results: List[Dict[str, Any]],
        agent_results: List[Dict[str, Any]]
    ) -> L2Summary:
        """
        L3 결과물들을 집계합니다.

        Args:
            group_id: L2 그룹 ID
            tool_results: L3-Tool Event Envelope 리스트
            agent_results: L3-Agent Event Envelope 리스트

        Returns:
            L2Summary: 중간 요약본
        """
        start_time = time.time()

        # 동적 딕셔너리 생성
        tools_summary = {}
        agents_summary = {}

        # L3-Tool 결과 집계
        for tool_result in tool_results:
            tool_name = tool_result.get("tool_name")
            if tool_name not in tools_summary:
                tools_summary[tool_name] = []

            tools_summary[tool_name].append({
                "file_path": tool_result.get("file_path"),
                "payload": tool_result.get("payload"),
                "execution_time_ms": tool_result.get("execution_time_ms")
            })

        # L3-Agent 결과 집계
        for agent_result in agent_results:
            agent_name = agent_result.get("tool_name")
            if agent_name not in agents_summary:
                agents_summary[agent_name] = []

            agents_summary[agent_name].append({
                "file_path": agent_result.get("file_path"),
                "payload": agent_result.get("payload"),
                "execution_time_ms": agent_result.get("execution_time_ms")
            })

        # 파일 수 계산
        file_count = len(set(
            [r.get("file_path") for r in tool_results if r.get("file_path")] +
            [r.get("file_path") for r in agent_results if r.get("file_path")]
        ))

        execution_time_ms = int((time.time() - start_time) * 1000)

        return L2Summary(
            group_id=group_id,
            file_count=file_count,
            tools_summary=tools_summary,
            agents_summary=agents_summary,
            execution_time_ms=execution_time_ms
        )

    def save_to_efs(self, summary: L2Summary) -> str:
        """
        L2 요약본을 EFS에 저장합니다.

        Args:
            summary: L2Summary 객체

        Returns:
            저장된 파일 경로
        """
        # 결과 디렉토리 생성
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 파일 경로
        file_name = f"l2_summary_{summary.group_id}.json"
        file_path = self.results_dir / file_name

        # JSON 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary.dict(), f, indent=2, ensure_ascii=False, default=str)

        return str(file_path)

    def load_from_efs(self, group_id: str) -> L2Summary:
        """
        EFS에서 L2 요약본을 로드합니다.

        Args:
            group_id: L2 그룹 ID

        Returns:
            L2Summary 객체

        Raises:
            FileNotFoundError: 파일이 없는 경우
        """
        file_name = f"l2_summary_{group_id}.json"
        file_path = self.results_dir / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"L2 요약본을 찾을 수 없음: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return L2Summary(**data)

    def load_all_summaries(self) -> List[L2Summary]:
        """
        모든 L2 요약본을 로드합니다 (L1이 호출)

        Returns:
            L2Summary 리스트
        """
        summaries = []

        if not self.results_dir.exists():
            return summaries

        for file_path in self.results_dir.glob("l2_summary_*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summaries.append(L2Summary(**data))

        return summaries


# 사용 예시
if __name__ == "__main__":
    # 테스트 데이터
    tool_results = [
        {
            "tool_name": "PYLINT_TOOL",
            "file_path": "main.py",
            "payload": {"score": 9.5},
            "execution_time_ms": 1200
        },
        {
            "tool_name": "PYLINT_TOOL",
            "file_path": "auth.py",
            "payload": {"score": 8.7},
            "execution_time_ms": 1500
        },
        {
            "tool_name": "SONARQUBE_TOOL",
            "file_path": "main.py",
            "payload": {"bugs": 0},
            "execution_time_ms": 2000
        }
    ]

    agent_results = [
        {
            "tool_name": "PROFICIENCY_AGENT",
            "file_path": "auth.py",
            "payload": {"level": "Senior", "confidence": 0.92},
            "execution_time_ms": 5000
        }
    ]

    reducer = L2Reducer(efs_mount_path="/tmp/test_efs")
    summary = reducer.aggregate_results("group_0001", tool_results, agent_results)

    print("L2 요약본:", summary.dict())

    # EFS 저장
    saved_path = reducer.save_to_efs(summary)
    print(f"저장 위치: {saved_path}")

    # 다시 로드
    loaded_summary = reducer.load_from_efs("group_0001")
    print(f"로드 성공: {loaded_summary.group_id}")
