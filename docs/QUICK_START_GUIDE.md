# 🚀 Multi-Agent Trading System 빠른 시작 가이드

## ⚡ 5분만에 시작하기

### 1단계: 준비사항 확인 (1분)
```bash
# Python 버전 확인
python --version  # 3.8 이상 필요

# 필수 라이브러리 설치
pip install pymongo pandas numpy pyyaml

# MongoDB 실행 확인
mongo --host localhost:27017
```

### 2단계: 프로젝트 디렉토리 이동 (30초)
```bash
cd C:\WorkSpace\AIAgentProject\AIAssistant\Project
```

### 3단계: 첫 실행 (3분)
```bash
# 자동 모드로 첫 실행
python multi_agent_trading_system.py --auto
```

### 4단계: 결과 확인 (30초)
실행이 완료되면 다음과 같은 결과를 확인할 수 있습니다:
- 백테스트 수익률
- 거래 통계
- 시장별 성과

---

## 📊 즉시 사용 가능한 명령어

### 기본 실행 명령어
```bash
# 1. 자동 모드 (추천 - 초보자용)
python multi_agent_trading_system.py --auto

# 2. 대화형 모드 (맞춤 설정)
python multi_agent_trading_system.py

# 3. 개별 에이전트 테스트
python data_agent.py      # 데이터 로딩 테스트
python strategy_agent.py  # 신호 생성 테스트
python service_agent.py   # 백테스트 테스트
```

### 기본 설정 (수정 불필요)
- **백테스트 기간**: 2023년 전체 (1년)
- **초기 자본**: 1억원
- **NASDAQ 종목**: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX
- **NYSE 종목**: JPM, BAC, WMT, JNJ, PG, KO, DIS, IBM
- **리스크 관리**: 자동 손절/익절

---

## 🎯 기대 결과

### 정상 실행 시 출력 예시
```
Multi-Agent Trading System 시작...

[시스템 검증] 시스템 요구사항 확인 중...
[정보] MongoDB 연결: healthy
[정보] 설정 파일: 4/4
[정보] 전체 상태: healthy
[정보] 데이터베이스: 31 개 트레이딩 DB 발견
[성공] 시스템 검증 완료 - 백테스트 실행 가능

[Phase 1] Data Agent 작업 시작
[Data Agent] 16개 종목 데이터 로딩 중...
[Data Agent] 기술지표 계산 완료

[Phase 2] Strategy Agent 작업 시작
[Strategy Agent] 194개 매매신호 생성 완료

[Phase 3] Service Agent 작업 시작
[Service Agent] 백테스트 실행 완료

================================================================================
                         백테스트 결과 요약
================================================================================
[정보] 총 수익률: 0.36%
[정보] 연율화 수익률: 0.53%
[정보] 샤프 비율: 0.603
[정보] 승률: 46.43%
[정보] 총 거래 수: 61회
================================================================================

[완료] Multi-Agent Trading System 실행이 완료되었습니다.
```

### 실행 시간 가이드
- **전체 실행 시간**: 약 2-3분
- **데이터 로딩**: 1.5초 (15,000+ 종목 스캔)
- **신호 생성**: 0.5초 (194개 신호)
- **백테스트 실행**: 0.05초 (250일 시뮬레이션)

---

## ❗ 문제 해결 (자주 발생하는 오류)

### 1. MongoDB 연결 오류
```bash
오류: "MongoDB connection failed"
해결: net start MongoDB
```

### 2. 모듈 없음 오류
```bash
오류: "No module named 'pymongo'"
해결: pip install pymongo pandas numpy pyyaml
```

### 3. 데이터베이스 없음 오류
```bash
오류: "Database not found"
해결: MongoDB에 NasDataBase_D, NysDataBase_D 확인
```

### 4. 권한 오류
```bash
오류: "Permission denied"
해결: 관리자 권한으로 실행
```

---

## 🔧 맞춤 설정 (선택사항)

### 다른 종목으로 테스트하기
```bash
# 대화형 모드 실행
python multi_agent_trading_system.py

# 원하는 종목 입력
NASDAQ 종목: AAPL,NVDA,TSLA,AMD
NYSE 종목: JPM,KO,DIS,V
```

### 다른 기간으로 테스트하기
```bash
# 대화형 모드에서
시작일: 2024-01-01
종료일: 2024-06-30
```

---

## 📞 도움이 필요하신가요?

### 1. 상세 매뉴얼 확인
```bash
# 전체 매뉴얼 (50+ 페이지)
docs/USER_MANUAL.md
```

### 2. 개별 에이전트 도움말
```bash
python data_agent.py --help
python strategy_agent.py --help
```

### 3. 로그 파일 확인
```bash
# 실행 후 생성되는 로그 파일
multi_agent_system.log
```

---

## ✅ 체크리스트 (첫 실행 전)

- [ ] Python 3.8+ 설치됨
- [ ] `pip install pymongo pandas numpy pyyaml` 실행함
- [ ] MongoDB 실행 중 (`net start MongoDB`)
- [ ] 프로젝트 디렉토리 (`Project/`)에 있음
- [ ] `python multi_agent_trading_system.py --auto` 실행 준비됨

**모든 항목 체크 완료 → 바로 실행하세요! 🚀**

---

## 🎉 성공적인 첫 실행을 위한 팁

1. **처음에는 자동 모드 사용**: 복잡한 설정 없이 바로 결과 확인
2. **결과를 차근차근 읽어보기**: 각 Phase별 진행 상황 모니터링
3. **로그 확인하기**: 상세한 실행 과정은 로그 파일에서 확인
4. **에러 발생 시 당황하지 말기**: 대부분 간단한 설정 문제

**Happy Trading! 📈**