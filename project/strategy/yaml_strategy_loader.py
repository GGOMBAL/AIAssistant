"""
YAML Strategy Loader - Strategy Agent Management

Loads and parses YAML strategy files into executable strategy objects.
Validates and prepares strategies for execution.

Owner: Strategy Agent
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from project.strategy.strategy_validator import StrategyValidator

logger = logging.getLogger(__name__)


@dataclass
class IndicatorSpec:
    """Indicator specification from YAML"""
    name: str
    parameters: Dict[str, Any]
    output_column: str
    input_column: str = "close"
    description: str = ""


@dataclass
class ConditionRule:
    """Single condition rule"""
    indicator: str
    operator: str
    value: Optional[Any] = None
    reference: Optional[str] = None
    multiplier: Optional[float] = None
    function: Optional[str] = None
    function_params: Optional[Dict] = None
    offset: Optional[int] = None
    lookback: Optional[int] = None
    description: str = ""


@dataclass
class ConditionGroup:
    """Group of condition rules"""
    group: str
    operator: str  # AND, OR, NOT
    rules: List[ConditionRule] = field(default_factory=list)


@dataclass
class EntryConditions:
    """Entry conditions for strategy"""
    conditions: List[ConditionGroup] = field(default_factory=list)
    logic: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExitConditions:
    """Exit conditions for strategy"""
    profit_target: Optional[Dict] = None
    stop_loss: Optional[Dict] = None
    signal_exit: Optional[Dict] = None
    time_exit: Optional[Dict] = None


@dataclass
class FilterRule:
    """Pre-entry filter rule"""
    name: str
    indicator: str
    operator: str
    value: Optional[Any] = None
    reference: Optional[str] = None
    multiplier: Optional[float] = None
    description: str = ""


@dataclass
class LoadedStrategy:
    """
    Loaded and parsed strategy object

    This object contains all strategy components in a structured format
    ready for execution.
    """
    # Metadata
    name: str
    version: str
    category: str
    market_type: str
    timeframe: str
    description: str = ""
    author: str = ""
    created: str = ""
    tags: List[str] = field(default_factory=list)

    # Components
    indicators: List[IndicatorSpec] = field(default_factory=list)
    entry: Optional[EntryConditions] = None
    exit: Optional[ExitConditions] = None
    filters: List[FilterRule] = field(default_factory=list)

    # Configuration
    universe: Dict[str, Any] = field(default_factory=dict)
    risk_management: Dict[str, Any] = field(default_factory=dict)
    backtest: Dict[str, Any] = field(default_factory=dict)
    optimization: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)

    # Raw YAML
    raw_yaml: Dict[str, Any] = field(default_factory=dict)

    def get_indicator_names(self) -> List[str]:
        """Get list of all indicator output column names"""
        return [ind.output_column for ind in self.indicators]

    def get_entry_group_names(self) -> List[str]:
        """Get list of all entry condition group names"""
        if not self.entry:
            return []
        return [group.group for group in self.entry.conditions]

    def get_required_data_columns(self) -> List[str]:
        """Get list of required data columns (OHLCV, etc.)"""
        columns = set()

        # Add standard OHLCV
        columns.update(['open', 'high', 'low', 'close', 'volume'])

        # Add indicator input columns
        for ind in self.indicators:
            columns.add(ind.input_column)

        # Add columns referenced in conditions
        if self.entry:
            for group in self.entry.conditions:
                for rule in group.rules:
                    # Check if indicator is a standard column
                    if rule.indicator in ['open', 'high', 'low', 'close', 'volume']:
                        columns.add(rule.indicator)
                    if rule.reference and rule.reference in ['open', 'high', 'low', 'close', 'volume']:
                        columns.add(rule.reference)

        return sorted(list(columns))


class YAMLStrategyLoader:
    """
    Loads and parses YAML strategy files

    Responsibilities:
    - Load YAML files
    - Validate using StrategyValidator
    - Parse into structured LoadedStrategy object
    - Extract all components (indicators, conditions, etc.)
    """

    def __init__(self, validator: Optional[StrategyValidator] = None):
        """
        Initialize YAML Strategy Loader

        Args:
            validator: Strategy validator instance. If None, creates new one.
        """
        if validator is None:
            self.validator = StrategyValidator()
        else:
            self.validator = validator

        logger.info("Initialized YAMLStrategyLoader")

    def load_from_file(self, yaml_path: str) -> Tuple[bool, Optional[LoadedStrategy], List[str]]:
        """
        Load strategy from YAML file

        Args:
            yaml_path: Path to YAML file

        Returns:
            Tuple of (success, loaded_strategy, error_messages)
        """
        logger.info(f"Loading strategy from: {yaml_path}")

        # Step 1: Validate YAML file
        is_valid, errors, strategy_dict = self.validator.validate_file(yaml_path)

        if not is_valid:
            logger.error(f"Strategy validation failed: {len(errors)} errors")
            return False, None, errors

        # Step 2: Parse into LoadedStrategy object
        try:
            loaded_strategy = self._parse_strategy(strategy_dict)
            logger.info(f"[OK] Successfully loaded strategy: {loaded_strategy.name}")
            return True, loaded_strategy, []

        except Exception as e:
            error_msg = f"Error parsing strategy: {e}"
            logger.error(error_msg)
            return False, None, [error_msg]

    def load_from_string(self, yaml_string: str) -> Tuple[bool, Optional[LoadedStrategy], List[str]]:
        """
        Load strategy from YAML string

        Args:
            yaml_string: YAML content as string

        Returns:
            Tuple of (success, loaded_strategy, error_messages)
        """
        # Validate
        is_valid, errors, strategy_dict = self.validator.validate_yaml_string(yaml_string)

        if not is_valid:
            return False, None, errors

        # Parse
        try:
            loaded_strategy = self._parse_strategy(strategy_dict)
            return True, loaded_strategy, []
        except Exception as e:
            return False, None, [str(e)]

    def _parse_strategy(self, strategy_dict: Dict) -> LoadedStrategy:
        """
        Parse strategy dictionary into LoadedStrategy object

        Args:
            strategy_dict: Validated strategy dictionary

        Returns:
            LoadedStrategy object
        """
        # Extract metadata
        strategy_meta = strategy_dict.get('strategy', {})

        # Parse indicators
        indicators = self._parse_indicators(strategy_dict.get('indicators', []))

        # Parse entry conditions
        entry = self._parse_entry_conditions(strategy_dict.get('entry', {}))

        # Parse exit conditions
        exit_cond = self._parse_exit_conditions(strategy_dict.get('exit', {}))

        # Parse filters
        filters = self._parse_filters(strategy_dict.get('filters', []))

        # Create LoadedStrategy object
        loaded = LoadedStrategy(
            # Metadata
            name=strategy_meta.get('name', 'Unknown'),
            version=strategy_meta.get('version', '1.0'),
            category=strategy_meta.get('category', 'unknown'),
            market_type=strategy_meta.get('market_type', 'stocks'),
            timeframe=strategy_meta.get('timeframe', 'daily'),
            description=strategy_meta.get('description', ''),
            author=strategy_meta.get('author', ''),
            created=strategy_meta.get('created', ''),
            tags=strategy_meta.get('tags', []),

            # Components
            indicators=indicators,
            entry=entry,
            exit=exit_cond,
            filters=filters,

            # Configuration
            universe=strategy_dict.get('universe', {}),
            risk_management=strategy_dict.get('risk_management', {}),
            backtest=strategy_dict.get('backtest', {}),
            optimization=strategy_dict.get('optimization', {}),
            monitoring=strategy_dict.get('monitoring', {}),

            # Raw YAML
            raw_yaml=strategy_dict
        )

        return loaded

    def _parse_indicators(self, indicators_list: List[Dict]) -> List[IndicatorSpec]:
        """Parse indicators list"""
        indicators = []

        for ind_dict in indicators_list:
            ind = IndicatorSpec(
                name=ind_dict['name'],
                parameters=ind_dict.get('parameters', {}),
                output_column=ind_dict['output_column'],
                input_column=ind_dict.get('input_column', 'close'),
                description=ind_dict.get('description', '')
            )
            indicators.append(ind)

        return indicators

    def _parse_entry_conditions(self, entry_dict: Dict) -> EntryConditions:
        """Parse entry conditions"""
        if not entry_dict:
            return EntryConditions()

        # Parse condition groups
        groups = []
        for group_dict in entry_dict.get('conditions', []):
            group = ConditionGroup(
                group=group_dict['group'],
                operator=group_dict['operator'],
                rules=self._parse_rules(group_dict.get('rules', []))
            )
            groups.append(group)

        return EntryConditions(
            conditions=groups,
            logic=entry_dict.get('logic', ''),
            constraints=entry_dict.get('constraints', {})
        )

    def _parse_rules(self, rules_list: List[Dict]) -> List[ConditionRule]:
        """Parse condition rules"""
        rules = []

        for rule_dict in rules_list:
            rule = ConditionRule(
                indicator=rule_dict['indicator'],
                operator=rule_dict['operator'],
                value=rule_dict.get('value'),
                reference=rule_dict.get('reference'),
                multiplier=rule_dict.get('multiplier'),
                function=rule_dict.get('function'),
                function_params=rule_dict.get('function_params'),
                offset=rule_dict.get('offset'),
                lookback=rule_dict.get('lookback'),
                description=rule_dict.get('description', '')
            )
            rules.append(rule)

        return rules

    def _parse_exit_conditions(self, exit_dict: Dict) -> ExitConditions:
        """Parse exit conditions"""
        if not exit_dict:
            return ExitConditions()

        # Parse signal exit if present
        signal_exit = None
        if 'signal_exit' in exit_dict and exit_dict['signal_exit'].get('enabled'):
            signal_exit = {
                'enabled': True,
                'conditions': []
            }
            for group_dict in exit_dict['signal_exit'].get('conditions', []):
                group = ConditionGroup(
                    group=group_dict['group'],
                    operator=group_dict['operator'],
                    rules=self._parse_rules(group_dict.get('rules', []))
                )
                signal_exit['conditions'].append(group)

        return ExitConditions(
            profit_target=exit_dict.get('profit_target'),
            stop_loss=exit_dict.get('stop_loss'),
            signal_exit=signal_exit,
            time_exit=exit_dict.get('time_exit')
        )

    def _parse_filters(self, filters_list: List[Dict]) -> List[FilterRule]:
        """Parse filter rules"""
        filters = []

        for filter_dict in filters_list:
            filter_rule = FilterRule(
                name=filter_dict['name'],
                indicator=filter_dict['indicator'],
                operator=filter_dict['operator'],
                value=filter_dict.get('value'),
                reference=filter_dict.get('reference'),
                multiplier=filter_dict.get('multiplier'),
                description=filter_dict.get('description', '')
            )
            filters.append(filter_rule)

        return filters


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test loader
    loader = YAMLStrategyLoader()

    # Load example strategy
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    success, strategy, errors = loader.load_from_file(str(yaml_path))

    if success and strategy:
        print("=" * 60)
        print("LOADED STRATEGY")
        print("=" * 60)
        print(f"Name: {strategy.name}")
        print(f"Version: {strategy.version}")
        print(f"Category: {strategy.category}")
        print(f"Timeframe: {strategy.timeframe}")
        print(f"\nIndicators ({len(strategy.indicators)}):")
        for ind in strategy.indicators:
            print(f"  - {ind.name}({', '.join(f'{k}={v}' for k, v in ind.parameters.items())}) -> {ind.output_column}")
        print(f"\nEntry Groups ({len(strategy.entry.conditions) if strategy.entry else 0}):")
        if strategy.entry:
            for group in strategy.entry.conditions:
                print(f"  - {group.group} ({group.operator}): {len(group.rules)} rules")
        print(f"\nFilters ({len(strategy.filters)}):")
        for filt in strategy.filters:
            print(f"  - {filt.name}: {filt.indicator} {filt.operator} {filt.value}")
        print("=" * 60)
    else:
        print(f"[FAILED] Loading failed:")
        for error in errors:
            print(f"  - {error}")
