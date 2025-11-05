"""
Strategy Validator - Strategy Agent Management

Validates YAML strategy files against JSON schema and business logic rules.
Ensures strategy definitions are correct before execution.

Owner: Strategy Agent
"""

import yaml
import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyValidator:
    """
    Validates strategy YAML files against schema and business rules.

    Responsibilities:
    - Load and parse YAML files
    - Validate against JSON schema
    - Check business logic constraints
    - Provide detailed error messages with line numbers
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize Strategy Validator

        Args:
            schema_path: Path to JSON schema file. If None, uses default.
        """
        if schema_path is None:
            # Default schema path
            project_root = Path(__file__).parent.parent.parent
            schema_path = project_root / "config" / "schemas" / "strategy_schema.json"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

        logger.info(f"Initialized StrategyValidator with schema: {self.schema_path}")

    def _load_schema(self) -> Dict:
        """
        Load JSON schema from file

        Returns:
            Schema dictionary
        """
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            logger.info(f"Loaded JSON schema from {self.schema_path}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema from {self.schema_path}: {e}")
            raise

    def validate_file(self, yaml_path: str) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Validate a YAML strategy file

        Args:
            yaml_path: Path to YAML file

        Returns:
            Tuple of (is_valid, error_messages, parsed_strategy)
        """
        errors = []

        # Step 1: Load YAML file
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                strategy = yaml.safe_load(f)
            logger.info(f"Successfully loaded YAML from {yaml_path}")
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {e}"
            logger.error(error_msg)
            return False, [error_msg], None
        except FileNotFoundError:
            error_msg = f"File not found: {yaml_path}"
            logger.error(error_msg)
            return False, [error_msg], None
        except Exception as e:
            error_msg = f"Error loading file {yaml_path}: {e}"
            logger.error(error_msg)
            return False, [error_msg], None

        # Step 2: Validate against JSON schema
        is_valid, schema_errors = self._validate_schema(strategy)
        if not is_valid:
            errors.extend(schema_errors)

        # Step 3: Validate business logic (even if schema validation failed)
        business_errors = self._validate_business_logic(strategy)
        errors.extend(business_errors)

        # Step 4: Validate indicator references
        indicator_errors = self._validate_indicators(strategy)
        errors.extend(indicator_errors)

        # Step 5: Validate date ranges
        date_errors = self._validate_dates(strategy)
        errors.extend(date_errors)

        # Determine overall validity
        is_valid = len(errors) == 0

        if is_valid:
            logger.info(f"[OK] Strategy validation passed: {yaml_path}")
        else:
            logger.warning(f"[FAILED] Strategy validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")

        return is_valid, errors, strategy if is_valid else None

    def _validate_schema(self, strategy: Dict) -> Tuple[bool, List[str]]:
        """
        Validate strategy against JSON schema

        Args:
            strategy: Parsed strategy dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            jsonschema.validate(instance=strategy, schema=self.schema)
            logger.debug("JSON schema validation passed")
            return True, []
        except jsonschema.ValidationError as e:
            # Format validation error with path
            path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            error_msg = f"Schema validation error at '{path}': {e.message}"
            errors.append(error_msg)
            logger.debug(f"Schema validation error: {error_msg}")
            return False, errors
        except jsonschema.SchemaError as e:
            error_msg = f"Invalid schema definition: {e.message}"
            errors.append(error_msg)
            logger.error(f"Schema error: {error_msg}")
            return False, errors
        except Exception as e:
            error_msg = f"Unexpected validation error: {e}"
            errors.append(error_msg)
            logger.error(f"Validation error: {error_msg}")
            return False, errors

    def _validate_business_logic(self, strategy: Dict) -> List[str]:
        """
        Validate business logic constraints

        Args:
            strategy: Parsed strategy dictionary

        Returns:
            List of error messages
        """
        errors = []

        # Check 1: Entry logic references valid groups
        if 'entry' in strategy:
            entry = strategy['entry']

            # Get all group names from conditions
            if 'conditions' in entry:
                group_names = {cond['group'] for cond in entry['conditions'] if 'group' in cond}

                # Parse logic expression and check group references
                if 'logic' in entry:
                    logic_expr = entry['logic']
                    # Simple check: ensure all words in logic are group names or operators
                    logic_words = logic_expr.replace('(', ' ').replace(')', ' ').split()
                    for word in logic_words:
                        if word not in ['AND', 'OR', 'NOT'] and word not in group_names:
                            errors.append(
                                f"Entry logic references undefined group '{word}'. "
                                f"Available groups: {', '.join(sorted(group_names))}"
                            )

        # Check 2: Exit signal logic (if exists)
        if 'exit' in strategy and 'signal_exit' in strategy['exit']:
            signal_exit = strategy['exit']['signal_exit']
            if signal_exit.get('enabled') and 'conditions' in signal_exit:
                # Ensure at least one condition exists
                if len(signal_exit['conditions']) == 0:
                    errors.append("Exit signal_exit is enabled but has no conditions")

        # Check 3: Risk management constraints
        if 'risk_management' in strategy:
            risk = strategy['risk_management']

            # Portfolio risk should be >= position risk
            if 'max_portfolio_risk' in risk and 'max_position_size' in risk:
                if risk['max_position_size'] > risk['max_portfolio_risk']:
                    errors.append(
                        f"max_position_size ({risk['max_position_size']}) cannot exceed "
                        f"max_portfolio_risk ({risk['max_portfolio_risk']})"
                    )

            # Position sizing base_risk should be reasonable
            if 'position_sizing' in risk and 'base_risk' in risk['position_sizing']:
                base_risk = risk['position_sizing']['base_risk']
                if base_risk > 0.10:  # 10% is very aggressive
                    errors.append(
                        f"Warning: base_risk ({base_risk*100:.1f}%) is very high. "
                        f"Recommended: <= 10%"
                    )

        # Check 4: Entry constraints consistency
        if 'entry' in strategy and 'constraints' in strategy['entry']:
            constraints = strategy['entry']['constraints']

            if 'max_positions' in constraints and 'risk_per_trade' in constraints:
                max_pos = constraints['max_positions']
                risk_per = constraints['risk_per_trade']

                # Total max risk = max_positions * risk_per_trade
                total_risk = max_pos * risk_per

                if total_risk > 1.0:
                    errors.append(
                        f"Warning: max_positions ({max_pos}) * risk_per_trade ({risk_per}) = "
                        f"{total_risk:.1f} exceeds 100% of capital"
                    )

        # Check 5: Backtest date range
        if 'backtest' in strategy:
            backtest = strategy['backtest']

            if 'start_date' in backtest and 'end_date' in backtest:
                try:
                    start = datetime.strptime(backtest['start_date'], '%Y-%m-%d')
                    end = datetime.strptime(backtest['end_date'], '%Y-%m-%d')

                    if start >= end:
                        errors.append(
                            f"Backtest start_date ({backtest['start_date']}) must be before "
                            f"end_date ({backtest['end_date']})"
                        )

                    # Warn if backtest period is very short
                    days = (end - start).days
                    if days < 365:
                        errors.append(
                            f"Warning: Backtest period is only {days} days. "
                            f"Recommended: >= 1 year for reliable results"
                        )
                except ValueError as e:
                    errors.append(f"Invalid date format in backtest section: {e}")

        return errors

    def _validate_indicators(self, strategy: Dict) -> List[str]:
        """
        Validate indicator references and parameters

        Args:
            strategy: Parsed strategy dictionary

        Returns:
            List of error messages
        """
        errors = []

        if 'indicators' not in strategy:
            return errors

        # Get all defined indicator output columns
        defined_indicators = set()
        for ind in strategy['indicators']:
            if 'output_column' in ind:
                defined_indicators.add(ind['output_column'])

        # Check entry conditions reference valid indicators
        if 'entry' in strategy and 'conditions' in strategy['entry']:
            for cond_group in strategy['entry']['conditions']:
                if 'rules' in cond_group:
                    for rule in cond_group['rules']:
                        # Check indicator field
                        if 'indicator' in rule:
                            ind_name = rule['indicator']
                            # Allow built-in columns (close, high, low, volume)
                            builtin = {'close', 'open', 'high', 'low', 'volume', 'Dclose', 'Dhigh', 'Dlow', 'Dvolume'}
                            if ind_name not in defined_indicators and ind_name not in builtin:
                                # Check if it's a common indicator that might exist in data
                                common_indicators = {'RS_Rating', 'RS_4W'}
                                if ind_name not in common_indicators:
                                    errors.append(
                                        f"Entry condition references undefined indicator '{ind_name}'. "
                                        f"Defined indicators: {', '.join(sorted(defined_indicators))}"
                                    )

                        # Check reference field
                        if 'reference' in rule:
                            ref_name = rule['reference']
                            builtin = {'close', 'open', 'high', 'low', 'volume', 'Dclose', 'Dhigh', 'Dlow', 'Dvolume'}
                            if ref_name not in defined_indicators and ref_name not in builtin:
                                common_indicators = {'Volume_SMA_20'}
                                if ref_name not in common_indicators:
                                    errors.append(
                                        f"Entry condition references undefined reference '{ref_name}'"
                                    )

        # Check exit conditions
        if 'exit' in strategy and 'signal_exit' in strategy['exit']:
            signal_exit = strategy['exit']['signal_exit']
            if 'conditions' in signal_exit:
                for cond_group in signal_exit['conditions']:
                    if 'rules' in cond_group:
                        for rule in cond_group['rules']:
                            if 'indicator' in rule:
                                ind_name = rule['indicator']
                                builtin = {'close', 'open', 'high', 'low', 'volume'}
                                if ind_name not in defined_indicators and ind_name not in builtin:
                                    errors.append(
                                        f"Exit condition references undefined indicator '{ind_name}'"
                                    )

        # Check filters
        if 'filters' in strategy:
            for filter_rule in strategy['filters']:
                if 'indicator' in filter_rule:
                    ind_name = filter_rule['indicator']
                    builtin = {'close', 'open', 'high', 'low', 'volume'}
                    common_indicators = {
                        'RS_Rating', 'avg_dollar_volume_20d',
                        # Fundamental data columns (from external data sources)
                        'market_cap', 'revenue_yoy', 'eps_yoy',
                        'revenue_prev_yoy', 'eps_prev_yoy',
                        'revenue_qoq', 'eps_qoq'
                    }
                    if (ind_name not in defined_indicators and
                        ind_name not in builtin and
                        ind_name not in common_indicators):
                        errors.append(
                            f"Filter '{filter_rule.get('name', 'unnamed')}' references "
                            f"undefined indicator '{ind_name}'"
                        )

        return errors

    def _validate_dates(self, strategy: Dict) -> List[str]:
        """
        Validate date ranges and formats

        Args:
            strategy: Parsed strategy dictionary

        Returns:
            List of error messages
        """
        errors = []

        # Check strategy creation date
        if 'strategy' in strategy and 'created' in strategy['strategy']:
            try:
                datetime.strptime(strategy['strategy']['created'], '%Y-%m-%d')
            except ValueError:
                errors.append(
                    f"Invalid date format in strategy.created: "
                    f"{strategy['strategy']['created']}. Expected: YYYY-MM-DD"
                )

        # Backtest dates already checked in business logic validation

        return errors

    def validate_yaml_string(self, yaml_string: str) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Validate a YAML string directly (useful for testing)

        Args:
            yaml_string: YAML content as string

        Returns:
            Tuple of (is_valid, error_messages, parsed_strategy)
        """
        errors = []

        # Parse YAML string
        try:
            strategy = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {e}"
            return False, [error_msg], None

        # Validate schema
        is_valid, schema_errors = self._validate_schema(strategy)
        errors.extend(schema_errors)

        # Validate business logic
        business_errors = self._validate_business_logic(strategy)
        errors.extend(business_errors)

        # Validate indicators
        indicator_errors = self._validate_indicators(strategy)
        errors.extend(indicator_errors)

        # Validate dates
        date_errors = self._validate_dates(strategy)
        errors.extend(date_errors)

        is_valid = len(errors) == 0

        return is_valid, errors, strategy if is_valid else None

    def get_strategy_summary(self, strategy: Dict) -> str:
        """
        Generate a human-readable summary of a strategy

        Args:
            strategy: Parsed and validated strategy dictionary

        Returns:
            Summary string
        """
        lines = []

        # Header
        if 'strategy' in strategy:
            strat = strategy['strategy']
            lines.append("=" * 60)
            lines.append(f"Strategy: {strat.get('name', 'Unknown')}")
            lines.append(f"Version: {strat.get('version', 'N/A')}")
            lines.append(f"Category: {strat.get('category', 'N/A')}")
            lines.append(f"Timeframe: {strat.get('timeframe', 'N/A')}")
            lines.append("=" * 60)

            if 'description' in strat:
                lines.append(f"\nDescription:\n{strat['description']}\n")

        # Indicators
        if 'indicators' in strategy:
            lines.append(f"\nIndicators ({len(strategy['indicators'])}):")
            for ind in strategy['indicators']:
                params = ind.get('parameters', {})
                param_str = ', '.join(f"{k}={v}" for k, v in params.items())
                lines.append(f"  - {ind['name']}({param_str}) -> {ind.get('output_column', 'N/A')}")

        # Entry conditions
        if 'entry' in strategy:
            entry = strategy['entry']
            lines.append(f"\nEntry Logic: {entry.get('logic', 'N/A')}")
            if 'conditions' in entry:
                lines.append(f"  Condition Groups ({len(entry['conditions'])}):")
                for cond in entry['conditions']:
                    group = cond.get('group', 'unnamed')
                    operator = cond.get('operator', 'AND')
                    lines.append(f"    - {group} ({operator}):")
                    if 'rules' in cond:
                        for rule in cond['rules']:
                            ind = rule.get('indicator', '?')
                            op = rule.get('operator', '?')
                            val = rule.get('value', rule.get('reference', '?'))
                            lines.append(f"        {ind} {op} {val}")

        # Exit conditions
        if 'exit' in strategy:
            exit_cond = strategy['exit']
            lines.append("\nExit Conditions:")

            if 'profit_target' in exit_cond and exit_cond['profit_target'].get('enabled'):
                pt = exit_cond['profit_target']
                lines.append(f"  - Profit Target: {pt.get('value', 'N/A')*100:.1f}%")

            if 'stop_loss' in exit_cond and exit_cond['stop_loss'].get('enabled'):
                sl = exit_cond['stop_loss']
                lines.append(f"  - Stop Loss: {sl.get('type', 'N/A')} (initial: {sl.get('initial_stop', 'N/A')*100:.1f}%)")

            if 'signal_exit' in exit_cond and exit_cond['signal_exit'].get('enabled'):
                lines.append("  - Signal-based Exit: Enabled")

        # Risk management
        if 'risk_management' in strategy:
            risk = strategy['risk_management']
            lines.append("\nRisk Management:")
            lines.append(f"  Initial Capital: ${risk.get('initial_capital', 0):,.0f}")
            lines.append(f"  Max Portfolio Risk: {risk.get('max_portfolio_risk', 0)*100:.1f}%")
            lines.append(f"  Max Position Size: {risk.get('max_position_size', 0)*100:.1f}%")

        # Backtest
        if 'backtest' in strategy:
            bt = strategy['backtest']
            lines.append("\nBacktest Configuration:")
            lines.append(f"  Period: {bt.get('start_date', 'N/A')} to {bt.get('end_date', 'N/A')}")
            if 'costs' in bt:
                costs = bt['costs']
                lines.append(f"  Commission: {costs.get('commission', 0)*100:.2f}%")
                lines.append(f"  Slippage: {costs.get('slippage', 0)*100:.2f}%")

        lines.append("=" * 60)

        return "\n".join(lines)


# Convenience function for quick validation
def validate_strategy_file(yaml_path: str, verbose: bool = True) -> bool:
    """
    Quick validation of a strategy file

    Args:
        yaml_path: Path to YAML strategy file
        verbose: Print detailed output

    Returns:
        True if valid, False otherwise
    """
    validator = StrategyValidator()
    is_valid, errors, strategy = validator.validate_file(yaml_path)

    if verbose:
        if is_valid:
            print(f"[OK] Strategy validation passed: {yaml_path}")
            if strategy:
                print("\n" + validator.get_strategy_summary(strategy))
        else:
            print(f"[FAILED] Strategy validation failed: {yaml_path}")
            print(f"\nErrors ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")

    return is_valid


if __name__ == "__main__":
    # Test with example strategy
    import sys

    if len(sys.argv) > 1:
        yaml_path = sys.argv[1]
    else:
        # Default: validate example strategy
        project_root = Path(__file__).parent.parent.parent
        yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    is_valid = validate_strategy_file(str(yaml_path), verbose=True)
    sys.exit(0 if is_valid else 1)
