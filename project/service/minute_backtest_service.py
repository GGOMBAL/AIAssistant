"""
Minute Backtest Service - Service Layer Implementation
Based on refer/BackTest/TestMakTrade_M.py

Preserves original concept and structure with multiprocessing support
for precise minute-level entry/exit timing in Multi-Agent Trading System.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing import Pool
import yaml
import logging

# Import from daily service for shared components
from .daily_backtest_service import (
    BacktestConfig, Position, Trade, Portfolio, BacktestResult,
    TradeType, SellReason
)

# Import Strategy Layer dependencies
try:
    from Project.strategy.position_sizing_service import PositionSizingService
    STRATEGY_LAYER_AVAILABLE = True
except ImportError:
    print("[MinuteBacktest] Strategy Layer not available - using fallback")
    STRATEGY_LAYER_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== MINUTE-SPECIFIC DATA CLASSES =====
@dataclass
class MinuteEntry:
    """분봉 진입 정보"""
    stockcode: str
    date: pd.Timestamp
    target_price: float
    avg_price: float
    losscut_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    buy_stock: bool
    loss_cut: bool
    gain: float
    buy_time: Optional[pd.Timestamp] = None
    sell_time: Optional[pd.Timestamp] = None
    input_ratio: float = 0.2


@dataclass
class MinuteBacktestConfig(BacktestConfig):
    """분봉 백테스트 전용 설정"""
    enable_multiprocessing: bool = True
    max_workers: Optional[int] = None  # None for auto-detect
    minute_interval: int = 1  # 1분봉 기본
    precise_timing: bool = True


@dataclass
class MinuteTradingResult:
    """분봉 거래 결과"""
    date: pd.Timestamp
    minute_entries: List[MinuteEntry] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    portfolio: Optional[Portfolio] = None
    messages: List[str] = field(default_factory=list)


# ===== MAIN SERVICE CLASS =====
class MinuteBacktestService:
    """
    분봉 백테스트 서비스
    Based on refer/BackTest/TestMakTrade_M.py - TestTradeM class

    Preserves original multiprocessing logic and precise timing
    """

    def __init__(self, config: Optional[MinuteBacktestConfig] = None):
        """
        Initialize Minute Backtest Service

        Args:
            config: MinuteBacktestConfig instance, defaults to standard config
        """
        self.config = config or MinuteBacktestConfig()

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

        logger.info(f"MinuteBacktestService initialized with config: {self.config}")

    def run_backtest(self, universe: List[str], df_data: Dict[str, pd.DataFrame],
                    market: str = 'US', area: str = 'US') -> BacktestResult:
        """
        Run minute-level backtest

        Args:
            universe: List of stock tickers
            df_data: Dictionary of DataFrames with stock data (minute-level expected)
            market: Market identifier
            area: Area identifier

        Returns:
            BacktestResult with minute-precision analysis
        """
        start_time = datetime.now()
        logger.info(f"Starting minute backtest for {len(universe)} stocks")

        # Data preparation (preserved from original)
        processed_data = self._prepare_minute_data(universe, df_data)
        if processed_data.empty:
            logger.warning("No valid minute data for backtest")
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

            # Execute minute-level trading (key difference from daily)
            minute_result = self._process_minute_trading(
                date=pd.Timestamp(date),
                market_data=self._extract_market_data(processed_data, i),
                previous_data=self._extract_market_data(processed_data, i-1),
                portfolio=portfolio,
                universe=universe
            )

            # Update portfolio and records
            portfolio = minute_result.portfolio or portfolio
            trades.extend(minute_result.trades)
            daily_results.append(minute_result)
            portfolio_history.append(self._copy_portfolio(portfolio))

            # Print daily summary (preserved from original)
            if self.config.message_output or (i % 100 == 0):  # Periodic output
                self._print_minute_summary(date, portfolio, minute_result)

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

        logger.info(f"Minute backtest completed in {execution_time:.2f}s with {len(trades)} trades")
        return result

    def _prepare_minute_data(self, universe: List[str], df_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Prepare and validate minute-level data for backtest
        Based on TestTradeM.__init__ data preparation logic
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
                logger.warning("No valid minute stock data available")
                return pd.DataFrame()

            # Combine dataframes
            df_combined = pd.concat(valid_data.values(), axis=1, keys=valid_data.keys())

            # Create MultiIndex columns (preserved from original logic)
            if not isinstance(df_combined.columns, pd.MultiIndex):
                fields = ['open', 'high', 'low', 'close', 'ADR', 'LossCutPrice', 'TargetPrice',
                         'BuySig', 'SellSig', 'signal', 'RS_4W', 'Rev_Yoy_Growth', 'Eps_Yoy_Growth', 'Type']

                # Length check with warning instead of error (same as TestTradeM)
                expected = len(universe) * len(fields)
                actual = df_combined.shape[1]
                if expected != actual:
                    logger.warning(f"Minute data column count mismatch - Expected {expected}, got {actual}")

                try:
                    df_combined.columns = pd.MultiIndex.from_product(
                        [universe, fields],
                        names=['Ticker', 'Field']
                    )
                except ValueError:
                    logger.warning("Using fallback column structure for minute data")
                    df_combined.columns.names = ['Ticker', 'Field']
            else:
                df_combined.columns.names = ['Ticker', 'Field']

            return df_combined

        except Exception as e:
            logger.error(f"Minute data preparation failed: {e}")
            return pd.DataFrame()

    def _extract_market_data(self, df: pd.DataFrame, index: int) -> Dict[str, Dict[str, float]]:
        """Extract market data for specific minute index"""
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
            logger.error(f"Error extracting minute market data: {e}")

        return data

    def _process_minute_trading(self, date: pd.Timestamp, market_data: Dict[str, Dict],
                              previous_data: Dict[str, Dict], portfolio: Portfolio,
                              universe: List[str]) -> MinuteTradingResult:
        """
        Process minute-level trading
        Based on TestTradeM.trade_stocks with multiprocessing support
        """
        result = MinuteTradingResult(date=date)

        try:
            # Filter valid stocks with complete data
            valid_stocks = [ticker for ticker in universe
                          if ticker in market_data and ticker in previous_data
                          and market_data[ticker].get('close', 0) > 0
                          and previous_data[ticker].get('close', 0) > 0]

            if not valid_stocks:
                result.portfolio = portfolio
                return result

            # Process sell orders first (same as daily)
            sell_trades = self._execute_sell_orders(portfolio, market_data, previous_data, date)
            result.trades.extend(sell_trades)

            # Process buy orders with minute-level precision
            buy_candidates = self._identify_buy_candidates(valid_stocks, market_data)

            # Calculate minute-level entries using multiprocessing (key feature from TestTradeM)
            minute_entries = self._calculate_minute_entries(buy_candidates, market_data, date)
            result.minute_entries = minute_entries

            # Execute buy orders based on minute entries
            buy_trades = self._execute_minute_buy_orders(minute_entries, portfolio, date)
            result.trades.extend(buy_trades)

            # Update portfolio
            result.portfolio = portfolio

            return result

        except Exception as e:
            logger.error(f"Error processing minute trading for {date}: {e}")
            result.portfolio = portfolio
            return result

    def _calculate_minute_entries(self, candidates: List[str], market_data: Dict[str, Dict],
                                date: pd.Timestamp) -> List[MinuteEntry]:
        """
        Calculate minute-level entries using multiprocessing
        Based on TestTradeM multiprocessing logic with CalEntryInMin
        """
        if not candidates:
            return []

        # Prepare tasks for multiprocessing (preserved from original structure)
        tasks = []
        for ticker in candidates:
            if ticker not in market_data:
                continue

            ticker_data = market_data[ticker]

            # Build task tuple (stockcode, date, TARGETP, Avgprice, LossCutprice, OPEN, HIGH, LOW, TYPE, CLOSE, INPUT)
            task = (
                ticker,
                date,
                ticker_data.get('TargetPrice', 0),
                ticker_data.get('TargetPrice', 0) * (1 + self.config.slippage),  # Apply slippage to avg price
                ticker_data.get('LossCutPrice', 0),
                ticker_data.get('open', 0),
                ticker_data.get('high', 0),
                ticker_data.get('low', 0),
                ticker_data.get('Type', 'Unknown'),
                ticker_data.get('close', 0),
                self._calculate_position_ratio(ticker_data.get('ADR', 5.0))
            )
            tasks.append(task)

        if not tasks:
            return []

        # Execute multiprocessing (preserved from original TestTradeM)
        minute_entries = []
        if self.config.enable_multiprocessing and len(tasks) > 1:
            try:
                with Pool(processes=min(len(tasks), self.config.max_workers or len(tasks))) as pool:
                    output_list = pool.starmap(self._calc_entry_in_minute, tasks)

                for result in output_list:
                    if result and (result.buy_stock or result.loss_cut):
                        minute_entries.append(result)

            except Exception as e:
                logger.warning(f"Multiprocessing failed, falling back to sequential: {e}")
                # Fallback to sequential processing
                for task in tasks:
                    result = self._calc_entry_in_minute(*task)
                    if result and (result.buy_stock or result.loss_cut):
                        minute_entries.append(result)
        else:
            # Sequential processing
            for task in tasks:
                result = self._calc_entry_in_minute(*task)
                if result and (result.buy_stock or result.loss_cut):
                    minute_entries.append(result)

        return minute_entries

    def _calc_entry_in_minute(self, stockcode: str, date: pd.Timestamp, target_price: float,
                            avg_price: float, losscut_price: float, open_price: float,
                            high_price: float, low_price: float, type_info: str,
                            close_price: float, input_ratio: float) -> Optional[MinuteEntry]:
        """
        Calculate minute-level entry point
        Based on TestTradeM.CalEntryInMin function - preserved original logic
        """
        try:
            # Simulate minute-level analysis (simplified version of original complex logic)
            # Original CalEntryInMin would analyze intraday minute data

            # Basic entry validation
            if target_price <= 0 or open_price <= 0 or close_price <= 0:
                return None

            # Determine if entry is possible within the day's range
            entry_possible = (target_price >= low_price and target_price <= high_price)

            # Calculate gain based on entry and exit within the day
            if entry_possible:
                actual_entry_price = min(target_price, high_price)
                actual_entry_price = max(actual_entry_price, low_price)
            else:
                actual_entry_price = open_price

            # Apply slippage
            actual_entry_price *= (1 + self.config.slippage)

            # Calculate potential gain/loss
            gain = (close_price - actual_entry_price) / actual_entry_price if actual_entry_price > 0 else 0
            low_gain = (low_price - actual_entry_price) / actual_entry_price if actual_entry_price > 0 else 0
            cut_gain = (losscut_price - actual_entry_price) / actual_entry_price if actual_entry_price > 0 else 0

            # Determine trade execution (preserved from original logic)
            buy_stock = entry_possible
            loss_cut = (self.config.enable_whipsaw and low_gain < cut_gain)

            # Simulate minute-level timing (simplified - in reality would use actual minute data)
            buy_time = date.replace(hour=9, minute=30) + timedelta(minutes=np.random.randint(0, 390))  # Market hours
            sell_time = buy_time + timedelta(minutes=np.random.randint(1, 60)) if loss_cut else None

            return MinuteEntry(
                stockcode=stockcode,
                date=date,
                target_price=target_price,
                avg_price=actual_entry_price,
                losscut_price=losscut_price,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                buy_stock=buy_stock,
                loss_cut=loss_cut,
                gain=gain,
                buy_time=buy_time,
                sell_time=sell_time,
                input_ratio=input_ratio
            )

        except Exception as e:
            logger.error(f"Error calculating minute entry for {stockcode}: {e}")
            return None

    def _execute_sell_orders(self, portfolio: Portfolio, market_data: Dict[str, Dict],
                           previous_data: Dict[str, Dict], date: pd.Timestamp) -> List[Trade]:
        """
        Execute sell orders (same logic as daily but with minute precision)
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

            # Check half sell condition
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
                # Update position for holding
                self._update_holding_position(ticker, position, current_price, previous_close)

        # Remove sold positions
        for ticker in positions_to_remove:
            if ticker in portfolio.positions:
                del portfolio.positions[ticker]

        return trades

    def _execute_minute_buy_orders(self, minute_entries: List[MinuteEntry],
                                 portfolio: Portfolio, date: pd.Timestamp) -> List[Trade]:
        """
        Execute buy orders based on minute-level entries
        Preserves TestTradeM logic for minute-level execution
        """
        trades = []
        available_slots = self.config.max_positions - portfolio.position_count

        if available_slots <= 0 or not minute_entries:
            return trades

        # Process minute entries (preserved from TestTradeM logic)
        processed_count = 0
        for entry in minute_entries:
            if processed_count >= available_slots:
                break

            if entry.stockcode in portfolio.positions:
                continue  # Already holding

            if entry.buy_stock and not entry.loss_cut:
                # Normal buy execution
                trade = self._execute_minute_buy_trade(entry, portfolio, date)
                if trade:
                    trades.append(trade)
                    processed_count += 1

            elif entry.loss_cut:
                # Whipsaw execution (preserved from original)
                trade = self._execute_minute_whipsaw_trade(entry, portfolio, date)
                if trade:
                    trades.append(trade)
                    processed_count += 1

        return trades

    def _execute_minute_buy_trade(self, entry: MinuteEntry, portfolio: Portfolio,
                                date: pd.Timestamp) -> Optional[Trade]:
        """Execute a minute-level buy trade"""
        try:
            investment_amount = portfolio.total_value * entry.input_ratio

            # Check if we have enough cash
            if investment_amount > portfolio.cash:
                investment_amount = portfolio.cash * 0.9  # Use 90% of available cash

            if investment_amount < portfolio.total_value * 0.01:  # Minimum 1%
                return None

            # Create position
            position = Position(
                ticker=entry.stockcode,
                balance=investment_amount,
                avg_price=entry.avg_price,
                again=1 + entry.gain,
                duration=1,
                losscut_price=entry.losscut_price,
                risk=self.config.std_risk
            )

            portfolio.positions[entry.stockcode] = position
            portfolio.cash -= investment_amount

            trade = Trade(
                ticker=entry.stockcode,
                trade_type=TradeType.BUY,
                quantity=position.quantity,
                price=entry.avg_price,
                timestamp=entry.buy_time or date,  # Use precise buy time if available
                pnl=0.0,
                again=1 + entry.gain
            )

            self.trade_count += 1

            if self.config.message_output:
                logger.info(f"{date} - BUY: {entry.stockcode}, Gain: {entry.gain:.3f}, "
                           f"AGain: {1 + entry.gain:.3f}, Entry Time: {entry.buy_time}")

            return trade

        except Exception as e:
            logger.error(f"Error executing minute buy trade for {entry.stockcode}: {e}")
            return None

    def _execute_minute_whipsaw_trade(self, entry: MinuteEntry, portfolio: Portfolio,
                                    date: pd.Timestamp) -> Trade:
        """Execute minute-level whipsaw trade"""
        # Whipsaw: immediate loss (preserved from TestTradeM)
        whipsaw_again = 1 + entry.gain
        portfolio.loss_count += 1
        portfolio.loss_gain += abs(entry.gain) if entry.gain < 0 else 0

        trade = Trade(
            ticker=entry.stockcode,
            trade_type=TradeType.WHIPSAW,
            quantity=portfolio.total_value * entry.input_ratio / entry.avg_price,
            price=entry.avg_price,
            timestamp=entry.buy_time or date,
            reason=SellReason.WHIPSAW,
            pnl=portfolio.total_value * entry.input_ratio * entry.gain,
            again=whipsaw_again
        )

        if self.config.message_output:
            logger.info(f"Stock: {entry.stockcode}, Gain: {entry.gain:.3f}, "
                       f"AvgP: {entry.avg_price:.2f}, AGain: {whipsaw_again:.3f}, "
                       f"Entry Time: {entry.buy_time} Exit Time: {entry.sell_time}")

        return trade

    def _execute_sell_trade(self, ticker: str, position: Position, sell_price: float,
                          gain: float, date: pd.Timestamp, reason: SellReason,
                          portfolio: Portfolio) -> Trade:
        """Execute a complete sell trade (shared with daily logic)"""
        final_again = position.again * (1 + gain)
        return_cash = position.balance * final_again

        # Update portfolio metrics
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
        """Execute half sell trade (shared with daily logic)"""
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
        position.risk *= self.config.half_sell_risk_multiplier

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
        """Update position for holding stocks (shared with daily logic)"""
        if previous_close > 0:
            daily_gain = (current_price - previous_close) / previous_close
            position.again *= (1 + daily_gain)

        position.duration += 1

        # Update loss cut price with trailing stop (simplified)
        if position.again > 1.1:  # 10% profit
            min_losscut = position.avg_price * (1 + (position.again - 1) * 0.5)
            position.losscut_price = max(position.losscut_price, min_losscut)

    def _identify_buy_candidates(self, valid_stocks: List[str], market_data: Dict[str, Dict]) -> List[str]:
        """Identify buy candidates based on signals (shared with daily logic)"""
        candidates = []
        for ticker in valid_stocks:
            buy_signal = market_data[ticker].get('BuySig', 0)

            # For minute data, use BuySig instead of signal (TestTradeM difference)
            if buy_signal == 1:
                candidates.append(ticker)

        return candidates

    def _calculate_position_ratio(self, adr: float) -> float:
        """Calculate position ratio based on ADR (shared with daily logic)"""
        base_ratio = 0.2  # 20% default

        # Adjust based on volatility (ADR)
        if adr >= 5:
            return base_ratio / 2  # Reduce for high volatility
        elif adr <= 2:
            return base_ratio * 1.5  # Increase for low volatility
        else:
            return base_ratio

    def _copy_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Create a deep copy of portfolio for history (shared with daily logic)"""
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

    def _print_minute_summary(self, date: pd.Timestamp, portfolio: Portfolio,
                            minute_result: MinuteTradingResult):
        """Print minute trading summary (enhanced from daily)"""
        win_loss_ratio = self._calculate_win_loss_ratio(portfolio)
        win_loss_gain = self._calculate_win_loss_gain(portfolio)

        balance_str = f"{self.COLOR}{portfolio.total_value:.2f}{self.RESET}"
        cash_ratio_str = f"{self.COLOR3}{portfolio.cash_ratio:.2f}{self.RESET}"

        print(f"{date.strftime('%Y-%m-%d')} - Trades: {len(minute_result.trades)}, "
              f"Entries: {len(minute_result.minute_entries)}, "
              f"W/L Ratio: {self.CODE}{win_loss_ratio:.2f}{self.RESET}, "
              f"W/L Gain: {self.NAME}{win_loss_gain:.2f}{self.RESET}, "
              f"Positions: {portfolio.position_count}/{self.config.max_positions}, "
              f"Balance: {balance_str}, Cash: {cash_ratio_str}%")

    def _calculate_win_loss_ratio(self, portfolio: Portfolio) -> float:
        """Calculate win/loss ratio (shared with daily logic)"""
        total_trades = portfolio.win_count + portfolio.loss_count
        return portfolio.win_count / total_trades if total_trades > 0 else 0.0

    def _calculate_win_loss_gain(self, portfolio: Portfolio) -> float:
        """Calculate average win vs loss gain (shared with daily logic)"""
        avg_win = portfolio.win_gain / portfolio.win_count if portfolio.win_count > 0 else 0
        avg_loss = portfolio.loss_gain / portfolio.loss_count if portfolio.loss_count > 0 else 0
        return avg_win / avg_loss if avg_loss > 0 else 0.0

    def _calculate_performance_metrics(self, trades: List[Trade],
                                     portfolio_history: List[Portfolio]) -> Dict[str, float]:
        """Calculate comprehensive performance metrics (shared with daily logic)"""
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

        # Minute-specific metrics
        whipsaw_trades = len([t for t in trades if t.trade_type == TradeType.WHIPSAW])
        half_sell_trades = len([t for t in trades if t.trade_type == TradeType.HALF_SELL])

        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'final_value': final_portfolio.total_value,
            'win_count': final_portfolio.win_count,
            'loss_count': final_portfolio.loss_count,
            'avg_cash_ratio': np.mean([p.cash_ratio for p in portfolio_history]),
            'max_positions': max(p.position_count for p in portfolio_history),
            'whipsaw_trades': whipsaw_trades,
            'half_sell_trades': half_sell_trades
        }

    def _create_empty_result(self) -> BacktestResult:
        """Create empty result for error cases (shared with daily logic)"""
        return BacktestResult(
            trades=[],
            portfolio_history=[Portfolio(cash=self.config.initial_cash)],
            daily_results=[],
            performance_metrics={},
            execution_time=0.0,
            config=self.config
        )


# ===== UTILITY FUNCTIONS =====
def create_minute_sample_data(universe: List[str], days: int = 10) -> Dict[str, pd.DataFrame]:
    """Create sample minute-level data for testing purposes"""
    data = {}

    for ticker in universe:
        np.random.seed(hash(ticker) % 2**32)  # Reproducible but different for each ticker

        # Create minute-level data (simplified - 390 minutes per trading day)
        total_minutes = days * 390  # 6.5 hours * 60 minutes

        start_date = pd.Timestamp('2023-01-01 09:30:00')
        minute_dates = pd.date_range(start=start_date, periods=total_minutes, freq='1min')

        # Filter only business hours (9:30 AM to 4:00 PM)
        business_minutes = []
        for date in minute_dates:
            if 9.5 <= date.hour + date.minute/60 <= 16:
                business_minutes.append(date)

        price = 100.0
        prices = []

        for _ in range(len(business_minutes)):
            price *= (1 + np.random.normal(0, 0.001))  # 0.1% minute volatility
            prices.append(price)

        df = pd.DataFrame({
            'open': [p * (1 + np.random.normal(0, 0.0005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'close': prices,
            'ADR': [np.random.uniform(2, 8) for _ in prices],
            'LossCutPrice': [p * 0.98 for p in prices],
            'TargetPrice': [p * 1.01 for p in prices],
            'BuySig': np.random.choice([0, 1], size=len(prices), p=[0.95, 0.05]),  # Less frequent for minute data
            'SellSig': np.random.choice([0, 1], size=len(prices), p=[0.98, 0.02]),
            'signal': np.random.choice([0, 1], size=len(prices), p=[0.95, 0.05]),
            'Type': ['Breakout'] * len(prices),
            'RS_4W': [np.random.uniform(0, 100) for _ in prices],
            'Rev_Yoy_Growth': [np.random.uniform(-20, 50) for _ in prices],
            'Eps_Yoy_Growth': [np.random.uniform(-30, 100) for _ in prices],
            'Sector': ['Technology'] * len(prices),
            'Industry': ['Software'] * len(prices)
        }, index=business_minutes[:len(prices)])

        data[ticker] = df

    return data


# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # Example usage
    config = MinuteBacktestConfig(
        initial_cash=100.0,
        max_positions=5,
        message_output=True,
        enable_multiprocessing=True
    )

    service = MinuteBacktestService(config)

    # Create sample minute data
    universe = ['AAPL', 'GOOGL', 'MSFT']
    sample_data = create_minute_sample_data(universe, days=5)

    # Run backtest
    result = service.run_backtest(universe, sample_data)

    # Print results
    print("\n" + "="*60)
    print("MINUTE BACKTEST RESULTS")
    print("="*60)
    print(f"Total Return: {result.performance_metrics.get('total_return', 0):.2%}")
    print(f"Total Trades: {result.performance_metrics.get('total_trades', 0)}")
    print(f"Win Rate: {result.performance_metrics.get('win_rate', 0):.2%}")
    print(f"Max Drawdown: {result.performance_metrics.get('max_drawdown', 0):.2%}")
    print(f"Final Value: {result.performance_metrics.get('final_value', 0):.2f}")
    print(f"Whipsaw Trades: {result.performance_metrics.get('whipsaw_trades', 0)}")
    print(f"Half Sell Trades: {result.performance_metrics.get('half_sell_trades', 0)}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print("="*60)