# KIS MCP 주문 시스템

**날짜**: 2025-11-06
**파일**: `project/Helper/KIS_MCP/kis_mcp_order_helper.py`
**기반**: KIS Trading MCP (https://github.com/koreainvestment/open-trading-api/tree/main/MCP)

---

## 개요

KIS (한국투자증권) MCP (Model Context Protocol)를 활용하여 해외주식 주문 시스템을 구현했습니다.

### 기존 문제

**APBK1269 오류**: "주문구분 입력오류입니다"
- 기존 코드에서 `ORD_DVSN: "01"` (시장가) 사용
- **KIS API는 해외주식에 대해 ORD_DVSN "01"을 지원하지 않음**

### 해결 방법

KIS MCP의 공식 API 문서를 참조하여 올바른 주문 타입을 확인하고 구현

---

## KIS API 주문 타입 (ORD_DVSN)

### 매수 주문 (TTTT1002U / VTTT1002U)

| 코드 | 타입 | 설명 | 모의투자 |
|------|------|------|----------|
| 00 | 지정가 | 가격을 지정한 주문 | ✅ |
| 32 | LOO | 장개시 지정가 | ❌ |
| 34 | LOC | 장마감 지정가 | ❌ |

### 매도 주문 (TTTT1006U / VTTT1006U)

| 코드 | 타입 | 설명 | 모의투자 |
|------|------|------|----------|
| 00 | 지정가 | 가격을 지정한 주문 | ✅ |
| 31 | MOO | 장개시 시장가 | ❌ |
| 32 | LOO | 장개시 지정가 | ❌ |
| 33 | MOC | 장마감 시장가 | ❌ |
| 34 | LOC | 장마감 지정가 | ❌ |

**중요**:
- **모의투자는 00(지정가)만 가능**
- **ORD_DVSN "01"은 존재하지 않음**

---

## 새로운 주문 시스템 구조

### KISMCPOrderHelper 클래스

```python
from project.Helper.KIS_MCP import KISMCPOrderHelper

# 초기화
kis_api = KISMCPOrderHelper(config)

# 인증
kis_api.make_token()

# 매수 주문
result = kis_api.make_buy_order(
    stock_code="AAPL",
    amt=1,
    price=0.0  # 0이면 현재가로 지정가 주문
)

# 매도 주문
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=1,
    price=0.0  # 0이면 MOO(장개시 시장가) 주문
)
```

---

## 주요 메서드

### 1. `make_token()`

KIS API 인증 토큰 발급

**Returns**:
- `True`: 인증 성공
- `False`: 인증 실패

**Example**:
```python
if kis_api.make_token():
    print("인증 성공")
else:
    print("인증 실패")
```

---

### 2. `place_order(stock_code, order_type, quantity, price, ord_dvsn)`

해외주식 주문 (범용)

**Parameters**:
- `stock_code` (str): 종목코드 (예: "AAPL")
- `order_type` (str): "buy" (매수) or "sell" (매도)
- `quantity` (int): 주문수량
- `price` (float): 주문가격 (0이면 시장가 유사 주문)
- `ord_dvsn` (str): 주문구분 (기본값: "00")

**Returns**:
```python
# 성공
{
    "success": True,
    "order_id": "1234567890",  # 주문번호 (ODNO)
    "message": "정상처리되었습니다",
    "rt_cd": "0",
    "msg_cd": "MCA00000"
}

# 실패
{
    "success": False,
    "error": "계좌 잔고 부족",
    "rt_cd": "1",
    "msg_cd": "MCA10001"
}
```

**Example**:
```python
result = kis_api.place_order(
    stock_code="AAPL",
    order_type="buy",
    quantity=10,
    price=150.0,
    ord_dvsn="00"  # 지정가
)

if result["success"]:
    print(f"주문 성공: {result['order_id']}")
else:
    print(f"주문 실패: {result['error']}")
```

---

### 3. `make_buy_order(stock_code, amt, price, use_market_on_open)`

매수 주문 (간편)

**Parameters**:
- `stock_code` (str): 종목코드
- `amt` (int): 수량
- `price` (float): 가격 (0이면 현재가로 지정가 주문)
- `use_market_on_open` (bool): True면 LOO(32) 사용 (기본값: False)

**Example**:
```python
# 현재가로 지정가 매수
result = kis_api.make_buy_order(
    stock_code="AAPL",
    amt=10,
    price=0.0
)

# 특정 가격으로 지정가 매수
result = kis_api.make_buy_order(
    stock_code="AAPL",
    amt=10,
    price=150.0
)

# 장개시 지정가 매수 (실전만)
result = kis_api.make_buy_order(
    stock_code="AAPL",
    amt=10,
    price=150.0,
    use_market_on_open=True
)
```

---

### 4. `make_sell_order(stock_code, amt, price, use_market_on_open)`

매도 주문 (간편)

**Parameters**:
- `stock_code` (str): 종목코드
- `amt` (int): 수량
- `price` (float): 가격 (0이면 현재가로 지정가 주문)
- `use_market_on_open` (bool): True면 MOO(31) 사용 (장 개시 전만 가능)

**Example**:
```python
# 현재가로 지정가 매도
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=0.0
)

# 특정 가격으로 지정가 매도
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=155.0
)

# MOO (장개시 시장가) 매도 - 장 개시 전만 가능 (실전만)
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=0.0,
    use_market_on_open=True
)
```

**중요**:
- `use_market_on_open=True`는 장 개시 전에만 주문 가능
- 일반 거래 시간에는 APBK2623 오류 발생
- 기본적으로는 현재가 지정가 주문 사용 권장

---

### 5. `get_current_price(stock_code)`

현재가 조회

**Parameters**:
- `stock_code` (str): 종목코드

**Returns**:
- `float`: 현재가 (실패 시 0.0)

**Example**:
```python
price = kis_api.get_current_price("AAPL")
if price > 0:
    print(f"AAPL 현재가: ${price:.2f}")
else:
    print("현재가 조회 실패")
```

---

### 6. `get_balance(currency)`

계좌 잔고 조회

**Parameters**:
- `currency` (str): 통화 코드 (기본값: "USD")

**Returns**:
```python
{
    "cash_balance": 10000.0,  # 현금 잔고
    "currency": "USD",
    "result": {...}  # 원본 API 응답
}
```

**Example**:
```python
balance = kis_api.get_balance("USD")
print(f"현재 잔고: ${balance['cash_balance']:,.2f}")
```

---

## 시장가 주문 처리

KIS API는 해외주식에 대해 정확한 "시장가" 주문을 지원하지 않습니다. 대신 다음과 같이 처리합니다:

### 매수 시장가

```python
# price=0.0 설정
result = kis_api.make_buy_order(
    stock_code="AAPL",
    amt=10,
    price=0.0
)
```

**처리 방식**:
1. 현재가 조회 (`get_current_price`)
2. 현재가로 지정가 주문 (ORD_DVSN: "00")

**장점**:
- 모의투자/실전 모두 동작
- 체결 가능성 높음

**단점**:
- 가격 변동 시 미체결 가능성
- 완전한 시장가는 아님

---

### 매도 시장가

```python
# price=0.0 설정
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=0.0
)
```

**처리 방식**:
1. 현재가 조회 (`get_current_price`)
2. 현재가로 지정가 주문 (ORD_DVSN: "00")

**장점**:
- 모의투자/실전 모두 동작
- 시간 제약 없음
- 체결 가능성 높음

**단점**:
- 가격 변동 시 미체결 가능성
- 완전한 시장가는 아님

**참고**:
- MOO(31)는 장 개시 전에만 주문 가능
- 일반 거래 시간에는 사용 불가
- `use_market_on_open=True`로 명시적 지정 시 MOO 사용

---

## 설정 (myStockInfo.yaml)

```yaml
# 모의 계좌
VIRT_APP_KEY: "your_virtual_app_key"
VIRT_APP_SECRET: "your_virtual_app_secret"
VIRT_CANO: "12345678"
VIRT_ACNT_PRDT_CD: "01"
VIRT_URL: "https://openapivts.koreainvestment.com:29443"

# 실제 계좌
REAL_APP_KEY: "your_real_app_key"
REAL_APP_SECRET: "your_real_app_secret"
REAL_CANO: "87654321"
REAL_ACNT_PRDT_CD: "01"
REAL_URL: "https://openapi.koreainvestment.com:9443"
```

---

## 테스트 스크립트

### 파일: `Test/test_kis_order.py`

```bash
# 실행
python Test/test_kis_order.py

# 계좌 선택
# 1. 모의 계좌 (Paper Trading)
# 2. 실제 계좌 (Live Trading)

# 주문 메뉴
# 1. 시장가 매수 주문 테스트 (AAPL 1주)
# 2. 시장가 매도 주문 테스트 (AAPL 1주)
# 3. 종료
```

### 테스트 순서

1. **모의 계좌 테스트**
   ```bash
   python Test/test_kis_order.py
   # 선택: 1 (모의 계좌)
   # 선택: 1 (매수 주문 테스트)
   ```

2. **주문 확인**
   - KIS API 인증
   - 계좌 잔고 확인
   - 현재가 조회
   - 주문 전송
   - 결과 확인

3. **실제 계좌 테스트 (신중하게!)**
   ```bash
   python Test/test_kis_order.py
   # 선택: 2 (실제 계좌)
   # 선택: 1 (매수 주문 테스트)
   ```

---

## Auto Trading 적용

### main_auto_trade.py 수정 필요

```python
# Before
from project.Helper.kis_api_helper_us import KISUSHelper

# After
from project.Helper.KIS_MCP import KISMCPOrderHelper

# 매수 주문
result = kis_api.make_buy_order(
    stock_code=symbol,
    amt=candidate['quantity'],
    price=0.0  # 현재가로 지정가 주문
)

# 익절/손절 매도
result = kis_api.make_sell_order(
    stock_code=symbol,
    amt=position['quantity'],
    price=0.0  # MOO (장개시 시장가)
)
```

---

## 주의사항

### 1. 모의투자 제한

- **지정가(00)만 가능**
- MOO/LOO/MOC/LOC 사용 불가
- 시장가 주문 시 자동으로 현재가 지정가로 변환

### 2. 거래소 코드

자동으로 추정되지만 부정확할 수 있음:

| 거래소 | 코드 | 종목 예시 |
|--------|------|-----------|
| 나스닥 | NASD | AAPL, MSFT, GOOGL |
| 뉴욕 | NYSE | JPM, BA, DIS |
| 아멕스 | AMEX | - |

**개선 필요**: 종목 마스터 파일에서 정확한 거래소 조회

### 3. 가격 단위

- **정수부**: 23자리
- **소수부**: 8자리
- 예: 150.50 → "150.50000000"

### 4. 주문 수량

- 해외 거래소별 최소 주문수량 확인 필요
- 일반적으로 1주부터 가능

---

## 오류 코드

### rt_cd == "0": 성공

| msg_cd | 의미 |
|--------|------|
| MCA00000 | 정상 처리 |

### rt_cd != "0": 실패

| rt_cd | msg_cd | 의미 | 대응 |
|-------|--------|------|------|
| 7 | APBK1269 | 주문구분 입력오류 | ord_dvsn 확인 |
| 7 | APBK2623 | MOO/LOO 주문불가 시간 | 지정가 사용 또는 시간 확인 |
| 1 | MCA10001 | 계좌 잔고 부족 | 잔고 확인 |
| 1 | MCA10002 | 주문 수량 초과 | 수량 조정 |
| 1 | MCA10003 | 거래 정지 종목 | 다른 종목 선택 |
| 1 | MCA10004 | 주문 시간 외 | 정규장 시간 확인 |

---

## 트러블슈팅

### 문제 1: APBK1269 오류 (주문구분 입력오류)

**원인**: 잘못된 ORD_DVSN 코드 사용

**해결**:
- 모의투자: 반드시 "00" 사용
- 실전투자: 매수(00/32/34), 매도(00/31/32/33/34)
- "01" 사용 금지

### 문제 2: APBK2623 오류 (MOO/LOO 주문불가 시간)

**원인**: MOO/LOO 주문은 특정 시간대에만 가능

**오류 메시지**:
```
[MOO 또는 LOO 주문불가 시간] 오류입니다.
```

**해결**:
```python
# ❌ 잘못된 방법: 일반 시간에 MOO 사용
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=0.0,
    use_market_on_open=True  # MOO는 장 개시 전만 가능
)

# ✅ 올바른 방법: 지정가 사용
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=0.0  # 현재가로 지정가 주문
)
```

**참고**:
- MOO/LOO는 장 개시 전에만 주문 가능
- 일반 거래 시간에는 지정가(00) 사용
- 현재 버전은 기본적으로 지정가 사용

### 문제 3: 주문이 미체결됨

**원인**: 지정가 주문 가격과 시장가 차이

**해결**:
- 매수: 현재가보다 약간 높게 (예: +0.5%)
- 매도: 현재가보다 약간 낮게 (예: -0.5%)

### 문제 4: 현재가 조회 실패

**원인**: 거래소 코드 불일치

**해결**:
```python
# 수동으로 거래소 지정
kis_api.get_market_code_us = lambda x: "NASD"  # 강제로 나스닥 설정
```

### 문제 5: 인증 실패

**원인**: API Key/Secret 오류

**해결**:
- myStockInfo.yaml 확인
- APP_KEY, APP_SECRET 정확성 확인
- 모의/실전 URL 확인

---

## 다음 단계

### 즉시 실행 가능

1. ✅ KIS MCP Order Helper 작성 완료
2. ✅ 테스트 스크립트 업데이트 완료
3. ⏳ **테스트 실행** - `python Test/test_kis_order.py`

### 추가 작업 필요

1. ⏳ `main_auto_trade.py`를 KIS MCP Helper로 전환
2. ⏳ 거래소 코드 자동 조회 개선 (종목 마스터 파일 활용)
3. ⏳ 주문 체결 확인 로직 추가
4. ⏳ 주문 취소/정정 기능 추가

---

## 참고 자료

### KIS MCP GitHub

- **Repository**: https://github.com/koreainvestment/open-trading-api
- **MCP Folder**: https://github.com/koreainvestment/open-trading-api/tree/main/MCP
- **Overseas Stock Order**: https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/overseas_stock/order

### KIS API 문서

- **API Portal**: https://apiportal.koreainvestment.com
- **해외주식 주문**: TTTT1002U (매수), TTTT1006U (매도)
- **모의투자 주문**: VTTT1002U (매수), VTTT1006U (매도)

---

**작성일**: 2025-11-06
**작성자**: Claude
**버전**: 1.0
