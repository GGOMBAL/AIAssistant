from DataBase.CalMongoDB import MongoDB
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import copy
from Strategy.Strategy_A import StrategyA
from DataBase.CalDBName import CalDataBaseName
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import sys
import os
import concurrent.futures
class Test:
    
    #def Quant_Main(file_name, Asset_Num, Strategy):
    def __init__(self, Universe, Market, area, start_day, end_day, StrategyName, Type):
        
        pd.set_option('future.no_silent_downcasting', True)
        
        self.Market = Market
        self.area = area
        self.start_day = start_day
        self.data_start_day = start_day - timedelta(days=365*3)
        self.end_day = end_day
        self.Universe = Universe
        self.StrategyName = StrategyName
        self.Type = Type
        
        self.RoadDataFromDB()
        
        # Initialize self.df to prevent AttributeError
        self.df = {}
        
        self.RunStrategy()



    def read_database_task(self, Market, area, data_type, Universe, data_start_day, end_day):
        """단일 데이터베이스 읽기 작업을 수행하는 함수"""
        DB = MongoDB(DB_addres="MONGODB_LOCAL")
        Database_name = CalDataBaseName(Market, area, data_type, "Stock")
        df, updated_universe = DB.ReadDataBase(Universe, Market, area, Database_name, data_start_day, end_day)
        return data_type, df, updated_universe

    # def RoadDataFromDB(self):
        
    #     DB = MongoDB(DB_addres = "MONGODB_LOCAL")

    #     Database_name = CalDataBaseName(self.Market, self.area, "W", "Stock")
    #     self.df_W, self.Universe = DB.ReadDataBase(self.Universe, self.Market, self.area, Database_name, self.data_start_day, self.end_day)

    #     Database_name = CalDataBaseName(self.Market, self.area, "RS", "Stock")
    #     self.df_RS, self.Universe = DB.ReadDataBase(self.Universe, self.Market, self.area, Database_name, self.data_start_day, self.end_day)

    #     Database_name = CalDataBaseName(self.Market, self.area, "AD", "Stock")
    #     self.df_D, self.Universe = DB.ReadDataBase(self.Universe, self.Market, self.area, Database_name, self.data_start_day, self.end_day)

    #     ## US SPECIFIC DB ##
    #     if self.area == 'US':
            
    #         Database_name = CalDataBaseName(self.Market, self.area, "E", "Stock")
    #         self.df_E, self.Universe = DB.ReadDataBase(self.Universe, self.Market, self.area, Database_name, self.data_start_day, self.end_day)

    #         Database_name = CalDataBaseName(self.Market, self.area, "F", "Stock")
    #         self.df_F, self.Universe = DB.ReadDataBase(self.Universe, self.Market, self.area, Database_name, self.data_start_day, self.end_day)

            
    #     print(f'## Read Database Done : {self.area} in {self.Market} - StockCnt : ' , len(self.Universe))
    def RoadDataFromDB(self):
        """ThreadPoolExecutor를 사용한 병렬 데이터베이스 읽기"""
        
        # 기본 데이터 타입들
        data_types = ["W", "RS", "AD"]
        
        # US 지역인 경우 추가 데이터 타입
        if self.area == 'US':
            data_types.extend(["E", "F"])
        
        # 병렬 실행 (ThreadPoolExecutor 사용)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(data_types)) as executor:
            # 모든 작업을 제출
            futures = {
                executor.submit(
                    self.read_database_task,
                    self.Market,
                    self.area,
                    data_type,
                    self.Universe,
                    self.data_start_day,
                    self.end_day
                ): data_type for data_type in data_types
            }
            
            # 각 데이터 타입별 updated_universe를 저장할 딕셔너리
            updated_universes = {}
            
            # 결과를 기다리고 처리
            for future in concurrent.futures.as_completed(futures):
                data_type = futures[future]
                try:
                    _, df, updated_universe = future.result()
                    
                    # 결과를 적절한 속성에 할당
                    if data_type == "W":
                        self.df_W = df
                        updated_universes['updated_universe_W'] = updated_universe
                    elif data_type == "RS":
                        self.df_RS = df
                        updated_universes['updated_universe_RS'] = updated_universe
                    elif data_type == "AD":
                        self.df_D = df
                        updated_universes['updated_universe_AD'] = updated_universe
                    elif data_type == "E":
                        self.df_E = df
                        updated_universes['updated_universe_E'] = updated_universe
                    elif data_type == "F":
                        self.df_F = df
                        updated_universes['updated_universe_F'] = updated_universe
                    
                except Exception as e:
                    print(f"{data_type} 데이터 로드 중 오류 발생: {e}")
            
            # 모든 updated_universe의 공통 ticker들로 self.Universe 설정
            if updated_universes:
                common_tickers = set(list(updated_universes.values())[0])
                for universe in updated_universes.values():
                    common_tickers = common_tickers.intersection(set(universe))
                self.Universe = list(common_tickers)
        
        print(f'## Read Database Done : {self.area} in {self.Market} - StockCnt : {len(self.Universe)}')
        
        if self.area == 'KR':
            self.Universe = ['A' + stock for stock in self.Universe]
        
        # self.Universe에 없는 ticker들을 모든 dataframe에서 제거
        universe_set = set(self.Universe)
        
        # df_W에서 제거
        if hasattr(self, 'df_W'):
            keys_to_remove = [key for key in self.df_W.keys() if key not in universe_set]
            for key in keys_to_remove:
                del self.df_W[key]
        
        # df_RS에서 제거
        if hasattr(self, 'df_RS'):
            keys_to_remove = [key for key in self.df_RS.keys() if key not in universe_set]
            for key in keys_to_remove:
                del self.df_RS[key]
        
        # df_D에서 제거
        if hasattr(self, 'df_D'):
            keys_to_remove = [key for key in self.df_D.keys() if key not in universe_set]
            for key in keys_to_remove:
                del self.df_D[key]
        
        # US 지역인 경우 추가 dataframe에서도 제거
        if self.area == 'US':
            if hasattr(self, 'df_E'):
                keys_to_remove = [key for key in self.df_E.keys() if key not in universe_set]
                for key in keys_to_remove:
                    del self.df_E[key]
            
            if hasattr(self, 'df_F'):
                keys_to_remove = [key for key in self.df_F.keys() if key not in universe_set]
                for key in keys_to_remove:
                    del self.df_F[key]
        
        # Optimized duplicate removal using vectorized operations
        for i in range(len(self.Universe)):
    
            stocks = self.Universe[i]
                
            self.df_W[stocks] = self.df_W[stocks][~self.df_W[stocks].index.duplicated()]
            self.df_RS[stocks] = self.df_RS[stocks][~self.df_RS[stocks].index.duplicated()]
            self.df_D[stocks] = self.df_D[stocks][~self.df_D[stocks].index.duplicated()]
            
            if self.area == 'US':
                self.df_E[stocks] = self.df_E[stocks][~self.df_E[stocks].index.duplicated()]
                self.df_F[stocks] = self.df_F[stocks][~self.df_F[stocks].index.duplicated()]
        
        # Reindex and merge fundamental data for US market
        if self.area == 'US':    
            for i in range(len(self.Universe)):
    
                stocks = self.Universe[i]

                self.df_F[stocks] = self.df_F[stocks].reindex(self.df_W[stocks].index, method='ffill')
                self.df_F[stocks] = pd.concat([self.df_W[stocks]['close'], self.df_F[stocks]], axis=1)

                self.df_F[stocks].ffill(inplace=True)
                self.df_F[stocks] = self.df_F[stocks][~self.df_F[stocks].index.duplicated()]

        ################################################################
        
    def RunStrategy(self):
        
               
        dfW1 = copy.deepcopy(self.df_W)
        dfD1 = copy.deepcopy(self.df_D)
        dfR1 = copy.deepcopy(self.df_RS)
        if self.area == 'US':
            dfE1 = copy.deepcopy(self.df_E)
            dfF1 = copy.deepcopy(self.df_F)
        else:
            dfE1 = 0
            dfF1 = 0
            
        Universe1 = copy.deepcopy(self.Universe)
        
        #print(f"Universe : {len(Universe1)} W : {len(dfW1.keys())} D : {len(dfD1.keys())} R : {len(dfR1.keys())} E: {len(dfE1.keys())} F : {len(dfF1.keys())}")
        
        # 1. 딕셔너리들을 리스트로 묶기
        if self.area == 'US':
            dicts = [dfW1, dfD1, dfR1, dfE1, dfF1]
        else:
            dicts = [dfW1, dfD1, dfR1]
            
        # 2. 공통 키 계산 (set.intersection 사용)
        common_keys = set(dicts[0]).intersection(*[set(d) for d in dicts[1:]])

        # 3. 각 딕셔너리에서 공통 키가 아닌 항목 삭제
        for d in dicts:
            for key in list(d.keys()):       # .keys()를 리스트로 복사해야 루프 중 삭제 가능
                if key not in common_keys:
                    del d[key]
        # if self.area == 'US':
        #     print(f"Univers : {len(Universe1)} W : {len(dfW1.keys())} D : {len(dfD1.keys())} R : {len(dfR1.keys())} E: {len(dfE1.keys())} F : {len(dfF1.keys())}")
        # else:
        #     print(f"Univers : {len(Universe1)} W : {len(dfW1.keys())} D : {len(dfD1.keys())} R : {len(dfR1.keys())}")
            
        if self.StrategyName == 'A':
            Strategy_1 = StrategyA(Universe1, self.area, dfW1 , dfD1, dfR1, dfE1, dfF1, self.start_day, self.end_day, self.Type)
            self.df, self.Universe, = Strategy_1.ReturnFunc()
            
        elif self.StrategyName == 'B':
            Strategy_1 = StrategyB(Universe1, self.area, dfW1 , dfD1, dfR1, dfE1, dfF1, self.start_day, self.end_day, self.Type)
            self.df, self.Universe, = Strategy_1.ReturnFunc()
            
        elif self.StrategyName == 'A+B':
            Strategy_1 = StrategyB(Universe1, self.area, dfW1 , dfD1, dfR1, dfE1, dfF1, self.start_day, self.end_day, self.Type)
            self.df, Universe1, = Strategy_1.ReturnFunc()
            
            dfW2 = copy.deepcopy(self.df_W)
            dfD2 = copy.deepcopy(self.df_D)
            dfR2 = copy.deepcopy(self.df_RS)
            if self.area == 'US':
                dfE2 = copy.deepcopy(self.df_E)
                dfF2 = copy.deepcopy(self.df_F)
            else:
                dfE2 = 0
                dfF2 = 0             
            Universe2 = copy.deepcopy(self.Universe)

            Strategy_2 = StrategyA(Universe2, self.area, dfW2 , dfD2, dfR2, dfE2, dfF2, self.start_day, self.end_day, self.Type)
            df2, Universe2, = Strategy_2.ReturnFunc()               

            self.df.update(df2)
            self.Universe = Universe1 + Universe2
        else:
            self.Universe = Universe1
                
        for i in range(len(self.Universe)):
            
            stocks = self.Universe[i]
                
            # if self.Type == 'Trading': 
            #     latest_date = self.df[stocks].index[-2]
            #     self.df[stocks] = self.df[stocks].loc[[latest_date]]
            # elif self.Type == 'Backtest' or self.Type == 'Plot': # 기존 Backtest, Plot 타입
            #     self.df[stocks]  = self.df[stocks][(self.df[stocks].index >= self.start_day) & (self.df[stocks].index <= self.end_day)]
            
            # Only filter if the stock data exists in self.df (populated by Strategy_A)
            if stocks in self.df and self.df[stocks] is not None:
                self.df[stocks]  = self.df[stocks][(self.df[stocks].index >= self.start_day) & (self.df[stocks].index <= self.end_day)]        
    
    def ReturnFunc(self):         
    
        print(f'## Read Database & Make Signal Done [{self.area}]- Stock Count : ' , len(self.Universe) )

        return self.df , self.Universe

    def ReturnStockState(self, code):
        
        try:
            for i in range(len(self.Universe)):
        
                if code == self.Universe[i]:

                    if self.Market == 'KR':
                        stocks = 'A' + self.Universe[i]
                    else:
                        stocks = self.Universe[i]

                    Return_Func_df = self.df[stocks]
        except:
            Return_Func_df = 0

        return Return_Func_df