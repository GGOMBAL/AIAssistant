# Project Technical Analysis Document

## 1. Project Overview

This project is a **US stock data collection and analysis system using the Alpha Vantage API**. Key features include real-time stock price data collection, corporate financial information inquiry, earnings calendar checking, and market status monitoring. The system is composed of a single file and collects various data from US stock markets such as NASDAQ, NYSE, and AMEX through the Alpha Vantage API, providing it processed in the form of a pandas DataFrame.

## 2. File Roles

- `AV_API_Helper.py`: The core module responsible for communication with the Alpha Vantage API, including all functions such as stock data collection, financial information inquiry, and market status checking.

## 3. Function and Class Specification

### `AV_API_Helper.py`

- **Function: `GetTicker(Market='NASDAQ', Type='Stock', Active=True) -> list`**
  - **Role**: Queries the list of active/inactive stock tickers from a specific market.
  - **Inputs**:
    - `Market` (str): The market to query ('NASDAQ', 'NYSE', 'NYSE MKT', 'NYSE ARCA', 'BATS').
    - `Type` (str): The security type ('Stock', 'ETF', etc.).
    - `Active` (bool): Whether the stock is active (True: active, False: inactive).
  - **Outputs**: (list) A list of ticker symbols matching the criteria.

- **Function: `GetOhlcvMin_Bender(stock_code, interval, outputsize, start_date='None') -> DataFrame`**
  - **Role**: Queries minute-level OHLCV data for a specific stock and converts it to the UTC timezone.
  - **Inputs**:
    - `stock_code` (str): The stock ticker symbol.
    - `interval` (str): The time interval ('1min', '5min', '15min', '30min', '60min').
    - `outputsize` (str): The data size ('compact', 'full').
    - `start_date` (str): The start date (default: 'None').
  - **Outputs**: (DataFrame) OHLCV data in the UTC timezone.

- **Function: `GetOhlcv_Bender(stock_code, outputsize, start_date='None') -> DataFrame`**
  - **Role**: Queries daily bar data for a specific stock and includes an adjustment factor for calculating adjusted prices.
  - **Inputs**:
    - `stock_code` (str): The stock ticker symbol.
    - `outputsize` (str): The data size ('compact', 'full').
    - `start_date` (str): The start date (default: 'None').
  - **Outputs**: (DataFrame) Daily bar data and adjustment factor.

- **Function: `CallUsFndmData(stocks) -> bool`**
  - **Role**: Checks the fundamental analysis data of a stock to determine if it meets investment criteria.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (bool) Whether the investment criteria are met.

- **Function: `CallUsEarningData(stocks) -> DataFrame`**
  - **Role**: Queries quarterly earnings data to provide EPS, guidance, and surprise information.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (DataFrame) Quarterly earnings data.

- **Function: `calculate_qoq(current_eps, previous_eps) -> float`**
  - **Role**: Calculates the Quarter-over-Quarter (QoQ) EPS growth rate.
  - **Inputs**:
    - `current_eps` (float): The current quarter's EPS.
    - `previous_eps` (float): The previous quarter's EPS.
  - **Outputs**: (float) The QoQ growth rate (%).

- **Function: `calculate_yoy(current_eps, year_ago_eps) -> float`**
  - **Role**: Calculates the Year-over-Year (YoY) EPS growth rate.
  - **Inputs**:
    - `current_eps` (float): The current quarter's EPS.
    - `year_ago_eps` (float): The EPS from the same quarter last year.
  - **Outputs**: (float) The YoY growth rate (%).

- **Function: `CallUsEarnCalendar(stock, df_return=False) -> bool or datetime`**
  - **Role**: Queries the earnings calendar within 3 months to check the earnings announcement schedule.
  - **Inputs**:
    - `stock` (str): The stock ticker symbol.
    - `df_return` (bool): Selects the return type (default: False).
  - **Outputs**: (bool or datetime) Earnings schedule information or whether criteria are met.

- **Function: `FindMarketFromCode(stocks) -> str`**
  - **Role**: Finds the market to which a stock belongs based on its ticker symbol.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (str) The market code ('NYS', 'NAS', 'AMX', 'None').

- **Function: `CallUsRevenueData(stocks) -> DataFrame`**
  - **Role**: Queries quarterly revenue data.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (DataFrame) Quarterly revenue data.

- **Function: `CallUsIncomeStatment(stocks) -> DataFrame`**
  - **Role**: Queries quarterly income statement data.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (DataFrame) Income statement data.

- **Function: `CallUsBalanceSheet(stocks) -> DataFrame`**
  - **Role**: Queries quarterly balance sheet data.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (DataFrame) Balance sheet data.

- **Function: `CallUsStockName(stocks) -> str`**
  - **Role**: Queries the company name corresponding to a stock ticker.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (str) The company name.

- **Function: `CallUsStockInfo(stocks, Type) -> DataFrame or str`**
  - **Role**: Queries basic information about a stock.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
    - `Type` (str): The information type ('Full' or a specific field name).
  - **Outputs**: (DataFrame or str) All information or a specific field value.

- **Function: `CallUsEtfInfo(stocks, Type) -> DataFrame or str`**
  - **Role**: Queries basic information about an ETF.
  - **Inputs**:
    - `stocks` (str): The ETF ticker symbol.
    - `Type` (str): The information type ('Full' or a specific field name).
  - **Outputs**: (DataFrame or str) All information or a specific field value.

- **Function: `CallUsStockDetailedFdmt(stocks) -> Series`**
  - **Role**: Queries detailed fundamental data and analyst ratings for a stock.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
  - **Outputs**: (Series) Detailed fundamental data.

- **Function: `ChkUsFndmDataUpdate(stocks, RequestType='LatestUpdate') -> date or float or bool`**
  - **Role**: Checks the latest update information for fundamental data.
  - **Inputs**:
    - `stocks` (str): The stock ticker symbol.
    - `RequestType` (str): The request type ('LatestUpdate', 'AnalystRating', 'MarketCapital').
  - **Outputs**: (date or float or bool) The result according to the request type.

- **Function: `GetExchangeRate(FROM, TO) -> str`**
  - **Role**: Queries the real-time exchange rate between two currencies.
  - **Inputs**:
    - `FROM` (str): The base currency code.
    - `TO` (str): The target currency code.
  - **Outputs**: (str) The exchange rate information.

- **Function: `ChkMarketOpen(Market, Return_Type='Status', Return_UTC=False) -> str or datetime or dict`**
  - **Role**: Checks the open/close status and time information for a specific market.
  - **Inputs**:
    - `Market` (str): The market code ('US', 'HK', 'JP').
    - `Return_Type` (str): The return type ('Status', 'Close', 'Open', 'All').
    - `Return_UTC` (bool): Whether to return in UTC timezone.
  - **Outputs**: (str or datetime or dict) Market status or time information.

## 4. Project Call Tree

```
Main Application
├── GetTicker()
│   └── requests.get() → CSV parsing → ticker filtering
├── GetOhlcvMin_Bender()
│   └── requests.get() → JSON parsing → DataFrame conversion → timezone conversion
├── GetOhlcv_Bender()
│   └── requests.get() → JSON parsing → DataFrame conversion → adjustment factor calculation
├── CallUsFndmData()
│   └── requests.get() → JSON parsing → condition validation
├── CallUsEarningData()
│   └── requests.get() → JSON parsing → DataFrame conversion
├── CallUsEarnCalendar()
│   └── requests.get() → CSV parsing → date filtering
├── FindMarketFromCode()
│   └── json.load() → market code lookup
├── CallUsRevenueData()
│   └── FundamentalData.get_income_statement_quarterly() → DataFrame processing
├── CallUsIncomeStatment()
│   └── requests.get() → JSON parsing → DataFrame conversion
├── CallUsBalanceSheet()
│   └── requests.get() → JSON parsing → DataFrame conversion
├── CallUsStockName()
│   └── requests.get() → JSON parsing → name extraction
├── CallUsStockInfo()
│   └── requests.get() → JSON parsing → data formatting
├── CallUsEtfInfo()
│   └── requests.get() → JSON parsing → data formatting
├── CallUsStockDetailedFdmt()
│   └── requests.get() → JSON parsing → analyst rating calculation
├── ChkUsFndmDataUpdate()
│   └── requests.get() → JSON parsing → conditional processing
├── GetExchangeRate()
│   └── requests.get() → JSON parsing → exchange rate extraction
└── ChkMarketOpen()
    └── requests.get() → JSON parsing → timezone conversion
```