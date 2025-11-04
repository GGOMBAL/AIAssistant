"""
Indicator Registry Manager - Database Agent Management

Manages the indicator registry (indicator_registry.json).
Provides API for querying, validating, and updating indicator metadata.

Owner: Database Agent
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class IndicatorMetadata:
    """
    Indicator metadata structure

    Attributes:
        name: Indicator name
        category: Category (trend, momentum, volatility, fundamental)
        description: Description of indicator
        parameters: List of parameter definitions
        inputs: Required input columns
        outputs: Output column definitions
        calculation: Calculation method description
        module: Python module path
        function: Function name
        generated: Whether this indicator was auto-generated
        validated: Whether this indicator has been validated
        tags: List of tags for searching
    """
    name: str
    category: str
    description: str
    parameters: List[Dict]
    inputs: List[str]
    outputs: List[Dict]
    calculation: str
    module: str
    function: str
    generated: bool
    validated: bool
    tags: List[str]
    example_usage: Optional[str] = None
    variants: Optional[List[Dict]] = None
    dependencies: Optional[List[str]] = None
    market_specific: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "parameters": self.parameters,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "calculation": self.calculation,
            "module": self.module,
            "function": self.function,
            "generated": self.generated,
            "validated": self.validated,
            "tags": self.tags,
            "example_usage": self.example_usage,
            "variants": self.variants,
            "dependencies": self.dependencies,
            "market_specific": self.market_specific
        }


class IndicatorRegistryManager:
    """
    Manages indicator registry and provides query/update operations

    Responsibilities:
    - Load and parse indicator_registry.json
    - Query indicators by name, category, tags
    - Validate indicator existence
    - Add new indicators
    - Update indicator metadata
    - Generate dependency graphs
    """

    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize Indicator Registry Manager

        Args:
            registry_path: Path to indicator_registry.json. If None, uses default.
        """
        if registry_path is None:
            # Default path
            project_root = Path(__file__).parent.parent.parent
            registry_path = project_root / "project" / "indicator" / "indicator_registry.json"

        self.registry_path = Path(registry_path)
        self.registry = None
        self._load_registry()

        logger.info(f"Initialized IndicatorRegistryManager with {self.get_indicator_count()} indicators")

    def _load_registry(self) -> None:
        """
        Load indicator registry from JSON file

        Raises:
            FileNotFoundError: If registry file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)

            logger.info(f"Loaded indicator registry from {self.registry_path}")
            logger.info(f"  Version: {self.registry.get('version', 'N/A')}")
            logger.info(f"  Total indicators: {self.registry.get('total_indicators', 0)}")

        except FileNotFoundError:
            logger.error(f"Registry file not found: {self.registry_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in registry file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            raise

    def save_registry(self) -> bool:
        """
        Save current registry to JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last_updated timestamp
            self.registry['last_updated'] = datetime.now().isoformat() + "Z"

            # Write to file
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved registry to {self.registry_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            return False

    def get_indicator(self, name: str, parameters: Optional[Dict] = None) -> Optional[IndicatorMetadata]:
        """
        Get indicator metadata by name

        Args:
            name: Indicator name (e.g., "SMA", "RSI")
            parameters: Optional parameters for variant matching

        Returns:
            IndicatorMetadata object or None if not found
        """
        if name not in self.registry['indicators']:
            logger.debug(f"Indicator '{name}' not found in registry")
            return None

        ind_data = self.registry['indicators'][name]

        try:
            metadata = IndicatorMetadata(
                name=ind_data['name'],
                category=ind_data['category'],
                description=ind_data['description'],
                parameters=ind_data['parameters'],
                inputs=ind_data['inputs'],
                outputs=ind_data['outputs'],
                calculation=ind_data['calculation'],
                module=ind_data['module'],
                function=ind_data['function'],
                generated=ind_data['generated'],
                validated=ind_data['validated'],
                tags=ind_data['tags'],
                example_usage=ind_data.get('example_usage'),
                variants=ind_data.get('variants'),
                dependencies=ind_data.get('dependencies'),
                market_specific=ind_data.get('market_specific')
            )

            return metadata

        except KeyError as e:
            logger.error(f"Missing required field in indicator '{name}': {e}")
            return None

    def list_indicators(self, category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       market: Optional[str] = None) -> List[str]:
        """
        List indicators filtered by category and/or tags

        Args:
            category: Filter by category (trend, momentum, volatility, fundamental)
            tags: Filter by tags (must have ALL specified tags)
            market: Filter by market (US, KR, etc.)

        Returns:
            List of indicator names
        """
        results = []

        for name, ind_data in self.registry['indicators'].items():
            # Category filter
            if category is not None and ind_data['category'] != category:
                continue

            # Tags filter (must have ALL specified tags)
            if tags is not None:
                if not all(tag in ind_data['tags'] for tag in tags):
                    continue

            # Market filter
            if market is not None:
                market_specific = ind_data.get('market_specific', [])
                if market_specific and market not in market_specific:
                    continue

            results.append(name)

        return sorted(results)

    def validate_indicator_exists(self, name: str, parameters: Optional[Dict] = None) -> bool:
        """
        Check if an indicator exists in the registry

        Args:
            name: Indicator name
            parameters: Optional parameters for variant matching

        Returns:
            True if exists, False otherwise
        """
        return name in self.registry['indicators']

    def add_indicator(self, metadata: IndicatorMetadata, overwrite: bool = False) -> bool:
        """
        Add a new indicator to the registry

        Args:
            metadata: Indicator metadata object
            overwrite: If True, overwrite existing indicator

        Returns:
            True if successful, False otherwise
        """
        if not overwrite and metadata.name in self.registry['indicators']:
            logger.warning(f"Indicator '{metadata.name}' already exists. Use overwrite=True to replace.")
            return False

        try:
            # Convert metadata to dict (exclude None values)
            ind_dict = {k: v for k, v in metadata.to_dict().items() if v is not None}

            # Add to registry
            self.registry['indicators'][metadata.name] = ind_dict

            # Update total count
            self.registry['total_indicators'] = len(self.registry['indicators'])

            # Save registry
            success = self.save_registry()

            if success:
                logger.info(f"[OK] Added indicator '{metadata.name}' to registry")
            else:
                logger.error(f"Failed to save registry after adding '{metadata.name}'")

            return success

        except Exception as e:
            logger.error(f"Error adding indicator '{metadata.name}': {e}")
            return False

    def search_indicators(self, query: str) -> List[str]:
        """
        Search indicators by name, description, or tags

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching indicator names
        """
        query_lower = query.lower()
        results = []

        for name, ind_data in self.registry['indicators'].items():
            # Search in name
            if query_lower in name.lower():
                results.append(name)
                continue

            # Search in description
            if query_lower in ind_data['description'].lower():
                results.append(name)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in ind_data['tags']):
                results.append(name)
                continue

        return sorted(results)

    def get_dependencies(self, indicator_name: str) -> List[str]:
        """
        Get dependencies for an indicator

        Args:
            indicator_name: Indicator name

        Returns:
            List of dependency indicator names
        """
        if indicator_name not in self.registry['indicators']:
            return []

        ind_data = self.registry['indicators'][indicator_name]
        return ind_data.get('dependencies', [])

    def get_category_indicators(self, category: str) -> List[str]:
        """
        Get all indicators in a category

        Args:
            category: Category name

        Returns:
            List of indicator names
        """
        if category not in self.registry.get('categories', {}):
            logger.warning(f"Category '{category}' not found in registry")
            return []

        return self.registry['categories'][category].get('indicators', [])

    def get_indicator_count(self) -> int:
        """
        Get total number of indicators in registry

        Returns:
            Indicator count
        """
        return len(self.registry.get('indicators', {}))

    def get_categories(self) -> List[str]:
        """
        Get list of all categories

        Returns:
            Category names
        """
        return list(self.registry.get('categories', {}).keys())

    def get_all_tags(self) -> List[str]:
        """
        Get list of all unique tags across all indicators

        Returns:
            Sorted list of unique tags
        """
        tags = set()
        for ind_data in self.registry['indicators'].values():
            tags.update(ind_data.get('tags', []))

        return sorted(tags)

    def get_indicator_summary(self) -> Dict:
        """
        Get summary statistics of the registry

        Returns:
            Summary dictionary
        """
        summary = {
            'version': self.registry.get('version', 'N/A'),
            'last_updated': self.registry.get('last_updated', 'N/A'),
            'total_indicators': self.get_indicator_count(),
            'categories': {},
            'generated_count': 0,
            'validated_count': 0,
            'tags': len(self.get_all_tags())
        }

        # Count by category
        for category in self.get_categories():
            category_indicators = self.list_indicators(category=category)
            summary['categories'][category] = len(category_indicators)

        # Count generated and validated
        for ind_data in self.registry['indicators'].values():
            if ind_data.get('generated', False):
                summary['generated_count'] += 1
            if ind_data.get('validated', False):
                summary['validated_count'] += 1

        return summary

    def validate_indicator_definition(self, name: str) -> Tuple[bool, List[str]]:
        """
        Validate an indicator definition

        Args:
            name: Indicator name

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if name not in self.registry['indicators']:
            return False, [f"Indicator '{name}' not found in registry"]

        ind_data = self.registry['indicators'][name]

        # Required fields
        required_fields = ['name', 'category', 'description', 'parameters', 'inputs',
                          'outputs', 'calculation', 'module', 'function', 'generated',
                          'validated', 'tags']

        for field in required_fields:
            if field not in ind_data:
                errors.append(f"Missing required field: {field}")

        # Validate category
        valid_categories = ['trend', 'momentum', 'volatility', 'fundamental', 'volume']
        if ind_data.get('category') not in valid_categories:
            errors.append(f"Invalid category: {ind_data.get('category')}")

        # Validate parameters structure
        if not isinstance(ind_data.get('parameters', []), list):
            errors.append("Parameters must be a list")

        # Validate inputs
        if not isinstance(ind_data.get('inputs', []), list):
            errors.append("Inputs must be a list")

        # Validate outputs
        if not isinstance(ind_data.get('outputs', []), list):
            errors.append("Outputs must be a list")

        return len(errors) == 0, errors

    def print_summary(self) -> None:
        """
        Print a formatted summary of the registry
        """
        summary = self.get_indicator_summary()

        print("=" * 60)
        print("INDICATOR REGISTRY SUMMARY")
        print("=" * 60)
        print(f"Version: {summary['version']}")
        print(f"Last Updated: {summary['last_updated']}")
        print(f"Total Indicators: {summary['total_indicators']}")
        print(f"  - Generated: {summary['generated_count']}")
        print(f"  - Validated: {summary['validated_count']}")
        print(f"Total Tags: {summary['tags']}")
        print(f"\nCategories:")
        for category, count in summary['categories'].items():
            print(f"  - {category}: {count}")
        print("=" * 60)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test registry manager
    manager = IndicatorRegistryManager()

    # Print summary
    manager.print_summary()

    # Test queries
    print("\nTrend Indicators:")
    for ind in manager.list_indicators(category='trend'):
        print(f"  - {ind}")

    print("\nSearching for 'moving average':")
    for ind in manager.search_indicators('moving average'):
        print(f"  - {ind}")

    # Test get indicator
    sma = manager.get_indicator('SMA')
    if sma:
        print(f"\nSMA Indicator:")
        print(f"  Name: {sma.name}")
        print(f"  Description: {sma.description}")
        print(f"  Parameters: {sma.parameters}")
        print(f"  Variants: {len(sma.variants) if sma.variants else 0}")
