# Easy Signal Configuration System - 제안서

**Version**: 1.0
**Created**: 2025-10-18
**Purpose**: 쉽게 Signal 조건을 변경할 수 있는 시스템 제안

---

## 📋 목차

1. [현재 문제점](#현재-문제점)
2. [제안하는 해결 방안](#제안하는-해결-방안)
3. [방안 1: 완전한 YAML 통합 (추천)](#방안-1-완전한-yaml-통합)
4. [방안 2: Strategy Manager CLI](#방안-2-strategy-manager-cli)
5. [방안 3: 하이브리드 접근](#방안-3-하이브리드-접근)
6. [구현 우선순위](#구현-우선순위)
7. [구현 계획](#구현-계획)

---

## 현재 문제점

### 1. 조건이 코드에 하드코딩됨

```python
# signal_generation_service.py:443
f_condition1 = market_cap >= 2000000000  # 코드에 직접 입력
f_condition3 = rev_yoy >= 0.1            # 변경하려면 코드 수정 필요
```

**문제**:
- ❌ 조건 변경할 때마다 코드 수정 필요
- ❌ Python 문법 오류 위험
- ❌ Git commit 필요

### 2. 두 파일을 모두 수정해야 함

**수정 필요 파일**:
1. `signal_generation_service.py` (Menu 2, 3)
2. `staged_signal_service.py` (Menu 1, 4)

**문제**:
- ❌ 한쪽만 수정하면 불일치 발생
- ❌ 실수 가능성 높음
- ❌ 유지보수 어려움

### 3. YAML 파일이 있지만 일부만 적용

**현재 상태**:
- ✅ RS threshold만 YAML에서 읽음
- ❌ Fundamental, Weekly, Earnings는 하드코딩

**문제**:
- ❌ YAML 수정해도 변경 안 됨
- ❌ 혼란 초래

### 4. 변경 후 즉시 반영 안 됨

**문제**:
- ❌ 프로그램 재시작 필요
- ❌ 테스트 시간 오래 걸림

---

## 제안하는 해결 방안

### 비교표

| 항목 | 현재 | 방안 1 (YAML) | 방안 2 (CLI) | 방안 3 (하이브리드) |
|------|------|--------------|-------------|-------------------|
| **수정 방법** | 코드 | YAML | 명령어 | YAML + 명령어 |
| **수정 시간** | 10분 | 1분 | 5초 | 5초~1분 |
| **Python 지식** | 필수 | 불필요 | 불필요 | 불필요 |
| **실수 위험** | 높음 | 낮음 | 매우 낮음 | 매우 낮음 |
| **유연성** | 높음 | 높음 | 중간 | 매우 높음 |
| **구현 시간** | - | 4-6시간 | 2-3시간 | 6-8시간 |

---

## 방안 1: 완전한 YAML 통합

### 개요

**모든 Signal 조건을 YAML 파일로 관리**

```yaml
# config/strategy_signal_config.yaml

# ==================== 전략 선택 ====================
active_strategy: "balanced"  # conservative / balanced / aggressive / custom

# ==================== 사전 정의된 전략 ====================
strategies:
  conservative:
    name: "보수적 전략 - 대형주 고성장"
    description: "안정적 수익 추구, 소수 정예 종목"

    fundamental_signal:
      enabled: true
      market_cap:
        min: 10000000000                # 10B USD (대형주만)
        max: 20000000000000             # 20T USD
      revenue:
        min_yoy: 0.15                   # 15% 성장 (엄격)
        min_prev_yoy: 0.05              # 5%
        min_value: 0
      eps:
        min_yoy: 0.15                   # 15% 성장 (엄격)
        min_prev_yoy: 0.05              # 5%
      growth_logic: "OR"                # Revenue OR EPS

    weekly_signal:
      enabled: true
      price_levels:
        require_1y_eq_2y_high: true
        require_2y_lt_1y_low: true
      high_stability:
        enabled: true
        factor: 1.03                    # 3% (더 엄격)
        shift_periods: 2
      low_distance:
        enabled: true
        factor: 1.4                     # 40% (더 높음)
        shift_periods: 1
      high_distance:
        enabled: true
        factor: 0.8                     # 80% (더 높음)
        shift_periods: 1

    rs_signal:
      enabled: true
      threshold: 95                     # 상위 5% (엄격)
      use_t_minus_1: true

    earnings_signal:
      enabled: false
      revenue:
        min_prev_yoy: 0.0
        require_growth: true
      eps:
        min_prev_yoy: 0.0
        require_growth: true

    daily_signal:
      enabled: true
      base_conditions:
        sma200_momentum:
          enabled: true
          allow_zero: true
        sma_downtrend:
          enabled: true
        rs:
          enabled: true
          threshold: 95                 # 상위 5%
      breakout:
        enabled: true
        timeframes: ['2Y', '1Y', '6M', '3M', '1M']
        stop_at_first: true
      prices:
        losscut_ratio: 0.98             # 2% 손절 (보수적)
        target_multiplier: 1.0
      use_t_minus_1: true

    thresholds:
      E: 1.0
      F: 1.0
      W: 1.0
      RS: 1.0
      D: 0.5

  balanced:
    name: "균형 전략 - 중형주 적정 성장"
    description: "리스크와 수익의 균형, 현재 기본 전략"

    fundamental_signal:
      enabled: true
      market_cap:
        min: 2000000000                 # 2B USD
        max: 20000000000000             # 20T USD
      revenue:
        min_yoy: 0.10                   # 10% 성장
        min_prev_yoy: 0.0               # 0%
        min_value: 0
      eps:
        min_yoy: 0.10                   # 10% 성장
        min_prev_yoy: 0.0               # 0%
      growth_logic: "OR"

    weekly_signal:
      enabled: true
      price_levels:
        require_1y_eq_2y_high: true
        require_2y_lt_1y_low: true
      high_stability:
        enabled: true
        factor: 1.05                    # 5%
        shift_periods: 2
      low_distance:
        enabled: true
        factor: 1.3                     # 30%
        shift_periods: 1
      high_distance:
        enabled: true
        factor: 0.7                     # 70%
        shift_periods: 1

    rs_signal:
      enabled: true
      threshold: 90                     # 상위 10%
      use_t_minus_1: true

    earnings_signal:
      enabled: false
      revenue:
        min_prev_yoy: 0.0
        require_growth: true
      eps:
        min_prev_yoy: 0.0
        require_growth: true

    daily_signal:
      enabled: true
      base_conditions:
        sma200_momentum:
          enabled: true
          allow_zero: true
        sma_downtrend:
          enabled: true
        rs:
          enabled: true
          threshold: 90
      breakout:
        enabled: true
        timeframes: ['2Y', '1Y', '6M', '3M', '1M']
        stop_at_first: true
      prices:
        losscut_ratio: 0.97             # 3% 손절
        target_multiplier: 1.0
      use_t_minus_1: true

    thresholds:
      E: 1.0
      F: 1.0
      W: 1.0
      RS: 1.0
      D: 0.5

  aggressive:
    name: "공격적 전략 - 중소형주 중성장"
    description: "고위험 고수익 추구, 다수 종목"

    fundamental_signal:
      enabled: true
      market_cap:
        min: 500000000                  # 500M USD (중소형주)
        max: 20000000000000             # 20T USD
      revenue:
        min_yoy: 0.05                   # 5% 성장 (완화)
        min_prev_yoy: 0.0               # 0%
        min_value: 0
      eps:
        min_yoy: 0.05                   # 5% 성장 (완화)
        min_prev_yoy: 0.0               # 0%
      growth_logic: "OR"

    weekly_signal:
      enabled: true
      price_levels:
        require_1y_eq_2y_high: true
        require_2y_lt_1y_low: true
      high_stability:
        enabled: true
        factor: 1.10                    # 10% (완화)
        shift_periods: 2
      low_distance:
        enabled: true
        factor: 1.2                     # 20% (낮음)
        shift_periods: 1
      high_distance:
        enabled: true
        factor: 0.6                     # 60% (낮음)
        shift_periods: 1

    rs_signal:
      enabled: true
      threshold: 80                     # 상위 20% (완화)
      use_t_minus_1: true

    earnings_signal:
      enabled: false
      revenue:
        min_prev_yoy: 0.0
        require_growth: true
      eps:
        min_prev_yoy: 0.0
        require_growth: true

    daily_signal:
      enabled: true
      base_conditions:
        sma200_momentum:
          enabled: true
          allow_zero: true
        sma_downtrend:
          enabled: true
        rs:
          enabled: true
          threshold: 80                 # 상위 20%
      breakout:
        enabled: true
        timeframes: ['2Y', '1Y', '6M', '3M', '1M']
        stop_at_first: true
      prices:
        losscut_ratio: 0.95             # 5% 손절 (공격적)
        target_multiplier: 1.0
      use_t_minus_1: true

    thresholds:
      E: 1.0
      F: 1.0
      W: 1.0
      RS: 1.0
      D: 0.5

  custom:
    name: "사용자 정의 전략"
    description: "자유롭게 조정 가능"

    fundamental_signal:
      enabled: true
      market_cap:
        min: 2000000000
        max: 20000000000000
      revenue:
        min_yoy: 0.08                   # 8% (원하는 대로 조정)
        min_prev_yoy: 0.0
        min_value: 0
      eps:
        min_yoy: 0.08                   # 8%
        min_prev_yoy: 0.0
      growth_logic: "OR"

    # ... 나머지 설정도 조정 가능
```

### 장점

1. **쉬운 변경**
   ```yaml
   # 1줄만 수정하면 전략 변경!
   active_strategy: "conservative"  # balanced → conservative
   ```

2. **코드 수정 불필요**
   - Python 문법 몰라도 됨
   - 실수 위험 없음

3. **사전 정의된 전략**
   - Conservative, Balanced, Aggressive 바로 선택
   - 검증된 조합

4. **Git 버전 관리**
   - YAML 파일만 commit
   - 변경 이력 추적 쉬움

5. **Hot Reload 가능** (선택적 구현)
   - 프로그램 재시작 없이 변경 적용

### 단점

1. **초기 구현 시간**
   - 4-6시간 소요
   - 두 서비스 모두 수정 필요

2. **YAML 문법**
   - 들여쓰기 민감
   - 실수 시 파싱 오류

---

## 방안 2: Strategy Manager CLI

### 개요

**명령어로 전략 전환**

```bash
# 전략 전환
python strategy_manager.py --switch conservative
python strategy_manager.py --switch balanced
python strategy_manager.py --switch aggressive

# 현재 전략 확인
python strategy_manager.py --show

# 전략 비교
python strategy_manager.py --compare conservative balanced

# 사용자 정의 전략 생성
python strategy_manager.py --create my_strategy
```

### 구조

```python
# strategy_manager.py

class StrategyManager:
    """전략 관리 CLI"""

    STRATEGIES = {
        'conservative': ConservativeStrategy(),
        'balanced': BalancedStrategy(),
        'aggressive': AggressiveStrategy(),
    }

    def switch_strategy(self, name: str):
        """전략 전환"""
        if name not in self.STRATEGIES:
            print(f"Unknown strategy: {name}")
            return

        strategy = self.STRATEGIES[name]

        # YAML 파일 업데이트
        self._update_yaml(strategy.to_dict())

        print(f"Switched to {name} strategy!")
        print(f"  Market Cap: {strategy.market_cap_min:,} ~ {strategy.market_cap_max:,}")
        print(f"  REV YoY: {strategy.rev_yoy_min*100:.1f}%")
        print(f"  EPS YoY: {strategy.eps_yoy_min*100:.1f}%")
        print(f"  RS Threshold: {strategy.rs_threshold}")
```

### 사용 예시

```bash
$ python strategy_manager.py --switch conservative

Switched to conservative strategy!
  Name: 보수적 전략 - 대형주 고성장
  Market Cap: 10,000,000,000 ~ 20,000,000,000,000
  REV YoY: 15.0%
  EPS YoY: 15.0%
  RS Threshold: 95
  Losscut: 2%

Restart the program to apply changes.
```

### 장점

1. **가장 쉬움**
   - 명령어 하나로 전략 변경
   - YAML 몰라도 됨

2. **빠름**
   - 5초 안에 전략 전환

3. **안전**
   - 검증된 전략만 제공
   - 실수 위험 없음

### 단점

1. **유연성 낮음**
   - 사전 정의된 전략만 선택 가능
   - 세부 조정 어려움

2. **CLI 구현 필요**
   - 2-3시간 소요

---

## 방안 3: 하이브리드 접근

### 개요

**YAML + CLI 조합**

```bash
# 빠른 전략 전환 (CLI)
python strategy_manager.py --switch conservative

# 세부 조정 (YAML)
# config/strategy_signal_config.yaml 직접 수정
# custom 전략 사용

# 전략 검증
python strategy_manager.py --validate

# 백테스트 비교
python strategy_manager.py --backtest conservative balanced aggressive
```

### 장점

1. **최고의 유연성**
   - CLI로 빠른 전환
   - YAML로 세부 조정

2. **사용자 친화적**
   - 초보자: CLI만 사용
   - 고급 사용자: YAML 직접 수정

3. **검증 기능**
   - 전략 유효성 자동 검사

### 단점

1. **구현 시간 가장 김**
   - 6-8시간 소요

2. **복잡도 증가**
   - 두 가지 방법 모두 관리

---

## 구현 우선순위

### Phase 1: 필수 (즉시 구현 권장)

1. **YAML 구조 정의** (30분)
   - `strategy_signal_config.yaml` 완성
   - 3가지 전략 정의

2. **Config Loader 완전 통합** (2-3시간)
   - `StrategySignalConfigLoader` 업그레이드
   - 모든 조건 YAML에서 읽도록 수정

3. **양쪽 서비스 수정** (2-3시간)
   - `signal_generation_service.py` 수정
   - `staged_signal_service.py` 수정
   - 하드코딩 제거, config에서 읽기

**총 소요 시간**: 4-6시간

### Phase 2: 추가 편의성 (선택적)

4. **Strategy Manager CLI** (2-3시간)
   - 전략 전환 명령어
   - 현재 전략 확인
   - 전략 비교

5. **검증 기능** (1-2시간)
   - YAML 유효성 검사
   - 전략 일관성 검증

**총 소요 시간**: 3-5시간

### Phase 3: 고급 기능 (나중에)

6. **Hot Reload** (2-3시간)
   - 재시작 없이 설정 변경

7. **백테스트 자동 비교** (2-3시간)
   - 여러 전략 동시 백테스트
   - 결과 비교 리포트

**총 소요 시간**: 4-6시간

---

## 구현 계획

### Step 1: YAML 구조 완성 (30분)

**파일**: `config/strategy_signal_config.yaml`

```yaml
# 현재 strategy_signal_config.yaml을 위 구조로 확장
active_strategy: "balanced"

strategies:
  conservative: { ... }
  balanced: { ... }
  aggressive: { ... }
  custom: { ... }
```

### Step 2: Config Loader 업그레이드 (2시간)

**파일**: `project/strategy/strategy_signal_config_loader.py`

**추가 메서드**:
```python
class StrategySignalConfigLoader:
    def get_active_strategy(self) -> str:
        """현재 활성화된 전략 이름"""
        return self.config.get('active_strategy', 'balanced')

    def get_strategy_config(self, strategy_name: str = None) -> Dict:
        """특정 전략의 설정 반환"""
        if strategy_name is None:
            strategy_name = self.get_active_strategy()

        strategies = self.config.get('strategies', {})
        return strategies.get(strategy_name, {})

    def get_fundamental_market_cap_min(self, strategy: str = None) -> float:
        """Fundamental 시가총액 최소값"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('market_cap', {}).get('min', 2000000000)

    # ... 모든 조건에 대한 getter 메서드 추가
```

### Step 3: 서비스 파일 수정 (2-3시간)

**파일 1**: `signal_generation_service.py`

**Before**:
```python
f_condition1 = market_cap >= 2000000000  # 하드코딩
```

**After**:
```python
min_market_cap = self.config_loader.get_fundamental_market_cap_min()
f_condition1 = market_cap >= min_market_cap  # Config에서 읽기
```

**파일 2**: `staged_signal_service.py`

**동일하게 수정**

### Step 4: 테스트 (1시간)

```bash
# 1. Conservative 전략 테스트
# config/strategy_signal_config.yaml 수정
active_strategy: "conservative"

# 실행
python main_auto_trade.py

# 2. Aggressive 전략 테스트
active_strategy: "aggressive"

# 실행
python main_auto_trade.py

# 3. 일관성 테스트
python Test/test_menu_consistency.py
```

### Step 5: CLI 구현 (선택적, 2-3시간)

**파일**: `strategy_manager.py`

```python
#!/usr/bin/env python3
"""
Strategy Manager CLI
전략 관리 명령줄 도구
"""

import argparse
import yaml
from pathlib import Path
from project.strategy.strategy_signal_config_loader import StrategySignalConfigLoader

def main():
    parser = argparse.ArgumentParser(description='Strategy Manager')
    parser.add_argument('--switch', help='Switch to strategy')
    parser.add_argument('--show', action='store_true', help='Show current strategy')
    parser.add_argument('--list', action='store_true', help='List all strategies')

    args = parser.parse_args()

    config_path = Path('config/strategy_signal_config.yaml')

    if args.switch:
        switch_strategy(config_path, args.switch)
    elif args.show:
        show_current_strategy(config_path)
    elif args.list:
        list_strategies(config_path)

def switch_strategy(config_path: Path, strategy: str):
    """전략 전환"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    if strategy not in config.get('strategies', {}):
        print(f"[ERROR] Unknown strategy: {strategy}")
        print(f"Available: {list(config.get('strategies', {}).keys())}")
        return

    config['active_strategy'] = strategy

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print(f"[SUCCESS] Switched to '{strategy}' strategy")
    print(f"\nRestart the program to apply changes:")
    print(f"  python main_auto_trade.py")

if __name__ == "__main__":
    main()
```

**사용**:
```bash
python strategy_manager.py --switch conservative
python strategy_manager.py --show
python strategy_manager.py --list
```

---

## 비용 대비 효과 분석

| 방안 | 구현 시간 | 사용 편의성 | 유지보수성 | 추천도 |
|------|----------|-----------|----------|--------|
| **현재 상태** | 0시간 | ⭐ (어려움) | ⭐ (어려움) | ❌ |
| **방안 1 (YAML)** | 4-6시간 | ⭐⭐⭐⭐ (쉬움) | ⭐⭐⭐⭐⭐ (쉬움) | ⭐⭐⭐⭐⭐ |
| **방안 2 (CLI)** | 2-3시간 | ⭐⭐⭐⭐⭐ (매우 쉬움) | ⭐⭐⭐ (보통) | ⭐⭐⭐ |
| **방안 3 (하이브리드)** | 6-8시간 | ⭐⭐⭐⭐⭐ (매우 쉬움) | ⭐⭐⭐⭐⭐ (쉬움) | ⭐⭐⭐⭐ |

---

## 최종 권장 사항

### 단기 (즉시 구현): 방안 1 - 완전한 YAML 통합

**이유**:
1. ✅ **가장 실용적** - 4-6시간 투자로 큰 효과
2. ✅ **유지보수 쉬움** - 코드 수정 없이 YAML만 관리
3. ✅ **검증된 방식** - 많은 프로젝트에서 사용
4. ✅ **확장 가능** - Phase 2, 3 추가 가능

### 중기 (여유 있을 때): 방안 2 - CLI 추가

**이유**:
1. ✅ **사용자 편의성 극대화**
2. ✅ **전략 전환 5초**
3. ✅ **실수 방지**

### 장기 (선택적): 고급 기능

1. Hot Reload
2. 자동 백테스트 비교
3. Web UI

---

## 구현 시작하시겠습니까?

**바로 시작 가능한 작업**:

1. **Step 1**: `config/strategy_signal_config.yaml` 확장 (30분)
2. **Step 2**: `strategy_signal_config_loader.py` 업그레이드 (2시간)
3. **Step 3**: 서비스 파일 수정 (2-3시간)
4. **Step 4**: 테스트 (1시간)

**총 예상 시간**: 5-6시간

**완료 후 효과**:
```bash
# Before (현재)
# 1. signal_generation_service.py 수정
# 2. staged_signal_service.py 수정
# 3. 테스트
# 4. 재시작
# 총 시간: 10-15분

# After (YAML 통합)
# 1. active_strategy: "conservative" (1줄 수정)
# 2. 재시작
# 총 시간: 30초
```

---

*Version: 1.0 | Created: 2025-10-18*
