#!/usr/bin/env python3
"""
Strategy Integration Service
실제 Strategy Layer에서 candidates와 holdings를 받아서 trading signals로 변환하는 서비스
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sys

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from strategy.signal_generation_service import SignalGenerationService
from strategy.position_sizing_service import PositionSizingService, CandidateStock
from strategy.account_analysis_service import AccountAnalysisService, StockHolding
from models.trading_models import TradingSignal, SignalType

logger = logging.getLogger(__name__)

class StrategyIntegrationService:
    """
    Strategy Layer와 Auto Trade Orchestrator 간의 통합 서비스
    실제 Strategy 구성요소들을 활용하여 매매 신호 생성
    """

    def __init__(self, area: str = 'US', std_risk: float = 0.05):
        self.area = area
        self.std_risk = std_risk

        # Strategy Layer 서비스들 초기화
        self.signal_service = SignalGenerationService(area=area, trading_mode=True)
        self.position_service = PositionSizingService(
            std_risk=std_risk,
            market=area,
            area=area,
            max_stock_list=10
        )
        self.account_service = AccountAnalysisService(area=area, std_risk=std_risk)

    async def get_trading_signals(self,
                                market_data: Dict[str, pd.DataFrame],
                                account_data: Dict[str, Any]) -> List[TradingSignal]:
        """
        Strategy Layer에서 실제 매매 신호를 생성

        Args:
            market_data: 시장 데이터 (daily, weekly, rs, fundamental, earnings)
            account_data: 계좌 데이터 (balance, holdings)

        Returns:
            TradingSignal 리스트
        """
        try:
            signals = []

            # 1. 현재 보유 종목 분석
            holdings_analysis = await self._analyze_current_holdings(
                account_data.get('holdings', []),
                account_data.get('balance', {}),
                market_data
            )

            # 2. 매수 후보 종목 생성
            buy_candidates = await self._generate_buy_candidates(
                market_data,
                holdings_analysis['current_positions']
            )

            # 3. 매도 신호 생성 (현재 보유 종목 기반)
            sell_signals = await self._generate_sell_signals(
                holdings_analysis['holdings'],
                market_data
            )

            # 4. 매수 신호 생성 (후보 종목 기반)
            buy_signals = await self._generate_buy_signals(
                buy_candidates,
                market_data,
                account_data.get('balance', {})
            )

            # 5. 모든 신호 결합
            signals.extend(sell_signals)
            signals.extend(buy_signals)

            logger.info(f"Generated {len(signals)} trading signals from Strategy Layer")
            return signals

        except Exception as e:
            logger.error(f"Error generating trading signals from Strategy Layer: {e}")
            return []

    async def _analyze_current_holdings(self,
                                      holdings_data: List[Dict[str, Any]],
                                      balance_data: Dict[str, Any],
                                      market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """현재 보유 종목 분석"""
        try:
            # AccountAnalysisService를 사용하여 보유 종목 분석
            analysis_result = self.account_service.analyze_account(
                holdings_data=holdings_data,
                balance_data=balance_data,
                market_data=market_data
            )

            # 현재 보유 종목 리스트 추출
            current_positions = [
                holding.ticker for holding in analysis_result.get('holdings', [])
                if hasattr(holding, 'ticker')
            ]

            return {
                'analysis': analysis_result,
                'holdings': analysis_result.get('holdings', []),
                'current_positions': current_positions,
                'account_summary': analysis_result.get('account_summary', {})
            }

        except Exception as e:
            logger.error(f"Error analyzing current holdings: {e}")
            return {'analysis': {}, 'holdings': [], 'current_positions': [], 'account_summary': {}}

    async def _generate_buy_candidates(self,
                                     market_data: Dict[str, pd.DataFrame],
                                     current_positions: List[str]) -> List[CandidateStock]:
        """매수 후보 종목 생성 (백테스트 모드와 동일한 로직 사용)"""
        try:
            candidates = []

            # MongoDB에서 로딩된 전체 유니버스 사용
            universe_data = market_data.get('universe', {})
            all_symbols = universe_data.get('all_symbols', [])

            if not all_symbols:
                # 폴백: daily 데이터에서 심볼 추출
                daily_data = market_data.get('daily', pd.DataFrame())
                if not daily_data.empty and 'symbol' in daily_data.columns:
                    all_symbols = daily_data['symbol'].unique().tolist()

            logger.info(f"전체 유니버스에서 {len(all_symbols)}개 심볼로 후보 분석 시작")

            # Position Sizing Service를 사용하여 후보 생성 (백테스트와 동일)
            try:
                # 안전한 후보 조회 - 메소드 존재 확인 후 호출
                if hasattr(self.position_service, 'get_candidates'):
                    strategy_candidates = await self.position_service.get_candidates()
                    logger.info(f"Position Sizing Service에서 {len(strategy_candidates)}개 후보 생성")
                else:
                    # 폴백: 빈 후보 리스트로 진행
                    strategy_candidates = []
                    logger.warning("Position Sizing Service 호출 실패, 전체 심볼 풀에서 후보 선택 진행")

                # 생성된 후보들을 CandidateStock 형태로 변환
                for candidate in strategy_candidates:
                    if hasattr(candidate, 'ticker') and candidate.ticker not in current_positions:
                        # 시장 데이터에서 해당 심볼의 현재 가격 및 지표 확인
                        symbol_data = self._get_symbol_market_data(candidate.ticker, market_data)

                        if symbol_data and symbol_data.get('current_price', 0) > 0:
                            # 백테스트와 동일한 후보 검증 로직
                            if self._validate_candidate_for_trading(candidate, symbol_data):
                                candidates.append(candidate)

            except Exception as e:
                logger.warning(f"Position Sizing Service 호출 실패, 대체 로직 사용: {e}")

                # 대체 로직: 직접 시장 데이터 분석
                candidates = await self._fallback_candidate_generation(
                    all_symbols, current_positions, market_data
                )

            # 백테스트와 동일한 정렬 및 필터링
            candidates = self._rank_and_filter_candidates(candidates, current_positions)

            logger.info(f"최종 {len(candidates)}개 매수 후보 생성")
            return candidates

        except Exception as e:
            logger.error(f"Error generating buy candidates: {e}")
            return []

    def _get_symbol_market_data(self, symbol: str, market_data: Dict[str, pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """심볼의 시장 데이터 조회"""
        try:
            daily_data = market_data.get('daily', pd.DataFrame())
            rs_data = market_data.get('rs', pd.DataFrame())

            if daily_data.empty:
                return None

            # 심볼 데이터 추출
            symbol_daily = self._extract_symbol_data(daily_data, symbol)
            symbol_rs = self._extract_symbol_data(rs_data, symbol)

            if symbol_daily.empty:
                return None

            # 최신 데이터 추출
            latest_daily = symbol_daily.iloc[-1]
            latest_rs = symbol_rs.iloc[-1] if not symbol_rs.empty else {}

            return {
                'current_price': latest_daily.get('Dclose', 0),
                'sma20': latest_daily.get('SMA20', 0),
                'sma50': latest_daily.get('SMA50', 0),
                'sma200': latest_daily.get('SMA200', 0),
                'rsi': latest_daily.get('RSI', 50),
                'rs_4w': latest_rs.get('RS_4W', 50),
                'rs_12w': latest_rs.get('RS_12W', 50),
                'volume': latest_daily.get('Volume', 0),
                'market': latest_rs.get('market', 'US')
            }

        except Exception as e:
            logger.warning(f"Error getting market data for {symbol}: {e}")
            return None

    def _validate_candidate_for_trading(self, candidate: CandidateStock, symbol_data: Dict[str, Any]) -> bool:
        """후보 종목의 거래 적합성 검증 (백테스트 기준 적용)"""
        try:
            current_price = symbol_data.get('current_price', 0)
            sma20 = symbol_data.get('sma20', 0)
            sma50 = symbol_data.get('sma50', 0)
            rs_4w = symbol_data.get('rs_4w', 50)
            volume = symbol_data.get('volume', 0)

            # 백테스트와 동일한 검증 기준
            checks = [
                current_price > 5.0,  # 최소 가격
                current_price > sma20 * 0.95,  # SMA20 근처 또는 상회
                rs_4w > 70,  # 상대강도 기준
                volume > 50000,  # 최소 거래량
                candidate.signal_strength > 0.6  # 최소 신호 강도
            ]

            return sum(checks) >= 3  # 5개 중 3개 이상 만족

        except Exception as e:
            logger.warning(f"Error validating candidate {candidate.ticker}: {e}")
            return False

    async def _fallback_candidate_generation(self, all_symbols: List[str],
                                           current_positions: List[str],
                                           market_data: Dict[str, pd.DataFrame]) -> List[CandidateStock]:
        """대체 후보 생성 로직"""
        try:
            candidates = []

            # 전달받은 모든 심볼 분석 (main에서 이미 필터링됨)
            # main_auto_trade.py에서 symbol_analysis 설정에 따라 이미 필터링된 상태
            analysis_symbols = all_symbols

            for symbol in analysis_symbols:
                if symbol in current_positions:
                    continue

                symbol_data = self._get_symbol_market_data(symbol, market_data)
                if not symbol_data:
                    continue

                # 간단한 점수 계산
                score = self._calculate_candidate_score(symbol_data)

                if score > 0.6:  # 최소 점수 기준
                    candidate = CandidateStock(
                        ticker=symbol,
                        sorting_metric=score,
                        target_price=symbol_data.get('current_price', 0) * 1.08,
                        signal_strength=score,
                        market_code=symbol_data.get('market', 'US')
                    )
                    candidates.append(candidate)

            return candidates

        except Exception as e:
            logger.error(f"Error in fallback candidate generation: {e}")
            return []

    def _calculate_candidate_score(self, symbol_data: Dict[str, Any]) -> float:
        """후보 점수 계산"""
        try:
            current_price = symbol_data.get('current_price', 0)
            sma20 = symbol_data.get('sma20', 0)
            sma50 = symbol_data.get('sma50', 0)
            rs_4w = symbol_data.get('rs_4w', 50)
            rsi = symbol_data.get('rsi', 50)

            score = 0.0

            # 가격 모멘텀
            if sma20 > 0 and current_price > sma20:
                score += 0.3
            if sma50 > 0 and sma20 > sma50:
                score += 0.2

            # 상대강도
            if rs_4w > 80:
                score += 0.3
            elif rs_4w > 70:
                score += 0.2

            # RSI
            if 40 < rsi < 70:
                score += 0.2

            return min(score, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating candidate score: {e}")
            return 0.0

    def _rank_and_filter_candidates(self, candidates: List[CandidateStock],
                                  current_positions: List[str]) -> List[CandidateStock]:
        """후보 순위 매기기 및 필터링"""
        try:
            # 신호 강도 기준으로 정렬
            candidates.sort(key=lambda x: x.signal_strength, reverse=True)

            # 최대 후보 수 제한 (백테스트와 동일)
            max_candidates = min(10, self.position_service.max_stock_list - len(current_positions))
            candidates = candidates[:max_candidates]

            return candidates

        except Exception as e:
            logger.error(f"Error ranking candidates: {e}")
            return candidates

    async def _generate_sell_signals(self,
                                   holdings: List[StockHolding],
                                   market_data: Dict[str, pd.DataFrame]) -> List[TradingSignal]:
        """매도 신호 생성 (보유 종목 기반)"""
        try:
            sell_signals = []
            daily_data = market_data.get('daily', pd.DataFrame())

            for holding in holdings:
                try:
                    if not hasattr(holding, 'ticker'):
                        continue

                    symbol = holding.ticker
                    symbol_daily = self._extract_symbol_data(daily_data, symbol)

                    if symbol_daily.empty:
                        continue

                    # 매도 신호 생성
                    sell_result = self.signal_service.generate_sell_signals(symbol_daily)

                    if sell_result['signal'] == SignalType.SELL:
                        signal = TradingSignal(
                            symbol=symbol,
                            signal_type=SignalType.SELL,
                            confidence=0.8,  # 매도 신호는 높은 신뢰도
                            price=sell_result.get('close_price', holding.current_price),
                            timestamp=datetime.now(),
                            strategy_name='HoldingAnalysis',
                            expected_return=-0.05,  # 손실 방지
                            target_price=sell_result.get('close_price', holding.current_price),
                            metadata={
                                'reason': sell_result.get('reason', 'Technical sell signal'),
                                'current_gain': getattr(holding, 'gain_percent', 0.0),
                                'holding_info': {
                                    'avg_price': getattr(holding, 'avg_price', 0.0),
                                    'amount': getattr(holding, 'amount', 0.0)
                                }
                            }
                        )
                        sell_signals.append(signal)

                except Exception as e:
                    logger.warning(f"Error processing sell signal for {holding.ticker if hasattr(holding, 'ticker') else 'unknown'}: {e}")
                    continue

            logger.info(f"Generated {len(sell_signals)} sell signals")
            return sell_signals

        except Exception as e:
            logger.error(f"Error generating sell signals: {e}")
            return []

    async def _generate_buy_signals(self,
                                  candidates: List[CandidateStock],
                                  market_data: Dict[str, pd.DataFrame],
                                  balance_data: Dict[str, Any]) -> List[TradingSignal]:
        """매수 신호 생성 (후보 종목 기반)"""
        try:
            buy_signals = []
            daily_data = market_data.get('daily', pd.DataFrame())

            # 계좌 잔고 정보
            total_balance = balance_data.get('total_balance', 100000)  # 기본값

            for candidate in candidates:
                try:
                    symbol = candidate.ticker
                    symbol_daily = self._extract_symbol_data(daily_data, symbol)

                    if symbol_daily.empty:
                        continue

                    # 현재 가격 추출
                    current_price = symbol_daily.iloc[-1].get('Dclose', candidate.target_price)
                    if current_price <= 0:
                        current_price = candidate.target_price

                    # ADR 계산 (변동성 지표)
                    if len(symbol_daily) >= 20:
                        high_low_range = symbol_daily['Dhigh'] - symbol_daily['Dlow'] if 'Dhigh' in symbol_daily.columns and 'Dlow' in symbol_daily.columns else pd.Series([2.0])
                        adr = high_low_range.tail(20).mean()
                    else:
                        adr = current_price * 0.02  # 기본 2% 변동성

                    # 포지션 사이즈 계산
                    position_ratio = self.position_service.calculate_position_size(
                        adr_range=adr / current_price * 100,  # 퍼센트로 변환
                        balance=total_balance
                    )

                    # 매수 신호 생성
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type=SignalType.BUY if candidate.signal_strength > 0.7 else SignalType.BUY,
                        confidence=candidate.signal_strength,
                        price=current_price,
                        timestamp=datetime.now(),
                        strategy_name='StrategyLayerIntegration',
                        expected_return=0.08,  # 8% 기대 수익률
                        target_price=candidate.target_price,
                        metadata={
                            'candidate_info': {
                                'sorting_metric': candidate.sorting_metric,
                                'signal_strength': candidate.signal_strength,
                                'market_code': candidate.market_code
                            },
                            'position_sizing': {
                                'position_ratio': position_ratio,
                                'adr': adr,
                                'recommended_amount': total_balance * position_ratio
                            }
                        }
                    )
                    buy_signals.append(signal)

                except Exception as e:
                    logger.warning(f"Error processing buy signal for {candidate.ticker}: {e}")
                    continue

            logger.info(f"Generated {len(buy_signals)} buy signals")
            return buy_signals

        except Exception as e:
            logger.error(f"Error generating buy signals: {e}")
            return []

    def _extract_symbol_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """DataFrame에서 특정 심볼의 데이터 추출"""
        try:
            if df.empty:
                return pd.DataFrame()

            # 심볼 컬럼이 있는 경우
            if 'symbol' in df.columns:
                return df[df['symbol'] == symbol].copy()

            # 인덱스가 심볼인 경우
            elif symbol in df.index:
                return df.loc[[symbol]].copy()

            # 멀티 인덱스인 경우
            elif hasattr(df.index, 'levels') and len(df.index.levels) > 1:
                try:
                    return df.xs(symbol, level=0).copy()
                except KeyError:
                    return pd.DataFrame()

            # 데이터가 없는 경우 빈 DataFrame 반환
            return pd.DataFrame()

        except Exception as e:
            logger.warning(f"Error extracting data for symbol {symbol}: {e}")
            return pd.DataFrame()

    async def get_portfolio_summary(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 요약 정보 제공"""
        try:
            holdings_analysis = await self._analyze_current_holdings(
                account_data.get('holdings', []),
                account_data.get('balance', {}),
                {}  # 시장 데이터 없이도 기본 분석 가능
            )

            return {
                'account_summary': holdings_analysis.get('account_summary', {}),
                'holdings_count': len(holdings_analysis.get('holdings', [])),
                'current_positions': holdings_analysis.get('current_positions', []),
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                'account_summary': {},
                'holdings_count': 0,
                'current_positions': [],
                'analysis_timestamp': datetime.now().isoformat()
            }

# 사용 예시를 위한 테스트 함수
async def test_strategy_integration():
    """Strategy Integration Service 테스트"""
    try:
        service = StrategyIntegrationService(area='US', std_risk=0.05)

        # 샘플 데이터
        sample_market_data = {
            'daily': pd.DataFrame({
                'symbol': ['AAPL', 'MSFT', 'GOOGL'] * 30,
                'Dhigh': np.random.uniform(150, 180, 90),
                'Dlow': np.random.uniform(140, 170, 90),
                'Dclose': np.random.uniform(145, 175, 90),
                'SMA20': np.random.uniform(140, 170, 90),
                'SMA50': np.random.uniform(135, 165, 90),
                'SMA200': np.random.uniform(130, 160, 90),
            }),
            'rs': pd.DataFrame({
                'symbol': ['AAPL', 'MSFT', 'GOOGL'] * 30,
                'RS_4W': np.random.uniform(80, 95, 90),
                'RS_12W': np.random.uniform(85, 95, 90),
            })
        }

        sample_account_data = {
            'balance': {'total_balance': 100000, 'cash_balance': 50000},
            'holdings': [
                {'StockCode': 'AAPL', 'StockAmt': 10, 'StockAvgPrice': 150.0, 'CurrentPrice': 160.0}
            ]
        }

        # 신호 생성 테스트
        signals = await service.get_trading_signals(sample_market_data, sample_account_data)
        print(f"Generated {len(signals)} signals")

        for signal in signals[:3]:  # 처음 3개만 출력
            print(f"Signal: {signal.symbol} {signal.signal_type.value} at ${signal.price:.2f}")

    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_strategy_integration())