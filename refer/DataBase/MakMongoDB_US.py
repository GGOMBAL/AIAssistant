import pymongo
from Path import MainPath
import Helper.KIS.KIS_Common as Common 
import json
import pandas as pd
from DataBase.CalMongoDB import MongoDB

from DataBase.CalDBName import CalFilePath
from DataBase.CalDBName import CalUniverseList
from DataBase.CalDBName import CalDataBaseName
from DataBase.CalDBName import ChgTickerName

from datetime import datetime, timedelta, time as dt_time
import Helper.KIS.KIS_API_Helper_US as KisUS
import Helper.DataBento.DataBento_API_Helper as Bento
import Helper.AlphaVantage.AV_API_Helper as Alpha
from Helper.KIS.KIS_Make_StockList import GetStockList
import pytz
import time
import pprint
import glob
import os
import yaml
        
import subprocess
import os
import logging
import finnhub
from multiprocessing import Pool
from databento import DBNStore

class ColMongoUsDB:

    def __init__(self,area,market):

        with open(MainPath + 'myStockInfo.yaml', encoding='UTF-8') as f:
            self.stock_info = yaml.load(f, Loader=yaml.FullLoader)

        self.area = area
        self.market = market
        
        # Define the timezone
        self.end_day   = datetime.now(pytz.utc)
        self.start_day = (datetime.now(pytz.utc) - timedelta(days=365*30))

        GetStockList(self.area, self.market)
        
        # JSON FILE PATH #######################################################
        self.Stock_List_file_path, self.Stock_Delist_file_path = CalFilePath(self.market, self.area, 'Stock')
        self.ETF_List_file_path, self.ETF_Delist_file_path = CalFilePath(self.market, self.area, 'ETF')
        
        # STOCK LIST CALL ######################################################
        self.StockList_US = CalUniverseList(self.market, self.area, 'Stock', Listing = True)
        self.delete_stocklist = CalUniverseList(self.market, self.area, 'Stock', Listing = False)

        with open(self.Stock_Delist_file_path, 'r') as json_file:
            self.delete_stocklist_manual = json.load(json_file)

        self.delete_stocklist = list(set(self.delete_stocklist) | set(self.delete_stocklist_manual))  # 합집합

        self.EtfList_US = CalUniverseList(self.market, self.area, 'ETF', Listing = True)
        self.delete_Etflist = CalUniverseList(self.market, self.area, 'ETF', Listing = False)

        ########################################################################    
        df_D = Alpha.GetOhlcv_Bender('AAPL', 'comfact', start_date='None')
        df_D.index = pd.to_datetime(df_D.index)
        self.latest_D = df_D.index[-1]
        self.latest_D = self.latest_D.tz_localize(pytz.timezone('UTC')).date()
        
        df_W = Alpha.GetOhlcv_Bender('AAPL', 'comfact', start_date='None')
        df_W.index = pd.to_datetime(df_W.index)
        last_valid_date = df_W.index.max()
        df_W = df_W.resample(rule='W-FRI').last()
        df_W = df_W[df_W.index <= last_valid_date]
        
        self.latest_W = df_W.index[-1] # datetime
        self.latest_W = self.latest_W.tz_localize(pytz.timezone('UTC')).date()       
    
    ###### ETF FUNCTION #########
    
    def MakeMongoDB_US_ETF(self, ohlcv = 'N'):
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.area + 'EtfGetData_D.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'EtfGetData_D.log'

        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
                
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        
        self.etf_database_name = CalDataBaseName(self.market, self.area, "D", "ETF")
        print(self.etf_database_name)
                
        self.db = conn.get_database(self.etf_database_name)
        totallength = len(self.EtfList_US)
        
        ####################################      

        for count in range(len(self.EtfList_US)):

            stocks = self.EtfList_US[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.etf_database_name, stocks, 'US') == True:

                try:
                    
                    # MongoDB에 저장된 마지막 날짜 가져오기
                    last_date_in_db = collection.find_one(sort=[('Date', -1)])['Date']
                    LatestDateinDB = last_date_in_db.date()

                    if self.latest_D > LatestDateinDB:

                        df_ALL = DB.GetStockHis(stocks, 'D', last_date_in_db, self.end_day, 'US', ohlcv)       ## KIS 주가데이터

                        # MongoDB에 없는 데이터만 필터링
                        df_ALL = df_ALL[df_ALL.index > last_date_in_db]
                        
                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)                      
                        
                        logging.info(f"{count} / {totallength} - UPDATE(ETF-D)    {stocks} TimeFrame : {LatestDateinDB} => {self.latest_D}")             

                    else:

                        logging.info(f"{count} / {totallength} - EXIST(ETF-D)    {stocks} TimeFrame : {LatestDateinDB} => {self.latest_D}")

                except Exception as e:
                    logging.info("Exception ", e)
                    self.delete_Etflist.append(stocks)   

            else:
                
                try:
                    
                    df_ALL = DB.GetStockHis(stocks, 'D', self.start_day, self.end_day,'US', ohlcv)    ## KIS 주가데이터
                    
                    ## 중복 인덱스 제거 ##
                    df_ALL = df_ALL[~df_ALL.index.duplicated(keep='first')]
                    df_ALL.index = df_ALL.index.tz_localize('UTC')
                    
                    logging.info(f"{count} / {totallength} - NEW(ETF-D)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]}")
                    
                    df_ALL = df_ALL.reset_index()

                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)
                    
                except Exception as e:
                    logging.info("Exception : ",stocks, e)
                    self.delete_Etflist.append(stocks)
                    
            stocks = self.EtfList_US[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

        with open(self.ETF_Delist_file_path, 'r') as json_file:
            TempUsStockList = json.load(json_file)

        self.delete_etflist = list(set(TempUsStockList) | set(self.delete_Etflist))

        with open(self.ETF_Delist_file_path, 'w') as outfile:
            json.dump(self.delete_Etflist, outfile)

    def MakeMongoDB_US_ETF_AD(self):


        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.area + 'EtfGetData_AD.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'EtfGetData_AD.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        str_database_name_D = CalDataBaseName(self.market, self.area, "D", "ETF")
        str_database_name_AD = CalDataBaseName(self.market, self.area, "AD", "ETF")
            
        db = conn.get_database(str_database_name_AD)
        self.df_D, self.EtfList_US = DB.ReadDataBase(self.EtfList_US, 'US', self.area, str_database_name_D, self.start_day, self.end_day)
        
        self.df_AD = self.CalcAdDataframe("D",self.EtfList_US)
        df =  self.df_AD
        
        totallength = len(self.EtfList_US)

        ####################################      

        for count in range(len(self.EtfList_US)):

            stocks = self.EtfList_US[count]
            collection = db.get_collection(stocks)

            try:
                ## 중복 인덱스 제거 ##
                df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]
                       
                logging.info(f"{count} / {totallength} - NEW(ETF_AD)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")

                # 데이터프레임을 딕셔너리로 변환
                df[stocks] = df[stocks].reset_index()  
                data_dict = df[stocks].to_dict("records")

                # MongoDB에 데이터 삽입
                collection.insert_many(data_dict)

            except Exception as e:
                print("Exception ", e)
                        
    ###### STOCK FUNCTION #######
        
    def MakeMongoDB_US_M(self):
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_M.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_M.log'
        
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        # Define the timezone
        utc = pytz.timezone('UTC')  
        # Get the current time in KST
        Initial_time = datetime.now(utc)
        
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],
                                   maxIdleTimeMS=120000,
                                   serverSelectionTimeoutMS=30000)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        self.str_database_name = CalDataBaseName(self.market, self.area, "M", "Stock")
        self.db = conn.get_database(self.str_database_name)
        totallength = len(self.StockList_US)

        for count in range(len(self.StockList_US)):
            
            stocks = self.StockList_US[count]
            
            collection = self.db.get_collection(stocks)

            if DB.ChkTableExist(self.str_database_name, stocks,'US') == True:         
                
                # MongoDB에 저장된 마지막 날짜 가져오기
                try:
                
                    latest_in_db = collection.find_one(sort=[('Datetime', -1)])['Datetime']                   
                    LatestDateinDB = latest_in_db.date()

                    if self.latest_D > LatestDateinDB:

                        df_ALL = Alpha.GetOhlcvMin_Bender(stocks, '1min', 'full', start_date=LatestDateinDB)

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Datetime'] = date
                            collection.insert_one(data)
                        
                        #end_time = datetime.now(utc)
                        #taking_time = (end_time - start_time).total_seconds()

                        logging.info(f"{count} / {totallength} - UPDATE(M)    {stocks} TimeFrame : {LatestDateinDB} => {self.latest_D}")
                    
                    else:
                        logging.info(f"{count} / {totallength} - EXIST(M)    {stocks}")
                
                except Exception as e:
                    logging.info(f"Exception {stocks} - {e}")
                    self.delete_stocklist.append(stocks)  

            else:
                
                try:

                    df_ALL = Alpha.GetOhlcvMin_Bender(stocks, '1min', 'full', start_date='None')
                    
                    df_ALL = df_ALL.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                    #end_time = datetime.now(utc)
                    #taking_time = (end_time - start_time).total_seconds()
                    
                    logging.info(f"{count} / {totallength} - NEW(M)    {stocks}")

                except Exception as e:
                    logging.info(f"Exception {stocks} - {e}")

        # Define the timezone
        utc = pytz.timezone('UTC')  

        # Get the current time in KST
        end_time = datetime.now(utc)
        taking_time = end_time - Initial_time
        logging.info(f"Get US Data Gettering Finished.. Total time : {taking_time}")

        ## deleted stock saved ##
        if self.market == 'NAS':
            file_path = MainPath + "json/NasdaqDeleteStockList.json"
        elif self.market == 'NYS':
            file_path = MainPath + "json/NyseDeleteStockList.json"
        elif self.market == 'AMX':
            file_path = MainPath + "json/AmexDeleteStockList.json"

        with open(file_path, 'w') as outfile:
            json.dump(self.delete_stocklist, outfile)

    def MakeMongoDB_US_D(self, ohlcv = 'N'):
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_D.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_D.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")


        if ohlcv == 'N':
            self.str_database_name = CalDataBaseName(self.market, self.area, "D", "Stock")
        else:            
            self.str_database_name = CalDataBaseName(self.market, self.area, "AD", "Stock")
            
        self.db = conn.get_database(self.str_database_name)
        totallength = len(self.StockList_US)

        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            
            if ohlcv == 'Y': #yfinance 티커로 변경경
                renamed_stock = ChgTickerName(stocks, self.area)
            else:        
                renamed_stock = str(stocks)
                
            collection = self.db.get_collection(stocks)
            #collection.create_index([('Date', pymongo.DESCENDING)])
            
            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:

                try:
                    
                    # MongoDB에 저장된 마지막 날짜 가져오기
                    last_date_in_db = collection.find_one(sort=[('Date', -1)])['Date']
                    LatestDateinDB = last_date_in_db.date()
                           
                    if self.end_day.date() > LatestDateinDB:

                        df_ALL = DB.GetStockHis(renamed_stock, 'D', last_date_in_db, self.end_day, self.area, ohlcv)       ## KIS 주가데이터

                        # MongoDB에 없는 데이터만 필터링
                        df_ALL = df_ALL[df_ALL.index > last_date_in_db]

                        if ohlcv == 'Y' and not df_ALL.empty:
                            
                            # 새 데이터 중 split_factor 값이 하나라도 0이 아니면 전체 데이터를 대체
                            if (df_ALL['split_factor'] != 0).any():
                                # 기존 데이터 삭제
                                collection.delete_many({})
                                # 전체 기간의 데이터 재조회
                                df_ALL = DB.GetStockHis(renamed_stock, 'D', self.start_day, self.end_day, self.area, ohlcv)
                                # 중복 인덱스 제거 및 타임존 로컬라이즈
                                df_ALL = df_ALL[~df_ALL.index.duplicated(keep='first')]
                                df_ALL.index = df_ALL.index.tz_localize('UTC')

                                logging.info(f"{count} / {totallength} - REPLACE(D) {stocks} due to nonzero split_factor. New TimeFrame: {df_ALL.index[0]} => {df_ALL.index[-1]}")
                                print(f"{count} / {totallength} - REPLACE(D) {stocks} due to nonzero split_factor. New TimeFrame: {df_ALL.index[0]} => {df_ALL.index[-1]}")  
                                
                                # DataFrame을 딕셔너리 리스트로 변환 후 삽입
                                df_ALL = df_ALL.reset_index()
                                data_dict = df_ALL.to_dict("records")

                                collection.drop()
                                collection.insert_many(data_dict)
                                
                            else:
                                # split_factor가 모두 0이면 기존 데이터에 이어 붙임
                                logging.info(f"{count} / {totallength} - UPDATE(D) {stocks} TimeFrame: {LatestDateinDB} => {self.latest_D}")
                                print(f"{count} / {totallength} - UPDATE(D) {stocks} TimeFrame: {LatestDateinDB} => {self.latest_D}")
                                
                                for date, row in df_ALL.iterrows():
                                    data = row.to_dict()
                                    data['Date'] = date
                                    collection.insert_one(data)
                                    
                        elif ohlcv == 'N' and not df_ALL.empty:

                            # 필터링된 데이터를 MongoDB에 저장
                            for date, row in df_ALL.iterrows():
                                #print(date, row)
                                data = row.to_dict()
                                data['Date'] = date
                                collection.insert_one(data)

                            #end_time = datetime.now(utc)
                            #taking_time = (end_time - start_time).total_seconds()

                            logging.info(f"{count} / {totallength} - UPDATE(D)    {stocks} TimeFrame : {LatestDateinDB} => {self.latest_D}")
                            print(f"{count} / {totallength} - UPDATE(D)    {stocks} TimeFrame : {LatestDateinDB} => {self.latest_D}")

                        else:

                            logging.info(f"{count} / {totallength} - EXIST(D)    {stocks} TimeFrame : {LatestDateinDB}")
                            print(f"{count} / {totallength} - EXIST(D)    {stocks} TimeFrame : {LatestDateinDB}")
                    else:

                        logging.info(f"{count} / {totallength} - EXIST(D)    {stocks} TimeFrame : {LatestDateinDB} => {self.end_day.date()}")
                        print(f"{count} / {totallength} - EXIST(D)    {stocks} TimeFrame : {LatestDateinDB} => {self.end_day.date()}")
                            
                except Exception as e:
                    logging.info("Exception ", e)
                    print("Exception ", e)

            else:
                
                try:
                    
                    df_ALL = DB.GetStockHis(renamed_stock, 'D', self.start_day, self.end_day, self.area, ohlcv)    ## KIS 주가데이터
                    
                    ## 중복 인덱스 제거 ##
                    df_ALL = df_ALL[~df_ALL.index.duplicated(keep='first')]
                    df_ALL.index = df_ALL.index.tz_localize('UTC')
                    logging.info(f"{count} / {totallength} - NEW(D)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]}")    
                    print(f"{count} / {totallength} - NEW(D)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]}")              
                    # 데이터프레임을 딕셔너리로 변환
                    df_ALL = df_ALL.reset_index()
                    data_dict = df_ALL.to_dict("records")
                    
                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)
                    
                except Exception as e:

                    if stocks not in self.delete_stocklist:
                        self.delete_stocklist.append(stocks)

        with open(self.Stock_Delist_file_path, 'w') as outfile:
            json.dump(self.delete_stocklist, outfile)            

    def MakeMongoDB_US_AD(self):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_AD.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_AD.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        str_database_name_D = CalDataBaseName(self.market, self.area, "D", "Stock")
        str_database_name_AD = CalDataBaseName(self.market, self.area, "AD", "Stock")
            
        db = conn.get_database(str_database_name_AD)
        self.df_D, self.StockList_US = DB.ReadDataBase(self.StockList_US, 'US', self.area, str_database_name_D, self.start_day, self.end_day)
        
        self.df_AD = self.CalcAdDataframe("D",self.StockList_US)
        df =  self.df_AD
        
        totallength = len(self.StockList_US)
        ####################################      

        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            collection = db.get_collection(stocks)

            try:
                ## 중복 인덱스 제거 ##
                df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]
                       
                logging.info(f"{count} / {totallength} - NEW(AD)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")
                print(f"{count} / {totallength} - NEW(AD)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")

                # 데이터프레임을 딕셔너리로 변환
                df[stocks] = df[stocks].reset_index()  
                data_dict = df[stocks].to_dict("records")

                # MongoDB에 데이터 삽입
                collection.drop()
                collection.insert_many(data_dict)

            except Exception as e:
                print("Exception ", e)

    def MakeMongoDB_US_D_Reverse(self):
    
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_RD.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_RD.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        str_database_name_D = CalDataBaseName(self.market, self.area, "D", "Stock")
        str_database_name_AD = CalDataBaseName(self.market, self.area, "AD", "Stock")
            
        db = conn.get_database(str_database_name_D)
        self.df_AD, self.StockList_US = DB.ReadDataBase(self.StockList_US, self.market, self.area, str_database_name_AD, self.start_day, self.end_day)

        self.df_D = self.CalcAdDataframe_Reverse("D")
        df =  self.df_D
        

        totallength = len(self.StockList_US)
        ####################################      

        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            collection = db.get_collection(stocks)

            try:
                ## 중복 인덱스 제거 ##
                df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]
                       
                logging.info(f"{count} / {totallength} - NEW(D)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")
                print(f"{count} / {totallength} - NEW(D)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")

                # 데이터프레임을 딕셔너리로 변환
                df[stocks] = df[stocks].reset_index()  
                data_dict = df[stocks].to_dict("records")

                # MongoDB에 데이터 삽입
                collection.insert_many(data_dict)

            except Exception as e:
                print("Exception ", e)
                
    def MakeMongoDB_US_W(self):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_W.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_W.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        self.str_database_name = CalDataBaseName(self.market, self.area, "W", "Stock")

        self.db = conn.get_database(self.str_database_name)
        
        str_database_name_D = CalDataBaseName(self.market, self.area, "AD", "Stock")
        
        #// 데이터베이스 정보를 가져온다
        df_D_Temp, self.StockList_US = DB.ReadDataBase(self.StockList_US, self.market, self.area, str_database_name_D, self.start_day, self.end_day)

        # 빈 dict 생성
        df = {}
                
        # 주봉 데이터 생성
        for key, df_temp in df_D_Temp.items():
            
            last_valid_date = df_temp.index.max()
            
            # 주간 단위로 resample
            df_resampled = df_temp.resample(rule='W-FRI')

            # 시가: 그 주의 첫 번째 거래일(보통 월요일) 시가
            open_price = df_resampled.first()['ad_open']
    
            # 고가: 그 주의 가장 높은 가격
            high_price = df_resampled.max()['ad_high']
    
            # 저가: 그 주의 가장 낮은 가격
            low_price = df_resampled.min()['ad_low']
    
            # 종가: 그 주의 마지막 거래일(보통 금요일) 종가
            close_price = df_resampled.last()['ad_close']
            
            volume = df_resampled.sum()['volume']
            
            #adfact = df_resampled['adfac'].apply(lambda x: x.prod())
            
            # 주봉 데이터프레임 생성
            df[key] = pd.DataFrame({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
                #'adfac': adfact
            })
            
            df[key] = df[key][df[key].index <= last_valid_date]
            df[key] = df[key][~df[key].index.duplicated(keep='first')]

            #df[key].index = df[key].index.tz_localize('UTC')
        
        self.df_W = df
        totallength = len(self.StockList_US)
        
        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]

            collection = self.db.get_collection(stocks)

            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_week_in_db_new = df[stocks].index[-1]
                
                if last_week_in_db_new.date() > last_week_in_db_old.date():

                    try:

                        ## 중복 인덱스 제거 ##
                        df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]
    
                        logging.info(f"{count} / {totallength} - NEW(W)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")
                        print(f"{count} / {totallength} - NEW(W)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")
    
                        # 데이터프레임을 딕셔너리로 변환
                        df[stocks] = df[stocks].reset_index()  
                        data_dict = df[stocks].to_dict("records")
    
                        # MongoDB에 데이터 삽입
                        collection.insert_many(data_dict)

                    except Exception as e:
                        print("Exception ", e)

                else:

                    logging.info(f"{count} / {totallength} - EXIST(W)    {stocks} TimeFrame : {last_week_in_db_new.date()} => {last_week_in_db_old.date()}")
                    print(f"{count} / {totallength} - EXIST(W)    {stocks} TimeFrame : {last_week_in_db_new.date()} => {last_week_in_db_old.date()}")

            else:
                
                try:
                    ## 중복 인덱스 제거 ##
                    df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]

                    logging.info(f"{count} / {totallength} - NEW(W)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")
                    print(f"{count} / {totallength} - NEW(W)    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")

                    # 데이터프레임을 딕셔너리로 변환
                    df[stocks] = df[stocks].reset_index()  
                    data_dict = df[stocks].to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.drop()
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)  
                    
    def MakeMongoDB_US_RS_SUB(self):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        #// 데이터베이스 정보를 가져온다
        self.str_database_name = CalDataBaseName(self.market, self.area, "AD", "Stock")

        self.db = conn.get_database(self.str_database_name)

        df_RS_4W = pd.DataFrame()
        df_RS_12W = pd.DataFrame()

        for count in range(len(self.StockList_US)):

            try:
                stocks = self.StockList_US[count]
                db_name = self.str_database_name

                df = DB.ExecuteSql(db_name, stocks)
                df = df[~df.index.duplicated(keep='first')]
                df_RS = df['ad_close']
                df_RS.name = stocks            

                try:
                    #df_RS_4W = (df_RS - df_RS.shift(4)) / df_RS.shift(4) * 100
                    df_RS_4W = (df_RS - df_RS.shift(4*5)) / df_RS.shift(4*5) * 100

                    if count == 0:
                        df_ALL_4W = df_RS_4W 
                    else:
                        df_ALL_4W = pd.concat([df_ALL_4W,df_RS_4W], axis=1)               
                except:pass


                try:
                    df_RS_12W = (df_RS - df_RS.shift(12*5)) / df_RS.shift(12*5) * 100
                    if count == 0:
                        df_ALL_12W = df_RS_12W 

                    else:
                        df_ALL_12W = pd.concat([df_ALL_12W,df_RS_12W], axis=1)              
                except:pass

                
            except Exception as e:
                print("Exception ", e)
        # 각 날짜별로 순위를 매기고, 결과를 원래 데이터 위치에 씌우기
        try:
            ranked_df_4W = df_ALL_4W.apply(self.rank_stocks, axis=0)
            ranked_df_4W = (ranked_df_4W*100).round(2)
            ranked_df_4W = ranked_df_4W.dropna(axis=0, how='all')

            ranked_df_12W = df_ALL_12W.apply(self.rank_stocks, axis=0)
            ranked_df_12W = (ranked_df_12W*100).round(2)   
            ranked_df_12W = ranked_df_12W.dropna(axis=0, how='all')   
        except:
            ranked_df_4W = 0
            ranked_df_12W = 0
        
        return ranked_df_4W, ranked_df_12W

    def MakeMongoDB_US_RS(self):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_RS.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_RS.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        ranked_df_4W, ranked_df_12W = self.MakeMongoDB_US_RS_SUB()

        Empty_Stocks = 0
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        self.str_database_name = CalDataBaseName(self.market, self.area, "RS", "Stock")
        self.db = conn.get_database(self.str_database_name)
        
        totallength = len(self.StockList_US)
        
        str_database_name_O = CalDataBaseName(self.market, self.area, "O", "Stock")
        
        ####################################        
        df_dict = dict()
        
        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            
            collection = self.db.get_collection(stocks)
                            
            try:
                Overiew = DB.ExecuteSql(str_database_name_O, stocks)
                
                finnhub_client = finnhub.Client(api_key=self.stock_info["FINNHUB_API_KEY"])
                output = finnhub_client.company_profile2(symbol=stocks)
                
                df_RS = pd.concat([ranked_df_4W[stocks], ranked_df_12W[stocks]], axis=1)
                df_RS.columns = ['RS_4W', 'RS_12W']
                df_RS = df_RS.dropna()
                df_RS['Sector'] = output['finnhubIndustry'] #Overiew['Sector'].iloc[-1]
                df_RS['Industry'] = Overiew['Industry'].iloc[-1]
                
                df_dict[stocks] = df_RS

                print(f"{count} / {totallength} - NEW(RS)    {stocks} ")                     
                
            except Exception as e:
                Empty_Stocks = Empty_Stocks + 1

        logging.info(" ## Start Sector RS Calculate by datetime ... ## ")
        
        # 함수 실행
        final_data = self.calculate_and_add_group_rs(df_dict)
        
        logging.info(" ## Finish Sector RS ## ")
        
        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            
            collection = self.db.get_collection(stocks)
                            
            try:
                
                # 데이터프레임을 딕셔너리로 변환
                final_data[stocks] = final_data[stocks].reset_index()  
                data_dict = final_data[stocks].to_dict("records")

                # MongoDB에 데이터 삽입
                collection.drop()
                collection.insert_many(data_dict)
                        
                logging.info(f"{count} / {totallength} - NEW(RS)    {stocks} ")
                print(f"{count} / {totallength} - NEW(RS)    {stocks} ")                     
                
            except Exception as e:
                Empty_Stocks = Empty_Stocks + 1
                    
    def MakeMongoDB_US_F(self):

        # Define the timezone
        utc = pytz.timezone('UTC')  

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_F.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_F.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        self.str_database_name = CalDataBaseName(self.market, self.area, "F", "Stock")
        self.db = conn.get_database(self.str_database_name)
        totallength = len(self.StockList_US)
        ####################################      

        for count in range(len(self.StockList_US)):

            time.sleep(1) # 1분에 75개 데이터만 허용
            stocks = self.StockList_US[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

            # Get the current time in KST
            start_time = datetime.now(utc)

            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                try:
                    last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                    LatestWeekinDB = last_week_in_db_old.date()
                    latest_updae = Alpha.ChkUsFndmDataUpdate(stocks, RequestType = 'LatestUpdate')

                    if latest_updae > LatestWeekinDB:

                        df_ALL = DB.GetStockHisFdmt(stocks)    ## KIS 주가데이터                     

                        # 데이터프레임을 딕셔너리로 변환
                        df_ALL = df_ALL.reset_index()  
                        data_dict = df_ALL.to_dict("records")

                        # MongoDB에 데이터 삽입
                        collection.insert_many(data_dict)

                        logging.info(f"{count} / {totallength} - UPDATE(F)    {stocks} TimeFrame : {LatestWeekinDB} => {latest_updae}")
                        print(f"{count} / {totallength} - UPDATE(F)    {stocks} TimeFrame : {LatestWeekinDB} => {latest_updae}")

                    else:

                        logging.info(f"{count} / {totallength} - EXIST(F)    {stocks}")
                        print(f"{count} / {totallength} - EXIST(F)    {stocks}")
                
                except Exception as e:
                    logging.info(f"Exception {stocks}")
            else:
                
                try:
                    df_ALL = DB.GetStockHisFdmt(stocks)    ## KIS 주가데이터                     

                    # 데이터프레임을 딕셔너리로 변환
                    df_ALL = df_ALL.reset_index()  
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                    logging.info(f"{count} / {totallength} - NEW(F)    {stocks} ")
                    print(f"{count} / {totallength} - NEW(F)    {stocks} ")
                except Exception as e:
                    logging.info(f"Exception {stocks}")

    def MakeMongoDB_US_E(self):
    
        # Define the timezone
        utc = pytz.timezone('UTC')  

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_E.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_E.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        self.str_database_name = CalDataBaseName(self.market, self.area, "E", "Stock")
        self.db = conn.get_database(self.str_database_name)
        totallength = len(self.StockList_US)
        ####################################      

        for count in range(len(self.StockList_US)):

            time.sleep(1) # 1분에 75개 데이터만 허용
            stocks = self.StockList_US[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                try:
                    last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                    LatestWeekinDB = last_week_in_db_old.date()
                    latest_update = Alpha.ChkUsFndmDataUpdate(stocks, RequestType = 'LatestUpdate')

                    if latest_update > LatestWeekinDB:

                        df_ALL = DB.GetStockHisEarn(stocks)    ## KIS 주가데이터                     

                        # 데이터프레임을 딕셔너리로 변환
                        df_ALL = df_ALL.reset_index()  
                        data_dict = df_ALL.to_dict("records")

                        # MongoDB에 데이터 삽입
                        collection.insert_many(data_dict)

                        logging.info(f"{count} / {totallength} - UPDATE(E)    {stocks} TimeFrame : {LatestWeekinDB} => {latest_update}")
                        print(f"{count} / {totallength} - UPDATE(E)    {stocks} TimeFrame : {LatestWeekinDB} => {latest_update}")

                    else:

                        logging.info(f"{count} / {totallength} - EXIST(E)    {stocks}")
                        print(f"{count} / {totallength} - EXIST(E)    {stocks}")
                
                except Exception as e:
                    print(f"Exception {stocks}")
            else:
                
                try:
                    df_ALL = DB.GetStockHisEarn(stocks)    ## KIS 주가데이터                     

                    # 데이터프레임을 딕셔너리로 변환
                    df_ALL = df_ALL.reset_index()  
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)
                    
                    logging.info(f"{count} / {totallength} - NEW(E)    {stocks}")
                    print(f"{count} / {totallength} - NEW(E)    {stocks}")
                    
                except Exception as e:
                    logging.info(f"Exception {stocks}, {e}")

    def MakeMongoDB_US_O(self):
        
        # Define the timezone
        utc = pytz.timezone('UTC')  

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_O.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_O.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        self.str_database_name = CalDataBaseName(self.market, self.area, "O", "Stock")
        self.db = conn.get_database(self.str_database_name)
        totallength = len(self.StockList_US)
        ####################################      

        for count in range(len(self.StockList_US)):
            
            start_time = datetime.now(pytz.timezone('Asia/Seoul'))
            
            #time.sleep(1) # 1분에 75개 데이터만 허용
            stocks = self.StockList_US[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:
                logging.info(f"{count} / {totallength} - EXIST(O)    {stocks}")
                # MongoDB에 저장된 마지막 날짜 가져오기
                #try:
                #    last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                #    LatestWeekinDB = last_week_in_db_old.date()
#
                #    if self.latest_W > LatestWeekinDB:
#
                #        Series = Alpha.CallUsStockDetailedFdmt(stocks)                  
                #        data = Series.to_dict()
                #        
                #        # MongoDB에 데이터 삽입
                #        data['Date'] = datetime.combine(self.latest_W, dt_time.min)
                #        collection.insert_one(data)
#
                #        logging.info(f"{count} / {totallength} - UPDATE(O)    {stocks} TimeFrame : {LatestWeekinDB} => {self.latest_W}")
#
                #    else:
#
                #        logging.info(f"{count} / {totallength} - EXIST(O)    {stocks}")
                #
                #except Exception as e:
                #    print(f"Exception {stocks}")
            else:
                
                try:
                    mid_time = datetime.now(pytz.timezone('Asia/Seoul'))
                    
                    Series = Alpha.CallUsStockDetailedFdmt(stocks)                  
                    data = Series.to_dict()
                        
                    # MongoDB에 데이터 삽입
                    data['Date'] = datetime.combine(self.latest_W, dt_time.min)
                    collection.insert_one(data)
                    
                    end_time = datetime.now(pytz.timezone('Asia/Seoul'))
                    
                    work_time = end_time - start_time
                    
                    print(f"{count} / {totallength} - NEW(O)    {stocks} TIME : {work_time}")
                    logging.info(f"{count} / {totallength} - NEW(O)    {stocks}")
                    
                except Exception as e:
                    logging.info(f"Exception {stocks}, {e}")
                    
    def MakeMongoDB_US_Copy(self,p_code,Type):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetDataCopy_' + p_code + '.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetDataCopy_' + p_code + '.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        
        self.str_database_name = CalDataBaseName(self.market, self.area, p_code, Type)

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        # LOCAL DB 호출 #
        df, self.StockList_US = DB.ReadDataBase(self.StockList_US, self.market, self.area, self.str_database_name, self.start_day, self.end_day)
        
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_NAS")
        self.db = conn.get_database(self.str_database_name)

        totallength = len(self.StockList_US)
        if p_code == 'M':
            indexf = 'Datetime'
        else:
            indexf = 'Date'
        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]

            collection = self.db.get_collection(stocks)

            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:
                
                try:
                    # MongoDB에 저장된 마지막 날짜 가져오기
                    last_D_in_db_old = collection.find_one(sort=[(indexf, -1)])[indexf]
                    last_D_in_db_new = df[stocks].index[-1]

                    # MongoDB에 저장된 마지막 날짜 가져오기
                    first_D_in_db_old = collection.find_one(sort=[(indexf, 1)])[indexf]
                    first_D_in_db_new = df[stocks].index[0]

                    if last_D_in_db_new.date() > last_D_in_db_old.date():

                        logging.info(f"{count} / {totallength} - UPDATE({p_code})    {stocks} TimeFrame : {last_D_in_db_old.date()} => {last_D_in_db_new.date()}") 
                        
                        df[stocks] = df[stocks][df[stocks].index > last_D_in_db_old]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df[stocks].iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data[indexf] = date
                            collection.insert_one(data)
                    
                    elif 0:#first_D_in_db_new.date() < first_D_in_db_old.date():

                        ## 중복 인덱스 제거 ##
                        df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]

                        logging.info(f"{count} / {totallength} - UPDATE({p_code})    {stocks} TimeFrame : {first_D_in_db_old.date()} => {first_D_in_db_new.date()}") 

                        df[stocks] = df[stocks][df[stocks].index < first_D_in_db_old]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df[stocks].iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data[indexf] = date
                            collection.insert_one(data)

                    else:

                        logging.info(f"{count} / {totallength} - EXIST({p_code})    {stocks} TimeFrame : {last_D_in_db_new.date()}")

                except Exception as e:
                    print("Exception ", e)

            else:
                
                try:
                    ## 중복 인덱스 제거 ##
                    df[stocks] = df[stocks][~df[stocks].index.duplicated(keep='first')]

                    logging.info(f"{count} / {totallength} - NEW({p_code})    {stocks} TimeFrame : {df[stocks].index.min()} => {df[stocks].index.max()}")

                    # 데이터프레임을 딕셔너리로 변환
                    df[stocks] = df[stocks].reset_index()  
                    data_dict = df[stocks].to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)  

    ###### TEMPORARY FUNCTION #######
    
    def MakeMongoDB_US_M_DataBento(self, area, start_date, end_date):
    
        for i in range(0, len(self.StockList_US), 100):

            Bento.GetOhlcv1minZip(self.StockList_US[i:i + 100], area, start_date, end_date )
            print(i+500," / ",len(self.StockList_US), " DONE ")
            
    def MakeMongoDB_US_M_DBN(self, stocks, folder_path):

        # 해당 티커에 맞는 파일 패턴을 생성합니다
        pattern = f"xnas-itch-*.ohlcv-1m.{stocks}.dbn"
        full_pattern = os.path.join(folder_path, pattern)
        files = glob.glob(full_pattern)
        #print(f"찾은 파일들 ({stocks}): {files}")

        if not files:
            #print(f"{stocks}에 대한 파일을 찾을 수 없습니다.")
        
            return 0
    
        for dbn_file in files:
            #print(f"Processing file: {dbn_file}")
            # dbn 파일을 DataFrame으로 로드합니다
            data = DBNStore.from_file(path=dbn_file)
            df = data.to_df()
            df.reset_index(inplace=True)
            df.drop(columns=['rtype', 'publisher_id', 'instrument_id','symbol'], inplace=True)
            df.rename(columns={'ts_event': 'Datetime'}, inplace=True)
            df.set_index('Datetime', inplace=True)
    
            return df
                    
    def MakeMongoDB_US_M_DB_merge(self, area = 'AMX'):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            filename=MainPath +'/Logs/' + self.area + '/' + self.market + '/UsSysGetData_DB_Merge.log',
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        self.new_added_stocklist = list()

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        nas = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")    

        #// 데이터베이스 정보를 가져온다
        if area == 'NAS':
            str_database_name = 'NasDataBase_M'
            
        elif area == 'NYS':
            str_database_name = 'NysDataBase_M'           
            
        elif area == 'AMX':
            str_database_name = 'AmxDataBase_M'
            

        db_Ori = conn.get_database(str_database_name)
        db_NAS = nas.get_database(str_database_name)
        
        ####################################      

        totallength = len(self.StockList_US)

        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            
            collection_o = db_Ori.get_collection(stocks)

            if DB.ChkTableExist(str_database_name, stocks,'US') == True:
                
                try:
                    # 데이터베이스에서 데이터 가져오기                  
                    df_Ori = DB.ExecuteSql(str_database_name, stocks)
                    last_index = df_Ori.index[-1]

                    collection_m = db_NAS.get_collection(stocks)
                    data = list(collection_m.find())
                    df_Mrg = pd.DataFrame(data).set_index('Datetime')
                    df_Mrg = df_Mrg[df_Mrg.index > last_index]

                    # 타임존 확인 및 변환
                    if df_Ori.index.tzinfo is None:  # df_Ori의 타임존이 없는 경우
                        df_Ori.index = df_Ori.index.tz_localize('UTC')  # UTC로 로컬라이즈
                    elif df_Ori.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                        df_Ori.index = df_Ori.index.tz_convert('UTC')
                    df_Ori.drop(columns=['_id'], inplace=True, errors='ignore')  # '_id' 컬럼 제거
                    
                    if df_Mrg.index.tzinfo is None:  # df의 타임존이 없는 경우
                        df_Mrg.index = df_Mrg.index.tz_localize('UTC')  # UTC로 로컬라이즈
                    elif df_Mrg.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                        df_Mrg.index = df_Mrg.index.tz_convert('UTC')

                    # 데이터 정렬
                    df_Ori.index.name = 'Datetime'
                    df_Ori = df_Ori.sort_values(by="Datetime")
                    
                    df_ALL = pd.concat([df_Mrg, df_Ori])
                    df_ALL = df_ALL.loc[~df_ALL.index.duplicated(keep='first')]  # 중복 제거
                    df_ALL.drop(columns=['_id'], inplace=True, errors='ignore')  # '_id' 컬럼 제거
                    df_ALL.index.name = 'Datetime'

                    # 최종 정렬
                    df_ALL = df_ALL.sort_values(by="Datetime")
                                    
                    logging.info(f"{count} / {totallength} - UPDATE(M)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]}")                       
                    df_ALL = df_ALL.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    collection_o.drop()
                    
                    # MongoDB에 데이터 삽입
                    collection_o.insert_many(data_dict)      
                
                except Exception as e:
                    print("Exception ", e)
                    
            else:                

                try:
                    data = list(collection_m.find())
                    df_Mrg = pd.DataFrame(data).set_index('Datetime')
                    df_Mrg.drop(columns=['_id'], inplace=True)

                    if df_Mrg.index.tzinfo is None:  # df의 타임존이 없는 경우
                        df_Mrg.index = df_Mrg.index.tz_localize('UTC')  # UTC로 로컬라이즈
                    elif df_Mrg.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                        df_Mrg.index = df_Mrg.index.tz_convert('UTC')
                    
                    df_Mrg.index.name = 'Datetime'
                    
                    df_Mrg = df_Mrg.sort_values(by="Datetime")
                    
                    logging.info(f"{count} / {totallength} - NEW(M)    {stocks} TimeFrame : {df_Mrg.index[0]} => {df_Mrg.index[-1]}")      

                    df_Mrg = df_Mrg.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_Mrg.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection_o.insert_many(data_dict)

                    self.new_added_stocklist.append(stocks)

                except Exception as e:
                    print("Exception [ ", stocks, " ] ", e)
                            
        ## new added stock saved ##
        if self.market == 'NAS':
            file_path = MainPath + "json/NasAddedStockList.json"
        elif self.market == 'NYS':
            file_path = MainPath + "json/NysAddedStockList.json"
        elif self.market == 'AMX':
            file_path = MainPath + "json/AmxAddedStockList.json"

        with open(file_path, 'w') as outfile:
            json.dump(self.new_added_stocklist, outfile)
            
    def MakeMongoDB_US_M_ZIP(self, area = 'AMX'):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        #// 데이터베이스 정보를 가져온다
        if area == 'NAS':
            self.str_database_name = 'NasDataBase_M_Bento'
            folder_path1 = "E:/Databento/DataBento_2102_2107/NAS"
            folder_path2 = "E:/Databento/DataBento_2107_2112/NAS"
            folder_path3 = "E:/Databento/DataBento_2112_2205/NAS"
            folder_path4 = "E:/Databento/DataBento_2205_2210/NAS"
            folder_path5 = "E:/Databento/DataBento_2210_2303/NAS"
            folder_path6 = "E:/Databento/DataBento_2303_2308/NAS"
            folder_path7 = "E:/Databento/DataBento_2308_2401/NAS"
            
        elif area == 'NYS':
            self.str_database_name = 'NysDataBase_M_Bento'
            folder_path1 = "E:/Databento/DataBento_2102_2107/NYS"
            folder_path2 = "E:/Databento/DataBento_2107_2112/NYS"
            folder_path3 = "E:/Databento/DataBento_2112_2205/NYS"
            folder_path4 = "E:/Databento/DataBento_2205_2210/NYS"
            folder_path5 = "E:/Databento/DataBento_2210_2303/NYS"
            folder_path6 = "E:/Databento/DataBento_2303_2308/NYS"
            folder_path7 = "E:/Databento/DataBento_2308_2401/NYS"
            
        elif area == 'AMX':
            self.str_database_name = 'AmxDataBase_M_Bento'
            folder_path1 = "E:/Databento/DataBento_2102_2107/AMX"
            folder_path2 = "E:/Databento/DataBento_2107_2112/AMX"
            folder_path3 = "E:/Databento/DataBento_2112_2205/AMX"
            folder_path4 = "E:/Databento/DataBento_2205_2210/AMX"
            folder_path5 = "E:/Databento/DataBento_2210_2303/AMX"
            folder_path6 = "E:/Databento/DataBento_2303_2308/AMX"
            folder_path7 = "E:/Databento/DataBento_2308_2401/AMX"

        self.db = conn.get_database(self.str_database_name)
        
        ####################################      

        #for i in range(0, len(self.StockList_US), 200):
        #            
        #    KisUS.GetOhlcv1minZip(self.StockList_US[i:i + 200])
        #    print(i+200," / ",len(self.StockList_US), " DONE ")
        
        for count in range(len(self.StockList_US)):
    
            stocks = self.StockList_US[count]
            
            collection = self.db.get_collection(stocks)
            
            try:
                df1 = self.MakeMongoDB_US_M_DBN(stocks, folder_path1)
                df2 = self.MakeMongoDB_US_M_DBN(stocks, folder_path2)
                df3 = self.MakeMongoDB_US_M_DBN(stocks, folder_path3)
                df4 = self.MakeMongoDB_US_M_DBN(stocks, folder_path4)
                df5 = self.MakeMongoDB_US_M_DBN(stocks, folder_path5)
                df6 = self.MakeMongoDB_US_M_DBN(stocks, folder_path6)
                df7 = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)
                
                df = pd.concat([df1, df2])
                df = pd.concat([df, df3])
                df = pd.concat([df, df4])
                df = pd.concat([df, df5])
                df = pd.concat([df, df6])
                df = pd.concat([df, df7])
                
                
                df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거
            except:
                
                try:
                    df2 = self.MakeMongoDB_US_M_DBN(stocks, folder_path2)
                    df3 = self.MakeMongoDB_US_M_DBN(stocks, folder_path3)
                    df4 = self.MakeMongoDB_US_M_DBN(stocks, folder_path4)
                    df5 = self.MakeMongoDB_US_M_DBN(stocks, folder_path5)
                    df6 = self.MakeMongoDB_US_M_DBN(stocks, folder_path6)
                    df7 = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)
                
                    df = pd.concat([df2, df3])
                    df = pd.concat([df, df4])
                    df = pd.concat([df, df5])
                    df = pd.concat([df, df6])
                    df = pd.concat([df, df7])
                
                    df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거
                except:
                    try:
                        df3 = self.MakeMongoDB_US_M_DBN(stocks, folder_path3)
                        df4 = self.MakeMongoDB_US_M_DBN(stocks, folder_path4)
                        df5 = self.MakeMongoDB_US_M_DBN(stocks, folder_path5)
                        df6 = self.MakeMongoDB_US_M_DBN(stocks, folder_path6)
                        df7 = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)

                        df = pd.concat([df3, df4])
                        df = pd.concat([df, df5])
                        df = pd.concat([df, df6])
                        df = pd.concat([df, df7])

                        df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거

                    except:
                        try:
                            df4 = self.MakeMongoDB_US_M_DBN(stocks, folder_path4)
                            df5 = self.MakeMongoDB_US_M_DBN(stocks, folder_path5)
                            df6 = self.MakeMongoDB_US_M_DBN(stocks, folder_path6)
                            df7 = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)

                            df = pd.concat([df4, df5])
                            df = pd.concat([df, df6])
                            df = pd.concat([df, df7])

                            df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거   
                            

                        except:
                            try:

                                df5 = self.MakeMongoDB_US_M_DBN(stocks, folder_path5)
                                df6 = self.MakeMongoDB_US_M_DBN(stocks, folder_path6)
                                df7 = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)

                                df = pd.concat([df5, df6])
                                df = pd.concat([df, df7])

                                df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거

                            except:
                                try:

                                    df6 = self.MakeMongoDB_US_M_DBN(stocks, folder_path6)
                                    df7 = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)

                                    df = pd.concat([df6, df7])

                                    df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거                                                
                                        
                                except:
                                    try:

                                        df = self.MakeMongoDB_US_M_DBN(stocks, folder_path7)

                                        df = df.loc[~df.index.duplicated(keep='first')]  # 중복 제거
                                    except:
                                        print(f"{stocks}에 대한 파일을 찾을 수 없습니다.")
                                        continue  # 다음 티커로 넘어갑니다
            
            if DB.ChkTableExist(self.str_database_name, stocks,'US') == True:
                continue
                try:
                    # 데이터베이스에서 데이터 가져오기
                    df_Ori = DB.ExecuteSql(self.str_database_name, stocks)

                    # 타임존 확인 및 변환
                    if df_Ori.index.tzinfo is None:  # df_Ori의 타임존이 없는 경우
                        df_Ori.index = df_Ori.index.tz_localize('UTC')  # UTC로 로컬라이즈
                    elif df_Ori.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                        df_Ori.index = df_Ori.index.tz_convert('UTC')

                    if df.index.tzinfo is None:  # df의 타임존이 없는 경우
                        df.index = df.index.tz_localize('UTC')  # UTC로 로컬라이즈
                    elif df.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                        df.index = df.index.tz_convert('UTC')

                    # 데이터 정렬
                    df_Ori.index.name = 'Datetime'
                    df_Ori = df_Ori.sort_values(by="Datetime")
                    df = df.sort_values(by="Datetime")

                    # 데이터 병합
                    df_O = df_Ori[df_Ori.index >= '2024-01-01']
                    df_ALL = pd.concat([df, df_O])
                    df_ALL = df_ALL.loc[~df_ALL.index.duplicated(keep='first')]  # 중복 제거
                    df_ALL.drop(columns=['_id'], inplace=True, errors='ignore')  # '_id' 컬럼 제거
                    df_ALL.index.name = 'Datetime'

                    # 최종 정렬
                    df_ALL = df_ALL.sort_values(by="Datetime")
                                    
                    print(count,"/",len(self.StockList_US)," - UPDATE(M)    ",stocks, " TimeFrame : ",df_ALL.index[0] , " => " , df_ALL.index[-1])
                                           
                    df_ALL = df_ALL.reset_index()
                
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    collection.drop()
                    
                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)      
                        
                except Exception as e:
                    print("Exception ", e)

            else:
                
                try:
                    
                    if df.index.tzinfo is None:  # df의 타임존이 없는 경우
                        df.index = df.index.tz_localize('UTC')  # UTC로 로컬라이즈
                    elif df.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                        df.index = df.index.tz_convert('UTC')
                    
                    df.index.name = 'Datetime'
                    
                    df = df.sort_values(by="Datetime")
                    #df_ALL.drop(columns=['_id'], inplace=True)
                    print(count,"/",len(self.StockList_US)," - NEW(M)    ",stocks, " TimeFrame : ",df.index[0] , " => " , df.index[-1])

                    df = df.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception [ ", stocks, " ] ", e)

    def MakeMongoDB_US_M_ZIP_Temp(self, area = 'AMX'):
    
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        #// 데이터베이스 정보를 가져온다
        if area == 'NAS':
            self.str_database_name = 'NasDataBase_M'
        elif area == 'NYS':
            self.str_database_name = 'NysDataBase_M'
        elif area == 'AMX':
            self.str_database_name = 'AmxDataBase_M'

        self.db = conn.get_database(self.str_database_name)
        
        ####################################      

        for count in range(len(self.StockList_US)):
    
            stocks = self.StockList_US[count]
            
            collection = self.db.get_collection(stocks)
            
            if DB.ChkTableExist(self.str_database_name, stocks,'US') == True:
                    
                data = list(collection.find())
                df_Stock = pd.DataFrame(data)
                
                df_Stock.drop(columns=['_id'], inplace=True)
                df_Stock.set_index('Datetime', inplace=True)
                df_Stock = df_Stock.sort_values(by="Datetime")   
                df_Stock = df_Stock[~df_Stock.index.duplicated(keep='first')]
                if df_Stock.index.tzinfo is None:  # df_Ori의 타임존이 없는 경우
                    df_Stock.index = df_Stock.index.tz_localize('UTC')  # UTC로 로컬라이즈
                elif df_Stock.index.tzinfo != pytz.UTC:  # 다른 타임존인 경우 UTC로 변환
                    df_Stock.index = df_Stock.index.tz_convert('UTC')

                collection.drop()
                
                df_Stock = df_Stock.reset_index()
                collection.insert_many(df_Stock.to_dict("records"))
                print(count,"/",len(self.StockList_US)," - UPDATE(M)    ",stocks)

            else:
                pass
            
    ###### SUB FUNCTION #######
                            
    # 각 날짜별로 주가 종가 데이터를 기준으로 순위를 매기는 함수
    def rank_stocks(self, data):
        return data.rank(pct=True)

    def copyDatabase(self, OLD_DataBase_Name, NEW_DataBase_Name, OldDBDrop = False):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        #OLD_DataBase_Name = 'NasDataBase_M_Dump'
        #NEW_DataBase_Name = 'NasDataBase_M'        
        
        # 기존 데이터베이스와 새로운 데이터베이스
        old_db = conn[OLD_DataBase_Name]
        new_db = conn[NEW_DataBase_Name]
                
        for i in range(len(old_db.list_collection_names())):
            
            collection_name = old_db.list_collection_names()[i]
            
            print(f"{i} : {len(old_db.list_collection_names())} - {collection_name}")
            
            old_collection = old_db[collection_name]
            new_collection = new_db[collection_name]
            
            # 기존 컬렉션의 모든 문서를 새 컬렉션에 삽입
            for doc in old_collection.find():
                new_collection.insert_one(doc)

        # 복사가 완료되면 기존 데이터베이스 삭제 (필요 시)
        print(f"{len(old_db.list_collection_names())} : {len(new_db.list_collection_names())} - CHCK")
        print("Database copied successfully!")
        if OldDBDrop == True:
            conn.drop_database(OLD_DataBase_Name)

    def copyDatabaseFromNAS(self, DataBase_Name):

        #// 몽고클라이언트를 만든다
        conn1 = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        # 기존 데이터베이스와 새로운 데이터베이스
        old_db = conn1[DataBase_Name]

        #// 몽고클라이언트를 만든다
        conn2 = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        new_db = conn2[DataBase_Name]

        for i in range(len(old_db.list_collection_names())):
            
            collection_name = old_db.list_collection_names()[i]
            
            print(f"{i} : {len(old_db.list_collection_names())} - {collection_name}")
            
            old_collection = old_db[collection_name]
            new_collection = new_db[collection_name]
            
            # 기존 컬렉션의 모든 문서를 새 컬렉션에 삽입
            for doc in old_collection.find():
                new_collection.insert_one(doc)

        # 복사가 완료되면 기존 데이터베이스 삭제 (필요 시)
        print(f"{len(old_db.list_collection_names())} : {len(new_db.list_collection_names())} - CHCK")
        print("Database copied successfully!")

    def CalcAdDataframe(self, p_code, Universe):
        
        if p_code == "D":
            
            df = self.df_D

            for count in range(len(Universe)):
            
                stocks = Universe[count]

                renamed_stock = str(stocks)

                # 수정계수의 누적곱 계산 (현재부터 해당 날짜까지의 누적 수정계수)
                df[renamed_stock]['Cumadfac'] = df[renamed_stock]['adfac'][::-1].cumprod()[::-1]

                # 누적 수정계수의 이전 값(shift(1))을 사용하여 수정주가 계산
                df[renamed_stock]['ad_open'] = df[renamed_stock]['open'] * df[renamed_stock]['Cumadfac'].shift(-1, fill_value=1)
                df[renamed_stock]['ad_high'] = df[renamed_stock]['high'] * df[renamed_stock]['Cumadfac'].shift(-1, fill_value=1)
                df[renamed_stock]['ad_low'] = df[renamed_stock]['low'] * df[renamed_stock]['Cumadfac'].shift(-1, fill_value=1)
                df[renamed_stock]['ad_close'] = df[renamed_stock]['close'] * df[renamed_stock]['Cumadfac'].shift(-1, fill_value=1)

                # 불필요한 컬럼 제거
                df[renamed_stock].drop(columns=['open', 'high', 'low', 'close'], inplace=True)

                # 수정된 주가를 반올림
                df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']] = df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']].round(4)

            return df
            
        elif p_code == "W":
            
            df = self.df_W

            for count in range(len(self.StockList_US)):
            
                stocks = self.StockList_US[count]

                renamed_stock = str(stocks)

                # 수정계수의 누적곱 계산 (현재부터 해당 날짜까지의 누적 수정계수)
                df[renamed_stock]['Cumadfac'] = df[renamed_stock]['adfac'][::-1].cumprod()[::-1]

                # 누적 수정계수의 이전 값(shift(1))을 사용하여 수정주가 계산
                df[renamed_stock]['ad_open'] = df[renamed_stock]['open'] * df[renamed_stock]['Cumadfac']
                df[renamed_stock]['ad_high'] = df[renamed_stock]['high'] * df[renamed_stock]['Cumadfac']
                df[renamed_stock]['ad_low'] = df[renamed_stock]['low'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_close'] = df[renamed_stock]['close'] * df[renamed_stock]['Cumadfac'].shift(-1, fill_value=1)

                # 불필요한 컬럼 제거
                df[renamed_stock].drop(columns=['open', 'high', 'low', 'close'], inplace=True)

                # 수정된 주가를 반올림
                df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']] = df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']].round(4)

            return df
        else:
            raise ValueError("not defined p_code")   

    def CalcAdDataframe_Reverse(self, p_code):
        
        if p_code == "D":
                        
            df = self.df_AD
            
            for count in range(len(self.StockList_US)):
    
                renamed_stock = self.StockList_US[count]
                
                df[renamed_stock] = df[renamed_stock].reset_index()
                df[renamed_stock]['Date'] = pd.to_datetime(df[renamed_stock]['Date'])
                df[renamed_stock].set_index('Date', inplace=True)

                # split_factor가 0인 경우는 기업행위가 없으므로 1.0으로 설정
                #df[renamed_stock]['adfac'] = df[renamed_stock]['split_factor'].apply(lambda x: x if x != 0 else 1.0)
                df[renamed_stock]['adfac'] = df[renamed_stock]['split_factor'].apply(lambda x: 1/x if x != 0 else 1.0)
                
                # 날짜별 누적 분할 계수를 계산 (과거 데이터에도 분할 효과를 반영하기 위해 역순 누적곱)
                df[renamed_stock]['Cumadfac'] = df[renamed_stock]['adfac'][::-1].cumprod()[::-1]
                
                # 각 가격 항목에 대해 원 주가 계산: 원가 = 수정주가 * 누적 split factor
                price_columns = ['ad_open', 'ad_high', 'ad_low', 'ad_close']
                
                for col in price_columns:
                    df[renamed_stock][col + '_o'] = df[renamed_stock][col] / df[renamed_stock]['Cumadfac']

                df[renamed_stock].rename(columns={'ad_open_o': 'open', 'ad_high_o': 'high', 'ad_low_o': 'low', 'ad_close_o':'close','volume':'volume'}, inplace=True)
                df[renamed_stock][['open', 'high', 'low', 'close']] = df[renamed_stock][['open', 'high', 'low', 'close']].round(4)
                df[renamed_stock].drop(columns=['ad_open', 'ad_high', 'ad_low', 'ad_close'], inplace=True)
                
            return df
        elif p_code == "W":
            pass       

    def CalcAdDataframe_Reverse1(self, p_code):
        
        if p_code == "D":
                        
            df = self.df_AD
            
            for count in range(len(self.StockList_US)):
            
                renamed_stock = self.StockList_US[count]
                
                df[renamed_stock] = df[renamed_stock].reset_index()
                df[renamed_stock]['Date'] = pd.to_datetime(df[renamed_stock]['Date'])
                df[renamed_stock].set_index('Date', inplace=True)
    
                # 기존 split_factor 값을 이용해 새로운 split_factor 값을 생성
                # 만약 원래 값이 0이면 기업행위가 없으므로 1.0, 아니면 1/x (예: 2이면 0.5)
                df[renamed_stock]['adfac'] = df[renamed_stock]['split_factor'].apply(lambda x: 1/x if x != 0 else 1.0)
                # 기존 split_factor 컬럼 삭제
    
                # 날짜별 누적 분할 계수를 계산 (역순 누적곱)
                df[renamed_stock]['Cumadfac'] = df[renamed_stock]['split_factor'][::-1].cumprod()[::-1]
    
                # 배당 보정 및 분할 보정을 적용하여 원 주가 복원
                # 원가 = 수정주가 / (1 - dividend_factor) * 누적 split factor
                price_columns = ['ad_open', 'ad_high', 'ad_low', 'ad_close']
                for col in price_columns:
                    df[renamed_stock][col + '_o'] = df[renamed_stock][col] / (1 - df[renamed_stock]['dividend_factor']) * df[renamed_stock]['Cumadfac']
    
                df[renamed_stock].rename(
                    columns={
                        'ad_open_o': 'open', 
                        'ad_high_o': 'high', 
                        'ad_low_o': 'low', 
                        'ad_close_o': 'close',
                        'volume': 'volume'
                    },
                    inplace=True
                )
                df[renamed_stock][['open', 'high', 'low', 'close']] = df[renamed_stock][['open', 'high', 'low', 'close']].round(4)
            
            return df
        elif p_code == "W":
            pass

    def calculate_and_add_group_rs(self, stock_data_dict: dict) -> dict:
        """
        티커별 데이터프레임이 담긴 딕셔너리를 받아,
        날짜별 Sector/Industry 평균 RS를 계산하고 각 데이터프레임에 추가합니다.

        :param stock_data_dict: {'티커': DataFrame, ...} 형태의 딕셔너리
        :return: 그룹 평균 RS 컬럼이 추가된 새로운 딕셔너리
        """
        
        # 1. 데이터 통합: 모든 데이터프레임을 하나로 합치기
        all_dfs = []
        for symbol, df in stock_data_dict.items():
            # 인덱스(Date)를 컬럼으로 변환하고, Symbol 컬럼 추가
            temp_df = df.reset_index()
            temp_df['Symbol'] = symbol
            all_dfs.append(temp_df)

        # 리스트에 담긴 모든 데이터프레임을 하나로 합침
        if not all_dfs:
            print("입력 데이터가 비어 있습니다.")
            return {}
            
        df_all = pd.concat(all_dfs, ignore_index=True)
        print("모든 주식 데이터 통합 완료.")

        # 2. 그룹 평균 계산
        print("날짜별 섹터 및 산업 평균 RS 계산 중...")
        
        # 계산할 RS 컬럼 목록
        rs_columns = ['RS_4W', 'RS_12W']

        for rs_col in rs_columns:
            # 섹터 평균 RS 계산
            sector_avg_col = f'Sector_{rs_col}'
            df_all[sector_avg_col] = df_all.groupby(['Date', 'Sector'])[rs_col].transform('mean').round(2)
            
            # 산업 평균 RS 계산
            industry_avg_col = f'Industry_{rs_col}'
            df_all[industry_avg_col] = df_all.groupby(['Date', 'Industry'])[rs_col].transform('mean').round(2)
            
        print("그룹 평균 계산 완료.")

        # 3. 결과 재분배: 다시 티커별 딕셔너리 형태로 변환
        result_dict = {}
        df_all.set_index('Date', inplace=True) # Date를 다시 인덱스로 설정
        
        for symbol in df_all['Symbol'].unique():
            # 각 티커에 해당하는 데이터만 필터링하고, 불필요한 Symbol 컬럼은 제거
            result_dict[symbol] = df_all[df_all['Symbol'] == symbol].drop(columns='Symbol')
            
        print("결과를 티커별 딕셔너리로 재분배 완료.")
        
        return result_dict
    
    def MakeMongoDB_US_Sector(self):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        if self.market != 'NA':
            filename = MainPath +'/Logs/' + self.area + '/' + self.market + '/' + self.market + 'SysGetData_RS.log'
        else:
            filename = MainPath +'/Logs/' + self.area + '/' + self.area + 'SysGetData_RS.log'
            
        logging.basicConfig(
            filename=filename,
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        Empty_Stocks = 0
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")

        totallength = len(self.StockList_US)
        
        ####################################        
        
        for count in range(len(self.StockList_US)):

            stocks = self.StockList_US[count]
            
            try:
                api_key = self.stock_info["FINNHUB_API_KEY"]
                finnhub_client = finnhub.Client(api_key=api_key)
                output = finnhub_client.company_profile2(symbol=stocks)

                print(f"{count} / {totallength} - NEW(SECT)    {stocks} - Sector : {output['finnhubIndustry']}")                     
                
            except Exception as e:
                Empty_Stocks = Empty_Stocks + 1

        logging.info(" ## Start Sector RS Calculate by datetime ... ## ")