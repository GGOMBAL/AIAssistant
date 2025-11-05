"""
Indicator Calculator - Database Agent Management

Calculates technical indicators for DataFrames.
Automatically detects missing indicators and calculates them.

Owner: Database Agent
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any

try:
    from project.database.indicator_registry_manager import IndicatorRegistryManager
except ImportError:
    IndicatorRegistryManager = None

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """
    Calculates technical indicators on DataFrames

    Responsibilities:
    - Detect required indicators from strategy
    - Check which indicators are missing
    - Calculate missing indicators
    - Add calculated indicators to DataFrame
    - Use registry to find calculation methods
    """

    def __init__(self, registry_manager: Optional['IndicatorRegistryManager'] = None):
        """
        Initialize Indicator Calculator

        Args:
            registry_manager: Registry manager instance (optional)
        """
        self.registry_manager = registry_manager

        logger.info("Initialized IndicatorCalculator")

    def calculate_missing_indicators(self,
                                     df: pd.DataFrame,
                                     required_indicators: List[str],
                                     inplace: bool = False) -> Tuple[pd.DataFrame, List[str]]:
        """
        Calculate missing indicators and add them to DataFrame

        Args:
            df: DataFrame with OHLCV data
            required_indicators: List of required indicator names
            inplace: If True, modify df in place

        Returns:
            Tuple of (updated_dataframe, list_of_calculated_indicators)
        """
        if not inplace:
            df = df.copy()

        calculated = []
        failed = []

        # Check which indicators are missing
        missing = [ind for ind in required_indicators if ind not in df.columns]

        if not missing:
            logger.info("All required indicators already present")
            return df, []

        logger.info(f"Missing indicators: {missing}")

        # Calculate each missing indicator
        for indicator_name in missing:
            success = self._calculate_single_indicator(df, indicator_name)

            if success:
                calculated.append(indicator_name)
                logger.info(f"[OK] Calculated: {indicator_name}")
            else:
                failed.append(indicator_name)
                logger.warning(f"[FAILED] Could not calculate: {indicator_name}")

        if failed:
            logger.warning(f"Failed to calculate {len(failed)} indicators: {failed}")

        return df, calculated

    def _calculate_single_indicator(self, df: pd.DataFrame, indicator_name: str) -> bool:
        """
        Calculate a single indicator

        Args:
            df: DataFrame (modified in place)
            indicator_name: Indicator name (e.g., "RSI_14", "SMA_20")

        Returns:
            True if successful
        """
        try:
            # Try to parse indicator name and parameters
            indicator_type, params = self._parse_indicator_name(indicator_name)

            # Route to appropriate calculation method
            if indicator_type == "RSI":
                return self._calculate_rsi(df, indicator_name, params)

            elif indicator_type == "SMA":
                return self._calculate_sma(df, indicator_name, params)

            elif indicator_type == "EMA":
                return self._calculate_ema(df, indicator_name, params)

            elif indicator_type == "MACD":
                return self._calculate_macd(df, indicator_name, params)

            elif indicator_type == "ATR":
                return self._calculate_atr(df, indicator_name, params)

            elif indicator_type in ["Highest", "Rolling_High"]:
                return self._calculate_rolling_high(df, indicator_name, params)

            elif indicator_type in ["Lowest", "Rolling_Low"]:
                return self._calculate_rolling_low(df, indicator_name, params)

            elif indicator_type == "BB":  # Bollinger Bands
                return self._calculate_bollinger_bands(df, indicator_name, params)

            elif indicator_type == "Volume_SMA":
                return self._calculate_volume_sma(df, indicator_name, params)

            else:
                # Try to find in registry
                logger.warning(f"Unknown indicator type: {indicator_type}")
                return False

        except Exception as e:
            logger.error(f"Error calculating {indicator_name}: {e}")
            return False

    def _parse_indicator_name(self, indicator_name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse indicator name to extract type and parameters

        Examples:
        - "RSI_14" -> ("RSI", {"period": 14})
        - "SMA_20" -> ("SMA", {"period": 20})
        - "MACD_12_26_9" -> ("MACD", {"fast": 12, "slow": 26, "signal": 9})

        Args:
            indicator_name: Indicator name string

        Returns:
            Tuple of (indicator_type, parameters_dict)
        """
        parts = indicator_name.split('_')

        if len(parts) == 0:
            return indicator_name, {}

        indicator_type = parts[0]
        params = {}

        # Extract numeric parameters
        numeric_parts = [p for p in parts[1:] if p.isdigit()]

        if indicator_type in ["RSI", "SMA", "EMA", "ATR"]:
            if numeric_parts:
                params["period"] = int(numeric_parts[0])

        elif indicator_type == "MACD":
            if len(numeric_parts) >= 3:
                params["fast_period"] = int(numeric_parts[0])
                params["slow_period"] = int(numeric_parts[1])
                params["signal_period"] = int(numeric_parts[2])

        elif indicator_type in ["Highest", "Rolling", "Lowest"]:
            # Handle "Highest_1M" -> period=20
            if "1M" in indicator_name:
                params["period"] = 20
            elif "3M" in indicator_name:
                params["period"] = 60
            elif numeric_parts:
                params["period"] = int(numeric_parts[0])

        elif indicator_type == "Volume":
            # Handle "Volume_SMA_20"
            if "SMA" in parts and numeric_parts:
                indicator_type = "Volume_SMA"
                params["period"] = int(numeric_parts[0])

        return indicator_type, params

    def _calculate_rsi(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate RSI"""
        period = params.get("period", 14)

        if 'close' not in df.columns:
            return False

        # Calculate RSI
        delta = df['close'].diff()
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        avg_gain = gains.ewm(com=period - 1, adjust=False, min_periods=period).mean()
        avg_loss = losses.ewm(com=period - 1, adjust=False, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        df[col_name] = rsi.fillna(50)
        return True

    def _calculate_sma(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate SMA"""
        period = params.get("period", 20)

        if 'close' not in df.columns:
            return False

        df[col_name] = df['close'].rolling(window=period, min_periods=period).mean()
        return True

    def _calculate_ema(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate EMA"""
        period = params.get("period", 20)

        if 'close' not in df.columns:
            return False

        df[col_name] = df['close'].ewm(span=period, adjust=False, min_periods=period).mean()
        return True

    def _calculate_macd(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate MACD"""
        fast = params.get("fast_period", 12)
        slow = params.get("slow_period", 26)
        signal_period = params.get("signal_period", 9)

        if 'close' not in df.columns:
            return False

        # Calculate EMAs
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        # Add MACD components
        df[f"MACD_{fast}_{slow}_{signal_period}"] = macd_line
        df[f"MACD_Signal_{fast}_{slow}_{signal_period}"] = signal_line
        df[f"MACD_Hist_{fast}_{slow}_{signal_period}"] = histogram

        # If col_name is just "MACD", use the main line
        if col_name == "MACD" or col_name == f"MACD_{fast}_{slow}_{signal_period}":
            df[col_name] = macd_line

        return True

    def _calculate_atr(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate ATR"""
        period = params.get("period", 14)

        required_cols = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return False

        # Calculate True Range
        prev_close = df['close'].shift(1)
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - prev_close).abs()
        tr3 = (df['low'] - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR as EMA of True Range
        df[col_name] = true_range.ewm(span=period, adjust=False, min_periods=period).mean()

        return True

    def _calculate_rolling_high(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate Rolling High"""
        period = params.get("period", 20)

        if 'high' not in df.columns:
            return False

        df[col_name] = df['high'].rolling(window=period, min_periods=period).max()
        return True

    def _calculate_rolling_low(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate Rolling Low"""
        period = params.get("period", 20)

        if 'low' not in df.columns:
            return False

        df[col_name] = df['low'].rolling(window=period, min_periods=period).min()
        return True

    def _calculate_bollinger_bands(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate Bollinger Bands"""
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2)

        if 'close' not in df.columns:
            return False

        # Calculate middle band (SMA)
        middle = df['close'].rolling(window=period, min_periods=period).mean()

        # Calculate standard deviation
        std = df['close'].rolling(window=period, min_periods=period).std()

        # Calculate upper and lower bands
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        # Add BB components
        df[f"BB_Middle_{period}"] = middle
        df[f"BB_Upper_{period}"] = upper
        df[f"BB_Lower_{period}"] = lower

        # If col_name is a specific band, use it
        if "Upper" in col_name:
            df[col_name] = upper
        elif "Lower" in col_name:
            df[col_name] = lower
        elif "Middle" in col_name:
            df[col_name] = middle

        return True

    def _calculate_volume_sma(self, df: pd.DataFrame, col_name: str, params: Dict) -> bool:
        """Calculate Volume SMA"""
        period = params.get("period", 20)

        if 'volume' not in df.columns:
            return False

        df[col_name] = df['volume'].rolling(window=period, min_periods=period).mean()
        return True

    def get_required_columns(self, indicator_name: str) -> List[str]:
        """
        Get required DataFrame columns for an indicator

        Args:
            indicator_name: Indicator name

        Returns:
            List of required column names
        """
        indicator_type, _ = self._parse_indicator_name(indicator_name)

        column_requirements = {
            "RSI": ["close"],
            "SMA": ["close"],
            "EMA": ["close"],
            "MACD": ["close"],
            "ATR": ["high", "low", "close"],
            "Highest": ["high"],
            "Rolling_High": ["high"],
            "Lowest": ["low"],
            "Rolling_Low": ["low"],
            "BB": ["close"],
            "Volume_SMA": ["volume"]
        }

        return column_requirements.get(indicator_type, ["close"])


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test calculator
    calculator = IndicatorCalculator()

    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(100) * 2),
        'high': 102 + np.cumsum(np.random.randn(100) * 2),
        'low': 98 + np.cumsum(np.random.randn(100) * 2),
        'close': 100 + np.cumsum(np.random.randn(100) * 2),
        'volume': 1000000 + np.random.randint(-100000, 100000, 100)
    }, index=dates)

    print("=" * 60)
    print("INDICATOR CALCULATOR TEST")
    print("=" * 60)
    print(f"Original columns: {list(df.columns)}")

    # Test calculating missing indicators
    required = ["RSI_14", "SMA_20", "SMA_50", "EMA_12", "Volume_SMA_20", "ATR_14"]

    df, calculated = calculator.calculate_missing_indicators(df, required)

    print(f"\nRequired indicators: {required}")
    print(f"Calculated: {calculated}")
    print(f"Final columns: {list(df.columns)}")

    # Verify calculations
    print(f"\nSample values (last 5 rows):")
    print(df[['close'] + calculated].tail())

    print("=" * 60)
