# Database Layer MongoDB Schema Specification

**Layer**: Database Layer
**Version**: 2.0
**Last Updated**: 2025-10-09
**Author**: Database Agent
**Dependencies**: MongoDB 4.4+, pymongo 4.0+

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Database Naming Convention](#database-naming-convention)
3. [Collection Schemas](#collection-schemas)
4. [Data Type Specifications](#data-type-specifications)
5. [Index Specifications](#index-specifications)
6. [Data Validation Rules](#data-validation-rules)
7. [Schema Examples](#schema-examples)
8. [Performance Considerations](#performance-considerations)

---

## 1. Overview

### 1.1 Schema Philosophy

MongoDB는 Schema-less 데이터베이스이지만, 본 프로젝트에서는 **명확한 스키마 규약**을 정의하여:
- 데이터 일관성 보장
- 타입 안정성 확보
- 성능 최적화 (인덱싱)
- 에러 예방 및 디버깅 용이성 증대

### 1.2 Schema Categories

```
US Market Data (미국 주식 시장 데이터)
├── Daily Data (D) - 일간 OHLCV 데이터
├── Weekly Data (W) - 주간 OHLCV 데이터
├── Relative Strength (RS) - 상대강도 데이터
├── Fundamental (F) - 펀더멘털 데이터
└── Earnings (E) - 실적 발표 데이터

KR Market Data (한국 주식 시장 데이터)
├── Daily Data (D) - 일간 OHLCV 데이터
├── Weekly Data (W) - 주간 OHLCV 데이터
└── [Future expansion...]
```

---

## 2. Database Naming Convention

### 2.1 Standard Format

```python
# Database Name Pattern
"{Market}{Type}DataBase_{PCode}"

# Examples
"NasDataBase_D"     # NASDAQ Daily
"NysDataBase_D"     # NYSE Daily
"NasDataBase_W"     # NASDAQ Weekly
"NasDataBase_RS"    # NASDAQ Relative Strength
"NasDataBase_F"     # NASDAQ Fundamental
"NasDataBase_E"     # NASDAQ Earnings
```

### 2.2 Market Codes

| Market | Code | Description |
|--------|------|-------------|
| NASDAQ | NAS | 나스닥 시장 |
| NYSE | NYS | 뉴욕 증권거래소 |
| KOSPI | KOS | 한국 코스피 |
| KOSDAQ | KOQ | 한국 코스닥 |
| AMEX | AMX | 미국 아멕스 |

### 2.3 Period Codes (PCode)

| PCode | Description | Update Frequency |
|-------|-------------|------------------|
| D | Daily | 매일 (시장 마감 후) |
| W | Weekly | 매주 금요일 |
| M | Monthly | 매월 말일 |
| RS | Relative Strength | 매주 (금요일) |
| F | Fundamental | 분기별 (실적 발표 후) |
| E | Earnings | 분기별 (실적 발표일) |

---

## 3. Collection Schemas

### 3.1 Daily Data Schema (D)

#### Collection Name: `{TICKER}` (예: "AAPL", "TSLA")

```javascript
{
  "_id": ObjectId("..."),
  "date": ISODate("2023-09-15T00:00:00.000Z"),
  "volume": NumberLong(75234100),
  "ad_open": 175.43,          // Adjusted Open
  "ad_high": 177.82,          // Adjusted High
  "ad_low": 174.91,           // Adjusted Low
  "ad_close": 176.54,         // Adjusted Close
  "open": 175.50,             // Raw Open
  "high": 177.90,             // Raw High
  "low": 175.00,              // Raw Low
  "close": 176.60,            // Raw Close
  "split_ratio": 1.0,         // Stock Split Ratio
  "dividend": 0.0,            // Dividend Amount
  "ticker": "AAPL",
  "market": "NAS",
  "updated_at": ISODate("2023-09-16T02:30:00.000Z")
}
```

#### Field Specifications:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| _id | ObjectId | Yes | MongoDB 고유 ID | Auto-generated |
| date | ISODate | Yes | 거래일 (UTC 기준) | Unique per ticker |
| volume | NumberLong | Yes | 거래량 | >= 0 |
| ad_open | Double | Yes | 조정 시가 | > 0 |
| ad_high | Double | Yes | 조정 고가 | >= ad_low |
| ad_low | Double | Yes | 조정 저가 | > 0 |
| ad_close | Double | Yes | 조정 종가 | > 0 |
| open | Double | Yes | 원시 시가 | > 0 |
| high | Double | Yes | 원시 고가 | >= low |
| low | Double | Yes | 원시 저가 | > 0 |
| close | Double | Yes | 원시 종가 | > 0 |
| split_ratio | Double | No | 주식 분할 비율 | Default: 1.0 |
| dividend | Double | No | 배당금 | >= 0, Default: 0.0 |
| ticker | String | Yes | 종목 코드 | Length: 1-10 |
| market | String | Yes | 시장 코드 | Enum: [NAS, NYS, ...] |
| updated_at | ISODate | Yes | 데이터 업데이트 시각 | Auto-generated |

---

### 3.2 Weekly Data Schema (W)

#### Collection Name: `{TICKER}` (예: "AAPL")

```javascript
{
  "_id": ObjectId("..."),
  "date": ISODate("2023-09-15T00:00:00.000Z"),  // Friday date
  "open": 173.25,
  "high": 178.90,
  "low": 172.80,
  "close": 176.54,
  "volume": NumberLong(325678900),
  "ticker": "AAPL",
  "market": "NAS",
  "week_start": ISODate("2023-09-11T00:00:00.000Z"),  // Monday
  "week_end": ISODate("2023-09-15T00:00:00.000Z"),    // Friday
  "updated_at": ISODate("2023-09-16T02:30:00.000Z")
}
```

#### Field Specifications:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| _id | ObjectId | Yes | MongoDB 고유 ID | Auto-generated |
| date | ISODate | Yes | 주간 종료일 (금요일) | Unique per ticker |
| open | Double | Yes | 주간 시가 (월요일 시가) | > 0 |
| high | Double | Yes | 주간 최고가 | >= low |
| low | Double | Yes | 주간 최저가 | > 0 |
| close | Double | Yes | 주간 종가 (금요일 종가) | > 0 |
| volume | NumberLong | Yes | 주간 총 거래량 | >= 0 |
| ticker | String | Yes | 종목 코드 | Length: 1-10 |
| market | String | Yes | 시장 코드 | Enum: [NAS, NYS, ...] |
| week_start | ISODate | Yes | 주간 시작일 (월요일) | < week_end |
| week_end | ISODate | Yes | 주간 종료일 (금요일) | > week_start |
| updated_at | ISODate | Yes | 데이터 업데이트 시각 | Auto-generated |

---

### 3.3 Relative Strength Schema (RS)

#### Collection Name: `{TICKER}` (예: "AAPL")

```javascript
{
  "_id": ObjectId("..."),
  "date": ISODate("2023-09-15T00:00:00.000Z"),
  "ticker": "AAPL",
  "market": "NAS",
  "RS_4W": 87.5,              // 4-Week Relative Strength
  "RS_12W": 91.3,             // 12-Week Relative Strength
  "RS_24W": 89.7,             // 24-Week Relative Strength
  "Sector": "Technology",
  "Industry": "Consumer Electronics",
  "Sector_RS_4W": 78.2,       // Sector 4W RS
  "Sector_RS_12W": 82.4,      // Sector 12W RS
  "Industry_RS_4W": 85.1,     // Industry 4W RS
  "Industry_RS_12W": 88.9,    // Industry 12W RS
  "Market_Cap": 2750000000000.0,  // in USD
  "updated_at": ISODate("2023-09-16T02:30:00.000Z")
}
```

#### Field Specifications:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| _id | ObjectId | Yes | MongoDB 고유 ID | Auto-generated |
| date | ISODate | Yes | 측정 기준일 | Unique per ticker |
| ticker | String | Yes | 종목 코드 | Length: 1-10 |
| market | String | Yes | 시장 코드 | Enum: [NAS, NYS, ...] |
| RS_4W | Double | Yes | 4주 상대강도 | 0-100 |
| RS_12W | Double | Yes | 12주 상대강도 | 0-100 |
| RS_24W | Double | No | 24주 상대강도 | 0-100 |
| Sector | String | Yes | 섹터명 | Not empty |
| Industry | String | Yes | 산업명 | Not empty |
| Sector_RS_4W | Double | Yes | 섹터 4주 RS | 0-100 |
| Sector_RS_12W | Double | Yes | 섹터 12주 RS | 0-100 |
| Industry_RS_4W | Double | Yes | 산업 4주 RS | 0-100 |
| Industry_RS_12W | Double | Yes | 산업 12주 RS | 0-100 |
| Market_Cap | Double | Yes | 시가총액 (USD) | > 0 |
| updated_at | ISODate | Yes | 데이터 업데이트 시각 | Auto-generated |

---

### 3.4 Fundamental Data Schema (F)

#### Collection Name: `{TICKER}` (예: "AAPL")

```javascript
{
  "_id": ObjectId("..."),
  "date": ISODate("2023-09-15T00:00:00.000Z"),
  "ticker": "AAPL",
  "market": "NAS",
  "EPS": 6.15,                // Earnings Per Share (TTM)
  "EPS_YOY": 0.12,            // EPS YoY Growth (12%)
  "REV_YOY": 0.08,            // Revenue YoY Growth (8%)
  "PER": 28.7,                // Price to Earnings Ratio
  "PBR": 42.3,                // Price to Book Ratio
  "PSR": 7.8,                 // Price to Sales Ratio
  "ROE": 0.147,               // Return on Equity (14.7%)
  "ROA": 0.285,               // Return on Assets (28.5%)
  "Debt_Equity": 1.78,        // Debt to Equity Ratio
  "Current_Ratio": 0.93,      // Current Ratio
  "Market_Cap": 2750000000000.0,
  "Book_Value_Per_Share": 4.18,
  "Dividend_Yield": 0.0051,   // 0.51%
  "Payout_Ratio": 0.15,       // 15%
  "updated_at": ISODate("2023-09-16T02:30:00.000Z")
}
```

#### Field Specifications:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| _id | ObjectId | Yes | MongoDB 고유 ID | Auto-generated |
| date | ISODate | Yes | 데이터 기준일 | Unique per ticker |
| ticker | String | Yes | 종목 코드 | Length: 1-10 |
| market | String | Yes | 시장 코드 | Enum: [NAS, NYS, ...] |
| EPS | Double | Yes | 주당순이익 (TTM) | Any |
| EPS_YOY | Double | Yes | EPS 전년 대비 성장률 | -1.0 to 10.0 |
| REV_YOY | Double | Yes | 매출 전년 대비 성장률 | -1.0 to 10.0 |
| PER | Double | Yes | 주가수익비율 | > 0 |
| PBR | Double | Yes | 주가순자산비율 | > 0 |
| PSR | Double | Yes | 주가매출비율 | > 0 |
| ROE | Double | Yes | 자기자본이익률 | -1.0 to 2.0 |
| ROA | Double | Yes | 총자산이익률 | -1.0 to 1.0 |
| Debt_Equity | Double | Yes | 부채비율 | >= 0 |
| Current_Ratio | Double | Yes | 유동비율 | >= 0 |
| Market_Cap | Double | Yes | 시가총액 (USD) | > 0 |
| Book_Value_Per_Share | Double | Yes | 주당 순자산가치 | > 0 |
| Dividend_Yield | Double | No | 배당수익률 | 0 to 0.2 |
| Payout_Ratio | Double | No | 배당성향 | 0 to 1.5 |
| updated_at | ISODate | Yes | 데이터 업데이트 시각 | Auto-generated |

---

### 3.5 Earnings Data Schema (E)

#### Collection Name: `{TICKER}` (예: "AAPL")

```javascript
{
  "_id": ObjectId("..."),
  "EarningDate": ISODate("2023-08-03T00:00:00.000Z"),
  "ticker": "AAPL",
  "market": "NAS",
  "quarter": "Q3 2023",
  "fiscal_year": 2023,
  "eps": 1.26,                // Actual EPS
  "eps_estimate": 1.19,       // Analyst Estimate
  "eps_surprise": 0.07,       // Beat by $0.07
  "eps_surprise_pct": 0.059,  // 5.9% surprise
  "eps_yoy": 0.054,           // 5.4% YoY growth
  "revenue": 81797000000.0,   // Actual Revenue (USD)
  "revenue_estimate": 81690000000.0,
  "rev_surprise": 107000000.0,
  "rev_surprise_pct": 0.0013,
  "rev_yoy": -0.014,          // -1.4% YoY
  "guidance_eps_low": 1.39,
  "guidance_eps_high": 1.44,
  "guidance_revenue_low": 89000000000.0,
  "guidance_revenue_high": 93000000000.0,
  "announced_at": ISODate("2023-08-03T21:00:00.000Z"),
  "updated_at": ISODate("2023-08-04T02:30:00.000Z")
}
```

#### Field Specifications:

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| _id | ObjectId | Yes | MongoDB 고유 ID | Auto-generated |
| EarningDate | ISODate | Yes | 실적 발표일 | Unique per ticker+quarter |
| ticker | String | Yes | 종목 코드 | Length: 1-10 |
| market | String | Yes | 시장 코드 | Enum: [NAS, NYS, ...] |
| quarter | String | Yes | 분기 정보 | Format: "Q1 2023" |
| fiscal_year | Int32 | Yes | 회계연도 | 2000-2100 |
| eps | Double | Yes | 실제 EPS | Any |
| eps_estimate | Double | Yes | EPS 예상치 | Any |
| eps_surprise | Double | Yes | EPS 서프라이즈 | Any |
| eps_surprise_pct | Double | Yes | EPS 서프라이즈 비율 | -1.0 to 2.0 |
| eps_yoy | Double | Yes | EPS 전년 동기 대비 | -1.0 to 5.0 |
| revenue | Double | Yes | 실제 매출 (USD) | > 0 |
| revenue_estimate | Double | Yes | 매출 예상치 (USD) | > 0 |
| rev_surprise | Double | Yes | 매출 서프라이즈 | Any |
| rev_surprise_pct | Double | Yes | 매출 서프라이즈 비율 | -1.0 to 2.0 |
| rev_yoy | Double | Yes | 매출 전년 동기 대비 | -1.0 to 5.0 |
| guidance_eps_low | Double | No | 가이던스 EPS 하한 | Any |
| guidance_eps_high | Double | No | 가이던스 EPS 상한 | >= guidance_eps_low |
| guidance_revenue_low | Double | No | 가이던스 매출 하한 | > 0 |
| guidance_revenue_high | Double | No | 가이던스 매출 상한 | >= guidance_revenue_low |
| announced_at | ISODate | Yes | 발표 시각 (UTC) | Not null |
| updated_at | ISODate | Yes | 데이터 업데이트 시각 | Auto-generated |

---

## 4. Data Type Specifications

### 4.1 MongoDB Data Types

| Python Type | MongoDB Type | Usage | Example |
|-------------|--------------|-------|---------|
| datetime | ISODate | 날짜/시각 필드 | `ISODate("2023-09-15T00:00:00.000Z")` |
| float | Double | 가격, 비율 데이터 | `175.43` |
| int | Int32 | 연도, 카운트 | `2023` |
| int (large) | NumberLong | 거래량 | `NumberLong(75234100)` |
| str | String | 티커, 텍스트 | `"AAPL"` |
| ObjectId | ObjectId | MongoDB ID | `ObjectId("64f9...")` |

### 4.2 Type Conversion Rules

```python
# Python → MongoDB
{
    "date": pd.to_datetime("2023-09-15").to_pydatetime(),  # → ISODate
    "volume": int(75234100),                                # → NumberLong
    "price": float(175.43),                                 # → Double
    "ticker": str("AAPL"),                                  # → String
}

# MongoDB → Python (pandas)
{
    "date": pd.to_datetime(doc["date"]),                   # ISODate → datetime64
    "volume": int(doc["volume"]),                          # NumberLong → int64
    "price": float(doc["price"]),                          # Double → float64
    "ticker": str(doc["ticker"]),                          # String → str
}
```

---

## 5. Index Specifications

### 5.1 Daily Data Indexes (D)

```javascript
// Primary Index (자동 생성)
db.AAPL.createIndex({ "_id": 1 })

// Date Index (필수 - 시계열 쿼리)
db.AAPL.createIndex({ "date": -1 }, { unique: true })

// Ticker Index (멀티 티커 쿼리용)
db.AAPL.createIndex({ "ticker": 1, "date": -1 })

// Compound Index (날짜 범위 쿼리)
db.AAPL.createIndex({ "market": 1, "date": -1 })

// Performance Index
db.AAPL.createIndex({ "updated_at": -1 })
```

### 5.2 Relative Strength Indexes (RS)

```javascript
// RS Value Index (RS 기반 정렬)
db.AAPL.createIndex({ "RS_12W": -1, "date": -1 })

// Sector/Industry Index (섹터 분석)
db.AAPL.createIndex({ "Sector": 1, "Industry": 1, "RS_12W": -1 })

// Market Cap Index (시가총액 필터링)
db.AAPL.createIndex({ "Market_Cap": -1 })
```

### 5.3 Fundamental Data Indexes (F)

```javascript
// Valuation Index (밸류에이션 분석)
db.AAPL.createIndex({ "PER": 1, "PBR": 1 })

// Growth Index (성장성 분석)
db.AAPL.createIndex({ "EPS_YOY": -1, "REV_YOY": -1 })

// Quality Index (수익성 분석)
db.AAPL.createIndex({ "ROE": -1, "ROA": -1 })
```

### 5.4 Earnings Data Indexes (E)

```javascript
// Earnings Date Index
db.AAPL.createIndex({ "EarningDate": -1 }, { unique: true })

// Surprise Index (서프라이즈 분석)
db.AAPL.createIndex({ "eps_surprise_pct": -1 })

// Fiscal Year Index
db.AAPL.createIndex({ "fiscal_year": -1, "quarter": 1 })
```

### 5.5 Index Performance Impact

| Index Type | Query Speed | Insert Speed | Storage Impact |
|------------|-------------|--------------|----------------|
| Single Field | 10-50x faster | -5% | +5-10% |
| Compound (2 fields) | 20-100x faster | -10% | +10-15% |
| Compound (3+ fields) | 30-200x faster | -15% | +15-25% |

**권장사항**:
- 자주 쿼리하는 필드에만 인덱스 생성
- 쓰기 작업이 많은 컬렉션은 인덱스 최소화
- 복합 인덱스는 쿼리 패턴에 맞게 필드 순서 조정

---

## 6. Data Validation Rules

### 6.1 Schema Validation (MongoDB 4.0+)

```javascript
// Daily Data Validation
db.createCollection("AAPL", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["date", "volume", "ad_close", "ticker"],
      properties: {
        date: {
          bsonType: "date",
          description: "must be a date and is required"
        },
        volume: {
          bsonType: "long",
          minimum: 0,
          description: "must be a long integer >= 0"
        },
        ad_close: {
          bsonType: "double",
          minimum: 0,
          exclusiveMinimum: true,
          description: "must be a double > 0"
        },
        ticker: {
          bsonType: "string",
          minLength: 1,
          maxLength: 10,
          description: "must be a string between 1-10 characters"
        }
      }
    }
  },
  validationLevel: "moderate",  // moderate | strict
  validationAction: "warn"      // warn | error
})
```

### 6.2 Python Validation Layer

```python
from typing import Dict, Any
import pandas as pd
from datetime import datetime

class DataValidator:
    """데이터 삽입 전 검증"""

    @staticmethod
    def validate_daily_data(doc: Dict[str, Any]) -> bool:
        """Daily 데이터 검증"""
        # Required fields
        required = ["date", "volume", "ad_close", "ticker"]
        if not all(k in doc for k in required):
            raise ValueError(f"Missing required fields: {required}")

        # Type validation
        if not isinstance(doc["date"], datetime):
            raise TypeError("date must be datetime")
        if not isinstance(doc["volume"], (int, float)) or doc["volume"] < 0:
            raise ValueError("volume must be >= 0")
        if not isinstance(doc["ad_close"], float) or doc["ad_close"] <= 0:
            raise ValueError("ad_close must be > 0")

        # Price relationship
        if "ad_high" in doc and "ad_low" in doc:
            if doc["ad_high"] < doc["ad_low"]:
                raise ValueError("ad_high must be >= ad_low")

        return True

    @staticmethod
    def validate_rs_data(doc: Dict[str, Any]) -> bool:
        """RS 데이터 검증"""
        # RS range validation
        for field in ["RS_4W", "RS_12W", "Sector_RS_4W", "Industry_RS_4W"]:
            if field in doc:
                if not 0 <= doc[field] <= 100:
                    raise ValueError(f"{field} must be in range [0, 100]")

        # Required categorization
        if not doc.get("Sector") or not doc.get("Industry"):
            raise ValueError("Sector and Industry are required")

        return True

    @staticmethod
    def validate_fundamental_data(doc: Dict[str, Any]) -> bool:
        """Fundamental 데이터 검증"""
        # Growth rate validation
        for field in ["EPS_YOY", "REV_YOY"]:
            if field in doc:
                if not -1.0 <= doc[field] <= 10.0:
                    raise ValueError(f"{field} must be in range [-1.0, 10.0]")

        # Ratio validation
        if doc.get("ROE") and not -1.0 <= doc["ROE"] <= 2.0:
            raise ValueError("ROE must be in range [-1.0, 2.0]")

        return True
```

### 6.3 Data Integrity Checks

```python
class DataIntegrityChecker:
    """데이터 무결성 체크"""

    @staticmethod
    def check_duplicates(db_name: str, collection: str) -> List[str]:
        """중복 데이터 확인"""
        pipeline = [
            {"$group": {"_id": "$date", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = list(db[collection].aggregate(pipeline))
        return [d["_id"] for d in duplicates]

    @staticmethod
    def check_missing_dates(ticker: str, start: datetime, end: datetime) -> List[datetime]:
        """누락된 거래일 확인"""
        # Get all dates in DB
        cursor = db[ticker].find(
            {"date": {"$gte": start, "$lte": end}},
            {"date": 1}
        ).sort("date", 1)

        db_dates = set(doc["date"].date() for doc in cursor)

        # Expected trading days (exclude weekends)
        expected = pd.bdate_range(start, end)
        expected_dates = set(expected.date)

        missing = expected_dates - db_dates
        return sorted(missing)

    @staticmethod
    def check_price_anomalies(ticker: str, threshold: float = 0.5) -> List[Dict]:
        """가격 이상치 확인 (50% 이상 변동)"""
        pipeline = [
            {"$sort": {"date": 1}},
            {"$project": {
                "date": 1,
                "close": "$ad_close",
                "prev_close": {"$arrayElemAt": ["$ad_close", -1]}
            }},
            {"$project": {
                "date": 1,
                "change_pct": {
                    "$divide": [
                        {"$subtract": ["$close", "$prev_close"]},
                        "$prev_close"
                    ]
                }
            }},
            {"$match": {
                "change_pct": {"$gte": threshold}
            }}
        ]
        return list(db[ticker].aggregate(pipeline))
```

---

## 7. Schema Examples

### 7.1 Complete Daily Data Document

```javascript
{
  "_id": ObjectId("64f9a1b2c3d4e5f6a7b8c9d0"),
  "date": ISODate("2023-09-15T00:00:00.000Z"),
  "volume": NumberLong(75234100),
  "ad_open": 175.43,
  "ad_high": 177.82,
  "ad_low": 174.91,
  "ad_close": 176.54,
  "open": 175.50,
  "high": 177.90,
  "low": 175.00,
  "close": 176.60,
  "split_ratio": 1.0,
  "dividend": 0.0,
  "ticker": "AAPL",
  "market": "NAS",
  "updated_at": ISODate("2023-09-16T02:30:00.000Z")
}
```

### 7.2 Complete RS Data Document

```javascript
{
  "_id": ObjectId("64f9a1b2c3d4e5f6a7b8c9d1"),
  "date": ISODate("2023-09-15T00:00:00.000Z"),
  "ticker": "AAPL",
  "market": "NAS",
  "RS_4W": 87.5,
  "RS_12W": 91.3,
  "RS_24W": 89.7,
  "Sector": "Technology",
  "Industry": "Consumer Electronics",
  "Sector_RS_4W": 78.2,
  "Sector_RS_12W": 82.4,
  "Industry_RS_4W": 85.1,
  "Industry_RS_12W": 88.9,
  "Market_Cap": 2750000000000.0,
  "updated_at": ISODate("2023-09-16T02:30:00.000Z")
}
```

### 7.3 Complete Earnings Data Document

```javascript
{
  "_id": ObjectId("64f9a1b2c3d4e5f6a7b8c9d2"),
  "EarningDate": ISODate("2023-08-03T00:00:00.000Z"),
  "ticker": "AAPL",
  "market": "NAS",
  "quarter": "Q3 2023",
  "fiscal_year": 2023,
  "eps": 1.26,
  "eps_estimate": 1.19,
  "eps_surprise": 0.07,
  "eps_surprise_pct": 0.059,
  "eps_yoy": 0.054,
  "revenue": 81797000000.0,
  "revenue_estimate": 81690000000.0,
  "rev_surprise": 107000000.0,
  "rev_surprise_pct": 0.0013,
  "rev_yoy": -0.014,
  "guidance_eps_low": 1.39,
  "guidance_eps_high": 1.44,
  "guidance_revenue_low": 89000000000.0,
  "guidance_revenue_high": 93000000000.0,
  "announced_at": ISODate("2023-08-03T21:00:00.000Z"),
  "updated_at": ISODate("2023-08-04T02:30:00.000Z")
}
```

---

## 8. Performance Considerations

### 8.1 Data Volume Estimates

| Database | Collections | Documents per Collection | Total Documents | Storage Size |
|----------|-------------|--------------------------|-----------------|--------------|
| NasDataBase_D | 8,878 | ~3,000 (3년 데이터) | 26.6M | ~15 GB |
| NysDataBase_D | 6,235 | ~3,000 | 18.7M | ~11 GB |
| NasDataBase_W | 8,878 | ~156 (3년 주간) | 1.4M | ~800 MB |
| NasDataBase_RS | 8,878 | ~156 | 1.4M | ~900 MB |
| NasDataBase_F | 8,878 | ~12 (분기별) | 106K | ~150 MB |
| NasDataBase_E | 8,878 | ~12 | 106K | ~180 MB |
| **Total** | **~53K** | - | **~48M** | **~28 GB** |

### 8.2 Query Optimization

```python
# ❌ Bad: Full Collection Scan
docs = db["AAPL"].find({})  # O(n)

# ✅ Good: Index-based Query
docs = db["AAPL"].find({"date": {"$gte": start_date}}).sort("date", -1)  # O(log n)

# ❌ Bad: Fetching All Fields
docs = db["AAPL"].find({"date": date})  # 모든 필드 반환

# ✅ Good: Projection
docs = db["AAPL"].find(
    {"date": date},
    {"_id": 0, "ad_close": 1, "volume": 1}  # 필요한 필드만
)

# ❌ Bad: Multiple Queries
for ticker in tickers:
    doc = db[ticker].find_one({"date": date})  # O(n) queries

# ✅ Good: Aggregation Pipeline
pipeline = [
    {"$match": {"date": date}},
    {"$group": {"_id": "$ticker", "close": {"$first": "$ad_close"}}}
]
docs = db.aggregate(pipeline)  # Single query
```

### 8.3 Memory Optimization

```python
# ❌ Bad: Load All Data
df = pd.DataFrame(list(db["AAPL"].find({})))  # 모든 데이터 메모리 로드

# ✅ Good: Streaming with Cursor
cursor = db["AAPL"].find({}).batch_size(1000)
for batch in cursor:
    process_batch(batch)  # 1000개씩 처리

# ✅ Good: Date Range Limiting
recent_data = db["AAPL"].find({
    "date": {"$gte": datetime.now() - timedelta(days=365)}
})
```

### 8.4 Write Performance

```python
# ❌ Bad: Individual Inserts
for doc in documents:
    db["AAPL"].insert_one(doc)  # O(n) operations

# ✅ Good: Bulk Insert
db["AAPL"].insert_many(documents, ordered=False)  # Single operation

# ✅ Good: Bulk Upsert
bulk_ops = [
    UpdateOne(
        {"date": doc["date"]},
        {"$set": doc},
        upsert=True
    ) for doc in documents
]
db["AAPL"].bulk_write(bulk_ops, ordered=False)
```

### 8.5 Index Usage Analysis

```javascript
// Query Plan 확인
db.AAPL.find({"date": {"$gte": ISODate("2023-01-01")}}).explain("executionStats")

// 출력 예시:
{
  "queryPlanner": {
    "winningPlan": {
      "stage": "FETCH",
      "inputStage": {
        "stage": "IXSCAN",  // ✅ Index Scan (Good!)
        "indexName": "date_-1"
      }
    }
  },
  "executionStats": {
    "executionTimeMillis": 12,
    "totalDocsExamined": 756,
    "totalKeysExamined": 756  // Same as docs = efficient
  }
}
```

---

## 9. Schema Migration

### 9.1 Version Control

```python
# Schema version tracking
SCHEMA_VERSIONS = {
    "DAILY_DATA": {
        "v1.0": "2023-01-01",  # Initial schema
        "v1.1": "2023-06-15",  # Added split_ratio, dividend
        "v2.0": "2023-09-01",  # Added updated_at
    },
    "RS_DATA": {
        "v1.0": "2023-01-01",
        "v1.1": "2023-07-01",  # Added RS_24W
    }
}

# Schema migration script
def migrate_daily_v1_to_v2():
    """Add updated_at field to existing documents"""
    db.AAPL.update_many(
        {"updated_at": {"$exists": False}},
        {"$set": {"updated_at": datetime.utcnow()}}
    )
```

### 9.2 Backward Compatibility

```python
def safe_read_document(doc: Dict) -> Dict:
    """Ensure backward compatibility when reading"""
    # Handle missing fields
    doc.setdefault("split_ratio", 1.0)
    doc.setdefault("dividend", 0.0)
    doc.setdefault("updated_at", doc.get("date"))

    return doc
```

---

## 10. References

### 10.1 Related Documents
- **DATABASE_LAYER_INTERFACE.md**: MongoDB CRUD 인터페이스 명세
- **DATABASE_MODULES.md**: Database 모듈 설명
- **INDICATOR_LAYER_INTERFACE.md**: Indicator Layer 입출력 규약
- **CLAUDE.md**: 프로젝트 전체 규칙

### 10.2 MongoDB Documentation
- MongoDB Schema Validation: https://docs.mongodb.com/manual/core/schema-validation/
- Index Strategies: https://docs.mongodb.com/manual/applications/indexes/
- Data Modeling: https://docs.mongodb.com/manual/core/data-modeling-introduction/

---

**Document Version**: 1.0
**Last Updated**: 2025-10-09
**Next Review**: 2025-11-09
**Maintained By**: Database Agent
