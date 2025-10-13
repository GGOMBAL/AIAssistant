# Layer 문서화 가이드

**Version**: 1.0
**Last Updated**: 2025-10-09
**Purpose**: 각 Layer의 Agent가 문서를 작성하고 관리하는 방법

---

## 📋 개요

모든 Layer는 **3가지 필수 문서**를 작성하고 유지해야 합니다:
1. **INTERFACE.md**: 입출력 인터페이스 명세
2. **MODULES.md**: 모듈 설명 및 사용법
3. **SPEC.md**: 상세 로직 및 알고리즘

---

## 🎯 Layer별 필수 문서

### 1. Indicator Layer (Data Agent 책임)
📁 위치: `project/indicator/`

- ✅ `INDICATOR_LAYER_INTERFACE.md` - **완료**
- ⏳ `INDICATOR_MODULES.md` - TODO
- ⏳ `TECHNICAL_INDICATORS_SPEC.md` - TODO

### 2. Strategy Layer (Strategy Agent 책임)
📁 위치: `project/strategy/`

- ⏳ `STRATEGY_LAYER_INTERFACE.md` - TODO
- ⏳ `STRATEGY_MODULES.md` - TODO
- ⏳ `SIGNAL_GENERATION_SPEC.md` - TODO

### 3. Service Layer (Service Agent 책임)
📁 위치: `project/service/`

- ⏳ `SERVICE_LAYER_INTERFACE.md` - TODO
- ⏳ `SERVICE_MODULES.md` - TODO
- ⏳ `BACKTEST_SERVICE_SPEC.md` - TODO
- ⏳ `ORDER_EXECUTION_SPEC.md` - TODO

### 4. Helper Layer (Helper Agent 책임)
📁 위치: `project/Helper/`

- ⏳ `HELPER_LAYER_INTERFACE.md` - TODO
- ⏳ `HELPER_MODULES.md` - TODO
- ⏳ `API_INTEGRATION_SPEC.md` - TODO

### 5. Database Layer (Data Agent 책임)
📁 위치: `project/database/`

- ⏳ `DATABASE_LAYER_INTERFACE.md` - TODO
- ⏳ `DATABASE_MODULES.md` - TODO
- ⏳ `MONGODB_SCHEMA.md` - TODO

---

## 📝 문서 작성 템플릿

### INTERFACE.md 템플릿

```markdown
# [Layer Name] Interface Specification

**Version**: 1.0
**Last Updated**: YYYY-MM-DD
**Managed by**: [Agent Name]
**Status**: Draft | Active | Deprecated

## 1. Overview
- Layer 목적 및 역할
- 주요 기능 요약

## 2. Input Interface
- 입력 파라미터 타입 및 설명
- 필수/선택 파라미터
- 데이터 포맷 (DataFrame, Dict 등)

## 3. Output Interface
- 반환 값 타입 및 설명
- 데이터 구조 (컬럼 명세 등)
- 성공/실패 응답 포맷

## 4. Error Handling
- 예외 타입 및 발생 조건
- 에러 코드 정의
- 복구 방법

## 5. Examples
- 기본 사용 예제
- 엣지 케이스 처리 예제

## 6. Dependencies
- 의존하는 다른 Layer
- 필수 라이브러리

## 7. Version History
- 변경 이력 및 버전 정보
```

### MODULES.md 템플릿

```markdown
# [Layer Name] Modules Documentation

**Version**: 1.0
**Last Updated**: YYYY-MM-DD
**Managed by**: [Agent Name]

## 모듈 개요

### 모듈 목록
1. [Module 1 Name]
2. [Module 2 Name]
...

---

## Module 1: [Name]

### Purpose
모듈의 목적과 책임

### Location
`project/[layer]/[module_name].py`

### Main Classes/Functions
- `ClassName1`: 설명
- `function_name1()`: 설명

### Usage Example
```python
# 코드 예제
```

### Dependencies
- 의존 모듈
- 외부 라이브러리

---

## Module 2: [Name]
...
```

### SPEC.md 템플릿

```markdown
# [Layer Name] Detailed Specification

**Version**: 1.0
**Last Updated**: YYYY-MM-DD
**Managed by**: [Agent Name]

## 1. Algorithm Details
- 핵심 알고리즘 설명
- 수식 및 의사코드

## 2. Performance Characteristics
- 시간 복잡도
- 공간 복잡도
- 병목 지점

## 3. Data Flow
- 데이터 흐름도
- 상태 전이도

## 4. Configuration
- 설정 파라미터
- 기본값 및 권장값

## 5. Testing Strategy
- 테스트 접근 방법
- 주요 테스트 케이스

## 6. Known Limitations
- 알려진 제약사항
- 회피 방법
```

---

## 🔄 문서 관리 워크플로우

### 1. 코드 변경 시
```
코드 수정 → 영향 받는 문서 식별 → 문서 업데이트 → 버전 증가
```

### 2. 인터페이스 변경 시
```
인터페이스 변경 → INTERFACE.md 업데이트 → 의존 Layer에 통보 → Version History 기록
```

### 3. 새 모듈 추가 시
```
모듈 생성 → MODULES.md에 섹션 추가 → INTERFACE.md에 영향 확인 → 예제 코드 작성
```

### 4. 정기 검증
```
월 1회 → 모든 문서 검토 → 코드와 일치 여부 확인 → 필요시 업데이트
```

---

## ✅ 문서 작성 체크리스트

### INTERFACE.md
- [ ] Overview 작성
- [ ] Input/Output 파라미터 모두 문서화
- [ ] 예외 처리 시나리오 정의
- [ ] 최소 2개 이상의 사용 예제
- [ ] Dependencies 명시
- [ ] Version History 기록

### MODULES.md
- [ ] 모든 모듈 리스트업
- [ ] 각 모듈의 Purpose 명확히 설명
- [ ] 주요 클래스/함수 문서화
- [ ] 사용 예제 포함
- [ ] 상호 의존성 다이어그램 (선택)

### SPEC.md
- [ ] 핵심 알고리즘 설명
- [ ] 성능 특성 분석
- [ ] 설정 파라미터 문서화
- [ ] Known Limitations 명시
- [ ] 테스트 전략 수립

---

## 📊 문서 품질 기준

### 필수 (Must Have)
- ✅ 모든 public 인터페이스 문서화
- ✅ 입출력 타입 명시
- ✅ 에러 핸들링 설명
- ✅ 최소 1개 이상의 예제

### 권장 (Should Have)
- 📝 다이어그램 (플로우차트, 시퀀스 다이어그램)
- 📝 성능 벤치마크
- 📝 Best Practices
- 📝 Troubleshooting 가이드

### 선택 (Nice to Have)
- 💡 고급 사용 예제
- 💡 최적화 팁
- 💡 마이그레이션 가이드
- 💡 FAQ

---

## 🚀 시작하기

### For Data Agent (Indicator Layer)
1. ✅ `INDICATOR_LAYER_INTERFACE.md` 완료됨 (참고용)
2. ⏳ `INDICATOR_MODULES.md` 작성 시작
3. ⏳ `TECHNICAL_INDICATORS_SPEC.md` 작성

### For Strategy Agent
1. `STRATEGY_LAYER_INTERFACE.md` 작성 (INDICATOR 참고)
2. `STRATEGY_MODULES.md` 작성
3. `SIGNAL_GENERATION_SPEC.md` 작성

### For Service Agent
1. `SERVICE_LAYER_INTERFACE.md` 작성
2. `SERVICE_MODULES.md` 작성
3. `BACKTEST_SERVICE_SPEC.md` 작성
4. `ORDER_EXECUTION_SPEC.md` 작성

### For Helper Agent
1. `HELPER_LAYER_INTERFACE.md` 작성
2. `HELPER_MODULES.md` 작성
3. `API_INTEGRATION_SPEC.md` 작성

---

## 📞 문의 및 지원

문서 작성 중 질문이나 불명확한 부분이 있으면:
1. CLAUDE.md의 섹션 17-18 참조
2. 다른 Layer의 완성된 문서 참조 (예: `INDICATOR_LAYER_INTERFACE.md`)
3. Orchestrator Agent에게 문의

---

## 📅 완료 목표

- **Phase 1 (Week 1)**: 모든 INTERFACE.md 완료
- **Phase 2 (Week 2)**: 모든 MODULES.md 완료
- **Phase 3 (Week 3)**: 모든 SPEC.md 완료
- **Phase 4 (Week 4)**: 문서 검증 및 정합성 체크

---

**Last Updated**: 2025-10-09
**Document Owner**: Orchestrator Agent
