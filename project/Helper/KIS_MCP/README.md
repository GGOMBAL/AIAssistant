# KIS MCP Module

한국투자증권 MCP (Model Context Protocol) 기반 주문 시스템

## 개요

KIS (한국투자증권) Open Trading API를 활용한 해외주식 주문 헬퍼 클래스입니다.

## 파일 구조

```
project/Helper/KIS_MCP/
├── __init__.py                    # 모듈 초기화
├── kis_mcp_order_helper.py        # 주문 헬퍼 클래스
└── README.md                      # 이 파일
```

## 사용 방법

### 임포트

```python
from project.Helper.KIS_MCP import KISMCPOrderHelper
```

### 초기화

```python
config = {
    'app_key': 'your_app_key',
    'app_secret': 'your_app_secret',
    'account_no': '12345678',
    'product_code': '01',
    'base_url': 'https://openapi.koreainvestment.com:9443',
    'is_virtual': False  # True for virtual account
}

kis_api = KISMCPOrderHelper(config)
```

### 인증

```python
if kis_api.make_token():
    print("인증 성공")
```

### 매수 주문

```python
result = kis_api.make_buy_order(
    stock_code="AAPL",
    amt=10,
    price=0.0  # 0이면 현재가로 지정가 주문
)

if result["success"]:
    print(f"주문 성공: {result['order_id']}")
else:
    print(f"주문 실패: {result['error']}")
```

### 매도 주문

```python
result = kis_api.make_sell_order(
    stock_code="AAPL",
    amt=10,
    price=0.0  # 0이면 현재가로 지정가 주문
)
```

### 현재가 조회

```python
price = kis_api.get_current_price("AAPL")
print(f"현재가: ${price:.2f}")
```

### 계좌 잔고 조회

```python
balance = kis_api.get_balance("USD")
print(f"잔고: ${balance['cash_balance']:,.2f}")
```

## 주문 타입 (ORD_DVSN)

### 매수 (TTTT1002U / VTTT1002U)

- `00`: 지정가
- `32`: LOO (장개시 지정가) - 실전만
- `34`: LOC (장마감 지정가) - 실전만

### 매도 (TTTT1006U / VTTT1006U)

- `00`: 지정가
- `31`: MOO (장개시 시장가) - 실전만
- `32`: LOO (장개시 지정가) - 실전만
- `33`: MOC (장마감 시장가) - 실전만
- `34`: LOC (장마감 지정가) - 실전만

**참고**: 모의투자는 `00` (지정가)만 사용 가능

## 시장가 주문 처리

KIS API는 해외주식에 대해 일반적인 시장가 주문을 지원하지 않습니다. 대신:

- **매수**: 현재가로 지정가 주문 (`ORD_DVSN: "00"`)
- **매도**: 현재가로 지정가 주문 (`ORD_DVSN: "00"`)

**참고**:
- MOO(31)는 장 개시 전에만 주문 가능
- 일반 거래 시간에는 지정가 사용
- `use_market_on_open=True`로 명시적 지정 시에만 MOO 사용

## 주요 특징

- ✅ KIS Open Trading API 완전 호환
- ✅ 모의투자/실전투자 자동 전환
- ✅ 현재가 자동 조회 및 지정가 주문
- ✅ 계좌 잔고 조회
- ✅ 오류 처리 및 로깅

## 테스트

```bash
python Test/test_kis_order.py
```

## 참고 문서

- **상세 가이드**: `docs/KIS_MCP_ORDER_SYSTEM.md`
- **KIS MCP GitHub**: https://github.com/koreainvestment/open-trading-api/tree/main/MCP
- **KIS API 포털**: https://apiportal.koreainvestment.com

## 라이선스

본 모듈은 KIS Open Trading API 기반으로 작성되었습니다.

## 작성 정보

- **작성일**: 2025-11-06
- **버전**: 1.0
- **기반**: KIS Trading MCP
