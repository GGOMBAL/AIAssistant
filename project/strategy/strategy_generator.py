"""
Strategy Generator - LLM-powered YAML Strategy Generation

Automatically generates YAML strategy files from natural language descriptions.
Uses LLM to extract indicators, conditions, and parameters.

Owner: Strategy Agent
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class StrategyGenerator:
    """
    Generates YAML strategy files from natural language descriptions

    Responsibilities:
    - Parse natural language strategy descriptions
    - Extract required indicators
    - Generate entry/exit conditions
    - Create valid YAML strategy files
    - Use LLM for intelligent extraction
    """

    def __init__(self, output_dir: str = None):
        """
        Initialize Strategy Generator

        Args:
            output_dir: Directory to save generated YAML files
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / "config" / "strategies"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load example strategies for few-shot learning
        self.example_strategies = self._load_example_strategies()

        logger.info(f"Initialized StrategyGenerator with output dir: {self.output_dir}")

    def generate_strategy(
        self,
        description: str,
        strategy_name: Optional[str] = None,
        author: str = "Auto-Generated",
        use_llm: bool = True
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Generate YAML strategy from natural language description

        Args:
            description: Natural language strategy description
            strategy_name: Name for the strategy (auto-generated if None)
            author: Strategy author name
            use_llm: Use LLM for intelligent parsing (if False, uses rule-based)

        Returns:
            Tuple of (success, yaml_path, errors)
        """
        logger.info(f"Generating strategy from description (LLM={use_llm})")

        try:
            # Parse description to extract strategy components
            if use_llm:
                components = self._parse_with_llm(description)
            else:
                components = self._parse_with_rules(description)

            if not components:
                return False, None, ["Failed to parse strategy description"]

            # Generate strategy name if not provided
            if not strategy_name:
                strategy_name = self._generate_strategy_name(components)

            # Build YAML structure
            yaml_content = self._build_yaml_structure(
                components=components,
                strategy_name=strategy_name,
                author=author
            )

            # Validate generated YAML
            validation_errors = self._validate_yaml_content(yaml_content)
            if validation_errors:
                return False, None, validation_errors

            # Save to file
            yaml_path = self._save_yaml_file(strategy_name, yaml_content)

            logger.info(f"[OK] Generated strategy: {yaml_path}")
            return True, str(yaml_path), []

        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            return False, None, [str(e)]

    def _parse_with_llm(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Parse strategy description using LLM

        Args:
            description: Strategy description

        Returns:
            Dictionary with strategy components
        """
        # Build prompt for LLM
        prompt = self._build_llm_prompt(description)

        # Call LLM (using simple mock for now - can be replaced with actual LLM call)
        try:
            response = self._call_llm(prompt)
            components = self._extract_components_from_llm_response(response)
            return components

        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}, falling back to rule-based")
            return self._parse_with_rules(description)

    def _parse_with_rules(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Parse strategy description using rule-based approach

        Args:
            description: Strategy description

        Returns:
            Dictionary with strategy components
        """
        description_lower = description.lower()

        # Extract indicators first
        indicators = self._extract_indicators(description_lower)

        # Then extract conditions using the indicator names
        indicator_map = {ind['output_column']: ind for ind in indicators}

        components = {
            'category': self._extract_category(description_lower),
            'indicators': indicators,
            'entry_conditions': self._extract_entry_conditions(description_lower, indicator_map),
            'exit_conditions': self._extract_exit_conditions(description_lower),
            'risk_management': self._extract_risk_management(description_lower),
            'description': description
        }

        return components

    def _extract_category(self, description: str) -> str:
        """Extract strategy category from description"""
        if any(word in description for word in ['mean reversion', 'oversold', 'overbought', 'reversal']):
            return 'mean_reversion'
        elif any(word in description for word in ['trend', 'momentum', 'breakout']):
            return 'trend_following'
        elif any(word in description for word in ['volatility', 'bollinger', 'atr']):
            return 'volatility'
        else:
            return 'other'

    def _extract_indicators(self, description: str) -> List[Dict]:
        """Extract required indicators from description"""
        indicators = []
        import re

        # RSI - extract period from patterns like "14-period RSI" or "RSI-14" or default to 14
        if 'rsi' in description:
            period = 14  # default
            # Look for explicit period mentions like "14-period rsi", "rsi 14", "rsi-14"
            match = re.search(r'(?:(\d+)[\s-]?(?:period|day)?\s*rsi|rsi[\s-]?(\d+)[\s-]?(?:period|day)?)', description)
            if match:
                period = int(match.group(1) or match.group(2))

            indicators.append({
                'name': 'RSI',
                'parameters': {'period': period},
                'output_column': f'RSI_{period}',
                'description': f'RSI indicator with period {period}'
            })

        # SMA - extract periods from patterns like "20-day SMA", "SMA 20"
        if 'sma' in description or 'simple moving average' in description or 'moving average' in description:
            # Look for patterns like "20-day sma", "sma 20", "sma-20"
            matches = re.findall(r'(?:(\d+)[\s-]?day\s*(?:sma|moving average)|(?:sma|moving average)[\s-]?(\d+))', description)

            if matches:
                periods = [int(m[0] or m[1]) for m in matches]
            else:
                periods = [20, 50]  # default

            for period in periods:
                indicators.append({
                    'name': 'SMA',
                    'parameters': {'period': period},
                    'output_column': f'SMA_{period}',
                    'description': f'Simple Moving Average with period {period}'
                })

        # EMA
        if 'ema' in description or 'exponential moving average' in description:
            periods = [12, 26]  # default
            import re
            matches = re.findall(r'ema[^\d]*(\d+)', description)
            if matches:
                periods = [int(m) for m in matches]

            for period in periods:
                indicators.append({
                    'name': 'EMA',
                    'parameters': {'period': period},
                    'output_column': f'EMA_{period}'
                })

        # MACD
        if 'macd' in description:
            indicators.append({
                'name': 'MACD',
                'parameters': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
                'output_column': 'MACD_12_26_9'
            })

        # ATR
        if 'atr' in description or 'average true range' in description:
            indicators.append({
                'name': 'ATR',
                'parameters': {'period': 14},
                'output_column': 'ATR_14'
            })

        # Volume
        if 'volume' in description:
            indicators.append({
                'name': 'Volume_SMA',
                'parameters': {'period': 20},
                'output_column': 'Volume_SMA_20'
            })

        return indicators

    def _extract_entry_conditions(self, description: str, indicator_map: Dict[str, Dict]) -> List[Dict]:
        """Extract entry conditions from description"""
        conditions = []
        rules = []
        import re

        # Find RSI indicator name from map
        rsi_column = next((k for k in indicator_map.keys() if k.startswith('RSI_')), 'RSI_14')
        sma_columns = [k for k in indicator_map.keys() if k.startswith('SMA_')]

        # RSI oversold - check if "RSI" and "below/oversold" are together
        if re.search(r'rsi\s+(?:is\s+)?(?:below|<|oversold)', description) or 'rsi.*below' in description or 'oversold' in description:
            threshold = 30  # default
            match = re.search(r'rsi.*?(?:below|<).*?(\d+)', description)
            if match:
                threshold = int(match.group(1))

            rules.append({
                'indicator': rsi_column,
                'operator': '<',
                'value': threshold,
                'description': f'RSI below {threshold}'
            })

        # RSI overbought - check if "RSI" and "above/overbought" are together
        if re.search(r'rsi\s+(?:is\s+)?(?:above|>|overbought)', description) or 'rsi.*above' in description:
            threshold = 70  # default
            match = re.search(r'rsi.*?(?:above|>).*?(\d+)', description)
            if match:
                threshold = int(match.group(1))

            rules.append({
                'indicator': rsi_column,
                'operator': '>',
                'value': threshold,
                'description': f'RSI above {threshold}'
            })

        # Price above MA - check if "price" and "above" are together
        if re.search(r'price\s+(?:is\s+)?above.*(?:sma|moving average)', description):
            # Use the first SMA from the indicator map
            sma_ref = sma_columns[0] if sma_columns else 'SMA_20'
            rules.append({
                'indicator': 'close',
                'operator': '>',
                'reference': sma_ref,
                'description': f'Price above {sma_ref}'
            })

        # Price below MA - check if "price" and "below" are together
        if re.search(r'price\s+(?:is\s+)?below.*(?:sma|moving average)', description):
            # Use the first SMA from the indicator map
            sma_ref = sma_columns[0] if sma_columns else 'SMA_20'
            rules.append({
                'indicator': 'close',
                'operator': '<',
                'reference': sma_ref,
                'description': f'Price below {sma_ref}'
            })

        # MACD crossover
        if 'macd' in description and 'cross' in description:
            if 'above' in description or 'bullish' in description:
                rules.append({
                    'indicator': 'MACD_12_26_9',
                    'operator': 'crosses_above',
                    'reference': 'MACD_Signal_9',
                    'description': 'MACD bullish crossover'
                })

        # Volume condition
        if 'volume' in description and ('above' in description or 'high' in description or 'confirm' in description):
            # Find volume indicator from map
            volume_ref = next((k for k in indicator_map.keys() if k.startswith('Volume_SMA_')), 'Volume_SMA_20')
            rules.append({
                'indicator': 'volume',
                'operator': '>',
                'reference': volume_ref,
                'description': 'Volume above average'
            })

        if rules:
            conditions.append({
                'group': 'entry_signals',
                'operator': 'AND',
                'rules': rules
            })

        return conditions

    def _extract_exit_conditions(self, description: str) -> Dict[str, Any]:
        """Extract exit conditions from description"""
        exit_conditions = {}

        # Profit target
        profit_match = None
        import re
        profit_patterns = [
            r'(?:sell\s+at\s+|profit\s+target\s+of\s+|target\s+of\s+)?(\d+)%\s+profit',
            r'profit[^\d]*(\d+)\s*%',
            r'target[^\d]*(\d+)\s*%',
            r'(\d+)\s*%[^\d]*profit',
        ]
        for pattern in profit_patterns:
            match = re.search(pattern, description.lower())
            if match:
                profit_match = int(match.group(1))
                break

        if profit_match:
            exit_conditions['profit_target'] = {
                'enabled': True,
                'type': 'percentage',
                'value': profit_match / 100.0
            }
        else:
            # Default profit target
            exit_conditions['profit_target'] = {
                'enabled': True,
                'type': 'percentage',
                'value': 0.10
            }

        # Stop loss
        stop_loss_match = None
        stop_patterns = [
            r'stop[^\d]*loss[^\d]*(\d+)%',
            r'loss[^\d]*(\d+)%',
        ]
        for pattern in stop_patterns:
            match = re.search(pattern, description)
            if match:
                stop_loss_match = int(match.group(1))
                break

        if 'trailing' in description or 'stepped' in description:
            exit_conditions['stop_loss'] = {
                'enabled': True,
                'type': 'stepped_trailing',
                'initial_stop': stop_loss_match / 100.0 if stop_loss_match else 0.03,
                'risk_unit': 0.05
            }
        else:
            exit_conditions['stop_loss'] = {
                'enabled': True,
                'type': 'stepped_trailing',
                'initial_stop': 0.03,
                'risk_unit': 0.05
            }

        return exit_conditions

    def _extract_risk_management(self, description: str) -> Dict[str, Any]:
        """Extract risk management parameters"""
        return {
            'initial_capital': 100000000.0,
            'max_portfolio_risk': 0.20,
            'max_position_size': 0.10,
            'position_sizing': {
                'method': 'risk_parity',
                'base_risk': 0.05
            }
        }

    def _build_yaml_structure(
        self,
        components: Dict[str, Any],
        strategy_name: str,
        author: str
    ) -> Dict[str, Any]:
        """Build complete YAML structure from components"""

        yaml_content = {
            'strategy': {
                'name': strategy_name,
                'version': '1.0',
                'author': author,
                'created': datetime.now().strftime('%Y-%m-%d'),
                'description': components.get('description', ''),
                'category': components.get('category', 'other'),
                'market_type': 'stocks',
                'timeframe': 'daily'
            },
            'indicators': components.get('indicators', []),
            'entry': {
                'conditions': components.get('entry_conditions', []),
                'logic': 'entry_signals' if components.get('entry_conditions') else 'true'
            },
            'exit': components.get('exit_conditions', {}),
            'risk_management': components.get('risk_management', {})
        }

        return yaml_content

    def _generate_strategy_name(self, components: Dict[str, Any]) -> str:
        """Generate strategy name from components"""
        category = components.get('category', 'custom')
        indicators = components.get('indicators', [])

        indicator_names = '_'.join([ind['name'] for ind in indicators[:2]])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return f"{category}_{indicator_names}_{timestamp}"

    def _validate_yaml_content(self, yaml_content: Dict) -> List[str]:
        """Validate generated YAML structure"""
        errors = []

        # Check required fields
        if 'strategy' not in yaml_content:
            errors.append("Missing 'strategy' section")

        if 'indicators' not in yaml_content or not yaml_content['indicators']:
            errors.append("No indicators defined")

        if 'entry' not in yaml_content:
            errors.append("Missing 'entry' section")

        if 'exit' not in yaml_content:
            errors.append("Missing 'exit' section")

        return errors

    def _save_yaml_file(self, strategy_name: str, yaml_content: Dict) -> Path:
        """Save YAML content to file"""
        filename = f"{strategy_name}.yaml"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        return filepath

    def _load_example_strategies(self) -> List[Dict]:
        """Load example strategies for few-shot learning"""
        examples = []

        example_dir = Path(__file__).parent.parent.parent / "config" / "strategies"
        if example_dir.exists():
            for yaml_file in example_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        strategy = yaml.safe_load(f)
                        examples.append(strategy)
                except Exception as e:
                    logger.warning(f"Could not load example: {yaml_file}: {e}")

        return examples

    def _build_llm_prompt(self, description: str) -> str:
        """Build prompt for LLM strategy extraction"""
        prompt = f"""
You are a trading strategy expert. Convert the following natural language strategy description into a structured format.

Strategy Description:
{description}

Extract the following components:
1. Strategy Category (mean_reversion, trend_following, volatility, momentum, other)
2. Required Indicators (RSI, SMA, EMA, MACD, ATR, Bollinger Bands, etc.)
   - Include parameters like period, fast/slow periods
3. Entry Conditions
   - Specific rules (e.g., "RSI < 30", "Price > SMA_20")
4. Exit Conditions
   - Profit target percentage
   - Stop loss percentage
   - Signal-based exits
5. Risk Management
   - Position sizing method
   - Maximum portfolio risk

Return your response as a JSON object with these components.

Example format:
{{
  "category": "mean_reversion",
  "indicators": [
    {{"name": "RSI", "parameters": {{"period": 14}}, "output_column": "RSI_14"}},
    {{"name": "SMA", "parameters": {{"period": 20}}, "output_column": "SMA_20"}}
  ],
  "entry_conditions": [
    {{
      "group": "entry_signals",
      "operator": "AND",
      "rules": [
        {{"indicator": "RSI_14", "operator": "<", "value": 30, "description": "RSI oversold"}},
        {{"indicator": "close", "operator": ">", "reference": "SMA_20", "description": "Price above SMA"}}
      ]
    }}
  ],
  "exit_conditions": {{
    "profit_target": {{"enabled": true, "type": "percentage", "value": 0.10}},
    "stop_loss": {{"enabled": true, "type": "stepped_trailing", "initial_stop": 0.03, "risk_unit": 0.05}}
  }},
  "risk_management": {{
    "initial_capital": 100000000.0,
    "max_portfolio_risk": 0.20,
    "max_position_size": 0.10
  }}
}}
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM to parse strategy (placeholder implementation)

        In production, this would call actual LLM API (OpenAI, Anthropic, etc.)
        """
        # This is a placeholder - in production, you would:
        # 1. Use LLMRouterClient
        # 2. Or call OpenAI/Anthropic API directly
        # 3. Parse the JSON response

        # For now, return empty to trigger fallback to rule-based
        raise NotImplementedError("LLM integration not yet implemented")

    def _extract_components_from_llm_response(self, response: str) -> Dict:
        """Extract strategy components from LLM JSON response"""
        try:
            components = json.loads(response)
            return components
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test strategy generator
    generator = StrategyGenerator()

    # Example 1: RSI mean reversion
    description1 = """
    Buy when RSI is below 30 (oversold) and price is above 20-day SMA.
    Sell at 10% profit or use 3% stepped trailing stop loss.
    Use volume confirmation (volume above 20-day average).
    """

    success, yaml_path, errors = generator.generate_strategy(
        description=description1,
        strategy_name="RSI_Mean_Reversion_Auto",
        use_llm=False  # Use rule-based for now
    )

    if success:
        print(f"[OK] Generated strategy: {yaml_path}")
    else:
        print(f"[FAILED] Errors: {errors}")

    # Example 2: MACD trend following
    description2 = """
    Enter long when MACD crosses above signal line with volume confirmation.
    Exit at 15% profit or when MACD crosses below signal line.
    """

    success2, yaml_path2, errors2 = generator.generate_strategy(
        description=description2,
        strategy_name="MACD_Trend_Auto",
        use_llm=False
    )

    if success2:
        print(f"[OK] Generated strategy: {yaml_path2}")
    else:
        print(f"[FAILED] Errors: {errors2}")
