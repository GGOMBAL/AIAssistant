import Helper.KIS.KIS_Make_TradingData as KisTRD
import numpy as np
import pandas as pd
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed


def _process_single_stock_technical_data(args):
    stock, p_code, area, dataframe_stock, trading_config = args
    try:
        processed_df = KisTRD.GetTrdData2(p_code, area, dataframe_stock, stock, trading_config)
        return stock, processed_df
    except Exception as e:
        print(f"Error processing technical data for {stock}: {e}")
        return stock, None

class GenTRD():

    def __init__(self, Universe, area, df_W, df_D, df_RS, df_E, df_F, start_day, end_day, Trading):

        self.Universe = Universe       
        self.area = area
        self.df_W = df_W
        self.df_D = df_D
        self.df_RS = df_RS
        self.df_E = df_E
        self.df_F = df_F
        self.start_day = start_day
        self.end_day = end_day
        self.Trading = Trading
        
        self.df_W = self.GetTechnicalData(self.Universe, self.df_W, 'W')
        for stock_code, df in self.df_W.items():
            self.df_W[stock_code] = self.optimize_dataframe_memory(df)

        self.df_RS = self.GetTechnicalData(self.Universe, self.df_RS, 'RS')
        for stock_code, df in self.df_RS.items():
            self.df_RS[stock_code] = self.optimize_dataframe_memory(df)

        #self.df_E = self.GetTechnicalData(self.Universe, self.df_E, 'E')
        #for stock_code, df in self.df_E.items():
        #    self.df_E[stock_code] = self.optimize_dataframe_memory(df)

        if self.area =='US':
            self.df_F = self.GetTechnicalData(self.Universe, self.df_F, 'F')
            for stock_code, df in self.df_F.items():
                self.df_F[stock_code] = self.optimize_dataframe_memory(df)
        else:
            self.df_F = 0

        self.df_D = self.GetTechnicalData(self.Universe, self.df_D, 'D')
        for stock_code, df in self.df_D.items():
            self.df_D[stock_code] = self.optimize_dataframe_memory(df)
        
        # 두 데이터프레임을 Date 열을 기준으로 병합
        for i in range(len(self.Universe)):
            
            stocks = self.Universe[i]

            self.df_RS[stocks] = self.df_RS[stocks][(self.df_RS[stocks].index >= self.start_day) & (self.df_RS[stocks].index <= self.end_day)]
            self.df_W[stocks]  = self.df_W[stocks][(self.df_W[stocks].index >= self.start_day) & (self.df_W[stocks].index <= self.end_day)]
            self.df_D[stocks]  = self.df_D[stocks][(self.df_D[stocks].index >= self.start_day) & (self.df_D[stocks].index <= self.end_day)]

            if self.area =='US':
                self.df_E[stocks]  = self.df_E[stocks][(self.df_E[stocks].index >= self.start_day) & (self.df_E[stocks].index <= self.end_day)]
                self.df_F[stocks]  = self.df_F[stocks][(self.df_F[stocks].index >= self.start_day) & (self.df_F[stocks].index <= self.end_day)]
                                    
        
    ##############################################

    def GetTechnicalData(self, Universe, df, PCode):
           
        tasks = []
        for stock in Universe:
            if stock in df:
                tasks.append((stock, PCode, self.area, df[stock], self.Trading))

        processed_data = {}
        
        # Use ThreadPoolExecutor for concurrent processing
        max_workers = min(len(tasks), 4)  # Limit workers to avoid overwhelming the system
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_stock = {
                executor.submit(_process_single_stock_technical_data, task): task[0] 
                for task in tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_stock):
                stock_code, processed_df_stock = future.result()
                if processed_df_stock is not None:
                    processed_data[stock_code] = self.optimize_dataframe_memory(processed_df_stock)
        
        return processed_data
    
    def optimize_dataframe_memory(self, df):
        for col in df.columns:
            if df[col].dtype == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
            elif df[col].dtype == 'int64':
                df[col] = pd.to_numeric(df[col], downcast='integer')
        return df

    def ReturnFunc(self):

        return self.df_D, self.df_W, self.df_RS, self.df_E, self.df_F

