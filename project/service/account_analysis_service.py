"""
Account Analysis Service

계좌 분석 및 포트폴리오 관리 서비스
KIS API를 통해 실시간 계좌 정보를 수집하고 분석
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..interfaces.service_interfaces import IAccountAnalysisService, BaseService
from ..models.trading_models import (
    Portfolio, PortfolioPosition, PriceData,
    MarketType, SystemStatus
)


class AccountAnalysisService(BaseService, IAccountAnalysisService):
    """계좌 분석 서비스 구현"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # KIS API 설정
        self.kis_config = config.get('kis_api', {})
        self.account_no = self.kis_config.get('account_no', '')
        self.is_virtual_account = self.kis_config.get('is_virtual', True)

        # 계좌 데이터 캐시
        self.current_portfolio: Optional[Portfolio] = None
        self.positions: Dict[str, PortfolioPosition] = {}
        self.account_balance: Dict[str, float] = {}
        self.real_holdings_data: List[Dict] = []  # 실제 보유 종목 데이터

        # 업데이트 관리
        self.last_update_time = None
        self.update_interval = 30  # 30초마다 업데이트
        self.update_task = None

        # 가격 데이터 연동 (LivePriceService로부터)
        self.price_data_cache: Dict[str, PriceData] = {}

        # 통계 데이터
        self.daily_pnl_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {}

    async def start_service(self) -> bool:
        """서비스 시작"""
        try:
            self.logger.info("[AccountAnalysisService] 서비스 시작")

            # KIS API 연결 초기화 (시뮬레이션)
            await self._initialize_kis_connection()

            # 초기 계좌 데이터 로드
            await self._load_initial_account_data()

            # 정기 업데이트 태스크 시작
            self.update_task = asyncio.create_task(self._account_update_loop())

            await self.initialize()
            self.logger.info("[AccountAnalysisService] 서비스 시작 완료")
            return True

        except Exception as e:
            self.log_error(f"서비스 시작 실패: {e}")
            return False

    async def stop_service(self) -> bool:
        """서비스 중지"""
        try:
            self.logger.info("[AccountAnalysisService] 서비스 중지")

            # 업데이트 태스크 중지
            if self.update_task and not self.update_task.done():
                self.update_task.cancel()

            await self.cleanup()
            return True

        except Exception as e:
            self.log_error(f"서비스 중지 실패: {e}")
            return False

    async def get_current_portfolio(self) -> Optional[Portfolio]:
        """현재 포트폴리오 조회"""
        try:
            if not self.current_portfolio or self._is_data_stale():
                await self._update_portfolio_data()

            return self.current_portfolio

        except Exception as e:
            self.log_error(f"포트폴리오 조회 실패: {e}")
            return None

    async def get_account_balance(self) -> Dict[str, float]:
        """계좌 잔고 조회"""
        try:
            # 실제로는 KIS API 호출
            await self._fetch_account_balance()
            return self.account_balance.copy()

        except Exception as e:
            self.log_error(f"계좌 잔고 조회 실패: {e}")
            return {}

    async def get_positions(self) -> List[PortfolioPosition]:
        """보유 포지션 목록"""
        try:
            if not self.positions or self._is_data_stale():
                await self._update_positions_data()

            return list(self.positions.values())

        except Exception as e:
            self.log_error(f"포지션 조회 실패: {e}")
            return []

    async def get_position_by_symbol(self, symbol: str) -> Optional[PortfolioPosition]:
        """특정 종목 포지션 조회"""
        try:
            if symbol in self.positions:
                # 실시간 가격으로 포지션 업데이트
                await self._update_position_with_current_price(symbol)
                return self.positions[symbol]

            return None

        except Exception as e:
            self.log_error(f"포지션 조회 실패 ({symbol}): {e}")
            return None

    async def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """포트폴리오 지표 계산"""
        try:
            metrics = {}

            portfolio = await self.get_current_portfolio()
            if not portfolio:
                return metrics

            # 기본 지표
            metrics['total_value'] = portfolio.total_value
            metrics['stock_value'] = portfolio.stock_value
            metrics['cash_ratio'] = portfolio.cash / portfolio.total_value if portfolio.total_value > 0 else 0
            metrics['position_count'] = portfolio.get_position_count()

            # 수익률 지표
            metrics['day_return'] = portfolio.day_pnl_pct
            metrics['total_return'] = portfolio.total_pnl_pct

            # 시장별 배분
            metrics['market_allocation'] = portfolio.get_market_allocation()

            # 위험도 지표
            metrics.update(await self._calculate_risk_metrics())

            # 성과 지표
            metrics.update(await self._calculate_performance_metrics())

            self.performance_metrics = metrics
            return metrics

        except Exception as e:
            self.log_error(f"포트폴리오 지표 계산 실패: {e}")
            return {}

    async def get_daily_pnl_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """일별 손익 히스토리"""
        try:
            # 최근 N일간의 손익 데이터 반환
            return self.daily_pnl_history[-days:] if self.daily_pnl_history else []

        except Exception as e:
            self.log_error(f"손익 히스토리 조회 실패: {e}")
            return []

    def set_price_data(self, symbol: str, price_data: PriceData) -> None:
        """가격 데이터 업데이트 (LivePriceService로부터)"""
        self.price_data_cache[symbol] = price_data

        # 해당 종목 포지션이 있으면 실시간 업데이트
        if symbol in self.positions:
            asyncio.create_task(self._update_position_with_price_data(symbol, price_data))

    async def _initialize_kis_connection(self) -> bool:
        """KIS API 연결 초기화 (시뮬레이션)"""
        try:
            # 실제로는 KIS API 토큰 획득 및 연결 테스트
            await asyncio.sleep(0.1)  # 연결 시뮬레이션

            self.logger.info(f"[AccountAnalysisService] KIS API 연결 성공 (계좌: {self.account_no})")
            return True

        except Exception as e:
            self.log_error(f"KIS API 연결 실패: {e}")
            return False

    async def _load_initial_account_data(self) -> None:
        """초기 계좌 데이터 로드"""
        try:
            # 계좌 잔고 조회
            await self._fetch_account_balance()

            # 보유 포지션 조회
            await self._fetch_positions()

            # 포트폴리오 계산
            await self._update_portfolio_data()

            self.last_update_time = datetime.now()
            self.logger.info("[AccountAnalysisService] 초기 계좌 데이터 로드 완료")

        except Exception as e:
            self.log_error(f"초기 데이터 로드 실패: {e}")

    async def _account_update_loop(self):
        """계좌 정보 업데이트 루프"""
        while self.is_running:
            try:
                await self._fetch_account_balance()
                await self._fetch_positions()
                await self._update_portfolio_data()

                # 일별 손익 기록
                await self._record_daily_pnl()

                self.last_update_time = datetime.now()

                # 업데이트 간격만큼 대기
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                self.log_error(f"계좌 업데이트 루프 오류: {e}")
                await asyncio.sleep(5)

    async def _fetch_account_balance(self) -> None:
        """계좌 잔고 조회 (실제 KIS API)"""
        try:
            # main_auto_trade.py의 get_account_data_from_helper 함수 임포트 및 호출
            import sys
            import os
            from pathlib import Path

            # main_auto_trade.py의 get_account_data_from_helper 함수 사용
            project_root = Path(__file__).parent.parent.parent
            sys.path.append(str(project_root))

            try:
                from main_auto_trade import get_account_data_from_helper

                # 실제 계좌 데이터 조회
                account_data = await get_account_data_from_helper()

                if account_data and account_data.get('balance'):
                    balance = account_data['balance']

                    # USD equivalent로 통합된 잔고 정보 사용
                    if balance.get('currency') == 'USD_EQUIVALENT':
                        self.account_balance = {
                            'total_value': balance.get('total_balance', 0),
                            'cash': balance.get('cash_balance', 0),
                            'stock_value': balance.get('stock_value', 0),
                            'buying_power': balance.get('cash_balance', 0),  # 현금 잔고를 매수력으로 사용
                            'day_pnl': balance.get('revenue', 0),  # revenue를 일간 손익으로 사용
                            'total_pnl': balance.get('revenue', 0)
                        }

                        # 실제 보유 종목 데이터도 저장
                        if account_data.get('holdings'):
                            self.set_real_holdings_data(account_data['holdings'])

                        self.logger.info(f"[REAL_API] 계좌 데이터 조회 성공 - 총자산: ${self.account_balance['total_value']:,.2f}")
                    else:
                        # 단일 통화 잔고
                        self.account_balance = {
                            'total_value': balance.get('total_balance', 0),
                            'cash': balance.get('cash_balance', 0),
                            'stock_value': balance.get('stock_value', 0),
                            'buying_power': balance.get('cash_balance', 0),
                            'day_pnl': balance.get('revenue', 0),
                            'total_pnl': balance.get('revenue', 0)
                        }

                        if account_data.get('holdings'):
                            self.set_real_holdings_data(account_data['holdings'])

                        self.logger.info(f"[REAL_API] 계좌 데이터 조회 성공 - 총자산: ${self.account_balance['total_value']:,.2f}")
                else:
                    self.logger.warning("계좌 데이터 조회 결과가 비어있습니다. 기본값을 사용합니다.")
                    self.account_balance = {
                        'total_value': 0.0,
                        'cash': 0.0,
                        'stock_value': 0.0,
                        'buying_power': 0.0,
                        'day_pnl': 0.0,
                        'total_pnl': 0.0
                    }

            except ImportError as e:
                self.logger.error(f"main_auto_trade 모듈 임포트 실패: {e}")
                # 폴백: 빈 잔고로 설정
                self.account_balance = {
                    'total_value': 0.0,
                    'cash': 0.0,
                    'stock_value': 0.0,
                    'buying_power': 0.0,
                    'day_pnl': 0.0,
                    'total_pnl': 0.0
                }

        except Exception as e:
            self.log_error(f"계좌 잔고 조회 실패: {e}")
            # 에러 시 빈 잔고로 설정
            self.account_balance = {
                'total_value': 0.0,
                'cash': 0.0,
                'stock_value': 0.0,
                'buying_power': 0.0,
                'day_pnl': 0.0,
                'total_pnl': 0.0
            }

    async def _fetch_positions(self) -> None:
        """보유 포지션 조회 (실제 데이터만 사용)"""
        try:
            # 실제 계좌 데이터가 있으면 사용
            if hasattr(self, 'real_holdings_data') and self.real_holdings_data:
                await self._load_real_positions()
                return

            # 실제 데이터가 없으면 빈 포지션으로 설정
            self.positions = {}
            self.logger.warning("실제 계좌 데이터가 없어 포지션을 빈 상태로 설정합니다.")

        except Exception as e:
            self.log_error(f"포지션 조회 실패: {e}")

    async def _load_real_positions(self) -> None:
        """실제 계좌 데이터로 포지션 로드"""
        try:
            self.positions = {}

            for holding in self.real_holdings_data:
                symbol = holding.get('StockCode', holding.get('symbol', ''))
                if not symbol:
                    continue

                quantity = float(holding.get('StockAmt', holding.get('quantity', 0)))
                avg_price = float(holding.get('StockAvgPrice', holding.get('avg_price', 0)))
                current_price = float(holding.get('CurrentPrice', holding.get('current_price', avg_price)))

                # 실시간 가격이 있으면 사용
                if symbol in self.price_data_cache:
                    current_price = self.price_data_cache[symbol].price

                market_value = quantity * current_price
                unrealized_pnl = (current_price - avg_price) * quantity
                unrealized_pnl_pct = (unrealized_pnl / (avg_price * quantity)) * 100 if avg_price > 0 else 0

                position = PortfolioPosition(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=avg_price,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    market=self._get_market_type(symbol),
                    sector=self._get_sector(symbol),
                    last_update=datetime.now()
                )

                self.positions[symbol] = position

            self.logger.info(f"실제 보유 종목 {len(self.positions)}개 로드 완료")

        except Exception as e:
            self.log_error(f"실제 포지션 로드 실패: {e}")

    def set_real_holdings_data(self, holdings_data: List[Dict]) -> None:
        """실제 보유 종목 데이터 설정"""
        self.real_holdings_data = holdings_data
        self.logger.info(f"실제 보유 종목 데이터 설정: {len(holdings_data)}개")

    async def refresh_positions_with_real_data(self) -> None:
        """실제 데이터로 포지션 새로고침"""
        if hasattr(self, 'real_holdings_data') and self.real_holdings_data:
            await self._load_real_positions()
            await self._update_portfolio_data()
            self.logger.info(f"실제 데이터로 포지션 새로고침 완료: {len(self.positions)}개")

    async def _update_portfolio_data(self) -> None:
        """포트폴리오 데이터 업데이트"""
        try:
            if not self.account_balance or not self.positions:
                return

            # 포지션별 시장가치 합계
            total_stock_value = sum(pos.market_value for pos in self.positions.values())

            # 총 자산가치
            total_value = self.account_balance.get('cash', 0) + total_stock_value

            # 일일 손익
            day_pnl = self.account_balance.get('day_pnl', 0)
            day_pnl_pct = (day_pnl / total_value) * 100 if total_value > 0 else 0

            # 총 손익
            total_pnl = self.account_balance.get('total_pnl', 0)
            total_pnl_pct = (total_pnl / (total_value - total_pnl)) * 100 if (total_value - total_pnl) > 0 else 0

            # Portfolio 객체 생성
            portfolio = Portfolio(
                total_value=total_value,
                cash=self.account_balance.get('cash', 0),
                stock_value=total_stock_value,
                day_pnl=day_pnl,
                total_pnl=total_pnl,
                day_pnl_pct=day_pnl_pct,
                total_pnl_pct=total_pnl_pct,
                positions=self.positions.copy(),
                last_update=datetime.now()
            )

            self.current_portfolio = portfolio

        except Exception as e:
            self.log_error(f"포트폴리오 데이터 업데이트 실패: {e}")

    async def _update_position_with_current_price(self, symbol: str) -> None:
        """현재 가격으로 포지션 업데이트"""
        try:
            if symbol not in self.positions:
                return

            # 실시간 가격 데이터 사용
            if symbol in self.price_data_cache:
                price_data = self.price_data_cache[symbol]
                await self._update_position_with_price_data(symbol, price_data)

        except Exception as e:
            self.log_error(f"포지션 가격 업데이트 실패 ({symbol}): {e}")

    async def _update_position_with_price_data(self, symbol: str, price_data: PriceData) -> None:
        """가격 데이터로 포지션 업데이트"""
        try:
            if symbol not in self.positions:
                return

            position = self.positions[symbol]

            # 새로운 시장가치 계산
            new_market_value = position.quantity * price_data.price
            new_unrealized_pnl = (price_data.price - position.avg_price) * position.quantity
            new_unrealized_pnl_pct = (new_unrealized_pnl / (position.avg_price * position.quantity)) * 100

            # 일일 변동
            day_change = price_data.change if price_data.change else 0
            day_change_pct = price_data.change_pct if price_data.change_pct else 0

            # 포지션 업데이트
            updated_position = PortfolioPosition(
                symbol=position.symbol,
                quantity=position.quantity,
                avg_price=position.avg_price,
                current_price=price_data.price,
                market_value=new_market_value,
                unrealized_pnl=new_unrealized_pnl,
                unrealized_pnl_pct=new_unrealized_pnl_pct,
                day_change=day_change,
                day_change_pct=day_change_pct,
                market=position.market,
                sector=position.sector,
                last_update=datetime.now()
            )

            self.positions[symbol] = updated_position

        except Exception as e:
            self.log_error(f"포지션 가격 업데이트 실패 ({symbol}): {e}")

    async def _calculate_risk_metrics(self) -> Dict[str, float]:
        """위험도 지표 계산"""
        try:
            metrics = {}

            if not self.positions:
                return metrics

            # 포지션 집중도 (최대 단일 종목 비중)
            if self.current_portfolio and self.current_portfolio.stock_value > 0:
                position_weights = [pos.market_value / self.current_portfolio.stock_value
                                 for pos in self.positions.values()]
                metrics['max_position_weight'] = max(position_weights) if position_weights else 0
                metrics['avg_position_weight'] = sum(position_weights) / len(position_weights) if position_weights else 0

            # 시장 집중도
            if self.current_portfolio:
                market_allocation = self.current_portfolio.get_market_allocation()
                if market_allocation:
                    metrics['market_diversification'] = len(market_allocation)
                    metrics['max_market_weight'] = max(market_allocation.values()) if market_allocation else 0

            # 변동성 (일일 손익의 표준편차)
            if len(self.daily_pnl_history) >= 5:
                daily_returns = [day['pnl_pct'] for day in self.daily_pnl_history[-30:]]
                metrics['volatility_30d'] = self._calculate_std_dev(daily_returns)

            return metrics

        except Exception as e:
            self.log_error(f"위험도 지표 계산 실패: {e}")
            return {}

    async def _calculate_performance_metrics(self) -> Dict[str, float]:
        """성과 지표 계산"""
        try:
            metrics = {}

            if not self.daily_pnl_history:
                return metrics

            # 최근 30일 성과
            recent_data = self.daily_pnl_history[-30:]

            if len(recent_data) >= 7:
                # 7일 수익률
                week_return = sum(day['pnl_pct'] for day in recent_data[-7:])
                metrics['return_7d'] = week_return

            if len(recent_data) >= 30:
                # 30일 수익률
                month_return = sum(day['pnl_pct'] for day in recent_data)
                metrics['return_30d'] = month_return

                # 승률 계산
                winning_days = sum(1 for day in recent_data if day['pnl'] > 0)
                metrics['win_rate_30d'] = (winning_days / len(recent_data)) * 100

            # 최대 손실일
            if recent_data:
                max_loss = min(day['pnl'] for day in recent_data)
                metrics['max_loss_30d'] = max_loss

                max_gain = max(day['pnl'] for day in recent_data)
                metrics['max_gain_30d'] = max_gain

            return metrics

        except Exception as e:
            self.log_error(f"성과 지표 계산 실패: {e}")
            return {}

    async def _record_daily_pnl(self) -> None:
        """일별 손익 기록"""
        try:
            if not self.current_portfolio:
                return

            today = datetime.now().date()

            # 오늘 데이터가 이미 있는지 확인
            if self.daily_pnl_history and self.daily_pnl_history[-1]['date'] == today.isoformat():
                # 오늘 데이터 업데이트
                self.daily_pnl_history[-1].update({
                    'pnl': self.current_portfolio.day_pnl,
                    'pnl_pct': self.current_portfolio.day_pnl_pct,
                    'total_value': self.current_portfolio.total_value,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                # 새로운 일자 데이터 추가
                daily_record = {
                    'date': today.isoformat(),
                    'pnl': self.current_portfolio.day_pnl,
                    'pnl_pct': self.current_portfolio.day_pnl_pct,
                    'total_value': self.current_portfolio.total_value,
                    'position_count': self.current_portfolio.get_position_count(),
                    'timestamp': datetime.now().isoformat()
                }

                self.daily_pnl_history.append(daily_record)

                # 최대 90일 히스토리 유지
                if len(self.daily_pnl_history) > 90:
                    self.daily_pnl_history = self.daily_pnl_history[-90:]

        except Exception as e:
            self.log_error(f"일별 손익 기록 실패: {e}")

    def _is_data_stale(self) -> bool:
        """데이터 만료 여부 확인"""
        if not self.last_update_time:
            return True

        elapsed = datetime.now() - self.last_update_time
        return elapsed.total_seconds() > self.update_interval

    def _get_market_type(self, symbol: str) -> MarketType:
        """심볼로 시장 유형 판단"""
        nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMZN']
        if symbol in nasdaq_symbols:
            return MarketType.NASDAQ
        else:
            return MarketType.NYSE

    def _get_sector(self, symbol: str) -> str:
        """심볼로 섹터 판단 (시뮬레이션)"""
        sector_map = {
            'AAPL': 'Technology',
            'MSFT': 'Technology',
            'GOOGL': 'Technology',
            'TSLA': 'Automotive',
            'NVDA': 'Technology'
        }
        return sector_map.get(symbol, 'Unknown')

    def _calculate_std_dev(self, values: List[float]) -> float:
        """표준편차 계산"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계"""
        return {
            'account_no': self.account_no,
            'is_virtual': self.is_virtual_account,
            'positions_count': len(self.positions),
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'portfolio_value': self.current_portfolio.total_value if self.current_portfolio else 0,
            'daily_pnl_records': len(self.daily_pnl_history),
            **self.get_health_status()
        }

    # IAccountAnalysisService 인터페이스 구현
    async def get_holdings(self) -> List[Dict]:
        """보유 종목 조회 (오케스트레이터 호환 형식)"""
        try:
            holdings = []
            for symbol, position in self.positions.items():
                holdings.append({
                    'ticker': symbol,
                    'symbol': symbol,
                    'StockCode': symbol,
                    'quantity': position.quantity,
                    'avg_price': position.avg_price,
                    'current_price': position.current_price,
                    'market_value': position.market_value,
                    'unrealized_pnl': position.unrealized_pnl,
                    'unrealized_pnl_pct': position.unrealized_pnl_pct
                })
            return holdings
        except Exception as e:
            self.log_error(f"보유 종목 조회 실패: {e}")
            return []

    async def get_holdings_dict(self) -> Dict[str, Dict]:
        """보유 종목 조회 (딕셔너리 형식)"""
        try:
            holdings = {}
            for symbol, position in self.positions.items():
                holdings[symbol] = {
                    'quantity': position.quantity,
                    'avg_price': position.avg_price,
                    'current_price': position.current_price,
                    'market_value': position.market_value,
                    'unrealized_pnl': position.unrealized_pnl,
                    'unrealized_pnl_pct': position.unrealized_pnl_pct
                }
            return holdings
        except Exception as e:
            self.log_error(f"보유 종목 조회 실패: {e}")
            return {}

    async def get_portfolio_value(self) -> Dict[str, float]:
        """포트폴리오 총 가치"""
        try:
            if not self.current_portfolio:
                await self._update_portfolio_data()

            if self.current_portfolio:
                return {
                    'total_value': self.current_portfolio.total_value,
                    'cash': self.current_portfolio.cash,
                    'stock_value': self.current_portfolio.stock_value,
                    'daily_pnl': self.current_portfolio.day_pnl,
                    'total_pnl': self.current_portfolio.total_pnl
                }
            else:
                return {
                    'total_value': 0.0,
                    'cash': 0.0,
                    'stock_value': 0.0,
                    'daily_pnl': 0.0,
                    'total_pnl': 0.0
                }
        except Exception as e:
            self.log_error(f"포트폴리오 가치 조회 실패: {e}")
            return {
                'total_value': 0.0,
                'cash': 0.0,
                'stock_value': 0.0,
                'daily_pnl': 0.0,
                'total_pnl': 0.0
            }

    async def get_available_cash(self) -> float:
        """매수 가능 현금"""
        try:
            if not self.current_portfolio:
                await self._update_portfolio_data()

            if self.current_portfolio:
                return self.current_portfolio.cash
            else:
                return 0.0
        except Exception as e:
            self.log_error(f"매수 가능 현금 조회 실패: {e}")
            return 0.0

    async def refresh_account_data(self) -> bool:
        """계좌 데이터 새로고침"""
        try:
            await self._fetch_account_balance()
            await self._fetch_positions()
            await self._update_portfolio_data()
            self.last_update_time = datetime.now()
            return True
        except Exception as e:
            self.log_error(f"계좌 데이터 새로고침 실패: {e}")
            return False


# 테스트 함수
async def test_account_analysis_service():
    """AccountAnalysisService 테스트"""
    print("\n=== AccountAnalysisService 테스트 시작 ===")

    config = {
        'kis_api': {
            'account_no': '12345678-01',
            'is_virtual': True
        }
    }

    service = AccountAnalysisService(config)

    try:
        # 서비스 시작
        success = await service.start_service()
        print(f"서비스 시작: {'성공' if success else '실패'}")

        # 초기 데이터 로딩 대기
        await asyncio.sleep(2)

        # 포트폴리오 조회
        portfolio = await service.get_current_portfolio()
        if portfolio:
            print(f"\n포트폴리오 정보:")
            print(f"  총 자산: ${portfolio.total_value:,.2f}")
            print(f"  현금: ${portfolio.cash:,.2f}")
            print(f"  주식: ${portfolio.stock_value:,.2f}")
            print(f"  일일 손익: ${portfolio.day_pnl:+,.2f} ({portfolio.day_pnl_pct:+.2f}%)")
            print(f"  보유 종목: {portfolio.get_position_count()}개")

        # 포지션 조회
        positions = await service.get_positions()
        print(f"\n보유 포지션 ({len(positions)}개):")
        for pos in positions:
            print(f"  {pos.symbol}: {pos.quantity}주 @ ${pos.current_price:.2f} "
                  f"(손익: ${pos.unrealized_pnl:+.2f}, {pos.unrealized_pnl_pct:+.2f}%)")

        # 계좌 잔고 조회
        balance = await service.get_account_balance()
        print(f"\n계좌 잔고: {balance}")

        # 포트폴리오 지표 계산
        metrics = await service.calculate_portfolio_metrics()
        print(f"\n포트폴리오 지표:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        # 실시간 가격 업데이트 시뮬레이션
        print("\n실시간 가격 업데이트 테스트 (3초)...")

        from ..models.trading_models import PriceData, MarketType
        import random

        for i in range(3):
            for symbol in ['AAPL', 'MSFT', 'GOOGL']:
                if symbol in service.positions:
                    old_price = service.positions[symbol].current_price
                    new_price = old_price * random.uniform(0.99, 1.01)

                    price_data = PriceData(
                        symbol=symbol,
                        price=new_price,
                        volume=random.randint(10000, 100000),
                        timestamp=datetime.now(),
                        change=new_price - old_price,
                        change_pct=((new_price - old_price) / old_price) * 100,
                        market=MarketType.NASDAQ
                    )

                    service.set_price_data(symbol, price_data)

            await asyncio.sleep(1)

        # 업데이트된 포트폴리오 확인
        updated_portfolio = await service.get_current_portfolio()
        if updated_portfolio:
            print(f"\n업데이트된 포트폴리오:")
            print(f"  총 자산: ${updated_portfolio.total_value:,.2f}")
            print(f"  일일 손익: ${updated_portfolio.day_pnl:+,.2f}")

        # 서비스 통계
        stats = service.get_service_stats()
        print(f"\n서비스 통계: {stats}")

        # 서비스 중지
        await service.stop_service()
        print("\n서비스 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_account_analysis_service())