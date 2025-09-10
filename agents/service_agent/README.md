# Service Agent

## Overview
Service Agent는 백테스팅, 트레이딩 실행, 데이터베이스 관리를 통합 관리하는 에이전트입니다.

## Responsibilities
- **Backtesting**: 전략 백테스팅 및 시뮬레이션
- **Trading Execution**: 실제 거래 실행 및 포지션 관리
- **Database Management**: 시장 데이터, 전략, 거래 데이터 저장 및 관리
- **Risk Control**: 실시간 리스크 모니터링 및 제어

## Managed Files
- `Project/service/backtester.py` - 백테스팅 엔진
- `Project/service/simulation_engine.py` - 거래 시뮬레이션
- `Project/service/trade_executor.py` - 거래 실행 관리
- `Project/service/position_manager.py` - 포지션 추적 및 관리
- `Project/service/risk_controller.py` - 리스크 제어
- `Project/database/market_db.py` - 시장 데이터베이스
- `Project/database/strategy_db.py` - 전략 데이터베이스
- `Project/database/trade_db.py` - 거래 데이터베이스
- `Project/database/backup_manager.py` - 백업 관리

## Collaborations
### Input
- **From Data Agent**: 히스토리컬 데이터, 실시간 피드
- **From Strategy Agent**: 트레이딩 신호, 전략 파라미터

### Output
- **To Helper Agent**: 브로커 API를 통한 주문 실행
- **To Database**: 백테스트 결과, 거래 기록 저장

## Configuration
- `config/trading_config.yaml` - 트레이딩 시스템 설정
- `config/database_config.yaml` - 데이터베이스 연결 설정