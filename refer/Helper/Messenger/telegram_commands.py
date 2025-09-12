# -*- coding: utf-8 -*-
import re
import logging
import warnings
from typing import List, Optional
from datetime import datetime
from Helper.BuyCandidateManager import BuyCandidateManager
import Helper.Messenger.telegram_bot as telegram_bot

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", message="The `hash` argument is deprecated", category=DeprecationWarning)

class TelegramCommandHandler:
    """텔레그램 명령어 처리 클래스"""
    
    def __init__(self):
        self.buy_candidate_manager = BuyCandidateManager()
        self.commands = {
            '/exclude': self.handle_exclude_command,
            '/include': self.handle_include_command,
            '/list_excluded': self.handle_list_excluded_command,
            '/clear_excluded': self.handle_clear_excluded_command,
            '/candidates': self.handle_candidates_command,
            '/help': self.handle_help_command
        }
    
    def parse_message(self, message: str) -> Optional[dict]:
        """
        텔레그램 메시지를 파싱하여 명령어와 인수 추출
        
        Args:
            message: 텔레그램 메시지 텍스트
            
        Returns:
            dict: 파싱된 명령어 정보 또는 None
        """
        message = message.strip()
        
        # 명령어 패턴 매칭
        if not message.startswith('/'):
            return None
        
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return {
            'command': command,
            'args': args,
            'full_message': message
        }
    
    def handle_command(self, message: str) -> str:
        """
        텔레그램 명령어 처리
        
        Args:
            message: 텔레그램 메시지
            
        Returns:
            str: 응답 메시지
        """
        try:
            parsed = self.parse_message(message)
            if not parsed:
                return "[ERROR] Invalid command format. Use /help for available commands."
            
            command = parsed['command']
            if command in self.commands:
                return self.commands[command](parsed['args'])
            else:
                return f"[ERROR] Unknown command: {command}. Use /help for available commands."
                
        except Exception as e:
            logging.error(f"Error handling Telegram command: {e}")
            return f"[ERROR] Error processing command: {str(e)}"
    
    def handle_exclude_command(self, args: List[str]) -> str:
        """
        특정 티커를 제외 리스트에 추가
        Usage: /exclude AAPL TSLA MSFT
        """
        if not args:
            return "[ERROR] Usage: /exclude <TICKER1> [TICKER2] [TICKER3] ..."
        
        success_tickers = []
        failed_tickers = []
        
        for ticker in args:
            ticker = ticker.upper().strip()
            if self._validate_ticker(ticker):
                if self.buy_candidate_manager.add_excluded_ticker(ticker):
                    success_tickers.append(ticker)
                else:
                    failed_tickers.append(ticker)
            else:
                failed_tickers.append(f"{ticker} (invalid format)")
        
        response_parts = []
        if success_tickers:
            response_parts.append(f"[OK] Excluded tickers: {', '.join(success_tickers)}")
        if failed_tickers:
            response_parts.append(f"[ERROR] Failed to exclude: {', '.join(failed_tickers)}")
        
        return "\n".join(response_parts)
    
    def handle_include_command(self, args: List[str]) -> str:
        """
        특정 티커를 제외 리스트에서 제거
        Usage: /include AAPL TSLA
        """
        if not args:
            return "[ERROR] Usage: /include <TICKER1> [TICKER2] [TICKER3] ..."
        
        success_tickers = []
        failed_tickers = []
        
        for ticker in args:
            ticker = ticker.upper().strip()
            if self._validate_ticker(ticker):
                if self.buy_candidate_manager.remove_excluded_ticker(ticker):
                    success_tickers.append(ticker)
                else:
                    failed_tickers.append(ticker)
            else:
                failed_tickers.append(f"{ticker} (invalid format)")
        
        response_parts = []
        if success_tickers:
            response_parts.append(f"[OK] Included tickers (removed from exclusion): {', '.join(success_tickers)}")
        if failed_tickers:
            response_parts.append(f"[ERROR] Failed to include: {', '.join(failed_tickers)}")
        
        return "\n".join(response_parts)
    
    def handle_list_excluded_command(self, args: List[str]) -> str:
        """
        현재 제외된 티커 목록 조회
        Usage: /list_excluded
        """
        excluded_tickers = self.buy_candidate_manager.load_excluded_tickers()
        
        if not excluded_tickers:
            return "[OK] No tickers are currently excluded."
        
        return f"🚫 Excluded tickers ({len(excluded_tickers)}):\n{', '.join(excluded_tickers)}"
    
    def handle_clear_excluded_command(self, args: List[str]) -> str:
        """
        모든 제외 티커 목록 초기화
        Usage: /clear_excluded
        """
        if self.buy_candidate_manager.clear_excluded_tickers():
            return "[OK] All excluded tickers cleared."
        else:
            return "[ERROR] Failed to clear excluded tickers."
    
    def handle_candidates_command(self, args: List[str]) -> str:
        """
        특정 날짜의 매수 후보 종목 조회 (여러 메시지로 분할 전송)
        Usage: /candidates [YYYY_MM_DD]
        """
        if args:
            date_str = args[0]
            if not self._validate_date_format(date_str):
                return "[ERROR] Invalid date format. Use YYYY_MM_DD (e.g., 2025_01_31)"
        else:
            # 오늘 날짜 사용
            date_str = datetime.now().strftime("%Y_%m_%d")
        
        summary_messages = self.buy_candidate_manager.get_candidate_summary(date_str)
        if summary_messages:
            # 첫 번째 메시지만 반환하고, 나머지는 별도로 전송
            import Helper.Messenger.telegram_bot as telegram_bot
            import time
            
            if len(summary_messages) > 1:
                # 첫 번째 메시지 이후의 메시지들을 순차적으로 전송
                for message in summary_messages[1:]:
                    time.sleep(1)  # Rate limit 방지
                    telegram_bot.SendMessageWithRetry(message)
            
            return summary_messages[0]  # 첫 번째 메시지 반환
        else:
            return f"[ERROR] No buy candidates found for {date_str}"
    
    def handle_help_command(self, args: List[str]) -> str:
        """
        도움말 메시지
        Usage: /help
        """
        help_text = """
🤖 **US Trading System Bot Commands:**

**Ticker Exclusion:**
• `/exclude <TICKER1> [TICKER2] ...` - Exclude tickers from trading
• `/include <TICKER1> [TICKER2] ...` - Remove tickers from exclusion list
• `/list_excluded` - Show currently excluded tickers
• `/clear_excluded` - Clear all excluded tickers

**Buy Candidates:**
• `/candidates [YYYY_MM_DD]` - Show buy candidates for date (default: today)

**General:**
• `/help` - Show this help message

**Examples:**
• `/exclude AAPL TSLA` - Exclude Apple and Tesla
• `/include MSFT` - Allow Microsoft trading again
• `/candidates 2025_01_31` - Show candidates for Jan 31, 2025
        """
        return help_text.strip()
    
    def _validate_ticker(self, ticker: str) -> bool:
        """
        티커 형식 검증
        
        Args:
            ticker: 티커 심볼
            
        Returns:
            bool: 유효한 티커 형식인지 여부
        """
        # 기본적인 티커 형식 검증 (1-5자 영문 대문자)
        pattern = r'^[A-Z]{1,5}$'
        return bool(re.match(pattern, ticker))
    
    def _validate_date_format(self, date_str: str) -> bool:
        """
        날짜 형식 검증 (YYYY_MM_DD)
        
        Args:
            date_str: 날짜 문자열
            
        Returns:
            bool: 유효한 날짜 형식인지 여부
        """
        try:
            datetime.strptime(date_str, "%Y_%m_%d")
            return True
        except ValueError:
            return False

def process_telegram_command(message: str) -> str:
    """
    텔레그램 명령어 처리 함수 (모듈 레벨)
    
    Args:
        message: 텔레그램 메시지
        
    Returns:
        str: 응답 메시지
    """
    handler = TelegramCommandHandler()
    response = handler.handle_command(message)
    
    # 응답 메시지를 텔레그램으로 전송
    try:
        telegram_bot.SendMessageWithRetry(response)
        logging.info(f"Telegram command processed: {message[:50]}...")
    except Exception as e:
        logging.error(f"Failed to send Telegram response: {e}")
        
    return response

if __name__ == "__main__":
    # 테스트를 위한 예제 실행
    handler = TelegramCommandHandler()
    
    test_commands = [
        "/help",
        "/exclude AAPL TSLA",
        "/list_excluded",
        "/candidates",
        "/include AAPL",
        "/clear_excluded"
    ]
    
    for cmd in test_commands:
        print(f"\n>>> {cmd}")
        response = handler.handle_command(cmd)
        print(response)