"""
MongoDB Operations - Data Agent Management
Based on refer/Database/CalMongoDB.py
Core MongoDB operations for trading data management
"""

import pandas as pd
import pymongo
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
import os

# Setup logging
logger = logging.getLogger(__name__)

class MongoDBOperations:
    """
    MongoDB operations class for trading data management
    Based on refer/Database/CalMongoDB.py MongoDB class
    Data Agent has exclusive management of this class
    """
    
    def __init__(self, db_address: str = "MONGODB_LOCAL"):
        """
        Initialize MongoDB Operations

        Args:
            db_address: Database address identifier in config
        """
        self.db_address = db_address
        self.stock_info = None
        self._load_config()

        # Single persistent connection (reuse throughout lifecycle)
        self._client = None
        self._connect()
    
    def _load_config(self):
        """Load database configuration from myStockInfo.yaml"""
        try:
            # Try to find config file in project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(project_root, 'myStockInfo.yaml')
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='UTF-8') as f:
                    self.stock_info = yaml.load(f, Loader=yaml.FullLoader)
            else:
                logger.warning(f"Configuration file not found at {config_path}")
                # Create default configuration structure
                self.stock_info = {
                    self.db_address: "localhost",
                    "MONGODB_PORT": 27017,
                    "MONGODB_ID": "admin", 
                    "MONGODB_PW": "password"
                }
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Default configuration
            self.stock_info = {
                self.db_address: "localhost",
                "MONGODB_PORT": 27017,
                "MONGODB_ID": "admin",
                "MONGODB_PW": "password"
            }
    
    def _connect(self):
        """Establish single persistent MongoDB connection"""
        try:
            if self._client is None:
                self._client = pymongo.MongoClient(
                    host=self.stock_info[self.db_address],
                    port=self.stock_info["MONGODB_PORT"],
                    username=self.stock_info["MONGODB_ID"],
                    password=self.stock_info["MONGODB_PW"],
                    maxPoolSize=10,
                    minPoolSize=1,
                    maxIdleTimeMS=10000,
                    connectTimeoutMS=20000,
                    serverSelectionTimeoutMS=20000,
                    waitQueueTimeoutMS=5000
                )
                logger.info(f"MongoDB connection established to {self.stock_info[self.db_address]}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _get_connection(self) -> pymongo.MongoClient:
        """Get the persistent MongoDB connection (for backward compatibility)"""
        if self._client is None:
            self._connect()
        return self._client

    def close(self):
        """Close MongoDB connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
    
    def make_stock_db(self, db_name: str, df_data: dict, stock: str) -> bool:
        """
        Create stock database entry
        Based on refer/Database/CalMongoDB.py MakStockDb method
        
        Args:
            db_name: Database name
            df_data: Data dictionary to store
            stock: Stock symbol
            
        Returns:
            bool: Success status
        """
        try:
            renamed_stock = "A" + stock
            
            conn = self._get_connection()
            db = conn.get_database(db_name)
            collection = db[renamed_stock]
            
            # Insert document into MongoDB
            collection.insert_one(df_data)

            return True
            
        except Exception as e:
            logger.error(f"Error creating stock DB for {stock}: {e}")
            return False
    
    def update_stock_db(self, db_name: str, df_data: dict, stock: str) -> bool:
        """
        Update stock database entry
        Based on refer/Database/CalMongoDB.py UpdStockDb method
        
        Args:
            db_name: Database name
            df_data: Data dictionary to update
            stock: Stock symbol
            
        Returns:
            bool: Success status
        """
        try:
            renamed_stock = "A" + stock
            
            conn = self._get_connection()
            db = conn.get_database(db_name)
            collection = db[renamed_stock]
            
            # Get today's date
            today = datetime.now()
            
            # Check if today's data already exists
            existing_data = collection.find_one({'Date': today})
            
            if not existing_data:
                # Get latest document
                latest_document = collection.find().sort('Date', -1).limit(1)
                
                # Insert new data (this would normally get OHLCV data from Helper)
                # For now, we'll insert the provided data
                if isinstance(df_data, pd.DataFrame):
                    df_data = df_data.reset_index()
                    
                    # Insert each row
                    for index, row in df_data.iterrows():
                        # Check if this date already exists
                        if collection.find_one({'Date': row['Date']}):
                            continue
                        
                        # Insert row
                        collection.insert_one(row.to_dict())
                else:
                    # Insert single document
                    collection.insert_one(df_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating stock DB for {stock}: {e}")
            return False
    
    def execute_query(self, db_name: str, collection_name: str, query: dict = None,
                     projection: dict = None, limit: int = None) -> pd.DataFrame:
        """
        Execute MongoDB query and return DataFrame
        Based on refer/Database/CalMongoDB.py ExecuteSql method

        Args:
            db_name: Database name
            collection_name: Collection name
            query: Query filter
            projection: Field projection
            limit: Result limit

        Returns:
            pd.DataFrame: Query results
        """
        try:
            # Validate collection name
            if not collection_name or not collection_name.strip():
                logger.error(f"Error executing query on {db_name}.: collection names cannot be empty")
                return pd.DataFrame()

            conn = self._get_connection()
            db = conn[db_name]
            collection = db[collection_name]

            # Build query
            if query is None:
                query = {}

            cursor = collection.find(query, projection)

            if limit:
                cursor = cursor.limit(limit)

            # Convert to DataFrame
            data = pd.DataFrame(list(cursor))
            return data

        except Exception as e:
            logger.error(f"Error executing query on {db_name}.{collection_name}: {e}")
            return pd.DataFrame()
    
    def get_latest_data(self, db_name: str, collection_name: str, date_field: str = 'Date') -> dict:
        """
        Get latest data from collection
        
        Args:
            db_name: Database name
            collection_name: Collection name
            date_field: Date field name for sorting
            
        Returns:
            dict: Latest document
        """
        try:
            conn = self._get_connection()
            db = conn[db_name]
            collection = db[collection_name]
            
            # Get latest document
            latest_doc = collection.find().sort(date_field, -1).limit(1)
            result = list(latest_doc)
            if result:
                return result[0]
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting latest data from {db_name}.{collection_name}: {e}")
            return {}
    
    def check_data_exists(self, db_name: str, collection_name: str, query: dict) -> bool:
        """
        Check if data exists in collection
        
        Args:
            db_name: Database name
            collection_name: Collection name
            query: Query to check
            
        Returns:
            bool: True if data exists
        """
        try:
            conn = self._get_connection()
            db = conn[db_name]
            collection = db[collection_name]
            
            result = collection.find_one(query)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking data existence in {db_name}.{collection_name}: {e}")
            return False
    
    def get_collection_names(self, db_name: str) -> list:
        """
        Get all collection names in database
        
        Args:
            db_name: Database name
            
        Returns:
            list: Collection names
        """
        try:
            conn = self._get_connection()
            db = conn[db_name]
            
            collections = db.list_collection_names()
            return collections
            
        except Exception as e:
            logger.error(f"Error getting collection names from {db_name}: {e}")
            return []
    
    def delete_collection(self, db_name: str, collection_name: str) -> bool:
        """
        Delete collection from database
        
        Args:
            db_name: Database name
            collection_name: Collection name
            
        Returns:
            bool: Success status
        """
        try:
            conn = self._get_connection()
            db = conn[db_name]
            
            db[collection_name].drop()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name} from {db_name}: {e}")
            return False
    
    def get_database_stats(self, db_name: str) -> dict:
        """
        Get database statistics
        
        Args:
            db_name: Database name
            
        Returns:
            dict: Database statistics
        """
        try:
            conn = self._get_connection()
            db = conn[db_name]
            
            stats = db.command("dbStats")
            collections = db.list_collection_names()
            result = {
                'database_name': db_name,
                'collections_count': len(collections),
                'collections': collections[:10],  # First 10 collections
                'data_size': stats.get('dataSize', 0),
                'storage_size': stats.get('storageSize', 0),
                'indexes': stats.get('indexes', 0),
                'objects': stats.get('objects', 0)
            }

            return result
            
        except Exception as e:
            logger.error(f"Error getting database stats for {db_name}: {e}")
            return {'database_name': db_name, 'error': str(e)}
    
    def test_connection(self) -> dict:
        """
        Test MongoDB connection
        
        Returns:
            dict: Connection test results
        """
        try:
            conn = self._get_connection()
            
            # Test connection with a simple command
            result = conn.admin.command('ping')
            
            # Get server info
            server_info = conn.server_info()
            return {
                'connected': True,
                'server_version': server_info.get('version'),
                'address': self.stock_info[self.db_address],
                'port': self.stock_info["MONGODB_PORT"],
                'ping_result': result
            }
            
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            return {
                'connected': False,
                'error': str(e),
                'address': self.stock_info[self.db_address],
                'port': self.stock_info["MONGODB_PORT"]
            }
    
    def get_summary(self) -> dict:
        """
        Get MongoDB operations summary
        
        Returns:
            dict: Summary information
        """
        connection_test = self.test_connection()
        
        return {
            'component': 'MongoDBOperations',
            'db_address': self.db_address,
            'connection_status': connection_test.get('connected', False),
            'server_info': connection_test,
            'supported_operations': [
                'make_stock_db',
                'update_stock_db', 
                'execute_query',
                'get_latest_data',
                'check_data_exists',
                'get_collection_names',
                'delete_collection',
                'get_database_stats'
            ],
            'data_agent_managed': True
        }