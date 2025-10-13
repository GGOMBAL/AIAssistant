# Data Agent Architecture Documentation

**버전**: 1.0
**작성일**: 2025-09-21
**업데이트**: 데이터 레이어 아키텍처 분석 완료

---

## 🎯 Data Agent 개요

Data Agent는 **데이터 수집, 지표 생성, 데이터베이스 관리를 전담**하는 에이전트로, 시장 데이터 처리와 기술적 지표 계산의 핵심 기능을 담당합니다.

### 주요 책임
- 시장 데이터 수집 및 정규화
- 기술적 지표 계산 및 생성
- 데이터베이스 스키마 관리 및 CRUD 연산
- 데이터 품질 검증 및 무결성 보장

---

## 📁 파일 접근 권한

### EXCLUSIVE (읽기/쓰기/실행)
Data Agent는 다음 파일들에 대해 **독점적 권한**을 가집니다:

```
Project/indicator/
├── technical_indicators.py          # 기술적 지표 생성 엔진
├── data_frame_generator.py         # 데이터프레임 생성 및 관리
└── __init__.py                     # 패키지 초기화

Project/database/
├── database_manager.py             # 통합 데이터베이스 관리자
├── mongodb_operations.py           # MongoDB 기본 연산
├── us_market_manager.py            # 미국 시장 데이터 관리
├── historical_data_manager.py      # 계좌/거래 내역 관리
├── database_name_calculator.py     # DB명 계산 유틸리티
└── __init__.py                     # 패키지 초기화
```

### READ-ONLY (읽기 전용)
다른 레이어에서 Data Agent의 결과를 읽을 수 있습니다:

```
storage/market_data/                # 시장 데이터 캐시 (다른 Agent 읽기 가능)
storage/indicators/                 # 계산된 지표 데이터 (다른 Agent 읽기 가능)
```

### 설정 파일 접근
```
config/api_credentials.yaml         # 데이터 API 자격증명 (읽기)
config/broker_config.yaml          # 시장 설정 정보 (읽기)
```

---

## 🏗️ 서비스 아키텍처

### 1. Technical Indicator Generator

**파일**: `technical_indicators.py`
**클래스**: `TechnicalIndicatorGenerator`
**기능**: 시장 데이터로부터 기술적 지표 계산 및 생성

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `get_technical_data()` | universe, df_dict, p_code | Dict | 기술적 지표 데이터 반환 |
| `_process_daily_data()` | 일봉 데이터 | pd.DataFrame | 일봉 기술적 지표 계산 |
| `_process_weekly_data()` | 주봉 데이터 | pd.DataFrame | 주봉 기술적 지표 계산 |
| `_process_rs_data()` | 가격 데이터 | pd.DataFrame | 상대강도(RS) 계산 |
| `_process_fundamental_data()` | 기본정보 | pd.DataFrame | 펀더멘털 지표 처리 |
| `return_processed_data()` | - | Tuple[Dict x5] | 모든 처리된 데이터 반환 |

#### 계산되는 지표들
```python
# 가격 관련 지표
- SMA (5, 10, 20, 60, 120, 200일)
- Highest (1M, 3M, 6M, 1Y, 2Y)
- ADR (Average Daily Range)

# 모멘텀 지표
- SMA Momentum (5, 10, 20, 60일)
- RS (Relative Strength) 4주/12주

# 볼륨 지표
- Volume 이동평균
- Volume Rate
```

### 2. DataFrame Generator

**파일**: `data_frame_generator.py`
**클래스**: `DataFrameGenerator`
**기능**: 데이터베이스로부터 데이터프레임 생성 및 관리

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `read_database_task()` | market, area, data_type | Dict[str, pd.DataFrame] | DB 데이터 읽기 |
| `load_data_from_database()` | - | None | 전체 데이터 로딩 |
| `get_strategy_data()` | strategy_name | Tuple[Dict, List] | 전략별 데이터 제공 |
| `filter_by_date_range()` | data_dict, 날짜범위 | Dict | 날짜 필터링 |
| `get_dataframes()` | - | Dict[str, Dict] | 모든 데이터프레임 반환 |

#### 지원 데이터 타입
```python
DATA_TYPES = [
    'Daily',        # 일봉 데이터
    'Weekly',       # 주봉 데이터
    'Fundamental',  # 기본정보
    'Earnings',     # 실적 데이터
    'Dividend'      # 배당 데이터
]
```

### 3. Database Manager

**파일**: `database_manager.py`
**클래스**: `DatabaseManager`
**기능**: 통합 데이터베이스 관리 및 조정

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `get_us_market_manager()` | market | USMarketDataManager | 시장별 매니저 반환 |
| `initialize_market_data()` | area, market, types | Dict[str, bool] | 시장 데이터 초기화 |
| `store_account_data()` | mode, account_data | bool | 계좌 데이터 저장 |
| `store_trade_data()` | mode, trade_data | bool | 거래 데이터 저장 |
| `get_database_name()` | market, area, p_code | str | DB명 계산 |
| `execute_database_query()` | db명, 컬렉션, 쿼리 | Any | 쿼리 실행 |

### 4. MongoDB Operations

**파일**: `mongodb_operations.py`
**클래스**: `MongoDBOperations`
**기능**: MongoDB 기본 CRUD 연산

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `make_stock_db()` | db명, df_data, stock | bool | 주식 DB 생성 |
| `update_stock_db()` | db명, df_data, stock | bool | 주식 DB 업데이트 |
| `execute_query()` | db명, 컬렉션, 쿼리 | List/Dict | 쿼리 실행 |
| `get_latest_data()` | db명, 컬렉션 | dict | 최신 데이터 조회 |
| `check_data_exists()` | db명, 컬렉션, 쿼리 | bool | 데이터 존재 확인 |

### 5. US Market Data Manager

**파일**: `us_market_manager.py`
**클래스**: `USMarketDataManager`
**기능**: 미국 시장 데이터 전용 관리

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `make_mongodb_us_stock()` | ohlcv 옵션 | bool | 미국 주식 DB 생성 |
| `make_mongodb_us_etf()` | ohlcv 옵션 | bool | 미국 ETF DB 생성 |
| `get_market_status()` | - | dict | 시장 상태 정보 |
| `validate_data_integrity()` | db명, 샘플크기 | dict | 데이터 무결성 검증 |

### 6. Historical Data Manager

**파일**: `historical_data_manager.py`
**클래스**: `HistoricalDataManager`
**기능**: 계좌 및 거래 내역 관리

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `make_mongodb_account()` | mode, account_dict | bool | 계좌 데이터 저장 |
| `make_mongodb_trade()` | mode, trade_dict | bool | 거래 데이터 저장 |
| `get_account_history()` | mode, 날짜범위 | Dict | 계좌 내역 조회 |
| `get_trade_history()` | mode, 날짜범위 | Dict | 거래 내역 조회 |

---

## 🔗 인터페이스 정의

### 입력 인터페이스

#### 1. 외부 시장 데이터 (from Helper Agent)
```python
{
    "universe": List[str],           # 종목 유니버스
    "market_data": {
        "daily": Dict[str, pd.DataFrame],    # 일봉 데이터
        "weekly": Dict[str, pd.DataFrame],   # 주봉 데이터
        "fundamental": Dict[str, pd.DataFrame], # 기본정보
        "earnings": Dict[str, pd.DataFrame]  # 실적 데이터
    }
}
```

#### 2. 계좌 데이터 (from Helper Agent)
```python
{
    "account_data": {
        "balance": Dict[str, float],     # 계좌 잔고
        "holdings": List[Dict],          # 보유 종목
        "cash": float                    # 현금 잔고
    },
    "trade_data": {
        "transactions": List[Dict],      # 거래 내역
        "orders": List[Dict]             # 주문 내역
    }
}
```

### 출력 인터페이스

#### 1. 기술적 지표 데이터 (to Strategy Agent)
```python
{
    "daily_indicators": Dict[str, pd.DataFrame],    # 일봉 지표
    "weekly_indicators": Dict[str, pd.DataFrame],   # 주봉 지표
    "rs_indicators": Dict[str, pd.DataFrame],       # RS 지표
    "fundamental_data": Dict[str, pd.DataFrame],    # 기본정보
    "earnings_data": Dict[str, pd.DataFrame],       # 실적 데이터
    "metadata": {
        "last_update": datetime,
        "data_quality": Dict[str, float],
        "coverage": Dict[str, int]
    }
}
```

#### 2. 데이터베이스 상태 (to Orchestrator)
```python
{
    "database_status": {
        "connection_status": Dict[str, bool],
        "data_freshness": Dict[str, datetime],
        "error_logs": List[str],
        "performance_metrics": Dict[str, float]
    },
    "data_summary": {
        "total_stocks": int,
        "latest_date": datetime,
        "data_completeness": float,
        "processing_time": float
    }
}
```

---

## 🗄️ 데이터베이스 스키마

### 1. 시장 데이터 스키마
```python
# 일봉/주봉 데이터
{
    "Date": datetime,
    "Open": float,
    "High": float,
    "Low": float,
    "Close": float,
    "Volume": int,
    "Adj_Close": float,
    # 기술적 지표
    "SMA_5": float,
    "SMA_20": float,
    "SMA_200": float,
    "Highest_1Y": float,
    "ADR_20": float,
    "Volume_SMA_20": float
}
```

### 2. 기본정보 스키마
```python
{
    "Date": datetime,
    "Market_Cap": float,
    "EPS": float,
    "Revenue": float,
    "Dividend_Yield": float,
    "P_E_Ratio": float,
    "Debt_to_Equity": float
}
```

### 3. 계좌 데이터 스키마
```python
{
    "timestamp": datetime,
    "account_type": str,        # "real" or "virtual"
    "total_asset": float,
    "cash_balance": float,
    "stock_value": float,
    "holdings": [
        {
            "ticker": str,
            "amount": float,
            "avg_price": float,
            "current_price": float,
            "market_value": float
        }
    ]
}
```

---

## ⚙️ 설정 파일 연동

### 1. API 자격증명
**파일**: `config/api_credentials.yaml`
```yaml
databases:
  mongodb_local:
    host: "localhost"
    port: 27017
    username: ""
    password: ""
  mongodb_nas:
    host: "192.168.1.100"
    port: 27017
    username: "trader"
    password: "encrypted_password"

external_apis:
  alpha_vantage:
    api_key: "api_key_here"
    requests_per_minute: 5
  yahoo_finance:
    timeout: 30
```

### 2. 브로커 설정
**파일**: `config/broker_config.yaml`
```yaml
markets:
  US:
    trading_hours:
      open: "09:30"
      close: "16:00"
      timezone: "America/New_York"
    data_sources:
      primary: "alpha_vantage"
      fallback: "yahoo_finance"
```

---

## 🔄 데이터 플로우

### 1. 시장 데이터 수집 플로우
```
[Helper Agent] → Raw Market Data → [Data Agent]
                     ↓
            DataFrameGenerator
                     ↓
            TechnicalIndicatorGenerator
                     ↓
            MongoDBOperations (저장)
                     ↓
[Strategy Agent] ← Processed Data ← [Data Agent]
```

### 2. 계좌 데이터 관리 플로우
```
[Helper Agent] → Account/Trade Data → [Data Agent]
                     ↓
            HistoricalDataManager
                     ↓
            MongoDBOperations (저장)
                     ↓
[Strategy Agent] ← Account Analysis Data ← [Data Agent]
```

---

## 🚨 제약사항 및 규칙

### 1. 데이터 접근 제한
- **절대 금지**: 외부 API 직접 호출 (Helper Agent를 통해서만)
- **읽기만 허용**: 설정 파일들 (`config/*.yaml`)
- **독점 권한**: `Project/indicator/`, `Project/database/` 내 모든 파일

### 2. 데이터 품질 보장
- **필수 검증**: 모든 입력 데이터의 스키마 검증
- **데이터 정합성**: 날짜 연속성 및 값 범위 검증
- **오류 처리**: 결측값 처리 및 이상값 탐지

### 3. 성능 최적화
- **메모리 관리**: 대용량 데이터프레임 청크 단위 처리
- **캐싱 전략**: 자주 사용되는 지표 데이터 캐싱
- **인덱싱**: 데이터베이스 쿼리 성능 최적화

---

## 📊 성능 지표

### 1. 데이터 처리 성능
- **지표 계산 시간**: < 10초 (1000종목 기준)
- **데이터 로딩 시간**: < 30초 (전체 유니버스)
- **데이터베이스 쿼리**: < 2초 (단일 종목)

### 2. 데이터 품질
- **데이터 완전성**: > 98% (결측값 비율)
- **계산 정확도**: 100% (기술적 지표)
- **실시간성**: < 5분 지연 (시장 데이터)

### 3. 시스템 안정성
- **가용시간**: > 99.5%
- **데이터 손실률**: < 0.1%
- **복구 시간**: < 1분 (장애 발생 시)

---

## 🔧 개발 및 유지보수

### 1. 데이터 스키마 관리
- **버전 관리**: 스키마 변경 시 하위 호환성 보장
- **마이그레이션**: 자동 데이터 마이그레이션 스크립트
- **백업**: 일일 자동 백업 및 복구 프로세스

### 2. 모니터링
- **데이터 품질 모니터링**: 실시간 품질 지표 추적
- **성능 모니터링**: 처리 시간 및 리소스 사용량
- **오류 알림**: 데이터 처리 실패 시 즉시 알림

### 3. 확장성
- **수평 확장**: 멀티 프로세스 데이터 처리 지원
- **새로운 지표**: 플러그인 방식으로 새 지표 추가
- **다중 시장**: 새로운 시장 데이터 소스 연동

---

**📝 문서 상태**: 데이터 레이어 아키텍처 분석 완료 (2025-09-21)
**다음 업데이트**: 실시간 데이터 파이프라인 구축 완료 시