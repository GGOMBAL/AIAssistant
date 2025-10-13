# Signal Configuration Guide
시그널 설정 가이드 - 사용자가 쉽게 시그널 조건을 변경하는 방법

## 📋 목차

1. [개요](#개요)
2. [설정 파일 구조](#설정-파일-구조)
3. [기본 사용법](#기본-사용법)
4. [조건 변경 예시](#조건-변경-예시)
5. [신규 지표 추가](#신규-지표-추가)
6. [고급 설정](#고급-설정)

---

## 개요

이 시스템은 **YAML 설정 파일**을 통해 시그널 발생 조건을 유연하게 변경할 수 있습니다.
코드를 직접 수정하지 않고도 RS 임계값, 펀더멘털 조건 등을 자유롭게 변경 가능합니다.

### 주요 기능

- ✅ **코드 수정 없이** 시그널 조건 변경
- ✅ RS, 주봉, 펀더멘털, 어닝스, 일봉 신호 각각 설정 가능
- ✅ 신호별 **가중치 조정**
- ✅ 신호 **활성화/비활성화** 토글
- ✅ **신규 지표 추가** 가능
- ✅ 설정 변경 후 **즉시 반영**

---

## 설정 파일 구조

### 파일 위치
```
config/signal_config.yaml
```

### 기본 구조

```yaml
strategy_name: "Multi-Timeframe Momentum Strategy"
version: "1.0"
enabled: true

# RS 신호 설정
rs_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "RS_4W"
      operator: ">="
      threshold: 90
      description: "4주 상대강도가 90 이상"

# 주봉 신호 설정
weekly_signal:
  enabled: true
  weight: 0.2
  conditions: [...]

# 펀더멘털 신호 설정
fundamental_signal:
  enabled: true
  weight: 0.2
  conditions: [...]

# 어닝스 신호 설정
earnings_signal:
  enabled: true
  weight: 0.2
  conditions: [...]

# 일봉 신호 설정
daily_rs_signal:
  enabled: true
  weight: 0.2
  breakout_types: {... }
```

---

## 기본 사용법

### 1. RS 임계값 변경

**시나리오**: RS >= 90 조건을 RS >= 80으로 완화하고 싶습니다.

**Before (기본값)**:
```yaml
rs_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "RS_4W"
      operator: ">="
      threshold: 90  # 현재 90
      description: "4주 상대강도가 90 이상"
```

**After (변경)**:
```yaml
rs_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "RS_4W"
      operator: ">="
      threshold: 80  # 90 → 80으로 변경
      description: "4주 상대강도가 80 이상"
```

**결과**: 이제 RS가 80 이상인 종목에서 신호가 발생합니다.

---

### 2. 신호 비활성화

**시나리오**: 어닝스 신호를 사용하지 않고 싶습니다.

```yaml
earnings_signal:
  enabled: false  # true → false로 변경
  weight: 0.2
  conditions: [...]
```

**결과**: 어닝스 신호가 계산되지 않으며, 전체 신호 강도 계산에서 제외됩니다.

---

### 3. 신호 가중치 조정

**시나리오**: RS 신호를 더 중요하게 만들고 싶습니다.

**Before**:
```yaml
rs_signal:
  weight: 0.2  # 20%

weekly_signal:
  weight: 0.2  # 20%
```

**After**:
```yaml
rs_signal:
  weight: 0.3  # 30%로 증가

weekly_signal:
  weight: 0.1  # 10%로 감소
```

**팁**: 전체 가중치의 합이 1.0이 되도록 조정하는 것이 좋습니다.

---

## 조건 변경 예시

### 예시 1: 펀더멘털 조건 강화

**Before**:
```yaml
fundamental_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "EPS_YOY"
      operator: ">"
      threshold: 0
      description: "EPS 전년 대비 성장"

    - indicator: "REV_YOY"
      operator: ">"
      threshold: 0
      description: "매출 전년 대비 성장"
```

**After (ROE 조건 추가)**:
```yaml
fundamental_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "EPS_YOY"
      operator: ">"
      threshold: 10  # 0 → 10으로 변경 (10% 이상 성장 요구)
      description: "EPS 전년 대비 10% 이상 성장"

    - indicator: "REV_YOY"
      operator: ">"
      threshold: 5  # 0 → 5로 변경
      description: "매출 전년 대비 5% 이상 성장"

    - indicator: "ROE"  # 신규 추가
      operator: ">="
      threshold: 15
      description: "ROE가 15% 이상"
```

**결과**: 더 엄격한 펀더멘털 조건이 적용됩니다.

---

### 예시 2: 일봉 브레이크아웃 조건 변경

**Before**:
```yaml
daily_rs_signal:
  breakout_types:
    highest_20:
      enabled: true
      lookback_period: 20
      rs_threshold: 90
      description: "20일 최고가 돌파 + RS >= 90"
```

**After**:
```yaml
daily_rs_signal:
  breakout_types:
    highest_20:
      enabled: true
      lookback_period: 30  # 20 → 30으로 변경
      rs_threshold: 85     # 90 → 85로 완화
      description: "30일 최고가 돌파 + RS >= 85"
```

**결과**: 30일 최고가 돌파 + RS 85 이상 조건으로 신호 발생.

---

## 신규 지표 추가

### 예시 1: PBR 조건 추가

```yaml
fundamental_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "EPS_YOY"
      operator: ">"
      threshold: 0
      description: "EPS 전년 대비 성장"

    - indicator: "REV_YOY"
      operator: ">"
      threshold: 0
      description: "매출 전년 대비 성장"

    # 신규 추가: PBR 조건
    - indicator: "PBR"
      operator: "<"
      threshold: 5
      description: "PBR이 5 미만 (저평가)"

    # 신규 추가: PSR 조건
    - indicator: "PSR"
      operator: "<"
      threshold: 3
      description: "PSR이 3 미만"
```

**주의**: 추가하려는 지표가 데이터프레임에 존재해야 합니다.

---

### 예시 2: RS_12W 조건 추가

```yaml
rs_signal:
  enabled: true
  weight: 0.2
  conditions:
    - indicator: "RS_4W"
      operator: ">="
      threshold: 90
      description: "4주 상대강도가 90 이상"

    # 신규 추가: 12주 RS 조건
    - indicator: "RS_12W"
      operator: ">="
      threshold: 85
      description: "12주 상대강도가 85 이상"
```

**결과**: RS_4W >= 90 AND RS_12W >= 85 조건이 모두 만족해야 RS 신호 발생.

---

## 고급 설정

### 1. 신호 결합 방식 변경

```yaml
signal_combination:
  # 최소 요구 신호 개수
  min_signals_required: 2  # 기본값: 2개 이상의 신호 필요

  # 신호 강도 계산 방식
  calculation_method: "weighted_average"  # "weighted_average" 또는 "majority_vote"

  # BUY 신호 발생을 위한 최소 신호 강도
  buy_threshold: 0.6  # 0.6 이상이어야 매수 신호 발생
```

**예시**: 더 보수적으로 변경
```yaml
signal_combination:
  min_signals_required: 3  # 3개 이상 신호 필요
  buy_threshold: 0.7       # 신호 강도 0.7 이상
```

---

### 2. 가격 타겟 조정

```yaml
price_targets:
  target_price_multiplier: 1.20   # 목표가: 진입가 대비 20% 상승
  losscut_price_multiplier: 0.95  # 손절가: 진입가 대비 5% 하락
```

**예시**: 리스크 리워드 비율 변경
```yaml
price_targets:
  target_price_multiplier: 1.30   # 목표가 30%로 증가
  losscut_price_multiplier: 0.90  # 손절가 10%로 확대
```

---

### 3. 리스크 관리 설정

```yaml
risk_management:
  max_position_size: 20  # 계좌 대비 최대 포지션 크기 (%)

  position_sizing_by_strength:
    enabled: true
    min_size: 5   # 최소 5%
    max_size: 20  # 최대 20%

  max_sector_concentration: 40  # 동일 섹터 최대 40%
```

---

## 설정 적용 방법

### 1. YAML 파일 수정

```bash
# 설정 파일 열기
nano config/signal_config.yaml

# 또는
vim config/signal_config.yaml
```

### 2. Python 코드에서 사용

```python
from project.strategy.signal_generation_service import SignalGenerationService

# 기본 설정 파일 사용
signal_service = SignalGenerationService(area='US')

# 또는 커스텀 설정 파일 사용
signal_service = SignalGenerationService(
    area='US',
    config_path='/path/to/custom_signal_config.yaml'
)

# 신호 생성
signals = signal_service.generate_comprehensive_signals(
    df_daily=df_D['AAPL'],
    df_weekly=df_W['AAPL'],
    df_rs=df_RS['AAPL'],
    df_fundamental=df_F['AAPL'],
    df_earnings=df_E['AAPL']
)
```

### 3. 설정 확인

```python
from project.strategy.signal_config_loader import SignalConfigLoader

# 설정 로더 생성
loader = SignalConfigLoader()

# 설정 요약 출력
loader.print_summary()

# 특정 값 확인
print(f"RS Threshold: {loader.get_rs_threshold()}")
print(f"RS Signal Weight: {loader.get_signal_weight('rs')}")
```

---

## 연산자 목록

설정 파일에서 사용 가능한 연산자:

| 연산자 | 의미 | 예시 |
|--------|------|------|
| `>` | 초과 | `threshold: 10` → 10 초과 |
| `>=` | 이상 | `threshold: 90` → 90 이상 |
| `<` | 미만 | `threshold: 5` → 5 미만 |
| `<=` | 이하 | `threshold: 100` → 100 이하 |
| `==` | 같음 | `threshold: 0` → 0과 같음 |
| `!=` | 다름 | `threshold: 0` → 0이 아님 |

---

## 자주 묻는 질문 (FAQ)

### Q1: 설정을 변경했는데 반영이 안됩니다.

**A**: 프로그램을 재시작하거나, `config_loader.reload()`를 호출하세요.

```python
signal_service.config_loader.reload()
```

### Q2: 여러 조건을 OR로 연결하고 싶습니다.

**A**: 현재는 AND 조건만 지원합니다. OR 조건이 필요한 경우 별도의 signal_type으로 분리하세요.

### Q3: 새로운 지표를 추가하려면 어떻게 하나요?

**A**:
1. DataFrameGenerator에서 해당 지표를 계산
2. signal_config.yaml에 조건 추가
3. 필요시 SignalGenerationService 코드 수정

### Q4: 설정 파일 문법이 틀렸는지 확인하려면?

**A**: YAML validator를 사용하거나, Python에서 직접 로드해보세요:

```python
import yaml
with open('config/signal_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(config)
```

---

## 추가 리소스

- [YAML 문법 가이드](https://yaml.org/)
- [SignalConfigLoader API 문서](../project/strategy/signal_config_loader.py)
- [SignalGenerationService API 문서](../project/strategy/signal_generation_service.py)

---

**마지막 업데이트**: 2025-10-13
**작성자**: AI Trading System Team
