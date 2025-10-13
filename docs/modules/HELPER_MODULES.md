# Helper Layer Modules Documentation

**버전**: 1.0
**작성일**: 2025-10-09
**Layer**: Helper Layer (External API Integration & System Services)
**담당 Agent**: Helper Agent
**참조**: HELPER_LAYER_INTERFACE.md, CLAUDE.md v2.4

---

## 1. 개요

Helper Layer는 외부 API 연동 및 시스템 서비스를 제공하는 6개의 핵심 모듈로 구성됩니다.

### 1.1 모듈 구성

```
project/Helper/
├── broker_api_connector.py    (529 lines) - 증권사 API 통합 커넥터
├── kis_api_helper_us.py       (771 lines) - KIS API 미국 시장 전용
├── kis_common.py              (359 lines) - KIS 공통 유틸리티
├── data_provider_api.py       (427 lines) - 데이터 프로바이더 통합
├── yfinance_helper.py         (296 lines) - Yahoo Finance 헬퍼
└── telegram_messenger.py      (419 lines) - Telegram 메신저
```

**총 코드 라인 수**: 2,801 lines (평균 467 lines/module)

### 1.2 모듈 간 의존성

```
broker_api_connector.py (BrokerAPIBase)
    └── kis_api_helper_us.py (KISUSHelper)
        └── kis_common.py (공통 함수)

data_provider_api.py (DataProviderBase)
    └── yfinance_helper.py (YFinanceHelper)

telegram_messenger.py (독립 모듈)
```

---

## 2. Module 1: broker_api_connector.py

**파일**: `project/Helper/broker_api_connector.py`
**라인 수**: 529 lines
**역할**: 증권사 API 통합 커넥터 (추상 기본 클래스 + KIS 구현체)

### 2.1 목적

- 증권사 API의 **추상 인터페이스 정의**
- KIS (한국투자증권) API **구현체 제공**
- 다양한 증권사 API를 **일관된 인터페이스**로 통합
- 인증, 주문, 잔고 조회 등 **핵심 기능 표준화**

### 2.2 주요 클래스

#### 2.2.1 BrokerAPIBase (추상 기본 클래스)

```python
class BrokerAPIBase(ABC):
    """
    모든 증권사 API의 기본 클래스

    Attributes:
        config: Dict - 설정 딕셔너리
        token: str - 인증 토큰
        base_url: str - API 기본 URL
    """

    @abstractmethod
    def authenticate(self) -> bool:
        """API 인증 수행"""

    @abstractmethod
    def is_market_open(self) -> bool:
        """시장 개장 여부 확인"""

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """현재가 조회"""

    @abstractmethod
    def get_balance(self) -> Dict[str, Any]:
        """계좌 잔고 조회"""

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: int,
                   price: float = None) -> Dict[str, Any]:
        """주문 실행"""
```

**설계 의도**:
- 다양한 증권사 API를 동일한 인터페이스로 통합
- 새로운 증권사 추가 시 확장 용이 (LS Securities, Interactive Brokers 등)
- Service Layer에서 증권사 독립적인 코드 작성 가능

#### 2.2.2 KISBrokerAPI (KIS 구현체)

```python
class KISBrokerAPI(BrokerAPIBase):
    """
    한국투자증권 API 구현

    Attributes:
        account_type: str - "REAL" or "VIRTUAL"
        app_key: str - API Key
        app_secret: str - API Secret
        account_no: str - 계좌번호
        product_code: str - 상품코드 (기본 "01")
        current_dist: str - 현재 계좌 구분
    """

    def make_token(self) -> Dict[str, Any]:
        """토큰 발급 (OAuth 2.0)"""

    def get_us_stock_price(self, ticker: str, exchange: str) -> Dict:
        """미국 주식 현재가 조회"""

    def get_us_balance(self) -> Dict:
        """미국 계좌 잔고 조회"""

    def place_us_order(self, ticker: str, side: str, qty: int,
                      price: float, order_type: str) -> Dict:
        """미국 주식 주문 실행"""
```

### 2.3 핵심 기능

#### 기능 1: 토큰 관리

```python
def make_token(self) -> Dict[str, Any]:
    """
    KIS API 토큰 발급

    Flow:
        1. /oauth2/tokenP 엔드포인트로 POST 요청
        2. app_key + app_secret으로 인증
        3. access_token 발급 (24시간 유효)
        4. 토큰을 self.token에 저장

    Returns:
        {
            "access_token": str,
            "token_type": "Bearer",
            "expires_in": 86400
        }
    """
    url = f"{self.base_url}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "appkey": self.app_key,
        "appsecret": self.app_secret
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        token_data = response.json()
        self.token = token_data["access_token"]
        return token_data
    else:
        raise Exception(f"Token issuance failed: {response.text}")
```

#### 기능 2: 현재가 조회

```python
def get_us_stock_price(self, ticker: str, exchange: str = "NASDAQ") -> Dict:
    """
    미국 주식 현재가 조회

    Args:
        ticker: 티커 심볼 (예: "AAPL")
        exchange: "NASDAQ", "NYSE", "AMEX"

    API Endpoint:
        GET /uapi/overseas-price/v1/quotations/price

    Returns:
        {
            "symbol": "AAPL",
            "current_price": 150.25,
            "high": 152.00,
            "low": 149.50,
            "volume": 50000000,
            "timestamp": "2023-12-01T20:00:00Z"
        }
    """
```

#### 기능 3: 주문 실행

```python
def place_us_order(self, ticker: str, side: str, qty: int,
                  price: float = None, order_type: str = "LIMIT") -> Dict:
    """
    미국 주식 주문 실행

    Args:
        ticker: 티커 심볼
        side: "BUY" or "SELL"
        qty: 수량
        price: 지정가 (None = 시장가)
        order_type: "LIMIT" or "MARKET"

    API Endpoint:
        POST /uapi/overseas-stock/v1/trading/order

    Returns:
        {
            "order_id": "20231201001",
            "status": "PENDING",
            "filled_quantity": 0,
            "message": "주문 접수 완료"
        }
    """
```

### 2.4 사용 예제

```python
from project.Helper.broker_api_connector import KISBrokerAPI

# 1. 실계좌 초기화
kis = KISBrokerAPI(
    config_path="config/api_credentials.yaml",
    account_type="REAL"
)

# 2. 인증
if kis.authenticate():
    print("✅ 인증 성공")

    # 3. 현재가 조회
    price = kis.get_current_price("AAPL")
    print(f"AAPL: ${price:.2f}")

    # 4. 주문 실행
    order = kis.place_order(
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=150.0
    )

    print(f"주문 ID: {order['order_id']}")
```

### 2.5 의존성

- **외부 패키지**: `requests`, `pytz`, `yaml`
- **내부 모듈**: `kis_common.py` (공통 함수)
- **설정 파일**: `config/api_credentials.yaml`

---

## 3. Module 2: kis_api_helper_us.py

**파일**: `project/Helper/kis_api_helper_us.py`
**라인 수**: 771 lines (가장 큰 모듈)
**역할**: KIS API 미국 시장 전용 헬퍼

### 3.1 목적

- KIS API의 **미국 시장 특화 기능** 제공
- 시장 개장 시간 체크 (Pre-Market, Regular, After-Market)
- 미국 주식 현재가, 잔고, 주문 등 **상세 구현**
- 토큰 만료 감지 및 **자동 갱신**

### 3.2 주요 클래스

#### KISUSHelper

```python
class KISUSHelper:
    """
    KIS API 미국 시장 전용 헬퍼

    Attributes:
        config: Dict - KIS API 설정
        app_key: str - API Key
        app_secret: str - API Secret
        account_no: str - 계좌번호
        product_code: str - 상품코드
        base_url: str - API Base URL
        token: str - 인증 토큰
    """

    def market_open_type(self, area: str = "US") -> str:
        """시장 상태 확인"""

    def check_and_refresh_token_if_expired(self, response) -> bool:
        """토큰 만료 확인 및 자동 갱신"""

    def make_request_with_token_retry(self, func, *args, **kwargs):
        """토큰 재시도 로직이 포함된 요청"""
```

### 3.3 핵심 기능

#### 기능 1: 시장 상태 확인

```python
def market_open_type(self, area: str = "US") -> str:
    """
    미국/홍콩 시장 개장 상태 확인

    미국 시장 시간 (뉴욕 시간):
        - Pre-Market: 04:00 ~ 09:30
        - Regular: 09:30 ~ 16:00
        - After-Market: 16:00 ~ 20:00
        - Closed: 20:00 ~ 04:00 (다음날)

    홍콩 시장 시간 (홍콩 시간):
        - Regular: 09:30 ~ 12:00, 13:00 ~ 16:00
        - Lunch Break: 12:00 ~ 13:00
        - Closed: 그 외 시간

    Args:
        area: "US" or "HK"

    Returns:
        "NormalOpen", "Pre-Market", "After-Market", "Closed"

    Implementation:
        1. 현재 UTC 시간 가져오기
        2. 해당 시장 시간대로 변환 (pytz 사용)
        3. 시간 범위 비교
        4. 상태 반환
    """
    now_utc = datetime.now(timezone.utc)

    if area.upper() == "US":
        ny_tz = pytz_timezone("America/New_York")
        now_local = now_utc.astimezone(ny_tz).time()

        pre_open = time(4, 0)
        reg_open = time(9, 30)
        reg_close = time(16, 0)
        after_close = time(20, 0)

        if pre_open <= now_local < reg_open:
            return "Pre-Market"
        elif reg_open <= now_local < reg_close:
            return "NormalOpen"
        elif reg_close <= now_local < after_close:
            return "After-Market"
        else:
            return "Closed"
```

**사용 사례**:
- 시장 개장 시간에만 주문 실행
- Pre-Market에서는 LIMIT 주문만 허용
- 시장 폐장 시 데이터 수집만 진행

#### 기능 2: 토큰 자동 갱신

```python
def check_and_refresh_token_if_expired(self, response) -> bool:
    """
    토큰 만료 감지 및 자동 갱신

    KIS API는 토큰 만료 시 에러 코드 "EGW00123" 반환

    Flow:
        1. API 응답 확인
        2. msg_cd == "EGW00123" 감지
        3. make_token() 호출하여 새 토큰 발급
        4. 3초 대기 (API 안정화)
        5. True 반환 (재시도 필요)

    Args:
        response: requests.Response 객체

    Returns:
        True = 토큰 갱신됨, 재시도 필요
        False = 정상 응답
    """
    if response.status_code != 200:
        response_data = response.json()
        if response_data.get("msg_cd") == "EGW00123":
            logger.warning("Token expired, attempting to refresh")

            try:
                self.make_token()
                time.sleep(3)
                logger.info("Token refreshed successfully")
                return True
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                return False

    return False
```

#### 기능 3: 재시도 로직

```python
def make_request_with_token_retry(self, func, *args, **kwargs):
    """
    토큰 재시도 로직이 포함된 요청 래퍼

    최대 2회 재시도 (토큰 갱신 포함)

    Args:
        func: 실행할 함수 (예: requests.get, requests.post)
        *args, **kwargs: func에 전달할 인자

    Returns:
        requests.Response

    Example:
        response = self.make_request_with_token_retry(
            requests.get,
            url=api_url,
            headers=headers
        )
    """
    max_retries = 2

    for attempt in range(max_retries):
        response = func(*args, **kwargs)

        # 토큰 만료 확인
        if self.check_and_refresh_token_if_expired(response):
            if attempt < max_retries - 1:
                logger.info(f"Retrying request (attempt {attempt + 2})")
                continue

        return response

    return response
```

### 3.4 사용 예제

```python
from project.Helper.kis_api_helper_us import KISUSHelper

# 1. 설정 로드
config = {
    "app_key": "YOUR_APP_KEY",
    "app_secret": "YOUR_APP_SECRET",
    "account_no": "12345678",
    "product_code": "01",
    "base_url": "https://openapi.koreainvestment.com:9443"
}

kis = KISUSHelper(config)

# 2. 시장 상태 확인
market_status = kis.market_open_type("US")

if market_status == "NormalOpen":
    print("🟢 정규 시장 개장 중")

    # 3. 현재가 조회 (토큰 자동 갱신 포함)
    price_data = kis.get_current_price_us("AAPL", "NASDAQ")
    print(f"AAPL: ${price_data['current_price']:.2f}")

elif market_status == "Pre-Market":
    print("🟡 프리마켓 시간")

else:
    print("🔴 시장 폐장")
```

### 3.5 의존성

- **외부 패키지**: `requests`, `pytz`, `pandas`
- **내부 모듈**: `kis_common.py`
- **설정 파일**: `config/api_credentials.yaml`

---

## 4. Module 3: kis_common.py

**파일**: `project/Helper/kis_common.py`
**라인 수**: 359 lines
**역할**: KIS API 공통 유틸리티 함수

### 4.1 목적

- KIS API에서 **공통으로 사용되는 함수** 제공
- HTTP 요청 헤더 생성
- 응답 데이터 파싱
- 에러 처리 유틸리티

### 4.2 주요 함수

#### 4.2.1 헤더 생성

```python
def create_kis_headers(token: str, tr_id: str, custtype: str = "P") -> Dict[str, str]:
    """
    KIS API 요청 헤더 생성

    Args:
        token: 인증 토큰
        tr_id: 거래 ID (API 종류별로 다름)
        custtype: 고객 타입 ("P" = 개인, "B" = 법인)

    Returns:
        {
            "authorization": f"Bearer {token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": tr_id,
            "custtype": custtype,
            "content-type": "application/json"
        }

    TR_ID 예시:
        - "HHDFS00000300": 미국 주식 현재가 조회
        - "JTTT1002U": 미국 주식 매수 주문
        - "JTTT1006U": 미국 주식 매도 주문
    """
```

#### 4.2.2 응답 파싱

```python
def parse_kis_response(response: requests.Response) -> Dict[str, Any]:
    """
    KIS API 응답 파싱 및 에러 처리

    KIS API 응답 구조:
        {
            "rt_cd": "0",           # 결과 코드 ("0" = 성공)
            "msg_cd": "MCA00000",   # 메시지 코드
            "msg1": "정상처리 되었습니다",
            "output": { ... }       # 실제 데이터
        }

    Args:
        response: requests.Response 객체

    Returns:
        output 딕셔너리 (성공 시)

    Raises:
        Exception: rt_cd != "0" 또는 HTTP 에러
    """
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    data = response.json()

    if data.get("rt_cd") != "0":
        error_msg = data.get("msg1", "Unknown error")
        raise Exception(f"KIS API Error: {error_msg}")

    return data.get("output", {})
```

### 4.3 사용 예제

```python
from project.Helper.kis_common import create_kis_headers, parse_kis_response
import requests

# 1. 헤더 생성
headers = create_kis_headers(
    token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    tr_id="HHDFS00000300",
    custtype="P"
)

# 2. API 요청
response = requests.get(
    url="https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price",
    headers=headers,
    params={"EXCD": "NAS", "SYMB": "AAPL"}
)

# 3. 응답 파싱
try:
    data = parse_kis_response(response)
    print(f"현재가: {data['last']}")
except Exception as e:
    print(f"에러: {e}")
```

---

## 5. Module 4: data_provider_api.py

**파일**: `project/Helper/data_provider_api.py`
**라인 수**: 427 lines
**역할**: 데이터 프로바이더 통합 (Alpha Vantage, Yahoo Finance)

### 5.1 목적

- 외부 데이터 프로바이더 API **추상화**
- Alpha Vantage API **구현**
- 티커 리스트, OHLCV, 펀더멘털 데이터 수집
- Rate Limit 관리

### 5.2 주요 클래스

#### 5.2.1 DataProviderBase (추상 기본 클래스)

```python
class DataProviderBase(ABC):
    """
    데이터 프로바이더 기본 클래스

    Attributes:
        config: Dict - 설정 딕셔너리
        api_key: str - API 키
    """

    @abstractmethod
    def get_ohlcv(self, symbol: str, start_date: datetime = None,
                  end_date: datetime = None, interval: str = "1d") -> pd.DataFrame:
        """OHLCV 데이터 조회"""

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """현재가 조회"""
```

#### 5.2.2 AlphaVantageAPI (Alpha Vantage 구현체)

```python
class AlphaVantageAPI(DataProviderBase):
    """
    Alpha Vantage API 구현

    Attributes:
        api_key: str - Alpha Vantage API 키
        base_url: str - "https://www.alphavantage.co/query"
        rate_limit_delay: int - 12초 (free tier: 5 calls/min)
    """

    def get_ticker_list(self, market: str = 'NASDAQ',
                       asset_type: str = 'Stock',
                       active: bool = True) -> List[str]:
        """티커 리스트 조회"""

    def get_ohlcv_intraday(self, symbol: str, interval: str = "1min",
                          outputsize: str = "compact") -> pd.DataFrame:
        """분봉 데이터 조회"""
```

### 5.3 핵심 기능

#### 기능 1: 티커 리스트 조회

```python
def get_ticker_list(self, market: str = 'NASDAQ',
                   asset_type: str = 'Stock',
                   active: bool = True) -> List[str]:
    """
    Alpha Vantage API로 티커 리스트 조회

    API Endpoint:
        GET https://www.alphavantage.co/query?function=LISTING_STATUS

    Args:
        market: "NASDAQ", "NYSE", "AMEX"
        asset_type: "Stock", "ETF"
        active: True = 상장 종목, False = 상장폐지

    Returns:
        List of tickers (예: ["AAPL", "MSFT", "GOOGL", ...])

    CSV Format:
        symbol,name,exchange,assetType,ipoDate,delistingDate,status
        AAPL,Apple Inc,NASDAQ,Stock,1980-12-12,null,Active

    Implementation:
        1. API 요청 (CSV 형식 응답)
        2. CSV 파싱
        3. market == NASDAQ and assetType == Stock 필터링
        4. 심볼만 추출하여 리스트 반환
    """
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
```

**사용 사례**:
- NASDAQ 전체 종목 리스트 가져오기 → Universe 생성
- ETF 종목만 필터링 → ETF 전략
- 상장폐지 종목 확인 → 데이터 정리

#### 기능 2: 분봉 데이터 조회

```python
def get_ohlcv_intraday(self, symbol: str, interval: str = "1min",
                      outputsize: str = "compact") -> pd.DataFrame:
    """
    분봉 OHLCV 데이터 조회 (고빈도 전략용)

    API Endpoint:
        GET https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY

    Args:
        symbol: 티커
        interval: "1min", "5min", "15min", "30min", "60min"
        outputsize: "compact" (최근 100개) or "full" (전체)

    Returns:
        DataFrame with columns: [open, high, low, close, volume]

    Rate Limiting:
        - Free tier: 5 calls/minute
        - 요청 후 12초 대기 (5 * 12 = 60초)
    """
    url = f"{self.base_url}?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&extended_hours=false&outputsize={outputsize}&apikey={self.api_key}"

    response = requests.get(url)
    time.sleep(self.rate_limit_delay)  # Rate limiting

    if response.status_code == 200:
        data = response.json()
        time_series = data.get(f"Time Series ({interval})", {})

        df = pd.DataFrame.from_dict(time_series, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        # 컬럼명 정리
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df = df.astype(float)

        return df
    else:
        logger.error(f"Failed to get intraday data: {response.status_code}")
        return pd.DataFrame()
```

### 5.4 사용 예제

```python
from project.Helper.data_provider_api import AlphaVantageAPI

# 1. API 초기화
av = AlphaVantageAPI(config_path="config/data_provider_config.yaml")

# 2. NASDAQ 종목 리스트
nasdaq_stocks = av.get_ticker_list(market="NASDAQ", asset_type="Stock")
print(f"NASDAQ 종목 수: {len(nasdaq_stocks)}")

# 3. 분봉 데이터 (5분봉)
df_5min = av.get_ohlcv_intraday("AAPL", interval="5min", outputsize="full")
print(f"5분봉 데이터: {len(df_5min)} rows")
print(df_5min.tail())
```

---

## 6. Module 5: yfinance_helper.py

**파일**: `project/Helper/yfinance_helper.py`
**라인 수**: 296 lines
**역할**: Yahoo Finance API 헬퍼

### 6.1 목적

- **Yahoo Finance** 데이터 수집 (무료, API 키 불필요)
- 일봉/주봉 OHLCV 데이터
- 펀더멘털 데이터 (P/E, ROE, EPS 등)
- Asset 정보 (Sector, Industry, Exchange)

### 6.2 주요 클래스

#### YFinanceHelper

```python
class YFinanceHelper:
    """
    Yahoo Finance API 헬퍼

    yfinance 라이브러리 기반
    """

    def get_ohlcv(self, stock_code: str, p_code: str,
                  start_date: datetime, end_date: datetime,
                  ohlcv: str = "Y") -> pd.DataFrame:
        """OHLCV 데이터 조회"""

    def get_asset_info(self, ticker: str, info_type: str = "quoteType") -> str:
        """Asset 정보 조회"""

    def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """펀더멘털 데이터 조회"""
```

### 6.3 핵심 기능

#### 기능 1: OHLCV 데이터 조회

```python
def get_ohlcv(self, stock_code: str, p_code: str,
              start_date: datetime, end_date: datetime,
              ohlcv: str = "Y") -> pd.DataFrame:
    """
    Yahoo Finance OHLCV 데이터 조회

    Args:
        stock_code: 티커 심볼
        p_code: "W" = 주봉, "D" = 일봉
        start_date: 시작일
        end_date: 종료일
        ohlcv: "Y" = 수정주가 (adjusted), "N" = 원본

    Returns:
        DataFrame with columns:
            [open, high, low, close, volume, dividends, stock_splits]

    Example:
                           open    high     low   close    volume
        2023-01-03 00:00:00+00:00  130.28  130.90  124.17  125.07  112117471
        2023-01-04 00:00:00+00:00  126.89  128.66  125.08  126.36   89113671
    """
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

    # Rename columns
    df.rename(columns={
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
        'Dividends': 'dividends',
        'Stock Splits': 'stock_splits'
    }, inplace=True)

    return df
```

#### 기능 2: 펀더멘털 데이터

```python
def get_fundamental_data(self, ticker: str) -> Dict[str, Any]:
    """
    Yahoo Finance 펀더멘털 데이터 조회

    Args:
        ticker: 티커 심볼

    Returns:
        {
            "market_cap": float,        # 시가총액 (억 달러)
            "pe_ratio": float,          # P/E Ratio
            "pb_ratio": float,          # P/B Ratio
            "ps_ratio": float,          # P/S Ratio
            "roe": float,               # Return on Equity (%)
            "roa": float,               # Return on Assets (%)
            "eps": float,               # Earnings Per Share
            "revenue": float,           # Revenue (억 달러)
            "net_income": float,        # Net Income (억 달러)
            "dividend_yield": float,    # Dividend Yield (%)
            "beta": float,              # Beta
            "52week_high": float,
            "52week_low": float
        }
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "market_cap": info.get("marketCap", 0) / 1e9,  # 억 달러
        "pe_ratio": info.get("trailingPE", None),
        "pb_ratio": info.get("priceToBook", None),
        "ps_ratio": info.get("priceToSalesTrailing12Months", None),
        "roe": info.get("returnOnEquity", None) * 100 if info.get("returnOnEquity") else None,
        "roa": info.get("returnOnAssets", None) * 100 if info.get("returnOnAssets") else None,
        "eps": info.get("trailingEps", None),
        "revenue": info.get("totalRevenue", 0) / 1e9,
        "net_income": info.get("netIncomeToCommon", 0) / 1e9,
        "dividend_yield": info.get("dividendYield", 0) * 100,
        "beta": info.get("beta", None),
        "52week_high": info.get("fiftyTwoWeekHigh", None),
        "52week_low": info.get("fiftyTwoWeekLow", None)
    }
```

### 6.4 사용 예제

```python
from project.Helper.yfinance_helper import YFinanceHelper
from datetime import datetime

yf = YFinanceHelper()

# 1. 일봉 데이터
df_daily = yf.get_ohlcv(
    stock_code="AAPL",
    p_code="D",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    ohlcv="Y"
)
print(f"일봉: {len(df_daily)} rows")

# 2. 펀더멘털 데이터
fundamental = yf.get_fundamental_data("AAPL")
print(f"P/E: {fundamental['pe_ratio']:.2f}")
print(f"ROE: {fundamental['roe']:.2f}%")

# 3. Asset 정보
sector = yf.get_asset_info("AAPL", "sector")
print(f"Sector: {sector}")
```

---

## 7. Module 6: telegram_messenger.py

**파일**: `project/Helper/telegram_messenger.py`
**라인 수**: 419 lines
**역할**: Telegram Bot 메신저

### 7.1 목적

- **Telegram Bot API** 연동
- 백테스트 결과, 주문 알림 전송
- 차트 이미지 전송
- 재시도 로직 (네트워크 불안정 대응)

### 7.2 주요 클래스

#### TelegramBot

```python
class TelegramBot:
    """
    Telegram Bot 메신저

    Attributes:
        bot_token: str - Bot API 토큰
        default_chat_id: str - 기본 채팅방 ID
        base_url: str - Telegram API URL
    """

    def send_message(self, message: str, chat_id: str = None,
                    parse_mode: str = 'HTML',
                    add_timestamp: bool = True) -> bool:
        """메시지 전송"""

    def send_message_with_retry(self, message: str, chat_id: str = None,
                               max_retries: int = 3,
                               retry_delay: int = 2) -> bool:
        """재시도 로직이 있는 메시지 전송"""

    def send_photo(self, photo_path: str, caption: str = None,
                   chat_id: str = None) -> bool:
        """이미지 전송"""

    def send_backtest_report(self, report: Dict, chart_path: str = None,
                            chat_id: str = None) -> Dict[str, Any]:
        """백테스트 리포트 전송"""
```

### 7.3 핵심 기능

#### 기능 1: 메시지 전송

```python
def send_message(self, message: str, chat_id: str = None,
                parse_mode: str = 'HTML',
                add_timestamp: bool = True) -> bool:
    """
    Telegram 메시지 전송

    Args:
        message: 메시지 내용
        chat_id: 채팅방 ID (None = default_chat_id)
        parse_mode: "HTML" or "Markdown"
        add_timestamp: 타임스탬프 추가 여부

    HTML 포맷 예시:
        <b>굵게</b>
        <i>기울임</i>
        <code>코드</code>
        <pre>여러 줄 코드</pre>

    Returns:
        True = 전송 성공, False = 실패
    """
    target_chat_id = chat_id or self.default_chat_id

    if not target_chat_id:
        logger.error("No chat ID provided")
        return False

    # Add timestamp
    if add_timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] {message}"
    else:
        formatted_msg = message

    # Send via Telegram API
    url = f"{self.base_url}/sendMessage"
    data = {
        'chat_id': target_chat_id,
        'text': formatted_msg,
        'parse_mode': parse_mode
    }

    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()

    logger.info(f"Telegram message sent to {target_chat_id}")
    return True
```

#### 기능 2: 백테스트 리포트 전송

```python
def send_backtest_report(self, report: Dict, chart_path: str = None,
                        chat_id: str = None) -> Dict[str, Any]:
    """
    백테스트 리포트를 포맷팅하여 Telegram 전송

    Args:
        report: Service Layer의 BacktestResult 딕셔너리
        chart_path: 차트 이미지 경로 (optional)
        chat_id: 채팅방 ID

    Returns:
        {
            "success": bool,
            "messages_sent": int,
            "message_ids": List[str]
        }

    HTML 포맷 예시:
        📊 <b>백테스트 결과</b>

        📈 <b>성과 지표</b>
        총 수익률: <code>+12.5%</code>
        샤프 비율: <code>1.25</code>
        최대 낙폭: <code>-5.2%</code>

        💰 <b>거래 통계</b>
        총 거래 수: <code>45</code>
        승률: <code>58.3%</code>
    """
    # 1. 리포트 포맷팅
    html_message = f"""
📊 <b>백테스트 결과</b>

📈 <b>성과 지표</b>
총 수익률: <code>{report['total_return']:+.2f}%</code>
샤프 비율: <code>{report['sharpe_ratio']:.3f}</code>
최대 낙폭: <code>{report['max_drawdown']:.2f}%</code>

💰 <b>거래 통계</b>
총 거래 수: <code>{report['total_trades']}</code>
승률: <code>{report['win_rate']:.2f}%</code>
평균 보유 기간: <code>{report['avg_holding_days']:.1f}일</code>
"""

    # 2. 메시지 전송
    success = self.send_message(html_message, chat_id, parse_mode="HTML")

    # 3. 차트 전송 (optional)
    photo_sent = False
    if chart_path and os.path.exists(chart_path):
        photo_sent = self.send_photo(chart_path, "📊 수익률 차트", chat_id)

    return {
        "success": success,
        "messages_sent": 1 + (1 if photo_sent else 0),
        "photo_sent": photo_sent
    }
```

### 7.4 사용 예제

```python
from project.Helper.telegram_messenger import TelegramBot

# 1. Bot 초기화
bot = TelegramBot(
    bot_token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    default_chat_id="-1001234567890"
)

# 2. 간단한 메시지
bot.send_message("📊 백테스트 시작")

# 3. HTML 포맷 메시지
html_msg = """
<b>주문 체결 알림</b>
종목: <code>AAPL</code>
수량: <code>10주</code>
가격: <code>$150.00</code>
"""
bot.send_message(html_msg, parse_mode="HTML")

# 4. 백테스트 리포트
report = {
    "total_return": 12.5,
    "sharpe_ratio": 1.25,
    "max_drawdown": -5.2,
    "total_trades": 45,
    "win_rate": 58.3,
    "avg_holding_days": 15.2
}

result = bot.send_backtest_report(
    report=report,
    chart_path="report/chart.png"
)

print(f"전송 완료: {result['messages_sent']}개 메시지")
```

---

## 8. 모듈 간 통합 예제

### 8.1 전체 시스템 통합 예제

```python
from project.Helper.broker_api_connector import KISBrokerAPI
from project.Helper.yfinance_helper import YFinanceHelper
from project.Helper.telegram_messenger import TelegramBot
from datetime import datetime, timedelta

# 1. 각 모듈 초기화
kis = KISBrokerAPI(config_path="config/api_credentials.yaml", account_type="REAL")
yf = YFinanceHelper()
bot = TelegramBot(bot_token="YOUR_TOKEN", default_chat_id="YOUR_CHAT_ID")

# 2. 시장 상태 확인
if kis.is_market_open():
    bot.send_message("🟢 시장 개장 - 트레이딩 시작")

    # 3. 종목 선정 (Yahoo Finance)
    df_aapl = yf.get_ohlcv(
        stock_code="AAPL",
        p_code="D",
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        ohlcv="Y"
    )

    # 4. 펀더멘털 체크
    fundamental = yf.get_fundamental_data("AAPL")
    pe_ratio = fundamental.get('pe_ratio', 0)

    if pe_ratio < 30:  # P/E < 30
        # 5. 주문 실행
        order = kis.place_order(
            symbol="AAPL",
            side="BUY",
            quantity=10,
            price=df_aapl.iloc[-1]['close']
        )

        # 6. 주문 결과 Telegram 전송
        if order['status'] == 'FILLED':
            bot.send_message(
                f"""
                <b>✅ 주문 체결</b>
                종목: <code>AAPL</code>
                수량: <code>10주</code>
                가격: <code>${df_aapl.iloc[-1]['close']:.2f}</code>
                P/E: <code>{pe_ratio:.2f}</code>
                """,
                parse_mode="HTML"
            )
        else:
            bot.send_message(f"❌ 주문 실패: {order['message']}")
else:
    bot.send_message("🔴 시장 폐장 - 대기 모드")
```

---

## 9. 성능 및 모니터링

### 9.1 성능 지표

| 모듈 | 주요 함수 | 평균 응답 시간 | 비고 |
|-----|----------|--------------|------|
| broker_api_connector | authenticate() | 1-2초 | 하루 1회 |
| broker_api_connector | get_current_price() | 0.3-0.5초 | - |
| broker_api_connector | place_order() | 1-3초 | 시장 상황에 따라 변동 |
| data_provider_api | get_ticker_list() | 5-10초 | CSV 파싱 시간 포함 |
| data_provider_api | get_ohlcv_intraday() | 3-5초 | 12초 대기 포함 |
| yfinance_helper | get_ohlcv() | 2-5초 | 1년 데이터 기준 |
| yfinance_helper | get_fundamental_data() | 1-3초 | - |
| telegram_messenger | send_message() | 0.5-1초 | 네트워크 상태에 따라 변동 |

### 9.2 에러율 모니터링

```python
import logging
from functools import wraps

def monitor_helper_function(func):
    """Helper 함수 모니터링 데코레이터"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            logger.info(f"{func.__name__} succeeded in {elapsed:.2f}s")
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise

    return wrapper

# 사용 예제
class MonitoredKISAPI(KISBrokerAPI):

    @monitor_helper_function
    def authenticate(self):
        return super().authenticate()

    @monitor_helper_function
    def place_order(self, *args, **kwargs):
        return super().place_order(*args, **kwargs)
```

---

## 10. 테스트 전략

### 10.1 단위 테스트

```python
import unittest
from project.Helper.yfinance_helper import YFinanceHelper

class TestYFinanceHelper(unittest.TestCase):

    def setUp(self):
        self.yf = YFinanceHelper()

    def test_get_ohlcv(self):
        """일봉 데이터 조회 테스트"""
        df = self.yf.get_ohlcv(
            stock_code="AAPL",
            p_code="D",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            ohlcv="Y"
        )

        self.assertFalse(df.empty)
        self.assertIn('close', df.columns)
        self.assertEqual(len(df), 20)  # ~20 trading days in Jan

    def test_get_asset_info(self):
        """Asset 정보 조회 테스트"""
        asset_type = self.yf.get_asset_info("AAPL", "quoteType")
        self.assertEqual(asset_type, "EQUITY")

        sector = self.yf.get_asset_info("AAPL", "sector")
        self.assertEqual(sector, "Technology")
```

### 10.2 통합 테스트

```python
def test_kis_telegram_integration():
    """KIS API + Telegram 통합 테스트"""

    # 1. KIS API 초기화
    kis = KISBrokerAPI(config_path="config/test_config.yaml", account_type="VIRTUAL")
    kis.authenticate()

    # 2. 잔고 조회
    balance = kis.get_balance()

    # 3. Telegram 전송
    bot = TelegramBot(bot_token="TEST_TOKEN", default_chat_id="TEST_CHAT")
    result = bot.send_message(f"잔고: ${balance['total_balance']:.2f}억")

    assert result == True
```

---

## 11. 의존성 및 요구사항

### 11.1 Python 패키지

```
yfinance==0.2.28
requests==2.31.0
pandas==2.0.3
pytz==2023.3
PyYAML==6.0.1
python-telegram-bot==20.4  # Optional
```

### 11.2 외부 API 요구사항

| API | 요구사항 | 비용 |
|-----|---------|------|
| Alpha Vantage | API 키 발급 | Free: 500 calls/day, Premium: $49.99/month |
| Yahoo Finance | 없음 (오픈 소스) | 무료 |
| KIS API | 계좌 개설 + API 신청 | 계좌 개설 필요 |
| Telegram Bot | Bot 생성 + Chat ID | 무료 |

---

## 12. 참조 문서

- **HELPER_LAYER_INTERFACE.md**: 인터페이스 명세
- **CLAUDE.md v2.4**: 프로젝트 규칙
- **config/api_credentials.yaml**: API 자격증명 예제
- **config/broker_config.yaml**: 증권사 설정

---

**작성자**: Service Agent
**검토자**: Orchestrator Agent
**승인 날짜**: 2025-10-09
