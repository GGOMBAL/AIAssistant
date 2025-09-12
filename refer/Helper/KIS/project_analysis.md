# Technical Analysis Report for Stock Auto-Trading System based on KIS API

## 1. Project Overview

This project is a comprehensive automated stock trading system utilizing the Korea Investment & Securities (KIS) API. It supports both Korean and US stock markets and can be operated with various account types (real, mock, retirement pension accounts).

### Key Features
- **Multi-Account Support**: Integrated management of real, mock, and retirement pension accounts.
- **Bi-national Market Support**: Multi-national stock markets including Korea (KOSPI/KOSDAQ), the US (NYSE/NASDAQ/AMEX), and Hong Kong.
- **Automated Order System**: Limit/market orders, continuous orders, smart limit orders.
- **Market Analysis**: Calculation of technical indicators, Relative Strength (RS) analysis, fundamental analysis.
- **Risk Management**: Automatic stop-loss, split buy/sell, portfolio rebalancing.

## 2. File Roles

- **`KIS_API_Helper_KR.py`**: API helper class dedicated to the Korean stock market. Provides all functions related to Korean stocks, such as orders, balance inquiry, price inquiry, and ETF analysis.
- **`KIS_API_Helper_US.py`**: API helper class dedicated to the US stock market. Provides features for overseas stock orders, exchange rate processing, and multi-exchange support.
- **`KIS_AutoLimit_System.py`**: Automated order management system. Implements tracking of open orders, re-ordering logic, and time-based order strategies.
- **`KIS_Common.py`**: Common functions module. A core library for account management, token processing, technical indicator calculation, and data analysis functions.
- **`KIS_Make_StockList.py`**: Stock list creation and management. Collects and classifies stock codes through the KIS API and external data sources.
- **`KIS_Make_Token.py`**: Automatic API token renewal system. Manages daily token re-issuance and multi-account tokens.
- **`KIS_Make_TradingData.py`**: Trading data generation engine. Creates comprehensive analysis data including technical indicators, relative strength, and momentum.
- **`KIS_Make_TradingData_KR.py`**: Trading data processor dedicated to Korean stocks.
- **`KIS_Make_TradingData_US.py`**: Trading data processor dedicated to US stocks.

## 3. Function and Class Specification

### `KIS_API_Helper_KR.py`

- **Function: `IsMarketOpen() -> bool`**
  - **Role**: Checks in real-time if the Korean stock market is open and verifies the actual tradable status through a dummy order.
  - **Inputs**: None
  - **Outputs**: (bool) Whether the market is open.

- **Function: `PriceAdjust(price, stock_code) -> int`**
  - **Role**: Adjusts a given price to the tick size of the corresponding stock to convert it into a valid order price.
  - **Inputs**:
    - `price` (float): The original price to adjust.
    - `stock_code` (str): The stock code.
  - **Outputs**: (int) The price adjusted to the tick size.

- **Function: `GetBalance() -> dict`**
  - **Role**: Queries the entire balance information of the account and returns stock valuation, cash balance, total assets, etc.
  - **Inputs**: None
  - **Outputs**: (dict) A dictionary with balance information (StockMoney, RemainMoney, TotalMoney, StockRevenue).

- **Function: `GetMyStockList() -> list`**
  - **Role**: Queries the list of currently held stocks and the detailed information for each stock.
  - **Inputs**: None
  - **Outputs**: (list) A list of held stock information.

- **Function: `GetCurrentPrice(stock_code) -> int`**
  - **Role**: Queries the real-time current price of a specified stock.
  - **Inputs**:
    - `stock_code` (str): The stock code.
  - **Outputs**: (int) The current stock price.

- **Function: `MakeBuyLimitOrder(stockcode, amt, price, adjustAmt=False) -> dict`**
  - **Role**: Executes a limit buy order and, based on an option, automatically adjusts to the purchasable quantity.
  - **Inputs**:
    - `stockcode` (str): The stock code.
    - `amt` (int): The order quantity.
    - `price` (float): The limit price.
    - `adjustAmt` (bool): Whether to automatically adjust the quantity to the maximum possible.
  - **Outputs**: (dict) Order result information.

- **Function: `MakeSellLimitOrder(stockcode, amt, price) -> dict`**
  - **Role**: Executes a limit sell order.
  - **Inputs**:
    - `stockcode` (str): The stock code.
    - `amt` (int): The order quantity.
    - `price` (float): The limit price.
  - **Outputs**: (dict) Order result information.

- **Function: `GetOrderList(stockcode="", side="ALL", status="ALL", limit=5) -> list`**
  - **Role**: Queries order history, allowing filtering by stock, buy/sell side, execution status, etc.
  - **Inputs**:
    - `stockcode` (str): Stock code to filter by.
    - `side` (str): Buy/sell side ("ALL", "BUY", "SELL").
    - `status` (str): Order status ("ALL", "OPEN", "CLOSE").
    - `limit` (int): Day limit for the query.
  - **Outputs**: (list) A list of order history.

- **Function: `GetETF_Nav(stock_code) -> float`**
  - **Role**: Queries the NAV (Net Asset Value) of an ETF through Naver crawling and pykrx.
  - **Inputs**:
    - `stock_code` (str): The ETF stock code.
  - **Outputs**: (float) The NAV value.

### `KIS_API_Helper_US.py`

- **Function: `IsMarketOpen() -> bool`**
  - **Role**: Checks if the US stock market is open and verifies the actual tradable status, considering holidays, etc.
  - **Inputs**: None
  - **Outputs**: (bool) Whether the market is open.

- **Function: `GetBalance(st="USD") -> dict`**
  - **Role**: Queries the balance of an overseas stock account in USD or KRW.
  - **Inputs**:
    - `st` (str): Currency unit ("USD" or "KRW").
  - **Outputs**: (dict) A dictionary with balance information.

- **Function: `GetCurrentPrice(stock_code) -> float`**
  - **Role**: Queries the current price of a stock by sequentially searching NASDAQ, NYSE, and AMEX.
  - **Inputs**:
    - `stock_code` (str): The stock code.
  - **Outputs**: (float) The current stock price.

- **Function: `MakeBuyLimitOrder(stockcode, amt, price, adjustAmt=False) -> dict`**
  - **Role**: Executes a limit buy order for an overseas stock.
  - **Inputs**:
    - `stockcode` (str): The stock code.
    - `amt` (int): The order quantity.
    - `price` (float): The limit price.
    - `adjustAmt` (bool): Whether to automatically adjust the quantity to the maximum possible.
  - **Outputs**: (dict) Order result information.

- **Function: `GetMarketCodeUS(stock_code) -> str`**
  - **Role**: Automatically detects the exchange where the stock is traded using its code.
  - **Inputs**:
    - `stock_code` (str): The stock code.
  - **Outputs**: (str) The exchange code ("NAS", "NYS", "AMS", "HKS", etc.).

### `KIS_Common.py`

- **Function: `SetChangeMode(dist="KJM_ISA") -> None`**
  - **Role**: Switches the currently used account to change the target for API calls.
  - **Inputs**:
    - `dist` (str): The account identifier code.
  - **Outputs**: None

- **Function: `GetToken(dist="KJM_ISA") -> str`**
  - **Role**: Reads the API token for the specified account from a file or creates a new one.
  - **Inputs**:
    - `dist` (str): The account identifier code.
  - **Outputs**: (str) The API token.

- **Function: `GetOhlcv(area, stock_code, limit=500) -> DataFrame`**
  - **Role**: Provides combined OHLCV data for stocks by region using KIS API, FinanceDataReader, Yahoo Finance, etc.
  - **Inputs**:
    - `area` (str): Area code ("KR", "US").
    - `stock_code` (str): The stock code.
    - `limit` (int): The number of data points to query.
  - **Outputs**: (DataFrame) The OHLCV dataframe.

- **Function: `AutoLimitDoAgain(botname, area, stock_code, target_price, do_amt, stock_type="NORMAL") -> str`**
  - **Role**: Registers an order in the automatic continuous order system to manage it persistently until execution.
  - **Inputs**:
    - `botname` (str): The bot's name.
    - `area` (str): The area code.
    - `stock_code` (str): The stock code.
    - `target_price` (float): The target price.
    - `do_amt` (int): The order quantity (positive: buy, negative: sell).
    - `stock_type` (str): The order type ("NORMAL", "TARGET_FIX", "DAY_END", etc.).
  - **Outputs**: (str) The order ID.

- **Function: `GetMA(ohlcv, period, st=100) -> float`**
  - **Role**: Calculates the Moving Average value.
  - **Inputs**:
    - `ohlcv` (DataFrame): The OHLCV data.
    - `period` (int): The moving average period.
    - `st` (int): The reference date index.
  - **Outputs**: (float) The moving average value.

- **Function: `GetRSI(ohlcv, period, st=100) -> float`**
  - **Role**: Calculates the RSI (Relative Strength Index) value.
  - **Inputs**:
    - `ohlcv` (DataFrame): The OHLCV data.
    - `period` (int): The RSI calculation period.
    - `st` (int): The reference date index.
  - **Outputs**: (float) The RSI value.

### `KIS_AutoLimit_System.py`

- **Function: `AutoLimit_System() -> None`**
  - **Role**: The main execution function of the automated order management system. It checks the status of all registered auto-orders and re-orders if necessary.
  - **Inputs**: None
  - **Outputs**: None

## 4. Project Call Tree

### Main Execution Flow
- `AutoLimit_System()` (Entry point for the auto-order system)
  - `-> KisKR.IsMarketOpen()` (Check if Korean market is open)
  - `-> KisUS.IsMarketOpen()` (Check if US market is open)