# MongoDB 사용 규칙

**최종 업데이트**: 2025-10-21
**적용 대상**: Database Agent, Indicator Agent

---

## 1. MongoDB 서버 규칙

### 핵심 규칙:
**백테스트 및 오토트레이딩은 MONGODB_LOCAL 서버를 사용합니다**.

### MongoDB 서버 구분:

#### MONGODB_LOCAL (localhost)
- **주소**: `localhost` 또는 `127.0.0.1:27017`
- **용도**:
  - 백테스트 실행
  - 오토트레이딩 시스템
  - 개발 및 테스트
- **데이터베이스**:
  - `NasDataBase_D` (NASDAQ 일간 데이터)
  - `NasDataBase_W` (NASDAQ 주간 데이터)
  - `NasDataBase_RS` (NASDAQ 상대강도 데이터)
  - `NasDataBase_F` (NASDAQ 펀더멘털 데이터)
  - `NasDataBase_E` (NASDAQ 어닝스 데이터)
  - `NysDataBase_D` (NYSE 일간 데이터)
  - `NysDataBase_W` (NYSE 주간 데이터)
  - 기타 등등
- **특징**:
  - 빠른 응답 속도
  - 로컬 데이터 접근
  - 네트워크 지연 없음

#### MONGODB_NAS (192.168.55.14)
- **주소**: `192.168.55.14:27017`
- **용도**:
  - 데이터 백업
  - 아카이브
- **특징**:
  - 네트워크 의존
  - 백업 전용
  - 느린 응답 속도 (네트워크 지연)

#### MONGODB_MAIN (192.168.55.85)
- **주소**: `192.168.55.85:27017`
- **용도**:
  - 프로덕션 데이터베이스 (미래 확장용)
- **특징**:
  - 현재 미사용
  - 향후 프로덕션 환경으로 전환 예정

---

## 2. 코드 설정

### Database Layer 설정:

```python
# project/database/mongodb_operations.py

from project.database.mongodb_operations import MongoDBOperations

# ✅ 올바른 예 - MONGODB_LOCAL 사용
db = MongoDBOperations(db_address="MONGODB_LOCAL")

# ❌ 잘못된 예 - NAS 또는 MAIN 사용
db = MongoDBOperations(db_address="MONGODB_NAS")  # 백업용이므로 느림
db = MongoDBOperations(db_address="MONGODB_MAIN")  # 미사용
```

### Indicator Layer 설정:

```python
# project/indicator/data_frame_generator.py

from project.database.mongodb_operations import MongoDBOperations

# ✅ 올바른 예
db = MongoDBOperations(db_address="MONGODB_LOCAL")
```

### myStockInfo.yaml 설정:

```yaml
# MongoDB 서버 주소 설정
MONGODB_LOCAL: localhost
MONGODB_NAS: 192.168.55.14
MONGODB_MAIN: 192.168.55.85
MONGODB_PORT: 27017
MONGODB_ID: admin
MONGODB_PW: wlsaud07
```

---

## 3. DataFrame Date 인덱스 규칙

### 핵심 규칙:
**MongoDB에서 읽은 모든 DataFrame은 Date를 인덱스로 설정해야 합니다**

### 이유:
1. **시계열 분석**: `.shift()`, `.rolling()` 등 시계열 메서드가 Date 기준으로 동작
2. **일관성**: 모든 Layer에서 동일한 인덱스 구조 사용
3. **중복 제거**: `index.duplicated()` 메서드로 중복 날짜 감지 가능
4. **필터링**: Date 범위로 쉽게 필터링 (`df['2024-01-01':'2024-12-31']`)
5. **출력 가독성**: Menu 2 같은 출력에서 Date가 인덱스로 표시

### 구현 위치:

#### `project/database/mongodb_operations.py`의 `execute_query` 메서드:

```python
def execute_query(
    self,
    db_name: str,
    collection_name: str,
    query: dict = None,
    projection: dict = None,
    limit: int = None
) -> pd.DataFrame:
    """
    Execute MongoDB query and return DataFrame with Date as index

    IMPORTANT: Always set Date as index for time-series analysis
    """
    try:
        # ... MongoDB 쿼리 실행 ...

        # Convert to DataFrame
        data = pd.DataFrame(list(cursor))

        # ✅ IMPORTANT: Always set Date as index for time-series analysis
        # This ensures consistent time-series operations across all layers
        if not data.empty and 'Date' in data.columns:
            data = data.set_index('Date')
            # Sort index to ensure chronological order
            data = data.sort_index()

        return data

    except Exception as e:
        logger.error(f"[ERROR] Error executing query on {db_name}.{collection_name}: {e}")
        return pd.DataFrame()
```

### 예시:

```python
# MongoDB에서 데이터 읽기
df = db.execute_query(
    db_name="NasDataBase_D",
    collection_name="AAPL",
    query={"Date": {"$gte": "2024-01-01"}}
)

# Date가 자동으로 인덱스로 설정됨
print(df.index)
# DatetimeIndex(['2024-01-02', '2024-01-03', ...], dtype='datetime64[ns]', name='Date')

# 시계열 연산 가능
df['SMA20'] = df['close'].rolling(window=20).mean()
df['Dhigh_shift1'] = df['high'].shift(1)

# Date 범위 필터링 가능
df_2024 = df['2024-01-01':'2024-12-31']

# 중복 날짜 확인
duplicates = df.index.duplicated()
if duplicates.any():
    print(f"[WARNING] Found {duplicates.sum()} duplicate dates")
```

### 주의사항:

- **Date가 없는 DataFrame**: 인덱스 설정하지 않음 (기본 RangeIndex 사용)
- **빈 DataFrame**: 인덱스 설정 시도하지 않음
- **Date 컬럼이 문자열인 경우**: `pd.to_datetime()` 자동 변환

### 관련 파일:
- `project/database/mongodb_operations.py` (라인 225-234): Date 인덱스 설정
- `project/indicator/data_frame_generator.py` (라인 523, 548, 552): index.duplicated() 사용

---

## 4. MongoDB 컬렉션 명명 규칙

### 시장별 데이터베이스:
```
NasDataBase_D  → NASDAQ Daily data
NasDataBase_W  → NASDAQ Weekly data
NasDataBase_RS → NASDAQ Relative Strength data
NasDataBase_F  → NASDAQ Fundamental data
NasDataBase_E  → NASDAQ Earnings data
NasDataBase_AD → NASDAQ Adjusted Daily data

NysDataBase_D  → NYSE Daily data
NysDataBase_W  → NYSE Weekly data
NysDataBase_RS → NYSE Relative Strength data
NysDataBase_F  → NYSE Fundamental data
NysDataBase_E  → NYSE Earnings data
NysDataBase_AD → NYSE Adjusted Daily data
```

### 컬렉션 명명:
- **컬렉션 이름 = 종목 티커** (예: `AAPL`, `MSFT`, `GOOGL`)
- **대문자 사용** (소문자 변환 금지)
- **특수문자 없음** (하이픈, 점 등 제거)

---

## 5. 데이터 스키마

### Daily Data (D) 스키마:
```python
{
    "Date": "2024-01-02T00:00:00.000Z",  # ISO 8601 형식
    "ad_open": 150.25,                   # Adjusted Open
    "ad_high": 152.75,                   # Adjusted High
    "ad_low": 149.80,                    # Adjusted Low
    "ad_close": 151.50,                  # Adjusted Close
    "volume": 1000000,                   # Volume
    "dividend": 0.0,                     # Dividend
    "split": 1.0                         # Stock Split
}
```

### Weekly Data (W) 스키마:
```python
{
    "Date": "2024-01-05T00:00:00.000Z",  # 주간 마지막 날 (금요일)
    "open": 150.00,
    "high": 155.00,
    "low": 148.00,
    "close": 153.00,
    "volume": 5000000
}
```

### Relative Strength (RS) 스키마:
```python
{
    "Date": "2024-01-02T00:00:00.000Z",
    "RS_4W": 75.5,                       # 4주 상대강도
    "RS_12W": 82.3,                      # 12주 상대강도
    "Sector": "Technology",              # 섹터
    "Industry": "Software",              # 산업
    "Sector_RS_4W": 65.2,               # 섹터 상대강도 4주
    "Sector_RS_12W": 70.1,              # 섹터 상대강도 12주
    "Industry_RS_4W": 68.5,             # 산업 상대강도 4주
    "Industry_RS_12W": 72.8             # 산업 상대강도 12주
}
```

### Fundamental (F) 스키마:
```python
{
    "Date": "2024-01-02T00:00:00.000Z",
    "marketCap": 2500000000000,          # 시가총액
    "totalRevenue": 100000000000,        # 총 매출
    "netIncome": 25000000000,            # 순이익
    "totalAssets": 350000000000,         # 총 자산
    "totalShareholderEquity": 150000000000,  # 총 자기자본
    "EPS": 6.50,                         # 주당순이익
    "EPS_YOY": 1.15,                     # EPS 전년비
    "REV_YOY": 1.10,                     # 매출 전년비
    "PBR": 15.5,                         # 주가순자산비율
    "PSR": 7.2,                          # 주가매출비율
    "ROE": 0.25                          # 자기자본이익률
}
```

### Earnings (E) 스키마:
```python
{
    "Date": "2024-01-02T00:00:00.000Z",
    "EarningDate": "2024-01-25",         # 어닝스 발표일
    "eps": 1.50,                         # 주당순이익
    "eps_yoy": 0.15,                     # EPS 전년 동기 대비 증감률
    "eps_qoq": 0.05,                     # EPS 전분기 대비 증감률
    "revenue": 50000000000,              # 매출
    "rev_yoy": 0.12,                     # 매출 전년 동기 대비 증감률
    "rev_qoq": 0.03,                     # 매출 전분기 대비 증감률
    "eps_surprise": 0.10                 # EPS 서프라이즈
}
```

---

## 6. 쿼리 최적화

### 인덱스 사용:
```python
# ✅ 올바른 예 - Date 인덱스 활용
query = {
    "Date": {
        "$gte": "2024-01-01T00:00:00.000Z",
        "$lte": "2024-12-31T23:59:59.999Z"
    }
}

# ❌ 잘못된 예 - 전체 스캔
query = {}  # 모든 데이터를 가져옴
```

### Projection 사용:
```python
# ✅ 올바른 예 - 필요한 컬럼만 조회
projection = {
    "Date": 1,
    "ad_close": 1,
    "volume": 1,
    "_id": 0
}

# ❌ 잘못된 예 - 모든 컬럼 조회
projection = None  # 모든 필드를 가져옴
```

### Limit 사용:
```python
# ✅ 올바른 예 - 필요한 만큼만 조회
limit = 1000  # 최근 1000일치만

# ❌ 잘못된 예 - 전체 조회
limit = None  # 모든 데이터를 가져옴
```

---

## 7. 에러 처리

### MongoDB 연결 에러:
```python
try:
    db = MongoDBOperations(db_address="MONGODB_LOCAL")
    data = db.execute_query(
        db_name="NasDataBase_D",
        collection_name="AAPL"
    )
except ConnectionError as e:
    logger.error(f"[ERROR] MongoDB connection failed: {e}")
    data = pd.DataFrame()
except Exception as e:
    logger.error(f"[ERROR] Unexpected MongoDB error: {e}")
    data = pd.DataFrame()
```

### 빈 데이터 처리:
```python
df = db.execute_query(db_name="NasDataBase_D", collection_name="AAPL")

if df.empty:
    logger.warning(f"[WARNING] No data found for AAPL")
    return pd.DataFrame()

# 필수 컬럼 확인
required_columns = ['ad_open', 'ad_high', 'ad_low', 'ad_close']
missing_columns = set(required_columns) - set(df.columns)

if missing_columns:
    logger.error(f"[ERROR] Missing columns: {missing_columns}")
    return pd.DataFrame()
```

---

## 8. 성능 고려사항

### 대량 데이터 조회 시:
1. **Batch 처리**: 한번에 모든 종목을 조회하지 말고 100개씩 분할
2. **병렬 처리**: `ThreadPoolExecutor` 사용하여 동시 조회
3. **캐싱**: 자주 사용하는 데이터는 메모리에 캐시

### 예시:
```python
from concurrent.futures import ThreadPoolExecutor

def load_symbols_parallel(symbols: List[str], batch_size: int = 100):
    """Load symbols in parallel batches"""

    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        # 100개씩 분할하여 병렬 처리
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]

            # 병렬 실행
            futures = {
                executor.submit(load_single_symbol, symbol): symbol
                for symbol in batch
            }

            # 결과 수집
            for future in futures:
                symbol = futures[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    logger.error(f"[ERROR] Failed to load {symbol}: {e}")

    return results
```

---

## 참조 문서

- **백테스트 vs 트레이딩**: `docs/rules/BACKTEST_VS_TRADING.md`
- **Database Layer 인터페이스**: `docs/interfaces/DATABASE_LAYER_INTERFACE.md`
- **Indicator Layer 인터페이스**: `docs/interfaces/INDICATOR_LAYER_INTERFACE.md`
