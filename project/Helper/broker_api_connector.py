"""
Broker API Connector - Helper Agent Service
Manages connections to various broker APIs including KIS, LS Securities
Based on reference code from refer/Helper/KIS and refer/Helper/LS
"""

import os
import json
import yaml
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import pytz
import math

logger = logging.getLogger(__name__)

class BrokerAPIBase(ABC):
    """Base class for broker API implementations"""
    
    def __init__(self, config_path: str = None):
        self.config = {}
        self.token = None
        self.base_url = ""
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load broker configuration from file"""
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
    def authenticate(self) -> bool:
        """Authenticate with broker API"""
        pass
    
    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance information"""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int, price: float = None) -> Dict[str, Any]:
        """Place an order"""
        pass

class KISBrokerAPI(BrokerAPIBase):
    """Korea Investment & Securities API implementation based on reference code"""
    
    def __init__(self, config_path: str = None, account_type: str = "REAL"):
        super().__init__(config_path)
        self.account_type = account_type
        self.app_key = ""
        self.app_secret = ""
        self.account_no = ""
        self.product_code = ""
        self.current_dist = ""
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup API credentials based on account type"""
        if not self.config:
            return

        try:
            if self.account_type == "REAL":
                self.app_key = self.config.get("REAL_APP_KEY", "")
                self.app_secret = self.config.get("REAL_APP_SECRET", "")
                self.account_no = self.config.get("REAL_CANO", "")
                self.product_code = self.config.get("REAL_ACNT_PRDT_CD", "01")
                self.base_url = self.config.get("REAL_URL", "")
            elif self.account_type == "VIRTUAL":
                self.app_key = self.config.get("VIRTUAL1_APP_KEY", "")
                self.app_secret = self.config.get("VIRTUAL1_APP_SECRET", "")
                self.account_no = self.config.get("VIRTUAL1_CANO", "")
                self.product_code = self.config.get("VIRTUAL1_ACNT_PRDT_CD", "01")
                self.base_url = self.config.get("VIRTUAL_URL", "")

            self.current_dist = self.account_type

            # 디버깅용 로그
            logger.info(f"KIS API 설정 완료:")
            logger.info(f"  계정 타입: {self.account_type}")
            logger.info(f"  계좌번호: {self.account_no}")
            logger.info(f"  상품코드: {self.product_code}")
            logger.info(f"  기본 URL: {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to setup KIS credentials: {e}")
    
    def set_change_mode(self, dist: str = "REAL"):
        """Switch account mode - similar to reference SetChangeMode"""
        self.current_dist = dist
        self.account_type = dist
        self._setup_credentials()
    
    def authenticate(self) -> bool:
        """Authenticate with KIS API and get access token"""
        try:
            url = f"{self.base_url}/oauth2/tokenP"
            
            headers = {
                "content-type": "application/json"
            }
            
            data = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                logger.info("KIS authentication successful")
                return True
            else:
                logger.error(f"KIS authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"KIS authentication error: {e}")
            return False
    
    def is_market_open(self) -> bool:
        """Check if Korean stock market is open - based on reference IsMarketOpen"""
        try:
            # Use Korea timezone
            now_time = datetime.now(pytz.timezone('Asia/Seoul'))
            
            # Check if it's weekend
            if now_time.weekday() >= 5:  # Saturday or Sunday
                return False
            
            # Check market hours (9:00 AM to 3:30 PM)
            if now_time.hour < 9 or now_time.hour > 15:
                return False
            
            if now_time.hour == 15 and now_time.minute > 30:
                return False
            
            # Additional API check for holidays using dummy order
            try:
                result = self._test_market_status_with_dummy_order()
                return result
            except:
                return True  # Default to open if API check fails
                
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
    
    def _test_market_status_with_dummy_order(self) -> bool:
        """Test market status with dummy order - based on reference code"""
        try:
            # Use dummy ETF order to check market status
            result = self.make_sell_limit_order("069500", 1, 1, "CHECK")
            
            # Market closed error codes from reference
            if result == "APBK0918" or result == "APBK0919":
                logger.info("Market is closed (holiday or non-trading day)")
                return False
            else:
                logger.info("Market is open")
                return True
                
        except Exception as e:
            logger.warning(f"Market status check failed: {e}")
            return True  # Assume open if check fails
    
    def price_adjust(self, price: float, stock_code: str) -> int:
        """Adjust price to valid tick size - based on reference PriceAdjust"""
        try:
            current_price = self.get_current_price(stock_code)
            price = int(price)
            
            # Determine tick size based on price range (Korean market rules)
            if price < 2000:
                tick = 1
            elif price < 5000:
                tick = 5
            elif price < 20000:
                tick = 10
            elif price < 50000:
                tick = 50
            elif price < 200000:
                tick = 100
            elif price < 500000:
                tick = 500
            else:
                tick = 1000
            
            # Round down to nearest tick
            adjusted_price = math.floor(price / tick) * tick
            
            return adjusted_price
            
        except Exception as e:
            logger.error(f"Error adjusting price: {e}")
            return int(price)
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for Korean stock"""
        try:
            if not self.token:
                if not self.authenticate():
                    raise Exception("Authentication failed")
            
            time.sleep(0.1)  # Rate limiting
            
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "FHKST01010100"
            }
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                output = result.get("output", {})
                return float(output.get("stck_prpr", 0))
            else:
                logger.error(f"Failed to get price for {symbol}: {response.status_code}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance information - based on reference GetBalance"""
        try:
            if not self.token:
                if not self.authenticate():
                    raise Exception("Authentication failed")
            
            time.sleep(0.2)  # Rate limiting as in reference
            
            path = "uapi/domestic-stock/v1/trading/inquire-balance"
            url = f"{self.base_url}/{path}"
            
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "TTTC8434R" if self.account_type == "REAL" else "VTTC8434R"
            }
            
            params = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.product_code,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                output2 = result.get("output2", [{}])[0]
                
                return {
                    "StockMoney": float(output2.get("scts_evlu_amt", 0)),      # Stock valuation
                    "RemainMoney": float(output2.get("dnca_tot_amt", 0)),     # Cash balance
                    "TotalMoney": float(output2.get("tot_evlu_amt", 0)),      # Total assets
                    "StockRevenue": float(output2.get("evlu_pfls_smtl_amt", 0)) # P&L
                }
            else:
                logger.error(f"Failed to get balance: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {}
    
    def make_buy_limit_order(self, stock_code: str, amt: int, price: float, adjust_amt: bool = False) -> Dict[str, Any]:
        """Make buy limit order - based on reference MakeBuyLimitOrder"""
        try:
            if not self.token:
                if not self.authenticate():
                    raise Exception("Authentication failed")
            
            # Adjust price to valid tick size
            adjusted_price = self.price_adjust(price, stock_code)
            
            # Auto adjust quantity if requested
            if adjust_amt:
                balance = self.get_balance()
                available_cash = balance.get("RemainMoney", 0)
                max_qty = int(available_cash / adjusted_price)
                amt = min(amt, max_qty)
            
            return self._place_order(stock_code, "BUY", amt, adjusted_price)
            
        except Exception as e:
            logger.error(f"Error placing buy order: {e}")
            return {"success": False, "error": str(e)}
    
    def make_sell_limit_order(self, stock_code: str, amt: int, price: float, mode: str = "NORMAL") -> Dict[str, Any]:
        """Make sell limit order - based on reference MakeSellLimitOrder"""
        try:
            if mode == "CHECK":
                # This is a market status check, return specific codes
                if not self.is_market_open():
                    return "APBK0918"  # Market closed code
                else:
                    return "SUCCESS"
            
            if not self.token:
                if not self.authenticate():
                    raise Exception("Authentication failed")
            
            # Adjust price to valid tick size
            adjusted_price = self.price_adjust(price, stock_code)
            
            return self._place_order(stock_code, "SELL", amt, adjusted_price)
            
        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return {"success": False, "error": str(e)}
    
    def _place_order(self, symbol: str, side: str, quantity: int, price: float) -> Dict[str, Any]:
        """Internal method to place orders"""
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            # Determine transaction ID based on side and account type
            if side.upper() == "BUY":
                tr_id = "TTTC0802U" if self.account_type == "REAL" else "VTTC0802U"
            else:  # SELL
                tr_id = "TTTC0801U" if self.account_type == "REAL" else "VTTC0801U"
            
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": tr_id
            }
            
            data = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.product_code,
                "PDNO": symbol,
                "ORD_DVSN": "00",  # 00: limit order
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(int(price))
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "order_id": result.get("output", {}).get("ODNO", ""),
                    "message": result.get("msg1", ""),
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Order failed: {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def place_order(self, symbol: str, side: str, quantity: int, price: float = None) -> Dict[str, Any]:
        """Generic place order method"""
        if side.upper() == "BUY":
            return self.make_buy_limit_order(symbol, quantity, price)
        elif side.upper() == "SELL":
            return self.make_sell_limit_order(symbol, quantity, price)
        else:
            return {"success": False, "error": f"Invalid side: {side}"}
    
    def get_my_stock_list(self) -> List[Dict[str, Any]]:
        """Get list of currently held stocks - based on reference GetMyStockList"""
        try:
            if not self.token:
                if not self.authenticate():
                    raise Exception("Authentication failed")
            
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "TTTC8434R" if self.account_type == "REAL" else "VTTC8434R"
            }
            
            params = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.product_code,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "01",  # 01 for stock list
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                output1 = result.get("output1", [])
                
                stock_list = []
                for stock in output1:
                    if int(stock.get("hldg_qty", 0)) > 0:  # Only stocks with holdings
                        stock_list.append({
                            "stock_code": stock.get("pdno", ""),
                            "stock_name": stock.get("prdt_name", ""),
                            "quantity": int(stock.get("hldg_qty", 0)),
                            "avg_price": float(stock.get("pchs_avg_pric", 0)),
                            "current_price": float(stock.get("prpr", 0)),
                            "evaluation_amount": float(stock.get("evlu_amt", 0)),
                            "profit_loss": float(stock.get("evlu_pfls_amt", 0)),
                            "profit_rate": float(stock.get("evlu_pfls_rt", 0))
                        })
                
                return stock_list
            else:
                logger.error(f"Failed to get stock list: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting stock list: {e}")
            return []

class BrokerAPIManager:
    """Manager class for multiple broker APIs"""
    
    def __init__(self):
        self.brokers = {}
        self.active_broker = None
    
    def add_broker(self, name: str, broker_api: BrokerAPIBase):
        """Add a broker API instance"""
        self.brokers[name] = broker_api
        
        # Set as active if it's the first one
        if not self.active_broker:
            self.active_broker = name
    
    def set_active_broker(self, name: str):
        """Set the active broker for operations"""
        if name in self.brokers:
            self.active_broker = name
        else:
            raise ValueError(f"Broker {name} not found")
    
    def get_active_broker(self) -> BrokerAPIBase:
        """Get the currently active broker API"""
        if self.active_broker and self.active_broker in self.brokers:
            return self.brokers[self.active_broker]
        else:
            raise ValueError("No active broker set")
    
    def is_market_open(self, broker_name: str = None) -> bool:
        """Check if market is open for specified or active broker"""
        broker = self.brokers.get(broker_name) if broker_name else self.get_active_broker()
        return broker.is_market_open()
    
    def get_current_price(self, symbol: str, broker_name: str = None) -> float:
        """Get current price from specified or active broker"""
        broker = self.brokers.get(broker_name) if broker_name else self.get_active_broker()
        return broker.get_current_price(symbol)
    
    def get_balance(self, broker_name: str = None) -> Dict[str, Any]:
        """Get balance from specified or active broker"""
        broker = self.brokers.get(broker_name) if broker_name else self.get_active_broker()
        return broker.get_balance()
    
    def place_order(self, symbol: str, side: str, quantity: int, price: float = None, broker_name: str = None) -> Dict[str, Any]:
        """Place order through specified or active broker"""
        broker = self.brokers.get(broker_name) if broker_name else self.get_active_broker()
        return broker.place_order(symbol, side, quantity, price)