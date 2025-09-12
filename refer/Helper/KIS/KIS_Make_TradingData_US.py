# -*- coding: utf-8 -*-

import Helper.KIS.KIS_Common as Common
import pprint
import json
from Main.Path import MainPath
import Helper.Messenger.telegram_bot as telegram_bot
def TradingData_Get_US():
    
    Common.SetChangeMode("VIRTUAL1")

    USStockList = list()
    #파일 경로입니다.
    US_file_path = MainPath + "UsStockCodeList.json"

    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(US_file_path, 'r') as json_file:
            USStockList = json.load(json_file)

    except Exception as e:
        print("Exception by First")



    print("Make Trading Data US Start!!")
    telegram_bot.SendMessageWithRetry("Make Trading Data US Start!!")


    UsTradingDataList = list()


    for stock_code in USStockList:


        try:
            print(stock_code, " ..Start.. ")

            df = Common.GetOhlcv("US",stock_code)
            pprint.pprint(df)

            TradingDataDict = dict()

            TradingDataDict['StockCode'] = stock_code #종목코드


            TradingDataDict['StockPrice_0'] = float(df['close'][-1]) #현재가(종가) 
            TradingDataDict['StockPrice_1'] = float(df['close'][-2]) #전날 종가
            TradingDataDict['StockPrice_2'] = float(df['close'][-3]) #전전날 종가


            TradingDataDict['StockRate'] = float(df['change'][-1]) * 100.0 #등락률!




            ############################## 거래대금 #######################################
            TradingDataDict['StockMoney_0'] = float(df['value'][-1]) #현재 기록된 거래대금
            TradingDataDict['StockMoney_1'] = float(df['value'][-2]) #그 전날 거래대금
            TradingDataDict['StockMoneyRate'] = TradingDataDict['StockMoney_0'] / TradingDataDict['StockMoney_1'] #전날 거래대금 대비 몇 배인지!
            #############################################################################




            ############################## 이동평균 #######################################
            #이동평균...
            try:
                TradingDataDict['StockMA5_0'] = Common.GetMA(df['close'],5,-1) #현재 종가기준 5일 이동평균선
                TradingDataDict['StockMA5_1'] = Common.GetMA(df['close'],5,-2) #그 전 5일 이동평균선
                TradingDataDict['StockMA5_2'] = Common.GetMA(df['close'],5,-3) #그 전전 5일 이동평균선
            except Exception as e:
                TradingDataDict['StockMA5_0'] = 0
                TradingDataDict['StockMA5_1'] = 0
                TradingDataDict['StockMA5_2'] = 0




            #이동평균...
            try:
                TradingDataDict['StockMA20_0'] = Common.GetMA(df['close'],20,-1) #현재 종가기준 20일 이동평균선
                TradingDataDict['StockMA20_1'] = Common.GetMA(df['close'],20,-2) #그 전 20일 이동평균선
                TradingDataDict['StockMA20_2'] = Common.GetMA(df['close'],20,-3) #그 전전 20일 이동평균선
            except Exception as e:
                TradingDataDict['StockMA20_0'] = 0
                TradingDataDict['StockMA20_1'] = 0
                TradingDataDict['StockMA20_2'] = 0



            #이동평균...
            try:
                TradingDataDict['StockMA60_0'] = Common.GetMA(df['close'],60,-1) #현재 종가기준 60일 이동평균선
                TradingDataDict['StockMA60_1'] = Common.GetMA(df['close'],60,-2) #그 전 60일 이동평균선
                TradingDataDict['StockMA60_2'] = Common.GetMA(df['close'],60,-3) #그 전전 60일 이동평균선
            except Exception as e:
                TradingDataDict['StockMA60_0'] = 0
                TradingDataDict['StockMA60_1'] = 0
                TradingDataDict['StockMA60_2'] = 0


            #이동평균...
            try:
                TradingDataDict['StockMA120_0'] = Common.GetMA(df['close'],120,-1) #현재 종가기준 60일 이동평균선
                TradingDataDict['StockMA120_1'] = Common.GetMA(df['close'],120,-2) #그 전 60일 이동평균선
                TradingDataDict['StockMA120_2'] = Common.GetMA(df['close'],120,-3) #그 전전 60일 이동평균선
            except Exception as e:
                TradingDataDict['StockMA120_0'] = 0
                TradingDataDict['StockMA120_1'] = 0
                TradingDataDict['StockMA120_2'] = 0
            #############################################################################     





            ############################## RSI #######################################
            #RSI...
            try:
                TradingDataDict['StockRSI_0'] = Common.GetRSI(df,14,-1) #현재 종가기준 RSI14 
                TradingDataDict['StockRSI_1'] = Common.GetRSI(df,14,-2) #그 전 RSI14 
                TradingDataDict['StockRSI_2'] = Common.GetRSI(df,14,-3) #그 전전 RSI14 
            except Exception as e:
                TradingDataDict['StockRSI_0'] = 0
                TradingDataDict['StockRSI_1'] = 0
                TradingDataDict['StockRSI_2'] = 0
            ############################################################################# 




            ############################## BB #######################################
            #현재 종가 기준 볼린저 밴드
            try:
                BB_0 = Common.GetBB(df,20,-1)
                TradingDataDict['StockBB_Middle_0'] = BB_0['ma']
                TradingDataDict['StockBB_Upper_0'] = BB_0['upper']
                TradingDataDict['StockBB_Lower_0'] = BB_0['lower']

            except Exception as e:
                TradingDataDict['StockBB_Middle_0'] = 0
                TradingDataDict['StockBB_Upper_0'] = 0
                TradingDataDict['StockBB_Lower_0'] = 0


            #그전 종가 기준 볼린저 밴드
            try:
                BB_1 = Common.GetBB(df,20,-2)
                TradingDataDict['StockBB_Middle_1'] = BB_1['ma']
                TradingDataDict['StockBB_Upper_1'] = BB_1['upper']
                TradingDataDict['StockBB_Lower_1'] = BB_1['lower']

            except Exception as e:
                TradingDataDict['StockBB_Middle_1'] = 0
                TradingDataDict['StockBB_Upper_1'] = 0
                TradingDataDict['StockBB_Lower_1'] = 0


            #그전전 종가 기준 볼린저 밴드
            try:
                BB_2 = Common.GetBB(df,20,-3)
                TradingDataDict['StockBB_Middle_2'] = BB_2['ma']
                TradingDataDict['StockBB_Upper_2'] = BB_2['upper']
                TradingDataDict['StockBB_Lower_2'] = BB_2['lower']

            except Exception as e:
                TradingDataDict['StockBB_Middle_2'] = 0
                TradingDataDict['StockBB_Upper_2'] = 0
                TradingDataDict['StockBB_Lower_2'] = 0

            ############################################################################# 

            UsTradingDataList.append(TradingDataDict)

            pprint.pprint(TradingDataDict)


            print(stock_code, " ..Done.. ")

        except Exception as e:
            print("Exception ", e)

    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    pprint.pprint(UsTradingDataList)

    print("--------------------------------------------------------")

    #파일 경로입니다.
    Us_data_file_path = MainPath + "json/UsTradingDataList.json"
    #파일에 리스트를 저장합니다
    with open(Us_data_file_path, 'w') as outfile:
        json.dump(UsTradingDataList, outfile)

    line_alert.SendMessage("Make Stock Trading Data US Done!!" + str(len(UsTradingDataList)))

