# Strategy Agent

## Agent Information
- **Agent Name**: Strategy Agent
- **Model**: Claude Opus 3.5
- **Layer**: Strategy Layer
- **Primary Responsibility**: Signal generation, position sizing, and strategic decision making

## Core Functions

### Signal Generation
- Generate trading signals based on indicator data
- Analyze market conditions and trends
- Process fundamental and technical analysis data
- Coordinate with Market Analysis Service

### Position Sizing
- Calculate optimal position sizes based on risk parameters
- Implement risk management strategies
- Account for portfolio balance and exposure limits

### Strategy Coordination
- Interface with other strategy layer components
- Coordinate signal timing with trade execution
- Validate strategy parameters and constraints

## Data Access Requirements

### Read Access
- `../../Project/indicator/` - All indicator data and calculations
- `../../Project/database/market_db/` - Historical market data
- `../../Project/database/backtest_db/` - Backtesting results
- `../../shared/configs/` - Strategy configuration files
- `../../shared/models/` - ML model outputs

### Write Access
- `./` - Agent-specific files and logs
- `../../Project/strategy/signals/` - Generated signals
- `../../Project/strategy/positions/` - Position sizing decisions
- `../../shared/communication/strategy_outputs/` - Communication with other agents

## Communication Interfaces

### Input Sources
- Indicator Layer: Technical and fundamental indicators
- Market Analysis Service: Market condition assessments
- Account Analysis Service: Portfolio status updates

### Output Targets
- Trade Agent: Execution signals
- Orchestrator: Strategy status and recommendations
- Reporting Layer: Performance metrics

## Configuration Files
- `strategy_config.yaml` - Strategy parameters and thresholds
- `risk_parameters.yaml` - Risk management settings
- `signal_weights.yaml` - Indicator weight configurations

## Task Management
- Receive tasks from Main Orchestrator via markdown files
- Process real-time market data updates
- Generate periodic strategy reviews
- Coordinate with backtesting for strategy validation

## Dependencies
- Data Agent: Market data feeds
- Model Agent: ML predictions
- API Agent: External data sources