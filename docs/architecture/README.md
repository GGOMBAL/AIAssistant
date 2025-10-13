# Architecture Documentation

**Version**: 1.0
**Last Updated**: 2025-10-06
**Managed by**: Orchestrator Agent

---

## 📐 아키텍처 문서 개요

이 폴더는 AI Assistant Multi-Agent Trading System의 모든 아키텍처 관련 문서를 포함합니다.

---

## 📚 문서 목록

### 시스템 전체 아키텍처

1. **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - 시스템 아키텍처 개요
   - 전체 시스템 구조
   - 주요 컴포넌트 설명
   - 시스템 플로우

2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - 전체 시스템 아키텍처
   - 상세 시스템 설계
   - 레이어별 구조

3. **[ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md)** - 아키텍처 가이드
   - 아키텍처 사용 가이드
   - 설계 원칙 및 패턴

4. **[UNIFIED_SYSTEM_ARCHITECTURE.md](UNIFIED_SYSTEM_ARCHITECTURE.md)** - 통합 시스템 아키텍처
   - 통합 아키텍처 뷰
   - 전체 시스템 통합

### 멀티 에이전트 시스템

5. **[MULTI_AGENT_SYSTEM_ARCHITECTURE.md](MULTI_AGENT_SYSTEM_ARCHITECTURE.md)** - 멀티 에이전트 시스템
   - 에이전트 간 협업 구조
   - 통신 아키텍처
   - 작업 분산 전략

### 에이전트별 아키텍처

6. **[DATA_AGENT_ARCHITECTURE.md](DATA_AGENT_ARCHITECTURE.md)** - Data Agent 아키텍처
   - 데이터 수집 및 처리 구조
   - 기술지표 계산 파이프라인

7. **[STRATEGY_AGENT_ARCHITECTURE.md](STRATEGY_AGENT_ARCHITECTURE.md)** - Strategy Agent 아키텍처
   - 전략 개발 프레임워크
   - 신호 생성 아키텍처

8. **[HELPER_AGENT_ARCHITECTURE.md](HELPER_AGENT_ARCHITECTURE.md)** - Helper Agent 아키텍처
   - 외부 API 연동 구조
   - 유틸리티 서비스 아키텍처

### 특수 시스템 아키텍처

9. **[DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)** - MongoDB 구조
   - 데이터베이스 스키마
   - 컬렉션 구조
   - 인덱싱 전략

10. **[SERVICE_LAYER_BACKTEST_ARCHITECTURE.md](SERVICE_LAYER_BACKTEST_ARCHITECTURE.md)** - 백테스트 아키텍처
    - 백테스트 엔진 구조
    - 성능 분석 시스템
    - 결과 저장 및 검증

---

## 🔗 관련 문서

### 인터페이스 문서
- [AGENT_INTERFACES.md](../AGENT_INTERFACES.md) - 에이전트 간 통신 프로토콜
- [INTERFACE_SPECIFICATION.md](../INTERFACE_SPECIFICATION.md) - 레이어 간 데이터 인터페이스

### 프로젝트 문서
- [CLAUDE.md](../../CLAUDE.md) - 프로젝트 핵심 규칙
- [docs/README.md](../README.md) - 문서 시스템 개요

---

## 📖 읽기 순서 추천

### 시스템 전체 이해
1. ARCHITECTURE_OVERVIEW.md (시작점)
2. MULTI_AGENT_SYSTEM_ARCHITECTURE.md (에이전트 협업)
3. UNIFIED_SYSTEM_ARCHITECTURE.md (통합 뷰)

### 에이전트 개발
1. MULTI_AGENT_SYSTEM_ARCHITECTURE.md (에이전트 구조)
2. 해당 에이전트 아키텍처 문서 (DATA/STRATEGY/HELPER)
3. ../AGENT_INTERFACES.md (통신 프로토콜)

### 데이터베이스 작업
1. DATABASE_ARCHITECTURE.md (DB 구조)
2. DATA_AGENT_ARCHITECTURE.md (데이터 처리)
3. ../INTERFACE_SPECIFICATION.md (데이터 형식)

### 백테스트 시스템
1. SERVICE_LAYER_BACKTEST_ARCHITECTURE.md (백테스트 엔진)
2. STRATEGY_AGENT_ARCHITECTURE.md (전략 구조)
3. DATABASE_ARCHITECTURE.md (데이터 저장)

---

## 🎯 아키텍처 원칙

### 설계 원칙
1. **모듈화**: 각 에이전트는 독립적으로 동작
2. **확장성**: 새로운 에이전트 추가 용이
3. **유지보수성**: 명확한 책임 분리
4. **성능**: 병렬 처리 및 최적화

### 통신 원칙
1. **표준화**: 정의된 인터페이스 준수
2. **비동기**: 블로킹 최소화
3. **에러 처리**: 견고한 오류 복구
4. **모니터링**: 성능 및 상태 추적

---

**업데이트 정책**: 아키텍처 변경 시 즉시 문서 업데이트
**관련 문서**: 모든 아키텍처 문서는 상호 연결되어 있습니다
