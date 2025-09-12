# -*- coding: utf-8 -*-

import FinanceDataReader as fdr
import json
from pykrx import stock
import Helper.AlphaVantage.AV_API_Helper as Alpha
from DataBase.CalDBName import CalUniverseList
from DataBase.CalDBName import CalFilePath
from Main.Path import MainPath
import os
import pandas as pd

def GetStockList(area, market, Type = 'Stock'):
     
    KoreaStockList = list()
    
    #에러 여부!
    USE_API = "ALPHA" # "KIS" / "ALPHA"

    if area == 'KR':

        if 0:#try:
            
            kospi_list = stock.get_market_ticker_list(market="KOSPI")
            kosdaq_list = stock.get_market_ticker_list(market="KOSDAQ")
            KoreaStockList = kospi_list + kosdaq_list

            #2천개가 안될리가 없다 
            if len(KoreaStockList) < 2000:
                Is_Error = True

        else:#except Exception as e:

            KoreaStockList,  KoreaEtfList = GetKrStockListbyKIS()

            result = "First Try Failed But Make Stock Code Done KR: "+ str(len(KoreaStockList))

        #파일 경로입니다.
        KR_Stock_File_Path = MainPath + "json/List/KR/KrStockCodeList.json"
        KR_ETF_File_Path = MainPath + "json/List/KR/KrEtfCodeList.json"

        #파일에 리스트를 저장합니다
        with open(KR_Stock_File_Path, 'w') as outfile:
            json.dump(KoreaStockList, outfile)
        
        with open(KR_ETF_File_Path, 'w') as outfile:
            json.dump(KoreaEtfList, outfile) 

    elif area == 'US':

        if Type == 'ETF':

            UsEtfList = list()

            AMXStockList,  AMXEtfList = GetUsStockListbyKIS('AMX')
            NASStockList,  NASEtfList = GetUsStockListbyKIS('NAS')
            NYSStockList,  NYSEtfList = GetUsStockListbyKIS('NYS')

            UsEtfList = AMXEtfList + NASEtfList + NYSEtfList

            #파일 경로입니다.
            us_file_path = MainPath + "json/UsETFCodeList.json"

            #파일에 리스트를 저장합니다
            with open(us_file_path, 'w') as outfile:
                json.dump(UsEtfList, outfile)

            result = "Make ETF Code Done US: "+ str(len(UsEtfList))
            print(result)

        elif market == 'AMX':      

            if 1:#USE_API == "KIS":

                USStockList_new,  USEtfList_new = GetUsStockListbyKIS(market)

                result = "First Try Failed But Make Stock Code Done KR: "+ str(len(USStockList_new))

            else:
                df_us1 = fdr.StockListing('AMEX')

                OriUSStockList = df_us1['Symbol'].to_list()

                USStockList_new = list()
                for v in OriUSStockList:
                    if v not in USStockList_new: #중복 제거한다!
                        if v.find(' ') == -1 and v.find('.') == -1: #공백이나 쩜이 있는 코드는 일단 제외시킨다!
                            USStockList_new.append(v)

                result = "Make Stock Code Done KR: "+ str(len(USStockList_new))

            try:

                Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'Stock')
                USStockList_old = CalUniverseList(market, area, 'Stock', Listing = True)

                union_set = set(USStockList_new) | set(USStockList_old)  # 집합 연산을 통한 병합
                USStockList = list(union_set)  # 다시 리스트 형태로 변환

                # 파일에 리스트를 저장합니다.
                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USStockList, outfile)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or writing the file: {e}")
                USStockList = list(set(USStockList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USStockList, outfile)
                    print("New file created successfully.")          

            ################################

            try:
                Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'ETF')
                USEtfList_old = CalUniverseList(market, area, 'ETF', Listing = True)

                union_set = set(USEtfList_new) | set(USEtfList_old)  # 집합 연산을 통한 병합
                USEtfList = list(union_set)  # 다시 리스트 형태로 변환

                # 파일에 리스트를 저장합니다.
                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USEtfList, outfile)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or writing the file: {e}")
                USEtfList = list(set(USEtfList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USEtfList, outfile)
                    print("New file created successfully.")     

            #result = "Make Code AMX : Stocks - " + str(len(USStockList)) + " Etfs - " + str(len(USEtfList))
            #print(result)

        elif market == 'NAS':

            if USE_API == "KIS":

                USStockList_new,  USEtfList_new = GetUsStockListbyKIS(market)

                result = "First Try Failed But Make Stock Code Done KR: "+ str(len(USStockList_new))

            elif USE_API == "ALPHA":

                USStockList_listed   = Alpha.GetTicker('NASDAQ', 'Stock', True)  # Listed
                USStockList_delisted = Alpha.GetTicker('NASDAQ', 'Stock', False) # Delisted
                USStockList_new = USStockList_listed + USStockList_delisted

                USEtfList_new = Alpha.GetTicker('NASDAQ', 'ETF')

                print(f"NAS Stocks: {str(len(USStockList_new))} , NAS ETFs : {str(len(USEtfList_new))}")

            else:

                df_us1 = fdr.StockListing('NASDAQ')

                OriUSStockList = df_us1['Symbol'].to_list()

                USStockList_new = list()
                for v in OriUSStockList:
                    if v not in USStockList_new: #중복 제거한다!
                        if v.find(' ') == -1 and v.find('.') == -1: #공백이나 쩜이 있는 코드는 일단 제외시킨다!
                            USStockList_new.append(v)

                result = "Make Stock Code Done KR: "+ str(len(USStockList_new))

            try:
                
                Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'Stock')
                USStockList_old = CalUniverseList(market, area, 'Stock', Listing = True)

                union_set = set(USStockList_new) | set(USStockList_old)  # 집합 연산을 통한 병합
                USStockList = list(union_set)  # 다시 리스트 형태로 변환

                # 파일에 리스트를 저장합니다.
                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USStockList, outfile)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or writing the file: {e}")
                USStockList = list(set(USStockList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USStockList, outfile)
                    print("New file created successfully.")          

            ################################

            try:
                Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'ETF')
                USEtfList_old = CalUniverseList(market, area, 'ETF', Listing = True)

                union_set = set(USEtfList_new) | set(USEtfList_old)  # 집합 연산을 통한 병합
                USEtfList = list(union_set)  # 다시 리스트 형태로 변환

                # 파일에 리스트를 저장합니다.
                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USEtfList, outfile)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or writing the file: {e}")
                USEtfList = list(set(USEtfList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USEtfList, outfile)
                    print("New file created successfully.")     

            #result = "Make Code NAS : Stocks - " + str(len(USStockList)) + " Etfs - " + str(len(USEtfList))
            #print(result)

        elif market == 'NYS':

            if USE_API == "KIS":

                USStockList_new,  USEtfList_new = GetUsStockListbyKIS(market)

                result = "First Try Failed But Make Stock Code Done KR: "+ str(len(USStockList_new))

            elif USE_API == "ALPHA":

                USStockList_1_listed = Alpha.GetTicker('NYSE', 'Stock', True)
                USStockList_2_listed = Alpha.GetTicker('NYSE MKT', 'Stock', True)
                USStockList_3_listed = Alpha.GetTicker('NYSE ARCA', 'Stock', True)

                USStockList_new_listed = USStockList_1_listed + USStockList_2_listed + USStockList_3_listed

                USStockList_1_delisted = Alpha.GetTicker('NYSE', 'Stock', False)
                USStockList_2_delisted = Alpha.GetTicker('NYSE MKT', 'Stock', False)
                USStockList_3_delisted = Alpha.GetTicker('NYSE ARCA', 'Stock', False)

                USStockList_new_delisted = USStockList_1_delisted + USStockList_2_delisted + USStockList_3_delisted
                USStockList_new = USStockList_new_listed + USStockList_new_delisted

                USEtfList_1 = Alpha.GetTicker('NYSE', 'ETF')
                USEtfList_2 = Alpha.GetTicker('NYSE MKT', 'ETF')
                USEtfList_3 = Alpha.GetTicker('NYSE ARCA', 'ETF')

                USEtfList_new = USEtfList_1 + USEtfList_2 + USEtfList_3

                print(f"NYS Stocks: {str(len(USStockList_new))} , NYS ETFs : {str(len(USEtfList_new))}")

            else:

                df_us1 = fdr.StockListing('NYSE')
                #df_us3 = fdr.StockListing('AMEX')

                OriUSStockList = df_us1['Symbol'].to_list()

                USStockList_new = list()
                for v in OriUSStockList:
                    if v not in USStockList_new: #중복 제거한다!
                        if v.find(' ') == -1 and v.find('.') == -1: #공백이나 쩜이 있는 코드는 일단 제외시킨다!
                            USStockList_new.append(v)

                result = "Make Stock Code Done KR: "+ str(len(USStockList_new))

            ################################

            try:
                Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'Stock')
                USStockList_old = CalUniverseList(market, area, 'Stock', Listing = True)

                union_set = set(USStockList_new) | set(USStockList_old)  # 집합 연산을 통한 병합
                USStockList = list(union_set)  # 다시 리스트 형태로 변환

                # 파일에 리스트를 저장합니다.
                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USStockList, outfile)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or writing the file: {e}")
                USStockList = list(set(USStockList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USStockList, outfile)
                    print("New file created successfully.")         

            ################################

            try:
                Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'ETF')
                USEtfList_old = CalUniverseList(market, area, 'ETF', Listing = True)

                union_set = set(USEtfList_new) | set(USEtfList_old)  # 집합 연산을 통한 병합
                USEtfList = list(union_set)  # 다시 리스트 형태로 변환

                # 파일에 리스트를 저장합니다.
                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USEtfList, outfile)

            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading or writing the file: {e}")
                USEtfList = list(set(USEtfList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

                with open(Listing_file_path, 'w') as outfile:
                    json.dump(USEtfList, outfile)
                    print("New file created successfully.")     

    elif area == 'VT':

        if market == 'HNX':

            if USE_API == "KIS":

                BTStockList,  BTEtfList = GetBTStockListbyKIS(market)

                result = "First Try Failed But Make Stock Code Done KR: "+ str(len(BTStockList))

            else:
                result = "Make Stock Code Done KR: "+ str(len(BTStockList))

            #파일 경로입니다.
            us_file_path = MainPath + "json/HnxStockCodeList.json"

            #파일에 리스트를 저장합니다
            with open(us_file_path, 'w') as outfile:
                json.dump(BTStockList, outfile)

            result = "Make Stock Code Done US: "+ str(len(BTStockList))
            print(result)

        elif market == 'HSX':

            if USE_API == "KIS":

                BTStockList,  BTEtfList = GetBTStockListbyKIS(market)

                result = "First Try Failed But Make Stock Code Done KR: "+ str(len(BTStockList))

            else:
                result = "Make Stock Code Done KR: "+ str(len(BTStockList))

            #파일 경로입니다.
            us_file_path = MainPath + "json/HsxStockCodeList.json"

            #파일에 리스트를 저장합니다
            with open(us_file_path, 'w') as outfile:
                json.dump(BTStockList, outfile)

            result = "Make Stock Code Done US: "+ str(len(BTStockList))
            print(result)

    elif area == 'HK':

        if 1:#USE_API == "KIS":

            USStockList_new,  USEtfList_new = GetUsStockListbyKIS(area)

            result = "First Try Failed But Make Stock Code Done HK: "+ str(len(USStockList_new))

        else:
            df_us1 = fdr.StockListing('SEHK')

            OriHKStockList = df_us1['Symbol'].to_list()

            USStockList_new = list()
            for v in OriHKStockList:
                if v not in USStockList_new: #중복 제거한다!
                    if v.find(' ') == -1 and v.find('.') == -1: #공백이나 쩜이 있는 코드는 일단 제외시킨다!
                        USStockList_new.append(v)

            result = "Make Stock Code Done HK: "+ str(len(USStockList_new))

            ################################
            
        try:
            Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'Stock')
            USStockList_old = CalUniverseList(market, area, 'Stock', Listing = True)

            union_set = set(USStockList_new) | set(USStockList_old)  # 집합 연산을 통한 병합
            USStockList = list(union_set)  # 다시 리스트 형태로 변환

            # 파일에 리스트를 저장합니다.
            with open(Listing_file_path, 'w') as outfile:
                json.dump(USStockList, outfile)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading or writing the file: {e}")
            USStockList = list(set(USStockList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

            with open(Listing_file_path, 'w') as outfile:
                json.dump(USStockList, outfile)
                print("New file created successfully.")         

        ################################

        try:
            Listing_file_path, Delisting_file_path = CalFilePath(market, area, 'ETF')
            USEtfList_old = CalUniverseList(market, area, 'ETF', Listing = True)

            union_set = set(USEtfList_new) | set(USEtfList_old)  # 집합 연산을 통한 병합
            USEtfList = list(union_set)  # 다시 리스트 형태로 변환

            # 파일에 리스트를 저장합니다.
            with open(Listing_file_path, 'w') as outfile:
                json.dump(USEtfList, outfile)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading or writing the file: {e}")
            USEtfList = list(set(USEtfList_new))  # 기존 파일이 문제 있으면 새로운 데이터만 저장

            with open(Listing_file_path, 'w') as outfile:
                json.dump(USEtfList, outfile)
                print("New file created successfully.")   
        
        
def GetKrStockListbyKIS():


    Kospi_stock = []
    Kospi_etf = []

    for master in KisMaster.Kospi.get(): # 코스피 종목 가져오기
        
        #(ST:주권, MF:증권투자회사, RT:부동산투자회사, SC:선박투자회사, IF:사회간접자본투융자회사, DR:주식예탁증서, EW:ELW, EF:ETF, SW:신주인수권증권, SR:신주인수권증서, BC:수익증권, FE:해외ETF, FS:외국주권)
        if master.stkgrp_code == 'ST' or master.stkgrp_code == 'MF' or master.stkgrp_code == 'RT' or master.stkgrp_code == 'SC' or master.stkgrp_code == 'IF' : 
            
            #print(f'[{master.shcode:7}: {master.stdcode}] {master.hname} - {master.stkgrp_code}')
            if master.preferred_stock_code == "0":
                Kospi_stock.append(str(master.shcode))
                #Kospi_stock_dic[str(master.shcode)] = str(master.hname)
                
            else:pass
            
        elif master.stkgrp_code == 'EF':
            Kospi_etf.append(str(master.shcode))
            #Kospi_etf_dic[str(master.shcode)] = str(master.hname)
            
        else:pass

    Kosdaq_stock = []
    Kosdaq_etf = []

    for master in KisMaster.Kosdaq.get(): # 코스닥 종목 가져오기
        if master.stkgrp_code == 'ST' or master.stkgrp_code == 'MF' or master.stkgrp_code == 'RT' or master.stkgrp_code == 'SC' or master.stkgrp_code == 'IF' : 
            
            if master.preferred_stock_code == "0":
                Kosdaq_stock.append(str(master.shcode))
                #Kosdaq_stock_dic[str(master.shcode)] = str(master.hname)

            else:pass
            
        elif master.stkgrp_code == 'EF':
            Kosdaq_etf.append(str(master.shcode))
            #Kosdaq_etf_dic[str(master.shcode)] = str(master.hname)
            
        else:pass

    Korea_stock = Kospi_stock + Kosdaq_stock
    Korea_ETF = Kospi_etf + Kosdaq_etf

    return Korea_stock,  Korea_ETF

def GetUsStockListbyKIS(area):

    if area == 'NAS':

        NAS_stock = []
        NAS_etf = []

        for master in KisMaster.Nasdaq.get(): # 코스피 종목 가져오기

            #(ST:주권, MF:증권투자회사, RT:부동산투자회사, SC:선박투자회사, IF:사회간접자본투융자회사, DR:주식예탁증서, EW:ELW, EF:ETF, SW:신주인수권증권, SR:신주인수권증서, BC:수익증권, FE:해외ETF, FS:외국주권)
            if int(master.stis) == 2:
                
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                NAS_stock.append(str(master.symb))

            elif int(master.stis) == 3:
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                NAS_etf.append(str(master.symb))

            else:pass

        return NAS_stock,  NAS_etf
    
    elif area == 'NYS':

        NYS_stock = []
        NYS_etf = []

        for master in KisMaster.Nyse.get(): # 코스피 종목 가져오기

            #(ST:주권, MF:증권투자회사, RT:부동산투자회사, SC:선박투자회사, IF:사회간접자본투융자회사, DR:주식예탁증서, EW:ELW, EF:ETF, SW:신주인수권증권, SR:신주인수권증서, BC:수익증권, FE:해외ETF, FS:외국주권)
            if int(master.stis) == 2:

                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                NYS_stock.append(str(master.symb))

            elif int(master.stis) == 3:
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                NYS_etf.append(str(master.symb))

            else:pass

        return NYS_stock,  NYS_etf
    
    elif area == 'AMX':

        AMX_stock = []
        AMX_etf = []

        for master in KisMaster.Amex.get(): # 코스피 종목 가져오기

            #(ST:주권, MF:증권투자회사, RT:부동산투자회사, SC:선박투자회사, IF:사회간접자본투융자회사, DR:주식예탁증서, EW:ELW, EF:ETF, SW:신주인수권증권, SR:신주인수권증서, BC:수익증권, FE:해외ETF, FS:외국주권)
            if int(master.stis) == 2:

                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                AMX_stock.append(str(master.symb))

            elif int(master.stis) == 3:
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                AMX_etf.append(str(master.symb))

            else:pass

        return AMX_stock,  AMX_etf
    

    elif area == 'HK':

        HK_stock = []
        HK_etf = []

        for master in KisMaster.Hongkong.get(): # 코스피 종목 가져오기

            #(ST:주권, MF:증권투자회사, RT:부동산투자회사, SC:선박투자회사, IF:사회간접자본투융자회사, DR:주식예탁증서, EW:ELW, EF:ETF, SW:신주인수권증권, SR:신주인수권증서, BC:수익증권, FE:해외ETF, FS:외국주권)
            if int(master.stis) == 2:

                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                HK_stock.append(str(master.symb))

            elif int(master.stis) == 3:
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                HK_etf.append(str(master.symb))

            else:pass

        return HK_stock,  HK_etf   

def GetBTStockListbyKIS(area):

    if area == 'HNX':
        print("DEBIG")
        HNX_stock = []
        HNX_etf = []

        for master in KisMaster.Hanoi.get(): # 코스피 종목 가져오기
            
            if int(master.stis) == 2:

                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                HNX_stock.append(str(master.symb))

            elif int(master.stis) == 3:
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                HNX_etf.append(str(master.symb))

            else:pass

        return HNX_stock,  HNX_etf
    
    elif area == 'HSX':

        HSX_stock = []
        HSX_etf = []

        for master in KisMaster.Hochiminh.get(): # 코스피 종목 가져오기

            #(ST:주권, MF:증권투자회사, RT:부동산투자회사, SC:선박투자회사, IF:사회간접자본투융자회사, DR:주식예탁증서, EW:ELW, EF:ETF, SW:신주인수권증권, SR:신주인수권증서, BC:수익증권, FE:해외ETF, FS:외국주권)
            if int(master.stis) == 2:

                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                HSX_stock.append(str(master.symb))

            elif int(master.stis) == 3:
                #print(f'[{master.exnm:7}: {master.symb}] {master.enam} - {master.etyp}')
                HSX_etf.append(str(master.symb))

            else:pass

        return HSX_stock,  HSX_etf
        
def GetStockListByExcel(sheet_name):
    
    File_path = MainPath + "Excel/" + sheet_name + ".xlsx"

    ## Get Trading Data From Excel
    df_ALL = pd.read_excel(File_path,header= 2,dtype=str,na_values ='NaN')

    Stock_List = []

    for stocks in df_ALL["코드"]:
        stocks = stocks[1:]  
        Stock_List.append(stocks)

    #파일 경로입니다.
    Stock_file_path = MainPath + "json/KrStockCodeList.json"

    #파일에 리스트를 저장합니다
    with open(Stock_file_path, 'w') as outfile:
        json.dump(Stock_List, outfile)

def CallStockList(Market, Area):

    Stock_file_path, Deleted_file_path = CalFilePath(Market, Area, 'Stock')
    
    with open(Stock_file_path, 'r') as json_file:
        UsStockList = json.load(json_file)

        try:
            with open(Deleted_file_path, 'r') as json_file:
                Delete_stocklist = json.load(json_file) 

            # b에 있는 요소를 a에서 삭제
            Universe = [item for item in UsStockList if item not in Delete_stocklist]
        except:
            Universe = UsStockList
    
    return Universe