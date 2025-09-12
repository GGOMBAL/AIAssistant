import requests
import json
from datetime import datetime

# Telegram Bot Configuration
BOT_TOKEN = '8181854217:AAGRS7WFHPt_ZgvVHdoLURmBxfy5N9WJyfI'
CHAT_ID = '6676456019'  # Replace with your actual chat ID (numeric ID or @channel_name)

# Try to import telegram library, but don't fail if it's not available
try:
    import telegram
    TELEGRAM_LIBRARY_AVAILABLE = True
except ImportError:
    TELEGRAM_LIBRARY_AVAILABLE = False
    print("Warning: python-telegram-bot library not available, using requests only")

def SendMessage(msg):
    """Send message to Telegram chat"""
    try:
        # Add timestamp to message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] {msg}"
        
        # Send message using requests (more reliable than telegram library)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': formatted_msg,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Telegram API request failed: {e}")
        if "Bad Request" in str(e):
            print("Note: Please update CHAT_ID in telegram_bot.py with a valid chat ID")
        return False
    except Exception as e:
        print(f"Telegram message send error: {e}")
        return False

def SendMessageWithRetry(msg, max_retries=3):
    """Send message with retry logic"""
    for attempt in range(max_retries):
        if SendMessage(msg):
            return True
        if attempt < max_retries - 1:
            import time
            time.sleep(2 ** attempt)  # Exponential backoff
    
    print(f"Failed to send Telegram message after {max_retries} attempts: {msg}")
    return False

def GetChatId():
    """Get available chat IDs from bot updates (for setup purposes)"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data['ok'] and data['result']:
            chat_ids = set()
            for update in data['result']:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    chat_name = update['message']['chat'].get('title', 'Private Chat')
                    chat_ids.add((chat_id, chat_name))
                    
            print("Available Chat IDs:")
            for chat_id, chat_name in chat_ids:
                print(f"  {chat_id} - {chat_name}")
        else:
            print("No recent messages found. Send a message to your bot first.")
            
    except Exception as e:
        print(f"Error getting chat IDs: {e}")

# Legacy compatibility - keep the bot object for any existing code if telegram library is available
if TELEGRAM_LIBRARY_AVAILABLE:
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
    except Exception as e:
        print(f"Warning: Could not initialize telegram bot: {e}")
        bot = None
else:
    bot = None
