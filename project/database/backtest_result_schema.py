"""
Backtest Result Schema and MongoDB Collection Initialization

Defines MongoDB collections and indexes for strategy backtesting results.
Based on implementation plan Section 5.1.

Collections:
1. strategy_configs - Strategy YAML snapshots
2. backtest_results - Performance metrics
3. trade_log - Individual trade records
4. strategy_comparison - Multi-strategy comparison metadata

Owner: Database Agent
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from project.database.mongodb_operations import MongoDBOperations

logger = logging.getLogger(__name__)


class BacktestResultSchema:
    """
    Manages MongoDB collections and schemas for backtest results

    Responsibilities:
    - Create collections if they don't exist
    - Create indexes for fast queries
    - Define document schemas (for documentation)
    """

    # Database name for backtest results
    DB_NAME = "BacktestResults"

    # Collection names
    COLLECTION_STRATEGY_CONFIGS = "strategy_configs"
    COLLECTION_BACKTEST_RESULTS = "backtest_results"
    COLLECTION_TRADE_LOG = "trade_log"
    COLLECTION_STRATEGY_COMPARISON = "strategy_comparison"

    def __init__(self, db: Optional[MongoDBOperations] = None):
        """
        Initialize schema manager

        Args:
            db: MongoDB operations instance. If None, creates new connection.
        """
        if db is None:
            self.db = MongoDBOperations(db_address="MONGODB_LOCAL")
        else:
            self.db = db

        logger.info(f"Initialized BacktestResultSchema for database: {self.DB_NAME}")

    def initialize_all_collections(self) -> bool:
        """
        Initialize all collections and indexes

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Initializing all backtest result collections...")

            # Create collections and indexes
            self._create_strategy_configs_collection()
            self._create_backtest_results_collection()
            self._create_trade_log_collection()
            self._create_strategy_comparison_collection()

            logger.info("[OK] All collections initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            return False

    def _create_strategy_configs_collection(self):
        """
        Create strategy_configs collection and indexes

        Stores strategy YAML configurations (immutable snapshots)
        """
        collection_name = self.COLLECTION_STRATEGY_CONFIGS

        logger.info(f"Creating collection: {collection_name}")

        # Ensure collection exists (MongoDB creates on first insert, but we can verify)
        try:
            # Get MongoDB client connection
            client = self.db._get_connection()

            # Create indexes for fast queries
            client[self.DB_NAME][collection_name].create_index(
                "strategy_id",
                unique=True,
                name="idx_strategy_id"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("strategy_name", 1), ("version", 1)],
                name="idx_strategy_name_version"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("created_at", -1)],
                name="idx_created_at"
            )

            client[self.DB_NAME][collection_name].create_index(
                "tags",
                name="idx_tags"
            )

            client[self.DB_NAME][collection_name].create_index(
                "config_hash",
                name="idx_config_hash"
            )

            logger.info(f"[OK] Created indexes for {collection_name}")

        except Exception as e:
            logger.error(f"Error creating {collection_name}: {e}")
            raise

    def _create_backtest_results_collection(self):
        """
        Create backtest_results collection and indexes

        Stores quantitative backtest performance metrics
        """
        collection_name = self.COLLECTION_BACKTEST_RESULTS

        logger.info(f"Creating collection: {collection_name}")

        try:
            # Get MongoDB client connection
            client = self.db._get_connection()

            # Create indexes
            client[self.DB_NAME][collection_name].create_index(
                "backtest_id",
                unique=True,
                name="idx_backtest_id"
            )

            client[self.DB_NAME][collection_name].create_index(
                "strategy_id",
                name="idx_strategy_id"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("executed_at", -1)],
                name="idx_executed_at"
            )

            # Performance metric indexes for sorting/filtering
            client[self.DB_NAME][collection_name].create_index(
                [("performance.sharpe_ratio", -1)],
                name="idx_sharpe_ratio"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("performance.total_return", -1)],
                name="idx_total_return"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("performance.max_drawdown", 1)],
                name="idx_max_drawdown"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("trade_stats.win_rate", -1)],
                name="idx_win_rate"
            )

            logger.info(f"[OK] Created indexes for {collection_name}")

        except Exception as e:
            logger.error(f"Error creating {collection_name}: {e}")
            raise

    def _create_trade_log_collection(self):
        """
        Create trade_log collection and indexes

        Stores individual trade records with entry/exit details
        """
        collection_name = self.COLLECTION_TRADE_LOG

        logger.info(f"Creating collection: {collection_name}")

        try:
            # Get MongoDB client connection
            client = self.db._get_connection()

            # Create indexes
            client[self.DB_NAME][collection_name].create_index(
                [("backtest_id", 1), ("trade_id", 1)],
                name="idx_backtest_trade"
            )

            client[self.DB_NAME][collection_name].create_index(
                "strategy_id",
                name="idx_strategy_id"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("symbol", 1), ("entry_date", -1)],
                name="idx_symbol_entry_date"
            )

            client[self.DB_NAME][collection_name].create_index(
                "outcome",
                name="idx_outcome"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("pnl_percentage", -1)],
                name="idx_pnl_percentage"
            )

            logger.info(f"[OK] Created indexes for {collection_name}")

        except Exception as e:
            logger.error(f"Error creating {collection_name}: {e}")
            raise

    def _create_strategy_comparison_collection(self):
        """
        Create strategy_comparison collection and indexes

        Stores multi-strategy comparison metadata
        """
        collection_name = self.COLLECTION_STRATEGY_COMPARISON

        logger.info(f"Creating collection: {collection_name}")

        try:
            # Get MongoDB client connection
            client = self.db._get_connection()

            # Create indexes
            client[self.DB_NAME][collection_name].create_index(
                "comparison_id",
                unique=True,
                name="idx_comparison_id"
            )

            client[self.DB_NAME][collection_name].create_index(
                [("created_at", -1)],
                name="idx_created_at"
            )

            client[self.DB_NAME][collection_name].create_index(
                "strategies",
                name="idx_strategies"
            )

            logger.info(f"[OK] Created indexes for {collection_name}")

        except Exception as e:
            logger.error(f"Error creating {collection_name}: {e}")
            raise

    @staticmethod
    def get_strategy_config_schema() -> Dict:
        """
        Get strategy_configs collection schema (for documentation)

        Returns:
            Schema dictionary
        """
        return {
            "_id": "ObjectId",
            "strategy_id": "str (unique) - Format: {name}_{version}_{timestamp}",
            "strategy_name": "str",
            "version": "str",
            "created_at": "datetime",
            "created_by": "str (agent name)",
            "config": {
                "strategy": "dict",
                "indicators": "list",
                "entry": "dict",
                "exit": "dict",
                "filters": "list",
                "risk_management": "dict",
                "backtest": "dict"
            },
            "config_hash": "str (sha256)",
            "category": "str",
            "tags": "list[str]",
            "market_type": "str",
            "timeframe": "str",
            "parent_strategy_id": "str (nullable)",
            "modification_notes": "str"
        }

    @staticmethod
    def get_backtest_results_schema() -> Dict:
        """
        Get backtest_results collection schema (for documentation)

        Returns:
            Schema dictionary
        """
        return {
            "_id": "ObjectId",
            "backtest_id": "str (unique)",
            "strategy_id": "str (foreign key)",
            "strategy_name": "str",
            "executed_at": "datetime",
            "execution_time_seconds": "float",
            "backtest_period": {
                "start_date": "datetime",
                "end_date": "datetime",
                "total_days": "int",
                "trading_days": "int"
            },
            "performance": {
                "total_return": "float",
                "annual_return": "float",
                "cumulative_return": "float",
                "benchmark_return": "float",
                "alpha": "float",
                "beta": "float",
                "sharpe_ratio": "float",
                "sortino_ratio": "float",
                "calmar_ratio": "float",
                "information_ratio": "float",
                "max_drawdown": "float",
                "max_drawdown_duration_days": "int",
                "avg_drawdown": "float",
                "volatility_annual": "float",
                "downside_volatility": "float"
            },
            "trade_stats": {
                "total_trades": "int",
                "winning_trades": "int",
                "losing_trades": "int",
                "win_rate": "float",
                "avg_win": "float",
                "avg_loss": "float",
                "largest_win": "float",
                "largest_loss": "float",
                "avg_trade_return": "float",
                "avg_trade_duration_days": "float",
                "median_trade_duration_days": "float",
                "profit_factor": "float",
                "expectancy": "float",
                "consecutive_wins_max": "int",
                "consecutive_losses_max": "int"
            },
            "risk_metrics": {
                "value_at_risk_95": "float",
                "conditional_var_95": "float",
                "max_position_size": "float",
                "avg_position_size": "float",
                "max_portfolio_exposure": "float",
                "avg_portfolio_exposure": "float",
                "max_leverage": "float",
                "turnover_annual": "float"
            },
            "exposure": {
                "avg_long_exposure": "float",
                "avg_short_exposure": "float",
                "max_concurrent_positions": "int",
                "avg_concurrent_positions": "float",
                "time_in_market": "float",
                "time_in_cash": "float"
            },
            "monthly_returns": "list[dict]",
            "yearly_summary": "list[dict]",
            "equity_curve": "list[dict] (sampled)",
            "benchmark_comparison": "dict",
            "strategy_metrics": "dict (strategy-specific)",
            "status": "str (completed, failed, running)",
            "validation_passed": "bool",
            "warnings": "list[str]",
            "errors": "list[str]"
        }

    @staticmethod
    def get_trade_log_schema() -> Dict:
        """
        Get trade_log collection schema (for documentation)

        Returns:
            Schema dictionary
        """
        return {
            "_id": "ObjectId",
            "backtest_id": "str",
            "strategy_id": "str",
            "trade_id": "str",
            "symbol": "str",
            "entry_date": "datetime",
            "entry_price": "float",
            "entry_signal": "dict",
            "entry_reason": "str",
            "shares": "int",
            "position_value": "float",
            "portfolio_allocation": "float",
            "stop_loss_price": "float",
            "exit_date": "datetime",
            "exit_price": "float",
            "exit_signal": "dict",
            "exit_reason": "str",
            "exit_type": "str (signal_exit, stop_loss, profit_target, time_exit)",
            "pnl_absolute": "float",
            "pnl_percentage": "float",
            "pnl_r_multiple": "float",
            "holding_period_days": "int",
            "commission_paid": "float",
            "slippage_cost": "float",
            "mae": "float (Maximum Adverse Excursion)",
            "mfe": "float (Maximum Favorable Excursion)",
            "outcome": "str (win, loss, breakeven)"
        }

    @staticmethod
    def get_strategy_comparison_schema() -> Dict:
        """
        Get strategy_comparison collection schema (for documentation)

        Returns:
            Schema dictionary
        """
        return {
            "_id": "ObjectId",
            "comparison_id": "str (unique)",
            "created_at": "datetime",
            "created_by": "str (agent name)",
            "strategies": "list[str] (strategy_ids)",
            "comparison_metrics": {
                "best_return": "str (strategy_id)",
                "best_sharpe": "str (strategy_id)",
                "lowest_drawdown": "str (strategy_id)",
                "highest_win_rate": "str (strategy_id)"
            },
            "summary_table": "list[dict]",
            "notes": "str"
        }

    def get_collection_stats(self) -> Dict:
        """
        Get statistics for all collections

        Returns:
            Dictionary with collection stats
        """
        stats = {}

        collections = [
            self.COLLECTION_STRATEGY_CONFIGS,
            self.COLLECTION_BACKTEST_RESULTS,
            self.COLLECTION_TRADE_LOG,
            self.COLLECTION_STRATEGY_COMPARISON
        ]

        client = self.db._get_connection()

        for coll_name in collections:
            try:
                collection = client[self.DB_NAME][coll_name]
                count = collection.count_documents({})
                indexes = collection.index_information()

                stats[coll_name] = {
                    "document_count": count,
                    "indexes": list(indexes.keys()),
                    "index_count": len(indexes)
                }
            except Exception as e:
                logger.error(f"Error getting stats for {coll_name}: {e}")
                stats[coll_name] = {"error": str(e)}

        return stats

    def drop_all_collections(self, confirm: bool = False):
        """
        Drop all backtest result collections (DANGEROUS - for testing only)

        Args:
            confirm: Must be True to proceed
        """
        if not confirm:
            logger.warning("drop_all_collections called without confirmation - aborting")
            return

        logger.warning("DROPPING ALL BACKTEST RESULT COLLECTIONS")

        collections = [
            self.COLLECTION_STRATEGY_CONFIGS,
            self.COLLECTION_BACKTEST_RESULTS,
            self.COLLECTION_TRADE_LOG,
            self.COLLECTION_STRATEGY_COMPARISON
        ]

        client = self.db._get_connection()

        for coll_name in collections:
            try:
                client[self.DB_NAME][coll_name].drop()
                logger.info(f"Dropped collection: {coll_name}")
            except Exception as e:
                logger.error(f"Error dropping {coll_name}: {e}")


def initialize_backtest_database():
    """
    Convenience function to initialize backtest database

    Returns:
        True if successful
    """
    logger.info("Initializing backtest database...")

    try:
        schema = BacktestResultSchema()
        success = schema.initialize_all_collections()

        if success:
            stats = schema.get_collection_stats()
            logger.info("\nCollection Statistics:")
            for coll_name, coll_stats in stats.items():
                logger.info(f"  {coll_name}:")
                logger.info(f"    Documents: {coll_stats.get('document_count', 0)}")
                logger.info(f"    Indexes: {coll_stats.get('index_count', 0)}")

        return success

    except Exception as e:
        logger.error(f"Failed to initialize backtest database: {e}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Initialize database
    success = initialize_backtest_database()

    if success:
        print("\n[OK] Backtest database initialized successfully")
    else:
        print("\n[FAILED] Backtest database initialization failed")

    exit(0 if success else 1)
