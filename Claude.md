# Claude AI Assistant 프로젝트 핵심 규칙

**프로젝트명**: AI Assistant Multi-Agent Trading System
**버전**: 1.0
**작성일**: 2025-09-15
**업데이트**: 모든 작업 시 필수 로드 및 적용

---

## 🔥 핵심 프로젝트 규칙 (필수 준수)

### 1. 멀티 에이전트 협업 시스템
이 프로젝트는 **여러개의 SubAgent를 연결하여 협업하는 시스템**입니다.

```
Orchestrator Agent (메인 관리자)
├── Data Agent (데이터 수집 및 지표 관리)
├── Strategy Agent (전략 개발 및 신호 생성)
├── Service Agent (백테스팅, 실행, DB 관리)
└── Helper Agent (외부 API 및 브로커 연결)
```

### 2. 오케스트레이터 에이전트 역할
**메인 에이전트인 오케스트레이터 에이전트가 전체 프로젝트를 관리**합니다.
- 전체 워크플로우 조정
- 각 서브 에이전트 작업 할당
- 에이전트간 통신 중재
- 시스템 상태 모니터링

### 3. 프롬프트 관리 체계
**오케스트레이터 에이전트가 각 서브 에이전트가 해야할 프롬프트를 작성하여 전달**합니다.
- 작업별 명확한 프롬프트 정의
- 에이전트 역할에 맞는 지시사항
- 결과 포맷 및 품질 기준 명시
- 에러 처리 및 fallback 절차

### 4. 파일 접근 권한 체계
**각각의 에이전트는 할당된 파일만 쓰기와 읽기가 가능**하며, **각각의 레이어간 인터페이스는 정의된 규칙에 따릅니다**.

#### 접근 권한 매트릭스:
- **Data Agent**: `Project/indicator/**/*.py`, `Project/database/**/*.py` (READ-ONLY for others)
- **Strategy Agent**: `Project/strategy/**/*.py` (EXCLUSIVE)
- **Service Agent**: `Project/service/**/*.py`, `Project/database/**/*.py` (shared with Data Agent)
- **Helper Agent**: `Project/Helper/**/*.py`, `myStockInfo.yaml` (EXCLUSIVE)

### 5. 파일 조직 및 배치 규칙 (신규)
**프로젝트 파일들은 명확한 규칙에 따라 조직되어야 합니다**.

#### 파일 배치 규칙:
- **테스트 파일**: 모든 `test_*.py` 파일은 `Test/` 폴더에 배치
- **데모 파일**: 모든 `*demo*.py` 파일은 `Test/Demo/` 폴더에 배치
- **프로덕션 파일**: 실제 운영 파일들은 루트 또는 적절한 프로젝트 폴더에 배치
- **설정 파일**: 모든 YAML 설정 파일은 `config/` 폴더에 배치

#### 폴더 구조:
```
Project/                    # 에이전트별 실제 코드
├── indicator/             # Data Agent 전용
├── strategy/              # Strategy Agent 전용
├── service/               # Service Agent 전용
└── Helper/                # Helper Agent 전용

Test/                      # 모든 테스트 파일
├── Demo/                  # 데모 및 예제 파일
├── test_*.py              # 각종 테스트 파일
└── *.py                   # 기타 테스트 관련 파일

config/                    # 설정 파일들
├── agent_model.yaml       # 에이전트 모델 설정
├── api_credentials.yaml   # API 자격증명
├── broker_config.yaml     # 브로커 설정
├── risk_management.yaml   # 리스크 관리
└── *.yaml                 # 기타 설정 파일

storage/                   # 데이터 저장소
├── agent_interactions/    # 에이전트 상호작용 로그
└── outputs/              # 결과 파일들
```

#### 파일 생성 규칙:
- **새로운 데모 파일**: 반드시 `Test/Demo/` 폴더에 생성
- **새로운 테스트 파일**: 반드시 `Test/` 폴더에 생성
- **임시 실험 파일**: `Test/` 폴더 하위에 적절한 위치에 생성
- **프로덕션 코드**: 에이전트별 지정된 폴더에 생성

---

## 📋 설정 파일 관리 규칙

### 6. 인터페이스 정의
**인터페이스는 `agent_interfaces.yaml` 파일에 정의되어 있습니다**.
- 에이전트간 함수 호출 규약
- 데이터 전달 포맷 정의
- 에러 처리 프로토콜
- 버전 호환성 관리

### 7. API 자격증명 관리
**계좌 정보와 API 키 정보들은 `api_credentials.yaml` 파일에 정의합니다**.
```yaml
# api_credentials.yaml 구조
brokers:
  kis:
    real_account: "encrypted_credentials"
    virtual_account: "encrypted_credentials"
  ls_securities:
    credentials: "encrypted_data"

external_apis:
  alpha_vantage: "api_key"
  telegram: "bot_token"
```

### 8. 브로커 설정 관리
**실제 마켓 오픈시간과 모의 계좌 실제 구분 등의 정보는 `broker_config.yaml` 파일에 정의합니다**.
- 마켓 오픈/클로즈 시간
- 거래 가능 상품 정의
- 주문 타입 및 제한사항
- 계좌 타입별 설정

### 9. 파일 소유권 관리
**각각의 파일에 대한 접근 권한 정보는 `file_ownership.yaml`에 정의합니다**.
- READ/WRITE/EXECUTE 권한 매트릭스
- 에이전트별 파일 접근 범위
- 크로스 에이전트 접근 규칙
- 보안 및 격리 정책

### 10. LLM 모델 할당 (신규)
**각각의 에이전트의 사용 LLM 모델은 `agent_model.yaml`에 기록합니다**.
```yaml
# agent_model.yaml 구조 예시
agents:
  orchestrator:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "claude-3-sonnet-20240229"
  data_agent:
    primary_model: "claude-3-sonnet-20240229"
    fallback_model: "gemini-pro"
  strategy_agent:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "gemini-pro"
```

### 11. 리스크 관리 분리 (신규)
**계좌의 리스크 매니지먼트 정보는 `risk_management.yaml`에 정의합니다**.
**기존 `broker_config.yaml`에 있던 내용을 분리합니다**.

분리 대상:
- `max_position_size`, `max_daily_loss`
- `max_orders_per_minute`, `max_concentration`
- `min_order_amount`, `max_order_amount`
- `default_stop_loss`, `max_stop_loss`

---

## 🤖 LLM 모델 관리 규칙

### 12. 구독 모델 체계 (신규)
**각각의 에이전트의 모델은 구독 모델을 사용하며, Gemini 모델을 Claude Code에서 사용하기 위해 라우터를 사용합니다**.

#### 모델 선택 기준:
- **Claude-3-Opus**: 복잡한 전략 개발, 중요한 의사결정
- **Claude-3-Sonnet**: 일반적인 데이터 처리, 서비스 운영
- **Gemini-Pro**: 대용량 데이터 분석, 빠른 응답 필요시

### 13. LLM 라우터 구현 (신규)
**LLM 모델 라우터는 `https://github.com/musistudio/claude-code-router`를 활용하여 구현합니다**.

#### 라우터 기능:
- 에이전트별 모델 자동 할당
- 모델 간 load balancing
- API 사용량 최적화
- Fallback 모델 자동 전환

---

## 🔒 보안 및 운영 규칙

### 데이터 보안
- API 키는 암호화하여 저장
- 실제 계좌 정보 접근 시 추가 인증
- 로그에 민감 정보 포함 금지
- 에이전트간 권한 격리 유지

### 에러 처리
- 각 에이전트별 독립적 에러 처리
- 시스템 전체 장애 방지를 위한 격리
- 자동 복구 메커니즘 구현
- 상세한 에러 로깅 및 알림

### 모니터링
- 에이전트별 성능 지표 추적
- API 사용량 및 비용 모니터링
- 시스템 리소스 사용량 추적
- 실시간 알림 시스템 운영

---

## ⚡ 필수 작업 흐름

### 모든 작업 시 확인사항:
1. [ ] 해당 에이전트의 파일 접근 권한 확인
2. [ ] 필요한 설정 파일들 로드 확인
3. [ ] 인터페이스 규약 준수 확인
4. [ ] 에러 처리 로직 구현
5. [ ] 로깅 및 모니터링 적용

### 설정 변경 시:
1. [ ] 관련 YAML 파일 업데이트
2. [ ] 영향 받는 에이전트들에게 변경사항 전파
3. [ ] 테스트 환경에서 검증
4. [ ] 프로덕션 배포 및 모니터링

### 새로운 기능 추가 시:
1. [ ] 에이전트 역할 분담 검토
2. [ ] 인터페이스 정의 업데이트
3. [ ] 파일 소유권 할당
4. [ ] 테스트 케이스 작성

---

## 🎯 성공 지표

### 시스템 안정성
- 에이전트간 협업 성공률 > 99%
- API 호출 실패율 < 1%
- 시스템 가용시간 > 99.9%

### 성능 최적화
- 응답 시간 < 5초 (일반 작업)
- 메모리 사용률 < 80%
- CPU 사용률 < 70%

### 보안 준수
- 권한 위반 사건 = 0
- 데이터 유출 사건 = 0
- 보안 감사 통과율 = 100%

---

## 📞 지원 및 문의

### 문제 발생 시:
1. **에이전트 협업 이슈**: `agent_interfaces.yaml` 확인
2. **권한 문제**: `file_ownership.yaml` 검토
3. **설정 오류**: 해당 YAML 파일 검증
4. **LLM 모델 이슈**: `agent_model.yaml` 및 라우터 상태 확인

### 문서 업데이트:
- 이 규칙은 프로젝트 진행에 따라 지속 업데이트됩니다
- 모든 변경사항은 버전 관리되며 이력을 추적합니다
- 새로운 규칙 추가 시 모든 에이전트에게 즉시 반영됩니다

---

## ✅ 체크리스트

### 프로젝트 시작 전:
- [ ] 모든 YAML 설정 파일 확인
- [ ] 에이전트별 권한 매트릭스 검토
- [ ] LLM 라우터 연결 테스트
- [ ] API 자격증명 검증

### 작업 진행 중:
- [ ] 이 규칙 문서 참조
- [ ] 에이전트간 인터페이스 준수
- [ ] 파일 접근 권한 확인
- [ ] 에러 처리 구현

### 작업 완료 후:
- [ ] 테스트 케이스 실행
- [ ] 문서 업데이트
- [ ] 성능 지표 확인
- [ ] 보안 검토 완료

---

**🚨 중요: 이 규칙은 모든 Claude 작업 세션에서 반드시 로드하고 적용해야 합니다.**

*규칙 버전: 1.0 | 최종 업데이트: 2025-09-15*