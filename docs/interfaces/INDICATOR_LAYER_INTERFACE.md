# Indicator Layer Interface Specification

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Data Agent
**Status**: Draft (To be completed by Data Agent)

---

## 1. Overview

### Purpose
Indicator Layer는 Raw 시장 데이터를 로드하고 기술적 지표를 계산하여 Strategy Layer에 제공합니다.

### Main Responsibilities
- MongoDB에서 시장 데이터 로드 (Daily, Weekly, RS, Fundamental, Earnings)
- 기술 지표 계산 (SMA, EMA, ADR, RSI 등)
- 데이터 정규화 및 전처리
- 표준화된 DataFrame 포맷으로 출력

### Key Components
- `DataFrameGenerator`: 메인 데이터 생성 클래스
- `TechnicalIndicators`: 기술 지표 계산 모듈

---

## 2. Input Interface

### 2.1. DataFrameGenerator 초기화

```python
def __init__(
    self,
    universe: List[str],        # 종목 리스트
    market: str = 'US',         # 시장 코드
    area: str = 'US',           # 지역 코드
    start_day: datetime = None, # 시작일
    end_day: datetime = None    # 종료일
)
```

**Parameters**:
- `universe` (List[str], required): 분석 대상 종목 심볼 리스트
- `market` (str, optional): 시장 코드 (기본값: 'US')
- `area` (str, optional): 지역 코드 (기본값: 'US')
- `start_day` (datetime, optional): 데이터 시작일 (기본값: 1년 전)
- `end_day` (datetime, optional): 데이터 종료일 (기본값: 오늘)

**Constraints**:
- `universe`는 최소 1개 이상의 심볼 포함
- `start_day < end_day`
- 최대 lookback 기간: 3년

### 2.2. 데이터 로드 메서드

```python
def load_data_from_database(self) -> None
```

**Parameters**: None

**Side Effects**:
- `self.df_D`, `self.df_W`, `self.df_RS`, `self.df_F`, `self.df_E` 속성 설정
- MongoDB 연결 및 데이터 읽기
- 기술 지표 자동 계산

---

## 3. Output Interface

### 3.1. 출력 데이터 구조

모든 출력은 `Dict[str, pd.DataFrame]` 형식:

```python
{
    "AAPL": pd.DataFrame(...),
    "MSFT": pd.DataFrame(...),
    ...
}
```

### 3.2. Daily Data (df_D)

**DataFrame Columns** (refer to `refer/debug_json/df_D_columns_after_TRD.json`):

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Dopen | float | 일간 시가 | 150.25 |
| Dhigh | float | 일간 고가 | 152.30 |
| Dlow | float | 일간 저가 | 149.80 |
| Dclose | float | 일간 종가 | 151.50 |
| Dvolume | int | 일간 거래량 | 1000000 |
| SMA20 | float | 20일 이동평균 | 150.00 |
| SMA50 | float | 50일 이동평균 | 148.50 |
| SMA200 | float | 200일 이동평균 | 145.00 |
| ADR | float | Average Daily Range (%) | 2.5 |
| Highest_1Y | float | 1년 최고가 | 160.00 |

**Index**: DatetimeIndex (ISO 8601 format)

### 3.3. Weekly Data (df_W)

**DataFrame Columns** (refer to `refer/debug_json/df_W_columns_after_TRD.json`):

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Wopen | float | 주간 시가 | 150.25 |
| Whigh | float | 주간 고가 | 155.00 |
| Wlow | float | 주간 저가 | 148.00 |
| Wclose | float | 주간 종가 | 153.00 |
| 52_H | float | 52주 최고가 | 165.00 |
| 52_L | float | 52주 최저가 | 130.00 |
| 1Year_H | float | 1년 최고가 | 165.00 |
| 1Year_L | float | 1년 최저가 | 135.00 |
| 2Year_H | float | 2년 최고가 | 170.00 |
| 2Year_L | float | 2년 최저가 | 120.00 |

### 3.4. Relative Strength (df_RS)

**DataFrame Columns**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| RS_4W | float | 4주 상대 강도 | 85.5 |
| RS_12W | float | 12주 상대 강도 | 78.3 |
| Sector | str | 섹터 | "Technology" |
| Industry | str | 산업 | "Software" |
| Sector_RS_4W | float | 섹터 평균 RS | 70.0 |
| Industry_RS_4W | float | 산업 평균 RS | 75.0 |

### 3.5. Fundamental Data (df_F)

**DataFrame Columns**:

| Column | Type | Description | Example | Unit |
|--------|------|-------------|---------|------|
| REV_YOY | float | 매출 전년 대비 성장률 | 0.155 | Decimal (0.155 = 15.5%) |
| EPS_YOY | float | EPS 전년 대비 성장률 | 0.203 | Decimal (0.203 = 20.3%) |
| REV_QOQ | float | 매출 전분기 대비 성장률 | 0.050 | Decimal (0.050 = 5.0%) |
| EPS_QOQ | float | EPS 전분기 대비 성장률 | 0.075 | Decimal (0.075 = 7.5%) |
| MarketCapitalization | float | 시가총액 (USD) | 2500000000 | USD |
| PBR | float | 주가순자산비율 | 5.2 | Ratio |
| PSR | float | 주가매출비율 | 3.8 | Ratio |
| ROE | float | 자기자본이익률 | 0.185 | Decimal (0.185 = 18.5%) |

### 3.6. Earnings Data (df_E)

**DataFrame Columns** (Converted from % to decimal format):

| Column | Type | Description | Example | Unit |
|--------|------|-------------|---------|------|
| EarningDate | datetime | 실적 발표일 | 2024-01-15 | Date |
| eps | float | 주당순이익 | 2.50 | USD |
| eps_yoy | float | EPS 전년 대비 성장률 | 0.250 | Decimal (0.250 = 25.0%) |
| eps_qoq | float | EPS 전분기 대비 성장률 | 0.100 | Decimal (0.100 = 10.0%) |
| revenue | float | 매출 (USD) | 50000000 | USD |
| rev_yoy | float | 매출 전년 대비 성장률 | 0.180 | Decimal (0.180 = 18.0%) |
| rev_qoq | float | 매출 전분기 대비 성장률 | 0.050 | Decimal (0.050 = 5.0%) |

**Note**: Earnings data (df_E) is automatically converted from percentage format to decimal format in the Indicator Layer.
- Source data: `eps_yoy = 25.0` (stored as 25%)
- After conversion: `eps_yoy = 0.25` (decimal format)
- This ensures consistency with Fundamental data (df_F) which uses decimal format.

---

## 4. Error Handling

### 4.1. Exception Types

| Exception | Condition | Recovery |
|-----------|-----------|----------|
| `MongoDBConnectionError` | MongoDB 연결 실패 | Helper Layer fallback 사용 |
| `DataNotFoundError` | 종목 데이터 없음 | 해당 종목 제외하고 계속 진행 |
| `InvalidDateRangeError` | start_day >= end_day | ValueError 발생 |
| `EmptyUniverseError` | universe가 빈 리스트 | ValueError 발생 |

### 4.2. Error Response Format

```python
{
    "error": {
        "code": "DATA_NOT_FOUND",
        "message": "No data found for symbol: AAPL",
        "symbol": "AAPL",
        "timestamp": "2025-10-09T10:30:00Z"
    }
}
```

---

## 5. Examples

### 5.1. Basic Usage

```python
from project.indicator.data_frame_generator import DataFrameGenerator
from datetime import datetime, timedelta

# 초기화
generator = DataFrameGenerator(
    universe=["AAPL", "MSFT", "GOOGL"],
    market="US",
    area="US",
    start_day=datetime.now() - timedelta(days=365),
    end_day=datetime.now()
)

# 데이터 로드
generator.load_data_from_database()

# 결과 접근
daily_data = generator.df_D
weekly_data = generator.df_W

print(f"Loaded {len(daily_data)} symbols")
print(f"AAPL daily data shape: {daily_data['AAPL'].shape}")
```

### 5.2. Accessing Specific Indicators

```python
# 특정 종목의 일간 데이터
aapl_daily = generator.df_D["AAPL"]

# SMA20 값 출력
print(aapl_daily["SMA20"].tail())

# 최근 52주 최고가
aapl_weekly = generator.df_W["AAPL"]
print(f"52-week high: {aapl_weekly['52_H'].iloc[-1]}")
```

### 5.3. Error Handling

```python
try:
    generator = DataFrameGenerator(
        universe=[],  # Empty universe
        market="US"
    )
except ValueError as e:
    print(f"Error: {e}")
    # Handle empty universe case
```

---

## 6. Dependencies

### 6.1. Internal Dependencies
- **Database Layer**: MongoDB 데이터 접근
- **Helper Layer**: 외부 API를 통한 데이터 보완

### 6.2. External Libraries
- `pandas >= 1.5.0`: DataFrame 처리
- `numpy >= 1.23.0`: 수치 계산
- `pymongo >= 4.0.0`: MongoDB 연결
- `ta-lib` (optional): 고급 기술 지표

### 6.3. Database Collections
- `NasDataBase_D`: NASDAQ 일간 데이터
- `NysDataBase_D`: NYSE 일간 데이터
- `NasDataBase_W`: NASDAQ 주간 데이터
- `NysDataBase_W`: NYSE 주간 데이터
- `NasDataBase_RS`: NASDAQ 상대강도 데이터
- `NysDataBase_RS`: NYSE 상대강도 데이터
- `NasDataBase_F`: NASDAQ 펀더멘털 데이터
- `NysDataBase_F`: NYSE 펀더멘털 데이터
- `NasDataBase_E`: NASDAQ 실적 데이터
- `NysDataBase_E`: NYSE 실적 데이터

---

## 7. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-09 | Initial draft created | Data Agent |

---

## 8. Notes

### Performance Considerations
- 500개 종목 × 3년 데이터: 약 10-15초 소요
- 병렬 처리로 성능 최적화 (ThreadPoolExecutor)
- 메모리 사용량: 약 500MB (500 종목 기준)

### Known Issues
- [ ] MongoDB 연결 타임아웃 처리 개선 필요
- [ ] Helper Layer fallback 로직 테스트 필요
- [ ] 대량 종목 처리 시 메모리 최적화 필요

### TODO
- [ ] 캐싱 메커니즘 추가
- [ ] 증분 업데이트 지원
- [ ] 데이터 품질 검증 로직 강화
