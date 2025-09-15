"""
Historical Data Manager - Data Agent Management
Based on refer/Database/MakMongoDB_Hist.py
Manages historical trading data and account information
"""

import pymongo
import pandas as pd
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os

from .mongodb_operations import MongoDBOperations

# Setup logging
logger = logging.getLogger(__name__)

class HistoricalDataManager:
    """
    Historical Data Manager for account and trading data
    Based on refer/Database/MakMongoDB_Hist.py ColMongoHistDB class
    Data Agent has exclusive management of this class
    """
    
    def __init__(self):
        """Initialize Historical Data Manager"""
        self._load_config()
        logger.info("Initialized HistoricalDataManager")
    
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
                    "MONGODB_NAS": "localhost",
                    "MONGODB_LOCAL": "localhost", 
                    "MONGODB_PORT": 27017,
                    "MONGODB_ID": "admin",
                    "MONGODB_PW": "password"
                }
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.stock_info = {
                "MONGODB_NAS": "localhost",
                "MONGODB_LOCAL": "localhost",
                "MONGODB_PORT": 27017,
                "MONGODB_ID": "admin",
                "MONGODB_PW": "password"
            }
    
    def _get_connection(self, db_type: str = "MONGODB_NAS") -> pymongo.MongoClient:
        """Get MongoDB connection for specified database type"""
        try:
            connection = pymongo.MongoClient(
                host=self.stock_info[db_type],
                port=self.stock_info["MONGODB_PORT"],
                username=self.stock_info["MONGODB_ID"],
                password=self.stock_info["MONGODB_PW"],
                maxIdleTimeMS=120000,
                serverSelectionTimeoutMS=30000
            )
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to {db_type}: {e}")
            raise
    
    def make_mongodb_account(self, mode: str, account_dict: Dict[str, Any]) -> bool:
        """
        Store account data in MongoDB
        Based on refer/Database/MakMongoDB_Hist.py MakeMongoDB_Accnt method
        
        Args:
            mode: Account mode/identifier
            account_dict: Account data dictionary with 'Date' key
            
        Returns:
            bool: Success status
        """
        try:
            # Set change mode (this would normally call Helper function)
            # Common.SetChangeMode(mode)
            
            conn = self._get_connection("MONGODB_NAS")
            
            # Get database and collection
            str_database_name = 'AccntDataBase'
            db = conn.get_database(str_database_name)
            collection = db.get_collection(mode)
            
            # Get update date from account dictionary
            updated_date = account_dict['Date']
            
            # Get list of existing collections
            list_of_collections = db.list_collection_names()
            
            # Check if collection exists and has data
            if mode in list_of_collections:
                collection = db.get_collection(mode)
                
                try:
                    # Get the most recent date from existing data
                    previous_date_doc = collection.find_one(sort=[('Date', -1)])
                    
                    if previous_date_doc:
                        previous_date = previous_date_doc['Date']
                        
                        # Compare dates (only date part, not time)
                        if previous_date.date() != account_dict['Date'].date():
                            print(f"## UPDATE : {mode} - {updated_date}")
                            collection.insert_one(account_dict)
                            logger.info(f"Updated account data for {mode} on {updated_date}")
                        else:
                            print(f"## EXIST : {mode} - {updated_date}")
                            logger.info(f"Account data for {mode} already exists for {updated_date}")
                    else:
                        # Collection exists but is empty
                        print(f"## NEW DATA : {mode} - {updated_date}")
                        collection.insert_one(account_dict)
                        logger.info(f"Added first account data for {mode} on {updated_date}")
                            
                except Exception as e:
                    print(f"## EXCEPTION : {mode} - {e}")
                    logger.error(f"Exception in account data update for {mode}: {e}")
                    
            else:
                # Collection doesn't exist, create it and insert data
                collection = db.get_collection(mode)
                print(f"## NEW : {mode} - {updated_date}")
                collection.insert_one(account_dict)
                logger.info(f"Created new account collection {mode} with data for {updated_date}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error in make_mongodb_account for {mode}: {e}")
            return False
    
    def make_mongodb_trade(self, mode: str, account_dict: Dict[str, Any]) -> bool:
        """
        Store trading data in MongoDB
        Based on refer/Database/MakMongoDB_Hist.py MakeMongoDB_Trade method
        
        Args:
            mode: Trading mode/identifier
            account_dict: Trading data dictionary with 'Date' key
            
        Returns:
            bool: Success status
        """
        try:
            # Set change mode (this would normally call Helper function)
            # Common.SetChangeMode(mode)
            
            conn = self._get_connection("MONGODB_NAS")
            
            # Get database and collection
            str_database_name = 'AccntDataBase_Trade'
            db = conn.get_database(str_database_name)
            
            # Get update date from account dictionary
            updated_date = account_dict['Date']
            
            # Get list of existing collections
            list_of_collections = db.list_collection_names()
            
            # Check if collection exists and has data
            if mode in list_of_collections:
                collection = db.get_collection(mode)
                
                try:
                    # Get the most recent date from existing data
                    previous_date_doc = collection.find_one(sort=[('Date', -1)])
                    
                    if previous_date_doc:
                        previous_date = previous_date_doc['Date']
                        
                        print(previous_date.date(), account_dict['Date'].date())
                        
                        # Compare dates (only date part, not time)
                        if previous_date.date() != account_dict['Date'].date():
                            print(f"## UPDATE : {mode} - {updated_date}")
                            collection.insert_one(account_dict)
                            logger.info(f"Updated trade data for {mode} on {updated_date}")
                        else:
                            print(f"## EXIST : {mode} - {updated_date}")
                            logger.info(f"Trade data for {mode} already exists for {updated_date}")
                    else:
                        # Collection exists but is empty
                        print(f"## NEW DATA : {mode} - {updated_date}")
                        collection.insert_one(account_dict)
                        logger.info(f"Added first trade data for {mode} on {updated_date}")
                            
                except Exception as e:
                    print(f"## EXCEPTION : {mode} - {e}")
                    logger.error(f"Exception in trade data update for {mode}: {e}")
                    
            else:
                # Collection doesn't exist, create it and insert data
                collection = db.get_collection(mode)
                print(f"## NEW : {mode} - {updated_date}")
                collection.insert_one(account_dict)
                logger.info(f"Created new trade collection {mode} with data for {updated_date}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error in make_mongodb_trade for {mode}: {e}")
            return False
    
    def get_account_history(self, mode: str, start_date: datetime = None, 
                           end_date: datetime = None) -> pd.DataFrame:
        """
        Get account history data
        
        Args:
            mode: Account mode/identifier
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            pd.DataFrame: Account history data
        """
        try:
            mongo_ops = MongoDBOperations("MONGODB_NAS")
            
            # Build query filter
            query = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = start_date
                if end_date:
                    date_filter['$lte'] = end_date
                query['Date'] = date_filter
            
            # Get data from AccntDataBase
            data = mongo_ops.execute_query('AccntDataBase', mode, query)
            
            logger.info(f"Retrieved {len(data)} account history records for {mode}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting account history for {mode}: {e}")
            return pd.DataFrame()
    
    def get_trade_history(self, mode: str, start_date: datetime = None,
                         end_date: datetime = None) -> pd.DataFrame:
        """
        Get trading history data
        
        Args:
            mode: Trading mode/identifier
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            pd.DataFrame: Trading history data
        """
        try:
            mongo_ops = MongoDBOperations("MONGODB_NAS")
            
            # Build query filter
            query = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = start_date
                if end_date:
                    date_filter['$lte'] = end_date
                query['Date'] = date_filter
            
            # Get data from AccntDataBase_Trade
            data = mongo_ops.execute_query('AccntDataBase_Trade', mode, query)
            
            logger.info(f"Retrieved {len(data)} trade history records for {mode}")
            return data
            
        except Exception as e:
            logger.error(f"Error getting trade history for {mode}: {e}")
            return pd.DataFrame()
    
    def get_latest_account_data(self, mode: str) -> Dict[str, Any]:
        """
        Get latest account data for a mode
        
        Args:
            mode: Account mode/identifier
            
        Returns:
            dict: Latest account data
        """
        try:
            mongo_ops = MongoDBOperations("MONGODB_NAS")
            latest_data = mongo_ops.get_latest_data('AccntDataBase', mode, 'Date')
            
            logger.info(f"Retrieved latest account data for {mode}")
            return latest_data
            
        except Exception as e:
            logger.error(f"Error getting latest account data for {mode}: {e}")
            return {}
    
    def get_latest_trade_data(self, mode: str) -> Dict[str, Any]:
        """
        Get latest trading data for a mode
        
        Args:
            mode: Trading mode/identifier
            
        Returns:
            dict: Latest trading data
        """
        try:
            mongo_ops = MongoDBOperations("MONGODB_NAS")
            latest_data = mongo_ops.get_latest_data('AccntDataBase_Trade', mode, 'Date')
            
            logger.info(f"Retrieved latest trade data for {mode}")
            return latest_data
            
        except Exception as e:
            logger.error(f"Error getting latest trade data for {mode}: {e}")
            return {}
    
    def delete_account_data(self, mode: str, target_date: datetime = None) -> bool:
        """
        Delete account data for a specific mode and optional date
        
        Args:
            mode: Account mode/identifier
            target_date: Specific date to delete (if None, deletes entire collection)
            
        Returns:
            bool: Success status
        """
        try:
            conn = self._get_connection("MONGODB_NAS")
            db = conn.get_database('AccntDataBase')
            collection = db.get_collection(mode)
            
            if target_date:
                # Delete specific date
                result = collection.delete_many({'Date': target_date})
                logger.info(f"Deleted {result.deleted_count} account records for {mode} on {target_date}")
            else:
                # Delete entire collection
                collection.drop()
                logger.info(f"Deleted entire account collection for {mode}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting account data for {mode}: {e}")
            return False
    
    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get summary of historical databases
        
        Returns:
            dict: Database summary information
        """
        try:
            mongo_ops = MongoDBOperations("MONGODB_NAS")
            
            # Get account database stats
            account_stats = mongo_ops.get_database_stats('AccntDataBase')
            
            # Get trade database stats
            trade_stats = mongo_ops.get_database_stats('AccntDataBase_Trade')
            
            summary = {
                'account_database': account_stats,
                'trade_database': trade_stats,
                'connection_status': mongo_ops.test_connection(),
                'component': 'HistoricalDataManager'
            }
            
            logger.info("Generated historical data summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return {'error': str(e)}
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get Historical Data Manager summary
        
        Returns:
            dict: Summary information
        """
        return {
            'component': 'HistoricalDataManager',
            'supported_operations': [
                'make_mongodb_account',
                'make_mongodb_trade',
                'get_account_history',
                'get_trade_history',
                'get_latest_account_data',
                'get_latest_trade_data',
                'delete_account_data'
            ],
            'managed_databases': [
                'AccntDataBase',
                'AccntDataBase_Trade'
            ],
            'connection_types': ['MONGODB_NAS', 'MONGODB_LOCAL'],
            'data_agent_managed': True
        }