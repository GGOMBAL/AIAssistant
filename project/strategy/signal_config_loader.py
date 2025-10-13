"""
Signal Configuration Loader
시그널 설정 파일 로더 - YAML 설정을 읽어서 SignalGenerationService에 전달
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConditionConfig:
    """단일 조건 설정"""
    indicator: str
    operator: str
    threshold: Optional[float] = None
    reference: Optional[str] = None
    multiplier: Optional[float] = None
    description: str = ""


@dataclass
class SignalTypeConfig:
    """신호 타입별 설정"""
    enabled: bool
    weight: float
    conditions: List[ConditionConfig] = field(default_factory=list)


@dataclass
class SignalConfig:
    """전체 시그널 설정"""
    strategy_name: str
    version: str
    enabled: bool

    # 신호 타입별 설정
    rs_signal: SignalTypeConfig
    weekly_signal: SignalTypeConfig
    fundamental_signal: SignalTypeConfig
    earnings_signal: SignalTypeConfig
    daily_rs_signal: SignalTypeConfig

    # 신호 결합 설정
    min_signals_required: int
    calculation_method: str
    buy_threshold: float
    confidence_levels: Dict[str, float]

    # 가격 타겟 설정
    target_price_multiplier: float
    losscut_price_multiplier: float
    use_atr_targets: bool
    atr_multiplier_target: float
    atr_multiplier_losscut: float

    # 일봉 브레이크아웃 설정
    breakout_types: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # 리스크 관리
    risk_management: Dict[str, Any] = field(default_factory=dict)

    # 신호 우선순위
    signal_priority: Dict[str, int] = field(default_factory=dict)


class SignalConfigLoader:
    """
    시그널 설정 파일 로더
    YAML 파일에서 시그널 생성 조건을 읽어옴
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize SignalConfigLoader

        Args:
            config_path: Path to signal_config.yaml file
                        If None, uses default path: config/signal_config.yaml
        """
        if config_path is None:
            # 프로젝트 루트에서 config/signal_config.yaml 찾기
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "signal_config.yaml"

        self.config_path = Path(config_path)

        if not self.config_path.exists():
            logger.warning(f"Signal config file not found: {self.config_path}")
            logger.warning("Using default configuration")
            self.config_data = self._get_default_config()
        else:
            logger.info(f"Loading signal config from: {self.config_path}")
            self.config_data = self._load_yaml()

        # 설정 파싱
        self.signal_config = self._parse_config()

    def _load_yaml(self) -> Dict[str, Any]:
        """YAML 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'strategy_name': 'Default Strategy',
            'version': '1.0',
            'enabled': True,
            'rs_signal': {
                'enabled': True,
                'weight': 0.2,
                'conditions': [
                    {'indicator': 'RS_4W', 'operator': '>=', 'threshold': 90, 'description': 'RS >= 90'}
                ]
            },
            'weekly_signal': {
                'enabled': True,
                'weight': 0.2,
                'conditions': []
            },
            'fundamental_signal': {
                'enabled': True,
                'weight': 0.2,
                'conditions': [
                    {'indicator': 'EPS_YOY', 'operator': '>', 'threshold': 0, 'description': 'EPS growth'},
                    {'indicator': 'REV_YOY', 'operator': '>', 'threshold': 0, 'description': 'Revenue growth'}
                ]
            },
            'earnings_signal': {
                'enabled': True,
                'weight': 0.2,
                'conditions': []
            },
            'daily_rs_signal': {
                'enabled': True,
                'weight': 0.2,
                'breakout_types': {}
            },
            'signal_combination': {
                'min_signals_required': 2,
                'calculation_method': 'weighted_average',
                'buy_threshold': 0.6,
                'confidence_levels': {'low': 0.5, 'medium': 0.7, 'high': 0.9}
            },
            'price_targets': {
                'target_price_multiplier': 1.20,
                'losscut_price_multiplier': 0.95,
                'use_atr_targets': False,
                'atr_multiplier_target': 3.0,
                'atr_multiplier_losscut': 2.0
            }
        }

    def _parse_config(self) -> SignalConfig:
        """설정 파싱"""
        try:
            # RS 신호 설정
            rs_config = self._parse_signal_type('rs_signal')

            # Weekly 신호 설정
            weekly_config = self._parse_signal_type('weekly_signal')

            # Fundamental 신호 설정
            fundamental_config = self._parse_signal_type('fundamental_signal')

            # Earnings 신호 설정
            earnings_config = self._parse_signal_type('earnings_signal')

            # Daily RS 신호 설정
            daily_rs_config = self._parse_signal_type('daily_rs_signal')

            # 신호 결합 설정
            combination = self.config_data.get('signal_combination', {})

            # 가격 타겟 설정
            price_targets = self.config_data.get('price_targets', {})

            # 브레이크아웃 타입 설정
            breakout_types = {}
            if 'daily_rs_signal' in self.config_data:
                breakout_types = self.config_data['daily_rs_signal'].get('breakout_types', {})

            # 리스크 관리 설정
            risk_management = self.config_data.get('risk_management', {})

            # 신호 우선순위
            signal_priority = self.config_data.get('signal_priority', {})

            return SignalConfig(
                strategy_name=self.config_data.get('strategy_name', 'Default Strategy'),
                version=self.config_data.get('version', '1.0'),
                enabled=self.config_data.get('enabled', True),
                rs_signal=rs_config,
                weekly_signal=weekly_config,
                fundamental_signal=fundamental_config,
                earnings_signal=earnings_config,
                daily_rs_signal=daily_rs_config,
                min_signals_required=combination.get('min_signals_required', 2),
                calculation_method=combination.get('calculation_method', 'weighted_average'),
                buy_threshold=combination.get('buy_threshold', 0.6),
                confidence_levels=combination.get('confidence_levels', {'low': 0.5, 'medium': 0.7, 'high': 0.9}),
                target_price_multiplier=price_targets.get('target_price_multiplier', 1.20),
                losscut_price_multiplier=price_targets.get('losscut_price_multiplier', 0.95),
                use_atr_targets=price_targets.get('use_atr_targets', False),
                atr_multiplier_target=price_targets.get('atr_multiplier_target', 3.0),
                atr_multiplier_losscut=price_targets.get('atr_multiplier_losscut', 2.0),
                breakout_types=breakout_types,
                risk_management=risk_management,
                signal_priority=signal_priority
            )

        except Exception as e:
            logger.error(f"Error parsing config: {e}")
            raise

    def _parse_signal_type(self, signal_type: str) -> SignalTypeConfig:
        """신호 타입별 설정 파싱"""
        signal_data = self.config_data.get(signal_type, {})

        enabled = signal_data.get('enabled', True)
        weight = signal_data.get('weight', 0.2)

        conditions = []
        for cond in signal_data.get('conditions', []):
            # type 필드가 있는 경우 (earnings 신호 등) 스킵
            if 'type' in cond:
                continue

            condition = ConditionConfig(
                indicator=cond.get('indicator', ''),
                operator=cond.get('operator', '>='),
                threshold=cond.get('threshold'),
                reference=cond.get('reference'),
                multiplier=cond.get('multiplier'),
                description=cond.get('description', '')
            )
            conditions.append(condition)

        return SignalTypeConfig(
            enabled=enabled,
            weight=weight,
            conditions=conditions
        )

    def get_config(self) -> SignalConfig:
        """설정 반환"""
        return self.signal_config

    def get_rs_threshold(self) -> float:
        """RS 임계값 반환"""
        for condition in self.signal_config.rs_signal.conditions:
            if condition.indicator == 'RS_4W':
                return condition.threshold or 90
        return 90

    def get_breakout_rs_threshold(self, breakout_type: str) -> float:
        """브레이크아웃 타입별 RS 임계값 반환"""
        breakout_config = self.signal_config.breakout_types.get(breakout_type, {})
        return breakout_config.get('rs_threshold', 90)

    def get_fundamental_conditions(self) -> List[ConditionConfig]:
        """펀더멘털 조건 리스트 반환"""
        return self.signal_config.fundamental_signal.conditions

    def is_signal_enabled(self, signal_type: str) -> bool:
        """신호 타입이 활성화되어 있는지 확인"""
        signal_map = {
            'rs': self.signal_config.rs_signal,
            'weekly': self.signal_config.weekly_signal,
            'fundamental': self.signal_config.fundamental_signal,
            'earnings': self.signal_config.earnings_signal,
            'daily_rs': self.signal_config.daily_rs_signal
        }

        signal = signal_map.get(signal_type)
        return signal.enabled if signal else False

    def get_signal_weight(self, signal_type: str) -> float:
        """신호 타입별 가중치 반환"""
        signal_map = {
            'rs': self.signal_config.rs_signal,
            'weekly': self.signal_config.weekly_signal,
            'fundamental': self.signal_config.fundamental_signal,
            'earnings': self.signal_config.earnings_signal,
            'daily_rs': self.signal_config.daily_rs_signal
        }

        signal = signal_map.get(signal_type)
        return signal.weight if signal else 0.0

    def evaluate_condition(self, condition: ConditionConfig, value: float,
                          reference_value: Optional[float] = None) -> bool:
        """
        조건 평가

        Args:
            condition: 평가할 조건
            value: 지표 값
            reference_value: 참조 값 (선택사항)

        Returns:
            조건 만족 여부
        """
        try:
            # reference가 있는 경우 (예: close > 52_week_high * 0.9)
            if condition.reference and reference_value is not None:
                threshold = reference_value * (condition.multiplier or 1.0)
            else:
                threshold = condition.threshold

            if threshold is None:
                return False

            # 연산자에 따라 평가
            if condition.operator == '>':
                return value > threshold
            elif condition.operator == '>=':
                return value >= threshold
            elif condition.operator == '<':
                return value < threshold
            elif condition.operator == '<=':
                return value <= threshold
            elif condition.operator == '==':
                return abs(value - threshold) < 1e-6
            elif condition.operator == '!=':
                return abs(value - threshold) >= 1e-6
            else:
                logger.warning(f"Unknown operator: {condition.operator}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def reload(self):
        """설정 파일 리로드"""
        logger.info("Reloading signal configuration...")
        self.config_data = self._load_yaml()
        self.signal_config = self._parse_config()
        logger.info("Signal configuration reloaded")

    def save_config(self, config_dict: Dict[str, Any]):
        """
        설정 저장

        Args:
            config_dict: 저장할 설정 딕셔너리
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Configuration saved to {self.config_path}")

            # 리로드
            self.reload()

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    def print_summary(self):
        """설정 요약 출력"""
        print("\n" + "="*80)
        print(f"SIGNAL CONFIGURATION SUMMARY")
        print("="*80)
        print(f"Strategy: {self.signal_config.strategy_name} v{self.signal_config.version}")
        print(f"Enabled: {self.signal_config.enabled}")
        print()

        print("Signal Weights:")
        print(f"  RS Signal: {self.signal_config.rs_signal.weight:.2f} (Enabled: {self.signal_config.rs_signal.enabled})")
        print(f"  Weekly Signal: {self.signal_config.weekly_signal.weight:.2f} (Enabled: {self.signal_config.weekly_signal.enabled})")
        print(f"  Fundamental Signal: {self.signal_config.fundamental_signal.weight:.2f} (Enabled: {self.signal_config.fundamental_signal.enabled})")
        print(f"  Earnings Signal: {self.signal_config.earnings_signal.weight:.2f} (Enabled: {self.signal_config.earnings_signal.enabled})")
        print(f"  Daily RS Signal: {self.signal_config.daily_rs_signal.weight:.2f} (Enabled: {self.signal_config.daily_rs_signal.enabled})")
        print()

        print("Signal Combination:")
        print(f"  Min Signals Required: {self.signal_config.min_signals_required}")
        print(f"  Calculation Method: {self.signal_config.calculation_method}")
        print(f"  Buy Threshold: {self.signal_config.buy_threshold:.2f}")
        print()

        print("RS Signal Conditions:")
        for cond in self.signal_config.rs_signal.conditions:
            print(f"  - {cond.indicator} {cond.operator} {cond.threshold}: {cond.description}")
        print()

        print("Fundamental Signal Conditions:")
        for cond in self.signal_config.fundamental_signal.conditions:
            print(f"  - {cond.indicator} {cond.operator} {cond.threshold}: {cond.description}")
        print()

        print("="*80)


# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # 설정 로더 생성
    loader = SignalConfigLoader()

    # 설정 요약 출력
    loader.print_summary()

    # 특정 값 가져오기
    print(f"\nRS Threshold: {loader.get_rs_threshold()}")
    print(f"RS Signal Enabled: {loader.is_signal_enabled('rs')}")
    print(f"RS Signal Weight: {loader.get_signal_weight('rs')}")

    # 조건 평가 예시
    rs_condition = loader.signal_config.rs_signal.conditions[0]
    rs_value = 95
    result = loader.evaluate_condition(rs_condition, rs_value)
    print(f"\nEvaluating: RS_4W ({rs_value}) {rs_condition.operator} {rs_condition.threshold}")
    print(f"Result: {result}")
