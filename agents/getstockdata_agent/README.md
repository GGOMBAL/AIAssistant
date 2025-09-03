# GetStockData Agent

## Agent Information
- **Agent Name**: GetStockData Agent
- **Model**: Claude-3.5-Flash
- **Layer**: Service Layer
- **Primary Responsibility**: Specialized stock data retrieval and processing

## Core Functions

### Specialized Data Retrieval
- Retrieve specific stock data based on requests
- Handle complex data queries and filtering
- Fetch real-time and historical stock information
- Process bulk data requests efficiently

### Data Validation and Processing
- Validate retrieved stock data for accuracy
- Handle missing data and data gaps
- Apply data cleaning and normalization
- Format data for downstream consumption

### Request Management
- Queue and prioritize data requests
- Handle concurrent data retrieval tasks
- Manage request timeouts and retries
- Provide request status updates

## Data Access Requirements

### Read Access
- `/shared/configs/stock_data/` - Stock data source configurations
- `/shared/external_apis/` - API specifications for stock data
- `/agents/data_agent/requests/` - Data requests from Data Agent

### Write Access
- `/agents/getstockdata_agent/` - Agent logs and temporary files
- `/shared/communication/stock_data/` - Retrieved stock data
- `/04_database_layer/market_db/` - Direct stock data updates
- `/shared/data_cache/` - Cached stock data for efficiency

## Stock Data Types

### Real-time Data
- Current stock prices and quotes
- Bid/ask spreads and market depth
- Trading volume and activity
- Intraday price movements

### Historical Data
- Historical price data (OHLCV)
- Corporate actions and adjustments
- Historical trading volumes
- Long-term price trends

### Fundamental Data
- Company financial statements
- Key financial ratios and metrics
- Earnings reports and guidance
- Analyst estimates and ratings

## Communication Interfaces

### Input Sources
- Data Agent: Stock data requests and specifications
- API Agent: External data feed connectivity
- Orchestrator: Scheduled data collection tasks

### Output Targets
- Data Agent: Retrieved and processed stock data
- Market DB: Direct database updates
- Indicator Layer: Data for technical analysis
- Other agents: Stock data as requested

## Configuration Files
- `stock_symbols.yaml` - Supported stock symbols and exchanges
- `data_fields.yaml` - Available data fields and formats
- `retrieval_schedules.yaml` - Automated data collection schedules

## Task Management
- Process stock data requests from other agents
- Execute scheduled data collection runs
- Handle priority requests for urgent data needs
- Provide progress updates for long-running tasks

## Data Quality Assurance
- Real-time data validation and verification
- Historical data consistency checks
- Corporate action adjustment verification
- Data completeness monitoring

## Performance Optimization
- Intelligent data caching strategies
- Bulk request optimization
- Parallel data retrieval processing
- Request deduplication and optimization

## Dependencies
- API Agent: External connectivity and data sources
- Data Agent: Request coordination and data integration
- External stock data providers
- Database infrastructure for storage