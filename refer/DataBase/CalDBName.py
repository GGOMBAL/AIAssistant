
from Path import MainPath
import json
import os

def CalDataBaseName(Market, area, p_code, type = 'Stock'):
    
    if area == 'KR':

        if type == 'ETF':
            pass
        else:
            Database_name_M = 'KrDataBase_M'
            Database_name_D = 'KrDataBase_D_ohlcv'
            Database_name_W = 'KrDataBase_W'
            Database_name_RS = 'KrDataBase_RS'
            Database_name_F = 'KrDataBase_F'
            Database_name_E = 'KrDataBase_E'
        
    elif area == 'VT':

        if type == 'ETF':
            pass
        else:
            if Market == 'HNX':
                Database_name_M = 'HnxDataBase_M'
                Database_name_D = 'HnxDataBase_D_ohlcv'
                Database_name_W = 'HnxDataBase_W'
                Database_name_RS = 'HnxDataBase_RS'
                Database_name_F = 'HnxDataBase_F'
                Database_name_E = 'HnxDataBase_E'
            elif Market == 'HSX':
                Database_name_M = 'HsxDataBase_M'
                Database_name_D = 'HsxDataBase_D_ohlcv'
                Database_name_W = 'HsxDataBase_W'
                Database_name_RS = 'HsxDataBase_RS'
                Database_name_F = 'HsxDataBase_F'
                Database_name_E = 'HsxDataBase_E'

    elif area == 'US':

        if type == 'ETF':
            Database_name_M = 'UsEtfDataBase_M'
            Database_name_D = 'UsEtfDataBase_D'
            Database_name_AD = 'UsEtfDataBase_AD'
            Database_name_W = 'UsEtfDataBase_W'           
            Database_name_RS = 'UsEtfDataBase_RS'
            Database_name_F = 'UsEtfDataBase_F'
            Database_name_E = 'UsEtfDataBase_E'
        else:    
            if Market == 'NYS':
                Database_name_M = 'NysDataBase_M'
                Database_name_D = 'NysDataBase_D'
                Database_name_AD = 'NysDataBase_AD'
                Database_name_W = 'NysDataBase_W'           
                Database_name_RS = 'NysDataBase_RS'
                Database_name_F = 'NysDataBase_F'
                Database_name_E = 'NysDataBase_E'
                Database_name_O = 'NysDataBase_O'
                
            elif Market == 'AMX':
                Database_name_M = 'AmxDataBase_M'
                Database_name_D = 'AmxDataBase_D'
                Database_name_AD = 'AmxDataBase_AD'
                Database_name_W = 'AmxDataBase_W'           
                Database_name_RS = 'AmxDataBase_RS'
                Database_name_F = 'AmxDataBase_F'
                Database_name_E = 'AmxDataBase_E'
                Database_name_O = 'AmxDataBase_O'

            else:
                Database_name_M = 'NasDataBase_M'
                Database_name_D = 'NasDataBase_D'
                Database_name_AD = 'NasDataBase_AD'
                Database_name_W = 'NasDataBase_W'           
                Database_name_RS = 'NasDataBase_RS'
                Database_name_F = 'NasDataBase_F'
                Database_name_E = 'NasDataBase_E'
                Database_name_O = 'NasDataBase_O'
    elif area == 'HK':

        if type == 'ETF':
            pass
        else:
            Database_name_M = 'HkDataBase_M'
            Database_name_D = 'HkDataBase_D'
            Database_name_AD = 'HkDataBase_AD'
            Database_name_W = 'HkDataBase_W'           
            Database_name_RS = 'HkDataBase_RS'
            Database_name_F = 'HkDataBase_F'
            Database_name_E = 'HkDataBase_E'

    if p_code == 'M':
        return  Database_name_M
    elif p_code == 'D':
        return  Database_name_D
    elif p_code == 'AD':
        return  Database_name_AD
    elif p_code == 'W':
        return  Database_name_W
    elif p_code == 'RS':
        return  Database_name_RS
    elif p_code == 'F':
        return  Database_name_F
    elif p_code == 'E':
        return  Database_name_E
    elif p_code == 'O':
        return  Database_name_O
        
def CalFilePath(Market, Area, Type):
    
    # 기본값 설정
    Listing_file_path = None
    Delisting_file_path = None

    if Type == 'Stock':

        if Area == 'US':
 
            #파일 경로입니다.
            if Market == 'NAS':
                Listing_file_path = MainPath + "json/List/US/NAS/NasStockList.json"
                Delisting_file_path = MainPath + "json/List/US/NAS/NasStockList_Deleted.json"

            elif Market == 'NYS':
                Listing_file_path = MainPath + "json/List/US/NYS/NysStockList.json"
                Delisting_file_path = MainPath + "json/List/US/NYS/NysStockList_Deleted.json"

            elif Market == 'AMX':
                Listing_file_path = MainPath + "json/List/US/AMX/AmxStockList.json"
                Delisting_file_path = MainPath + "json/List/US/AMX/AmxStockList_Deleted.json"

        elif Area == 'HK':

            Listing_file_path = MainPath + "json/List/HK/NA/HkStockList.json"
            Delisting_file_path = MainPath + "json/List/HK/NA/HkStockList_Deleted.json"

        elif Area == 'KR':
    
            Listing_file_path = MainPath + "json/List/KR/NA/KrStockList.json"
            Delisting_file_path = MainPath + "json/List/KR/NA/KrStockList_Deleted.json"
            
    elif Type == 'ETF':

        if Area == 'US':

            #파일 경로입니다.
            if Market == 'NAS':
                Listing_file_path = MainPath + "json/List/US/NAS/NasEtfList.json"
                Delisting_file_path = MainPath + "json/List/US/NAS/NasEtfList_Deleted.json"
            elif Market == 'NYS':
                Listing_file_path = MainPath + "json/List/US/NYS/NysEtfList.json"
                Delisting_file_path = MainPath + "json/List/US/NYS/NysEtfList_Deleted.json"
            elif Market == 'AMX':
                Listing_file_path = MainPath + "json/List/US/AMX/AmxEtfList.json"
                Delisting_file_path = MainPath + "json/List/US/AMX/AmxEtfList_Deleted.json"
        
        elif Area == 'HK':
    
            Listing_file_path = MainPath + "json/List/HK/NA/HkEtfList.json"
            Delisting_file_path = MainPath + "json/List/HK/NA/HkEtfList_Deleted.json"
            
        elif Area == 'KR':
        
            Listing_file_path = MainPath + "json/List/KR/NA/KrEtfList.json"
            Delisting_file_path = MainPath + "json/List/KR/NA/KrEtfList_Deleted.json"
    else:
        pass

    return Listing_file_path, Delisting_file_path

def CalUniverseList(Market, Area, Type, Listing = True):

    List_file_path, Delist_file_path = CalFilePath(Market, Area, Type)
    
    try:
        with open(List_file_path, 'r') as json_file:
            List_All = json.load(json_file)
    except:
        List_All = list()

    try:
        with open(Delist_file_path, 'r') as json_file:
            delete_list = json.load(json_file)
    except:
        delete_list = list()
       
    Final_List = [item for item in List_All if item not in delete_list]
        
    if Listing == True:                
        return Final_List
    else:
        return delete_list

def ChgTickerName(StockCode, Area):
    """
    티커명을 변환하는 함수.
    
    Parameters:
        Market (str): 원래의 티커 문자열 (예: "00981", "10981", "01981")
        Area (str): 거래소 지역 (예: "HK")
        Type (any): 티커 타입 (현재는 미사용)
        
    Returns:
        str: 변환된 티커 문자열 (예: "0981.HK", "10981.HK", "1981.HK")
    """
    if Area.upper() == "HK":
        # 만약 티커가 5자리이고 앞에 0이 있으면 정수 변환 후 4자리 문자열로 맞춤
        if len(StockCode) == 5 and StockCode.startswith("0"):
            new_ticker = str(int(StockCode)).zfill(4)
        else:
            new_ticker = StockCode
            
        return new_ticker + ".HK"
    
    elif Area.upper() == "KR":
        new_ticker = "A"+str(StockCode)
    
    else:
        new_ticker = str(StockCode)
        
        return new_ticker




        