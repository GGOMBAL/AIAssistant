# Data Agent

## Overview
Data Agent는 Data Gathering Service를 관리하며 모든 시장 데이터 수집, 처리, 지표 계산을 담당하는 에이전트입니다.

## Responsibilities
- **Data Gathering Service**: 중앙화된 데이터 수집 서비스 관리
- **Technical Indicators**: 기술적 지표 계산 및 분석
- **Fundamental Analysis**: 펀더멘털 지표 관리
- **Market Scanning**: 시장 스캐닝 및 필터링
- **Data Processing**: 데이터 정규화, 검증, 처리

## Managed Files
- `Project/indicator/technical_indicators.py` - 기술적 지표 계산
- `Project/indicator/fundamental_indicators.py` - 펀더멘털 지표
- `Project/indicator/market_scanner.py` - 시장 스캐너
- `Project/service/data_gathering_service.py` - 데이터 수집 서비스
- `Project/service/data_processor.py` - 데이터 처리 파이프라인
- `Project/service/data_normalizer.py` - 데이터 정규화
- `Project/service/data_validator.py` - 데이터 품질 검증

## Collaborations
### Input
- **From Helper Agent**: 외부 API로부터 원시 시장 데이터

### Output
- **To Strategy Agent**: 처리된 시장 데이터 및 지표
- **To Service Agent**: 백테스팅/트레이딩용 히스토리컬 데이터

## Technical Indicators
- **Trend**: MA, EMA, MACD, ADX
- **Momentum**: RSI, Stochastic, Williams %R
- **Volatility**: Bollinger Bands, ATR, Standard Deviation
- **Volume**: OBV, Volume Profile, VWAP

## Data Types Managed

### Market Data
- Stock prices (OHLCV) across all timeframes
- Volume and trading statistics
- Corporate actions and dividends
- Market indices and benchmarks

### Alternative Data
- ETF holdings and performance
- Cryptocurrency prices and metrics
- Economic indicators
- News sentiment data

### Fundamental Data
- Financial statements
- Company metrics and ratios
- Analyst ratings and estimates
- Sector and industry classifications

## Configuration
- `config/data_sources.yaml` - 데이터 소스 설정