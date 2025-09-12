"""
Telegram Messenger - Helper Agent Service
Handles Telegram bot notifications and commands
Based on reference code from refer/Helper/Messenger
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram Bot for notifications and commands"""
    
    def __init__(self, bot_token: str, default_chat_id: str = None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Try to import telegram library, but don't fail if it's not available
        try:
            import telegram
            self.telegram_library_available = True
        except ImportError:
            self.telegram_library_available = False
            logger.warning("python-telegram-bot library not available, using requests only")
    
    def send_message(self, message: str, chat_id: str = None, parse_mode: str = 'HTML', 
                    add_timestamp: bool = True) -> bool:
        """Send message to Telegram chat - based on reference SendMessage"""
        try:
            target_chat_id = chat_id or self.default_chat_id
            
            if not target_chat_id:
                logger.error("No chat ID provided")
                return False
            
            # Add timestamp to message if requested
            if add_timestamp:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                formatted_msg = f"[{timestamp}] {message}"
            else:
                formatted_msg = message
            
            # Send message using requests (more reliable than telegram library)
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': target_chat_id,
                'text': formatted_msg,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram message sent successfully to {target_chat_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram API request failed: {e}")
            if "Bad Request" in str(e):
                logger.error("Note: Please update chat_id with a valid chat ID")
            return False
        except Exception as e:
            logger.error(f"Telegram message send error: {e}")
            return False
    
    def send_message_with_retry(self, message: str, chat_id: str = None, max_retries: int = 3, 
                               retry_delay: int = 2) -> bool:
        """Send message with retry logic - based on reference SendMessageWithRetry"""
        for attempt in range(max_retries):
            if self.send_message(message, chat_id):
                return True
            
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                logger.warning(f"Telegram send attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
        
        logger.error(f"Failed to send Telegram message after {max_retries} attempts")
        return False
    
    def send_photo(self, photo_path: str, caption: str = None, chat_id: str = None) -> bool:
        """Send photo to Telegram chat"""
        try:
            target_chat_id = chat_id or self.default_chat_id
            
            if not target_chat_id:
                logger.error("No chat ID provided")
                return False
            
            url = f"{self.base_url}/sendPhoto"
            
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': target_chat_id,
                    'caption': caption or ""
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
            
            logger.info(f"Photo sent successfully to {target_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            return False
    
    def send_document(self, document_path: str, caption: str = None, chat_id: str = None) -> bool:
        """Send document to Telegram chat"""
        try:
            target_chat_id = chat_id or self.default_chat_id
            
            if not target_chat_id:
                logger.error("No chat ID provided")
                return False
            
            url = f"{self.base_url}/sendDocument"
            
            with open(document_path, 'rb') as document:
                files = {'document': document}
                data = {
                    'chat_id': target_chat_id,
                    'caption': caption or ""
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
            
            logger.info(f"Document sent successfully to {target_chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending document: {e}")
            return False
    
    def get_updates(self, offset: int = None, limit: int = 100, timeout: int = 0) -> List[Dict[str, Any]]:
        """Get updates from Telegram bot API"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                'limit': limit,
                'timeout': timeout
            }
            
            if offset is not None:
                params['offset'] = offset
            
            response = requests.get(url, params=params, timeout=timeout + 10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('result', [])
            
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    def get_chat_info(self, chat_id: str = None) -> Dict[str, Any]:
        """Get information about a chat"""
        try:
            target_chat_id = chat_id or self.default_chat_id
            
            if not target_chat_id:
                return {}
            
            url = f"{self.base_url}/getChat"
            params = {'chat_id': target_chat_id}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('result', {})
            
        except Exception as e:
            logger.error(f"Error getting chat info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test bot connection and authentication"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"Bot connection test successful: {bot_info.get('username', 'Unknown')}")
                return True
            else:
                logger.error("Bot connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Bot connection test error: {e}")
            return False

class TelegramNotificationService:
    """High-level Telegram notification service"""
    
    def __init__(self, bot_token: str, chat_ids: List[str] = None):
        self.bot = TelegramBot(bot_token)
        self.chat_ids = chat_ids or []
        self.message_templates = {}
        self._setup_default_templates()
    
    def _setup_default_templates(self):
        """Setup default message templates"""
        self.message_templates = {
            'trading_signal': "🔔 <b>Trading Signal</b>\n📈 Symbol: {symbol}\n🎯 Action: {action}\n💰 Price: {price}\n📊 Strategy: {strategy}",
            'order_executed': "✅ <b>Order Executed</b>\n📈 {symbol}: {side} {quantity} @ {price}\n💰 Total: {total_amount}",
            'market_alert': "⚠️ <b>Market Alert</b>\n📊 {message}",
            'system_error': "❌ <b>System Error</b>\n🔧 {error_message}\n⏰ Time: {timestamp}",
            'daily_summary': "📊 <b>Daily Summary</b>\n💰 P&L: {pnl}\n📈 Trades: {trade_count}\n🎯 Win Rate: {win_rate}%",
            'balance_update': "💰 <b>Balance Update</b>\n💵 Cash: {cash}\n📈 Stocks: {stocks}\n💯 Total: {total}",
            'market_open': "🔔 <b>Market Status</b>\n📈 Market is now OPEN\n⏰ {timestamp}",
            'market_close': "🔔 <b>Market Status</b>\n📉 Market is now CLOSED\n⏰ {timestamp}"
        }
    
    def add_chat_id(self, chat_id: str):
        """Add a chat ID to the notification list"""
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)
    
    def remove_chat_id(self, chat_id: str):
        """Remove a chat ID from the notification list"""
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
    
    def set_template(self, template_name: str, template: str):
        """Set a custom message template"""
        self.message_templates[template_name] = template
    
    def send_notification(self, template_name: str, data: Dict[str, Any], 
                         chat_ids: List[str] = None) -> bool:
        """Send notification using template"""
        try:
            if template_name not in self.message_templates:
                logger.error(f"Template {template_name} not found")
                return False
            
            template = self.message_templates[template_name]
            message = template.format(**data)
            
            target_chat_ids = chat_ids or self.chat_ids
            
            if not target_chat_ids:
                logger.error("No chat IDs configured")
                return False
            
            success = True
            for chat_id in target_chat_ids:
                if not self.bot.send_message_with_retry(message, chat_id):
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def send_trading_signal(self, symbol: str, action: str, price: float, 
                           strategy: str = "Unknown") -> bool:
        """Send trading signal notification"""
        data = {
            'symbol': symbol,
            'action': action.upper(),
            'price': price,
            'strategy': strategy
        }
        return self.send_notification('trading_signal', data)
    
    def send_order_executed(self, symbol: str, side: str, quantity: int, 
                           price: float) -> bool:
        """Send order execution notification"""
        data = {
            'symbol': symbol,
            'side': side.upper(),
            'quantity': quantity,
            'price': price,
            'total_amount': quantity * price
        }
        return self.send_notification('order_executed', data)
    
    def send_market_alert(self, message: str) -> bool:
        """Send market alert notification"""
        data = {'message': message}
        return self.send_notification('market_alert', data)
    
    def send_system_error(self, error_message: str) -> bool:
        """Send system error notification"""
        data = {
            'error_message': error_message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return self.send_notification('system_error', data)
    
    def send_daily_summary(self, pnl: float, trade_count: int, win_rate: float) -> bool:
        """Send daily trading summary"""
        data = {
            'pnl': f"{pnl:,.2f}",
            'trade_count': trade_count,
            'win_rate': f"{win_rate:.1f}"
        }
        return self.send_notification('daily_summary', data)
    
    def send_balance_update(self, cash: float, stocks: float, total: float) -> bool:
        """Send balance update notification"""
        data = {
            'cash': f"{cash:,.0f}",
            'stocks': f"{stocks:,.0f}",
            'total': f"{total:,.0f}"
        }
        return self.send_notification('balance_update', data)
    
    def send_market_status(self, is_open: bool) -> bool:
        """Send market status notification"""
        template_name = 'market_open' if is_open else 'market_close'
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return self.send_notification(template_name, data)
    
    def test_notifications(self) -> bool:
        """Test notification system"""
        test_message = "🤖 Telegram notification system test - All systems operational!"
        
        success = True
        for chat_id in self.chat_ids:
            if not self.bot.send_message(test_message, chat_id):
                success = False
        
        return success

class TelegramCommandHandler:
    """Handle incoming Telegram commands"""
    
    def __init__(self, bot: TelegramBot):
        self.bot = bot
        self.commands = {}
        self.last_update_id = 0
        self._setup_default_commands()
    
    def _setup_default_commands(self):
        """Setup default commands"""
        self.commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/status': self._handle_status,
            '/balance': self._handle_balance,
            '/positions': self._handle_positions,
        }
    
    def add_command(self, command: str, handler):
        """Add a custom command handler"""
        self.commands[command] = handler
    
    def _handle_start(self, message: Dict[str, Any]) -> str:
        """Handle /start command"""
        return "🤖 Welcome to AI Trading Assistant!\nUse /help to see available commands."
    
    def _handle_help(self, message: Dict[str, Any]) -> str:
        """Handle /help command"""
        help_text = "📋 <b>Available Commands:</b>\n\n"
        for command in self.commands.keys():
            help_text += f"{command}\n"
        return help_text
    
    def _handle_status(self, message: Dict[str, Any]) -> str:
        """Handle /status command"""
        return "✅ AI Trading Assistant is running normally.\n📊 All systems operational."
    
    def _handle_balance(self, message: Dict[str, Any]) -> str:
        """Handle /balance command"""
        # This would integrate with the broker API to get real balance
        return "💰 Balance information would be displayed here.\n(Integration with broker API required)"
    
    def _handle_positions(self, message: Dict[str, Any]) -> str:
        """Handle /positions command"""
        # This would integrate with the broker API to get positions
        return "📊 Position information would be displayed here.\n(Integration with broker API required)"
    
    def process_updates(self, handle_commands: bool = True) -> List[Dict[str, Any]]:
        """Process incoming updates and handle commands"""
        try:
            updates = self.bot.get_updates(offset=self.last_update_id + 1)
            
            processed_updates = []
            
            for update in updates:
                self.last_update_id = update.get('update_id', self.last_update_id)
                
                if 'message' in update and handle_commands:
                    message = update['message']
                    text = message.get('text', '')
                    
                    if text.startswith('/'):
                        command = text.split()[0]
                        if command in self.commands:
                            try:
                                response = self.commands[command](message)
                                chat_id = message['chat']['id']
                                self.bot.send_message(response, str(chat_id))
                            except Exception as e:
                                logger.error(f"Error handling command {command}: {e}")
                
                processed_updates.append(update)
            
            return processed_updates
            
        except Exception as e:
            logger.error(f"Error processing updates: {e}")
            return []