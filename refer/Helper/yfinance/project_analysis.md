# Project Technical Analysis Document

## 1. Project Overview

This project is a utility module for collecting and processing financial data from the US stock market. It utilizes the Yahoo Finance API (yfinance) to provide functions for querying OHLCV (Open, High, Low, Close, Volume) data for stocks and ETFs, checking asset information, and fetching exchange rate data.

The core architecture is a single module structure, where each function is responsible for a specific financial data query feature. This module is used as part of a larger financial data analysis system and works in conjunction with the KIS (Korea Investment & Securities) helper module.

## 2. File Roles

- `YF_API_Helper_US.py`: The core helper module for querying US stock market data. It is responsible for querying stock price data, asset information, and exchange rate information via the Yahoo Finance API and returning it in a standardized format.

## 3. Function and Class Specification

### `YF_API_Helper_US.py`

- **Function: `GetOhlcv(stock_code, p_code, start_date, end_date, ohlcv="Y") -> pandas.DataFrame`**
  - **Role**: Queries and processes OHLCV data from Yahoo Finance for a specified stock code and period, then returns it.
  - **Inputs**:
    - `stock_code` (str): The ticker symbol of the stock to query.
    - `p_code` (str): Period code ('W' for weekly, others for daily).
    - `start_date` (datetime): Query start date.
    - `end_date` (datetime): Query end date.
    - `ohlcv` (str): Whether to use adjusted prices ('Y' for adjusted, 'N' for original).
  - **Outputs**: (pandas.DataFrame) A dataframe with the date as the index, containing OHLCV and dividend/split information.

- **Function: `get_asset_info(ticker, type="quoteType") -> str`**
  - **Role**: Queries and returns the asset type (stock/ETF) or exchange information for a given ticker.
  - **Inputs**:
    - `ticker` (str): The ticker symbol of the asset to query.
    - `type` (str): The type of information to return ('quoteType' for asset type, 'exchange' for exchange information).
  - **Outputs**: (str) Asset type ('ETF', 'Stock', etc.) or exchange name ('NASDAQ', 'NYSE', etc.).

- **Function: `get_fx_rate(pair, period="1d", interval="1d") -> pandas.DataFrame`**
  - **Role**: Queries exchange rate information for a specified currency pair and returns it as historical data.
  - **Inputs**:
    - `pair` (str): Exchange rate symbol (e.g., "USDKRW=X", "HKDKRW=X").
    - `period` (str): Query period (default: "1d").
    - `interval` (str): Data interval (default: "1d").
  - **Outputs**: (pandas.DataFrame) A dataframe containing historical exchange rate data.

## 4. Project Call Tree

This project mainly consists of API functions called from external sources, so the internal call relationships are simple:

- `GetOhlcv` (Independent execution)
  - `-> yf.Ticker()` (external library)
  - `-> stock.history()` (external library)
  - `-> df.round()` (pandas method)
  - `-> df.rename()` (pandas method)
  - `-> df.index.tz_convert()` (pandas method)
  - `-> df.index.tz_localize()` (pandas method)

- `get_asset_info` (Independent execution)
  - `-> yf.Ticker()` (external library)
  - `-> ticker.info` (external library attribute)

- `get_fx_rate` (Independent execution)
  - `-> yf.Ticker()` (external library)
  - `-> fx.history()` (external library)

Each function runs independently, primarily calling methods from the yfinance and pandas libraries to process data.