"""
Yahoo Finance Helper - Helper Agent Service
Based on reference code from refer/Helper/yfinance/YF_API_Helper_US.py
"""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class YFinanceHelper:
    """Yahoo Finance API Helper for US market data"""
    
    def __init__(self):
        pass
    
    def get_ohlcv(self, stock_code: str, p_code: str, start_date: datetime, 
                  end_date: datetime, ohlcv: str = "Y") -> pd.DataFrame:
        """
        Get OHLCV data from Yahoo Finance - from reference GetOhlcv
        
        Args:
            stock_code: Ticker symbol
            p_code: Period code ('W' for weekly, others for daily)
            start_date: Query start date
            end_date: Query end date
            ohlcv: 'Y' for adjusted prices, 'N' for original
            
        Returns:
            DataFrame with OHLCV and dividend/split information
        """
        try:
            ticker = yf.Ticker(stock_code)
            
            # Determine interval
            interval = "1wk" if p_code == "W" else "1d"
            
            # Download data
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=(ohlcv == "Y")
            )
            
            if df.empty:
                logger.warning(f"No data found for {stock_code}")
                return pd.DataFrame()
            
            # Round to 2 decimal places
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].round(2)
            
            # Rename columns to match expected format
            df.rename(columns={
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Dividends': 'dividends',
                'Stock Splits': 'stock_splits'
            }, inplace=True)
            
            # Handle timezone conversion
            if df.index.tz is not None:
                df.index = df.index.tz_convert('UTC')
            else:
                df.index = df.index.tz_localize('UTC')
            
            logger.info(f"Retrieved {len(df)} records for {stock_code}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {stock_code}: {e}")
            return pd.DataFrame()
    
    def get_asset_info(self, ticker: str, info_type: str = "quoteType") -> str:
        """
        Get asset information - from reference get_asset_info
        
        Args:
            ticker: Ticker symbol
            info_type: 'quoteType' for asset type, 'exchange' for exchange info
            
        Returns:
            Asset type ('ETF', 'Stock', etc.) or exchange name
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                logger.warning(f"No info found for {ticker}")
                return ""
            
            result = info.get(info_type, "")
            
            if info_type == "quoteType":
                # Standardize quote types
                if result.upper() in ["ETF", "MUTUALFUND"]:
                    return "ETF"
                elif result.upper() in ["EQUITY", "STOCK"]:
                    return "Stock"
                else:
                    return result
            
            return str(result)
            
        except Exception as e:
            logger.error(f"Error getting asset info for {ticker}: {e}")
            return ""
    
    def get_fx_rate(self, pair: str, period: str = "1d", interval: str = "1d") -> pd.DataFrame:
        """
        Get exchange rate data - from reference get_fx_rate
        
        Args:
            pair: Exchange rate symbol (e.g., "USDKRW=X", "HKDKRW=X")
            period: Query period (default: "1d")
            interval: Data interval (default: "1d")
            
        Returns:
            DataFrame containing historical exchange rate data
        """
        try:
            fx = yf.Ticker(pair)
            
            df = fx.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No exchange rate data found for {pair}")
                return pd.DataFrame()
            
            # Rename columns for consistency
            df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low', 
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)
            
            logger.info(f"Retrieved exchange rate data for {pair}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting exchange rate for {pair}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, ticker: str) -> float:
        """Get current price for a ticker"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try different price fields
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field] is not None:
                    return float(info[field])
            
            # Fallback to latest close price
            history = stock.history(period="1d")
            if not history.empty:
                return float(history['Close'].iloc[-1])
            
            logger.warning(f"No current price found for {ticker}")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return 0.0
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """Get comprehensive company information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                return {}
            
            # Extract key information
            company_info = {
                'symbol': ticker,
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'profit_margins': info.get('profitMargins', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'ex_dividend_date': info.get('exDividendDate', None),
                'beta': info.get('beta', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0),
                'avg_volume': info.get('averageVolume', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0),
                'insider_percent': info.get('heldPercentInsiders', 0),
                'institution_percent': info.get('heldPercentInstitutions', 0)
            }
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error getting company info for {ticker}: {e}")
            return {}
    
    def search_tickers(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search for tickers by company name or symbol"""
        try:
            # This is a simple implementation
            # In practice, you might want to use a more comprehensive search
            results = []
            
            # Try to get info for the query as a symbol
            try:
                stock = yf.Ticker(query.upper())
                info = stock.info
                
                if info and 'longName' in info:
                    results.append({
                        'symbol': query.upper(),
                        'name': info.get('longName', ''),
                        'type': info.get('quoteType', 'EQUITY')
                    })
            except:
                pass
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching tickers for {query}: {e}")
            return []
    
    def get_financial_data(self, ticker: str, statement_type: str = "income") -> pd.DataFrame:
        """
        Get financial statement data
        
        Args:
            ticker: Ticker symbol
            statement_type: 'income', 'balance', 'cashflow'
        """
        try:
            stock = yf.Ticker(ticker)
            
            if statement_type.lower() == "income":
                df = stock.financials
            elif statement_type.lower() == "balance":
                df = stock.balance_sheet
            elif statement_type.lower() == "cashflow":
                df = stock.cashflow
            else:
                logger.error(f"Invalid statement type: {statement_type}")
                return pd.DataFrame()
            
            if df.empty:
                logger.warning(f"No {statement_type} data found for {ticker}")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting {statement_type} data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_analyst_recommendations(self, ticker: str) -> pd.DataFrame:
        """Get analyst recommendations"""
        try:
            stock = yf.Ticker(ticker)
            recommendations = stock.recommendations
            
            if recommendations is None or recommendations.empty:
                logger.warning(f"No analyst recommendations found for {ticker}")
                return pd.DataFrame()
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting analyst recommendations for {ticker}: {e}")
            return pd.DataFrame()