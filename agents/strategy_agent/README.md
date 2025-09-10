# Strategy Agent

## Overview
Strategy Agent는 트레이딩 전략 개발, 신호 생성, 포지션 크기 결정을 담당하는 에이전트입니다.

## Responsibilities
- **Signal Generation**: 시장 데이터와 지표를 기반으로 매매 신호 생성
- **Position Sizing**: 리스크 관리를 고려한 최적 포지션 크기 계산
- **Risk Management**: 전략 수준의 리스크 관리 규칙 적용
- **Portfolio Optimization**: 포트폴리오 최적화 알고리즘 실행
- **Strategy Evaluation**: 전략 성과 평가 및 개선

## Managed Files
- `Project/strategy/signal_generator.py` - 트레이딩 신호 생성
- `Project/strategy/position_sizing.py` - 포지션 크기 계산
- `Project/strategy/risk_management.py` - 리스크 관리 규칙
- `Project/strategy/portfolio_optimizer.py` - 포트폴리오 최적화
- `Project/strategy/strategy_evaluator.py` - 전략 성과 평가
- `Project/strategy/strategy_factory.py` - 전략 생성 팩토리

## Collaborations
### Input
- **From Data Agent**: 처리된 시장 데이터, 기술적/펀더멘털 지표

### Output
- **To Service Agent**: 매매 신호, 포지션 크기, 리스크 파라미터

## Strategy Types
- **Trend Following**: 추세 추종 전략
- **Mean Reversion**: 평균 회귀 전략
- **Momentum**: 모멘텀 기반 전략
- **Arbitrage**: 차익거래 전략
- **Machine Learning**: ML 기반 예측 전략

## Risk Management
- **Position Limits**: 개별 포지션 한도
- **Portfolio Exposure**: 포트폴리오 노출도 관리
- **Stop Loss**: 손절 규칙
- **Max Drawdown**: 최대 낙폭 제한

## Configuration
- `config/strategy_config.yaml` - 전략 파라미터 설정