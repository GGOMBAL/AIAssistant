# Trading System - Execution Modules

**Created**: 2025-10-12
**Version**: 1.0

---

## 📋 What's New

3개의 독립 실행 모듈과 RUN AGENT 통합 관리 시스템이 생성되었습니다.

### Files Created:

1. **run_backtest.py** - 백테스트 실행 모듈
2. **run_auto_trading.py** - 자동 트레이딩 실행 모듈
3. **run_signal_check.py** - 개별 종목 신호 확인 모듈
4. **run_agent.py** (updated) - RUN AGENT 통합 관리자
5. **docs/EXECUTION_MODULES.md** - 상세 문서

---

## 🚀 Quick Start

### 방법 1: RUN AGENT 사용 (권장)

```bash
python run_agent.py
```

대화형 메뉴에서 1-3 선택:
- `1` - 백테스트 실행
- `2` - 자동 트레이딩 실행
- `3` - 개별 종목 확인

### 방법 2: 개별 실행

```bash
# 백테스트
python run_backtest.py

# 자동 트레이딩
python run_auto_trading.py

# 개별 종목 확인
python run_signal_check.py AAPL
```

---

## 📊 시스템 구조

```
RUN AGENT (run_agent.py)
    │
    ├── run_backtest.py          [백테스트]
    │   ├── FULL mode (전체 종목)
    │   └── LIMITED mode (500개)
    │
    ├── run_auto_trading.py      [자동 트레이딩]
    │   ├── REAL account
    │   ├── VIRTUAL account
    │   ├── FULL mode
    │   └── LIMITED mode
    │
    └── run_signal_check.py      [개별 종목]
        ├── Market detection
        ├── 3-year data analysis
        └── 5 DataFrame output
```

---

## 💡 주요 기능

### 1. run_backtest.py
- ✅ MongoDB에서 NASDAQ + NYSE 전체 종목 로드 (~15,000개)
- ✅ FULL/LIMITED 모드 지원
- ✅ 매매 시그널 자동 생성
- ✅ 백테스트 실행 및 결과 리포팅
- ✅ 결과: `Report/Backtest/backtest_report_*.yaml`

### 2. run_auto_trading.py
- ✅ REAL/VIRTUAL 계좌 모드
- ✅ 매수 신호 종목 자동 스크리닝
- ✅ 신호 강도 기준 정렬 (상위 20개)
- ✅ 실시간 시그널 생성
- ✅ 결과: `Report/AutoTrading/auto_trading_signals_*.yaml`
- ⚠️ KIS API 연동 필요 (주문 실행 향후 구현)

### 3. run_signal_check.py
- ✅ 특정 종목 상세 분석
- ✅ 마켓 자동 탐지 (NASDAQ/NYSE)
- ✅ 5가지 데이터프레임 전체 출력:
  - df_W (Weekly) - Last 5 rows
  - df_D (Daily) - Last 10 rows
  - df_RS (Relative Strength) - Last 5 rows
  - df_E (Earnings) - Last 5 rows
  - df_F (Fundamental) - Last 5 rows
- ✅ 결과: `Report/SignalCheck/signal_check_*.yaml`

### 4. RUN AGENT (run_agent.py)
- ✅ 3개 모듈 통합 관리
- ✅ 대화형 메뉴 인터페이스
- ✅ 프로세스 모니터링
- ✅ 실행 히스토리 추적
- ✅ 에러 처리 및 로깅

---

## 📁 Output Locations

```
Report/
├── Backtest/
│   └── backtest_report_YYYYMMDD_HHMMSS.yaml
│
├── AutoTrading/
│   └── auto_trading_signals_YYYYMMDD_HHMMSS.yaml
│
├── SignalCheck/
│   └── signal_check_<SYMBOL>_YYYYMMDD_HHMMSS.yaml
│
└── RunAgent/
    └── run_agent_log_YYYYMMDD_HHMMSS.yaml
```

---

## 🔧 Configuration

### Global Settings

각 모듈 상단에서 설정 변경 가능:

```python
# run_backtest.py
BACKTEST_MODE = 'FULL'  # or 'LIMITED'

# run_auto_trading.py
TRADING_MODE = 'FULL'   # or 'LIMITED'
ACCOUNT_TYPE = 'REAL'   # or 'VIRTUAL'

# run_signal_check.py
# 커맨드라인 인자로 심볼 전달: python run_signal_check.py AAPL
```

### MongoDB Settings

`myStockInfo.yaml` 파일 확인:
- MONGODB_LOCAL address
- MONGODB_PORT
- MONGODB_ID
- MONGODB_PW

---

## 📖 Documentation

상세 문서는 다음 파일 참조:

- **docs/EXECUTION_MODULES.md** - 실행 모듈 상세 가이드
- **docs/ARCHITECTURE_OVERVIEW.md** - 시스템 아키텍처
- **docs/AGENT_INTERFACES.md** - 에이전트 간 통신
- **Draw/Architecture Design v2.png** - 아키텍처 다이어그램

---

## ⚠️ Important Notes

### REAL Account Trading
```
WARNING: run_auto_trading.py에서 REAL 계좌 선택 시
실제 거래가 실행됩니다!
```

현재 KIS API 연동이 되어있지 않아 **주문 실행은 되지 않습니다**.
향후 KIS API 연동 후 실제 주문이 가능합니다.

### Performance

- **FULL mode**: ~15,000 symbols (NASDAQ + NYSE)
  - 처리 시간: 약 10-30분
  - 메모리: ~2GB 권장

- **LIMITED mode**: 500 symbols
  - 처리 시간: 약 1-3분
  - 메모리: ~1GB 권장

---

## 🐛 Troubleshooting

### 1. MongoDB Connection Error
```bash
# Check MongoDB is running
# Verify myStockInfo.yaml configuration
# Check connection pooling settings
```

### 2. No Symbols Found
```bash
# Verify databases exist: NasDataBase_D, NysDataBase_D
# Check collection names (no 'A' prefix)
# Ensure MongoDB has data
```

### 3. Module Not Found
```bash
# Ensure all 3 files exist in root directory:
ls run_backtest.py
ls run_auto_trading.py
ls run_signal_check.py
ls run_agent.py
```

---

## 🔄 Integration with Multi-Agent System

```
Orchestrator Agent
    ↓
├── HELPER_AGENT
├── DATABASE_AGENT
├── STRATEGY_AGENT
├── SERVICE_AGENT
└── RUN_AGENT ← 새로 추가됨
    ├── run_backtest.py
    ├── run_auto_trading.py
    └── run_signal_check.py
```

RUN AGENT는 다른 에이전트들과 **동등한 레벨의 독립 에이전트**입니다.

---

## 📝 Example Usage

### Example 1: 백테스트 실행

```bash
$ python run_backtest.py

============================================================
BACKTEST EXECUTION MODULE
============================================================

Backtest Period: 2024-10-12 ~ 2025-10-12
Mode: FULL

[1/4] Loading universe symbols...
  NASDAQ: 8,944 symbols
  NYSE: 6,277 symbols
  Total unique: 15,113 symbols

[2/4] Generating dataframes...
Dataframes generated: 14,892 symbols with data

[3/4] Generating trading signals...
Total signals processed: 14,892
  Buy signals: 142
  Sell signals: 28
  Hold signals: 14,722

[4/4] Running backtest...

============================================================
BACKTEST SUMMARY
============================================================
Total Return: 12.34%
Total Trades: 156
Win Rate: 54.23%
Sharpe Ratio: 1.234
Max Drawdown: -8.45%
============================================================

Results saved to: Report/Backtest/backtest_report_20251012_153045.yaml
```

### Example 2: 개별 종목 확인

```bash
$ python run_signal_check.py AAPL

================================================================================
INDIVIDUAL SYMBOL SIGNAL CHECK
================================================================================

Symbol: AAPL

[1/5] Checking market...
Market: NASDAQ

[2/5] Loading data...
Data loaded successfully (3 years)

[3/5] Generating signal...

[4/5] Signal Summary
================================================================================

Final Signal: BUY
Signal Strength: 8.5
Confidence: 0.85

Latest Price: $178.42
Day High: $179.20
Day Low: $177.15

Sector: Technology
Industry: Consumer Electronics

[5/5] DataFrame Details
================================================================================

[1/5] Weekly Data (df_W) - Last 5 rows:
--------------------------------------------------------------------------------
              Wopen    Whigh     Wlow   Wclose    52_H    52_L
2025-10-06  175.20   179.50   174.80   178.90  195.30  164.20
2025-09-29  172.40   175.80   171.90   175.20  195.30  164.20
...

Results saved to: Report/SignalCheck/signal_check_AAPL_20251012_153120.yaml
```

### Example 3: RUN AGENT 사용

```bash
$ python run_agent.py

================================================================================
                         RUN AGENT v2.1
                 Trading System Execution Manager
================================================================================

================================================================================
                     RUN AGENT - Execution Manager
================================================================================

Available Modules:
  1. Backtest Execution          (run_backtest.py)
  2. Auto Trading Execution      (run_auto_trading.py)
  3. Individual Signal Check     (run_signal_check.py)

  0. Exit
================================================================================

Enter choice (0-3): 1

Backtest Mode:
  1. FULL mode (all symbols)
  2. LIMITED mode (500 symbols)
Select mode (1-2): 2

[RUN AGENT] 백테스트 실행
...
```

---

## ✅ Testing Checklist

실행 모듈 테스트:

- [ ] `python run_backtest.py` - 백테스트 실행 확인
- [ ] `python run_auto_trading.py` - 자동 트레이딩 실행 확인
- [ ] `python run_signal_check.py AAPL` - 개별 종목 확인
- [ ] `python run_agent.py` - RUN AGENT 대화형 모드 확인
- [ ] Report 폴더에 결과 파일 생성 확인

---

## 🎯 Next Steps

### Immediate
1. Test all 3 modules individually
2. Test RUN AGENT integration
3. Verify output files are generated correctly

### Future Enhancements
1. **KIS API Integration** (run_auto_trading.py)
   - Real order execution
   - Position management
   - Auto stop-loss/take-profit

2. **Scheduler Integration**
   - Cron job support
   - Scheduled backtests
   - Auto trading at market open

3. **Notification System**
   - Email alerts
   - Telegram bot integration
   - Trading signal notifications

4. **Performance Dashboard**
   - Web UI for monitoring
   - Real-time status display
   - Historical performance charts

---

## 📞 Support

문제 발생 시:

1. 로그 파일 확인:
   - `backtest.log`
   - `auto_trading.log`
   - `signal_check.log`
   - `run_agent.log`

2. MongoDB 연결 확인:
   - `myStockInfo.yaml` 설정
   - MongoDB 서비스 실행 상태

3. 문서 참조:
   - `docs/EXECUTION_MODULES.md`
   - `docs/ARCHITECTURE_OVERVIEW.md`

---

**Version**: 1.0
**Created**: 2025-10-12
**Architecture**: Based on Architecture Design v2.png
