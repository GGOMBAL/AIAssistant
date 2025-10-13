# 🚀 Multi-Agent Trading System

**NasDataBase와 NysDataBase를 통합한 지능형 백테스트 시스템**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Latest-green.svg)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

Multi-Agent Trading System은 **5개의 전문화된 AI 에이전트**가 협력하여 NASDAQ과 NYSE 시장 데이터를 통합 분석하고 백테스트를 수행하는 차세대 트레이딩 시스템입니다.

## 🚀 빠른 시작

### 1단계: 환경 설정 (1분)
```bash
# 필수 라이브러리 설치
pip install pymongo pandas numpy pyyaml

# MongoDB 실행 확인
net start MongoDB
```

### 2단계: 즉시 실행 (30초)
```bash
cd C:\WorkSpace\AIAgentProject\AIAssistant\Project
python multi_agent_trading_system.py --auto
```

### 3단계: 결과 확인
```
================================================================================
                         백테스트 결과 요약
================================================================================
[정보] 총 수익률: 0.36%
[정보] 연율화 수익률: 0.53%
[정보] 샤프 비율: 0.603
[정보] 승률: 46.43%
[정보] 총 거래 수: 61회
================================================================================
```

**🎉 3분 안에 완전한 백테스트 결과를 확인하세요!**

## ✨ 주요 특징

### 🤖 **Multi-Agent 협업**
- **5개 전문 에이전트**가 독립적으로 작업하며 협력
- **실시간 작업 분배** 및 결과 통합
- **장애 격리** 및 자동 복구 메커니즘

### 📊 **시장별 차별화 전략**
- **NASDAQ**: 빠른 성장주 전략 (5일/20일 MA, 높은 모멘텀)
- **NYSE**: 안정적 가치주 전략 (10일/50일 MA, 보수적 접근)
- **동적 파라미터 조정** 및 시장 상황 적응

### 🗄️ **Big Data 처리**
- **15,000+ 종목** 실시간 데이터 처리
- **MongoDB 통합** (NasDataBase_D, NysDataBase_D)
- **메모리 최적화** 및 고속 계산 엔진

## 🏗️ 시스템 아키텍처

### 🤖 에이전트 구성

```
┌─────────────────────────────────────────────────────────────┐
│                    RUN AGENT                                │
│              (최상위 실행 관리자)                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Orchestrator Agent                            │
│              (작업 분배 및 조정)                            │
└─┬─────────┬─────────┬─────────┬─────────────────────────────┘
  │         │         │         │
  ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌─────────┐
│ Data  │ │Strategy│ │Service│ │ Helper  │
│ Agent │ │ Agent │ │ Agent │ │ Agent   │
│       │ │       │ │       │ │         │
│MongoDB│ │시장별  │ │백테스트│ │시스템   │
│ 연동  │ │전략   │ │ 실행  │ │ 관리   │
└───────┘ └───────┘ └───────┘ └─────────┘
```

### 📋 에이전트별 역할

| 에이전트 | 주요 기능 | 파일명 |
|---------|----------|--------|
| 🚀 **RUN AGENT** | 최상위 실행 관리, 전체 Agent 라이프사이클 관리 | `run_agent.py` |
| 🎭 **Orchestrator** | 작업 분배 및 조정, Agent 간 통신 중재 | `orchestrator/main_orchestrator.py` |
| 📊 **Database Agent** | MongoDB 데이터 로딩, 기술지표 계산 | `project/router/data_agent_router.py` |
| 🧠 **Strategy Agent** | 시장별 매매신호 생성, 전략 최적화 | `project/router/strategy_agent_router.py` |
| ⚡ **Service Agent** | 백테스트 실행, 포트폴리오 관리 | `project/router/service_agent_router.py` |
| 🔧 **Helper Agent** | 시스템 설정, MongoDB 연결 관리 | `project/router/helper_agent_router.py` |

## 📖 사용 방법

### 🎯 기본 실행 모드

#### 1. RUN AGENT로 실행 (권장)
```bash
python run_agent.py

# 새로운 아키텍처:
# • RUN AGENT가 모든 Agent 관리
# • 자동 Agent 초기화 및 종료
# • 실시간 상태 모니터링
```

#### 2. 레거시 모드
```bash
python main_auto_trade.py

# Project Layer 직접 사용:
# • Indicator Layer → Strategy Layer → Service Layer
# • 기존 방식 호환성 유지
```

#### 3. 개별 Layer 테스트
```bash
# Project Layer별 직접 실행
python -m project.indicator.data_frame_generator
python -m project.strategy.signal_generation_service
python -m project.service.daily_backtest_service
```

## ⚡ 성능

### 🚀 실행 성능
```
전체 실행 시간: 1.93초
├── 시스템 검증: 0.2초
├── 데이터 로딩: 1.38초 (15,113 종목)
├── 신호 생성: 0.30초 (194개 신호)
└── 백테스트: 0.05초 (250일 시뮬레이션)
```

### 📊 처리 용량
```
데이터 처리량:
├── MongoDB 종목: 15,113개
├── 일봉 데이터 포인트: 4,000,000+
├── 기술지표 계산: 512개 지표
└── 메모리 사용량: < 500MB
```

### 🎯 백테스트 정확도
```
2023년 실제 데이터 기준:
├── 총 수익률: 0.36%
├── 샤프 비율: 0.603
├── 최대 드로우다운: 0.89%
├── 승률: 46.43%
└── 거래 수: 61회
```

## 📚 문서

### 📖 상세 가이드
- **[사용자 매뉴얼](docs/USER_MANUAL.md)** - 완전한 사용 가이드 (50+ 페이지)
- **[빠른 시작 가이드](docs/QUICK_START_GUIDE.md)** - 5분 만에 시작하기
- **[아키텍처 가이드](docs/ARCHITECTURE_GUIDE.md)** - 시스템 설계 및 구조

### 🔧 주요 파일 구조
```
# 최상위 실행
run_agent.py                       # 🚀 RUN AGENT (메인 실행)
main_auto_trade.py                 # 🔄 레거시 실행 파일

# Agent 구조
agents/
├── run_agent/                     # 🚀 RUN AGENT
│   ├── agent.py
│   ├── config.yaml
│   └── README.md
├── helper_agent/                  # 🔧 Helper Agent
├── database_agent/                # 📊 Database Agent (구조 예정)
├── strategy_agent/                # 🧠 Strategy Agent
└── service_agent/                 # ⚡ Service Agent

# Orchestrator
orchestrator/
├── main_orchestrator.py           # 🎭 메인 오케스트레이터
├── multi_agent_orchestrator.py
└── agent_scheduler.py

# Project Layers
project/
├── indicator/                     # Indicator Layer
│   ├── data_frame_generator.py
│   └── technical_indicators.py
├── strategy/                      # Strategy Layer
│   └── signal_generation_service.py
├── service/                       # Service Layer
│   └── daily_backtest_service.py
├── database/                      # Database Layer
│   ├── mongodb_operations.py
│   └── database_manager.py
├── Helper/                        # Helper Layer
│   └── kis_api_helper_us.py
└── router/                        # Agent Routers
    ├── helper_agent_router.py
    ├── data_agent_router.py
    ├── strategy_agent_router.py
    └── service_agent_router.py

# 설정 파일
config/
├── api_credentials.yaml           # API 인증 정보
├── broker_config.yaml             # 브로커 설정
├── agent_model.yaml               # Agent 모델 설정
└── risk_management.yaml           # 리스크 관리

# 문서
docs/
├── interfaces/                    # Layer 인터페이스 명세
│   ├── STRATEGY_LAYER_INTERFACE.md
│   ├── SERVICE_LAYER_INTERFACE.md
│   ├── HELPER_LAYER_INTERFACE.md
│   ├── INDICATOR_LAYER_INTERFACE.md
│   └── DATABASE_LAYER_INTERFACE.md
├── modules/                       # Layer 모듈 설명
│   ├── STRATEGY_MODULES.md
│   ├── SERVICE_MODULES.md
│   ├── HELPER_MODULES.md
│   ├── INDICATOR_MODULES.md
│   └── DATABASE_MODULES.md
├── specs/                         # 알고리즘 상세
│   ├── SIGNAL_GENERATION_SPEC.md
│   ├── BACKTEST_SERVICE_SPEC.md
│   ├── API_INTEGRATION_SPEC.md
│   ├── TECHNICAL_INDICATORS_SPEC.md
│   └── DATABASE_SCHEMA.md
└── architecture/                  # 아키텍처 문서
```

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

### 2. MongoDB 설정
```bash
# Windows에서 MongoDB 시작
net start MongoDB

# 연결 확인
mongo --host localhost:27017
```

### 3. 첫 실행 테스트
```bash
# 프로젝트 디렉토리로 이동
cd C:\WorkSpace\AIAgentProject\AIAssistant\Project

# 자동 모드로 테스트 실행
python multi_agent_trading_system.py --auto
```

## 📞 지원

### 🆘 문제 해결
1. **MongoDB 연결 실패**: `net start MongoDB` 실행
2. **모듈 없음 오류**: `pip install pymongo pandas numpy pyyaml`
3. **데이터베이스 없음**: MongoDB에 NasDataBase_D, NysDataBase_D 확인

### 📧 연락처
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **이메일**: support@multi-agent-trading.com
- **문서**: [docs/](docs/) 디렉토리 참조

## 📄 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

---

**🚀 지금 바로 시작하세요!**

```bash
# 새로운 RUN AGENT 방식 (권장)
python run_agent.py

# 또는 레거시 방식
python main_auto_trade.py
```

**Happy Trading! 📈**

---

## 📊 최근 업데이트 (2025-10-09)

### ✅ 새로운 아키텍처 (v2.0)
- **RUN AGENT 추가**: 최상위 실행 관리자 구현
- **Layer 구조 명확화**: 5개 Layer 완전 분리 (Helper, Database, Indicator, Strategy, Service)
- **문서화 완료**: 15개 문서 완성 (interfaces, modules, specs)

### 📚 문서 체계 완성
- **Interface 문서**: 5개 Layer 입출력 명세
- **Modules 문서**: 모든 모듈 상세 설명
- **Spec 문서**: 알고리즘 및 스키마 명세

### 🏗️ 아키텍처 개선
```
이전: Orchestrator → Agent
현재: RUN AGENT → Orchestrator → Agent → Layer
```