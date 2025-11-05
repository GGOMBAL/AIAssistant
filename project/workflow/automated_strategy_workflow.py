"""
Automated Strategy Workflow - Orchestrator Management

Complete end-to-end automated workflow for strategy development and testing.
Integrates all phases: Generation → Validation → Backtest → Report

Owner: Orchestrator Agent
"""

import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd

from project.strategy.strategy_generator import StrategyGenerator
from project.strategy.yaml_strategy_loader import YAMLStrategyLoader
from project.service.yaml_backtest_service import YAMLBacktestService
from project.reporting.strategy_report_generator import StrategyReportGenerator

logger = logging.getLogger(__name__)


class AutomatedStrategyWorkflow:
    """
    Automated end-to-end strategy workflow

    Complete pipeline:
    1. Generate YAML strategy from natural language
    2. Validate strategy structure
    3. Run backtest on provided data
    4. Generate comprehensive report

    Responsibilities:
    - Orchestrate all workflow steps
    - Handle errors gracefully
    - Provide progress feedback
    - Generate final reports
    """

    def __init__(
        self,
        strategy_output_dir: Optional[str] = None,
        report_output_dir: Optional[str] = None
    ):
        """
        Initialize Automated Workflow

        Args:
            strategy_output_dir: Directory to save generated strategies
            report_output_dir: Directory to save reports
        """
        self.generator = StrategyGenerator(output_dir=strategy_output_dir)
        self.loader = YAMLStrategyLoader()
        self.backtest_service = YAMLBacktestService()
        self.report_generator = StrategyReportGenerator(output_dir=report_output_dir)

        logger.info("Initialized AutomatedStrategyWorkflow")

    def run_complete_workflow(
        self,
        strategy_description: str,
        data: Dict[str, pd.DataFrame],
        strategy_name: Optional[str] = None,
        author: str = "Auto-Generated",
        use_llm: bool = False,
        store_backtest: bool = False,
        save_report: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete automated workflow

        Args:
            strategy_description: Natural language strategy description
            data: Market data dictionary {symbol: DataFrame}
            strategy_name: Name for strategy (auto-generated if None)
            author: Strategy author
            use_llm: Use LLM for strategy generation
            store_backtest: Store backtest results in MongoDB
            save_report: Save report to file

        Returns:
            Dictionary with complete workflow results
        """
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("AUTOMATED STRATEGY WORKFLOW - START")
        logger.info("=" * 80)

        workflow_result = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'yaml_path': None,
            'backtest_result': None,
            'report': None,
            'execution_time': 0
        }

        try:
            # ========================================
            # STEP 1: Generate YAML Strategy
            # ========================================
            print(f"\n[Step 1/4] Generating YAML strategy...")
            logger.info("[Step 1/4] Generating YAML strategy from description")

            gen_success, yaml_path, gen_errors = self.generator.generate_strategy(
                description=strategy_description,
                strategy_name=strategy_name,
                author=author,
                use_llm=use_llm
            )

            if not gen_success:
                workflow_result['errors'].extend(gen_errors)
                logger.error(f"[FAILED] Strategy generation failed: {gen_errors}")
                return workflow_result

            workflow_result['steps_completed'].append('generation')
            workflow_result['yaml_path'] = yaml_path
            print(f"[OK] Strategy generated: {yaml_path}")
            logger.info(f"[OK] Strategy generated: {yaml_path}")

            # ========================================
            # STEP 2: Validate Strategy
            # ========================================
            print(f"\n[Step 2/4] Validating strategy...")
            logger.info("[Step 2/4] Validating generated strategy")

            val_success, strategy, val_errors = self.loader.load_from_file(yaml_path)

            if not val_success:
                workflow_result['errors'].extend(val_errors)
                logger.error(f"[FAILED] Strategy validation failed: {val_errors}")
                return workflow_result

            workflow_result['steps_completed'].append('validation')
            print(f"[OK] Strategy validated: {strategy.name} v{strategy.version}")
            logger.info(f"[OK] Strategy validated: {strategy.name} v{strategy.version}")
            logger.info(f"  Required indicators: {strategy.get_indicator_names()}")

            # ========================================
            # STEP 3: Run Backtest
            # ========================================
            print(f"\n[Step 3/4] Running backtest...")
            logger.info("[Step 3/4] Running backtest")

            backtest_results = self.backtest_service.backtest_strategy(
                strategy=strategy,
                data=data,
                store_results=store_backtest
            )

            if not backtest_results['success']:
                workflow_result['errors'].extend(backtest_results.get('errors', []))
                logger.error(f"[FAILED] Backtest failed: {backtest_results.get('errors', [])}")
                return workflow_result

            workflow_result['steps_completed'].append('backtest')
            workflow_result['backtest_result'] = backtest_results['backtest_result']

            bt_result = backtest_results['backtest_result']
            perf = bt_result.performance_metrics

            print(f"[OK] Backtest completed in {backtest_results['execution_time']:.2f}s")
            print(f"  Total trades: {len(bt_result.trades)}")
            print(f"  Total return: {perf.get('total_return', 0):.2%}")
            print(f"  Sharpe ratio: {perf.get('sharpe_ratio', 0):.2f}")
            print(f"  Max drawdown: {perf.get('max_drawdown', 0):.2%}")

            logger.info(f"[OK] Backtest completed")
            logger.info(f"  Execution time: {backtest_results['execution_time']:.2f}s")
            logger.info(f"  Total trades: {len(bt_result.trades)}")

            # ========================================
            # STEP 4: Generate Report
            # ========================================
            print(f"\n[Step 4/4] Generating report...")
            logger.info("[Step 4/4] Generating comprehensive report")

            report = self.report_generator.generate_report(
                strategy_name=strategy.name,
                backtest_result=bt_result,
                execution_time=backtest_results['execution_time'],
                include_trades=True,
                save_to_file=save_report
            )

            workflow_result['steps_completed'].append('report')
            workflow_result['report'] = report

            print(f"[OK] Report generated")
            logger.info(f"[OK] Report generated")

            # ========================================
            # WORKFLOW COMPLETE
            # ========================================
            workflow_result['success'] = True
            workflow_result['execution_time'] = (datetime.now() - start_time).total_seconds()

            print(f"\n{'='*80}")
            print(f"WORKFLOW COMPLETED SUCCESSFULLY")
            print(f"{'='*80}")
            print(f"Total execution time: {workflow_result['execution_time']:.2f}s")
            print(f"Steps completed: {' -> '.join(workflow_result['steps_completed'])}")
            print(f"{'='*80}\n")

            logger.info("=" * 80)
            logger.info("AUTOMATED STRATEGY WORKFLOW - COMPLETE")
            logger.info(f"Total time: {workflow_result['execution_time']:.2f}s")
            logger.info("=" * 80)

            # Print report to console
            print("\n" + report)

            return workflow_result

        except Exception as e:
            workflow_result['errors'].append(str(e))
            logger.error(f"Workflow failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return workflow_result

    def run_from_existing_yaml(
        self,
        yaml_path: str,
        data: Dict[str, pd.DataFrame],
        store_backtest: bool = False,
        save_report: bool = True
    ) -> Dict[str, Any]:
        """
        Run workflow from existing YAML file (skip generation step)

        Args:
            yaml_path: Path to existing YAML strategy
            data: Market data
            store_backtest: Store results in MongoDB
            save_report: Save report to file

        Returns:
            Dictionary with workflow results
        """
        start_time = datetime.now()

        logger.info("Running workflow from existing YAML")

        workflow_result = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'yaml_path': yaml_path,
            'backtest_result': None,
            'report': None,
            'execution_time': 0
        }

        try:
            # Load strategy
            print(f"[Step 1/3] Loading strategy from: {yaml_path}")
            success, strategy, errors = self.loader.load_from_file(yaml_path)

            if not success:
                workflow_result['errors'].extend(errors)
                return workflow_result

            workflow_result['steps_completed'].append('validation')
            print(f"[OK] Strategy loaded: {strategy.name}")

            # Run backtest
            print(f"[Step 2/3] Running backtest...")
            backtest_results = self.backtest_service.backtest_strategy(
                strategy=strategy,
                data=data,
                store_results=store_backtest
            )

            if not backtest_results['success']:
                workflow_result['errors'].extend(backtest_results.get('errors', []))
                return workflow_result

            workflow_result['steps_completed'].append('backtest')
            workflow_result['backtest_result'] = backtest_results['backtest_result']

            bt_result = backtest_results['backtest_result']
            print(f"[OK] Backtest completed: {len(bt_result.trades)} trades")

            # Generate report
            print(f"[Step 3/3] Generating report...")
            report = self.report_generator.generate_report(
                strategy_name=strategy.name,
                backtest_result=bt_result,
                execution_time=backtest_results['execution_time'],
                include_trades=True,
                save_to_file=save_report
            )

            workflow_result['steps_completed'].append('report')
            workflow_result['report'] = report
            workflow_result['success'] = True
            workflow_result['execution_time'] = (datetime.now() - start_time).total_seconds()

            print(f"\n[OK] Workflow completed in {workflow_result['execution_time']:.2f}s\n")
            print(report)

            return workflow_result

        except Exception as e:
            workflow_result['errors'].append(str(e))
            logger.error(f"Workflow failed: {e}")
            return workflow_result


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    import numpy as np

    # Create test data
    dates = pd.date_range('2023-01-01', periods=252, freq='D')
    data = {}

    for symbol in ['AAPL', 'MSFT', 'GOOGL']:
        # Create price data with some volatility
        trend = np.linspace(100, 120, 252)
        noise = np.random.randn(252) * 3
        close_prices = trend + noise

        # Add some oversold dips (more extreme to trigger RSI < 30)
        for i in [50, 100, 150, 200]:
            if i < len(close_prices):
                close_prices[i:i+15] -= 15  # Increased drop: 10->15, duration: 10->15

        df = pd.DataFrame({
            'open': close_prices * (1 + np.random.uniform(-0.01, 0.01, 252)),
            'high': close_prices * (1 + np.random.uniform(0.00, 0.02, 252)),
            'low': close_prices * (1 + np.random.uniform(-0.02, 0.00, 252)),
            'close': close_prices,
            'volume': 1000000 + np.random.randint(-200000, 200000, 252)
        }, index=dates)

        data[symbol] = df

    # Test automated workflow
    workflow = AutomatedStrategyWorkflow()

    strategy_description = """
    Buy when RSI is below 30 (oversold) and price is below 20-day SMA.
    Sell at 10% profit target or use 3% initial stop with 5% stepped trailing.
    """

    print("=" * 80)
    print("TESTING AUTOMATED STRATEGY WORKFLOW")
    print("=" * 80)

    result = workflow.run_complete_workflow(
        strategy_description=strategy_description,
        data=data,
        strategy_name="RSI_Test_Strategy",
        use_llm=False,
        save_report=True
    )

    if result['success']:
        print("\n[SUCCESS] Workflow completed successfully!")
        print(f"YAML saved to: {result['yaml_path']}")
        print(f"Total execution time: {result['execution_time']:.2f}s")
    else:
        print(f"\n[FAILED] Workflow failed: {result['errors']}")
