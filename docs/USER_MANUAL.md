# Multi-Agent Trading System 사용자 매뉴얼

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [설치 및 설정](#설치-및-설정)
4. [사용 방법](#사용-방법)
5. [동작 원리](#동작-원리)
6. [설정 파일 관리](#설정-파일-관리)
7. [문제 해결](#문제-해결)
8. [성능 최적화](#성능-최적화)

---

## 🎯 시스템 개요

**Multi-Agent Trading System**은 NasDataBase와 NysDataBase를 통합하여 백테스트를 수행하는 지능형 트레이딩 시스템입니다.

### 주요 특징
- **Multi-Agent 협업**: 5개의 전문화된 에이전트가 협력
- **시장별 차별화 전략**: NASDAQ 성장주 vs NYSE 가치주
- **실시간 리스크 관리**: 포지션 크기 조절 및 손익 관리
- **MongoDB 통합**: 15,000+ 종목 실제 데이터 활용
- **완전 자동화**: 설정부터 결과 분석까지 원클릭

### 시스템 성능
- **처리 속도**: 15,000+ 종목 데이터를 2초 이내 로딩
- **백테스트 실행**: 1년간 데이터 0.05초 처리
- **메모리 효율성**: 최적화된 데이터 구조로 안정적 실행

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                        │
│          multi_agent_trading_system.py                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Orchestrator Agent                            │
│              (시스템 총괄 관리)                             │
└─┬─────────┬─────────┬─────────┬─────────────────────────────┘
  │         │         │         │
  ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌─────────┐
│ Data  │ │Strategy│ │Service│ │ Helper  │
│ Agent │ │ Agent │ │ Agent │ │ Agent   │
└─┬─────┘ └─┬─────┘ └─┬─────┘ └─┬───────┘
  │         │         │         │
  ▼         ▼         ▼         ▼
┌─────────────────────────────────────────┐
│            MongoDB Database             │
│  ┌─────────────┐ ┌─────────────┐       │
│  │NasDataBase_D│ │NysDataBase_D│       │
│  │ 8,878 종목  │ │ 6,235 종목  │       │
│  └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────┘
```

### 에이전트별 역할

#### 🎭 Orchestrator Agent (orchestrator_agent.py)
- **역할**: 전체 시스템 총괄 관리
- **기능**:
  - 워크플로우 조정 및 작업 분배
  - 에이전트간 통신 중재
  - 결과 통합 및 최종 리포트 생성
  - 시스템 상태 모니터링

#### 📊 Data Agent (data_agent.py)
- **역할**: 데이터 수집 및 전처리
- **기능**:
  - MongoDB에서 NasDataBase_D, NysDataBase_D 로딩
  - 기술지표 계산 (MA, RSI, Bollinger Bands, MACD, etc.)
  - 데이터 품질 검증 및 정제
  - 시장별 데이터 분리 관리

#### 🧠 Strategy Agent (strategy_agent.py)
- **역할**: 매매 신호 생성
- **기능**:
  - 시장별 차별화 전략 적용
  - NASDAQ: 빠른 성장주 전략 (5일/20일 MA)
  - NYSE: 안정적 가치주 전략 (10일/50일 MA)
  - 신호 품질 평가 및 필터링

#### ⚡ Service Agent (service_agent.py)
- **역할**: 백테스트 실행 및 분석
- **기능**:
  - 시장별 분리된 포트폴리오 관리
  - 실시간 리스크 모니터링
  - 손익 계산 및 성과 분석
  - 거래 통계 생성

#### 🔧 Helper Agent (helper_agent.py)
- **역할**: 시스템 리소스 관리
- **기능**:
  - MongoDB 연결 관리
  - 설정 파일 자동 생성 및 로딩
  - 시스템 상태 검증
  - 로깅 및 모니터링

---

## 🛠️ 설치 및 설정

### 1. 시스템 요구사항

```bash
# Python 버전
Python 3.8 이상

# 필수 라이브러리
pip install pymongo pandas numpy pyyaml

# 데이터베이스
MongoDB (로컬 또는 원격)
```

### 2. 프로젝트 구조

```
AIAssistant/
├── Project/                          # 메인 에이전트 디렉토리
│   ├── multi_agent_trading_system.py # 통합 실행 파일
│   ├── orchestrator_agent.py         # 오케스트레이터
│   ├── data_agent.py                 # 데이터 에이전트
│   ├── strategy_agent.py             # 전략 에이전트
│   ├── service_agent.py              # 서비스 에이전트
│   └── helper_agent.py               # 헬퍼 에이전트
├── config/                           # 설정 파일 디렉토리
│   ├── api_credentials.yaml          # API 인증 정보
│   ├── broker_config.yaml            # 브로커 설정
│   ├── agent_model.yaml              # 에이전트 모델 설정
│   └── risk_management.yaml          # 리스크 관리 설정
└── docs/                             # 문서 디렉토리
    └── USER_MANUAL.md                # 이 매뉴얼
```

### 3. MongoDB 설정

#### 로컬 MongoDB 설치
```bash
# Windows
# MongoDB Community Server 다운로드 및 설치
# https://www.mongodb.com/try/download/community

# 서비스 시작
net start MongoDB

# 연결 확인
mongo --host localhost:27017
```

#### 데이터베이스 구조 확인
```javascript
// MongoDB 쉘에서 실행
show dbs                    // 모든 데이터베이스 확인
use NasDataBase_D          // NASDAQ 데이터베이스 선택
show collections           // 종목 컬렉션 확인 (각 종목이 컬렉션)
db.AAPL.findOne()          // AAPL 데이터 샘플 확인
```

---

## 🚀 사용 방법

### 1. 기본 실행 (자동 모드)

```bash
# 프로젝트 디렉토리로 이동
cd C:\WorkSpace\AIAgentProject\AIAssistant\Project

# 자동 모드 실행 (기본 설정 사용)
python multi_agent_trading_system.py --auto
```

**자동 모드 기본 설정:**
- 백테스트 기간: 2023-01-01 ~ 2023-12-31
- NASDAQ 종목: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX
- NYSE 종목: JPM, BAC, WMT, JNJ, PG, KO, DIS, IBM

### 2. 대화형 모드 (사용자 정의)

```bash
# 대화형 모드 실행
python multi_agent_trading_system.py
```

**대화형 모드에서 설정 가능한 항목:**
```
백테스트 기간 설정:
시작일 (기본값: 2023-01-01): 2024-01-01
종료일 (기본값: 2023-12-31): 2024-12-31

테스트 종목 설정:
NASDAQ 종목 (기본값: AAPL,MSFT,GOOGL,AMZN,TSLA)
NASDAQ 종목 (쉼표 구분): AAPL,NVDA,TSLA

NYSE 종목 (기본값: JPM,BAC,WMT,JNJ,PG)
NYSE 종목 (쉼표 구분): JPM,KO,DIS
```

### 3. 개별 에이전트 테스트

```bash
# 데이터 에이전트 단독 테스트
python data_agent.py

# 전략 에이전트 단독 테스트
python strategy_agent.py

# 서비스 에이전트 단독 테스트
python service_agent.py

# 헬퍼 에이전트 단독 테스트
python helper_agent.py
```

---

## ⚙️ 동작 원리

### 1. 전체 워크플로우

```
시작 → 시스템 검증 → 데이터 로딩 → 신호 생성 → 백테스트 실행 → 결과 분석 → 완료
  ↓         ↓           ↓          ↓           ↓            ↓         ↓
Helper   Helper      Data       Strategy    Service   Orchestrator   출력
Agent    Agent       Agent      Agent       Agent     Agent
```

### 2. Phase별 상세 동작

#### Phase 1: 시스템 검증 및 초기화
```python
# Helper Agent가 수행
1. MongoDB 연결 상태 확인
2. 설정 파일 로드 (없으면 자동 생성)
3. 데이터베이스 스캔 (NasDataBase_D, NysDataBase_D)
4. 시스템 리소스 상태 검증
```

#### Phase 2: 데이터 로딩 및 전처리
```python
# Data Agent가 수행
1. 사용자 지정 종목 리스트 처리
2. MongoDB에서 종목별 일봉 데이터 로딩
3. 기술지표 계산 (32개 컬럼)
   - 이동평균: MA5, MA10, MA20, MA50
   - 모멘텀: RSI14, MACD, Stochastic
   - 변동성: Bollinger Bands, ATR
4. 데이터 품질 검증 및 정제
```

#### Phase 3: 매매 신호 생성
```python
# Strategy Agent가 수행
1. 시장별 전략 파라미터 로드
   - NASDAQ: {'ma_fast': 5, 'ma_slow': 20, 'rsi_oversold': 25}
   - NYSE: {'ma_fast': 10, 'ma_slow': 50, 'rsi_oversold': 35}

2. 종목별 신호 생성
   - 골든크로스/데드크로스 감지
   - RSI 과매수/과매도 확인
   - 볼린저밴드 돌파 신호
   - 거래량 이상 감지

3. 신호 품질 평가 및 필터링
```

#### Phase 4: 백테스트 실행
```python
# Service Agent가 수행
1. 포트폴리오 초기화
   - 초기 자본: 100,000,000원
   - NASDAQ/NYSE 각각 50% 할당

2. 일별 시뮬레이션
   - 매수/매도 신호 처리
   - 포지션 크기 계산 (최대 15%/종목)
   - 리스크 관리 (손절: 8%, 익절: 25%)

3. 성과 계산
   - 총 수익률, 샤프 비율
   - 최대 드로우다운
   - 거래 통계 (승률, 평균 손익)
```

### 3. 시장별 전략 차이점

#### NASDAQ 전략 (성장주 중심)
```python
전략_특징 = {
    'ma_fast': 5,           # 빠른 추세 포착
    'ma_slow': 20,          # 단기 모멘텀 중시
    'rsi_oversold': 25,     # 과매도 조건 완화
    'volume_threshold': 1.5, # 높은 거래량 요구
    'volatility_threshold': 0.02  # 높은 변동성 허용
}

매수_조건 = {
    '골든크로스': 'MA5 > MA20',
    'RSI_반등': 'RSI < 25에서 상승',
    '거래량_급증': '거래량 > 평균 1.5배',
    '모멘텀_확인': '최근 10일 상승 모멘텀'
}
```

#### NYSE 전략 (가치주 중심)
```python
전략_특징 = {
    'ma_fast': 10,          # 안정적 추세 확인
    'ma_slow': 50,          # 장기 추세 중시
    'rsi_oversold': 35,     # 보수적 과매도 조건
    'volume_threshold': 1.2, # 적당한 거래량
    'volatility_threshold': 0.015  # 낮은 변동성 선호
}

매수_조건 = {
    '골든크로스': 'MA10 > MA50',
    'RSI_반등': 'RSI < 35에서 상승',
    '안정성_확인': '볼린저밴드 하단 근처',
    '배당_수익률': '높은 배당 수익률 (선택적)'
}
```

---

## 📁 설정 파일 관리

### 1. api_credentials.yaml
```yaml
mongodb:
  host: localhost
  port: 27017
  username: ""           # 필요시 입력
  password: ""           # 필요시 입력
  auth_database: admin

brokers:
  kis:
    real_account:
      app_key: ""        # 실계좌 API 키
      app_secret: ""     # 실계좌 비밀키
      account_number: "" # 계좌번호
    virtual_account:
      app_key: ""        # 모의계좌 API 키
      app_secret: ""     # 모의계좌 비밀키
      account_number: "" # 모의계좌번호

external_apis:
  alpha_vantage: ""      # Alpha Vantage API 키
  telegram_bot_token: "" # 텔레그램 봇 토큰
```

### 2. broker_config.yaml
```yaml
trading_hours:
  market_open: "09:00"
  market_close: "15:30"
  timezone: "Asia/Seoul"

supported_markets:
  - NASDAQ
  - NYSE
  - KOSPI
  - KOSDAQ

order_types:
  - market
  - limit
  - stop
  - stop_limit
```

### 3. risk_management.yaml
```yaml
position_limits:
  max_position_size: 0.1      # 포트폴리오의 10%
  max_concentration: 0.2      # 단일 종목 최대 20%
  max_sector_exposure: 0.3    # 단일 섹터 최대 30%

risk_limits:
  max_daily_loss: 0.02        # 일일 최대 손실 2%
  max_monthly_loss: 0.1       # 월간 최대 손실 10%
  max_drawdown: 0.15          # 최대 드로우다운 15%

order_limits:
  max_orders_per_minute: 10
  min_order_amount: 1000      # 최소 주문 금액
  max_order_amount: 10000000  # 최대 주문 금액

stop_loss:
  default_stop_loss: 0.05     # 기본 손절 5%
  max_stop_loss: 0.1          # 최대 손절 10%
  trailing_stop: true
```

### 4. agent_model.yaml
```yaml
agents:
  orchestrator:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "claude-3-sonnet-20240229"
  data_agent:
    primary_model: "claude-3-sonnet-20240229"
    fallback_model: "gemini-pro"
  strategy_agent:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "gemini-pro"
  service_agent:
    primary_model: "claude-3-sonnet-20240229"
    fallback_model: "claude-3-haiku-20240307"
  helper_agent:
    primary_model: "claude-3-haiku-20240307"
    fallback_model: "gemini-pro"
```

---

## 🔧 문제 해결

### 1. 일반적인 오류

#### MongoDB 연결 실패
```bash
오류: ServerSelectionTimeoutError
해결:
1. MongoDB 서비스 실행 확인
   net start MongoDB
2. 연결 정보 확인 (api_credentials.yaml)
3. 방화벽 설정 확인
```

#### 데이터베이스 없음 오류
```bash
오류: Database 'NasDataBase_D' not found
해결:
1. MongoDB에 데이터베이스 존재 확인
   mongo
   show dbs
2. 데이터베이스 이름 정확성 확인
3. 권한 설정 확인
```

#### 메모리 부족 오류
```bash
오류: MemoryError
해결:
1. 종목 수 줄이기 (기본 16개 → 8개)
2. 백테스트 기간 단축 (1년 → 6개월)
3. Python 메모리 설정 증가
```

### 2. 성능 최적화

#### 데이터 로딩 속도 개선
```python
# 병렬 처리 활성화
ENABLE_PARALLEL_LOADING = True
MAX_WORKERS = 4

# 캐시 사용
USE_DATA_CACHE = True
CACHE_EXPIRE_HOURS = 24
```

#### 메모리 사용량 최적화
```python
# 데이터 타입 최적화
OPTIMIZE_DTYPES = True
USE_CATEGORICAL = True

# 배치 처리
BATCH_SIZE = 1000
STREAMING_MODE = True
```

### 3. 로그 확인

#### 시스템 로그 위치
```bash
# 메인 로그 파일
multi_agent_system.log

# 에이전트별 로그
data_agent.log
strategy_agent.log
service_agent.log
helper_agent.log
```

#### 로그 레벨 설정
```python
# config/logging.yaml
level: INFO  # DEBUG, INFO, WARNING, ERROR

handlers:
  console:
    level: INFO
  file:
    level: DEBUG
    filename: "system.log"
```

---

## 📊 결과 해석

### 1. 백테스트 결과 예시

```
================================================================================
                         백테스트 결과 요약
================================================================================

[기본 정보]
• 백테스트 기간: 2023-01-01 ~ 2023-12-31
• NASDAQ 종목: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX
• NYSE 종목: JPM, BAC, WMT, JNJ, PG, KO, DIS, IBM

[성과 지표]
• 총 수익률: 0.36%
• 연율화 수익률: 0.53%
• 샤프 비율: 0.603
• 최대 드로우다운: 0.89%
• 변동성: 0.61%

[거래 통계]
• 총 거래 수: 61
• 승률: 46.43%
• 평균 수익: 15,234원
• 평균 손실: -12,890원
• Profit Factor: 1.18

[시장별 성과]
• NASDAQ 수익률: 0.42%
• NASDAQ 거래 수: 12
• NYSE 수익률: 0.31%
• NYSE 거래 수: 49

[최종 포트폴리오]
• 최종 자산: 100,360,648원
• 현금 잔고: 85,420,000원
• 주식 가치: 14,940,648원
• 보유 종목 수: 3
================================================================================
```

### 2. 성과 지표 해석

#### 수익률 지표
- **총 수익률**: 전체 기간 동안의 수익률
- **연율화 수익률**: 1년 기준으로 환산한 수익률
- **벤치마크 대비**: S&P 500, NASDAQ 지수와 비교

#### 리스크 지표
- **샤프 비율**: 위험 대비 수익률 (0.5 이상 양호)
- **최대 드로우다운**: 최고점 대비 최대 하락폭
- **변동성**: 수익률의 표준편차

#### 거래 통계
- **승률**: 수익 거래 비율 (50% 이상 우수)
- **Profit Factor**: 총 수익/총 손실 (1.5 이상 우수)
- **평균 보유기간**: 포지션 평균 보유 일수

### 3. 시장별 성과 분석

#### NASDAQ vs NYSE 비교
```python
성과_분석 = {
    'NASDAQ': {
        '특징': '높은 변동성, 빠른 수익 실현',
        '적합한_시장': '상승장, 모멘텀 강한 시기',
        '주의사항': '급격한 하락 위험'
    },
    'NYSE': {
        '특징': '안정적 수익, 낮은 변동성',
        '적합한_시장': '횡보장, 불확실한 시기',
        '주의사항': '수익 기회 제한적'
    }
}
```

---

## 🚀 고급 사용법

### 1. 사용자 정의 전략 추가

#### 새로운 전략 파일 생성
```python
# custom_strategy.py
class CustomStrategy:
    def __init__(self, params):
        self.params = params

    def generate_signals(self, data):
        # 사용자 정의 신호 생성 로직
        buy_signals = []
        sell_signals = []

        # 예: 볼린저밴드 + RSI 조합 전략
        for i in range(len(data)):
            if (data['RSI'][i] < 30 and
                data['Close'][i] < data['BB_Lower'][i]):
                buy_signals.append(i)

        return buy_signals, sell_signals
```

#### 전략 등록
```python
# strategy_agent.py 수정
from custom_strategy import CustomStrategy

def _load_custom_strategies(self):
    self.custom_strategies = {
        'bollinger_rsi': CustomStrategy({
            'rsi_threshold': 30,
            'bb_std': 2
        })
    }
```

### 2. 실시간 모니터링 추가

#### 웹 대시보드 연동
```python
# dashboard_integration.py
import streamlit as st
import plotly.graph_objects as go

def create_dashboard(backtest_results):
    st.title("Multi-Agent Trading Dashboard")

    # 성과 차트
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=backtest_results['dates'],
        y=backtest_results['portfolio_value'],
        name='Portfolio Value'
    ))
    st.plotly_chart(fig)

    # 거래 내역
    st.dataframe(backtest_results['trades'])
```

#### 텔레그램 알림 연동
```python
# telegram_notifier.py
import telegram

def send_notification(bot_token, chat_id, message):
    bot = telegram.Bot(token=bot_token)
    bot.send_message(chat_id=chat_id, text=message)

# 백테스트 완료 시 알림
def notify_completion(results):
    message = f"""
    백테스트 완료!
    수익률: {results['total_return']:.2%}
    거래 수: {results['total_trades']}
    승률: {results['win_rate']:.1%}
    """
    send_notification(BOT_TOKEN, CHAT_ID, message)
```

### 3. 데이터 확장

#### 추가 데이터소스 연결
```python
# data_sources.py
class AlphaVantageConnector:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_fundamental_data(self, symbol):
        # 기본 지표 데이터 수집
        pass

    def get_news_sentiment(self, symbol):
        # 뉴스 감성 분석 데이터
        pass

# data_agent.py에 통합
def _load_external_data(self, symbols):
    alpha_vantage = AlphaVantageConnector(self.api_key)

    for symbol in symbols:
        # 기본 지표 추가
        fundamental = alpha_vantage.get_fundamental_data(symbol)
        self.market_data[symbol] = pd.concat([
            self.market_data[symbol],
            fundamental
        ], axis=1)
```

---

## 📞 지원 및 문의

### 문제 신고
- **GitHub Issues**: [프로젝트 Repository]/issues
- **이메일**: support@trading-system.com

### 개발자 커뮤니티
- **Discord**: Multi-Agent Trading 커뮤니티
- **Slack**: #trading-system-dev

### 문서 업데이트
이 매뉴얼은 시스템 업데이트에 따라 지속적으로 개선됩니다.
- **버전**: 1.0
- **최종 업데이트**: 2025-09-22
- **다음 업데이트 예정**: 2025-10-01

---

## 📋 체크리스트

### 설치 완료 확인
- [ ] Python 3.8+ 설치됨
- [ ] 필수 라이브러리 설치됨 (pymongo, pandas, numpy, pyyaml)
- [ ] MongoDB 설치 및 실행 중
- [ ] 프로젝트 파일 다운로드 완료

### 설정 완료 확인
- [ ] config/ 디렉토리에 YAML 파일들 생성됨
- [ ] MongoDB 연결 정보 설정됨
- [ ] 데이터베이스 접근 권한 확인됨
- [ ] 테스트 실행 성공

### 첫 실행 확인
- [ ] `python multi_agent_trading_system.py --auto` 실행 성공
- [ ] 모든 에이전트 초기화 완료
- [ ] 백테스트 결과 출력됨
- [ ] 로그 파일 생성됨

**🎉 모든 항목이 체크되면 시스템 사용 준비가 완료되었습니다!**