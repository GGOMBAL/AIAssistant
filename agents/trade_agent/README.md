# Trade Agent

## Agent Information
- **Agent Name**: Trade Agent
- **Model**: Claude-3.5-Flash
- **Layer**: Service Layer / User Interface Layer
- **Primary Responsibility**: Trade execution, order management, and trade tracking

## Core Functions

### Trade Execution
- Execute buy/sell orders based on strategy signals
- Manage order types (market, limit, stop-loss)
- Handle trade timing and execution optimization
- Interface with trading platforms and brokers

### Order Management
- Queue and prioritize trade orders
- Monitor order status and fills
- Handle partial fills and order modifications
- Implement trade validation and safety checks

### Trade Tracking
- Record all executed trades in Trade DB
- Track trade performance and slippage
- Monitor position updates in real-time
- Generate trade confirmations and notifications

## Data Access Requirements

### Read Access
- `/02_strategy_layer/signals/` - Trading signals from Strategy Agent
- `/04_database_layer/market_db/` - Current market prices and data
- `/shared/configs/trading/` - Trading configuration and limits
- `/shared/communication/strategy_outputs/` - Strategy decisions

### Write Access
- `/agents/trade_agent/` - Agent-specific logs and temporary files
- `/04_database_layer/trade_db/` - Trade records and execution data
- `/06_ui_layer/trading_service/` - Trading interface updates
- `/shared/communication/trade_updates/` - Trade status communications

## Communication Interfaces

### Input Sources
- Strategy Agent: Trading signals and position sizing
- Market Data: Real-time price feeds
- Account Analysis Service: Available capital and margin

### Output Targets
- Audit Trade Service: Trade verification
- Reporting Layer: Trade performance data
- Orchestrator: Execution status updates
- User Interface: Trade confirmations

## Configuration Files
- `trading_config.yaml` - Trading parameters and limits
- `broker_settings.yaml` - Broker API configurations
- `execution_rules.yaml` - Trade execution logic and timing

## Task Management
- Process trade signals in order of priority
- Execute trades within specified time windows
- Handle emergency stop/liquidation commands
- Provide real-time execution status updates

## Safety Mechanisms
- Pre-trade validation and risk checks
- Maximum position size enforcement
- Daily loss limit monitoring
- Broker connection health monitoring

## Dependencies
- Strategy Agent: Trade signals
- Data Agent: Market data feeds  
- API Agent: Broker connectivity
- Account services: Balance verification