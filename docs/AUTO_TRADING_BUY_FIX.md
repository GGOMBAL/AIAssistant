# 오토 트레이딩 매수 조건 수정

**날짜**: 2025-11-06
**파일**: `main_auto_trade.py`
**이슈**: 오토 트레이딩에서 실제 주문이 체결되지 않는 문제

---

## 🔍 문제 분석

### 원인

**매수 조건과 TargetPrice의 불일치**

#### 변경 전 매수 조건 (line 2583)

```python
if abs(current_price - candidate['target_price']) / candidate['target_price'] < 0.01:
    # 현재가가 목표가의 1% 이내에 있을 때만 매수
```

#### TargetPrice 설정

```python
TargetPrice = min(Highest_1M, Highest_3M, Highest_6M, Highest_1Y, Highest_2Y)
# = 과거 최고가 중 최소값 (저항선)
```

#### 실제 데이터 예시

**AAPL (2025-11-04)**:
```
현재가:      $270.04
TargetPrice: $277.32 (과거 최고가)
차이:        $7.28 / $277.32 = 2.6%

결과: 2.6% > 1% → 매수 조건 미충족 ❌
```

**문제**: TargetPrice가 과거 최고가(저항선)인데, 매수 조건은 "현재가가 목표가 근처일 때"로 설정되어 있어서 매수가 실행되지 않음.

---

## ✅ 수정 내용

### TargetPrice 역할 재정의

**변경 전**: 매수 진입가 + 익절 목표가 (혼용)
**변경 후**: **익절 목표가 전용** (과거 최고가 = 저항선)

### 매수 조건 변경

**변경 전**:
```python
if abs(current_price - candidate['target_price']) / candidate['target_price'] < 0.01:
    # 목표가의 1% 이내일 때만 매수
    print(f"\n[BUY SIGNAL] {symbol}...")
    if execute_real_orders and is_regular_market_hours():
        # 주문 실행
```

**변경 후**:
```python
# 오토 트레이딩: 시그널이 발생한 종목은 현재가에 즉시 매수
# TargetPrice는 익절 목표가로만 사용 (과거 최고가 = 저항선)
# 매수 조건: 시그널 발생 즉시
print(f"\n[BUY SIGNAL] {symbol}...")

if execute_real_orders and is_regular_market_hours():
    # 주문 실행
```

### 핵심 변경

**조건문 제거**: 가격 비교 조건(`if abs(...) < 0.01`)을 제거하여 **즉시 매수** 실행

---

## 🎯 수정 후 동작 방식

### 매수 로직

1. **시그널 발생**: E→F→W→RS→D 필터를 통과한 종목이 `buy_candidates`에 등록
2. **WebSocket 연결**: 해당 종목의 실시간 가격 수신 시작
3. **첫 가격 업데이트 수신 시 즉시 매수**:
   ```python
   if candidate['status'] == 'waiting':
       print(f"[BUY SIGNAL] {symbol}: ${current_price:.2f}")

       if execute_real_orders and is_regular_market_hours():
           # KIS API로 매수 주문 전송
           result = kis_api.make_buy_limit_order(...)
   ```

### 매수 실행 조건

매수가 실행되려면 다음 **모든 조건**을 만족해야 합니다:

| 조건 | 설명 | 확인 방법 |
|------|------|----------|
| ✅ `candidate['status'] == 'waiting'` | 매수 대기 상태 | 시그널 발생 시 자동 설정 |
| ✅ `execute_real_orders == True` | 실제 주문 모드 활성화 | 프로그램 시작 시 선택 |
| ✅ `is_regular_market_hours() == True` | 정규장 시간 (09:30-16:00 ET) | 자동 체크 |

---

## 📊 시나리오별 동작

### 시나리오 1: 정규장 시간 + 실제 주문 모드

```
09:35 ET - 프로그램 시작
          └─> AAPL, MSFT, GOOGL 시그널 발생
          └─> buy_candidates에 등록 (status='waiting')
          └─> WebSocket 연결

09:36 ET - AAPL 가격 업데이트: $270.04
          └─> [BUY SIGNAL] AAPL: $270.04
          └─> KIS API 매수 주문 전송
          └─> [OK] AAPL 매수 주문 체결
          └─> status='waiting' → 'filled'

09:36 ET - MSFT 가격 업데이트: $514.33
          └─> [BUY SIGNAL] MSFT: $514.33
          └─> KIS API 매수 주문 전송
          └─> [OK] MSFT 매수 주문 체결
```

### 시나리오 2: 정규장 외 시간

```
08:00 ET - 프로그램 시작 (장전)
          └─> AAPL 시그널 발생
          └─> WebSocket 연결

08:01 ET - AAPL 가격 업데이트: $270.04
          └─> [BUY SIGNAL] AAPL: $270.04
          └─> [INFO] AAPL 매수 대기 (정규장 시간 아님)
          └─> status='waiting' 유지

09:30 ET - 정규장 시작
          └─> 다음 가격 업데이트 시 매수 실행
```

### 시나리오 3: 시뮬레이션 모드

```
09:35 ET - 프로그램 시작 (execute_real_orders=False)
          └─> AAPL 시그널 발생
          └─> WebSocket 연결

09:36 ET - AAPL 가격 업데이트: $270.04
          └─> [BUY SIGNAL] AAPL: $270.04
          └─> [SIMULATION] AAPL 매수 주문 (실제 주문 비활성화)
          └─> 실제 주문 미전송 (모니터링만)
```

---

## 💡 TargetPrice와 익절 로직

### TargetPrice 계산

```python
TargetPrice = min(Highest_1M, Highest_3M, Highest_6M, Highest_1Y, Highest_2Y)
```

### 익절 조건 (line 2635)

```python
if current_price >= position['target_price']:
    print(f"[TAKE PROFIT] {symbol}: ${current_price:.2f} >= ${position['target_price']:.2f}")
    # 매도 주문 실행
```

### 예시

**AAPL 트레이딩**:
```
매수:     $270.04 (현재가)
TargetPrice: $277.32 (과거 최고가 = 저항선)

익절 조건:
  $270.04 → $277.32 (+2.7%) 도달 시 매도

실현 가능성:
  ✅ 현실적 (과거에 도달했던 가격)
  ✅ 보수적 (가장 낮은 저항선)
```

---

## ⚠️ 주의사항

### 1. 즉시 매수의 의미

- **변경 전**: 목표가 근처에 도달할 때까지 대기
- **변경 후**: 시그널 발생 시 현재가에 즉시 매수

### 2. 가격 리스크

**장점**:
- 조기 진입으로 더 낮은 가격에 매수 가능
- 신고가 돌파 전 포지션 확보

**단점**:
- 추가 하락 위험 존재
- 횡보 기간 연장 가능성

**대응**:
- 손절가 철저히 준수 (3% 초기 손절 + Stepped Trailing Stop)
- 포지션 크기 관리 중요

### 3. 주문 타입

현재 `make_buy_limit_order` 사용:
```python
result = kis_api.make_buy_limit_order(
    stock_code=symbol,
    amt=candidate['quantity'],
    price=current_price  # 현재가로 지정가 주문
)
```

**지정가 주문**: 현재가에 지정가로 주문 전송
- 장점: 슬리피지 최소화
- 단점: 가격이 급변하면 미체결 가능

**대안**: `make_buy_market_order` 사용 시 즉시 체결 보장 (슬리피지 발생)

---

## 🧪 테스트 방법

### 1. 시뮬레이션 모드 테스트

```bash
python main_auto_trade.py
# 선택:
# - 계좌 타입: 1 (모의 계좌)
# - 주문 실행: 1 (모니터링 전용)
```

**확인사항**:
- `[BUY SIGNAL]` 메시지 출력 확인
- `[SIMULATION]` 매수 주문 확인
- 실제 주문 미전송 확인

### 2. 실제 주문 테스트 (모의 계좌)

```bash
python main_auto_trade.py
# 선택:
# - 계좌 타입: 1 (모의 계좌)
# - 주문 실행: 2 (실제 주문 실행)
```

**확인사항**:
- `[BUY SIGNAL]` 메시지 출력
- `[OK] {symbol} 매수 주문 체결` 확인
- 주문번호 출력 확인
- KIS 모의 계좌에서 주문 내역 확인

### 3. 로그 확인

```python
# 정상 동작 로그
[BUY SIGNAL] AAPL: $270.04 (Target: $277.32)
[OK] AAPL 매수 주문 체결
     주문번호: 123456789
     수량: 10주 @ $270.04

# 에러 발생 시
[BUY SIGNAL] AAPL: $270.04 (Target: $277.32)
[ERROR] AAPL 매수 주문 실패
     rt_cd: XXX, msg_cd: XXX
     에러: [에러 메시지]
```

---

## 🔧 트러블슈팅

### 문제 1: 여전히 주문이 실행되지 않음

**체크리스트**:
1. `execute_real_orders == True` 확인
   ```
   실행 모드: [REAL] 실제 주문 실행  ← 이게 표시되어야 함
   ```

2. 정규장 시간 확인
   ```
   장 상태: [OPEN] 장중  ← 이게 표시되어야 함
   ```

3. `candidate['status']` 확인
   - 'waiting' → 매수 대기 중 ✅
   - 'filled' → 이미 매수 완료 ❌

4. WebSocket 연결 확인
   ```
   [OK] WebSocket 연결 성공: AAPL
   ```

### 문제 2: 주문은 보냈지만 체결 안됨

**원인**:
- 지정가 주문이 현재가와 불일치
- 유동성 부족
- 거래 정지

**해결책**:
- Market Order로 변경 (즉시 체결 보장)
- 지정가를 Bid/Ask 고려하여 조정

### 문제 3: KIS API 에러

**확인**:
```python
[ERROR] AAPL 매수 주문 실패
     rt_cd: XXX, msg_cd: XXX
     에러: [에러 메시지]
```

**대응**:
- rt_cd, msg_cd로 KIS API 문서 확인
- 계좌 잔고 확인
- 주문 가능 시간 확인
- API 권한 확인

---

## 📝 관련 파일

- `main_auto_trade.py` (line 2577-2619): 매수 로직
- `docs/D_CONDITION_UPDATE.md`: D 조건 변경 내역
- `project/strategy/staged_signal_service.py`: TargetPrice 계산

---

## 🔄 변경 이력

| 날짜 | 변경사항 | 작성자 |
|------|----------|--------|
| 2025-11-06 | 매수 조건 제거, 즉시 매수 로직으로 변경 | Claude |

---

## 📋 체크리스트 (운영자용)

실제 운영 전 확인사항:

- [ ] 시뮬레이션 모드 테스트 완료
- [ ] 모의 계좌에서 주문 실행 테스트 완료
- [ ] KIS API 인증 정상 작동 확인
- [ ] 정규장 시간 체크 로직 검증
- [ ] 손절가/익절가 로직 확인
- [ ] 포지션 크기 계산 검증
- [ ] WebSocket 연결 안정성 확인
- [ ] 에러 핸들링 동작 확인

**실제 계좌 사용 시**:
- [ ] 소액으로 먼저 테스트
- [ ] 1-2일 모니터링 후 본격 운영
- [ ] 손익 로그 지속 확인
