"""
Prompt Generator for Multi-Agent System
Orchestrator가 Sub-Agent에게 전달할 프롬프트를 동적으로 생성합니다.

Version: 1.0
Created: 2025-10-09
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    """작업 타입 정의"""
    DATA_COLLECTION = "data_collection"
    DATA_ANALYSIS = "data_analysis"
    SIGNAL_GENERATION = "signal_generation"
    BACKTEST = "backtest"
    TRADING = "trading"
    REPORTING = "reporting"

class RequestType(Enum):
    """요청 타입 정의 (실행 vs 코드 수정)"""
    EXECUTION = "execution"        # 기존 코드 실행 (파일 실행, 함수 호출)
    CODE_MODIFICATION = "code_modification"  # 코드 수정 또는 추가

class CodeModificationPhase(Enum):
    """코드 수정 단계 정의"""
    PLANNING = "planning"          # 1단계: Plan 생성
    REVIEW = "review"              # 2단계: Orchestrator 리뷰
    IMPLEMENTATION = "implementation"  # 3단계: 코드 작업 수행

@dataclass
class PromptContext:
    """프롬프트 생성을 위한 컨텍스트"""
    task_type: TaskType
    request_type: RequestType  # 추가: 실행 vs 코드 수정
    user_request: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    modification_target: Dict[str, Any] = None  # 코드 수정 시: {layer, function, purpose}
    code_modification_phase: CodeModificationPhase = None  # 코드 수정 단계
    plan_data: Dict[str, Any] = None  # Plan 단계 데이터

class PromptGenerator:
    """
    프롬프트 생성기

    사용자 요청을 분석하여 각 Sub-Agent에게 적합한 프롬프트를 생성합니다.
    """

    def __init__(self):
        self.agent_templates = self._load_agent_templates()

    def _load_agent_templates(self) -> Dict[str, str]:
        """Agent별 프롬프트 템플릿"""
        return {
            "helper_agent": """
You are a Helper Agent specializing in external API integration and data collection.

**Your Task**: {task_description}

**Context**:
- User Request: {user_request}
- Parameters: {parameters}

**Your Responsibilities**:
1. Integrate with external APIs (KIS API, Alpha Vantage, Yahoo Finance)
2. Collect and validate data
3. Handle authentication and rate limiting
4. Return structured data

**Expected Output Format**:
```json
{{
    "status": "success" or "error",
    "data": {{...}},
    "metadata": {{
        "source": "api_name",
        "timestamp": "ISO 8601",
        "records_count": number
    }},
    "error": "error message if any"
}}
```

Please proceed with the task.
""",

            "database_agent": """
You are a Database Agent specializing in MongoDB data management.

**Your Task**: {task_description}

**Context**:
- User Request: {user_request}
- Parameters: {parameters}
- Database: {database_name}
- Collection: {collection_name}

**Your Responsibilities**:
1. Perform CRUD operations on MongoDB
2. Load historical market data (OHLCV, technical indicators)
3. Query data efficiently with proper indexes
4. Validate data schema and ensure integrity

**System Architecture**:
- Available Databases: NasDataBase_D (8,878 NASDAQ stocks), NysDataBase_D (6,235 NYSE stocks)
- Data includes: Daily/Weekly/Monthly OHLCV, Technical Indicators, Fundamentals, Earnings
- You DO NOT execute backtests - that's Service Agent's role
- You DO NOT generate signals - that's Strategy Agent's role

**Expected Output Format**:
```json
{{
    "status": "success" or "error",
    "operation": "insert/update/delete/read",
    "affected_documents": number,
    "data": {{...}},
    "error": "error message if any"
}}
```

Please proceed with the task.
""",

            "strategy_agent": """
You are a Strategy Agent specializing in trading signal generation.

**Your Task**: {task_description}

**Context**:
- User Request: {user_request}
- Market: {market}
- Symbols: {symbols}
- Timeframe: {timeframe}
- Strategy Type: {strategy_type}

**Your Responsibilities**:
1. Analyze market data and technical indicators provided by Database Agent
2. Generate BUY/SELL/HOLD signals with entry/exit prices
3. Calculate position sizes based on risk management rules
4. Provide confidence scores and detailed reasoning for each signal

**System Architecture**:
- You receive data from Database Agent (OHLCV, indicators, fundamentals)
- You DO NOT execute backtests - that's Service Agent's role
- You DO NOT access MongoDB directly - request data through Database Agent
- Your signals are used by Service Agent for backtesting or live trading

**Expected Output Format**:
```json
{{
    "signals": [
        {{
            "symbol": "TICKER",
            "signal": "BUY/SELL/HOLD",
            "confidence": 0.0-1.0,
            "entry_price": number,
            "target_price": number,
            "stop_loss": number,
            "position_size": number,
            "reasoning": "explanation"
        }}
    ],
    "metadata": {{
        "timestamp": "ISO 8601",
        "strategy": "strategy_name",
        "total_signals": number
    }}
}}
```

Please proceed with the task.
""",

            "service_agent": """
You are a Service Agent specializing in backtesting and portfolio management.

**Your Task**: {task_description}

**Context**:
- User Request: {user_request}
- Parameters: {parameters}
- Initial Cash: {initial_cash}
- Period: {start_date} to {end_date}

**Your Responsibilities**:
1. Execute backtest simulations using signals from Strategy Agent
2. Manage portfolio positions (entry/exit, position sizing)
3. Calculate comprehensive performance metrics (returns, Sharpe, drawdown, etc.)
4. Generate detailed trade-by-trade reports

**System Architecture**:
- You receive trading signals from Strategy Agent
- You receive historical data from Database Agent
- You DO NOT generate signals - that's Strategy Agent's role
- You DO NOT access MongoDB directly - request data through Database Agent
- Your role is EXECUTION and PERFORMANCE ANALYSIS

**Expected Output Format**:
```json
{{
    "backtest_result": {{
        "total_return": number,
        "sharpe_ratio": number,
        "max_drawdown": number,
        "win_rate": number,
        "total_trades": number,
        "profit_factor": number
    }},
    "trades": [
        {{
            "date": "ISO 8601",
            "symbol": "TICKER",
            "action": "BUY/SELL",
            "quantity": number,
            "price": number,
            "pnl": number
        }}
    ],
    "portfolio_summary": {{
        "final_value": number,
        "max_positions": number,
        "avg_holding_period": number
    }}
}}
```

Please proceed with the task.
""",

            "run_agent": """
You are a RUN Agent specializing in file execution and process management.

**Your Task**: {task_description}

**Context**:
- User Request: {user_request}
- Parameters: {parameters}
- File Path: {file_path}
- Arguments: {args}

**Your Responsibilities**:
1. Execute Python scripts (.py files)
2. Monitor process execution and status
3. Capture output (stdout/stderr)
4. Report execution results with timing and status
5. Manage file system operations

**System Architecture**:
- You are a PEER-LEVEL agent (same level as Helper, Database, Strategy, Service)
- You DO NOT manage other agents - that's Orchestrator's role
- You specialize in FILE EXECUTION and PROCESS MANAGEMENT
- You work independently from other agents

**Expected Output Format**:
```json
{{
    "status": "success" or "error" or "timeout",
    "file_path": "path/to/file.py",
    "return_code": number,
    "stdout": "standard output",
    "stderr": "standard error",
    "duration": number (seconds),
    "start_time": "ISO 8601",
    "end_time": "ISO 8601"
}}
```

Please proceed with the task.
"""
        }

    def generate_prompt(
        self,
        agent_name: str,
        context: PromptContext
    ) -> str:
        """
        Agent와 컨텍스트에 맞는 프롬프트 생성

        Args:
            agent_name: Agent 이름 (helper_agent, database_agent, etc.)
            context: 프롬프트 컨텍스트

        Returns:
            생성된 프롬프트 문자열
        """
        # Request Type에 따라 다른 프롬프트 생성
        if context.request_type == RequestType.CODE_MODIFICATION:
            return self._generate_code_modification_prompt(agent_name, context)
        else:
            return self._generate_execution_prompt(agent_name, context)

    def _generate_execution_prompt(
        self,
        agent_name: str,
        context: PromptContext
    ) -> str:
        """
        실행(EXECUTION) 요청에 대한 프롬프트 생성

        기존 코드를 수정하지 않고 정해진 입력 형태에 따라 프롬프트 전달 및 실행
        """
        template = self.agent_templates.get(agent_name)

        if not template:
            # 기본 템플릿
            template = """
You are a {agent_name}.

**Task**: {task_description}
**User Request**: {user_request}
**Parameters**: {parameters}

Please complete this task and return the result in a structured format.
"""

        # 템플릿 변수 채우기
        template_vars = {
            'agent_name': agent_name.replace('_', ' ').title(),
            'task_description': self._generate_task_description(context, agent_name),
            'user_request': context.user_request,
            'parameters': self._format_parameters(context.parameters),
            # 기본값 제공
            'database_name': context.parameters.get('database_name', 'NasDataBase_D'),
            'collection_name': context.parameters.get('collection_name', ''),
            'market': context.parameters.get('market', 'US'),
            'symbols': context.parameters.get('symbols', []),
            'timeframe': context.parameters.get('timeframe', '1d'),
            'strategy_type': context.parameters.get('strategy_type', 'momentum'),
            'initial_cash': context.parameters.get('initial_cash', 100000.0),
            'start_date': context.parameters.get('start_date', ''),
            'end_date': context.parameters.get('end_date', ''),
            # RUN_AGENT 관련 파라미터
            'file_path': context.parameters.get('file_path', ''),
            'args': context.parameters.get('args', [])
        }

        # 추가 파라미터 병합
        template_vars.update(context.parameters)

        prompt = template.format(**template_vars)

        # 의존성 정보 추가
        if context.dependencies:
            prompt += f"\n\n**Dependencies**: This task depends on: {', '.join(context.dependencies)}"

        return prompt

    def _generate_code_modification_prompt(
        self,
        agent_name: str,
        context: PromptContext
    ) -> str:
        """
        코드 수정(CODE_MODIFICATION) 요청에 대한 프롬프트 생성

        단계별 처리:
        1. PLANNING: Sub-Agent가 Plan 생성
        2. REVIEW: Orchestrator가 Plan 리뷰
        3. IMPLEMENTATION: Sub-Agent가 승인된 Plan 기반으로 코드 작업 수행
        """
        # 단계 결정 (기본값: PLANNING)
        phase = context.code_modification_phase or CodeModificationPhase.PLANNING

        if phase == CodeModificationPhase.PLANNING:
            return self._generate_planning_prompt(agent_name, context)
        elif phase == CodeModificationPhase.IMPLEMENTATION:
            return self._generate_implementation_prompt(agent_name, context)
        else:
            # REVIEW 단계는 Orchestrator가 직접 처리
            return ""

    def _generate_planning_prompt(
        self,
        agent_name: str,
        context: PromptContext
    ) -> str:
        """
        PLANNING 단계: Sub-Agent가 Plan을 생성하는 프롬프트
        """
        # Layer Architecture 컨텍스트
        layer_architecture = self._get_layer_architecture_context()

        # 수정 대상 분석
        modification_target = context.modification_target or self._analyze_modification_target(
            context.user_request,
            context.task_type
        )

        prompt = f"""
You are a {agent_name.replace('_', ' ').title()} responsible for code modification.

**Request Type**: CODE MODIFICATION - PLANNING PHASE
**User Request**: {context.user_request}

## Layer Architecture Context

{layer_architecture}

## Modification Target

**Layer**: {modification_target.get('layer', 'Not specified')}
**Target File**: {modification_target.get('file_path', 'Not specified')}
**Target Component**: {modification_target.get('component_type', 'function')} - {modification_target.get('component_name', 'To be determined')}

## Required Modifications

**Purpose**: {modification_target.get('purpose', context.user_request)}

**Specifications**:
{self._format_modification_specifications(modification_target)}

## Agent Responsibilities

As {agent_name.replace('_', ' ').title()}, you are responsible for:
{self._get_agent_modification_responsibilities(agent_name)}

## PLANNING PHASE INSTRUCTIONS

**IMPORTANT**: This is the PLANNING phase. You must ONLY generate a detailed plan.
DO NOT implement any code changes at this stage.

Your plan will be reviewed by the Orchestrator Agent before implementation.

## Output Requirements

Please provide a comprehensive plan in the following JSON format:

```json
{{
    "phase": "planning",
    "analysis": {{
        "current_code_structure": "Detailed analysis of existing code in target layer/file",
        "identified_issues": ["Issue 1", "Issue 2"],
        "modification_scope": "Scope of changes needed"
    }},
    "function_specification": {{
        "name": "function_name",
        "parameters": [
            {{"name": "param1", "type": "type1", "description": "Purpose of param1"}},
            {{"name": "param2", "type": "type2", "description": "Purpose of param2"}}
        ],
        "return_type": "return_type",
        "return_description": "What this function returns",
        "purpose": "Clear description of what this function does",
        "algorithm": "High-level algorithm description"
    }},
    "implementation_plan": {{
        "steps": [
            {{
                "step_number": 1,
                "description": "Step description",
                "files_to_modify": ["file1.py"],
                "estimated_complexity": "low/medium/high"
            }}
        ],
        "dependencies": ["Dependency 1", "Dependency 2"],
        "risks": ["Risk 1", "Risk 2"]
    }},
    "interface_impact": {{
        "affected_layers": ["layer1", "layer2"],
        "affected_files": ["file1.py", "file2.py"],
        "interface_changes": [
            {{
                "type": "new_function/modify_signature/new_parameter",
                "description": "Description of change",
                "backward_compatible": true/false
            }}
        ],
        "migration_needed": true/false
    }},
    "test_requirements": {{
        "unit_tests": ["Test case 1", "Test case 2"],
        "integration_tests": ["Integration test 1"],
        "test_data_needed": ["Data requirement 1"]
    }},
    "estimated_effort": {{
        "hours": 2.5,
        "complexity": "low/medium/high",
        "confidence": 0.85
    }}
}}
```

**Parameters**: {self._format_parameters(context.parameters)}
"""

        return prompt

    def _generate_implementation_prompt(
        self,
        agent_name: str,
        context: PromptContext
    ) -> str:
        """
        IMPLEMENTATION 단계: 승인된 Plan을 기반으로 코드를 작성하는 프롬프트
        """
        plan_data = context.plan_data or {}

        prompt = f"""
You are a {agent_name.replace('_', ' ').title()} responsible for code modification.

**Request Type**: CODE MODIFICATION - IMPLEMENTATION PHASE
**User Request**: {context.user_request}

## Approved Plan

The following plan has been reviewed and approved by the Orchestrator:

```json
{self._format_plan_summary(plan_data)}
```

## IMPLEMENTATION PHASE INSTRUCTIONS

**IMPORTANT**: This is the IMPLEMENTATION phase. You must now implement the approved plan.

Follow these guidelines:
1. Implement exactly according to the approved plan
2. Maintain interface compatibility as specified
3. Follow project coding standards (see CLAUDE.md)
4. Add appropriate docstrings and comments
5. Include error handling and validation
6. Ensure backward compatibility if specified in plan

## Required Output

Provide the implementation in the following JSON format:

```json
{{
    "phase": "implementation",
    "implemented_changes": [
        {{
            "file_path": "path/to/file.py",
            "change_type": "new_function/modify_function/new_class",
            "code": "Complete code implementation",
            "line_number": "Insert at line N or append",
            "description": "What this change does"
        }}
    ],
    "tests_implemented": [
        {{
            "test_file": "path/to/test_file.py",
            "test_code": "Complete test code",
            "description": "What this test verifies"
        }}
    ],
    "documentation_updates": [
        {{
            "file_path": "path/to/doc.md",
            "updates": "Documentation changes needed"
        }}
    ],
    "verification": {{
        "all_tests_pass": true/false,
        "interface_compatible": true/false,
        "no_breaking_changes": true/false
    }},
    "notes": "Any important notes about the implementation"
}}
```

**Parameters**: {self._format_parameters(context.parameters)}
"""

        return prompt

    def _generate_task_description(self, context: PromptContext, agent_name: str = None) -> str:
        """
        Agent별, 작업 타입에 따른 정확한 설명 생성

        각 Agent는 전체 워크플로우에서 자신의 역할만 수행해야 합니다.
        """
        # Agent별 전문 영역 정의
        agent_specializations = {
            "helper_agent": {
                TaskType.DATA_COLLECTION: "Collect market data from external APIs (KIS API, Alpha Vantage, Yahoo Finance)",
                TaskType.DATA_ANALYSIS: "Fetch additional data needed for analysis",
                TaskType.SIGNAL_GENERATION: "Provide real-time market data for signal generation",
                TaskType.BACKTEST: "Retrieve historical fundamental data if needed",
                TaskType.REPORTING: "Gather external performance benchmarks"
            },
            "database_agent": {
                TaskType.DATA_COLLECTION: "Store collected data in MongoDB with validation",
                TaskType.DATA_ANALYSIS: "Query and retrieve data from MongoDB for analysis",
                TaskType.SIGNAL_GENERATION: "Load historical price and volume data from MongoDB",
                TaskType.BACKTEST: "Load multi-year historical data from MongoDB (OHLCV, indicators)",
                TaskType.REPORTING: "Retrieve trading history and performance data from MongoDB"
            },
            "strategy_agent": {
                TaskType.DATA_COLLECTION: "Not applicable - Strategy Agent does not collect data",
                TaskType.DATA_ANALYSIS: "Analyze market patterns and identify trading opportunities",
                TaskType.SIGNAL_GENERATION: "Generate BUY/SELL/HOLD signals with confidence scores",
                TaskType.BACKTEST: "Generate historical trading signals for backtest period",
                TaskType.REPORTING: "Provide strategy performance analysis and signal statistics"
            },
            "service_agent": {
                TaskType.DATA_COLLECTION: "Not applicable - Service Agent does not collect data",
                TaskType.DATA_ANALYSIS: "Calculate portfolio metrics and risk analytics",
                TaskType.SIGNAL_GENERATION: "Not applicable - Service Agent does not generate signals",
                TaskType.BACKTEST: "Execute backtest simulation using provided signals and calculate performance metrics",
                TaskType.REPORTING: "Generate comprehensive backtest reports and visualizations"
            },
            "run_agent": {
                TaskType.DATA_COLLECTION: "Not applicable - RUN Agent does not collect data",
                TaskType.DATA_ANALYSIS: "Execute analysis scripts and aggregate results",
                TaskType.SIGNAL_GENERATION: "Not applicable - RUN Agent does not generate signals",
                TaskType.BACKTEST: "Execute backtest Python scripts and capture execution results",
                TaskType.TRADING: "Execute trading scripts and monitor process status",
                TaskType.REPORTING: "Execute reporting scripts and collect output files"
            }
        }

        if agent_name and agent_name in agent_specializations:
            task_map = agent_specializations[agent_name]
            description = task_map.get(context.task_type)
            if description:
                return description

        # Fallback: 일반적인 설명
        descriptions = {
            TaskType.DATA_COLLECTION: "Collect and validate data from external sources",
            TaskType.DATA_ANALYSIS: "Analyze data and extract insights",
            TaskType.SIGNAL_GENERATION: "Generate trading signals based on analysis",
            TaskType.BACKTEST: "Execute backtest simulation and evaluate performance",
            TaskType.TRADING: "Execute trading orders and manage positions",
            TaskType.REPORTING: "Generate comprehensive reports and analytics"
        }
        return descriptions.get(context.task_type, "Complete the assigned task")

    def _format_parameters(self, params: Dict[str, Any]) -> str:
        """파라미터를 읽기 쉬운 형식으로 포맷"""
        if not params:
            return "None"

        formatted = []
        for key, value in params.items():
            formatted.append(f"  - {key}: {value}")

        return "\n".join(formatted)

    def _get_layer_architecture_context(self) -> str:
        """
        프로젝트의 Layer Architecture 컨텍스트 반환
        """
        return """
The project follows a multi-layer architecture:

1. **Helper Layer** (project/Helper/)
   - External API integration (KIS API, Alpha Vantage, Yahoo Finance)
   - System configuration management
   - MongoDB connection management
   - Files: kis_api_helper_us.py, mongo_config.py, etc.

2. **Data/Indicator Layer** (project/indicator/)
   - MongoDB data loading and validation
   - Technical indicator calculation (SMA, ADR, ATR, RS, etc.)
   - Data transformation (Market DB → Strategy Layer format)
   - Files: load_indicator.py, calculate_indicators.py, etc.

3. **Strategy Layer** (project/strategy/)
   - Trading signal generation (BUY/SELL/HOLD)
   - Universe selection and filtering
   - Market-specific strategies (NASDAQ vs NYSE)
   - Files: strategy_us.py, signal_generator.py, etc.

4. **Service Layer** (project/service/)
   - Backtest execution and portfolio management
   - Risk management and position sizing
   - Performance analysis and reporting
   - Files: daily_backtest_service.py, portfolio_manager.py, etc.

**Data Flow**: Helper → Data/Indicator → Strategy → Service

**Interface Standards**: Defined in docs/INTERFACE_SPECIFICATION.md
"""

    def _analyze_modification_target(self, user_request: str, task_type: TaskType) -> Dict[str, Any]:
        """
        사용자 요청과 작업 타입을 기반으로 수정 대상 분석
        """
        user_request_lower = user_request.lower()

        # Layer 결정
        layer = "Not specified"
        file_path = "Not specified"

        if any(keyword in user_request_lower for keyword in ['api', 'helper', 'external', 'kis', 'alpha']):
            layer = "Helper Layer"
            file_path = "project/Helper/"
        elif any(keyword in user_request_lower for keyword in ['indicator', 'data', 'mongodb', 'load', 'calculate']):
            layer = "Data/Indicator Layer"
            file_path = "project/indicator/"
        elif any(keyword in user_request_lower for keyword in ['strategy', 'signal', 'universe', 'buy', 'sell']):
            layer = "Strategy Layer"
            file_path = "project/strategy/"
        elif any(keyword in user_request_lower for keyword in ['backtest', 'service', 'portfolio', 'risk']):
            layer = "Service Layer"
            file_path = "project/service/"

        # Component 타입 결정
        component_type = "function"
        if any(keyword in user_request_lower for keyword in ['class', 'agent', 'manager', 'handler']):
            component_type = "class"
        elif any(keyword in user_request_lower for keyword in ['method']):
            component_type = "method"

        return {
            "layer": layer,
            "file_path": file_path,
            "component_type": component_type,
            "component_name": "To be determined by agent",
            "purpose": user_request,
            "modifications": []
        }

    def _format_modification_specifications(self, modification_target: Dict[str, Any]) -> str:
        """
        수정 사양을 포맷팅하여 반환
        """
        specs = []

        if modification_target.get('modifications'):
            for mod in modification_target['modifications']:
                specs.append(f"- {mod}")
        else:
            specs.append("- Analyze the user request and determine specific modifications needed")
            specs.append("- Follow interface specifications in docs/INTERFACE_SPECIFICATION.md")
            specs.append("- Maintain compatibility with existing code")

        return "\n".join(specs)

    def _get_agent_modification_responsibilities(self, agent_name: str) -> str:
        """
        Agent별 코드 수정 책임 반환
        """
        responsibilities = {
            "helper_agent": """
- Modifying external API integration logic
- Updating system configuration handling
- Improving MongoDB connection management
- Adding new data sources or API endpoints
""",
            "database_agent": """
- Modifying data loading and validation logic
- Updating technical indicator calculations
- Improving data transformation between layers
- Optimizing MongoDB queries and data access
""",
            "strategy_agent": """
- Modifying trading signal generation logic
- Updating universe selection criteria
- Improving market-specific strategy implementations
- Adding new trading strategies or filters
""",
            "service_agent": """
- Modifying backtest execution logic
- Updating portfolio management algorithms
- Improving risk management rules
- Adding new performance metrics or reports
""",
            "run_agent": """
- Modifying file execution and process management
- Updating execution monitoring and logging
- Improving error handling and recovery
- Adding new execution modes or workflows
"""
        }

        return responsibilities.get(agent_name, "- General code modification and improvement")

    def _format_plan_summary(self, plan_data: Dict[str, Any]) -> str:
        """
        Plan 데이터를 요약하여 JSON 문자열로 포맷팅
        """
        import json

        if not plan_data:
            return "{}"

        # 주요 필드만 추출하여 요약
        summary = {
            "phase": plan_data.get("phase", "planning"),
            "function_name": plan_data.get("function_specification", {}).get("name", ""),
            "purpose": plan_data.get("function_specification", {}).get("purpose", ""),
            "implementation_steps": len(plan_data.get("implementation_plan", {}).get("steps", [])),
            "affected_layers": plan_data.get("interface_impact", {}).get("affected_layers", []),
            "estimated_effort": plan_data.get("estimated_effort", {}),
            "full_plan": plan_data  # 전체 Plan도 포함
        }

        return json.dumps(summary, indent=2, ensure_ascii=False)

    def _determine_request_type(self, user_input_lower: str) -> RequestType:
        """
        사용자 요청이 실행인지 코드 수정인지 결정

        실행 (EXECUTION) 키워드:
        - 실행, execute, run, 테스트, test, 백테스트, backtest
        - 조회, query, 검색, search, 확인, check
        - 생성 (시그널, 리포트 등), generate

        코드 수정 (CODE_MODIFICATION) 키워드:
        - 수정, modify, change, update, fix
        - 추가, add, create, implement
        - 개선, improve, refactor, optimize
        - 함수, function, 메서드, method, 클래스, class
        """
        # 실행 키워드
        execution_keywords = [
            'backtest', '백테스트', 'run', '실행', 'execute',
            'test', '테스트', 'check', '확인', 'query', '조회',
            'search', '검색', 'generate', '생성',
            'show', '보여', 'display', '표시', 'get', '가져'
        ]

        # 코드 수정 키워드
        modification_keywords = [
            'modify', '수정', 'change', '변경', 'update', '업데이트',
            'add', '추가', 'create', '만들', 'implement', '구현',
            'fix', '고치', 'improve', '개선', 'refactor', '리팩토링',
            'optimize', '최적화', 'function', '함수', 'method', '메서드',
            'class', '클래스', 'code', '코드'
        ]

        # 코드 수정 키워드가 있으면 CODE_MODIFICATION
        if any(keyword in user_input_lower for keyword in modification_keywords):
            return RequestType.CODE_MODIFICATION

        # 실행 키워드가 있거나, 키워드가 없으면 기본적으로 EXECUTION
        return RequestType.EXECUTION

    def parse_user_request(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 입력을 분석하여 어떤 Agent들이 필요한지 결정

        Args:
            user_input: 사용자 요청 문자열

        Returns:
            분석 결과 딕셔너리
        """
        user_input_lower = user_input.lower()

        result = {
            "agents_needed": [],
            "task_type": None,
            "request_type": None,  # 추가
            "parameters": {},
            "workflow": [],
            "modification_target": None  # 추가
        }

        # 1단계: Request Type 결정 (실행 vs 코드 수정)
        result["request_type"] = self._determine_request_type(user_input_lower)

        # 키워드 기반 Agent 매칭
        if any(keyword in user_input_lower for keyword in ['backtest', '백테스트', 'test strategy']):
            result["task_type"] = TaskType.BACKTEST
            result["agents_needed"] = ["run_agent"]
            result["workflow"] = [
                {"agent": "run_agent", "task": "Execute main_auto_trade.py for backtest"}
            ]
            # 백테스트 파일 경로 설정
            result["parameters"]["file_path"] = "main_auto_trade.py"
            result["parameters"]["backtest_mode"] = True

        elif any(keyword in user_input_lower for keyword in ['signal', '시그널', 'buy', 'sell']):
            result["task_type"] = TaskType.SIGNAL_GENERATION
            result["agents_needed"] = ["database_agent", "strategy_agent"]
            result["workflow"] = [
                {"agent": "database_agent", "task": "Load market data"},
                {"agent": "strategy_agent", "task": "Generate trading signals"}
            ]

        elif any(keyword in user_input_lower for keyword in ['data', '데이터', 'collect', 'fetch']):
            result["task_type"] = TaskType.DATA_COLLECTION
            result["agents_needed"] = ["helper_agent", "database_agent"]
            result["workflow"] = [
                {"agent": "helper_agent", "task": "Collect data from APIs"},
                {"agent": "database_agent", "task": "Store data in MongoDB"}
            ]

        elif any(keyword in user_input_lower for keyword in ['analyze', '분석', 'report', 'performance']):
            result["task_type"] = TaskType.REPORTING
            result["agents_needed"] = ["database_agent", "service_agent"]
            result["workflow"] = [
                {"agent": "database_agent", "task": "Load performance data"},
                {"agent": "service_agent", "task": "Generate analysis report"}
            ]

        else:
            # 기본: 모든 Agent 활성화
            result["task_type"] = TaskType.DATA_ANALYSIS
            result["agents_needed"] = ["helper_agent", "database_agent", "strategy_agent", "service_agent"]

        # 파라미터 추출 (간단한 예시)
        if "nasdaq" in user_input_lower or "nyse" in user_input_lower:
            result["parameters"]["market"] = "NASDAQ" if "nasdaq" in user_input_lower else "NYSE"

        # 날짜 추출 (간단한 예시)
        import re
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, user_input)
        if len(dates) >= 2:
            result["parameters"]["start_date"] = dates[0]
            result["parameters"]["end_date"] = dates[1]

        return result

# 사용 예시
if __name__ == "__main__":
    generator = PromptGenerator()

    # 예시 1: 백테스트 요청
    user_request = "NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘"
    analysis = generator.parse_user_request(user_request)

    print("=" * 60)
    print("User Request Analysis")
    print("=" * 60)
    print(f"Task Type: {analysis['task_type']}")
    print(f"Agents Needed: {analysis['agents_needed']}")
    print(f"Parameters: {analysis['parameters']}")
    print(f"\nWorkflow:")
    for step in analysis['workflow']:
        print(f"  {step['agent']}: {step['task']}")

    # 예시 2: Strategy Agent 프롬프트 생성
    context = PromptContext(
        task_type=TaskType.SIGNAL_GENERATION,
        user_request=user_request,
        parameters={
            "market": "NASDAQ",
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "timeframe": "1d",
            "strategy_type": "momentum"
        },
        dependencies=["database_agent"]
    )

    prompt = generator.generate_prompt("strategy_agent", context)

    print("\n" + "=" * 60)
    print("Generated Prompt for Strategy Agent")
    print("=" * 60)
    print(prompt)
