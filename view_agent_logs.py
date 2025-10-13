"""
Agent Interaction Log Viewer
저장된 Agent 상호작용 로그를 조회하고 분석하는 유틸리티

Usage:
    python view_agent_logs.py                    # 최신 세션 보기
    python view_agent_logs.py --session SESSION_ID  # 특정 세션 보기
    python view_agent_logs.py --list             # 모든 세션 목록
    python view_agent_logs.py --agent database_agent  # 특정 Agent 필터링
    python view_agent_logs.py --stats            # 통계만 보기

Author: Orchestrator
Date: 2025-10-09
"""

import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class LogViewer:
    """로그 뷰어"""

    def __init__(self, log_dir: str = "storage/agent_interactions"):
        self.log_dir = Path(log_dir)

        if not self.log_dir.exists():
            print(f"[ERROR] Log directory not found: {self.log_dir}")
            exit(1)

    def list_sessions(self) -> List[Dict[str, str]]:
        """모든 세션 목록 반환"""
        sessions = []

        for yaml_file in sorted(self.log_dir.glob("session_*.yaml"), reverse=True):
            session_id = yaml_file.stem.replace("session_", "")

            # 파일 크기 및 수정 시간
            size_kb = yaml_file.stat().st_size / 1024
            mtime = datetime.fromtimestamp(yaml_file.stat().st_mtime)

            sessions.append({
                "session_id": session_id,
                "file": str(yaml_file),
                "size_kb": f"{size_kb:.2f}",
                "modified": mtime.strftime("%Y-%m-%d %H:%M:%S")
            })

        return sessions

    def load_session(self, session_id: str) -> Optional[Dict]:
        """특정 세션 로드"""
        yaml_file = self.log_dir / f"session_{session_id}.yaml"

        if not yaml_file.exists():
            print(f"[ERROR] Session not found: {session_id}")
            return None

        with open(yaml_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def load_latest_session(self) -> Optional[Dict]:
        """최신 세션 로드"""
        sessions = self.list_sessions()
        if not sessions:
            print("[ERROR] No sessions found")
            return None

        latest = sessions[0]
        return self.load_session(latest["session_id"])

    def display_statistics(self, session: Dict) -> None:
        """통계 정보 표시"""
        stats = session.get("statistics", {})

        print("\n" + "=" * 80)
        print("SESSION STATISTICS")
        print("=" * 80)
        print(f"Session ID: {session['session_id']}")
        print(f"Start Time: {session.get('start_time', 'N/A')}")
        print(f"End Time: {session.get('end_time', 'N/A')}")
        print("-" * 80)
        print(f"Total Interactions: {stats.get('total_interactions', 0)}")
        print(f"Prompts Sent: {stats.get('prompts_sent', 0)}")
        print(f"Responses Received: {stats.get('responses_received', 0)}")
        print(f"Errors Occurred: {stats.get('errors_occurred', 0)}")
        print("-" * 80)
        print(f"Total Tokens: {stats.get('total_tokens', 0):,}")
        print(f"Total Duration: {stats.get('total_duration_ms', 0):.2f}ms")
        print(f"Average Duration: {stats.get('average_duration_ms', 0):.2f}ms")
        print("-" * 80)
        print(f"Agents Used: {', '.join(stats.get('agents_used', []))}")
        print("=" * 80)

    def display_interactions(
        self,
        session: Dict,
        agent_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> None:
        """상호작용 내역 표시"""
        interactions = session.get("interactions", [])

        # Agent 필터링
        if agent_filter:
            interactions = [
                i for i in interactions
                if i['from_agent'] == agent_filter or i['to_agent'] == agent_filter
            ]

        # Limit 적용
        if limit:
            interactions = interactions[:limit]

        print("\n" + "=" * 80)
        print(f"INTERACTIONS ({len(interactions)} records)")
        print("=" * 80)

        for idx, interaction in enumerate(interactions, 1):
            print(f"\n[{idx}] {interaction['interaction_type'].upper()}")
            print(f"Time: {interaction['timestamp']}")
            print(f"From: {interaction['from_agent']} → To: {interaction['to_agent']}")
            print(f"ID: {interaction['interaction_id']}")

            if interaction['interaction_type'] == 'prompt':
                print("-" * 80)
                print("Prompt:")
                print(interaction['content'][:500])  # 처음 500자만
                if len(interaction['content']) > 500:
                    print("... (truncated)")

            elif interaction['interaction_type'] == 'response':
                print("-" * 80)
                print("Response:")
                print(interaction['content'][:500])  # 처음 500자만
                if len(interaction['content']) > 500:
                    print("... (truncated)")

                if interaction.get('duration_ms'):
                    print(f"\nDuration: {interaction['duration_ms']:.2f}ms")
                if interaction.get('token_count'):
                    print(f"Tokens: {interaction['token_count']}")
                if interaction.get('model_used'):
                    print(f"Model: {interaction['model_used']}")

            elif interaction['interaction_type'] == 'error':
                print("-" * 80)
                print(f"ERROR: {interaction.get('error_message', 'Unknown error')}")
                if interaction.get('stack_trace'):
                    print("\nStack Trace:")
                    print(interaction['stack_trace'][:300])  # 처음 300자만

            print("=" * 80)

    def display_agent_summary(self, session: Dict) -> None:
        """Agent별 요약 표시"""
        interactions = session.get("interactions", [])
        agent_stats = {}

        for interaction in interactions:
            for agent in [interaction['from_agent'], interaction['to_agent']]:
                if agent not in agent_stats:
                    agent_stats[agent] = {
                        "prompts_sent": 0,
                        "responses_received": 0,
                        "errors": 0,
                        "total_duration": 0.0,
                        "total_tokens": 0
                    }

                if interaction['from_agent'] == agent and interaction['interaction_type'] == 'prompt':
                    agent_stats[agent]["prompts_sent"] += 1

                if interaction['to_agent'] == agent and interaction['interaction_type'] == 'response':
                    agent_stats[agent]["responses_received"] += 1
                    if interaction.get('duration_ms'):
                        agent_stats[agent]["total_duration"] += interaction['duration_ms']
                    if interaction.get('token_count'):
                        agent_stats[agent]["total_tokens"] += interaction['token_count']

                if interaction['interaction_type'] == 'error':
                    agent_stats[agent]["errors"] += 1

        print("\n" + "=" * 80)
        print("AGENT SUMMARY")
        print("=" * 80)

        for agent, stats in agent_stats.items():
            print(f"\n{agent}:")
            print(f"  Prompts Sent: {stats['prompts_sent']}")
            print(f"  Responses Received: {stats['responses_received']}")
            print(f"  Errors: {stats['errors']}")
            print(f"  Total Duration: {stats['total_duration']:.2f}ms")
            print(f"  Total Tokens: {stats['total_tokens']}")

            if stats['responses_received'] > 0:
                avg_duration = stats['total_duration'] / stats['responses_received']
                avg_tokens = stats['total_tokens'] / stats['responses_received']
                print(f"  Avg Duration: {avg_duration:.2f}ms")
                print(f"  Avg Tokens: {avg_tokens:.0f}")

        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Agent Interaction Log Viewer")
    parser.add_argument("--session", type=str, help="Session ID to view")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--agent", type=str, help="Filter by agent name")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--limit", type=int, help="Limit number of interactions to display")
    parser.add_argument("--agent-summary", action="store_true", help="Show agent summary")

    args = parser.parse_args()

    viewer = LogViewer()

    # 세션 목록 보기
    if args.list:
        sessions = viewer.list_sessions()
        print("\n" + "=" * 80)
        print("AVAILABLE SESSIONS")
        print("=" * 80)
        for session in sessions:
            print(f"\nSession ID: {session['session_id']}")
            print(f"  File: {session['file']}")
            print(f"  Size: {session['size_kb']} KB")
            print(f"  Modified: {session['modified']}")
        print("=" * 80)
        return

    # 세션 로드
    if args.session:
        session = viewer.load_session(args.session)
    else:
        session = viewer.load_latest_session()

    if not session:
        return

    # 통계 표시
    viewer.display_statistics(session)

    # Agent별 요약 표시
    if args.agent_summary:
        viewer.display_agent_summary(session)

    # 상호작용 내역 표시 (stats only가 아닌 경우)
    if not args.stats:
        viewer.display_interactions(
            session,
            agent_filter=args.agent,
            limit=args.limit
        )


if __name__ == "__main__":
    main()
