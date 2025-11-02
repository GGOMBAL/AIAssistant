# 코드 품질 규칙

**최종 업데이트**: 2025-10-21
**적용 대상**: 모든 Agent 및 모든 Python 코드

---

## 1. 파일 라인 수 제한

### 기본 규칙:
- **신규 파일은 1000줄 이내를 목표로 작성**
- **최대 1500줄까지 허용** (1500줄 초과 시 반드시 모듈 분리)
- 파일 생성/수정 시 라인 수 자동 체크
- 기존 파일은 점진적으로 1000줄 이하로 리팩토링

### 예외 사항:
- **메인 실행 파일** (main_auto_trade.py 등): 2000줄까지 허용
- **통합 설정 파일** (CLAUDE.md 등): 분리 권장하지만 예외 가능

### 라인 수 초과 시 조치:
1. **1000-1500줄**: 경고 발생, 다음 작업 시 분리 검토
2. **1500줄 초과**: 즉시 모듈 분리 필수
   - 관련 기능별로 별도 파일 생성
   - 공통 유틸리티는 `utils/` 폴더로 분리
   - 클래스별로 파일 분리 검토

### 모듈 분리 예시:
```python
# Before: monolithic_service.py (2000 lines)
class BacktestService:
    def __init__(self): ...
    def run_backtest(self): ...
    def calculate_metrics(self): ...
    def generate_report(self): ...
    def save_results(self): ...

# After: Split into modules
# backtest_service.py (500 lines) - Main orchestration
# backtest_metrics.py (400 lines) - Metrics calculation
# backtest_reporter.py (400 lines) - Report generation
# backtest_storage.py (300 lines) - Result storage
```

---

## 2. 이모지 사용 금지

### 핵심 규칙:
**Python 코드, 로그 메시지, 주석에 이모지(✅, ❌, 🚀 등) 사용 절대 금지**

### 이유:
- **Windows cp949 인코딩 환경에서 UnicodeEncodeError 발생 방지**
- 크로스 플랫폼 호환성 보장
- 로그 파일의 가독성 유지

### 대체 표현:
| 이모지 | 대체 텍스트 |
|-------|-----------|
| ✅ | [OK] |
| ❌ | [FAIL] 또는 [ERROR] |
| ⚠️ | [WARNING] |
| ℹ️ | [INFO] |
| 🚀 | [STARTED] |
| 🏁 | [COMPLETED] |
| 📊 | [DATA] |
| 💰 | [PRICE] |
| 📈 | [UP] |
| 📉 | [DOWN] |

### 올바른 사용 예시:

```python
# ❌ 잘못된 예
print("✅ Backtest completed successfully!")
logger.info("🚀 Starting trading system...")
print(f"📊 Total trades: {total_trades}")

# ✅ 올바른 예
print("[OK] Backtest completed successfully!")
logger.info("[STARTED] Starting trading system...")
print(f"[DATA] Total trades: {total_trades}")
```

### 예외:
- **문서 파일(.md, .txt)에서는 이모지 사용 가능**
- Markdown 문서에서 시각적 구분을 위한 이모지는 허용

---

## 3. 모듈 인터페이스 관리

### 기본 규칙:
- **모든 Layer는 인터페이스 문서(MD)를 반드시 작성**
- **모듈 간 통신은 문서화된 인터페이스를 통해서만 수행**
- 각 Layer의 담당 Agent가 문서를 기억하고 관리

### 인터페이스 문서 위치:
```
docs/interfaces/
├── HELPER_LAYER_INTERFACE.md
├── DATABASE_LAYER_INTERFACE.md
├── INDICATOR_LAYER_INTERFACE.md
├── STRATEGY_LAYER_INTERFACE.md
├── SERVICE_LAYER_INTERFACE.md
└── REPORT_LAYER_INTERFACE.md
```

### 인터페이스 변경 시:
1. **Orchestrator에게 변경 요청**
2. **영향 받는 모든 Agent와 협의**
3. **승인 후 변경 실행**
4. **인터페이스 문서 즉시 업데이트**
5. **관련 Agent에게 변경사항 통보**

---

## 4. 코딩 스타일

### Python 코딩 표준:
- **PEP 8** 준수
- **Type hints** 적극 사용
- **Docstrings** 필수 작성

### Docstring 형식:
```python
def calculate_signal(
    df_daily: pd.DataFrame,
    df_weekly: pd.DataFrame,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Calculate trading signal based on daily and weekly data.

    Args:
        df_daily: Daily price data with OHLCV columns
        df_weekly: Weekly price data with technical indicators
        threshold: Minimum signal strength threshold (default: 0.5)

    Returns:
        Dictionary containing:
            - final_signal: SignalType enum (BUY/SELL/HOLD)
            - signal_strength: float (0.0 to 1.0)
            - confidence: float (0.0 to 1.0)
            - target_price: float
            - losscut_price: float

    Raises:
        ValueError: If dataframes are empty or missing required columns

    Example:
        >>> signal = calculate_signal(df_D, df_W, threshold=0.6)
        >>> print(signal['final_signal'])
        SignalType.BUY
    """
    # Implementation
    pass
```

### 변수 명명 규칙:
```python
# ✅ 올바른 예
df_daily = load_daily_data()
signal_strength = calculate_strength()
is_backtest = True
MAX_POSITIONS = 10

# ❌ 잘못된 예
d = load_daily_data()  # 너무 짧음
signalStrength = calculate_strength()  # camelCase 대신 snake_case 사용
ib = True  # 의미 불명확
maxPositions = 10  # 상수는 UPPER_CASE
```

---

## 5. 에러 처리

### 기본 원칙:
- **모든 외부 API 호출은 try-except로 감싸기**
- **구체적인 예외 타입 지정**
- **에러 로그 남기기**
- **적절한 기본값 또는 fallback 제공**

### 에러 처리 예시:
```python
# ✅ 올바른 예
def load_market_data(symbol: str) -> pd.DataFrame:
    """Load market data with proper error handling"""
    try:
        data = fetch_from_api(symbol)
        if data is None or data.empty:
            logger.warning(f"[WARNING] No data for {symbol}, returning empty DataFrame")
            return pd.DataFrame()
        return data

    except ConnectionError as e:
        logger.error(f"[ERROR] Connection failed for {symbol}: {e}")
        return pd.DataFrame()

    except ValueError as e:
        logger.error(f"[ERROR] Invalid data for {symbol}: {e}")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"[ERROR] Unexpected error for {symbol}: {e}")
        return pd.DataFrame()

# ❌ 잘못된 예
def load_market_data(symbol: str) -> pd.DataFrame:
    """No error handling - dangerous!"""
    data = fetch_from_api(symbol)  # What if this fails?
    return data
```

---

## 6. 로깅 규칙

### 로그 레벨:
- **DEBUG**: 개발 중 디버깅 정보
- **INFO**: 일반 실행 흐름 정보
- **WARNING**: 경고 (처리는 계속됨)
- **ERROR**: 에러 (일부 기능 실패)
- **CRITICAL**: 치명적 오류 (시스템 중단)

### 로깅 예시:
```python
import logging
logger = logging.getLogger(__name__)

# DEBUG
logger.debug("[DEBUG] DataFrame shape: %s", df.shape)

# INFO
logger.info("[INFO] Loaded %d symbols from database", len(symbols))

# WARNING
logger.warning("[WARNING] Missing data for %s, using fallback", symbol)

# ERROR
logger.error("[ERROR] Failed to calculate signal for %s: %s", symbol, e)

# CRITICAL
logger.critical("[CRITICAL] MongoDB connection lost, system halted")
```

### 로그 메시지 형식:
```python
# ✅ 올바른 예
logger.info("[INFO] Backtest completed: %.2f%% return", total_return * 100)
logger.error("[ERROR] Symbol %s failed validation: %s", symbol, reason)

# ❌ 잘못된 예
logger.info(f"Backtest completed: {total_return * 100}%")  # f-string 대신 %s 사용
logger.error("Error!")  # 구체적 정보 없음
```

---

## 7. 테스트 코드

### 테스트 파일 위치:
- 모든 `test_*.py` 파일은 `Test/` 폴더에 배치
- 통합 테스트: `Test/integration/`
- 유닛 테스트: `Test/unit/`

### 테스트 커버리지:
- **핵심 로직**: 80% 이상
- **유틸리티 함수**: 60% 이상
- **UI/CLI 코드**: 30% 이상

### 테스트 명명 규칙:
```python
def test_signal_generation_with_valid_data():
    """Test that signal generation works with valid input"""
    pass

def test_signal_generation_with_empty_data():
    """Test that signal generation handles empty dataframe"""
    pass

def test_signal_generation_with_missing_columns():
    """Test that signal generation raises error for missing columns"""
    pass
```

---

## 8. Git Commit 메시지

### Commit 메시지 형식:
```
<type>: <subject>

<body>

<footer>
```

### Type:
- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **docs**: 문서 수정
- **refactor**: 코드 리팩토링
- **test**: 테스트 추가/수정
- **chore**: 빌드/설정 변경

### 예시:
```
feat: Add real-time monitoring for held positions

- Monitor buy signal stocks (top 10)
- Monitor currently held positions
- Display separate lists for each category

Agents: Service
Ref: main_auto_trade.py:2087-2131
```

---

## 9. 코드 리뷰 체크리스트

### 제출 전 확인사항:
- [ ] 파일 라인 수 1500줄 이하
- [ ] 이모지 사용하지 않음
- [ ] 모든 함수에 docstring 작성
- [ ] Type hints 추가
- [ ] 에러 처리 구현
- [ ] 로그 메시지 포함
- [ ] 테스트 코드 작성
- [ ] 인터페이스 문서 업데이트

---

## 참조 문서

- **Agent 협업**: `docs/rules/AGENT_COLLABORATION.md`
- **파일 권한**: `docs/rules/FILE_PERMISSIONS.md`
- **MongoDB 규칙**: `docs/rules/MONGODB_RULES.md`
