# DATABASE ARCHITECTURE & INTERFACE DOCUMENTATION

**Data Agent Exclusive Management**  
**Version**: 1.0  
**Last Updated**: 2025-09-12  
**Responsible Agent**: Data Agent  

---

## EXECUTIVE SUMMARY

The Database Layer provides comprehensive MongoDB operations and data management for the AI Assistant trading system. This layer is exclusively managed by the **Data Agent** and serves as the central data persistence and retrieval system for all trading operations, market data, and historical records.

### Key Features:
- **MongoDB Integration**: Complete MongoDB operations with connection management
- **Multi-Market Support**: US (NYS, NAS, AMX), KR, VT (HNX, HSX), HK markets
- **Historical Data Management**: Account and trading history tracking
- **Database Name Calculation**: Dynamic database naming based on market/area/type
- **Data Integrity Validation**: Comprehensive data validation and integrity checks
- **Error Handling**: Robust error management and logging

---

## ARCHITECTURE OVERVIEW

### Layer Structure
```
Project/database/
├── __init__.py
├── database_manager.py              # Main interface - coordinates all operations
├── mongodb_operations.py            # Core MongoDB operations
├── database_name_calculator.py      # Database naming and universe management  
├── us_market_manager.py            # US market-specific operations
└── historical_data_manager.py      # Account and trading history management
```

### Component Relationships
```
                    ┌─────────────────────────┐
                    │    Database Manager     │
                    │   (Main Interface)      │
                    └────────┬────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
     ┌────▼────┐     ┌──────▼──────┐     ┌────▼────┐
     │MongoDB  │     │  US Market  │     │Historical│
     │Operations│     │   Manager   │     │Data Mgr │
     └────┬────┘     └──────┬──────┘     └────┬────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                   ┌────────▼────────┐
                   │ Database Name   │
                   │   Calculator    │
                   └─────────────────┘
```

---

## COMPONENT SPECIFICATIONS

### 1. Database Manager (`database_manager.py`)

**Purpose**: Main interface coordinating all database operations

**Key Methods**:
```python
class DatabaseManager:
    def __init__(self)
    def get_us_market_manager(market: str) -> USMarketDataManager
    def initialize_market_data(area: str, market: str, data_types: List[str]) -> Dict[str, bool]
    def store_account_data(mode: str, account_data: Dict) -> bool
    def store_trade_data(mode: str, trade_data: Dict) -> bool
    def get_database_name(market: str, area: str, p_code: str, security_type: str) -> str
    def get_universe_list(market: str, area: str, security_type: str, listing: bool) -> List[str]
    def execute_database_query(db_name: str, collection_name: str, query: Dict, limit: int) -> DataFrame
    def test_all_connections() -> Dict[str, Any]
    def get_database_statistics() -> Dict[str, Any]
    def validate_database_integrity(area: str, sample_size: int) -> Dict[str, Any]
    def get_summary() -> Dict[str, Any]
```

**Usage Example**:
```python
# Initialize Database Manager
db_manager = DatabaseManager()

# Initialize US market data
results = db_manager.initialize_market_data('US', 'NAS', ['Stock', 'ETF'])

# Store account data
account_data = {'Date': datetime.now(), 'balance': 10000, 'positions': []}
success = db_manager.store_account_data('PAPER_TRADING', account_data)

# Query database
df = db_manager.execute_database_query('NasDataBase_D', 'AAPL', {'Date': {'$gte': datetime(2024, 1, 1)}})
```

### 2. MongoDB Operations (`mongodb_operations.py`)

**Purpose**: Core MongoDB connectivity and operations

**Key Methods**:
```python
class MongoDBOperations:
    def __init__(db_address: str = "MONGODB_LOCAL")
    def make_stock_db(db_name: str, df_data: dict, stock: str) -> bool
    def update_stock_db(db_name: str, df_data: dict, stock: str) -> bool
    def execute_query(db_name: str, collection_name: str, query: dict, projection: dict, limit: int) -> DataFrame
    def get_latest_data(db_name: str, collection_name: str, date_field: str) -> dict
    def check_data_exists(db_name: str, collection_name: str, query: dict) -> bool
    def get_collection_names(db_name: str) -> list
    def delete_collection(db_name: str, collection_name: str) -> bool
    def get_database_stats(db_name: str) -> dict
    def test_connection() -> dict
```

**Configuration Requirements**:
```yaml
# myStockInfo.yaml
MONGODB_LOCAL: "localhost"
MONGODB_NAS: "mongodb-server"
MONGODB_PORT: 27017
MONGODB_ID: "admin"
MONGODB_PW: "password"
```

### 3. Database Name Calculator (`database_name_calculator.py`)

**Purpose**: Calculate database names and manage universe lists

**Key Functions**:
```python
def calculate_database_name(market: str, area: str, p_code: str, type: str) -> str
def calculate_file_path(market: str, area: str, security_type: str) -> Tuple[str, str]
def calculate_universe_list(market: str, area: str, security_type: str, listing: bool) -> List[str]
def change_ticker_name(stock_code: str, area: str) -> str

class DatabaseNameCalculator:
    def get_database_name(market, area, p_code, security_type) -> str
    def get_file_paths(market, area, security_type) -> Tuple[str, str]
    def get_universe_list(market, area, security_type, listing) -> List[str]
    def transform_ticker_name(stock_code, area) -> str
```

**Database Naming Convention**:
```python
# US Markets
'NYS' + 'US' + 'D' + 'Stock' -> 'NysDataBase_D'
'NAS' + 'US' + 'W' + 'ETF' -> 'NasEtfDataBase_W'

# Korean Market
'NA' + 'KR' + 'D' + 'Stock' -> 'KrDataBase_D_ohlcv'

# Data Type Codes:
# M = Minute, D = Daily, AD = Adjusted Daily, W = Weekly
# RS = Relative Strength, F = Fundamental, E = Earnings, O = Options
```

### 4. US Market Manager (`us_market_manager.py`)

**Purpose**: US-specific market data operations

**Key Methods**:
```python
class USMarketDataManager:
    def __init__(area: str, market: str)
    def make_mongodb_us_etf(ohlcv: str) -> bool
    def make_mongodb_us_stock(ohlcv: str) -> bool
    def get_market_status() -> dict
    def validate_data_integrity(db_name: str, sample_size: int) -> dict
    def get_summary() -> dict
```

**Supported Markets**:
- **NYS**: New York Stock Exchange
- **NAS**: NASDAQ
- **AMX**: AMEX

### 5. Historical Data Manager (`historical_data_manager.py`)

**Purpose**: Account and trading history management

**Key Methods**:
```python
class HistoricalDataManager:
    def __init__(self)
    def make_mongodb_account(mode: str, account_dict: Dict) -> bool
    def make_mongodb_trade(mode: str, account_dict: Dict) -> bool
    def get_account_history(mode: str, start_date: datetime, end_date: datetime) -> DataFrame
    def get_trade_history(mode: str, start_date: datetime, end_date: datetime) -> DataFrame
    def get_latest_account_data(mode: str) -> Dict
    def get_latest_trade_data(mode: str) -> Dict
    def delete_account_data(mode: str, target_date: datetime) -> bool
    def get_database_summary() -> Dict
```

**Managed Databases**:
- `AccntDataBase`: Account balance and position data
- `AccntDataBase_Trade`: Trading transaction history

---

## DATA MODELS

### Market Data Structure
```python
# Stock/ETF OHLCV Data
{
    'symbol': 'AAPL',
    'date': datetime.utcnow(),
    'open': 150.00,
    'high': 152.50,
    'low': 149.00,
    'close': 151.25,
    'volume': 50000000,
    'adjusted_close': 151.25
}

# Weekly Data (aggregated from daily)
{
    'symbol': 'AAPL',
    'week_ending': datetime.utcnow(),
    'weekly_open': 148.00,
    'weekly_high': 155.00,
    'weekly_low': 147.50,
    'weekly_close': 151.25,
    'weekly_volume': 250000000
}
```

### Account Data Structure
```python
# Account Balance Data
{
    'Date': datetime.utcnow(),
    'account_type': 'PAPER_TRADING',
    'total_balance': 50000.00,
    'available_cash': 25000.00,
    'invested_amount': 25000.00,
    'positions': [
        {
            'symbol': 'AAPL',
            'quantity': 100,
            'avg_price': 150.00,
            'current_price': 151.25,
            'market_value': 15125.00
        }
    ],
    'daily_pnl': 125.00,
    'total_pnl': 1250.00
}

# Trading Transaction Data
{
    'Date': datetime.utcnow(),
    'account_type': 'PAPER_TRADING',
    'symbol': 'AAPL',
    'action': 'BUY',
    'quantity': 100,
    'price': 150.00,
    'total_amount': 15000.00,
    'fees': 1.00,
    'order_id': 'ORD_12345'
}
```

---

## API INTERFACES

### For Strategy Agent (Indicator Layer Integration)
```python
# Get processed market data for indicators
from Project.database.database_manager import DatabaseManager

db_manager = DatabaseManager()

# Get daily data for indicator calculations
daily_data = db_manager.execute_database_query(
    db_name='NasDataBase_D',
    collection_name='AAPL',
    query={'Date': {'$gte': datetime(2024, 1, 1)}},
    limit=200
)

# Get universe list for strategy processing  
stock_universe = db_manager.get_universe_list('NAS', 'US', 'Stock', True)
```

### For Service Agent (Trading Operations)
```python
# Store trading results and account updates
from Project.database.database_manager import DatabaseManager

db_manager = DatabaseManager()

# Store account data after trading
account_data = {
    'Date': datetime.now(),
    'total_balance': 52500.00,
    'positions': updated_positions
}
success = db_manager.store_account_data('LIVE_TRADING', account_data)

# Store trade execution
trade_data = {
    'Date': datetime.now(),
    'symbol': 'AAPL',
    'action': 'SELL',
    'quantity': 50,
    'price': 155.00
}
success = db_manager.store_trade_data('LIVE_TRADING', trade_data)
```

### For Helper Agent (Data Provider Integration)
```python
# Helper agents use database functions for data storage
from Project.database.mongodb_operations import MongoDBOperations

mongo_ops = MongoDBOperations()

# Store market data retrieved from APIs
market_data = {
    'Date': datetime.now(),
    'open': 150.0,
    'high': 152.0,
    'low': 149.0,
    'close': 151.0,
    'volume': 1000000
}
success = mongo_ops.make_stock_db('NasDataBase_D', market_data, 'AAPL')
```

---

## OPERATIONAL PROCEDURES

### Daily Operations
1. **Market Data Updates**:
   ```python
   # Initialize market data for the day
   db_manager = DatabaseManager()
   nas_manager = db_manager.get_us_market_manager('NAS')
   
   # Update stock data
   nas_manager.make_mongodb_us_stock('Y')
   
   # Update ETF data
   nas_manager.make_mongodb_us_etf('Y')
   ```

2. **Data Integrity Validation**:
   ```python
   # Validate database integrity
   validation_results = db_manager.validate_database_integrity('US', sample_size=10)
   
   if validation_results['overall_success_rate'] < 95:
       logger.warning("Data integrity issues detected")
   ```

### Weekly Operations
1. **Database Statistics Review**:
   ```python
   # Get comprehensive database statistics
   stats = db_manager.get_database_statistics()
   
   # Review connection health
   connection_tests = db_manager.test_all_connections()
   ```

2. **Historical Data Cleanup**:
   ```python
   # Clean up old temporary data (if needed)
   historical_manager = HistoricalDataManager()
   
   # Review account data for inconsistencies
   account_summary = historical_manager.get_database_summary()
   ```

---

## ERROR HANDLING & LOGGING

### Error Handling Patterns
```python
try:
    result = db_manager.initialize_market_data('US', 'NAS', ['Stock'])
    if not all(result.values()):
        logger.error(f"Market data initialization failed: {result}")
        # Implement fallback strategy
except Exception as e:
    logger.error(f"Database operation failed: {e}")
    # Implement recovery mechanism
```

### Logging Configuration
```python
import logging

# Database operations should use structured logging
logger = logging.getLogger(__name__)

# Log levels:
# INFO: Successful operations, routine status updates
# WARNING: Performance issues, minor data inconsistencies  
# ERROR: Failed operations, connection issues
# CRITICAL: Database corruption, complete system failures
```

---

## PERFORMANCE OPTIMIZATION

### Connection Management
- **Connection Pooling**: MongoDB connections are properly managed with timeout settings
- **Connection Testing**: Regular health checks prevent stale connections
- **Error Recovery**: Automatic reconnection on connection failures

### Query Optimization
- **Indexing Strategy**: Ensure proper indexing on Date fields and symbol fields
- **Query Limits**: Use limits to prevent large result sets from overwhelming memory
- **Projection**: Only fetch required fields to minimize data transfer

### Memory Management
```python
# Efficient data processing
def process_large_dataset(db_name, collection_name):
    mongo_ops = MongoDBOperations()
    
    # Process data in chunks to manage memory
    batch_size = 1000
    offset = 0
    
    while True:
        batch_data = mongo_ops.execute_query(
            db_name, collection_name, 
            query={}, 
            limit=batch_size
        )
        
        if batch_data.empty:
            break
            
        # Process batch
        process_batch(batch_data)
        offset += batch_size
```

---

## SECURITY CONSIDERATIONS

### Access Control
- **Data Agent Exclusive**: Only Data Agent can modify database implementations
- **Cross-Agent Access**: Other agents use defined interfaces only
- **Credential Management**: Database credentials managed through configuration files

### Data Protection
- **Connection Security**: Use secured MongoDB connections with authentication
- **Input Validation**: Validate all input data before database operations
- **Audit Logging**: Log all database modification operations

### Backup & Recovery
```python
# Database backup procedures (Data Agent responsibility)
def backup_database(db_name: str, backup_path: str) -> bool:
    try:
        mongo_ops = MongoDBOperations()
        # Implementation would use mongodump or similar
        logger.info(f"Database {db_name} backed up to {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Backup failed for {db_name}: {e}")
        return False
```

---

## TESTING STRATEGY

### Unit Tests
- **Component Testing**: Each database component has comprehensive unit tests
- **Mock Testing**: Database operations can be mocked for integration testing
- **Error Simulation**: Tests include error condition simulation

### Integration Tests
- **Cross-Component**: Tests verify interaction between database components
- **Agent Integration**: Tests verify proper usage by other agents
- **Performance Tests**: Load testing for high-volume operations

### Validation Tests
```python
# Example validation test
def test_database_integrity():
    db_manager = DatabaseManager()
    
    # Test connection
    connection_test = db_manager.test_all_connections()
    assert connection_test['overall_status'] == 'connected'
    
    # Test data integrity
    validation = db_manager.validate_database_integrity('US', 5)
    assert validation['overall_success_rate'] > 90
    
    # Test query operations
    result = db_manager.execute_database_query('NasDataBase_D', 'AAPL', {}, 10)
    assert isinstance(result, pd.DataFrame)
```

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] MongoDB server configured and accessible
- [ ] Database credentials properly set in myStockInfo.yaml
- [ ] Universe list files available and up-to-date
- [ ] All unit tests passing
- [ ] Integration tests with other layers passing

### Post-Deployment
- [ ] Connection tests successful
- [ ] Data integrity validation passed
- [ ] Market data initialization successful
- [ ] Historical data operations functional
- [ ] Logging and monitoring active

---

## TROUBLESHOOTING GUIDE

### Common Issues

**1. Connection Failures**
```
Symptoms: "Failed to connect to MongoDB"
Solutions:
- Verify MongoDB server is running
- Check network connectivity
- Validate credentials in myStockInfo.yaml
- Review firewall settings
```

**2. Data Integrity Issues**
```
Symptoms: validation_results['overall_success_rate'] < 90%
Solutions:
- Run detailed integrity check with larger sample size
- Check for corrupted collections
- Verify data format consistency
- Review recent data loading operations
```

**3. Performance Issues**
```
Symptoms: Slow query responses
Solutions:
- Check database indexes
- Monitor memory usage
- Review query complexity
- Consider connection pooling optimization
```

**4. Universe List Issues**
```
Symptoms: Empty stock/ETF lists
Solutions:
- Verify JSON files exist in correct paths
- Check file format and encoding
- Update universe list files from data providers
- Verify file permissions
```

---

## MAINTENANCE SCHEDULE

### Daily
- [ ] Monitor database connections
- [ ] Review error logs
- [ ] Check data integrity on critical collections

### Weekly  
- [ ] Comprehensive database statistics review
- [ ] Performance monitoring analysis
- [ ] Update universe lists if needed

### Monthly
- [ ] Full database integrity validation
- [ ] Backup verification
- [ ] Performance optimization review
- [ ] Security audit

---

## CONTACT & SUPPORT

**Responsible Agent**: Data Agent  
**Layer**: Database Layer  
**Priority**: P1 (Critical System Component)

**For Issues**:
- Database connectivity problems: Check MongoDB server status
- Data integrity issues: Run validation tools
- Performance problems: Review query optimization
- Access control issues: Verify agent permissions

**Documentation Updates**:
- Data Agent maintains this documentation
- Updates coordinated with architecture changes
- Version controlled with database implementations

---

*This documentation is maintained by the Data Agent and updated with each database layer modification.*