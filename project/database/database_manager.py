"""
Database Manager - Data Agent Management
Main interface for all database operations
Coordinates MongoDB operations, US market data, and historical data management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .mongodb_operations import MongoDBOperations
from .database_name_calculator import DatabaseNameCalculator
from .us_market_manager import USMarketDataManager
from .historical_data_manager import HistoricalDataManager

# Setup logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Main Database Manager coordinating all database operations
    Data Agent has exclusive management of this class
    """
    
    def __init__(self):
        """Initialize Database Manager with all sub-components"""
        self.mongodb_ops = MongoDBOperations()
        self.name_calculator = DatabaseNameCalculator()
        self.historical_manager = HistoricalDataManager()
        
        # US market managers (can be extended for other markets)
        self.us_market_managers = {}
        
        logger.info("Initialized DatabaseManager with all sub-components")
    
    def get_us_market_manager(self, market: str) -> USMarketDataManager:
        """
        Get or create US market manager for specific market
        
        Args:
            market: Market identifier (NYS, NAS, AMX)
            
        Returns:
            USMarketDataManager: Market manager instance
        """
        if market not in self.us_market_managers:
            self.us_market_managers[market] = USMarketDataManager('US', market)
            logger.info(f"Created US market manager for {market}")
        
        return self.us_market_managers[market]
    
    def initialize_market_data(self, area: str, market: str, data_types: List[str] = None) -> Dict[str, bool]:
        """
        Initialize market data for specific area and market
        
        Args:
            area: Area identifier (US, KR, VT, HK)
            market: Market identifier
            data_types: List of data types to initialize (Stock, ETF)
            
        Returns:
            dict: Initialization results
        """
        results = {}
        
        try:
            if area == 'US':
                market_manager = self.get_us_market_manager(market)
                
                if not data_types:
                    data_types = ['Stock', 'ETF']
                
                for data_type in data_types:
                    try:
                        if data_type == 'Stock':
                            success = market_manager.make_mongodb_us_stock()
                            results[f'{market}_Stock'] = success
                        elif data_type == 'ETF':
                            success = market_manager.make_mongodb_us_etf()
                            results[f'{market}_ETF'] = success
                    except Exception as e:
                        logger.error(f"Error initializing {data_type} data for {market}: {e}")
                        results[f'{market}_{data_type}'] = False
                        
            else:
                logger.warning(f"Market data initialization not yet implemented for area: {area}")
                results[f'{area}_{market}'] = False
                
        except Exception as e:
            logger.error(f"Error in initialize_market_data for {area} {market}: {e}")
            results['error'] = str(e)
        
        return results
    
    def store_account_data(self, mode: str, account_data: Dict[str, Any]) -> bool:
        """
        Store account data using historical data manager
        
        Args:
            mode: Account mode identifier
            account_data: Account data with Date field
            
        Returns:
            bool: Success status
        """
        try:
            return self.historical_manager.make_mongodb_account(mode, account_data)
        except Exception as e:
            logger.error(f"Error storing account data for {mode}: {e}")
            return False
    
    def store_trade_data(self, mode: str, trade_data: Dict[str, Any]) -> bool:
        """
        Store trading data using historical data manager
        
        Args:
            mode: Trading mode identifier
            trade_data: Trading data with Date field
            
        Returns:
            bool: Success status
        """
        try:
            return self.historical_manager.make_mongodb_trade(mode, trade_data)
        except Exception as e:
            logger.error(f"Error storing trade data for {mode}: {e}")
            return False
    
    def get_database_name(self, market: str, area: str, p_code: str, 
                         security_type: str = 'Stock') -> str:
        """
        Get database name using name calculator
        
        Args:
            market: Market identifier
            area: Area identifier
            p_code: Data type code
            security_type: Security type (Stock/ETF)
            
        Returns:
            str: Database name
        """
        return self.name_calculator.get_database_name(market, area, p_code, security_type)
    
    def get_universe_list(self, market: str, area: str, security_type: str, 
                         listing: bool = True) -> List[str]:
        """
        Get universe list using name calculator
        
        Args:
            market: Market identifier
            area: Area identifier
            security_type: Security type (Stock/ETF)
            listing: Active listings (True) or delisted (False)
            
        Returns:
            List[str]: List of symbols
        """
        return self.name_calculator.get_universe_list(market, area, security_type, listing)
    
    def execute_database_query(self, db_name: str, collection_name: str, 
                              query: Dict = None, limit: int = None) -> Any:
        """
        Execute database query using MongoDB operations
        
        Args:
            db_name: Database name
            collection_name: Collection name
            query: Query filter
            limit: Result limit
            
        Returns:
            pandas.DataFrame: Query results
        """
        return self.mongodb_ops.execute_query(db_name, collection_name, query, None, limit)
    
    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test all database connections
        
        Returns:
            dict: Connection test results for all components
        """
        results = {}
        
        try:
            # Test main MongoDB connection
            results['mongodb_operations'] = self.mongodb_ops.test_connection()
            
            # Test historical data connections
            historical_summary = self.historical_manager.get_database_summary()
            results['historical_data'] = historical_summary.get('connection_status', {})
            
            # Test US market connections (if any exist)
            results['us_markets'] = {}
            for market, manager in self.us_market_managers.items():
                market_status = manager.get_market_status()
                results['us_markets'][market] = {
                    'status': 'connected',
                    'stock_count': market_status['stock_count'],
                    'etf_count': market_status['etf_count']
                }
            
            # Overall status
            all_connected = all(
                conn.get('connected', False) if isinstance(conn, dict) else True
                for conn in results.values()
            )
            
            results['overall_status'] = 'connected' if all_connected else 'partial_connection'
            
        except Exception as e:
            logger.error(f"Error testing connections: {e}")
            results['error'] = str(e)
            results['overall_status'] = 'failed'
        
        return results
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        
        Returns:
            dict: Database statistics across all components
        """
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'mongodb_operations': self.mongodb_ops.get_summary(),
                'name_calculator': self.name_calculator.get_summary(),
                'historical_manager': self.historical_manager.get_database_summary(),
                'us_market_managers': {}
            }
            
            # Get US market statistics
            for market, manager in self.us_market_managers.items():
                stats['us_market_managers'][market] = manager.get_summary()
            
            # Connection tests
            stats['connection_tests'] = self.test_all_connections()
            
            logger.info("Generated comprehensive database statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating database statistics: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def validate_database_integrity(self, area: str = 'US', sample_size: int = 5) -> Dict[str, Any]:
        """
        Validate database integrity across markets
        
        Args:
            area: Area to validate (default US)
            sample_size: Number of collections to sample per database
            
        Returns:
            dict: Validation results
        """
        validation_results = {
            'area': area,
            'validation_timestamp': datetime.now().isoformat(),
            'databases_validated': 0,
            'total_errors': 0,
            'validation_details': {}
        }
        
        try:
            if area == 'US':
                markets = ['NYS', 'NAS', 'AMX']
                
                for market in markets:
                    try:
                        manager = self.get_us_market_manager(market)
                        
                        # Validate stock database
                        stock_db_name = self.get_database_name(market, area, 'D', 'Stock')
                        stock_validation = manager.validate_data_integrity(stock_db_name, sample_size)
                        
                        # Validate ETF database  
                        etf_db_name = self.get_database_name(market, area, 'D', 'ETF')
                        etf_validation = manager.validate_data_integrity(etf_db_name, sample_size)
                        
                        validation_results['validation_details'][market] = {
                            'stock_database': stock_validation,
                            'etf_database': etf_validation
                        }
                        
                        validation_results['databases_validated'] += 2
                        validation_results['total_errors'] += (
                            stock_validation.get('invalid_collections', 0) +
                            etf_validation.get('invalid_collections', 0)
                        )
                        
                    except Exception as market_error:
                        logger.error(f"Error validating {market}: {market_error}")
                        validation_results['validation_details'][market] = {
                            'error': str(market_error)
                        }
                        validation_results['total_errors'] += 1
            
            # Calculate overall success rate
            total_collections = sum(
                details.get('stock_database', {}).get('sampled_collections', 0) +
                details.get('etf_database', {}).get('sampled_collections', 0)
                for details in validation_results['validation_details'].values()
                if isinstance(details, dict) and 'error' not in details
            )
            
            if total_collections > 0:
                success_rate = ((total_collections - validation_results['total_errors']) / total_collections) * 100
                validation_results['overall_success_rate'] = round(success_rate, 2)
            else:
                validation_results['overall_success_rate'] = 0
            
        except Exception as e:
            logger.error(f"Error in database integrity validation: {e}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive Database Manager summary
        
        Returns:
            dict: Complete summary of all database components
        """
        return {
            'component': 'DatabaseManager',
            'sub_components': {
                'mongodb_operations': self.mongodb_ops.get_summary(),
                'name_calculator': self.name_calculator.get_summary(),
                'historical_manager': self.historical_manager.get_summary(),
                'us_market_managers_count': len(self.us_market_managers)
            },
            'supported_operations': [
                'initialize_market_data',
                'store_account_data',
                'store_trade_data',
                'get_database_name',
                'get_universe_list',
                'execute_database_query',
                'test_all_connections',
                'get_database_statistics',
                'validate_database_integrity'
            ],
            'data_agent_managed': True,
            'markets_supported': {
                'US': ['NYS', 'NAS', 'AMX'],
                'KR': ['NA'],
                'VT': ['HNX', 'HSX'],
                'HK': ['NA']
            }
        }