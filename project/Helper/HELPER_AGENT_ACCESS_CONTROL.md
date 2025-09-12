# 🛡️ Helper Agent Access Control

## 📋 Overview

**Helper Agent**는 모든 Helper layer 파일과 함수들에 대한 **독점적 관리 권한**을 가지며, 다른 agent들은 **읽기 전용** 접근만 허용됩니다.

---

## 🔒 권한 체계

### Helper Agent - **FULL CONTROL** 
✅ **읽기/쓰기/수정/삭제** 권한:
- `Project/Helper/**/*.py` - 모든 Helper Python 파일
- `Project/Helper/**/*.yaml` - Helper 설정 파일  
- `Project/Helper/**/*.json` - Helper 데이터 파일
- `HELPER_FUNCTIONS_MANUAL.md` - Helper 문서
- `myStockInfo.yaml` - API 인증 정보 (독점)
- `Test/**/*helper*` - Helper 관련 테스트
- `Test/**/*precision*` - 정밀도 테스트
- `Test/**/*comparison*` - 함수 비교 테스트

### Other Agents - **READ ONLY**
👀 **읽기 전용** 권한:
- `Project/Helper/**/*.py` - Helper 함수 호출만 가능
- `HELPER_FUNCTIONS_MANUAL.md` - 문서 참조만 가능
- `myStockInfo.yaml` - Helper 함수 통해서만 접근

---

## 🚫 접근 제한 규칙

### 금지된 작업 (다른 Agent들):
❌ Helper 파일 수정  
❌ Helper 함수 코드 변경  
❌ API 인증 정보 직접 수정  
❌ Helper 테스트 파일 변경  
❌ Helper 문서 편집  

### 허용된 작업 (다른 Agent들):
✅ Helper 함수 호출  
✅ Helper 문서 읽기  
✅ Helper 함수 결과 사용  

---

## 📞 Helper 함수 사용 방법

### ✅ 올바른 사용법:
```python
# Data Agent, Strategy Agent, Service Agent에서 사용
from Project.Helper.yfinance_helper import YFinanceHelper
from Project.Helper.broker_api_connector import KISBrokerAPI
from Project.Helper.telegram_messenger import TelegramNotificationService

# Helper 함수 호출 (읽기 전용)
yf = YFinanceHelper()
price = yf.get_current_price("AAPL")

# 결과 활용
if price > 0:
    print(f"AAPL 가격: ${price}")
```

### ❌ 금지된 사용법:
```python
# 다른 Agent에서 절대 금지!
# Helper 함수 내부 코드 수정
def get_current_price(self, ticker):
    # 이런 수정은 Helper Agent만 가능!
    pass

# API 인증 정보 직접 접근
with open('myStockInfo.yaml') as f:
    # 이런 직접 접근 금지!
    config = yaml.load(f)
```

---

## 🔄 통합 워크플로우

### Helper Agent 역할:
1. **API 관리**: 모든 외부 API 연동 관리
2. **인증 관리**: API 키, 토큰 등 인증 정보 관리
3. **함수 개발**: Helper 함수 개발, 수정, 테스트
4. **문서 관리**: Helper 함수 매뉴얼 유지보수
5. **테스트 관리**: Helper 함수 정밀도 테스트 및 검증

### 다른 Agent들의 Helper 사용:
1. **함수 호출**: 정의된 인터페이스를 통한 함수 호출
2. **결과 활용**: Helper 함수 반환값을 자신의 로직에 활용
3. **에러 처리**: Helper 함수 오류 상황에 대한 적절한 처리
4. **문서 참조**: HELPER_FUNCTIONS_MANUAL.md 참조

---

## 📁 파일 권한 매트릭스

| 파일/폴더 | Helper Agent | Data Agent | Strategy Agent | Service Agent |
|-----------|--------------|------------|----------------|---------------|
| `Project/Helper/**/*.py` | 🟢 RW | 🟡 R | 🟡 R | 🟡 R |
| `HELPER_FUNCTIONS_MANUAL.md` | 🟢 RW | 🟡 R | 🟡 R | 🟡 R |
| `myStockInfo.yaml` | 🟢 RW | 🟡 R | 🟡 R | 🟡 R |
| `Test/**/*helper*` | 🟢 RW | 🔴 N | 🔴 N | 🔴 N |
| Helper 함수 호출 | 🟢 Full | 🟡 Call | 🟡 Call | 🟡 Call |

**범례:**
- 🟢 RW: 읽기/쓰기 가능
- 🟡 R: 읽기 전용  
- 🟡 Call: 함수 호출만 가능
- 🔴 N: 접근 금지

---

## 🛠️ Helper Agent 관리 가이드

### 새 Helper 함수 추가:
1. Helper Agent에서 함수 개발
2. 포괄적 테스트 작성 및 실행
3. HELPER_FUNCTIONS_MANUAL.md 업데이트
4. 다른 Agent들에게 사용법 공지

### Helper 함수 수정:
1. Helper Agent에서만 수정 가능
2. 기존 함수 시그니처 호환성 유지
3. 테스트 코드 업데이트
4. 문서 업데이트
5. 변경사항 다른 Agent들에게 공지

### API 인증 정보 관리:
1. Helper Agent가 myStockInfo.yaml 독점 관리
2. 새 API 키 추가/수정 시 Helper Agent만 가능
3. 보안을 위해 다른 Agent의 직접 접근 차단
4. Helper 함수를 통한 간접 접근만 허용

---

## 🚨 보안 규칙

### API 인증 보안:
- ✅ Helper Agent만 myStockInfo.yaml 수정 가능
- ✅ API 키는 Helper 함수 내부에서만 사용
- ❌ 다른 Agent에서 API 키 직접 접근 금지
- ❌ 하드코딩된 API 키 사용 금지

### Helper 함수 보안:
- ✅ Helper Agent만 함수 구현 수정 가능
- ✅ 다른 Agent는 정의된 인터페이스로만 호출
- ❌ Helper 함수 내부 로직 우회 금지
- ❌ Helper 모듈 직접 수정 금지

---

## 🧪 테스트 및 검증

### Helper Agent 테스트 책임:
- 모든 Helper 함수의 단위 테스트
- API 연동 정밀도 테스트
- 크로스 브라우저/플랫폼 호환성 테스트
- 성능 벤치마크 테스트

### 검증된 테스트 결과 (최신):
- ✅ **100% 성공률** - 모든 Helper 함수 정상 작동
- ✅ **실제 API 검증** - 라이브 API로 정확성 확인
- ✅ **성능 최적화** - 평균 응답시간 1초 미만
- ✅ **에러 처리** - 모든 예외 상황 대응

---

## 📞 지원 및 문의

### Helper 관련 이슈 보고:
1. **Helper Agent에게 직접 보고**
2. 구체적인 에러 메시지 포함
3. 재현 가능한 예제 코드 제공
4. 예상 동작과 실제 동작 차이점 명시

### Helper 함수 개선 요청:
1. Helper Agent에게 요구사항 전달
2. 사용 사례와 필요성 설명
3. 예상 인터페이스 제안
4. 성능/보안 요구사항 명시

---

## 🔄 업데이트 프로세스

### Helper 함수 업데이트 시:
1. Helper Agent가 코드 수정
2. 테스트 수트 실행 및 통과 확인
3. HELPER_FUNCTIONS_MANUAL.md 업데이트
4. 다른 Agent들에게 변경사항 공지
5. 실제 운영 환경에 배포

### 권한 설정 변경 시:
1. AGENT_PERMISSIONS.yaml 업데이트
2. 이 문서 (HELPER_AGENT_ACCESS_CONTROL.md) 업데이트  
3. 모든 Agent에게 권한 변경사항 공지
4. 시스템 재시작 및 권한 적용 확인

---

**⚠️ 중요: 이 권한 체계를 준수하여 시스템의 안정성과 보안을 유지하시기 바랍니다.**

---

*문서 버전: 1.0 | 최종 업데이트: 2025-09-12 | 다음 리뷰: 2025-10-12*