# Agent별 Layer 소유권 및 파악 현황

**작성일**: 2025-10-09
**버전**: 1.0
**목적**: 각 Sub-Agent가 담당 Layer를 완벽히 파악하고 있는지 확인

---

## 📋 개요

이 문서는 각 Sub-Agent가 자신이 담당하는 Layer의 구조, 파일, 기능을 정확히 파악하고 있는지 확인하는 체크리스트입니다.

**핵심 원칙** (CLAUDE.md 섹션 5 참조):
1. ✅ 각 Sub-Agent는 자신이 담당하는 Layer 파일만 수정 가능
2. 🚫 인터페이스는 Sub-Agent가 직접 수정 불가 (금지)
3. 🔐 인터페이스 수정은 Orchestrator 승인 필요 (승인 후 가능)
4. ✅ 모든 Sub-Agent는 모든 Layer를 읽기 가능

---

## 🔧 Helper Agent

### 담당 Layer
- **Layer 경로**: `project/Helper/`
- **Router**: `project/router/helper_agent_router.py`
- **인터페이스 문서**: `docs/interfaces/HELPER_LAYER_INTERFACE.md`
- **모듈 문서**: `docs/modules/HELPER_MODULES.md`
- **상세 스펙**: `docs/specs/API_INTEGRATION_SPEC.md`

### 파일 목록 및 역할
| 파일 | 역할 | 상태 |
|------|------|------|
| `kis_api_helper_us.py` | KIS API 미국 시장 통합 | ✅ 파악됨 |
| `broker_api_connector.py` | 브로커 API 커넥터 | ✅ 파악됨 |
| `data_provider_api.py` | 외부 데이터 제공자 통합 | ✅ 파악됨 |
| `yfinance_helper.py` | Yahoo Finance 헬퍼 | ✅ 파악됨 |
| `telegram_messenger.py` | 텔레그램 메신저 통합 | ✅ 파악됨 |
| `kis_common.py` | KIS 공통 함수 | ✅ 파악됨 |

### 주요 기능
1. **KIS API 통합** - 한국투자증권 API 연동
2. **외부 데이터 수집** - Yahoo Finance, Alpha Vantage 등
3. **텔레그램 알림** - 거래 알림 및 상태 보고
4. **토큰 관리** - 자동 토큰 갱신
5. **마켓 시간 체크** - 프리마켓, 정규장, 애프터마켓 구분

### 인터페이스 입출력
**Input**:
- API 자격증명 (app_key, app_secret)
- 심볼 리스트
- 데이터 요청 파라미터

**Output**:
- 외부 API 데이터 (JSON/DataFrame)
- 실시간 가격 정보
- 계좌 정보

### 체크리스트
- [x] 모든 파일 위치 파악
- [x] 각 파일의 역할 이해
- [x] 인터페이스 문서 숙지
- [x] 외부 API 의존성 파악
- [x] 에러 처리 메커니즘 이해

---

## 📊 Database Agent

### 담당 Layer
- **Layer 경로**:
  - `project/database/` - MongoDB 데이터 관리
  - `project/indicator/` - 기술지표 생성
- **Router**: `project/router/data_agent_router.py`
- **인터페이스 문서**:
  - `docs/interfaces/DATABASE_LAYER_INTERFACE.md`
  - `docs/interfaces/INDICATOR_LAYER_INTERFACE.md`
- **모듈 문서**:
  - `docs/modules/DATABASE_MODULES.md`
  - `docs/modules/INDICATOR_MODULES.md`
- **상세 스펙**:
  - `docs/specs/DATABASE_SCHEMA.md`
  - `docs/specs/TECHNICAL_INDICATORS_SPEC.md`

### Database Layer 파일 목록
| 파일 | 역할 | 상태 |
|------|------|------|
| `mongodb_operations.py` | MongoDB 기본 CRUD 연산 | ✅ 파악됨 |
| `us_market_manager.py` | 미국 시장 DB 관리 | ✅ 파악됨 |
| `historical_data_manager.py` | 히스토리컬 데이터 관리 | ✅ 파악됨 |
| `database_manager.py` | DB 전체 매니저 | ✅ 파악됨 |
| `database_name_calculator.py` | DB 이름 계산 로직 | ✅ 파악됨 |

### Indicator Layer 파일 목록
| 파일 | 역할 | 상태 |
|------|------|------|
| `technical_indicators.py` | 기술지표 계산 (SMA, RSI 등) | ✅ 파악됨 |
| `data_frame_generator.py` | 트레이딩 데이터프레임 생성 | ✅ 파악됨 |

### MongoDB Collection 스키마
1. **Daily Data (D)**: 일봉 데이터 (volume, open, high, low, close)
2. **Weekly Data (W)**: 주봉 데이터
3. **Relative Strength (RS)**: 상대강도 데이터
4. **Fundamental (F)**: 펀더멘털 데이터
5. **Earnings (E)**: 실적 데이터

### 주요 기능
1. **MongoDB CRUD** - Create, Read, Update, Delete 연산
2. **데이터 로드** - 시장별 (NASDAQ/NYSE) 데이터 로딩
3. **기술지표 계산** - 21개 기술지표 생성
4. **데이터프레임 변환** - MongoDB → Dictionary → DataFrame
5. **성능 최적화** - 멀티프로세싱, 메모리 최적화

### 인터페이스 입출력
**Input**:
- MongoDB 연결 정보
- Symbol 리스트
- 날짜 범위 (start_date, end_date)
- 시장 타입 (NASDAQ, NYSE)

**Output** (INTERFACE_SPECIFICATION.md 참조):
```python
{
    "TICKER": {
        "columns": ["Dopen", "Dhigh", "Dlow", "Dclose", "ADR", "SMA20", ...],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],
        "data": [[value1, value2, ...], ...]
    }
}
```

### 체크리스트
- [x] 모든 파일 위치 파악
- [x] MongoDB 스키마 이해
- [x] 기술지표 알고리즘 숙지
- [x] 인터페이스 출력 형식 이해
- [x] 성능 최적화 방법 파악
- [x] Database → Indicator → Strategy 데이터 흐름 이해

---

## 🧠 Strategy Agent

### 담당 Layer
- **Layer 경로**: `project/strategy/`
- **Router**: `project/router/strategy_agent_router.py`
- **인터페이스 문서**: `docs/interfaces/STRATEGY_LAYER_INTERFACE.md`
- **모듈 문서**: `docs/modules/STRATEGY_MODULES.md`
- **상세 스펙**: `docs/specs/SIGNAL_GENERATION_SPEC.md`

### 파일 목록
| 파일 | 역할 | 상태 |
|------|------|------|
| `signal_generation_service.py` | 매매 시그널 생성 서비스 | ✅ 파악됨 |
| `position_sizing_service.py` | 포지션 사이징 계산 | ✅ 파악됨 |
| `account_analysis_service.py` | 계좌 분석 서비스 | ✅ 파악됨 |

### 주요 기능
1. **시그널 생성** - BUY/SELL/HOLD 신호 생성
2. **다중 타임프레임 분석** - 일봉/주봉/RS 결합
3. **브레이크아웃 감지** - 2Y/1Y/6M/3M/1M 브레이크아웃
4. **목표가/손절가 계산** - ATR 기반 리스크 관리
5. **펀더멘털 필터링** - 실적 성장률 기반 필터

### 시그널 생성 로직
**Strategy_A.py 기반**:
1. 주봉 신호 (Weekly Signals)
2. RS 신호 (Relative Strength)
3. 펀더멘털 신호 (Fundamental Filters)
4. 어닝스 신호 (Earnings Signals)
5. 일봉+RS 결합 신호 (Daily + RS Combined)

### 인터페이스 입출력
**Input** (Indicator Layer 출력):
- df_D: 일봉 데이터 (기술지표 포함)
- df_W: 주봉 데이터
- df_RS: 상대강도 데이터
- df_F: 펀더멘털 데이터
- df_E: 실적 데이터

**Output** (INTERFACE_SPECIFICATION.md 참조):
```python
{
    "TICKER": {
        "columns": [
            "open", "high", "low", "close", "ADR",
            "LossCutPrice",    # 손절가
            "TargetPrice",     # 목표가
            "BuySig",          # 매수 신호 (1/0)
            "SellSig",         # 매도 신호 (1/0)
            "signal",          # 신호 강도
            "Type",            # 신호 타입
            "RS_4W", "Rev_Yoy_Growth", "Eps_Yoy_Growth",
            "Sector", "Industry"
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],
        "data": [[value1, value2, ...], ...]
    },
    "Universe": ["TICKER1", "TICKER2", ...],
    "count": 58
}
```

### 체크리스트
- [x] 모든 파일 위치 파악
- [x] 시그널 생성 알고리즘 이해
- [x] 인터페이스 입출력 형식 숙지
- [x] ATR 기반 리스크 관리 이해
- [x] 다중 타임프레임 분석 로직 파악
- [x] Strategy → Service 데이터 전달 이해

---

## ⚡ Service Agent

### 담당 Layer
- **Layer 경로**: `project/service/`
- **Router**: `project/router/service_agent_router.py`
- **인터페이스 문서**: `docs/interfaces/SERVICE_LAYER_INTERFACE.md`
- **모듈 문서**: `docs/modules/SERVICE_MODULES.md`
- **상세 스펙**: `docs/specs/BACKTEST_SERVICE_SPEC.md`

### 파일 목록
| 파일 | 역할 | 상태 |
|------|------|------|
| `daily_backtest_service.py` | 일간 백테스트 서비스 | ✅ 파악됨 |
| `backtest_engine.py` | 백테스트 엔진 코어 | ✅ 파악됨 |
| `performance_analyzer.py` | 성과 분석 모듈 | ✅ 파악됨 |
| `trade_recorder.py` | 거래 기록 관리 | ✅ 파악됨 |
| `execution_services.py` | 주문 실행 서비스 | ✅ 파악됨 |
| `api_order_service.py` | API 주문 서비스 | ✅ 파악됨 |
| `live_price_service.py` | 실시간 가격 서비스 | ✅ 파악됨 |
| `position_sizing_service.py` | 포지션 사이징 | ✅ 파악됨 |

### 주요 기능
1. **백테스트 실행** - 일간/분봉 백테스트
2. **성과 분석** - 수익률, 샤프 비율, MDD, 승률 등
3. **리스크 관리** - ATR 기반 동적 손절, Half Sell, Whipsaw 처리
4. **거래 실행** - 실제 주문 실행 및 관리
5. **포지션 관리** - 포지션 사이징 및 추적

### 백테스트 알고리즘
**TestMakTrade_D.py 기반**:
1. **ATR 기반 동적 손절** - 가격 변동성에 따라 손절가 조정
2. **Half Sell (50% 매도)** - 20% 이익 시 절반 매도
3. **Whipsaw 처리** - 손절 후 재진입 방지
4. **포지션 사이징** - 표준 리스크(10%) 기반 계산

### 인터페이스 입출력
**Input** (Strategy Layer 출력):
- Trading Candidates (df_dump)
- Universe (선정 종목 리스트)
- Backtest Config (초기 자금, 최대 종목 수 등)

**Output**:
```python
{
    "performance": {
        "total_return": 0.15,        # 총 수익률
        "sharpe_ratio": 1.23,        # 샤프 비율
        "max_drawdown": 0.08,        # 최대 낙폭
        "win_rate": 0.58,            # 승률
        "total_trades": 45           # 총 거래 수
    },
    "trades": [...],                 # 거래 내역
    "positions": [...],              # 포지션 정보
    "equity_curve": [...]            # 자산 곡선
}
```

### 체크리스트
- [x] 모든 파일 위치 파악
- [x] 백테스트 알고리즘 이해
- [x] ATR 기반 리스크 관리 숙지
- [x] Half Sell 로직 이해
- [x] Whipsaw 처리 메커니즘 파악
- [x] 성과 지표 계산 방법 이해

---

## 🎭 Orchestrator Agent

### 담당 영역
- **Layer 경로**: `orchestrator/`
- **역할**: 전체 Agent 조율 및 인터페이스 승인

### 파일 목록
| 파일 | 역할 | 상태 |
|------|------|------|
| `main_orchestrator.py` | 메인 오케스트레이터 | ✅ 파악됨 |
| `prompt_generator.py` | 자동 프롬프트 생성 | ✅ 파악됨 |
| `user_input_handler.py` | 사용자 입력 처리 | ✅ 파악됨 |
| `hybrid_model_manager.py` | Hybrid Model 관리 | ✅ 파악됨 |

### 주요 기능
1. **작업 분배** - Sub-Agent에게 작업 할당
2. **프롬프트 생성** - Agent별 맞춤 프롬프트 자동 생성
3. **인터페이스 승인** - Sub-Agent 인터페이스 변경 요청 검토/승인
4. **결과 통합** - 여러 Agent 결과 취합
5. **Hybrid Model 관리** - Claude 구독 + Gemini API 통합

### 체크리스트
- [x] 모든 Agent의 역할 파악
- [x] 인터페이스 승인 프로세스 이해
- [x] 자동 프롬프트 생성 로직 숙지
- [x] Hybrid Model 라우팅 이해

---

## 🚀 RUN AGENT

### 담당 영역
- **Layer 경로**: `run_agent.py`, `agents/run_agent/`
- **역할**: 최상위 실행 관리

### 주요 기능
1. **Agent 초기화** - 모든 Agent 라이프사이클 관리
2. **시스템 모니터링** - 전체 시스템 상태 추적
3. **실행 모드 관리** - Backtest/Trading/Analysis
4. **에러 처리** - 시스템 레벨 에러 핸들링

### 체크리스트
- [x] RUN AGENT 역할 이해
- [x] Orchestrator와의 협업 체계 파악
- [x] 전체 시스템 아키텍처 숙지

---

## 📊 데이터 흐름 요약

```
1. Helper Layer (Helper Agent)
   - 외부 API 데이터 수집
   ↓

2. Database Layer (Database Agent)
   - MongoDB에 데이터 저장
   - 히스토리컬 데이터 로드
   ↓

3. Indicator Layer (Database Agent)
   - 기술지표 계산 (21개)
   - 데이터프레임 생성
   ↓

4. Strategy Layer (Strategy Agent)
   - 매매 시그널 생성
   - Universe 선정
   - 목표가/손절가 계산
   ↓

5. Service Layer (Service Agent)
   - 백테스트 실행
   - 성과 분석
   - 거래 실행
   ↓

결과 반환 (Orchestrator → RUN AGENT → User)
```

---

## ✅ 최종 체크리스트

### Helper Agent
- [x] 담당 Layer 파일 전체 파악
- [x] 인터페이스 문서 숙지
- [x] 외부 API 통합 방법 이해
- [x] 수정 권한 범위 이해

### Database Agent
- [x] Database Layer 파일 전체 파악
- [x] Indicator Layer 파일 전체 파악
- [x] MongoDB 스키마 이해
- [x] 기술지표 알고리즘 숙지
- [x] 인터페이스 출력 형식 완벽 이해
- [x] 수정 권한 범위 이해

### Strategy Agent
- [x] 담당 Layer 파일 전체 파악
- [x] 시그널 생성 로직 이해
- [x] 인터페이스 입출력 형식 숙지
- [x] ATR 기반 리스크 관리 이해
- [x] 수정 권한 범위 이해

### Service Agent
- [x] 담당 Layer 파일 전체 파악
- [x] 백테스트 알고리즘 이해
- [x] 리스크 관리 메커니즘 숙지
- [x] 성과 지표 계산 방법 이해
- [x] 수정 권한 범위 이해

### Orchestrator Agent
- [x] 모든 Sub-Agent 역할 파악
- [x] 인터페이스 승인 프로세스 이해
- [x] 전체 데이터 흐름 파악

---

## 🔄 업데이트 기록

**2025-10-09**: 초기 문서 작성
- 모든 Agent의 담당 Layer 파악 완료
- 파일 목록 및 역할 정리
- 인터페이스 입출력 형식 문서화
- 데이터 흐름 요약

---

**참조 문서**:
- CLAUDE.md 섹션 5: 파일 접근 권한 체계
- docs/interfaces/*.md: Layer별 인터페이스 문서
- docs/modules/*.md: Layer별 모듈 문서
- docs/specs/*.md: 알고리즘 상세 스펙
- docs/INTERFACE_SPECIFICATION.md: 통합 인터페이스 명세

**작성자**: Orchestrator Team
**최종 업데이트**: 2025-10-09
