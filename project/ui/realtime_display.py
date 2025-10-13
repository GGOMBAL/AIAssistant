"""
Real-time Display Component

실시간 거래 데이터 및 시스템 상태를 표시하는 UI 컴포넌트
콘솔 기반 실시간 업데이트 화면 제공
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict

from ..models.trading_models import PriceData, Portfolio, SystemStatus, TradingSignal


class RealTimeDisplay:
    """실시간 화면 표시 클래스"""

    def __init__(self):
        # 화면 관리
        self.is_active = False
        self.display_thread = None
        self.update_interval = 1.0  # 1초마다 업데이트

        # 데이터 저장
        self.price_data: Dict[str, PriceData] = {}
        self.portfolio: Optional[Portfolio] = None
        self.system_status: Optional[SystemStatus] = None
        self.recent_signals: deque = deque(maxlen=20)
        self.recent_orders: deque = deque(maxlen=10)

        # 통계 데이터
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))  # 1분간 히스토리
        self.update_count = 0
        self.last_update_time = None

        # 화면 설정
        self.display_mode = "full"  # full, compact, minimal
        self.selected_symbols = []  # 화면에 표시할 심볼들

        # 색상 코드 (ANSI)
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'gray': '\033[90m'
        }

    def start_display(self, symbols: List[str] = None, mode: str = "full") -> None:
        """실시간 화면 표시 시작"""
        if self.is_active:
            return

        self.display_mode = mode
        self.selected_symbols = symbols or []
        self.is_active = True

        # 별도 스레드에서 화면 업데이트
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()

        print(f"\n{self.colors['green']}=== 실시간 거래 모니터 시작 ==={self.colors['reset']}")
        print(f"표시 모드: {mode}")
        if symbols:
            print(f"감시 종목: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}")

    def stop_display(self) -> None:
        """실시간 화면 표시 중지"""
        if not self.is_active:
            return

        self.is_active = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2)

        print(f"\n{self.colors['yellow']}=== 실시간 모니터 중지 ==={self.colors['reset']}")

    def update_symbols(self, new_symbols: List[str]) -> None:
        """디스플레이할 종목 동적 업데이트"""
        self.selected_symbols = new_symbols
        print(f"\n{self.colors['blue']}[DATA] 모니터링 종목 업데이트: {', '.join(new_symbols[:10])}{'...' if len(new_symbols) > 10 else ''}{self.colors['reset']}")

    def update_candidate_data(self, candidate_data: Dict[str, Any]) -> None:
        """후보종목 데이터 업데이트"""
        self.candidate_data = candidate_data

    def update_price(self, price_data: PriceData) -> None:
        """가격 데이터 업데이트"""
        symbol = price_data.symbol
        self.price_data[symbol] = price_data
        self.price_history[symbol].append({
            'price': price_data.price,
            'time': price_data.timestamp,
            'volume': price_data.volume
        })

        self.update_count += 1
        self.last_update_time = datetime.now()

    def update_portfolio(self, portfolio: Portfolio) -> None:
        """포트폴리오 데이터 업데이트"""
        self.portfolio = portfolio

    def update_system_status(self, status: SystemStatus) -> None:
        """시스템 상태 업데이트"""
        self.system_status = status

    def add_signal(self, signal: TradingSignal) -> None:
        """매매 신호 추가"""
        self.recent_signals.appendleft({
            'signal': signal,
            'time': datetime.now()
        })

    def add_order_result(self, order_result: Dict[str, Any]) -> None:
        """주문 결과 추가"""
        self.recent_orders.appendleft({
            'result': order_result,
            'time': datetime.now()
        })

    def _display_loop(self) -> None:
        """화면 업데이트 루프"""
        while self.is_active:
            try:
                self._update_screen()
                time.sleep(self.update_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(1)

    def _update_screen(self) -> None:
        """화면 업데이트"""
        # 화면 클리어 (Windows/Linux 호환)
        os.system('cls' if os.name == 'nt' else 'clear')

        # 헤더 표시
        self._print_header()

        # 모드별 화면 표시
        if self.display_mode == "full":
            self._print_full_display()
        elif self.display_mode == "compact":
            self._print_compact_display()
        else:
            self._print_minimal_display()

        # 푸터 표시
        self._print_footer()

    def _print_header(self) -> None:
        """헤더 출력"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"{self.colors['bold']}{self.colors['cyan']}")
        print("=" * 100)
        print(f"  [MONITOR] AUTO TRADE SYSTEM - REAL TIME MONITOR  |  {now}")
        print("=" * 100)
        print(f"{self.colors['reset']}")

    def _print_full_display(self) -> None:
        """전체 화면 모드"""
        # 시스템 상태
        self._print_system_status()
        print()

        # 포트폴리오 요약
        self._print_portfolio_summary()
        print()

        # 후보종목 상세 정보
        self._print_candidates_detail()
        print()

        # 실시간 가격 정보
        self._print_price_data()
        print()

        # 최근 신호
        self._print_recent_signals()
        print()

        # 최근 주문
        self._print_recent_orders()

    def _print_compact_display(self) -> None:
        """간단 화면 모드"""
        # 시스템 상태 (한 줄)
        if self.system_status:
            status_color = self.colors['green'] if self.system_status.is_trading_active else self.colors['red']
            trading_status = "ACTIVE" if self.system_status.is_trading_active else "INACTIVE"
            market_status = "OPEN" if self.system_status.is_market_open else "CLOSED"

            print(f"Status: {status_color}{trading_status}{self.colors['reset']} | "
                  f"Market: {market_status} | "
                  f"WebSocket: {'ON' if self.system_status.websocket_connected else 'OFF'}")

        print()

        # 포트폴리오 요약 (한 줄)
        if self.portfolio:
            pnl_color = self.colors['green'] if self.portfolio.day_pnl >= 0 else self.colors['red']
            print(f"Portfolio: ${self.portfolio.total_value:,.2f} | "
                  f"Day P&L: {pnl_color}{self.portfolio.day_pnl:+.2f} "
                  f"({self.portfolio.day_pnl_pct:+.2f}%){self.colors['reset']}")

        print()

        # 감시 종목 가격 (테이블 형태)
        self._print_price_table_compact()

    def _print_minimal_display(self) -> None:
        """최소 화면 모드"""
        # 핵심 정보만 표시
        if self.portfolio:
            pnl_color = self.colors['green'] if self.portfolio.day_pnl >= 0 else self.colors['red']
            print(f"P&L: {pnl_color}{self.portfolio.day_pnl:+.2f} ({self.portfolio.day_pnl_pct:+.2f}%){self.colors['reset']}")

        # 최근 신호 1개
        if self.recent_signals:
            latest_signal = self.recent_signals[0]['signal']
            signal_color = self.colors['green'] if latest_signal.is_buy_signal() else self.colors['red']
            # Handle signal_type being either enum or string
            signal_type_str = latest_signal.signal_type.value if hasattr(latest_signal.signal_type, 'value') else str(latest_signal.signal_type)
            print(f"Latest: {signal_color}{latest_signal.symbol} {signal_type_str}{self.colors['reset']}")

    def _print_system_status(self) -> None:
        """시스템 상태 출력"""
        if not self.system_status:
            print(f"{self.colors['gray']}System Status: No data{self.colors['reset']}")
            return

        status = self.system_status

        # 상태별 색상
        trading_color = self.colors['green'] if status.is_trading_active else self.colors['red']
        market_color = self.colors['green'] if status.is_market_open else self.colors['yellow']
        ws_color = self.colors['green'] if status.websocket_connected else self.colors['red']

        print(f"{self.colors['bold']}[SYSTEM] STATUS{self.colors['reset']}")
        print(f"  Trading: {trading_color}{'ACTIVE' if status.is_trading_active else 'INACTIVE'}{self.colors['reset']}")
        print(f"  Market: {market_color}{'OPEN' if status.is_market_open else 'CLOSED'}{self.colors['reset']}")
        print(f"  WebSocket: {ws_color}{'CONNECTED' if status.websocket_connected else 'DISCONNECTED'}{self.colors['reset']}")

        if status.uptime:
            hours = int(status.uptime / 3600)
            minutes = int((status.uptime % 3600) / 60)
            print(f"  Uptime: {hours:02d}:{minutes:02d}")

        if status.orders_today > 0:
            success_rate = status.get_success_rate() * 100
            print(f"  Orders Today: {status.orders_today} (Success: {success_rate:.1f}%)")

    def _print_portfolio_summary(self) -> None:
        """포트폴리오 요약 출력 (실제 계좌 데이터 기반, 원화 환산 포함)"""
        if not self.portfolio:
            print(f"{self.colors['gray']}Portfolio: No data{self.colors['reset']}")
            return

        p = self.portfolio

        # 원화 환산을 위한 환율
        usd_to_krw = 1350

        # P&L 색상
        day_pnl_color = self.colors['green'] if p.day_pnl >= 0 else self.colors['red']
        total_pnl_color = self.colors['green'] if p.total_pnl >= 0 else self.colors['red']

        print(f"{self.colors['bold']}[PORTFOLIO] Real Account{self.colors['reset']}")
        print(f"  Total Value: ${p.total_value:,.2f} (₩{p.total_value * usd_to_krw:,.0f})")
        print(f"  Cash: ${p.cash:,.2f} (₩{p.cash * usd_to_krw:,.0f}) | Stock: ${p.stock_value:,.2f} (₩{p.stock_value * usd_to_krw:,.0f})")
        print(f"  Day P&L: {day_pnl_color}{p.day_pnl:+,.2f} (₩{p.day_pnl * usd_to_krw:+,.0f}) ({p.day_pnl_pct:+.2f}%){self.colors['reset']}")
        print(f"  Total P&L: {total_pnl_color}{p.total_pnl:+,.2f} (₩{p.total_pnl * usd_to_krw:+,.0f}) ({p.total_pnl_pct:+.2f}%){self.colors['reset']}")

        # 보유종목 상세 정보 (손절가 및 갭 포함)
        if hasattr(p, 'positions') and p.positions:
            print(f"  Holdings: {len(p.positions)} positions")
            self._print_holdings_detail(p.positions)
        else:
            print(f"  Holdings: 0 positions")

    def _print_holdings_detail(self, positions: Dict) -> None:
        """보유종목 상세 정보 (손절가 및 갭 포함)"""
        print(f"\n  {self.colors['bold']}[HOLDINGS] DETAIL{self.colors['reset']}")
        print(f"  {'Symbol':<8} {'Qty':<6} {'Price':<8} {'LossCut':<8} {'Gap%':<7} {'P&L%':<7}")
        print(f"  {'-'*8} {'-'*6} {'-'*8} {'-'*8} {'-'*7} {'-'*7}")

        for symbol, position in positions.items():
            current_price = position.current_price if hasattr(position, 'current_price') else 0
            qty = position.quantity if hasattr(position, 'quantity') else 0

            # 손절가 계산 (평균가의 95% 기본값)
            avg_price = position.avg_price if hasattr(position, 'avg_price') else current_price
            loss_cut_price = avg_price * 0.95  # 5% 손절

            # 손절가와 현재 가격 갭 계산
            if current_price > 0 and loss_cut_price > 0:
                gap_pct = ((current_price - loss_cut_price) / loss_cut_price) * 100
                gap_color = self.colors['green'] if gap_pct > 0 else self.colors['red']
            else:
                gap_pct = 0
                gap_color = self.colors['gray']

            # P&L 퍼센트
            pnl_pct = position.unrealized_pnl_pct if hasattr(position, 'unrealized_pnl_pct') else 0
            pnl_color = self.colors['green'] if pnl_pct >= 0 else self.colors['red']

            print(f"  {symbol:<8} {qty:<6} ${current_price:<7.2f} ${loss_cut_price:<7.2f} "
                  f"{gap_color}{gap_pct:+6.1f}{self.colors['reset']} "
                  f"{pnl_color}{pnl_pct:+6.1f}{self.colors['reset']}")

    def _print_candidates_detail(self) -> None:
        """후보종목 상세 정보 (목표가 및 갭 포함)"""
        # 후보종목 데이터가 있다면 표시
        if hasattr(self, 'candidate_data') and self.candidate_data:
            print(f"\n  {self.colors['bold']}[CANDIDATES] DETAIL{self.colors['reset']}")
            print(f"  {'Symbol':<8} {'Current':<8} {'Target':<8} {'Gap%':<7} {'Signal':<8}")
            print(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*7} {'-'*8}")

            for symbol, candidate in self.candidate_data.items():
                current_price = self.price_data.get(symbol, {}).get('price', 0) if hasattr(self, 'price_data') else 0
                target_price = candidate.get('target_price', current_price * 1.1)  # 10% 상승 목표 기본값

                # 목표가와 현재 가격 갭 계산
                if current_price > 0 and target_price > 0:
                    gap_pct = ((target_price - current_price) / current_price) * 100
                    gap_color = self.colors['green'] if gap_pct > 0 else self.colors['red']
                else:
                    gap_pct = 0
                    gap_color = self.colors['gray']

                signal_type = candidate.get('signal_type', 'BUY')
                signal_color = self.colors['green'] if signal_type == 'BUY' else self.colors['red']

                print(f"  {symbol:<8} ${current_price:<7.2f} ${target_price:<7.2f} "
                      f"{gap_color}{gap_pct:+6.1f}{self.colors['reset']} "
                      f"{signal_color}{signal_type:<8}{self.colors['reset']}")

    def _print_price_data(self) -> None:
        """실시간 가격 데이터 출력"""
        if not self.price_data:
            print(f"{self.colors['gray']}Price Data: No data{self.colors['reset']}")
            return

        print(f"{self.colors['bold']}[PRICES] REAL-TIME{self.colors['reset']}")

        # 표시할 종목 선택
        symbols_to_show = self.selected_symbols if self.selected_symbols else list(self.price_data.keys())
        symbols_to_show = symbols_to_show[:10]  # 최대 10개

        # 테이블 헤더
        print(f"  {'Symbol':<8} {'Price':<10} {'Change':<12} {'Volume':<12} {'Time':<8}")
        print(f"  {'-'*8} {'-'*10} {'-'*12} {'-'*12} {'-'*8}")

        # 가격 데이터 출력
        for symbol in symbols_to_show:
            if symbol in self.price_data:
                data = self.price_data[symbol]

                # 변동 색상
                change_color = self.colors['reset']
                if data.change:
                    change_color = self.colors['green'] if data.change > 0 else self.colors['red']

                change_str = f"{data.change:+.2f}" if data.change else "N/A"
                change_pct_str = f"({data.change_pct:+.2f}%)" if data.change_pct else ""

                time_str = data.timestamp.strftime("%H:%M:%S")

                print(f"  {symbol:<8} ${data.price:<9.2f} "
                      f"{change_color}{change_str:<6} {change_pct_str:<5}{self.colors['reset']} "
                      f"{data.volume:<12,} {time_str}")

    def _print_price_table_compact(self) -> None:
        """간단한 가격 테이블"""
        if not self.price_data:
            return

        symbols_to_show = self.selected_symbols if self.selected_symbols else list(self.price_data.keys())
        symbols_to_show = symbols_to_show[:5]  # 최대 5개

        for symbol in symbols_to_show:
            if symbol in self.price_data:
                data = self.price_data[symbol]
                change_color = self.colors['green'] if data.change and data.change > 0 else self.colors['red']
                change_str = f"{data.change:+.2f}" if data.change else "0.00"

                print(f"{symbol}: ${data.price:.2f} {change_color}{change_str}{self.colors['reset']}")

    def _print_recent_signals(self) -> None:
        """최근 신호 출력"""
        if not self.recent_signals:
            print(f"{self.colors['gray']}Recent Signals: No data{self.colors['reset']}")
            return

        print(f"{self.colors['bold']}[SIGNALS] RECENT{self.colors['reset']}")

        for i, signal_data in enumerate(list(self.recent_signals)[:5]):  # 최근 5개
            signal = signal_data['signal']
            time_ago = datetime.now() - signal_data['time']

            # 신호 타입별 색상
            if signal.is_buy_signal():
                signal_color = self.colors['green']
                signal_icon = "[BUY]"
            elif signal.is_sell_signal():
                signal_color = self.colors['red']
                signal_icon = "[SELL]"
            else:
                signal_color = self.colors['yellow']
                signal_icon = "[HOLD]"

            time_str = f"{int(time_ago.total_seconds())}s ago"

            # Handle signal_type being either enum or string
            signal_type_str = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)

            print(f"  {signal_icon} {signal.symbol:<8} "
                  f"{signal_color}{signal_type_str:<12}{self.colors['reset']} "
                  f"${signal.price:.2f} ({signal.confidence:.2f}) {time_str}")

    def _print_recent_orders(self) -> None:
        """최근 주문 출력"""
        if not self.recent_orders:
            print(f"{self.colors['gray']}Recent Orders: No data{self.colors['reset']}")
            return

        print(f"{self.colors['bold']}[ORDERS] RECENT{self.colors['reset']}")

        for i, order_data in enumerate(list(self.recent_orders)[:3]):  # 최근 3개
            order = order_data['result']
            time_ago = datetime.now() - order_data['time']

            # 상태별 색상
            status = order.get('status', 'UNKNOWN')
            if status == 'FILLED':
                status_color = self.colors['green']
                status_icon = "[OK]"
            elif status in ['CANCELLED', 'REJECTED']:
                status_color = self.colors['red']
                status_icon = "[FAIL]"
            else:
                status_color = self.colors['yellow']
                status_icon = "⏳"

            symbol = order.get('symbol', 'N/A')
            order_type = order.get('order_type', 'N/A')
            quantity = order.get('quantity', 0)
            price = order.get('price', 0)

            time_str = f"{int(time_ago.total_seconds())}s ago"

            print(f"  {status_icon} {symbol:<8} {order_type:<4} {quantity:>6} @ ${price:.2f} "
                  f"{status_color}{status}{self.colors['reset']} {time_str}")

    def _print_footer(self) -> None:
        """푸터 출력"""
        now = datetime.now()

        print(f"\n{self.colors['gray']}")
        print("-" * 100)

        # 업데이트 정보
        if self.last_update_time:
            update_ago = now - self.last_update_time
            print(f"Last Update: {update_ago.total_seconds():.1f}s ago | "
                  f"Updates: {self.update_count} | "
                  f"Mode: {self.display_mode}")

        # 조작 안내
        print("Press Ctrl+C to stop monitoring")

        print(f"{self.colors['reset']}")

    def set_display_mode(self, mode: str) -> None:
        """화면 표시 모드 변경"""
        if mode in ["full", "compact", "minimal"]:
            self.display_mode = mode
            print(f"Display mode changed to: {mode}")

    def set_selected_symbols(self, symbols: List[str]) -> None:
        """표시할 심볼 설정"""
        self.selected_symbols = symbols[:20]  # 최대 20개
        print(f"Display symbols set: {', '.join(self.selected_symbols[:5])}{'...' if len(symbols) > 5 else ''}")

    def get_display_stats(self) -> Dict[str, Any]:
        """화면 표시 통계"""
        return {
            'is_active': self.is_active,
            'display_mode': self.display_mode,
            'update_count': self.update_count,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'price_data_count': len(self.price_data),
            'selected_symbols_count': len(self.selected_symbols),
            'recent_signals_count': len(self.recent_signals),
            'recent_orders_count': len(self.recent_orders)
        }


# 테스트 함수
async def test_realtime_display():
    """RealTimeDisplay 테스트"""
    print("\n=== RealTimeDisplay 테스트 시작 ===")

    display = RealTimeDisplay()

    # 테스트 데이터 생성
    import random
    from datetime import datetime

    # 샘플 포트폴리오
    from ..models.trading_models import Portfolio, PortfolioPosition, SystemStatus, TradingSignal, SignalType, MarketType

    portfolio = Portfolio(
        total_value=100000.0,
        cash=20000.0,
        stock_value=80000.0,
        day_pnl=2500.0,
        total_pnl=15000.0,
        day_pnl_pct=2.5,
        total_pnl_pct=15.0
    )

    # 시스템 상태
    system_status = SystemStatus(
        is_trading_active=True,
        is_market_open=True,
        websocket_connected=True,
        orders_today=10,
        successful_orders=8,
        uptime=3600
    )

    # 테스트 심볼
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    try:
        # 화면 시작
        display.start_display(test_symbols, "full")

        # 데이터 업데이트
        display.update_portfolio(portfolio)
        display.update_system_status(system_status)

        # 가격 데이터 시뮬레이션
        base_prices = {'AAPL': 174.25, 'MSFT': 338.92, 'GOOGL': 125.87, 'TSLA': 248.33, 'NVDA': 421.45}

        print("\n실시간 가격 업데이트 시뮬레이션 (10초)...")

        for i in range(10):
            for symbol in test_symbols:
                base_price = base_prices[symbol]
                change = random.uniform(-0.02, 0.02)
                new_price = base_price * (1 + change)

                price_data = PriceData(
                    symbol=symbol,
                    price=new_price,
                    volume=random.randint(10000, 100000),
                    timestamp=datetime.now(),
                    change=new_price - base_price,
                    change_pct=change * 100,
                    market=MarketType.NASDAQ
                )

                display.update_price(price_data)
                base_prices[symbol] = new_price

            # 가끔 신호 생성
            if i % 3 == 0:
                signal = TradingSignal(
                    symbol=random.choice(test_symbols),
                    signal_type=random.choice([SignalType.BUY, SignalType.SELL, SignalType.HOLD]),
                    confidence=random.uniform(0.6, 0.9),
                    price=random.uniform(100, 400),
                    timestamp=datetime.now(),
                    strategy_name="TestStrategy"
                )
                display.add_signal(signal)

            await asyncio.sleep(1)

        # 화면 모드 테스트
        print("\n화면 모드 변경 테스트...")
        display.set_display_mode("compact")
        await asyncio.sleep(3)

        display.set_display_mode("minimal")
        await asyncio.sleep(3)

        # 통계 출력
        stats = display.get_display_stats()
        print(f"\n화면 표시 통계: {stats}")

        # 화면 중지
        display.stop_display()
        print("\n테스트 완료")

    except KeyboardInterrupt:
        print("\n테스트 중단됨")
        display.stop_display()
    except Exception as e:
        print(f"테스트 실패: {e}")
        display.stop_display()

if __name__ == "__main__":
    asyncio.run(test_realtime_display())