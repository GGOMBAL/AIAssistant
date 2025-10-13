# Signal Timeline Feature Documentation

**Version**: 1.0
**Last Updated**: 2025-10-13
**Managed by**: Orchestrator Agent

**Related Documentation**:
- [AGENT_INTERFACES.md](AGENT_INTERFACES.md) - Agent communication protocols
- [INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md) - Data structure interfaces
- [DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md) - Column specifications

---

## 개요

**Signal Timeline Feature**는 개별 종목의 **W(Weekly), D(Daily), RS(Relative Strength), E(Earnings), F(Fundamental)** 시그널을 타임라인 형태로 시각화하는 기능입니다.

이 기능은 main_auto_trade.py의 **메뉴 옵션 #4**로 제공되며, 사용자가 종목과 분석 기간을 선택하면 Staged Pipeline을 통해 시그널을 생성하고 최근 100개 거래일의 시그널을 테이블 형태로 출력합니다.

---

## 아키텍처

### 시스템 흐름

```
사용자 입력
    ↓
show_ticker_signal_timeline()  (main_auto_trade.py:961-1060)
    ↓
StagedPipelineService  (E → F → W → RS → D 단계별 필터링)
    ↓
Data Structure Conversion  (stage → symbol 구조 변환)
    ↓
_print_ticker_signal_timeline()  (main_auto_trade.py:120-297)
    ↓
타임라인 출력 (100 trading days)
```

### 핵심 컴포넌트

| 컴포넌트 | 위치 | 역할 |
|---------|------|------|
| `show_ticker_signal_timeline()` | main_auto_trade.py:961-1060 | 사용자 입력 처리 및 파이프라인 실행 |
| `StagedPipelineService` | project/service/staged_pipeline_service.py | 단계별 필터링 및 데이터 로딩 |
| `_print_ticker_signal_timeline()` | main_auto_trade.py:120-297 | 타임라인 시각화 출력 |

---

## 사용 방법

### 메뉴에서 실행

```bash
python main_auto_trade.py

1. 자동 백테스트 실행 (전체 종목)
2. 개별 종목 시그널 확인
3. 오토 트레이딩 시스템 (실거래)
4. 개별 티커 시그널 타임라인 (W/D/RS/E/F)  ← 선택
5. 종료

선택 (1-5): 4
```

### 사용자 입력

#### 1. 종목 코드 입력
```
분석할 종목 코드를 입력하세요 (쉼표로 구분, 예: AAPL,MSFT,GOOGL):
종목 코드: AAPL,MSFT,GOOGL
```

#### 2. 분석 기간 선택
```
분석 기간을 선택하세요:
1. 최근 3개월
2. 최근 6개월
3. 최근 1년
4. 최근 2년

선택 (1-4, 기본값: 1): 3
```

---

## 출력 형식

### 타임라인 테이블

```
[AAPL] 시그널 타임라인 (최근 100 거래일)

날짜       종가      W      D      RS     E      F
---------- --------- ------ ------ ------ ------ ------
2025-10-13 $150.25  ✓ 신고 ✓ 급등 ✓ 강세 -      ✓ 우수
2025-10-12 $149.80  ✓ 신고 -      ✓ 강세 -      ✓ 우수
2025-10-11 $148.50  -      -      ✓ 강세 ✓ 양호 ✓ 우수
...
```

### 시그널 타입 설명

#### W (Weekly Signal)
- **✓ 신고가**: 52주 신고가 달성 (Wclose >= 52_H)
- **-**: 해당 없음

#### D (Daily Signal)
- **✓ 급등**: 일일 급등 패턴 (DayJolts == 1)
- **✓ 브레이크**: 저항 돌파 (DayBreak == 1)
- **-**: 해당 없음

#### RS (Relative Strength Signal)
- **✓ 강세**: RS_4W > RS_SMA5 (4주 상대강도가 5일 이평 위)
- **✓ 약세**: RS_4W < RS_SMA5
- **-**: 데이터 없음

#### E (Earnings Signal)
- **✓ 양호**: 최근 분기 실적 발표 데이터 존재
- **-**: 데이터 없음

#### F (Fundamental Signal)
- **✓ 우수**: 펀더멘털 데이터 존재 (PBR, PSR, ROE 등)
- **-**: 데이터 없음

---

## 기술 명세

### show_ticker_signal_timeline() 함수

**파일**: main_auto_trade.py:961-1060

**시그니처**:
```python
async def show_ticker_signal_timeline(config: dict) -> None
```

**파라미터**:
- `config`: 시스템 설정 딕셔너리 (myStockInfo.yaml에서 로드)

**동작 흐름**:

1. **사용자 입력 수집**
   ```python
   symbols_input = input("종목 코드: ").strip().upper()
   symbols = [s.strip() for s in symbols_input.split(',')]
   ```

2. **분석 기간 계산**
   ```python
   period_choice = input("\n선택 (1-4, 기본값: 1): ").strip() or "1"

   period_mapping = {
       "1": 90,   # 3개월
       "2": 180,  # 6개월
       "3": 365,  # 1년
       "4": 730   # 2년
   }
   ```

3. **StagedPipelineService 실행**
   ```python
   pipeline = StagedPipelineService(
       config=config,
       market='US',
       area='US',
       start_day=data_start,
       end_day=end_date
   )

   pipeline_results = pipeline.run_staged_pipeline(symbols)
   ```

4. **데이터 구조 변환**
   ```python
   # {stage: {symbol: df}} → {symbol: {stage: df}}
   all_loaded_data = pipeline.data_loader.get_all_loaded_data()

   final_candidates_data = {}
   for stage, symbols_data in all_loaded_data.items():
       if isinstance(symbols_data, dict):
           for symbol, df in symbols_data.items():
               if symbol not in final_candidates_data:
                   final_candidates_data[symbol] = {}
               final_candidates_data[symbol][stage] = df
   ```

5. **타임라인 출력**
   ```python
   _print_ticker_signal_timeline(final_candidates_data, symbols_with_d_data, num_days=100)
   ```

### _print_ticker_signal_timeline() 함수

**파일**: main_auto_trade.py:120-297

**시그니처**:
```python
def _print_ticker_signal_timeline(
    candidates_data: Dict,
    symbols: List[str],
    num_days: int = 100
) -> None
```

**파라미터**:
- `candidates_data`: `{symbol: {stage: DataFrame}}` 형태의 데이터
- `symbols`: 출력할 종목 코드 리스트
- `num_days`: 출력할 거래일 수 (기본 100일)

**핵심 기능**:

#### 1. DateTime Index 변환 (lines 143-154)
```python
if not isinstance(df_D.index, pd.DatetimeIndex):
    if 'Date' in df_D.columns:
        df_D['Date'] = pd.to_datetime(df_D['Date'])
        df_D = df_D.set_index('Date')
    elif isinstance(df_D.index[0], (int, np.integer)):
        print(f"\n[{symbol}] 시그널 타임라인 - 날짜 정보 없음 (인덱스가 정수)")
        continue
    else:
        df_D.index = pd.to_datetime(df_D.index)
```

#### 2. 전체 Stage DataFrame Index 통일 (lines 165-183)
```python
signals = {}
for stage_name, stage_df in [
    ('W', stage_data.get('W')),
    ('D', df_D),
    ('RS', stage_data.get('RS')),
    ('E', stage_data.get('E')),
    ('F', stage_data.get('F'))
]:
    if stage_df is not None and len(stage_df) > 0:
        if not isinstance(stage_df.index, pd.DatetimeIndex):
            stage_df = stage_df.copy()
            if 'Date' in stage_df.columns:
                stage_df['Date'] = pd.to_datetime(stage_df['Date'])
                stage_df = stage_df.set_index('Date')
            elif not isinstance(stage_df.index[0], (int, np.integer)):
                stage_df.index = pd.to_datetime(stage_df.index)
        signals[stage_name] = stage_df
```

#### 3. 유연한 컬럼명 검색 (lines 191-196, 209-221)
```python
# Close price lookup
close_price = 0
for col in ['close', 'Dclose', 'Close']:
    if col in df_D.columns:
        close_price = df_D.loc[date, col]
        break

# Weekly signal lookup
w_close = 0
for col in ['close', 'Wclose', 'Close']:
    if col in w_data.columns:
        w_close = w_latest.get(col, 0)
        break

w_52h = 0
for col in ['52_H', '52_high', 'high_52w']:
    if col in w_data.columns:
        w_52h = w_latest.get(col, 0)
        break
```

#### 4. 시그널 판정 로직

**Weekly Signal**:
```python
if w_close > 0 and w_52h > 0 and w_close >= w_52h:
    w_sig = "✓ 신고가"
else:
    w_sig = "-"
```

**Daily Signal**:
```python
day_jolts = row.get('DayJolts', 0)
day_break = row.get('DayBreak', 0)

if day_jolts == 1:
    d_sig = "✓ 급등"
elif day_break == 1:
    d_sig = "✓ 브레이크"
else:
    d_sig = "-"
```

**RS Signal**:
```python
if 'RS_4W' in row and 'RS_SMA5' in row:
    rs_4w = row['RS_4W']
    rs_sma5 = row['RS_SMA5']
    if rs_4w > rs_sma5:
        rs_sig = "✓ 강세"
    else:
        rs_sig = "✓ 약세"
else:
    rs_sig = "-"
```

---

## 데이터 구조 인터페이스

### Input: StagedPipelineService 출력

```python
{
    "E": {  # Earnings stage
        "AAPL": pd.DataFrame([...]),
        "MSFT": pd.DataFrame([...])
    },
    "F": {  # Fundamental stage
        "AAPL": pd.DataFrame([...]),
        "MSFT": pd.DataFrame([...])
    },
    "W": {  # Weekly stage
        "AAPL": pd.DataFrame([...]),
        "MSFT": pd.DataFrame([...])
    },
    "RS": {  # Relative Strength stage
        "AAPL": pd.DataFrame([...]),
        "MSFT": pd.DataFrame([...])
    },
    "D": {  # Daily stage
        "AAPL": pd.DataFrame([...]),
        "MSFT": pd.DataFrame([...])
    }
}
```

### Converted: Timeline Function Input

```python
{
    "AAPL": {
        "E": pd.DataFrame([...]),
        "F": pd.DataFrame([...]),
        "W": pd.DataFrame([...]),
        "RS": pd.DataFrame([...]),
        "D": pd.DataFrame([...])
    },
    "MSFT": {
        "E": pd.DataFrame([...]),
        "F": pd.DataFrame([...]),
        "W": pd.DataFrame([...]),
        "RS": pd.DataFrame([...]),
        "D": pd.DataFrame([...])
    }
}
```

### DataFrame Schema

각 DataFrame은 다음 컬럼을 포함합니다 (자세한 명세는 [DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md) 참조):

**D (Daily)**:
- `Dopen`, `Dhigh`, `Dlow`, `Dclose`, `Dvolume`
- `DayJolts`, `DayBreak` (신호 컬럼)
- `SMA20`, `SMA50`, `SMA200`, `ADR`

**W (Weekly)**:
- `Wopen`, `Whigh`, `Wlow`, `Wclose`
- `52_H`, `52_L`, `1Year_H`

**RS (Relative Strength)**:
- `RS_4W`, `RS_12W`, `RS_SMA5`, `RS_SMA20`
- `Sector`, `Industry`, `Sector_RS_4W`

**E (Earnings)**:
- `EarningDate`, `eps`, `eps_yoy`, `revenue`, `rev_yoy`

**F (Fundamental)**:
- `EPS`, `EPS_YOY`, `REV_YOY`, `PBR`, `PSR`, `ROE`, `ROA`, `EBITDA`

---

## 에러 처리

### 1. 종목 데이터 없음
```python
if symbol not in candidates_data:
    print(f"[경고] {symbol}: 데이터 없음")
    continue
```

### 2. Daily 데이터 없음
```python
if 'D' not in stage_data:
    print(f"[경고] {symbol}: Daily 데이터 없음")
    continue
```

### 3. Integer Index 처리
```python
if isinstance(df_D.index[0], (int, np.integer)):
    print(f"\n[{symbol}] 시그널 타임라인 - 날짜 정보 없음 (인덱스가 정수)")
    continue
```

### 4. 컬럼 누락 처리
```python
# 유연한 컬럼명 검색으로 다양한 명명 규칙 대응
for col in ['close', 'Dclose', 'Close']:
    if col in df_D.columns:
        close_price = df_D.loc[date, col]
        break
else:
    close_price = 0  # 찾지 못한 경우 기본값
```

---

## 성능 최적화

### 1. DataFrame Index 사전 변환
모든 Stage DataFrame의 Index를 사전에 DatetimeIndex로 변환하여 반복적인 타입 체크 제거

### 2. 컬럼 검색 최적화
컬럼명 후보 리스트를 사용하여 빠른 Fallback 처리

### 3. 메모리 효율
- 최근 100일 데이터만 처리 (`tail(num_days)`)
- 불필요한 DataFrame 복사 최소화 (`.copy()` 선택적 사용)

---

## 향후 개선 사항

### 1. 시각화 강화
- 테이블 대신 그래프 차트 옵션 추가
- 시그널 패턴 하이라이팅
- 색상 코딩 (강세=초록, 약세=빨강)

### 2. 필터링 기능
- 특정 시그널 타입만 표시 (예: W와 D만)
- 시그널 발생일만 필터링

### 3. 내보내기 기능
- CSV 파일로 저장
- Excel 리포트 생성
- 이메일/텔레그램 전송

### 4. 비교 분석
- 여러 종목 시그널 동시 비교
- 섹터별 시그널 트렌드 분석

---

## 관련 문서

- **[AGENT_INTERFACES.md](AGENT_INTERFACES.md)**: `show_ticker_signal_timeline()` 인터페이스 정의
- **[INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md)**: DataFrame 구조 명세
- **[DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md)**: 컬럼 스펙 상세
- **[architecture/SERVICE_LAYER_BACKTEST_ARCHITECTURE.md](architecture/SERVICE_LAYER_BACKTEST_ARCHITECTURE.md)**: StagedPipelineService 아키텍처

---

**업데이트 정책**: 신규 시그널 타입 추가 또는 출력 형식 변경 시 즉시 업데이트
**관리자**: Orchestrator Agent
**피드백**: 사용자 경험 개선을 위한 피드백 환영
