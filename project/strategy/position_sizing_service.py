#!/usr/bin/env python3
"""
Position Sizing Service - Strategy Layer
Based on refer/Strategy/Strategy_M.py
Implements position sizing, risk management, and portfolio optimization
Note: Backtest execution functions (buy_stock, sell_stock, etc.) are moved to Service Layer
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import os
import yaml
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketCondition(Enum):
    """Market condition levels"""
    POOR = 1
    MODERATE = 2
    GOOD = 3

@dataclass
class PositionSizeConfig:
    """Position sizing configuration"""
    std_risk: float = 0.05
    max_stock_list: int = 10
    min_loss_cut_percentage: float = 0.03
    max_single_stock_ratio: float = 0.4
    pyramiding_ratio: float = 0.1
    enable_pyramiding: bool = True
    enable_half_sell: bool = True

@dataclass
class CandidateStock:
    """매수 후보 종목 정보"""
    ticker: str
    sorting_metric: float
    target_price: float
    signal_strength: float
    market_code: str = 'US'

class PositionSizingService:
    """
    포지션 사이징 및 리스크 관리 서비스
    Strategy_M.py의 핵심 로직 구현 (백테스팅 실행 함수 제외)
    """

    def __init__(self,
                 std_risk: float = 0.05,
                 market: str = 'US',
                 area: str = 'US',
                 max_stock_list: int = 10,
                 slippage: float = 0.001):

        self.std_risk = std_risk
        self.market = market
        self.area = area
        self.max_stock_list = max_stock_list
        self.slippage = slippage
        self.market_condition = MarketCondition.MODERATE

        # Load configuration from YAML
        self.config = self._load_config()
        self._apply_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file (Strategy_M.py의 _load_min_loss_cut_percentage 로직)"""
        try:
            config_paths = [
                'config/risk_management.yaml',
                '../config/risk_management.yaml',
                'Main/myStockInfo.yaml',
                '../Main/myStockInfo.yaml',
                'myStockInfo.yaml'
            ]

            config_file = None
            for path in config_paths:
                if os.path.exists(path):
                    config_file = path
                    break

            if config_file:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Extract market-specific configuration
                market_config = config.get('market_specific_configs', {}).get(self.area, {})

                return {
                    'min_loss_cut_percentage': market_config.get('min_loss_cut_percentage', 0.03),
                    'max_single_stock_ratio': market_config.get('max_single_stock_ratio', 0.4),
                    'pyramiding_ratio': market_config.get('pyramiding_ratio', 0.1),
                    'enable_pyramiding': market_config.get('operational_flags', {}).get('enable_pyramiding', True),
                    'enable_half_sell': market_config.get('operational_flags', {}).get('enable_half_sell', True),
                }
            else:
                logger.warning("Configuration file not found, using defaults")
                return {}

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    def _apply_config(self):
        """Apply loaded configuration"""
        self.min_loss_cut_percentage = self.config.get('min_loss_cut_percentage', 0.03)
        self.max_single_stock_ratio = self.config.get('max_single_stock_ratio', 0.4)
        self.pyramiding_ratio = self.config.get('pyramiding_ratio', 0.1)
        self.enable_pyramiding = self.config.get('enable_pyramiding', True)
        self.enable_half_sell = self.config.get('enable_half_sell', True)

    def calculate_position_size(self,
                              adr_range: float,
                              balance: float,
                              market_condition: Optional[MarketCondition] = None) -> float:
        """
        포지션 사이즈 계산 (Strategy_M.py의 CalcPosSizing 로직)

        Args:
            adr_range: Average Daily Range (변동성 지표)
            balance: 총 잔고
            market_condition: 시장 상황 (선택)

        Returns:
            투자 비율 (0.0 ~ 1.0)
        """
        try:
            std_input_size = 0.2  # 기본 20%

            # ADR 기반 조정
            if adr_range >= 5:
                position_ratio = std_input_size / 2  # 변동성이 클 때 절반으로 감소
            else:
                position_ratio = std_input_size

            # 시장 상황 기반 추가 조정
            if market_condition:
                if market_condition == MarketCondition.POOR:
                    position_ratio *= 0.5
                elif market_condition == MarketCondition.GOOD:
                    position_ratio *= 1.2

            # 최대 단일 종목 비율 제한
            position_ratio = min(position_ratio, self.max_single_stock_ratio)

            return position_ratio

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.1  # 기본값 반환

    def calculate_losscut_price(self,
                              current_gain: float,
                              previous_losscut: float,
                              avg_price: float,
                              risk: float) -> float:
        """
        손절가 계산 (Strategy_M.py의 CalcLossCutPrice 로직)

        Args:
            current_gain: 현재 수익률 (1.0 기준, 1.05 = 5% 수익)
            previous_losscut: 이전 손절가
            avg_price: 평균 단가
            risk: 리스크 비율

        Returns:
            새로운 손절가
        """
        try:
            if current_gain < (1 + self.std_risk):
                # 수익이 표준 리스크보다 작을 때
                cut_line = (1 - self.std_risk)
                new_losscut = avg_price * cut_line
            else:
                # 수익이 표준 리스크보다 클 때 (트레일링 스탑)
                cut_line = 1 - ((round((current_gain - 1) / risk, 0) - 1) * risk)
                new_losscut = avg_price * cut_line

            # 최소 손절 비율 적용
            min_cut_line = 1 - self.min_loss_cut_percentage
            min_losscut_price = avg_price * min_cut_line

            # 최소 손절가보다 낮아지지 않도록 보정
            if new_losscut < min_losscut_price:
                new_losscut = min_losscut_price

            # 이전 손절가보다 높을 때만 업데이트 (트레일링 스탑)
            if new_losscut > previous_losscut:
                return new_losscut
            else:
                return previous_losscut

        except Exception as e:
            logger.error(f"Error calculating losscut price: {e}")
            return previous_losscut

    def calculate_win_loss_ratio(self,
                               win_count: int,
                               loss_count: int,
                               total_win_gain: float,
                               total_loss_gain: float) -> Tuple[float, float]:
        """
        승률 및 손익비 계산 (Strategy_M.py의 CalcWinLossRatio 로직)

        Returns:
            (승률 %, 평균승리/평균손실 비율)
        """
        try:
            total_count = win_count + loss_count

            if total_count > 0:
                # 승률 계산 (백분율)
                win_rate = round(win_count * 100 / total_count, 1)

                # 손익비 계산
                if win_count > 0 and loss_count > 0:
                    avg_win = abs(total_win_gain / win_count)
                    avg_loss = abs(total_loss_gain / loss_count)
                    win_loss_gain_ratio = round(avg_win / avg_loss, 3)
                elif win_count > 0:
                    win_loss_gain_ratio = 999.0  # 모든 거래가 수익
                elif loss_count > 0:
                    win_loss_gain_ratio = 0.0  # 모든 거래가 손실
                else:
                    win_loss_gain_ratio = 0.0
            else:
                win_rate = 0
                win_loss_gain_ratio = 0

            return win_rate, win_loss_gain_ratio

        except Exception as e:
            logger.error(f"Error calculating win/loss ratio: {e}")
            return 0.0, 0.0

    def calculate_market_condition(self,
                                 position_count: int,
                                 win_rate: float) -> MarketCondition:
        """
        시장 상황 계산 (Strategy_M.py의 CalcMarketCond 로직)

        Args:
            position_count: 현재 보유 종목 수
            win_rate: 승률 (%)

        Returns:
            시장 상황
        """
        try:
            stock_ratio = position_count / self.max_stock_list

            if win_rate < 30 or stock_ratio == 0:
                market_condition = MarketCondition.POOR
            elif win_rate < 50:
                market_condition = MarketCondition.MODERATE
            else:
                market_condition = MarketCondition.GOOD

            self.market_condition = market_condition
            return market_condition

        except Exception as e:
            logger.error(f"Error calculating market condition: {e}")
            return MarketCondition.MODERATE

    def calculate_cash_ratio(self, market_condition: MarketCondition = None) -> float:
        """
        현금 비율 계산 (Strategy_M.py의 CalcCashRatio 로직)

        Returns:
            현금 보유 비율 (0.0 ~ 1.0)
        """
        try:
            if market_condition is None:
                market_condition = self.market_condition

            if market_condition == MarketCondition.GOOD:
                cash_ratio = 0.0  # 상승 추세에서는 현금 최소화
            else:
                cash_ratio = 0.5  # 보통/하락 추세에서는 현금 50% 유지

            return cash_ratio

        except Exception as e:
            logger.error(f"Error calculating cash ratio: {e}")
            return 0.3  # 기본값

    def select_candidate_stocks_single(self,
                                     buy_signals: np.ndarray,
                                     stock_list: List[str],
                                     sorting_metric: np.ndarray,
                                     target_prices: np.ndarray,
                                     high_prices: np.ndarray,
                                     current_positions: List[str],
                                     position_count: int) -> Tuple[List[str], int]:
        """
        단일 지표 기반 매수 후보 선정 (Strategy_M.py의 select_candidate_stocks_single 로직)

        Args:
            buy_signals: 매수 신호 배열 (1/0)
            stock_list: 종목 리스트
            sorting_metric: 정렬 기준 지표 (RS, EPS 등)
            target_prices: 목표가 배열
            high_prices: 당일 고가 배열
            current_positions: 현재 보유 종목
            position_count: 현재 보유 종목 수

        Returns:
            (후보 종목 리스트, 후보 종목 수)
        """
        try:
            # 조건 1: 매수 신호가 1인 종목
            signal_mask = buy_signals == 1

            # 조건 2: 당일 고가가 목표가 이상인 종목
            price_mask = high_prices >= target_prices

            # 최종 후보 마스크
            final_mask = signal_mask & price_mask

            # 후보 종목 추출
            candidate_stocks = np.array(stock_list)[final_mask]
            candidate_metrics = sorting_metric[final_mask]

            # 현재 보유 종목 제외
            filtered_candidates = [
                (stock, metric)
                for stock, metric in zip(candidate_stocks, candidate_metrics)
                if stock not in current_positions
            ]

            # 정렬 기준 지표 기준 내림차순 정렬
            sorted_candidates = sorted(filtered_candidates, key=lambda x: x[1], reverse=True)
            final_candidates = [stock for stock, _ in sorted_candidates]

            # 매수 가능한 종목 수만큼 선택
            available_positions = self.max_stock_list - position_count
            selected_candidates = final_candidates[:int(available_positions)]

            return selected_candidates, len(selected_candidates)

        except Exception as e:
            logger.error(f"Error selecting candidate stocks: {e}")
            return [], 0

    def select_candidate_stocks_multi(self,
                                    buy_signals: np.ndarray,
                                    stock_list: List[str],
                                    rev_growth: np.ndarray,
                                    eps_growth: np.ndarray,
                                    current_positions: List[str],
                                    position_count: int) -> Tuple[List[str], int]:
        """
        다중 지표 기반 매수 후보 선정 (Strategy_M.py의 select_candidate_stocks_multi 로직)
        REV와 EPS 성장률을 종합하여 순위 매기기

        Returns:
            (후보 종목 리스트, 후보 종목 수)
        """
        try:
            # 매수 신호가 있는 종목 선택
            signal_mask = buy_signals == 1
            candidate_stocks = np.array(stock_list)[signal_mask]
            candidate_rev = rev_growth[signal_mask]
            candidate_eps = eps_growth[signal_mask]

            # 현재 보유 종목 제외
            filtered_candidates = [
                (stock, rev, eps)
                for stock, rev, eps in zip(candidate_stocks, candidate_rev, candidate_eps)
                if stock not in current_positions
            ]

            if len(filtered_candidates) > 0:
                # 각 지표별 순위 계산
                rev_values = np.array([item[1] for item in filtered_candidates])
                eps_values = np.array([item[2] for item in filtered_candidates])

                def rank_descending(arr):
                    """내림차순 순위 계산"""
                    order = np.argsort(-arr)
                    ranks = np.empty_like(order)
                    ranks[order] = np.arange(1, len(arr) + 1)
                    return ranks

                rev_ranks = rank_descending(rev_values)
                eps_ranks = rank_descending(eps_values)

                # 순위 합계 계산 (낮을수록 좋음)
                total_ranks = rev_ranks + eps_ranks

                # 순위 합계 기준 오름차순 정렬
                sorted_indices = np.argsort(total_ranks)
                sorted_candidates = [filtered_candidates[i] for i in sorted_indices]
                final_candidates = [stock for stock, _, _ in sorted_candidates]
            else:
                final_candidates = []

            # 매수 가능한 종목 수만큼 선택
            available_positions = self.max_stock_list - position_count
            selected_candidates = final_candidates[:int(available_positions)]

            return selected_candidates, len(selected_candidates)

        except Exception as e:
            logger.error(f"Error selecting multi-metric candidate stocks: {e}")
            return [], 0

    def calculate_pyramid_parameters(self,
                                   current_balance: float,
                                   existing_position_value: float,
                                   current_gain: float,
                                   avg_price: float) -> Dict[str, float]:
        """
        피라미딩 매수 파라미터 계산

        Args:
            current_balance: 현재 총 잔고
            existing_position_value: 기존 포지션 가치
            current_gain: 현재 수익률
            avg_price: 평균 단가

        Returns:
            피라미딩 관련 계산 결과
        """
        try:
            if not self.enable_pyramiding:
                return {'can_pyramid': False, 'additional_amount': 0.0}

            # 추가 투자 금액 (총 잔고의 피라미딩 비율)
            additional_cash = current_balance * self.pyramiding_ratio

            # 현재 주가 계산
            current_price = avg_price * current_gain

            # 추가 매수 가능 수량
            additional_shares = additional_cash / current_price if current_price > 0 else 0

            # 기존 수량 계산
            original_investment = existing_position_value / current_gain if current_gain > 0 else existing_position_value
            existing_shares = original_investment / avg_price if avg_price > 0 else 0

            # 새로운 가중평균가 계산
            if existing_shares + additional_shares > 0:
                total_cost = (existing_shares * avg_price) + (additional_shares * current_price)
                new_avg_price = total_cost / (existing_shares + additional_shares)
            else:
                new_avg_price = avg_price

            return {
                'can_pyramid': True,
                'additional_amount': additional_cash,
                'additional_shares': additional_shares,
                'new_avg_price': new_avg_price,
                'total_shares': existing_shares + additional_shares,
                'current_price': current_price
            }

        except Exception as e:
            logger.error(f"Error calculating pyramid parameters: {e}")
            return {'can_pyramid': False, 'additional_amount': 0.0}

    def calculate_half_sell_parameters(self,
                                     current_position_value: float,
                                     current_gain: float) -> Dict[str, float]:
        """
        반매도 파라미터 계산

        Returns:
            반매도 관련 계산 결과
        """
        try:
            if not self.enable_half_sell:
                return {'can_half_sell': False, 'sell_amount': 0.0}

            # 절반 매도 금액
            half_sell_amount = current_position_value / 2

            # 매도 후 현금 증가분 (슬리피지 고려)
            cash_increase = half_sell_amount * (1 - self.slippage)

            # 남은 포지션 가치
            remaining_position_value = current_position_value - half_sell_amount

            return {
                'can_half_sell': True,
                'sell_amount': half_sell_amount,
                'cash_increase': cash_increase,
                'remaining_position_value': remaining_position_value,
                'sell_ratio': 0.5
            }

        except Exception as e:
            logger.error(f"Error calculating half sell parameters: {e}")
            return {'can_half_sell': False, 'sell_amount': 0.0}

    def validate_position_constraints(self,
                                    new_position_value: float,
                                    total_balance: float,
                                    current_positions: int) -> Dict[str, bool]:
        """
        포지션 제약 조건 검증

        Returns:
            제약 조건 검증 결과
        """
        try:
            constraints = {
                'max_positions_ok': current_positions < self.max_stock_list,
                'max_single_ratio_ok': (new_position_value / total_balance) <= self.max_single_stock_ratio,
                'min_cash_ok': (total_balance * 0.1) < total_balance,  # 최소 10% 현금 보유
                'all_constraints_ok': True
            }

            # 모든 제약 조건 만족 여부
            constraints['all_constraints_ok'] = all([
                constraints['max_positions_ok'],
                constraints['max_single_ratio_ok'],
                constraints['min_cash_ok']
            ])

            return constraints

        except Exception as e:
            logger.error(f"Error validating position constraints: {e}")
            return {'all_constraints_ok': False}

# 테스트 및 사용 예시
def create_sample_position_data():
    """테스트용 샘플 데이터 생성"""
    np.random.seed(42)

    stock_list = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'INTC', 'ORCL']
    buy_signals = np.random.choice([0, 1], size=len(stock_list), p=[0.7, 0.3])
    rs_values = np.random.uniform(50, 100, len(stock_list))
    target_prices = np.random.uniform(100, 200, len(stock_list))
    high_prices = np.random.uniform(95, 205, len(stock_list))

    return {
        'stock_list': stock_list,
        'buy_signals': buy_signals,
        'rs_values': rs_values,
        'target_prices': target_prices,
        'high_prices': high_prices
    }

if __name__ == "__main__":
    # 테스트 실행
    service = PositionSizingService(
        std_risk=0.05,
        market='US',
        area='US',
        max_stock_list=10
    )

    # 샘플 데이터 생성
    sample_data = create_sample_position_data()

    # 포지션 사이즈 계산 테스트
    position_size = service.calculate_position_size(adr_range=3.0, balance=100000)
    print(f"Position Size: {position_size:.3f} ({position_size*100:.1f}%)")

    # 손절가 계산 테스트
    losscut_price = service.calculate_losscut_price(
        current_gain=1.08, previous_losscut=95.0, avg_price=100.0, risk=0.05
    )
    print(f"Loss Cut Price: ${losscut_price:.2f}")

    # 후보 종목 선정 테스트
    candidates, count = service.select_candidate_stocks_single(
        buy_signals=sample_data['buy_signals'],
        stock_list=sample_data['stock_list'],
        sorting_metric=sample_data['rs_values'],
        target_prices=sample_data['target_prices'],
        high_prices=sample_data['high_prices'],
        current_positions=['AAPL', 'MSFT'],
        position_count=2
    )
    print(f"Selected Candidates: {candidates[:3]} (Total: {count})")

    # 시장 상황 계산 테스트
    market_condition = service.calculate_market_condition(position_count=5, win_rate=65)
    print(f"Market Condition: {market_condition}")

    print("\nPosition Sizing Service Test Completed Successfully!")