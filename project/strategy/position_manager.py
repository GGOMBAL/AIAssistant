"""
Position Manager - 포지션 관리 및 손절가 계산

Strategy Agent가 관리하는 포지션 관련 로직:
- 손절가 계산 (기본 손절 + 트레일링 스탑)
- 포지션 사이징
- 리스크 관리

Reference: refer/SystemBackTest/Strategy/Strategy_M.py:288-312
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PositionManager:
    """
    포지션 관리 클래스

    주요 기능:
    1. 손절가 계산 (CalcLossCutPrice)
       - 수익 < 5%: 기본 손절 (평균가 × 0.95)
       - 수익 >= 5%: 트레일링 스탑 적용
    2. 포지션 사이징
    3. 리스크 관리
    """

    def __init__(self, config: dict):
        """
        Initialize PositionManager

        Args:
            config: 시스템 설정
                - std_risk_per_trade: 표준 리스크 (기본: 0.05 = 5%)
                - min_loss_cut_percentage: 최소 손절 비율 (기본: 0.03 = 3%)
        """
        self.config = config

        # 미국 시장 설정
        us_config = config.get('market_specific_configs', {}).get('US', {})

        # 표준 리스크: 5%
        self.std_risk = us_config.get('std_risk_per_trade', 0.05)

        # 최소 손절 비율: 3%
        self.min_loss_cut_percentage = us_config.get('min_loss_cut_percentage', 0.03)

        logger.info(f"[PositionManager] Initialized - Std Risk: {self.std_risk:.1%}, "
                   f"Min Loss Cut: {self.min_loss_cut_percentage:.1%}")

    def calc_losscut_price(
        self,
        again: float,
        current_losscut: float,
        avg_price: float,
        risk: Optional[float] = None
    ) -> float:
        """
        손절가 계산 (단계별 트레일링 스탑 포함)

        Reference: Strategy_M.py:288-312 (Modified to stepped trailing stop)

        Args:
            again: 누적 수익률 (1.0 = 본전, 1.05 = +5%, 0.95 = -5%)
            current_losscut: 현재 손절가
            avg_price: 평균 매수가
            risk: 리스크 비율 (기본값: std_risk = 5%)

        Returns:
            새로운 손절가 (현재 손절가보다 높을 때만 업데이트)

        Stepped Trailing Stop Logic:
            1. Profit units = floor(current_profit / RISK)
            2. Losscut = Entry + (profit_units - 1) * RISK
            3. Minimum losscut: -3% from entry
            4. Creates stepped buffer zones, NOT constant percentage

        Example (Entry=$100, RISK=5%):
            Profit Range    | Units | Losscut | From Entry
            +0% ~ +4.99%    | 0     | $97.00  | -3%
            +5% ~ +9.99%    | 1     | $100.00 | 0%
            +10% ~ +14.99%  | 2     | $105.00 | +5%
            +15% ~ +19.99%  | 3     | $110.00 | +10%

        Detail Examples:
            - again=1.03 (+3%): units=0, Losscut=$97.00 (-3%)
            - again=1.06 (+6%): units=1, Losscut=$100.00 (0%)
            - again=1.08 (+8%): units=1, Losscut=$100.00 (0%)
            - again=1.11 (+11%): units=2, Losscut=$105.00 (+5%)
        """
        if risk is None:
            risk = self.std_risk

        try:
            # 1. 리스크 범위 계산
            if again < (1 + self.std_risk):  # again < 1.05 (수익 < 5%)
                # 기본 손절: 평균가 × (1 - min_loss_cut_percentage) = 평균가 × 0.97
                losscut_new = avg_price * (1 - self.min_loss_cut_percentage)

            else:  # again >= 1.05 (수익 >= 5%)
                # 단계별 트레일링 스탑 적용
                # Stepped Trailing Stop: Losscut = Entry + (profit_units - 1) * RISK
                profit_ratio = again - 1  # 수익률 (예: 0.10 = 10%)
                profit_units = int(profit_ratio / risk)  # 리스크 단위 수 (floor)
                # 단계별 손절가 계산: 진입가 + (단위 - 1) * RISK
                losscut_new = avg_price * (1 + (profit_units - 1) * risk)

            # 2. 최소 손절 비율 보장 (3%)
            min_cut_line = 1 - self.min_loss_cut_percentage
            min_loss_cut_price = avg_price * min_cut_line

            if losscut_new < min_loss_cut_price:
                losscut_new = min_loss_cut_price
                logger.debug(f"[PositionManager] Applied minimum loss cut: ${min_loss_cut_price:.2f} "
                           f"(min_loss_cut_percentage: {self.min_loss_cut_percentage:.1%})")

            # 3. 손절가는 올라가기만 함 (하락하지 않음)
            if losscut_new > current_losscut:
                losscut_pct = ((losscut_new / avg_price) - 1) * 100
                logger.info(f"[PositionManager] Losscut updated: ${current_losscut:.2f} → ${losscut_new:.2f} "
                          f"(Again: {again:.2f}, Losscut: {losscut_pct:+.1f}% from entry)")
                return losscut_new
            else:
                # 현재 손절가 유지
                return current_losscut

        except Exception as e:
            logger.error(f"[ERROR] calc_losscut_price failed: {e}")
            # 에러 시 현재 손절가 유지
            return current_losscut

    def calculate_position_size(
        self,
        balance: float,
        current_price: float,
        max_positions: int,
        current_positions: int,
        max_single_stock_ratio: float = 0.4
    ) -> Dict[str, Any]:
        """
        포지션 사이징 계산

        Args:
            balance: 현재 잔고
            current_price: 현재 주가
            max_positions: 최대 보유 종목 수
            current_positions: 현재 보유 종목 수
            max_single_stock_ratio: 단일 종목 최대 비율 (기본: 40%)

        Returns:
            {
                'position_value': 포지션 금액,
                'quantity': 매수 수량,
                'percentage': 포트폴리오 대비 비율
            }
        """
        try:
            # 1. 남은 포지션 슬롯 계산
            available_slots = max_positions - current_positions

            if available_slots <= 0:
                return {
                    'position_value': 0,
                    'quantity': 0,
                    'percentage': 0
                }

            # 2. 균등 분할 비율 계산
            equal_weight = 1.0 / max_positions

            # 3. 최대 비율 제한 적용
            position_ratio = min(equal_weight, max_single_stock_ratio)

            # 4. 포지션 금액 계산
            position_value = balance * position_ratio

            # 5. 매수 수량 계산 (정수)
            quantity = int(position_value / current_price)

            # 6. 실제 투자 금액 (수량 × 가격)
            actual_value = quantity * current_price
            actual_percentage = actual_value / balance if balance > 0 else 0

            logger.info(f"[PositionManager] Position sizing: "
                       f"${actual_value:.2f} ({actual_percentage:.1%}), "
                       f"{quantity} shares @ ${current_price:.2f}")

            return {
                'position_value': actual_value,
                'quantity': quantity,
                'percentage': actual_percentage
            }

        except Exception as e:
            logger.error(f"[ERROR] calculate_position_size failed: {e}")
            return {
                'position_value': 0,
                'quantity': 0,
                'percentage': 0
            }

    def update_position_status(
        self,
        position: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        포지션 상태 업데이트 (AGain 계산 및 손절가 갱신)

        Args:
            position: 현재 포지션 정보
                {
                    'symbol': 종목 코드,
                    'quantity': 보유 수량,
                    'avg_price': 평균 매수가,
                    'current_price': 이전 현재가,
                    'losscut_price': 현재 손절가,
                    'again': 누적 수익률,
                    'risk': 리스크 비율
                }
            current_price: 현재 주가

        Returns:
            업데이트된 포지션 정보
        """
        try:
            symbol = position['symbol']
            avg_price = position['avg_price']
            prev_price = position.get('current_price', avg_price)
            prev_again = position.get('again', 1.0)
            current_losscut = position['losscut_price']
            risk = position.get('risk', self.std_risk)

            # 1. 일일 수익률 계산
            daily_gain = (current_price - prev_price) / prev_price if prev_price > 0 else 0

            # 2. AGain 업데이트 (누적 수익률)
            new_again = prev_again * (1 + daily_gain)

            # 3. 손절가 업데이트 (트레일링 스탑 적용)
            new_losscut = self.calc_losscut_price(
                again=new_again,
                current_losscut=current_losscut,
                avg_price=avg_price,
                risk=risk
            )

            # 4. 손익 계산
            market_value = current_price * position['quantity']
            original_value = avg_price * position['quantity']
            profit_loss = market_value - original_value
            profit_rate = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0

            # 5. 포지션 정보 업데이트
            updated_position = position.copy()
            updated_position.update({
                'current_price': current_price,
                'again': new_again,
                'losscut_price': new_losscut,
                'market_value': market_value,
                'profit_loss': profit_loss,
                'profit_rate': profit_rate
            })

            logger.debug(f"[PositionManager] {symbol} updated - "
                        f"Price: ${current_price:.2f}, "
                        f"Again: {new_again:.3f}, "
                        f"Losscut: ${new_losscut:.2f}, "
                        f"P&L: ${profit_loss:.2f} ({profit_rate:+.2f}%)")

            return updated_position

        except Exception as e:
            logger.error(f"[ERROR] update_position_status failed: {e}")
            return position
