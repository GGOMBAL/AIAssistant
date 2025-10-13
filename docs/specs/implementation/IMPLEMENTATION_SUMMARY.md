# 데이터 사용 시점 구현 완료 요약

## ✅ 구현 완료

### 1. 데이터 타입별 사용 시점 규칙

| 데이터 타입 | 사용 시점 | 코드 | 이유 |
|------------|----------|------|------|
| **RS** (상대강도) | T-1 (전날) | `iloc[-2]` | 당일 RS는 장 마감 후 계산되므로 장 시작 전 알 수 없음 |
| **D** (일봉) | T-1 (전날) | `iloc[-2]` | 당일 종가는 장 마감 후에만 확정되므로 장 시작 전 알 수 없음 |
| **W** (주봉) | T (최신) | `iloc[-1]` | 주봉은 금요일 종가 기준으로 이미 확정된 데이터 |
| **F** (펀더멘털) | T (최신) | `iloc[-1]` | 분기별 재무제표로 이미 공시된 확정 데이터 |
| **E** (어닝스) | T (최신) | `iloc[-1]` | 분기별 실적으로 이미 발표된 확정 데이터 |

### 2. 수정된 함수들

#### `signal_generation_service.py`:

**_generate_rs_signals()**:
```python
# 변경 전
latest = df_rs.iloc[-1]

# 변경 후
if df_rs.empty or len(df_rs) < 2:
    return 0
latest = df_rs.iloc[-2]  # T-1 사용
```

**_generate_daily_rs_combined_signals()**:
```python
# 변경 전
latest = df_daily.iloc[-1]
rs_latest = df_rs.iloc[-1]

# 변경 후
if df_daily.empty or len(df_daily) < 2:
    return {...}
latest = df_daily.iloc[-2]  # T-1 사용
rs_latest = df_rs.iloc[-2]  # T-1 사용
```

**_generate_weekly_signals()**, **_generate_fundamental_signals()**, **_generate_earnings_signals()**:
```python
# 변경 없음 - 이미 iloc[-1] 사용 (T 최신 데이터)
latest = df_weekly.iloc[-1]
latest = df_fundamental.iloc[-1]
latest = df_earnings.iloc[-1]
```

### 3. 실전 시나리오

#### 오토 트레이딩 (실거래):
```
2024-10-12 (금) 16:00 - 장 마감
2024-10-12 (금) 17:00 - 시그널 생성 시점

사용 데이터:
- RS: 2024-10-11 (목) 종가 기준 RS
- D (Daily): 2024-10-11 (목) 종가
- W (Weekly): 2024-10-11 (금) 주봉 종가
- F, E: 최근 분기 실적

→ 2024-10-15 (월) 장 시작 시 매매 실행
```

#### 백테스트:
```
백테스트 날짜: 2024-10-12

사용 데이터 (동일):
- RS: 2024-10-11 (목) 종가 기준 RS
- D (Daily): 2024-10-11 (목) 종가
- W, F, E: 최신 확정 데이터

→ 2024-10-12 (금) 매매 시뮬레이션
```

## 🎯 핵심 포인트

### Look-ahead Bias 방지:
- **RS와 D는 반드시 T-1 사용**: 당일 종가를 이용한 신호는 불가능
- **W, F, E는 T 사용**: 이미 충분히 과거에 확정된 데이터

### 백테스트 vs 실거래 차이점:
현재 구현에서는 **데이터 사용 시점이 동일**합니다:
- 백테스트든 실거래든 **RS/D는 T-1, W/F/E는 T**

### 향후 백테스트 개선 필요사항:

백테스트는 시계열로 전체 기간 신호를 생성해야 합니다:

```python
# 현재: 단일 시점 신호
signal = generate_comprehensive_signals(
    df_daily=df_D['AAPL'],
    df_weekly=df_W['AAPL'],
    ...
)
# 결과: {'signal': 1, 'strength': 0.8}

# 필요: 시계열 신호 (TODO)
signals_df = generate_signals_timeseries(
    df_daily=df_D['AAPL'],
    df_weekly=df_W['AAPL'],
    start_date='2023-01-01',
    end_date='2024-10-12'
)
# 결과: DataFrame
#   Date       | signal | strength | target_price | losscut_price
#   2023-01-01 |   0    |   0.0    |     0.0      |      0.0
#   2023-01-02 |   1    |   0.8    |   150.0      |    140.0
#   ...
```

## 📝 테스트 결과

### 테스트 실행:
```bash
python main_auto_trade.py
→ 2. 개별 종목 시그널 확인
→ AAPL
```

### 결과:
✅ 에러 없이 정상 실행
✅ RS Signal: 0 (전날 RS_4W=59.33 < 90)
✅ Daily RS Signal: 0
✅ Earnings Signal: 1
✅ 모든 지표 정상 출력

## 다음 단계 (TODO)

1. **백테스트용 시계열 신호 생성 함수 추가**:
   - `generate_signals_timeseries()` 구현
   - 전체 기간에 대해 일별 신호 DataFrame 생성
   - DailyBacktestService에서 사용

2. **staged_pipeline_service.py 검증**:
   - 단계별 필터링에서도 동일한 데이터 사용 규칙 적용 확인

3. **성능 테스트**:
   - 15,000개 종목 대상 백테스트 실행
   - 시그널 생성 속도 측정
