# AI Assistant 프로젝트 재구성 계획

**계획 수립일**: 2025-09-15
**실행 담당**: Claude Code
**프로젝트**: Multi-Agent Trading System

---

## 📋 프로젝트 개요

### 목표
AI Assistant 프로젝트의 문서 및 설정 파일 체계화를 통한 멀티 에이전트 시스템 최적화

### 주요 변경사항
1. **Claude.md** 생성 - 프로젝트 핵심 규칙 정의
2. **MD 파일 구조화** - 문서 체계 정리
3. **새로운 YAML 설정 파일** 생성
4. **LLM 라우터 통합** 계획 수립

---

## 🗂️ 파일 구조 재정의

### 현재 구조
```
AIAssistant/
├── README.md
├── DATABASE_ARCHITECTURE.md
├── HELPER_FUNCTIONS_MANUAL.md
├── Report/
│   ├── final_indicator_validation_report.md
│   ├── indicator_validation_report_updated.md
│   ├── real_mongodb_integration_report.txt
│   └── test_output.txt
└── config/
    ├── agent_interfaces.yaml
    ├── broker_config.yaml
    └── file_ownership.yaml
```

### 목표 구조
```
AIAssistant/
├── Claude.md                          # 🆕 프로젝트 핵심 규칙
├── README.md                          # 메인 프로젝트 문서
├── docs/                              # 🆕 문서 폴더
│   ├── DATABASE_ARCHITECTURE.md
│   ├── HELPER_FUNCTIONS_MANUAL.md
│   └── ARCHITECTURE_OVERVIEW.md      # 🆕 전체 아키텍처
├── Report/                            # 테스트 리포트
├── plan/                              # 🆕 계획 문서
│   └── project_reorganization_plan.md
└── config/
    ├── agent_interfaces.yaml
    ├── agent_model.yaml              # 🆕 LLM 모델 정의
    ├── api_credentials.yaml          # 🆕 API 키 관리
    ├── broker_config.yaml            # 브로커 설정 (간소화)
    ├── risk_management.yaml          # 🆕 리스크 관리
    └── file_ownership.yaml
```

---

## 📝 실행 계획

### Phase 1: 핵심 문서 생성
- [x] plan 폴더 생성
- [x] 프로젝트 계획 문서 작성
- [ ] Claude.md 프로젝트 규칙 파일 생성
- [ ] docs 폴더 생성 및 문서 이동

### Phase 2: 설정 파일 재구성
- [ ] agent_model.yaml 생성 (LLM 모델 정의)
- [ ] broker_config.yaml에서 리스크 관리 부분 추출
- [ ] risk_management.yaml 생성
- [ ] api_credentials.yaml 템플릿 생성

### Phase 3: LLM 라우터 통합
- [ ] claude-code-router 연동 계획 수립
- [ ] Gemini 모델 라우팅 구조 설계
- [ ] 구독 모델 관리 방안 정의

---

## 🤖 멀티 에이전트 시스템 규칙

### 1. 에이전트 협업 구조
```
Orchestrator Agent (메인)
├── Data Agent (Indicator Layer)
├── Strategy Agent (Strategy Layer)
├── Service Agent (Service Layer)
└── Helper Agent (Service Layer)
```

### 2. 파일 접근 권한
- **agent_interfaces.yaml**: 인터페이스 정의
- **file_ownership.yaml**: 파일 접근 권한
- **agent_model.yaml**: 각 에이전트별 LLM 모델

### 3. 설정 관리
- **api_credentials.yaml**: 계좌/API 키 정보
- **broker_config.yaml**: 마켓 오픈시간, 계좌 구분
- **risk_management.yaml**: 리스크 매니지먼트 규칙

### 4. LLM 모델 관리
- **구독 모델 기반**: 각 에이전트별 모델 할당
- **Gemini 라우터**: claude-code-router 활용
- **모델 스위칭**: 작업별 최적 모델 선택

---

## 🎯 실행 단계별 상세 계획

### Step 1: Claude.md 생성
**목표**: 프로젝트 핵심 규칙 문서화
**내용**:
- 멀티 에이전트 시스템 구조
- 오케스트레이터 역할 정의
- 에이전트간 인터페이스 규칙
- 파일 접근 권한 원칙
- LLM 라우터 사용 규칙

### Step 2: 문서 구조화
**목표**: 기존 MD 파일들의 체계적 정리
**작업**:
- docs 폴더 생성
- 아키텍처 문서 이동
- 새로운 통합 아키텍처 문서 생성

### Step 3: 설정 파일 분리
**목표**: broker_config.yaml 최적화
**작업**:
- 리스크 관리 부분 추출
- risk_management.yaml 생성
- 각 에이전트별 모델 정의

### Step 4: LLM 라우터 통합
**목표**: Gemini 모델 활용 기반 구축
**작업**:
- claude-code-router 연동 방안
- 구독 모델 관리 시스템
- 모델별 성능 최적화

---

## 📊 예상 결과

### 개선 효과
1. **체계적 문서 관리**: 명확한 구조와 접근성
2. **효율적 설정 관리**: 용도별 파일 분리
3. **유연한 LLM 활용**: 다중 모델 지원
4. **명확한 규칙**: 에이전트간 협업 최적화

### 성공 지표
- [ ] 모든 문서가 용도별로 정리됨
- [ ] 설정 파일이 기능별로 분리됨
- [ ] LLM 라우터 연동 완료
- [ ] 에이전트 협업 규칙 명문화

---

## 🔄 다음 단계

이 계획 수립 후 단계별로 실행하여:
1. **즉시 실행**: Claude.md 및 문서 정리
2. **단기 목표**: 설정 파일 재구성
3. **중기 목표**: LLM 라우터 통합
4. **장기 목표**: 전체 시스템 최적화

---

*계획 수립 완료 - 실행 단계로 진행*