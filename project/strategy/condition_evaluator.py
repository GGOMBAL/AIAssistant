"""
Condition Evaluator - Strategy Agent Management

Evaluates strategy conditions against DataFrame data.
Supports advanced operators and complex logical expressions.

Owner: Strategy Agent
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Union

from project.strategy.yaml_strategy_loader import (
    ConditionRule, ConditionGroup, LoadedStrategy
)

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """
    Evaluates strategy conditions against DataFrame

    Supports:
    - Basic comparison operators (>, <, ==, !=, >=, <=)
    - Special operators (crosses_above, crosses_below, between, in_list)
    - Dynamic references (compare indicator to another column)
    - Multipliers (reference * multiplier)
    - Functions (rolling_mean, etc.)
    - Logical operators (AND, OR, NOT)
    """

    def __init__(self):
        """Initialize Condition Evaluator"""
        logger.info("Initialized ConditionEvaluator")

    def evaluate_entry_conditions(self, strategy: LoadedStrategy,
                                  df: pd.DataFrame) -> pd.Series:
        """
        Evaluate all entry conditions for a strategy

        Args:
            strategy: Loaded strategy object
            df: DataFrame with OHLCV and indicator data

        Returns:
            Boolean Series indicating where entry conditions are met
        """
        if not strategy.entry or not strategy.entry.conditions:
            logger.warning("No entry conditions defined")
            return pd.Series(False, index=df.index)

        # Evaluate each condition group
        group_results = {}
        for group in strategy.entry.conditions:
            group_result = self.evaluate_condition_group(group, df)
            group_results[group.group] = group_result

        # Combine groups using logic expression
        if strategy.entry.logic:
            result = self._evaluate_logic_expression(
                strategy.entry.logic,
                group_results,
                df.index
            )
        else:
            # Default: AND all groups
            result = pd.Series(True, index=df.index)
            for group_result in group_results.values():
                result = result & group_result

        return result

    def evaluate_condition_group(self, group: ConditionGroup,
                                 df: pd.DataFrame) -> pd.Series:
        """
        Evaluate a single condition group

        Args:
            group: Condition group to evaluate
            df: DataFrame

        Returns:
            Boolean Series for this group
        """
        if not group.rules:
            return pd.Series(True, index=df.index)

        # Evaluate each rule
        rule_results = []
        for rule in group.rules:
            rule_result = self.evaluate_rule(rule, df)
            rule_results.append(rule_result)

        # Combine rules using group operator
        if group.operator == "AND":
            result = rule_results[0]
            for r in rule_results[1:]:
                result = result & r
        elif group.operator == "OR":
            result = rule_results[0]
            for r in rule_results[1:]:
                result = result | r
        elif group.operator == "NOT":
            # NOT of first rule
            result = ~rule_results[0]
        else:
            logger.error(f"Unknown group operator: {group.operator}")
            result = pd.Series(False, index=df.index)

        return result

    def evaluate_rule(self, rule: ConditionRule, df: pd.DataFrame) -> pd.Series:
        """
        Evaluate a single condition rule

        Args:
            rule: Condition rule
            df: DataFrame

        Returns:
            Boolean Series for this rule
        """
        try:
            # Get indicator/column value
            if rule.indicator not in df.columns:
                logger.warning(f"Column '{rule.indicator}' not found in DataFrame")
                return pd.Series(False, index=df.index)

            indicator_series = df[rule.indicator]

            # Apply offset if specified
            if rule.offset:
                indicator_series = indicator_series.shift(rule.offset)

            # Get comparison value
            if rule.reference:
                # Compare to another column
                comparison_value = self._get_reference_value(rule, df)
            elif rule.value is not None:
                # Compare to fixed value
                comparison_value = rule.value
            else:
                logger.warning(f"Rule has no value or reference: {rule}")
                return pd.Series(False, index=df.index)

            # Evaluate based on operator
            result = self._apply_operator(
                indicator_series,
                rule.operator,
                comparison_value,
                rule
            )

            return result

        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return pd.Series(False, index=df.index)

    def _get_reference_value(self, rule: ConditionRule, df: pd.DataFrame) -> Union[pd.Series, float]:
        """
        Get reference value (with optional function and multiplier)

        Args:
            rule: Condition rule
            df: DataFrame

        Returns:
            Series or scalar value for comparison
        """
        if rule.reference not in df.columns:
            logger.warning(f"Reference column '{rule.reference}' not found")
            return 0

        ref_series = df[rule.reference]

        # Apply function if specified
        if rule.function:
            ref_series = self._apply_function(ref_series, rule.function, rule.function_params)

        # Apply multiplier if specified
        if rule.multiplier:
            ref_series = ref_series * rule.multiplier

        return ref_series

    def _apply_function(self, series: pd.Series, function: str,
                       params: Optional[Dict] = None) -> pd.Series:
        """
        Apply function to series

        Args:
            series: Input series
            function: Function name
            params: Function parameters

        Returns:
            Transformed series
        """
        params = params or {}

        try:
            if function == "rolling_mean":
                window = params.get('window', 20)
                return series.rolling(window=window).mean()

            elif function == "rolling_std":
                window = params.get('window', 20)
                return series.rolling(window=window).std()

            elif function == "rolling_max":
                window = params.get('window', 20)
                return series.rolling(window=window).max()

            elif function == "rolling_min":
                window = params.get('window', 20)
                return series.rolling(window=window).min()

            elif function == "ewm":
                span = params.get('span', 20)
                return series.ewm(span=span).mean()

            else:
                logger.warning(f"Unknown function: {function}")
                return series

        except Exception as e:
            logger.error(f"Error applying function {function}: {e}")
            return series

    def _apply_operator(self, left: pd.Series, operator: str,
                       right: Union[pd.Series, float],
                       rule: ConditionRule) -> pd.Series:
        """
        Apply comparison operator

        Args:
            left: Left side (indicator)
            operator: Comparison operator
            right: Right side (value or reference)
            rule: Original rule (for special operators)

        Returns:
            Boolean Series
        """
        try:
            # Basic comparison operators
            if operator == ">":
                return left > right
            elif operator == ">=":
                return left >= right
            elif operator == "<":
                return left < right
            elif operator == "<=":
                return left <= right
            elif operator == "==":
                return left == right
            elif operator == "!=":
                return left != right

            # Special operators
            elif operator == "crosses_above":
                return self._crosses_above(left, right, rule.lookback or 1)

            elif operator == "crosses_below":
                return self._crosses_below(left, right, rule.lookback or 1)

            elif operator == "between":
                # Expect right to be [min, max]
                if isinstance(right, (list, tuple)) and len(right) == 2:
                    return (left >= right[0]) & (left <= right[1])
                else:
                    logger.warning("between operator requires [min, max] list")
                    return pd.Series(False, index=left.index)

            elif operator == "in_list":
                # Expect right to be list of values
                if isinstance(right, (list, tuple)):
                    return left.isin(right)
                else:
                    return left == right

            else:
                logger.warning(f"Unknown operator: {operator}")
                return pd.Series(False, index=left.index)

        except Exception as e:
            logger.error(f"Error applying operator {operator}: {e}")
            return pd.Series(False, index=left.index)

    def _crosses_above(self, series: pd.Series, threshold: Union[pd.Series, float],
                      lookback: int = 1) -> pd.Series:
        """
        Check if series crosses above threshold

        Args:
            series: Time series
            threshold: Threshold value or series
            lookback: Number of periods to look back

        Returns:
            Boolean Series where crossover occurred
        """
        # Current value is above threshold
        above = series > threshold

        # Previous value was below threshold
        below_before = series.shift(lookback) <= threshold

        # Crossover = currently above AND was below before
        crossover = above & below_before

        return crossover

    def _crosses_below(self, series: pd.Series, threshold: Union[pd.Series, float],
                      lookback: int = 1) -> pd.Series:
        """
        Check if series crosses below threshold

        Args:
            series: Time series
            threshold: Threshold value or series
            lookback: Number of periods to look back

        Returns:
            Boolean Series where crossover occurred
        """
        # Current value is below threshold
        below = series < threshold

        # Previous value was above threshold
        above_before = series.shift(lookback) >= threshold

        # Crossover = currently below AND was above before
        crossover = below & above_before

        return crossover

    def _evaluate_logic_expression(self, logic: str,
                                   group_results: Dict[str, pd.Series],
                                   index: pd.Index) -> pd.Series:
        """
        Evaluate logic expression combining groups

        Args:
            logic: Logic expression (e.g., "group1 AND group2")
            group_results: Dictionary mapping group names to boolean Series
            index: DataFrame index

        Returns:
            Combined boolean Series
        """
        # Replace group names with temporary variables
        expression = logic
        for i, group_name in enumerate(group_results.keys()):
            # Replace group_name with g{i}
            expression = expression.replace(group_name, f"g{i}")

        # Prepare variables for eval
        eval_vars = {}
        for i, (group_name, result) in enumerate(group_results.items()):
            eval_vars[f"g{i}"] = result

        # Replace logical operators
        expression = expression.replace(" AND ", " & ")
        expression = expression.replace(" OR ", " | ")
        expression = expression.replace(" NOT ", " ~ ")

        try:
            # Evaluate expression
            result = eval(expression, {}, eval_vars)
            return result
        except Exception as e:
            logger.error(f"Error evaluating logic expression '{logic}': {e}")
            return pd.Series(False, index=index)

    def evaluate_filters(self, filters: List, df: pd.DataFrame) -> pd.Series:
        """
        Evaluate filter rules

        Args:
            filters: List of FilterRule objects
            df: DataFrame

        Returns:
            Boolean Series where all filters pass
        """
        if not filters:
            return pd.Series(True, index=df.index)

        result = pd.Series(True, index=df.index)

        for filter_rule in filters:
            # Convert FilterRule to ConditionRule for evaluation
            rule = ConditionRule(
                indicator=filter_rule.indicator,
                operator=filter_rule.operator,
                value=filter_rule.value,
                reference=filter_rule.reference,
                multiplier=filter_rule.multiplier,
                description=filter_rule.description
            )

            filter_result = self.evaluate_rule(rule, df)
            result = result & filter_result

        return result

    def evaluate_exit_conditions(self, strategy: LoadedStrategy,
                                 df: pd.DataFrame,
                                 position_info: Optional[Dict] = None) -> Dict[str, pd.Series]:
        """
        Evaluate exit conditions

        Args:
            strategy: Loaded strategy
            df: DataFrame
            position_info: Optional position information (for profit target, stop loss)

        Returns:
            Dictionary with exit signals for each type
        """
        exit_signals = {}

        if not strategy.exit:
            return exit_signals

        # Signal-based exit
        if strategy.exit.signal_exit and strategy.exit.signal_exit.get('enabled'):
            signal_exit = pd.Series(False, index=df.index)

            for group in strategy.exit.signal_exit['conditions']:
                group_result = self.evaluate_condition_group(group, df)
                signal_exit = signal_exit | group_result  # OR logic for exit groups

            exit_signals['signal_exit'] = signal_exit

        # Profit target and stop loss would be evaluated differently
        # (require position entry price, which comes from position manager)

        return exit_signals


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test evaluator with sample data
    from project.strategy.yaml_strategy_loader import YAMLStrategyLoader
    from pathlib import Path

    # Load strategy
    loader = YAMLStrategyLoader()
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    success, strategy, errors = loader.load_from_file(str(yaml_path))

    if success and strategy:
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'close': 100 + np.cumsum(np.random.randn(100) * 2),
            'high': 102 + np.cumsum(np.random.randn(100) * 2),
            'low': 98 + np.cumsum(np.random.randn(100) * 2),
            'volume': 1000000 + np.random.randint(-100000, 100000, 100)
        }, index=dates)

        # Add mock indicators
        df['RSI_14'] = 50 + np.random.randn(100) * 15
        df['SMA_20'] = df['close'].rolling(20).mean()
        df['SMA_50'] = df['close'].rolling(50).mean()
        df['Volume_SMA_20'] = df['volume'].rolling(20).mean()
        df['RS_Rating'] = 50 + np.random.randn(100) * 20

        # Evaluate conditions
        evaluator = ConditionEvaluator()

        # Test entry conditions
        entry_signals = evaluator.evaluate_entry_conditions(strategy, df)
        print("=" * 60)
        print("CONDITION EVALUATOR TEST")
        print("=" * 60)
        print(f"Total periods: {len(df)}")
        print(f"Entry signals: {entry_signals.sum()}")
        print(f"Entry rate: {entry_signals.sum() / len(df) * 100:.1f}%")

        # Test filters
        filter_result = evaluator.evaluate_filters(strategy.filters, df)
        print(f"\nFilter pass: {filter_result.sum()}")
        print(f"Filter pass rate: {filter_result.sum() / len(df) * 100:.1f}%")

        # Combined (entry AND filters)
        final_signals = entry_signals & filter_result
        print(f"\nFinal signals (entry AND filters): {final_signals.sum()}")
        print(f"Final signal rate: {final_signals.sum() / len(df) * 100:.1f}%")

        if final_signals.sum() > 0:
            print(f"\nSignal dates:")
            signal_dates = df[final_signals].index.tolist()
            for date in signal_dates[:5]:  # Show first 5
                print(f"  - {date.strftime('%Y-%m-%d')}")
            if len(signal_dates) > 5:
                print(f"  ... and {len(signal_dates) - 5} more")

        print("=" * 60)
    else:
        print("[FAILED] Could not load strategy")
