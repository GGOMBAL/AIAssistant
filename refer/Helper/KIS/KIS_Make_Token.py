import Helper.KIS.KIS_Common as common
import time
import json
from Main.Path import MainPath
import Helper.LS.LS_Common as LScommon

def GetToken(mode='ALL'):

    time_info = time.gmtime()   
    strYMD = str(time_info.tm_year) + "_" + str(time_info.tm_mon) + "_" + str(time_info.tm_mday)
    
    Folder_Path =  MainPath + "json/token/"
    YMD_file_path = Folder_Path + "KisToken.json"
    
    #실 계좌 모의 계좌의 토큰 값을 받아서 파일에 저장합니다.
    
    try:
        with open(YMD_file_path, 'r') as json_file:
            YMDDict = json.load(json_file)
            
            if YMDDict['ymd_st'] == strYMD:
                pass
            else:
                common.MakeToken("KJM_US")
                YMDDict = dict()
                YMDDict['ymd_st'] = strYMD
        
                with open(YMD_file_path, 'w') as outfile:
                    json.dump(YMDDict, outfile) 
    except:    
            common.MakeToken("KJM_US")
            
            YMDDict = dict()
            YMDDict['ymd_st'] = strYMD
        
            with open(YMD_file_path, 'w') as outfile:
                json.dump(YMDDict, outfile)       