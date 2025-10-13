"""
Output Validator for Multi-Agent System
Sub-Agent의 출력을 검증하고 개선이 필요한지 판단합니다.

Version: 1.0
Created: 2025-10-10
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """검증 상태"""
    VALID = "valid"  # 검증 통과
    INVALID = "invalid"  # 검증 실패
    INCOMPLETE = "incomplete"  # 불완전한 출력
    ERROR = "error"  # 에러 포함


@dataclass
class ValidationResult:
    """검증 결과"""
    status: ValidationStatus
    confidence: float  # 0.0 ~ 1.0
    issues: List[str]  # 발견된 문제들
    suggestions: List[str]  # 개선 제안
    needs_refinement: bool  # 재작업 필요 여부
    agent_name: str


class OutputValidator:
    """
    Agent 출력 검증기

    각 Agent의 출력을 검증하고, 개선이 필요한 경우 피드백을 생성합니다.
    """

    def __init__(self, validation_criteria: Dict[str, Any] = None):
        """
        Args:
            validation_criteria: 검증 기준 (myStockInfo.yaml에서 로드)
        """
        self.criteria = validation_criteria or {
            'min_confidence': 0.7,
            'require_complete_data': True,
            'check_error_presence': True
        }

        logger.info("[OutputValidator] 초기화 완료")
        logger.info(f"  검증 기준: {self.criteria}")

    def validate_agent_output(
        self,
        agent_name: str,
        agent_output: Dict[str, Any],
        task_type: str = None
    ) -> ValidationResult:
        """
        Agent 출력 검증

        Args:
            agent_name: Agent 이름
            agent_output: Agent의 출력
            task_type: 작업 타입 (선택)

        Returns:
            ValidationResult
        """
        logger.info(f"[Validation] {agent_name} 출력 검증 시작")

        issues = []
        suggestions = []
        confidence = 1.0

        # 1. 기본 구조 검증
        if not isinstance(agent_output, dict):
            issues.append("출력이 딕셔너리 형식이 아닙니다")
            confidence *= 0.1
        else:
            # 2. 상태 확인
            status = agent_output.get('status', 'unknown')
            if status == 'error':
                issues.append("Agent가 에러를 반환했습니다")
                confidence *= 0.3

                # 에러 메시지 추출
                error_msg = agent_output.get('error', 'Unknown error')
                issues.append(f"에러: {error_msg}")

                # 개선 제안
                if 'timeout' in error_msg.lower():
                    suggestions.append("타임아웃 발생 - 작업을 더 작은 단위로 분할하세요")
                elif 'not found' in error_msg.lower():
                    suggestions.append("리소스를 찾을 수 없음 - 입력 파라미터를 확인하세요")
                else:
                    suggestions.append("에러 원인을 분석하고 재시도하세요")

            elif status == 'timeout':
                issues.append("작업 시간 초과")
                confidence *= 0.4
                suggestions.append("타임아웃 시간 증가 또는 작업 분할")

            # 3. 응답 내용 검증
            response = agent_output.get('response', '')
            if not response or len(response.strip()) < 10:
                issues.append("응답 내용이 너무 짧거나 비어있습니다")
                confidence *= 0.5
                suggestions.append("더 상세한 정보를 요청하세요")

            # 4. Agent별 특화 검증
            if agent_name == 'database_agent':
                issues_db, sugg_db, conf_db = self._validate_database_output(agent_output)
                issues.extend(issues_db)
                suggestions.extend(sugg_db)
                confidence *= conf_db

            elif agent_name == 'strategy_agent':
                issues_st, sugg_st, conf_st = self._validate_strategy_output(agent_output)
                issues.extend(issues_st)
                suggestions.extend(sugg_st)
                confidence *= conf_st

            elif agent_name == 'service_agent':
                issues_sv, sugg_sv, conf_sv = self._validate_service_output(agent_output)
                issues.extend(issues_sv)
                suggestions.extend(sugg_sv)
                confidence *= conf_sv

            elif agent_name == 'run_agent':
                issues_run, sugg_run, conf_run = self._validate_run_output(agent_output)
                issues.extend(issues_run)
                suggestions.extend(sugg_run)
                confidence *= conf_run

        # 5. 최종 검증 상태 결정
        validation_status = self._determine_status(
            issues, confidence, agent_output.get('status')
        )

        # 6. 재작업 필요 여부 판단
        needs_refinement = (
            confidence < self.criteria.get('min_confidence', 0.7) or
            validation_status in [ValidationStatus.INVALID, ValidationStatus.INCOMPLETE]
        )

        result = ValidationResult(
            status=validation_status,
            confidence=confidence,
            issues=issues,
            suggestions=suggestions,
            needs_refinement=needs_refinement,
            agent_name=agent_name
        )

        logger.info(f"[Validation] {agent_name} 검증 완료: {validation_status.value} (신뢰도: {confidence:.2f})")
        if needs_refinement:
            logger.warning(f"  재작업 필요: {len(issues)}개 이슈 발견")

        return result

    def _validate_database_output(self, output: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """Database Agent 출력 검증"""
        issues = []
        suggestions = []
        confidence = 1.0

        # 데이터 필드 확인
        if 'data' not in output:
            issues.append("데이터 필드가 없습니다")
            confidence *= 0.6
            suggestions.append("query 결과를 'data' 필드에 포함하세요")

        # affected_documents 확인
        affected = output.get('affected_documents', 0)
        if affected == 0:
            issues.append("처리된 문서가 없습니다")
            confidence *= 0.7
            suggestions.append("쿼리 조건을 확인하거나 데이터베이스 상태를 점검하세요")

        # operation 타입 확인
        operation = output.get('operation', '')
        if not operation:
            issues.append("operation 타입이 명시되지 않았습니다")
            confidence *= 0.9

        return issues, suggestions, confidence

    def _validate_strategy_output(self, output: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """Strategy Agent 출력 검증"""
        issues = []
        suggestions = []
        confidence = 1.0

        # 시그널 데이터 확인
        signals = output.get('signals', [])
        if not signals:
            issues.append("생성된 시그널이 없습니다")
            confidence *= 0.5
            suggestions.append("시그널 생성 조건을 완화하거나 데이터를 확인하세요")
        else:
            # 시그널 품질 확인
            for i, signal in enumerate(signals[:5]):  # 최대 5개만 검증
                if 'symbol' not in signal:
                    issues.append(f"시그널 {i+1}에 symbol이 없습니다")
                    confidence *= 0.9

                if 'signal' not in signal:
                    issues.append(f"시그널 {i+1}에 매매 방향이 없습니다")
                    confidence *= 0.8

                if 'confidence' in signal:
                    sig_conf = signal['confidence']
                    if sig_conf < 0.5:
                        issues.append(f"시그널 {i+1}의 신뢰도가 낮습니다 ({sig_conf:.2f})")
                        confidence *= 0.95

        # metadata 확인
        metadata = output.get('metadata', {})
        if not metadata:
            issues.append("메타데이터가 없습니다")
            confidence *= 0.95

        return issues, suggestions, confidence

    def _validate_service_output(self, output: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """Service Agent 출력 검증"""
        issues = []
        suggestions = []
        confidence = 1.0

        # 백테스트 결과 확인
        backtest_result = output.get('backtest_result', {})
        if not backtest_result:
            issues.append("백테스트 결과가 없습니다")
            confidence *= 0.5
            suggestions.append("백테스트 실행을 확인하세요")
        else:
            # 필수 지표 확인
            required_metrics = ['total_return', 'sharpe_ratio', 'max_drawdown', 'total_trades']
            missing = [m for m in required_metrics if m not in backtest_result]
            if missing:
                issues.append(f"필수 지표 누락: {', '.join(missing)}")
                confidence *= 0.7
                suggestions.append("백테스트 엔진이 모든 지표를 계산하도록 확인하세요")

            # 거래 횟수 확인
            total_trades = backtest_result.get('total_trades', 0)
            if total_trades == 0:
                issues.append("거래가 발생하지 않았습니다")
                confidence *= 0.6
                suggestions.append("시그널 생성 또는 진입 조건을 확인하세요")

        return issues, suggestions, confidence

    def _validate_run_output(self, output: Dict[str, Any]) -> Tuple[List[str], List[str], float]:
        """RUN Agent 출력 검증"""
        issues = []
        suggestions = []
        confidence = 1.0

        # 반환 코드 확인
        return_code = output.get('return_code', -1)
        if return_code != 0:
            issues.append(f"비정상 종료 (코드: {return_code})")
            confidence *= 0.5
            suggestions.append("스크립트 에러를 확인하고 수정하세요")

        # stderr 확인
        stderr = output.get('stderr', '')
        if stderr and len(stderr) > 10:
            issues.append("표준 에러 출력이 있습니다")
            confidence *= 0.8

        # 실행 시간 확인
        duration = output.get('duration', 0)
        if duration > 300:  # 5분 이상
            issues.append("실행 시간이 길었습니다")
            confidence *= 0.95
            suggestions.append("스크립트 최적화를 고려하세요")

        return issues, suggestions, confidence

    def _determine_status(
        self,
        issues: List[str],
        confidence: float,
        agent_status: str
    ) -> ValidationStatus:
        """최종 검증 상태 결정"""

        if agent_status == 'error':
            return ValidationStatus.ERROR

        if not issues:
            return ValidationStatus.VALID

        if confidence < 0.5:
            return ValidationStatus.INVALID

        if confidence < 0.7:
            return ValidationStatus.INCOMPLETE

        return ValidationStatus.VALID

    def generate_refinement_prompt(
        self,
        validation_result: ValidationResult,
        original_prompt: str,
        previous_output: Dict[str, Any]
    ) -> str:
        """
        개선을 위한 새로운 프롬프트 생성

        Args:
            validation_result: 검증 결과
            original_prompt: 원본 프롬프트
            previous_output: 이전 출력

        Returns:
            개선된 프롬프트
        """
        refinement_prompt = f"""{original_prompt}

**[이전 시도 피드백]**

이전 출력에서 다음 문제가 발견되었습니다:

"""
        # 이슈 추가
        for i, issue in enumerate(validation_result.issues, 1):
            refinement_prompt += f"{i}. {issue}\n"

        # 개선 제안 추가
        if validation_result.suggestions:
            refinement_prompt += "\n**개선 제안**:\n"
            for i, suggestion in enumerate(validation_result.suggestions, 1):
                refinement_prompt += f"{i}. {suggestion}\n"

        # 이전 출력 요약 추가
        refinement_prompt += f"""
**이전 출력 요약**:
- 상태: {previous_output.get('status', 'unknown')}
- 신뢰도: {validation_result.confidence:.2f}

위 피드백을 반영하여 개선된 결과를 생성해주세요.
"""

        return refinement_prompt


# 사용 예시
if __name__ == "__main__":
    # 테스트
    validator = OutputValidator({
        'min_confidence': 0.7,
        'require_complete_data': True,
        'check_error_presence': True
    })

    # Database Agent 출력 예시
    db_output = {
        'status': 'success',
        'operation': 'read',
        'affected_documents': 100,
        'data': {'symbols': ['AAPL', 'MSFT']},
        'response': 'Successfully loaded 100 documents from NasDataBase_D'
    }

    result = validator.validate_agent_output('database_agent', db_output)
    print(f"Status: {result.status.value}")
    print(f"Confidence: {result.confidence}")
    print(f"Needs Refinement: {result.needs_refinement}")
    print(f"Issues: {result.issues}")
    print(f"Suggestions: {result.suggestions}")
