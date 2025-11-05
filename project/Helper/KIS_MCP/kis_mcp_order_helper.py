"""
KIS MCP Order Helper
한국투자증권 MCP를 활용한 해외주식 주문 헬퍼

Based on: KIS Trading MCP
GitHub: https://github.com/koreainvestment/open-trading-api/tree/main/MCP
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KISMCPOrderHelper:
    """KIS MCP를 활용한 해외주식 주문 헬퍼"""

    def __init__(self, config: dict):
        """
        Args:
            config: myStockInfo.yaml 설정
                - app_key: KIS API Key
                - app_secret: KIS API Secret
                - account_no: 계좌번호 (CANO)
                - product_code: 계좌상품코드 (ACNT_PRDT_CD)
                - base_url: API Base URL
                - is_virtual: 모의투자 여부
        """
        self.app_key = config.get('app_key')
        self.app_secret = config.get('app_secret')
        self.account_no = config.get('account_no')
        self.product_code = config.get('product_code')
        self.base_url = config.get('base_url', 'https://openapi.koreainvestment.com:9443')
        self.is_virtual = config.get('is_virtual', False)
        self.token = None
        self.token_expires = None

    def make_token(self) -> bool:
        """인증 토큰 발급"""
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

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                self.token = result.get("access_token")
                logger.info("[OK] KIS API 인증 성공")
                return True
            else:
                logger.error(f"[ERROR] 인증 실패: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"[ERROR] 인증 오류: {e}")
            return False

    def get_market_code_us(self, symbol: str) -> str:
        """미국 종목의 거래소 코드 반환

        Args:
            symbol: 종목 코드

        Returns:
            NASD: 나스닥
            NYSE: 뉴욕증권거래소
            AMEX: 아멕스
        """
        # TODO: 실제로는 종목 마스터 파일에서 조회해야 함
        # 간단한 휴리스틱으로 추정
        nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA']

        if symbol in nasdaq_symbols:
            return 'NASD'
        else:
            return 'NYSE'

    def place_order(
        self,
        stock_code: str,
        order_type: str,  # 'buy' or 'sell'
        quantity: int,
        price: float = 0.0,
        ord_dvsn: str = "00"
    ) -> Dict[str, Any]:
        """해외주식 주문

        Args:
            stock_code: 종목코드
            order_type: 'buy' (매수) or 'sell' (매도)
            quantity: 주문수량
            price: 주문가격 (0이면 시장가 유사 주문)
            ord_dvsn: 주문구분
                매수: 00(지정가), 32(LOO), 34(LOC)
                매도: 00(지정가), 31(MOO), 32(LOO), 33(MOC), 34(LOC)
                모의투자: 00만 가능

        Returns:
            성공: {"success": True, "order_id": "...", "message": "..."}
            실패: {"success": False, "error": "...", "rt_cd": "...", "msg_cd": "..."}
        """
        try:
            if not self.token:
                if not self.make_token():
                    return {"success": False, "error": "인증 실패"}

            # 거래소 코드
            market_code = self.get_market_code_us(stock_code)

            # TR ID 결정
            if self.is_virtual:
                tr_id = "VTTT1002U" if order_type.lower() == 'buy' else "VTTT1006U"
            else:
                tr_id = "TTTT1002U" if order_type.lower() == 'buy' else "TTTT1006U"

            # 모의투자는 지정가(00)만 가능
            if self.is_virtual and ord_dvsn != "00":
                logger.warning(f"[WARNING] 모의투자는 지정가(00)만 가능합니다. ord_dvsn을 00으로 변경")
                ord_dvsn = "00"

            url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"

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
                "PDNO": stock_code,
                "ORD_QTY": str(quantity),
                "OVRS_ORD_UNPR": str(price) if price > 0 else "0",
                "ORD_SVR_DVSN_CD": "0",
                "ORD_DVSN": ord_dvsn
            }

            logger.info(f"[ORDER] {order_type.upper()} {stock_code} x{quantity} @ ${price:.2f} (ord_dvsn={ord_dvsn})")

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                rt_cd = result.get("rt_cd", "")

                if rt_cd == "0":
                    order_id = result.get("output", {}).get("ODNO", "")
                    message = result.get("msg1", "주문 성공")

                    logger.info(f"[OK] 주문 체결: ODNO={order_id}")

                    return {
                        "success": True,
                        "order_id": order_id,
                        "message": message,
                        "rt_cd": rt_cd,
                        "msg_cd": result.get("msg_cd", ""),
                        "result": result
                    }
                else:
                    msg_cd = result.get("msg_cd", "")
                    message = result.get("msg1", "주문 실패")

                    logger.error(f"[ERROR] 주문 실패: rt_cd={rt_cd}, msg_cd={msg_cd}, message={message}")

                    return {
                        "success": False,
                        "error": message,
                        "rt_cd": rt_cd,
                        "msg_cd": msg_cd,
                        "message": message,
                        "result": result
                    }
            else:
                logger.error(f"[ERROR] HTTP {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }

        except Exception as e:
            logger.error(f"[ERROR] 주문 오류: {e}")
            return {"success": False, "error": str(e)}

    def make_buy_order(
        self,
        stock_code: str,
        amt: int,
        price: float = 0.0,
        use_market_on_open: bool = False
    ) -> Dict[str, Any]:
        """매수 주문

        Args:
            stock_code: 종목코드
            amt: 수량
            price: 가격 (0이면 현재가로 지정가 주문)
            use_market_on_open: True면 LOO(32) 사용

        Returns:
            주문 결과
        """
        ord_dvsn = "32" if use_market_on_open and not self.is_virtual else "00"
        return self.place_order(stock_code, 'buy', amt, price, ord_dvsn)

    def make_sell_order(
        self,
        stock_code: str,
        amt: int,
        price: float = 0.0,
        use_market_on_open: bool = False
    ) -> Dict[str, Any]:
        """매도 주문

        Args:
            stock_code: 종목코드
            amt: 수량
            price: 가격 (0이면 현재가로 지정가 주문)
            use_market_on_open: True면 MOO(31) 사용 (장 개시 전만 가능)

        Returns:
            주문 결과
        """
        # MOO/LOO는 특정 시간대에만 가능하므로 기본적으로 지정가 사용
        if use_market_on_open and not self.is_virtual:
            # 사용자가 명시적으로 MOO 요청 시에만 사용
            ord_dvsn = "31"  # MOO (Market on Open)
        else:
            ord_dvsn = "00"  # 지정가

        # price=0일 때 현재가로 지정가 주문
        if price == 0.0:
            current_price = self.get_current_price(stock_code)
            if current_price > 0:
                price = current_price
                logger.info(f"[INFO] 매도 주문: 현재가 ${price:.2f}로 지정가 주문")
            else:
                return {"success": False, "error": "현재가 조회 실패"}

        return self.place_order(stock_code, 'sell', amt, price, ord_dvsn)

    def get_current_price(self, stock_code: str) -> float:
        """현재가 조회

        Args:
            stock_code: 종목코드

        Returns:
            현재가 (실패 시 0.0)
        """
        try:
            if not self.token:
                if not self.make_token():
                    return 0.0

            market_code = self.get_market_code_us(stock_code)

            # 거래소 코드 변환 (NASD -> NAS, NYSE -> NYS, AMEX -> AMS)
            exchange_map = {
                'NASD': 'NAS',
                'NYSE': 'NYS',
                'AMEX': 'AMS'
            }
            exchange = exchange_map.get(market_code, market_code)

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
            logger.error(f"[ERROR] 현재가 조회 오류: {e}")
            return 0.0

    def get_balance(self, currency: str = "USD") -> Dict[str, Any]:
        """계좌 잔고 조회

        Args:
            currency: 통화 코드

        Returns:
            잔고 정보
        """
        try:
            if not self.token:
                if not self.make_token():
                    return {"cash_balance": 0.0}

            url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"

            tr_id = "VTTT3007R" if self.is_virtual else "TTTS3007R"

            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
                "tr_id": tr_id
            }

            params = {
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.product_code,
                "OVRS_EXCG_CD": "NASD",  # Default to NASDAQ
                "TR_CRCY_CD": currency
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                output = result.get("output2", {})

                cash_balance = float(output.get("frcr_dncl_amt_2", 0))

                return {
                    "cash_balance": cash_balance,
                    "currency": currency,
                    "result": result
                }
            else:
                logger.error(f"[ERROR] 잔고 조회 실패: {response.status_code}")
                return {"cash_balance": 0.0}

        except Exception as e:
            logger.error(f"[ERROR] 잔고 조회 오류: {e}")
            return {"cash_balance": 0.0}
