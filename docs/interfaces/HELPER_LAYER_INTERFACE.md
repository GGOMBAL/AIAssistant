# Helper Layer Interface Specification

**버전**: 1.0
**작성일**: 2025-10-09
**Layer**: Helper Layer (External API Integration & System Services)
**담당 Agent**: Helper Agent
**참조**: CLAUDE.md v2.4, docs/AGENT_INTERFACES.md

---

## 1. 개요

Helper Layer는 외부 API 연동 및 시스템 서비스를 담당하는 레이어입니다.

### 1.1 주요 역할
- 🔌 **Broker API 연동**: KIS, LS Securities 등 증권사 API 연결
- 📊 **Data Provider API**: Alpha Vantage, Yahoo Finance 데이터 수집
- 📱 **Telegram Messenger**: 알림 및 메시지 전송
- 🔐 **인증 관리**: API 토큰 발급 및 갱신
- ⏰ **시장 상태 확인**: 미국/홍콩 시장 개장 여부 체크
- 📈 **실시간 가격 조회**: 현재가, OHLCV 데이터 조회

### 1.2 파일 구성
```
project/Helper/
├── broker_api_connector.py    (529 lines) - 증권사 API 커넥터
├── kis_api_helper_us.py       (771 lines) - KIS API 미국 시장
├── kis_common.py              (359 lines) - KIS 공통 함수
├── KIS_MCP/                   - KIS MCP 기반 주문 시스템 (NEW)
│   ├── __init__.py
│   ├── kis_mcp_order_helper.py  (367 lines) - KIS MCP 주문 헬퍼
│   └── README.md               - KIS MCP 사용 가이드
├── data_provider_api.py       (427 lines) - 데이터 프로바이더 API
├── yfinance_helper.py         (296 lines) - Yahoo Finance 헬퍼
└── telegram_messenger.py      (419 lines) - Telegram Bot
```

---

## 2. 입력 인터페이스

Helper Layer는 주로 **설정 파일**과 **외부 API 요청 파라미터**를 입력받습니다.

### 2.1 설정 파일 입력

#### 2.1.1 Broker API 설정 (broker_config.yaml)
```yaml
# KIS API 설정
KIS:
  REAL:
    app_key: "encrypted_real_app_key"
    app_secret: "encrypted_real_secret"
    account_no: "12345678"
    product_code: "01"
    base_url: "https://openapi.koreainvestment.com:9443"

  VIRTUAL:
    app_key: "virtual_app_key"
    app_secret: "virtual_secret"
    account_no: "50012345"
    product_code: "01"
    base_url: "https://openapivts.koreainvestment.com:29443"

# LS Securities API 설정
LS:
  app_key: "ls_app_key"
  app_secret: "ls_secret"
  account_no: "LS_ACCOUNT"
```

#### 2.1.2 Data Provider 설정 (data_provider_config.yaml)
```yaml
# Alpha Vantage
AlphaVantage:
  api_key: "YOUR_ALPHA_VANTAGE_KEY"
  rate_limit_delay: 12  # seconds (free tier: 5 calls/min)

# Yahoo Finance (no API key needed)
YahooFinance:
  timeout: 10  # seconds
  max_retries: 3
```

#### 2.1.3 Telegram Bot 설정 (telegram_config.yaml)
```yaml
Telegram:
  bot_token: "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
  default_chat_id: "-1001234567890"
  parse_mode: "HTML"
  add_timestamp: true
```

### 2.2 함수 호출 입력

#### 2.2.1 Broker API 입력

**인증 요청**:
```python
# Input: None (설정 파일에서 자동 로드)
# Output: 토큰 발급 성공 여부
is_authenticated: bool
```

**시장 상태 확인**:
```python
# Input
{
    "area": str  # "US" or "HK"
}

# Output
market_status: str  # "NormalOpen", "Pre-Market", "After-Market", "Closed"
```

**현재가 조회**:
```python
# Input
{
    "symbol": str,     # 티커 심볼 (예: "AAPL")
    "exchange": str    # 거래소 (예: "NASDAQ", "NYSE")
}

# Output
{
    "symbol": str,
    "current_price": float,
    "timestamp": str,  # ISO 8601 format
    "currency": str    # "USD"
}
```

**계좌 잔고 조회**:
```python
# Input: None (계좌 정보는 설정 파일에서)

# Output
{
    "total_balance": float,      # 총 자산 (억원)
    "cash_balance": float,       # 현금 잔고 (억원)
    "stock_value": float,        # 주식 평가액 (억원)
    "currency": str,             # "USD"
    "positions": [
        {
            "symbol": str,
            "quantity": int,
            "avg_price": float,
            "current_price": float,
            "market_value": float,
            "unrealized_pnl": float,
            "unrealized_pnl_pct": float
        }
    ]
}
```

**주문 실행**:
```python
# Input
{
    "symbol": str,        # 티커 심볼
    "side": str,          # "BUY" or "SELL"
    "quantity": int,      # 주문 수량
    "price": float,       # 지정가 (None이면 시장가)
    "order_type": str     # "LIMIT" or "MARKET"
}

# Output
{
    "order_id": str,
    "symbol": str,
    "side": str,
    "quantity": int,
    "price": float,
    "status": str,        # "PENDING", "FILLED", "CANCELLED", "REJECTED"
    "filled_quantity": int,
    "timestamp": str,     # ISO 8601
    "message": str
}
```

#### 2.2.2 Data Provider API 입력

**OHLCV 데이터 조회 (일봉)**:
```python
# Input
{
    "symbol": str,            # 티커 심볼
    "start_date": datetime,   # 시작일
    "end_date": datetime,     # 종료일
    "interval": str,          # "1d" (daily) or "1wk" (weekly)
    "adjusted": bool          # True = 수정주가, False = 원본
}

# Output
{
    "symbol": str,
    "data": pd.DataFrame with columns:
        - index: datetime (UTC timezone)
        - open: float
        - high: float
        - low: float
        - close: float
        - volume: int
        - dividends: float (optional)
        - stock_splits: float (optional)
}
```

**분봉 데이터 조회 (Alpha Vantage)**:
```python
# Input
{
    "symbol": str,
    "interval": str,      # "1min", "5min", "15min", "30min", "60min"
    "outputsize": str     # "compact" (최근 100개) or "full" (전체)
}

# Output
{
    "symbol": str,
    "interval": str,
    "data": pd.DataFrame with columns:
        - index: datetime (UTC timezone)
        - open: float
        - high: float
        - low: float
        - close: float
        - volume: int
}
```

**티커 리스트 조회 (Alpha Vantage)**:
```python
# Input
{
    "market": str,        # "NASDAQ", "NYSE", "AMEX"
    "asset_type": str,    # "Stock", "ETF"
    "active": bool        # True = 상장 종목, False = 상장폐지 종목
}

# Output
{
    "market": str,
    "asset_type": str,
    "tickers": List[str],
    "count": int
}
```

**Asset 정보 조회**:
```python
# Input
{
    "ticker": str,
    "info_type": str  # "quoteType", "exchange", "sector", "industry"
}

# Output (info_type = "quoteType")
{
    "ticker": str,
    "quote_type": str,  # "EQUITY", "ETF", "MUTUALFUND"
    "exchange": str,
    "sector": str,
    "industry": str
}
```

**펀더멘털 데이터 조회 (Yahoo Finance)**:
```python
# Input
{
    "ticker": str,
    "metrics": List[str]  # ["eps", "revenue", "marketCap", "peRatio", ...]
}

# Output
{
    "ticker": str,
    "data": {
        "eps": float,
        "revenue": float,
        "marketCap": float,
        "peRatio": float,
        "pbRatio": float,
        "roe": float,
        "roa": float,
        ...
    },
    "last_updated": str  # ISO 8601
}
```

#### 2.2.3 Telegram Messenger 입력

**메시지 전송**:
```python
# Input
{
    "message": str,
    "chat_id": str,           # None이면 default_chat_id 사용
    "parse_mode": str,        # "HTML" or "Markdown"
    "add_timestamp": bool     # True = 타임스탬프 추가
}

# Output
{
    "success": bool,
    "message_id": str,        # Telegram message ID
    "timestamp": str
}
```

**이미지 전송**:
```python
# Input
{
    "photo_path": str,        # 이미지 파일 경로
    "caption": str,           # 이미지 설명
    "chat_id": str
}

# Output
{
    "success": bool,
    "message_id": str,
    "timestamp": str
}
```

**백테스트 리포트 전송**:
```python
# Input
{
    "report": Dict,           # 백테스트 리포트 (Service Layer 출력)
    "chart_path": str,        # 차트 이미지 경로 (optional)
    "chat_id": str
}

# Output
{
    "success": bool,
    "messages_sent": int,     # 전송된 메시지 수
    "timestamp": str
}
```

---

## 3. 출력 인터페이스

### 3.1 Broker API 출력

#### 3.1.1 KIS API 토큰 발급
```python
{
    "access_token": str,
    "token_type": str,           # "Bearer"
    "expires_in": int,           # 초 단위 (86400 = 24시간)
    "issued_at": str,            # ISO 8601
    "expires_at": str            # ISO 8601
}
```

#### 3.1.2 계좌 잔고 조회 응답
```python
{
    "account_no": str,
    "total_balance": float,      # 총 자산 (억원)
    "cash_balance": float,       # 현금 (억원)
    "stock_value": float,        # 주식 평가액 (억원)
    "total_pnl": float,          # 총 손익 (억원)
    "total_pnl_pct": float,      # 총 손익률 (%)
    "currency": str,             # "USD"
    "positions": [
        {
            "symbol": str,
            "name": str,
            "quantity": int,
            "avg_price": float,
            "current_price": float,
            "market_value": float,
            "unrealized_pnl": float,
            "unrealized_pnl_pct": float
        }
    ],
    "timestamp": str             # ISO 8601
}
```

#### 3.1.3 주문 실행 응답
```python
{
    "order_id": str,             # KIS 주문번호
    "symbol": str,
    "side": str,                 # "BUY" or "SELL"
    "quantity": int,
    "price": float,
    "order_type": str,           # "LIMIT" or "MARKET"
    "status": str,               # "PENDING", "FILLED", "CANCELLED", "REJECTED"
    "filled_quantity": int,
    "filled_avg_price": float,
    "commission": float,
    "timestamp": str,
    "message": str,              # 상태 메시지
    "error_code": str,           # 에러 코드 (에러 발생 시)
    "error_message": str         # 에러 메시지 (에러 발생 시)
}
```

### 3.2 Data Provider API 출력

#### 3.2.1 OHLCV 데이터 (DataFrame)
```python
# pandas DataFrame
{
    "index": pd.DatetimeIndex,   # UTC timezone
    "columns": [
        "open": float,           # 시가
        "high": float,           # 고가
        "low": float,            # 저가
        "close": float,          # 종가
        "volume": int,           # 거래량
        "dividends": float,      # 배당금 (optional)
        "stock_splits": float    # 주식 분할 (optional)
    ]
}
```

**예시**:
```
                           open    high     low   close      volume  dividends  stock_splits
2023-01-03 00:00:00+00:00  130.28  130.90  124.17  125.07  112117471        0.0           0.0
2023-01-04 00:00:00+00:00  126.89  128.66  125.08  126.36   89113671        0.0           0.0
2023-01-05 00:00:00+00:00  127.13  127.77  124.76  125.02   80962746        0.0           0.0
```

#### 3.2.2 티커 리스트
```python
{
    "market": str,               # "NASDAQ", "NYSE"
    "asset_type": str,           # "Stock", "ETF"
    "active": bool,
    "tickers": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", ...
    ],
    "count": int,                # 종목 수
    "last_updated": str          # ISO 8601
}
```

#### 3.2.3 펀더멘털 데이터
```python
{
    "ticker": str,
    "company_name": str,
    "sector": str,
    "industry": str,
    "market_cap": float,         # 시가총액 (억 달러)
    "pe_ratio": float,           # P/E 비율
    "pb_ratio": float,           # P/B 비율
    "ps_ratio": float,           # P/S 비율
    "roe": float,                # ROE (%)
    "roa": float,                # ROA (%)
    "eps": float,                # EPS (주당순이익)
    "revenue": float,            # 매출액 (억 달러)
    "net_income": float,         # 순이익 (억 달러)
    "dividend_yield": float,     # 배당수익률 (%)
    "beta": float,               # 베타 (시장 대비 변동성)
    "52week_high": float,
    "52week_low": float,
    "last_updated": str          # ISO 8601
}
```

### 3.3 Telegram Messenger 출력

#### 3.3.1 메시지 전송 응답
```python
{
    "success": bool,
    "message_id": str,           # Telegram message ID
    "chat_id": str,
    "timestamp": str,            # ISO 8601
    "error_message": str         # 에러 메시지 (실패 시)
}
```

#### 3.3.2 백테스트 리포트 전송 응답
```python
{
    "success": bool,
    "messages_sent": int,        # 전송된 메시지 수
    "message_ids": List[str],    # Telegram message IDs
    "photo_sent": bool,          # 차트 전송 여부
    "timestamp": str,
    "error_message": str         # 에러 메시지 (실패 시)
}
```

---

## 4. 클래스 및 메서드 명세

### 4.1 BrokerAPIBase (추상 기본 클래스)

**파일**: `broker_api_connector.py`

```python
class BrokerAPIBase(ABC):
    """증권사 API 기본 클래스"""

    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 설정 파일 경로 (.yaml or .json)
        """
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """
        API 인증 수행

        Returns:
            인증 성공 여부
        """
        pass

    @abstractmethod
    def is_market_open(self) -> bool:
        """
        시장 개장 여부 확인

        Returns:
            True = 개장, False = 폐장
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """
        현재가 조회

        Args:
            symbol: 티커 심볼

        Returns:
            현재가
        """
        pass

    @abstractmethod
    def get_balance(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Returns:
            계좌 정보 딕셔너리
        """
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int,
                   price: float = None) -> Dict[str, Any]:
        """
        주문 실행

        Args:
            symbol: 티커 심볼
            side: "BUY" or "SELL"
            quantity: 주문 수량
            price: 지정가 (None = 시장가)

        Returns:
            주문 결과 딕셔너리
        """
        pass
```

### 4.2 KISBrokerAPI (KIS API 구현체)

**파일**: `broker_api_connector.py`

```python
class KISBrokerAPI(BrokerAPIBase):
    """한국투자증권 API 구현"""

    def __init__(self, config_path: str = None, account_type: str = "REAL"):
        """
        Args:
            config_path: 설정 파일 경로
            account_type: "REAL" or "VIRTUAL"
        """
        pass

    def make_token(self) -> Dict[str, Any]:
        """
        토큰 발급

        Returns:
            {
                "access_token": str,
                "token_type": str,
                "expires_in": int
            }
        """
        pass

    def check_and_refresh_token_if_expired(self, response) -> bool:
        """
        토큰 만료 확인 및 자동 갱신

        Args:
            response: API 응답 객체

        Returns:
            토큰 갱신 여부
        """
        pass
```

### 4.3 KISUSHelper (KIS API 미국 시장 전용)

**파일**: `kis_api_helper_us.py`

```python
class KISUSHelper:
    """KIS API 미국 시장 전용 헬퍼"""

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: KIS API 설정 딕셔너리
        """
        pass

    def market_open_type(self, area: str = "US") -> str:
        """
        시장 상태 확인

        Args:
            area: "US" or "HK"

        Returns:
            "NormalOpen", "Pre-Market", "After-Market", "Closed"
        """
        pass

    def get_current_price_us(self, ticker: str, exchange: str = "NASDAQ") -> Dict[str, Any]:
        """
        미국 주식 현재가 조회

        Args:
            ticker: 티커 심볼
            exchange: "NASDAQ" or "NYSE"

        Returns:
            {
                "symbol": str,
                "current_price": float,
                "timestamp": str
            }
        """
        pass

    def get_balance_us(self) -> Dict[str, Any]:
        """
        미국 계좌 잔고 조회

        Returns:
            계좌 정보 딕셔너리
        """
        pass

    def place_order_us(self, symbol: str, side: str, quantity: int,
                      price: float = None, order_type: str = "LIMIT") -> Dict[str, Any]:
        """
        미국 주식 주문

        Args:
            symbol: 티커 심볼
            side: "BUY" or "SELL"
            quantity: 수량
            price: 지정가
            order_type: "LIMIT" or "MARKET"

        Returns:
            주문 결과
        """
        pass
```

### 4.3.1 KISMCPOrderHelper (KIS MCP 주문 헬퍼) **[NEW]**

**파일**: `KIS_MCP/kis_mcp_order_helper.py`

**작성일**: 2025-11-06
**기반**: [KIS Trading MCP](https://github.com/koreainvestment/open-trading-api/tree/main/MCP)

```python
class KISMCPOrderHelper:
    """KIS MCP를 활용한 해외주식 주문 헬퍼

    KIS Open Trading API의 MCP (Model Context Protocol) 기반 주문 시스템.
    기존 kis_api_helper_us.py와 별도로 운영되며, 더 간결하고 안정적인 주문 처리 제공.
    """

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
        pass

    def make_token(self) -> bool:
        """
        인증 토큰 발급

        Returns:
            인증 성공 여부
        """
        pass

    def make_buy_order(
        self,
        stock_code: str,
        amt: int,
        price: float = 0.0,
        use_market_on_open: bool = False
    ) -> Dict[str, Any]:
        """
        매수 주문

        Args:
            stock_code: 종목코드
            amt: 수량
            price: 가격 (0이면 현재가로 지정가 주문)
            use_market_on_open: True면 LOO(32) 사용 (실전만)

        Returns:
            {
                "success": bool,
                "order_id": str,
                "message": str,
                "rt_cd": str,
                "msg_cd": str
            }
        """
        pass

    def make_sell_order(
        self,
        stock_code: str,
        amt: int,
        price: float = 0.0,
        use_market_on_open: bool = False
    ) -> Dict[str, Any]:
        """
        매도 주문

        Args:
            stock_code: 종목코드
            amt: 수량
            price: 가격 (0이면 현재가로 지정가 주문)
            use_market_on_open: True면 MOO(31) 사용 (장 개시 전만 가능)

        Returns:
            주문 결과 딕셔너리
        """
        pass

    def get_current_price(self, stock_code: str) -> float:
        """
        현재가 조회

        Args:
            stock_code: 종목코드

        Returns:
            현재가 (실패 시 0.0)
        """
        pass

    def get_balance(self, currency: str = "USD") -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Args:
            currency: 통화 코드

        Returns:
            {
                "cash_balance": float,
                "currency": str,
                "result": dict
            }
        """
        pass

    def get_market_code_us(self, symbol: str) -> str:
        """
        미국 종목의 거래소 코드 반환

        Args:
            symbol: 종목 코드

        Returns:
            NASD: 나스닥
            NYSE: 뉴욕증권거래소
            AMEX: 아멕스
        """
        pass
```

**주요 특징**:
- KIS Open Trading API 완전 호환
- 모의투자/실전투자 자동 전환
- 현재가 자동 조회 및 지정가 주문
- 계좌 잔고 조회
- 오류 처리 및 로깅

**ORD_DVSN (주문 타입)**:

매수 (TTTT1002U / VTTT1002U):
- `00`: 지정가
- `32`: LOO (장개시 지정가) - 실전만
- `34`: LOC (장마감 지정가) - 실전만

매도 (TTTT1006U / VTTT1006U):
- `00`: 지정가
- `31`: MOO (장개시 시장가) - 실전만
- `32`: LOO (장개시 지정가) - 실전만
- `33`: MOC (장마감 시장가) - 실전만
- `34`: LOC (장마감 지정가) - 실전만

**참고**: 모의투자는 `00` (지정가)만 사용 가능

**시장가 주문 처리**:

KIS API는 해외주식에 대해 일반적인 시장가 주문을 지원하지 않습니다. 대신:
- **매수**: 현재가로 지정가 주문 (`ORD_DVSN: "00"`)
- **매도**: 현재가로 지정가 주문 (`ORD_DVSN: "00"`)

**참고**:
- MOO(31)는 장 개시 전에만 주문 가능
- 일반 거래 시간에는 지정가 사용
- `use_market_on_open=True`로 명시적 지정 시에만 MOO 사용

**상세 문서**: `docs/KIS_MCP_ORDER_SYSTEM.md`

### 4.4 DataProviderBase (데이터 프로바이더 기본 클래스)

**파일**: `data_provider_api.py`

```python
class DataProviderBase(ABC):
    """데이터 프로바이더 기본 클래스"""

    @abstractmethod
    def get_ohlcv(self, symbol: str, start_date: datetime = None,
                  end_date: datetime = None, interval: str = "1d") -> pd.DataFrame:
        """
        OHLCV 데이터 조회

        Args:
            symbol: 티커 심볼
            start_date: 시작일
            end_date: 종료일
            interval: "1d", "1wk", "1mo"

        Returns:
            OHLCV DataFrame
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """현재가 조회"""
        pass
```

### 4.5 AlphaVantageAPI (Alpha Vantage 구현체)

**파일**: `data_provider_api.py`

```python
class AlphaVantageAPI(DataProviderBase):
    """Alpha Vantage API 구현"""

    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 설정 파일 경로
        """
        pass

    def get_ticker_list(self, market: str = 'NASDAQ',
                       asset_type: str = 'Stock',
                       active: bool = True) -> List[str]:
        """
        티커 리스트 조회

        Args:
            market: "NASDAQ", "NYSE", "AMEX"
            asset_type: "Stock", "ETF"
            active: True = 상장 종목

        Returns:
            티커 리스트
        """
        pass

    def get_ohlcv_intraday(self, symbol: str, interval: str = "1min",
                          outputsize: str = "compact") -> pd.DataFrame:
        """
        분봉 데이터 조회

        Args:
            symbol: 티커
            interval: "1min", "5min", "15min", "30min", "60min"
            outputsize: "compact" (100개) or "full"

        Returns:
            분봉 DataFrame
        """
        pass
```

### 4.6 YFinanceHelper (Yahoo Finance 헬퍼)

**파일**: `yfinance_helper.py`

```python
class YFinanceHelper:
    """Yahoo Finance API 헬퍼"""

    def get_ohlcv(self, stock_code: str, p_code: str,
                  start_date: datetime, end_date: datetime,
                  ohlcv: str = "Y") -> pd.DataFrame:
        """
        OHLCV 데이터 조회

        Args:
            stock_code: 티커 심볼
            p_code: "W" = 주봉, "D" = 일봉
            start_date: 시작일
            end_date: 종료일
            ohlcv: "Y" = 수정주가, "N" = 원본

        Returns:
            OHLCV DataFrame
        """
        pass

    def get_asset_info(self, ticker: str, info_type: str = "quoteType") -> str:
        """
        Asset 정보 조회

        Args:
            ticker: 티커
            info_type: "quoteType", "exchange", "sector", "industry"

        Returns:
            정보 문자열
        """
        pass

    def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """
        펀더멘털 데이터 조회

        Args:
            ticker: 티커

        Returns:
            펀더멘털 딕셔너리
        """
        pass
```

### 4.7 TelegramBot (Telegram 메신저)

**파일**: `telegram_messenger.py`

```python
class TelegramBot:
    """Telegram Bot 메신저"""

    def __init__(self, bot_token: str, default_chat_id: str = None):
        """
        Args:
            bot_token: Telegram Bot API 토큰
            default_chat_id: 기본 채팅방 ID
        """
        pass

    def send_message(self, message: str, chat_id: str = None,
                    parse_mode: str = 'HTML',
                    add_timestamp: bool = True) -> bool:
        """
        메시지 전송

        Args:
            message: 메시지 내용
            chat_id: 채팅방 ID (None = default)
            parse_mode: "HTML" or "Markdown"
            add_timestamp: 타임스탬프 추가 여부

        Returns:
            전송 성공 여부
        """
        pass

    def send_message_with_retry(self, message: str, chat_id: str = None,
                               max_retries: int = 3,
                               retry_delay: int = 2) -> bool:
        """
        재시도 로직이 있는 메시지 전송

        Args:
            message: 메시지 내용
            chat_id: 채팅방 ID
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 대기 시간 (초)

        Returns:
            전송 성공 여부
        """
        pass

    def send_photo(self, photo_path: str, caption: str = None,
                   chat_id: str = None) -> bool:
        """
        이미지 전송

        Args:
            photo_path: 이미지 파일 경로
            caption: 이미지 설명
            chat_id: 채팅방 ID

        Returns:
            전송 성공 여부
        """
        pass

    def send_backtest_report(self, report: Dict, chart_path: str = None,
                            chat_id: str = None) -> Dict[str, Any]:
        """
        백테스트 리포트 전송

        Args:
            report: 백테스트 리포트 딕셔너리
            chart_path: 차트 이미지 경로
            chat_id: 채팅방 ID

        Returns:
            {
                "success": bool,
                "messages_sent": int,
                "message_ids": List[str]
            }
        """
        pass
```

---

## 5. 사용 예제

### 5.1 KIS API 사용 예제

```python
from project.Helper.broker_api_connector import KISBrokerAPI

# 1. API 초기화 (실계좌)
kis = KISBrokerAPI(
    config_path="config/api_credentials.yaml",
    account_type="REAL"
)

# 2. 인증
if kis.authenticate():
    print("✅ KIS API 인증 성공")

# 3. 시장 상태 확인
if kis.is_market_open():
    print("🟢 시장 개장 중")

    # 4. 현재가 조회
    price = kis.get_current_price("AAPL")
    print(f"AAPL 현재가: ${price:.2f}")

    # 5. 계좌 잔고 조회
    balance = kis.get_balance()
    print(f"총 자산: ${balance['total_balance']:.2f}억")
    print(f"현금: ${balance['cash_balance']:.2f}억")

    # 6. 주문 실행
    order = kis.place_order(
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=150.0
    )

    if order['status'] == 'FILLED':
        print(f"✅ 주문 체결: {order['symbol']} {order['quantity']}주")
    else:
        print(f"❌ 주문 실패: {order['message']}")
else:
    print("🔴 시장 폐장")
```

### 5.2 Yahoo Finance 사용 예제

```python
from project.Helper.yfinance_helper import YFinanceHelper
from datetime import datetime, timedelta

# 1. 헬퍼 초기화
yf = YFinanceHelper()

# 2. 일봉 데이터 조회
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)

df_daily = yf.get_ohlcv(
    stock_code="AAPL",
    p_code="D",
    start_date=start_date,
    end_date=end_date,
    ohlcv="Y"  # 수정주가
)

print(f"✅ AAPL 일봉 데이터: {len(df_daily)} rows")
print(df_daily.tail())

# 3. 주봉 데이터 조회
df_weekly = yf.get_ohlcv(
    stock_code="AAPL",
    p_code="W",
    start_date=start_date,
    end_date=end_date
)

print(f"✅ AAPL 주봉 데이터: {len(df_weekly)} rows")

# 4. Asset 정보 조회
asset_type = yf.get_asset_info("AAPL", "quoteType")
print(f"AAPL Asset Type: {asset_type}")  # "EQUITY"

sector = yf.get_asset_info("AAPL", "sector")
print(f"AAPL Sector: {sector}")  # "Technology"

# 5. 펀더멘털 데이터 조회
fundamental = yf.get_fundamental_data("AAPL")
print(f"AAPL P/E Ratio: {fundamental.get('pe_ratio', 'N/A')}")
print(f"AAPL ROE: {fundamental.get('roe', 'N/A')}%")
```

### 5.3 Alpha Vantage 사용 예제

```python
from project.Helper.data_provider_api import AlphaVantageAPI

# 1. API 초기화
av = AlphaVantageAPI(config_path="config/data_provider_config.yaml")

# 2. 티커 리스트 조회
nasdaq_stocks = av.get_ticker_list(
    market="NASDAQ",
    asset_type="Stock",
    active=True
)

print(f"✅ NASDAQ 상장 종목: {len(nasdaq_stocks)}개")
print(f"예시: {nasdaq_stocks[:10]}")

# 3. 분봉 데이터 조회
df_intraday = av.get_ohlcv_intraday(
    symbol="AAPL",
    interval="5min",
    outputsize="compact"
)

print(f"✅ AAPL 5분봉 데이터: {len(df_intraday)} rows")
print(df_intraday.tail())

# 4. 일봉 데이터 조회
df_daily = av.get_ohlcv(
    symbol="AAPL",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    interval="1d"
)

print(f"✅ AAPL 일봉 데이터: {len(df_daily)} rows")
```

### 5.4 Telegram 메시지 전송 예제

```python
from project.Helper.telegram_messenger import TelegramBot

# 1. Bot 초기화
bot = TelegramBot(
    bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    default_chat_id="-1001234567890"
)

# 2. 간단한 메시지 전송
success = bot.send_message(
    message="📊 백테스트가 시작되었습니다.",
    add_timestamp=True
)

if success:
    print("✅ Telegram 메시지 전송 완료")

# 3. HTML 포맷 메시지
html_message = """
<b>📈 백테스트 결과</b>
총 수익률: <code>+12.5%</code>
샤프 비율: <code>1.25</code>
최대 낙폭: <code>-5.2%</code>
"""

bot.send_message(
    message=html_message,
    parse_mode="HTML"
)

# 4. 차트 이미지 전송
bot.send_photo(
    photo_path="report/backtest_chart.png",
    caption="📊 백테스트 수익률 차트"
)

# 5. 백테스트 리포트 전송 (Service Layer 연동)
backtest_report = {
    "total_return": 12.5,
    "sharpe_ratio": 1.25,
    "max_drawdown": -5.2,
    "win_rate": 58.3,
    "total_trades": 45
}

result = bot.send_backtest_report(
    report=backtest_report,
    chart_path="report/backtest_chart.png"
)

print(f"✅ 리포트 전송 완료: {result['messages_sent']}개 메시지")
```

---

## 6. 에러 처리

### 6.1 표준 에러 응답 형식

```python
{
    "success": False,
    "error_code": str,           # "AUTH_FAILED", "API_LIMIT", "NETWORK_ERROR"
    "error_message": str,        # 상세 에러 메시지
    "timestamp": str,            # ISO 8601
    "retry_after": int           # 재시도 가능 시간 (초, optional)
}
```

### 6.2 에러 코드 및 처리

| 에러 코드 | 설명 | 대응 방법 |
|----------|------|----------|
| `AUTH_FAILED` | API 인증 실패 | 토큰 재발급 시도 |
| `TOKEN_EXPIRED` | 토큰 만료 | 자동 토큰 갱신 후 재시도 |
| `API_LIMIT` | API 호출 한도 초과 | rate_limit_delay 후 재시도 |
| `NETWORK_ERROR` | 네트워크 오류 | 최대 3회 재시도 |
| `INVALID_SYMBOL` | 잘못된 티커 심볼 | 사용자에게 에러 반환 |
| `MARKET_CLOSED` | 시장 폐장 | 시장 개장 시간 확인 후 대기 |
| `INSUFFICIENT_BALANCE` | 잔고 부족 | 주문 수량 조정 또는 취소 |
| `ORDER_REJECTED` | 주문 거부 | 주문 파라미터 검증 |

### 6.3 에러 처리 예제

```python
from project.Helper.broker_api_connector import KISBrokerAPI
import logging

logger = logging.getLogger(__name__)

def safe_order_execution(kis: KISBrokerAPI, symbol: str, quantity: int):
    """안전한 주문 실행 (에러 처리 포함)"""

    max_retries = 3

    for attempt in range(max_retries):
        try:
            # 1. 시장 상태 확인
            if not kis.is_market_open():
                logger.warning("Market is closed")
                return {"success": False, "error_code": "MARKET_CLOSED"}

            # 2. 주문 실행
            order = kis.place_order(
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                price=None  # 시장가
            )

            # 3. 성공
            if order.get('status') == 'FILLED':
                logger.info(f"Order filled: {symbol} x {quantity}")
                return {"success": True, "order": order}

            # 4. 주문 거부
            elif order.get('status') == 'REJECTED':
                logger.error(f"Order rejected: {order.get('message')}")
                return {
                    "success": False,
                    "error_code": "ORDER_REJECTED",
                    "error_message": order.get('message')
                }

        except Exception as e:
            logger.error(f"Order attempt {attempt + 1} failed: {e}")

            # 토큰 만료 에러 처리
            if "TOKEN_EXPIRED" in str(e):
                kis.authenticate()  # 재인증
                continue

            # 네트워크 에러 재시도
            if "NETWORK_ERROR" in str(e) and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue

            # 재시도 불가능한 에러
            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "error_message": str(e)
            }

    # 최대 재시도 횟수 초과
    return {
        "success": False,
        "error_code": "MAX_RETRIES_EXCEEDED",
        "error_message": f"Failed after {max_retries} attempts"
    }
```

---

## 7. 성능 및 제약사항

### 7.1 API 호출 한도 (Rate Limits)

| API Provider | Free Tier Limit | 대응 방법 |
|-------------|----------------|----------|
| Alpha Vantage | 5 calls/minute, 500 calls/day | `rate_limit_delay = 12초` |
| Yahoo Finance | 2000 calls/hour | 자동 백오프 처리 |
| KIS API | 초당 20건 | 요청 큐 관리 |
| Telegram Bot | 30 messages/second | 메시지 배치 전송 |

### 7.2 응답 시간

| 작업 | 평균 응답 시간 | 비고 |
|-----|--------------|------|
| KIS 토큰 발급 | 1-2초 | 하루 1회 |
| 현재가 조회 | 0.3-0.5초 | 캐싱 가능 |
| 계좌 잔고 조회 | 0.5-1초 | - |
| 주문 실행 | 1-3초 | 시장 상황에 따라 변동 |
| OHLCV 조회 (1년) | 2-5초 | 티커당 |
| Telegram 메시지 | 0.5-1초 | 네트워크 상태에 따라 변동 |

### 7.3 데이터 크기

| 데이터 타입 | 크기 (1년 기준) | 비고 |
|-----------|---------------|------|
| 일봉 OHLCV | ~252 rows | 252 거래일 |
| 주봉 OHLCV | ~52 rows | 52주 |
| 분봉 (1min) | ~23,400 rows | 시장 개장 시간만 |
| 펀더멘털 | ~50 KB | 티커당 |

---

## 8. 의존성

### 8.1 Python 패키지

```python
# requirements.txt
yfinance==0.2.28         # Yahoo Finance API
requests==2.31.0         # HTTP 요청
pandas==2.0.3            # 데이터 처리
pytz==2023.3             # 시간대 처리
PyYAML==6.0.1            # YAML 파일 파싱
python-telegram-bot==20.4  # Telegram Bot (optional)
```

### 8.2 외부 API

- **Alpha Vantage**: API 키 필요 (무료/유료)
- **Yahoo Finance**: API 키 불필요
- **KIS API**: 계좌 개설 및 API 신청 필요
- **Telegram Bot**: Bot 토큰 및 채팅방 ID 필요

### 8.3 설정 파일 의존성

```
config/
├── api_credentials.yaml    # API 인증 정보
├── broker_config.yaml       # 증권사 설정
└── data_provider_config.yaml  # 데이터 프로바이더 설정
```

---

## 9. 버전 관리

### 9.1 인터페이스 버전

- **현재 버전**: 1.0 (2025-10-09)
- **호환성**: Indicator Layer 1.0+, Strategy Layer 1.0+, Service Layer 1.0+

### 9.2 변경 이력

| 버전 | 날짜 | 변경 사항 |
|-----|------|----------|
| 1.1 | 2025-11-06 | KIS MCP 주문 헬퍼 추가 (KISMCPOrderHelper) |
| 1.0 | 2025-10-09 | 초기 인터페이스 명세 작성 |

---

## 10. 참조 문서

- **CLAUDE.md v2.4**: 프로젝트 핵심 규칙
- **docs/AGENT_INTERFACES.md**: Agent 간 통신 프로토콜
- **config/broker_config.yaml**: 증권사 설정 예제
- **config/api_credentials.yaml**: API 자격증명 예제
- **project/service/SERVICE_LAYER_INTERFACE.md**: Service Layer 인터페이스

---

**작성자**: Service Agent
**검토자**: Orchestrator Agent
**승인 날짜**: 2025-10-09
