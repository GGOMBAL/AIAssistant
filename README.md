# AI Trading Assistant - Multi-Agent System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Anthropic Claude](https://img.shields.io/badge/AI-Claude-purple.svg)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A sophisticated multi-agent trading system powered by Claude AI, designed for automated trading strategy development, backtesting, and execution.

## 🏗️ System Architecture

This project implements a **4-agent architecture** that collaborates to provide comprehensive trading system functionality:

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│   Data Agent    │ Strategy Agent  │ Service Agent   │ Helper Agent    │
│ (Indicator)     │ (Strategy)      │ (Service)       │ (Service)       │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Data Gathering  │ Signal Gen.     │ Backtesting     │ Broker APIs     │
│ Tech Indicators │ Position Size   │ Trade Execution │ External Data   │
│ Market Scanner  │ Risk Mgmt       │ Database Mgmt   │ API Rate Limit  │
│ Data Validation │ Portfolio Opt   │ Risk Control    │ Webhooks        │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### Agent Collaboration Flow
```
Helper → Data → Strategy → Service
  ↓       ↓         ↓         ↓
외부API → 지표 → 신호생성 → 실행/DB
```

## 🤖 Agent Specifications

### 1. Data Agent (Indicator Layer)
**Role**: Data Gathering Service & Technical Indicator Management
- **Model**: Claude-3-Opus-20240229
- **Priority**: 1 (Critical)
- **Capabilities**: 
  - Data collection and validation
  - Technical indicator calculation
  - Market scanning and filtering
  - Data normalization and processing

**Managed Files** (Full R/W Access):
- `Project/indicator/technical_indicators.py`
- `Project/indicator/fundamental_indicators.py`
- `Project/indicator/market_scanner.py`
- `Project/service/data_gathering_service.py`
- `Project/service/data_processor.py`

**Helper Functions Access**: 👀 **READ-ONLY** - Can call Helper functions but cannot modify

### 2. Strategy Agent (Strategy Layer)
**Role**: Trading Strategy Development & Signal Generation
- **Model**: Claude-3-Opus-20240229  
- **Priority**: 1 (Critical)
- **Capabilities**:
  - Trading signal generation
  - Position sizing optimization
  - Risk management rules
  - Portfolio optimization

**Managed Files** (Full R/W Access):
- `Project/strategy/signal_generator.py`
- `Project/strategy/position_sizing.py`
- `Project/strategy/risk_management.py`
- `Project/strategy/portfolio_optimizer.py`

**Helper Functions Access**: 👀 **READ-ONLY** - Can call Helper functions but cannot modify

### 3. Service Agent (Service Layer)
**Role**: Backtesting, Trading Execution & Database Management
- **Model**: Claude-3-5-Sonnet-20241022
- **Priority**: 2 (High)
- **Capabilities**:
  - Strategy backtesting and simulation
  - Trade execution and position management
  - Database operations and backup
  - Risk control systems

**Managed Files** (Full R/W Access):
- `Project/service/backtester.py`
- `Project/service/trade_executor.py`
- `Project/service/position_manager.py`
- `Project/database/market_db.py`
- `Project/database/trade_db.py`

**Helper Functions Access**: 👀 **READ-ONLY** - Can call Helper functions but cannot modify

### 4. Helper Agent (Service Layer) 🔒
**Role**: External API Management & Broker Connections (**EXCLUSIVE CONTROL**)
- **Model**: Claude-3-5-Sonnet-20241022
- **Priority**: 2 (High)
- **Access Control**: **EXCLUSIVE** - Only Helper Agent can modify Helper files
- **Capabilities**:
  - Broker API integration (KIS, YFinance, Alpha Vantage)
  - External data provider APIs
  - Telegram notification system
  - API credential management
  - Function testing and validation

**Exclusively Managed Files** (Full R/W Access):
- `Project/Helper/broker_api_connector.py` 🔒
- `Project/Helper/kis_api_helper_us.py` 🔒
- `Project/Helper/kis_common.py` 🔒
- `Project/Helper/yfinance_helper.py` 🔒
- `Project/Helper/data_provider_api.py` 🔒
- `Project/Helper/telegram_messenger.py` 🔒
- `HELPER_FUNCTIONS_MANUAL.md` 🔒
- `myStockInfo.yaml` 🔒 (API Credentials)
- `Test/**/*helper*`, `Test/**/*precision*`, `Test/**/*comparison*` 🔒

**Other Agents**: **READ-ONLY** access to Helper functions through defined interfaces

## 🛡️ Access Control & Permissions

### Helper Agent Exclusive Control 🔒
The **Helper Agent** has **EXCLUSIVE** control over all Helper layer files and API integrations:

- ✅ **ONLY Helper Agent** can modify Helper files
- ✅ **ONLY Helper Agent** can manage API credentials (`myStockInfo.yaml`)
- ✅ **ONLY Helper Agent** can update Helper tests and documentation
- 👀 **Other Agents** have **READ-ONLY** access through defined interfaces

### Permission Matrix
| Resource | Helper Agent | Other Agents |
|----------|--------------|--------------|
| Helper Files (`Project/Helper/**/*.py`) | 🟢 Full R/W | 👀 Read-Only |
| API Credentials (`myStockInfo.yaml`) | 🟢 Full R/W | 👀 Function Access Only |
| Helper Documentation | 🟢 Full R/W | 👀 Read-Only |
| Helper Tests | 🟢 Full R/W | 🚫 No Access |

### Security Rules
- 🔒 API keys only accessible through Helper functions
- 🔒 No direct modification of Helper code by other agents
- 🔒 All Helper changes must go through Helper Agent
- 🔒 Cross-agent integration through defined interfaces only

**For detailed access control information, see:**
- [`AGENT_PERMISSIONS.yaml`](AGENT_PERMISSIONS.yaml)
- [`Project/Helper/HELPER_AGENT_ACCESS_CONTROL.md`](Project/Helper/HELPER_AGENT_ACCESS_CONTROL.md)

## 🔧 Core Components

### Management System
- **`management/agent_management_system.py`**: Central management and validation system
- **`shared/multi_agent_system.py`**: Agent initialization and collaboration framework
- **`shared/claude_client.py`**: Claude API client with agent-specific configurations

### Orchestration
- **`orchestrator/main_orchestrator.py`**: Main workflow coordinator
- **`orchestrator/agent_scheduler.py`**: Task scheduling and execution management
- **`orchestrator/multi_agent_orchestrator.py`**: Inter-agent communication system

### Configuration
- **`config/agent_interfaces.yaml`**: Agent interface definitions and collaborations
- **`config/collaboration_matrix.yaml`**: Detailed collaboration relationships
- **`config/file_ownership.yaml`**: File ownership and permission management

## 🚀 Getting Started

### Prerequisites
```bash
pip install anthropic
pip install pyyaml
pip install asyncio
```

### Environment Setup
```bash
export ANTHROPIC_API_KEY="your-claude-api-key"
```

### Basic Usage

#### 1. Initialize the System
```python
from orchestrator.main_orchestrator import MainOrchestrator

orchestrator = MainOrchestrator(api_key="your-api-key")
```

#### 2. Execute Trading Workflow
```python
await orchestrator.execute_workflow("daily_trading", {
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "timeframe": "1d",
    "mode": "paper"
})
```

#### 3. Run Backtesting
```python
await orchestrator.execute_workflow("backtest", {
    "symbols": ["AAPL"],
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "strategy": "mean_reversion"
})
```

#### 4. Management Interface
```python
from management.agent_management_system import AgentManagementCLI

cli = AgentManagementCLI()
cli.interactive_menu()  # Launch interactive management
```

## 📊 Workflow Types

### 1. Daily Trading Workflow
- Data collection from external sources
- Technical indicator calculation
- Signal generation and position sizing
- Trade execution (paper/live)

### 2. Backtesting Workflow
- Historical data loading
- Strategy simulation
- Performance analysis and metrics

### 3. Data Update Workflow
- Multi-source data aggregation
- Data consolidation and validation
- Database updates

## 🛠️ Technical Features

### Multi-Agent Communication
- Asynchronous message passing
- Topic-based publish/subscribe
- Dependency-aware task scheduling

### API Management
- Rate limiting (30 requests/min, 1000/day)
- Priority-based execution
- Model-specific agent assignment

### Configuration Management
- YAML-based configuration
- Hot-reload capability
- Validation and consistency checks

### Execution Modes
- **BATCH**: Sequential execution with dependencies
- **PARALLEL**: Concurrent execution
- **ROUND_ROBIN**: Load balancing across agents

## 📁 Project Structure

```
AIAssistant/
├── agents/                    # Agent-specific documentation
│   ├── data_agent/
│   ├── strategy_agent/
│   ├── service_agent/
│   └── helper_agent/
├── config/                    # Configuration files
│   ├── agent_interfaces.yaml
│   ├── collaboration_matrix.yaml
│   └── file_ownership.yaml
├── management/                # System management
│   └── agent_management_system.py
├── orchestrator/             # Workflow orchestration
│   ├── main_orchestrator.py
│   ├── agent_scheduler.py
│   └── multi_agent_orchestrator.py
├── shared/                   # Shared utilities
│   ├── claude_client.py
│   ├── multi_agent_system.py
│   └── api_manager.py
└── Project/                  # Implementation files
    ├── Helper/               # Helper Agent services
    ├── indicator/            # Data Agent indicators
    ├── strategy/             # Strategy Agent strategies
    ├── service/              # Service Agent services
    └── database/             # Service Agent database
```

## 🔍 System Monitoring

### Real-time Status
```python
status = orchestrator.get_system_status()
print(json.dumps(status, indent=2))
```

### Agent Validation
```python
from management.agent_management_system import AgentManagementSystem

mgmt = AgentManagementSystem()
validation = mgmt.validate_agent_setup("data_agent")
```

## 🚦 Current Status

✅ **Completed**:
- 4-agent architecture design
- Configuration system setup
- Agent management framework
- Orchestration system
- Documentation structure

🔄 **In Progress**:
- Project folder structure creation
- Individual agent implementation
- Interface layer development

📋 **Planned**:
- UI/Reporting layer
- Live trading integration
- Performance optimization
- Extended backtesting features

## 🤝 Contributing

1. Follow the established agent architecture
2. Maintain configuration consistency
3. Update documentation for new features
4. Test agent interactions thoroughly

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Project Configuration Guide](./config/README.md)
- [Agent Development Guide](./agents/README.md)

---

*Last Updated: 2025-09-11*
*Architecture Version: 4-Agent Enhanced Management System*