# How to Change Signal Conditions

**Version**: 1.0
**Last Updated**: 2025-10-18

---

## 📋 Overview

이 가이드는 **Signal 조건을 YAML 파일로 쉽게 변경하는 방법**을 설명합니다.

---

## 🎯 빠른 시작

### Step 1: 설정 파일 열기

```bash
# YAML 설정 파일 위치
config/strategy_signal_config.yaml
```

### Step 2: 조건 수정

예시: Fundamental Signal의 최소 시가총액을 **3B USD**로 변경

```yaml
# Before
fundamental_signal:
  market_cap:
    min: 2000000000         # 2 Billion USD

# After
fundamental_signal:
  market_cap:
    min: 3000000000         # 3 Billion USD
```

### Step 3: 저장 및 재시작

```bash
# 파일 저장 후 프로그램 재시작
python main_auto_trade.py
```

---

## 📊 주요 변경 시나리오

### 시나리오 1: Fundamental Signal 완화 (더 많은 종목 선정)

**목표**: 성장률 기준을 10% → 5%로 낮춰서 더 많은 종목 통과

```yaml
fundamental_signal:
  revenue:
    min_yoy: 0.05           # 10% → 5%
  eps:
    min_yoy: 0.05           # 10% → 5%
```

**효과**:
- ✅ 성장률 5~10% 종목도 통과
- ⚠️ 종목 수 증가 → 리스크 증가 가능

---

### 시나리오 2: Fundamental Signal 강화 (더 엄격한 선정)

**목표**: 시가총액 기준을 2B → 5B USD로 높여서 대형주만 선정

```yaml
fundamental_signal:
  market_cap:
    min: 5000000000         # 2B → 5B USD
```

**효과**:
- ✅ 대형주만 선정 → 리스크 감소
- ⚠️ 종목 수 감소 → 기회 감소

---

### 시나리오 3: Weekly Signal 조정

**목표**: 52주 고점 안정성 조건 완화 (5% → 10%)

```yaml
weekly_signal:
  high_stability:
    factor: 1.10            # 1.05 (5%) → 1.10 (10%)
```

**효과**:
- ✅ 변동성 높은 종목도 통과
- ⚠️ 불안정한 종목 증가 가능

---

### 시나리오 4: RS Signal 조정

**목표**: RS 임계값을 90 → 80으로 낮춰서 더 많은 종목 통과

```yaml
rs_signal:
  threshold: 80             # 90 → 80 (상위 20%)
```

**효과**:
- ✅ 상대 강도 80~90 종목도 통과
- ⚠️ 시장 대비 약한 종목도 포함될 수 있음

---

### 시나리오 5: Daily Signal 손절 비율 조정

**목표**: 손절 비율을 3% → 5%로 완화

```yaml
daily_signal:
  prices:
    losscut_ratio: 0.95     # 0.97 (3% 손절) → 0.95 (5% 손절)
```

**효과**:
- ✅ 손절 여유 증가
- ⚠️ 손실 폭 증가 가능

---

## 🔧 모든 설정 항목

### 1️⃣ Earnings Signal (E)

| 항목 | 현재값 | 설명 | 변경 시 효과 |
|------|-------|------|-------------|
| `revenue.min_prev_yoy` | `0.0` | 이전 분기 최소 매출 YoY | 높이면 → 더 엄격 |
| `eps.min_prev_yoy` | `0.0` | 이전 분기 최소 EPS YoY | 높이면 → 더 엄격 |
| `revenue.require_growth` | `true` | 이전 대비 성장 필수 | false → 완화 |
| `eps.require_growth` | `true` | 이전 대비 성장 필수 | false → 완화 |

---

### 2️⃣ Fundamental Signal (F)

| 항목 | 현재값 | 설명 | 변경 시 효과 |
|------|-------|------|-------------|
| `market_cap.min` | `2,000,000,000` | 최소 시가총액 (USD) | 높이면 → 대형주만 |
| `market_cap.max` | `20,000,000,000,000` | 최대 시가총액 (USD) | 낮추면 → 소형주 제외 |
| `revenue.min_yoy` | `0.10` (10%) | 최소 매출 YoY | 높이면 → 더 엄격 |
| `revenue.min_prev_yoy` | `0.0` (0%) | 이전 분기 최소 매출 YoY | 높이면 → 더 엄격 |
| `eps.min_yoy` | `0.10` (10%) | 최소 EPS YoY | 높이면 → 더 엄격 |
| `eps.min_prev_yoy` | `0.0` (0%) | 이전 분기 최소 EPS YoY | 높이면 → 더 엄격 |

---

### 3️⃣ Weekly Signal (W)

| 항목 | 현재값 | 설명 | 변경 시 효과 |
|------|-------|------|-------------|
| `high_stability.factor` | `1.05` (5%) | 52주 고점 안정성 계수 | 높이면 → 완화 |
| `low_distance.factor` | `1.3` (30%) | 52주 저점 거리 계수 | 낮추면 → 완화 |
| `high_distance.factor` | `0.7` (70%) | 52주 고점 거리 계수 | 낮추면 → 완화 |
| `high_stability.shift_periods` | `2` | shift 주기 (주) | 변경 권장 안함 |

---

### 4️⃣ RS Signal

| 항목 | 현재값 | 설명 | 변경 시 효과 |
|------|-------|------|-------------|
| `threshold` | `90` | RS_4W 최소값 | 낮추면 → 완화 |
| `use_t_minus_1` | `true` | T-1 데이터 사용 | 변경 권장 안함 |

---

### 5️⃣ Daily Signal (D)

| 항목 | 현재값 | 설명 | 변경 시 효과 |
|------|-------|------|-------------|
| `base_conditions.rs.threshold` | `90` | RS 최소값 | 낮추면 → 완화 |
| `prices.losscut_ratio` | `0.97` (3%) | 손절 비율 | 낮추면 → 손절폭 증가 |
| `prices.target_multiplier` | `1.0` | 목표가 배수 | 높이면 → 목표가 증가 |
| `breakout.timeframes` | `['2Y', '1Y', '6M', '3M', '1M']` | 브레이크아웃 검사 기간 | 변경 가능 |

---

## 📝 변경 예시

### 예시 1: 보수적 전략 (대형주, 고성장)

```yaml
fundamental_signal:
  market_cap:
    min: 10000000000        # 10B USD 이상 (대형주)
  revenue:
    min_yoy: 0.15           # 15% 성장 필수
  eps:
    min_yoy: 0.15           # 15% 성장 필수

rs_signal:
  threshold: 95             # 상위 5%만
```

**효과**: 소수 정예 종목, 안정적 수익

---

### 예시 2: 공격적 전략 (중소형주, 중성장)

```yaml
fundamental_signal:
  market_cap:
    min: 500000000          # 500M USD 이상 (중소형주)
  revenue:
    min_yoy: 0.05           # 5% 성장
  eps:
    min_yoy: 0.05           # 5% 성장

rs_signal:
  threshold: 80             # 상위 20%
```

**효과**: 다수 종목, 고위험 고수익

---

### 예시 3: 균형 전략

```yaml
fundamental_signal:
  market_cap:
    min: 2000000000         # 2B USD (현재값 유지)
  revenue:
    min_yoy: 0.08           # 8% 성장 (약간 완화)
  eps:
    min_yoy: 0.08           # 8% 성장 (약간 완화)

rs_signal:
  threshold: 85             # 상위 15%
```

**효과**: 중간 종목 수, 균형잡힌 리스크

---

## ⚠️ 주의사항

### 1. 변경 후 반드시 테스트

```bash
# 백테스트로 검증
python main_auto_trade.py
# 메뉴 1번 선택

# 개별 종목 확인
# 메뉴 2번 선택
```

### 2. 조건 완화 시 위험

- ✅ 종목 수 증가
- ⚠️ 저품질 종목 포함 가능
- ⚠️ 리스크 증가

### 3. 조건 강화 시 위험

- ✅ 고품질 종목만 선정
- ⚠️ 종목 수 감소
- ⚠️ 기회 손실

### 4. 권장하지 않는 변경

| 항목 | 이유 |
|------|------|
| `use_t_minus_1` | 데이터 타이밍 로직, 변경 시 오류 가능 |
| `shift_periods` | 기술 지표 계산 로직, 변경 시 오류 가능 |
| `combination_logic` | Signal 결합 로직, 변경 시 예상치 못한 결과 |

---

## 🚀 변경 후 검증 프로세스

### Step 1: YAML 파일 수정
```bash
# config/strategy_signal_config.yaml 수정
nano config/strategy_signal_config.yaml
```

### Step 2: 설정 확인
```bash
# Config Loader 테스트
python project/strategy/strategy_signal_config_loader.py
```

### Step 3: 백테스트 실행
```bash
# 메뉴 1번: 자동 백테스트
python main_auto_trade.py
```

### Step 4: 결과 분석
- 종목 수 변화 확인
- 수익률 변화 확인
- 리스크 지표 확인

### Step 5: 실전 적용 전 검토
- 최소 1개월 백테스트 데이터 분석
- 다양한 시장 상황에서 테스트
- 리스크 허용 범위 내 확인

---

## 📞 도움말

### 설정 파일 위치
```
config/strategy_signal_config.yaml
```

### 문서 위치
- 조건 상세 명세: `docs/CURRENT_SIGNAL_CONDITIONS.md`
- Signal 규칙: `docs/interfaces/STRATEGY_SIGNAL_RULES.md`

### 테스트 파일
- Fundamental 통일 테스트: `Test/test_fundamental_signal_unified.py`
- Menu 일관성 테스트: `Test/test_menu_consistency.py`

---

**조건 변경은 신중하게!**
**변경 후 반드시 백테스트로 검증하세요!**
