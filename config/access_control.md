# AIAgentProject - Access Control Matrix

## Overview
This document defines read/write permissions for each agent in the AIAgentProject multi-agent system. Each agent has specific access rights to ensure security and proper data flow.

## Permission Levels
- **R** = Read Access
- **W** = Write Access  
- **RW** = Read/Write Access
- **-** = No Access

## Access Control Matrix

| Path/Resource | Orchestrator | Strategy | Trade | Data | Model | Backtest | Evaluation | API | GetStock |
|---------------|-------------|----------|-------|------|-------|----------|------------|-----|----------|
| **Project Layer Access** |
| `./Project/indicator/` | R | R | R | W | R | R | R | - | W |
| `./Project/strategy/` | R | RW | R | - | W | R | R | - | - |
| `./Project/service/` | R | R | W | W | R | W | R | W | W |
| `./Project/database/` | R | R | W | RW | R | RW | R | - | W |
| `./Project/reporting/` | R | R | - | - | - | W | W | - | - |
| `./Project/ui/` | R | R | W | - | - | - | R | - | - |
| **Agent Directories** |
| `./agents/strategy_agent/` | R | RW | - | - | - | - | - | - | - |
| `./agents/trade_agent/` | R | - | RW | - | - | - | - | - | - |
| `./agents/data_agent/` | R | - | - | RW | - | - | - | R | R |
| `./agents/model_agent/` | R | - | - | - | RW | R | R | - | - |
| `./agents/backtest_agent/` | R | R | - | - | - | RW | R | - | - |
| `./agents/evaluation_agent/` | R | - | - | - | - | - | RW | - | - |
| `./agents/api_agent/` | R | - | R | R | - | - | - | RW | R |
| `./agents/getstockdata_agent/` | R | - | - | R | - | - | - | R | RW |
| **Shared Resources** |
| `./shared/configs/` | RW | R | R | R | R | R | R | R | R |
| `./shared/communication/` | RW | R | R | R | R | R | R | R | R |
| `./shared/models/` | R | R | - | - | RW | R | R | - | - |
| `./shared/external_apis/` | R | - | - | R | - | - | - | RW | R |
| `./shared/data_cache/` | R | - | - | W | - | - | - | W | RW |
| **Management** |
| `./orchestrator/` | RW | - | - | - | - | - | - | - | - |
| `./config/` | RW | - | - | - | - | - | - | - | - |
| `./docs/` | RW | - | - | - | - | - | - | - | - |

## Detailed Permissions by Agent

### Main Orchestrator Agent
**Full System Oversight**
- Read access to all layers and agent outputs
- Write access to system configuration and task management
- Exclusive write access to orchestrator directory
- Manages inter-agent communication channels

### Strategy Agent (Claude Opus 3.5)
**Strategy Management**
- Read: All indicator data, market data, backtest results
- Write: Strategy signals, position sizing decisions, model signals
- No access: Trade execution, raw data collection, system config

### Trade Agent (Claude-3.5-Flash)  
**Trade Execution**
- Read: Strategy signals, market data, trading configs
- Write: Trade database, UI updates, execution logs
- No access: Strategy generation, data collection, system config

### Data Agent (Claude Opus)
**Data Management**
- Read: External API configs, data requests
- Write: All databases, indicator layer, data cache
- Highest database write privileges for data integrity

### Model Agent (Claude-3.5-Flash)
**ML Model Management**
- Read: All training data, indicator data, backtest results  
- Write: Model artifacts, predictions, strategy layer model signals
- No access: Trade execution, data collection APIs

### Backtest Agent (Claude-3.5-Flash)
**Performance Testing**
- Read: Historical data, strategy configs, model outputs
- Write: Backtest database, performance reports
- No access: Live trading, data collection, system config

### Evaluation Agent (Claude-3.5-Flash)  
**Performance Analysis**
- Read: All performance data, trade results, model outputs
- Write: Evaluation reports, risk analysis
- No access: Strategy generation, trade execution, data collection

### API Agent (Claude-3.5-Flash)
**External Connectivity**
- Read: API configurations, data requests from other agents
- Write: Service layer integration, external data cache
- No access: Databases (except through data agent), strategy logic

### GetStockData Agent (Claude-3.5-Flash)
**Specialized Data Retrieval**  
- Read: Stock data configs, API settings, data requests
- Write: Stock data cache, market database (stock data only)
- Limited database write access for stock data updates

## Security Principles

### 1. Principle of Least Privilege
Each agent has only the minimum access required for its functions.

### 2. Separation of Concerns
- Strategy agents don't execute trades
- Data agents don't make strategy decisions  
- Trade agents don't collect raw data

### 3. Data Integrity Protection
- Only Data Agent has full database write access
- Other agents have limited write access to specific data types
- Orchestrator maintains system-wide read access for monitoring

### 4. Communication Control
All inter-agent communication flows through shared communication channels managed by the Orchestrator.

## Implementation Notes

### Folder Permissions
- Each agent should have a dedicated service account
- File system permissions should enforce the access matrix
- Shared directories require careful permission management

### API Security
- API credentials managed centrally by API Agent
- No agent stores credentials locally
- All external API access routed through API Agent

### Database Security  
- Database connections managed by Data Agent
- Other agents access data through service interfaces
- Write access to specific tables/collections only

### Monitoring and Auditing
- All file access logged by Orchestrator
- Permission violations trigger alerts
- Regular access reviews and updates