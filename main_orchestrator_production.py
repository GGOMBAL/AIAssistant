#!/usr/bin/env python3
"""
Production Main Orchestrator - Entry Point
AI Assistant Multi-Agent Trading System
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "project"))

from production_orchestrator import ProductionOrchestrator
from gemini_client import GeminiClient

class MainOrchestratorProduction:
    """메인 오케스트레이터 - 프로덕션 환경"""

    def __init__(self):
        self.orchestrator = ProductionOrchestrator()
        self.gemini_client = GeminiClient()
        self.project_root = project_root

    def run_analysis(self, user_request: str) -> dict:
        """
        사용자 요청을 받아 전체 분석 실행
        """
        print(f"[INFO] Starting analysis for: {user_request}")

        try:
            # 오케스트레이터 실행 (비동기 함수를 동기적으로 실행)
            import asyncio
            result = asyncio.run(self.orchestrator.execute_trading_workflow(user_request))

            print(f"[SUCCESS] Analysis completed successfully")
            print(f"[INFO] Generated files: {result.get('project_integration', {}).get('strategies_created', [])}")
            print(f"[INFO] Services created: {result.get('project_integration', {}).get('services_configured', [])}")

            return result

        except Exception as e:
            print(f"[ERROR] Analysis failed: {str(e)}")
            return {"error": str(e), "status": "failed"}

    def list_generated_files(self) -> dict:
        """생성된 파일 목록 반환"""
        strategy_dir = self.project_root / "Project" / "strategy"
        service_dir = self.project_root / "Project" / "service"

        files = {
            "strategies": [],
            "services": [],
            "interactions": []
        }

        if strategy_dir.exists():
            files["strategies"] = [f.name for f in strategy_dir.glob("*.py")]

        if service_dir.exists():
            files["services"] = [f.name for f in service_dir.glob("*.py")]

        interactions_dir = self.project_root / "storage" / "agent_interactions"
        if interactions_dir.exists():
            files["interactions"] = [f.name for f in interactions_dir.glob("*.json")]

        return files

    def get_workflow_results(self) -> list:
        """워크플로우 결과 목록 반환"""
        results_dir = self.project_root / "outputs" / "agent_results"
        results = []

        if results_dir.exists():
            for result_file in results_dir.glob("workflow_result_*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        results.append({
                            "file": result_file.name,
                            "workflow_id": result_data.get("workflow_id"),
                            "timestamp": result_data.get("execution_timestamp"),
                            "user_request": result_data.get("user_request"),
                            "status": "completed"
                        })
                except Exception as e:
                    print(f"[WARNING] Could not read result file {result_file}: {e}")

        return results

def main():
    """메인 실행 함수"""
    print("=== AI Assistant Multi-Agent Trading System ===")
    print("Production Orchestrator v1.0")
    print()

    orchestrator = MainOrchestratorProduction()

    while True:
        print("\n[OPTIONS]")
        print("1. Run new analysis")
        print("2. List generated files")
        print("3. Show workflow results")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            user_request = input("\nEnter your request: ").strip()
            if user_request:
                result = orchestrator.run_analysis(user_request)
                print(f"\nResult summary:")
                print(f"- Workflow ID: {result.get('workflow_id', 'N/A')}")
                print(f"- Quality Score: {result.get('quality_metrics', {}).get('average_quality_score', 'N/A')}")
                print(f"- Files Generated: {len(result.get('project_integration', {}).get('strategies_created', []) + result.get('project_integration', {}).get('services_configured', []))}")

        elif choice == "2":
            files = orchestrator.list_generated_files()
            print(f"\n[GENERATED FILES]")
            print(f"Strategies: {len(files['strategies'])} files")
            for f in files['strategies']:
                print(f"  - {f}")
            print(f"Services: {len(files['services'])} files")
            for f in files['services']:
                print(f"  - {f}")
            print(f"Interactions: {len(files['interactions'])} files")

        elif choice == "3":
            results = orchestrator.get_workflow_results()
            print(f"\n[WORKFLOW RESULTS] ({len(results)} total)")
            for result in results[-5:]:  # Show last 5 results
                print(f"- {result['timestamp']}: {result['user_request'][:50]}...")
                print(f"  File: {result['file']}")
                print(f"  ID: {result['workflow_id']}")

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()