import traceback
import pymongo
from Path import MainPath
import Helper.KIS.KIS_Common as Common 
import json
import pandas as pd
from DataBase.CalMongoDB import MongoDB
from datetime import datetime, timedelta
import Helper.KIS.KIS_API_Helper_KR as KisKR
import Helper.LS.LS_API_Helper_KR as LsKr
from Helper.KIS.KIS_Make_StockList import GetStockList
import yaml
import pprint
import pytz

from pymongo import InsertOne, errors
import logging
from multiprocessing import Pool
from DataBase.CalDBName import CalFilePath
class ColMongoDB:

    def __init__(self):

        with open(MainPath + 'myStockInfo.yaml', encoding='UTF-8') as f:
            self.stock_info = yaml.load(f, Loader=yaml.FullLoader)

        #Common.SetChangeMode("VIRTUAL1")
 
        self.end_day = datetime.now()
        self.start_day = (datetime.now() - timedelta(days=365*30))#.strftime('%Y-%m-%d')
        
        GetStockList(area = 'KR', market = "NA")

        self.List_file_path, self.Delist_file_path = CalFilePath("NA", 'KR', 'Stock')
                      
        with open(self.List_file_path, 'r') as json_file:
            KoreaStockList = json.load(json_file)
        
        try:
            with open(self.Delist_file_path, 'r') as json_file:
                self.delete_stocklist = json.load(json_file) 
        # b에 있는 요소를 a에서 삭제
            self.StockList_KR = [item for item in KoreaStockList if item not in self.delete_stocklist]

        except:
            self.StockList_KR = KoreaStockList
            self.delete_stocklist = list()

        df_Test = KisKR.GetOhlcv('005930',"D",(self.end_day - timedelta(days=10)),self.end_day,adVar=0)
        df_Test.index = pd.to_datetime(df_Test.index)
        self.latest_D = df_Test.index[-1].date() # datetime
        
        df_M = KisKR.GetOhlcv('005930',"M",(self.end_day - timedelta(days=100)),self.end_day,adVar=0)
        df_M.index = pd.to_datetime(df_M.index)
        self.latest_M = df_M.index[-1] # datetime
       
    ######################################################################
    def MakeMongoDB_KR_M(self):
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 로깅 설정
        logging.basicConfig(
            filename=MainPath +'/Logs/KR/KrSysGetData_M.log',
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )    

        # Define the timezone
        kst = pytz.timezone('Asia/Seoul')  

        # Get the current time in KST
        Initial_time = datetime.now(kst)
        
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],
                                   maxIdleTimeMS=120000,
                                   serverSelectionTimeoutMS=30000)
        
        DB = MongoDB(DB_addres = "MONGODB_NAS")

        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_M'

        self.db = conn.get_database(self.str_database_name)
        totallength = len(self.StockList_KR)

        for count in range(len(self.StockList_KR)):
            
            stocks = str(self.StockList_KR[count])
            renamed_stock = "A"+str(stocks)

            if DB.ChkTableExist(self.str_database_name, stocks,'KR') == True:
                # 인덱스 생성 (한 번만 수행)
             
                collection = self.db.get_collection(renamed_stock)
                
                # MongoDB에 저장된 마지막 날짜 가져오기
                try:

                    latest_in_db = collection.find_one(sort=[('Datetime', -1)])['Datetime']                   
                    LatestDateinDB = latest_in_db.date()

                    if self.latest_D > LatestDateinDB:

                        df_ALL = LsKr.GetLsOhlcvMin(stocks, LatestDateinDB, self.latest_D, period=1)
                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Datetime'] = date
                            collection.insert_one(data)

                        logging.info(f"{count} / {totallength} - UPDATE(M)    {stocks} TimeFrame : {LatestDateinDB} => {self.latest_D}")
                    
                    else:

                        logging.info(f"{count} / {totallength} - EXIST(M)    {stocks}")
                
                except Exception as e:
                    logging.info(f"Exception {stocks} - {e}")
                    self.delete_stocklist.append(stocks)  

            else:
                
                try:

                    df_ALL = LsKr.GetLsOhlcvMin(stocks, self.end_day - timedelta(days=300), self.end_day, period=1)
                    
                    df_ALL = df_ALL.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)
                    
                    logging.info(f"{count} / {totallength} - NEW(M)    {stocks}")

                except Exception as e:
                    logging.info(f"Exception {stocks} - {e}")

        # Define the timezone
        kst = pytz.timezone('Asia/Seoul')  

        # Get the current time in KST
        end_time = datetime.now(kst)
        taking_time = end_time - Initial_time
        logging.info(f"Get US Data Gettering Finished.. Total time : {taking_time}")
            
    ######################################################################
    def MakeMongoDB_KR_M_(self):
        
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 로깅 설정
        logging.basicConfig(
            filename=MainPath +'/Logs/KR/KrSysGetData_M.log',
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )    
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        DB = MongoDB(DB_addres = "MONGODB_NAS")

        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_M'
        self.db = conn.get_database(self.str_database_name)

        totallength = len(self.StockList_KR)

        # 인덱스 생성 (한 번만 수행)
        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]
            renamed_stock = "A"+str(stocks)
            
            #collection.create_index([('Datetime', pymongo.DESCENDING)])
            #print(f"indexing .. {renamed_stock}")
            #print(f"{count} / {totallength} - indexing (M) - {stocks}")
           
            if DB.ChkTableExist(self.str_database_name, stocks, 'KR'):
                
                try:
                    collection = self.db.get_collection(renamed_stock)
                    latest_in_db_doc = collection.find_one(sort=[('Datetime', -1)])
                    LatestDateinDB = latest_in_db_doc['Datetime'].date()

                    if self.latest_D > LatestDateinDB:
                    
                        df_ALL = LsKr.GetLsOhlcvMin(stocks, LatestDateinDB, self.latest_D, period=1)

                        if not df_ALL.empty:
                            for date, row in df_ALL.iterrows():

                                data = row.to_dict()
                                data['Datetime'] = date
                                collection.insert_one(data)
                        else:
                            logging.info(f"No new data for {stocks}")
                            print(f"No new data for {stocks}")
                        
                        logging.info(f"UPDATE(M) {stocks} TimeFrame: {df_ALL['Datetime'].iloc[0]} => {df_ALL['Datetime'].iloc[-1]} ")
                        print(f"UPDATE(M) {stocks} TimeFrame: {df_ALL['Datetime'].iloc[0]} => {df_ALL['Datetime'].iloc[-1]} ")
                    else:
                        logging.info(f"{count} / {totallength} - EXIST (M) {stocks} : {KisKR.GetStockName(stocks)} ")
                        print(f"{count} / {totallength} - EXIST (M) {stocks} : {KisKR.GetStockName(stocks)} ")
                
                except Exception as e:
                    logging.error(f"Exception while updating {stocks}: {e}")
                    print(f"Exception while updating {stocks}: {e}")
            else:
                try:
                    
                    df_ALL = LsKr.GetLsOhlcvMin(stocks, self.end_day - timedelta(days=300), self.end_day, period=1)
                    logging.info(f"{count} / {totallength} - NEW(M)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]} ")
                    print(f"{count} / {totallength} - NEW(M)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]} ")

                    if not df_ALL.empty:
                        df_ALL.reset_index(inplace=True)
                        data_list = df_ALL.to_dict('records')
                        collection.insert_many(data_list)
                    else:
                        logging.info(f"No data for {stocks}")
                        print(f"No data for {stocks}")

                except Exception as e:
                    logging.error(f"Exception while inserting new {stocks}: {e}")
                    self.delete_stocklist.append(stocks)

        # 멀티프로세싱 적용
        #with Pool(processes=4) as pool:
        #    pool.map(process_stock, self.StockList_KR)

    def MakeMongoDB_KR_M_temp(self):

        logging.basicConfig(filename='/app/SourceCode/Logs/KrSysGetData.log', level=logging.INFO)

        # Define the timezone
        kst = pytz.timezone('Asia/Seoul')  
    
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_M'
        self.db = conn.get_database(self.str_database_name)
        templist = ['278470', '443060', '462870', '475150', '481850', '487570', '489790', '068100', '088340', '105760', '126730', '140430',
                    '145170', '160190', '199430', '199480', '199550', '209640', '289930', '295310', '308430', '336680', '062040', '347850',
                    '351870', '360350', '362990', '373110', '381620', '389500', '389650', '412540', '415380', '418620', '420570', '431190',
                    '437730', '440290', '443670', '450330', '452200', '376270', '452430', '453450', '455900', '456010', '456070', '457370',
                    '457550','458650','458870','460470','460930','460940','461030','461300','462350','462510','464080','464280','464500',
                    '465480','466100','468760','469480','469750','469900','471050','472220','472230','472850','473000','473050','473370',
                    '473950','474170','474490','474660','474930','475240','475250','475400','475580','476080','476470','477340','477380',
                    '477470','477530','477760','478110','478390','478440','478780','479880','481890','482520','482680','486630','488060']
        totallength = len(self.StockList_KR)
        self.StockList_KR = templist
        database_name = 'KrDataBase_D'
        database = conn.get_database(database_name)
        ####################################      
        
        for count in range(len(self.StockList_KR)):

            # Get the current time in KST
            start_time = datetime.now(kst)
            stocks = self.StockList_KR[count]

            renamed_stock = "A"+str(stocks)
            collection = self.db.get_collection(renamed_stock)
            databasecollection = database.get_collection(renamed_stock)

            collection.create_index([('Datetime', pymongo.DESCENDING)])

            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                #try:
                #    latest_in_db = collection.find_one(sort=[('Datetime', -1)])['Datetime']
                #except:
                latest_in_db = databasecollection.find_one(sort=[('Date', 1)])['Date']
                LatestDateinDB = latest_in_db.date()
                print(LatestDateinDB)
                if 0:#self.latest_D > LatestDateinDB:

                    try:
                        #df_ALL = LsKr.GetLsOhlcvMin(stocks,(LatestDateinDB - timedelta(days=1)),self.latest_D,period=1)
                        df_ALL = LsKr.GetLsOhlcvMin(stocks,LatestDateinDB,self.latest_D,period=1)
                        # Get the current time in KST
                        api_end_time = datetime.now(kst)
                        API_time_takes = (api_end_time - start_time).total_seconds()

                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Datetime'] = date
                            collection.insert_one(data)

                        # Get the current time in KST
                        db_end_time = datetime.now(kst) 
                        DB_time_takes = (db_end_time - api_end_time).total_seconds()

                        print(f"{count} / {totallength} - UPDATE(M)    {stocks} TimeFrame : {df_ALL.index[0]} => {df_ALL.index[-1]}  Time Takes ( API : {API_time_takes} / DB write : {DB_time_takes})")

                    except Exception as e:
                        print("Exception ", e)
                
                elif stocks in templist:
                    
                    if 1:#try:
                        print(count,"/",len(self.StockList_KR)," - NEW (M) ",stocks," : ",KisKR.GetStockName(stocks))
                        
                        df_ALL = LsKr.GetLsOhlcvMin(stocks,LatestDateinDB, self.end_day,period=1)
                        df_ALL = df_ALL.reset_index()

                        # 데이터프레임을 딕셔너리로 변환
                        data_dict = df_ALL.to_dict("records")

                        # MongoDB에 데이터 삽입
                        collection.insert_many(data_dict)

                    else:#except Exception as e:
                        print("Exception ", e)
                else:
                    print(f"{count} / {totallength} - EXIST (M) {stocks} : {KisKR.GetStockName(stocks)} ")


            else:
                
                try:
                    print(count,"/",len(self.StockList_KR)," - NEW (M) ",stocks," : ",KisKR.GetStockName(stocks))

                    df_ALL = LsKr.GetLsOhlcvMin(stocks,self.end_day - timedelta(days=300), self.end_day,period=1)
                    df_ALL = df_ALL.reset_index()

                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)
                    self.delete_stocklist.append(stocks)

        #파일 경로입니다.
        file_path = MainPath + "json/KrDeleteStockList.json"
        
        #with open(file_path, 'w') as outfile:
        #    json.dump(self.delete_stocklist, outfile)
        
    def MakeMongoDB_KR_AD(self):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_AD'
        self.db = conn.get_database(self.str_database_name)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        str_database_name_D = 'KrDataBase_D'
        self.df_D, self.StockList_KR = DB.ReadDataBase(self.StockList_KR, 'ALL', 'KR', str_database_name_D, self.start_day, self.end_day)

        self.df_AD = self.CalcAdDataframe("D")
        df =  self.df_AD
        
        
        ####################################      

        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]

            renamed_stock = "A"+str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_date_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_date_in_db_new =  df[renamed_stock].index[-1]
                
                if last_date_in_db_new > last_date_in_db_old:

                    try:
                        print(count,"/",len(self.StockList_KR)," - UPDATE (AD) ",stocks," : "," ( ",last_date_in_db_old.date()," > ",last_date_in_db_new.date(), " )")
                        # MongoDB에 없는 데이터만 필터링
                        df[renamed_stock] = df[renamed_stock][df[renamed_stock].index > last_date_in_db_old]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df[renamed_stock].iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    except Exception as e:
                        print("Exception ", e)

                else:
                    print(count,"/",len(self.StockList_KR)," - EXIST (AD) ",stocks,  last_date_in_db_new.date() , last_date_in_db_old.date())


            else:
                
                try:
                    ## 중복 인덱스 제거 ##
                    df[renamed_stock] = df[renamed_stock][~df[renamed_stock].index.duplicated(keep='first')]
                    print(count,"/",len(self.StockList_KR)," - NEW (AD)  ",stocks, df[renamed_stock].index.min(), " > ", df[renamed_stock].index.max())                         

                    # 데이터프레임을 딕셔너리로 변환
                    df[renamed_stock] = df[renamed_stock].reset_index()  
                    data_dict = df[renamed_stock].to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)

    def MakeMongoDB_KR_D(self,ohlcv = 'N'):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 로깅 설정
        logging.basicConfig(
            filename=MainPath +'/Logs/KR/KrSysGetData_D.log',
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )    
        
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        #// 데이터베이스 정보를 가져온다
        if ohlcv == 'N':
            self.str_database_name = 'KrDataBase_D'
        else:
            self.str_database_name = 'KrDataBase_D_ohlcv'
            
        self.db = conn.get_database(self.str_database_name)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        totallength = len(self.StockList_KR)
        
        ####################################      

        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]

            renamed_stock = "A"+str(stocks)
            collection = self.db.get_collection(renamed_stock)
            #collection.create_index([('Date', pymongo.DESCENDING)])

            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                try:
                    # MongoDB에 저장된 마지막 날짜 가져오기
                    last_date_in_db = collection.find_one(sort=[('Date', -1)])['Date']
                    LatestDateinDB = last_date_in_db.date()

                    if self.latest_D > LatestDateinDB:
                    
                        df_ALL = DB.GetStockHis(stocks, 'D', last_date_in_db, self.end_day, 'KR', ohlcv)       ## KIS 주가데이터        
                        
                        df_ALL['adfac'] = 1 + (df_ALL['divfac'] / 100)                       
                        df_ALL.drop(columns=['divfac'], inplace=True)

                        # MongoDB에 없는 데이터만 필터링
                        df_ALL = df_ALL[df_ALL.index > last_date_in_db]

                        logging.info(f"UPDATE(D) {stocks} TimeFrame: {LatestDateinDB} => {df_ALL.index[-1]} ")

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)
                            
                    else:
                        
                        logging.info(f"{count} / {totallength} - EXIST(D)    {stocks}")
                        
                except Exception as e:
                    logging.info(f"Exception {stocks} - {e}")
                    self.delete_stocklist.append(stocks)
            else:
            
                try:
                    df_ALL = DB.GetStockHis(stocks,'D', self.start_day, self.end_day, 'KR', ohlcv)

                    df_ALL['adfac'] = 1 + (df_ALL['divfac'] / 100)                       
                    df_ALL.drop(columns=['divfac'], inplace=True)
                                                                                       
                    df_ALL = df_ALL.reset_index()

                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)
                    
                    logging.info(f"{count} / {totallength} - NEW(D)    {stocks}")

                except Exception as e:
                    logging.info(f"Exception {stocks} - {e}")
                    self.delete_stocklist.append(stocks)

        with open(self.Delist_file_path, 'w') as outfile:
            json.dump(self.delete_stocklist, outfile)

    def MakeMongoDB_KR_F(self):

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 로깅 설정
        logging.basicConfig(
            filename=MainPath +'/Logs/KR/KrSysGetData_F.log',
            filemode='w',  # 덮어쓰기로 설정
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )    

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_F'
        self.db = conn.get_database(self.str_database_name)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        totallength = len(self.StockList_KR)

        ####################################      

        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]

            renamed_stock = "A"+str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_datetime_in_db = collection.find_one(sort=[('Date', -1)])['Date']
                last_date_in_db = last_datetime_in_db.date()
                
                if self.latest_D > last_date_in_db:

                    try:

                        df_ALL = DB.GetStockHisKRX(stocks, last_date_in_db, self.end_day)    ## KRX 주가데이터
                        
                        # MongoDB에 없는 데이터만 필터링
                        df_ALL = df_ALL[df_ALL.index > last_datetime_in_db]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                        logging.info(f"{count} / {totallength} - UPDATE(F)    {stocks} TimeFrame : {last_datetime_in_db} => {self.latest_D}")

                    except Exception as e:
                        logging.info(f"Exception {stocks} - {e}")
                else:
                    logging.info(f"{count} / {totallength} - EXIST(F)    {stocks}")

            else:
            
                try:
                    df_ALL = DB.GetStockHisKRX(stocks, self.start_day, self.end_day)    ## KRX 주가데이터
                    df_ALL = df_ALL.reset_index()

                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                    logging.info(f"{count} / {totallength} - NEW(F)    {stocks}")

                except Exception as e:

                    logging.info(f"Exception {stocks} - {e}")

        #파일 경로입니다.
        file_path = MainPath + "json/KrDeleteStockList.json"
        
        with open(file_path, 'w') as outfile:
            json.dump(self.delete_stocklist, outfile)

    def MakeMongoDB_KR_AW(self):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_AW'
        self.db = conn.get_database(self.str_database_name)
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        str_database_name_D = 'KrDataBase_W'
        self.df_W, self.StockList_KR = DB.ReadDataBase(self.StockList_KR, 'ALL', 'KR', str_database_name_D, self.start_day, self.end_day)
        
        self.df_AW = self.CalcAdDataframe("W")
        df =  self.df_AW

        ####################################      

        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]

            renamed_stock = "A"+str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_week_in_db_new =  df[renamed_stock].index[-1]
                
                if last_week_in_db_new > last_week_in_db_old:

                    try:
                        print(count,"/",len(self.StockList_KR)," - UPDATE(AW) ",stocks," : "," ( ",last_week_in_db_old.date()," > ",last_week_in_db_new.date(), " )")
                        # MongoDB에 없는 데이터만 필터링
                        df[renamed_stock] = df[renamed_stock][df[renamed_stock].index > last_week_in_db_old]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df[renamed_stock].iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    except Exception as e:
                        print("Exception ", e)

                else:
                    print(count,"/",len(self.StockList_KR)," - EXIST(AW)  ",stocks,  last_week_in_db_new.date() , last_week_in_db_old.date())


            else:
                
                try:
                    ## 중복 인덱스 제거 ##
                    df[renamed_stock] = df[renamed_stock][~df[renamed_stock].index.duplicated(keep='first')]
                    print(count,"/",len(self.StockList_KR)," - NEW(AW)   ",stocks, df[renamed_stock].index.min(), " > ", df[renamed_stock].index.max())                         

                    # 데이터프레임을 딕셔너리로 변환
                    df[renamed_stock] = df[renamed_stock].reset_index()  
                    data_dict = df[renamed_stock].to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)

    def MakeMongoDB_KR_W(self):
    
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_W'
        self.db = conn.get_database(self.str_database_name)
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        totallength = len(self.StockList_KR)
        
        str_database_name_D = 'KrDataBase_D'
        df_D_Temp, self.StockList_KR = DB.ReadDataBase(self.StockList_KR, 'ALL', 'KR', str_database_name_D, self.start_day, self.end_day)
        
        # 빈 dict 생성
        df = {}
                
        # 주봉 데이터 생성
        for key, df_temp in df_D_Temp.items():
            
            last_valid_date = df_temp.index.max()
            
            # 주간 단위로 resample
            df_resampled = df_temp.resample(rule='W-FRI')

            # 시가: 그 주의 첫 번째 거래일(보통 월요일) 시가
            open_price = df_resampled.first()['open']
    
            # 고가: 그 주의 가장 높은 가격
            high_price = df_resampled.max()['high']
    
            # 저가: 그 주의 가장 낮은 가격
            low_price = df_resampled.min()['low']
    
            # 종가: 그 주의 마지막 거래일(보통 금요일) 종가
            close_price = df_resampled.last()['close']
            
            volume = df_resampled.sum()['volume']
            
            adfact = df_resampled['adfac'].apply(lambda x: x.prod())
            
            # 주봉 데이터프레임 생성
            df[key] = pd.DataFrame({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'adfac': adfact
            })
            
            df[key] = df[key][df[key].index <= last_valid_date]
            df[key] = df[key][~df[key].index.duplicated(keep='first')]
            
        self.df_W = df
        
        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]

            renamed_stock = "A"+str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_week_in_db_new = df[renamed_stock].index[-1]
                if last_week_in_db_new > last_week_in_db_old:

                    try:
                        print(count,"/",len(self.StockList_KR)," - UPDATE (W) ",stocks," : "," ( ",last_week_in_db_old.date()," > ",last_week_in_db_new.date(), " )")
                        # MongoDB에 없는 데이터만 필터링
                        df[renamed_stock] = df[renamed_stock][df[renamed_stock].index > last_week_in_db_old]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df[renamed_stock].iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    except Exception as e:
                        print("Exception ", e)

                else:
                    print(count,"/",len(self.StockList_KR)," - EXIST (W) ",stocks,  last_week_in_db_new.date() , last_week_in_db_old.date())


            else:
                
                try:
                    ## 중복 인덱스 제거 ##
                    df[renamed_stock] = df[renamed_stock][~df[renamed_stock].index.duplicated(keep='first')]
                    print(count,"/",len(self.StockList_KR)," - NEW (W)   ",stocks, df[renamed_stock].index.min(), " > ", df[renamed_stock].index.max())                         

                    # 데이터프레임을 딕셔너리로 변환
                    df[renamed_stock] = df[renamed_stock].reset_index()  
                    data_dict = df[renamed_stock].to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)
        
    def CalcAdDataframe(self, p_code):
        
        if p_code == "D":
            
            df = self.df_D

            for count in range(len(self.StockList_KR)):
            
                stocks = self.StockList_KR[count]

                renamed_stock = "A"+str(stocks)

                # 수정계수의 누적곱 계산 (현재부터 해당 날짜까지의 누적 수정계수)
                df[renamed_stock]['Cumadfac'] = df[renamed_stock]['adfac'][::-1].cumprod()[::-1]

                # 누적 수정계수의 이전 값(shift(1))을 사용하여 수정주가 계산
                df[renamed_stock]['ad_open'] = df[renamed_stock]['open'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_high'] = df[renamed_stock]['high'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_low'] = df[renamed_stock]['low'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_close'] = df[renamed_stock]['close'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)

                # 불필요한 컬럼 제거
                df[renamed_stock].drop(columns=['open', 'high', 'low', 'close'], inplace=True)

                # 수정된 주가를 반올림
                df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']] = df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']].round(0)

            return df
            
        elif p_code == "W":
            
            df = self.df_W

            for count in range(len(self.StockList_KR)):
            
                stocks = self.StockList_KR[count]

                renamed_stock = "A"+str(stocks)

                # 수정계수의 누적곱 계산 (현재부터 해당 날짜까지의 누적 수정계수)
                df[renamed_stock]['Cumadfac'] = df[renamed_stock]['adfac'][::-1].cumprod()[::-1]

                # 누적 수정계수의 이전 값(shift(1))을 사용하여 수정주가 계산
                df[renamed_stock]['ad_open'] = df[renamed_stock]['open'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_high'] = df[renamed_stock]['high'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_low'] = df[renamed_stock]['low'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)
                df[renamed_stock]['ad_close'] = df[renamed_stock]['close'] * df[renamed_stock]['Cumadfac'].shift(1, fill_value=1)

                # 불필요한 컬럼 제거
                df[renamed_stock].drop(columns=['open', 'high', 'low', 'close'], inplace=True)

                # 수정된 주가를 반올림
                df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']] = df[renamed_stock][['ad_open', 'ad_high', 'ad_low', 'ad_close']].round(0)
            return df
        else:
            raise ValueError("not defined p_code")   

    def MakeRSData_KR_Sub(self):

        df_ALL_20D = pd.DataFrame()
        df_ALL_120D = pd.DataFrame()

        for count in range(len(self.StockList_KR)):
            
            try:
                stocks = self.StockList_KR[count]
                renamed_stock = "A"+str(stocks)
                
                df = self.df_AW[renamed_stock]
                df_RS = df['ad_close']
                df_RS.name = stocks

                df_RS_20D = (df_RS - df_RS.shift(20)) / df_RS.shift(20) * 100
                df_RS_120D = (df_RS - df_RS.shift(60)) / df_RS.shift(60) * 100
 
                if count == 0:

                    df_ALL_20D = df_RS_20D 
                    df_ALL_120D = df_RS_120D 

                else:

                    df_ALL_20D = pd.concat([df_ALL_20D,df_RS_20D], axis=1)
                    df_ALL_120D = pd.concat([df_ALL_120D,df_RS_120D], axis=1)
                
            except:
                pass

        # 각 날짜별로 순위를 매기고, 결과를 원래 데이터 위치에 씌우기
        ranked_df_4W = df_ALL_20D.apply(self.rank_stocks, axis=0)
        ranked_df_4W = (ranked_df_4W*100).round(2)
        
        ranked_df_52W = df_ALL_120D.apply(self.rank_stocks, axis=0)
        ranked_df_52W = (ranked_df_52W*100).round(2)   
                
        return ranked_df_4W, ranked_df_52W

    def MakeMongoDB_KR_Sort_Sector(self, df, type = '업종소', length = 4):

        df_RS_Ranked = df.reset_index()
        
        # 섹터 정보를 로드합니다.
        quant_data = pd.read_excel(MainPath + 'Excel/QuantData.xlsx', usecols=['코드',type])
        quant_data['Ticker'] = quant_data['코드'].str.replace('A', '').astype(str).str.strip()

        # 티커를 섹터로 매핑합니다.
        ticker_to_sector = quant_data.set_index('Ticker')[type].to_dict()

        # DataFrame을 긴 형식으로 변환합니다.
        sector_data = df_RS_Ranked.melt(id_vars=['Date'], var_name='Ticker', value_name='RS')
        sector_data['Ticker'] = sector_data['Ticker'].str.replace('A', '')
        sector_data['Sector'] = sector_data['Ticker'].map(ticker_to_sector)

        # 각 날짜별로 섹터의 평균 RS 값을 계산합니다. (None 값을 무시하고 계산)
        average_rs_by_sector = sector_data.groupby(['Date', 'Sector'])['RS'].mean().reset_index()

        # 각 날짜별로 섹터를 컬럼으로 하는 데이터 프레임 생성
        pivot_table_temp = average_rs_by_sector.pivot(index='Date', columns='Sector', values='RS')
        
        pivot_table = pivot_table_temp.apply(self.rank_stocks, axis=0)
        pivot_table = (pivot_table*100).round(2)
        pivot_table = pivot_table.dropna()
        # 마지막 날짜에서 RS 값이 높은 순서대로 정렬
        last_date = pivot_table.index.max()
        sorted_last_date = pivot_table.loc[last_date].sort_values(ascending=False)

        # 가장 높은 3개와 가장 낮은 3개 출력
        if type == '업종소' and length == 4:
            print(type + " : Top 10 Sectors on the last date:")
            pprint.pprint(sorted_last_date.head(10))
            
            print("\n" + type + " : Bottom 10 Sectors on the last date:")
            pprint.pprint(sorted_last_date.tail(10))
        else:pass

        if type == '업종대' and length == 4:
            pprint.pprint(sorted_last_date.head(5))
            pprint.pprint(sorted_last_date.tail(5))
        else:pass

        return pivot_table
    
    def MakeMongoDB_KR_GetSector_S(self, CodeName, df_Sector):

        try:
            for stock in df_Sector.index:
    
                if stock == CodeName:

                    GetSector = df_Sector['업종소'].loc[stock]
                    break
        except:
            print("Not Defined sector small")
        return GetSector

    def MakeMongoDB_KR_GetSector_B(self, CodeName, df_Sector):

        try:
            for stock in df_Sector.index:
    
                if stock == CodeName:

                    GetSector = df_Sector['업종대'].loc[stock]
                    break
        except:
            print("Not Defined sector small")
            GetSector = 'Not Defined'
        return GetSector
        
    def MakeMongoDB_KR_RS(self):
        
        DB = MongoDB(DB_addres = "MONGODB_LOCAL")
        str_database_name_W = 'KrDataBase_AD'
        self.df_AW, self.StockList_KR = DB.ReadDataBase(self.StockList_KR, 'ALL', 'KR', str_database_name_W, self.start_day, self.end_day)

        file_name = MainPath + 'Excel/QuantData.xlsx'
        df_Sector = pd.read_excel(file_name,header= 0,index_col='코드',dtype=str,na_values ='NaN')

        ranked_df_4W, ranked_df_52W = self.MakeRSData_KR_Sub()

        Sector_S_RS_4W = self.MakeMongoDB_KR_Sort_Sector(ranked_df_4W, type = '업종소', length = 4).round(1)
        Sector_S_RS_52W = self.MakeMongoDB_KR_Sort_Sector(ranked_df_52W, type = '업종소', length = 52).round(1)
        
        Sector_B_RS_4W = self.MakeMongoDB_KR_Sort_Sector(ranked_df_4W, type = '업종대', length = 4).round(1)
        Sector_B_RS_52W = self.MakeMongoDB_KR_Sort_Sector(ranked_df_52W, type = '업종대', length = 52).round(1)

        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        self.str_database_name = 'KrDataBase_RS'
        self.db = conn.get_database(self.str_database_name)

        ####################################        

        for count in range(len(self.StockList_KR)):

            stocks = self.StockList_KR[count]
            renamed_stock = "A"+str(stocks)
            
            collection = self.db.get_collection(renamed_stock)
            
            if DB.ChkTableExist(self.str_database_name, stocks, 'KR') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_week_in_db_new = ranked_df_4W[stocks].index[-1]
                
                if last_week_in_db_new > last_week_in_db_old:
                    
                    try:
                        print(count,"/",len(self.StockList_KR)," - UPDATE ",stocks," : ",KisKR.GetStockName(stocks)," ( ",last_week_in_db_old," > ",last_week_in_db_new, " )")

                        #df_ALL = DB.GetStockHis_W(stocks, last_date_in_db, self.end_day)
                        
                        df_RS = pd.concat([ranked_df_4W[stocks], ranked_df_52W[stocks]], axis=1)
                        df_RS.columns = ['RS_4W', 'RS_52W']
                        df_RS = df_RS.dropna()
                        #df_ALL = pd.concat([df_ALL,df_RS], axis=1)
                        df_ALL = df_RS
                        Sector_S = self.MakeMongoDB_KR_GetSector_S(renamed_stock,df_Sector)
                        Sector_B = self.MakeMongoDB_KR_GetSector_B(renamed_stock,df_Sector)

                        df_RS_S_Sector = pd.concat([Sector_S_RS_4W[Sector_S], Sector_S_RS_52W[Sector_S]], axis=1)
                        df_RS_S_Sector.columns = ['Sec_S_RS_4W', 'Sec_S_RS_52W']
                        df_RS_S_Sector = df_RS_S_Sector.dropna()
                        df_ALL = pd.concat([df_ALL,df_RS_S_Sector], axis=1)

                        df_RS_B_Sector = pd.concat([Sector_B_RS_4W[Sector_B], Sector_B_RS_52W[Sector_B]], axis=1)
                        df_RS_B_Sector.columns = ['Sec_B_RS_4W', 'Sec_B_RS_52W']
                        df_RS_B_Sector = df_RS_B_Sector.dropna()
                        df_ALL = pd.concat([df_ALL,df_RS_B_Sector], axis=1)

                        df_ALL['Sector_S'] = Sector_S
                        df_ALL['Sector_B'] = Sector_B
                        
                        # MongoDB에 없는 데이터만 필터링
                        df_ALL = df_ALL[df_ALL.index > last_week_in_db_old]
                        
                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    except Exception as e:
                        print("Exception ", e)
                else:
                    print(count,"/",len(self.StockList_KR)," - EXIST  ",stocks," : ",KisKR.GetStockName(stocks))


            else:
                print(count,"/",len(self.StockList_KR)," - NEW    ",stocks," : ",KisKR.GetStockName(stocks))

                try:
                    #df_ALL = DB.GetStockHis_W(stocks, self.start_day, self.end_day)
                    df_RS = pd.concat([ranked_df_4W[stocks], ranked_df_52W[stocks]], axis=1)
                    df_RS.columns = ['RS_4W', 'RS_52W']
                    df_RS = df_RS.dropna()
                    #df_ALL = pd.concat([df_ALL,df_RS], axis=1)
                    df_ALL = df_RS
                    
                    Sector_S = self.MakeMongoDB_KR_GetSector_S(renamed_stock,df_Sector)
                    Sector_B = self.MakeMongoDB_KR_GetSector_B(renamed_stock,df_Sector)

                    df_RS_S_Sector = pd.concat([Sector_S_RS_4W[Sector_S], Sector_S_RS_52W[Sector_S]], axis=1)
                    df_RS_S_Sector.columns = ['Sec_S_RS_4W', 'Sec_S_RS_52W']
                    #df_RS_S_Sector = df_RS_S_Sector.dropna()
                    df_ALL = pd.concat([df_ALL,df_RS_S_Sector], axis=1)
                    
                    df_RS_B_Sector = pd.concat([Sector_B_RS_4W[Sector_B], Sector_B_RS_52W[Sector_B]], axis=1)
                    df_RS_B_Sector.columns = ['Sec_B_RS_4W', 'Sec_B_RS_52W']
                    #df_RS_B_Sector = df_RS_B_Sector.dropna()
                    df_ALL = pd.concat([df_ALL,df_RS_B_Sector], axis=1)

                    df_ALL['Sector_S'] = Sector_S
                    df_ALL['Sector_B'] = Sector_B
                    
                    df_ALL = df_ALL.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)


    # 각 날짜별로 주가 종가 데이터를 기준으로 순위를 매기는 함수
    def rank_stocks(self, data):
        return data.rank(pct=True)
        

    def CalcAdFactor(self, str_database_name):
        
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        if str_database_name == 'KrDataBase_W':
            
            db_O = conn.get_database(str_database_name)
            db_A = conn.get_database('KrDataBase_AW')
            db_ADF = conn.get_database('KrDataBase')
        ####################################      

        for count in range(len(self.StockList_KR)):
            
            stocks = self.StockList_KR[count]
            try:
                renamed_stock = "A"+str(stocks)
                collection_O = db_O.get_collection(renamed_stock)
                collection_A = db_A.get_collection(renamed_stock)
                collection = db_ADF.get_collection(renamed_stock)
                # MongoDB에서 모든 데이터를 조회
                cursor_O = collection_O.find({})
                cursor_A = collection_A.find({})

                # Cursor를 리스트로 변환한 후 DataFrame으로 변환
                data_O = list(cursor_O)
                data_A = list(cursor_A)

                # MongoDB의 ObjectId 제거 (필요에 따라)
                for record_O in data_O:
                    record_O.pop('_id', None)  # '_id' 필드가 필요 없으면 제거
                for record_A in data_A:
                    record_A.pop('_id', None)  # '_id' 필드가 필요 없으면 제거    

                # DataFrame으로 변환
                df_O = pd.DataFrame(data_O)
                df_O.set_index('Date', inplace=True)            
                df_A = pd.DataFrame(data_A)
                df_A.set_index('Date', inplace=True) 

                # 두 데이터프레임의 인덱스 교집합 구하기
                common_index = df_O.index.intersection(df_A.index)

                # 교집합을 기반으로 두 데이터프레임에서 해당 행만 남기기
                df1_common = df_O.loc[common_index]
                df2_common = df_A.loc[common_index]

                df = DB.GetAdjustFactor(df1_common,df2_common)

                print(count,"/",len(self.StockList_KR)," - NEW    ",stocks," : ",KisKR.GetStockName(stocks))

                df = df.reset_index()

                # 데이터프레임을 딕셔너리로 변환
                data_dict = df.to_dict("records")

                # MongoDB에 데이터 삽입
                collection.insert_many(data_dict)

            except Exception as e:
                print("Exception ", e)
                self.delete_stocklist.append(stocks)
            
               