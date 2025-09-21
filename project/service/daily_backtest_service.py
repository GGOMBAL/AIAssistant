"""
Daily Backtest Service - Service Layer Implementation
Based on refer/BackTest/TestMakTrade_D.py

Preserves original concept and structure while modernizing architecture
for Service Layer integration in Multi-Agent Trading System.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
import logging

# Import Strategy Layer dependencies
try:
    from Project.strategy.position_sizing_service import PositionSizingService
    STRATEGY_LAYER_AVAILABLE = True
except ImportError:
    print("[DailyBacktest] Strategy Layer not available - using fallback")
    STRATEGY_LAYER_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== ENUMS =====
class TradeType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HALF_SELL = "HALF_SELL"
    WHIPSAW = "WHIPSAW"
    HOLD = "HOLD"


class SellReason(Enum):
    LOSSCUT = "LOSSCUT"
    SIGNAL_SELL = "SIGNAL_SELL"
    HALF_SELL_PROFIT = "HALF_SELL_PROFIT"
    WHIPSAW = "WHIPSAW"


# ===== DATA CLASSES =====
@dataclass
class BacktestConfig:
    """백테스트 설정"""
    initial_cash: float = 100.0  # 초기 현금 (억원)
    max_positions: int = 10      # 최대 보유 종목수
    slippage: float = 0.002      # 슬리피지 (0.2%)
    std_risk: float = 0.05       # 표준 리스크 (5%)
    init_risk: float = 0.03      # 초기 손절 리스크 (3%)
    half_sell_threshold: float = 0.20  # 50% 매도 임계값 (20%)
    half_sell_risk_multiplier: float = 2.0  # 50% 매도 후 리스크 배수
    enable_whipsaw: bool = True        # 휩쏘 처리 활성화
    enable_half_sell: bool = True      # 50% 매도 활성화
    enable_rebuying: bool = True       # 재매수 허용
    message_output: bool = False       # 거래 메시지 출력


@dataclass
class Position:
    """포지션 정보"""
    ticker: str
    balance: float = 0.0           # 투자 금액
    avg_price: float = 0.0         # 평균 단가
    again: float = 1.0             # 누적 수익률
    duration: float = 0.0          # 보유 기간
    losscut_price: float = 0.0     # 손절가
    risk: float = 0.0              # 리스크 레벨

    @property
    def quantity(self) -> float:
        """보유 수량 계산"""
        return self.balance / self.avg_price if self.avg_price > 0 else 0.0

    @property
    def market_value(self) -> float:
        """시장 가치 계산"""
        return self.balance * self.again

    @property
    def unrealized_pnl(self) -> float:
        """미실현 손익"""
        return self.market_value - self.balance


@dataclass
class Trade:
    """거래 기록"""
    ticker: str
    trade_type: TradeType
    quantity: float
    price: float
    timestamp: pd.Timestamp
    reason: Optional[SellReason] = None
    pnl: float = 0.0
    again: float = 1.0
    buy_date: Optional[pd.Timestamp] = None
    buy_price: Optional[float] = None
    holding_days: Optional[float] = None
    risk: Optional[float] = None


@dataclass
class Portfolio:
    """포트폴리오 상태"""
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)

    # 성과 지표
    win_count: float = 0.0
    loss_count: float = 0.0
    win_gain: float = 0.0
    loss_gain: float = 0.0

    @property
    def stock_value(self) -> float:
        """주식 자산 가치"""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """총 자산 가치"""
        return self.cash + self.stock_value

    @property
    def position_count(self) -> int:
        """보유 종목수"""
        return len(self.positions)

    @property
    def cash_ratio(self) -> float:
        """현금 비율"""
        return (self.cash / self.total_value * 100) if self.total_value > 0 else 0.0


@dataclass
class DayTradingResult:
    """일일 거래 결과"""
    date: pd.Timestamp
    trades: List[Trade] = field(default_factory=list)
    portfolio: Optional[Portfolio] = None
    buy_candidates: List[str] = field(default_factory=list)
    sell_candidates: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)


@dataclass
class BacktestResult:
    """백테스트 결과"""
    trades: List[Trade]
    portfolio_history: List[Portfolio]
    daily_results: List[DayTradingResult]
    performance_metrics: Dict[str, float]
    execution_time: float
    config: BacktestConfig


# ===== MAIN SERVICE CLASS =====
class DailyBacktestService:
    """
    일봉 백테스트 서비스
    Based on refer/BackTest/TestMakTrade_D.py - TestTradeD class

    Preserves original logic while modernizing for Service Layer
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize Daily Backtest Service

        Args:
            config: BacktestConfig instance, defaults to standard config
        """
        self.config = config or BacktestConfig()

        # Initialize Strategy Layer connection
        if STRATEGY_LAYER_AVAILABLE:
            self.position_sizing_service = PositionSizingService()
        else:
            self.position_sizing_service = None
            logger.warning("Strategy Layer not available - using fallback calculations")

        # Color codes for output (preserved from original)
        self.CODE = '\033[95m'
        self.NAME = '\033[94m'
        self.COLOR = '\033[91m'
        self.COLOR2 = '\033[92m'
        self.COLOR3 = '\033[93m'
        self.RESET = '\033[0m'

        # Trading state
        self.half_sell_executed = set()  # Track half-sold stocks
        self.trade_count = 0

        logger.info(f"DailyBacktestService initialized with config: {self.config}")

    def run_backtest(self, universe: List[str], df_data: Dict[str, pd.DataFrame],
                    market: str = 'US', area: str = 'US') -> BacktestResult:
        """
        Run daily backtest

        Args:
            universe: List of stock tickers
            df_data: Dictionary of DataFrames with stock data
            market: Market identifier
            area: Area identifier

        Returns:
            BacktestResult with complete analysis
        """
        start_time = datetime.now()
        logger.info(f"Starting daily backtest for {len(universe)} stocks")

        # Data preparation (preserved from original)
        processed_data = self._prepare_data(universe, df_data)
        if processed_data.empty:
            logger.warning("No valid data for backtest")
            return self._create_empty_result()

        # Initialize portfolio
        portfolio = Portfolio(cash=self.config.initial_cash)

        # Run trading simulation
        trades = []
        portfolio_history = []
        daily_results = []

        dates = processed_data.index.values

        for i, date in enumerate(dates):
            if i == 0:
                # First day initialization
                portfolio_history.append(self._copy_portfolio(portfolio))
                continue

            # Execute daily trading
            day_result = self._process_trading_day(
                date=pd.Timestamp(date),
                market_data=self._extract_market_data(processed_data, i),
                previous_data=self._extract_market_data(processed_data, i-1),
                portfolio=portfolio,
                universe=universe
            )

            # Update portfolio and records
            portfolio = day_result.portfolio or portfolio
            trades.extend(day_result.trades)
            daily_results.append(day_result)
            portfolio_history.append(self._copy_portfolio(portfolio))

            # Print daily summary (preserved from original)
            if self.config.message_output or (i % 100 == 0):  # Periodic output
                self._print_daily_summary(date, portfolio, day_result)

        # Calculate performance metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        performance_metrics = self._calculate_performance_metrics(trades, portfolio_history)

        result = BacktestResult(
            trades=trades,
            portfolio_history=portfolio_history,
            daily_results=daily_results,
            performance_metrics=performance_metrics,
            execution_time=execution_time,
            config=self.config
        )

        logger.info(f"Backtest completed in {execution_time:.2f}s with {len(trades)} trades")
        return result

    def _prepare_data(self, universe: List[str], df_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Prepare and validate data for backtest
        Based on TestTradeD.__init__ data preparation logic
        """
        try:
            # Filter columns (preserved from original)
            filtered_cols = [
                'open', 'high', 'low', 'close', 'ADR', 'LossCutPrice', 'TargetPrice',
                'BuySig', 'SellSig', 'signal', 'Type', 'RS_4W', 'Rev_Yoy_Growth',
                'Eps_Yoy_Growth', 'Sector', 'Industry'
            ]

            # Apply column filtering
            for ticker in universe:
                if ticker in df_data and not df_data[ticker].empty:
                    available_cols = [col for col in filtered_cols if col in df_data[ticker].columns]
                    df_data[ticker] = df_data[ticker][available_cols]

            # Handle empty data case
            valid_data = {k: v for k, v in df_data.items() if not v.empty}
            if not valid_data:
                logger.warning("No valid stock data available")
                return pd.DataFrame()

            # Combine dataframes
            df_combined = pd.concat(valid_data.values(), axis=1, keys=valid_data.keys())

            # Create MultiIndex columns (preserved from original logic)
            if not isinstance(df_combined.columns, pd.MultiIndex):
                fields = ['open', 'high', 'low', 'close', 'ADR', 'LossCutPrice', 'TargetPrice',
                         'BuySig', 'SellSig', 'signal', 'RS_4W', 'Rev_Yoy_Growth', 'Eps_Yoy_Growth', 'Type']

                # Length check with warning instead of error
                expected = len(universe) * len(fields)
                actual = df_combined.shape[1]
                if expected != actual:
                    logger.warning(f"Column count mismatch - Expected {expected}, got {actual}")

                # Create MultiIndex with available columns
                try:
                    df_combined.columns = pd.MultiIndex.from_product(
                        [universe, fields],
                        names=['Ticker', 'Field']
                    )
                except ValueError:
                    # Fallback: use available data structure
                    logger.warning("Using fallback column structure")
                    df_combined.columns.names = ['Ticker', 'Field']
            else:
                df_combined.columns.names = ['Ticker', 'Field']

            return df_combined

        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            return pd.DataFrame()

    def _extract_market_data(self, df: pd.DataFrame, index: int) -> Dict[str, Dict[str, float]]:
        """Extract market data for specific date index"""
        if df.empty or index >= len(df):
            return {}

        data = {}
        try:
            date_data = df.iloc[index]
            for ticker in df.columns.levels[0]:
                ticker_data = {}
                for field in df.columns.levels[1]:
                    if (ticker, field) in date_data.index:
                        value = date_data[(ticker, field)]
                        ticker_data[field] = float(value) if pd.notna(value) else 0.0
                data[ticker] = ticker_data
        except Exception as e:
            logger.error(f"Error extracting market data: {e}")

        return data

    def _process_trading_day(self, date: pd.Timestamp, market_data: Dict[str, Dict],
                           previous_data: Dict[str, Dict], portfolio: Portfolio,
                           universe: List[str]) -> DayTradingResult:
        """
        Process single trading day
        Based on TestTradeD.trade_stocks main loop logic
        """
        result = DayTradingResult(date=date)

        try:
            # Filter valid stocks with complete data
            valid_stocks = [ticker for ticker in universe
                          if ticker in market_data and ticker in previous_data
                          and market_data[ticker].get('close', 0) > 0
                          and previous_data[ticker].get('close', 0) > 0]

            if not valid_stocks:
                result.portfolio = portfolio
                return result

            # Process sell orders first (preserved order from original)
            sell_trades = self._execute_sell_orders(portfolio, market_data, previous_data, date)
            result.trades.extend(sell_trades)

            # Process buy orders for available positions
            buy_candidates = self._identify_buy_candidates(valid_stocks, market_data)
            result.buy_candidates = buy_candidates

            buy_trades = self._execute_buy_orders(buy_candidates, portfolio, market_data, date)
            result.trades.extend(buy_trades)

            # Update portfolio
            result.portfolio = portfolio

            return result

        except Exception as e:
            logger.error(f"Error processing trading day {date}: {e}")
            result.portfolio = portfolio
            return result

    def _execute_sell_orders(self, portfolio: Portfolio, market_data: Dict[str, Dict],
                           previous_data: Dict[str, Dict], date: pd.Timestamp) -> List[Trade]:
        """
        Execute sell orders based on conditions
        Preserved logic from TestTradeD.trade_stocks sell processing
        """
        trades = []
        positions_to_remove = []

        for ticker, position in portfolio.positions.items():
            if ticker not in market_data or ticker not in previous_data:
                continue

            current_price = market_data[ticker].get('close', 0)
            previous_close = previous_data[ticker].get('close', 0)
            low_price = market_data[ticker].get('low', current_price)
            open_price = market_data[ticker].get('open', current_price)
            sell_signal = market_data[ticker].get('SellSig', 0)

            if previous_close <= 0:
                continue

            # Check loss cut condition
            if low_price < position.losscut_price:
                sell_price = min(open_price, position.losscut_price) if open_price < position.losscut_price else position.losscut_price
                gain = (sell_price - previous_close) / previous_close

                trade = self._execute_sell_trade(
                    ticker, position, sell_price, gain, date, SellReason.LOSSCUT, portfolio
                )
                trades.append(trade)
                positions_to_remove.append(ticker)

            # Check sell signal condition
            elif sell_signal == 1:
                sell_price = open_price
                gain = (sell_price - previous_close) / previous_close

                trade = self._execute_sell_trade(
                    ticker, position, sell_price, gain, date, SellReason.SIGNAL_SELL, portfolio
                )
                trades.append(trade)
                positions_to_remove.append(ticker)

            # Check half sell condition (preserved from original)
            elif (position.again >= (1 + self.config.half_sell_threshold) and
                  ticker not in self.half_sell_executed and
                  self.config.enable_half_sell):

                sell_price = current_price
                gain = (sell_price - previous_close) / previous_close

                trade = self._execute_half_sell_trade(
                    ticker, position, sell_price, gain, date, portfolio
                )
                trades.append(trade)
                self.half_sell_executed.add(ticker)

            else:
                # Update position for holding (preserved from original remain_stock logic)
                self._update_holding_position(ticker, position, current_price, previous_close)

        # Remove sold positions
        for ticker in positions_to_remove:
            if ticker in portfolio.positions:
                del portfolio.positions[ticker]

        return trades

    def _execute_sell_trade(self, ticker: str, position: Position, sell_price: float,
                          gain: float, date: pd.Timestamp, reason: SellReason,
                          portfolio: Portfolio) -> Trade:
        """Execute a complete sell trade"""
        final_again = position.again * (1 + gain)
        return_cash = position.balance * final_again

        # Update portfolio metrics (preserved from original sell_stock logic)
        portfolio.cash += return_cash

        if final_again >= 1.0:
            portfolio.win_count += 1
            portfolio.win_gain += final_again - 1
        else:
            portfolio.loss_count += 1
            portfolio.loss_gain += 1 - final_again

        trade = Trade(
            ticker=ticker,
            trade_type=TradeType.SELL,
            quantity=position.quantity,
            price=sell_price,
            timestamp=date,
            reason=reason,
            pnl=return_cash - position.balance,
            again=final_again,
            buy_price=position.avg_price,
            holding_days=position.duration,
            risk=position.risk
        )

        self.trade_count += 1

        if self.config.message_output:
            logger.info(f"{date} - SELL: {ticker}, AGAIN: {final_again:.3f}, "
                       f"HoldDays: {position.duration}, Price: {sell_price:.2f}")

        return trade

    def _execute_half_sell_trade(self, ticker: str, position: Position, sell_price: float,
                               gain: float, date: pd.Timestamp, portfolio: Portfolio) -> Trade:
        """Execute half sell trade (preserved from original half_sell_stock logic)"""
        # Calculate half sell metrics
        half_gain = position.again * (1 + gain)
        half_return_cash = position.balance * 0.5 * half_gain

        # Update portfolio
        portfolio.cash += half_return_cash
        portfolio.win_count += 0.5  # Half position win
        portfolio.win_gain += (half_gain - 1) * 0.5

        # Update position (keep remaining 50%)
        position.balance *= 0.5
        position.again = half_gain
        position.risk *= self.config.half_sell_risk_multiplier  # Increase risk for remaining position

        trade = Trade(
            ticker=ticker,
            trade_type=TradeType.HALF_SELL,
            quantity=position.quantity * 0.5,
            price=sell_price,
            timestamp=date,
            reason=SellReason.HALF_SELL_PROFIT,
            pnl=half_return_cash - position.balance,
            again=half_gain,
            buy_price=position.avg_price,
            holding_days=position.duration,
            risk=position.risk
        )

        if self.config.message_output:
            logger.info(f"{date} - HALF SELL: {ticker}, AGAIN: {half_gain:.3f}, "
                       f"NewRisk: {position.risk:.3f}")

        return trade

    def _update_holding_position(self, ticker: str, position: Position,
                               current_price: float, previous_close: float):
        """Update position for holding stocks (preserved from remain_stock logic)"""
        if previous_close > 0:
            daily_gain = (current_price - previous_close) / previous_close
            position.again *= (1 + daily_gain)

        position.duration += 1

        # Update loss cut price based on trailing stop (simplified version)
        if hasattr(self.position_sizing_service, 'calculate_losscut_price'):
            try:
                losscut_result = self.position_sizing_service.calculate_losscut_price(
                    position.again, position.losscut_price, position.avg_price, position.risk
                )
                position.losscut_price = losscut_result.get('new_losscut_price', position.losscut_price)
            except Exception:
                # Fallback: simple trailing stop
                if position.again > 1.1:  # 10% profit
                    min_losscut = position.avg_price * (1 + (position.again - 1) * 0.5)
                    position.losscut_price = max(position.losscut_price, min_losscut)

    def _identify_buy_candidates(self, valid_stocks: List[str], market_data: Dict[str, Dict]) -> List[str]:
        """Identify buy candidates based on signals"""
        candidates = []
        for ticker in valid_stocks:
            buy_signal = market_data[ticker].get('BuySig', 0)
            signal = market_data[ticker].get('signal', 0)

            if buy_signal == 1 or signal == 1:
                candidates.append(ticker)

        return candidates

    def _execute_buy_orders(self, candidates: List[str], portfolio: Portfolio,
                          market_data: Dict[str, Dict], date: pd.Timestamp) -> List[Trade]:
        """Execute buy orders for candidates"""
        trades = []
        available_slots = self.config.max_positions - portfolio.position_count

        if available_slots <= 0 or not candidates:
            return trades

        # Process candidates (simplified version of original complex logic)
        for ticker in candidates[:available_slots]:
            if ticker in portfolio.positions:
                continue  # Already holding

            trade = self._execute_buy_trade(ticker, portfolio, market_data[ticker], date)
            if trade:
                trades.append(trade)

        return trades

    def _execute_buy_trade(self, ticker: str, portfolio: Portfolio,
                         ticker_data: Dict[str, float], date: pd.Timestamp) -> Optional[Trade]:
        """Execute a buy trade"""
        try:
            target_price = ticker_data.get('TargetPrice', 0)
            open_price = ticker_data.get('open', 0)
            high_price = ticker_data.get('high', 0)
            low_price = ticker_data.get('low', 0)
            close_price = ticker_data.get('close', 0)
            adr = ticker_data.get('ADR', 5.0)

            if target_price <= 0 or open_price <= 0:
                return None

            # Determine entry price (preserved from original logic)
            if target_price >= open_price and target_price <= high_price:
                entry_price = target_price
            elif target_price < open_price:
                entry_price = open_price
            else:
                entry_price = open_price

            # Apply slippage
            entry_price *= (1 + self.config.slippage)

            # Calculate position size (simplified version)
            position_ratio = self._calculate_position_ratio(adr)
            investment_amount = portfolio.total_value * position_ratio

            # Check if we have enough cash
            if investment_amount > portfolio.cash:
                investment_amount = portfolio.cash * 0.9  # Use 90% of available cash

            if investment_amount < portfolio.total_value * 0.01:  # Minimum 1%
                return None

            # Calculate loss cut price
            losscut_price = entry_price * (1 - self.config.init_risk)

            # Check for whipsaw condition (preserved from original)
            daily_gain = (close_price - entry_price) / entry_price if entry_price > 0 else 0
            low_gain = (low_price - entry_price) / entry_price if entry_price > 0 else 0
            cut_gain = (losscut_price - entry_price) / entry_price if entry_price > 0 else 0

            if self.config.enable_whipsaw and low_gain < cut_gain:
                # Whipsaw condition - immediate loss cut
                return self._execute_whipsaw_trade(ticker, entry_price, daily_gain, date, portfolio, investment_amount)

            # Normal buy execution
            position = Position(
                ticker=ticker,
                balance=investment_amount,
                avg_price=entry_price,
                again=1 + daily_gain,
                duration=1,
                losscut_price=losscut_price,
                risk=self.config.std_risk
            )

            portfolio.positions[ticker] = position
            portfolio.cash -= investment_amount

            trade = Trade(
                ticker=ticker,
                trade_type=TradeType.BUY,
                quantity=position.quantity,
                price=entry_price,
                timestamp=date,
                pnl=0.0,
                again=1 + daily_gain
            )

            self.trade_count += 1

            if self.config.message_output:
                logger.info(f"{date} - BUY: {ticker}, Price: {entry_price:.2f}, "
                           f"Amount: {investment_amount:.1f}")

            return trade

        except Exception as e:
            logger.error(f"Error executing buy trade for {ticker}: {e}")
            return None

    def _execute_whipsaw_trade(self, ticker: str, entry_price: float, daily_gain: float,
                             date: pd.Timestamp, portfolio: Portfolio, investment_amount: float) -> Trade:
        """Execute whipsaw trade (immediate buy and sell)"""
        # Whipsaw: immediate loss
        whipsaw_again = 1 + daily_gain
        portfolio.loss_count += 1
        portfolio.loss_gain += abs(daily_gain) if daily_gain < 0 else 0

        trade = Trade(
            ticker=ticker,
            trade_type=TradeType.WHIPSAW,
            quantity=investment_amount / entry_price,
            price=entry_price,
            timestamp=date,
            reason=SellReason.WHIPSAW,
            pnl=investment_amount * daily_gain,
            again=whipsaw_again
        )

        if self.config.message_output:
            logger.info(f"{date} - WHIPSAW: {ticker}, AGAIN: {whipsaw_again:.3f}")

        return trade

    def _calculate_position_ratio(self, adr: float) -> float:
        """Calculate position ratio based on ADR (simplified version)"""
        base_ratio = 0.2  # 20% default

        # Adjust based on volatility (ADR)
        if adr >= 5:
            return base_ratio / 2  # Reduce for high volatility
        elif adr <= 2:
            return base_ratio * 1.5  # Increase for low volatility
        else:
            return base_ratio

    def _copy_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Create a deep copy of portfolio for history"""
        new_positions = {}
        for ticker, pos in portfolio.positions.items():
            new_positions[ticker] = Position(
                ticker=pos.ticker,
                balance=pos.balance,
                avg_price=pos.avg_price,
                again=pos.again,
                duration=pos.duration,
                losscut_price=pos.losscut_price,
                risk=pos.risk
            )

        return Portfolio(
            cash=portfolio.cash,
            positions=new_positions,
            win_count=portfolio.win_count,
            loss_count=portfolio.loss_count,
            win_gain=portfolio.win_gain,
            loss_gain=portfolio.loss_gain
        )

    def _print_daily_summary(self, date: pd.Timestamp, portfolio: Portfolio, day_result: DayTradingResult):
        """Print daily summary (preserved from original output format)"""
        win_loss_ratio = self._calculate_win_loss_ratio(portfolio)
        win_loss_gain = self._calculate_win_loss_gain(portfolio)

        balance_str = f"{self.COLOR}{portfolio.total_value:.2f}{self.RESET}"
        cash_ratio_str = f"{self.COLOR3}{portfolio.cash_ratio:.2f}{self.RESET}"

        print(f"{date.strftime('%Y-%m-%d')} - Trades: {len(day_result.trades)}, "
              f"W/L Ratio: {self.CODE}{win_loss_ratio:.2f}{self.RESET}, "
              f"W/L Gain: {self.NAME}{win_loss_gain:.2f}{self.RESET}, "
              f"Positions: {portfolio.position_count}/{self.config.max_positions}, "
              f"Balance: {balance_str}, Cash: {cash_ratio_str}%, "
              f"Candidates: {len(day_result.buy_candidates)}")

    def _calculate_win_loss_ratio(self, portfolio: Portfolio) -> float:
        """Calculate win/loss ratio"""
        total_trades = portfolio.win_count + portfolio.loss_count
        return portfolio.win_count / total_trades if total_trades > 0 else 0.0

    def _calculate_win_loss_gain(self, portfolio: Portfolio) -> float:
        """Calculate average win vs loss gain"""
        avg_win = portfolio.win_gain / portfolio.win_count if portfolio.win_count > 0 else 0
        avg_loss = portfolio.loss_gain / portfolio.loss_count if portfolio.loss_count > 0 else 0
        return avg_win / avg_loss if avg_loss > 0 else 0.0

    def _calculate_performance_metrics(self, trades: List[Trade], portfolio_history: List[Portfolio]) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if not portfolio_history:
            return {}

        final_portfolio = portfolio_history[-1]
        initial_value = portfolio_history[0].total_value if portfolio_history else 100.0

        total_return = (final_portfolio.total_value - initial_value) / initial_value
        total_trades = len(trades)
        win_rate = self._calculate_win_loss_ratio(final_portfolio)

        # Calculate equity curve for additional metrics
        equity_values = [p.total_value for p in portfolio_history]
        equity_series = pd.Series(equity_values)

        # Calculate maximum drawdown
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min()

        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'final_value': final_portfolio.total_value,
            'win_count': final_portfolio.win_count,
            'loss_count': final_portfolio.loss_count,
            'avg_cash_ratio': np.mean([p.cash_ratio for p in portfolio_history]),
            'max_positions': max(p.position_count for p in portfolio_history)
        }

    def _create_empty_result(self) -> BacktestResult:
        """Create empty result for error cases"""
        return BacktestResult(
            trades=[],
            portfolio_history=[Portfolio(cash=self.config.initial_cash)],
            daily_results=[],
            performance_metrics={},
            execution_time=0.0,
            config=self.config
        )


# ===== UTILITY FUNCTIONS =====
def load_backtest_config(config_path: str = None) -> BacktestConfig:
    """Load backtest configuration from YAML file"""
    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # Extract backtest specific configuration
            backtest_config = config_data.get('backtest', {})
            return BacktestConfig(**backtest_config)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")

    return BacktestConfig()


def create_sample_data(universe: List[str], days: int = 100) -> Dict[str, pd.DataFrame]:
    """Create sample data for testing purposes"""
    data = {}
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

    for ticker in universe:
        np.random.seed(hash(ticker) % 2**32)  # Reproducible but different for each ticker

        price = 100.0
        prices = []

        for _ in range(days):
            price *= (1 + np.random.normal(0, 0.02))  # 2% daily volatility
            prices.append(price)

        df = pd.DataFrame({
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'ADR': [np.random.uniform(2, 8) for _ in prices],
            'LossCutPrice': [p * 0.95 for p in prices],
            'TargetPrice': [p * 1.02 for p in prices],
            'BuySig': np.random.choice([0, 1], size=days, p=[0.9, 0.1]),
            'SellSig': np.random.choice([0, 1], size=days, p=[0.95, 0.05]),
            'signal': np.random.choice([0, 1], size=days, p=[0.9, 0.1]),
            'Type': ['Breakout'] * days,
            'RS_4W': [np.random.uniform(0, 100) for _ in prices],
            'Rev_Yoy_Growth': [np.random.uniform(-20, 50) for _ in prices],
            'Eps_Yoy_Growth': [np.random.uniform(-30, 100) for _ in prices],
            'Sector': ['Technology'] * days,
            'Industry': ['Software'] * days
        }, index=dates)

        data[ticker] = df

    return data


# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # Example usage
    config = BacktestConfig(
        initial_cash=100.0,
        max_positions=5,
        message_output=True
    )

    service = DailyBacktestService(config)

    # Create sample data
    universe = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    sample_data = create_sample_data(universe, days=50)

    # Run backtest
    result = service.run_backtest(universe, sample_data)

    # Print results
    print("\n" + "="*60)
    print("DAILY BACKTEST RESULTS")
    print("="*60)
    print(f"Total Return: {result.performance_metrics.get('total_return', 0):.2%}")
    print(f"Total Trades: {result.performance_metrics.get('total_trades', 0)}")
    print(f"Win Rate: {result.performance_metrics.get('win_rate', 0):.2%}")
    print(f"Max Drawdown: {result.performance_metrics.get('max_drawdown', 0):.2%}")
    print(f"Final Value: {result.performance_metrics.get('final_value', 0):.2f}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print("="*60)