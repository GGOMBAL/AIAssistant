# 🚀 자동매매 시스템 빠른 시작 가이드

## 1. 시스템 구동 방법

### 🖱️ 간단한 방법
```bash
# Windows 배치파일 실행
start_trading.bat
```

### 💻 직접 실행
```bash
# Python으로 직접 실행
python main_auto_trade.py
```

## 2. 실제 거래 설정 (중요!)

### ✅ 자동 설정 완료

시스템이 `myStockInfo.yaml` 파일에서 자동으로 KIS API 설정을 로드합니다:

- **기본값**: 모의투자 계정 (VIRTUAL1) 자동 사용
- **실투자 전환**: `main_auto_trade.py` 파일 43번째 줄 수정
  ```python
  use_virtual = False  # 실투자로 변경하려면 False
  ```

### 🔧 계정 변경 방법

다른 계정을 사용하려면 `main_auto_trade.py`에서 계정 정보 변경:
```python
# 모의투자 계정들
VIRTUAL1_APP_KEY, VIRTUAL1_APP_SECRET, VIRTUAL1_CANO

# 실투자 계정들
REAL_APP_KEY, REAL_APP_SECRET, REAL_CANO
REAL2_APP_KEY, REAL2_APP_SECRET, REAL2_CANO
# ... REAL6까지 사용 가능
```

## 3. 시스템 동작 확인

### 📊 실행 후 확인 사항

1. **시스템 시작 로그**
   ```
   === 자동매매 시스템 시작 ===
   ✅ 시스템 시작 완료
   ✅ 자동 거래 활성화 완료
   🚀 자동매매 시스템 운영 시작
   ```

2. **주기적 상태 출력** (30초마다)
   ```
   📈 시스템 상태: 14:30:15
      실행상태: True
      거래활성: True
      처리신호: 4개
      실행주문: 2개
      현재신호: 2개
      포트폴리오: $100,000
      일일손익: 🟢 $1,250 (+1.25%)
      리스크상태: 🟢 NORMAL
   ```

## 4. 시스템 제어

### 🛑 안전한 종료
- **Ctrl+C** 누르면 안전하게 종료됩니다
- 진행 중인 주문은 완료 후 종료됩니다

### ⚙️ 실시간 설정 변경
시스템 실행 중에는 설정 변경이 불가능합니다.
변경이 필요하면 시스템을 중단하고 설정 수정 후 재시작하세요.

## 5. 매매 신호 추가 방법

### 🤖 실제 Strategy Layer 연동 (신규!)

시스템이 실제 Strategy Layer에서 candidates와 holdings를 기반으로 신호를 생성합니다:

```python
# Strategy Integration Service가 자동으로 실행
# 1. Helper Agent에서 계좌 데이터 수집 (보유 종목, 잔고)
# 2. Data Agent에서 시장 데이터 수집 (기술 지표, RS 데이터)
# 3. Strategy Layer 구성요소들이 실제 신호 생성:
#    - SignalGenerationService: 다중 타임프레임 분석
#    - PositionSizingService: 매수 후보 선정
#    - AccountAnalysisService: 보유 종목 분석
# 4. 생성된 신호를 AutoTradeOrchestrator에 전송

# 실행 시 로그 예시:
# Strategy Layer에서 실제 매매 신호 생성 중...
# Strategy Layer에서 5개 실제 신호 생성 완료
# 📊 Strategy 신호 추가: AAPL BUY (신뢰도: 0.85)
```

### 🔄 신호 생성 프로세스

1. **보유 종목 분석**: AccountAnalysisService로 현재 포트폴리오 분석
2. **매수 후보 선정**: PositionSizingService로 candidates 생성
3. **기술적 분석**: SignalGenerationService로 다중 타임프레임 신호 생성
4. **매도 신호**: 보유 종목의 기술적 매도 조건 체크
5. **통합 신호**: 모든 분석 결과를 TradingSignal로 변환

## 6. 로그 확인

### 📜 로그 파일
- **파일 위치**: `auto_trade.log`
- **내용**: 모든 거래 활동, 에러, 상태 변화 기록

### 🔍 실시간 모니터링
실행 중인 콘솔에서 실시간으로 모든 활동을 확인할 수 있습니다.

## 7. 안전 장치

### 🛡️ 자동 리스크 관리
- 일일 손실 5% 초과 시 자동 거래 중단
- 포지션 집중도 20% 초과 시 신규 주문 제한
- 급격한 가격 변동 시 리스크 알림

### 🚨 긴급 상황 대응
- 시스템 오류 시 안전 모드로 전환
- 네트워크 끊김 시 자동 재연결
- API 한도 초과 시 대기 후 재시도

## 8. 문제 해결

### ❌ 시스템 시작 실패
1. KIS API 설정 확인
2. 네트워크 연결 상태 확인
3. 로그 파일에서 상세 오류 메시지 확인

### ⚠️ 거래 활성화 실패
1. 계좌 상태 확인 (잔고, 거래 가능 여부)
2. 리스크 한도 설정 확인
3. API 연결 상태 확인

### 🔧 성능 문제
1. 메모리 사용량 확인
2. 네트워크 지연 시간 확인
3. 로그 레벨 조정 (INFO → WARNING)

## 9. 운영 팁

### 💡 권장 사항
1. **모의투자부터 시작**: 실투자 전 충분한 테스트
2. **소액으로 시작**: 초기에는 작은 금액으로 시작
3. **주기적 모니터링**: 하루에 몇 번씩 상태 확인
4. **로그 백업**: 중요한 거래 데이터 백업

### 📈 최적화 설정
```python
# 보수적 설정 (안전한 운영)
'risk_management': {
    'max_daily_loss': 0.02,      # 2%
    'max_position_size': 0.05,   # 5%
    'max_concentration': 0.15,   # 15%
}

# 적극적 설정 (높은 수익 추구)
'risk_management': {
    'max_daily_loss': 0.08,      # 8%
    'max_position_size': 0.15,   # 15%
    'max_concentration': 0.25,   # 25%
}
```

---

## ⚡ 즉시 시작하기

1. **자동 설정 확인** → `myStockInfo.yaml` 파일 존재 확인 ✅
2. **배치 파일 실행** → `start_trading.bat` 더블클릭
3. **상태 모니터링** → 콘솔 출력 확인
4. **안전 종료** → Ctrl+C

**🎯 목표**: 완전 자동화된 안전한 투자 시스템 운영

---

*"설정만 하면 알아서 거래하는 스마트한 투자 파트너"*