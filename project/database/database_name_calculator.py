"""
Database Name Calculator - Data Agent Management
Based on refer/Database/CalDBName.py
Calculates database names and file paths for different markets and regions
"""

import json
import os
from typing import Tuple, List, Optional
import logging

# Setup logging
logger = logging.getLogger(__name__)

def calculate_database_name(market: str, area: str, p_code: str, type: str = 'Stock') -> str:
    """
    Calculate database name based on market, area, and data type
    Based on refer/Database/CalDBName.py CalDataBaseName function
    
    Args:
        market: Market identifier (NYS, NAS, AMX, etc.)
        area: Area identifier (US, KR, VT, HK)
        p_code: Data type code (M, D, AD, W, RS, F, E, O)
        type: Security type ('Stock' or 'ETF')
    
    Returns:
        str: Database name
    """
    database_names = {}
    
    if area == 'KR':
        if type == 'ETF':
            # ETF not implemented in reference
            pass
        else:
            database_names = {
                'M': 'KrDataBase_M',
                'D': 'KrDataBase_D_ohlcv',
                'W': 'KrDataBase_W',
                'RS': 'KrDataBase_RS',
                'F': 'KrDataBase_F',
                'E': 'KrDataBase_E'
            }
        
    elif area == 'VT':
        if type == 'ETF':
            # ETF not implemented in reference
            pass
        else:
            if market == 'HNX':
                database_names = {
                    'M': 'HnxDataBase_M',
                    'D': 'HnxDataBase_D_ohlcv',
                    'W': 'HnxDataBase_W',
                    'RS': 'HnxDataBase_RS',
                    'F': 'HnxDataBase_F',
                    'E': 'HnxDataBase_E'
                }
            elif market == 'HSX':
                database_names = {
                    'M': 'HsxDataBase_M',
                    'D': 'HsxDataBase_D_ohlcv',
                    'W': 'HsxDataBase_W',
                    'RS': 'HsxDataBase_RS',
                    'F': 'HsxDataBase_F',
                    'E': 'HsxDataBase_E'
                }

    elif area == 'US':
        if type == 'ETF':
            if market == 'NYS':
                database_names = {
                    'M': 'NysEtfDataBase_M',
                    'D': 'NysEtfDataBase_D',
                    'AD': 'NysEtfDataBase_AD',
                    'W': 'NysEtfDataBase_W',           
                    'RS': 'NysEtfDataBase_RS',
                    'F': 'NysEtfDataBase_F',
                    'E': 'NysEtfDataBase_E'
                }
            elif market == 'AMX':
                database_names = {
                    'M': 'AmxEtfDataBase_M',
                    'D': 'AmxEtfDataBase_D',
                    'AD': 'AmxEtfDataBase_AD',
                    'W': 'AmxEtfDataBase_W',           
                    'RS': 'AmxEtfDataBase_RS',
                    'F': 'AmxEtfDataBase_F',
                    'E': 'AmxEtfDataBase_E'
                }
            else:  # NAS
                database_names = {
                    'M': 'NasEtfDataBase_M',
                    'D': 'NasEtfDataBase_D',
                    'AD': 'NasEtfDataBase_AD',
                    'W': 'NasEtfDataBase_W',           
                    'RS': 'NasEtfDataBase_RS',
                    'F': 'NasEtfDataBase_F',
                    'E': 'NasEtfDataBase_E'
                }
        else:    
            if market == 'NYS':
                database_names = {
                    'M': 'NysDataBase_M',
                    'D': 'NysDataBase_D',
                    'AD': 'NysDataBase_AD',
                    'W': 'NysDataBase_W',           
                    'RS': 'NysDataBase_RS',
                    'F': 'NysDataBase_F',
                    'E': 'NysDataBase_E',
                    'O': 'NysDataBase_O'
                }
            elif market == 'AMX':
                database_names = {
                    'M': 'AmxDataBase_M',
                    'D': 'AmxDataBase_D',
                    'AD': 'AmxDataBase_AD',
                    'W': 'AmxDataBase_W',           
                    'RS': 'AmxDataBase_RS',
                    'F': 'AmxDataBase_F',
                    'E': 'AmxDataBase_E',
                    'O': 'AmxDataBase_O'
                }
            else:  # Default to NAS
                database_names = {
                    'M': 'NasDataBase_M',
                    'D': 'NasDataBase_D',
                    'AD': 'NasDataBase_AD',
                    'W': 'NasDataBase_W',           
                    'RS': 'NasDataBase_RS',
                    'F': 'NasDataBase_F',
                    'E': 'NasDataBase_E',
                    'O': 'NasDataBase_O'
                }
                
    elif area == 'HK':
        if type == 'ETF':
            # ETF not implemented in reference
            pass
        else:
            database_names = {
                'M': 'HkDataBase_M',
                'D': 'HkDataBase_D',
                'AD': 'HkDataBase_AD',
                'W': 'HkDataBase_W',           
                'RS': 'HkDataBase_RS',
                'F': 'HkDataBase_F',
                'E': 'HkDataBase_E'
            }
    
    return database_names.get(p_code, f"Unknown_{area}_{market}_{p_code}")

def calculate_file_path(market: str, area: str, security_type: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Calculate file paths for listing and delisting files
    Based on refer/Database/CalDBName.py CalFilePath function
    
    Args:
        market: Market identifier
        area: Area identifier  
        security_type: 'Stock' or 'ETF'
    
    Returns:
        Tuple of (listing_file_path, delisting_file_path)
    """
    # Base project path (would normally use MainPath)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base_path = os.path.join(project_root, "json", "List")
    
    listing_file_path = None
    delisting_file_path = None

    if security_type == 'Stock':
        if area == 'US':
            if market == 'NAS':
                listing_file_path = os.path.join(base_path, "US", "NAS", "NasStockList.json")
                delisting_file_path = os.path.join(base_path, "US", "NAS", "NasStockList_Deleted.json")
            elif market == 'NYS':
                listing_file_path = os.path.join(base_path, "US", "NYS", "NysStockList.json")
                delisting_file_path = os.path.join(base_path, "US", "NYS", "NysStockList_Deleted.json")
            elif market == 'AMX':
                listing_file_path = os.path.join(base_path, "US", "AMX", "AmxStockList.json")
                delisting_file_path = os.path.join(base_path, "US", "AMX", "AmxStockList_Deleted.json")

        elif area == 'HK':
            listing_file_path = os.path.join(base_path, "HK", "NA", "HkStockList.json")
            delisting_file_path = os.path.join(base_path, "HK", "NA", "HkStockList_Deleted.json")

        elif area == 'KR':
            listing_file_path = os.path.join(base_path, "KR", "NA", "KrStockList.json")
            delisting_file_path = os.path.join(base_path, "KR", "NA", "KrStockList_Deleted.json")
            
    elif security_type == 'ETF':
        if area == 'US':
            if market == 'NAS':
                listing_file_path = os.path.join(base_path, "US", "NAS", "NasEtfList.json")
                delisting_file_path = os.path.join(base_path, "US", "NAS", "NasEtfList_Deleted.json")
            elif market == 'NYS':
                listing_file_path = os.path.join(base_path, "US", "NYS", "NysEtfList.json")
                delisting_file_path = os.path.join(base_path, "US", "NYS", "NysEtfList_Deleted.json")
            elif market == 'AMX':
                listing_file_path = os.path.join(base_path, "US", "AMX", "AmxEtfList.json")
                delisting_file_path = os.path.join(base_path, "US", "AMX", "AmxEtfList_Deleted.json")
        
        elif area == 'HK':
            listing_file_path = os.path.join(base_path, "HK", "NA", "HkEtfList.json")
            delisting_file_path = os.path.join(base_path, "HK", "NA", "HkEtfList_Deleted.json")
            
        elif area == 'KR':
            listing_file_path = os.path.join(base_path, "KR", "NA", "KrEtfList.json")
            delisting_file_path = os.path.join(base_path, "KR", "NA", "KrEtfList_Deleted.json")

    return listing_file_path, delisting_file_path

def calculate_universe_list(market: str, area: str, security_type: str, listing: bool = True) -> List[str]:
    """
    Calculate universe list for given market and area
    Based on refer/Database/CalDBName.py CalUniverseList function
    
    Args:
        market: Market identifier
        area: Area identifier
        security_type: 'Stock' or 'ETF'
        listing: True for active listings, False for delisted securities
    
    Returns:
        List of stock/ETF symbols
    """
    list_file_path, delist_file_path = calculate_file_path(market, area, security_type)
    
    try:
        if list_file_path and os.path.exists(list_file_path):
            with open(list_file_path, 'r', encoding='utf-8') as json_file:
                list_all = json.load(json_file)
        else:
            list_all = []
    except Exception as e:
        logger.warning(f"Could not load listing file {list_file_path}: {e}")
        list_all = []

    try:
        if delist_file_path and os.path.exists(delist_file_path):
            with open(delist_file_path, 'r', encoding='utf-8') as json_file:
                delete_list = json.load(json_file)
        else:
            delete_list = []
    except Exception as e:
        logger.warning(f"Could not load delisting file {delist_file_path}: {e}")
        delete_list = []
       
    final_list = [item for item in list_all if item not in delete_list]
        
    if listing:                
        return final_list
    else:
        return delete_list

def change_ticker_name(stock_code: str, area: str) -> str:
    """
    Transform ticker name based on area
    Based on refer/Database/CalDBName.py ChgTickerName function
    
    Args:
        stock_code: Original ticker code
        area: Area identifier
        
    Returns:
        str: Transformed ticker name
    """
    if area.upper() == "HK":
        # If ticker is 5 digits and starts with 0, convert to integer then back to 4-digit string
        if len(stock_code) == 5 and stock_code.startswith("0"):
            new_ticker = str(int(stock_code)).zfill(4)
        else:
            new_ticker = stock_code
            
        return new_ticker + ".HK"
    
    elif area.upper() == "KR":
        new_ticker = "A" + str(stock_code)
        return new_ticker
    
    else:
        return str(stock_code)

class DatabaseNameCalculator:
    """
    Main class for database name calculations
    Data Agent has exclusive management of this class
    """
    
    def __init__(self):
        """Initialize Database Name Calculator"""
        logger.info("Initialized DatabaseNameCalculator for Data Agent management")
    
    def get_database_name(self, market: str, area: str, p_code: str, security_type: str = 'Stock') -> str:
        """Get database name for given parameters"""
        return calculate_database_name(market, area, p_code, security_type)
    
    def get_file_paths(self, market: str, area: str, security_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Get file paths for listing and delisting files"""
        return calculate_file_path(market, area, security_type)
    
    def get_universe_list(self, market: str, area: str, security_type: str, listing: bool = True) -> List[str]:
        """Get universe list for given market and area"""
        return calculate_universe_list(market, area, security_type, listing)
    
    def transform_ticker_name(self, stock_code: str, area: str) -> str:
        """Transform ticker name based on area"""
        return change_ticker_name(stock_code, area)
    
    def get_summary(self) -> dict:
        """Get summary of database calculator configuration"""
        return {
            'component': 'DatabaseNameCalculator',
            'supported_areas': ['US', 'KR', 'VT', 'HK'],
            'supported_markets': {
                'US': ['NYS', 'NAS', 'AMX'],
                'VT': ['HNX', 'HSX'],
                'KR': ['NA'],
                'HK': ['NA']
            },
            'supported_data_types': ['M', 'D', 'AD', 'W', 'RS', 'F', 'E', 'O'],
            'supported_security_types': ['Stock', 'ETF'],
            'data_agent_managed': True
        }