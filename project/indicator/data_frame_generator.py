"""
Data Frame Generator - Strategy Agent Management
Based on refer/BackTest/TestMain.py
Generates df_W, df_RS, df_D, df_E, df_F data frames for indicator processing
Now integrated with Database Layer
"""

import pandas as pd
import copy
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import sys
import os

# Add project root to path for database imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Import Database Layer components
try:
    from project.database.mongodb_operations import MongoDBOperations
    from project.database.database_name_calculator import calculate_database_name
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)

class DataFrameGenerator:
    """
    Generates trading data frames based on refer/BackTest/TestMain.py logic
    Strategy Agent has exclusive management of this class
    """
    
    def __init__(self, universe: List[str] = None, market: str = 'US', area: str = 'US',
                 start_day: datetime = None, end_day: datetime = None, is_backtest: bool = False):
        """
        Initialize DataFrameGenerator

        Args:
            universe: List of stock symbols
            market: Market identifier
            area: Market area (US, KR, etc)
            start_day: Start date for data
            end_day: End date for data
            is_backtest: True for backtest mode (prevents future reference), False for live trading
        """
        pd.set_option('future.no_silent_downcasting', True)

        self.market = market
        self.area = area
        self.is_backtest = is_backtest

        # Set default dates if not provided
        if start_day is None:
            start_day = datetime.now() - timedelta(days=365)
        if end_day is None:
            end_day = datetime.now()
        if universe is None:
            universe = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

        # Convert string dates to datetime if needed
        if isinstance(start_day, str):
            start_day = datetime.strptime(start_day, '%Y-%m-%d')
        if isinstance(end_day, str):
            end_day = datetime.strptime(end_day, '%Y-%m-%d')

        self.start_day = start_day
        self.data_start_day = start_day - timedelta(days=365*3)  # 3 years of historical data
        self.end_day = end_day

        # Clean and validate universe
        self.universe = [s.strip() for s in universe if s and s.strip()]

        if len(self.universe) != len(universe):
            logger.warning(f"Filtered {len(universe) - len(self.universe)} invalid symbols from universe")

        # Initialize data frames
        self.df_W = {}   # Weekly data
        self.df_RS = {}  # Relative strength data
        self.df_D = {}   # Daily data
        self.df_E = {}   # Earnings data (US only)
        self.df_F = {}   # Fundamental data (US only)

        # Single MongoDB connection for all operations (reuse connection)
        self.db = None
        if DATABASE_AVAILABLE:
            self.db = MongoDBOperations(db_address="MONGODB_LOCAL")

        logger.info(f"Initialized DataFrameGenerator for {area} market with {len(universe)} symbols")
    
    def read_database_task(self, market: str, area: str, data_type: str, 
                          universe: List[str], data_start_day: datetime, 
                          end_day: datetime) -> Tuple[str, Dict, List[str]]:
        """
        Single database read task - integrated with Database Layer
        Based on refer/BackTest/TestMain.py read_database_task
        
        Args:
            market: Market identifier
            area: Market area
            data_type: Type of data (W, RS, AD, E, F)
            universe: List of symbols
            data_start_day: Start date
            end_day: End date
            
        Returns:
            Tuple of (data_type, dataframe_dict, updated_universe)
        """
        try:
            if DATABASE_AVAILABLE and self.db is not None:
                # Use existing Database connection (reuse connection)
                database_name = calculate_database_name(market, area, data_type, "Stock")

                # Call ReadDataBase method (equivalent to refer implementation)
                df_dict, updated_universe = self._read_from_mongodb(
                    self.db, universe, market, area, database_name, data_start_day, end_day
                )

                return data_type, df_dict, updated_universe
            else:
                # Use Helper Layer to get real market data when database is not available
                logger.info(f"Database not available, using Helper Layer for {data_type} data")
                return self._get_helper_data(data_type, universe, data_start_day, end_day)

        except Exception as e:
            logger.error(f"Error reading {data_type} data: {e}")
            # Return empty structure on error
            df_dict = {symbol: pd.DataFrame() for symbol in universe}
            return data_type, df_dict, universe
    
    def _read_from_mongodb(self, db: Any, universe: List[str], 
                          market: str, area: str, database_name: str, 
                          data_start_day: datetime, end_day: datetime) -> Tuple[Dict, List[str]]:
        """
        Read data from MongoDB - equivalent to MongoDB.ReadDataBase method
        
        Args:
            db: MongoDB operations instance
            universe: List of stock symbols
            market: Market identifier
            area: Area identifier  
            database_name: Database name to query
            data_start_day: Start date
            end_day: End date
            
        Returns:
            Tuple of (dataframe_dict, updated_universe)
        """
        df_dict = {}
        updated_universe = []

        try:
            # Filter out empty or invalid symbols
            valid_symbols = [s for s in universe if s and s.strip()]

            for symbol in valid_symbols:
                try:
                    # Skip if symbol is empty after strip
                    if not symbol.strip():
                        continue

                    # Query data for each symbol
                    df = db.execute_query(
                        db_name=database_name,
                        collection_name=symbol.strip(),
                        query={
                            'Date': {
                                '$gte': data_start_day,
                                '$lte': end_day
                            }
                        }
                    )

                    if not df.empty:
                        df_dict[symbol] = df
                        updated_universe.append(symbol)

                except Exception as e:
                    logger.debug(f"Error reading {symbol} from {database_name}: {e}")
                    continue
                    
            logger.info(f"Successfully read data for {len(updated_universe)} symbols from {database_name}")
            return df_dict, updated_universe
            
        except Exception as e:
            logger.error(f"Error reading from MongoDB database {database_name}: {e}")
            return {}, []
    
    def _simulate_database_read(self, data_type: str, universe: List[str], 
                               data_start_day: datetime, end_day: datetime) -> Tuple[str, Dict, List[str]]:
        """
        Simulate database read when Database Layer is not available
        
        Args:
            data_type: Type of data to simulate
            universe: List of symbols
            data_start_day: Start date
            end_day: End date
            
        Returns:
            Tuple of (data_type, dataframe_dict, updated_universe)
        """
        try:
            df_dict = {}
            for symbol in universe:
                df = self._create_placeholder_dataframe(data_start_day, end_day)
                df_dict[symbol] = df
            
            return data_type, df_dict, universe
            
        except Exception as e:
            logger.error(f"Error in simulation mode: {e}")
            return data_type, {}, []

    def _get_helper_data(self, data_type: str, universe: List[str],
                        data_start_day: datetime, end_day: datetime) -> Tuple[str, Dict, List[str]]:
        """
        Get real market data using Helper Layer when database is not available

        Args:
            data_type: Type of data (W, RS, AD, E, F)
            universe: List of stock symbols
            data_start_day: Start date
            end_day: End date

        Returns:
            Tuple of (data_type, dataframe_dict, updated_universe)
        """
        try:
            # Only get data for AD (daily data) using Helper
            if data_type == "AD":
                return self._get_market_data_from_helper_v2(data_type, universe, data_start_day, end_day)
            else:
                # For other data types, return placeholder
                return self._simulate_database_read(data_type, universe, data_start_day, end_day)
        except Exception as e:
            logger.error(f"Error getting helper data for {data_type}: {e}")
            return self._simulate_database_read(data_type, universe, data_start_day, end_day)

    def _get_market_data_from_helper_v2(self, data_type: str, universe: List[str],
                                       data_start_day: datetime, end_day: datetime) -> Tuple[str, Dict, List[str]]:
        """
        Get real market data using Helper functions (updated version)

        Args:
            data_type: Data type
            universe: List of stock symbols
            data_start_day: Start date
            end_day: End date

        Returns:
            Tuple of (data_type, dataframe_dict, updated_universe)
        """
        try:
            # Import Helper functions (read-only access)
            from Project.Helper.yfinance_helper import YFinanceHelper

            yf = YFinanceHelper()
            df_dict = {}
            successful_tickers = []

            for symbol in universe:
                try:
                    # Get OHLCV data using Helper function
                    df = yf.get_ohlcv(symbol, "D", data_start_day, end_day)

                    if not df.empty:
                        # Rename to match refer format
                        df = df.rename(columns={
                            'open': 'ad_open',
                            'high': 'ad_high',
                            'low': 'ad_low',
                            'close': 'ad_close',
                            'volume': 'volume'
                        })

                        # Add required columns
                        if 'dividends' in df.columns:
                            df['dividend_factor'] = df['dividends']
                        else:
                            df['dividend_factor'] = 0.0

                        if 'stock_splits' in df.columns:
                            df['split_factor'] = df['stock_splits']
                        else:
                            df['split_factor'] = 0.0

                        df_dict[symbol] = df
                        successful_tickers.append(symbol)
                        logger.info(f"Retrieved {len(df)} records for {symbol}")
                    else:
                        logger.warning(f"No data retrieved for {symbol}")

                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {e}")
                    continue

            return data_type, df_dict, successful_tickers

        except Exception as e:
            logger.error(f"Error in _get_market_data_from_helper_v2: {e}")
            return data_type, {}, []

    def _get_market_data_from_helper(self, universe: List[str], data_type: str) -> Dict[str, pd.DataFrame]:
        """
        Get real market data using Helper functions
        
        Args:
            universe: List of stock symbols
            data_type: Data type (W for weekly, AD for daily)
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        try:
            # Import Helper functions (read-only access)
            from Project.Helper.yfinance_helper import YFinanceHelper
            
            yf = YFinanceHelper()
            df_dict = {}
            
            # Determine period based on data type
            period_map = {
                "W": "1wk",  # Weekly data
                "AD": "1d"   # Daily data (AD = Adjusted Daily)
            }
            
            period = period_map.get(data_type, "1d")
            
            for symbol in universe[:5]:  # Limit to first 5 for testing
                try:
                    # Get OHLCV data using Helper function
                    df = yf.get_ohlcv(symbol, "D", self.data_start_day, self.end_day)
                    
                    if not df.empty:
                        # Ensure required columns exist
                        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        
                        if not missing_columns:
                            # Rename to match refer format
                            df = df.rename(columns={
                                'Open': 'ad_open',
                                'High': 'ad_high', 
                                'Low': 'ad_low',
                                'Close': 'ad_close',
                                'Volume': 'volume'
                            })
                            
                            # Add dividends and splits if not present
                            if 'Dividends' in df.columns:
                                df['dividend_factor'] = df['Dividends']
                            else:
                                df['dividend_factor'] = 0.0
                                
                            if 'Stock Splits' in df.columns:
                                df['split_factor'] = df['Stock Splits']
                            else:
                                df['split_factor'] = 0.0
                            
                            df_dict[symbol] = df
                            logger.info(f"Retrieved {len(df)} records for {symbol}")
                        else:
                            logger.warning(f"Missing columns for {symbol}: {missing_columns}")
                    else:
                        logger.warning(f"No data retrieved for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {e}")
                    continue
            
            return df_dict
            
        except Exception as e:
            logger.error(f"Error in _get_market_data_from_helper: {e}")
            return {}
    
    def _create_placeholder_dataframe(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Create placeholder DataFrame for data types not available from Helper
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Placeholder DataFrame
        """
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Create basic structure matching refer format
        df = pd.DataFrame(index=date_range)
        df['value'] = 0.0
        df['indicator'] = 0.0
        
        return df
    
    def load_data_from_database(self) -> None:
        """
        Load data from database using parallel processing (based on refer implementation)
        """
        logger.info("Starting parallel database loading...")
        
        # Basic data types
        data_types = ["W", "RS", "AD"]
        
        # US area gets additional data types  
        if self.area == 'US':
            data_types.extend(["E", "F"])
        
        # Parallel execution using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(data_types)) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self.read_database_task,
                    self.market,
                    self.area, 
                    data_type,
                    self.universe,
                    self.data_start_day,
                    self.end_day
                ): data_type for data_type in data_types
            }
            
            # Store updated universes for each data type
            updated_universes = {}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                data_type = futures[future]
                try:
                    _, df, updated_universe = future.result()
                    
                    # Assign to appropriate attribute
                    if data_type == "W":
                        self.df_W = df
                        updated_universes['updated_universe_W'] = updated_universe
                    elif data_type == "RS":
                        self.df_RS = df
                        updated_universes['updated_universe_RS'] = updated_universe
                    elif data_type == "AD":
                        self.df_D = df
                        updated_universes['updated_universe_AD'] = updated_universe
                    elif data_type == "E":
                        self.df_E = df
                        updated_universes['updated_universe_E'] = updated_universe
                    elif data_type == "F":
                        self.df_F = df
                        updated_universes['updated_universe_F'] = updated_universe
                    
                    logger.info(f"Loaded {data_type} data successfully")
                    
                except Exception as e:
                    logger.error(f"Error loading {data_type} data: {e}")
        
        # Find common tickers across all datasets
        if updated_universes:
            common_tickers = set(list(updated_universes.values())[0])
            for universe in updated_universes.values():
                common_tickers = common_tickers.intersection(set(universe))
            self.universe = list(common_tickers)
        
        logger.info(f"Database loading complete. Common tickers: {len(self.universe)}")
        
        # Apply KR-specific formatting if needed
        if self.area == 'KR':
            self.universe = ['A' + stock for stock in self.universe]
        
        # Remove tickers not in common universe from all dataframes
        self._cleanup_dataframes()

        # Remove duplicates and apply post-processing (includes all technical indicators)
        self._post_process_dataframes()
    
    def _cleanup_dataframes(self) -> None:
        """Remove tickers not in common universe from all dataframes"""
        universe_set = set(self.universe)
        
        # Clean df_W
        if hasattr(self, 'df_W') and self.df_W:
            keys_to_remove = [key for key in self.df_W.keys() if key not in universe_set]
            for key in keys_to_remove:
                del self.df_W[key]
        
        # Clean df_RS
        if hasattr(self, 'df_RS') and self.df_RS:
            keys_to_remove = [key for key in self.df_RS.keys() if key not in universe_set]
            for key in keys_to_remove:
                del self.df_RS[key]
        
        # Clean df_D
        if hasattr(self, 'df_D') and self.df_D:
            keys_to_remove = [key for key in self.df_D.keys() if key not in universe_set]
            for key in keys_to_remove:
                del self.df_D[key]
        
        # Clean US-specific dataframes
        if self.area == 'US':
            if hasattr(self, 'df_E') and self.df_E:
                keys_to_remove = [key for key in self.df_E.keys() if key not in universe_set]
                for key in keys_to_remove:
                    del self.df_E[key]
            
            if hasattr(self, 'df_F') and self.df_F:
                keys_to_remove = [key for key in self.df_F.keys() if key not in universe_set]
                for key in keys_to_remove:
                    del self.df_F[key]
    
    def _post_process_dataframes(self) -> None:
        """Remove duplicates and apply post-processing (based on refer logic)"""
        logger.info("Post-processing dataframes...")

        # Remove duplicates only (technical indicators will be handled by TechnicalIndicatorGenerator)
        for stock in self.universe:
            try:
                # Process Weekly data - remove duplicates only
                if stock in self.df_W:
                    self.df_W[stock] = self.df_W[stock][~self.df_W[stock].index.duplicated()]

                # Process RS data - remove duplicates only
                if stock in self.df_RS:
                    self.df_RS[stock] = self.df_RS[stock][~self.df_RS[stock].index.duplicated()]

                # Process Daily data - remove duplicates only
                if stock in self.df_D:
                    self.df_D[stock] = self.df_D[stock][~self.df_D[stock].index.duplicated()]

                # US-specific processing
                if self.area == 'US':
                    if stock in self.df_E:
                        self.df_E[stock] = self.df_E[stock][~self.df_E[stock].index.duplicated()]

                        # Convert earnings percentage data to decimal format
                        # eps_yoy, eps_qoq, rev_yoy, rev_qoq are stored as % (25.0 = 25%)
                        # Convert to decimal format (0.25 = 25%) to match fundamental data
                        percentage_columns = ['eps_yoy', 'eps_qoq', 'rev_yoy', 'rev_qoq']
                        for col in percentage_columns:
                            if col in self.df_E[stock].columns:
                                self.df_E[stock][col] = self.df_E[stock][col] / 100.0

                    if stock in self.df_F:
                        self.df_F[stock] = self.df_F[stock][~self.df_F[stock].index.duplicated()]

            except Exception as e:
                logger.error(f"Error processing {stock}: {e}")

        # Reindex and merge fundamental data for US market (based on refer logic)
        if self.area == 'US':
            self._process_fundamental_data()

        # Apply technical indicators processing using TechnicalIndicatorGenerator
        # This will handle ALL column renaming and indicator calculations
        self._apply_technical_indicators()

    def _apply_technical_indicators(self) -> None:
        """
        Apply technical indicators using TechnicalIndicatorGenerator
        This processes all dataframes and adds calculated indicators
        """
        try:
            from project.indicator.technical_indicators import TechnicalIndicatorGenerator

            logger.info("Applying technical indicators...")

            # Initialize TechnicalIndicatorGenerator with current dataframes
            tech_gen = TechnicalIndicatorGenerator(
                universe=self.universe,
                area=self.area,
                df_W=self.df_W,
                df_D=self.df_D,
                df_RS=self.df_RS,
                df_E=self.df_E,
                df_F=self.df_F,
                start_day=self.start_day,
                end_day=self.end_day,
                trading=not self.is_backtest  # trading=True for live, False for backtest
            )

            # Get processed dataframes with all technical indicators
            self.df_D, self.df_W, self.df_RS, self.df_E, self.df_F = tech_gen.return_processed_data()

            logger.info("Technical indicators applied successfully")

        except Exception as e:
            logger.error(f"Error applying technical indicators: {e}")
            import traceback
            traceback.print_exc()

    def _process_fundamental_data(self) -> None:
        """
        Process fundamental data for US market
        Join with Daily close prices from XXXDataBase_AD (df_D)

        IMPORTANT: F 데이터는 분기별 인덱스, D 데이터는 일별 인덱스
        F 데이터의 각 날짜에 맞는 D 데이터의 close 값을 조인해야 함
        Based on GetTrdData2 F section requirement

        NOTE: At this point, columns are NOT renamed yet (still ad_close, not Dclose)
        """
        logger.info("Processing US fundamental data...")

        for stock in self.universe:
            try:
                if stock in self.df_F and stock in self.df_D:
                    # Get daily close data (columns NOT renamed yet, so use ad_close)
                    daily_close = None
                    if 'ad_close' in self.df_D[stock].columns:
                        daily_close = self.df_D[stock]['ad_close']
                    elif 'close' in self.df_D[stock].columns:
                        daily_close = self.df_D[stock]['close']
                    elif 'Dclose' in self.df_D[stock].columns:
                        daily_close = self.df_D[stock]['Dclose']

                    if daily_close is None:
                        logger.warning(f"No close price column found for {stock} in daily data")
                        continue

                    # Join close prices to fundamental data based on F data's index
                    # Use merge with nearest date matching (forward fill)
                    df_f_with_close = self.df_F[stock].copy()

                    # For each fundamental data date, find the corresponding close price
                    # If exact date match exists, use it; otherwise use nearest previous date
                    close_values = []
                    for f_date in df_f_with_close.index:
                        # Find closest date in daily data that is <= f_date
                        valid_dates = daily_close.index[daily_close.index <= f_date]
                        if len(valid_dates) > 0:
                            closest_date = valid_dates[-1]  # Most recent date
                            close_values.append(daily_close.loc[closest_date])
                        else:
                            # No previous date available, use forward fill from daily data
                            close_values.append(None)

                    # Add 'close' column to fundamental data
                    df_f_with_close['close'] = close_values

                    # Forward fill any None values
                    df_f_with_close['close'] = df_f_with_close['close'].ffill()

                    # Update fundamental dataframe
                    self.df_F[stock] = df_f_with_close

                    # Forward fill other missing fundamental values
                    self.df_F[stock].ffill(inplace=True)

                    # Remove duplicates
                    self.df_F[stock] = self.df_F[stock][~self.df_F[stock].index.duplicated()]

                    logger.debug(f"Processed fundamental data for {stock}: {len(self.df_F[stock])} records with close prices")

            except Exception as e:
                logger.error(f"Error processing fundamental data for {stock}: {e}")
                import traceback
                traceback.print_exc()

    def get_strategy_data(self, strategy_name: str = 'A') -> Tuple[Dict, List[str]]:
        """
        Prepare data for strategy processing (based on refer RunStrategy logic)
        
        Args:
            strategy_name: Name of strategy to run
            
        Returns:
            Tuple of (processed_dataframes_dict, updated_universe)
        """
        logger.info(f"Preparing data for strategy {strategy_name}")
        
        # Deep copy dataframes for strategy processing
        dfW1 = copy.deepcopy(self.df_W)
        dfD1 = copy.deepcopy(self.df_D)  
        dfR1 = copy.deepcopy(self.df_RS)
        
        if self.area == 'US':
            dfE1 = copy.deepcopy(self.df_E)
            dfF1 = copy.deepcopy(self.df_F)
        else:
            dfE1 = {}
            dfF1 = {}
        
        universe1 = copy.deepcopy(self.universe)
        
        # Find common keys across all dictionaries
        if self.area == 'US':
            dicts = [dfW1, dfD1, dfR1, dfE1, dfF1]
        else:
            dicts = [dfW1, dfD1, dfR1]
        
        # Calculate common keys
        common_keys = set(dicts[0]).intersection(*[set(d) for d in dicts[1:]])
        
        # Remove non-common keys from each dictionary
        for d in dicts:
            for key in list(d.keys()):
                if key not in common_keys:
                    del d[key]
        
        logger.info(f"Strategy data prepared. Common keys: {len(common_keys)}")
        
        return {
            'df_W': dfW1,
            'df_D': dfD1, 
            'df_RS': dfR1,
            'df_E': dfE1,
            'df_F': dfF1,
            'universe': universe1,
            'area': self.area
        }, list(common_keys)
    
    def filter_by_date_range(self, data_dict: Dict, start_day: datetime, end_day: datetime) -> Dict:
        """
        Filter dataframes by date range
        
        Args:
            data_dict: Dictionary containing dataframes
            start_day: Start date
            end_day: End date
            
        Returns:
            Filtered data dictionary
        """
        logger.info(f"Filtering data by date range: {start_day} to {end_day}")
        
        filtered_data = {}
        
        for key, df_dict in data_dict.items():
            if key == 'universe' or key == 'area':
                filtered_data[key] = df_dict
                continue
                
            if isinstance(df_dict, dict):
                filtered_df_dict = {}
                for stock, df in df_dict.items():
                    try:
                        if not df.empty:
                            filtered_df = df[
                                (df.index >= start_day) & (df.index <= end_day)
                            ]
                            filtered_df_dict[stock] = filtered_df
                    except Exception as e:
                        logger.error(f"Error filtering {stock} in {key}: {e}")
                        filtered_df_dict[stock] = df
                
                filtered_data[key] = filtered_df_dict
            else:
                filtered_data[key] = df_dict
        
        return filtered_data
    
    def get_dataframes(self) -> Dict[str, Dict]:
        """
        Get all generated dataframes
        
        Returns:
            Dictionary containing all dataframes
        """
        return {
            'df_W': self.df_W,
            'df_RS': self.df_RS, 
            'df_D': self.df_D,
            'df_E': self.df_E if self.area == 'US' else {},
            'df_F': self.df_F if self.area == 'US' else {},
            'universe': self.universe,
            'area': self.area,
            'market': self.market
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary information about loaded data
        
        Returns:
            Summary dictionary
        """
        summary = {
            'universe_count': len(self.universe),
            'area': self.area,
            'market': self.market,
            'date_range': f"{self.start_day} to {self.end_day}",
            'data_types': []
        }
        
        if self.df_W:
            summary['data_types'].append('Weekly (W)')
            summary['weekly_symbols'] = len(self.df_W)
            
        if self.df_RS:
            summary['data_types'].append('Relative Strength (RS)')
            summary['rs_symbols'] = len(self.df_RS)
            
        if self.df_D:
            summary['data_types'].append('Daily (D)')
            summary['daily_symbols'] = len(self.df_D)
            
        if self.area == 'US':
            if self.df_E:
                summary['data_types'].append('Earnings (E)')
                summary['earnings_symbols'] = len(self.df_E)
                
            if self.df_F:
                summary['data_types'].append('Fundamental (F)')
                summary['fundamental_symbols'] = len(self.df_F)
        
        return summary