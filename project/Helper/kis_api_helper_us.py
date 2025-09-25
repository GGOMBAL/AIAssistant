"""
KIS API Helper for US Markets - Helper Agent Service
Based on reference code from refer/Helper/KIS/KIS_API_Helper_US.py
"""

import requests
import json
import logging
from datetime import datetime, timedelta, timezone, time
from pytz import timezone as pytz_timezone
import pprint
import time as time_module
import yaml
import pandas as pd
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class KISUSHelper:
    """KIS API Helper for US market operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app_key = config.get("app_key", "")
        self.app_secret = config.get("app_secret", "")
        self.account_no = config.get("account_no", "")
        self.product_code = config.get("product_code", "")
        self.base_url = config.get("base_url", "")
        self.token = None
    
    def check_and_refresh_token_if_expired(self, response):
        """Token expiry check and auto renewal - from reference"""
        try:
            if response.status_code != 200:
                response_data = response.json()
                if response_data.get("msg_cd") == "EGW00123":
                    logger.warning("Token expired, attempting to refresh")
                    
                    # Force token refresh
                    try:
                        self.make_token()
                        time_module.sleep(3)
                        logger.info("Token refreshed successfully")
                        return True
                    except Exception as token_error:
                        logger.error(f"Token refresh failed: {token_error}")
                        return False
        except Exception as e:
            logger.error(f"Error checking token: {e}")
        
        return False
    
    def make_request_with_token_retry(self, func, *args, **kwargs):
        """Request function with token retry - from reference"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                response = func(*args, **kwargs)
                
                # Check for token expiry
                if self.check_and_refresh_token_if_expired(response):
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying request (attempt {attempt + 2}/{max_retries})")
                        continue
                
                return response
                
            except Exception as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
        
        return response
    
    def market_open_type(self, area: str = "US") -> str:
        """
        Market status check for US/HK markets - from reference MarketOpenType
        area == "US" : US stock market (Pre-market/Regular/After-market/Closed)
        area == "HK" : Hong Kong stock market (Regular/Closed)
        """
        now_utc = datetime.now(timezone.utc)
        
        if area.upper() == "US":
            # Convert to New York timezone
            ny_tz = pytz_timezone("America/New_York")
            now_local = now_utc.astimezone(ny_tz).time()
            
            pre_open = time(4, 0)      # 4:00 AM
            reg_open = time(9, 30)     # 9:30 AM
            reg_close = time(16, 0)    # 4:00 PM
            after_close = time(20, 0)  # 8:00 PM
            
            if pre_open <= now_local < reg_open:
                return "Pre-Market"
            elif reg_open <= now_local < reg_close:
                return "NormalOpen"
            elif reg_close <= now_local < after_close:
                return "After-Market"
            else:
                return "Closed"
        
        elif area.upper() == "HK":
            # Convert to Hong Kong timezone
            hk_tz = pytz_timezone("Asia/Hong_Kong")
            now_hk = now_utc.astimezone(hk_tz)
            t = now_hk.time()
            
            # Check weekend (Saturday=5, Sunday=6)
            if now_hk.weekday() >= 5:
                return "Closed"
            
            # Regular hours: 09:30–12:00, lunch break 12:00–13:00, 13:00–16:00
            morning_open, morning_close = time(9, 30), time(12, 0)
            afternoon_open, afternoon_close = time(13, 0), time(16, 0)
            
            if (morning_open <= t < morning_close) or (afternoon_open <= t < afternoon_close):
                return "NormalOpen"
            else:
                return "Closed"
        
        else:
            raise ValueError("Invalid area: please use 'US' or 'HK'")
    
    def is_market_open(self) -> bool:
        """Check if US market is open - from reference IsMarketOpen"""
        now_time = datetime.now(pytz_timezone('America/New_York'))
        date_week = now_time.weekday()
        
        is_open = False
        
        # Weekend check
        if date_week == 5 or date_week == 6:  # Saturday or Sunday
            is_open = False
        else:
            # Local time 9:30 AM to 4:00 PM
            if now_time.hour >= 9 and now_time.hour <= 15:
                is_open = True
                
                if now_time.hour == 9 and now_time.minute < 30:
                    is_open = False
                
                if now_time.hour == 15 and now_time.minute > 50:
                    is_open = False
        
        # Additional check for holidays
        if is_open:
            logger.info("Time is OK... but one more check needed for holidays")
            # Could add holiday check here if needed
        
        return is_open
    
    def make_token(self) -> bool:
        """Generate authentication token"""
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
                logger.info("US KIS authentication successful")
                return True
            else:
                logger.error(f"US KIS authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"US KIS authentication error: {e}")
            return False
    
    def get_balance(self, currency: str = "USD") -> Dict[str, Any]:
        """Get overseas account balance - based on reference GetBalance function"""
        try:
            if not self.token:
                if not self.make_token():
                    raise Exception("Authentication failed")

            import time
            time.sleep(0.2)

            # API path and URL setup
            path = "uapi/overseas-stock/v1/trading/inquire-present-balance"
            url = f"{self.base_url}/{path}"

            # Transaction ID based on account type
            tr_id = "CTRP6504R"  # Real account
            if self.config.get('is_virtual', False):
                tr_id = "VTRP6504R"  # Virtual account

            # Request parameters
            params = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.product_code,
                "WCRC_FRCR_DVSN_CD": "02",
                "NATN_CD": "840",  # US country code
                "TR_MKET_CD": "00",  # Market code
                "INQR_DVSN_CD": "00"  # Inquiry division
            }

            # Request headers
            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appKey": self.app_key,
                "appSecret": self.app_secret,
                "tr_id": tr_id,
                "custtype": "P"
            }

            # Make request
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()

                if result.get("rt_cd") == '0':
                    # Parse balance data like reference function
                    output2 = result.get('output2', [])
                    output3 = result.get('output3', {})

                    # Get stock holdings for accurate calculation
                    my_stocks = self.get_holdings()

                    stock_original_total = sum(float(stock.get('original_value', 0)) for stock in my_stocks)
                    stock_current_total = sum(float(stock.get('market_value', 0)) for stock in my_stocks)

                    balance_dict = {}
                    exchange_rate = 1200  # Default rate

                    if currency == "USD":
                        # Find USD data in output2
                        for data in output2:
                            if data.get('crcy_cd') == "USD":
                                # Available cash (order possible amount)
                                balance_dict['RemainMoney'] = (
                                    float(data.get('frcr_dncl_amt_2', 0)) -
                                    float(data.get('frcr_buy_amt_smtl', 0)) +
                                    float(data.get('frcr_sll_amt_smtl', 0))
                                )
                                exchange_rate = data.get('frst_bltn_exrt', 1200)
                                break

                        # Handle virtual account edge case
                        if self.config.get('is_virtual', False) and balance_dict.get('RemainMoney', 0) == 0:
                            # Use output3 for virtual account
                            balance_dict['StockMoney'] = stock_current_total
                            balance_dict['StockRevenue'] = stock_current_total - stock_original_total
                            balance_dict['RemainMoney'] = float(output3.get('frcr_evlu_tota', 0)) / float(exchange_rate)
                            balance_dict['TotalMoney'] = balance_dict['StockMoney'] + balance_dict['RemainMoney']
                        else:
                            # Real account calculation
                            balance_dict['StockMoney'] = stock_current_total
                            balance_dict['StockRevenue'] = stock_current_total - stock_original_total
                            balance_dict['TotalMoney'] = balance_dict['StockMoney'] + balance_dict['RemainMoney']

                    # Convert to standard format
                    return {
                        'total_balance': balance_dict.get('TotalMoney', 0),
                        'cash_balance': balance_dict.get('RemainMoney', 0),
                        'stock_value': balance_dict.get('StockMoney', 0),
                        'revenue': balance_dict.get('StockRevenue', 0),
                        'currency': currency,
                        'exchange_rate': exchange_rate
                    }
                else:
                    logger.error(f"API error: {result.get('msg1', 'Unknown error')}")
                    return {}
            else:
                logger.error(f"HTTP error: {response.status_code} - {response.text}")
                return {}
            
            time_module.sleep(0.2)  # Rate limiting
            
            path = "uapi/overseas-stock/v1/trading/inquire-balance"
            url = f"{self.base_url}/{path}"
            
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "TTTS3012R"  # Overseas balance inquiry
            }
            
            params = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.product_code,
                "OVRS_EXCG_CD": "NASD",  # NASDAQ
                "TR_CRCY_CD": currency,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": ""
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                output2 = result.get("output2", [{}])[0]
                
                return {
                    "currency": currency,
                    "total_balance": float(output2.get("frcr_evlu_tota", 0)),
                    "cash_balance": float(output2.get("frcr_buy_psbl_amt1", 0)),
                    "stock_value": float(output2.get("evlu_amt_smtl_amt", 0)),
                    "profit_loss": float(output2.get("frcr_evlu_pfls_amt", 0))
                }
            else:
                logger.error(f"Failed to get US balance: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting US balance: {e}")
            return {}

    def get_holdings(self, currency: str = "USD") -> List[Dict[str, Any]]:
        """Get overseas stock holdings - based on reference GetMyStockList function"""
        try:
            if not self.token:
                if not self.make_token():
                    raise Exception("Authentication failed")

            import time
            stock_list = []

            # API path setup
            path = "uapi/overseas-stock/v1/trading/inquire-balance"
            url = f"{self.base_url}/{path}"

            # Check multiple markets like reference function
            markets_to_check = [
                {"market": "NASD", "currency": "USD"},  # NASDAQ
                {"market": "NYS", "currency": "USD"},   # NYSE
                {"market": "AMEX", "currency": "USD"},  # AMEX
                {"market": "SEHK", "currency": "HKD"}   # Hong Kong (if needed)
            ]

            for market_info in markets_to_check:
                if currency == "USD" and market_info["currency"] != "USD":
                    continue  # Skip non-USD markets when requesting USD

                try:
                    time.sleep(0.2)  # Rate limiting

                    # Transaction ID based on account type
                    tr_id = "TTTS3012R"  # Real account
                    if self.config.get('is_virtual', False):
                        tr_id = "VTTS3012R"  # Virtual account

                    # Request parameters
                    params = {
                        "CANO": self.account_no,
                        "ACNT_PRDT_CD": self.product_code,
                        "OVRS_EXCG_CD": market_info["market"],
                        "TR_CRCY_CD": market_info["currency"],
                        "CTX_AREA_FK200": "",
                        "CTX_AREA_NK200": ""
                    }

                    # Request headers
                    headers = {
                        "Content-Type": "application/json",
                        "authorization": f"Bearer {self.token}",
                        "appKey": self.app_key,
                        "appSecret": self.app_secret,
                        "tr_id": tr_id,
                        "custtype": "P"
                    }

                    # Make request
                    response = requests.get(url, headers=headers, params=params)

                    if response.status_code == 200:
                        result = response.json()

                        if result.get("rt_cd") == '0':
                            # Parse holdings data
                            output1 = result.get('output1', [])

                            for stock_data in output1:
                                # Only include stocks with positive holdings
                                quantity = float(stock_data.get('ovrs_cblc_qty', 0))
                                if quantity > 0:
                                    # Calculate values
                                    avg_price = float(stock_data.get('pchs_avg_pric', 0))
                                    current_price = float(stock_data.get('now_pric2', 0))
                                    original_value = quantity * avg_price
                                    market_value = quantity * current_price
                                    profit_loss = market_value - original_value
                                    profit_rate = (profit_loss / original_value * 100) if original_value > 0 else 0

                                    stock_info = {
                                        'symbol': stock_data.get('ovrs_pdno', ''),
                                        'company_name': stock_data.get('ovrs_item_name', ''),
                                        'quantity': quantity,
                                        'avg_price': avg_price,
                                        'current_price': current_price,
                                        'original_value': original_value,
                                        'market_value': market_value,
                                        'profit_loss': profit_loss,
                                        'profit_rate': profit_rate,
                                        'currency': market_info["currency"],
                                        'market': market_info["market"]
                                    }
                                    stock_list.append(stock_info)

                except Exception as market_error:
                    logger.warning(f"Error checking {market_info['market']} market: {market_error}")
                    continue

            logger.info(f"Found {len(stock_list)} holdings across all markets")
            return stock_list

        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return []
    
    def get_current_price(self, stock_code: str) -> float:
        """Get current price for US stock"""
        try:
            if not self.token:
                if not self.make_token():
                    raise Exception("Authentication failed")
            
            time_module.sleep(0.1)  # Rate limiting
            
            # Try different exchanges
            exchanges = ["NASD", "NYSE", "AMEX"]  # NASDAQ, NYSE, AMEX
            
            for exchange in exchanges:
                try:
                    url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
                    
                    headers = {
                        "content-type": "application/json",
                        "authorization": f"Bearer {self.token}",
                        "appkey": self.app_key,
                        "appsecret": self.app_secret,
                        "tr_id": "HHDFS00000300"
                    }
                    
                    params = {
                        "AUTH": "",
                        "EXCD": exchange,
                        "SYMB": stock_code
                    }
                    
                    response = requests.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        result = response.json()
                        output = result.get("output", {})
                        price = float(output.get("last", 0))
                        
                        if price > 0:
                            return price
                            
                except Exception as e:
                    logger.warning(f"Failed to get price from {exchange}: {e}")
                    continue
            
            logger.error(f"Failed to get price for {stock_code} from all exchanges")
            return 0.0
                
        except Exception as e:
            logger.error(f"Error getting current price for {stock_code}: {e}")
            return 0.0
    
    def get_market_code_us(self, stock_code: str) -> str:
        """Automatically detect exchange for stock code - from reference GetMarketCodeUS"""
        try:
            exchanges = ["NASD", "NYSE", "AMEX", "HKS"]
            
            for exchange in exchanges:
                try:
                    price = self._test_price_on_exchange(stock_code, exchange)
                    if price > 0:
                        return exchange
                except:
                    continue
            
            return "NAS"  # Default to NASDAQ
            
        except Exception as e:
            logger.error(f"Error detecting market code for {stock_code}: {e}")
            return "NAS"
    
    def _test_price_on_exchange(self, stock_code: str, exchange: str) -> float:
        """Test if stock exists on specific exchange"""
        try:
            if not self.token:
                if not self.make_token():
                    return 0.0
            
            url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
            
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": "HHDFS00000300"
            }
            
            params = {
                "AUTH": "",
                "EXCD": exchange,
                "SYMB": stock_code
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                output = result.get("output", {})
                return float(output.get("last", 0))
            
            return 0.0
            
        except Exception as e:
            return 0.0
    
    def make_buy_limit_order(self, stock_code: str, amt: int, price: float, 
                            adjust_amt: bool = False) -> Dict[str, Any]:
        """Make buy limit order for US stock"""
        try:
            if not self.token:
                if not self.make_token():
                    raise Exception("Authentication failed")
            
            # Auto adjust quantity if requested
            if adjust_amt:
                balance = self.get_balance("USD")
                available_cash = balance.get("cash_balance", 0)
                max_qty = int(available_cash / price)
                amt = min(amt, max_qty)
            
            # Detect market code
            market_code = self.get_market_code_us(stock_code)
            
            return self._place_us_order(stock_code, "BUY", amt, price, market_code)
            
        except Exception as e:
            logger.error(f"Error placing US buy order: {e}")
            return {"success": False, "error": str(e)}
    
    def make_sell_limit_order(self, stock_code: str, amt: int, price: float) -> Dict[str, Any]:
        """Make sell limit order for US stock"""
        try:
            if not self.token:
                if not self.make_token():
                    raise Exception("Authentication failed")
            
            # Detect market code
            market_code = self.get_market_code_us(stock_code)
            
            return self._place_us_order(stock_code, "SELL", amt, price, market_code)
            
        except Exception as e:
            logger.error(f"Error placing US sell order: {e}")
            return {"success": False, "error": str(e)}
    
    def _place_us_order(self, symbol: str, side: str, quantity: int, price: float, 
                       market_code: str) -> Dict[str, Any]:
        """Internal method to place US orders"""
        try:
            url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
            
            # Determine transaction ID based on side
            if side.upper() == "BUY":
                tr_id = "TTTT1002U"  # US buy order
            else:  # SELL
                tr_id = "TTTT1001U"  # US sell order
            
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
                "OVRS_EXCG_CD": market_code,
                "PDNO": symbol,
                "ORD_QTY": str(quantity),
                "OVRS_ORD_UNPR": str(price),
                "ORD_SVR_DVSN_CD": "0",  # Order division
                "ORD_DVSN": "00"  # 00: limit order
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
                    "error": f"US Order failed: {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"Error placing US order: {e}")
            return {
                "success": False,
                "error": str(e)
            }