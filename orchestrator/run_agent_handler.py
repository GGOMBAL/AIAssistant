"""
RUN AGENT Handler
RUN AGENT의 백테스트 실행을 위한 전용 핸들러

Purpose:
- RUN AGENT를 통한 백테스트 실행 처리
- 에러 발생 시 자동 재시도 및 프롬프트 개선
- 파라미터 검증 및 보완

Created: 2025-10-14
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class RunAgentHandler:
    """
    RUN AGENT 전용 핸들러

    백테스트 실행 요청을 처리하고,
    실패 시 자동으로 프롬프트를 개선하여 재시도합니다.
    """

    def __init__(self, run_agent=None):
        """
        Initialize RunAgentHandler

        Args:
            run_agent: RUN AGENT 인스턴스
        """
        self.run_agent = run_agent
        self.execution_history = []

    async def execute_backtest_with_feedback(
        self,
        user_request: str,
        analysis: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        백테스트 실행 (자동 재시도 포함)

        Args:
            user_request: 사용자 요청
            analysis: 요청 분석 결과
            max_retries: 최대 재시도 횟수

        Returns:
            실행 결과
        """
        # 백테스트 파일 경로 찾기
        backtest_files = self._find_backtest_files()

        if not backtest_files:
            logger.error("[RUN AGENT] 백테스트 파일을 찾을 수 없습니다")
            return {
                "status": "error",
                "error": "No backtest file found",
                "suggestions": [
                    "Create run_backtest.py",
                    "Create run_backtest_auto.py",
                    "Check Test folder for backtest scripts"
                ]
            }

        # 파라미터 추출
        parameters = self._extract_backtest_parameters(user_request, analysis)

        # 재시도 루프
        for attempt in range(max_retries):
            logger.info(f"[RUN AGENT] 백테스트 실행 시도 {attempt + 1}/{max_retries}")

            # 백테스트 파일 선택
            file_path = backtest_files[0] if attempt == 0 else self._select_alternative_file(backtest_files, attempt)

            # 실행
            result = await self._execute_backtest_file(file_path, parameters)

            # 성공 시 반환
            if result.get("status") == "success":
                logger.info(f"[RUN AGENT] 백테스트 실행 성공 (시도 {attempt + 1})")
                return result

            # 실패 시 파라미터 개선
            if attempt < max_retries - 1:
                logger.warning(f"[RUN AGENT] 실행 실패, 파라미터 개선 중...")
                parameters = self._improve_parameters(parameters, result)
                await asyncio.sleep(1)  # 잠시 대기

        # 모든 시도 실패
        logger.error(f"[RUN AGENT] 백테스트 실행 실패 (모든 시도 소진)")
        return {
            "status": "error",
            "error": "Failed after all retries",
            "attempts": max_retries,
            "last_error": result.get("error", "Unknown error")
        }

    def _find_backtest_files(self) -> List[Path]:
        """
        백테스트 실행 가능한 파일 찾기

        Returns:
            백테스트 파일 경로 리스트
        """
        possible_files = [
            "Test/Demo/demo_backtest.py",  # 우선 순위 1
            "Test/test_backtest.py",
            "Test/run_backtest.py",
            "Test/run_backtest_auto.py",
            "run_backtest.py",
            "run_backtest_auto.py"
        ]

        found_files = []
        for file_path in possible_files:
            path = Path(file_path)
            if path.exists():
                found_files.append(path)
                logger.info(f"[RUN AGENT] 백테스트 파일 발견: {path}")

        return found_files

    def _extract_backtest_parameters(
        self,
        user_request: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        사용자 요청에서 백테스트 파라미터 추출

        Args:
            user_request: 사용자 요청
            analysis: 요청 분석 결과

        Returns:
            백테스트 파라미터
        """
        params = analysis.get("parameters", {})

        # 날짜 추출
        import re
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, user_request)

        if len(dates) >= 2:
            params["start_date"] = dates[0]
            params["end_date"] = dates[1]
        elif len(dates) == 1:
            params["end_date"] = dates[0]
            # 시작일 추정 (3개월 전)
            from datetime import datetime, timedelta
            end = datetime.strptime(dates[0], "%Y-%m-%d")
            start = end - timedelta(days=90)
            params["start_date"] = start.strftime("%Y-%m-%d")
        else:
            # 기본값 설정 (최근 6개월)
            from datetime import datetime, timedelta
            end = datetime.now()
            start = end - timedelta(days=180)
            params["start_date"] = start.strftime("%Y-%m-%d")
            params["end_date"] = end.strftime("%Y-%m-%d")

        # 종목 추출
        if "nasdaq" in user_request.lower():
            params["market"] = "NASDAQ"
        elif "nyse" in user_request.lower():
            params["market"] = "NYSE"
        else:
            params["market"] = "ALL"

        # 심볼 추출
        symbol_pattern = r'\b[A-Z]{2,5}\b'
        symbols = re.findall(symbol_pattern, user_request)
        if symbols:
            params["symbols"] = symbols

        logger.info(f"[RUN AGENT] 추출된 파라미터: {params}")
        return params

    async def _execute_backtest_file(
        self,
        file_path: Path,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        백테스트 파일 실행

        Args:
            file_path: 실행할 파일 경로
            parameters: 백테스트 파라미터

        Returns:
            실행 결과
        """
        if not self.run_agent:
            logger.error("[RUN AGENT] RunAgent 인스턴스가 없습니다")
            return {
                "status": "error",
                "error": "RunAgent not initialized"
            }

        # 인자 구성
        args = []
        if "start_date" in parameters:
            args.extend(["--start-date", parameters["start_date"]])
        if "end_date" in parameters:
            args.extend(["--end-date", parameters["end_date"]])
        if "symbols" in parameters:
            args.extend(["--symbols", ",".join(parameters["symbols"])])
        elif "market" in parameters:
            args.extend(["--market", parameters["market"]])

        logger.info(f"[RUN AGENT] 실행: {file_path} {' '.join(args)}")

        try:
            # RUN AGENT의 execute_python_file 호출
            result = await self.run_agent.execute_python_file(
                file_path=str(file_path),
                args=args,
                timeout=600  # 10분 타임아웃
            )

            # 실행 히스토리 저장
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": str(file_path),
                "parameters": parameters,
                "result": result
            })

            # 결과 분석 및 포맷팅
            if result.get("status") == "success":
                # stdout에서 백테스트 결과 추출
                summary = self._extract_backtest_summary(result.get("stdout", ""))

                return {
                    "status": "success",
                    "file_path": str(file_path),
                    "duration": result.get("duration", 0),
                    "summary": summary,
                    "raw_output": result.get("stdout", "")
                }
            else:
                return {
                    "status": "error",
                    "file_path": str(file_path),
                    "error": result.get("stderr", result.get("error", "Unknown error")),
                    "return_code": result.get("return_code", -1)
                }

        except Exception as e:
            logger.error(f"[RUN AGENT] 실행 중 예외: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _select_alternative_file(
        self,
        backtest_files: List[Path],
        attempt: int
    ) -> Path:
        """
        재시도 시 대체 백테스트 파일 선택

        Args:
            backtest_files: 사용 가능한 파일 리스트
            attempt: 시도 횟수

        Returns:
            선택된 파일 경로
        """
        # 순환 선택
        index = attempt % len(backtest_files)
        return backtest_files[index]

    def _improve_parameters(
        self,
        parameters: Dict[str, Any],
        previous_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        실패한 실행을 바탕으로 파라미터 개선

        Args:
            parameters: 현재 파라미터
            previous_result: 이전 실행 결과

        Returns:
            개선된 파라미터
        """
        error_msg = previous_result.get("error", "").lower()

        # 에러 메시지 분석하여 파라미터 조정
        if "no data" in error_msg or "empty" in error_msg:
            # 날짜 범위 확장
            from datetime import datetime, timedelta
            if "start_date" in parameters:
                start = datetime.strptime(parameters["start_date"], "%Y-%m-%d")
                start = start - timedelta(days=30)
                parameters["start_date"] = start.strftime("%Y-%m-%d")
                logger.info(f"[RUN AGENT] 날짜 범위 확장: {parameters['start_date']}")

        elif "symbol" in error_msg or "ticker" in error_msg:
            # 기본 심볼 추가
            if "symbols" not in parameters:
                parameters["symbols"] = ["AAPL", "MSFT", "GOOGL"]
                logger.info(f"[RUN AGENT] 기본 심볼 추가: {parameters['symbols']}")

        elif "timeout" in error_msg:
            # 심볼 수 줄이기
            if "symbols" in parameters and len(parameters["symbols"]) > 3:
                parameters["symbols"] = parameters["symbols"][:3]
                logger.info(f"[RUN AGENT] 심볼 수 축소: {parameters['symbols']}")

        return parameters

    def _extract_backtest_summary(self, stdout: str) -> str:
        """
        stdout에서 백테스트 요약 추출

        Args:
            stdout: 표준 출력

        Returns:
            요약 문자열
        """
        lines = stdout.split('\n')
        summary_lines = []

        # 주요 지표 찾기
        keywords = [
            "total return", "sharpe", "drawdown", "win rate",
            "수익률", "샤프", "낙폭", "승률",
            "trades", "거래", "profit", "loss"
        ]

        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                summary_lines.append(line.strip())

        if summary_lines:
            return "\n".join(summary_lines[-10:])  # 마지막 10줄
        else:
            # 전체 출력의 마지막 부분 반환
            return "\n".join(lines[-20:]) if lines else "No output"

    def get_execution_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        실행 히스토리 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            실행 히스토리
        """
        return self.execution_history[-limit:]