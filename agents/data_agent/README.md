# Data Agent

## Agent Information
- **Agent Name**: Data Agent
- **Model**: Claude Opus
- **Layer**: Service Layer / Database Layer
- **Primary Responsibility**: Data collection, processing, and management across all timeframes

## Core Functions

### Data Collection
- Gather market data from multiple sources
- Collect fundamental data for analysis
- Retrieve ETF and cryptocurrency data
- Coordinate with GetStockData Agent for specific requests

### Data Processing
- Clean and normalize incoming data
- Handle data validation and quality checks
- Process different timeframes (daily, weekly, monthly, minute)
- Transform raw data into usable formats

### Database Management
- Maintain Market DB with current and historical data
- Ensure data consistency and integrity
- Manage data storage optimization
- Handle database backup and recovery

## Data Access Requirements

### Read Access
- `../../shared/configs/data_sources/` - Data source configurations
- `../../shared/external_apis/` - External data feed settings
- `../../Project/database/` - All database access for reading

### Write Access
- `./` - Agent-specific processing logs
- `../../Project/database/market_db/` - Market data storage
- `../../Project/service/data_gathering/` - Data pipeline management
- `../../Project/indicator/` - Processed data for indicators
- `../../shared/communication/data_updates/` - Data availability notifications

## Data Types Managed

### Market Data
- Stock prices (OHLCV) across all timeframes
- Volume and trading statistics
- Corporate actions and dividends
- Market indices and benchmarks

### Alternative Data
- ETF holdings and performance
- Cryptocurrency prices and metrics
- Economic indicators
- News sentiment data

### Fundamental Data
- Financial statements
- Company metrics and ratios
- Analyst ratings and estimates
- Sector and industry classifications

## Communication Interfaces

### Input Sources
- External Scheduler: Data update triggers
- GetStockData Agent: Specific data requests
- API Agent: External data feeds
- AlphaVantage and other APIs

### Output Targets
- All Indicator Layer components
- Strategy and Analysis services
- Reporting Layer for data summaries
- Other agents requiring market data

## Configuration Files
- `data_sources.yaml` - External data source configurations
- `update_schedules.yaml` - Data refresh timing and frequency
- `data_quality.yaml` - Validation rules and quality checks

## Task Management
- Execute scheduled data updates
- Handle ad-hoc data requests from other agents
- Monitor data feed health and connectivity
- Perform data quality audits and corrections

## Data Quality Assurance
- Real-time data validation
- Historical data consistency checks
- Missing data detection and interpolation
- Data anomaly identification and flagging

## Dependencies
- GetStockData Agent: Specialized data retrieval
- API Agent: External connectivity
- External data providers: AlphaVantage, etc.
- Database infrastructure