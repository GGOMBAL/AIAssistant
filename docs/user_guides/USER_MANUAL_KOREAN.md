# AI Trading System 사용 매뉴얼

**버전**: 2.0
**작성일**: 2025-10-10
**대상**: 오토트레이딩, 백테스트, 개별종목 데이터 확인

---

## 목차
1. [시스템 개요](#1-시스템-개요)
2. [설치 및 환경 설정](#2-설치-및-환경-설정)
3. [Interactive Orchestrator 사용법](#3-interactive-orchestrator-사용법)
4. [백테스트 실행](#4-백테스트-실행)
5. [개별 종목 데이터 확인](#5-개별-종목-데이터-확인)
6. [오토트레이딩 시스템](#6-오토트레이딩-시스템)
7. [문제 해결](#7-문제-해결)

---

## 1. 시스템 개요

### 1.1 Multi-Agent 아키텍처

본 시스템은 5개의 독립 Agent가 협업하는 구조입니다:

```
Interactive Orchestrator (사용자 인터페이스)
    ↓
UserInputHandler (입력 분석 및 라우팅)
    ↓
├── Helper Agent    : 외부 API 데이터 수집
├── Database Agent  : MongoDB 데이터 관리
├── Strategy Agent  : 매매 시그널 생성
├── Service Agent   : 백테스트 실행
└── RUN Agent       : 파일 실행 및 프로세스 관리
```

### 1.2 주요 기능

- **백테스트**: 과거 데이터로 전략 성과 검증
- **데이터 조회**: MongoDB에서 종목별 OHLCV, 지표, 펀더멘털 데이터 확인
- **시그널 생성**: 전략에 따른 매수/매도 신호 생성
- **오토트레이딩**: 실시간 자동 매매 (현재 백테스트 모드 지원)

---

## 2. 설치 및 환경 설정

### 2.1 사전 요구사항

```bash
# Python 3.12 이상
python --version

# MongoDB 연결 확인
mongo --host localhost --port 27017 -u admin -p wlsaud07
```

### 2.2 필수 패키지 설치

```bash
cd C:\WorkSpace\AIAgentProject\AIAssistant
pip install -r requirements.txt
```

주요 패키지:
- `pymongo`: MongoDB 연결
- `pandas`: 데이터 처리
- `pyyaml`: 설정 파일 관리
- `google-generativeai`: Gemini API (Sub-Agent용)

### 2.3 설정 파일 확인

**myStockInfo.yaml** 파일에서 다음 설정 확인:

```yaml
# MongoDB 연결 정보 (백테스트는 MONGODB_LOCAL 사용)
MONGODB_LOCAL: localhost
MONGODB_NAS: 192.168.55.14    # 백업 전용
MONGODB_PORT: 27017
MONGODB_ID: admin
MONGODB_PW: wlsaud07

# 백테스트 설정
backtest_settings:
  default_mode:
    use_all_symbols: false
    max_symbols: 20
    sample_size: 20

# Orchestrator 설정 (반복 검증)
orchestrator_settings:
  max_iterations: 5
  enable_output_validation: true
  stop_on_success: true
```

---

## 3. Interactive Orchestrator 사용법

### 3.1 실행 방법

```bash
cd C:\WorkSpace\AIAgentProject\AIAssistant
python interactive_orchestrator.py
```

### 3.2 메인 화면

```
================================================================================
                    Interactive Orchestrator v2.1
               Multi-Agent System (Peer-level Architecture)
================================================================================

사용 가능한 명령어:
  - 자연어 입력: 원하는 작업을 자연어로 입력하세요
  - 'status': RUN_AGENT 상태 확인
  - 'exit' 또는 'quit': 종료
  - 'help': 도움말

예시:
  - 'NASDAQ 종목들의 2024-01-01부터 2024-06-30까지 백테스트 실행해줘'
  - 'AAPL, MSFT의 최근 데이터 시그널 생성해줘'
  - 'MongoDB에서 주간 데이터 로드해줘'
  - 'run_backtest_auto.py 파일 실행해줘' (RUN_AGENT 사용)

================================================================================

You:
```

### 3.3 기본 명령어

#### 3.3.1 시스템 상태 확인
```
You: status
```

출력 예시:
```
[RUN_AGENT Status]
  Work Directory: C:\WorkSpace\AIAgentProject\AIAssistant
  Running Processes: 0
  Execution History: 3 items
```

#### 3.3.2 도움말 보기
```
You: help
```

#### 3.3.3 종료
```
You: exit
또는
You: quit
```

---

## 4. 백테스트 실행

### 4.1 기본 백테스트

#### 4.1.1 자연어 요청 (추천)

```
You: NASDAQ 종목 100개로 2024-01-01부터 2024-12-31까지 백테스트 실행해줘
```

시스템이 자동으로:
1. Database Agent가 MongoDB에서 데이터 로드
2. Strategy Agent가 매매 시그널 생성
3. Service Agent가 백테스트 실행
4. 결과 리포트 생성

#### 4.1.2 파일 직접 실행

**방법 A: 직접 실행**
```bash
python main_auto_trade.py
```

**방법 B: RUN Agent를 통한 실행**
```
You: main_auto_trade.py 파일 실행해줘
```

### 4.2 백테스트 설정 변경

**myStockInfo.yaml** 파일 수정:

```yaml
backtest_settings:
  default_mode:
    use_all_symbols: false    # 전체 종목 사용 여부
    max_symbols: 100          # 최대 종목 수
    sample_size: 100          # 샘플 크기

market_specific_configs:
  US:
    backtest_parameters:
      start_date: '2024-01-01'
      end_date: 'auto'        # 또는 '2024-12-31'
      time_frame: D           # D(일봉), W(주봉), M(월봉)
```

### 4.3 백테스트 결과 확인

결과는 다음 위치에 저장됩니다:

```
Report/Backtest/
├── backtest_report_YYYYMMDD_HHMMSS.yaml
└── summary_YYYYMMDD_HHMMSS.yaml
```

**summary 파일 예시**:
```yaml
performance_metrics:
  total_return: 15.23%
  sharpe_ratio: 1.45
  max_drawdown: -12.5%
  total_trades: 125
  win_rate: 58.4%

period:
  start_date: '2024-01-01'
  end_date: '2024-12-31'
  trading_days: 252
```

---

## 5. 개별 종목 데이터 확인

### 5.1 MongoDB 데이터 조회

#### 5.1.1 기본 데이터 로드

```
You: MongoDB에서 AAPL 종목 데이터 로드해줘
```

또는

```
You: NASDAQ 데이터베이스에서 MSFT, GOOGL, AMZN 데이터 가져와줘
```

#### 5.1.2 특정 기간 데이터

```
You: AAPL의 2024년 1월부터 6월까지 일봉 데이터 보여줘
```

### 5.2 기술 지표 확인

```
You: TSLA의 최근 기술지표 계산해줘
```

시스템이 제공하는 지표:
- **이동평균**: SMA20, SMA50, SMA200
- **변동성**: ADR, ATR
- **추세**: Highest52W, Lowest52W
- **상대강도**: RS_4W, RS_12W

### 5.3 시그널 생성

```
You: AAPL, MSFT, GOOGL 종목의 매매 시그널 생성해줘
```

출력 예시:
```
[Strategy Agent Result]
Signals Generated: 3

AAPL:
  Signal: BUY
  Confidence: 0.85
  Entry Price: $182.50
  Target Price: $195.00
  Stop Loss: $175.00

MSFT:
  Signal: HOLD
  Confidence: 0.60
  Current Price: $375.20

GOOGL:
  Signal: SELL
  Confidence: 0.75
  Exit Price: $138.50
```

### 5.4 데이터 통계 확인

```
You: NASDAQ 데이터베이스 통계 보여줘
```

또는

```
You: 전체 종목 수와 데이터 상태 확인해줘
```

---

## 6. 오토트레이딩 시스템

### 6.1 자동 매매 실행 (현재 백테스트 모드)

#### 6.1.1 main_auto_trade.py 사용

```bash
# 직접 실행
python main_auto_trade.py
```

또는

```
# Interactive Orchestrator에서 실행
You: main_auto_trade.py 파일 실행해줘
```

#### 6.1.2 설정 변경

**myStockInfo.yaml** 수정:

```yaml
global_settings:
  DEBUG: true               # 디버그 모드
  BACKTEST_MODE: LIMITED    # LIMITED (500종목) 또는 FULL

market_specific_configs:
  US:
    max_holding_stocks: 10
    std_risk_per_trade: 0.05
    operational_flags:
      buy_new_stocks: true
      enable_pyramiding: true
      enable_half_sell: true
```

### 6.2 실시간 모니터링

```
You: 실시간 포트폴리오 상태 보여줘
```

또는

```
You: 현재 보유 종목과 수익률 확인해줘
```

### 6.3 매매 실행 (향후 기능)

```
You: AAPL 10주 시장가 매수해줘
```

**주의**: 현재는 백테스트 모드만 지원합니다. 실거래는 추가 개발 필요.

---

## 7. 문제 해결

### 7.1 자주 발생하는 오류

#### 7.1.1 MongoDB 연결 실패

**증상**:
```
ERROR: Failed to connect to MongoDB
```

**해결 방법**:
1. MongoDB 서버 실행 확인
2. `myStockInfo.yaml`에서 연결 정보 확인
3. 네트워크 연결 확인

```bash
# MongoDB 연결 테스트
mongo --host localhost --port 27017 -u admin -p wlsaud07
```

#### 7.1.2 데이터 없음

**증상**:
```
WARNING: No data found for symbol AAPL
```

**해결 방법**:
1. MongoDB에 데이터가 있는지 확인
2. 종목 티커가 올바른지 확인 (대문자 사용)
3. 데이터베이스 이름 확인 (NasDataBase_D, NysDataBase_D)

#### 7.1.3 Agent 응답 없음

**증상**:
```
[WARNING] Agent timeout after 60 seconds
```

**해결 방법**:
1. 네트워크 연결 확인
2. Gemini API 키 확인 (`GOOGLE_API_KEY` 환경변수)
3. `orchestrator_settings`의 `max_iterations` 확인

```bash
# Gemini API 키 확인
echo $GOOGLE_API_KEY
```

#### 7.1.4 UnicodeEncodeError (이모지)

**증상**:
```
UnicodeEncodeError: 'cp949' codec can't encode character
```

**해결 방법**:
- 최신 코드는 이모지를 사용하지 않음
- 기존 로그 파일에 이모지가 있으면 무시하고 진행

### 7.2 성능 최적화

#### 7.2.1 백테스트 속도 개선

1. **종목 수 제한**:
```yaml
backtest_settings:
  default_mode:
    max_symbols: 20  # 적은 수로 시작
```

2. **병렬 처리 활성화**:
```yaml
performance_settings:
  parallel_processing: true
  worker_count: 4
```

3. **캐싱 활성화**:
```yaml
optimization:
  caching:
    enabled: true
    cache_duration: 3600
```

#### 7.2.2 메모리 사용량 최적화

```yaml
backtest_settings:
  performance_settings:
    include_trade_history: false  # 상세 이력 비활성화
    include_symbol_performance: true
```

### 7.3 로그 확인

#### 7.3.1 주요 로그 파일

```
logs/
├── auto_trade.log           # 메인 시스템 로그
├── run_agent.log            # RUN Agent 로그
└── orchestrator/
    └── session_*.yaml       # Agent 상호작용 로그
```

#### 7.3.2 로그 레벨 조정

**myStockInfo.yaml**:
```yaml
global_settings:
  DEBUG: true                # 상세 로그
  default_log_level: INFO    # INFO, DEBUG, WARNING, ERROR
```

---

## 8. 고급 기능

### 8.1 커스텀 전략 실행

1. 전략 파일 작성: `project/strategy/my_strategy.py`
2. Interactive Orchestrator에서 요청:
```
You: my_strategy.py 전략으로 백테스트 실행해줘
```

### 8.2 배치 작업

여러 작업을 순차 실행:
```
You: 다음 작업 순서대로 실행해줘
1. NASDAQ 데이터 로드
2. 시그널 생성
3. 백테스트 실행
4. 결과 리포트 생성
```

### 8.3 LLM Router 활용

Sub-Agent는 Claude 3.5 Sonnet을 사용합니다:

```bash
# Router 상태 확인
curl http://localhost:3000/api/health

# 사용 가능한 모델 확인
curl http://localhost:3000/api/models
```

---

## 9. 빠른 시작 가이드

### 9.1 처음 사용자 (5분 안에 백테스트)

```bash
# 1. 프로젝트 디렉토리로 이동
cd C:\WorkSpace\AIAgentProject\AIAssistant

# 2. Interactive Orchestrator 실행
python interactive_orchestrator.py

# 3. 백테스트 실행 (자연어 입력)
You: NASDAQ 종목 20개로 최근 1년간 백테스트 실행해줘

# 4. 결과 확인
You: 백테스트 결과 요약 보여줘
```

### 9.2 개별 종목 분석 (3분)

```bash
# 1. Interactive Orchestrator 실행
python interactive_orchestrator.py

# 2. 종목 데이터 로드
You: AAPL, MSFT, TSLA 데이터 로드해줘

# 3. 시그널 생성
You: 이 종목들의 매매 시그널 생성해줘

# 4. 결과 확인
(자동으로 출력됨)
```

---

## 10. 참고 자료

### 10.1 문서

- **아키텍처**: `docs/architecture/ARCHITECTURE_OVERVIEW.md`
- **인터페이스**: `docs/INTERFACE_SPECIFICATION.md`
- **Agent 매뉴얼**: `docs/AGENT_INTERFACES.md`

### 10.2 설정 파일

- **메인 설정**: `myStockInfo.yaml`
- **Agent 모델**: `config/agent_model.yaml`
- **Router 설정**: `llm-router/router_config.json`

### 10.3 예제 스크립트

```
Test/
├── test_iteration_system.py    # 반복 검증 테스트
├── verify_5_agents.py           # Agent 설정 확인
└── check_agents.py              # Agent 구성 확인
```

---

## 지원 및 문의

문제 발생 시:
1. 로그 파일 확인
2. GitHub Issues 등록
3. 문서 참조

**버전**: 2.0
**최종 업데이트**: 2025-10-10
