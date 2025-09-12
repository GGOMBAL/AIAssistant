"""
Technical Indicators Generator - Strategy Agent Management
Based on refer/Indicator/GenTradingData.py and refer/Helper/KIS/KIS_Make_TradingData.py
Generates technical indicators for trading dataframes
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Setup logging
logger = logging.getLogger(__name__)

class TechnicalIndicatorGenerator:
    """
    Generates technical indicators based on refer/Indicator/GenTradingData.py logic
    Strategy Agent has exclusive management of this class
    """
    
    def __init__(self, universe: List[str], area: str, df_W: Dict, df_D: Dict, 
                 df_RS: Dict, df_E: Dict, df_F: Dict, start_day, end_day, trading: bool = True):
        """
        Initialize Technical Indicator Generator
        
        Args:
            universe: List of stock symbols
            area: Market area (US, KR, etc)
            df_W: Weekly dataframes dictionary
            df_D: Daily dataframes dictionary  
            df_RS: Relative strength dataframes dictionary
            df_E: Earnings dataframes dictionary
            df_F: Fundamental dataframes dictionary
            start_day: Start date
            end_day: End date
            trading: Trading mode flag
        """
        self.universe = universe
        self.area = area
        self.df_W = df_W
        self.df_D = df_D
        self.df_RS = df_RS
        self.df_E = df_E
        self.df_F = df_F
        self.start_day = start_day
        self.end_day = end_day
        self.trading = trading
        
        logger.info(f"Initialized TechnicalIndicatorGenerator for {area} with {len(universe)} symbols")
        
        # Process technical indicators for each dataframe type
        self._process_all_indicators()
    
    def _process_all_indicators(self) -> None:
        """Process technical indicators for all dataframe types"""
        logger.info("Starting technical indicator processing...")
        
        # Process weekly data
        self.df_W = self.get_technical_data(self.universe, self.df_W, 'W')
        for stock_code, df in self.df_W.items():
            self.df_W[stock_code] = self._optimize_dataframe_memory(df)
        
        # Process relative strength data
        self.df_RS = self.get_technical_data(self.universe, self.df_RS, 'RS')
        for stock_code, df in self.df_RS.items():
            self.df_RS[stock_code] = self._optimize_dataframe_memory(df)
        
        # Process fundamental data for US market
        if self.area == 'US' and self.df_F:
            self.df_F = self.get_technical_data(self.universe, self.df_F, 'F')
            for stock_code, df in self.df_F.items():
                self.df_F[stock_code] = self._optimize_dataframe_memory(df)
        
        # Process daily data (most important, done last)
        self.df_D = self.get_technical_data(self.universe, self.df_D, 'D')
        for stock_code, df in self.df_D.items():
            self.df_D[stock_code] = self._optimize_dataframe_memory(df)
        
        # Apply date filtering
        self._apply_date_filtering()
        
        logger.info("Technical indicator processing completed")
    
    def get_technical_data(self, universe: List[str], df_dict: Dict, p_code: str) -> Dict:
        """
        Generate technical data for given universe and dataframe type
        Based on refer/Indicator/GenTradingData.py logic
        
        Args:
            universe: List of stock symbols
            df_dict: Dictionary of dataframes
            p_code: Period code (W, RS, D, E, F)
            
        Returns:
            Dictionary of processed dataframes
        """
        logger.info(f"Processing technical data for {p_code} period")
        
        # Prepare tasks for parallel processing
        tasks = []
        for stock in universe:
            if stock in df_dict and not df_dict[stock].empty:
                tasks.append((stock, p_code, self.area, df_dict[stock], self.trading))
        
        processed_data = {}
        
        # Use ThreadPoolExecutor for concurrent processing
        max_workers = min(len(tasks), 4)  # Limit workers to avoid overwhelming
        
        if max_workers > 0:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_stock = {
                    executor.submit(self._process_single_stock_technical_data, task): task[0]
                    for task in tasks
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_stock):
                    stock_code, processed_df_stock = future.result()
                    if processed_df_stock is not None and not processed_df_stock.empty:
                        processed_data[stock_code] = self._optimize_dataframe_memory(processed_df_stock)
                    else:
                        logger.warning(f"No processed data for {stock_code}")
        
        logger.info(f"Processed {len(processed_data)} stocks for {p_code} period")
        return processed_data
    
    def _process_single_stock_technical_data(self, args: Tuple) -> Tuple[str, Optional[pd.DataFrame]]:
        """
        Process technical data for a single stock (based on refer implementation)
        
        Args:
            args: Tuple of (stock, p_code, area, dataframe_stock, trading_config)
            
        Returns:
            Tuple of (stock_code, processed_dataframe)
        """
        stock, p_code, area, dataframe_stock, trading = args
        
        try:
            # Process based on period code
            processed_df = self._get_trading_data(p_code, area, dataframe_stock.copy(), stock, trading)
            return stock, processed_df
        except Exception as e:
            logger.error(f"Error processing technical data for {stock}: {e}")
            return stock, None
    
    def _get_trading_data(self, p_code: str, area: str, dataframe: pd.DataFrame, 
                         stock: str, trading: bool = True) -> pd.DataFrame:
        """
        Generate trading data based on refer/Helper/KIS/KIS_Make_TradingData.py logic
        
        Args:
            p_code: Period code
            area: Market area
            dataframe: Input dataframe
            stock: Stock symbol
            trading: Trading mode
            
        Returns:
            Processed dataframe with technical indicators
        """
        if p_code == 'D':  # Daily data processing
            return self._process_daily_data(dataframe, stock, trading)
        elif p_code == 'W':  # Weekly data processing
            return self._process_weekly_data(dataframe, stock, trading)
        elif p_code == 'RS':  # Relative strength data
            return self._process_rs_data(dataframe, stock, trading)
        elif p_code == 'F':  # Fundamental data (US only)
            return self._process_fundamental_data(dataframe, stock, trading)
        else:
            # Default processing
            return dataframe
    
    def _process_daily_data(self, dataframe: pd.DataFrame, stock: str, trading: bool) -> pd.DataFrame:
        """
        Process daily data with technical indicators
        Based on refer/Helper/KIS/KIS_Make_TradingData.py GetTrdData2 function
        """
        try:
            # Rename columns to standard format
            if 'ad_open' in dataframe.columns:
                dataframe = dataframe.rename(columns={
                    'ad_open': 'open', 
                    'ad_close': 'close', 
                    'ad_high': 'high', 
                    'ad_low': 'low'
                })
            
            # Calculate technical indicators
            if trading:
                # Real-time trading indicators (current values)
                dataframe['Highest_2Y'] = self._get_high(dataframe, period=200*2)
                dataframe['Highest_1Y'] = self._get_high(dataframe, period=200*1) 
                dataframe['Highest_6M'] = self._get_high(dataframe, period=100*1)
                dataframe['Highest_3M'] = self._get_high(dataframe, period=50*1)
                dataframe['Highest_1M'] = self._get_high(dataframe, period=20*1)
                dataframe['SMA200_M'] = self._get_sma_momentum(dataframe, 200, 3)
                dataframe['SMA20'] = self._get_ma(dataframe['close'], 20, 100)
                dataframe['SMA50'] = self._get_ma(dataframe['close'], 50, 100)
                dataframe['SMA200'] = self._get_ma(dataframe['close'], 200, 100)
                dataframe['ADR'] = self._get_adr_pct(dataframe, 20)
            else:
                # Backtest indicators (shifted values to avoid look-ahead bias)
                dataframe['Highest_2Y'] = self._get_high(dataframe, period=200*2).shift()
                dataframe['Highest_1Y'] = self._get_high(dataframe, period=200*1).shift()
                dataframe['Highest_6M'] = self._get_high(dataframe, period=100*1).shift()
                dataframe['Highest_3M'] = self._get_high(dataframe, period=50*1).shift()
                dataframe['Highest_1M'] = self._get_high(dataframe, period=20*1).shift()
                dataframe['SMA200_M'] = self._get_sma_momentum(dataframe, 200, 3).shift()
                dataframe['SMA20'] = self._get_ma(dataframe['close'], 20, 100).shift()
                dataframe['SMA50'] = self._get_ma(dataframe['close'], 50, 100).shift()
                dataframe['SMA200'] = self._get_ma(dataframe['close'], 200, 100).shift()
                dataframe['ADR'] = self._get_adr_pct(dataframe, 20).shift()
            
            # Rename columns to daily format
            dataframe = dataframe.rename(columns={
                'open': 'Dopen', 
                'close': 'Dclose', 
                'high': 'Dhigh', 
                'low': 'Dlow', 
                'volume': 'Dvolume'
            })
            
        except Exception as e:
            logger.error(f"Error in daily data processing for {stock}: {e}")
            # Set default values on error
            for col in ['SMA200_M', 'SMA20', 'SMA50', 'SMA200', 'Highest_2Y', 
                       'Highest_1Y', 'Highest_6M', 'Highest_3M', 'Highest_1M', 'ADR']:
                dataframe[col] = 0
        
        return dataframe
    
    def _process_weekly_data(self, dataframe: pd.DataFrame, stock: str, trading: bool) -> pd.DataFrame:
        """Process weekly data with technical indicators"""
        try:
            # Rename columns
            if 'ad_open' in dataframe.columns:
                dataframe = dataframe.rename(columns={
                    'ad_open': 'open', 
                    'ad_close': 'close', 
                    'ad_high': 'high', 
                    'ad_low': 'low'
                })
            
            # Weekly technical indicators
            if trading:
                dataframe['WHighest_2Y'] = self._get_high(dataframe, period=52*2)
                dataframe['WHighest_1Y'] = self._get_high(dataframe, period=52*1)
                dataframe['WSMA20'] = self._get_ma(dataframe['close'], 20, 52)
                dataframe['WSMA50'] = self._get_ma(dataframe['close'], 50, 52)
            else:
                dataframe['WHighest_2Y'] = self._get_high(dataframe, period=52*2).shift()
                dataframe['WHighest_1Y'] = self._get_high(dataframe, period=52*1).shift()
                dataframe['WSMA20'] = self._get_ma(dataframe['close'], 20, 52).shift()
                dataframe['WSMA50'] = self._get_ma(dataframe['close'], 50, 52).shift()
            
            # Rename to weekly format
            dataframe = dataframe.rename(columns={
                'open': 'Wopen', 
                'close': 'Wclose', 
                'high': 'Whigh', 
                'low': 'Wlow', 
                'volume': 'Wvolume'
            })
            
        except Exception as e:
            logger.error(f"Error in weekly data processing for {stock}: {e}")
            # Set default values
            for col in ['WHighest_2Y', 'WHighest_1Y', 'WSMA20', 'WSMA50']:
                dataframe[col] = 0
        
        return dataframe
    
    def _process_rs_data(self, dataframe: pd.DataFrame, stock: str, trading: bool) -> pd.DataFrame:
        """Process relative strength data"""
        try:
            # Basic RS processing
            if trading:
                dataframe['RS_4W'] = self._get_rs_value(dataframe, 4)
                dataframe['RS_52W'] = self._get_rs_value(dataframe, 52)
            else:
                dataframe['RS_4W'] = self._get_rs_value(dataframe, 4).shift()
                dataframe['RS_52W'] = self._get_rs_value(dataframe, 52).shift()
                
        except Exception as e:
            logger.error(f"Error in RS data processing for {stock}: {e}")
            dataframe['RS_4W'] = 0
            dataframe['RS_52W'] = 0
        
        return dataframe
    
    def _process_fundamental_data(self, dataframe: pd.DataFrame, stock: str, trading: bool) -> pd.DataFrame:
        """Process fundamental data (US market only)"""
        try:
            # Basic fundamental processing
            if 'value' in dataframe.columns:
                if trading:
                    dataframe['F_MA10'] = dataframe['value'].rolling(window=10).mean()
                    dataframe['F_MA20'] = dataframe['value'].rolling(window=20).mean()
                else:
                    dataframe['F_MA10'] = dataframe['value'].rolling(window=10).mean().shift()
                    dataframe['F_MA20'] = dataframe['value'].rolling(window=20).mean().shift()
            
        except Exception as e:
            logger.error(f"Error in fundamental data processing for {stock}: {e}")
            dataframe['F_MA10'] = 0
            dataframe['F_MA20'] = 0
        
        return dataframe
    
    # Technical Indicator Calculation Methods
    
    def _get_high(self, dataframe: pd.DataFrame, period: int) -> pd.Series:
        """Calculate rolling high over specified period"""
        if 'high' in dataframe.columns:
            return dataframe['high'].rolling(window=period, min_periods=1).max()
        return pd.Series(0, index=dataframe.index)
    
    def _get_ma(self, series: pd.Series, period: int, min_periods: int) -> pd.Series:
        """Calculate moving average"""
        return series.rolling(window=period, min_periods=min(period, min_periods)).mean()
    
    def _get_sma_momentum(self, dataframe: pd.DataFrame, ma_period: int, mom_period: int) -> pd.Series:
        """Calculate SMA momentum"""
        if 'close' in dataframe.columns:
            sma = dataframe['close'].rolling(window=ma_period, min_periods=1).mean()
            return sma.pct_change(periods=mom_period) * 100
        return pd.Series(0, index=dataframe.index)
    
    def _get_adr_pct(self, dataframe: pd.DataFrame, window: int) -> pd.Series:
        """Calculate Average Daily Range percentage"""
        try:
            if 'high' in dataframe.columns and 'low' in dataframe.columns and 'close' in dataframe.columns:
                daily_range = (dataframe['high'] - dataframe['low']) / dataframe['close'] * 100
                return daily_range.rolling(window=window, min_periods=1).mean()
        except:
            pass
        return pd.Series(0, index=dataframe.index)
    
    def _get_rs_value(self, dataframe: pd.DataFrame, period: int) -> pd.Series:
        """Calculate relative strength value"""
        if 'value' in dataframe.columns:
            return dataframe['value'].rolling(window=period, min_periods=1).mean()
        return pd.Series(0, index=dataframe.index)
    
    def _apply_date_filtering(self) -> None:
        """Apply date range filtering to all processed dataframes"""
        logger.info(f"Applying date filtering: {self.start_day} to {self.end_day}")
        
        for stock in self.universe:
            # Filter RS data
            if stock in self.df_RS:
                self.df_RS[stock] = self.df_RS[stock][
                    (self.df_RS[stock].index >= self.start_day) & 
                    (self.df_RS[stock].index <= self.end_day)
                ]
            
            # Filter weekly data
            if stock in self.df_W:
                self.df_W[stock] = self.df_W[stock][
                    (self.df_W[stock].index >= self.start_day) & 
                    (self.df_W[stock].index <= self.end_day)
                ]
            
            # Filter daily data
            if stock in self.df_D:
                self.df_D[stock] = self.df_D[stock][
                    (self.df_D[stock].index >= self.start_day) & 
                    (self.df_D[stock].index <= self.end_day)
                ]
            
            # Filter US-specific data
            if self.area == 'US':
                if stock in self.df_E:
                    self.df_E[stock] = self.df_E[stock][
                        (self.df_E[stock].index >= self.start_day) & 
                        (self.df_E[stock].index <= self.end_day)
                    ]
                
                if stock in self.df_F:
                    self.df_F[stock] = self.df_F[stock][
                        (self.df_F[stock].index >= self.start_day) & 
                        (self.df_F[stock].index <= self.end_day)
                    ]
    
    def _optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize dataframe memory usage
        Based on refer/Indicator/GenTradingData.py logic
        """
        if df.empty:
            return df
            
        try:
            for col in df.columns:
                if df[col].dtype == 'float64':
                    df[col] = pd.to_numeric(df[col], downcast='float')
                elif df[col].dtype == 'int64':
                    df[col] = pd.to_numeric(df[col], downcast='integer')
        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
        
        return df
    
    def return_processed_data(self) -> Tuple[Dict, Dict, Dict, Dict, Dict]:
        """
        Return all processed dataframes
        Based on refer/Indicator/GenTradingData.py ReturnFunc
        
        Returns:
            Tuple of (df_D, df_W, df_RS, df_E, df_F)
        """
        return self.df_D, self.df_W, self.df_RS, self.df_E, self.df_F
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of processed technical indicators
        
        Returns:
            Summary dictionary
        """
        summary = {
            'universe_count': len(self.universe),
            'area': self.area,
            'trading_mode': self.trading,
            'date_range': f"{self.start_day} to {self.end_day}",
            'processed_dataframes': {}
        }
        
        # Count processed symbols in each dataframe
        for df_name, df_dict in [
            ('daily', self.df_D), 
            ('weekly', self.df_W), 
            ('rs', self.df_RS),
            ('earnings', self.df_E),
            ('fundamental', self.df_F)
        ]:
            if df_dict:
                summary['processed_dataframes'][df_name] = {
                    'symbol_count': len(df_dict),
                    'symbols': list(df_dict.keys())[:5]  # First 5 symbols as sample
                }
        
        return summary
    
    def get_processed_dataframes(self) -> Tuple[Dict, Dict, Dict, Dict, Dict]:
        """
        Alias for return_processed_data for compatibility
        """
        return self.return_processed_data()