# Reporting Layer Documentation

## Overview

The Reporting Layer is responsible for all visualization and reporting functionality in the AI Trading System. It is managed by the **Report Agent**, which provides a centralized interface for generating charts, dashboards, and reports.

## Architecture

```
Reporting Layer
├── Report Agent (Manager)
│   ├── Backtest Dashboard Generation
│   ├── Stock Chart Generation
│   ├── Trading Monitor Dashboard
│   └── Signal Timeline Visualization
├── Services
│   ├── BacktestReportService
│   ├── StockChartReportService
│   ├── TradingMonitorService
│   └── SignalTimelineService
└── Visualization Components
    ├── Stock Chart Visualizer
    ├── Backtest Visualizer
    └── MongoDB Data Loader
```

## Integration with main_auto_trade.py

The Report Agent is fully integrated with all four options in `main_auto_trade.py`:

### Option 1: Auto Backtest with Dashboard
- **Function**: `run_auto_backtest()`
- **Report Feature**: Generates comprehensive backtest performance dashboard
- **Output**: HTML dashboard with portfolio value, drawdown, returns, and trade analysis

### Option 2: Individual Stock Signal with Chart
- **Function**: `check_single_symbol_signal()`
- **Report Feature**: Creates candlestick chart with buy/sell signals
- **Output**: Interactive HTML chart with technical indicators and signals

### Option 3: Auto Trading with Monitor Dashboard
- **Function**: `run_auto_trading()`
- **Report Feature**: Real-time trading monitor dashboard
- **Output**: Live dashboard showing positions, P&L, and pending orders

### Option 4: Signal Timeline Visualization
- **Function**: `show_ticker_signal_timeline()`
- **Report Feature**: Timeline visualization of multi-stage signals (W/D/RS/E/F)
- **Output**: Timeline chart showing signal evolution over time

## Report Agent API

### Initialization
```python
from project.reporting.report_agent import ReportAgent

# Initialize with configuration
config = load_config()
report_agent = ReportAgent(config)
```

### Core Methods

#### 1. Generate Backtest Report
```python
dashboard_path = report_agent.generate_backtest_report(
    backtest_results=results,  # From DailyBacktestService
    benchmark_data=benchmark,   # Optional benchmark comparison
    save=True                  # Save to file
)
```

#### 2. Generate Stock Signal Chart
```python
chart_path = report_agent.generate_stock_signal_chart(
    ticker="AAPL",
    stock_data=df_daily,       # DataFrame with OHLCV
    buy_signals=buy_df,        # Buy signal DataFrame
    sell_signals=sell_df,      # Sell signal DataFrame
    save=True
)
```

#### 3. Generate Trading Monitor Dashboard
```python
monitor_path = report_agent.generate_trading_monitor_dashboard(
    positions=current_positions,    # List of position dicts
    pending_orders=order_list,      # List of pending orders
    market_status=status_dict,      # Market status info
    save=True
)
```

#### 4. Generate Signal Timeline Chart
```python
timeline_path = report_agent.generate_signal_timeline_chart(
    ticker="AAPL",
    signals_data=signals_df,    # DataFrame with date/stage/signal
    save=True
)
```

## Output Files

All generated visualizations are saved to:
- **Directory**: `project/reporting/outputs/`
- **Formats**: HTML (interactive), PNG (static images)
- **Naming**: `{type}_{ticker}_{timestamp}.html`

Example outputs:
- `backtest_dashboard_20241014_143022.html`
- `AAPL_chart_20241014_143022.html`
- `trading_monitor_20241014_143022.html`
- `AAPL_timeline_20241014_143022.html`

## Services

### BacktestReportService
- Creates comprehensive backtest performance dashboards
- Includes portfolio value, drawdown analysis, trade statistics
- Supports benchmark comparison

### StockChartReportService
- Generates candlestick charts with technical indicators
- Overlays buy/sell signals on price charts
- Includes volume analysis

### TradingMonitorService
- Real-time position monitoring
- P&L tracking and analysis
- Order status visualization

### SignalTimelineService
- Multi-stage signal visualization (W/D/RS/E/F)
- Timeline view of signal evolution
- Signal strength heatmaps

## MongoDB Integration

The Reporting Layer directly connects to MongoDB for data retrieval:

```python
# MongoDB connection configuration
config = {
    'MONGODB_LOCAL': 'localhost',
    'MONGODB_PORT': 27017,
    'MONGODB_ID': 'admin',
    'MONGODB_PW': 'password'
}

# Supported markets
markets = ['NASDAQ', 'NYSE', 'KOSPI', 'KOSDAQ']

# Data types
data_types = ['daily', 'weekly', 'rs', 'fundamental', 'earnings']
```

## Usage Examples

### Example 1: Backtest with Visualization
```python
# Run backtest
backtest_results = await run_backtest_staged(
    symbols=["AAPL", "MSFT"],
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_cash=100000.0,
    config=config
)

# Generate dashboard
report = ReportAgent(config)
dashboard = report.generate_backtest_report(
    backtest_results=backtest_results,
    save=True
)
print(f"Dashboard saved to: {dashboard}")
```

### Example 2: Stock Chart with Signals
```python
# Check signal
signal_data = await check_single_symbol_signal("AAPL", config)

# Chart is automatically generated and saved
# Output: project/reporting/outputs/AAPL_chart_*.html
```

### Example 3: Trading Monitor
```python
# Run auto trading
buy_signals = await run_auto_trading(config)

# Monitor dashboard is automatically created
# Output: project/reporting/outputs/trading_monitor_*.html
```

### Example 4: Signal Timeline
```python
# Show timeline
await show_ticker_signal_timeline(config)
# Enter symbols when prompted: AAPL,MSFT,GOOGL

# Timeline charts are automatically generated
# Output: project/reporting/outputs/{ticker}_timeline_*.html
```

## Configuration

The Report Agent uses configuration from `myStockInfo.yaml`:

```yaml
# MongoDB settings
MONGODB_LOCAL: localhost
MONGODB_PORT: 27017

# Output settings
reporting:
  output_dir: project/reporting/outputs
  save_html: true
  save_png: false
  auto_open: false  # Auto-open in browser
```

## Dependencies

Required packages:
- `plotly>=5.0.0` - Interactive charting
- `pandas>=1.3.0` - Data manipulation
- `pymongo>=3.12.0` - MongoDB connection
- `numpy>=1.20.0` - Numerical operations

## Testing

Run the test suite to verify integration:

```bash
cd Test
python test_main_auto_trade_report.py
```

This will test:
1. Report Agent initialization
2. All four option integrations
3. File generation and saving
4. MongoDB connectivity

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Check MongoDB is running: `mongod --version`
   - Verify credentials in `myStockInfo.yaml`
   - Ensure correct database names (NasDataBase_D, NysDataBase_D)

2. **Chart Not Displaying**
   - Check Plotly installation: `pip install plotly`
   - Verify HTML file was created in `outputs/`
   - Open HTML file in modern browser

3. **No Data in Visualization**
   - Confirm MongoDB has data for requested symbols
   - Check date range covers available data
   - Verify symbol exists in database

## Future Enhancements

### Planned Features
- Real-time chart updates via WebSocket
- Multi-market comparison dashboards
- Advanced technical indicator overlays
- Portfolio optimization visualizations
- Risk analysis reports

### Integration Points
- Connect with live market data feeds
- Integrate with broker APIs for real-time positions
- Add alert system for signal changes
- Support for mobile responsive dashboards

## Support

For issues or questions:
1. Check this documentation
2. Review test scripts in `Test/` directory
3. Check MongoDB data availability
4. Verify all dependencies are installed

## Version History

- **v1.0.0** (2024-10-14): Initial release with full integration
  - Report Agent created
  - All four options integrated
  - MongoDB direct connection
  - Comprehensive visualization suite

---

**Last Updated**: 2024-10-14
**Maintainer**: Report Agent Team
**Contact**: [Project Repository]