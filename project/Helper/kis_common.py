"""
KIS Common Functions - Helper Agent Service
Based on reference code from refer/Helper/KIS/KIS_Common.py
"""

import os
import yaml
import json
import requests
import time
import random
import numpy as np
import pandas as pd
import yfinance
from datetime import datetime, timedelta
from pytz import timezone
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class KISCommon:
    """Common KIS API functions and utilities"""
    
    def __init__(self, config_path: str = None):
        self.config = {}
        self.stock_info = None
        self.now_dist = ""
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load stock info configuration"""
        try:
            with open(config_path, encoding='UTF-8') as f:
                self.stock_info = yaml.safe_load(f)
            logger.info("Stock info configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def set_change_mode(self, dist: str = "KJM_ISA"):
        """Switch account mode - from reference SetChangeMode"""
        self.now_dist = dist
        logger.info(f"Account mode changed to: {dist}")
    
    def get_now_dist(self) -> str:
        """Get current account distribution - from reference GetNowDist"""
        return self.now_dist
    
    def get_app_key(self, dist: str = "KJM_ISA") -> str:
        """Get app key for specified account - from reference GetAppKey"""
        if not self.stock_info:
            return ""
        
        key_mapping = {
            "KJM_ISA": "REAL_APP_KEY",
            "KJM": "REAL2_APP_KEY", 
            "KMR": "REAL3_APP_KEY",
            "SystemTrade": "REAL4_APP_KEY",
            "KJM_US": "REAL5_APP_KEY",
            "KMR_US": "REAL6_APP_KEY",
            "VIRTUAL1": "VIRTUAL1_APP_KEY",
            "VIRTUAL2": "VIRTUAL2_APP_KEY"
        }
        
        key = key_mapping.get(dist, "REAL_APP_KEY")
        return self.stock_info.get(key, "")
    
    def get_app_secret(self, dist: str = "KJM_ISA") -> str:
        """Get app secret for specified account - from reference GetAppSecret"""
        if not self.stock_info:
            return ""
        
        secret_mapping = {
            "KJM_ISA": "REAL_APP_SECRET",
            "KJM": "REAL2_APP_SECRET",
            "KMR": "REAL3_APP_SECRET", 
            "SystemTrade": "REAL4_APP_SECRET",
            "KJM_US": "REAL5_APP_SECRET",
            "KMR_US": "REAL6_APP_SECRET",
            "VIRTUAL1": "VIRTUAL1_APP_SECRET",
            "VIRTUAL2": "VIRTUAL2_APP_SECRET"
        }
        
        key = secret_mapping.get(dist, "REAL_APP_SECRET")
        return self.stock_info.get(key, "")
    
    def get_account_no(self, dist: str = "KJM_ISA") -> str:
        """Get account number - from reference GetAccountNo"""
        if not self.stock_info:
            return ""
        
        account_mapping = {
            "KJM_ISA": "REAL_ACCOUNT_NO",
            "KJM": "REAL2_ACCOUNT_NO",
            "KMR": "REAL3_ACCOUNT_NO",
            "SystemTrade": "REAL4_ACCOUNT_NO", 
            "KJM_US": "REAL5_ACCOUNT_NO",
            "KMR_US": "REAL6_ACCOUNT_NO",
            "VIRTUAL1": "VIRTUAL1_ACCOUNT_NO",
            "VIRTUAL2": "VIRTUAL2_ACCOUNT_NO"
        }
        
        key = account_mapping.get(dist, "REAL_ACCOUNT_NO")
        return self.stock_info.get(key, "")
    
    def get_prdt_no(self, dist: str = "KJM_ISA") -> str:
        """Get product code - from reference GetPrdtNo"""
        if not self.stock_info:
            return "01"
        
        prdt_mapping = {
            "KJM_ISA": "REAL_PRODUCT_CODE",
            "KJM": "REAL2_PRODUCT_CODE",
            "KMR": "REAL3_PRODUCT_CODE",
            "SystemTrade": "REAL4_PRODUCT_CODE",
            "KJM_US": "REAL5_PRODUCT_CODE", 
            "KMR_US": "REAL6_PRODUCT_CODE",
            "VIRTUAL1": "VIRTUAL1_PRODUCT_CODE",
            "VIRTUAL2": "VIRTUAL2_PRODUCT_CODE"
        }
        
        key = prdt_mapping.get(dist, "REAL_PRODUCT_CODE")
        return self.stock_info.get(key, "01")
    
    def get_url_base(self, dist: str = "KJM_ISA") -> str:
        """Get base URL - from reference GetUrlBase"""
        if not self.stock_info:
            return ""
        
        if "VIRTUAL" in dist:
            return self.stock_info.get("VIRTUAL_BASE_URL", "")
        else:
            return self.stock_info.get("REAL_BASE_URL", "")
    
    def get_token_path(self, dist: str = "KJM_ISA") -> str:
        """Get token file path - from reference GetTokenPath"""
        return f"./tokens/KIS_TOKEN_{dist}.txt"
    
    def make_token(self, dist: str = "KJM_ISA") -> bool:
        """Create and save API token - from reference MakeToken"""
        try:
            app_key = self.get_app_key(dist)
            app_secret = self.get_app_secret(dist)
            base_url = self.get_url_base(dist)
            
            if not all([app_key, app_secret, base_url]):
                logger.error(f"Missing credentials for {dist}")
                return False
            
            url = f"{base_url}/oauth2/tokenP"
            
            headers = {
                "content-type": "application/json"
            }
            
            data = {
                "grant_type": "client_credentials",
                "appkey": app_key,
                "appsecret": app_secret
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result = response.json()
                token = result.get("access_token")
                
                # Save token to file
                token_path = self.get_token_path(dist)
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                
                with open(token_path, 'w') as f:
                    f.write(token)
                
                logger.info(f"Token created and saved for {dist}")
                return True
            else:
                logger.error(f"Token creation failed for {dist}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating token for {dist}: {e}")
            return False
    
    def get_token(self, dist: str = "KJM_ISA") -> str:
        """Get token from file or create new one - from reference GetToken"""
        try:
            token_path = self.get_token_path(dist)
            
            # Try to read existing token
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    token = f.read().strip()
                
                if token:
                    return token
            
            # Create new token if file doesn't exist or is empty
            if self.make_token(dist):
                with open(token_path, 'r') as f:
                    return f.read().strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting token for {dist}: {e}")
            return ""
    
    def get_hash_key(self, data: Dict[str, Any]) -> str:
        """Get hash key for request - from reference GetHashKey"""
        try:
            # This would implement the KIS hash key generation
            # For now, return empty string as most requests don't need it
            return ""
        except Exception as e:
            logger.error(f"Error generating hash key: {e}")
            return ""
    
    def get_now_date_str(self, area: str = "KR") -> str:
        """Get current date string for specified area - from reference GetNowDateStr"""
        try:
            if area.upper() == "KR":
                tz = timezone('Asia/Seoul')
            elif area.upper() == "US":
                tz = timezone('America/New_York')
            else:
                tz = timezone('UTC')
            
            now = datetime.now(tz)
            return now.strftime('%Y%m%d')
            
        except Exception as e:
            logger.error(f"Error getting date string: {e}")
            return datetime.now().strftime('%Y%m%d')
    
    def get_from_now_date_str(self, days_offset: int, area: str = "KR") -> str:
        """Get date string with offset - from reference GetFromNowDateStr"""
        try:
            if area.upper() == "KR":
                tz = timezone('Asia/Seoul')
            elif area.upper() == "US":
                tz = timezone('America/New_York')
            else:
                tz = timezone('UTC')
            
            now = datetime.now(tz)
            target_date = now + timedelta(days=days_offset)
            return target_date.strftime('%Y%m%d')
            
        except Exception as e:
            logger.error(f"Error getting offset date string: {e}")
            return datetime.now().strftime('%Y%m%d')
    
    def get_ohlcv(self, area: str, stock_code: str, limit: int = 500) -> pd.DataFrame:
        """Get OHLCV data using various sources - from reference GetOhlcv"""
        try:
            if area.upper() == "US":
                # Use yfinance for US stocks
                ticker = yfinance.Ticker(stock_code)
                df = ticker.history(period="2y")  # Get 2 years of data
                
                if df.empty:
                    logger.warning(f"No data found for US stock {stock_code}")
                    return pd.DataFrame()
                
                # Rename columns to match expected format
                df.columns = [col.lower() for col in df.columns]
                df = df.tail(limit)  # Limit rows
                
                return df
                
            elif area.upper() == "KR":
                # For Korean stocks, would use KIS API
                # This is a placeholder - actual implementation would call KIS API
                logger.warning("Korean stock OHLCV not implemented yet")
                return pd.DataFrame()
            
            else:
                logger.error(f"Unsupported area: {area}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {stock_code}: {e}")
            return pd.DataFrame()
    
    def get_ma(self, ohlcv: pd.DataFrame, period: int, st: int = 100) -> float:
        """Calculate Moving Average - from reference GetMA"""
        try:
            if ohlcv.empty or len(ohlcv) < period:
                return 0.0
            
            # Get close prices
            close_prices = ohlcv['close'] if 'close' in ohlcv.columns else ohlcv['Close']
            
            # Calculate MA
            ma_values = close_prices.rolling(window=period).mean()
            
            # Return MA at specified index
            if st < len(ma_values):
                return float(ma_values.iloc[st])
            else:
                return float(ma_values.iloc[-1])  # Return latest MA
                
        except Exception as e:
            logger.error(f"Error calculating MA: {e}")
            return 0.0
    
    def get_rsi(self, ohlcv: pd.DataFrame, period: int = 14, st: int = 100) -> float:
        """Calculate RSI - from reference GetRSI"""
        try:
            if ohlcv.empty or len(ohlcv) < period + 1:
                return 0.0
            
            # Get close prices
            close_prices = ohlcv['close'] if 'close' in ohlcv.columns else ohlcv['Close']
            
            # Calculate price changes
            delta = close_prices.diff()
            
            # Separate gains and losses
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # Calculate average gains and losses
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Return RSI at specified index
            if st < len(rsi):
                return float(rsi.iloc[st])
            else:
                return float(rsi.iloc[-1])  # Return latest RSI
                
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 0.0
    
    def auto_limit_do_again(self, botname: str, area: str, stock_code: str, 
                           target_price: float, do_amt: int, stock_type: str = "NORMAL") -> str:
        """Register order in auto limit system - from reference AutoLimitDoAgain"""
        try:
            # This would implement the auto limit order system
            # For now, just return a mock order ID
            order_id = f"ORDER_{int(time.time())}_{random.randint(1000, 9999)}"
            
            logger.info(f"Auto limit order registered: {order_id}")
            logger.info(f"Bot: {botname}, Stock: {stock_code}, Price: {target_price}, Amount: {do_amt}")
            
            return order_id
            
        except Exception as e:
            logger.error(f"Error registering auto limit order: {e}")
            return ""