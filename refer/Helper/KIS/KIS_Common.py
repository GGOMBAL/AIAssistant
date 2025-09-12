import os
import yaml
import pprint
import json
import requests

from datetime import datetime, timedelta
from pytz import timezone

import Helper.KIS.KIS_API_Helper_US as KisUS
import Helper.KIS.KIS_API_Helper_KR as KisKR

import time
import random
import numpy as np

import FinanceDataReader as fdr
import pandas_datareader.data as web
from pykrx import stock

import numpy
import pandas as pd

import yfinance
from Main.Path import MainPath

stock_info = None

#설정 파일 정보를 읽어 옵니다.
with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
    stock_info = yaml.load(f, Loader=yaml.FullLoader)
      
NOW_DIST = ""

## Function List ##

# SetChangeMode()       # 계좌 전환 함수! REAL 실계좌 VIRTUAL 모의계좌
# GetNowDist()          # 현재 선택된 계좌정보를 리턴!
# GetAppKey()           # 앱 키를 반환하는 함수
# GetAppSecret()        # 앱시크릿을 리턴!
# GetAccountNo()        # 계좌 정보(계좌번호)를 리턴!
# GetPrdtNo()           # 계좌 정보(삼품코드)를 리턴!
# GetUrlBase()          # URL주소를 리턴!
# GetTokenPath()        # 토큰 저장할 경로
# MakeToken()           # 토큰 값을 리퀘스트 해서 실제로 만들어서 파일에 저장하는 함수!! 첫번째 파라미터: "KJM_ISA" 실계좌, "VIRTUAL" 모의계좌
# GetToken()            # 파일에 저장된 토큰값을 읽는 함수.. 만약 파일이 없다면 MakeToken 함수를 호출한다!
# GetHashKey()          # 해시키를 리턴한다!
# GetNowDateStr()       # 한국인지 미국인지 구분해 현재 날짜정보를 리턴해 줍니다!
# GetFromNowDateStr()   # 현재날짜에서 이전/이후 날짜를 구해서 리턴! (미래의 날짜를 구할 일은 없겠지만..)

## Function Def ##

def SetChangeMode(dist = "KJM_ISA"):
    global NOW_DIST 
    NOW_DIST = dist

def GetNowDist():
    global NOW_DIST 
    return NOW_DIST

def GetAppKey(dist = "KJM_ISA"):
    
    if dist == "KJM_ISA":
        key = "REAL_APP_KEY"
    elif dist == "KJM":
        key = "REAL2_APP_KEY"
    elif dist == "KMR":
        key = "REAL3_APP_KEY"
    elif dist == "SystemTrade":
        key = "REAL4_APP_KEY"
    elif dist == "KJM_US":
        key = "REAL5_APP_KEY"
    elif dist == "KMR_US":
        key = "REAL6_APP_KEY"
    elif dist == "VIRTUAL1":
        key = "VIRTUAL1_APP_KEY"
    elif dist == "VIRTUAL2":
        key = "VIRTUAL2_APP_KEY"
    else:
        # Default to REAL_APP_KEY for unknown distributions
        key = "REAL_APP_KEY"

    return stock_info[key]

def GetAppSecret(dist = "KJM_ISA"):
    
    if dist == "KJM_ISA":
        key = "REAL_APP_SECRET"
    elif dist == "KJM":
        key = "REAL2_APP_SECRET"
    elif dist == "KMR":
        key = "REAL3_APP_SECRET"
    elif dist == "SystemTrade":
        key = "REAL4_APP_SECRET"
    elif dist == "KJM_US":
        key = "REAL5_APP_SECRET"
    elif dist == "KMR_US":
        key = "REAL6_APP_SECRET"
    elif dist == "VIRTUAL1":
        key = "VIRTUAL1_APP_SECRET"
    elif dist == "VIRTUAL2":
        key = "VIRTUAL2_APP_SECRET"
    else:
        # Default to REAL_APP_SECRET for unknown distributions
        key = "REAL_APP_SECRET"
        
    return stock_info[key]

def GetAccountNo(dist = "KJM_ISA"):

    if dist == "KJM_ISA":
        key = "REAL_CANO"
    elif dist == "KJM":
        key = "REAL2_CANO"
    elif dist == "KMR":
        key = "REAL3_CANO"
    elif dist == "SystemTrade":
        key = "REAL4_CANO"
    elif dist == "KJM_US":
        key = "REAL5_CANO"
    elif dist == "KMR_US":
        key = "REAL6_CANO"
    elif dist == "VIRTUAL1":
        key = "VIRTUAL1_CANO"
    elif dist == "VIRTUAL2":
        key = "VIRTUAL2_CANO"
    else:
        # Default to REAL_CANO for unknown distributions
        key = "REAL_CANO"
        
    return stock_info[key]

def GetPrdtNo(dist = "KJM_ISA"):
    
    if dist == "KJM_ISA":
        key = "REAL_ACNT_PRDT_CD"
    elif dist == "KJM":
        key = "REAL2_ACNT_PRDT_CD"
    elif dist == "KMR":
        key = "REAL3_ACNT_PRDT_CD"
    elif dist == "SystemTrade":
        key = "REAL4_ACNT_PRDT_CD"
    elif dist == "KJM_US":
        key = "REAL5_ACNT_PRDT_CD"
    elif dist == "KMR_US":
        key = "REAL6_ACNT_PRDT_CD"
    elif dist == "VIRTUAL1":
        key = "VIRTUAL1_ACNT_PRDT_CD"
    elif dist == "VIRTUAL2":
        key = "VIRTUAL2_ACNT_PRDT_CD"
    else:
        # Default to REAL_ACNT_PRDT_CD for unknown distributions
        key = "REAL_ACNT_PRDT_CD"
        
    return stock_info[key]

def GetKisID(dist = "KJM_ISA"):
    
    if dist == "KJM_ISA":
        key = "REAL_KIS_ID"
    elif dist == "KJM":
        key = "REAL2_KIS_ID"
    elif dist == "KMR":
        key = "REAL3_KIS_ID"
    elif dist == "SystemTrade":
        key = "REAL4_KIS_ID"
    elif dist == "KJM_US":
        key = "REAL5_KIS_ID"
    elif dist == "KMR_US":
        key = "REAL6_KIS_ID"
    elif dist == "VIRTUAL1":
        key = "VIRTUAL1_KIS_ID"
    elif dist == "VIRTUAL2":
        key = "VIRTUAL2_KIS_ID"
    else:
        # Default to REAL_KIS_ID for unknown distributions
        key = "REAL_KIS_ID"
        
    return stock_info[key]

def GetUrlBase(dist = "KJM_ISA",websocket = False):
    
    if dist == "VIRTUAL1" or dist == "VIRTUAL2":
        if websocket == True:
            key = "VIRTUAL_WEBSOCKET_URL"
        else:
            key = "VIRTUAL_URL"
    else:
        if websocket == True:
            key = "REAL_WEBSOCKET_URL"
        else:
            key = "REAL_URL"
        
    return stock_info[key]

def GetTrID(market = "KR", websocket = False):
    
    if market == "KR":
        #key = {"체결":'H0STCNT0', "호가":'H0STASP0', "체잔":'H0STCNI0',}
        key = {"체결":'H0STCNT0'}
    else: #"US"
        #key = {"체결":'HDFSCNT0', "호가":'HDFSASP0', "체잔":'H0GSCNI0',}
        key = {"체결":'HDFSCNT0'}
        #key = {"체결":'HDFSCNT0', "체잔":'H0GSCNI0',}
        
    return key

def GetTokenPath(dist = "KJM_ISA"):

    if dist == "KJM_ISA":
        key = "REAL_TOKEN_PATH"
    elif dist == "KJM":
        key = "REAL2_TOKEN_PATH"
    elif dist == "KMR":
        key = "REAL3_TOKEN_PATH"
    elif dist == "SystemTrade":
        key = "REAL4_TOKEN_PATH"
    elif dist == "KJM_US":
        key = "REAL5_TOKEN_PATH"
    elif dist == "KMR_US":
        key = "REAL6_TOKEN_PATH"
    elif dist == "VIRTUAL1":
        key = "VIRTUAL1_TOKEN_PATH"
    elif dist == "VIRTUAL2":
        key = "VIRTUAL2_TOKEN_PATH"
    else:
        # Default to REAL_TOKEN_PATH for unknown distributions
        key = "REAL_TOKEN_PATH"
        
    return stock_info[key]        

def SetAccntInfo(dist = "KJM_ISA", market = "KR"):

    if dist == 'VIRTUAL1' or dist == 'VIRTUAL2':
        api_info = dict(app_key = GetAppKey(dist),
                        secret_key = GetAppSecret(dist),
                        acc_num = GetAccountNo(dist),
                        id = GetKisID(dist),
                        ws_url = GetUrlBase(dist,True),
                        tr_id_dict = GetTrID(market),
                        paper = True)
    else:
        api_info = dict(app_key = GetAppKey(dist),
                        secret_key = GetAppSecret(dist),
                        acc_num = GetAccountNo(dist),
                        id = GetKisID(dist),
                        ws_url = GetUrlBase(dist,True),
                        tr_id_dict = GetTrID(market),
                        paper = False)

    return api_info

def MakeToken(dist = "KJM_US"):

    headers = {"content-type":"application/json"}
    body = {
        "grant_type":"client_credentials",
        "appkey":GetAppKey(dist), 
        "appsecret":GetAppSecret(dist)
        }
    
    PATH = "oauth2/tokenP"
    URL = f"{GetUrlBase(dist)}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    print(f"Run make tokent {headers}, {dist}")
    
    if res.status_code == 200:
        my_token = res.json()["access_token"]

        #빈 딕셔너리를 선언합니다!
        dataDict = dict()

        #해당 토큰을 파일로 저장해 둡니다!
        TokenPath = MainPath + GetTokenPath(dist)
        dataDict["authorization"] = my_token
        with open(TokenPath, 'w') as outfile:
            json.dump(dataDict, outfile)   

        print('Get Authentification token Success!')  
        return my_token

    else:
        print('Get Authentification token fail!')  
        return "FAIL"

def MakeWebSocketKey(dist = "KJM_ISA"):

    headers = {"content-type":"application/json"}
    body = {
        "grant_type":"client_credentials",
        "appkey":GetAppKey(dist), 
        "appsecret":GetAppSecret(dist)
        }

    PATH = "tryitout/H0STCNT0"
    URL = f"{GetUrlBase(dist,True)}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    
    if res.status_code == 200:
        my_socket = res.json()["approval_key"]

        return my_socket

    else:
        print('Get WebSocket key fail!')  
        return "FAIL"
        
def GetToken(dist = "KJM_ISA"):
        
    #빈 딕셔너리를 선언합니다!
    dataDict = dict()

    try:
        TokenPath = MainPath + GetTokenPath(dist)
        #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
        with open(TokenPath, 'r') as json_file:
            
            dataDict = json.load(json_file)

        return dataDict['authorization']

    except Exception as e:
        print("Exception by First")

        #처음에는 파일이 존재하지 않을테니깐 바로 토큰 값을 구해서 리턴!
        return MakeToken(dist)

def GetHashKey(datas):

    PATH = "uapi/hashkey"
    URL = f"{GetUrlBase(NOW_DIST)}/{PATH}"

    headers = {
    'content-Type' : 'application/json',
    'appKey' : GetAppKey(NOW_DIST),
    'appSecret' : GetAppSecret(NOW_DIST),
    }

    res = requests.post(URL, headers=headers, data=json.dumps(datas))

    if res.status_code == 200 :
        return res.json()["HASH"]
    else:
        print("Error Code : " + str(res.status_code) + " | " + res.text)
        return None

def GetNowDateStr(area = "KR", type= "NONE" ):
    timezone_info = timezone('Asia/Seoul')
    if area == "US":
        timezone_info = timezone('America/New_York')

    now = datetime.now(timezone_info)
    if type.upper() == "NONE":
        return now.strftime("%Y%m%d")
    else:
        return now.strftime("%Y-%m-%d")

def GetFromNowDateStr(area = "KR", type= "NONE" , days=100):
    timezone_info = timezone('Asia/Seoul')
    if area == "US":
        timezone_info = timezone('America/New_York')

    now = datetime.now(timezone_info)

    if days < 0:
        next = now - timedelta(days=abs(days))
    else:
        next = now + timedelta(days=days)

    if type.upper() == "NONE":
        return next.strftime("%Y%m%d")
    else:
        return next.strftime("%Y-%m-%d")
############################################################################################################################################################

#통합 증거금 사용시 잔고 확인!
def GetBalanceKrwTotal():
    kr_data = KisKR.GetBalance()
    us_data = KisUS.GetBalance("KRW")

    balanceDict = dict()

    balanceDict['RemainMoney'] = str(float(kr_data['RemainMoney']) + float(us_data['RemainMoney']))
    #주식 총 평가 금액
    balanceDict['StockMoney'] = str(float(kr_data['StockMoney']) + float(us_data['StockMoney']))
    #평가 손익 금액
    balanceDict['StockRevenue'] = str(float(kr_data['StockRevenue']) + float(us_data['StockRevenue']))
    #총 평가 금액
    balanceDict['TotalMoney'] = str(float(kr_data['TotalMoney']) + float(us_data['TotalMoney']))

    return balanceDict

############################################################################################################################################################
#OHLCV 값을 한국투자증권 혹은 FinanceDataReader 혹은 야후 파이낸스에서 가지고 옴!
def GetOhlcv(area, stock_code, limit = 500):

    Adjlimit = limit * 1.7 #주말을 감안하면 5개를 가져오려면 적어도 7개는 뒤져야 된다. 1.4가 이상적이지만 혹시 모를 연속 공휴일 있을지 모르므로 1.7로 보정해준다

    df = None

    start_date = GetFromNowDateStr("KR","NONE",-36500),
    end_date = GetNowDateStr("KR")
    except_riase = False

    try:
        if area == "US":
            
            start_date = GetFromNowDateStr("US","NONE",-36500),
            end_date = GetNowDateStr("US")
            
            df = KisUS.GetOhlcv(stock_code,"D",start_date,end_date,adVar=1)

            #한투에서 100개 이상 못가져 오니깐 그 이상은 아래 로직을 탄다. 혹은 없는 종목이라면 역시 아래 로직을 탄다
            if Adjlimit > 100 or len(df) == 0:

                #미국은 보다 빠른 야후부터 
                except_riase = False
                try:
                    df = GetOhlcv2(area,stock_code,Adjlimit)
                except Exception as e:
                    except_riase = True
                    
                if except_riase == True:
                    df = GetOhlcv1(area,stock_code,Adjlimit)

        
        else:

            start_date = GetFromNowDateStr("KR","NONE",-36500),
            end_date = GetNowDateStr("KR")
            
            df = KisKR.GetOhlcv(stock_code,"D",start_date,end_date,adVar=1)           

            #한투에서 100개 이상 못가져 오니깐 그 이상은 아래 로직을 탄다. 혹은 없는 종목이라면 역시 아래 로직을 탄다
            if Adjlimit > 100 or len(df) == 0:

                #한국은 KRX 정보데이터시스템 부터 
                except_riase = False
                try:
                    df = GetOhlcv1(area,stock_code,Adjlimit)
                except Exception as e:
                    except_riase = True
                    
                if except_riase == True:
                    df = GetOhlcv2(area,stock_code,Adjlimit)


    except Exception as e:
        print(e)
        except_riase = True
    

    if except_riase == True:
        return df
    else:
        return df[-limit:]

#한국 주식은 KRX 정보데이터시스템에서 가져온다. 그런데 미국주식 크롤링의 경우 investing.com 에서 가져오는데 안전하게 2초 정도 쉬어야 한다!
# https://financedata.github.io/posts/finance-data-reader-users-guide.html
def GetOhlcv1(area, stock_code, limit = 500):

    df = fdr.DataReader(stock_code,GetFromNowDateStr(area,"BAR",-limit),GetNowDateStr(area,"BAR"))

    try :
        df = df[[ 'Open', 'High', 'Low', 'Adj Close', 'Volume']]
    except Exception:
        df = df[[ 'Open', 'High', 'Low', 'Close', 'Volume']]

    df.columns = [ 'open', 'high', 'low', 'close', 'volume']
    df.index.name = "Date"

    #거래량과 시가,종가,저가,고가의 평균을 곱해 대략의 거래대금을 구해서 value 라는 항목에 넣는다 ㅎ
    df.insert(5,'value',((df['open'] + df['high'] + df['low'] + df['close'])/4.0) * df['volume'])


    df.insert(6,'change',(df['close'] - df['close'].shift(1)) / df['close'].shift(1))

    df[[ 'open', 'high', 'low', 'close', 'volume', 'change']] = df[[ 'open', 'high', 'low', 'close', 'volume', 'change']].apply(pd.to_numeric)

    #미국주식은 2초를 쉬어주자! 안그러면 24시간 정지당할 수 있다!
    if area == "US":
        time.sleep(2.0)
    else:
        time.sleep(0.2)


    return df

def GetKRXOhlcv(stock_code,start_date,end_date,adVar=1):

    #start_date = GetFromNowDateStr("KR","NONE",-3650)
    #end_date = GetNowDateStr("KR","NONE")
    if(adVar):
        start_date = GetFromNowDateStr("KR","NONE",-36500)
        end_date = GetNowDateStr("KR","NONE")
    else:pass
    
    if type(start_date) != str:
        start_date = start_date.strftime('%Y%m%d')
    if type(end_date) != str:
        end_date = end_date.strftime('%Y%m%d')
        
    df_market_cap = stock.get_market_cap_by_date(start_date, end_date, stock_code)
    
    df_market_cap = df_market_cap[[ '시가총액' ]]
    df_market_cap.columns = [ 'capital' ]
    
    df_p2 = stock.get_market_fundamental_by_date(start_date, end_date, stock_code)
    df_p2 = df_p2[['PER','PBR','EPS','DIV']]
    df_p2.columns = ['per','pbr','eps','div']

    #df_ohlcv = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
    #df_ohlcv = df_ohlcv[[ '시가', '고가', '저가', '종가', '거래량', '등락률' ]]
    #df_ohlcv.columns = [ 'open', 'high', 'low', 'close', 'volume', 'change']
    
    if 1:#try:
        df_type = stock.get_market_trading_value_by_date(start_date, end_date, stock_code)
        df_type = df_type[['기관합계','기타법인','개인','외국인합계']]
        df_type.columns = ['기관', '기타', '개인', '외국인']

        df = pd.concat([df_market_cap['capital'], df_p2[['per','pbr','eps','div']],df_type], axis=1)
    else:#except:
        df = pd.concat([df_market_cap['capital'], df_p2[['per','pbr','eps','div']]], axis=1)
    df.index.name = "Date"
    df = df.apply(pd.to_numeric)
    #df[[ 'capital','open', 'high', 'low', 'close', 'volume', 'change','per','pbr','eps','div']] = df[[ 'capital','open', 'high', 'low', 'close', 'volume', 'change','per','pbr','eps','div']].apply(pd.to_numeric)
    df = df.round(2)
    df.index = pd.to_datetime(df.index)
    
    return df

#pykrx를 통해 지수 정보를 읽어온다!
#아래 2줄로 활용가능한 지수를 체크할 수 있다!!
#for index_v in stock.get_index_ticker_list(market='KOSDAQ'): #KOSPI 지수도 확인 가능!
#    print(index_v, stock.get_index_ticker_name(index_v))

def GetIndexOhlcvPyKrx(index_code, start_date , end_date):

    df = stock.get_index_ohlcv(start_date, end_date, index_code)

    df = df[[ '시가', '고가', '저가', '종가', '거래량', '거래대금' ]]
    df.columns = [ 'open', 'high', 'low', 'close', 'volume', 'value']
    df.index.name = "Date"
    df.insert(6,'change',(df['close'] - df['close'].shift(1)) / df['close'].shift(1))
    df[[ 'open', 'high', 'low', 'close', 'volume', 'change']] = df[[ 'open', 'high', 'low', 'close', 'volume', 'change']].apply(pd.to_numeric)

    time.sleep(0.2)

    return df

############################################################################################################################################################
'''
!!!!!stock_type 유형!!!!!

TARGET_FIX : 
첫 주문한 지정가격이 절대 변하지 않는다. 체결되기 전까지 매일 매일 재주문!!!

NORMAL : 
지정된 카운팅에 해당하는 날 전에는 계속 타겟 가격으로 주문을 넣다가 
카운팅 날짜 부터는 현재가 그 다음날에는 지정가로 일 단위로 주문을 넣는 루즈한 로직


DAY_END : 
지정가로 주문을 넣지만 하루안에 주문을 끝낸다.  장중에 매시간마다 해당 주문을 체크해서 현재가로 지정가 주문을 변경 (체결 확률 업! ) 
마지막 장 끝나기 전 시간에도 수량이 남아있다면 이때는 시장가로 마무리 !


DAY_END_TRY_ETF:
DAY_END랑 비슷하지만 ETF의 NAV와 괴리율을 고려해서 하루안에 끝내거나 다음 날로 넘김 (클래스 설명 참조)

'''
#area 지역: US or KR, 종목코드, 목표 가격, 수량 (양수면 매수 음수면 매도) 연속성 주문 시스템!
def AutoLimitDoAgain(botname, area, stock_code, target_price, do_amt, stock_type = "NORMAL"):

    #수량이 0이면 거른다!
    if int(do_amt) == 0:
        return None


    if area == "KR":
        #print("KR")

        MyStockList = KisKR.GetMyStockList()


        stock_amt = 0
        for my_stock in MyStockList:
            if my_stock['StockCode'] == stock_code:
                stock_amt = int(my_stock['StockAmt'])
                break

        AutoLimitData = dict()
        AutoLimitData['Area'] = area                #지역
        AutoLimitData['NowDist'] = GetNowDist()     #구분
        AutoLimitData['BotName'] = botname          #봇 이름
        AutoLimitData['StockCode'] = stock_code      #종목코드
        AutoLimitData['TargetPrice'] = float(target_price)   #타겟 주문 가격
        AutoLimitData['OrderAmt'] = int(do_amt)              #주문 수량 양수면 매수 음수면 매도 
        
        OrderData = None

        #사야된다
        if do_amt > 0:
            AutoLimitData['TargetAmt'] = stock_amt + abs(AutoLimitData['OrderAmt'])  #최종 목표 수량 (현재수량 + 주문수량)

            try:

                OrderData = KisKR.MakeBuyLimitOrder(stock_code,abs(do_amt),target_price)
                AutoLimitData['OrderNum'] = OrderData["OrderNum"]      #주문아이디1
                AutoLimitData['OrderNum2'] = OrderData["OrderNum2"]    #주문아이디2
                AutoLimitData['OrderTime'] = OrderData["OrderTime"]    #주문시간

            except Exception as e:

                #시간 정보를 읽는다
                time_info = time.gmtime()
                AutoLimitData['OrderNum'] = 0
                AutoLimitData['OrderNum2'] = 0
                AutoLimitData['OrderTime'] = GetNowDateStr(area) + str(time_info.tm_hour) + str(time_info.tm_min) + str(time_info.tm_sec)

                        

        #팔아야 된다!
        else:

            AutoLimitData['TargetAmt'] = stock_amt - abs(AutoLimitData['OrderAmt']) #최종 목표 수량 (현재수량 - 주문수량)

            try:
                    
                OrderData = KisKR.MakeSellLimitOrder(stock_code,abs(do_amt),target_price)
                AutoLimitData['OrderNum'] = OrderData["OrderNum"]
                AutoLimitData['OrderNum2'] = OrderData["OrderNum2"]   
                AutoLimitData['OrderTime'] = OrderData["OrderTime"]   

            except Exception as e:

                #시간 정보를 읽는다
                time_info = time.gmtime()
                AutoLimitData['OrderNum'] = 0
                AutoLimitData['OrderNum2'] = 0
                AutoLimitData['OrderTime'] = GetNowDateStr(area) + str(time_info.tm_hour) + str(time_info.tm_min) + str(time_info.tm_sec)

                        
                        
        AutoLimitData['IsCancel'] = 'N'  #주문 취소 여부
        AutoLimitData['IsDone'] = 'N'    #주문 완료 여부
        AutoLimitData['TryCnt'] = 0    #재주문 숫자 
        AutoLimitData['DelDate'] =  GetFromNowDateStr(area,"NONE",10)    #10일 미래의 날짜 즉 10일 후에는 해당 데이터를 삭제처리할 예정 (어자피 하루만 유효한 주문들이다. 하루 지나고 삭제해도 되지만 참고를 위해 10일간 남겨둔다)
        AutoLimitData['StockType'] = stock_type #stock_type 유형

        #해당 데이터의 ID를 만든다! 여러 항목의 조합으로 고유하도록!  이 아이디를 리턴해 봇에서 줘서 필요한 봇은 이 아이디를 가지고 리스트를 만들어 사용하면 된다!
        AutoLimitData['Id'] = AutoLimitData['NowDist'] + botname + area + str(stock_code) + str(AutoLimitData["OrderNum"]) + str(AutoLimitData["OrderNum2"]) + str(AutoLimitData["OrderTime"]) + str(do_amt) + str(target_price) 
    

        SaveAutoLimitDoAgainData(AutoLimitData)




        #등록된 해당 주문 데이터 ID를 리턴한다
        return AutoLimitData['Id']

        


    else:
        print("US")


        MyStockList = KisUS.GetMyStockList()


        stock_amt = 0
        for my_stock in MyStockList:
            if my_stock['StockCode'] == stock_code:
                stock_amt = int(my_stock['StockAmt'])
                break

        AutoLimitData = dict()
        AutoLimitData['Area'] = area                #지역
        AutoLimitData['NowDist'] = GetNowDist()     #구분
        AutoLimitData['BotName'] = botname          #봇 이름
        AutoLimitData['StockCode'] = stock_code      #종목코드
        AutoLimitData['TargetPrice'] = float(target_price)   #타겟 주문 가격
        AutoLimitData['OrderAmt'] = int(do_amt)              #주문 수량 양수면 매수 음수면 매도 
        
        #사야된다
        if do_amt > 0:
            AutoLimitData['TargetAmt'] = stock_amt + abs(AutoLimitData['OrderAmt'])  #최종 목표 수량 (현재수량 + 주문수량)


            try:

                OrderData = KisUS.MakeBuyLimitOrder(stock_code,abs(do_amt),target_price)
                AutoLimitData['OrderNum'] = OrderData["OrderNum"]      #주문아이디1
                AutoLimitData['OrderNum2'] = OrderData["OrderNum2"]    #주문아이디2
                AutoLimitData['OrderTime'] = OrderData["OrderTime"]    #주문시간


            except Exception as e:

                #시간 정보를 읽는다
                time_info = time.gmtime()
                AutoLimitData['OrderNum'] = 0
                AutoLimitData['OrderNum2'] = 0
                AutoLimitData['OrderTime'] = GetNowDateStr(area)  + str(time_info.tm_hour) + str(time_info.tm_min) + str(time_info.tm_sec) 


        #팔아야 된다!
        else:

            AutoLimitData['TargetAmt'] = stock_amt - abs(AutoLimitData['OrderAmt']) #최종 목표 수량 (현재수량 - 주문수량)

            try:
                OrderData = KisUS.MakeSellLimitOrder(stock_code,abs(do_amt),target_price)
                AutoLimitData['OrderNum'] = OrderData["OrderNum"]
                AutoLimitData['OrderNum2'] = OrderData["OrderNum2"]   
                AutoLimitData['OrderTime'] = OrderData["OrderTime"]   

            except Exception as e:

                #시간 정보를 읽는다
                time_info = time.gmtime()
                AutoLimitData['OrderNum'] = 0
                AutoLimitData['OrderNum2'] = 0
                AutoLimitData['OrderTime'] = GetNowDateStr(area)  + str(time_info.tm_hour) + str(time_info.tm_min) + str(time_info.tm_sec) 



        AutoLimitData['IsCancel'] = 'N' #주문 취소 여부
        AutoLimitData['IsDone'] = 'N'   #주문 완료 여부
        AutoLimitData['TryCnt'] = 0    #재주문 숫자 
        AutoLimitData['DelDate'] =  GetFromNowDateStr(area,"NONE",10)    #10일 미래의 날짜 즉 10일 후에는 해당 데이터를 삭제처리할 예정 (어자피 하루만 유효한 주문들이다. 하루 지나고 삭제해도 되지만 참고를 위해 10일간 남겨둔다)
        AutoLimitData['StockType'] = stock_type #stock_type 유형


        #해당 데이터의 ID를 만든다! 여러 항목의 조합으로 고유하도록!  이 아이디를 리턴해 봇에서 줘서 필요한 봇은 이 아이디를 가지고 리스트를 만들어 사용하면 된다!
        AutoLimitData['Id'] = AutoLimitData['NowDist'] + botname + area + str(stock_code) + str(AutoLimitData["OrderNum"]) + str(AutoLimitData["OrderNum2"]) + str(AutoLimitData["OrderTime"]) + str(do_amt) + str(target_price) 
    

        SaveAutoLimitDoAgainData(AutoLimitData)


            

        #등록된 해당 주문 데이터 ID를 리턴한다
        return AutoLimitData['Id']
            
#자동 주문 데이터를 각 봇 파일에 저장을 하는 함수!
def SaveAutoLimitDoAgainData(AutoLimitData):


    #파일 경로입니다.
    auto_order_file_path = MainPath + "json/" + AutoLimitData['Area'] + "_" + AutoLimitData['NowDist'] + "_" + AutoLimitData['BotName'] + "AutoOrderList.json"

    #이렇게 랜덤하게 쉬어줘야 혹시나 있을 중복 파일 접근 방지!
    time.sleep(random.random()*0.1)
    
    #자동 주문 리스트 읽기!
    AutoOrderList = list()
    try:
        with open(auto_order_file_path, 'r') as json_file:
            AutoOrderList = json.load(json_file)
    except Exception as e:
        print("Exception by First")

    #!!!! 넘어온 데이터를 리스트에 추가하고 저장하기!!!!
    AutoOrderList.append(AutoLimitData)
    with open(auto_order_file_path, 'w') as outfile:
        json.dump(AutoOrderList, outfile)





    #봇마다 고유한 경로(자동주문리스트 파일의 경로)를 1개씩 저장해 둔다
    #이를 for문 돌면 전체 모든 봇의 자동주문 리스트에 접근해서 처리할 수 있다
    time.sleep(random.random()*0.1)
    bot_path_file_path = MainPath + "json/BotOrderListPath.json"
    BotOrderPathList = list()
    try:
        with open(bot_path_file_path, 'r') as json_file:
            BotOrderPathList = json.load(json_file)

    except Exception as e:
        print("Exception by First")



    #읽어와서 중복되지 않은 것만 등록한다!
    IsAlreadyIn = False
    for botOrderPath in BotOrderPathList:
        if botOrderPath == auto_order_file_path:
            IsAlreadyIn = True
            break

    #현재 저 파일에 없다면 추가해준다!!
    if IsAlreadyIn == False:
        BotOrderPathList.append(auto_order_file_path)

        with open(bot_path_file_path, 'w') as outfile:
            json.dump(BotOrderPathList, outfile)

#주문 아이디를 받아 해당 주문을 취소하는 로직
def DelAutoLimitOrder(AutoOrderId):

    bot_path_file_path = MainPath + "json/BotOrderListPath.json"

    #각 봇 별로 들어가 있는 자동 주문 리스트!!!
    BotOrderPathList = list()
    try:
        with open(bot_path_file_path, 'r') as json_file:
            BotOrderPathList = json.load(json_file)

    except Exception as e:
        print("Exception by First")

    IsFindOrder = False
    time.sleep(random.random()*0.01)
    #오토 리미트 주문 데이터가 있는 모든 봇을 순회하며 처리한다!!
    for botOrderPath in BotOrderPathList:

        #이 botOrderPath는 각 봇의 고유한 경로 (리미트 오토 주문들이 저장되어 있는 파일 경로)
        print("----->" , botOrderPath)

        AutoOrderList = list()

        try:
            with open(botOrderPath, 'r') as json_file:
                AutoOrderList = json.load(json_file)

        except Exception as e:
            print("Exception by First")



       
        
        #해당 봇의 읽어온 주문 데이터들을 순회합니다.
        for AutoLimitData in AutoOrderList:

            try:

                #해당 주문을 찾았다!!!
                if AutoLimitData['Id'] == AutoOrderId:


                    #해당 주문의 계좌를 바라보도록 셋팅 합니다!!
                    SetChangeMode(AutoLimitData['NowDist']) 

                    ########## 현재 살아있는 주문을 취소!!! #######

                    #내 주식 잔고 리스트를 읽어서 현재 보유 수량 정보를 stock_amt에 넣어요!
                    MyStockList = KisUS.GetMyStockList()
                    if AutoLimitData['Area'] == "KR":
                        MyStockList = KisKR.GetMyStockList()


                    #미체결 수량이 들어갈 변수!
                    GapAmt = 0

                    stock_amt = 0
                    for my_stock in MyStockList:
                        if my_stock['StockCode'] == AutoLimitData['StockCode']:
                            stock_amt = int(my_stock['StockAmt'])
                            print(my_stock['StockName'], stock_amt)
                            break

                    #일단 목표로 하는 수량에서 현재 보유수량을 빼줍니다.
                    #이는 종목의 주문이 1개일 때 유효합니다. 왜 그런지 그리고TargetAmt값이 뭔지는 KIS_Common의 AutoLimitDoAgain함수를 살펴보세요
                    GapAmt = abs(AutoLimitData['TargetAmt'] - stock_amt)

                    Is_Except = False
                    try:

                        #주문리스트를 읽어 온다! 퇴직연금계좌 IRP계좌에서는 이 정보를 못가져와 예외가 발생합니다!!
                        OrderList = KisKR.GetOrderList(AutoLimitData['StockCode'])

                        print(len(OrderList) , " <--- Order OK!!!!!!")
                        
                        #주문 번호를 이용해 해당 주문을 찾습니다!!!
                        for OrderInfo in OrderList:
                            if OrderInfo['OrderNum'] == AutoLimitData['OrderNum'] and float(OrderInfo["OrderNum2"]) == float(AutoLimitData['OrderNum2']):
                                GapAmt = abs(OrderInfo["OrderResultAmt"] - OrderInfo["OrderAmt"])

                                if AutoLimitData['Area'] == "KR":
                                    KisKR.CancelModifyOrder(AutoLimitData['StockCode'],AutoLimitData['OrderNum'],AutoLimitData['OrderNum2'],abs(GapAmt),KisKR.GetCurrentPrice(AutoLimitData['StockCode']),"CANCEL")
                                else:
                                    KisUS.CancelModifyOrder(AutoLimitData['StockCode'],AutoLimitData['OrderNum2'],AutoLimitData['OrderAmt'],KisUS.GetCurrentPrice(AutoLimitData['StockCode']),"CANCEL")
                                        
                                break

                    except Exception as e:
                        #예외 발생!
                        Is_Except = True
                        print("Exception", e)

                    #예외가 발생했다면 
                    if Is_Except == True:
                        try:
                            #취소!
                            if AutoLimitData['Area'] == "KR":
                                KisKR.CancelModifyOrder(AutoLimitData['StockCode'],AutoLimitData['OrderNum'],AutoLimitData['OrderNum2'],abs(GapAmt),KisKR.GetCurrentPrice(AutoLimitData['StockCode']),"CANCEL")
                            else:
                                #미국은 2차 시도! 최초 주문수량으로 취소가 되는지 남은 미체결 수량으로 취소가 되는지 불분명..이렇게 하면 위에서 1번 여기서 1번 취소처리 함으로써 취소가 안된 주문을 확실히 취소 처리 할 수 있다!
                                KisUS.CancelModifyOrder(AutoLimitData['StockCode'],AutoLimitData['OrderNum2'],abs(GapAmt),KisUS.GetCurrentPrice(AutoLimitData['StockCode']),"CANCEL")
                        except Exception as e:
                            print("Exception", e)
       

                    ##########실제로 리스트에서 제거#######
                    AutoOrderList.remove(AutoLimitData)

                    with open(botOrderPath, 'w') as outfile:
                        json.dump(AutoOrderList, outfile)

                    IsFindOrder = True

                    break



            except Exception as e:
                print("Exception by First")

        if IsFindOrder == True:
            break

#해당 봇의 모든 주문데이터를 취소하는 로직!
def AllDelAutoLimitOrder(bot_name):

    bot_path_file_path = MainPath + "json/BotOrderListPath.json"

    #각 봇 별로 들어가 있는 자동 주문 리스트!!!
    BotOrderPathList = list()
    try:
        with open(bot_path_file_path, 'r') as json_file:
            BotOrderPathList = json.load(json_file)

    except Exception as e:
        print("Exception by First")

    IsFindBot = False
    time.sleep(random.random()*0.01)
    #오토 리미트 주문 데이터가 있는 모든 봇을 순회하며 처리한다!!
    for botOrderPath in BotOrderPathList:

        #이 botOrderPath는 각 봇의 고유한 경로 (리미트 오토 주문들이 저장되어 있는 파일 경로)
        print("----->" , botOrderPath)

        AutoOrderList = list()

        try:
            with open(botOrderPath, 'r') as json_file:
                AutoOrderList = json.load(json_file)

        except Exception as e:
            print("Exception by First")


        #해당 봇의 읽어온 주문 데이터들을 순회합니다.
        for AutoLimitData in AutoOrderList:

            if AutoLimitData['BotName'] == bot_name:
                print("DELETE ", bot_name , " ORDER ->" , AutoLimitData['Id'])
                DelAutoLimitOrder(AutoLimitData['Id'])
                IsFindBot = True
        

        if IsFindBot == True:
            break

############################################################################################################################################################

#종가 데이터를 가지고 오는데 신규 상장되서 이전 데이터가 없다면 신규 상장일의 정보를 리턴해준다!
def GetCloseData(df,st):
    
    if len(df) < abs(st):
        return df['close'][-len(df)] 
    else:
        return df['close'][st] 
        
#넘어온 종목 코드 리스트에 해당 종목이 있는지 여부를 체크하는 함수!
def CheckStockCodeInList(stock_code_list,find_code):
    InOk = False
    for stock_code in stock_code_list:
        if stock_code == find_code:
            InOk = True
            break

    return InOk   

############################################################################################################################################################

#이동평균선 수치를 구해준다 첫번째: 일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetMA(ohlcv,period,st=100):
    
    ma = ohlcv.rolling(period).mean()
    
    if st == 100:
        return ma
    else:
        return round(float(ma.iloc[st]),2)

#최고가 계산
def GetMax(ohlcv,period,st=100):
    close = ohlcv["close"]

    if len(close) < period:
        period = len(close)
    mv = close.rolling(window =period).max()

    if st == 100:
        return mv
    else:
        return float(mv.iloc[st])

def GetAllTimeMax(ohlcv,st=100):
    close = ohlcv["close"]
    mv = close.max()
    
    if st == 100:
        return mv
    else:
        return float(mv.iloc[st])
        
#최고가 계산
#def GetHigh(ohlcv,period,st=100):
#    close = ohlcv["high"]
#    mv = close.rolling(window =period).max()
#    
#    if st == 100:
#        return mv
#    else:
#        return float(mv.iloc[st])

# 200일 이동평균 위에 있을 때는 최고가 계산, 밑에 있을 경우 이전 최고값 유지
def GetCloseHigh(ohlcv, period):
    
    close = ohlcv["close"]
    moving_avg = ohlcv["close"].rolling(window=200).mean()  # 200일 이동평균 계산
    mv = close.rolling(window=period).max()  # 주어진 기간 내 최고가 계산
    
    # 새로운 리스트에 최고가 값을 넣을 준비
    high_with_previous = []
    previous_high = None  # 이전 최고값을 저장할 변수

    for i in range(len(mv)):
        if close.iloc[i] > moving_avg.iloc[i]:  # 200일 이동평균 위에 있는 경우
            previous_high = mv.iloc[i]  # 최고가 업데이트
        high_with_previous.append(previous_high)  # 최고가 또는 이전 최고가 저장

    # 시리즈 형태로 변환
    high_with_previous = pd.Series(high_with_previous, index=mv.index)
    
    return high_with_previous

# 200일 이동평균 위에 있을 때는 최고가 계산, 밑에 있을 경우 이전 최고값 유지
def GetHigh(ohlcv, period):
    
    close = ohlcv["high"]
    moving_avg = ohlcv["close"].rolling(window=200).mean()  # 200일 이동평균 계산
    mv = close.rolling(window=period).max()  # 주어진 기간 내 최고가 계산
    
    # 새로운 리스트에 최고가 값을 넣을 준비
    high_with_previous = []
    previous_high = None  # 이전 최고값을 저장할 변수

    for i in range(len(mv)):
        if close.iloc[i] > moving_avg.iloc[i]:  # 200일 이동평균 위에 있는 경우
            previous_high = mv.iloc[i]  # 최고가 업데이트
        high_with_previous.append(previous_high)  # 최고가 또는 이전 최고가 저장

    # 시리즈 형태로 변환
    high_with_previous = pd.Series(high_with_previous, index=mv.index)
    
    return high_with_previous
    
#최저가 계산
def GetMin(ohlcv,period,st=100):
    close = ohlcv["close"]

    if len(close) < period:
        period = len(close)
    mv = close.rolling(window =period).min()

    if st == 100:
        return mv
    else:
        return float(mv.iloc[st])
    
def GetRSIMin(RSI,period,st=100):

    if len(RSI) < period:
        period = len(RSI)
    mv = RSI.rolling(window =period).min()

    if st == 100:
        return mv
    else:
        return float(mv.iloc[st])


#def GetSMA_MOM12(ohlcv,period,st=100):
#    
#    SMA = pd.DataFrame(columns=['SMA200','SMA150','SMA50'],index=ohlcv.index)
#    
#    SMA['SMA200'] = ohlcv["close"].rolling(200).mean()
#    SMA['SMA150'] = ohlcv["close"].rolling(150).mean()
#    SMA['SMA50'] = ohlcv["close"].rolling(50).mean()
#    
#    SMA = SMA.reset_index()
#
#    ## Str to Datetime ##
#    if SMA['Date'].dtype != 'datetime64[ns]':
#        SMA['Date'] = pd.to_datetime(SMA['Date'])
#    else:pass
#
#    SMA = SMA.set_index('Date')
#
#    SMA_col_list = list(SMA.columns)
#    
#    mom_col_list = [col+'_M' for col in SMA_col_list]
#    SMA[mom_col_list] = SMA.apply(lambda x: get_momentum6(x, SMA, SMA_col_list), axis=1)
#    
#    if period == 12:
#        sma_m = SMA["SMA200_M"]  
#    elif period == 6:
#        sma_m = SMA["SMA150_M"]
#    elif period == 3:
#        sma_m = SMA["SMA50_M"]  
#    if st == 100:
#        return SMA["SMA200_M"]
#    else:
#        return float(sma_m.iloc[st])

def GetSMA_MOM12(ohlcv,period,period2,st=100):

    #SMA = pd.DataFrame(columns=['SMA200','SMA150','SMA50'],index=ohlcv.index)
    SMA = pd.DataFrame(index=ohlcv.index)
    SMA['SMA200'] = ohlcv["close"].rolling(200).mean()
    SMA['SMA150'] = ohlcv["close"].rolling(150).mean()
    SMA['SMA20'] = ohlcv["close"].rolling(50).mean()
        
    SMA = SMA.reset_index()
    ## Str to Datetime ##
    if SMA['Date'].dtype != 'datetime64[ns]':
        SMA['Date'] = pd.to_datetime(SMA['Date'])
    else:pass
       
    SMA = SMA.set_index('Date')

    SMA.fillna(0)
    SMA.round(2)
    if period == 200:
        SMA['SMA200_M'] = SMA['SMA200'] / SMA['SMA200'].shift(20*period2) - 1
        SMA['SMA200_RM'] = SMA['SMA200_M'] / SMA['SMA200_M'].mean()

        if st == 100: return SMA['SMA200_M']
        else:         return SMA['SMA200_M'].iloc[st]

    elif period == 150:
        SMA['SMA150_M'] = SMA['SMA150'] / SMA['SMA150'].shift(20*period2) - 1
        SMA['SMA150_RM'] = SMA['SMA150_M'] / SMA['SMA150_M'].mean()

        if st == 100: return SMA['SMA150_M']
        else:         return SMA['SMA150_M'].iloc[st]

    else:
        SMA['SMA20_M'] = SMA['SMA20'] / SMA['SMA20'].shift(20*period2) - 1
        SMA['SMA20_RM'] = SMA['SMA20_M'] / SMA['SMA20_M'].mean()

        if st == 100: return SMA['SMA20_M']
        else:         return SMA['SMA20_M'].iloc[st]

def GetMOM(ohlcv,period,st=100):
    
    MOM = pd.DataFrame(columns=['close'],index=ohlcv.index)
    MOM['close'] = ohlcv["close"]
    MOM = MOM.reset_index()
    
    ## Str to Datetime ##
    if MOM['Date'].dtype != 'datetime64[ns]':
        MOM['Date'] = pd.to_datetime(MOM['Date'])
    else:pass
       
    MOM = MOM.set_index('Date')

    MOM['close_M'] = MOM['close'] / MOM['close'].shift(20*period) - 1
    MOM['close_RM'] = MOM['close_M'] / MOM['close_M'].mean()

    if st == 100: return MOM['close_RM']
    else:         return MOM['close_RM'].iloc[st]

def GetBuyMom(ohlcv,col,period,st=100):
    
    MOM = pd.DataFrame(columns=[col],index=ohlcv.index)
    MOM[col] = ohlcv[col]
    MOM = MOM.reset_index()

    ## Str to Datetime ##
    if MOM['Date'].dtype != 'datetime64[ns]':
        MOM['Date'] = pd.to_datetime(MOM['Date'])
    else:pass
    
    MOM[col+'_' + str(period) + 'MA'] = MOM[col].rolling(period).mean() #20주 이동평균
    MOM[col+'_52MA'] = MOM[col].rolling(52).mean() #20주 이동평균
    MOM[col+'_MOM'] = MOM[col+'_' + str(period) + 'MA'] / MOM[col+'_52MA']
    
    MOM = MOM.set_index('Date')
    
    if st == 100: return MOM[col+'_MOM']
    else:         return MOM[col+'_MOM'].iloc[st]

#1개월 모멘텀
def get_momentum1(x, df_ALL, universe):

    temp_list = [0 for i in range(len(x.index))]
    momentum = pd.Series(temp_list, index=x.index)
    before1 = df_ALL[x.name-timedelta(days=35):x.name-timedelta(days=30)].iloc[-1][universe]

    momentum = round((12 * (x / before1 - 1)),2)
    try:
        before1 = df_ALL[x.name-timedelta(days=35):x.name-timedelta(days=30)].iloc[-1][universe]

        momentum = round((12 * (x / before1 - 1)),2)
    except:
        pass

    return momentum
                
#12개월 모멘텀
def get_momentum12(x, df_ALL, universe):

    temp_list = [0 for i in range(len(x.index))]
    momentum = pd.Series(temp_list, index=x.index)

    try:
        before1 = df_ALL[x.name-timedelta(days=35):x.name-timedelta(days=30)].iloc[-1][universe]
        before3 = df_ALL[x.name-timedelta(days=95):x.name-timedelta(days=90)].iloc[-1][universe]     
        before6 = df_ALL[x.name-timedelta(days=185):x.name-timedelta(days=180)].iloc[-1][universe]        
        before12 = df_ALL[x.name-timedelta(days=370):x.name-timedelta(days=365)].iloc[-1][universe]

        momentum = round((12 * (x / before1 - 1) + 4 * (x / before3 - 1) + 2 * (x / before6 - 1) + (x / before12 - 1)),2)
        #print(momentum)
    except:
        pass
    
    return momentum
#6개월 모멘텀
def get_momentum6(x, df_ALL, universe):

    temp_list = [0 for i in range(len(x.index))]
    momentum = pd.Series(temp_list, index=x.index)

    try:
        before1 = df_ALL[x.name-timedelta(days=35):x.name-timedelta(days=30)].iloc[-1][universe]
        before3 = df_ALL[x.name-timedelta(days=95):x.name-timedelta(days=90)].iloc[-1][universe]     
        before6 = df_ALL[x.name-timedelta(days=185):x.name-timedelta(days=180)].iloc[-1][universe]        

        momentum = round((12 * (x / before1 - 1) + 4 * (x / before3 - 1) + 2 * (x / before6 - 1)),2)
    except:
        pass

    return momentum
#3개월 모멘텀
def get_momentum3(x, df_ALL, universe):

    temp_list = [0 for i in range(len(x.index))]
    momentum = pd.Series(temp_list, index=x.index)

    try:
        before1 = df_ALL[x.name-timedelta(days=35):x.name-timedelta(days=30)].iloc[-1][universe]
        before3 = df_ALL[x.name-timedelta(days=95):x.name-timedelta(days=90)].iloc[-1][universe]        

        momentum = round((12 * (x / before1 - 1) + 4 * (x / before3 - 1)),2)
    except:
        pass

    return momentum

#RS WITH ALL
def get_RS_wMarket(ohlcv,period):
    
    kospi = GetIndexOhlcvPyKrx("1001")
    kosdaq = GetIndexOhlcvPyKrx("2001")
    
    kospi_def = (kospi['close'][-1] - kospi['close'][-period])/kospi['close'][-period]
    kosdaq_def = (kosdaq['close'][-1] - kosdaq['close'][-period])/kosdaq['close'][-period]
    market_def = (kospi_def + kosdaq_def)/2
    ohlcv_def = (ohlcv['close'][-1] - ohlcv['close'][-period])/ohlcv['close'][-period]
    
    rs = round(ohlcv_def / market_def,2)
    
    return float(rs)

#RS WITH KOSDAQ
def get_RS_wKosdaq(ohlcv,period):
    
    kosdaq = GetIndexOhlcvPyKrx("2001")
    
    kosdaq_def = (kosdaq['close'][-1] - kosdaq['close'][-period])/kosdaq['close'][-period]
    ohlcv_def = (ohlcv['close'][-1] - ohlcv['close'][-period])/ohlcv['close'][-period]
    
    rs = round(ohlcv_def / kosdaq_def,2)
    
    return float(rs)

def getRS_Long_ST(ohlcv,st=100,sm=100):
    
    start_date = ohlcv['close'].index[0].strftime("%Y%m%d")
    end_date = GetNowDateStr("KR","NONE")
    #GetFromNowDateStr("KR","NONE",-limit), GetNowDateStr("KR","NONE")

    kosdaq = GetIndexOhlcvPyKrx("2001",start_date,end_date)
    KSD = kosdaq['close']
    OHLCV = ohlcv['close']

    KSD_st = (KSD - KSD.shift(st)) / KSD.shift(st)
    OHLCV_st = (OHLCV - OHLCV.shift(st)) / OHLCV.shift(st)
    RS_st = OHLCV_st / KSD_st
    
    RS_st = RS_st.rolling(sm).mean() # RS SMA150
    
    return RS_st


def getRS_Long(ohlcv,st=100):
    
    start_date = ohlcv['close'].index[0].strftime("%Y%m%d")
    end_date = GetNowDateStr("KR","NONE")
    #GetFromNowDateStr("KR","NONE",-limit), GetNowDateStr("KR","NONE")

    kosdaq = GetIndexOhlcvPyKrx("2001",start_date,end_date)
    KSD = kosdaq['close']
    OHLCV = ohlcv['close']

    KSD_50 = (KSD - KSD.shift(50)) / KSD.shift(50)
    OHLCV_50 = (OHLCV - OHLCV.shift(50)) / OHLCV.shift(50)
    RS_50 = OHLCV_50 / KSD_50

    KSD_100 = (KSD - KSD.shift(100)) / KSD.shift(100)
    OHLCV_100 = (OHLCV - OHLCV.shift(100)) / OHLCV.shift(100)
    RS_100 = OHLCV_100 / KSD_100

    KSD_200 = (KSD - KSD.shift(200)) / KSD.shift(200)
    OHLCV_200 = (OHLCV - OHLCV.shift(200)) / OHLCV.shift(200)
    RS_200 = OHLCV_200 / KSD_200

    RS = (RS_200 + RS_50 + RS_100)/3
    
    RS = RS.rolling(st).mean() # RS SMA150
    
    return RS

def getRS_Row(ohlcv,st=100):
    
    ohlcv_M = ohlcv.resample(rule='M').last()
    df = ohlcv_M['close']
    df['change'] = df.pct_change()

    print(df)

    return ohlcv_M

def getRS_Short(ohlcv,st=100):
    
    start_date = ohlcv['close'].index[0].strftime("%Y%m%d")
    end_date = GetNowDateStr("KR","NONE")
    #GetFromNowDateStr("KR","NONE",-limit), GetNowDateStr("KR","NONE")

    kosdaq = GetIndexOhlcvPyKrx("2001",start_date,end_date)
    KSD = kosdaq['close']
    OHLCV = ohlcv['close']

    KSD_5 = (KSD - KSD.shift(5)) / KSD.shift(5)
    OHLCV_5 = (OHLCV - OHLCV.shift(5)) / OHLCV.shift(5)
    RS_5 = OHLCV_5 / KSD_5

    KSD_10 = (KSD - KSD.shift(10)) / KSD.shift(10)
    OHLCV_10 = (OHLCV - OHLCV.shift(10)) / OHLCV.shift(10)
    RS_10 = OHLCV_10 / KSD_10

    KSD_20 = (KSD - KSD.shift(20)) / KSD.shift(20)
    OHLCV_20 = (OHLCV - OHLCV.shift(20)) / OHLCV.shift(20)
    RS_20 = OHLCV_20 / KSD_20

    RS = (RS_5 + RS_10 + RS_20)/3
    #RS = RS_20
    
    RS = RS.rolling(st).mean() # RS SMA150

    if st == 100: return RS
    else:         return RS.iloc[st]


#ATR
def GetATR(ohlcv,period,st=100):
    high = ohlcv["high"]
    low = ohlcv["low"]
    close = ohlcv["close"].shift(1)
    close = close.fillna(0)
    TR1 = high - low
    TR2 = high - close
    TR3 = low - close
    TR = pd.DataFrame(columns=['TR'],index=TR1.index)
    
    for i in range(len(TR1)):     
        
        if TR1.iloc[i] > TR2.iloc[i] and TR1.iloc[i] > TR3.iloc[i]:
            TR.loc[TR.index[i],'TR'] = TR1.iloc[i]
        elif TR2.iloc[i] > TR1.iloc[i] and TR2.iloc[i] > TR3.iloc[i]:
            TR.loc[TR.index[i],'TR'] = TR2.iloc[i]
        else:
            TR.loc[TR.index[i],'TR'] = TR3.iloc[i]
    
    ATR = TR.rolling(window =period).mean()
    #print(ATR.tail(1))
    if st == 100:
        return round(ATR['TR'],2)
    else:
        return round(float(ATR['TR'].iloc[st]),2)

def GetADR_Pct(ohlcv,period,st=100):
    
    # True Range 계산
    ohlcv['H-L'] = ohlcv['high'] - ohlcv['low']
    ohlcv['H-C'] = abs(ohlcv['high'] - ohlcv['close'].shift(1))
    ohlcv['L-C'] = abs(ohlcv['low'] - ohlcv['close'].shift(1))
    
    ohlcv['True Range'] = ohlcv[['H-L', 'H-C', 'L-C']].max(axis=1)
    
    # ADR(%) 계산 (True Range를 이전 종가로 나누어 백분율로 변환)
    ohlcv['ADR_P'] = (ohlcv['True Range'] / ohlcv['close'].shift(1)) * 100
    
    # 이동 평균을 통해 ADR(%) 계산
    ohlcv['ADR_P'] = ohlcv['ADR_P'].rolling(window=period).mean()
    
    # 불필요한 컬럼 제거
    ohlcv = ohlcv.drop(['H-L', 'H-C', 'L-C'], axis=1)
    
    if st == 100:
        return ohlcv['ADR_P']
    else:
        return ohlcv['ADR_P'][st]

def GetATR(ohlcv, period=14):
    """
    ATR(Average True Range)를 계산하는 함수.
    
    ohlcv: OHLCV 데이터프레임 (열: 'high', 'low', 'close')
    period: ATR을 계산할 기간 (기본값은 14일)
    
    반환값: ATR 값이 추가된 데이터프레임
    """
    
    # True Range(TR) 계산
    ohlcv['high_low'] = ohlcv['high'] - ohlcv['low']  # 현재 고가와 저가의 차이
    ohlcv['high_close_prev'] = np.abs(ohlcv['high'] - ohlcv['close'].shift(1))  # 현재 고가와 이전 종가의 차이
    ohlcv['low_close_prev'] = np.abs(ohlcv['low'] - ohlcv['close'].shift(1))  # 현재 저가와 이전 종가의 차이
    
    # True Range(TR) 값은 세 값 중 가장 큰 값
    ohlcv['TR'] = ohlcv[['high_low', 'high_close_prev', 'low_close_prev']].max(axis=1)
    
    # ATR 계산 (기본적으로 14일 이동 평균)
    ohlcv['ATR'] = ohlcv['TR'].rolling(window=period).mean()
    
    # 불필요한 열 제거 (선택 사항)
    ohlcv.drop(['high_low', 'high_close_prev', 'low_close_prev', 'TR'], axis=1, inplace=True)
    
    return ohlcv

def GetSupperTrend(ohlcv, atr_period=10, multiplier=3):
    # ATR 계산
    data = GetATR(ohlcv, atr_period)
    data = data.ffill()

    # hl2 계산
    data['hl2'] = (data['high'] + data['low']) / 2
    
    # 기본 상한 밴드와 하한 밴드 계산
    data['basic_upperband'] = data['hl2'] + multiplier * data['ATR']
    data['basic_lowerband'] = data['hl2'] - multiplier * data['ATR']
    
    # 상한/하한 밴드 및 슈퍼트렌드 값 초기화
    data['upperband'] = data['basic_upperband']
    data['lowerband'] = data['basic_lowerband']
    data['supertrend'] = np.nan
    data['in_uptrend'] = True  # 트렌드 방향을 저장할 열, 초기값은 True (업트렌드)
    
    # NaN 값이 있는 첫 번째 행의 인덱스 찾기
    first_nan_index = data['basic_upperband'].first_valid_index()

    # 만약 NaN 값이 있다면 그 이전 데이터 삭제
    if first_nan_index is not None:
        data = data.loc[first_nan_index:]
    else:
        data = data.copy()  # NaN 값이 없는 경우 전체 데이터 유지

    # 첫 번째 값 설정
    data.loc[data.index[0], 'supertrend'] = data['basic_lowerband'].iloc[0]
    
    for i in range(1,len(data)):
        current = data.index[i]
                
        # 상한 밴드 업데이트: 기본 상한 밴드가 이전 상한 밴드보다 작거나, 이전 종가가 이전 상한 밴드보다 클 경우 상한 밴드를 업데이트
        if data['basic_upperband'].iloc[i] < data['upperband'].iloc[i-1] or data['close'].iloc[i-1] > data['upperband'].iloc[i-1]:
            data.loc[current, 'upperband'] = data['basic_upperband'].iloc[i]
        else:
            data.loc[current, 'upperband'] = data['upperband'].iloc[i-1]
        
        # 하한 밴드 업데이트: 기본 하한 밴드가 이전 하한 밴드보다 크거나, 이전 종가가 이전 하한 밴드보다 작을 경우 하한 밴드를 업데이트
        if data['basic_lowerband'].iloc[i] > data['lowerband'].iloc[i-1] or data['close'].iloc[i-1] < data['lowerband'].iloc[i-1]:
            data.loc[current, 'lowerband'] = data['basic_lowerband'].iloc[i]
        else:
            data.loc[current, 'lowerband'] = data['lowerband'].iloc[i-1]
        
        # 트렌드 방향 결정
        if data['close'].iloc[i] >= data['upperband'].iloc[i-1]:
            data.loc[current, 'in_uptrend'] = True
        elif data['close'].iloc[i] <= data['lowerband'].iloc[i-1]:
            data.loc[current, 'in_uptrend'] = False
        else:
            data.loc[current, 'in_uptrend'] = data['in_uptrend'].iloc[i-1]
        
        # 슈퍼트렌드 값 설정 (트렌드 방향에 따라 상한 또는 하한 밴드를 사용)
        if data['in_uptrend'].iloc[i]:
            data.loc[current, 'supertrend'] = data['lowerband'].iloc[i]
        else:
            data.loc[current, 'supertrend'] = data['upperband'].iloc[i]
    
    
    # 필요한 열만 반환
    return data[['supertrend', 'lowerband', 'upperband', 'in_uptrend']]

    
def Darvas_box(ohlcv,period,select,st=100):

    ohlcv['HH'] = ohlcv['high'].rolling(window=period).max()
    ohlcv['LL'] = ohlcv['low'].rolling(window=period).min()
    
    ohlcv['NH'] = np.where(ohlcv['high'] > ohlcv['HH'].shift(1), ohlcv['high'], np.nan)
    ohlcv['NL'] = np.where(ohlcv['low'] < ohlcv['LL'].shift(1), ohlcv['low'], np.nan)
    
    ohlcv['BOX1'] = np.where(ohlcv['high'].rolling(window=period-2).max() < ohlcv['high'].rolling(window=period-1).max(), 1, 0)
    
    ohlcv['TOP'] = np.where((ohlcv['high'].diff(period-2) > 0) & (ohlcv['BOX1'] == 1), ohlcv['NH'], np.nan)
    ohlcv['BOTTOM'] = np.where((ohlcv['low'].diff(period-2) < 0) & (ohlcv['BOX1'] == 1), ohlcv['NL'], np.nan)
    
    if st == 100:
        return ohlcv[select]
    else:
        return ohlcv[select][st]

def Donchian_channel(ohlcv, period = 20,select = 'Upper', st=100):
    
    if select == 'Upper':
        ohlcv['Upper'] = ohlcv['high'].rolling(window=period).max().shift()
    elif select == 'Lower':
        ohlcv['Lower'] = ohlcv['low'].rolling(window=period).min().shift()
    else:
        ohlcv['Upper'] = ohlcv['high'].rolling(window=period).max().shift()
        ohlcv['Lower'] = ohlcv['low'].rolling(window=period).min().shift()
        ohlcv['Middle'] = (ohlcv['Upper'] + ohlcv['Lower']) / 2
    
    return ohlcv[select]

def GetMDD(ohlcv,period=100,st=100):
    
    ohlcv.truncate(before=ohlcv.index[period])
    
    ohlcv['MDD'] = (-100)*(ohlcv['close'].rolling(window=period).max() - ohlcv['close'])/ohlcv['close'].rolling(window=period).max()
    
    return ohlcv['MDD']

def ChkCandle(df,st=100):
    # 음봉과 양봉을 판단하는 함수를 정의합니다.
    def is_bull_or_bear(row):
        if row['close'] > row['open']:
            return '+'
        #elif row['Close'] < row['Open']:
        #    return '-'
        else:
            return '-'

    # 각 행에 대해 함수를 적용합니다.
    df['Candle'] = df.apply(is_bull_or_bear, axis=1)
    if st == 100:
        return df['Candle']
    else:
        return df['Candle'].iloc[st]
   
#RSI지표 수치를 구해준다. 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
def GetRSI(ohlcv,period,st=100):
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()

    RS = round(100 - (100 / (1 + _gain / _loss)),2)
    
    if st == 100:
        return RS
    else:
        return RS.iloc[st]
    
def GetStockGain(ohlcv,period):
    
    GAIN = (ohlcv["close"] - ohlcv["close"].shift(period))/ohlcv["close"].shift(period)
    
    return GAIN

def GetBaseLength(ohlcv):
    """
    박스권 길이를 계산하는 함수 (엄격한 동일 고가 기준).
    
    Parameters:
    ohlcv (pd.DataFrame): 'high', 'close' 컬럼 포함

    Returns:
    int: 박스권의 길이 (주 수)
    """
    base_length = 0
    max_high = None

    for i in range(len(ohlcv)):
        high = ohlcv.iloc[i]['1Year_H']
        close = ohlcv.iloc[i]['close']

        if max_high is None:
            max_high = high
            base_length = 1 if close >= high * 0.6 else 0
            continue

        if high > max_high:
            # 고가가 새로 갱신되면 초기화
            max_high = high
            base_length = 1 if close >= high * 0.6 else 0
        elif high == max_high:
            if close >= high * 0.6:
                base_length += 1
            else:
                break  # 종가 조건 위반 시 종료
        else:
            break  # 고가가 낮아져도 종료
            
    return base_length


#볼린저 밴드를 구해준다 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜
#차트와 다소 오차가 있을 수 있습니다.
def GetBB(ohlcv,period,st,uni = 2.0):
    dic_bb = dict()

    ohlcv = ohlcv[::-1]
    ohlcv = ohlcv.shift(st + 1)
    close = ohlcv["close"].iloc[::-1]

    unit = uni
    bb_center=numpy.mean(close[len(close)-period:len(close)])
    band1=unit*numpy.std(close[len(close)-period:len(close)])

    dic_bb['ma'] = round(float(bb_center),2)
    dic_bb['upper'] = round(float(bb_center + band1),2)
    dic_bb['lower'] = round(float(bb_center - band1),2)

    return dic_bb

def BollingerBands(ohlcv, window_size=20, num_of_std=2):
    
    data = ohlcv['close']
    
    # 이동 평균 계산
    rolling_mean = data.rolling(window=window_size).mean()

    # 이동 표준편차 계산
    rolling_std = data.rolling(window=window_size).std().shift()

    # 볼린저 밴드 상한선 계산
    ohlcv['UpperB'] = rolling_mean + (rolling_std * num_of_std)
    bollinger_band_upper = ohlcv['UpperB'].shift()
    
    # 볼린저 밴드 하한선 계산
    ohlcv['LowerB'] = rolling_mean - (rolling_std * num_of_std)
    bollinger_band_lower = ohlcv['LowerB'].shift()
    
    return rolling_mean, bollinger_band_upper, bollinger_band_lower

def BreakSpprtLine(ohlcv,st=100):
    data = ohlcv    
    data['1Year_H'] = GetHigh(data,12*5)  #월봉기준 12 = 1Y / 36 = 3Y
    
    # 데이터를 순회하면서 최대값과 최소값을 업데이트합니다.
    for i in range(len(data)):
        
        if i == 0:
            data.loc[data.index[i],'Break_Line'] = data['1Year_H'].iloc[i]
            data.loc[data.index[i],'Spprt_Line'] = data['low'].iloc[i]
            
            data.loc[data.index[i],'Resistance Broken'] = 0
            data.loc[data.index[i],'Resistance Broken Time'] = 0
            data.loc[data.index[i],'Support Broken'] = 0
            data.loc[data.index[i],'Support Broken Time'] = 0
            
        elif data['high'].iloc[i] >= data['1Year_H'].iloc[i-1]:
            data.loc[data.index[i],'Break_Line'] = data['high'].iloc[i]
            data.loc[data.index[i],'Spprt_Line'] = data['low'].iloc[i]

            data.loc[data.index[i],'Resistance Broken'] = 1
            data.loc[data.index[i],'Resistance Broken Time'] = data['Resistance Broken Time'].iloc[i-1] + 1
            data.loc[data.index[i],'Support Broken'] = 0
            data.loc[data.index[i],'Support Broken Time'] = 0
            
        elif data['low'].iloc[i] < data['Spprt_Line'].iloc[i-1]:
            data.loc[data.index[i],'Break_Line'] = data['1Year_H'].iloc[i-1]
            data.loc[data.index[i],'Spprt_Line'] = data['low'].iloc[i]    
            
            data.loc[data.index[i],'Resistance Broken'] = 0
            data.loc[data.index[i],'Resistance Broken Time'] = 0
            data.loc[data.index[i],'Support Broken'] = 1
            data.loc[data.index[i],'Support Broken Time'] = data['Support Broken Time'].iloc[i-1] + 1
        else:
            data.loc[data.index[i],'Break_Line'] = data['1Year_H'].iloc[i-1]
            data.loc[data.index[i],'Spprt_Line'] = data['Spprt_Line'].iloc[i-1]
            
            data.loc[data.index[i],'Resistance Broken'] = 0
            if data['Resistance Broken Time'].iloc[i-1] != 0:  
                data.loc[data.index[i],'Resistance Broken Time'] = data['Resistance Broken Time'].iloc[i-1] + 1
                
            data.loc[data.index[i],'Support Broken'] = 1
            if data['Support Broken Time'].iloc[i-1] != 0:  
                data.loc[data.index[i],'Support Broken Time'] = data['Support Broken Time'].iloc[i-1] + 1    

            data.loc[data.index[i],'Support Broken'] = 0

    if st == 100:
        return data
    else:
        return data.iloc[st]
    #return data['Break_Line'].iloc[st], data['Spprt_Line'].iloc[st], data['Resistance Broken'].iloc[st], data['Support Broken'].iloc[st], data['Resistance Broken Time'].iloc[st], data['Support Broken Time'].iloc[st]



#일목 균형표의 각 데이타를 리턴한다 첫번째: 분봉/일봉 정보, 두번째: 기준 날짜
def GetIC(ohlcv,st):

    high_prices = ohlcv['high']
    close_prices = ohlcv['close']
    low_prices = ohlcv['low']


    nine_period_high =  ohlcv['high'].shift(-2-st).rolling(window=9).max()
    nine_period_low = ohlcv['low'].shift(-2-st).rolling(window=9).min()
    ohlcv['conversion'] = (nine_period_high + nine_period_low) /2
    
    period26_high = high_prices.shift(-2-st).rolling(window=26).max()
    period26_low = low_prices.shift(-2-st).rolling(window=26).min()
    ohlcv['base'] = (period26_high + period26_low) / 2
    
    ohlcv['sunhang_span_a'] = ((ohlcv['conversion'] + ohlcv['base']) / 2).shift(26)
    
    
    period52_high = high_prices.shift(-2-st).rolling(window=52).max()
    period52_low = low_prices.shift(-2-st).rolling(window=52).min()
    ohlcv['sunhang_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    
    
    ohlcv['huhang_span'] = close_prices.shift(-26)


    nine_period_high_real =  ohlcv['high'].rolling(window=9).max()
    nine_period_low_real = ohlcv['low'].rolling(window=9).min()
    ohlcv['conversion'] = (nine_period_high_real + nine_period_low_real) /2
    
    period26_high_real = high_prices.rolling(window=26).max()
    period26_low_real = low_prices.rolling(window=26).min()
    ohlcv['base'] = (period26_high_real + period26_low_real) / 2
    


    
    dic_ic = dict()

    dic_ic['conversion'] = ohlcv['conversion'].iloc[st]
    dic_ic['base'] = ohlcv['base'].iloc[st]
    dic_ic['huhang_span'] = ohlcv['huhang_span'].iloc[-27]
    dic_ic['sunhang_span_a'] = ohlcv['sunhang_span_a'].iloc[-1]
    dic_ic['sunhang_span_b'] = ohlcv['sunhang_span_b'].iloc[-1]


  

    return dic_ic




#MACD의 12,26,9 각 데이타를 리턴한다 첫번째: 분봉/일봉 정보, 두번째: 기준 날짜
def GetMACD(ohlcv,st):
    macd_short, macd_long, macd_signal=12,26,9

    ohlcv["MACD_short"]=ohlcv["close"].ewm(span=macd_short).mean()
    ohlcv["MACD_long"]=ohlcv["close"].ewm(span=macd_long).mean()
    ohlcv["MACD"]=ohlcv["MACD_short"] - ohlcv["MACD_long"]
    ohlcv["MACD_signal"]=ohlcv["MACD"].ewm(span=macd_signal).mean() 

    dic_macd = dict()
    
    dic_macd['macd'] = ohlcv["MACD"].iloc[st]
    dic_macd['macd_siginal'] = ohlcv["MACD_signal"].iloc[st]
    dic_macd['ocl'] = dic_macd['macd'] - dic_macd['macd_siginal']

    return dic_macd
#스토캐스틱 %K %D 값을 구해준다 첫번째: 분봉/일봉 정보, 두번째: 기간, 세번째: 기준 날짜

def GetStoch(ohlcv,period,st):

    dic_stoch = dict()

    ndays_high = ohlcv['high'].rolling(window=period, min_periods=1).max()
    ndays_low = ohlcv['low'].rolling(window=period, min_periods=1).min()
    fast_k = (ohlcv['close'] - ndays_low)/(ndays_high - ndays_low)*100
    slow_d = fast_k.rolling(window=3, min_periods=1).mean()

    dic_stoch['fast_k'] = fast_k.iloc[st]
    dic_stoch['slow_d'] = slow_d.iloc[st]

    return dic_stoch

def GetSectorName(stock_code,type = 'Small'):

    file_name = MainPath + 'Excel/QuantData.xlsx'

    df = pd.read_excel(file_name,header= 0,index_col='코드',dtype=str,na_values ='NaN')
    
    CodeName = "A"+stock_code
    for stock in df.index:
        
        if stock == CodeName:
            
            if type == "Small":
                GetSector = df['업종소'].loc[stock]
            else:
                GetSector = df['업종대'].loc[stock]

    return GetSector

def GetSectorRSVal(stock_code,RSType = "S", RSLength = 4):

    from DataBase.CalMongoDB import MongoDB as DB

    renamed_stock = "A"+str(stock_code)

    #// 데이터베이스 정보를 가져온다
    str_database_name = 'KrDataBase_RS'
    
    df = DB.ExecuteSql(str_database_name, renamed_stock)
    #print(df)
    if RSType == "S":
        if RSLength == 4:
            ReturnRS = df['Sec_S_RS_4W']
        else:
            ReturnRS = df['Sec_S_RS_52W']
    else: #"B"
        if RSLength == 4:
            ReturnRS = df['Sec_B_RS_4W']
        else:
            ReturnRS = df['Sec_B_RS_52W']
    return ReturnRS

def GetStockRSVal(stock_code,RSLength = 4):

    from DataBase.CalMongoDB import MongoDB as DB
    
    renamed_stock = "A"+str(stock_code)

    #// 데이터베이스 정보를 가져온다
    str_database_name = 'KrDataBase_RS'
    
    df = DB.ExecuteSql(str_database_name, renamed_stock)
    #print(df)

    if RSLength == 4:
        ReturnRS = df['RS_4W']
    else:
        ReturnRS = df['RS_52W']

    return ReturnRS

def is_dst(dt):
    """
    주어진 datetime(dt)이 DST(일광 절약 시간제) 기간에 속하는지 확인합니다.
    미국은 3월 둘째 일요일부터 11월 첫째 일요일(종료일 미포함)까지 DST를 적용합니다.
    """
    year = dt.year

    # 3월 첫날로부터 3월 첫 번째 일요일 구하기
    march_first = datetime(year, 3, 1)
    first_sunday_offset = (6 - march_first.weekday()) % 7  # weekday(): 월=0, 일=6
    first_sunday = march_first + timedelta(days=first_sunday_offset)
    # 3월 둘째 일요일은 첫 번째 일요일에 7일 더한 날
    second_sunday = first_sunday + timedelta(days=7)

    # 11월 첫날로부터 11월 첫 번째 일요일 구하기
    nov_first = datetime(year, 11, 1)
    first_sunday_nov_offset = (6 - nov_first.weekday()) % 7
    first_sunday_nov = nov_first + timedelta(days=first_sunday_nov_offset)

    # DST: 3월 둘째 일요일(포함)부터 11월 첫째 일요일(미포함)까지
    return second_sunday.date() <= dt.date() < first_sunday_nov.date()
