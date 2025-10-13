# Helper Agent Architecture Documentation

**버전**: 1.0
**작성일**: 2025-09-21
**업데이트**: 외부 연동 레이어 아키텍처 분석 완료

---

## 🎯 Helper Agent 개요

Helper Agent는 **외부 API 연결, 브로커 연동, 알림 서비스를 전담**하는 에이전트로, 시스템과 외부 세계 간의 모든 통신을 담당합니다.

### 주요 책임
- 외부 시장 데이터 API 연동 및 관리
- 브로커 API를 통한 계좌 정보 및 주문 처리
- 텔레그램을 통한 실시간 알림 및 커뮤니케이션
- 외부 서비스 인증 및 보안 관리

---

## 📁 파일 접근 권한

### EXCLUSIVE (읽기/쓰기/실행)
Helper Agent는 다음 파일들에 대해 **독점적 권한**을 가집니다:

```
Project/Helper/
├── broker_api_connector.py         # 브로커 API 통합 연결
├── data_provider_api.py            # 외부 데이터 제공자 API
├── kis_api_helper_us.py            # 한국투자증권 미국 거래 API
├── kis_common.py                   # 한국투자증권 공통 기능
├── telegram_messenger.py           # 텔레그램 메신저 서비스
├── yfinance_helper.py              # Yahoo Finance API 헬퍼
├── HELPER_AGENT_ACCESS_CONTROL.md  # 접근 제어 문서
└── __init__.py                     # 패키지 초기화

myStockInfo.yaml                    # 개인 투자 정보 (Helper Agent 전용)
```

### READ-ONLY (읽기 전용)
Helper Agent가 참조해야 하는 설정 파일들:

```
config/api_credentials.yaml         # API 자격증명 (읽기)
config/broker_config.yaml          # 브로커 설정 (읽기)
config/risk_management.yaml        # 리스크 관리 설정 (읽기)
```

### 출력 데이터 (다른 Agent 읽기 가능)
```
storage/market_data/                # 수집된 시장 데이터
storage/account_data/               # 계좌 정보 스냅샷
storage/notifications/              # 발송된 알림 로그
```

---

## 🏗️ 서비스 아키텍처

### 1. Data Provider Services

#### 1.1 YFinance Helper
**파일**: `yfinance_helper.py`
**클래스**: `YFinanceHelper`
**기능**: Yahoo Finance API를 통한 시장 데이터 수집

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `get_ohlcv()` | ticker, 기간 | pd.DataFrame | OHLCV 데이터 수집 |
| `get_current_price()` | ticker | float | 현재가 조회 |
| `get_company_info()` | ticker | Dict[str, Any] | 기업 정보 조회 |
| `get_financial_data()` | ticker, 재무제표 유형 | pd.DataFrame | 재무 데이터 |
| `get_analyst_recommendations()` | ticker | pd.DataFrame | 애널리스트 추천 |

#### 1.2 Alpha Vantage API
**파일**: `data_provider_api.py`
**클래스**: `AlphaVantageAPI`
**기능**: Alpha Vantage API를 통한 고품질 시장 데이터 수집

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `get_ticker_list()` | market, asset_type | List[str] | 종목 리스트 조회 |
| `get_ohlcv()` | symbol, 기간 | pd.DataFrame | 일봉 데이터 수집 |
| `get_ohlcv_intraday()` | symbol, interval | pd.DataFrame | 분봉 데이터 수집 |
| `get_fundamental_data()` | symbol | Dict[str, Any] | 기본정보 데이터 |
| `get_earnings_data()` | symbol | pd.DataFrame | 실적 데이터 |

#### 1.3 Data Provider Manager
**파일**: `data_provider_api.py`
**클래스**: `DataProviderManager`
**기능**: 다중 데이터 제공자 통합 관리

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `add_provider()` | name, provider | None | 데이터 제공자 추가 |
| `set_default_provider()` | name | None | 기본 제공자 설정 |
| `get_ohlcv()` | symbol, 기간, provider | pd.DataFrame | 통합 데이터 조회 |
| `get_multiple_prices()` | symbols, provider | Dict[str, float] | 다중 종목 현재가 |

### 2. Broker API Services

#### 2.1 KIS Common
**파일**: `kis_common.py`
**클래스**: `KISCommon`
**기능**: 한국투자증권 API 공통 기능

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `make_token()` | dist (계좌구분) | bool | 인증 토큰 생성 |
| `get_token()` | dist | str | 인증 토큰 조회 |
| `get_hash_key()` | data | str | 해시키 생성 |
| `get_ohlcv()` | area, stock_code | pd.DataFrame | OHLCV 데이터 조회 |

#### 2.2 KIS US Helper
**파일**: `kis_api_helper_us.py`
**클래스**: `KISUSHelper`
**기능**: 한국투자증권 미국 거래 전용 API

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `is_market_open()` | - | bool | 미국 시장 개장 여부 |
| `get_balance()` | currency | Dict[str, Any] | 계좌 잔고 조회 |
| `get_current_price()` | stock_code | float | 현재가 조회 |
| `make_buy_limit_order()` | stock_code, amt, price | Dict[str, Any] | 매수 주문 |
| `make_sell_limit_order()` | stock_code, amt, price | Dict[str, Any] | 매도 주문 |

#### 2.3 Broker API Manager
**파일**: `broker_api_connector.py`
**클래스**: `BrokerAPIManager`
**기능**: 다중 브로커 API 통합 관리

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `add_broker()` | name, broker_api | None | 브로커 API 추가 |
| `set_active_broker()` | name | None | 활성 브로커 설정 |
| `is_market_open()` | broker_name | bool | 시장 개장 여부 |
| `place_order()` | symbol, side, quantity, price | Dict[str, Any] | 통합 주문 처리 |

### 3. Communication Services

#### 3.1 Telegram Bot
**파일**: `telegram_messenger.py`
**클래스**: `TelegramBot`
**기능**: 기본 텔레그램 봇 기능

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `send_message()` | message, chat_id | bool | 메시지 전송 |
| `send_photo()` | photo_path, caption | bool | 이미지 전송 |
| `send_document()` | document_path, caption | bool | 문서 전송 |
| `get_updates()` | offset, limit | List[Dict] | 업데이트 수신 |

#### 3.2 Telegram Notification Service
**파일**: `telegram_messenger.py`
**클래스**: `TelegramNotificationService`
**기능**: 거래 알림 전문 서비스

#### 핵심 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `send_trading_signal()` | symbol, action, price | bool | 거래 신호 알림 |
| `send_order_executed()` | symbol, side, quantity | bool | 주문 체결 알림 |
| `send_daily_summary()` | pnl, trade_count, win_rate | bool | 일일 요약 |
| `send_balance_update()` | cash, stocks, total | bool | 잔고 업데이트 |

#### 3.3 Telegram Command Handler
**파일**: `telegram_messenger.py`
**클래스**: `TelegramCommandHandler`
**기능**: 텔레그램 명령어 처리

#### 지원 명령어
```
/start    - 봇 시작
/help     - 도움말
/status   - 시스템 상태
/balance  - 계좌 잔고
/positions - 보유 포지션
```

---

## 🔗 인터페이스 정의

### 입력 인터페이스

#### 1. 데이터 요청 (from Data Agent)
```python
{
    "data_request": {
        "symbols": List[str],           # 조회할 종목 리스트
        "data_type": str,               # "ohlcv", "fundamental", "earnings"
        "start_date": datetime,         # 시작 날짜
        "end_date": datetime,           # 종료 날짜
        "provider": str                 # 데이터 제공자 (선택사항)
    }
}
```

#### 2. 주문 요청 (from Service Agent)
```python
{
    "order_request": {
        "symbol": str,                  # 종목 코드
        "side": str,                    # "BUY" or "SELL"
        "quantity": int,                # 수량
        "price": float,                 # 가격 (None이면 시장가)
        "order_type": str,              # "LIMIT", "MARKET"
        "account_type": str             # "REAL", "VIRTUAL"
    }
}
```

#### 3. 알림 요청 (from Orchestrator)
```python
{
    "notification_request": {
        "type": str,                    # "trading", "system", "balance"
        "message": str,                 # 메시지 내용
        "data": Dict[str, Any],         # 추가 데이터
        "urgency": str                  # "LOW", "MEDIUM", "HIGH"
    }
}
```

### 출력 인터페이스

#### 1. 시장 데이터 (to Data Agent)
```python
{
    "market_data": {
        "symbols": Dict[str, pd.DataFrame],  # 종목별 데이터
        "metadata": {
            "provider": str,                 # 데이터 제공자
            "last_update": datetime,         # 마지막 업데이트
            "data_quality": float,           # 데이터 품질 점수
            "api_usage": Dict[str, int]      # API 사용량
        }
    }
}
```

#### 2. 계좌 정보 (to Strategy Agent)
```python
{
    "account_data": {
        "balance": {
            "cash": float,               # 현금 잔고
            "total_asset": float,        # 총 자산
            "buying_power": float        # 매수 가능 금액
        },
        "holdings": [
            {
                "symbol": str,           # 종목 코드
                "quantity": int,         # 보유 수량
                "avg_price": float,      # 평균 단가
                "current_price": float,  # 현재가
                "market_value": float,   # 시장 가치
                "unrealized_pnl": float  # 미실현 손익
            }
        ],
        "trading_status": {
            "is_market_open": bool,      # 시장 개장 여부
            "last_sync": datetime        # 마지막 동기화 시간
        }
    }
}
```

#### 3. 주문 결과 (to Service Agent)
```python
{
    "order_result": {
        "order_id": str,                 # 주문 ID
        "status": str,                   # "FILLED", "PENDING", "REJECTED"
        "filled_quantity": int,          # 체결 수량
        "filled_price": float,           # 체결 가격
        "remaining_quantity": int,       # 미체결 수량
        "commission": float,             # 수수료
        "timestamp": datetime,           # 처리 시간
        "error_message": str             # 오류 메시지 (있는 경우)
    }
}
```

---

## ⚙️ 설정 파일 연동

### 1. API 자격증명
**파일**: `config/api_credentials.yaml`
```yaml
external_apis:
  alpha_vantage:
    api_key: "encrypted_api_key"
    requests_per_minute: 5
    timeout: 30

  yahoo_finance:
    timeout: 30
    rate_limit: 2000  # per hour

brokers:
  kis:
    real_account:
      app_key: "encrypted_app_key"
      app_secret: "encrypted_app_secret"
      account_no: "encrypted_account"
      url_base: "https://openapi.koreainvestment.com:9443"

    virtual_account:
      app_key: "encrypted_virtual_app_key"
      app_secret: "encrypted_virtual_app_secret"
      account_no: "encrypted_virtual_account"
      url_base: "https://openapivts.koreainvestment.com:29443"

notifications:
  telegram:
    bot_token: "encrypted_bot_token"
    chat_ids: ["encrypted_chat_id"]
    default_parse_mode: "HTML"
```

### 2. 개인 투자 정보
**파일**: `myStockInfo.yaml`
```yaml
user_preferences:
  risk_tolerance: "MODERATE"  # LOW, MODERATE, HIGH
  investment_style: "GROWTH"  # GROWTH, VALUE, DIVIDEND
  preferred_sectors: ["TECH", "HEALTHCARE", "FINANCE"]

watchlist:
  us_stocks: ["AAPL", "GOOGL", "MSFT", "TSLA"]
  etfs: ["SPY", "QQQ", "VTI"]

notification_settings:
  price_alerts: true
  order_confirmations: true
  daily_summary: true
  system_errors: true

trading_preferences:
  default_order_type: "LIMIT"
  auto_limit_adjustment: true
  position_sizing_method: "FIXED_RATIO"
```

---

## 🔄 데이터 플로우

### 1. 시장 데이터 수집 플로우
```
[External APIs] → [Helper Agent] → [Data Agent]
     ↓               ↓               ↓
Alpha Vantage → DataProviderManager → DataFrameGenerator
Yahoo Finance → YFinanceHelper → TechnicalIndicators
```

### 2. 거래 실행 플로우
```
[Service Agent] → [Helper Agent] → [Broker APIs]
     ↓               ↓               ↓
Order Request → BrokerAPIManager → KIS US API
              → Account Sync → Real/Virtual Account
```

### 3. 알림 플로우
```
[Orchestrator] → [Helper Agent] → [Telegram]
     ↓               ↓               ↓
System Events → NotificationService → Users
Trading Signals → TelegramBot → Chat Groups
```

---

## 🚨 제약사항 및 규칙

### 1. 보안 관리
- **API 키 암호화**: 모든 외부 API 키는 암호화하여 저장
- **접근 제한**: myStockInfo.yaml은 Helper Agent만 접근 가능
- **로그 마스킹**: 민감 정보는 로그에 기록하지 않음

### 2. API 사용량 관리
- **Rate Limiting**: 각 API의 사용량 제한 준수
- **Fallback 전략**: 주 API 실패 시 백업 API 자동 전환
- **캐싱**: 중복 요청 최소화를 위한 데이터 캐싱

### 3. 오류 처리
- **재시도 로직**: 네트워크 오류 시 자동 재시도
- **Circuit Breaker**: 연속 실패 시 API 차단
- **알림 발송**: 중요한 오류 발생 시 즉시 알림

---

## 📊 성능 지표

### 1. API 응답 성능
- **시장 데이터 조회**: < 5초 (100종목 기준)
- **현재가 조회**: < 2초 (단일 종목)
- **주문 처리**: < 3초 (단일 주문)

### 2. 가용성
- **API 연결 성공률**: > 99.5%
- **알림 발송 성공률**: > 99.9%
- **데이터 신선도**: < 1분 지연

### 3. 보안 지표
- **API 키 노출 사건**: 0건
- **인증 실패율**: < 0.1%
- **보안 감사 통과율**: 100%

---

## 🔧 개발 및 유지보수

### 1. API 버전 관리
- **Wrapper 패턴**: API 변경에 대한 내부 코드 격리
- **Deprecation 처리**: 구 API 지원 종료 대응
- **Documentation**: API 명세 변경 추적

### 2. 모니터링
- **API 상태 모니터링**: 실시간 API 서비스 상태 확인
- **사용량 추적**: API 쿼터 사용량 모니터링
- **성능 측정**: 응답 시간 및 처리량 추적

### 3. 확장성
- **새 브로커 추가**: 플러그인 방식으로 새 브로커 API 연동
- **다중 시장 지원**: 한국, 일본 등 새로운 시장 추가
- **알림 채널 확장**: 이메일, SMS 등 추가 알림 방식

---

**📝 문서 상태**: 외부 연동 레이어 아키텍처 분석 완료 (2025-09-21)
**다음 업데이트**: 새로운 브로커 API 연동 완료 시