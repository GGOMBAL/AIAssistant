"""
Report Agent Router
Handles communication between Orchestrator and Report Agent
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import Report Agent
from agents.report_agent.agent import ReportAgent

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportAgentRouter:
    """
    Router for Report Agent

    Responsibilities:
    - Route requests from Orchestrator to Report Agent
    - Validate input data
    - Format responses
    - Handle errors gracefully
    - Manage Report Agent lifecycle
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Report Agent Router

        Args:
            config: Router configuration
        """
        self.config = config or {}
        self.name = "Report Agent Router"

        # Initialize Report Agent
        agent_config = self.config.get('agent_config', {})
        self.report_agent = ReportAgent(config=agent_config)

        # Request tracking
        self.request_count = 0
        self.last_request_time = None
        self.request_history = []

        logger.info(f"[{self.name}] Initialized")

    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request from Orchestrator

        Args:
            request: Request dictionary with:
                - action: Type of report to generate
                - data: Input data (order_history, market_prices, etc.)
                - params: Additional parameters

        Returns:
            Response dictionary with:
                - status: 'success' or 'error'
                - data: Report data or error message
                - metadata: Request metadata
        """
        logger.info(f"[{self.name}] Processing request: {request.get('action', 'unknown')}")

        # Track request
        self.request_count += 1
        self.last_request_time = datetime.now()

        try:
            # Validate request
            validation_result = self._validate_request(request)
            if not validation_result['valid']:
                return self._error_response(validation_result['error'])

            # Extract request components
            action = request.get('action')
            data = request.get('data', {})
            params = request.get('params', {})

            # Route to appropriate handler
            if action == 'generate_report':
                response = self._handle_generate_report(data, params)
            elif action == 'generate_pl_report':
                response = self._handle_pl_report(data)
            elif action == 'generate_balance_report':
                response = self._handle_balance_report(data, params)
            elif action == 'analyze_gap':
                response = self._handle_gap_analysis(data)
            elif action == 'generate_quantstats_report':
                response = self._handle_quantstats_report(data, params)
            elif action == 'get_text_report':
                response = self._handle_text_report(params)
            elif action == 'save_report':
                response = self._handle_save_report(params)
            elif action == 'get_status':
                response = self._handle_get_status()
            else:
                return self._error_response(f"Unknown action: {action}")

            # Track successful request
            self._track_request(request, response)

            return response

        except Exception as e:
            logger.error(f"[{self.name}] Error processing request: {str(e)}")
            return self._error_response(str(e))

    def _handle_generate_report(self,
                               data: Dict[str, Any],
                               params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive report generation"""
        # Extract data
        order_history = self._extract_order_history(data)
        market_prices = data.get('market_prices', None)

        if market_prices is not None and not isinstance(market_prices, pd.DataFrame):
            market_prices = pd.DataFrame(market_prices)

        # Get report type
        report_type = params.get('report_type', 'full')

        # Generate report
        report = self.report_agent.generate_comprehensive_report(
            order_history=order_history,
            market_prices=market_prices,
            report_type=report_type
        )

        return self._success_response(report)

    def _handle_pl_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle P/L report generation"""
        order_history = self._extract_order_history(data)
        report = self.report_agent.generate_pl_report(order_history)
        return self._success_response(report)

    def _handle_balance_report(self,
                              data: Dict[str, Any],
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle balance report generation"""
        order_history = self._extract_order_history(data)
        market_prices = data.get('market_prices', None)

        if market_prices is not None and not isinstance(market_prices, pd.DataFrame):
            market_prices = pd.DataFrame(market_prices)

        report = self.report_agent.generate_balance_report(order_history, market_prices)
        return self._success_response(report)

    def _handle_gap_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GAP analysis between backtest and live"""
        backtest_orders = data.get('backtest_orders')
        live_orders = data.get('live_orders')

        if backtest_orders is None or live_orders is None:
            return self._error_response("Both backtest_orders and live_orders required for GAP analysis")

        # Convert to DataFrames if needed
        if not isinstance(backtest_orders, pd.DataFrame):
            backtest_orders = pd.DataFrame(backtest_orders)
        if not isinstance(live_orders, pd.DataFrame):
            live_orders = pd.DataFrame(live_orders)

        report = self.report_agent.analyze_gap(backtest_orders, live_orders)
        return self._success_response(report)

    def _handle_quantstats_report(self,
                                  data: Dict[str, Any],
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle QuantStats report generation

        Args:
            data: Input data containing backtest_result
            params: Parameters including benchmark, title, etc.

        Returns:
            Response dictionary with HTML path and metrics
        """
        try:
            # Import wrapper
            from project.reporting.backtest_report_wrapper import generate_backtest_report

            # Extract backtest result
            backtest_result = data.get('backtest_result')
            if backtest_result is None:
                return self._error_response("backtest_result required in data")

            # Extract parameters
            benchmark = params.get('benchmark', None)
            title = params.get('title', None)
            initial_capital = params.get('initial_capital', 100000.0)
            output_dir = params.get('output_dir', 'visualization_output/reports')

            # Generate report
            html_path, metrics = generate_backtest_report(
                backtest_result=backtest_result,
                output_dir=output_dir,
                benchmark=benchmark,
                title=title,
                initial_capital=initial_capital
            )

            if html_path is None:
                return self._error_response("Failed to generate QuantStats report")

            # Return response
            return self._success_response({
                'html_path': html_path,
                'metrics': metrics,
                'message': f'QuantStats report generated: {html_path}'
            })

        except Exception as e:
            logger.error(f"Error generating QuantStats report: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(f"QuantStats report generation failed: {str(e)}")

    def _handle_text_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text report retrieval"""
        report_type = params.get('report_type', 'last')
        text_report = self.report_agent.get_text_report(report_type)
        return self._success_response({'text_report': text_report})

    def _handle_save_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report saving"""
        filepath = params.get('filepath')
        format = params.get('format', 'json')

        if not filepath:
            return self._error_response("filepath parameter required")

        success = self.report_agent.save_report(filepath, format)

        if success:
            return self._success_response({'message': f"Report saved to {filepath}"})
        else:
            return self._error_response("Failed to save report")

    def _handle_get_status(self) -> Dict[str, Any]:
        """Handle status request"""
        status = {
            'agent_name': self.report_agent.name,
            'agent_version': self.report_agent.version,
            'request_count': self.request_count,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'reports_generated': len(self.report_agent.generated_reports),
            'last_report_type': self.report_agent.last_report.get('report_type', None)
                               if self.report_agent.last_report else None
        }
        return self._success_response(status)

    def _extract_order_history(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract and validate order history from data

        Args:
            data: Input data dictionary

        Returns:
            Order history DataFrame
        """
        order_history = data.get('order_history')

        if order_history is None:
            raise ValueError("order_history is required")

        # Convert to DataFrame if needed
        if not isinstance(order_history, pd.DataFrame):
            order_history = pd.DataFrame(order_history)

        # Validate required columns
        required_columns = ['ticker', 'order_type', 'order_date', 'execution_price', 'quantity']
        missing_columns = [col for col in required_columns if col not in order_history.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Ensure date column is datetime
        order_history['order_date'] = pd.to_datetime(order_history['order_date'])

        # Add commission column if missing
        if 'commission' not in order_history.columns:
            order_history['commission'] = 0

        return order_history

    def _validate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming request

        Args:
            request: Request to validate

        Returns:
            Validation result with 'valid' and optional 'error' keys
        """
        # Check for required fields
        if not isinstance(request, dict):
            return {'valid': False, 'error': 'Request must be a dictionary'}

        if 'action' not in request:
            return {'valid': False, 'error': 'Request missing action field'}

        action = request.get('action')

        # Validate based on action
        if action in ['generate_report', 'generate_pl_report', 'generate_balance_report']:
            if 'data' not in request:
                return {'valid': False, 'error': f'{action} requires data field'}

            data = request.get('data')
            if not isinstance(data, dict):
                return {'valid': False, 'error': 'Data must be a dictionary'}

            if 'order_history' not in data:
                return {'valid': False, 'error': 'order_history required in data'}

        elif action == 'analyze_gap':
            data = request.get('data', {})
            if 'backtest_orders' not in data or 'live_orders' not in data:
                return {'valid': False,
                       'error': 'analyze_gap requires both backtest_orders and live_orders'}

        elif action == 'save_report':
            params = request.get('params', {})
            if 'filepath' not in params:
                return {'valid': False, 'error': 'save_report requires filepath parameter'}

        return {'valid': True}

    def _track_request(self, request: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Track request for history and analytics"""
        self.request_history.append({
            'timestamp': datetime.now(),
            'action': request.get('action'),
            'status': response.get('status'),
            'response_time': datetime.now() - self.last_request_time
        })

        # Keep only last 100 requests
        if len(self.request_history) > 100:
            self.request_history = self.request_history[-100:]

    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Create success response"""
        return {
            'status': 'success',
            'data': data,
            'metadata': {
                'router': self.name,
                'timestamp': datetime.now().isoformat(),
                'request_id': self.request_count
            }
        }

    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'status': 'error',
            'error': error_msg,
            'metadata': {
                'router': self.name,
                'timestamp': datetime.now().isoformat(),
                'request_id': self.request_count
            }
        }

    def get_capabilities(self) -> List[str]:
        """
        Get list of Report Agent capabilities

        Returns:
            List of available actions
        """
        return [
            'generate_report',
            'generate_pl_report',
            'generate_balance_report',
            'analyze_gap',
            'generate_quantstats_report',
            'get_text_report',
            'save_report',
            'get_status'
        ]

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get Report Agent information

        Returns:
            Agent information dictionary
        """
        return {
            'name': self.report_agent.name,
            'version': self.report_agent.version,
            'capabilities': self.get_capabilities(),
            'report_types': ['full', 'pl', 'balance', 'summary', 'gap'],
            'output_formats': ['json', 'text'],
            'access_rights': {
                'read': ['all_layers'],
                'write': ['reporting_layer'],
                'input': ['order_history', 'market_prices'],
                'output': ['analysis_reports']
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize router
    router = ReportAgentRouter()

    # Sample order history
    sample_orders = pd.DataFrame({
        'ticker': ['AAPL', 'AAPL', 'MSFT', 'MSFT'],
        'order_type': ['BUY', 'SELL', 'BUY', 'SELL'],
        'order_date': pd.date_range('2024-01-01', periods=4, freq='D'),
        'execution_price': [150, 155, 300, 310],
        'quantity': [100, 100, 50, 50],
        'commission': [1, 1, 1, 1]
    })

    # Test request
    request = {
        'action': 'generate_report',
        'data': {
            'order_history': sample_orders
        },
        'params': {
            'report_type': 'summary'
        }
    }

    # Process request
    response = router.process_request(request)

    # Print response
    if response['status'] == 'success':
        print("Report generated successfully!")
        print(f"Report data: {response['data']}")
    else:
        print(f"Error: {response['error']}")