"""
US Market Data Manager - Data Agent Management
Based on refer/Database/MakMongoDB_US.py
Manages US market data collection and MongoDB operations
"""

import pymongo
import pandas as pd
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pytz
import yaml
import os
from pathlib import Path

from .mongodb_operations import MongoDBOperations
from .database_name_calculator import (
    calculate_file_path, 
    calculate_universe_list, 
    calculate_database_name,
    change_ticker_name
)

# Setup logging
logger = logging.getLogger(__name__)

class USMarketDataManager:
    """
    US Market Data Manager for MongoDB operations
    Based on refer/Database/MakMongoDB_US.py ColMongoUsDB class
    Data Agent has exclusive management of this class
    """
    
    def __init__(self, area: str, market: str):
        """
        Initialize US Market Data Manager
        
        Args:
            area: Area identifier (should be 'US')
            market: Market identifier (NYS, NAS, AMX)
        """
        self.area = area
        self.market = market
        
        # Load configuration
        self._load_config()
        
        # Set timezone
        self.end_day = datetime.now(pytz.utc)
        self.start_day = (datetime.now(pytz.utc) - timedelta(days=365*30))
        
        # Initialize file paths
        self._initialize_paths()
        
        # Load stock and ETF lists
        self._load_universe_lists()
        
        # Initialize latest dates (would normally get from Alpha Vantage)
        self._initialize_latest_dates()
        
        logger.info(f"Initialized USMarketDataManager for {area} {market}")
    
    def _load_config(self):
        """Load database configuration"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, 'myStockInfo.yaml')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='UTF-8') as f:
                    self.stock_info = yaml.load(f, Loader=yaml.FullLoader)
            else:
                # Default configuration
                self.stock_info = {
                    "MONGODB_LOCAL": "localhost",
                    "MONGODB_PORT": 27017,
                    "MONGODB_ID": "admin",
                    "MONGODB_PW": "password"
                }
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.stock_info = {
                "MONGODB_LOCAL": "localhost",
                "MONGODB_PORT": 27017,
                "MONGODB_ID": "admin", 
                "MONGODB_PW": "password"
            }
    
    def _initialize_paths(self):
        """Initialize file paths for stock and ETF lists"""
        try:
            # JSON file paths
            self.stock_list_file_path, self.stock_delist_file_path = calculate_file_path(
                self.market, self.area, 'Stock'
            )
            self.etf_list_file_path, self.etf_delist_file_path = calculate_file_path(
                self.market, self.area, 'ETF'
            )
            
            logger.info("Initialized file paths for stock and ETF lists")
            
        except Exception as e:
            logger.error(f"Error initializing paths: {e}")
            self.stock_list_file_path = None
            self.stock_delist_file_path = None
            self.etf_list_file_path = None
            self.etf_delist_file_path = None
    
    def _load_universe_lists(self):
        """Load stock and ETF universe lists"""
        try:
            # Stock lists
            self.stock_list_us = calculate_universe_list(self.market, self.area, 'Stock', True)
            self.delete_stock_list = calculate_universe_list(self.market, self.area, 'Stock', False)
            
            # Load manual delete list if available
            try:
                if self.stock_delist_file_path and os.path.exists(self.stock_delist_file_path):
                    with open(self.stock_delist_file_path, 'r') as json_file:
                        delete_stock_list_manual = json.load(json_file)
                else:
                    delete_stock_list_manual = []
            except:
                delete_stock_list_manual = []
            
            # Combine delete lists (union)
            self.delete_stock_list = list(set(self.delete_stock_list) | set(delete_stock_list_manual))
            
            # ETF lists
            self.etf_list_us = calculate_universe_list(self.market, self.area, 'ETF', True)
            self.delete_etf_list = calculate_universe_list(self.market, self.area, 'ETF', False)
            
            logger.info(f"Loaded {len(self.stock_list_us)} stocks and {len(self.etf_list_us)} ETFs")
            
        except Exception as e:
            logger.error(f"Error loading universe lists: {e}")
            self.stock_list_us = []
            self.delete_stock_list = []
            self.etf_list_us = []
            self.delete_etf_list = []
    
    def _initialize_latest_dates(self):
        """Initialize latest data dates (simulated)"""
        try:
            # In the original, this gets data from Alpha Vantage
            # For now, we'll use current date - 1 day as latest
            today = datetime.now(pytz.utc)
            
            self.latest_d = (today - timedelta(days=1)).date()
            self.latest_w = (today - timedelta(days=7)).date()
            
            logger.info(f"Set latest dates: D={self.latest_d}, W={self.latest_w}")
            
        except Exception as e:
            logger.error(f"Error initializing latest dates: {e}")
            self.latest_d = datetime.now(pytz.utc).date()
            self.latest_w = datetime.now(pytz.utc).date()
    
    def make_mongodb_us_etf(self, ohlcv: str = 'N') -> bool:
        """
        Create MongoDB for US ETF data
        Based on refer/Database/MakMongoDB_US.py MakeMongoDB_US_ETF method
        
        Args:
            ohlcv: OHLCV data flag
            
        Returns:
            bool: Success status
        """
        try:
            # Setup logging
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Logs', self.area)
            if self.market != 'NA':
                log_dir = os.path.join(log_dir, self.market)
            
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'{self.area}EtfGetData_D.log')
            
            # Configure logging
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
                
            logging.basicConfig(
                filename=log_file,
                filemode='w',
                format='%(asctime)s - %(levelname)s - %(message)s',
                level=logging.INFO
            )
            
            # MongoDB connection
            conn = pymongo.MongoClient(
                host=self.stock_info["MONGODB_LOCAL"], 
                port=self.stock_info["MONGODB_PORT"],
                username=self.stock_info["MONGODB_ID"],
                password=self.stock_info["MONGODB_PW"]
            )
            
            # Process ETF data
            db_name = calculate_database_name(self.market, self.area, 'D', 'ETF')
            db = conn.get_database(db_name)
            
            processed_count = 0
            for etf_symbol in self.etf_list_us[:5]:  # Limit to first 5 for testing
                try:
                    collection = db[etf_symbol]
                    
                    # This would normally get OHLCV data from data providers
                    # For now, create sample data structure
                    sample_data = {
                        'symbol': etf_symbol,
                        'date': datetime.now(pytz.utc),
                        'processed': True,
                        'data_type': 'ETF_OHLCV'
                    }
                    
                    # Check if data already exists
                    existing = collection.find_one({'date': sample_data['date']})
                    if not existing:
                        collection.insert_one(sample_data)
                        processed_count += 1
                        logging.info(f"Processed ETF {etf_symbol}")
                    
                except Exception as etf_error:
                    logging.error(f"Error processing ETF {etf_symbol}: {etf_error}")
                    continue
            
            conn.close()
            logger.info(f"Successfully processed {processed_count} ETFs for MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Error in make_mongodb_us_etf: {e}")
            return False
    
    def make_mongodb_us_stock(self, ohlcv: str = 'N') -> bool:
        """
        Create MongoDB for US Stock data
        Similar to ETF method but for stocks
        
        Args:
            ohlcv: OHLCV data flag
            
        Returns:
            bool: Success status
        """
        try:
            # MongoDB connection
            conn = pymongo.MongoClient(
                host=self.stock_info["MONGODB_LOCAL"], 
                port=self.stock_info["MONGODB_PORT"],
                username=self.stock_info["MONGODB_ID"],
                password=self.stock_info["MONGODB_PW"]
            )
            
            # Process Stock data
            db_name = calculate_database_name(self.market, self.area, 'D', 'Stock')
            db = conn.get_database(db_name)
            
            processed_count = 0
            for stock_symbol in self.stock_list_us[:5]:  # Limit to first 5 for testing
                try:
                    collection = db[stock_symbol]
                    
                    # This would normally get OHLCV data from data providers
                    # For now, create sample data structure
                    sample_data = {
                        'symbol': stock_symbol,
                        'date': datetime.now(pytz.utc),
                        'processed': True,
                        'data_type': 'STOCK_OHLCV'
                    }
                    
                    # Check if data already exists
                    existing = collection.find_one({'date': sample_data['date']})
                    if not existing:
                        collection.insert_one(sample_data)
                        processed_count += 1
                        logger.info(f"Processed stock {stock_symbol}")
                    
                except Exception as stock_error:
                    logger.error(f"Error processing stock {stock_symbol}: {stock_error}")
                    continue
            
            conn.close()
            logger.info(f"Successfully processed {processed_count} stocks for MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Error in make_mongodb_us_stock: {e}")
            return False
    
    def get_market_status(self) -> dict:
        """
        Get current market status and data freshness
        
        Returns:
            dict: Market status information
        """
        return {
            'area': self.area,
            'market': self.market,
            'latest_daily_date': str(self.latest_d),
            'latest_weekly_date': str(self.latest_w),
            'stock_count': len(self.stock_list_us),
            'etf_count': len(self.etf_list_us),
            'delisted_stocks': len(self.delete_stock_list),
            'delisted_etfs': len(self.delete_etf_list),
            'data_period': {
                'start': str(self.start_day.date()),
                'end': str(self.end_day.date())
            }
        }
    
    def validate_data_integrity(self, db_name: str, sample_size: int = 10) -> dict:
        """
        Validate data integrity in database
        
        Args:
            db_name: Database name to validate
            sample_size: Number of collections to sample
            
        Returns:
            dict: Validation results
        """
        try:
            mongo_ops = MongoDBOperations("MONGODB_LOCAL")
            collections = mongo_ops.get_collection_names(db_name)
            
            validation_results = {
                'database': db_name,
                'total_collections': len(collections),
                'sampled_collections': min(sample_size, len(collections)),
                'valid_collections': 0,
                'invalid_collections': 0,
                'errors': []
            }
            
            # Sample collections for validation
            sample_collections = collections[:sample_size] if len(collections) >= sample_size else collections
            
            for collection_name in sample_collections:
                try:
                    # Check if collection has data
                    data = mongo_ops.execute_query(db_name, collection_name, limit=1)
                    
                    if not data.empty:
                        validation_results['valid_collections'] += 1
                    else:
                        validation_results['invalid_collections'] += 1
                        validation_results['errors'].append(f"Empty collection: {collection_name}")
                        
                except Exception as e:
                    validation_results['invalid_collections'] += 1
                    validation_results['errors'].append(f"Error in {collection_name}: {str(e)}")
            
            validation_results['success_rate'] = (
                validation_results['valid_collections'] / 
                validation_results['sampled_collections']
            ) * 100 if validation_results['sampled_collections'] > 0 else 0
            
            logger.info(f"Data integrity validation completed for {db_name}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in data integrity validation: {e}")
            return {
                'database': db_name,
                'error': str(e),
                'success_rate': 0
            }
    
    def get_summary(self) -> dict:
        """
        Get US Market Data Manager summary
        
        Returns:
            dict: Summary information
        """
        market_status = self.get_market_status()
        
        return {
            'component': 'USMarketDataManager',
            'market_info': market_status,
            'supported_operations': [
                'make_mongodb_us_etf',
                'make_mongodb_us_stock', 
                'get_market_status',
                'validate_data_integrity'
            ],
            'database_types': {
                'stock_daily': calculate_database_name(self.market, self.area, 'D', 'Stock'),
                'etf_daily': calculate_database_name(self.market, self.area, 'D', 'ETF'),
                'stock_weekly': calculate_database_name(self.market, self.area, 'W', 'Stock'),
                'etf_weekly': calculate_database_name(self.market, self.area, 'W', 'ETF')
            },
            'data_agent_managed': True
        }