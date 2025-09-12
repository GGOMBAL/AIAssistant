"""
Data Provider API - Helper Agent Service
Manages connections to external data providers including Alpha Vantage, Yahoo Finance
"""

import os
import json
import yaml
import time
import requests
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import pytz
import csv

logger = logging.getLogger(__name__)

class DataProviderBase(ABC):
    """Base class for data provider implementations"""
    
    def __init__(self, config_path: str = None):
        self.config = {}
        self.api_key = ""
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load provider configuration from file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, start_date: datetime = None, end_date: datetime = None, 
                  interval: str = "1d") -> pd.DataFrame:
        """Get OHLCV data for a symbol"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        pass

class AlphaVantageAPI(DataProviderBase):
    """Alpha Vantage API implementation for US market data"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.api_key = self.config.get("ALPHA_VANTAGE_API_KEY", "") if self.config else ""
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls per minute
    
    def get_ticker_list(self, market: str = 'NASDAQ', asset_type: str = 'Stock', active: bool = True) -> List[str]:
        """Get list of tickers for specified market"""
        try:
            if active:
                url = f"{self.base_url}?function=LISTING_STATUS&apikey={self.api_key}"
            else:
                url = f"{self.base_url}?function=LISTING_STATUS&state=delisted&apikey={self.api_key}"
            
            response = requests.get(url)
            
            if response.status_code == 200:
                decoded_content = response.content.decode('utf-8')
                cr = csv.reader(decoded_content.splitlines(), delimiter=',')
                ticker_list = []
                
                for row in cr:
                    if len(row) >= 4 and row[2] == market and row[3] == asset_type:
                        ticker_list.append(row[0])
                
                return ticker_list
            else:
                logger.error(f"Failed to get ticker list: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting ticker list: {e}")
            return []
    
    def get_ohlcv_intraday(self, symbol: str, interval: str = "1min", outputsize: str = "compact") -> pd.DataFrame:
        """Get intraday OHLCV data"""
        try:
            url = f"{self.base_url}?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&extended_hours=false&outputsize={outputsize}&apikey={self.api_key}"
            
            response = requests.get(url)
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return pd.DataFrame()
                
                period_key = f'Time Series ({interval})'
                if period_key not in data:
                    logger.error(f"No data found for {symbol}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(data[period_key]).T
                df.index = pd.to_datetime(df.index)
                df = df.apply(pd.to_numeric)
                df.index.name = 'Datetime'
                
                # Rename columns
                column_mapping = {
                    '1. open': 'open',
                    '2. high': 'high',
                    '3. low': 'low',
                    '4. close': 'close',
                    '5. volume': 'volume'
                }
                
                df = df.rename(columns=column_mapping)
                df = df[['open', 'high', 'low', 'close', 'volume']]
                df.sort_index(inplace=True)
                
                # Convert to UTC timezone
                if df.index.tz is None:
                    df.index = df.index.tz_localize('US/Eastern')
                df.index = df.index.tz_convert('UTC')
                
                return df
            else:
                logger.error(f"Failed to get intraday data for {symbol}: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_ohlcv(self, symbol: str, start_date: datetime = None, end_date: datetime = None, 
                  interval: str = "1d") -> pd.DataFrame:
        """Get daily OHLCV data"""
        try:
            if interval != "1d":
                return self.get_ohlcv_intraday(symbol, interval)
            
            url = f"{self.base_url}?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={self.api_key}"
            
            response = requests.get(url)
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                
                if "Error Message" in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return pd.DataFrame()
                
                if "Time Series (Daily)" not in data:
                    logger.error(f"No data found for {symbol}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(data["Time Series (Daily)"]).T
                df.index = pd.to_datetime(df.index)
                df = df.apply(pd.to_numeric)
                df.index.name = 'Date'
                
                # Rename columns
                column_mapping = {
                    '1. open': 'open',
                    '2. high': 'high',
                    '3. low': 'low',
                    '4. close': 'close',
                    '5. adjusted close': 'adj_close',
                    '6. volume': 'volume',
                    '7. dividend amount': 'dividend',
                    '8. split coefficient': 'split_coefficient'
                }
                
                df = df.rename(columns=column_mapping)
                df.sort_index(inplace=True)
                
                # Filter by date range if provided
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                
                return df
            else:
                logger.error(f"Failed to get daily data for {symbol}: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price using Alpha Vantage quote endpoint"""
        try:
            url = f"{self.base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
            
            response = requests.get(url)
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                
                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    return float(quote.get("05. price", 0))
                else:
                    logger.error(f"No quote data found for {symbol}")
                    return 0.0
            else:
                logger.error(f"Failed to get current price for {symbol}: {response.status_code}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental analysis data"""
        try:
            url = f"{self.base_url}?function=OVERVIEW&symbol={symbol}&apikey={self.api_key}"
            
            response = requests.get(url)
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                
                if "Symbol" in data:
                    return data
                else:
                    logger.error(f"No fundamental data found for {symbol}")
                    return {}
            else:
                logger.error(f"Failed to get fundamental data for {symbol}: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting fundamental data for {symbol}: {e}")
            return {}
    
    def get_earnings_data(self, symbol: str) -> pd.DataFrame:
        """Get quarterly earnings data"""
        try:
            url = f"{self.base_url}?function=EARNINGS&symbol={symbol}&apikey={self.api_key}"
            
            response = requests.get(url)
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                
                if "quarterlyEarnings" in data:
                    df = pd.DataFrame(data["quarterlyEarnings"])
                    return df
                else:
                    logger.error(f"No earnings data found for {symbol}")
                    return pd.DataFrame()
            else:
                logger.error(f"Failed to get earnings data for {symbol}: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting earnings data for {symbol}: {e}")
            return pd.DataFrame()

class YahooFinanceAPI(DataProviderBase):
    """Yahoo Finance API implementation"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
    
    def get_ohlcv(self, symbol: str, start_date: datetime = None, end_date: datetime = None, 
                  interval: str = "1d") -> pd.DataFrame:
        """Get OHLCV data using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=365)
            
            # Download data
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Round to 2 decimal places
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].round(2)
            
            # Handle timezone
            if df.index.tz is not None:
                df.index = df.index.tz_convert('UTC')
            else:
                df.index = df.index.tz_localize('UTC')
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price using yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    return float(info[field])
            
            # Fallback to latest close price
            history = ticker.history(period="1d")
            if not history.empty:
                return float(history['Close'].iloc[-1])
            
            logger.warning(f"No current price found for {symbol}")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    def get_asset_info(self, symbol: str, info_type: str = "quoteType") -> str:
        """Get asset information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return str(info.get(info_type, ""))
            
        except Exception as e:
            logger.error(f"Error getting asset info for {symbol}: {e}")
            return ""
    
    def get_exchange_rate(self, pair: str, period: str = "1d", interval: str = "1d") -> pd.DataFrame:
        """Get exchange rate data"""
        try:
            ticker = yf.Ticker(pair)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No exchange rate data found for {pair}")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting exchange rate for {pair}: {e}")
            return pd.DataFrame()

class DataProviderManager:
    """Manager class for multiple data providers"""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = None
    
    def add_provider(self, name: str, provider: DataProviderBase):
        """Add a data provider"""
        self.providers[name] = provider
        
        # Set as default if it's the first one
        if not self.default_provider:
            self.default_provider = name
    
    def set_default_provider(self, name: str):
        """Set the default provider"""
        if name in self.providers:
            self.default_provider = name
        else:
            raise ValueError(f"Provider {name} not found")
    
    def get_provider(self, name: str = None) -> DataProviderBase:
        """Get a specific provider or the default one"""
        provider_name = name or self.default_provider
        
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        else:
            raise ValueError(f"Provider {provider_name} not found")
    
    def get_ohlcv(self, symbol: str, start_date: datetime = None, end_date: datetime = None, 
                  interval: str = "1d", provider: str = None) -> pd.DataFrame:
        """Get OHLCV data from specified or default provider"""
        provider_obj = self.get_provider(provider)
        return provider_obj.get_ohlcv(symbol, start_date, end_date, interval)
    
    def get_current_price(self, symbol: str, provider: str = None) -> float:
        """Get current price from specified or default provider"""
        provider_obj = self.get_provider(provider)
        return provider_obj.get_current_price(symbol)
    
    def get_multiple_prices(self, symbols: List[str], provider: str = None) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        provider_obj = self.get_provider(provider)
        prices = {}
        
        for symbol in symbols:
            try:
                prices[symbol] = provider_obj.get_current_price(symbol)
            except Exception as e:
                logger.error(f"Error getting price for {symbol}: {e}")
                prices[symbol] = 0.0
        
        return prices