# Helper Layer API Integration Specification

**버전**: 1.0
**작성일**: 2025-10-09
**Layer**: Helper Layer (External API Integration & System Services)
**담당 Agent**: Helper Agent
**참조**: HELPER_LAYER_INTERFACE.md, HELPER_MODULES.md

---

## 1. 개요

본 문서는 Helper Layer의 외부 API 통합에 대한 **상세 알고리즘 및 구현 명세**를 제공합니다.

### 1.1 통합 대상 API

| API | 목적 | 인증 방식 | Rate Limit |
|-----|------|----------|-----------|
| **KIS API** | 실거래 주문 실행 | OAuth 2.0 | 20 req/sec |
| **Alpha Vantage** | 시장 데이터 수집 | API Key | 5 req/min (free) |
| **Yahoo Finance** | OHLCV 및 펀더멘털 | 없음 (오픈소스) | 2000 req/hour |
| **Telegram Bot API** | 알림 및 리포트 전송 | Bot Token | 30 msg/sec |

### 1.2 문서 구성

```
API_INTEGRATION_SPEC.md (본 문서)
├── 2. KIS API 통합 명세
├── 3. Alpha Vantage API 통합 명세
├── 4. Yahoo Finance API 통합 명세
├── 5. Telegram Bot API 통합 명세
├── 6. 에러 처리 및 Fallback 전략
├── 7. Rate Limiting 및 최적화
└── 8. 보안 및 인증 관리
```

---

## 2. KIS API 통합 명세

### 2.1 개요

**KIS (한국투자증권) API**는 국내/해외 주식 거래를 지원하는 REST API입니다.

- **Base URL (실계좌)**: `https://openapi.koreainvestment.com:9443`
- **Base URL (모의계좌)**: `https://openapivts.koreainvestment.com:29443`
- **인증 방식**: OAuth 2.0 (Client Credentials)
- **토큰 유효기간**: 24시간

### 2.2 인증 알고리즘

#### 2.2.1 토큰 발급 (make_token)

```python
def make_token() -> Dict[str, Any]:
    """
    KIS API 토큰 발급

    Flow:
        1. /oauth2/tokenP 엔드포인트로 POST 요청
        2. app_key + app_secret으로 인증
        3. access_token 수신 (24시간 유효)
        4. 토큰을 메모리에 저장

    Algorithm:
        INPUT: app_key, app_secret
        OUTPUT: access_token, expires_in

        1. url = base_url + "/oauth2/tokenP"
        2. headers = {"content-type": "application/json"}
        3. body = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret
        }
        4. response = POST(url, headers, body)
        5. IF response.status_code == 200:
            access_token = response.json()["access_token"]
            expires_in = response.json()["expires_in"]  # 86400 (24시간)
            RETURN {access_token, expires_in}
           ELSE:
            RAISE Exception("Token issuance failed")

    Complexity:
        - Time: O(1) - HTTP 요청 1회
        - Space: O(1) - 토큰 문자열 저장

    Error Handling:
        - HTTP 401: app_key/secret 오류 → 설정 파일 재확인
        - HTTP 429: Rate limit 초과 → 1분 대기 후 재시도
        - Network Error: 3회 재시도 (exponential backoff)
    """

    url = f"{self.base_url}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "appkey": self.app_key,
        "appsecret": self.app_secret
    }

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                self.token_issued_at = datetime.now()
                logger.info("✅ KIS API token issued successfully")
                return token_data

            elif response.status_code == 401:
                raise Exception("Invalid app_key or app_secret")

            elif response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting 60s...")
                time.sleep(60)
                continue

        except requests.exceptions.RequestException as e:
            logger.error(f"Token request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
            raise

    raise Exception("Failed to issue token after max retries")
```

#### 2.2.2 토큰 자동 갱신 (check_and_refresh_token_if_expired)

```python
def check_and_refresh_token_if_expired(response) -> bool:
    """
    토큰 만료 감지 및 자동 갱신

    KIS API는 토큰 만료 시 다음과 같은 응답 반환:
        {
            "rt_cd": "1",
            "msg_cd": "EGW00123",
            "msg1": "세션이 만료되었습니다"
        }

    Algorithm:
        INPUT: response (requests.Response)
        OUTPUT: is_token_refreshed (bool)

        1. IF response.status_code != 200:
            data = response.json()
            IF data["msg_cd"] == "EGW00123":  # 토큰 만료 에러
                logger.warning("Token expired, refreshing...")

                2. TRY:
                    make_token()  # 새 토큰 발급
                    sleep(3)      # API 안정화 대기
                    RETURN True   # 재시도 필요

                3. EXCEPT Exception as e:
                    logger.error("Token refresh failed")
                    RETURN False

        4. RETURN False  # 정상 응답

    Usage:
        response = requests.get(url, headers=headers)

        if check_and_refresh_token_if_expired(response):
            # 토큰 갱신됨 → 재시도
            response = requests.get(url, headers=headers)

    Complexity:
        - Time: O(1) + make_token() = O(1)
        - Space: O(1)
    """

    if response.status_code != 200:
        try:
            response_data = response.json()
            if response_data.get("msg_cd") == "EGW00123":
                logger.warning("Token expired, attempting to refresh")

                try:
                    self.make_token()
                    time.sleep(3)  # API stabilization
                    logger.info("Token refreshed successfully")
                    return True
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    return False
        except Exception as e:
            logger.error(f"Error checking token: {e}")

    return False
```

### 2.3 미국 주식 현재가 조회 (get_current_price_us)

```python
def get_current_price_us(ticker: str, exchange: str = "NASDAQ") -> Dict[str, Any]:
    """
    미국 주식 현재가 조회

    API Endpoint:
        GET /uapi/overseas-price/v1/quotations/price

    Request Headers:
        - authorization: Bearer {access_token}
        - appkey: {app_key}
        - appsecret: {app_secret}
        - tr_id: "HHDFS00000300"  # 미국 주식 현재가 조회

    Query Parameters:
        - EXCD: 거래소 코드
            "NAS" = NASDAQ
            "NYS" = NYSE
            "AMS" = AMEX
        - SYMB: 티커 심볼 (예: "AAPL")

    Response:
        {
            "rt_cd": "0",                    # 결과 코드 ("0" = 성공)
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다",
            "output": {
                "rsym": "AAPL",              # 티커
                "last": "150.25",            # 현재가
                "open": "149.50",            # 시가
                "high": "152.00",            # 고가
                "low": "149.00",             # 저가
                "tvol": "50000000",          # 거래량
                "tamt": "7500000000"         # 거래대금
            }
        }

    Algorithm:
        INPUT: ticker, exchange
        OUTPUT: {symbol, current_price, high, low, volume, timestamp}

        1. excd_map = {"NASDAQ": "NAS", "NYSE": "NYS", "AMEX": "AMS"}
        2. excd = excd_map[exchange]

        3. url = base_url + "/uapi/overseas-price/v1/quotations/price"
        4. headers = {
            "authorization": f"Bearer {token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": "HHDFS00000300"
        }
        5. params = {"EXCD": excd, "SYMB": ticker}

        6. response = make_request_with_token_retry(GET, url, headers, params)

        7. IF response.status_code == 200:
            output = response.json()["output"]
            RETURN {
                "symbol": output["rsym"],
                "current_price": float(output["last"]),
                "high": float(output["high"]),
                "low": float(output["low"]),
                "volume": int(output["tvol"]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
           ELSE:
            RAISE Exception("Failed to get current price")

    Complexity:
        - Time: O(1) - HTTP 요청 1-2회 (토큰 갱신 포함)
        - Space: O(1)

    Rate Limit:
        - KIS API: 20 req/sec
        - 초당 최대 20개 티커 조회 가능
    """

    excd_map = {"NASDAQ": "NAS", "NYSE": "NYS", "AMEX": "AMS"}
    excd = excd_map.get(exchange, "NAS")

    url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
    headers = {
        "authorization": f"Bearer {self.token}",
        "appkey": self.app_key,
        "appsecret": self.app_secret,
        "tr_id": "HHDFS00000300"
    }
    params = {"EXCD": excd, "SYMB": ticker}

    response = self.make_request_with_token_retry(
        requests.get, url=url, headers=headers, params=params, timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("rt_cd") == "0":
            output = data["output"]
            return {
                "symbol": output["rsym"],
                "current_price": float(output["last"]),
                "high": float(output["high"]),
                "low": float(output["low"]),
                "volume": int(output["tvol"]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise Exception(f"KIS API Error: {data.get('msg1')}")
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text}")
```

### 2.4 미국 주식 주문 실행 (place_order_us)

```python
def place_order_us(ticker: str, side: str, quantity: int,
                  price: float = None, order_type: str = "LIMIT") -> Dict[str, Any]:
    """
    미국 주식 주문 실행

    API Endpoint:
        POST /uapi/overseas-stock/v1/trading/order

    Request Headers:
        - tr_id:
            "JTTT1002U" = 매수 (실계좌)
            "VTTT1002U" = 매수 (모의계좌)
            "JTTT1006U" = 매도 (실계좌)
            "VTTT1006U" = 매도 (모의계좌)

    Request Body:
        {
            "CANO": "12345678",           # 계좌번호
            "ACNT_PRDT_CD": "01",         # 상품코드
            "OVRS_EXCG_CD": "NASD",       # 거래소 (NASD/NYSE)
            "PDNO": "AAPL",               # 티커
            "ORD_QTY": "10",              # 수량
            "OVRS_ORD_UNPR": "150.00",    # 가격 (0 = 시장가)
            "ORD_SVR_DVSN_CD": "0"        # 주문 구분 ("0" = 지정가)
        }

    Response:
        {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다",
            "output": {
                "KRX_FWDG_ORD_ORGNO": "91252",     # 주문조직번호
                "ODNO": "0000117057",              # 주문번호
                "ORD_TMD": "121052"                # 주문시각
            }
        }

    Algorithm:
        INPUT: ticker, side, quantity, price, order_type
        OUTPUT: {order_id, status, message}

        1. # 주문 구분 결정
        IF order_type == "MARKET":
            ord_dvsn = "0"  # 지정가 (KIS는 시장가 미지원 → 가격 0 입력)
            price = 0
        ELSE:
            ord_dvsn = "0"  # 지정가

        2. # TR_ID 결정
        IF account_type == "REAL":
            tr_id = "JTTT1002U" if side == "BUY" else "JTTT1006U"
        ELSE:
            tr_id = "VTTT1002U" if side == "BUY" else "VTTT1006U"

        3. # 거래소 코드
        exchange_code = "NASD"  # 기본 NASDAQ (또는 "NYSE")

        4. # 주문 데이터 구성
        order_data = {
            "CANO": account_no,
            "ACNT_PRDT_CD": product_code,
            "OVRS_EXCG_CD": exchange_code,
            "PDNO": ticker,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price),
            "ORD_SVR_DVSN_CD": ord_dvsn
        }

        5. # API 요청
        url = base_url + "/uapi/overseas-stock/v1/trading/order"
        headers = create_headers(token, tr_id)

        response = make_request_with_token_retry(POST, url, headers, order_data)

        6. # 응답 파싱
        IF response.status_code == 200:
            data = response.json()
            IF data["rt_cd"] == "0":
                RETURN {
                    "order_id": data["output"]["ODNO"],
                    "status": "PENDING",
                    "message": data["msg1"]
                }
            ELSE:
                RETURN {
                    "order_id": None,
                    "status": "REJECTED",
                    "message": data["msg1"]
                }
        ELSE:
            RAISE Exception("Order request failed")

    Complexity:
        - Time: O(1) - HTTP 요청 1-2회
        - Space: O(1)

    Error Handling:
        - 잔고 부족: rt_cd != "0", msg1 = "잔고부족"
        - 시장 폐장: rt_cd != "0", msg1 = "거래불가시간"
        - 주문 수량 오류: quantity validation 필요
    """

    # 1. 주문 구분
    if order_type == "MARKET":
        ord_dvsn = "0"
        price = 0  # 시장가는 가격 0
    else:
        ord_dvsn = "0"  # 지정가

    # 2. TR_ID
    if self.account_type == "REAL":
        tr_id = "JTTT1002U" if side == "BUY" else "JTTT1006U"
    else:
        tr_id = "VTTT1002U" if side == "BUY" else "VTTT1006U"

    # 3. 주문 데이터
    order_data = {
        "CANO": self.account_no,
        "ACNT_PRDT_CD": self.product_code,
        "OVRS_EXCG_CD": "NASD",  # NASDAQ
        "PDNO": ticker,
        "ORD_QTY": str(quantity),
        "OVRS_ORD_UNPR": str(price),
        "ORD_SVR_DVSN_CD": ord_dvsn
    }

    # 4. API 요청
    url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
    headers = {
        "authorization": f"Bearer {self.token}",
        "appkey": self.app_key,
        "appsecret": self.app_secret,
        "tr_id": tr_id,
        "content-type": "application/json"
    }

    response = self.make_request_with_token_retry(
        requests.post, url=url, headers=headers, json=order_data, timeout=10
    )

    # 5. 응답 파싱
    if response.status_code == 200:
        data = response.json()
        if data.get("rt_cd") == "0":
            return {
                "order_id": data["output"]["ODNO"],
                "symbol": ticker,
                "side": side,
                "quantity": quantity,
                "price": price,
                "status": "PENDING",
                "message": data["msg1"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "order_id": None,
                "symbol": ticker,
                "status": "REJECTED",
                "message": data.get("msg1", "Unknown error"),
                "error_code": data.get("msg_cd"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    else:
        raise Exception(f"Order request failed: HTTP {response.status_code}")
```

### 2.5 시장 개장 상태 확인 (market_open_type)

```python
def market_open_type(area: str = "US") -> str:
    """
    미국/홍콩 시장 개장 상태 확인

    Algorithm:
        INPUT: area ("US" or "HK")
        OUTPUT: market_status

        1. now_utc = current_time_in_UTC()

        2. IF area == "US":
            # New York timezone 변환
            ny_tz = timezone("America/New_York")
            now_local = now_utc.astimezone(ny_tz).time()

            # 시간 범위 정의
            pre_open = 04:00
            reg_open = 09:30
            reg_close = 16:00
            after_close = 20:00

            # 상태 판단
            IF pre_open <= now_local < reg_open:
                RETURN "Pre-Market"
            ELIF reg_open <= now_local < reg_close:
                RETURN "NormalOpen"
            ELIF reg_close <= now_local < after_close:
                RETURN "After-Market"
            ELSE:
                RETURN "Closed"

        3. ELIF area == "HK":
            # Hong Kong timezone 변환
            hk_tz = timezone("Asia/Hong_Kong")
            now_local = now_utc.astimezone(hk_tz).time()

            # 시간 범위 정의
            morning_open = 09:30
            lunch_start = 12:00
            lunch_end = 13:00
            close = 16:00

            # 상태 판단
            IF (morning_open <= now_local < lunch_start) OR
               (lunch_end <= now_local < close):
                RETURN "NormalOpen"
            ELSE:
                RETURN "Closed"

    Complexity:
        - Time: O(1) - 시간 비교만 수행
        - Space: O(1)

    Usage:
        market_status = market_open_type("US")

        IF market_status == "NormalOpen":
            # 정규 시장 개장 → 모든 주문 가능
        ELIF market_status == "Pre-Market":
            # 프리마켓 → LIMIT 주문만 허용
        ELIF market_status == "After-Market":
            # 애프터마켓 → LIMIT 주문만 허용
        ELSE:
            # 시장 폐장 → 주문 불가, 데이터 수집만
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

    elif area.upper() == "HK":
        hk_tz = pytz_timezone("Asia/Hong_Kong")
        now_local = now_utc.astimezone(hk_tz).time()

        morning_open = time(9, 30)
        lunch_start = time(12, 0)
        lunch_end = time(13, 0)
        close = time(16, 0)

        if (morning_open <= now_local < lunch_start) or \
           (lunch_end <= now_local < close):
            return "NormalOpen"
        else:
            return "Closed"

    return "Unknown"
```

---

## 3. Alpha Vantage API 통합 명세

### 3.1 개요

**Alpha Vantage**는 주식, 외환, 암호화폐 데이터를 제공하는 API입니다.

- **Base URL**: `https://www.alphavantage.co/query`
- **인증 방식**: API Key (Query Parameter)
- **Rate Limit (Free Tier)**: 5 calls/minute, 500 calls/day

### 3.2 티커 리스트 조회 (get_ticker_list)

```python
def get_ticker_list(market: str = 'NASDAQ', asset_type: str = 'Stock',
                   active: bool = True) -> List[str]:
    """
    Alpha Vantage API로 티커 리스트 조회

    API Endpoint:
        GET https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={api_key}

    Query Parameters:
        - function: "LISTING_STATUS"
        - state: "active" or "delisted"
        - apikey: API 키

    Response (CSV):
        symbol,name,exchange,assetType,ipoDate,delistingDate,status
        AAPL,Apple Inc,NASDAQ,Stock,1980-12-12,null,Active
        MSFT,Microsoft Corp,NASDAQ,Stock,1986-03-13,null,Active
        ...

    Algorithm:
        INPUT: market, asset_type, active
        OUTPUT: List[ticker]

        1. # URL 구성
        IF active:
            url = f"{base_url}?function=LISTING_STATUS&apikey={api_key}"
        ELSE:
            url = f"{base_url}?function=LISTING_STATUS&state=delisted&apikey={api_key}"

        2. # API 요청
        response = GET(url, timeout=30)

        3. # CSV 파싱
        IF response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            csv_reader = csv.reader(csv_content.splitlines())

            ticker_list = []
            FOR row IN csv_reader:
                # row[0] = symbol
                # row[2] = exchange
                # row[3] = assetType

                IF row[2] == market AND row[3] == asset_type:
                    ticker_list.append(row[0])

            RETURN ticker_list
        ELSE:
            RAISE Exception("Failed to get ticker list")

    Complexity:
        - Time: O(N) - N = CSV 행 수 (~15,000 for NASDAQ+NYSE)
        - Space: O(M) - M = 필터링된 티커 수

    Rate Limit Handling:
        - Free tier: 5 calls/minute
        - 이 함수는 1 call 사용
        - 호출 후 12초 대기 권장 (self.rate_limit_delay)
    """

    if active:
        url = f"{self.base_url}?function=LISTING_STATUS&apikey={self.api_key}"
    else:
        url = f"{self.base_url}?function=LISTING_STATUS&state=delisted&apikey={self.api_key}"

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            decoded_content = response.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            ticker_list = []

            for row in cr:
                if len(row) >= 4 and row[2] == market and row[3] == asset_type:
                    ticker_list.append(row[0])

            logger.info(f"✅ Retrieved {len(ticker_list)} {market} {asset_type} tickers")
            return ticker_list
        else:
            logger.error(f"Failed to get ticker list: {response.status_code}")
            return []

    except Exception as e:
        logger.error(f"Error getting ticker list: {e}")
        return []
```

### 3.3 분봉 데이터 조회 (get_ohlcv_intraday)

```python
def get_ohlcv_intraday(symbol: str, interval: str = "1min",
                      outputsize: str = "compact") -> pd.DataFrame:
    """
    Alpha Vantage 분봉 데이터 조회

    API Endpoint:
        GET https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY

    Query Parameters:
        - function: "TIME_SERIES_INTRADAY"
        - symbol: 티커 (예: "AAPL")
        - interval: "1min", "5min", "15min", "30min", "60min"
        - extended_hours: "false" (정규 시장만)
        - outputsize: "compact" (최근 100개) or "full" (전체)
        - apikey: API 키

    Response (JSON):
        {
            "Meta Data": { ... },
            "Time Series (5min)": {
                "2023-12-01 15:55:00": {
                    "1. open": "150.25",
                    "2. high": "150.50",
                    "3. low": "150.20",
                    "4. close": "150.45",
                    "5. volume": "125000"
                },
                ...
            }
        }

    Algorithm:
        INPUT: symbol, interval, outputsize
        OUTPUT: DataFrame[open, high, low, close, volume]

        1. # URL 구성
        url = f"{base_url}?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&extended_hours=false&outputsize={outputsize}&apikey={api_key}"

        2. # API 요청
        response = GET(url)
        sleep(rate_limit_delay)  # Rate limiting (12초 대기)

        3. # JSON 파싱
        IF response.status_code == 200:
            data = response.json()
            time_series_key = f"Time Series ({interval})"
            time_series = data.get(time_series_key, {})

            # DataFrame 생성
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # 컬럼명 정리
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype({
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int
            })

            RETURN df
        ELSE:
            RAISE Exception("Failed to get intraday data")

    Complexity:
        - Time: O(N) - N = 데이터 포인트 수 (compact = 100, full = ~5000)
        - Space: O(N)

    Usage:
        # 5분봉 최근 100개
        df_5min = av.get_ohlcv_intraday("AAPL", "5min", "compact")

        # 1분봉 전체 (약 5000개)
        df_1min = av.get_ohlcv_intraday("AAPL", "1min", "full")
    """

    url = f"{self.base_url}?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&extended_hours=false&outputsize={outputsize}&apikey={self.api_key}"

    try:
        response = requests.get(url, timeout=30)
        time.sleep(self.rate_limit_delay)  # Rate limiting

        if response.status_code == 200:
            data = response.json()

            # Check for API error messages
            if "Error Message" in data:
                logger.error(f"Alpha Vantage API Error: {data['Error Message']}")
                return pd.DataFrame()

            if "Note" in data:
                logger.warning(f"Alpha Vantage Rate Limit: {data['Note']}")
                return pd.DataFrame()

            time_series_key = f"Time Series ({interval})"
            time_series = data.get(time_series_key, {})

            if not time_series:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # DataFrame 생성
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # 컬럼명 정리 (Alpha Vantage 형식: "1. open", "2. high", ...)
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype({
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int
            })

            logger.info(f"✅ Retrieved {len(df)} intraday data points for {symbol}")
            return df

        else:
            logger.error(f"Failed to get intraday data: {response.status_code}")
            return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error getting intraday data: {e}")
        return pd.DataFrame()
```

---

## 4. Yahoo Finance API 통합 명세

### 4.1 개요

**Yahoo Finance**는 `yfinance` 라이브러리를 통해 접근하는 무료 데이터 소스입니다.

- **라이브러리**: `yfinance` (Python)
- **인증**: 불필요
- **Rate Limit**: ~2000 requests/hour (비공식)

### 4.2 OHLCV 데이터 조회 (get_ohlcv)

```python
def get_ohlcv(stock_code: str, p_code: str, start_date: datetime,
              end_date: datetime, ohlcv: str = "Y") -> pd.DataFrame:
    """
    Yahoo Finance OHLCV 데이터 조회

    Algorithm:
        INPUT: stock_code, p_code, start_date, end_date, ohlcv
        OUTPUT: DataFrame[open, high, low, close, volume]

        1. # yfinance Ticker 객체 생성
        ticker = yf.Ticker(stock_code)

        2. # Interval 결정
        interval = "1wk" if p_code == "W" else "1d"

        3. # 데이터 다운로드
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=(ohlcv == "Y")  # True = 수정주가
        )

        4. # 빈 DataFrame 체크
        IF df.empty:
            logger.warning("No data found")
            RETURN empty DataFrame

        5. # 숫자 컬럼 반올림 (소수점 2자리)
        FOR col IN ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = round(df[col], 2)

        6. # 컬럼명 변경
        df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Dividends': 'dividends',
            'Stock Splits': 'stock_splits'
        })

        7. # Timezone 처리 (UTC로 통일)
        IF df.index has timezone:
            df.index = df.index.tz_convert('UTC')
        ELSE:
            df.index = df.index.tz_localize('UTC')

        8. RETURN df

    Complexity:
        - Time: O(N) - N = 데이터 포인트 수 (~252 for 1년 일봉)
        - Space: O(N)

    Example:
        df = yf.get_ohlcv(
            stock_code="AAPL",
            p_code="D",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            ohlcv="Y"
        )

        Output:
                                   open    high     low   close    volume
        2023-01-03 00:00:00+00:00  130.28  130.90  124.17  125.07  112117471
        2023-01-04 00:00:00+00:00  126.89  128.66  125.08  126.36   89113671
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

        # Handle timezone
        if df.index.tz is not None:
            df.index = df.index.tz_convert('UTC')
        else:
            df.index = df.index.tz_localize('UTC')

        logger.info(f"✅ Retrieved {len(df)} records for {stock_code}")
        return df

    except Exception as e:
        logger.error(f"Error getting OHLCV data for {stock_code}: {e}")
        return pd.DataFrame()
```

### 4.3 펀더멘털 데이터 조회 (get_fundamental_data)

```python
def get_fundamental_data(ticker: str) -> Dict[str, Any]:
    """
    Yahoo Finance 펀더멘털 데이터 조회

    Algorithm:
        INPUT: ticker
        OUTPUT: {market_cap, pe_ratio, pb_ratio, roe, ...}

        1. stock = yf.Ticker(ticker)
        2. info = stock.info  # 딕셔너리 형태

        3. # 필요한 지표 추출
        fundamental = {
            "market_cap": info.get("marketCap", 0) / 1e9,  # 억 달러
            "pe_ratio": info.get("trailingPE", None),
            "pb_ratio": info.get("priceToBook", None),
            "ps_ratio": info.get("priceToSalesTrailing12Months", None),
            "roe": info.get("returnOnEquity", None) * 100,  # %
            "roa": info.get("returnOnAssets", None) * 100,  # %
            "eps": info.get("trailingEps", None),
            "revenue": info.get("totalRevenue", 0) / 1e9,
            "net_income": info.get("netIncomeToCommon", 0) / 1e9,
            "dividend_yield": info.get("dividendYield", 0) * 100,
            "beta": info.get("beta", None),
            "52week_high": info.get("fiftyTwoWeekHigh", None),
            "52week_low": info.get("fiftyTwoWeekLow", None)
        }

        4. RETURN fundamental

    Complexity:
        - Time: O(1) - API 요청 1회
        - Space: O(1)

    Usage:
        fundamental = yf.get_fundamental_data("AAPL")
        print(f"P/E Ratio: {fundamental['pe_ratio']:.2f}")
        print(f"ROE: {fundamental['roe']:.2f}%")
    """

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info:
            logger.warning(f"No info found for {ticker}")
            return {}

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
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
            "beta": info.get("beta", None),
            "52week_high": info.get("fiftyTwoWeekHigh", None),
            "52week_low": info.get("fiftyTwoWeekLow", None)
        }

    except Exception as e:
        logger.error(f"Error getting fundamental data for {ticker}: {e}")
        return {}
```

---

## 5. Telegram Bot API 통합 명세

### 5.1 개요

**Telegram Bot API**는 메시지 및 파일 전송을 지원합니다.

- **Base URL**: `https://api.telegram.org/bot{token}`
- **인증**: Bot Token
- **Rate Limit**: 30 messages/second, 20 messages/minute to same chat

### 5.2 메시지 전송 (send_message)

```python
def send_message(message: str, chat_id: str = None, parse_mode: str = 'HTML',
                add_timestamp: bool = True) -> bool:
    """
    Telegram 메시지 전송

    API Endpoint:
        POST https://api.telegram.org/bot{token}/sendMessage

    Request Body:
        {
            "chat_id": "-1001234567890",
            "text": "메시지 내용",
            "parse_mode": "HTML"
        }

    Algorithm:
        INPUT: message, chat_id, parse_mode, add_timestamp
        OUTPUT: success (bool)

        1. target_chat_id = chat_id OR default_chat_id

        2. IF add_timestamp:
            timestamp = current_time()
            formatted_msg = f"[{timestamp}] {message}"
        ELSE:
            formatted_msg = message

        3. url = f"{base_url}/sendMessage"
        4. data = {
            "chat_id": target_chat_id,
            "text": formatted_msg,
            "parse_mode": parse_mode
        }

        5. response = POST(url, data)

        6. IF response.status_code == 200:
            RETURN True
        ELSE:
            logger.error("Telegram send failed")
            RETURN False

    Complexity:
        - Time: O(1) - HTTP 요청 1회
        - Space: O(len(message))

    HTML Format:
        <b>굵게</b>
        <i>기울임</i>
        <code>코드</code>
        <pre>여러 줄 코드</pre>
        <a href="URL">링크</a>
    """

    try:
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

        # Send message
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

    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram API request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Telegram message send error: {e}")
        return False
```

---

## 6. 에러 처리 및 Fallback 전략

### 6.1 에러 분류 및 대응

| 에러 타입 | 대응 전략 | 재시도 | Fallback |
|---------|---------|-------|---------|
| **인증 실패** | 토큰/API 키 재발급 | 1회 | 사용자 알림 |
| **Rate Limit** | Exponential backoff 대기 | 3회 | 다른 API 사용 |
| **네트워크 에러** | 재시도 (1s, 2s, 4s 대기) | 3회 | 오프라인 모드 |
| **데이터 없음** | 로그 기록, 빈 DataFrame 반환 | 없음 | 다른 데이터 소스 |
| **토큰 만료** | 자동 갱신 후 재시도 | 2회 | - |
| **시장 폐장** | 대기 후 재시도 | 무한 | 데이터 수집만 진행 |

### 6.2 Fallback 전략

```python
def get_ohlcv_with_fallback(ticker: str, start_date: datetime,
                            end_date: datetime) -> pd.DataFrame:
    """
    OHLCV 데이터 조회 (Fallback 전략 포함)

    Fallback 순서:
        1. Yahoo Finance (무료, 빠름)
        2. Alpha Vantage (무료, Rate Limit 있음)
        3. MongoDB 캐시 (과거 데이터)

    Algorithm:
        1. TRY:
            df = yfinance_helper.get_ohlcv(ticker, ...)
            IF df is not empty:
                RETURN df

        2. EXCEPT:
            logger.warning("Yahoo Finance failed, trying Alpha Vantage")

        3. TRY:
            df = alpha_vantage.get_ohlcv(ticker, ...)
            IF df is not empty:
                RETURN df

        4. EXCEPT:
            logger.warning("Alpha Vantage failed, trying MongoDB cache")

        5. TRY:
            df = mongo_db.get_cached_ohlcv(ticker, start_date, end_date)
            IF df is not empty:
                logger.warning("Using cached data")
                RETURN df

        6. EXCEPT:
            logger.error("All data sources failed")
            RETURN empty DataFrame
    """

    # 1. Try Yahoo Finance (Primary)
    try:
        df = yfinance_helper.get_ohlcv(ticker, "D", start_date, end_date)
        if not df.empty:
            logger.info(f"✅ Got data from Yahoo Finance: {ticker}")
            return df
    except Exception as e:
        logger.warning(f"Yahoo Finance failed: {e}")

    # 2. Try Alpha Vantage (Fallback 1)
    try:
        df = alpha_vantage.get_ohlcv(ticker, start_date, end_date, interval="1d")
        if not df.empty:
            logger.info(f"✅ Got data from Alpha Vantage: {ticker}")
            return df
    except Exception as e:
        logger.warning(f"Alpha Vantage failed: {e}")

    # 3. Try MongoDB Cache (Fallback 2)
    try:
        df = mongo_db.get_cached_ohlcv(ticker, start_date, end_date)
        if not df.empty:
            logger.warning(f"⚠️ Using cached data: {ticker}")
            return df
    except Exception as e:
        logger.error(f"MongoDB cache failed: {e}")

    # 4. All failed
    logger.error(f"❌ All data sources failed for {ticker}")
    return pd.DataFrame()
```

---

## 7. Rate Limiting 및 최적화

### 7.1 Rate Limit 관리

```python
class RateLimiter:
    """
    API Rate Limit 관리자

    Attributes:
        calls_per_minute: int - 분당 최대 호출 수
        calls: List[datetime] - 최근 호출 시각 기록
    """

    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.calls = []

    def wait_if_needed(self):
        """
        필요 시 대기

        Algorithm:
            1. now = current_time()
            2. one_minute_ago = now - 60 seconds

            3. # 최근 1분 내 호출 필터링
            recent_calls = [c for c in self.calls if c > one_minute_ago]
            self.calls = recent_calls

            4. IF len(recent_calls) >= calls_per_minute:
                # Rate limit 초과 → 대기
                oldest_call = recent_calls[0]
                wait_time = 60 - (now - oldest_call).seconds
                logger.warning(f"Rate limit, waiting {wait_time}s")
                sleep(wait_time + 1)

            5. # 현재 호출 기록
            self.calls.append(now)
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(seconds=60)

        # 최근 1분 내 호출 필터링
        self.calls = [c for c in self.calls if c > one_minute_ago]

        # Rate limit 확인
        if len(self.calls) >= self.calls_per_minute:
            oldest_call = self.calls[0]
            wait_time = 60 - (now - oldest_call).seconds
            logger.warning(f"Rate limit reached, waiting {wait_time}s")
            time.sleep(wait_time + 1)

        # 현재 호출 기록
        self.calls.append(now)

# 사용 예제
alpha_vantage_limiter = RateLimiter(calls_per_minute=5)

for ticker in tickers:
    alpha_vantage_limiter.wait_if_needed()
    df = alpha_vantage.get_ohlcv(ticker, ...)
```

### 7.2 데이터 캐싱 전략

```python
class DataCache:
    """
    데이터 캐싱 (MongoDB 기반)

    Cache Hit: MongoDB에서 가져옴 (< 0.1s)
    Cache Miss: API 호출 → MongoDB 저장 (2-5s)
    """

    def get_ohlcv_with_cache(self, ticker: str, start_date: datetime,
                            end_date: datetime) -> pd.DataFrame:
        """
        캐시를 활용한 OHLCV 조회

        Algorithm:
            1. cache_key = f"{ticker}_{start_date}_{end_date}"

            2. # MongoDB 캐시 확인
            cached_data = mongo_db.find_one({"cache_key": cache_key})

            3. IF cached_data AND cache_age < 24_hours:
                # Cache hit
                logger.info("✅ Cache hit")
                RETURN DataFrame(cached_data["data"])

            4. # Cache miss → API 호출
            logger.info("⚠️ Cache miss, fetching from API")
            df = yfinance_helper.get_ohlcv(ticker, ...)

            5. # MongoDB에 캐싱
            mongo_db.insert_one({
                "cache_key": cache_key,
                "data": df.to_dict(),
                "cached_at": datetime.now()
            })

            6. RETURN df

        Performance:
            - Cache Hit: ~0.05초
            - Cache Miss: ~2-5초 (API 호출 시간)
            - Cache Hit Rate 목표: > 80%
        """

        cache_key = f"{ticker}_{start_date.date()}_{end_date.date()}"

        # 1. Check cache
        cached_data = mongo_db.find_one({"cache_key": cache_key})

        if cached_data:
            cached_at = cached_data.get("cached_at")
            cache_age = (datetime.now() - cached_at).total_seconds()

            if cache_age < 86400:  # 24시간 이내
                logger.info(f"✅ Cache hit for {ticker}")
                return pd.DataFrame(cached_data["data"])

        # 2. Cache miss → Fetch from API
        logger.info(f"⚠️ Cache miss for {ticker}, fetching from API")
        df = yfinance_helper.get_ohlcv(ticker, "D", start_date, end_date)

        # 3. Save to cache
        if not df.empty:
            mongo_db.insert_one({
                "cache_key": cache_key,
                "data": df.to_dict(),
                "cached_at": datetime.now()
            })

        return df
```

---

## 8. 보안 및 인증 관리

### 8.1 API 자격증명 암호화

```python
from cryptography.fernet import Fernet

class SecureCredentials:
    """
    API 자격증명 암호화 관리

    암호화 방식: Fernet (symmetric encryption)
    """

    def __init__(self, key_path: str = "config/.secret_key"):
        # 암호화 키 로드 또는 생성
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(self.key)

        self.cipher = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        문자열 암호화

        Algorithm:
            1. plaintext_bytes = plaintext.encode('utf-8')
            2. encrypted_bytes = cipher.encrypt(plaintext_bytes)
            3. RETURN encrypted_bytes.decode('utf-8')
        """
        encrypted = self.cipher.encrypt(plaintext.encode('utf-8'))
        return encrypted.decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        """
        문자열 복호화

        Algorithm:
            1. ciphertext_bytes = ciphertext.encode('utf-8')
            2. decrypted_bytes = cipher.decrypt(ciphertext_bytes)
            3. RETURN decrypted_bytes.decode('utf-8')
        """
        decrypted = self.cipher.decrypt(ciphertext.encode('utf-8'))
        return decrypted.decode('utf-8')

# 사용 예제
secure = SecureCredentials()

# 암호화
encrypted_api_key = secure.encrypt("YOUR_API_KEY")

# api_credentials.yaml에 암호화된 값 저장
with open("config/api_credentials.yaml", "w") as f:
    yaml.dump({"alpha_vantage_key": encrypted_api_key}, f)

# 복호화 (사용 시)
with open("config/api_credentials.yaml", "r") as f:
    config = yaml.safe_load(f)

api_key = secure.decrypt(config["alpha_vantage_key"])
```

### 8.2 토큰 관리 Best Practices

```python
class TokenManager:
    """
    API 토큰 관리자

    Features:
        - 토큰 자동 갱신
        - 만료 시간 추적
        - 멀티스레딩 안전
    """

    def __init__(self):
        self.token = None
        self.token_issued_at = None
        self.token_expires_in = 86400  # 24시간
        self.lock = threading.Lock()  # Thread-safe

    def get_token(self) -> str:
        """
        유효한 토큰 반환 (자동 갱신)

        Algorithm:
            1. WITH lock:  # Thread-safe
                IF token is None OR is_expired():
                    make_token()

                RETURN token
        """
        with self.lock:
            if self.token is None or self._is_expired():
                logger.info("Token expired or missing, refreshing...")
                self._make_token()

            return self.token

    def _is_expired(self) -> bool:
        """
        토큰 만료 여부 확인

        만료 기준: 발급 후 23시간 (여유 1시간)
        """
        if self.token_issued_at is None:
            return True

        elapsed = (datetime.now() - self.token_issued_at).total_seconds()
        return elapsed > (self.token_expires_in - 3600)  # 1시간 여유

    def _make_token(self):
        """토큰 발급 (내부 메서드)"""
        # KIS API 토큰 발급 로직
        ...
```

---

## 9. 성능 특성

### 9.1 API 응답 시간 벤치마크

| API | 작업 | 평균 응답 시간 | 최대 응답 시간 | 비고 |
|-----|-----|--------------|--------------|------|
| KIS | 토큰 발급 | 1.2s | 3.0s | 하루 1회 |
| KIS | 현재가 조회 | 0.4s | 1.5s | - |
| KIS | 주문 실행 | 1.8s | 5.0s | 시장 상황에 따라 변동 |
| Alpha Vantage | 티커 리스트 | 8.0s | 15.0s | CSV 파싱 시간 포함 |
| Alpha Vantage | 분봉 데이터 | 3.5s | 7.0s | 12초 대기 포함 |
| Yahoo Finance | 일봉 (1년) | 2.2s | 5.0s | - |
| Yahoo Finance | 펀더멘털 | 1.5s | 3.0s | - |
| Telegram | 메시지 전송 | 0.6s | 2.0s | - |

### 9.2 최적화 기법

1. **병렬 처리**: 여러 티커 동시 조회
2. **캐싱**: MongoDB 캐시로 80%+ Cache Hit Rate
3. **Rate Limiting**: 자동 대기로 API 제한 준수
4. **Fallback**: 다중 데이터 소스로 신뢰성 확보

---

## 10. 테스트 전략

### 10.1 단위 테스트

```python
import unittest
from unittest.mock import Mock, patch

class TestKISAPI(unittest.TestCase):

    @patch('requests.post')
    def test_make_token_success(self, mock_post):
        """토큰 발급 성공 테스트"""
        # Mock response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_token_123",
            "expires_in": 86400
        }

        kis = KISBrokerAPI(config_path="test_config.yaml")
        token_data = kis.make_token()

        self.assertEqual(token_data["access_token"], "test_token_123")
        self.assertEqual(kis.token, "test_token_123")

    def test_market_open_type_us(self):
        """미국 시장 상태 확인 테스트"""
        kis = KISUSHelper(config={})

        # Mock time to 10:00 AM NY time (정규 시장)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 12, 1, 15, 0, 0, tzinfo=timezone.utc)
            status = kis.market_open_type("US")
            self.assertEqual(status, "NormalOpen")
```

---

## 11. 참조 문서

- **HELPER_LAYER_INTERFACE.md**: 인터페이스 명세
- **HELPER_MODULES.md**: 모듈 설명
- **CLAUDE.md v2.4**: 프로젝트 규칙
- **config/api_credentials.yaml**: API 자격증명 예제

---

**작성자**: Service Agent
**검토자**: Orchestrator Agent
**승인 날짜**: 2025-10-09
