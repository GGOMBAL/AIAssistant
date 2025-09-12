import traceback
import Helper.KIS.KIS_Common as Common 
import pprint
import pandas as pd
from datetime import datetime, timedelta
import time
import Helper.KIS.KIS_API_Helper_US as KisUS

def GetTRDDataDic(df,df_W,df_KRX, stock_code):

    TradingDataDict = dict()
    
    time_info = time.gmtime()
    #년월 문자열을 만든다 즉 2022년 9월이라면 2022_9 라는 문자열이 만들어져 strYM에 들어간다!
    strYMD = str(time_info.tm_year) + "_" + str(time_info.tm_mon) + "_" + str(time_info.tm_mday)

    TradingDataDict['Date']         = strYMD                                                    #날짜 정보
    TradingDataDict['StockCode']    = stock_code                                                #종목코드
    TradingDataDict['StockPrice_0'] = float(df['close'].iloc[-1])                                #현재가(종가) 
    TradingDataDict['StockPrice_1'] = float(df['close'].iloc[-2])                                #전날 종가
    TradingDataDict['StockRate']    = (TradingDataDict['StockPrice_0'] - TradingDataDict['StockPrice_1'])*100 / TradingDataDict['StockPrice_1']#float(df['change'].iloc[-1]) * 100.0                          #등락률!
    TradingDataDict['Sector_S']     = Common.GetSectorName(stock_code,type = "Small")             #한국 주식 업종 소
    TradingDataDict['Sector_B']     = Common.GetSectorName(stock_code,type = "Big")             #한국 주식 업종 대
    TradingDataDict['StockCap']     = float(df_KRX['capital'].iloc[-1])
    TradingDataDict['StockCap']     = float(df_KRX['eps'].iloc[-1])
    try:
        TradingDataDict['SectorRS_S_4W'] = Common.GetSectorRSVal(stock_code,"S",4).iloc[-1]
        TradingDataDict['SectorRS_S_52W'] = Common.GetSectorRSVal(stock_code,"B",52).iloc[-1]
        TradingDataDict['SectorRS_B_4W'] = Common.GetSectorRSVal(stock_code,"S",4).iloc[-1]
        TradingDataDict['SectorRS_B_52W'] = Common.GetSectorRSVal(stock_code,"B",52).iloc[-1]
    except Exception as e:
        TradingDataDict['SectorRS_S_4W'] = 0
        TradingDataDict['SectorRS_S_52W'] = 0
        TradingDataDict['SectorRS_B_4W'] = 0
        TradingDataDict['SectorRS_B_52W'] = 0

    try:
        TradingDataDict['StockRS_4W'] = Common.GetStockRSVal(stock_code,4).iloc[-1]
        TradingDataDict['StockRS_52W'] = Common.GetStockRSVal(stock_code,52).iloc[-1]

    except Exception as e:
        TradingDataDict['StockRS_4W'] = 0
        TradingDataDict['StockRS_52W'] = 0

    try:
        TradingDataDict['SMA200_M'] = Common.GetSMA_MOM12(df,200,3).shift().iloc[-1]          #종가 기준 SMA200 모멘텀
        #TradingDataDict['SMA150_M'] = Common.GetSMA_MOM12(df,150,3).shift().iloc[-1]          #종가 기준 SMA150 모멘텀
        #TradingDataDict['SMA50_M']  = Common.GetSMA_MOM12(df,50,3).shift().iloc[-1]           #종가 기준 SMA50 모멘텀     
    
    except Exception as e:
        TradingDataDict['SMA200_M'] = 0
        #TradingDataDict['SMA150_M'] = 0
        #TradingDataDict['SMA50_M'] = 0

    try:
        #TradingDataDict['SMA5']  = Common.GetMA(df['close'],5,100).shift().iloc[-1]                  #현재 종가기준 20일 이동평균선
        TradingDataDict['SMA20']  = Common.GetMA(df['close'],20,100).shift().iloc[-1]                  #현재 종가기준 20일 이동평균선
        TradingDataDict['SMA50']  = Common.GetMA(df['close'],50,100).shift().iloc[-1]                  #현재 종가기준 60일 이동평균선
        #TradingDataDict['SMA150'] = Common.GetMA(df['close'],150,100).shift().iloc[-1]                 #현재 종가기준 120일 이동평균선
        #TradingDataDict['SMA200'] = Common.GetMA(df['close'],200,100).shift().iloc[-1]                 #현재 종가기준 200일 이동평균선
    except Exception as e:
        #TradingDataDict['SMA5']  = 0
        TradingDataDict['SMA20']  = 0
        TradingDataDict['SMA50']  = 0
        #TradingDataDict['SMA150'] = 0
        #TradingDataDict['SMA200'] = 0

    try:
        TradingDataDict['52_H'] = Common.GetMax(df_W,52*5).shift().iloc[-1]                     #현재 종가기준 52주 최고가
        TradingDataDict['52_L'] = Common.GetMin(df_W,52*5).shift().iloc[-1]                     #현재 종가기준 52주 최저가
    except Exception as e:
        TradingDataDict['52_H'] = 0
        TradingDataDict['52_L'] = 0

    try:
        TradingDataDict['1Year_H'] = Common.GetMax(df_W,12*5).iloc[-1]                  #월봉기준 12 = 1Y / 36 = 3Y
        TradingDataDict['2Year_H'] = Common.GetMax(df_W,24*5).iloc[-1]                  #월봉기준 12 = 1Y / 36 = 3Y
        TradingDataDict['1Year_L'] = Common.GetMin(df_W,12*5).iloc[-1]                  #월봉기준 12 = 1Y / 36 = 3Y
        TradingDataDict['2Year_L'] = Common.GetMin(df_W,24*5).iloc[-1]                  #월봉기준 12 = 1Y / 36 = 3Y
                
    except Exception as e:
        TradingDataDict['1Year_H'] = 0
        TradingDataDict['2Year_H'] = 0
        TradingDataDict['1Year_L'] = 0
        TradingDataDict['2Year_L'] = 0

    try:
        TradingDataDict['Lowest'] = df_W['low'].rolling(window=52).min().shift().iloc[-1]
        TradingDataDict['Highest'] = df_W['high'].rolling(window=52).max().shift().iloc[-1]
    except Exception as e:
        TradingDataDict['Lowest'] = 0
        TradingDataDict['Highest'] = 0

    return TradingDataDict

def GetTrdData2(p_code, area ,dataframe, stocks, Trading = True):

    if p_code == 'D':
        
        dataframe.rename(columns={'ad_open': 'open', 'ad_close': 'close', 'ad_high': 'high', 'ad_low': 'low'}, inplace=True)
        
        try:
            if Trading == True:

                dataframe['Highest_2Y'] = Common.GetHigh(dataframe,period=200*2)
                dataframe['Highest_1Y'] = Common.GetHigh(dataframe,period=200*1)
                dataframe['Highest_6M'] = Common.GetHigh(dataframe,period=100*1)
                dataframe['Highest_3M'] = Common.GetHigh(dataframe,period=50*1)
                dataframe['Highest_1M'] = Common.GetHigh(dataframe,period=20*1)
                dataframe['SMA200_M'] = Common.GetSMA_MOM12(dataframe,200,3)
                dataframe['SMA20']  = Common.GetMA(dataframe['close'],20,100)
                dataframe['SMA50']  = Common.GetMA(dataframe['close'],50,100)
                dataframe['SMA200']  = Common.GetMA(dataframe['close'],200,100) 
                dataframe['ADR']        = Common.GetADR_Pct(dataframe,20)                            # window 20 ADR              
            else:

                dataframe['Highest_2Y'] = Common.GetHigh(dataframe,period=200*2).shift()
                dataframe['Highest_1Y'] = Common.GetHigh(dataframe,period=200*1).shift()
                dataframe['Highest_6M'] = Common.GetHigh(dataframe,period=100*1).shift()
                dataframe['Highest_3M'] = Common.GetHigh(dataframe,period=50*1).shift()
                dataframe['Highest_1M'] = Common.GetHigh(dataframe,period=20*1).shift()
                dataframe['SMA200_M'] = Common.GetSMA_MOM12(dataframe,200,3).shift()                  #종가 기준 SMA200 모멘텀   
                dataframe['SMA20']  = Common.GetMA(dataframe['close'],20,100).shift()                 #현재 종가기준 20일 이동평균선
                dataframe['SMA50']  = Common.GetMA(dataframe['close'],50,100).shift()                 #현재 종가기준 60일 이동평균선
                dataframe['SMA200'] = Common.GetMA(dataframe['close'],200,100).shift()                #현재 종가기준 200일 이동평균선               
                dataframe['ADR'] = Common.GetADR_Pct(dataframe,20).shift()                            # window 20 ADR
                                
        except Exception as e:
            print("D Error : ",e,stocks)

            dataframe['SMA200_M']  = 0
            dataframe['SMA20']     = 0
            dataframe['SMA50']     = 0
            dataframe['SMA200']    = 0
            dataframe['Highest_2Y'] = 0
            dataframe['Highest_1Y'] = 0
            dataframe['Highest_6M'] = 0
            dataframe['Highest_3M'] = 0
            dataframe['Highest_1M'] = 0
            dataframe['ADR']       = 0

                
        dataframe.rename(columns={'open': 'Dopen', 'close': 'Dclose', 'high': 'Dhigh', 'low': 'Dlow', 'volume':'Dvolume'}, inplace=True)


    if p_code == 'W':
        
        dataframe.rename(columns={'ad_open': 'open', 'ad_close': 'close', 'ad_high': 'high', 'ad_low': 'low'}, inplace=True)
        
        try:
            dataframe['52_H'] = Common.GetMax(dataframe,52)                                 #현재 종가기준 52주 최고가
            dataframe['52_L'] = Common.GetMin(dataframe,52)                                 #현재 종가기준 52주 최저가
            dataframe['1Year_H'] = Common.GetMax(dataframe,12*4)                            #월봉기준 12 = 1Y / 36 = 3Y
            dataframe['2Year_H'] = Common.GetMax(dataframe,24*4)                            #월봉기준 12 = 1Y / 36 = 3Y
            dataframe['1Year_L'] = Common.GetMin(dataframe,12*4)                            #월봉기준 12 = 1Y / 36 = 3Y
            dataframe['2Year_L'] = Common.GetMin(dataframe,24*4)                            #월봉기준 12 = 1Y / 36 = 3Y

        except Exception as e:
            print("W Error : ",e) 
            dataframe['52_H'] = 0
            dataframe['52_L'] = 0
            dataframe['1Year_H'] = 0
            dataframe['2Year_H'] = 0
            dataframe['1Year_L'] = 0
            dataframe['2Year_L'] = 0


        dataframe.rename(columns={'open': 'Wopen', 'close': 'Wclose', 'high': 'Whigh', 'low': 'Wlow', 'volume':'Wvolume'}, inplace=True)
        

    if p_code == 'RS':
        
        try:
            if Trading == True:
                dataframe['RS_SMA5']  = Common.GetMA(dataframe['RS_4W'],5,100)
                dataframe['RS_SMA20'] = Common.GetMA(dataframe['RS_4W'],20,100)
            else:
                dataframe['RS_SMA5']  = Common.GetMA(dataframe['RS_4W'],5,100).shift()
                dataframe['RS_SMA20'] = Common.GetMA(dataframe['RS_4W'],20,100).shift()

        except Exception as e:
            print("RS Error : ",e) 
            dataframe['RS_SMA5']  = 0
            dataframe['RS_SMA20'] = 0
                                
   
    if p_code == 'F':
        
        try:

            # Market Capitalization (시가총액)
            dataframe['MarketCapitalization'] = dataframe['close'] * dataframe['commonStockSharesOutstanding']
            # EPS (Earnings Per Share)
            dataframe['EPS'] = dataframe['netIncome'] / dataframe['commonStockSharesOutstanding']
            # PER (Price-to-Earnings Ratio)
            #dataframe['PER'] = dataframe['close'] / dataframe['EPS']
            # PBR (Price-to-Book Ratio)
            dataframe['PBR'] = dataframe['close'] / (dataframe['totalShareholderEquity'] / dataframe['commonStockSharesOutstanding'])
            # PSR (Price-to-Sales Ratio)
            dataframe['PSR'] = dataframe['close'] / (dataframe['totalRevenue'] / dataframe['commonStockSharesOutstanding'])
            # ROE (Return on Equity)
            dataframe['ROE'] = (dataframe['netIncome'] / dataframe['totalShareholderEquity']) * 100
            # ROA (Return on Assets)
            dataframe['ROA'] = (dataframe['netIncome'] / dataframe['totalAssets']) * 100
            # GPA (Gross Profit to Asset Ratio)
            dataframe['GPA'] = (dataframe['grossProfit'] / dataframe['totalAssets']) * 100
            # OPM (Operating Profit Margin)
            dataframe['OPM'] = (dataframe['operatingIncome'] / dataframe['totalRevenue']) * 100
            # PEG (Price-to-Earnings Growth Ratio)
            #dataframe['PEG'] = dataframe['PER'] / dataframe['eps_yoy']
            # EBITDA 계산
            dataframe['EBITDA'] = dataframe['operatingIncome'] + dataframe['depreciationAndAmortization']
            # EV (Enterprise Value) 계산
            dataframe['EV'] = dataframe['MarketCapitalization'] + dataframe['totalLiabilities'] - dataframe['cashAndCashEquivalentsAtCarryingValue']
            # EV/EBITDA 계산
            dataframe['EV/EBITDA'] = dataframe['EV'] / dataframe['EBITDA']
            # 데이터 프레임을 불러온 후, 'Date' 인덱스가 Datetime 타입인 행만 필터링합니다.
            dataframe = dataframe[pd.to_datetime(dataframe.index, errors='coerce').notna()]
            dataframe.drop(columns={"grossProfit","totalRevenue","operatingIncome","depreciationAndAmortization","ebitda","netIncome","totalAssets","cashAndCashEquivalentsAtCarryingValue","totalLiabilities","totalShareholderEquity","commonStockSharesOutstanding","longTermDebt","shortTermDebt","commonStock","retainedEarnings"}, inplace=True)

        except Exception as e:
            print("KRX Error : ",e)        
        
    return dataframe
