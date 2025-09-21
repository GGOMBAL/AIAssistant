#!/usr/bin/env python3
"""
Production Orchestrator System
실제 프로젝트와 연동되는 오케스트레이터 시스템
"""

import os
import sys
import json
import asyncio
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator_reviewer import WorkflowOrchestrator, OrchestratorReviewer, AgentStorageManager
from orchestrator.main_orchestrator import MainOrchestrator

class ProductionOrchestrator:
    """실제 프로젝트용 오케스트레이터"""

    def __init__(self):
        self.config = self._load_project_config()
        self.workflow_orchestrator = WorkflowOrchestrator()
        self.storage_manager = AgentStorageManager()
        self.session_log = []

        # 프로젝트 디렉토리 설정
        self.project_dirs = {
            'data': Path("Project/indicator"),
            'strategy': Path("Project/strategy"),
            'service': Path("Project/service"),
            'helper': Path("Project/Helper"),
            'logs': Path("logs/orchestrator"),
            'outputs': Path("outputs/agent_results")
        }

        # 디렉토리 생성
        for dir_path in self.project_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_project_config(self) -> Dict[str, Any]:
        """프로젝트 설정 로드"""
        try:
            config_files = [
                "config/agent_model.yaml",
                "config/api_credentials.yaml",
                "config/broker_config.yaml",
                "config/risk_management.yaml"
            ]

            config = {}
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        file_config = yaml.safe_load(f)
                        config.update(file_config)

            return config
        except Exception as e:
            print(f"[ERROR] Failed to load project config: {e}")
            return {}

    def _log_session(self, message: str, level: str = "INFO"):
        """세션 로그 기록"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.session_log.append(log_entry)

        # 콘솔 출력
        print(f"[{timestamp}] [{level}] {message}")

        # 로그 파일 저장
        log_file = self.project_dirs['logs'] / f"session_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    async def execute_trading_workflow(self, user_request: str, workflow_type: str = "comprehensive") -> Dict[str, Any]:
        """트레이딩 워크플로우 실행"""

        self._log_session(f"Starting trading workflow: {workflow_type}", "INFO")
        self._log_session(f"User request: {user_request}", "INFO")

        try:
            # 1. 워크플로우 실행
            result = await self.workflow_orchestrator.process_complete_workflow(user_request)

            if 'error' in result:
                self._log_session(f"Workflow failed: {result['error']}", "ERROR")
                return result

            # 2. 결과 분석 및 실제 프로젝트 파일 생성
            project_integration = await self._integrate_with_project_files(result)

            # 3. 최종 결과 패키징
            final_result = {
                "workflow_id": result["workflow_id"],
                "user_request": user_request,
                "workflow_type": workflow_type,
                "execution_timestamp": datetime.now().isoformat(),
                "agent_results": result["agent_summaries"],
                "project_integration": project_integration,
                "quality_metrics": self._calculate_quality_metrics(result),
                "next_actions": self._suggest_next_actions(result)
            }

            # 4. 결과 저장
            await self._save_workflow_result(final_result)

            self._log_session("Trading workflow completed successfully", "SUCCESS")
            return final_result

        except Exception as e:
            self._log_session(f"Workflow execution failed: {str(e)}", "ERROR")
            return {"error": f"Workflow execution failed: {str(e)}"}

    async def _integrate_with_project_files(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 결과를 실제 프로젝트 파일과 연동"""

        integration_results = {
            "files_created": [],
            "files_updated": [],
            "indicators_generated": [],
            "strategies_created": [],
            "services_configured": []
        }

        for agent_summary in workflow_result.get("agent_summaries", []):
            agent_name = agent_summary.get("agent_name")

            if agent_name == "data_agent":
                # 데이터 에이전트 결과 → 인디케이터 파일 생성
                indicator_files = await self._create_indicator_files(agent_summary)
                integration_results["indicators_generated"].extend(indicator_files)

            elif agent_name == "strategy_agent":
                # 전략 에이전트 결과 → 전략 파일 생성
                strategy_files = await self._create_strategy_files(agent_summary)
                integration_results["strategies_created"].extend(strategy_files)

            elif agent_name == "service_agent":
                # 서비스 에이전트 결과 → 서비스 설정 파일 생성
                service_files = await self._create_service_files(agent_summary)
                integration_results["services_configured"].extend(service_files)

            elif agent_name == "helper_agent":
                # 헬퍼 에이전트 결과 → 헬퍼 파일 생성
                helper_files = await self._create_helper_files(agent_summary)
                integration_results["files_created"].extend(helper_files)

        return integration_results

    async def _create_indicator_files(self, agent_summary: Dict[str, Any]) -> List[str]:
        """데이터 에이전트 결과로 인디케이터 파일 생성"""
        files_created = []

        try:
            # 인디케이터 파일 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 1. 데이터 수집 스크립트 생성
            data_collector_file = self.project_dirs['data'] / f"data_collector_{timestamp}.py"
            data_collector_content = f'''#!/usr/bin/env python3
"""
Data Collector - Generated by Orchestrator
Generated: {datetime.now().isoformat()}
Based on agent analysis: {agent_summary.get("interaction_id", "")}
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

class DataCollector:
    """데이터 수집기"""

    def __init__(self):
        self.data_sources = []

    def collect_market_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        """시장 데이터 수집"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            print(f"Data collection failed for {{symbol}}: {{e}}")
            return pd.DataFrame()

    def validate_data(self, df: pd.DataFrame) -> bool:
        """데이터 검증"""
        if df.empty:
            return False

        # 기본 검증 로직
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        return all(col in df.columns for col in required_columns)

    def save_to_database(self, df: pd.DataFrame, table_name: str):
        """데이터베이스에 저장"""
        # 실제 데이터베이스 저장 로직 구현
        print(f"Saving {{len(df)}} records to {{table_name}}")

# Agent Response Summary:
# {agent_summary.get("final_output", agent_summary.get("response", ""))[:500]}...
'''

            with open(data_collector_file, 'w', encoding='utf-8') as f:
                f.write(data_collector_content)

            files_created.append(str(data_collector_file))

            # 2. 인디케이터 계산 스크립트 생성
            indicator_file = self.project_dirs['data'] / f"indicators_{timestamp}.py"
            indicator_content = f'''#!/usr/bin/env python3
"""
Technical Indicators - Generated by Orchestrator
Generated: {datetime.now().isoformat()}
"""

import pandas as pd
import numpy as np
import talib

class TechnicalIndicators:
    """기술적 지표 계산"""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """단순이동평균"""
        return df['Close'].rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """RSI 지표"""
        return talib.RSI(df['Close'].values, timeperiod=period)

    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """MACD 지표"""
        macd, signal, histogram = talib.MACD(df['Close'].values)
        return {{
            'macd': pd.Series(macd, index=df.index),
            'signal': pd.Series(signal, index=df.index),
            'histogram': pd.Series(histogram, index=df.index)
        }}
'''

            with open(indicator_file, 'w', encoding='utf-8') as f:
                f.write(indicator_content)

            files_created.append(str(indicator_file))

            self._log_session(f"Created {len(files_created)} indicator files", "INFO")

        except Exception as e:
            self._log_session(f"Failed to create indicator files: {e}", "ERROR")

        return files_created

    async def _create_strategy_files(self, agent_summary: Dict[str, Any]) -> List[str]:
        """전략 에이전트 결과로 전략 파일 생성"""
        files_created = []

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 전략 클래스 생성
            strategy_file = self.project_dirs['strategy'] / f"trading_strategy_{timestamp}.py"
            strategy_content = f'''#!/usr/bin/env python3
"""
Trading Strategy - Generated by Orchestrator
Generated: {datetime.now().isoformat()}
Based on agent analysis: {agent_summary.get("interaction_id", "")}
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from enum import Enum

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TradingStrategy:
    """거래 전략"""

    def __init__(self):
        self.signals = []
        self.positions = {{}}

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, any]:
        """시장 분석"""
        analysis = {{
            "trend": self._analyze_trend(df),
            "momentum": self._analyze_momentum(df),
            "volatility": self._calculate_volatility(df)
        }}
        return analysis

    def generate_signals(self, df: pd.DataFrame) -> List[Dict[str, any]]:
        """매매 신호 생성"""
        signals = []

        # 기본 신호 생성 로직
        sma_short = df['Close'].rolling(10).mean()
        sma_long = df['Close'].rolling(30).mean()

        for i in range(len(df)):
            if i < 30:  # 충분한 데이터가 없으면 스킵
                continue

            signal = SignalType.HOLD

            if sma_short.iloc[i] > sma_long.iloc[i] and sma_short.iloc[i-1] <= sma_long.iloc[i-1]:
                signal = SignalType.BUY
            elif sma_short.iloc[i] < sma_long.iloc[i] and sma_short.iloc[i-1] >= sma_long.iloc[i-1]:
                signal = SignalType.SELL

            if signal != SignalType.HOLD:
                signals.append({{
                    "timestamp": df.index[i],
                    "signal": signal.value,
                    "price": df['Close'].iloc[i],
                    "confidence": 0.7  # 기본 신뢰도
                }})

        return signals

    def _analyze_trend(self, df: pd.DataFrame) -> str:
        """트렌드 분석"""
        if len(df) < 20:
            return "insufficient_data"

        recent_prices = df['Close'].tail(20)
        if recent_prices.iloc[-1] > recent_prices.iloc[0]:
            return "uptrend"
        elif recent_prices.iloc[-1] < recent_prices.iloc[0]:
            return "downtrend"
        else:
            return "sideways"

    def _analyze_momentum(self, df: pd.DataFrame) -> float:
        """모멘텀 분석"""
        if len(df) < 10:
            return 0.0

        price_change = (df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]
        return price_change

    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """변동성 계산"""
        if len(df) < 20:
            return 0.0

        returns = df['Close'].pct_change().dropna()
        return returns.std() * np.sqrt(252)  # 연율화

# Agent Response Summary:
# {agent_summary.get("final_output", agent_summary.get("response", ""))[:500]}...
'''

            with open(strategy_file, 'w', encoding='utf-8') as f:
                f.write(strategy_content)

            files_created.append(str(strategy_file))

            self._log_session(f"Created strategy file: {strategy_file}", "INFO")

        except Exception as e:
            self._log_session(f"Failed to create strategy files: {e}", "ERROR")

        return files_created

    async def _create_service_files(self, agent_summary: Dict[str, Any]) -> List[str]:
        """서비스 에이전트 결과로 서비스 파일 생성"""
        files_created = []

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 백테스팅 서비스 생성
            service_file = self.project_dirs['service'] / f"backtest_service_{timestamp}.py"
            service_content = f'''#!/usr/bin/env python3
"""
Backtesting Service - Generated by Orchestrator
Generated: {datetime.now().isoformat()}
Based on agent analysis: {agent_summary.get("interaction_id", "")}
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime

class BacktestService:
    """백테스팅 서비스"""

    def __init__(self):
        self.initial_capital = 100000  # 초기 자본
        self.commission = 0.001  # 수수료 0.1%

    def run_backtest(self, df: pd.DataFrame, signals: List[Dict]) -> Dict[str, any]:
        """백테스팅 실행"""

        portfolio_value = self.initial_capital
        positions = 0
        cash = self.initial_capital
        trades = []

        for signal in signals:
            timestamp = signal['timestamp']
            price = signal['price']
            signal_type = signal['signal']

            if signal_type == 'BUY' and cash > price:
                # 매수
                shares = int(cash * 0.95 / price)  # 95% 자금 사용
                cost = shares * price * (1 + self.commission)

                if cost <= cash:
                    cash -= cost
                    positions += shares
                    trades.append({{
                        'timestamp': timestamp,
                        'type': 'BUY',
                        'shares': shares,
                        'price': price,
                        'cost': cost
                    }})

            elif signal_type == 'SELL' and positions > 0:
                # 매도
                revenue = positions * price * (1 - self.commission)
                cash += revenue
                trades.append({{
                    'timestamp': timestamp,
                    'type': 'SELL',
                    'shares': positions,
                    'price': price,
                    'revenue': revenue
                }})
                positions = 0

        # 최종 포트폴리오 가치 계산
        final_price = df['Close'].iloc[-1]
        final_value = cash + (positions * final_price)

        return {{
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': (final_value - self.initial_capital) / self.initial_capital,
            'total_trades': len(trades),
            'trades': trades
        }}

    def calculate_metrics(self, backtest_result: Dict) -> Dict[str, float]:
        """성과 지표 계산"""

        total_return = backtest_result['total_return']
        trades = backtest_result['trades']

        # 샤프 비율 계산 (간단화)
        if len(trades) > 0:
            returns = []
            for i in range(1, len(trades)):
                if trades[i]['type'] == 'SELL' and trades[i-1]['type'] == 'BUY':
                    trade_return = (trades[i]['revenue'] - trades[i-1]['cost']) / trades[i-1]['cost']
                    returns.append(trade_return)

            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0

        return {{
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': self._calculate_max_drawdown(trades),
            'win_rate': self._calculate_win_rate(trades)
        }}

    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """최대 손실폭 계산"""
        # 간단화된 구현
        return 0.0

    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """승률 계산"""
        # 간단화된 구현
        return 0.0

# Agent Response Summary:
# {agent_summary.get("final_output", agent_summary.get("response", ""))[:500]}...
'''

            with open(service_file, 'w', encoding='utf-8') as f:
                f.write(service_content)

            files_created.append(str(service_file))

            self._log_session(f"Created service file: {service_file}", "INFO")

        except Exception as e:
            self._log_session(f"Failed to create service files: {e}", "ERROR")

        return files_created

    async def _create_helper_files(self, agent_summary: Dict[str, Any]) -> List[str]:
        """헬퍼 에이전트 결과로 헬퍼 파일 생성"""
        files_created = []

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # API 헬퍼 파일 생성
            helper_file = self.project_dirs['helper'] / f"api_helper_{timestamp}.py"
            helper_content = f'''#!/usr/bin/env python3
"""
API Helper - Generated by Orchestrator
Generated: {datetime.now().isoformat()}
Based on agent analysis: {agent_summary.get("interaction_id", "")}
"""

import requests
import json
from typing import Dict, Any, Optional
import os

class APIHelper:
    """API 연동 헬퍼"""

    def __init__(self):
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, str]:
        """API 키 로드"""
        return {{
            'google': os.getenv('GOOGLE_API_KEY', ''),
            'anthropic': os.getenv('ANTHROPIC_API_KEY', ''),
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_KEY', '')
        }}

    def send_notification(self, message: str, channel: str = "default") -> bool:
        """알림 전송"""
        try:
            # 알림 전송 로직 구현
            print(f"[NOTIFICATION] {{channel}}: {{message}}")
            return True
        except Exception as e:
            print(f"Notification failed: {{e}}")
            return False

    def fetch_external_data(self, source: str, params: Dict[str, Any]) -> Optional[Dict]:
        """외부 데이터 가져오기"""
        try:
            # 외부 API 호출 로직 구현
            if source == "alpha_vantage":
                return self._fetch_alpha_vantage_data(params)
            else:
                print(f"Unknown data source: {{source}}")
                return None
        except Exception as e:
            print(f"External data fetch failed: {{e}}")
            return None

    def _fetch_alpha_vantage_data(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Alpha Vantage 데이터 가져오기"""
        # 실제 구현 필요
        return {{"status": "simulated", "data": []}}

# Agent Response Summary:
# {agent_summary.get("final_output", agent_summary.get("response", ""))[:500]}...
'''

            with open(helper_file, 'w', encoding='utf-8') as f:
                f.write(helper_content)

            files_created.append(str(helper_file))

            self._log_session(f"Created helper file: {helper_file}", "INFO")

        except Exception as e:
            self._log_session(f"Failed to create helper files: {e}", "ERROR")

        return files_created

    def _calculate_quality_metrics(self, workflow_result: Dict[str, Any]) -> Dict[str, float]:
        """품질 지표 계산"""

        quality_scores = []
        total_agents = len(workflow_result.get("agent_summaries", []))

        for agent_summary in workflow_result.get("agent_summaries", []):
            if agent_summary.get("quality_score"):
                quality_scores.append(agent_summary["quality_score"])

        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            min_quality = min(quality_scores)
            max_quality = max(quality_scores)
        else:
            avg_quality = min_quality = max_quality = 0.0

        return {
            "average_quality_score": avg_quality,
            "minimum_quality_score": min_quality,
            "maximum_quality_score": max_quality,
            "agents_reviewed": len(quality_scores),
            "total_agents": total_agents,
            "review_coverage": len(quality_scores) / total_agents if total_agents > 0 else 0.0
        }

    def _suggest_next_actions(self, workflow_result: Dict[str, Any]) -> List[str]:
        """다음 액션 제안"""

        suggestions = []

        # 품질 점수 기반 제안
        for agent_summary in workflow_result.get("agent_summaries", []):
            quality_score = agent_summary.get("quality_score", 0)
            agent_name = agent_summary.get("agent_name", "unknown")

            if quality_score < 6.0:
                suggestions.append(f"{agent_name} 결과 품질 개선 필요 (현재 점수: {quality_score}/10)")

            if agent_summary.get("has_corrections"):
                suggestions.append(f"{agent_name} 교정사항 적용 확인")

        # 프로젝트 연동 제안
        suggestions.extend([
            "생성된 파일들을 프로젝트에 통합",
            "백테스팅 실행하여 전략 검증",
            "실시간 데이터로 전략 테스트",
            "리스크 관리 파라미터 조정"
        ])

        return suggestions

    async def _save_workflow_result(self, result: Dict[str, Any]):
        """워크플로우 결과 저장"""

        # 결과 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.project_dirs['outputs'] / f"workflow_result_{timestamp}.json"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        self._log_session(f"Workflow result saved to: {result_file}", "INFO")

# 메인 실행 함수
async def main():
    """메인 실행 함수"""

    orchestrator = ProductionOrchestrator()

    # 테스트 실행
    test_request = "AAPL 주식에 대한 종합적인 기술적 분석을 수행하고, 단기 및 중기 매매 전략을 개발해주세요. 백테스팅도 포함해서 실행해주세요."

    print("="*80)
    print("PRODUCTION ORCHESTRATOR - TRADING WORKFLOW")
    print("="*80)

    result = await orchestrator.execute_trading_workflow(test_request, "comprehensive")

    print("\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)

    if 'error' not in result:
        print(f"Workflow ID: {result['workflow_id']}")
        print(f"Agents Executed: {len(result['agent_results'])}")
        print(f"Files Created: {sum(len(files) for files in result['project_integration'].values())}")
        print(f"Average Quality: {result['quality_metrics']['average_quality_score']:.1f}/10")
        print(f"Next Actions: {len(result['next_actions'])} items")
    else:
        print(f"Execution Failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())