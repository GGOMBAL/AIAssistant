# Project Technical Analysis Document

## 1. Project Overview

This project is a system for generating and processing stock trading data. Its main purpose is to add technical analysis indicators to stock data of various timeframes (daily, weekly, etc.) and filter the data by a specified period to process it into a form usable for trading strategies.

The system supports the US and other regional stock markets and provides an architecture that can integrally handle various data types (daily, weekly, relative strength, returns, fundamentals, etc.). It generates technical analysis data through the KIS (Korea Investment & Securities) API and returns it in a structured format for use in the trading system.

## 2. File Roles

- `GenTradingData.py`: The main file that provides the core class for generating and processing stock trading data. It is responsible for adding technical analysis indicators to stock data of various timeframes and filtering by a specified period.

## 3. Function and Class Specification

### `GenTradingData.py`

- **Class: `GenTRD`**
  - **Role**: The main class for generating and processing stock trading data, applying technical analysis to data of various timeframes and performing period-based filtering.

- **Method: `__init__(self, Universe, area, df_W, df_D, df_RS, df_E, df_F, start_day, end_day, Trading)`**
  - **Role**: Initializes the class instance, applies technical analysis to all dataframes, and then filters the data by the specified period.
  - **Inputs**:
    - `Universe` (list): A list of stock symbols to be analyzed
    - `area` (str): Market area identifier ('US' or other)
    - `df_W` (dict): Dictionary containing weekly data
    - `df_D` (dict): Dictionary containing daily data
    - `df_RS` (dict): Dictionary containing relative strength data
    - `df_E` (dict): Dictionary containing returns data
    - `df_F` (dict): Dictionary containing fundamental data
    - `start_day` (str/datetime): Data start date
    - `end_day` (str/datetime): Data end date
    - `Trading` (object): Trading-related configuration object
  - **Outputs**: None (initialization method)

- **Method: `GetTechnicalData(self, Universe, df, PCode)`**
  - **Role**: A method that adds technical analysis indicators to a given dataframe. It generates technical analysis data for each stock symbol through the KIS API.
  - **Inputs**:
    - `Universe` (list): A list of stock symbols to be analyzed
    - `df` (dict): Dictionary of dataframes to which technical analysis will be applied
    - `PCode` (str): Data type code ('W': Weekly, 'D': Daily, 'RS': Relative Strength, 'E': Returns, 'F': Fundamentals)
  - **Outputs**: (dict) A dictionary of dataframes with technical analysis applied

- **Method: `ReturnFunc(self)`**
  - **Role**: A method that returns all processed dataframes, allowing access to the processed data from outside the class.
  - **Inputs**: None
  - **Outputs**: (tuple) Five processed dataframe dictionaries (df_D, df_W, df_RS, df_E, df_F)

## 4. Project Call Tree

- `GenTRD.__init__`
  - `-> GetTechnicalData` (Processing weekly data)
    - `-> KisTRD.GetTrdData2`
  - `-> GetTechnicalData` (Processing relative strength data)
    - `-> KisTRD.GetTrdData2`
  - `-> GetTechnicalData` (Processing fundamental data, US market only)
    - `-> KisTRD.GetTrdData2`
  - `-> GetTechnicalData` (Processing daily data)
    - `-> KisTRD.GetTrdData2`
- `GenTRD.ReturnFunc`
  - `-> return processed dataframes`