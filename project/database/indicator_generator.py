"""
Indicator Generator - Database Agent Management

Generates technical indicator code from templates or using LLM.
Validates generated code and registers new indicators.

Owner: Database Agent
"""

import ast
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd

# Import registry manager
from project.database.indicator_registry_manager import IndicatorRegistryManager, IndicatorMetadata

logger = logging.getLogger(__name__)


class IndicatorGenerator:
    """
    Generates technical indicator code from templates or LLM

    Responsibilities:
    - Load indicator templates
    - Generate code from templates with parameter substitution
    - Generate code using LLM (Anthropic Claude)
    - Validate generated code (syntax, execution, logic)
    - Write code to generated/ module
    - Register new indicators in registry
    - Generate unit tests
    """

    def __init__(self, registry_manager: Optional[IndicatorRegistryManager] = None):
        """
        Initialize Indicator Generator

        Args:
            registry_manager: Registry manager instance. If None, creates new one.
        """
        if registry_manager is None:
            self.registry_manager = IndicatorRegistryManager()
        else:
            self.registry_manager = registry_manager

        # Paths
        project_root = Path(__file__).parent.parent.parent
        self.templates_dir = project_root / "project" / "indicator" / "templates"
        self.generated_dir = project_root / "project" / "indicator" / "generated"

        # Ensure generated dir exists
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized IndicatorGenerator")
        logger.info(f"  Templates dir: {self.templates_dir}")
        logger.info(f"  Generated dir: {self.generated_dir}")

    def load_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Load all indicator templates

        Returns:
            Dictionary mapping category -> template_name -> template_content
        """
        templates = {}

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return templates

        # Scan template directories
        for category_dir in self.templates_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category = category_dir.name
            templates[category] = {}

            for template_file in category_dir.glob("*.template"):
                template_name = template_file.stem
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                    templates[category][template_name] = template_content
                    logger.debug(f"Loaded template: {category}/{template_name}")
                except Exception as e:
                    logger.error(f"Error loading template {template_file}: {e}")

        logger.info(f"Loaded {sum(len(t) for t in templates.values())} templates from {len(templates)} categories")
        return templates

    def generate_from_template(self, template_name: str, category: str,
                               parameters: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        Generate indicator code from template

        Args:
            template_name: Template name (e.g., "rsi")
            category: Category (e.g., "momentum")
            parameters: Parameters to substitute (e.g., {"period": 14})

        Returns:
            Tuple of (success, generated_code, error_message)
        """
        try:
            # Load template
            template_path = self.templates_dir / category / f"{template_name}.template"
            if not template_path.exists():
                return False, "", f"Template not found: {category}/{template_name}"

            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Substitute parameters
            generated_code = template_content
            for param_name, param_value in parameters.items():
                # Replace {param_name} with param_value
                generated_code = generated_code.replace(f"{{{param_name}}}", str(param_value))

            logger.info(f"[OK] Generated code from template: {category}/{template_name}")
            logger.info(f"     Parameters: {parameters}")

            return True, generated_code, None

        except Exception as e:
            logger.error(f"Error generating from template: {e}")
            return False, "", str(e)

    def generate_from_llm(self, indicator_description: str,
                         indicator_name: str,
                         category: str,
                         parameters: Optional[Dict] = None,
                         reference_code: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Generate indicator code using LLM (Anthropic Claude)

        Args:
            indicator_description: Natural language description of indicator
            indicator_name: Desired indicator name
            category: Category (trend, momentum, volatility, etc.)
            parameters: Optional parameters dictionary
            reference_code: Optional reference code for context

        Returns:
            Tuple of (success, generated_code, error_message)
        """
        try:
            # Check if Anthropic API is available
            try:
                import anthropic
            except ImportError:
                error_msg = "anthropic package not installed. Run: pip install anthropic"
                logger.error(error_msg)
                return False, "", error_msg

            # Get API key from environment
            import os
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                error_msg = "ANTHROPIC_API_KEY environment variable not set"
                logger.error(error_msg)
                return False, "", error_msg

            # Construct prompt
            prompt = self._build_llm_prompt(
                indicator_description=indicator_description,
                indicator_name=indicator_name,
                category=category,
                parameters=parameters,
                reference_code=reference_code
            )

            # Call Anthropic API
            client = anthropic.Anthropic(api_key=api_key)

            logger.info(f"Calling Anthropic API to generate {indicator_name}...")

            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Latest Sonnet model
                max_tokens=4096,
                temperature=0.2,  # Low temperature for code generation
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract code from response
            generated_code = message.content[0].text

            # Extract Python code from markdown if present
            generated_code = self._extract_code_from_markdown(generated_code)

            logger.info(f"[OK] Generated code using LLM for: {indicator_name}")

            return True, generated_code, None

        except Exception as e:
            logger.error(f"Error generating from LLM: {e}")
            return False, "", str(e)

    def _build_llm_prompt(self, indicator_description: str, indicator_name: str,
                         category: str, parameters: Optional[Dict],
                         reference_code: Optional[str]) -> str:
        """
        Build LLM prompt for indicator generation

        Args:
            indicator_description: Indicator description
            indicator_name: Indicator name
            category: Category
            parameters: Parameters
            reference_code: Reference code

        Returns:
            Prompt string
        """
        prompt = f"""Generate Python code for a technical indicator with the following specifications:

**Indicator Name**: {indicator_name}
**Category**: {category}
**Description**: {indicator_description}
"""

        if parameters:
            prompt += f"\n**Parameters**: {json.dumps(parameters, indent=2)}\n"

        prompt += """
**Requirements**:
1. Create a standalone function that calculates the indicator
2. Function signature: `def calculate_{indicator_name}(data: pd.Series, **params) -> pd.Series`
3. Input: pandas Series (typically close price)
4. Output: pandas Series with same index as input
5. Handle edge cases (NaN values, empty data, single value)
6. Include comprehensive docstring with:
   - Description
   - Parameters with types and defaults
   - Returns format
   - Example usage
   - References (if applicable)
7. Use numpy/pandas for calculations (vectorized operations)
8. No side effects (pure function)
9. Include `__indicator_metadata__` dictionary at the end with:
   - name, category, description
   - parameters list
   - inputs, outputs
   - calculation method
   - tags

**Example Structure**:
```python
import pandas as pd
import numpy as np

def calculate_my_indicator(data: pd.Series, period: int = 14) -> pd.Series:
    \"\"\"
    Calculate My Indicator.

    Parameters:
    -----------
    data : pd.Series
        Price series
    period : int, default=14
        Calculation period

    Returns:
    --------
    pd.Series
        Indicator values

    Example:
    --------
    >>> df['MY_INDICATOR'] = calculate_my_indicator(df['close'], period=14)
    \"\"\"
    # Validation
    if not isinstance(data, pd.Series):
        raise TypeError("Input data must be pandas Series")

    # Calculation
    result = ... # your calculation here

    return result

__indicator_metadata__ = {{
    "name": "MY_INDICATOR",
    "category": "momentum",
    ...
}}
```
"""

        if reference_code:
            prompt += f"\n**Reference Code** (for context):\n```python\n{reference_code}\n```\n"

        prompt += "\nPlease generate ONLY the Python code (no additional explanation). The code should be production-ready and well-tested."

        return prompt

    def _extract_code_from_markdown(self, text: str) -> str:
        """
        Extract Python code from markdown code blocks

        Args:
            text: Response text (may contain markdown)

        Returns:
            Extracted Python code
        """
        # Pattern for ```python ... ``` blocks
        pattern = r"```python\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0]

        # Pattern for ``` ... ``` blocks
        pattern = r"```\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0]

        # No markdown, return as-is
        return text

    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated code

        Args:
            code: Generated Python code

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Step 1: Syntax validation
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors

        # Step 2: Check for required imports
        required_imports = ['pandas', 'numpy']
        for imp in required_imports:
            if f"import {imp}" not in code:
                errors.append(f"Missing required import: {imp}")

        # Step 3: Check for function definition
        if "def calculate_" not in code:
            errors.append("Missing function definition (must start with 'calculate_')")

        # Step 4: Check for metadata
        if "__indicator_metadata__" not in code:
            errors.append("Missing __indicator_metadata__ dictionary")

        # Step 5: Check for docstring
        if '"""' not in code and "'''" not in code:
            errors.append("Missing docstring")

        return len(errors) == 0, errors

    def execute_test(self, code: str, test_data: Optional[pd.Series] = None) -> Tuple[bool, Optional[str]]:
        """
        Execute generated code on test data

        Args:
            code: Generated Python code
            test_data: Optional test data. If None, generates synthetic data.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Generate test data if not provided
            if test_data is None:
                test_data = pd.Series(
                    [100 + i + (i % 10) for i in range(100)],
                    index=pd.date_range('2024-01-01', periods=100, freq='D')
                )

            # Create execution environment
            exec_globals = {
                'pd': pd,
                'np': __import__('numpy')
            }

            # Execute code
            exec(code, exec_globals)

            # Find the calculate_ function
            func_name = None
            for name in exec_globals:
                if name.startswith('calculate_'):
                    func_name = name
                    break

            if not func_name:
                return False, "No calculate_ function found in generated code"

            # Call function
            result = exec_globals[func_name](test_data)

            # Validate result
            if not isinstance(result, pd.Series):
                return False, f"Function returned {type(result)}, expected pd.Series"

            if len(result) != len(test_data):
                return False, f"Result length ({len(result)}) doesn't match input ({len(test_data)})"

            # Check for inf/nan (some are acceptable, but not all)
            if result.isna().all():
                return False, "Result contains only NaN values"

            if result.isinf().any():
                return False, "Result contains infinite values"

            logger.info("[OK] Execution test passed")
            return True, None

        except Exception as e:
            return False, f"Execution error: {e}"

    def write_to_module(self, code: str, category: str, indicator_name: str) -> bool:
        """
        Write generated code to module file

        Args:
            code: Generated Python code
            category: Category (momentum, trend, etc.)
            indicator_name: Indicator name

        Returns:
            True if successful
        """
        try:
            # Determine output file
            output_file = self.generated_dir / f"{category}_indicators.py"

            # If file exists, append; otherwise create
            if output_file.exists():
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n# ====== {indicator_name} ======\n")
                    f.write(code)
                logger.info(f"Appended {indicator_name} to {output_file}")
            else:
                # Create new file with header
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f'"""\nGenerated {category.title()} Indicators\n')
                    f.write(f'Auto-generated by IndicatorGenerator\n')
                    f.write(f'Generated: {datetime.now().isoformat()}\n')
                    f.write('"""\n\n')
                    f.write('import pandas as pd\n')
                    f.write('import numpy as np\n\n')
                    f.write(f"# ====== {indicator_name} ======\n")
                    f.write(code)
                logger.info(f"Created {output_file} with {indicator_name}")

            return True

        except Exception as e:
            logger.error(f"Error writing to module: {e}")
            return False

    def generate_and_register(self, method: str, indicator_name: str, category: str,
                             parameters: Optional[Dict] = None,
                             template_name: Optional[str] = None,
                             description: Optional[str] = None,
                             auto_register: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Generate indicator and optionally register it

        Args:
            method: Generation method ("template" or "llm")
            indicator_name: Indicator name
            category: Category
            parameters: Parameters dictionary
            template_name: Template name (for template method)
            description: Natural language description (for LLM method)
            auto_register: Automatically register in registry

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Step 1: Generate code
            if method == "template":
                if not template_name:
                    return False, "template_name required for template method"
                success, code, error = self.generate_from_template(
                    template_name=template_name,
                    category=category,
                    parameters=parameters or {}
                )
            elif method == "llm":
                if not description:
                    return False, "description required for LLM method"
                success, code, error = self.generate_from_llm(
                    indicator_description=description,
                    indicator_name=indicator_name,
                    category=category,
                    parameters=parameters
                )
            else:
                return False, f"Unknown method: {method}"

            if not success:
                return False, f"Generation failed: {error}"

            # Step 2: Validate code
            is_valid, errors = self.validate_code(code)
            if not is_valid:
                return False, f"Validation failed: {'; '.join(errors)}"

            # Step 3: Execute test
            success, error = self.execute_test(code)
            if not success:
                return False, f"Execution test failed: {error}"

            # Step 4: Write to module
            success = self.write_to_module(code, category, indicator_name)
            if not success:
                return False, "Failed to write to module"

            # Step 5: Register (if requested)
            if auto_register:
                # Extract metadata from code (TODO: implement metadata extraction)
                logger.info(f"Auto-registration not fully implemented yet for {indicator_name}")

            logger.info(f"[OK] Successfully generated and validated: {indicator_name}")
            return True, None

        except Exception as e:
            logger.error(f"Error in generate_and_register: {e}")
            return False, str(e)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test generator
    generator = IndicatorGenerator()

    # Test template generation
    print("=" * 60)
    print("Testing Template-Based Generation")
    print("=" * 60)

    success, error = generator.generate_and_register(
        method="template",
        indicator_name="RSI_14",
        category="momentum",
        template_name="rsi",
        parameters={"period": 14},
        auto_register=False
    )

    if success:
        print("[OK] Template generation successful!")
    else:
        print(f"[FAILED] Template generation failed: {error}")

    print("\n" + "=" * 60)
    print("For LLM generation, set ANTHROPIC_API_KEY environment variable")
    print("=" * 60)
