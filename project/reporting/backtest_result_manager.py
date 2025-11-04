"""
Backtest Result Manager - Report Agent Management

Manages storage and retrieval of backtest results in MongoDB.
Provides API for storing strategies, results, trades, and comparisons.

Owner: Report Agent
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from project.database.mongodb_operations import MongoDBOperations
from project.database.backtest_result_schema import BacktestResultSchema

logger = logging.getLogger(__name__)


class BacktestResultManager:
    """
    Manages backtest result storage and retrieval

    Responsibilities:
    - Store strategy configurations
    - Store backtest results (performance metrics)
    - Store trade logs
    - Create strategy comparisons
    - Query and retrieve results
    """

    def __init__(self, db: Optional[MongoDBOperations] = None):
        """
        Initialize Backtest Result Manager

        Args:
            db: MongoDB operations instance. If None, creates new connection.
        """
        if db is None:
            self.db = MongoDBOperations(db_address="MONGODB_LOCAL")
        else:
            self.db = db

        self.schema = BacktestResultSchema(self.db)

        # Collection names
        self.db_name = BacktestResultSchema.DB_NAME
        self.coll_strategies = BacktestResultSchema.COLLECTION_STRATEGY_CONFIGS
        self.coll_results = BacktestResultSchema.COLLECTION_BACKTEST_RESULTS
        self.coll_trades = BacktestResultSchema.COLLECTION_TRADE_LOG
        self.coll_comparison = BacktestResultSchema.COLLECTION_STRATEGY_COMPARISON

        logger.info("Initialized BacktestResultManager")

    def _get_client(self):
        """Get MongoDB client"""
        return self.db._get_connection()

    def generate_strategy_id(self, strategy_name: str, version: str) -> str:
        """
        Generate unique strategy ID

        Args:
            strategy_name: Strategy name
            version: Version string

        Returns:
            Unique strategy ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{strategy_name}_{version}_{timestamp}"

    def generate_backtest_id(self, strategy_id: str) -> str:
        """
        Generate unique backtest ID

        Args:
            strategy_id: Strategy ID

        Returns:
            Unique backtest ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"BT_{strategy_id}_{timestamp}"

    def calculate_config_hash(self, config: Dict) -> str:
        """
        Calculate SHA256 hash of strategy configuration

        Args:
            config: Strategy configuration dictionary

        Returns:
            SHA256 hash string
        """
        config_json = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()

    def store_strategy_config(self, strategy: Dict, strategy_id: Optional[str] = None) -> str:
        """
        Store strategy configuration in MongoDB

        Args:
            strategy: Strategy dictionary (from YAML)
            strategy_id: Optional strategy ID. If None, generates new one.

        Returns:
            Strategy ID
        """
        try:
            # Generate strategy ID if not provided
            if strategy_id is None:
                strategy_meta = strategy.get('strategy', {})
                strategy_id = self.generate_strategy_id(
                    strategy_name=strategy_meta.get('name', 'unknown'),
                    version=strategy_meta.get('version', '1.0')
                )

            # Calculate config hash
            config_hash = self.calculate_config_hash(strategy)

            # Prepare document
            doc = {
                "strategy_id": strategy_id,
                "strategy_name": strategy.get('strategy', {}).get('name', 'unknown'),
                "version": strategy.get('strategy', {}).get('version', '1.0'),
                "created_at": datetime.now(),
                "created_by": "strategy_agent",
                "config": strategy,
                "config_hash": config_hash,
                "category": strategy.get('strategy', {}).get('category', 'unknown'),
                "tags": strategy.get('strategy', {}).get('tags', []),
                "market_type": strategy.get('strategy', {}).get('market_type', 'stocks'),
                "timeframe": strategy.get('strategy', {}).get('timeframe', 'daily'),
                "parent_strategy_id": None,
                "modification_notes": "Initial version"
            }

            # Insert into MongoDB
            client = self._get_client()
            collection = client[self.db_name][self.coll_strategies]

            # Use update_one with upsert to avoid duplicates
            result = collection.update_one(
                {"strategy_id": strategy_id},
                {"$set": doc},
                upsert=True
            )

            logger.info(f"[OK] Stored strategy config: {strategy_id}")
            return strategy_id

        except Exception as e:
            logger.error(f"Error storing strategy config: {e}")
            raise

    def store_backtest_result(self, backtest_id: str, strategy_id: str,
                             performance: Dict, trade_stats: Dict,
                             backtest_period: Dict,
                             **kwargs) -> bool:
        """
        Store backtest result in MongoDB

        Args:
            backtest_id: Backtest ID
            strategy_id: Strategy ID (foreign key)
            performance: Performance metrics dictionary
            trade_stats: Trade statistics dictionary
            backtest_period: Backtest period info
            **kwargs: Additional fields (risk_metrics, exposure, etc.)

        Returns:
            True if successful
        """
        try:
            # Prepare document
            doc = {
                "backtest_id": backtest_id,
                "strategy_id": strategy_id,
                "strategy_name": kwargs.get('strategy_name', 'unknown'),
                "executed_at": datetime.now(),
                "execution_time_seconds": kwargs.get('execution_time_seconds', 0),
                "backtest_period": backtest_period,
                "performance": performance,
                "trade_stats": trade_stats,
                "risk_metrics": kwargs.get('risk_metrics', {}),
                "exposure": kwargs.get('exposure', {}),
                "monthly_returns": kwargs.get('monthly_returns', []),
                "yearly_summary": kwargs.get('yearly_summary', []),
                "equity_curve": kwargs.get('equity_curve', []),
                "benchmark_comparison": kwargs.get('benchmark_comparison', {}),
                "strategy_metrics": kwargs.get('strategy_metrics', {}),
                "status": "completed",
                "validation_passed": True,
                "warnings": kwargs.get('warnings', []),
                "errors": kwargs.get('errors', [])
            }

            # Insert into MongoDB
            client = self._get_client()
            collection = client[self.db_name][self.coll_results]

            collection.insert_one(doc)

            logger.info(f"[OK] Stored backtest result: {backtest_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing backtest result: {e}")
            return False

    def store_trade(self, backtest_id: str, strategy_id: str, trade: Dict) -> bool:
        """
        Store individual trade in MongoDB

        Args:
            backtest_id: Backtest ID
            strategy_id: Strategy ID
            trade: Trade dictionary

        Returns:
            True if successful
        """
        try:
            # Add IDs to trade
            trade["backtest_id"] = backtest_id
            trade["strategy_id"] = strategy_id

            # Insert into MongoDB
            client = self._get_client()
            collection = client[self.db_name][self.coll_trades]

            collection.insert_one(trade)

            return True

        except Exception as e:
            logger.error(f"Error storing trade: {e}")
            return False

    def get_strategy_config(self, strategy_id: str) -> Optional[Dict]:
        """
        Retrieve strategy configuration

        Args:
            strategy_id: Strategy ID

        Returns:
            Strategy document or None
        """
        try:
            client = self._get_client()
            collection = client[self.db_name][self.coll_strategies]

            doc = collection.find_one({"strategy_id": strategy_id})

            return doc

        except Exception as e:
            logger.error(f"Error retrieving strategy config: {e}")
            return None

    def get_backtest_result(self, backtest_id: str) -> Optional[Dict]:
        """
        Retrieve backtest result

        Args:
            backtest_id: Backtest ID

        Returns:
            Backtest result document or None
        """
        try:
            client = self._get_client()
            collection = client[self.db_name][self.coll_results]

            doc = collection.find_one({"backtest_id": backtest_id})

            return doc

        except Exception as e:
            logger.error(f"Error retrieving backtest result: {e}")
            return None

    def list_strategies(self, category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       limit: int = 100) -> List[Dict]:
        """
        List strategy configurations

        Args:
            category: Filter by category
            tags: Filter by tags
            limit: Maximum number of results

        Returns:
            List of strategy documents
        """
        try:
            client = self._get_client()
            collection = client[self.db_name][self.coll_strategies]

            # Build query
            query = {}
            if category:
                query["category"] = category
            if tags:
                query["tags"] = {"$all": tags}

            # Find and sort by created_at descending
            cursor = collection.find(query).sort("created_at", -1).limit(limit)

            return list(cursor)

        except Exception as e:
            logger.error(f"Error listing strategies: {e}")
            return []

    def list_backtest_results(self, strategy_id: Optional[str] = None,
                             sort_by: str = "executed_at",
                             limit: int = 100) -> List[Dict]:
        """
        List backtest results

        Args:
            strategy_id: Filter by strategy ID
            sort_by: Sort field (executed_at, performance.sharpe_ratio, etc.)
            limit: Maximum number of results

        Returns:
            List of backtest result documents
        """
        try:
            client = self._get_client()
            collection = client[self.db_name][self.coll_results]

            # Build query
            query = {}
            if strategy_id:
                query["strategy_id"] = strategy_id

            # Find and sort
            cursor = collection.find(query).sort(sort_by, -1).limit(limit)

            return list(cursor)

        except Exception as e:
            logger.error(f"Error listing backtest results: {e}")
            return []

    def get_trades(self, backtest_id: str) -> List[Dict]:
        """
        Retrieve all trades for a backtest

        Args:
            backtest_id: Backtest ID

        Returns:
            List of trade documents
        """
        try:
            client = self._get_client()
            collection = client[self.db_name][self.coll_trades]

            cursor = collection.find({"backtest_id": backtest_id})

            return list(cursor)

        except Exception as e:
            logger.error(f"Error retrieving trades: {e}")
            return []

    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics of stored results

        Returns:
            Summary dictionary
        """
        try:
            client = self._get_client()

            stats = {
                "total_strategies": client[self.db_name][self.coll_strategies].count_documents({}),
                "total_backtests": client[self.db_name][self.coll_results].count_documents({}),
                "total_trades": client[self.db_name][self.coll_trades].count_documents({}),
                "total_comparisons": client[self.db_name][self.coll_comparison].count_documents({})
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {}


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test manager
    manager = BacktestResultManager()

    # Get summary stats
    stats = manager.get_summary_stats()
    print("=" * 60)
    print("BACKTEST RESULT MANAGER - SUMMARY")
    print("=" * 60)
    print(f"Total Strategies: {stats.get('total_strategies', 0)}")
    print(f"Total Backtests: {stats.get('total_backtests', 0)}")
    print(f"Total Trades: {stats.get('total_trades', 0)}")
    print(f"Total Comparisons: {stats.get('total_comparisons', 0)}")
    print("=" * 60)
