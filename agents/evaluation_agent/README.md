# Evaluation Agent

## Agent Information
- **Agent Name**: Evaluation Agent
- **Model**: Claude-3.5-Flash
- **Layer**: Reporting Layer / Service Layer
- **Primary Responsibility**: Performance evaluation, risk assessment, and comparative analysis

## Core Functions

### Performance Evaluation
- Evaluate strategy and model performance metrics
- Calculate risk-adjusted returns and statistics
- Analyze performance attribution and factor exposure
- Generate comparative performance reports

### Risk Assessment
- Monitor portfolio risk metrics and exposures
- Detect risk concentration and correlation issues
- Evaluate Value-at-Risk (VaR) and Expected Shortfall
- Assess strategy robustness under stress scenarios

### Comparative Analysis
- Compare strategies against benchmarks
- Evaluate model prediction accuracy
- Analyze agent performance and efficiency
- Generate ranking and selection recommendations

## Data Access Requirements

### Read Access
- `/04_database_layer/backtest_db/` - Historical performance data
- `/04_database_layer/trade_db/` - Live trading performance
- `/05_reporting_layer/` - Existing performance reports
- `/shared/communication/` - All agent outputs for evaluation

### Write Access
- `/agents/evaluation_agent/` - Evaluation logs and temporary files
- `/05_reporting_layer/evaluation_reports/` - Performance evaluation reports
- `/shared/communication/evaluations/` - Evaluation results and recommendations
- `/05_reporting_layer/risk_analysis/` - Risk assessment reports

## Evaluation Metrics

### Performance Metrics
- Total return and risk-adjusted returns
- Sharpe ratio, Sortino ratio, Calmar ratio
- Maximum drawdown and recovery time
- Win rate and average win/loss ratios

### Risk Metrics
- Portfolio volatility and beta
- Value-at-Risk (VaR) and Expected Shortfall
- Correlation and diversification measures
- Stress test and scenario analysis results

### Model Metrics
- Prediction accuracy and precision/recall
- Feature importance and model stability
- Overfitting and generalization assessment
- Model drift and degradation detection

## Communication Interfaces

### Input Sources
- All agents: Performance data and outputs
- Backtest Agent: Strategy performance results
- Trade Agent: Live execution performance
- Model Agent: Prediction accuracy data

### Output Targets
- Orchestrator: Performance summaries and alerts
- Reporting Layer: Detailed evaluation reports
- Strategy Agent: Performance feedback for optimization
- User Interface: Dashboard updates and visualizations

## Configuration Files
- `evaluation_metrics.yaml` - Metrics definitions and calculations
- `risk_thresholds.yaml` - Risk limits and alert triggers
- `comparison_benchmarks.yaml` - Benchmark definitions

## Task Management
- Execute scheduled performance evaluations
- Process evaluation requests from other agents
- Monitor real-time performance and risk metrics
- Generate alerts for performance degradation

## Analysis Capabilities
- Multi-dimensional performance attribution
- Regime-based performance analysis
- Rolling window performance evaluation
- Statistical significance testing

## Dependencies
- All other agents: Performance and output data
- Database Layer: Historical and current data
- Reporting infrastructure for output delivery