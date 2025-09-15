from Helper.KIS.KIS_Make_Token import GetToken 
from DataBase.MakMongoDB_US import ColMongoUsDB 
import Helper.KIS.KIS_API_Helper_US as KisUS
from datetime import datetime
from multiprocessing import Process
# Line notify removed - import kept for compatibility
import Helper.Messenger.line_alert as line_alert
import Helper.KIS.KIS_Common as Common 
import pprint
import pytz
import json
from Path import MainPath
import os
import yaml
import multiprocessing
import time
import signal
import sys
import traceback
from functools import wraps

# Progress state file path
PROGRESS_FILE = MainPath + '/json/us_progress_state.json'
RETRY_MAX = 3
TIMEOUT_SECONDS = 300  # 5 minute timeout

def save_progress(step, market='', operation=''):
    """Save progress state"""
    progress_data = {
        'timestamp': datetime.now().isoformat(),
        'step': step,
        'market': market,
        'operation': operation,
        'completed': False
    }
    
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress_data, f, indent=2)
    except Exception as e:
        pass  # Silent failure

def load_progress():
    """Load progress state"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        pass  # Silent failure
    return None

def clear_progress():
    """Clear progress state"""
    try:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
    except Exception as e:
        pass  # Silent failure

def timeout_handler(signum, frame):
    """Timeout handler"""
    raise TimeoutError("API call timeout")

def retry_with_timeout(max_retries=RETRY_MAX, timeout=TIMEOUT_SECONDS):
    """Retry and timeout decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    # Timeout setting (use alternative method since signal.alarm not supported on Windows)
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    pass  # Silent retry
                    
                    # Logging
                    import logging
                    # Suppress detailed error logs for cleaner output
                    
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30  # 30s, 60s, 90s wait
                        pass  # Silent wait
                        time.sleep(wait_time)
                    else:
                        # Send alert on final failure
                        try:
                            error_msg = f"US data collection final failure\nFunction: {func.__name__}\nError: {str(e)}"
                            # Line notify removed
                            # line_alert.SendMessage(error_msg)
                        except:
                            pass
                        raise e
            return None
        return wrapper
    return decorator

def safe_db_operation(operation_name, db_func, market='', step=''):
    """Safe DB operation execution"""
    save_progress(step, market, operation_name)
    
    @retry_with_timeout()
    def execute_operation():
        pass  # Silent operation start
        result = db_func()
        pass  # Silent operation completion
        return result
    
    try:
        return execute_operation()
    except Exception as e:
        error_msg = f"[{market}] {operation_name} final failure: {str(e)}"
        print(error_msg)
        raise e

def should_skip_step(current_step, saved_progress):
    """Determine whether to skip step based on saved progress state"""
    if not saved_progress:
        return False
    
    # Check if same date
    saved_date = datetime.fromisoformat(saved_progress['timestamp']).date()
    current_date = datetime.now().date()
    
    if saved_date != current_date:
        return False
    
    # Skip if current step is before saved step
    step_order = {
        'token': 1,
        'weekend_nas_w': 2,
        'weekend_nys_w': 3,
        'weekend_nas_f': 4,
        'weekend_nys_f': 5,
        'weekday_nys_d': 6,
        'weekday_nys_ad': 7,
        'weekday_nys_rs': 8,
        'weekday_nas_d': 9,
        'weekday_nas_ad': 10,
        'weekday_nas_rs': 11,
        'weekend_nas_e': 12,
        'weekend_nas_m': 13,
        'weekend_nys_e': 14,
        'weekend_nys_m': 15,
        'amx_etf': 16,
        'amx_etf_ad': 17
    }
    
    current_order = step_order.get(current_step, 0)
    saved_order = step_order.get(saved_progress.get('step', ''), 0)
    
    return current_order <= saved_order

if __name__ == '__main__':
    
    # Record start time
    start_time = datetime.now(pytz.timezone('Asia/Seoul'))
    pass  # Silent start
    
    # Check saved progress state
    saved_progress = load_progress()
    if saved_progress:
        pass  # Silent progress found
        
    try:
        # Configure logging first
        import logging
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            filename=MainPath + '/Logs/UsGetDataHist.log',
            filemode='a',
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        # Process started - minimal logging
        
        # Token generation
        if not should_skip_step('token', saved_progress):
            if datetime.now() >= datetime.now().replace(hour=1, minute=0):
                save_progress('token', '', 'GetToken')
                
                @retry_with_timeout()
                def get_token_safe():
                    return GetToken()
                
                get_token_safe()
                # Token completed
        else:
            pass  # Silent skip
            
        # Timezone setup
        nyt = pytz.timezone('America/New_York') 
        nyt_time = datetime.now(nyt)
        
        Common.SetChangeMode("KJM_US")
        
        if nyt_time.weekday() == 5 or nyt_time.weekday() == 6:
            pass  # Silent weekend mode
            # Weekend mode
        else:
            pass  # Silent weekday mode
            # Weekday mode
        
        ####################################################
        # Main data collection tasks
        ####################################################
        
        if nyt_time.weekday() == 5:  # Saturday - weekend tasks
            
            # NASDAQ weekly data
            if not should_skip_step('weekend_nas_w', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Weekly data collection', DB.MakeMongoDB_US_W, 'NASDAQ', 'weekend_nas_w')
            
            # NYSE weekly data  
            if not should_skip_step('weekend_nys_w', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Weekly data collection', DB.MakeMongoDB_US_W, 'NYSE', 'weekend_nys_w')
                
            # NASDAQ fundamental data
            if not should_skip_step('weekend_nas_f', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Fundamental data collection', DB.MakeMongoDB_US_F, 'NASDAQ', 'weekend_nas_f')
            
            # NYSE fundamental data
            if not should_skip_step('weekend_nys_f', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Fundamental data collection', DB.MakeMongoDB_US_F, 'NYSE', 'weekend_nys_f')
                        
        else:  # Weekday tasks
            
            # NYSE daily data
            if not should_skip_step('weekday_nys_d', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Daily data collection', DB.MakeMongoDB_US_D, 'NYSE', 'weekday_nys_d')
            
            if not should_skip_step('weekday_nys_ad', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Adjusted daily data collection', DB.MakeMongoDB_US_AD, 'NYSE', 'weekday_nys_ad')
            
            if not should_skip_step('weekday_nys_rs', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Relative strength data collection', DB.MakeMongoDB_US_RS, 'NYSE', 'weekday_nys_rs')
            
            # NASDAQ daily data
            if not should_skip_step('weekday_nas_d', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Daily data collection', DB.MakeMongoDB_US_D, 'NASDAQ', 'weekday_nas_d')
            
            if not should_skip_step('weekday_nas_ad', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Adjusted daily data collection', DB.MakeMongoDB_US_AD, 'NASDAQ', 'weekday_nas_ad')
            
            if not should_skip_step('weekday_nas_rs', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Relative strength data collection', DB.MakeMongoDB_US_RS, 'NASDAQ', 'weekday_nas_rs')

        ####################################################
        # Additional weekend tasks (earnings, monthly data)
        ####################################################
        
        if nyt_time.weekday() == 5:  # Saturday only
            
            # NASDAQ earnings data
            if not should_skip_step('weekend_nas_e', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Earnings data collection', DB.MakeMongoDB_US_E, 'NASDAQ', 'weekend_nas_e')
            
            if not should_skip_step('weekend_nas_m', saved_progress):
                DB = ColMongoUsDB('US','NAS')
                safe_db_operation('Monthly data collection', DB.MakeMongoDB_US_M, 'NASDAQ', 'weekend_nas_m')
            
            # NYSE earnings data
            if not should_skip_step('weekend_nys_e', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Earnings data collection', DB.MakeMongoDB_US_E, 'NYSE', 'weekend_nys_e')
            
            if not should_skip_step('weekend_nys_m', saved_progress):
                DB = ColMongoUsDB('US','NYS')
                safe_db_operation('Monthly data collection', DB.MakeMongoDB_US_M, 'NYSE', 'weekend_nys_m')

        ####################################################        
        # ETF data collection (weekdays only)
        ####################################################
        
        area = 'US'
        market = 'AMX'
        
        if nyt_time.weekday() != 5:  # Not Saturday
            
            if not should_skip_step('amx_etf', saved_progress):
                DB = ColMongoUsDB(area, market)
                safe_db_operation('ETF data collection', DB.MakeMongoDB_US_ETF, 'AMEX', 'amx_etf')
            
            if not should_skip_step('amx_etf_ad', saved_progress):
                DB = ColMongoUsDB(area, market)
                safe_db_operation('ETF adjusted data collection', DB.MakeMongoDB_US_ETF_AD, 'AMEX', 'amx_etf_ad')

        # All tasks completed - clear progress state
        clear_progress()
        
        # Calculate completion time
        kst = pytz.timezone('Asia/Seoul')   
        kst_time = datetime.now(kst)
        end_time = datetime.now(pytz.timezone('Asia/Seoul'))
        
        taking_time = (end_time - start_time).total_seconds()
        taking_H = int(taking_time / 3600)
        taking_M = int((taking_time - taking_H*3600) / 60)
        
        strYMD = str(kst_time.year) + "Y " + str(kst_time.month) + "M " + str(kst_time.day) + "D"
        
        # Completion logging
        if nyt_time.weekday() == 5:
            success_msg = f"UPDATE US DataBase [W/F/E/M] at {kst_time.year}Y {kst_time.month}M {kst_time.day}D ## Takes : {taking_H}H {taking_M}M ## [SUCCESS]"
        else:
            success_msg = f"UPDATE US DataBase [D/AD/RS/ETF] at {kst_time.year}Y {kst_time.month}M {kst_time.day}D ## Takes : {taking_H}H {taking_M}M ## [SUCCESS]"
        
        # Ensure logging is properly configured and write the success message
        print(success_msg)  # Print to console as well
        logging.info(success_msg)
        pass  # Silent completion
            
    except Exception as e:
        # Handle total process failure
        kst_error = datetime.now(pytz.timezone('Asia/Seoul'))
        logging.error(f"UPDATE US DataBase FAILED at {kst_error.year}Y {kst_error.month}M {kst_error.day}D ## Error: {str(e)}")
        
        # Maintain progress state for resume on restart
        sys.exit(1)
        
    ############## FUNDAMENTAL DATA UPDATE ################

