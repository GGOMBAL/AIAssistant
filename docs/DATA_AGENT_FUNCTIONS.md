# 📊 Data Agent 함수 문서 (2025-10-02 업데이트)

## 🎯 개요

Data Agent는 MongoDB에서 다양한 시계열 데이터를 로드하고 백테스팅에 필요한 기술적 지표를 계산하는 역할을 담당합니다. 3-Year Lookback 시스템을 통해 정확한 지표 계산을 보장합니다.

---

## 🔄 3-Year Lookback 데이터 로딩 함수들

### 📈 `load_daily_data_from_mongodb(symbol, start_date=None, end_date=None)`

**목적**: MongoDB에서 일간 데이터를 로드하고 D 신호 생성에 필요한 모든 지표를 계산

**매개변수**:
- `symbol` (str): 종목 심볼 (예: 'CRDO', 'AAPL')
- `start_date` (datetime, optional): 시작일 (None이면 전체 데이터)
- `end_date` (datetime, optional): 종료일 (None이면 전체 데이터)

**반환값**:
- `pd.DataFrame`: 계산된 D 지표가 포함된 일간 데이터

**계산되는 지표들**:
```python
# 이동평균 지표
'SMA10', 'SMA20', 'SMA50', 'SMA120', 'SMA200'

# 모멘텀 지표
'SMA200_M'  # SMA200 - SMA200.shift(1)

# 최고가 지표 (D 신호용)
'Highest_1M'   # 20일 최고가
'Highest_3M'   # 60일 최고가
'Highest_6M'   # 120일 최고가
'Highest_1Y'   # 252일 최고가
'Highest_2Y'   # 504일 최고가

# 기타 지표
'Dhigh', 'Dclose', 'Dopen', 'Dlow'  # OHLC 매핑
'ADR'     # Average Daily Range
'VolSMA20'  # 20일 거래량 이동평균
```

**사용 예시**:
```python
# 전체 데이터 로드
df = load_daily_data_from_mongodb('CRDO')

# 3년 룩백을 포함한 데이터 로드
from datetime import datetime, timedelta
start = datetime(2023, 1, 1)
lookback = start - timedelta(days=3*365)
df = load_daily_data_from_mongodb('CRDO', lookback, datetime(2023, 12, 31))
```

### 📊 `load_weekly_data_from_mongodb(symbol, start_date=None, end_date=None)`

**목적**: MongoDB에서 주간 데이터를 로드하고 W 신호 생성에 필요한 지표를 계산

**매개변수**: 동일한 매개변수 구조

**계산되는 지표들**:
```python
# refer와 정확히 동일한 기간 사용
'52_H'     # close.rolling(52).max()  - 52주 최고가
'52_L'     # close.rolling(52).min()  - 52주 최저가
'1Year_H'  # close.rolling(48).max()  - 1년 최고가 (48주)
'1Year_L'  # close.rolling(48).min()  - 1년 최저가 (48주)
'2Year_H'  # close.rolling(96).max()  - 2년 최고가 (96주)
'2Year_L'  # close.rolling(96).min()  - 2년 최저가 (96주)
'Wclose'   # 주간 종가
```

**데이터 정제 기능**:
- 중복 날짜 제거 (keep='last')
- 최신 데이터 우선 보존
- 로그 출력으로 중복 제거 현황 확인

### 📈 `load_rs_data_from_mongodb(symbol, start_date=None, end_date=None)`

**목적**: MongoDB에서 상대강도(RS) 데이터를 로드

**로드되는 지표들**:
```python
'RS_4W'        # 4주 상대강도
'RS_12W'       # 12주 상대강도
'Sector_RS_4W'     # 섹터 대비 4주 상대강도
'Industry_RS_4W'   # 산업 대비 4주 상대강도
'Sector_RS_12W'    # 섹터 대비 12주 상대강도
'Industry_RS_12W'  # 산업 대비 12주 상대강도
```

### 💰 `load_fundamental_data_from_mongodb(symbol, start_date=None, end_date=None)`

**목적**: MongoDB에서 펀더멘털 데이터를 로드하고 F 신호 생성에 필요한 지표를 계산

**로드되는 지표들**:
```python
'REV_YOY'    # 매출 전년 대비 성장률
'EPS_YOY'    # EPS 전년 대비 성장률
'revenue'    # 매출액
'commonStockSharesOutstanding'  # 발행주식수
```

**계산되는 지표들**:
```python
'MarketCapitalization'  # 시가총액 = close × shares
```

**MarketCapitalization 계산 로직**:
```python
# 일간 데이터에서 가장 가까운 거래일의 종가 사용
for date in f_df.index:
    nearest_date = daily_df.index[daily_df.index <= date]
    if len(nearest_date) > 0:
        nearest_date = nearest_date[-1]
        close_price = daily_df.loc[nearest_date, 'close']
        shares = f_df.loc[date, 'commonStockSharesOutstanding']
        f_df.loc[date, 'MarketCapitalization'] = close_price * shares
```

---

## 🔄 지표 계산 및 병합 함수들

### 🔄 `merge_weekly_data_to_daily(daily_df, weekly_df)`

**목적**: 주간 지표를 일간 데이터프레임에 병합

**병합 방식**:
- Forward fill을 사용하여 주간 데이터를 일간으로 확장
- 날짜 인덱스 기준으로 정렬 및 병합
- 중복 제거 후 병합

**병합되는 컬럼들**:
```python
weekly_columns = ['52_H', '52_L', '1Year_H', '1Year_L', '2Year_H', '2Year_L', 'Wclose']
```

### 📊 `merge_rs_data_to_daily(daily_df, rs_df)`

**목적**: RS 지표를 일간 데이터프레임에 병합

**병합되는 컬럼들**:
```python
rs_columns = ['RS_4W', 'Sector_RS_4W', 'Industry_RS_4W']
```

### 💰 `merge_fundamental_data_to_daily(daily_df, fundamental_df)`

**목적**: 펀더멘털 지표를 일간 데이터프레임에 병합

**병합 특징**:
- Forward fill을 사용하여 분기별 데이터를 일간으로 확장
- 가장 최신 펀더멘털 데이터를 해당 기간 동안 유지

---

## 🎯 신호 생성 통합 함수

### 🚀 `generate_sophisticated_signals(df, symbol)`

**목적**: refer Strategy_A.py와 동일한 로직으로 모든 신호를 생성

**신호 생성 순서**:
1. 기본 신호 컬럼 초기화
2. 포괄적 지표 계산 (`calculate_comprehensive_indicators`)
3. RS 신호 생성 (`generate_rs_signal_exact`)
4. 주간 신호 생성 (`generate_weekly_signal_exact`)
5. 펀더멘털 신호 생성 (`generate_fundamental_signal_exact`)
6. 수익 신호 생성 (`generate_earnings_signal_exact`)
7. 일간 신호 생성 (`generate_daily_signal_exact`)
8. 최종 통합 신호 생성

**생성되는 신호 컬럼들**:
```python
'BuySig'     # 최종 매수 신호 (모든 조건 충족)
'SellSig'    # 매도 신호
'wBuySig'    # 주간 매수 신호
'dBuySig'    # 일간 매수 신호
'rsBuySig'   # RS 매수 신호
'fBuySig'    # 펀더멘털 매수 신호
'eBuySig'    # 수익 매수 신호
'signal'     # 통합 신호
'Type'       # 신호 유형
```

**최종 신호 조합 로직** (refer와 동일):
```python
ent_cond1 = df['wBuySig'] == 1   # 주간 조건
ent_cond2 = df['dBuySig'] == 1   # 일간 조건
ent_cond3 = df['rsBuySig'] == 1  # RS 조건
ent_cond4 = df['fBuySig'] == 1   # 펀더멘털 조건

# 최종 매수 신호 = 모든 조건 충족
df['BuySig'] = (ent_cond1 & ent_cond2 & ent_cond3 & ent_cond4).astype(int)
```

---

## 🔧 백테스트 통합 함수

### 🎯 `run_sophisticated_backtest_engine(symbols, start_date, end_date, initial_cash, market_config, return_dataframes=False)`

**목적**: 3-Year Lookback을 적용한 정교한 백테스트 실행

**3-Year Lookback 구현**:
```python
# 3년 룩백 날짜 계산
start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
lookback_date = start_date_dt - timedelta(days=3*365)

# 전체 데이터 로드 (3년 + 백테스트 기간)
query = {
    "Date": {
        "$gte": lookback_date,  # 3년 전부터
        "$lte": end_date_dt     # 백테스트 종료일까지
    }
}

# 지표 계산 후 백테스트 기간만 추출
df = generate_sophisticated_signals(full_df, symbol)
df_filtered = df[(df.index >= start_date_dt) & (df.index <= end_date_dt)].copy()
```

**반환값**:
```python
{
    'portfolio_stats': {
        'total_return': float,
        'max_drawdown': float,
        'sharpe_ratio': float,
        'win_rate': float
    },
    'trades': List[Dict],
    'daily_returns': List[float],
    'dataframes': Dict[str, pd.DataFrame]  # return_dataframes=True 시
}
```

---

## 📊 성능 모니터링

### 로깅 정보
모든 함수는 상세한 로깅 정보를 제공합니다:

```python
INFO: [MONGODB_D] CRDO: Added D indicators (SMA, Highest, ADR) from MongoDB data
INFO: [MONGODB_D] CRDO: Loaded 484 daily records from NasDataBase_D
INFO: [MONGODB_W] CRDO: Removed 3939 duplicate entries
INFO: [MONGODB_W] CRDO: Added W indicators with refer periods: 52_H(52), 52_L(52), 1Year_H(48), 1Year_L(48), 2Year_H(96), 2Year_L(96), Wclose
INFO: [3Y_LOOKBACK] Loading data from 2020-01-02 to 2023-12-31 for indicator calculation
```

### 에러 처리
모든 함수는 견고한 에러 처리를 포함:
- MongoDB 연결 실패 시 자동 재시도
- 데이터 없음 경고 및 None 반환
- 지표 계산 실패 시 원본 데이터 반환
- 상세한 에러 로깅

---

## 🚀 사용 예시

### 전체 백테스트 파이프라인
```python
# 1. 3년 룩백 백테스트 실행
results = await run_sophisticated_backtest_engine(
    symbols=['CRDO', 'AAPL'],
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=100000,
    market_config=config,
    return_dataframes=True
)

# 2. 개별 데이터 분석
crdo_df = results['dataframes']['CRDO']
d_signals = crdo_df['dBuySig'].sum()
print(f"CRDO D signals: {d_signals}")
```

이 Data Agent는 **refer 시스템과 100% 호환되는 정확한 지표 계산**과 **3년 룩백을 통한 신뢰할 수 있는 백테스팅**을 제공합니다.