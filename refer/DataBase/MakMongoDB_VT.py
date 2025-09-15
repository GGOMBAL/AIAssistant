import pymongo
from Path import MainPath
import Helper.KIS.KIS_Common as Common 
import json
import pandas as pd
from DataBase.CalMongoDB import MongoDB as DB
from datetime import datetime, timedelta
import Helper.KIS.KIS_API_Helper_US as KisUS
from Helper.KIS.KIS_Make_StockList import GetStockList
import pytz
import time
import pprint
from Path import MainPath
import os
import yaml
class ColMongoVtDB:

    def __init__(self,area):

        with open(MainPath + 'myStockInfo.yaml', encoding='UTF-8') as f:
            self.stock_info = yaml.load(f, Loader=yaml.FullLoader)
			
        self.area = area
        self.end_day = (datetime.now(pytz.utc))
        self.start_day = (datetime.now(pytz.utc) - timedelta(days=3650))#.strftime('%Y-%m-%d')

        GetStockList(self.area, self.market)

        #파일 경로입니다.
        if self.area == 'HNX':
            Stock_file_path = MainPath + "json/HnxStockCodeList.json"
            Deleted_file_path = MainPath + "json/HnxDeleteStockList.json"
        elif self.area == 'HSX':
            Stock_file_path = MainPath + "json/HsxStockCodeList.json"
            Deleted_file_path = MainPath + "json/HsxDeleteStockList.json"

        with open(Stock_file_path, 'r') as json_file:
            BtStockList = json.load(json_file)
        
        try:
            with open(Deleted_file_path, 'r') as json_file:
                self.delete_stocklist = json.load(json_file)

        # b에 있는 요소를 a에서 삭제
            self.StockList_VT = [item for item in BtStockList if item not in self.delete_stocklist]
        except:
            self.StockList_VT = BtStockList
            self.delete_stocklist = list()

        df_D = KisUS.GetOhlcv('VCB',"D",Common.GetNowDateStr("US"))
        df_D.index = pd.to_datetime(df_D.index)
        self.latest_D = df_D.index[-1]
        self.latest_D = self.latest_D.tz_localize(pytz.timezone('UTC')).date()
#
        df_W = KisUS.GetOhlcv('VCB',"W",Common.GetNowDateStr("US"))
        df_W.index = pd.to_datetime(df_W.index)
        self.latest_W = df_W.index[-1] # datetime
        self.first_W = df_W.index[0] # datetime
        self.latest_W = self.latest_W.tz_localize(pytz.timezone('UTC')).date()   
        self.first_W = self.first_W.tz_localize(pytz.timezone('UTC')).date()   
        
    ######################################################################
    ######################################################################

    def MakeMongoDB_VT_M(self, area = 'HNX'):
    
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        if area == 'HNX':
            self.str_database_name = 'HnxDataBase_M'
        elif area == 'HSX':
            self.str_database_name = 'HsxDataBase_M'
        
        self.db = conn.get_database(self.str_database_name)

        ####################################      

        for count in range(len(self.StockList_VT)):

            stocks = self.StockList_VT[count]

            collection = self.db.get_collection(stocks)

            if DB.ChkTableExist(self.str_database_name, stocks,'VT') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                latest_in_db = collection.find_one(sort=[('Datetime', -1)])['Datetime']
                LatestDateinDB = latest_in_db.date()

                if self.latest_D > LatestDateinDB:

                    try:

                        df_ALL = KisUS.GetOhlcvMin(stocks, area)    ## KRX 주가데이터

                        print(count,"/",len(self.StockList_VT)," - UPDATE(M)    ",stocks, " TimeFrame : ",df_ALL.index[0] , " => " , df_ALL.index[-1])

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Datetime'] = date
                            collection.insert_one(data)
      
                    except Exception as e:
                        print("Exception ", e)

                else:
                    print(count,"/",len(self.StockList_VT)," - EXIST(M)  ",stocks)


            else:
                
                try:
                    df_ALL = KisUS.GetOhlcvMin(stocks, area)    ## KRX 주가데이터
                    
                    print(count,"/",len(self.StockList_VT)," - NEW(M)    ",stocks, " TimeFrame : ",df_ALL.index[0] , " => " , df_ALL.index[-1])

                    df_ALL = df_ALL.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception [ ", stocks, " ] ", e)

    def MakeMongoDB_VT_D(self, area = 'HNX', ohlcv = 'N'):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        
        #// 데이터베이스 정보를 가져온다
        if ohlcv == 'N':
            if area == 'HNX':
                self.str_database_name = 'HnxDataBase_D'
            elif area == 'HSX':
                self.str_database_name = 'HsxDataBase_D'
        else:            
            if area == 'HNX':
                self.str_database_name = 'HnxDataBase_D_ohlcv'
            elif area == 'HSX':
                self.str_database_name = 'HsxDataBase_D_ohlcv'

        self.db = conn.get_database(self.str_database_name)

        Temp_delete_stocklist = list()
        ####################################      

        for count in range(len(self.StockList_VT)):

            stocks = self.StockList_VT[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'VT') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_date_in_db = collection.find_one(sort=[('Date', -1)])['Date']

                if self.latest_D > last_date_in_db.date():
                    
                    try:
                        df_ALL = DB.GetStockHis(stocks, 'D', last_date_in_db, self.end_day, 'VT', ohlcv)       ## KIS 주가데이터
                        print(count,"/",len(self.StockList_VT)," - UPDATE(D) ",stocks," : "," ( ",last_date_in_db.date()," > ",self.latest_D, " )")
                        # MongoDB에 없는 데이터만 필터링
                        df_ALL = df_ALL[df_ALL.index > last_date_in_db]


                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_ALL.iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    except Exception as e:
                        print("Exception ", e)
                        self.delete_stocklist.append(stocks)                 

                else:
                    print(count,"/",len(self.StockList_VT)," - EXIST(D)  ",stocks,  self.latest_D , last_date_in_db)


            else:
                
                try:
                    
                    df_ALL = DB.GetStockHis(stocks, 'D', self.start_day, self.end_day,'VT', ohlcv)    ## KIS 주가데이터
                    print(count,"/",len(self.StockList_VT)," - NEW(D) ",stocks," : "," ( ",df_ALL.index[0]," > ",df_ALL.index[-1], " )")
                    
                    ## 중복 인덱스 제거 ##
                    df_ALL = df_ALL[~df_ALL.index.duplicated(keep='first')]
                    df_ALL.index = df_ALL.index.tz_localize('UTC')
                    df_ALL = df_ALL.reset_index()

                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_ALL.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception : ",stocks, e)
                    Temp_delete_stocklist.append(stocks)

                #파일 경로입니다.
        if self.area == 'HNX':
            file_path = MainPath + "json/HnxDeleteStockList.json"
        elif self.area == 'HSX':
            file_path = MainPath + "json/HsxDeleteStockList.json"

        with open(file_path, 'r') as json_file:
            TempUsStockList = json.load(json_file)

        self.delete_stocklist = list(set(TempUsStockList) | set(Temp_delete_stocklist))

        with open(file_path, 'w') as outfile:
            json.dump(self.delete_stocklist, outfile)
                                
    def MakeMongoDB_VT_W(self, area = 'NAS'):
    
        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        if area == 'HNX':
            self.str_database_name = 'HnxDataBase_W'
        elif area == 'HSX':
            self.str_database_name = 'HsxDataBase_W'

        self.db = conn.get_database(self.str_database_name)
        
        #// 데이터베이스 정보를 가져온다
        if area == 'HNX':
            str_database_name_D = 'HnxDataBase_D_ohlcv'
        elif area == 'HSX':
            str_database_name_D = 'HsxDataBase_D_ohlcv'

        df_D_Temp, self.StockList_VT = DB.ReadDataBase(self.StockList_VT, 'US', area, str_database_name_D, self.start_day, self.end_day)

        # 빈 dict 생성
        df = {}
        
        timezone = pytz.timezone('US/Eastern')
        
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

            #df[key].index = df[key].index.tz_localize('UTC')
        
        self.df_W = df
        
        for count in range(len(self.StockList_VT)):

            stocks = self.StockList_VT[count]

            renamed_stock = str(stocks)
            collection = self.db.get_collection(renamed_stock)

            if DB.ChkTableExist(self.str_database_name, stocks, 'US') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_week_in_db_new = df[renamed_stock].index[-1]
                
                if last_week_in_db_new.date() > last_week_in_db_old.date():

                    if 1:#try:
                        print(count,"/",len(self.StockList_VT)," - UPDATE(W) ",stocks," : "," ( ",last_week_in_db_old.date()," > ",last_week_in_db_new.date(), " )")

                        # MongoDB에 없는 데이터만 필터링
                        df[renamed_stock] = df[renamed_stock][df[renamed_stock].index > last_week_in_db_old]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df[renamed_stock].iterrows():
                            #print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    else:#except Exception as e:
                        print("Exception ", e)

                else:
                    print(count,"/",len(self.StockList_VT)," - EXIST(W)  ",stocks,  last_week_in_db_new.date() , last_week_in_db_old.date())


            else:
                
                try:
                    ## 중복 인덱스 제거 ##
                    df[renamed_stock] = df[renamed_stock][~df[renamed_stock].index.duplicated(keep='first')]
                    print(count,"/",len(self.StockList_VT)," - NEW(W)    ",stocks, df[renamed_stock].index.min(), " > ", df[renamed_stock].index.max())                         

                    # 데이터프레임을 딕셔너리로 변환
                    df[renamed_stock] = df[renamed_stock].reset_index()  
                    data_dict = df[renamed_stock].to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    print("Exception ", e)  
                    
    def MakeMongoDB_VT_RS_SUB(self, area = 'HNX'):

        #// 몽고클라이언트를 만든다
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        #// 데이터베이스 정보를 가져온다
        if area == 'HNX':
            self.str_database_name = 'HnxDataBase_W'
        elif area == 'HSX':
            self.str_database_name = 'HsxDataBase_W'

        self.db = conn.get_database(self.str_database_name)

        df_RS_4W = pd.DataFrame()
        df_RS_52W = pd.DataFrame()

        for count in range(len(self.StockList_VT)):

            try:
                stocks = self.StockList_VT[count]
                db_name = self.str_database_name

                df = DB.ExecuteSql(db_name, stocks)
                df = df[~df.index.duplicated(keep='first')]
                df_RS = df['close']
                df_RS.name = stocks            

                try:
                    df_RS_4W = (df_RS - df_RS.shift(4)) / df_RS.shift(4) * 100
                    if count == 0:
                        df_ALL_4W = df_RS_4W 
                    else:
                        df_ALL_4W = pd.concat([df_ALL_4W,df_RS_4W], axis=1)               
                except:
                    df_RS_4W = 0

                try:
                    df_RS_52W = (df_RS - df_RS.shift(52)) / df_RS.shift(52) * 100
                    if count == 0:
                        df_ALL_52W = df_RS_52W 

                    else:
                        df_ALL_52W = pd.concat([df_ALL_52W,df_RS_52W], axis=1)              
                except:
                    df_ALL_52W = 0
                
            except:pass#Exception as e:
                #print(e)

        # 각 날짜별로 순위를 매기고, 결과를 원래 데이터 위치에 씌우기
        ranked_df_4W = df_ALL_4W.apply(self.rank_stocks, axis=0)
        ranked_df_4W = (ranked_df_4W*100).round(2)
        ranked_df_4W = ranked_df_4W.dropna(axis=0, how='all')

        ranked_df_52W = df_ALL_52W.apply(self.rank_stocks, axis=0)
        ranked_df_52W = (ranked_df_52W*100).round(2)   
        ranked_df_52W = ranked_df_52W.dropna(axis=0, how='all')   

        return ranked_df_4W, ranked_df_52W

    def MakeMongoDB_VT_RS(self, area = 'HNX'):
        
        ranked_df_4W, ranked_df_52W = self.MakeMongoDB_VT_RS_SUB(area)
        Empty_Stocks = 0
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_LOCAL"], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        if area == 'HNX':
            self.str_database_name = 'HnxDataBase_RS'
        elif area == 'HSX':
            self.str_database_name = 'HsxDataBase_RS'

        self.db = conn.get_database(self.str_database_name)

        ####################################        

        for count in range(len(self.StockList_VT)):

            stocks = self.StockList_VT[count]
            
            collection = self.db.get_collection(stocks)
            
            if DB.ChkTableExist(self.str_database_name, stocks,'US') == True:

                # MongoDB에 저장된 마지막 날짜 가져오기
                last_week_in_db_old = collection.find_one(sort=[('Date', -1)])['Date']
                last_week_in_db_new = ranked_df_4W[stocks].index[-1]
                
                if last_week_in_db_new > last_week_in_db_old:
                    
                    try:
                        print(count,"/",len(self.StockList_VT)," - UPDATE ",stocks," : "," ( ",last_week_in_db_new," > ",self.latest_W, " )")
                        
                        df_RS = pd.concat([ranked_df_4W[stocks], ranked_df_52W[stocks]], axis=1)
                        df_RS.columns = ['RS_4W', 'RS_52W']
                        df_RS = df_RS.dropna()
                        
                        # MongoDB에 없는 데이터만 필터링
                        df_RS = df_RS[df_RS.index > last_week_in_db_new]

                        # 필터링된 데이터를 MongoDB에 저장
                        for date, row in df_RS.iterrows():
                            print(date, row)
                            data = row.to_dict()
                            data['Date'] = date
                            collection.insert_one(data)

                    except Exception as e:
                        print("Exception ", e)
                else:
                    print(count,"/",len(self.StockList_VT)," - EXIST  ",stocks)


            else:
                
                try:

                    df_RS = pd.concat([ranked_df_4W[stocks], ranked_df_52W[stocks]], axis=1)
                    print(count,"/",len(self.StockList_VT)," - NEW ",stocks)
                    #print(df_RS)
                    df_RS.columns = ['RS_4W', 'RS_52W']
                    
                    df_RS = df_RS.dropna()
                    df_RS = df_RS.reset_index()
                    
                    # 데이터프레임을 딕셔너리로 변환
                    data_dict = df_RS.to_dict("records")

                    # MongoDB에 데이터 삽입
                    collection.insert_many(data_dict)

                except Exception as e:
                    Empty_Stocks = Empty_Stocks + 1
                    print("Exception ", stocks , e, Empty_Stocks)
                                
    # 각 날짜별로 주가 종가 데이터를 기준으로 순위를 매기는 함수
    def rank_stocks(self, data):
        return data.rank(pct=True)

