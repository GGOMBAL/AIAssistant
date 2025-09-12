# Technical Analysis Document

## 1. Project Overview

This is a comprehensive quantitative trading system designed for backtesting and executing stock trading strategies across multiple markets (US and KR). The system integrates with MongoDB for data storage, implements multiple trading strategies, and provides visualization capabilities. The architecture follows a modular design with separate components for data access, strategy execution, trading simulation, and plotting.

The core functionality includes:
- Multi-market data retrieval from MongoDB databases
- Strategy execution with configurable parameters
- Backtesting engine with portfolio management
- Risk management and position sizing
- Trade execution simulation with slippage and loss cuts
- Performance visualization and reporting

## 2. File Roles

- `TestMain.py`: Main orchestration module that handles data retrieval from MongoDB, strategy execution, and coordinates the overall workflow
- `TestMakePlot.py`: Visualization module responsible for creating candlestick charts and plotting trading signals and performance metrics
- `TestMakTrade_D.py`: Trading simulation engine that executes backtesting, manages portfolio positions, and tracks trading performance
- `__init__.py`: Package initialization file (empty)

## 3. Function and Class Specification

### `TestMain.py`
- **Class: `Test`**
  - **Role**: Main controller class that orchestrates data loading, strategy execution, and result compilation
  - **Method: `__init__`**
    - **Role**: Initialize the test environment and execute the complete workflow
    - **Inputs**:
      - `Universe` (list): List of stock symbols to analyze
      - `Market` (str): Market type identifier
      - `area` (str): Geographic region ('US' or 'KR')
      - `start_day` (datetime): Start date for analysis
      - `end_day` (datetime): End date for analysis
      - `StrategyName` (str): Strategy identifier ('A', 'B', or 'A+B')
      - `Type` (str): Execution type ('Trading', 'Backtest', or 'Plot')
    - **Outputs**: None (initializes instance variables)
  - **Method: `RoadDataFromDB`**
    - **Role**: Retrieve and process data from MongoDB databases
    - **Inputs**: None (uses instance variables)
    - **Outputs**: None (populates instance DataFrames)
  - **Method: `RunStrategy`**
    - **Role**: Execute the specified trading strategy on the loaded data
    - **Inputs**: None (uses instance variables)
    - **Outputs**: None (populates df and Universe instance variables)
  - **Method: `ReturnFunc`**
    - **Role**: Return processed data and universe for external use
    - **Inputs**: None
    - **Outputs**: (tuple) Returns df (dict) and Universe (list)
  - **Method: `ReturnStockState`**
    - **Role**: Retrieve specific stock data for a given code
    - **Inputs**:
      - `code` (str): Stock symbol to retrieve
    - **Outputs**: (DataFrame or int) Stock data or 0 if not found

### `TestMakePlot.py`
- **Class: `TMakPlot`**
  - **Role**: Handle plotting configuration and initialization
  - **Method: `__init__`**
    - **Role**: Initialize plotting parameters and data
    - **Inputs**:
      - `Universe` (list): List of stock symbols
      - `df_Comb` (dict): Combined DataFrame dictionary
    - **Outputs**: None (sets instance variables)

- **Function: `PlotSingleStocks(PlotStockCode, df) -> None`**
  - **Role**: Create candlestick charts for individual stocks with trading signals
  - **Inputs**:
    - `PlotStockCode` (str): Stock symbol to plot
    - `df` (dict): Dictionary containing stock data
  - **Outputs**: None (displays matplotlib plot)

- **Function: `PlotStocknBalance(self, PlotStockCode) -> None`**
  - **Role**: Create candlestick charts with buy/sell signals for balance analysis
  - **Inputs**:
    - `PlotStockCode` (str): Stock symbol to plot
  - **Outputs**: None (displays matplotlib plot)

### `TestMakTrade_D.py`
- **Class: `TestTradeD`**
  - **Role**: Execute trading simulation with portfolio management and risk controls
  - **Method: `__init__`**
    - **Role**: Initialize trading parameters and prepare data structures
    - **Inputs**:
      - `Universe` (list): List of stock symbols
      - `Market` (str): Market identifier
      - `Area` (str): Geographic region
      - `df` (dict): Stock data dictionary
      - `risk` (float): Risk tolerance parameter
      - `MaxStockCnt` (int): Maximum number of stocks in portfolio
      - `TimeFrame` (str): Time frame for analysis
    - **Outputs**: None (initializes trading environment)
  - **Method: `trade_stocks`**
    - **Role**: Execute the main trading simulation loop
    - **Inputs**:
      - `trading_df` (DataFrame): Trading data with MultiIndex columns
      - `result_df` (DataFrame): Result storage DataFrame
    - **Outputs**: (tuple) Returns updated result_df and trade_stock_list
  - **Method: `get_daily_decision_log`**
    - **Role**: Retrieve detailed daily trading decisions
    - **Inputs**: None
    - **Outputs**: (list) Daily decision log entries
  - **Method: `ReturnFuc`**
    - **Role**: Return combined results from trading simulation
    - **Inputs**: None
    - **Outputs**: (tuple) Returns df_Comb, df_Bal, and Universe

## 4. Project Call Tree

- `Test.__init__`
  - `-> RoadDataFromDB`
    - `-> MongoDB.ReadDataBase` (from DataBase.CalMongoDB)
    - `-> CalDataBaseName` (from DataBase.CalDBName)
  - `-> RunStrategy`
    - `-> StrategyA.__init__` (from Strategy.Strategy_A)
    - `-> StrategyB.__init__` (from Strategy.Strategy_B)
    - `-> StrategyA.ReturnFunc`
    - `-> StrategyB.ReturnFunc`
- `TestTradeD.__init__`
  - `-> StrategyM.__init__` (from Strategy.Strategy_M)
  - `-> trade_stocks`
    - `-> StrategyM.CalcCashRatio`
    - `-> StrategyM.select_candidate_stocks_single`
    - `-> StrategyM.CalcPosSizing`
    - `-> StrategyM.sell_stock`
    - `-> StrategyM.buy_stock`
    - `-> StrategyM.remain_stock`
    - `-> StrategyM.whipsaw`
    - `-> StrategyM.CalcWinLossRatio`
- `TMakPlot.__init__`
- `PlotSingleStocks`
  - `-> mpf.make_addplot`
  - `-> mpf.plot`
- `PlotStocknBalance`
  - `-> mpf.make_addplot`
  - `-> mpf.plot`