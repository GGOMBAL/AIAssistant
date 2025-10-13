# Database Layer Interface Specification

**버전**: 1.0
**작성일**: 2025-10-09
**Layer**: Database Layer (MongoDB Data Management)
**담당 Agent**: Data Agent (Database Agent)
**참조**: CLAUDE.md v2.4, docs/AGENT_INTERFACES.md

---

## 1. 개요

Database Layer는 MongoDB 데이터베이스를 관리하고 CRUD 연산을 제공하는 레이어입니다.

### 1.1 주요 역할
- 🗄️ **MongoDB 연결 관리**: Connection pooling 및 인증
- 📊 **OHLCV 데이터 저장/조회**: 일봉, 주봉, 분봉 데이터
- 📈 **상대강도 데이터 관리**: RS_4W, RS_12W 데이터
- 💰 **펀더멘털 데이터 관리**: EPS, Revenue, ROE 등
- 📅 **실적 데이터 관리**: Earnings 발표일 및 실적
- 🔍 **데이터베이스 이름 계산**: Market, Area, Type별 DB 네이밍

### 1.2 파일 구성
```
project/database/
├── mongodb_operations.py         (404 lines) - MongoDB CRUD 연산
├── database_name_calculator.py   (325 lines) - DB 이름 계산
├── database_manager.py            (354 lines) - 통합 DB 관리
├── historical_data_manager.py     (421 lines) - 과거 데이터 관리
└── us_market_manager.py           (400 lines) - 미국 시장 데이터 관리
```

---

## 2. 입력 인터페이스

### 2.1 MongoDB 연결 설정

#### 2.1.1 설정 파일 (myStockInfo.yaml)

```yaml
# MongoDB 연결 정보
MONGODB_LOCAL: "localhost"
MONGODB_PORT: 27017
MONGODB_ID: "admin"
MONGODB_PW: "your_password"

# 외부 MongoDB (선택)
MONGODB_CLOUD: "mongodb+srv://cluster0.xxxxx.mongodb.net"
```

#### 2.1.2 연결 초기화

```python
# Input
{
    "db_address": str  # "MONGODB_LOCAL" or "MONGODB_CLOUD"
}

# 내부 처리
connection = pymongo.MongoClient(
    host=stock_info[db_address],
    port=stock_info["MONGODB_PORT"],
    username=stock_info["MONGODB_ID"],
    password=stock_info["MONGODB_PW"]
)
```

### 2.2 데이터베이스 이름 계산

#### 2.2.1 calculate_database_name

```python
# Input
{
    "market": str,    # "NAS", "NYS", "AMX", "KR", "HNX", "HSX"
    "area": str,      # "US", "KR", "VT", "HK"
    "p_code": str,    # "M", "D", "AD", "W", "RS", "F", "E", "O"
    "type": str       # "Stock" or "ETF"
}

# Output
database_name: str

# Examples
calculate_database_name("NAS", "US", "D", "Stock") → "NasDataBase_D"
calculate_database_name("NYS", "US", "W", "Stock") → "NysDataBase_W"
calculate_database_name("NAS", "US", "RS", "Stock") → "NasDataBase_RS"
calculate_database_name("KR", "KR", "D", "Stock") → "KrDataBase_D_ohlcv"
```

**p_code 설명**:
- `M`: 분봉 (Minute)
- `D`: 일봉 (Daily) - 원본
- `AD`: 수정 일봉 (Adjusted Daily)
- `W`: 주봉 (Weekly)
- `RS`: 상대강도 (Relative Strength)
- `F`: 펀더멘털 (Fundamental)
- `E`: 실적 (Earnings)
- `O`: 옵션 (Options)

### 2.3 CRUD 연산 입력

#### 2.3.1 데이터 삽입 (Create)

```python
# Input
{
    "db_name": str,           # "NasDataBase_D"
    "collection_name": str,   # "AAPL"
    "data": Dict or List[Dict]
}

# Data Format (단일 문서)
{
    "Date": datetime,         # 날짜 (ISO 8601)
    "open": float,            # 시가
    "high": float,            # 고가
    "low": float,             # 저가
    "close": float,           # 종가
    "volume": int,            # 거래량
    "dividends": float,       # 배당금 (선택)
    "stock_splits": float     # 주식 분할 (선택)
}

# Output
{
    "success": bool,
    "inserted_count": int,    # 삽입된 문서 수
    "message": str
}
```

#### 2.3.2 데이터 조회 (Read)

```python
# Input
{
    "db_name": str,           # "NasDataBase_D"
    "collection_name": str,   # "AAPL"
    "query": Dict,            # MongoDB query
    "projection": Dict,       # 반환할 필드 (선택)
    "sort": List[Tuple],      # 정렬 (선택)
    "limit": int              # 개수 제한 (선택)
}

# Query Examples
# 1. 날짜 범위 조회
{
    "Date": {
        "$gte": datetime(2023, 1, 1),
        "$lte": datetime(2023, 12, 31)
    }
}

# 2. 조건 조회
{
    "close": {"$gt": 150.0},
    "volume": {"$gt": 50000000}
}

# 3. 전체 조회
{}

# Output
pd.DataFrame or List[Dict]
```

#### 2.3.3 데이터 업데이트 (Update)

```python
# Input
{
    "db_name": str,
    "collection_name": str,
    "query": Dict,            # 업데이트할 문서 선택
    "update": Dict,           # 업데이트 내용
    "upsert": bool            # True = 없으면 삽입
}

# Update Examples
# 1. 특정 필드 업데이트
{
    "query": {"Date": datetime(2023, 12, 1)},
    "update": {"$set": {"close": 155.5}}
}

# 2. 여러 필드 업데이트
{
    "query": {"Date": datetime(2023, 12, 1)},
    "update": {
        "$set": {
            "close": 155.5,
            "volume": 60000000
        }
    }
}

# Output
{
    "success": bool,
    "matched_count": int,     # 매치된 문서 수
    "modified_count": int,    # 수정된 문서 수
    "message": str
}
```

#### 2.3.4 데이터 삭제 (Delete)

```python
# Input
{
    "db_name": str,
    "collection_name": str,
    "query": Dict             # 삭제할 문서 선택
}

# Output
{
    "success": bool,
    "deleted_count": int,     # 삭제된 문서 수
    "message": str
}
```

### 2.4 컬렉션 관리

#### 2.4.1 컬렉션 목록 조회

```python
# Input
{
    "db_name": str            # "NasDataBase_D"
}

# Output
{
    "collections": List[str], # ["AAPL", "MSFT", "GOOGL", ...]
    "count": int              # 컬렉션 수
}
```

#### 2.4.2 컬렉션 삭제

```python
# Input
{
    "db_name": str,
    "collection_name": str
}

# Output
{
    "success": bool,
    "message": str
}
```

---

## 3. 출력 인터페이스

### 3.1 OHLCV 데이터 출력

#### 3.1.1 일봉 데이터 (Daily)

```python
# pandas DataFrame
{
    "index": pd.DatetimeIndex,   # UTC timezone
    "columns": [
        "Date": datetime,        # 날짜
        "open": float,           # 시가
        "high": float,           # 고가
        "low": float,            # 저가
        "close": float,          # 종가
        "volume": int,           # 거래량
        "dividends": float,      # 배당금
        "stock_splits": float    # 주식 분할
    ]
}
```

**예시**:
```
                          Date    open    high     low   close      volume  dividends  stock_splits
2023-01-03 00:00:00+00:00  130.28  130.90  124.17  125.07  112117471        0.0           0.0
2023-01-04 00:00:00+00:00  126.89  128.66  125.08  126.36   89113671        0.0           0.0
2023-01-05 00:00:00+00:00  127.13  127.77  124.76  125.02   80962746        0.0           0.0
```

#### 3.1.2 주봉 데이터 (Weekly)

```python
# pandas DataFrame
{
    "index": pd.DatetimeIndex,   # 주간 금요일
    "columns": [
        "Date": datetime,
        "open": float,           # 주간 시가
        "high": float,           # 주간 고가
        "low": float,            # 주간 저가
        "close": float,          # 주간 종가
        "volume": int            # 주간 거래량
    ]
}
```

### 3.2 상대강도 데이터 출력 (RS)

```python
# pandas DataFrame
{
    "index": pd.DatetimeIndex,
    "columns": [
        "Date": datetime,
        "RS_4W": float,          # 4주 상대강도 (0-100)
        "RS_12W": float,         # 12주 상대강도 (0-100)
        "Sector": str,           # 섹터 (예: "Technology")
        "Industry": str,         # 산업 (예: "Consumer Electronics")
        "Sector_RS_4W": float,   # 섹터 4주 상대강도
        "Sector_RS_12W": float   # 섹터 12주 상대강도
    ]
}
```

**예시**:
```
                          Date  RS_4W  RS_12W      Sector               Industry  Sector_RS_4W
2023-12-01 00:00:00+00:00    92.5    88.3  Technology  Consumer Electronics          85.2
2023-12-08 00:00:00+00:00    93.1    89.0  Technology  Consumer Electronics          86.5
```

### 3.3 펀더멘털 데이터 출력 (F)

```python
# pandas DataFrame
{
    "index": pd.DatetimeIndex,
    "columns": [
        "Date": datetime,
        "EPS": float,            # 주당순이익
        "EPS_YOY": float,        # EPS 전년 대비 성장률 (%)
        "REV_YOY": float,        # 매출 전년 대비 성장률 (%)
        "PBR": float,            # Price to Book Ratio
        "PSR": float,            # Price to Sales Ratio
        "ROE": float,            # Return on Equity (%)
        "ROA": float,            # Return on Assets (%)
        "EBITDA": float,         # EBITDA (억 달러)
        "Market_Cap": float      # 시가총액 (억 달러)
    ]
}
```

### 3.4 실적 데이터 출력 (E)

```python
# pandas DataFrame
{
    "index": pd.DatetimeIndex,
    "columns": [
        "EarningDate": datetime, # 실적 발표일
        "eps": float,            # 발표 EPS
        "eps_yoy": float,        # EPS 성장률 (%)
        "revenue": float,        # 매출 (억 달러)
        "rev_yoy": float,        # 매출 성장률 (%)
        "surprise": float,       # 예상 대비 서프라이즈 (%)
        "estimate_eps": float    # 예상 EPS
    ]
}
```

**예시**:
```
  EarningDate    eps  eps_yoy  revenue  rev_yoy  surprise  estimate_eps
2023-10-26      1.46     10.6    895.2      8.2       2.5          1.42
2023-07-27      1.40      8.5    872.5      7.8       3.1          1.36
```

---

## 4. 데이터베이스 스키마

### 4.1 데이터베이스 네이밍 규칙

```
{Market}{Type}DataBase_{PCode}

Examples:
- NasDataBase_D: NASDAQ 일봉
- NysDataBase_W: NYSE 주봉
- NasDataBase_RS: NASDAQ 상대강도
- KrDataBase_D_ohlcv: 한국 일봉
- NasEtfDataBase_D: NASDAQ ETF 일봉
```

### 4.2 컬렉션 네이밍 규칙

```
# 주식: 티커 심볼 그대로
AAPL, MSFT, GOOGL

# 한국 주식: "A" 접두어
A005930 (삼성전자)

# ETF: 티커 심볼 그대로
SPY, QQQ, IWM
```

### 4.3 인덱스

```python
# 모든 컬렉션 공통
{
    "Date": 1  # 날짜 오름차순 인덱스 (필수)
}

# 복합 인덱스 (성능 최적화)
{
    "Date": 1,
    "close": 1
}
```

---

## 5. 주요 함수 명세

### 5.1 MongoDBOperations 클래스

```python
class MongoDBOperations:
    """MongoDB CRUD 연산 클래스"""

    def __init__(self, db_address: str = "MONGODB_LOCAL"):
        """
        Args:
            db_address: MongoDB 주소 식별자
        """
        pass

    def insert_documents(self, db_name: str, collection_name: str,
                        documents: Union[Dict, List[Dict]]) -> Dict[str, Any]:
        """
        문서 삽입

        Args:
            db_name: 데이터베이스 이름
            collection_name: 컬렉션 이름
            documents: 삽입할 문서 (단일 or 리스트)

        Returns:
            {
                "success": bool,
                "inserted_count": int
            }
        """
        pass

    def read_documents(self, db_name: str, collection_name: str,
                      query: Dict = None, projection: Dict = None,
                      sort: List[Tuple] = None, limit: int = 0) -> pd.DataFrame:
        """
        문서 조회

        Args:
            db_name: 데이터베이스 이름
            collection_name: 컬렉션 이름
            query: MongoDB 쿼리
            projection: 반환할 필드
            sort: 정렬 [(field, direction), ...]
            limit: 개수 제한

        Returns:
            pd.DataFrame
        """
        pass

    def update_documents(self, db_name: str, collection_name: str,
                        query: Dict, update: Dict,
                        upsert: bool = False) -> Dict[str, Any]:
        """
        문서 업데이트

        Args:
            db_name: 데이터베이스 이름
            collection_name: 컬렉션 이름
            query: 업데이트할 문서 선택
            update: 업데이트 내용
            upsert: True = 없으면 삽입

        Returns:
            {
                "success": bool,
                "matched_count": int,
                "modified_count": int
            }
        """
        pass

    def delete_documents(self, db_name: str, collection_name: str,
                        query: Dict) -> Dict[str, Any]:
        """
        문서 삭제

        Args:
            db_name: 데이터베이스 이름
            collection_name: 컬렉션 이름
            query: 삭제할 문서 선택

        Returns:
            {
                "success": bool,
                "deleted_count": int
            }
        """
        pass

    def list_collections(self, db_name: str) -> List[str]:
        """
        컬렉션 목록 조회

        Args:
            db_name: 데이터베이스 이름

        Returns:
            List[str]: 컬렉션 이름 리스트
        """
        pass

    def drop_collection(self, db_name: str, collection_name: str) -> bool:
        """
        컬렉션 삭제

        Args:
            db_name: 데이터베이스 이름
            collection_name: 컬렉션 이름

        Returns:
            bool: 성공 여부
        """
        pass
```

### 5.2 database_name_calculator 함수

```python
def calculate_database_name(market: str, area: str, p_code: str,
                           type: str = 'Stock') -> str:
    """
    데이터베이스 이름 계산

    Args:
        market: 시장 ("NAS", "NYS", "AMX", "KR", "HNX", "HSX")
        area: 지역 ("US", "KR", "VT", "HK")
        p_code: 데이터 타입 ("M", "D", "AD", "W", "RS", "F", "E")
        type: 증권 타입 ("Stock" or "ETF")

    Returns:
        str: 데이터베이스 이름

    Examples:
        >>> calculate_database_name("NAS", "US", "D", "Stock")
        'NasDataBase_D'

        >>> calculate_database_name("NYS", "US", "W", "Stock")
        'NysDataBase_W'

        >>> calculate_database_name("KR", "KR", "RS", "Stock")
        'KrDataBase_RS'
    """
    pass

def calculate_file_path(area: str, p_code: str, stock: str) -> str:
    """
    파일 경로 계산 (CSV 저장용)

    Args:
        area: 지역
        p_code: 데이터 타입
        stock: 종목 코드

    Returns:
        str: 파일 경로
    """
    pass
```

---

## 6. 사용 예제

### 6.1 기본 CRUD 연산

```python
from project.database.mongodb_operations import MongoDBOperations
from project.database.database_name_calculator import calculate_database_name
from datetime import datetime

# 1. MongoDB 연결
db = MongoDBOperations(db_address="MONGODB_LOCAL")

# 2. 데이터베이스 이름 계산
db_name = calculate_database_name("NAS", "US", "D", "Stock")
print(f"Database: {db_name}")  # "NasDataBase_D"

# 3. 데이터 삽입
documents = [
    {
        "Date": datetime(2023, 12, 1),
        "open": 150.0,
        "high": 152.5,
        "low": 149.0,
        "close": 151.5,
        "volume": 50000000
    },
    {
        "Date": datetime(2023, 12, 2),
        "open": 151.5,
        "high": 153.0,
        "low": 150.5,
        "close": 152.0,
        "volume": 55000000
    }
]

result = db.insert_documents(db_name, "AAPL", documents)
print(f"Inserted: {result['inserted_count']} documents")

# 4. 데이터 조회
query = {
    "Date": {
        "$gte": datetime(2023, 12, 1),
        "$lte": datetime(2023, 12, 31)
    }
}

df = db.read_documents(db_name, "AAPL", query)
print(f"Retrieved {len(df)} records")
print(df.head())

# 5. 데이터 업데이트
update_result = db.update_documents(
    db_name,
    "AAPL",
    query={"Date": datetime(2023, 12, 1)},
    update={"$set": {"close": 152.0}}
)
print(f"Updated: {update_result['modified_count']} documents")

# 6. 데이터 삭제
delete_result = db.delete_documents(
    db_name,
    "AAPL",
    query={"Date": {"$lt": datetime(2020, 1, 1)}}
)
print(f"Deleted: {delete_result['deleted_count']} documents")
```

### 6.2 Indicator Layer 연동 예제

```python
from project.database.mongodb_operations import MongoDBOperations
from project.database.database_name_calculator import calculate_database_name
from datetime import datetime, timedelta

# Indicator Layer에서 사용하는 방식
def load_data_for_indicator_layer(universe: List[str], start_date: datetime,
                                  end_date: datetime):
    """Indicator Layer용 데이터 로딩"""

    db = MongoDBOperations(db_address="MONGODB_LOCAL")

    # 일봉 데이터 로딩
    db_name_daily = calculate_database_name("NAS", "US", "AD", "Stock")

    df_D = {}
    for ticker in universe:
        query = {
            "Date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        df = db.read_documents(db_name_daily, ticker, query)

        if not df.empty:
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            df_D[ticker] = df

    # 주봉 데이터 로딩
    db_name_weekly = calculate_database_name("NAS", "US", "W", "Stock")

    df_W = {}
    for ticker in universe:
        df = db.read_documents(db_name_weekly, ticker, query)
        if not df.empty:
            df.set_index('Date', inplace=True)
            df_W[ticker] = df

    return df_D, df_W

# 사용 예제
universe = ["AAPL", "MSFT", "GOOGL"]
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)

df_D, df_W = load_data_for_indicator_layer(universe, start_date, end_date)

print(f"Loaded daily data for {len(df_D)} tickers")
print(f"Loaded weekly data for {len(df_W)} tickers")
```

---

## 7. 에러 처리

### 7.1 표준 에러 응답

```python
{
    "success": False,
    "error_code": str,        # "CONNECTION_ERROR", "QUERY_ERROR", "NOT_FOUND"
    "error_message": str,     # 상세 에러 메시지
    "timestamp": str          # ISO 8601
}
```

### 7.2 에러 코드 및 처리

| 에러 코드 | 설명 | 대응 방법 |
|----------|------|----------|
| `CONNECTION_ERROR` | MongoDB 연결 실패 | 연결 정보 확인, MongoDB 서버 상태 확인 |
| `AUTHENTICATION_ERROR` | 인증 실패 | 사용자명/비밀번호 확인 |
| `QUERY_ERROR` | 쿼리 실행 실패 | 쿼리 문법 확인 |
| `NOT_FOUND` | 데이터베이스/컬렉션 없음 | 존재 여부 확인 |
| `DUPLICATE_KEY` | 중복 키 에러 | 기존 데이터 확인 또는 업데이트 사용 |
| `TIMEOUT` | 작업 시간 초과 | 쿼리 최적화, 인덱스 추가 |

---

## 8. 성능 및 제약사항

### 8.1 성능 특성

| 작업 | 100 종목 | 500 종목 | 1000 종목 |
|-----|---------|---------|----------|
| **읽기 (1년 데이터)** | 0.3초 | 1.5초 | 3.0초 |
| **쓰기 (1년 데이터)** | 0.5초 | 2.5초 | 5.0초 |
| **인덱스 생성** | 0.1초 | 0.5초 | 1.0초 |

### 8.2 데이터 크기

| 데이터 타입 | 1년 (1 종목) | 3년 (1 종목) | 500 종목 (1년) |
|-----------|-------------|-------------|---------------|
| 일봉 (D) | ~252 docs | ~756 docs | 126,000 docs |
| 주봉 (W) | ~52 docs | ~156 docs | 26,000 docs |
| 총 크기 | ~50 KB | ~150 KB | ~25 MB |

### 8.3 제약사항

1. **컬렉션 수 제한**: MongoDB는 단일 데이터베이스당 ~24,000개 컬렉션 지원
2. **문서 크기**: 최대 16 MB (BSON 제한)
3. **인덱스 수**: 컬렉션당 최대 64개
4. **Connection Pool**: 기본 100개 연결 (설정 가능)

---

## 9. 의존성

### 9.1 Python 패키지

```
pymongo==4.5.0
pandas==2.0.3
PyYAML==6.0.1
```

### 9.2 외부 시스템

- **MongoDB**: v4.0 이상 (v5.0+ 권장)
- **설정 파일**: `myStockInfo.yaml` (프로젝트 루트)

---

## 10. 참조 문서

- **CLAUDE.md v2.4**: 프로젝트 규칙
- **docs/AGENT_INTERFACES.md**: Agent 간 통신 프로토콜
- **refer/Database/CalMongoDB.py**: 참조 구현
- **refer/Database/CalDBName.py**: DB 네이밍 참조

---

**작성자**: Data Agent (Database Agent)
**검토자**: Orchestrator Agent
**승인 날짜**: 2025-10-09
