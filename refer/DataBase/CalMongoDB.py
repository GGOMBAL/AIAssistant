import pandas as pd
import time
import datetime
import traceback
import pandas as pd
from Path import MainPath        
from datetime import datetime, timedelta
import pymongo
import Helper.KIS.KIS_Common as Common
import Helper.KIS.KIS_API_Helper_KR as KisKR
import Helper.KIS.KIS_API_Helper_US as KisUS
import Helper.AlphaVantage.AV_API_Helper as Alpha
import Helper.yfinance.YF_API_Helper_US as YF
import pytz
import yaml

from DataBase.CalDBName import CalDataBaseName

class MongoDB: 
    
    def __init__(self,DB_addres = "MONGODB_LOCAL"):
        
        self.DB_addres = DB_addres

        with open(MainPath + 'myStockInfo.yaml', encoding='UTF-8') as f:
            self.stock_info = yaml.load(f, Loader=yaml.FullLoader)

    def MakStockDb(self,db_name,df_ALL,stock):
        
        renamed_stock = "A" + stock

        conn = pymongo.MongoClient(host=self.stock_info[self.DB_addres], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        
        #// 데이터베이스 정보를 가져온다
        str_database_name = db_name
        db = conn.get_database(str_database_name)

        collection = db[renamed_stock]

        # MongoDB에 행을 저장합니다.
        collection.insert_one(df_ALL)

    def UpdStockDb(self, db_name,df_ALL,stock):

        renamed_stock = "A" + stock

        conn = pymongo.MongoClient(host=self.stock_info[self.DB_addres], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        #// 데이터베이스 정보를 가져온다
        str_database_name = db_name
        db = conn.get_database(str_database_name)

        collection = db[renamed_stock]
        
        # 오늘 날짜
        today = datetime.now()

        # MongoDB에서 오늘 날짜의 주가 데이터 확인
        stock_data = collection.find_one({'Date': today})

        if not stock_data:
            
            latest_document = collection.find().sort('Date', -1).limit(1)

            dataframes = {}
            cursor = db[collection].find({})
            dataframes[collection] = pd.DataFrame(list(cursor))


            df_ALL = Common.GetOhlcv("KR",stock)
            df_ALL = df_ALL.reset_index()
    
            # 각 행을 순회하며 MongoDB에 저장합니다.
            for index, row in df_ALL.iterrows():
            # 'date' 필드가 이미 존재하는지 확인합니다.
                if collection.find_one({'Date': row['Date']}):
                    #print(f"Skipping duplicate date: {row['Date']}")
                    continue

            # MongoDB에 행을 저장합니다.
            collection.insert_one(row.to_dict())
            
    def ExecuteSql(self, db_name, table_name):
        
        # MongoDB에 연결
        connection = pymongo.MongoClient(host=self.stock_info[self.DB_addres], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)

        db = connection[db_name]
        
        # 컬렉션 선택
        collection = db[table_name]

        # 데이터 가져오기
        data = pd.DataFrame(list(collection.find()))


        try:
            df = data.set_index('Date')
        except:
            df = data.set_index('Datetime')
            
        return df

    def ChkTableExist(self, db_name, table_name, area):

        # MongoDB에 연결
        connection = pymongo.MongoClient(host=self.stock_info[self.DB_addres], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        db = connection[db_name]

        # 컬렉션 이름을 확인
        list_of_collections = db.list_collection_names()
        if area == 'KR':
            renamed_stock = "A" + str(table_name)
        else:
            renamed_stock = str(table_name)

        if renamed_stock in list_of_collections:
            return True
        else:
            return False

    def GetStockHisKRX(self, stknum, start_date, end_date):

        try:
            df_ALL = Common.GetKRXOhlcv(stknum,start_date,end_date,adVar=0)
            df_ALL.reset_index(inplace=True)

            df_ALL.sort_values(by='Date', ascending=True, inplace = True)
            df_ALL = df_ALL.dropna(subset=['Date'], how='any', axis=0)
            df_ALL.set_index('Date', inplace=True)  

            return df_ALL
        except:
            return 0
            
    def GetStockHis_W(self, stknum, start_date, end_date, ohlcv = "Y"):

        df_ALL = pd.DataFrame()
        Data_Concat_is_Done = False

        if type(start_date) == str:
            start_date = datetime.strptime(start_date, "%Y%m%d")
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, "%Y%m%d")

        while Data_Concat_is_Done == False:

            if end_date - start_date > timedelta(weeks=100):
                
                Start_D = start_date
                End_D = start_date + timedelta(weeks=100)
                start_date = End_D + timedelta(weeks=1)
                        
                #df_Stock = kis.get_stock_data(stknum,Start_D,End_D)
                df_Stock = KisKR.GetOhlcv(stknum,"W",(Start_D.strftime('%Y%m%d')),(End_D.strftime('%Y%m%d')), 0, ohlcv)
                
                try:
                    df_ALL = pd.concat([df_ALL,df_Stock])
                except:
                    pass
                    
                Data_Concat_is_Done = False                
                
                time.sleep(0.01)
            else:
                Start_D = start_date
                End_D = end_date

                #df_Stock = kis.get_stock_data(stknum,Start_D,End_D)
                df_Stock = KisKR.GetOhlcv(stknum,"W",(Start_D.strftime('%Y%m%d')),(End_D.strftime('%Y%m%d')),0, ohlcv)
                df_ALL = pd.concat([df_ALL,df_Stock])

                Data_Concat_is_Done = True
                time.sleep(0.01)
        
        df_ALL.index = pd.to_datetime(df_ALL.index)
        
        return df_ALL
    
    def GetStockHis(self, stknum,p_code, start_date, end_date, area = 'KR', ohlcv = "Y"):

        df_ALL = pd.DataFrame()
        Data_Concat_is_Done = False

        if type(start_date) == str:
            start_date = datetime.strptime(start_date, "%Y%m%d")
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, "%Y%m%d")

        changed_end_date = end_date

        if area == 'KR':

            all_data = []
            while start_date <= end_date:
                
                # Define the range
                if end_date - start_date > timedelta(days=100):
                    temp_end_date = start_date + timedelta(days=100)
                else:
                    temp_end_date = end_date

                # Convert to required string format
                start_str = start_date.strftime('%Y%m%d')
                end_str = temp_end_date.strftime('%Y%m%d')

                # Fetch the stock data

                df_stock = KisKR.GetOhlcv(stknum, "D", start_str, end_str, 0, ohlcv)
                
                # Append to the list
                if isinstance(df_stock, list):pass
                elif df_stock.empty:pass
                else:    
                    all_data.append(df_stock)

                # Update the start date
                start_date = temp_end_date + timedelta(days=1)

                # Sleep if needed
                time.sleep(0.01)

            # Concatenate all dataframes at once

            df_ALL = pd.concat(all_data)

        elif area == 'HK':
            
            if ohlcv == 'Y':
                
                df_ALL = YF.GetOhlcv(stknum,p_code, start_date, changed_end_date, ohlcv)
                    
            else:
                
                while Data_Concat_is_Done == False:

                    timezone = pytz.timezone('UTC')  # or any specific timezone

                    if changed_end_date.astimezone(timezone).date() - start_date.astimezone(timezone).date() > timedelta(days=100):
                        
                        df_Stock = KisUS.GetOhlcv(stknum,p_code,changed_end_date, ohlcv)

                        if isinstance(df_Stock, pd.DataFrame):
                            df_ALL = df_ALL.combine_first(df_Stock)
                            changed_end_date = changed_end_date - timedelta(days=100)
                            Data_Concat_is_Done = False    

                        else:
                            Data_Concat_is_Done = True   

                        time.sleep(0.01)
                    else:

                        df_Stock = KisUS.GetOhlcv(stknum,p_code,changed_end_date, ohlcv)

                        if isinstance(df_Stock, pd.DataFrame):
                            df_ALL = pd.concat([df_ALL,df_Stock])
                        else:pass

                        Data_Concat_is_Done = True
                        time.sleep(0.01)

                df_YF = YF.GetOhlcv(stknum,p_code, start_date, changed_end_date, ohlcv)
                df_YF['split_factor']
        else:

            timezone = pytz.timezone('UTC')  # or any specific timezone
            
            if end_date.astimezone(timezone).date() - start_date.astimezone(timezone).date() > timedelta(days=100):

                df_ALL = Alpha.GetOhlcv_Bender(stknum, 'full', start_date)
            
            else:

                df_ALL = Alpha.GetOhlcv_Bender(stknum, 'comfact', start_date)              

        #print(df_ALL.index[0] , " - ", df_ALL.index[-1])
        df_ALL.index = pd.to_datetime(df_ALL.index)

    ## Data Clean up ##
        df_ALL.sort_values(by='Date', ascending=True, inplace = True)
        
        if ohlcv == 'Y':
            df_ALL[['ad_open', 'ad_high', 'ad_low', 'ad_close', 'volume']] = df_ALL[['ad_open', 'ad_high', 'ad_low', 'ad_close', 'volume']].apply(pd.to_numeric)      
        else:
            df_ALL[['open', 'high', 'low', 'close', 'volume']] = df_ALL[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric) 
             
        time.sleep(0.1)

        return df_ALL
                             
    def ReadDataBase(self, stock_list, Market, area, str_database_name, frdate , todate):
        
        conn = pymongo.MongoClient(host=self.stock_info[self.DB_addres], port=self.stock_info["MONGODB_PORT"], \
                                   username=self.stock_info["MONGODB_ID"],
                                   password=self.stock_info["MONGODB_PW"],)
        db = conn.get_database(str_database_name)
        # 여기서 데이터베이스 작업 수행
        
        # 각 컬렉션의 데이터를 가져와서 DataFrame에 저장합니다.
        dataframes = {}
        lst_cnt = 0

        for i in range(len(stock_list)):
            
            if area == 'KR':
                stocks = 'A' + str(stock_list[i])
            else:
                stocks = str(stock_list[i])
            
            try:
                cursor = db[stocks].find({'Date' : {'$gte' : frdate, '$lte' : todate}},{'_id' : False})
                dataframes[stocks] = pd.DataFrame(list(cursor))
            
                #if dataframes[stocks].empty or len(dataframes[stocks].index) != LenthOfData:
                if dataframes[stocks].empty:
                    #print("delete : ",stocks)
                    del dataframes[stocks]

                else:
                    dataframes[stocks] = dataframes[stocks].sort_values(by='Date', ascending=True)
                    dataframes[stocks] = dataframes[stocks].set_index('Date')
     
                    dataframes[stocks] = dataframes[stocks].ffill()
                    dataframes[stocks] = dataframes[stocks][~dataframes[stocks].index.duplicated(keep='first')]
            except:
                pass
            #time.sleep(0.01)

        if area == 'KR':
            Universe_Temp = list(dataframes.keys())
            Universe = []

            for i in range(len(Universe_Temp)):
                Universe.append(Universe_Temp[i][1:])

            return dataframes, Universe
        else:
            Universe = list(dataframes.keys())
            
            return dataframes, Universe
        
    def GetAdjustFactor(self, df, df_AD):
        
        merged_df = pd.merge(df, df_AD, on='Date', suffixes=('_original', '_adjusted'))
        
        # 수정계수 계산: 수정계수 = 수정주가 / 원주가
        merged_df['AD_Factor'] = merged_df['close_adjusted'] / merged_df['close_original']

        # 필요한 열만 추출 (날짜와 수정계수)
        adjustment_factors_df = merged_df[['AD_Factor']]
    
        return adjustment_factors_df
    

    def GetStockHisEarn(self, stknum):

        try:           
            df_Earn = Alpha.CallUsEarningData(stknum)
            df_Earn.reset_index(inplace=True)
            df_Earn.sort_values(by='Date', ascending=True, inplace = True)
            
            df_Earn['eps_qoq'] = df_Earn.apply(lambda row: Alpha.calculate_qoq(row['eps'], df_Earn['eps'].shift(1).loc[row.name]), axis=1)
            df_Earn['eps_yoy'] = df_Earn.apply(lambda row: Alpha.calculate_yoy(row['eps'], df_Earn['eps'].shift(4).loc[row.name]), axis=1)
                        
            df_Rev = Alpha.CallUsRevenueData(stknum)           
            df_Rev.reset_index(inplace=True)
            df_Rev.sort_values(by='Date', ascending=True, inplace = True)
            
            df_Rev['rev_qoq'] = df_Rev.apply(lambda row: Alpha.calculate_qoq(row['revenue'], df_Rev['revenue'].shift(1).loc[row.name]), axis=1)
            df_Rev['rev_yoy'] = df_Rev.apply(lambda row: Alpha.calculate_yoy(row['revenue'], df_Rev['revenue'].shift(4).loc[row.name]), axis=1)
            
            df_ALL = pd.merge(df_Earn, df_Rev, on='Date', how='outer')
            df_ALL.ffill(inplace=True)
            df_ALL = df_ALL.dropna(subset=['Date'], how='any', axis=0)   
            df_ALL.reset_index(inplace=True)          
            df_ALL.sort_values(by='Date', ascending=True, inplace = True)
            
            df_ALL.set_index('EarningDate', inplace=True)
            df_ALL = df_ALL[~df_ALL.index.duplicated()]      
                
        except:
            df_ALL.empty
          
        return df_ALL
    
    def GetStockHisFdmt(self, stknum):

        try:     
            df_Income = Alpha.CallUsIncomeStatment(stknum)
            df_Balance = Alpha.CallUsBalanceSheet(stknum) 
            df_Rev = Alpha.CallUsRevenueData(stknum)    
            
            df_Income = pd.merge(df_Income, df_Balance, on='Date', how='outer')    
            df_Income = pd.merge(df_Income, df_Rev, on='Date', how='outer') 
                   
            df_Income.reset_index(inplace=True)
            df_Income.sort_values(by='Date', ascending=True, inplace = True)            
            df_Income.ffill(inplace=True)
        
            df_ALL = df_Income.dropna(subset=['Date'], how='any', axis=0)
            df_ALL.set_index('Date', inplace=True)     
            
            df_ALL['EPS'] = df_ALL['netIncome'] / df_ALL['commonStockSharesOutstanding']
            df_ALL['EPS_YOY'] = df_ALL['EPS'] / df_ALL['EPS'].shift(4)
            df_ALL['EPS_QOQ'] = df_ALL['EPS'] / df_ALL['EPS'].shift(1)            
            df_ALL['REV_YOY'] = df_ALL['revenue'] / df_ALL['revenue'].shift(4)
            df_ALL['REV_QOQ'] = df_ALL['revenue'] / df_ALL['revenue'].shift(1)            
            df_ALL[['EPS', 'EPS_YOY', 'EPS_QOQ', 'REV_YOY', 'REV_QOQ']] = df_ALL[['EPS', 'EPS_YOY', 'EPS_QOQ', 'REV_YOY', 'REV_QOQ']].round(2)        
        except:
            df_ALL.empty   
                        
        return df_ALL
