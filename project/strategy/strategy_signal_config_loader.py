#!/usr/bin/env python3
"""
Strategy Signal Configuration Loader - Multi-Strategy Support
YAML 기반 Signal 조건 설정 로더 (여러 전략 지원)

Version: 2.0
Last Updated: 2025-10-18

Usage:
    config = StrategySignalConfigLoader()

    # Get active strategy
    active = config.get_active_strategy()  # "balanced"

    # Get fundamental conditions from active strategy
    min_market_cap = config.get_fundamental_market_cap_min()
    min_rev_yoy = config.get_fundamental_revenue_min_yoy()

    # Get from specific strategy
    min_market_cap = config.get_fundamental_market_cap_min(strategy='conservative')
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StrategySignalConfigLoader:
    """
    Strategy Signal 조건 설정 로더 - Multi-Strategy Support
    config/strategy_signal_config.yaml 파일을 로드하여 Signal 조건 제공
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader

        Args:
            config_path: Path to strategy_signal_config.yaml
                        If None, uses default path: config/strategy_signal_config.yaml
        """
        if config_path is None:
            # Default path
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'strategy_signal_config.yaml'

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded strategy signal config from: {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file not found"""
        logger.warning("Using default hardcoded configuration")
        return {
            'active_strategy': 'balanced',
            'strategies': {
                'balanced': {
                    'earnings_signal': {'enabled': False},
                    'fundamental_signal': {
                        'enabled': True,
                        'market_cap': {'min': 2000000000, 'max': 20000000000000},
                        'revenue': {'min_yoy': 0.1, 'min_prev_yoy': 0.0, 'min_value': 0},
                        'eps': {'min_yoy': 0.1, 'min_prev_yoy': 0.0},
                        'growth_logic': 'OR'
                    },
                    'weekly_signal': {
                        'enabled': True,
                        'high_stability': {'factor': 1.05, 'shift_periods': 2},
                        'low_distance': {'factor': 1.3, 'shift_periods': 1},
                        'high_distance': {'factor': 0.7, 'shift_periods': 1}
                    },
                    'rs_signal': {
                        'enabled': True,
                        'threshold': 90,
                        'use_t_minus_1': True
                    },
                    'daily_signal': {
                        'enabled': True,
                        'base_conditions': {
                            'rs': {'threshold': 90}
                        },
                        'prices': {'losscut_ratio': 0.97},
                        'use_t_minus_1': True
                    },
                    'thresholds': {
                        'E': 1.0, 'F': 1.0, 'W': 1.0, 'RS': 1.0, 'D': 0.5
                    }
                }
            }
        }

    # =========================================================================
    # Strategy Selection
    # =========================================================================
    def get_active_strategy(self) -> str:
        """
        Get currently active strategy name

        Returns:
            Strategy name (e.g., 'balanced', 'conservative', 'aggressive')
        """
        return self.config.get('active_strategy', 'balanced')

    def get_strategy_config(self, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific strategy

        Args:
            strategy: Strategy name. If None, uses active strategy.

        Returns:
            Strategy configuration dictionary
        """
        if strategy is None:
            strategy = self.get_active_strategy()

        strategies = self.config.get('strategies', {})
        return strategies.get(strategy, {})

    def list_strategies(self) -> list:
        """
        Get list of available strategies

        Returns:
            List of strategy names
        """
        return list(self.config.get('strategies', {}).keys())

    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all strategies configuration

        Returns:
            Dictionary of all strategies
        """
        return self.config.get('strategies', {})

    # =========================================================================
    # Signal Enabled Checks (Generic)
    # =========================================================================
    def is_signal_enabled(self, signal_name: str, strategy: Optional[str] = None) -> bool:
        """
        Check if a signal is enabled

        Args:
            signal_name: 'earnings', 'fundamental', 'weekly', 'rs', or 'daily_rs'
            strategy: Strategy name (optional)

        Returns:
            True if signal is enabled, False otherwise
        """
        config = self.get_strategy_config(strategy)

        signal_map = {
            'earnings': 'earnings_signal',
            'fundamental': 'fundamental_signal',
            'weekly': 'weekly_signal',
            'rs': 'rs_signal',
            'daily_rs': 'daily_signal'  # daily_rs uses daily_signal config
        }

        config_key = signal_map.get(signal_name)
        if config_key:
            return config.get(config_key, {}).get('enabled', True)
        return True

    # =========================================================================
    # Earnings Signal Config
    # =========================================================================
    def is_earnings_enabled(self, strategy: Optional[str] = None) -> bool:
        """Check if earnings signal is enabled"""
        config = self.get_strategy_config(strategy)
        return config.get('earnings_signal', {}).get('enabled', False)

    def get_earnings_revenue_min_prev_yoy(self, strategy: Optional[str] = None) -> float:
        """Get earnings revenue min_prev_yoy"""
        config = self.get_strategy_config(strategy)
        return config.get('earnings_signal', {}).get('revenue', {}).get('min_prev_yoy', 0.0)

    def get_earnings_eps_min_prev_yoy(self, strategy: Optional[str] = None) -> float:
        """Get earnings EPS min_prev_yoy"""
        config = self.get_strategy_config(strategy)
        return config.get('earnings_signal', {}).get('eps', {}).get('min_prev_yoy', 0.0)

    def get_earnings_revenue_require_growth(self, strategy: Optional[str] = None) -> bool:
        """Get earnings revenue require_growth flag"""
        config = self.get_strategy_config(strategy)
        return config.get('earnings_signal', {}).get('revenue', {}).get('require_growth', True)

    def get_earnings_eps_require_growth(self, strategy: Optional[str] = None) -> bool:
        """Get earnings EPS require_growth flag"""
        config = self.get_strategy_config(strategy)
        return config.get('earnings_signal', {}).get('eps', {}).get('require_growth', True)

    # =========================================================================
    # Fundamental Signal Config
    # =========================================================================
    def is_fundamental_enabled(self, strategy: Optional[str] = None) -> bool:
        """Check if fundamental signal is enabled"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('enabled', True)

    def get_fundamental_market_cap_min(self, strategy: Optional[str] = None) -> float:
        """Get fundamental market cap minimum"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('market_cap', {}).get('min', 2000000000)

    def get_fundamental_market_cap_max(self, strategy: Optional[str] = None) -> float:
        """Get fundamental market cap maximum"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('market_cap', {}).get('max', 20000000000000)

    def get_fundamental_revenue_min_yoy(self, strategy: Optional[str] = None) -> float:
        """Get fundamental revenue min_yoy"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('revenue', {}).get('min_yoy', 0.1)

    def get_fundamental_revenue_min_prev_yoy(self, strategy: Optional[str] = None) -> float:
        """Get fundamental revenue min_prev_yoy"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('revenue', {}).get('min_prev_yoy', 0.0)

    def get_fundamental_eps_min_yoy(self, strategy: Optional[str] = None) -> float:
        """Get fundamental EPS min_yoy"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('eps', {}).get('min_yoy', 0.1)

    def get_fundamental_eps_min_prev_yoy(self, strategy: Optional[str] = None) -> float:
        """Get fundamental EPS min_prev_yoy"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('eps', {}).get('min_prev_yoy', 0.0)

    def get_fundamental_revenue_min_value(self, strategy: Optional[str] = None) -> float:
        """Get fundamental revenue min_value"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('revenue', {}).get('min_value', 0)

    def get_fundamental_growth_logic(self, strategy: Optional[str] = None) -> str:
        """Get fundamental growth logic (OR/AND)"""
        config = self.get_strategy_config(strategy)
        return config.get('fundamental_signal', {}).get('growth_logic', 'OR')

    # =========================================================================
    # Weekly Signal Config
    # =========================================================================
    def is_weekly_enabled(self, strategy: Optional[str] = None) -> bool:
        """Check if weekly signal is enabled"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('enabled', True)

    def get_weekly_high_stability_factor(self, strategy: Optional[str] = None) -> float:
        """Get weekly high stability factor"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('high_stability', {}).get('factor', 1.05)

    def get_weekly_high_stability_shift(self, strategy: Optional[str] = None) -> int:
        """Get weekly high stability shift periods"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('high_stability', {}).get('shift_periods', 2)

    def get_weekly_low_distance_factor(self, strategy: Optional[str] = None) -> float:
        """Get weekly low distance factor"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('low_distance', {}).get('factor', 1.3)

    def get_weekly_low_distance_shift(self, strategy: Optional[str] = None) -> int:
        """Get weekly low distance shift periods"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('low_distance', {}).get('shift_periods', 1)

    def get_weekly_high_distance_factor(self, strategy: Optional[str] = None) -> float:
        """Get weekly high distance factor"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('high_distance', {}).get('factor', 0.7)

    def get_weekly_high_distance_shift(self, strategy: Optional[str] = None) -> int:
        """Get weekly high distance shift periods"""
        config = self.get_strategy_config(strategy)
        return config.get('weekly_signal', {}).get('high_distance', {}).get('shift_periods', 1)

    # =========================================================================
    # RS Signal Config
    # =========================================================================
    def is_rs_enabled(self, strategy: Optional[str] = None) -> bool:
        """Check if RS signal is enabled"""
        config = self.get_strategy_config(strategy)
        return config.get('rs_signal', {}).get('enabled', True)

    def get_rs_threshold(self, strategy: Optional[str] = None) -> float:
        """Get RS threshold"""
        config = self.get_strategy_config(strategy)
        return config.get('rs_signal', {}).get('threshold', 90)

    def get_rs_use_t_minus_1(self, strategy: Optional[str] = None) -> bool:
        """Get RS use_t_minus_1 flag"""
        config = self.get_strategy_config(strategy)
        return config.get('rs_signal', {}).get('use_t_minus_1', True)

    # =========================================================================
    # Daily Signal Config
    # =========================================================================
    def is_daily_enabled(self, strategy: Optional[str] = None) -> bool:
        """Check if daily signal is enabled"""
        config = self.get_strategy_config(strategy)
        return config.get('daily_signal', {}).get('enabled', True)

    def get_daily_rs_threshold(self, strategy: Optional[str] = None) -> float:
        """Get daily RS threshold"""
        config = self.get_strategy_config(strategy)
        return config.get('daily_signal', {}).get('base_conditions', {}).get('rs', {}).get('threshold', 90)

    def get_daily_losscut_ratio(self, strategy: Optional[str] = None) -> float:
        """Get daily losscut ratio"""
        config = self.get_strategy_config(strategy)
        return config.get('daily_signal', {}).get('prices', {}).get('losscut_ratio', 0.97)

    def get_daily_target_multiplier(self, strategy: Optional[str] = None) -> float:
        """Get daily target price multiplier"""
        config = self.get_strategy_config(strategy)
        return config.get('daily_signal', {}).get('prices', {}).get('target_multiplier', 1.0)

    def get_daily_breakout_timeframes(self, strategy: Optional[str] = None) -> list:
        """Get daily breakout timeframes"""
        config = self.get_strategy_config(strategy)
        return config.get('daily_signal', {}).get('breakout', {}).get('timeframes', ['2Y', '1Y', '6M', '3M', '1M'])

    # =========================================================================
    # Thresholds
    # =========================================================================
    def get_threshold(self, stage: str, strategy: Optional[str] = None) -> float:
        """
        Get threshold for a specific stage

        Args:
            stage: 'E', 'F', 'W', 'RS', or 'D'
            strategy: Strategy name (optional)

        Returns:
            Threshold value (default 1.0)
        """
        config = self.get_strategy_config(strategy)
        return config.get('thresholds', {}).get(stage, 1.0)

    def get_all_thresholds(self, strategy: Optional[str] = None) -> Dict[str, float]:
        """Get all thresholds"""
        config = self.get_strategy_config(strategy)
        return config.get('thresholds', {
            'E': 1.0, 'F': 1.0, 'W': 1.0, 'RS': 1.0, 'D': 0.5
        })

    # =========================================================================
    # Backward Compatibility (Generic accessors)
    # =========================================================================
    def get_fundamental_config(self, *keys) -> Any:
        """
        Get fundamental signal configuration (backward compatible)

        Example:
            min_market_cap = config.get_fundamental_config('market_cap', 'min')
            min_rev_yoy = config.get_fundamental_config('revenue', 'min_yoy')
        """
        config = self.get_strategy_config()
        result = config.get('fundamental_signal', {})
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    def get_weekly_config(self, *keys) -> Any:
        """Get weekly signal configuration (backward compatible)"""
        config = self.get_strategy_config()
        result = config.get('weekly_signal', {})
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    def get_rs_config(self, *keys) -> Any:
        """Get RS signal configuration (backward compatible)"""
        config = self.get_strategy_config()
        result = config.get('rs_signal', {})
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    def get_daily_config(self, *keys) -> Any:
        """Get daily signal configuration (backward compatible)"""
        config = self.get_strategy_config()
        result = config.get('daily_signal', {})
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    def get_earnings_config(self, *keys) -> Any:
        """Get earnings signal configuration (backward compatible)"""
        config = self.get_strategy_config()
        result = config.get('earnings_signal', {})
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    # =========================================================================
    # Final Signal Config
    # =========================================================================
    def get_final_signal_config(self, *keys) -> Any:
        """
        Get final signal combination configuration

        Example:
            required = config.get_final_signal_config('required_signals', 'fundamental')
            buy_confidence = config.get_final_signal_config('confidence', 'buy_confidence')
        """
        result = self.config.get('final_signal', {})
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return None
        return result

    # =========================================================================
    # Execution Modes
    # =========================================================================
    def get_execution_mode_config(self, mode: str) -> Dict[str, Any]:
        """
        Get execution mode configuration

        Args:
            mode: 'backtest', 'symbol_check', 'live_trading', 'timeline'

        Returns:
            Execution mode configuration
        """
        return self.config.get('execution_modes', {}).get(mode, {})

    # =========================================================================
    # Utility Methods
    # =========================================================================
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        logger.info("Configuration reloaded")

    def get_raw_config(self) -> Dict[str, Any]:
        """Get raw configuration dictionary"""
        return self.config

    def print_summary(self, strategy: Optional[str] = None):
        """
        Print configuration summary

        Args:
            strategy: Strategy name. If None, uses active strategy.
        """
        if strategy is None:
            strategy = self.get_active_strategy()

        print("\n" + "="*80)
        print(f"STRATEGY SIGNAL CONFIGURATION SUMMARY - {strategy.upper()}")
        print("="*80)

        config = self.get_strategy_config(strategy)
        print(f"\nStrategy: {config.get('name', strategy)}")
        print(f"Description: {config.get('description', 'N/A')}")

        # Earnings
        print("\n[Earnings Signal]")
        print(f"  Enabled: {self.is_earnings_enabled(strategy)}")
        print(f"  Min Prev Revenue YoY: {self.get_earnings_revenue_min_prev_yoy(strategy)*100:.1f}%")
        print(f"  Min Prev EPS YoY: {self.get_earnings_eps_min_prev_yoy(strategy)*100:.1f}%")

        # Fundamental
        print("\n[Fundamental Signal]")
        print(f"  Enabled: {self.is_fundamental_enabled(strategy)}")
        print(f"  Min Market Cap: ${self.get_fundamental_market_cap_min(strategy):,}")
        print(f"  Max Market Cap: ${self.get_fundamental_market_cap_max(strategy):,}")
        print(f"  Min Revenue YoY: {self.get_fundamental_revenue_min_yoy(strategy)*100:.1f}%")
        print(f"  Min EPS YoY: {self.get_fundamental_eps_min_yoy(strategy)*100:.1f}%")

        # Weekly
        print("\n[Weekly Signal]")
        print(f"  Enabled: {self.is_weekly_enabled(strategy)}")
        print(f"  High Stability Factor: {self.get_weekly_high_stability_factor(strategy)}")
        print(f"  Low Distance Factor: {self.get_weekly_low_distance_factor(strategy)}")
        print(f"  High Distance Factor: {self.get_weekly_high_distance_factor(strategy)}")

        # RS
        print("\n[RS Signal]")
        print(f"  Enabled: {self.is_rs_enabled(strategy)}")
        print(f"  Threshold: {self.get_rs_threshold(strategy)}")
        print(f"  Use T-1 Data: {self.get_rs_use_t_minus_1(strategy)}")

        # Daily
        print("\n[Daily Signal]")
        print(f"  Enabled: {self.is_daily_enabled(strategy)}")
        print(f"  RS Threshold: {self.get_daily_rs_threshold(strategy)}")
        print(f"  Losscut Ratio: {self.get_daily_losscut_ratio(strategy)}")
        print(f"  Breakout Timeframes: {self.get_daily_breakout_timeframes(strategy)}")

        # Thresholds
        print("\n[Thresholds]")
        for stage, threshold in self.get_all_thresholds(strategy).items():
            print(f"  {stage}: {threshold}")

        print("\n" + "="*80)

    def print_all_strategies(self):
        """Print summary of all strategies"""
        strategies = self.list_strategies()
        active = self.get_active_strategy()

        print("\n" + "="*80)
        print("ALL AVAILABLE STRATEGIES")
        print("="*80)

        for strategy in strategies:
            marker = " [ACTIVE]" if strategy == active else ""
            print(f"\n{strategy.upper()}{marker}")
            print("-" * 40)

            config = self.get_strategy_config(strategy)
            print(f"Name: {config.get('name', 'N/A')}")
            print(f"Description: {config.get('description', 'N/A')}")
            print(f"MarketCap: ${self.get_fundamental_market_cap_min(strategy)/1e9:.1f}B+")
            print(f"REV YoY: {self.get_fundamental_revenue_min_yoy(strategy)*100:.0f}%+")
            print(f"RS Threshold: {self.get_rs_threshold(strategy)}")
            print(f"Losscut: {(1-self.get_daily_losscut_ratio(strategy))*100:.0f}%")

        print("\n" + "="*80)


# =============================================================================
# Example Usage
# =============================================================================
if __name__ == "__main__":
    # Create config loader
    config = StrategySignalConfigLoader()

    # Print all strategies
    config.print_all_strategies()

    # Print active strategy details
    print(f"\n\nActive Strategy: {config.get_active_strategy()}")
    config.print_summary()

    # Example: Get specific values from active strategy
    print("\n" + "="*80)
    print("EXAMPLE USAGE - Active Strategy")
    print("="*80)

    print(f"\nFundamental - Min Market Cap: ${config.get_fundamental_market_cap_min():,}")
    print(f"Fundamental - Min Revenue YoY: {config.get_fundamental_revenue_min_yoy()*100:.1f}%")
    print(f"Weekly - High Stability Factor: {config.get_weekly_high_stability_factor()}")
    print(f"RS - Threshold: {config.get_rs_threshold()}")
    print(f"Daily - Losscut Ratio: {config.get_daily_losscut_ratio()}")

    # Example: Get values from specific strategy
    print("\n" + "="*80)
    print("EXAMPLE USAGE - Conservative Strategy")
    print("="*80)

    print(f"\nFundamental - Min Market Cap: ${config.get_fundamental_market_cap_min('conservative'):,}")
    print(f"Fundamental - Min Revenue YoY: {config.get_fundamental_revenue_min_yoy('conservative')*100:.1f}%")
    print(f"RS - Threshold: {config.get_rs_threshold('conservative')}")
