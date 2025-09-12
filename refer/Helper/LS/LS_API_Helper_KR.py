import Helper.KIS.KIS_Common as Common
import requests
import json

from datetime import datetime, timedelta
from pytz import timezone

import pprint
import time
import pytz

import pandas as pd

from pykrx import stock
import Helper.LS.LS_Common as LScommon

    
def GetLsOhlcvMin(stock_code,start_date,end_date,period):

    if period == 0:
        
        
        duration = end_date - start_date
        print(duration.days)
        start_date = start_date.strftime('%Y%m%d')
        end_date = end_date.strftime('%Y%m%d')
        
        time.sleep(0.2)

        PATH = "stock/chart"
        URL = f"{LScommon.GetUrlBase(LScommon.GetNowDist())}/{PATH}"
         
        for i in range(duration.days):
            
            if i == 0:
                inp_tr_cont = "N"
                inp_cts_date = ""
                inp_cts_time = ""
                inp_tr_cont_key = ""
                inp_start_date = ""
                inp_end_date = "999999"
                time.sleep(1)
            else:
                inp_tr_cont = "Y"
                inp_cts_date = cts_date
                inp_cts_time = cts_time
                inp_tr_cont_key = tr_cont_key
                inp_start_date = ""
                inp_end_date = ""    
                time.sleep(1)            

            # 헤더 설정
            headers = {"Content-Type":"application/json; charset=UTF-8", 
                   "authorization": f"Bearer {LScommon.GetToken(LScommon.GetNowDist())}",
                   #"appkey":LScommon.GetAppKey(LScommon.GetNowDist()),
                   #"appsecretkey":LScommon.GetAppSecret(LScommon.GetNowDist()),
                   "tr_cd":"t8412",
                   "tr_cont":inp_tr_cont,
                   "tr_cont_key":inp_tr_cont_key
                   }
            
            body = {"t8412InBlock" : {
                "shcode" : stock_code,
                "ncnt" : 1,
                "qrycnt" : 500,
                "nday" : "0",
                "sdate" : start_date,
                "stime" : "",
                "edate" : end_date,
                "etime" : "",
                "cts_date" : inp_cts_date,
                "cts_time" : inp_cts_time,
                "comp_yn" : "N"
                }
            }
           
                # 호출
            res = requests.post(URL, headers=headers, json=body)
            tr_cont_key = res.headers['tr_cont_key']
            cts_date = res.json()['t8412OutBlock']['cts_date']
            cts_time = res.json()['t8412OutBlock']['cts_time'] 
            #print(f" 호출횟수 : {i} Code : {res.status_code} | - cts_date : {cts_date}, cts_time : {cts_time}")
            Result = res.json()['t8412OutBlock']
            
            if res.status_code == 200:

                ResultList = res.json()['t8412OutBlock1']
                df = list()

                if len(pd.DataFrame(ResultList)) > 0:
                    OhlcvList = list()

                    for ohlcv in ResultList:
                        if len(ohlcv) == 0:
                            continue
                        OhlcvData = dict()
                        try:

                            OhlcvData['date'] = ohlcv['date']
                            OhlcvData['time'] = ohlcv['time']
                            OhlcvData['open'] = float(ohlcv['open'])
                            OhlcvData['high'] = float(ohlcv['high'])
                            OhlcvData['low'] = float(ohlcv['low'])
                            OhlcvData['close'] = float(ohlcv['close'])
                            OhlcvData['volume'] = float(ohlcv['jdiff_vol'])

                            OhlcvList.append(OhlcvData)

                        except Exception as e:
                            print("E:", e)

                    if len(OhlcvList) > 0:
                        df = pd.DataFrame(OhlcvList)
                        df['Datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                        df = df.set_index('Datetime')
                        df.drop(columns=['date', 'time'], inplace=True)
                        df = df.sort_values(by="Datetime")
                        listtemp = [ 'open', 'high', 'low', 'close', 'volume']
                        df[listtemp] = df[listtemp].apply(pd.to_numeric)

                #return df
            else:
                print("Error Code : " + str(res.status_code) + " | " + res.text)
            
            
            if i == 0:
                df_ALL = df
            else:
                df_ALL = pd.concat([df_ALL,df])
        return df_ALL        
            
    else:
        difference_in_days = (end_date - start_date).days

        for i in range(difference_in_days):
            
            changed_start_date = start_date + timedelta(days=i+1)
            changed_start_date = changed_start_date.strftime('%Y%m%d')
            
            time.sleep(1)
            
            PATH = "stock/chart"
            URL = f"{LScommon.GetUrlBase(LScommon.GetNowDist())}/{PATH}"

            # 헤더 설정
            headers = {"Content-Type":"application/json; charset=UTF-8", 
                       "authorization": f"Bearer {LScommon.GetToken(LScommon.GetNowDist())}",
                       "appkey":LScommon.GetAppKey(LScommon.GetNowDist()),
                       "appsecretkey":LScommon.GetAppSecret(LScommon.GetNowDist()),
                       "tr_cd":"t8412",
                       "tr_cont":"N"
                       }

            body = {"t8412InBlock" : {
                "shcode" : stock_code,
                "ncnt" : 1,
                "qrycnt" : 500,
                "nday" : "1",
                "sdate" : changed_start_date,
                "stime" : "",
                "edate" : changed_start_date,
                "etime" : "",
                "cts_date" : "",
                "cts_time" : "",
                "comp_yn" : "N"
                }
            }

            # 호출
            res = requests.post(URL, headers=headers, json=body)

            if res.status_code == 200:

                ResultList = res.json()['t8412OutBlock1']

                df = list()

                if len(pd.DataFrame(ResultList)) > 0:

                    OhlcvList = list()


                    for ohlcv in ResultList:

                        if len(ohlcv) == 0:
                            continue

                        OhlcvData = dict()

                        try:

                            OhlcvData['date'] = ohlcv['date']
                            OhlcvData['time'] = ohlcv['time']
                            OhlcvData['open'] = float(ohlcv['open'])
                            OhlcvData['high'] = float(ohlcv['high'])
                            OhlcvData['low'] = float(ohlcv['low'])
                            OhlcvData['close'] = float(ohlcv['close'])
                            OhlcvData['volume'] = float(ohlcv['jdiff_vol'])

                            OhlcvList.append(OhlcvData)

                        except Exception as e:
                            print("E:", e)

                    if len(OhlcvList) > 0:

                        df = pd.DataFrame(OhlcvList)
                        df['Datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                        df = df.set_index('Datetime')
                        df.drop(columns=['date', 'time'], inplace=True)
                        df = df.sort_values(by="Datetime")

                        listtemp = [ 'open', 'high', 'low', 'close', 'volume']
                        df[listtemp] = df[listtemp].apply(pd.to_numeric)

                    #print(df)
                if i == 0:
                    df_ALL = df
                else:
                    df_ALL = pd.concat([df_ALL,df], axis=0)
                
            else:
                print("Error Code : " + str(res.status_code) + " | " + res.text)
                return res.json()["msg_cd"]
        
        return df_ALL
