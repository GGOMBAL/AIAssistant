"""
Helper Agent Router Integration
Claude.md 규칙 준수: Helper Agent의 LLM 라우터 통합

Author: Helper Agent
Date: 2025-09-15
Layer: Service Layer
Rules: Claude.md 규칙 1, 4, 9, 11, 12 준수 + EXCLUSIVE CONTROL
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.llm_router_client import LLMRouterClient, RouterResponse
from typing import Dict, Any, List, Optional
import logging
import yaml
import json
import requests
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MCPCredentials:
    """MCP 인증 정보"""
    app_key: str
    app_secret: str
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

@dataclass
class MCPResponse:
    """MCP API 응답 정보"""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    response_time: Optional[float] = None

class KoreaInvestmentMCP:
    """
    한국투자증권 MCP (Model Context Protocol) 통합 클래스
    Claude.md 규칙 4에 따른 Helper Agent 독점 제어
    """

    def __init__(self, config_path: str = None):
        """MCP 클라이언트 초기화"""
        self.config_path = config_path or "config/mcp_integration.yaml"
        self.config = self._load_config()
        self.credentials: Optional[MCPCredentials] = None
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.is_enabled = False

        logger.info("Korea Investment MCP initialized (DISABLED by default)")

    def _load_config(self) -> Dict[str, Any]:
        """MCP 설정 파일 로드"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), '..', '..', self.config_path)
            with open(config_file, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.warning(f"MCP config not found, using defaults: {e}")
            return {"mcp_providers": {"korea_investment": {"enabled": False}}}

    def activate_mcp(self, app_key: str, app_secret: str) -> bool:
        """
        MCP 활성화 매크로
        Claude.md 규칙 4에 따른 Helper Agent 독점 기능
        """
        try:
            # 자격증명 설정
            self.credentials = MCPCredentials(app_key=app_key, app_secret=app_secret)

            # OAuth 토큰 획득
            if self._authenticate():
                self.is_enabled = True
                logger.info("Korea Investment MCP activated successfully")
                return True
            else:
                logger.error("MCP activation failed - authentication error")
                return False

        except Exception as e:
            logger.error(f"MCP activation failed: {e}")
            return False

    def deactivate_mcp(self) -> bool:
        """MCP 비활성화 매크로"""
        try:
            self.is_enabled = False
            self.credentials = None
            logger.info("Korea Investment MCP deactivated")
            return True
        except Exception as e:
            logger.error(f"MCP deactivation failed: {e}")
            return False

    def _authenticate(self) -> bool:
        """OAuth 인증 수행"""
        if not self.credentials:
            return False

        try:
            auth_url = f"{self.base_url}/oauth2/tokenP"
            headers = {
                "content-type": "application/json"
            }
            data = {
                "grant_type": "client_credentials",
                "appkey": self.credentials.app_key,
                "appsecret": self.credentials.app_secret
            }

            response = requests.post(auth_url, headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                self.credentials.access_token = token_data.get("access_token")
                # 토큰 만료 시간 설정 (1시간)
                self.credentials.token_expires_at = datetime.now().timestamp() + 3600
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def get_current_price(self, symbol: str, market: str = "KOSPI") -> MCPResponse:
        """현재가 조회"""
        if not self.is_enabled:
            return MCPResponse(success=False, data={}, error_message="MCP not activated")

        try:
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
            url = f"{self.base_url}{endpoint}"

            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.credentials.access_token}",
                "appkey": self.credentials.app_key,
                "appsecret": self.credentials.app_secret,
                "tr_id": "FHKST01010100"
            }

            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }

            start_time = datetime.now()
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response_time = (datetime.now() - start_time).total_seconds()

            if response.status_code == 200:
                data = response.json()
                return MCPResponse(
                    success=True,
                    data=data,
                    response_time=response_time
                )
            else:
                return MCPResponse(
                    success=False,
                    data={},
                    error_message=f"API error: {response.status_code}",
                    response_time=response_time
                )

        except Exception as e:
            return MCPResponse(
                success=False,
                data={},
                error_message=str(e)
            )

    def get_account_balance(self) -> MCPResponse:
        """계좌 잔고 조회"""
        if not self.is_enabled:
            return MCPResponse(success=False, data={}, error_message="MCP not activated")

        try:
            endpoint = "/uapi/domestic-stock/v1/trading/inquire-balance"
            url = f"{self.base_url}{endpoint}"

            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.credentials.access_token}",
                "appkey": self.credentials.app_key,
                "appsecret": self.credentials.app_secret,
                "tr_id": "TTTC8434R"
            }

            params = {
                "CANO": "00000000",  # 계좌번호 (실제 사용 시 설정)
                "ACNT_PRDT_CD": "01",
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }

            start_time = datetime.now()
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response_time = (datetime.now() - start_time).total_seconds()

            if response.status_code == 200:
                data = response.json()
                return MCPResponse(
                    success=True,
                    data=data,
                    response_time=response_time
                )
            else:
                return MCPResponse(
                    success=False,
                    data={},
                    error_message=f"API error: {response.status_code}",
                    response_time=response_time
                )

        except Exception as e:
            return MCPResponse(
                success=False,
                data={},
                error_message=str(e)
            )

    def place_order(self, symbol: str, quantity: int, price: float, side: str) -> MCPResponse:
        """주문 실행 (테스트용)"""
        if not self.is_enabled:
            return MCPResponse(success=False, data={}, error_message="MCP not activated")

        # 실제 주문은 위험하므로 시뮬레이션만 수행
        logger.warning("ORDER SIMULATION ONLY - No real order placed")

        simulation_result = {
            "order_id": f"SIM_{int(datetime.now().timestamp())}",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "side": side,
            "status": "SIMULATED",
            "timestamp": datetime.now().isoformat()
        }

        return MCPResponse(
            success=True,
            data=simulation_result,
            response_time=0.1
        )

    def test_connectivity(self) -> MCPResponse:
        """MCP 연결 테스트"""
        if not self.is_enabled:
            return MCPResponse(success=False, data={}, error_message="MCP not activated")

        try:
            # 간단한 API 호출로 연결 테스트
            test_result = self.get_current_price("005930")  # 삼성전자

            if test_result.success:
                return MCPResponse(
                    success=True,
                    data={
                        "status": "connected",
                        "test_symbol": "005930",
                        "response_time": test_result.response_time
                    }
                )
            else:
                return MCPResponse(
                    success=False,
                    data={},
                    error_message="Connectivity test failed"
                )

        except Exception as e:
            return MCPResponse(
                success=False,
                data={},
                error_message=f"Test failed: {e}"
            )

class HelperAgentRouter:
    """
    Helper Agent LLM 라우터 통합

    Claude.md 규칙에 따른 Helper Agent의 LLM 요청 처리:
    - API 통합: claude-3-sonnet (안정성)
    - 대용량 데이터: gemini-pro (효율성)
    - 간단한 작업: claude-3-haiku (비용 효율)
    - 중요한 알림: claude-3-sonnet (정확성)

    ⚠️ EXCLUSIVE CONTROL: Helper Agent만 Helper 파일 수정 가능
    """

    def __init__(self):
        """Helper Agent 라우터 초기화"""
        self.router = LLMRouterClient()
        self.agent_name = "helper_agent"

        # MCP 통합 초기화 (EXCLUSIVE CONTROL)
        self.mcp_client = KoreaInvestmentMCP()

        # Helper Agent 작업 유형별 모델 매핑
        self.task_model_mapping = {
            "api_integration": "claude-3-sonnet-20240229",
            "data_processing": "gemini-pro",
            "credential_management": "claude-3-sonnet-20240229",
            "notification_services": "claude-3-sonnet-20240229",
            "simple_api_calls": "claude-3-haiku-20240307",
            "external_communication": "claude-3-sonnet-20240229",
            "webhook_processing": "claude-3-haiku-20240307",
            "rate_limit_management": "claude-3-haiku-20240307",
            # MCP 관련 작업 추가
            "mcp_integration": "claude-3-sonnet-20240229",
            "mcp_market_data": "claude-3-haiku-20240307",
            "mcp_trading": "claude-3-sonnet-20240229",
            "mcp_account_management": "claude-3-sonnet-20240229"
        }

        logger.info("Helper Agent Router initialized with EXCLUSIVE CONTROL")

    def process_api_integration(
        self,
        api_provider: str,
        integration_type: str,
        configuration: Dict[str, Any],
        requirements: Dict[str, Any] = None
    ) -> RouterResponse:
        """
        외부 API 통합 처리

        Args:
            api_provider: API 제공자
            integration_type: 통합 유형
            configuration: 설정 정보
            requirements: 요구사항

        Returns:
            RouterResponse: API 통합 결과
        """
        message = f"""
        Integrate external API with trading system:
        - Provider: {api_provider}
        - Integration type: {integration_type}
        - Configuration: {configuration}
        - Requirements: {requirements or 'standard'}

        Perform API integration:
        1. Authentication setup
        2. Endpoint configuration
        3. Rate limiting implementation
        4. Error handling setup
        5. Testing and validation
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="api_integration",
            message=message,
            context={
                "external_integration": True,
                "stability_critical": True,
                "provider": api_provider
            },
            preferences={
                "temperature": 0.2,  # 안정적인 통합
                "max_tokens": 2500
            }
        )

    def process_large_dataset(
        self,
        data_source: str,
        data_size: int,
        processing_type: str,
        output_format: str = "json"
    ) -> RouterResponse:
        """
        대용량 데이터 처리 (Gemini 모델 활용)

        Args:
            data_source: 데이터 소스
            data_size: 데이터 크기
            processing_type: 처리 유형
            output_format: 출력 형식

        Returns:
            RouterResponse: 데이터 처리 결과
        """
        # 대용량 데이터는 Gemini 모델 사용
        message = f"""
        Process large dataset efficiently:
        - Source: {data_source}
        - Size: {data_size} records
        - Processing: {processing_type}
        - Output format: {output_format}

        Execute data processing:
        1. Data ingestion optimization
        2. Batch processing strategy
        3. Memory management
        4. Quality validation
        5. Output generation
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="data_processing",
            message=message,
            context={
                "large_dataset": True,
                "performance_critical": True,
                "data_size": data_size
            },
            preferences={
                "temperature": 0.1,  # 정확한 처리
                "max_tokens": 2000
            }
        )

    def manage_api_credentials(
        self,
        credential_type: str,
        operation: str,
        security_level: str = "high"
    ) -> RouterResponse:
        """
        API 자격증명 관리 (EXCLUSIVE CONTROL)

        Args:
            credential_type: 자격증명 유형
            operation: 작업 (create, update, rotate, validate)
            security_level: 보안 수준

        Returns:
            RouterResponse: 자격증명 관리 결과
        """
        message = f"""
        Manage API credentials securely:
        - Credential type: {credential_type}
        - Operation: {operation}
        - Security level: {security_level}

        Execute credential management:
        1. Security validation
        2. Encryption handling
        3. Access control verification
        4. Audit logging
        5. Backup procedures
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="credential_management",
            message=message,
            context={
                "security_critical": True,
                "exclusive_access": True,
                "helper_only": True
            },
            preferences={
                "temperature": 0.1,  # 최고 보안
                "max_tokens": 1500
            }
        )

    def send_trading_notification(
        self,
        notification_type: str,
        message_data: Dict[str, Any],
        recipients: List[str],
        urgency: str = "normal"
    ) -> RouterResponse:
        """
        거래 알림 전송 처리

        Args:
            notification_type: 알림 유형
            message_data: 메시지 데이터
            recipients: 수신자 목록
            urgency: 긴급도

        Returns:
            RouterResponse: 알림 전송 결과
        """
        message = f"""
        Send trading notification:
        - Type: {notification_type}
        - Recipients: {len(recipients)} contacts
        - Urgency: {urgency}
        - Data: {message_data}

        Execute notification delivery:
        1. Message formatting
        2. Recipient validation
        3. Channel selection (Telegram/Email/SMS)
        4. Delivery confirmation
        5. Retry handling
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="notification_services",
            message=message,
            context={
                "communication": True,
                "time_sensitive": urgency in ["high", "critical"],
                "external_delivery": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 1500
            }
        )

    def execute_simple_api_call(
        self,
        endpoint: str,
        method: str,
        parameters: Dict[str, Any] = None,
        timeout: int = 30
    ) -> RouterResponse:
        """
        간단한 API 호출 실행 (비용 효율적)

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드
            parameters: 매개변수
            timeout: 타임아웃

        Returns:
            RouterResponse: API 호출 결과
        """
        message = f"""
        Execute simple API call:
        - Endpoint: {endpoint}
        - Method: {method}
        - Parameters: {parameters or 'none'}
        - Timeout: {timeout}s

        Perform API call:
        1. Request validation
        2. Authentication
        3. Call execution
        4. Response handling
        5. Error management
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="simple_api_calls",
            message=message,
            context={
                "simple_operation": True,
                "cost_optimization": True,
                "fast_response": True
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 800  # 간단한 응답
            }
        )

    def handle_webhook_request(
        self,
        webhook_source: str,
        payload_data: Dict[str, Any],
        validation_rules: Dict[str, Any]
    ) -> RouterResponse:
        """
        웹훅 요청 처리

        Args:
            webhook_source: 웹훅 소스
            payload_data: 페이로드 데이터
            validation_rules: 검증 규칙

        Returns:
            RouterResponse: 웹훅 처리 결과
        """
        message = f"""
        Process incoming webhook:
        - Source: {webhook_source}
        - Payload: {payload_data}
        - Validation rules: {validation_rules}

        Handle webhook processing:
        1. Source verification
        2. Payload validation
        3. Data extraction
        4. Action triggering
        5. Response generation
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="webhook_processing",
            message=message,
            context={
                "real_time_processing": True,
                "external_source": True,
                "validation_required": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 1200
            }
        )

    def manage_rate_limits(
        self,
        api_provider: str,
        current_usage: Dict[str, Any],
        limits: Dict[str, Any],
        optimization_strategy: str = "adaptive"
    ) -> RouterResponse:
        """
        API 사용량 및 레이트 리미트 관리

        Args:
            api_provider: API 제공자
            current_usage: 현재 사용량
            limits: 제한 설정
            optimization_strategy: 최적화 전략

        Returns:
            RouterResponse: 레이트 리미트 관리 결과
        """
        message = f"""
        Manage API rate limits:
        - Provider: {api_provider}
        - Current usage: {current_usage}
        - Limits: {limits}
        - Strategy: {optimization_strategy}

        Execute rate limit management:
        1. Usage monitoring
        2. Limit tracking
        3. Request queuing
        4. Priority handling
        5. Optimization recommendations
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="rate_limit_management",
            message=message,
            context={
                "resource_management": True,
                "optimization_focus": True,
                "provider": api_provider
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 1500
            }
        )

    def process_external_data_feed(
        self,
        feed_source: str,
        data_format: str,
        real_time: bool = True,
        processing_requirements: Dict[str, Any] = None
    ) -> RouterResponse:
        """
        외부 데이터 피드 처리

        Args:
            feed_source: 데이터 피드 소스
            data_format: 데이터 형식
            real_time: 실시간 여부
            processing_requirements: 처리 요구사항

        Returns:
            RouterResponse: 데이터 피드 처리 결과
        """
        message = f"""
        Process external data feed:
        - Source: {feed_source}
        - Format: {data_format}
        - Real-time: {real_time}
        - Requirements: {processing_requirements or 'standard'}

        Execute data feed processing:
        1. Connection establishment
        2. Data stream handling
        3. Format standardization
        4. Quality validation
        5. Downstream distribution
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="external_communication",
            message=message,
            context={
                "data_streaming": real_time,
                "external_integration": True,
                "continuous_processing": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 2000
            }
        )

    def get_model_for_cost_optimization(self, task_complexity: str) -> str:
        """
        비용 최적화를 위한 모델 선택

        Args:
            task_complexity: 작업 복잡도

        Returns:
            str: 최적 모델명
        """
        if task_complexity == "simple":
            return "claude-3-haiku-20240307"  # 가장 경제적
        elif task_complexity == "medium":
            return "claude-3-sonnet-20240229"
        elif task_complexity == "complex":
            return "claude-3-sonnet-20240229"
        else:  # large_data
            return "gemini-pro"  # 대용량 처리 최적

    def validate_helper_exclusive_access(self, operation: str) -> bool:
        """
        Helper Agent 독점 접근 권한 검증

        Args:
            operation: 수행하려는 작업

        Returns:
            bool: 접근 권한 여부
        """
        # Claude.md 규칙 4에 따른 Helper Agent 독점 접근 검증
        helper_exclusive_operations = [
            "credential_management",
            "helper_file_modification",
            "mystockinfo_update",
            "helper_test_execution"
        ]

        return operation in helper_exclusive_operations

    # ========== MCP 통합 메서드 (EXCLUSIVE CONTROL) ==========

    def activate_korea_investment_mcp(
        self,
        app_key: str,
        app_secret: str,
        test_connection: bool = True
    ) -> RouterResponse:
        """
        한국투자증권 MCP 활성화 매크로
        Claude.md 규칙 4에 따른 Helper Agent 독점 기능
        """
        message = f"""
        Activate Korea Investment MCP integration:
        - App Key: [PROVIDED]
        - App Secret: [PROVIDED]
        - Test Connection: {test_connection}

        Execute MCP activation:
        1. Validate credentials format
        2. Establish OAuth authentication
        3. Test API connectivity
        4. Enable trading features
        5. Start monitoring systems
        """

        # 실제 MCP 활성화 시도
        try:
            activation_success = self.mcp_client.activate_mcp(app_key, app_secret)

            if activation_success and test_connection:
                test_result = self.mcp_client.test_connectivity()
                if not test_result.success:
                    self.mcp_client.deactivate_mcp()
                    activation_success = False

            context = {
                "mcp_activation": True,
                "exclusive_control": True,
                "security_critical": True,
                "activation_result": activation_success
            }

        except Exception as e:
            logger.error(f"MCP activation error: {e}")
            context = {
                "mcp_activation": True,
                "exclusive_control": True,
                "security_critical": True,
                "activation_result": False,
                "error": str(e)
            }

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="mcp_integration",
            message=message,
            context=context,
            preferences={
                "temperature": 0.1,
                "max_tokens": 1500
            }
        )

    def deactivate_korea_investment_mcp(self) -> RouterResponse:
        """MCP 비활성화 매크로"""
        message = """
        Deactivate Korea Investment MCP integration:

        Execute MCP deactivation:
        1. Clear authentication tokens
        2. Disable API features
        3. Stop monitoring systems
        4. Clean up resources
        5. Update security logs
        """

        # 실제 MCP 비활성화
        deactivation_success = self.mcp_client.deactivate_mcp()

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="mcp_integration",
            message=message,
            context={
                "mcp_deactivation": True,
                "exclusive_control": True,
                "cleanup_operation": True,
                "deactivation_result": deactivation_success
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 1000
            }
        )

    def get_mcp_market_data(
        self,
        symbol: str,
        data_type: str = "current_price",
        market: str = "KOSPI"
    ) -> RouterResponse:
        """MCP를 통한 시장 데이터 조회"""
        message = f"""
        Retrieve market data via Korea Investment MCP:
        - Symbol: {symbol}
        - Data Type: {data_type}
        - Market: {market}

        Execute market data retrieval:
        1. Validate symbol format
        2. Check MCP connection status
        3. Make API request
        4. Process response data
        5. Return formatted results
        """

        # 실제 MCP 데이터 조회
        mcp_result = None
        try:
            if data_type == "current_price":
                mcp_result = self.mcp_client.get_current_price(symbol, market)
        except Exception as e:
            logger.error(f"MCP market data error: {e}")

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="mcp_market_data",
            message=message,
            context={
                "mcp_enabled": self.mcp_client.is_enabled,
                "market_data_request": True,
                "symbol": symbol,
                "mcp_result": mcp_result.data if mcp_result and mcp_result.success else None
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 1200
            }
        )

    def execute_mcp_trading_simulation(
        self,
        symbol: str,
        quantity: int,
        price: float,
        side: str
    ) -> RouterResponse:
        """MCP 거래 시뮬레이션 (실제 주문 아님)"""
        message = f"""
        Execute trading simulation via Korea Investment MCP:
        - Symbol: {symbol}
        - Quantity: {quantity}
        - Price: {price}
        - Side: {side}

        Execute trading simulation:
        1. Validate order parameters
        2. Check account status
        3. Simulate order placement
        4. Calculate estimated costs
        5. Return simulation results
        """

        # 실제 MCP 시뮬레이션
        simulation_result = None
        try:
            simulation_result = self.mcp_client.place_order(symbol, quantity, price, side)
        except Exception as e:
            logger.error(f"MCP trading simulation error: {e}")

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="mcp_trading",
            message=message,
            context={
                "mcp_enabled": self.mcp_client.is_enabled,
                "trading_simulation": True,
                "order_details": {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "side": side
                },
                "simulation_result": simulation_result.data if simulation_result and simulation_result.success else None
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 1500
            }
        )

    def get_mcp_account_status(self) -> RouterResponse:
        """MCP 계좌 상태 조회"""
        message = """
        Retrieve account status via Korea Investment MCP:

        Execute account status inquiry:
        1. Check MCP authentication
        2. Query account balance
        3. Get portfolio positions
        4. Check trading permissions
        5. Return account summary
        """

        # 실제 MCP 계좌 조회
        account_result = None
        try:
            account_result = self.mcp_client.get_account_balance()
        except Exception as e:
            logger.error(f"MCP account status error: {e}")

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="mcp_account_management",
            message=message,
            context={
                "mcp_enabled": self.mcp_client.is_enabled,
                "account_inquiry": True,
                "account_result": account_result.data if account_result and account_result.success else None
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 1500
            }
        )

    def test_mcp_connectivity(self) -> RouterResponse:
        """MCP 연결 테스트"""
        message = """
        Test Korea Investment MCP connectivity:

        Execute connectivity test:
        1. Check authentication status
        2. Test basic API call
        3. Validate response format
        4. Measure response time
        5. Report connection health
        """

        # 실제 MCP 연결 테스트
        test_result = None
        try:
            test_result = self.mcp_client.test_connectivity()
        except Exception as e:
            logger.error(f"MCP connectivity test error: {e}")

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="mcp_integration",
            message=message,
            context={
                "mcp_enabled": self.mcp_client.is_enabled,
                "connectivity_test": True,
                "test_result": test_result.data if test_result and test_result.success else None
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 1200
            }
        )

    def get_mcp_status(self) -> Dict[str, Any]:
        """MCP 상태 정보 반환"""
        return {
            "mcp_enabled": self.mcp_client.is_enabled,
            "provider": "korea_investment",
            "authenticated": self.mcp_client.credentials is not None,
            "token_valid": (
                self.mcp_client.credentials.access_token is not None
                if self.mcp_client.credentials else False
            ),
            "exclusive_control": True,
            "helper_agent_only": True
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Helper Agent 라우터 성능 지표"""
        return {
            **self.router.get_metrics(),
            "agent_name": self.agent_name,
            "specialized_tasks": list(self.task_model_mapping.keys()),
            "exclusive_control": True,
            "focus": "external_integration_and_cost_efficiency"
        }

# Example usage functions for Helper Agent
def integrate_new_broker_api(
    broker_name: str,
    api_endpoints: Dict[str, str],
    auth_method: str
) -> RouterResponse:
    """새 브로커 API 통합 예시"""
    router = HelperAgentRouter()
    return router.process_api_integration(
        api_provider=broker_name,
        integration_type="broker_trading_api",
        configuration={
            "endpoints": api_endpoints,
            "auth_method": auth_method,
            "rate_limits": {"calls_per_minute": 60}
        },
        requirements={
            "real_time_data": True,
            "order_execution": True,
            "account_info": True
        }
    )

def send_trade_alert(
    symbol: str,
    action: str,
    price: float,
    reason: str
) -> RouterResponse:
    """거래 알림 전송 예시"""
    router = HelperAgentRouter()
    return router.send_trading_notification(
        notification_type="trade_signal",
        message_data={
            "symbol": symbol,
            "action": action,
            "price": price,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        },
        recipients=["admin", "trader"],
        urgency="high"
    )

def fetch_market_data(
    provider: str,
    symbols: List[str],
    data_type: str = "quotes"
) -> RouterResponse:
    """시장 데이터 조회 예시"""
    router = HelperAgentRouter()

    if len(symbols) > 100:  # 대용량 데이터
        return router.process_large_dataset(
            data_source=provider,
            data_size=len(symbols),
            processing_type=data_type,
            output_format="json"
        )
    else:  # 간단한 API 호출
        return router.execute_simple_api_call(
            endpoint=f"/{provider}/quotes",
            method="GET",
            parameters={"symbols": ",".join(symbols), "type": data_type}
        )

# ========== MCP 사용 예시 함수들 (EXCLUSIVE CONTROL) ==========

def activate_mcp_with_credentials(app_key: str, app_secret: str) -> RouterResponse:
    """MCP 활성화 예시"""
    router = HelperAgentRouter()
    return router.activate_korea_investment_mcp(
        app_key=app_key,
        app_secret=app_secret,
        test_connection=True
    )

def get_samsung_electronics_price() -> RouterResponse:
    """삼성전자 현재가 조회 예시"""
    router = HelperAgentRouter()
    return router.get_mcp_market_data(
        symbol="005930",
        data_type="current_price",
        market="KOSPI"
    )

def simulate_stock_purchase(symbol: str, quantity: int, price: float) -> RouterResponse:
    """주식 매수 시뮬레이션 예시"""
    router = HelperAgentRouter()
    return router.execute_mcp_trading_simulation(
        symbol=symbol,
        quantity=quantity,
        price=price,
        side="buy"
    )

def check_account_balance() -> RouterResponse:
    """계좌 잔고 확인 예시"""
    router = HelperAgentRouter()
    return router.get_mcp_account_status()

def test_mcp_system() -> RouterResponse:
    """MCP 시스템 테스트 예시"""
    router = HelperAgentRouter()
    return router.test_mcp_connectivity()

def get_mcp_system_status() -> Dict[str, Any]:
    """MCP 시스템 상태 확인 예시"""
    router = HelperAgentRouter()
    return router.get_mcp_status()

# MCP 매크로 예시 사용법
def demo_mcp_workflow():
    """MCP 전체 워크플로우 데모"""
    router = HelperAgentRouter()

    print("=== MCP Demo Workflow ===")

    # 1. MCP 상태 확인
    status = router.get_mcp_status()
    print(f"MCP Status: {status}")

    # 2. MCP 활성화 (실제 credentials 필요)
    # activation = router.activate_korea_investment_mcp("APP_KEY", "APP_SECRET")

    # 3. 연결 테스트
    test_result = router.test_mcp_connectivity()
    print(f"Connectivity Test: {test_result.success if hasattr(test_result, 'success') else 'No test performed'}")

    # 4. 시장 데이터 조회
    market_data = router.get_mcp_market_data("005930", "current_price", "KOSPI")
    print(f"Market Data Request: {market_data.success if hasattr(market_data, 'success') else 'Processed'}")

    # 5. 계좌 상태 조회
    account_status = router.get_mcp_account_status()
    print(f"Account Status: {account_status.success if hasattr(account_status, 'success') else 'Processed'}")

    print("=== Demo Complete ===")

if __name__ == "__main__":
    # Helper Agent MCP 데모 실행
    demo_mcp_workflow()