# Backtest Agent

## Agent Information
- **Agent Name**: Backtest Agent
- **Model**: Claude-3.5-Flash
- **Layer**: Service Layer / Database Layer
- **Primary Responsibility**: Strategy backtesting, performance analysis, and validation

## Core Functions

### Strategy Backtesting
- Execute historical strategy simulations
- Test trading strategies against historical data
- Simulate order execution and market impact
- Generate performance metrics and statistics

### Performance Analysis
- Calculate risk-adjusted returns (Sharpe, Sortino ratios)
- Analyze drawdown patterns and recovery times
- Measure strategy consistency across market conditions
- Compare strategy performance against benchmarks

### Validation and Optimization
- Validate strategy parameters and assumptions
- Identify optimal parameter ranges
- Detect overfitting and robustness issues
- Generate confidence intervals for performance metrics

## Data Access Requirements

### Read Access
- `/04_database_layer/market_db/` - Historical market data
- `/02_strategy_layer/` - Strategy configurations and signals
- `/01_indicator_layer/` - Historical indicator calculations
- `/shared/configs/backtest/` - Backtesting parameters

### Write Access
- `/agents/backtest_agent/` - Agent-specific results and logs
- `/04_database_layer/backtest_db/` - Backtest results and analysis
- `/shared/communication/backtest_results/` - Performance reports
- `/05_reporting_layer/backtest_reports/` - Detailed analysis reports

## Communication Interfaces

### Input Sources
- Strategy Agent: Strategy definitions and parameters
- Data Agent: Historical market data
- Model Agent: ML model predictions for validation

### Output Targets
- Strategy Agent: Performance feedback and optimization suggestions
- Evaluation Agent: Strategy comparison data
- Reporting Layer: Performance visualization
- Orchestrator: Backtesting status and recommendations

## Configuration Files
- `backtest_config.yaml` - Backtesting parameters and settings
- `performance_metrics.yaml` - Metrics calculation definitions
- `benchmark_settings.yaml` - Benchmark comparison configurations

## Task Management
- Execute scheduled strategy backtests
- Process backtest requests from Strategy Agent
- Generate periodic performance reviews
- Update backtest database with new results

## Analysis Capabilities
- Monte Carlo simulation for robustness testing
- Walk-forward analysis for temporal validation
- Cross-validation across different market periods
- Stress testing under extreme market conditions

## Dependencies
- Data Agent: Historical data feeds
- Strategy Agent: Strategy definitions
- Model Agent: Predictive model outputs
- Database infrastructure for result storage