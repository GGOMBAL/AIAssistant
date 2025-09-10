# Helper Agent

## Overview
Helper Agent는 증권사 API 및 외부 데이터 제공자 API를 관리하는 에이전트입니다.

## Responsibilities
- **Broker API Management**: 증권사 API 연결 및 주문 실행
- **External Data Integration**: 외부 데이터 제공자 API 통합
- **API Rate Limiting**: API 호출 제한 및 할당량 관리
- **Health Monitoring**: API 상태 모니터링 및 알림

## Managed Files
- `Project/service/broker_api_connector.py` - 브로커 API 연결
- `Project/service/data_provider_api.py` - 데이터 제공자 API
- `Project/service/api_rate_limiter.py` - API 속도 제한
- `Project/service/webhook_handler.py` - 웹훅 처리
- `Project/service/external_data_router.py` - 외부 데이터 라우팅
- `Project/service/api_health_monitor.py` - API 상태 모니터링

## Collaborations
### Input
- **From Service Agent**: 주문 실행 요청, 계좌 정보 조회

### Output
- **To Data Agent**: 외부 시장 데이터, 뉴스, 경제 지표
- **To Service Agent**: 주문 체결 확인, 포지션 업데이트

## External APIs
- **Stock Market Data**: AlphaVantage, Yahoo Finance, IEX Cloud
- **Korean Brokers**: 키움증권, 한국투자증권, NH투자증권
- **Global Brokers**: Interactive Brokers, TD Ameritrade
- **Alternative Data**: News API, Economic Calendar API

## Configuration
- `config/api_credentials.yaml` - API 인증 정보
- `config/broker_config.yaml` - 브로커별 설정