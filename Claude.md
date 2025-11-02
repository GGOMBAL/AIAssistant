# Claude AI Assistant - 핵심 규칙 (Quick Reference)

**프로젝트명**: AI Assistant Multi-Agent Trading System
**버전**: 3.1 (Stepped Trailing Stop & Feature Updates)
**최종 업데이트**: 2025-11-03

---

## 🚨 필수 규칙 (항상 기억)

### 1. Multi-Agent 시스템

이 프로젝트는 **여러개의 SubAgent를 연결하여 협업하는 시스템**입니다.

```
RUN AGENT (최상위 실행 관리자)
    ↓
Orchestrator Agent (작업 분배 및 조정)
    ↓
├── Helper Agent (외부 API 데이터 수집)
├── Database Agent (MongoDB 데이터 관리)
├── Strategy Agent (시장별 매매신호 생성)
├── Service Agent (백테스트 실행, 포트폴리오 관리)
└── Report Agent (거래 분석 및 리포팅)
```

**상세**: `docs/rules/AGENT_COLLABORATION.md`

---

### 2. 파일 접근 권한

- **읽기**: 모든 Agent가 모든 Layer 읽기 가능 ✅
- **쓰기**: 담당 Layer만 수정 가능 🔐
- **인터페이스**: Orchestrator 승인 필요 🔐

| Agent | 담당 Layer | 수정 권한 |
|-------|-----------|----------|
| Helper Agent | `project/Helper/` | ✅ |
| Database Agent | `project/database/`, `project/indicator/` | ✅ |
| Strategy Agent | `project/strategy/` | ✅ |
| Service Agent | `project/service/` | ✅ |
| Report Agent | `project/reporting/` | ✅ |
| Orchestrator | 모든 인터페이스 | ✅ 승인 권한 |

**상세**: `docs/rules/FILE_PERMISSIONS.md`

---

### 3. MongoDB 사용 규칙

#### 핵심 원칙:
- **백테스트/오토트레이딩**: `MONGODB_LOCAL` 사용 필수
- **DataFrame Date 인덱스**: 모든 DataFrame은 Date를 인덱스로 설정

```python
# ✅ 올바른 예
db = MongoDBOperations(db_address="MONGODB_LOCAL")

# DataFrame Date 인덱스 자동 설정
df = db.execute_query(db_name="NasDataBase_D", collection_name="AAPL")
# df.index = DatetimeIndex(['2024-01-02', '2024-01-03', ...])
```

**상세**: `docs/rules/MONGODB_RULES.md`

---

### 4. 백테스트 vs 트레이딩 모드

#### 핵심 차이점:
- **백테스트 (is_backtest=True)**: D-1 데이터로 Highest 계산 (미래 참조 방지)
- **트레이딩 (is_backtest=False)**: 당일 데이터 포함

```python
# 백테스트 모드
df['Highest_1M'] = df['Dhigh'].shift(1).rolling(20).max()  # D-1 데이터

# 트레이딩 모드
df['Highest_1M'] = df['Dhigh'].rolling(20).max()  # 당일 포함
```

**상세**: `docs/rules/BACKTEST_VS_TRADING.md`

---

### 5. 코드 품질 기준

#### 필수 준수:
- **파일 라인 수**: 1000줄 목표, 1500줄 최대
- **이모지 사용 금지**: Python 코드, 로그, 주석에서 금지 (cp949 인코딩 문제)
- **인터페이스 문서**: 모든 Layer는 인터페이스 문서(MD) 필수 작성

```python
# ❌ 잘못된 예
print("✅ Backtest completed!")

# ✅ 올바른 예
print("[OK] Backtest completed!")
```

**상세**: `docs/rules/CODE_QUALITY.md`

---

### 6. 핵심 기능

#### 6.1. Stepped Trailing Stop (단계별 손절가 관리)

**일반 트레일링 스탑과의 차이점**:
- 일반: 현재가 대비 고정 % 버퍼 유지
- Stepped: 수익 단위별 단계적 보호 구간

**로직**:
```python
profit_units = int((current_profit) / RISK)  # RISK = 5%

if profit_units < 1:
    losscut = entry_price * 0.97  # -3% 고정
else:
    losscut = entry_price * (1 + (profit_units - 1) * RISK)
```

**예시 테이블** (Entry=$150, RISK=5%):

| 수익률 | Units | 손절가 | 진입가 대비 |
|--------|-------|--------|------------|
| 0~4.99% | 0 | $145.50 | -3% |
| 5~9.99% | 1 | $150.00 | 0% |
| 10~14.99% | 2 | $157.50 | +5% |
| 15~19.99% | 3 | $165.00 | +10% |

**적용 범위**: 백테스트 & 오토트레이딩 모두

**관련 파일**:
- `project/strategy/position_manager.py`: PositionManager.calc_losscut_price()
- `project/service/daily_backtest_service.py`: _calculate_refer_losscut_price()

#### 6.2. Config 파일 통합

**사용 파일**: `config/strategy_signal_config.yaml` (단일 파일 통합)

**주요 설정**:
```yaml
backtest:
  initial_cash: 100000000.0  # 100M (1억원)
  std_risk: 0.05             # RISK 5%
  init_risk: 0.03            # 최소 손절 -3%
```

**삭제된 파일**:
- `config/signal_config.yaml` (미사용 제안서)
- `config/staged_pipeline_config.yaml` (strategy_signal_config.yaml로 통합)

#### 6.3. Signal Timeline 필터 정보

매매 신호 후보가 필터링될 때 **왜 필터되었는지** Description에 표시:

```
[FILTERED] RS=65 (Need >=70), Below SMA20(174.25)
[OK] All conditions passed
```

**적용 위치**: `main_auto_trade.py` - Signal Timeline 출력 부분

#### 6.4. 마켓 시간 체크 (Auto-Trading)

**기능**: 주말 또는 마켓 클로즈 시 WebSocket 자동 종료

**체크 조건**:
- 주말 (토,일) 체크
- 미국 동부시간 기준 09:30~16:00 체크

**적용 위치**: `main_auto_trade.py` - is_market_open() 함수

---

## 📚 인터페이스 규약

각 Layer는 정의된 인터페이스 준수 필수:

| Layer | 인터페이스 문서 | 담당 Agent |
|-------|---------------|-----------|
| Strategy | `docs/interfaces/STRATEGY_LAYER_INTERFACE.md` | Strategy Agent |
| Service | `docs/interfaces/SERVICE_LAYER_INTERFACE.md` | Service Agent |
| Indicator | `docs/interfaces/INDICATOR_LAYER_INTERFACE.md` | Database Agent |
| Database | `docs/interfaces/DATABASE_LAYER_INTERFACE.md` | Database Agent |
| Helper | `docs/interfaces/HELPER_LAYER_INTERFACE.md` | Helper Agent |
| Report | `docs/interfaces/REPORT_LAYER_INTERFACE.md` | Report Agent |

---

## 🗂️ 문서 체계

### 규칙 문서 (`docs/rules/`)
- **AGENT_COLLABORATION.md**: Agent 협업 규칙
- **FILE_PERMISSIONS.md**: 파일 접근 권한
- **CODE_QUALITY.md**: 코드 품질 기준
- **MONGODB_RULES.md**: MongoDB 사용 규칙
- **BACKTEST_VS_TRADING.md**: 백테스트 vs 트레이딩

### 인터페이스 문서 (`docs/interfaces/`)
- Layer 간 데이터 인터페이스 명세
- 입출력 포맷 정의

### 모듈 문서 (`docs/modules/`)
- Layer별 모듈 설명
- 사용법 및 예제

### 아키텍처 문서 (`docs/architecture/`)
- 시스템 아키텍처 개요
- 데이터 흐름 다이어그램

---

## ⚡ 작업 시작 전 체크리스트

### 필수 확인 사항:
- [ ] **담당 Agent 확인** - 내가 이 파일을 수정할 권한이 있는가?
- [ ] **파일 수정 권한 확인** - `docs/rules/FILE_PERMISSIONS.md` 참조
- [ ] **관련 인터페이스 문서 확인** - `docs/interfaces/` 참조
- [ ] **MongoDB 서버 설정 확인** - MONGODB_LOCAL 사용 중인가?

### 작업 유형별 참조 문서:

| 작업 유형 | 참조 문서 |
|----------|----------|
| Agent 협업 | `docs/rules/AGENT_COLLABORATION.md` |
| 파일 수정 | `docs/rules/FILE_PERMISSIONS.md` |
| 코드 작성 | `docs/rules/CODE_QUALITY.md` |
| MongoDB 작업 | `docs/rules/MONGODB_RULES.md` |
| 백테스트 개발 | `docs/rules/BACKTEST_VS_TRADING.md` |
| 인터페이스 변경 | `docs/interfaces/{LAYER}_INTERFACE.md` |

---

## 🎯 작업 완료 후 체크리스트

### 필수 확인:
- [ ] **코드 품질 기준 충족** - 1500줄 이하, 이모지 없음
- [ ] **인터페이스 문서 업데이트** - 변경사항 반영
- [ ] **테스트 실행** - `Test/` 폴더에 테스트 파일 작성
- [ ] **관련 Agent에게 통보** - 인터페이스 변경 시

---

## 🏗️ 프로젝트 구조 (간략)

```
# 최상위 실행
run_agent.py                   # RUN AGENT
main_auto_trade.py             # 통합 메인 실행 파일

# Agent 및 Orchestrator
agents/                        # Agent 폴더
orchestrator/                  # Orchestrator

# Project Layers
project/
├── Helper/                    # Helper Layer
├── database/                  # Database Layer
├── indicator/                 # Indicator Layer
├── strategy/                  # Strategy Layer
├── service/                   # Service Layer
├── reporting/                 # Report Layer
└── router/                    # Agent Routers

# 문서
docs/
├── rules/                     # 프로젝트 규칙 ⭐
├── interfaces/                # Layer 인터페이스
├── modules/                   # 모듈 설명
└── architecture/              # 아키텍처

# 테스트 및 설정
Test/                          # 모든 테스트 파일
config/                        # 설정 파일들
```

---

## 📞 문제 발생 시

### 1. Agent 협업 이슈
- 권한 확인: `docs/rules/FILE_PERMISSIONS.md`
- 협업 규칙: `docs/rules/AGENT_COLLABORATION.md`

### 2. 코드 작성 이슈
- 품질 기준: `docs/rules/CODE_QUALITY.md`
- 인터페이스: `docs/interfaces/`

### 3. 데이터베이스 이슈
- MongoDB 규칙: `docs/rules/MONGODB_RULES.md`
- 백테스트 모드: `docs/rules/BACKTEST_VS_TRADING.md`

---

## 📖 주요 변경 이력

### 2025-11-03 (v3.1)
- **Stepped Trailing Stop 구현**: 단계별 손절가 관리 시스템 (백테스트 & 오토트레이딩)
- **Config 파일 통합**: strategy_signal_config.yaml로 통합 (단일 설정 파일)
- **Signal Timeline 개선**: 필터 조건 상세 정보 표시
- **마켓 시간 체크**: 주말/마켓 클로즈 시 WebSocket 자동 종료
- **백테스트 초기자본**: 100M (1억원) 설정
- **RISK 파라미터 정정**: 10% → 5% (1 unit = 5%)

### 2025-10-21 (v3.0)
- 문서 분산 구조로 리팩토링
- 핵심 규칙만 CLAUDE.md에 유지
- 상세 규칙은 `docs/rules/`로 분리

### 2025-10-18 (v2.6)
- MongoDB Date 인덱스 규칙 추가
- 백테스트 vs 트레이딩 모드 구분 명확화

### 2025-10-11 (v2.5)
- MongoDB MONGODB_LOCAL 사용 규칙 추가

### 2025-10-09 (v2.4)
- Orchestrator-driven Workflow 추가
- Plan 폴더 구조 정의

---

**🚨 중요: 이 규칙은 모든 Claude 작업 세션에서 반드시 로드하고 적용해야 합니다.**

**규칙 버전**: 3.1 (Stepped Trailing Stop & Feature Updates)
**최종 업데이트**: 2025-11-03
