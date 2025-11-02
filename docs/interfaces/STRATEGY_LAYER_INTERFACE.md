# Strategy Layer Interface Specification

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Strategy Agent
**Status**: Active

---

## 1. Overview

### Purpose
Strategy Layer는 Indicator Layer에서 제공한 기술지표 데이터를 분석하여 매매 신호를 생성합니다.

### Main Responsibilities
- 다중 타임프레임 분석 (일봉, 주봉, RS)
- 펀더멘털 및 어닝스 분석
- 종합 매매 신호 생성 (BUY/SELL/HOLD)
- 목표가 및 손절가 계산
- 신호 강도 및 신뢰도 평가

### Key Components
- `SignalGenerationService`: 메인 시그널 생성 서비스
- `PositionManager`: 포지션 관리 및 손절가 계산 (Stepped Trailing Stop)
- `PositionSizingService`: 포지션 사이즈 계산
- `AccountAnalysisService`: 계좌 분석 및 리밸런싱

---

## 2. Input Interface

### 2.1. SignalGenerationService 초기화

```python
def __init__(
    self,
    area: str = 'US',           # 시장 지역
    trading_mode: bool = False  # 실거래 모드 여부
)
```

**Parameters**:
- `area` (str, optional): 시장 지역 코드 (기본값: 'US')
- `trading_mode` (bool, optional): 실거래 모드 활성화 (기본값: False)

### 2.2. 종합 시그널 생성 메서드

```python
def generate_comprehensive_signals(
    self,
    df_daily: pd.DataFrame,              # 필수: 일간 데이터
    df_weekly: pd.DataFrame = None,      # 선택: 주간 데이터
    df_rs: pd.DataFrame = None,          # 선택: RS 데이터
    df_fundamental: pd.DataFrame = None, # 선택: 펀더멘털 데이터
    df_earnings: pd.DataFrame = None     # 선택: 어닝스 데이터
) -> Dict[str, Any]
```

**Parameters**:
- `df_daily` (pd.DataFrame, **required**): 일간 OHLCV 데이터
  - 필수 컬럼: `Dopen`, `Dhigh`, `Dlow`, `Dclose`, `Dvolume`
  - 기술지표: `SMA20`, `SMA50`, `SMA200`, `ADR`, `Highest_1Y` 등

- `df_weekly` (pd.DataFrame, optional): 주간 데이터
  - 컬럼: `Wopen`, `Whigh`, `Wlow`, `Wclose`, `52_H`, `52_L`, `1Year_H`, `2Year_H` 등

- `df_rs` (pd.DataFrame, optional): 상대강도 데이터
  - 컬럼: `RS_4W`, `RS_12W`, `Sector`, `Industry`, `Sector_RS_4W` 등

- `df_fundamental` (pd.DataFrame, optional): 펀더멘털 데이터
  - 컬럼: `REV_YOY`, `EPS_YOY`, `MarketCapitalization`, `PBR`, `ROE` 등
  - **Unit**: Growth rates are in decimal format (0.1 = 10%)

- `df_earnings` (pd.DataFrame, optional): 어닝스 데이터
  - 컬럼: `EarningDate`, `eps`, `eps_yoy`, `revenue`, `rev_yoy` 등
  - **Unit**: Growth rates are in decimal format (0.25 = 25%), automatically converted by Indicator Layer

**Constraints**:
- `df_daily`는 최소 200일 이상의 데이터 필요 (SMA200 계산용)
- 모든 DataFrame은 DatetimeIndex 사용
- 선택 파라미터가 None인 경우 해당 시그널은 0으로 처리

---

## 3. Output Interface

### 3.1. 출력 데이터 구조

```python
{
    'final_signal': SignalType,      # BUY | SELL | HOLD
    'signal_strength': float,        # 0.0 ~ 1.0
    'signal_components': {
        'weekly': int,               # 0 or 1
        'rs': int,                   # 0 or 1
        'fundamental': int,          # 0 or 1
        'earnings': int,             # 0 or 1
        'daily_rs': int              # 0 or 1
    },
    'target_price': float,           # 목표가 (USD)
    'losscut_price': float,          # 손절가 (USD)
    'signal_type': BreakoutType,     # 신호 타입
    'confidence': float              # 신뢰도 (0.0 ~ 1.0)
}
```

### 3.2. 필드 상세 설명

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| final_signal | SignalType | BUY/SELL/HOLD | 최종 매매 신호 |
| signal_strength | float | 0.0 ~ 1.0 | 신호 강도 (1.0 = 최강) |
| weekly | int | 0 or 1 | 주봉 조건 통과 여부 |
| rs | int | 0 or 1 | 상대강도 조건 통과 여부 |
| fundamental | int | 0 or 1 | 펀더멘털 조건 통과 여부 |
| earnings | int | 0 or 1 | 어닝스 조건 통과 여부 |
| daily_rs | int | 0 or 1 | 일봉+RS 결합 신호 |
| target_price | float | > 0 | 목표 매도가 |
| losscut_price | float | > 0 | 손절가 |
| signal_type | BreakoutType | enum | 돌파 타입 (2Y/1Y/6M/3M/1M) |
| confidence | float | 0.0 ~ 1.0 | 신호 신뢰도 |

### 3.3. SignalType Enum

```python
class SignalType(Enum):
    BUY = "BUY"      # 매수 신호
    SELL = "SELL"    # 매도 신호
    HOLD = "HOLD"    # 관망
```

### 3.4. BreakoutType Enum

```python
class BreakoutType(Enum):
    BREAKOUT_2Y = "Breakout_2Y"    # 2년 신고가 돌파
    BREAKOUT_1Y = "Breakout_1Y"    # 1년 신고가 돌파
    BREAKOUT_6M = "Breakout_6M"    # 6개월 신고가 돌파
    BREAKOUT_3M = "Breakout_3M"    # 3개월 신고가 돌파
    BREAKOUT_1M = "Breakout_1M"    # 1개월 신고가 돌파
    RS_12W_1M = "RS_12W_1M"        # RS 기반 신호
```

---

## 4. Signal Generation Logic

### 4.1. 주봉 신호 (Weekly Signal)

5가지 조건을 모두 만족해야 신호 발생:

1. `1Year_H == 2Year_H` (1년 고점 = 2년 고점)
2. `2Year_L < 1Year_L` (2년 저점 < 1년 저점)
3. `52_H <= 52_H.shift(2) * 1.05` (52주 고점 변동 5% 이내)
4. `Wclose.shift(1) > 52_L * 1.3` (전주 종가 > 52주 저점 * 1.3)
5. `Wclose.shift(1) > 52_H * 0.7` (전주 종가 > 52주 고점 * 0.7)

### 4.2. RS 신호 (Relative Strength Signal)

```python
RS_4W >= 90  # 상위 10% 이내
```

### 4.3. 펀더멘털 신호 (Fundamental Signal)

3가지 조건을 모두 만족:

1. `MarketCapitalization >= 2B` (시가총액 20억 달러 이상)
2. `REV_YOY >= 0.1` (매출 성장률 10% 이상, decimal format)
3. `EPS_YOY >= 0.1` (EPS 성장률 10% 이상, decimal format)

**Note**: All growth rates use decimal format (0.1 = 10%, 0.25 = 25%)

### 4.4. 어닝스 신호 (Earnings Signal)

최근 어닝스 발표 후 긍정적 서프라이즈

### 4.5. 최종 신호 결합 로직

```python
# 2개 이상의 신호가 발생하면 BUY
if (weekly + rs + daily_rs) >= 2:
    final_signal = SignalType.BUY
```

---

## 5. Error Handling

### 5.1. Exception Types

| Exception | Condition | Recovery |
|-----------|-----------|----------|
| `InvalidDataFrameError` | 필수 컬럼 누락 | ValueError 발생 |
| `InsufficientDataError` | 데이터 부족 (< 200일) | HOLD 신호 반환 |
| `InvalidDateRangeError` | 날짜 범위 오류 | ValueError 발생 |

### 5.2. Error Response Format

에러 발생 시 기본 응답 반환:

```python
{
    'final_signal': SignalType.HOLD,
    'signal_strength': 0.0,
    'signal_components': {},
    'target_price': 0.0,
    'losscut_price': 0.0,
    'signal_type': None,
    'confidence': 0.0,
    'error': {
        'code': 'ERROR_CODE',
        'message': 'Error description'
    }
}
```

---

## 6. Examples

### 6.1. Basic Usage

```python
from project.strategy.signal_generation_service import SignalGenerationService
from project.indicator.data_frame_generator import DataFrameGenerator

# 1. Indicator Layer에서 데이터 로드
generator = DataFrameGenerator(
    universe=["AAPL"],
    market="US",
    area="US"
)
generator.load_data_from_database()

# 2. Strategy Layer 초기화
signal_service = SignalGenerationService(area='US', trading_mode=False)

# 3. 신호 생성
signals = signal_service.generate_comprehensive_signals(
    df_daily=generator.df_D["AAPL"],
    df_weekly=generator.df_W["AAPL"],
    df_rs=generator.df_RS["AAPL"],
    df_fundamental=generator.df_F["AAPL"],
    df_earnings=generator.df_E["AAPL"]
)

# 4. 결과 출력
print(f"Final Signal: {signals['final_signal'].value}")
print(f"Signal Strength: {signals['signal_strength']:.2f}")
print(f"Target Price: ${signals['target_price']:.2f}")
print(f"Losscut Price: ${signals['losscut_price']:.2f}")
print(f"Confidence: {signals['confidence']:.2f}")
```

### 6.2. Minimal Usage (Daily Data Only)

```python
# 일간 데이터만 사용
signals = signal_service.generate_comprehensive_signals(
    df_daily=df_daily
)

# weekly, rs, fundamental, earnings는 None이므로
# 해당 시그널 컴포넌트는 0으로 처리됨
```

### 6.3. Signal Component Analysis

```python
# 개별 신호 컴포넌트 확인
components = signals['signal_components']

print(f"Weekly Signal: {components['weekly']}")
print(f"RS Signal: {components['rs']}")
print(f"Fundamental Signal: {components['fundamental']}")
print(f"Earnings Signal: {components['earnings']}")
print(f"Daily+RS Signal: {components['daily_rs']}")

# 총 통과한 조건 수
total_signals = sum(components.values())
print(f"Total signals passed: {total_signals}")
```

---

## 7. Dependencies

### 7.1. Internal Dependencies
- **Indicator Layer**: 기술지표 계산된 DataFrame 제공
  - `DataFrameGenerator`: 데이터 로드 및 전처리

### 7.2. External Libraries
- `pandas >= 1.5.0`: DataFrame 처리
- `numpy >= 1.23.0`: 수치 계산

### 7.3. Data Flow

```
Indicator Layer (df_D, df_W, df_RS, df_F, df_E)
        ↓
Strategy Layer (SignalGenerationService)
        ↓
Service Layer (DailyBacktestService / OrderManager)
```

---

## 8. Performance Characteristics

### 8.1. Processing Time
- 단일 종목 시그널 생성: < 10ms
- 500개 종목 배치 처리: < 5초

### 8.2. Memory Usage
- 종목당 메모리: ~1MB
- 500개 종목: ~500MB

### 8.3. Optimization Tips
- 배치 처리 시 멀티프로세싱 사용
- 시그널 캐싱으로 중복 계산 방지
- 필수 컬럼만 로드하여 메모리 절약

---

## 9. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-09 | Initial version | Strategy Agent |

---

## 10. Notes

### Known Limitations
- 일간 데이터 200일 미만 시 SMA200 계산 불가
- RS 데이터 없을 시 RS 신호 생성 불가
- 주봉 데이터 최소 3개 필요 (shift(2) 사용)

### Future Enhancements
- [ ] 머신러닝 기반 신호 강도 예측
- [ ] 신호 백테스팅 자동화
- [ ] 실시간 신호 스트리밍 지원
- [ ] 커스텀 전략 플러그인 시스템

### Related Documents
- `STRATEGY_MODULES.md`: 전략 모듈 상세 설명
- `SIGNAL_GENERATION_SPEC.md`: 시그널 생성 알고리즘 상세
- `docs/INTERFACE_SPECIFICATION.md`: 레이어 간 데이터 인터페이스

---

## 11. PositionManager - Stepped Trailing Stop

### 11.1. Overview

`PositionManager` 클래스는 포지션 관리 및 손절가 계산을 담당합니다. 특히, **Stepped Trailing Stop** 로직을 구현하여 일반적인 트레일링 스탑과 달리 단계별 손절가 보호 구간을 제공합니다.

### 11.2. Initialization

```python
from project.strategy.position_manager import PositionManager

position_manager = PositionManager(config)
```

**Config Parameters**:
```python
{
    'market_specific_configs': {
        'US': {
            'std_risk_per_trade': 0.05,          # RISK (5% = 1 unit)
            'min_loss_cut_percentage': 0.03      # Minimum losscut (-3%)
        }
    }
}
```

### 11.3. Stepped Trailing Stop Logic

**핵심 개념**:
- **Profit Units**: 수익을 RISK 단위로 나눈 값 (floor 연산)
- **Stepped Protection**: 수익 단위별로 손절가가 단계적으로 상승
- **NOT Constant Buffer**: 일반적인 트레일링 스탑과 달리 고정 % 버퍼가 아님

**Formula**:
```python
profit_units = int((current_profit) / RISK)

if profit_units < 1:
    losscut = entry_price * (1 - min_loss_cut_percentage)  # -3% 고정
else:
    losscut = entry_price * (1 + (profit_units - 1) * RISK)
```

**Example Table** (Entry=$150, RISK=5%):

| Profit Range | Profit Units | Losscut Price | From Entry | Protection Zone |
|--------------|--------------|---------------|------------|-----------------|
| +0% ~ +4.99% | 0 | $145.50 | -3% | Initial Stop |
| +5% ~ +9.99% | 1 | $150.00 | 0% | Breakeven |
| +10% ~ +14.99% | 2 | $157.50 | +5% | Profit Lock 1 |
| +15% ~ +19.99% | 3 | $165.00 | +10% | Profit Lock 2 |
| +20% ~ +24.99% | 4 | $172.50 | +15% | Profit Lock 3 |

### 11.4. Key Methods

#### 11.4.1. calc_losscut_price()

```python
def calc_losscut_price(
    self,
    again: float,              # 누적 수익률 (1.0 = 본전, 1.10 = +10%)
    current_losscut: float,    # 현재 손절가
    avg_price: float,          # 평균 진입가
    risk: Optional[float] = None  # RISK (기본: 0.05)
) -> float:
    """
    단계별 트레일링 스탑 손절가 계산

    Returns:
        새로운 손절가 (현재 손절가보다 높을 때만 업데이트)
    """
```

**Behavior**:
- 손절가는 **올라가기만** 하고 절대 내려가지 않음
- 최소 손절가 (-3%) 보장
- 단계별 보호 구간 생성

#### 11.4.2. update_position_status()

```python
def update_position_status(
    self,
    position: Dict[str, Any],  # 현재 포지션 정보
    current_price: float       # 현재 가격
) -> Dict[str, Any]:
    """
    포지션 상태 업데이트 (AGain 계산 및 손절가 갱신)

    Returns:
        업데이트된 포지션 정보 (losscut_price, again, profit_loss 등)
    """
```

### 11.5. Usage Example

```python
# 1. PositionManager 초기화
from project.strategy.position_manager import PositionManager

config = {
    'market_specific_configs': {
        'US': {
            'std_risk_per_trade': 0.05,
            'min_loss_cut_percentage': 0.03
        }
    }
}
position_manager = PositionManager(config)

# 2. 포지션 정보
position = {
    'symbol': 'AAPL',
    'quantity': 100,
    'avg_price': 150.0,
    'current_price': 150.0,
    'losscut_price': 145.50,  # Initial: -3%
    'again': 1.0,
    'risk': 0.05
}

# 3. 가격이 +10% 상승 -> $165.00
updated_position = position_manager.update_position_status(
    position=position,
    current_price=165.0
)

print(f"New Losscut: ${updated_position['losscut_price']:.2f}")
# Output: $157.50 (진입가 대비 +5%)

# 4. 가격이 +15% 상승 -> $172.50
updated_position = position_manager.update_position_status(
    position=updated_position,
    current_price=172.50
)

print(f"New Losscut: ${updated_position['losscut_price']:.2f}")
# Output: $165.00 (진입가 대비 +10%)
```

### 11.6. Integration Points

**Backtest**:
- `project/service/daily_backtest_service.py`
- `_calculate_refer_losscut_price()` 함수에서 동일한 Stepped Trailing Stop 로직 사용

**Auto-Trading**:
- `main_auto_trade.py`
- WebSocket 실시간 가격 업데이트 시 `PositionManager.update_position_status()` 호출

### 11.7. Comparison: Traditional vs Stepped Trailing Stop

| Aspect | Traditional Trailing Stop | Stepped Trailing Stop |
|--------|---------------------------|------------------------|
| Buffer Type | Constant % from current price | Stepped zones by profit units |
| Example (+8% profit) | Losscut at +3% (8%-5%) | Losscut at 0% (unit 1) |
| Example (+11% profit) | Losscut at +6% (11%-5%) | Losscut at +5% (unit 2) |
| Profit Protection | Linear, smooth | Stepped, zone-based |
| Risk Control | Fixed % buffer always maintained | Discrete protection levels |

**Why Stepped?**:
- 명확한 보호 구간 (5% 단위)
- 과도한 손절 방지 (일시적 조정에 강함)
- 심리적 안정감 (명확한 목표 지점)
