"""
Agent Interaction Logger
Orchestrator와 Sub-Agent 간의 모든 프롬프트와 응답을 로그로 기록

Author: Orchestrator
Date: 2025-10-09
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass, asdict
from enum import Enum

log = logging.getLogger(__name__)


class InteractionType(Enum):
    """상호작용 타입"""
    PROMPT = "prompt"           # Orchestrator → Sub-Agent
    RESPONSE = "response"       # Sub-Agent → Orchestrator
    ERROR = "error"             # 에러 발생
    TIMEOUT = "timeout"         # 타임아웃


class AgentRole(Enum):
    """Agent 역할"""
    ORCHESTRATOR = "orchestrator"
    HELPER = "helper_agent"
    DATABASE = "database_agent"
    STRATEGY = "strategy_agent"
    SERVICE = "service_agent"


@dataclass
class InteractionRecord:
    """상호작용 기록"""
    session_id: str                 # 세션 ID
    interaction_id: str             # 상호작용 ID (UUID)
    timestamp: str                  # 타임스탬프
    interaction_type: str           # 상호작용 타입 (prompt/response/error)

    # Agent 정보
    from_agent: str                 # 발신 Agent
    to_agent: str                   # 수신 Agent

    # 내용
    content: str                    # 프롬프트 또는 응답 내용
    metadata: Dict[str, Any]        # 메타데이터 (모델, 토큰 수 등)

    # 성능 지표
    duration_ms: Optional[float] = None     # 응답 시간 (밀리초)
    token_count: Optional[int] = None       # 토큰 수
    model_used: Optional[str] = None        # 사용된 모델

    # 오류 정보
    error_message: Optional[str] = None     # 에러 메시지
    stack_trace: Optional[str] = None       # 스택 트레이스


class AgentInteractionLogger:
    """
    Agent 상호작용 로거

    모든 Orchestrator ↔ Sub-Agent 간의 통신을 로그로 기록
    """

    def __init__(self, log_dir: str = "storage/agent_interactions"):
        """
        로거 초기화

        Args:
            log_dir: 로그 저장 디렉토리
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 세션 ID 생성
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 현재 세션 로그 파일들
        self.json_log_file = self.log_dir / f"session_{self.session_id}.json"
        self.yaml_log_file = self.log_dir / f"session_{self.session_id}.yaml"
        self.text_log_file = self.log_dir / f"session_{self.session_id}.log"

        # 상호작용 기록 저장소
        self.interactions: List[InteractionRecord] = []

        # 통계 정보
        self.stats = {
            "total_interactions": 0,
            "prompts_sent": 0,
            "responses_received": 0,
            "errors_occurred": 0,
            "total_tokens": 0,
            "total_duration_ms": 0.0,
            "agents_used": set()
        }

        log.info(f"[AgentInteractionLogger] Session started: {self.session_id}")
        log.info(f"[AgentInteractionLogger] Logs will be saved to: {self.log_dir}")

    def log_prompt(
        self,
        from_agent: str,
        to_agent: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Orchestrator가 Sub-Agent에게 보내는 프롬프트 기록

        Args:
            from_agent: 발신 Agent (보통 orchestrator)
            to_agent: 수신 Agent (helper/database/strategy/service)
            prompt: 프롬프트 내용
            metadata: 추가 메타데이터

        Returns:
            interaction_id: 생성된 상호작용 ID
        """
        import uuid

        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        record = InteractionRecord(
            session_id=self.session_id,
            interaction_id=interaction_id,
            timestamp=timestamp,
            interaction_type=InteractionType.PROMPT.value,
            from_agent=from_agent,
            to_agent=to_agent,
            content=prompt,
            metadata=metadata or {},
            token_count=len(prompt.split())  # 간단한 토큰 추정
        )

        self.interactions.append(record)
        self.stats["total_interactions"] += 1
        self.stats["prompts_sent"] += 1
        self.stats["agents_used"].add(to_agent)

        # 즉시 파일에 기록
        self._append_to_logs(record)

        log.info(f"[Prompt] {from_agent} -> {to_agent} | ID: {interaction_id[:8]}")

        return interaction_id

    def log_response(
        self,
        interaction_id: str,
        from_agent: str,
        to_agent: str,
        response: str,
        duration_ms: Optional[float] = None,
        token_count: Optional[int] = None,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Sub-Agent가 Orchestrator에게 보내는 응답 기록

        Args:
            interaction_id: 원본 프롬프트의 ID
            from_agent: 발신 Agent (helper/database/strategy/service)
            to_agent: 수신 Agent (보통 orchestrator)
            response: 응답 내용
            duration_ms: 응답 시간 (밀리초)
            token_count: 토큰 수
            model_used: 사용된 모델
            metadata: 추가 메타데이터
        """
        timestamp = datetime.now().isoformat()

        record = InteractionRecord(
            session_id=self.session_id,
            interaction_id=interaction_id,
            timestamp=timestamp,
            interaction_type=InteractionType.RESPONSE.value,
            from_agent=from_agent,
            to_agent=to_agent,
            content=response,
            metadata=metadata or {},
            duration_ms=duration_ms,
            token_count=token_count or len(response.split()),
            model_used=model_used
        )

        self.interactions.append(record)
        self.stats["total_interactions"] += 1
        self.stats["responses_received"] += 1

        if duration_ms:
            self.stats["total_duration_ms"] += duration_ms
        if token_count:
            self.stats["total_tokens"] += token_count

        # 즉시 파일에 기록
        self._append_to_logs(record)

        log.info(f"[Response] {from_agent} -> {to_agent} | "
                f"Duration: {duration_ms:.0f}ms | Tokens: {token_count}" if duration_ms and token_count else "")

    def log_error(
        self,
        interaction_id: str,
        from_agent: str,
        to_agent: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        에러 기록

        Args:
            interaction_id: 관련 상호작용 ID
            from_agent: 에러 발생 Agent
            to_agent: 에러 보고 대상 Agent
            error_message: 에러 메시지
            stack_trace: 스택 트레이스
            metadata: 추가 메타데이터
        """
        timestamp = datetime.now().isoformat()

        record = InteractionRecord(
            session_id=self.session_id,
            interaction_id=interaction_id,
            timestamp=timestamp,
            interaction_type=InteractionType.ERROR.value,
            from_agent=from_agent,
            to_agent=to_agent,
            content=error_message,
            metadata=metadata or {},
            error_message=error_message,
            stack_trace=stack_trace
        )

        self.interactions.append(record)
        self.stats["total_interactions"] += 1
        self.stats["errors_occurred"] += 1

        # 즉시 파일에 기록
        self._append_to_logs(record)

        log.error(f"[Error] {from_agent} -> {to_agent} | {error_message}")

    def _append_to_logs(self, record: InteractionRecord) -> None:
        """로그 파일에 기록 추가"""

        # JSON 형식으로 저장
        with open(self.json_log_file, 'a', encoding='utf-8') as f:
            json.dump(asdict(record), f, ensure_ascii=False, indent=2)
            f.write('\n')

        # 텍스트 형식으로 저장 (읽기 쉬움)
        try:
            with open(self.text_log_file, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"[{record.timestamp}] {record.interaction_type.upper()}\n")
                f.write(f"From: {record.from_agent} -> To: {record.to_agent}\n")
                f.write(f"ID: {record.interaction_id}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Content:\n{record.content}\n")

                if record.duration_ms:
                    f.write(f"\nDuration: {record.duration_ms:.2f}ms\n")
                if record.token_count:
                    f.write(f"Tokens: {record.token_count}\n")
                if record.model_used:
                    f.write(f"Model: {record.model_used}\n")
                if record.error_message:
                    f.write(f"\nError: {record.error_message}\n")
                if record.stack_trace:
                    f.write(f"Stack Trace:\n{record.stack_trace}\n")

                f.write("=" * 80 + "\n\n")
        except Exception as e:
            log.error(f"텍스트 로그 작성 오류: {e}")

    def save_session_summary(self) -> None:
        """세션 요약 저장"""

        summary = {
            "session_id": self.session_id,
            "start_time": self.interactions[0].timestamp if self.interactions else None,
            "end_time": datetime.now().isoformat(),
            "statistics": {
                "total_interactions": self.stats["total_interactions"],
                "prompts_sent": self.stats["prompts_sent"],
                "responses_received": self.stats["responses_received"],
                "errors_occurred": self.stats["errors_occurred"],
                "total_tokens": self.stats["total_tokens"],
                "total_duration_ms": self.stats["total_duration_ms"],
                "average_duration_ms": (
                    self.stats["total_duration_ms"] / self.stats["responses_received"]
                    if self.stats["responses_received"] > 0 else 0
                ),
                "agents_used": list(self.stats["agents_used"])
            },
            "interactions": [asdict(record) for record in self.interactions]
        }

        # YAML 형식으로 전체 세션 저장
        with open(self.yaml_log_file, 'w', encoding='utf-8') as f:
            yaml.dump(summary, f, allow_unicode=True, default_flow_style=False)

        log.info(f"[AgentInteractionLogger] Session summary saved: {self.yaml_log_file}")

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            "session_id": self.session_id,
            "total_interactions": self.stats["total_interactions"],
            "prompts_sent": self.stats["prompts_sent"],
            "responses_received": self.stats["responses_received"],
            "errors_occurred": self.stats["errors_occurred"],
            "total_tokens": self.stats["total_tokens"],
            "total_duration_ms": self.stats["total_duration_ms"],
            "average_duration_ms": (
                self.stats["total_duration_ms"] / self.stats["responses_received"]
                if self.stats["responses_received"] > 0 else 0
            ),
            "agents_used": list(self.stats["agents_used"])
        }

    def get_agent_interactions(self, agent_name: str) -> List[InteractionRecord]:
        """특정 Agent의 상호작용 기록 조회"""
        return [
            record for record in self.interactions
            if record.from_agent == agent_name or record.to_agent == agent_name
        ]

    def get_interaction_chain(self, interaction_id: str) -> List[InteractionRecord]:
        """특정 상호작용 ID의 전체 체인 조회 (프롬프트 → 응답 → 에러)"""
        return [
            record for record in self.interactions
            if record.interaction_id == interaction_id
        ]


# 전역 로거 인스턴스 (싱글톤 패턴)
_global_logger: Optional[AgentInteractionLogger] = None


def get_interaction_logger() -> AgentInteractionLogger:
    """전역 상호작용 로거 가져오기"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AgentInteractionLogger()
    return _global_logger


def initialize_interaction_logger(log_dir: str = "storage/agent_interactions") -> AgentInteractionLogger:
    """상호작용 로거 초기화"""
    global _global_logger
    _global_logger = AgentInteractionLogger(log_dir)
    return _global_logger


# 사용 예시
if __name__ == "__main__":
    import time

    # 로거 초기화
    logger = AgentInteractionLogger()

    # 예시 1: 프롬프트 기록
    interaction_id = logger.log_prompt(
        from_agent="orchestrator",
        to_agent="database_agent",
        prompt="Load historical data for NASDAQ symbols from 2024-01-01 to 2024-06-30",
        metadata={"task_type": "data_loading", "market": "NASDAQ"}
    )

    # 시뮬레이션: Agent 처리 시간
    time.sleep(0.5)

    # 예시 2: 응답 기록
    logger.log_response(
        interaction_id=interaction_id,
        from_agent="database_agent",
        to_agent="orchestrator",
        response="Successfully loaded 15,113 symbols with 180 days of data",
        duration_ms=500,
        token_count=150,
        model_used="gemini-2.5-flash",
        metadata={"symbols_loaded": 15113, "days": 180}
    )

    # 예시 3: 다른 Agent와의 상호작용
    interaction_id2 = logger.log_prompt(
        from_agent="orchestrator",
        to_agent="strategy_agent",
        prompt="Generate trading signals for loaded symbols",
        metadata={"task_type": "signal_generation"}
    )

    time.sleep(1.0)

    logger.log_response(
        interaction_id=interaction_id2,
        from_agent="strategy_agent",
        to_agent="orchestrator",
        response="Generated 194 trading signals (58 BUY, 136 HOLD)",
        duration_ms=1000,
        token_count=200,
        model_used="gemini-2.5-flash"
    )

    # 예시 4: 에러 기록
    interaction_id3 = logger.log_prompt(
        from_agent="orchestrator",
        to_agent="service_agent",
        prompt="Run backtest with invalid parameters"
    )

    logger.log_error(
        interaction_id=interaction_id3,
        from_agent="service_agent",
        to_agent="orchestrator",
        error_message="Invalid backtest parameters: initial_cash must be positive",
        stack_trace="Traceback (most recent call last):\n  File ...",
        metadata={"error_type": "ValidationError"}
    )

    # 통계 출력
    print("\n" + "=" * 80)
    print("Session Statistics")
    print("=" * 80)
    stats = logger.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # 세션 요약 저장
    logger.save_session_summary()

    print(f"\n[OK] Logs saved to: {logger.log_dir}")
    print(f"  - JSON: {logger.json_log_file}")
    print(f"  - YAML: {logger.yaml_log_file}")
    print(f"  - TEXT: {logger.text_log_file}")
