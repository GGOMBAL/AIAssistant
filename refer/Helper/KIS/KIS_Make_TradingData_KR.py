# -*- coding: utf-8 -*-

import Helper.KIS.KIS_Common as Common
import pprint
import json
import Helper.KIS.KIS_API_Helper_KR as KisKR
import Helper.KIS.KIS_Make_TradingData as KisTRD
import pandas as pd
from Main.Path import MainPath
from datetime import datetime
from datetime import datetime, timedelta
from pykrx import stock
import pytz

def TradingData_Get_KR(KoreaStockList,Mode='None'):
    
    # Define the timezone
    kst = pytz.timezone('Asia/Seoul')

    # Get the current time in KST
    kst_time = datetime.now(kst)

    #년월 문자열을 만든다 즉 2022년 9월이라면 2022_9 라는 문자열이 만들어져 strYM에 들어간다!
    strYMD = str(kst_time.year) + "_" + str(kst_time.month) + "_" + str(kst_time.day)

    YMDDict = dict()
    YMDDict['ymd_st'] = strYMD

    #Common.SetChangeMode("VIRTUAL1")
    
    if Mode == 'None':

        TradingData = TradingData_Get_KR_Sub(KoreaStockList)

    else:

        Folder_Path =  MainPath + "json/Account/"
        YMD_file_path = Folder_Path + Mode + strYMD + ".json"
        
        try:
            with open(YMD_file_path, 'r'):

                Data_file_path = MainPath + "json/Trading/" + Mode + "_TradingData.json" 
                with open(Data_file_path, 'r') as json_file:
                    TradingData = json.load(json_file)
        except:
        
            TradingData = TradingData_Get_KR_Sub(KoreaStockList)
        
            with open(YMD_file_path, 'w') as outfile:
                json.dump(YMDDict, outfile)   

    return TradingData

def TradingData_Get_KR_Sub(KoreaStockList):
        
    KrTradingDataList = list()

    for i in range(len(KoreaStockList)):
    
        stock_code = KoreaStockList[i]

        if 1:#try:
            pprint.pprint("Make Trading Data Progress : " + str(i+1) + " / " + str(len(KoreaStockList)))
 
            df_W = KisKR.GetOhlcv(stock_code,"W",datetime.now() - timedelta(days=365*2),datetime.now(),adVar=0)
            df_W = df_W.set_index(pd.to_datetime(df_W.index))

            df_KRX = Common.GetKRXOhlcv(stock_code,datetime.now() - timedelta(days=365*2),datetime.now(),adVar=0)
            df_KRX = df_KRX.set_index(pd.to_datetime(df_KRX.index))
            
            df_D = KisKR.GetOhlcv(stock_code,'D',datetime.now() - timedelta(days=365*2),datetime.now(),adVar=0)
            df_D = df_D.set_index(pd.to_datetime(df_D.index))

            #############################################################################

            TradingDataDict = KisTRD.GetTRDDataDic(df_D,df_W,df_KRX,stock_code)

            KrTradingDataList.append(TradingDataDict)

        else:#except Exception as e:
            pprint.pprint(e)

    return KrTradingDataList
################################################################################################################

