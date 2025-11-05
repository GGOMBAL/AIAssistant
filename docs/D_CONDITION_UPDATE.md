# D 조건 업데이트 - 신고가 돌파 분리

**업데이트 날짜**: 2025-11-06
**변경 파일**: `project/strategy/staged_signal_service.py`

## 변경 요약

D(Daily) 조건의 신고가 돌파 체크를 **백테스트에서만 사용**하도록 수정했습니다.

### 변경 전

- **백테스트 모드**: 신고가 돌파 조건 적용 (Dhigh > Highest_1M/3M/6M/1Y/2Y)
- **오토 트레이딩 모드**: 신고가 돌파 조건 적용 (동일)
- **결과**: 조정/횡보장에서 매수 후보 종목이 0개 발생

### 변경 후

- **백테스트 모드** (`execution_mode='analysis'`): 신고가 돌파 조건 적용 (기존 방식 유지)
- **오토 트레이딩 모드** (`execution_mode='trading'` or `'live'`): 신고가 돌파 조건 **미적용**, 모든 종목 통과
- **결과**: E→F→W→RS 단계를 통과한 모든 종목이 최종 매수 후보로 선정

---

## 상세 변경사항

### 1. 신고가 돌파 조건 분리

**파일**: `project/strategy/staged_signal_service.py`
**메서드**: `_stage_daily_signal()`
**라인**: ~690

```python
# 변경 전: 모든 모드에서 신고가 돌파 체크
logger.info("[Daily Stage] ENABLED - Applying daily breakout filters")

# 변경 후: execution_mode에 따라 분기
if self.execution_mode in ['trading', 'live']:
    logger.info("[Daily Stage] AUTO TRADING MODE - Passing ALL symbols (no breakout filtering)")
    logger.info("[Daily Stage] Breakout filtering is only applied in backtest/analysis mode")

    # 모든 종목 통과 (신호 컬럼만 추가)
    for symbol in symbols:
        df['BuySig'] = 1.0  # 모든 종목에 매수 신호
        df['SellSig'] = 0.0
        df['signal'] = 1.0
        # ... TargetPrice, LossCutPrice 계산

    return StageResult(
        passed_symbols=symbols,
        signals={symbol: 1.0 for symbol in symbols},
        stage_name='Daily (Auto Trading - No Breakout Filter)',
        total_input=len(symbols),
        total_passed=len(symbols),
        filter_rate=1.0
    )

# 백테스트 모드: 기존 신고가 돌파 로직 수행
logger.info("[Daily Stage] BACKTEST MODE - Applying daily breakout filters")
# ... (기존 돌파 체크 로직)
```

### 2. TargetPrice 계산 방식 변경

**변경 내용**: TargetPrice를 Highest 값들 중 **최소값**으로 설정

#### 오토 트레이딩 모드 (신규 추가)

```python
# Calculate TargetPrice: minimum of all Highest values
highest_cols = ['Highest_1M', 'Highest_3M', 'Highest_6M', 'Highest_1Y', 'Highest_2Y']
available_highest = [col for col in highest_cols if col in df.columns]

if available_highest:
    # For each row, find minimum of available Highest values
    df['TargetPrice'] = df[available_highest].min(axis=1)
else:
    # Fallback: 20% above current close
    df['TargetPrice'] = df.get('Dclose', df.get('close', 0)) * 1.20

# LossCutPrice: use configured ratio
losscut_ratio = 0.97  # Default 3% stop loss
if self.signal_config_loader:
    losscut_ratio = self.signal_config_loader.get_daily_losscut_ratio()
df['LossCutPrice'] = df.get('Dclose', df.get('close', 0)) * losscut_ratio
```

#### 백테스트 모드 (신규 추가)

백테스트 모드에도 동일한 TargetPrice 계산 로직 추가:

```python
# Initialize signal columns for backtest
df['BuySig'] = 0.0
df['SellSig'] = 0.0
df['signal'] = 0.0
if 'Type' not in df.columns:
    df['Type'] = 'Staged'

# Calculate TargetPrice: minimum of all Highest values (for each date)
highest_cols = ['Highest_1M', 'Highest_3M', 'Highest_6M', 'Highest_1Y', 'Highest_2Y']
available_highest = [col for col in highest_cols if col in df.columns]

if available_highest:
    df['TargetPrice'] = df[available_highest].min(axis=1)
else:
    df['TargetPrice'] = df.get('Dclose', df.get('close', 0)) * 1.20

# LossCutPrice
losscut_ratio = 0.97
if self.signal_config_loader:
    losscut_ratio = self.signal_config_loader.get_daily_losscut_ratio()
df['LossCutPrice'] = df.get('Dclose', df.get('close', 0)) * losscut_ratio
```

---

## TargetPrice 계산 예시

### AAPL (2025-11-04)

```
Highest_1M:  $277.32
Highest_3M:  $277.32
Highest_6M:  $277.32
Highest_1Y:  $277.32
Highest_2Y:  $277.32

TargetPrice = min($277.32, $277.32, $277.32, $277.32, $277.32) = $277.32
```

### MSFT (2025-11-04)

```
Highest_1M:  $553.72  ← 최소값
Highest_3M:  $553.72
Highest_6M:  $555.45
Highest_1Y:  $555.45
Highest_2Y:  $555.45

TargetPrice = min($553.72, $553.72, $555.45, $555.45, $555.45) = $553.72
```

### 의미

- TargetPrice는 가장 가까운 저항선 (최근 고점)으로 설정
- 보수적인 목표가 설정 (가장 낮은 고점 = 가장 가까운 목표)
- 실현 가능성이 높은 이익 실현 구간

---

## 테스트 결과

### 오토 트레이딩 모드 테스트

**테스트 파일**: `Test/debug_auto_trading_staged_pipeline.py`

**결과 (변경 전)**:
```
Stage 5: Daily
  Input:  7 symbols
  Passed: 0 symbols  ← 모든 종목 탈락
```

**결과 (변경 후)**:
```
Stage 5: Daily (Auto Trading - No Breakout Filter)
  Input:  7 symbols
  Passed: 7 symbols  ← 모든 종목 통과

Final Candidates: 7 symbols
  - AAPL, MSFT, GOOGL, AMZN, META, NFLX, PLTR
```

### TargetPrice 검증

**테스트 파일**: `Test/verify_target_price.py`

**검증 결과**:
```
AAPL:
  Expected TargetPrice (min): $277.32
  Actual TargetPrice:          $277.32
  [OK] TargetPrice is correct!

GOOGL:
  Expected TargetPrice (min): $291.59
  Actual TargetPrice:          $291.59
  [OK] TargetPrice is correct!

MSFT:
  Expected TargetPrice (min): $553.72
  Actual TargetPrice:          $553.72
  [OK] TargetPrice is correct!
```

---

## 영향 범위

### 영향을 받는 기능

1. **오토 트레이딩** (`main_auto_trade.py` - Menu 3)
   - D 조건이 더 이상 종목을 필터링하지 않음
   - E→F→W→RS 단계를 통과한 모든 종목이 최종 후보
   - 매수 후보 종목 수 증가 예상

2. **백테스트** (`main_auto_trade.py` - Menu 1)
   - **영향 없음** - 기존 방식 유지
   - 신고가 돌파 조건 계속 적용
   - TargetPrice 계산만 변경 (최소 Highest 값 사용)

3. **Signal Timeline** (`main_auto_trade.py` - Menu 4)
   - **영향 없음** - 백테스트와 동일하게 작동
   - `execution_mode='analysis'` 사용

### 영향을 받지 않는 기능

- Individual Symbol Check (Menu 2)
- YAML Strategy 백테스트 (별도 시스템)

---

## 전략 철학 변경

### 변경 전: 모멘텀 돌파 전략

- **개념**: 신고가를 돌파하는 종목만 매수
- **장점**: 강한 모멘텀 확인, 명확한 진입 시점
- **단점**: 횡보/조정장에서 후보 부족

### 변경 후: 품질 필터링 전략

- **개념**: E/F/W/RS 조건을 만족하는 우량 종목 매수
- **장점**: 시장 국면에 관계없이 후보 확보, 조기 진입 가능
- **단점**: 추가 하락 위험 존재 (손절가 관리 중요)

---

## 사용자 영향

### 오토 트레이딩 사용자

**긍정적 변화**:
- 조정/횡보장에서도 매수 후보 발견 가능
- 신고가 돌파 전 조기 진입으로 더 낮은 가격 매수
- E/F/W/RS 조건을 만족하는 펀더멘털 우수 종목 선별

**주의사항**:
- 추가 하락 위험 존재 (손절가 철저히 준수 필요)
- 횡보 기간 연장 가능성
- 포지션 크기 관리 중요

### 백테스트 사용자

**변화 없음**:
- 기존 백테스트 결과와 동일한 방식 유지
- 신고가 돌파 조건 계속 적용
- 과거 성과 비교 가능

---

## 설정 파일 연동

### execution_mode 설정

`config/strategy_signal_config.yaml` 파일에서 관리:

```yaml
execution_modes:
  # Backtest mode (Menu 1)
  backtest:
    use_staged_pipeline: true
    execution_mode: 'analysis'  # 신고가 돌파 적용
    is_backtest: true

  # Live trading (Menu 3)
  live_trading:
    use_staged_pipeline: true
    execution_mode: 'live'      # 신고가 돌파 미적용
    is_backtest: false

  # Signal timeline (Menu 4)
  timeline:
    use_staged_pipeline: true
    execution_mode: 'analysis'  # 신고가 돌파 적용
    is_backtest: false
```

---

## 코드 참조

### 주요 변경 위치

**파일**: `project/strategy/staged_signal_service.py`

| 라인 범위 | 변경 내용 |
|----------|----------|
| 690-736 | 오토 트레이딩 모드 신규 로직 추가 |
| 738-741 | 백테스트 모드 구분 로그 추가 |
| 824-846 | 백테스트 모드 TargetPrice/LossCutPrice 계산 추가 |

---

## 추가 고려사항

### 리스크 관리

1. **손절가 준수**: 오토 트레이딩에서 LossCutPrice 철저히 관리
2. **포지션 크기**: 조기 진입으로 인한 리스크 고려하여 포지션 조절
3. **시장 상황 모니터링**: 전반적인 시장 하락 시 진입 보류 고려

### 향후 개선 방향

1. **하이브리드 조건**: 신고가 근접 시 가중치 추가
2. **변동성 조건**: 저변동성 횡보 시 진입 지양
3. **섹터 모멘텀**: 섹터 전체 약세 시 진입 보류

---

## 관련 문서

- `docs/BACKTEST_COMPARISON.md` - 백테스트 시스템 비교
- `docs/rules/BACKTEST_VS_TRADING.md` - 백테스트 vs 트레이딩 모드
- `config/strategy_signal_config.yaml` - 전략 설정 파일

---

## 변경 이력

| 날짜 | 변경사항 | 작성자 |
|------|----------|--------|
| 2025-11-06 | D 조건 신고가 돌파 분리, TargetPrice 계산 변경 | Claude |
