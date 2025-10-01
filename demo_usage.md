# AI Assistant Multi-Agent Trading System 사용법

## 실행 방법

### 1. 대화형 모드 (권장)
```bash
python main_auto_trade.py
```

**실행 시 나타나는 메뉴:**
```
============================================================
[AI] AI Assistant Multi-Agent Trading System
============================================================

모드를 선택하세요:
1  실시간 트레이딩 시스템
2  백테스트 시스템
3  종료
------------------------------------------------------------

선택 (1-3):
```

### 2. 백테스트 설정 예시

백테스트를 선택하면 다음과 같은 설정 과정을 거칩니다:

```
[SETUP] 백테스트 설정
----------------------------------------

[DATE] 백테스트 기간 설정:
시작 날짜 (YYYY-MM-DD, 기본: 2023-01-01):
종료 날짜 (YYYY-MM-DD, 기본: 2024-01-01):

[CAPITAL] 초기 자본 설정:
초기 자본 (백만원 단위, 기본: 100 = 1억원):

[SYMBOLS] 종목 선택:
1. 전체 종목 (myStockInfo.yaml 설정에 따름)
2. 특정 종목 직접 입력
선택 (1-2, 기본: 1):

[CONFIRM] 백테스트 설정 확인:
  [DATE] 기간: 2023-01-01 ~ 2024-01-01
  [CAPITAL] 초기 자본: 100.0백만원
  [SYMBOLS] 대상 종목: 전체 종목 (설정파일 따름)

계속 진행하시겠습니까? (Y/n):
```

### 3. 명령행 모드

#### 실시간 트레이딩
```bash
python main_auto_trade.py --mode TRADING
```

#### 백테스트
```bash
# 기본 전종목 백테스트
python main_auto_trade.py --mode BACKTEST --start-date 2023-01-01 --end-date 2024-01-01

# 특정 종목 백테스트
python main_auto_trade.py --mode BACKTEST --symbols AAPL,MSFT,GOOGL --start-date 2023-01-01 --end-date 2024-01-01

# 초기 자본 지정
python main_auto_trade.py --mode BACKTEST --initial-cash 50 --start-date 2023-01-01 --end-date 2024-01-01
```

## 설정 파일 (myStockInfo.yaml)

### 백테스트 설정 섹션
```yaml
backtest_settings:
  default_mode:
    use_all_symbols: true      # 전체 종목 사용
    max_symbols: null          # 종목 수 제한 (null=무제한)
    sample_size: 500           # 샘플링 시 종목 수

  symbol_selection:
    method: 'database_all'     # 전체 DB 종목
    exclude_penny_stocks: true # 페니스톡 제외
    min_market_cap: 1000000000 # 최소 시가총액 (10억달러)
    min_daily_volume: 1000000  # 최소 일거래량 (100만주)

  performance_settings:
    include_trade_history: true      # 거래 이력 포함
    include_symbol_performance: true # 종목별 성과
    include_financial_metrics: true  # 샤프지수 등
    include_drawdown_analysis: true  # 낙폭 분석

  report_settings:
    output_directory: 'Report/Backtest' # 저장 폴더
    file_format: 'yaml'              # 파일 형식
```

## 백테스트 결과

### 저장 위치
- `Report/Backtest/backtest_report_YYYYMMDD_HHMMSS.yaml` - 포괄적인 상세 보고서
- `Report/Backtest/summary_YYYYMMDD_HHMMSS.yaml` - 요약 보고서

### 포함 내용
1. **Overview**: 기간, 종목수, 전략 설명
2. **Financial Metrics**:
   - 수익률 지표 (총/연환산 수익률, 변동성)
   - 리스크 지표 (샤프지수, 소르티노지수, 칼마지수, VaR)
   - 거래 지표 (총거래수, 승률, 프로핏팩터)
3. **Daily Performance**: 일별 성과 기록
4. **Trade History**: 매매 이력
5. **Symbol Performance**: 종목별 수익/손실
6. **Drawdown Analysis**: 낙폭 분석

## 주요 특징

### 통합 시스템
- **동일한 신호 로직**: 백테스트와 실거래가 동일한 전략 사용
- **데이터 시점 차이**: Strategy Agent에서 제어 (백테스트: t-1, 실거래: t)
- **포괄적 분석**: 샤프지수, 소르티노지수, 칼마지수 등 금융지표

### 대규모 백테스트
- **전종목 지원**: NASDAQ + NYSE 전체 종목 (수천개)
- **설정 기반**: myStockInfo.yaml에서 종목 선택 방식 제어
- **성능 최적화**: 병렬 처리 및 메모리 효율적 구현

### 사용자 친화적 인터페이스
- **대화형 설정**: 단계별 설정 입력
- **명령행 지원**: 자동화 스크립트 지원
- **포괄적 결과**: YAML 형식의 상세 보고서