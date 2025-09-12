import Helper.KIS.KIS_Common as Common
import yfinance as yf
import pandas as pd

from datetime import datetime, timedelta
import time

def GetOhlcv(stock_code, p_code, start_date, end_date, ohlcv = "Y"):

    time.sleep(1.0)

    stock = yf.Ticker(stock_code)
    interval = '1wk' if p_code == 'W' else '1d'
    auto_adjust = True if ohlcv == "Y" else False

    stock = yf.Ticker(stock_code)
    
    start_date_naive = start_date.replace(tzinfo=None)
    end_date_naive = end_date.replace(tzinfo=None)
                        
    if end_date_naive - start_date_naive > timedelta(days=365):
        df = stock.history(period = 'max', interval=interval,auto_adjust=auto_adjust)
    else:
        df = stock.history(interval=interval, start=start_date, end=end_date, auto_adjust=auto_adjust)

    df = df.round(4)
    if ohlcv == "Y":
        df.rename(columns={'Open': 'ad_open', 'High': 'ad_high', 'Low': 'ad_low', 'Close':'ad_close','Volume':'volume','Dividends':'dividend_factor', 'Stock Splits':'split_factor'}, inplace=True)
    else:
        df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close':'close','Volume':'volume','Dividends':'dividend_factor', 'Stock Splits':'split_factor'}, inplace=True)

    df.index = df.index.tz_convert('UTC')
    df.index = df.index.tz_localize(None)

    return df

def get_asset_info(ticker, type = 'quoteType'):
    
    try:
        info = yf.Ticker(ticker).info
        
        asset_type = info.get("quoteType", "Unknown")  # 'ETF' or 'EQUITY'
        exchange = info.get("exchange", "Unknown")     # 'NMS', 'AMEX', 'NYSE' 등

        # 거래소 이름 매핑 (yfinance 약어 → 실제 이름)
        exchange_map = {
            "NMS": "NASDAQ",
            "NYQ": "NYSE",
            "ASE": "AMEX",
            "ARCX": "NYSE ARCA",
            "BATS": "BATS",
        }

        exchange_full = exchange_map.get(exchange, exchange)

        if type == 'exchange':
            return exchange_full
        else:
            return "ETF" if asset_type == "ETF" else "Stock" if asset_type == "EQUITY" else asset_type

    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}
    
def get_fx_rate(pair: str, period: str = "1d", interval: str = "1d"):
    """
    환율 조회 함수
    :param pair: 환율 심볼 (예: "USDKRW=X", "HKDKRW=X")
    :param period: 조회 기간 (기본 "1d" = 오늘 하루)
    :param interval: 데이터 간격 (기본 "1d" = 하루 단위)
    :return: DataFrame 형태의 환율 히스토리
    """
    # Ticker 객체 생성
    fx = yf.Ticker(pair)
    # 히스토리 데이터 가져오기
    hist = fx.history(period=period, interval=interval)
    return hist