# AIAgentProject - Complete Folder Structure

## Full Directory Tree
```
AIAgentProject/
│
├── Project/                               # Core Project Layers
│   ├── indicator/                         # Technical & Fundamental Indicators
│   │   ├── fundamental_data/
│   │   ├── relative_strength/
│   │   ├── monthly_indicators/
│   │   ├── weekly_indicators/
│   │   ├── daily_indicators/
│   │   ├── etf_indicators/
│   │   └── btc_indicators/
│   │
│   ├── strategy/                          # Strategy Logic & Signal Generation
│   │   ├── signals/
│   │   ├── positions/
│   │   ├── model_signals/
│   │   └── strategy_configs/
│   │
│   ├── service/                           # Core Services & Processing
│   │   ├── data_gathering/
│   │   ├── minute_data_indicator/
│   │   ├── analysis_service/
│   │   ├── benchmark_service/
│   │   ├── audit_trade_service/
│   │   ├── btc_signal_service/
│   │   └── api_integration/
│   │
│   ├── database/                          # Data Storage & Management
│   │   ├── market_db/
│   │   ├── backtest_db/
│   │   └── trade_db/
│   │
│   ├── reporting/                         # Analysis & Reporting
│   │   ├── cap_analysis/
│   │   ├── risk_analysis/
│   │   ├── balance_analysis/
│   │   ├── evaluation_reports/
│   │   ├── backtest_reports/
│   │   └── generated_reports/
│   │
│   └── ui/                                # User Interfaces
│       ├── web_service/
│       ├── trading_service/
│       └── dashboards/
│
├── agents/                                # Individual Agent Implementations
│   ├── strategy_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   └── tasks/
│   │
│   ├── trade_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   └── tasks/
│   │
│   ├── data_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   ├── requests/
│   │   └── tasks/
│   │
│   ├── model_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   └── tasks/
│   │
│   ├── backtest_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   └── tasks/
│   │
│   ├── evaluation_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   └── tasks/
│   │
│   ├── api_agent/
│   │   ├── README.md
│   │   ├── configs/
│   │   ├── logs/
│   │   └── tasks/
│   │
│   └── getstockdata_agent/
│       ├── README.md
│       ├── configs/
│       ├── logs/
│       └── tasks/
│
├── orchestrator/                          # Main Orchestrator Agent
│   ├── README.md
│   ├── task_management/
│   ├── workflow_templates/
│   ├── system_health/
│   └── logs/
│
├── shared/                                # Shared Resources
│   ├── communication/
│   │   ├── strategy_outputs/
│   │   ├── trade_updates/
│   │   ├── data_updates/
│   │   ├── predictions/
│   │   ├── backtest_results/
│   │   ├── evaluations/
│   │   ├── api_data/
│   │   └── stock_data/
│   │
│   ├── configs/
│   │   ├── data_sources/
│   │   ├── trading/
│   │   ├── backtest/
│   │   ├── models/
│   │   ├── api_settings/
│   │   └── stock_data/
│   │
│   ├── models/
│   │   ├── trained_models/
│   │   ├── model_metadata/
│   │   └── predictions/
│   │
│   ├── external_apis/
│   │   ├── alphavantage/
│   │   ├── broker_apis/
│   │   └── data_feeds/
│   │
│   ├── data_cache/
│   │   ├── market_data/
│   │   ├── stock_data/
│   │   └── api_responses/
│   │
│   └── tasks/
│       ├── active_tasks/
│       ├── completed_tasks/
│       └── task_templates/
│
├── config/                                # System Configuration
│   ├── access_control.md
│   ├── system_config.yaml
│   ├── security_settings.yaml
│   └── deployment_config.yaml
│
└── docs/                                  # System Documentation
    ├── folder_structure.md
    ├── architecture_diagram.png
    ├── agent_interactions.md
    ├── workflow_documentation.md
    └── api_documentation.md

README.md                                  # Main project documentation
```

## Layer Descriptions

### Project/indicator/
Contains all technical and fundamental indicators that process raw market data into analytical insights.

### Project/strategy/  
Houses strategy logic, signal generation algorithms, and position sizing calculations.

### Project/service/
Core system services including data processing, analysis services, and external integrations.

### Project/database/
Data storage systems for market data, backtesting results, and trading records.

### Project/reporting/
Analysis and reporting components for performance evaluation and risk assessment.

### Project/ui/
User interface components including web services and trading dashboards.

## Agent Organization

Each agent maintains:
- **README.md**: Agent documentation and specifications
- **configs/**: Agent-specific configuration files  
- **logs/**: Agent execution and error logs
- **tasks/**: Active and completed task files

## Shared Resources

### ./shared/communication/
Inter-agent communication channels organized by data type and source agent.

### ./shared/configs/
Centralized configuration management for cross-agent settings.

### ./shared/models/
Machine learning model storage and management.

### ./shared/tasks/
Task management system for orchestrator-agent coordination.

## Security Considerations

- Agent directories have restricted access based on access control matrix
- Shared resources implement read/write permissions per agent requirements
- Configuration files separated by security level and agent access needs
- Logs maintained separately for each agent to support debugging and auditing