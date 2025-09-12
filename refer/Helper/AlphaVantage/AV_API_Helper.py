import Helper.KIS.KIS_Common as Common
#from Helper.KIS.KIS_Make_StockList import CallStockList #Temp
import requests
import json
import pprint
import time
import yaml
import pandas as pd
import operator
import pytz
import csv
import requests

from Main.Path import MainPath
from datetime import datetime, timedelta, date
from pytz import timezone

from alpha_vantage.fundamentaldata import FundamentalData

def GetTicker(Market='NASDAQ', Type='Stock', Active = True):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    if Active == True:
        CSV_URL = 'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=' + KEY
    else:
        CSV_URL = 'https://www.alphavantage.co/query?function=LISTING_STATUS&state=delisted&apikey=' + KEY

    with requests.Session() as s:
        download = s.get(CSV_URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        ticker_dict = {}
        for row in my_list:
            ticker_dict[row[0]] = {
            "Company Name": row[1],
            "Market": row[2],
            "Type": row[3],
            "Listing Date": row[4],
            "Delisting Date": row[5],
            "Activate": row[6]
            }

        # 결과 출력
        #for ticker, info in ticker_dict.items():
        #    print(f"{ticker}: {info}")

        # market list = 'NYSE MKT', 'exchange', 'NYSE', 'NYSE ARCA', 'NASDAQ', 'BATS'

        ticker_list = [ticker for ticker, info in ticker_dict.items() 
                        if info["Market"] == Market and info["Type"] == Type]

        #nasdaq_active_ticker_info = {ticker: info for ticker, info in ticker_dict.items() 
        #                     if info["Market"] == Market and info["Type"] != Type}
    
    return ticker_list

def GetOhlcvMin_Bender(stock_code, interval, outputsize, start_date='None'):

    from alpha_vantage.timeseries import TimeSeries
    import pandas as pd

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]
    
    extended_hours = 'false'
    # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='+stock_code+'&interval='+interval+'&extended_hours=' + extended_hours +'&outputsize='+outputsize+'&apikey='+KEY

    r = requests.get(url)   
    data = r.json()
    period = f'Time Series ({interval})'
    
    df = pd.DataFrame(data[period]).T
    df.index = pd.to_datetime(df.index)
    df = df.apply(pd.to_numeric)
    df.index.name = 'Datetime'

    # 데이터 출력
    chosend_fld = ['1. open', '2. high', '3. low', '4. close', '5. volume']
    renamed_fld = ['open', 'high', 'low', 'close', 'volume']
    
    df = df[chosend_fld]
    ren_dict = dict()

    i = 0
    for x in chosend_fld:
        ren_dict[x] = renamed_fld[i]
        i += 1

    df.rename(columns = ren_dict, inplace=True)

    df.sort_values(by='Datetime', ascending=True, inplace = True)
    listtemp = [ 'open', 'high', 'low', 'close', 'volume']
    df[listtemp] = df[listtemp].apply(pd.to_numeric)
    if start_date != 'None':
        df = df[df.index >= pd.to_datetime(start_date)]
    local_tz = pytz.timezone('America/New_York')
    #fixed_est = pytz.FixedOffset(-300)
                        
    # 3. 인덱스에 고정된 UTC-5 시간대 적용
    df.index = df.index.tz_localize(local_tz)
                        
    # UTC로 변환
    df.index = [dt.astimezone(pytz.UTC) for dt in df.index]
    df.index = df.index.tz_convert('UTC')
    df.index.name = 'Datetime'

    time.sleep(0.1)   
                     
    return df

#당일 분봉 구하기 - alpha ventage
def GetOhlcv_Bender(stock_code, outputsize, start_date='None'):

    from alpha_vantage.timeseries import TimeSeries
    import pandas as pd

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]


    # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol='+stock_code+'&outputsize='+outputsize+'&apikey='+KEY
    r = requests.get(url)   
    data = r.json()
    
    df = pd.DataFrame(data['Time Series (Daily)']).T
    df.index = pd.to_datetime(df.index)
    df = df.apply(pd.to_numeric)

    #df.reset_index(inplace=True)

    # 데이터 출력
    chosend_fld = ['1. open', '2. high', '3. low', '4. close', '5. adjusted close', '6. volume', '7. dividend amount', '8. split coefficient']
    renamed_fld = ['open', 'high', 'low', 'close', 'adjusted close', 'volume', 'divamt', 'splitfac']
    
    df = df[chosend_fld]
    ren_dict = dict()
#
    i = 0
    for x in chosend_fld:
        ren_dict[x] = renamed_fld[i]
        i += 1
#
    df.rename(columns = ren_dict, inplace=True)
    #df.set_index('Datetime', inplace=True)

    # 각 날짜별 수정계수 계산
    df['dividend_factor'] = (df['close'] - df['divamt']) / df['close']
    df['split_factor'] = 1.0 / df['splitfac']
    df['adfac'] = df['split_factor'] #df['dividend_factor'] * df['split_factor']
    df.drop(columns=['divamt', 'splitfac', 'adjusted close'],inplace=True)
    df.index.name = 'Date'
    df.index = pd.to_datetime(df.index)

    if start_date != 'None':
        df = df[df.index >= pd.to_datetime(start_date.date())]

    df.sort_values(by='Date', ascending=True, inplace = True)

    return df

def CallUsFndmData(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    try:
        Capital = int(data['MarketCapitalization'])
        EPS_Growth_YOY = float(data['QuarterlyEarningsGrowthYOY'])
        REV_Growth_YOY = float(data['QuarterlyRevenueGrowthYOY'])
        #print(Capital, EPS_Growth_YOY, REV_Growth_YOY)
        time.sleep(1)

        if Capital >= 1000000000 and Capital < 10000000000 and EPS_Growth_YOY > 0 and REV_Growth_YOY > 0:
            result = True
        else:
            result = False
    except:
        #print(data['MarketCapitalization'], data['QuarterlyEarningsGrowthYOY'], data['QuarterlyRevenueGrowthYOY'])
        result = False
        
    return result

def CallUsEarningData(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=EARNINGS&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    
    Qdata = data['quarterlyEarnings']
    
    df = pd.DataFrame(Qdata)
    
    Filltered_Col = ['fiscalDateEnding','reportedDate', 'reportedEPS', 'estimatedEPS', 'surprisePercentage']
    df = df[Filltered_Col]
    df.rename(columns={'fiscalDateEnding':'Date','reportedDate': 'EarningDate', 'reportedEPS': 'eps', 'surprisePercentage': 'eps_sup', 'estimatedEPS':'eps_guidence'}, inplace=True)
    df[['Date']] = df[['Date']].apply(pd.to_datetime) 
    df.set_index('Date', inplace=True)

    #df[['EPS','EPS_Sup','EPS_Guid']] = df[['EPS','EPS_Sup','EPS_Guid']].ffill()
    #df[['EPS','EPS_Sup','EPS_Guid']] = df[['EPS','EPS_Sup','EPS_Guid']].astype(float)

    df['eps'] = df['eps'].astype(float)
    # 변환 함수 정의
    df[['eps_sup', 'eps_guidence']] = df[['eps_sup', 'eps_guidence']].apply(lambda col: col.map(lambda x: 0 if x == 'None' else float(x)))

    df = df.sort_index(ascending=True)
    
    #df['eps_qoq'] = df.apply(lambda row: calculate_qoq(row['eps'], df['eps'].shift(1).loc[row.name]), axis=1)
    #df['eps_yoy'] = df.apply(lambda row: calculate_yoy(row['eps'], df['eps'].shift(4).loc[row.name]), axis=1)
    ## EPS 증가율을 새로운 열에 계산
    #df['eps_growth_QoQ'] = df['eps'].pct_change().apply(lambda x: x * 100 if pd.notnull(x) else 0)
    #
    #for i in range(1, len(df)):
    #    current_eps = df.iloc[i]['eps']
    #    previous_eps = df.iloc[i-1]['eps']
    #
    #    if (current_eps > 0 and previous_eps < 0) or (current_eps < 0 and previous_eps > 0):
    #        df.iloc[i, df.columns.get_loc('eps_growth_QoQ')] = calculate_eps_growth(current_eps, previous_eps)
    #
    #df[['eps_sup', 'eps_qoq', 'eps_yoy']] = df[['eps_sup', 'eps_qoq', 'eps_yoy']].round(2)
    df[['eps_sup']] = df[['eps_sup']].round(2)
    df = df.fillna(0)
    time.sleep(1)
    return df

def calculate_qoq(current_eps, previous_eps):

    if isinstance(previous_eps, pd.Series):
        previous_eps = previous_eps.iloc[0] if not previous_eps.empty else 0

    if previous_eps == 0:
        if current_eps == 0:
            return 0
        else:
            return current_eps * 100
    else:
        return (current_eps - previous_eps) / abs(previous_eps) * 100

def calculate_yoy(current_eps, year_ago_eps):
    # year_ago_eps가 시리즈일 경우 단일 값을 추출
    if isinstance(year_ago_eps, pd.Series):
        year_ago_eps = year_ago_eps.iloc[0] if not year_ago_eps.empty else None

    if pd.notnull(year_ago_eps):
        return calculate_qoq(current_eps, year_ago_eps)
    else:
        return None

def CallUsEarnCalendar(stock, df_return = False):

    import csv
    import requests

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    CSV_URL = 'https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month' + '&apikey=' + KEY

    Universe_NAS = CallStockList("US", "NAS")
    Universe_NYS = CallStockList("US", "NYS")
    Universe = Universe_NAS + Universe_NYS

    df=pd.DataFrame(columns=["EarningDate_1", "EarningDate_2"], index=Universe)

    try:
        with requests.Session() as s:
            download = s.get(CSV_URL)
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            my_list = list(cr)

            df = pd.DataFrame(my_list)
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)
            df.set_index('symbol',inplace=True)

            df_filtered = df[df['currency'] == 'USD'].copy()
            # Convert 'reportDate' to datetime to enable proper comparison
            df_filtered['reportDate'] = pd.to_datetime(df_filtered['reportDate'])
            result = df_filtered.loc[stock]
            # Print or use the filtered DataFrame

            if isinstance(result, pd.DataFrame):
                result = result.sort_values(by='reportDate', ascending=True)
                EarningDate =  result.iloc[0]['reportDate']
            else:
                EarningDate =  result['reportDate']
            
            time.sleep(1)

            if df_return == True:
                return EarningDate
            else:
                if EarningDate > datetime.now() + timedelta(days=5):
                    return True
                else:
                    return False
    except:
        return False
            
def FindMarketFromCode(stocks):

    NyseStockList = list()

    #파일 경로입니다.
    us_file_path = MainPath + "json/NyseStockCodeList.json"

    #파일에 리스트를 저장합니다
    with open(us_file_path, 'r') as json_file:
        NyseStockList = json.load(json_file)
    
    NasdaqStockList = list()

    #파일 경로입니다.
    us_file_path = MainPath + "json/NasdaqStockCodeList.json"

    #파일에 리스트를 저장합니다
    with open(us_file_path, 'r') as json_file:
        NasdaqStockList = json.load(json_file)

    #파일 경로입니다.
    us_file_path = MainPath + "json/AmexStockCodeList.json"

    #파일에 리스트를 저장합니다
    with open(us_file_path, 'r') as json_file:
        AmexStockList = json.load(json_file)
        
    if stocks in NyseStockList:
        return 'NYS'
    elif stocks in NasdaqStockList:
        return 'NAS'
    elif stocks in AmexStockList:
        return 'AMX'
    else:
        return 'None'
    
def CallUsRevenueData(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]
    # Alpha Vantage API 키 입력
    api_key = KEY  # 여기에 본인의 API 키를 입력하세요

    # FundamentalData 객체 초기화
    fd = FundamentalData(key=api_key, output_format='pandas')

    # 분기별 손익계산서 데이터 가져오기
    income_statement, _ = fd.get_income_statement_quarterly(symbol=stocks)
    
    # 필요한 열 선택 및 데이터 정렬
    income_statement = income_statement[['fiscalDateEnding', 'totalRevenue']]
    income_statement['fiscalDateEnding'] = pd.to_datetime(income_statement['fiscalDateEnding'])
    income_statement.sort_values(by='fiscalDateEnding', inplace=True, ascending=True)
 
    try:
        # 'totalRevenue' 열을 숫자 형식으로 변환 (문자열에서 콤마 제거 후 변환)
        income_statement['totalRevenue'] = income_statement['totalRevenue'].replace(',', '', regex=True).astype(float)
    except:
        # 예외 발생 시, 문자열을 NaN으로 변환하고, 이후 NaN을 0으로 대체
        income_statement['totalRevenue'] = pd.to_numeric(income_statement['totalRevenue'], errors='coerce').fillna(0)

    income_statement = income_statement.reset_index(drop=True)
    
    # 연간 및 분기별 시계열 데이터프레임 생성
    income_statement.rename(columns={'fiscalDateEnding': 'Date', 'totalRevenue': 'revenue', 'RevenueGrowthPct': 'rev_yoy',}, inplace=True)

    income_statement.set_index('Date', inplace=True)
    df = income_statement.sort_index(ascending=True)
    time.sleep(1)

    return df

def CallUsIncomeStatment(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
        
    api_key = stock_info["ALPHA_VENTAGE_API_KEY"]    

    url = 'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=' + stocks + '&apikey=' + api_key
    r = requests.get(url)
    data = r.json()
    #'earningsPerShare' (리스트에 없으므로 추가 확인 필요)

    df = pd.DataFrame(data['quarterlyReports'])
    
    Filltered_Col = \
        ['fiscalDateEnding','grossProfit','totalRevenue','operatingIncome','depreciationAndAmortization','ebitda','netIncome']
    
    df = df[Filltered_Col]
    df.rename(columns={'fiscalDateEnding':'Date'}, inplace=True)
    df.set_index('Date',inplace=True)
    df.index = pd.to_datetime(df.index)
    
    numeric_Col = \
        ['grossProfit','totalRevenue','operatingIncome','depreciationAndAmortization','ebitda','netIncome']
        
    df['ebitda'] = pd.to_numeric(df['ebitda'], errors='coerce').ffill()
    df['totalRevenue'] = pd.to_numeric(df['totalRevenue'], errors='coerce').ffill()
    df['netIncome'] = pd.to_numeric(df['netIncome'], errors='coerce').ffill()
    df['grossProfit'] = pd.to_numeric(df['grossProfit'], errors='coerce').ffill()
    df['operatingIncome'] = pd.to_numeric(df['operatingIncome'], errors='coerce').ffill()
    df['depreciationAndAmortization'] = pd.to_numeric(df['depreciationAndAmortization'], errors='coerce').ffill()

    #df[numeric_Col] = pd.to_numeric(df[numeric_Col], errors='coerce').fillna(0)
    #df[numeric_Col] = df[numeric_Col].apply(pd.to_numeric)
    time.sleep(1.0)

    return df

def CallUsBalanceSheet(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
        
    api_key = stock_info["ALPHA_VENTAGE_API_KEY"]    

    url = 'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=' + stocks + '&apikey=' + api_key
    r = requests.get(url)
    data = r.json()
    
    df = pd.DataFrame(data['quarterlyReports'])
        
    Filltered_Col = \
        ['fiscalDateEnding','totalAssets','cashAndCashEquivalentsAtCarryingValue','totalLiabilities','totalShareholderEquity','commonStockSharesOutstanding','longTermDebt','shortTermDebt','commonStock','retainedEarnings']

    df = df[Filltered_Col]
    df.rename(columns={'fiscalDateEnding':'Date'}, inplace=True)
    df.set_index('Date',inplace=True)
    df.index = pd.to_datetime(df.index)
    
    numeric_Col = \
        ['totalAssets','cashAndCashEquivalentsAtCarryingValue','totalLiabilities','totalShareholderEquity','commonStockSharesOutstanding','longTermDebt','shortTermDebt','commonStock','retainedEarnings']

    # 필요한 열을 숫자 형식으로 변환 및 NaN 값을 ffill()로 이전 데이터로 채우기
    df['totalShareholderEquity'] = pd.to_numeric(df['totalShareholderEquity'], errors='coerce').ffill()
    df['commonStockSharesOutstanding'] = pd.to_numeric(df['commonStockSharesOutstanding'], errors='coerce').ffill()
    df['shortTermDebt'] = pd.to_numeric(df['shortTermDebt'], errors='coerce').ffill()
    df['longTermDebt'] = pd.to_numeric(df['longTermDebt'], errors='coerce').ffill()
    df['cashAndCashEquivalentsAtCarryingValue'] = pd.to_numeric(df['cashAndCashEquivalentsAtCarryingValue'], errors='coerce').ffill()
    df['totalLiabilities'] = pd.to_numeric(df['totalLiabilities'], errors='coerce').ffill()
    df['totalAssets'] = pd.to_numeric(df['totalAssets'], errors='coerce').ffill()
    df['commonStock'] = pd.to_numeric(df['commonStock'], errors='coerce').ffill()
    df['retainedEarnings'] = pd.to_numeric(df['retainedEarnings'], errors='coerce').ffill()
              
    #df[numeric_Col] = pd.to_numeric(df[numeric_Col], errors='coerce').fillna(0)
    #df[numeric_Col] = df[numeric_Col].apply(pd.to_numeric)
    time.sleep(1.0)

    return df

def CallUsStockName(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    print(data)    
    return data['Name']

def CallUsStockInfo(stocks, Type):
    
    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    
    if Type == 'Full':
        return pd.DataFrame([data])
    else:    
        return data[Type]

def CallUsEtfInfo(stocks, Type):
    
    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=ETF_PROFILE&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    
    if Type == 'Full':
        return pd.DataFrame([data])
    else:    
        return data[Type]

def CallUsStockDetailedFdmt(stocks):

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    series = pd.Series(data)

    Filltered_Col = \
        ['Symbol','Exchange','Sector','Industry','FiscalYearEnd','MarketCapitalization','EBITDA','PERatio',
         'PEGRatio','BookValue','DividendPerShare','DividendYield','EPS','ProfitMargin','OperatingMarginTTM',
         'ReturnOnAssetsTTM','ReturnOnEquityTTM','RevenueTTM','GrossProfitTTM','DilutedEPSTTM',
         'QuarterlyEarningsGrowthYOY', 'QuarterlyRevenueGrowthYOY', 'AnalystTargetPrice', 
         'AnalystRatingStrongBuy', 'AnalystRatingBuy', 'AnalystRatingHold', 'AnalystRatingSell',
         'AnalystRatingStrongSell', 'TrailingPE', 'ForwardPE', 'PriceToSalesRatioTTM', 'PriceToBookRatio',
         'EVToRevenue', 'EVToEBITDA', 'Beta']
        
    series = series[Filltered_Col]
    
    series.rename({'PERatio': 'PER', 'PEGRatio': 'PEG', 'PriceToBookRatio': 'PBR','ReturnOnAssetsTTM': 'ROA','ReturnOnEquityTTM': 'ROE', 'PriceToSalesRatioTTM': 'PSR',
                   'QuarterlyEarningsGrowthYOY': 'EpsYoY','QuarterlyRevenueGrowthYOY': 'RevYoY'
                   }, inplace=True)
    
    score = (float(series['AnalystRatingStrongBuy'])*4 + float(series['AnalystRatingBuy'])*2 + float(series['AnalystRatingHold']) - float(series['AnalystRatingSell'])*2 - float(series['AnalystRatingStrongSell'])*4)
    analyst_cnt = (float(series['AnalystRatingStrongBuy']) + float(series['AnalystRatingBuy']) + float(series['AnalystRatingHold']) + float(series['AnalystRatingSell']) + float(series['AnalystRatingStrongSell']))
    
    series['AnalystRating'] = round(score / analyst_cnt,2)

    series.drop(['AnalystRatingStrongBuy','AnalystRatingBuy','AnalystRatingHold','AnalystRatingSell','AnalystRatingStrongSell'], inplace=True)
        
    return series

def ChkUsFndmDataUpdate(stocks, RequestType = 'LatestUpdate'):

    # RequestType #
    # 1. LatestUpdate
    # 2. AnalystRating
    # 3. MarketCapital

    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]

    url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + stocks + '&apikey=' + KEY
    r = requests.get(url)
    data = r.json()

    try:
        if RequestType == 'LatestUpdate':

            LatestQuarter = data['LatestQuarter']
            result = datetime.strptime(LatestQuarter, '%Y-%m-%d')
            result = result.date()
            time.sleep(1)

        elif RequestType == 'AnalystRating':
            
            score = (float(data['AnalystRatingStrongBuy'])*4 + float(data['AnalystRatingBuy'])*2 + float(data['AnalystRatingHold']) - float(data['AnalystRatingSell'])*2 - float(data['AnalystRatingStrongSell'])*4)
            analyst_cnt = (float(data['AnalystRatingStrongBuy']) + float(data['AnalystRatingBuy']) + float(data['AnalystRatingHold']) + float(data['AnalystRatingSell']) + float(data['AnalystRatingStrongSell']))
    
            result = round(score / analyst_cnt,2)
            time.sleep(1)

        elif RequestType == 'MarketCapital':

            result = float(data['AnalystRaMarketCapitalizationtingStrongBuy'])

        else:
            ValueError("Request Type miss defined")
            result = False

    except:
        ValueError("Response Failed..")
        result = False
        
    return result

def GetExchangeRate(FROM,TO):
    
    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]
    
    url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=' + FROM + '&to_currency=' + TO + '&apikey=' + KEY
    r = requests.get(url)
    ExchangeRate = r.json()

    return ExchangeRate['Realtime Currency Exchange Rate']['5. Exchange Rate']

def ChkMarketOpen(Market, Return_Type = 'Status', Return_UTC = False):
    
    with open(MainPath + 'Main/myStockInfo.yaml', encoding='UTF-8') as f:
        stock_info = yaml.load(f, Loader=yaml.FullLoader)
    KEY = stock_info["ALPHA_VENTAGE_API_KEY"]
    
    # 지역별 타임존 매핑 (필요에 따라 수정)
    tz_mapping = {
        "United States": "America/New_York",
        "Canada": "America/Toronto",
        "United Kingdom": "Europe/London",
        "Germany": "Europe/Berlin",
        "France": "Europe/Paris",
        "Spain": "Europe/Madrid",
        "Portugal": "Europe/Lisbon",
        "Japan": "Asia/Tokyo",
        "India": "Asia/Kolkata",
        "Mainland China": "Asia/Shanghai",
        "Hong Kong": "Asia/Hong_Kong",
        "Brazil": "America/Sao_Paulo",
        "Mexico": "America/Mexico_City",
        "South Africa": "Africa/Johannesburg",
        # 그 외의 경우 기본값으로 UTC 사용
    }
    
    if Market == 'US':
        Market_Inp = "United States"
    elif Market == 'HK':
        Market_Inp = "Hong Kong"
    elif Market == 'JP':
        Market_Inp = "Japan"
                
    # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
    url = 'https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=' + KEY
    r = requests.get(url)
    data = r.json()
    data['markets']
    
    for market in data.get("markets", []):
        if market.get("region") == Market_Inp:
            if Return_Type == 'Status':
                return market.get("current_status")
            elif Return_Type == 'Close':
                # 예시에서는 'Open' 요청 시 local_close(거래 마감 시간)를 UTC로 변환
                local_time_str = market.get("local_close")
            elif Return_Type == 'Open':
                # 'Close' 요청 시 local_open(거래 시작 시간)을 UTC로 변환
                local_time_str = market.get("local_open")
            elif Return_Type == 'All':
                return market
            else:
                return None

            # 로컬 시간 문자열 (예: "16:15")을 datetime 객체로 변환
            # 날짜 정보가 없으므로 오늘 날짜를 사용합니다.
            try:
                local_time = datetime.strptime(local_time_str, "%H:%M")
            except (TypeError, ValueError):
                return None  # 시간 문자열이 올바르지 않을 경우
            
            today = date.today()
            # 오늘 날짜와 시간 정보를 결합
            local_dt = datetime.combine(today, local_time.time())
            
            # 해당 지역의 타임존 정보 가져오기. 매핑에 없으면 기본 UTC 사용.
            tz_local = pytz.timezone(tz_mapping.get(Market_Inp, "UTC"))
            local_dt = tz_local.localize(local_dt)
            
            # UTC로 변환
            utc_dt = local_dt.astimezone(pytz.utc)
            
            # 원하는 포맷(예: "HH:MM")으로 변환하여 반환
            if Return_UTC == False:
                return local_dt
            else:
                return utc_dt
    return None
