# Trading Visualization System

## 📊 개요

AI Trading System을 위한 종합적인 시각화 모듈입니다. Pandas Data Analysis MCP를 활용하여 주식 차트, 매매 시그널, 백테스트 결과를 시각화합니다.

## ✨ 주요 기능

### 1. 주식 차트 시각화 (`stock_chart_visualizer.py`)
- **캔들스틱 차트**: OHLC 데이터 시각화
- **매수/매도 시그널**: 차트에 시그널 표시
- **기술지표**: SMA20, SMA50, SMA200 오버레이
- **거래량 차트**: 하단 서브플롯에 거래량 표시
- **인터랙티브 차트**: Plotly를 사용한 줌/팬 기능

### 2. 백테스트 결과 시각화 (`backtest_visualizer.py`)
- **성과 대시보드**: 4개 차트를 한 화면에 표시
- **누적 수익률**: 포트폴리오 vs 벤치마크
- **드로우다운 분석**: 최대 낙폭 시각화
- **거래 분석**: 승률, P&L 분포, 상위 수익 종목
- **성과 지표 테이블**: 샤프비율, 수익률 등

### 3. MongoDB 직접 연동 (`mongodb_data_loader.py`) ⭐ NEW
- **직접 데이터베이스 연결**: MONGODB_LOCAL 서버 직접 접속
- **다양한 데이터 타입 지원**: 일간/주간/RS/펀더멘털/실적 데이터
- **멀티 마켓 지원**: NASDAQ (8,944종목), NYSE (6,277종목), KOSPI, KOSDAQ, HSI
- **데이터 캐싱**: 빠른 재조회를 위한 메모리 캐싱
- **백테스트 결과 로드**: MongoDB에 저장된 백테스트 결과 직접 조회

### 4. 시스템 통합 (`trading_visualizer_integration.py`)
- **MongoDB 직접 연동**: 데이터베이스에서 직접 데이터 로드
- **Layer 간 데이터 변환**: Indicator/Strategy Layer 데이터 처리
- **자동 파일 저장**: HTML/PNG/PDF 형식 지원
- **포트폴리오 분석**: 보유 종목 및 섹터 분포
- **여러 종목 동시 처리**: 병렬 데이터 로드 및 시각화

## 📦 설치

### 필수 라이브러리
```bash
pip install pandas numpy plotly matplotlib seaborn
```

### 선택적 라이브러리 (고급 기능)
```bash
pip install kaleido  # 이미지 내보내기
pip install mplfinance  # 고급 금융 차트
```

## 🚀 빠른 시작

### 1. 주식 차트 생성
```python
from visualization import StockChartVisualizer

# 시각화 객체 생성
visualizer = StockChartVisualizer()

# 캔들스틱 차트 생성
fig = visualizer.create_candlestick_chart(
    df=stock_data,           # DataFrame with OHLCV
    ticker="AAPL",           # 종목 코드
    buy_signals=buy_df,      # 매수 시그널
    sell_signals=sell_df,    # 매도 시그널
    show_volume=True,        # 거래량 표시
    show_sma=True           # 이동평균 표시
)

# 차트 저장
visualizer.save_chart(fig, "AAPL_chart.html", format='html')
```

### 2. 백테스트 결과 시각화
```python
from visualization import BacktestVisualizer

# 백테스트 시각화 객체 생성
backtest_viz = BacktestVisualizer()

# 성과 대시보드 생성
dashboard = backtest_viz.create_performance_dashboard(
    backtest_results=results,    # 백테스트 결과 딕셔너리
    benchmark_data=benchmark      # 벤치마크 데이터 (선택)
)

# 대시보드 저장
dashboard.write_html("backtest_dashboard.html")
```

### 3. 시스템 통합 사용
```python
from visualization import TradingVisualizerIntegration

# 통합 객체 생성 (MongoDB 연동)
integration = TradingVisualizerIntegration(db_address="MONGODB_LOCAL")

# MongoDB에서 직접 데이터 로드하여 시각화
result = integration.visualize_stock_with_signals(
    ticker="AAPL",
    market="NASDAQ",
    start_date="2024-01-01",
    end_date="2024-10-14",
    load_from_db=True,        # MongoDB에서 직접 로드
    save=True
)

# 여러 종목 동시 시각화
multi_result = integration.visualize_multiple_stocks_from_db(
    tickers=["AAPL", "MSFT", "GOOGL"],
    market="NASDAQ",
    save=True
)

# 백테스트 결과 시각화
backtest_result = integration.visualize_backtest_results(
    backtest_output=backtest_data,  # Service Layer 출력
    benchmark=benchmark_series,
    save=True
)
```

### 4. MongoDB 데이터 직접 로드
```python
from visualization.mongodb_data_loader import MongoDBDataLoader

# 데이터 로더 생성
loader = MongoDBDataLoader(db_address="MONGODB_LOCAL")

# 개별 종목 데이터 로드
df = loader.load_stock_data(
    ticker="AAPL",
    market="NASDAQ",
    data_type="daily",
    start_date="2024-01-01",
    end_date="2024-10-14"
)

# 사용 가능한 종목 리스트 조회
tickers = loader.get_available_tickers(market="NASDAQ")
print(f"Available stocks: {len(tickers)}")  # 8,944 stocks
```

## 📁 파일 구조

```
visualization/
├── __init__.py                      # 모듈 초기화
├── stock_chart_visualizer.py        # 주식 차트 시각화
├── backtest_visualizer.py           # 백테스트 결과 시각화
├── trading_visualizer_integration.py # 시스템 통합
└── README.md                        # 문서

Test/
├── Demo/
│   ├── demo_visualization.py        # 시각화 데모
│   └── charts/                      # 생성된 차트 저장
└── test_visualization_integration.py # 통합 테스트

visualization_output/                # 기본 출력 디렉토리
├── *.html                          # 인터랙티브 차트
├── *.png                           # 정적 이미지
└── test_summary.json               # 테스트 결과
```

## 🎨 차트 종류

### 주식 차트
- **캔들스틱 차트**: 가격 움직임 시각화
- **시그널 분포**: 월별 매수/매도 시그널 분포
- **기술지표 오버레이**: SMA, 볼린저 밴드 등

### 백테스트 차트
- **포트폴리오 가치**: 시간에 따른 자산 가치 변화
- **월별 수익률**: 바 차트로 표시된 월별 성과
- **드로우다운**: 최고점 대비 하락폭
- **거래 분석**: 승률, P&L 분포, 거래 빈도

### 포트폴리오 차트
- **보유 종목 파이 차트**: 종목별 비중
- **섹터 분포**: 섹터별 투자 비중
- **상위 수익 종목**: 수익 기여도 상위 종목

## 🔧 커스터마이징

### 색상 테마 변경
```python
visualizer = StockChartVisualizer()
visualizer.default_colors = {
    'buy': '#00FF00',   # 매수 시그널 색상
    'sell': '#FF0000',  # 매도 시그널 색상
    'up': '#26a69a',    # 상승 캔들 색상
    'down': '#ef5350'   # 하락 캔들 색상
}
```

### 차트 레이아웃 조정
```python
fig.update_layout(
    title="Custom Title",
    height=800,           # 차트 높이
    template='plotly_dark',  # 다크 테마
    showlegend=True
)
```

## 📊 데이터 형식

### 주가 데이터 (DataFrame)
```python
# 필수 컬럼
df = pd.DataFrame({
    'Open': [...],     # 시가
    'High': [...],     # 고가
    'Low': [...],      # 저가
    'Close': [...],    # 종가
    'Volume': [...]    # 거래량
})
df.index = pd.DatetimeIndex(...)  # 날짜 인덱스
```

### 시그널 데이터
```python
# 매수/매도 시그널
buy_signals = pd.DataFrame({
    'Price': [...],         # 시그널 가격
    'Signal_Type': [...]    # 시그널 타입
})
buy_signals.index = pd.DatetimeIndex(...)
```

### 백테스트 결과
```python
backtest_results = {
    'portfolio_value': pd.Series(...),   # 포트폴리오 가치
    'returns': pd.Series(...),           # 일일 수익률
    'drawdown': pd.Series(...),          # 드로우다운
    'trades': {...},                     # 거래 통계
    'metrics': {...}                     # 성과 지표
}
```

## 🐛 문제 해결

### 차트가 표시되지 않음
- 브라우저에서 JavaScript가 활성화되어 있는지 확인
- HTML 파일을 로컬에서 열 때 파일 경로 확인

### 메모리 부족
- 대용량 데이터는 샘플링하여 사용
- `head_limit` 파라미터로 데이터 제한

### 한글 표시 문제
- matplotlib 한글 폰트 설정 확인
- Plotly는 기본적으로 한글 지원

## 📚 추가 리소스

- [Plotly Documentation](https://plotly.com/python/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Trading System Documentation](../docs/)

## 🤝 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

## 📝 라이선스

이 프로젝트는 AI Trading System의 일부입니다.

---

**Version**: 1.0.0
**Last Updated**: 2024-10-14
**Author**: AI Trading System Team