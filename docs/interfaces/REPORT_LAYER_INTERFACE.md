# Report Layer Interface Specification

## 1. Overview

The Report Layer provides comprehensive trading performance analysis and reporting capabilities. It analyzes trading history, tracks balance evolution, and generates actionable insights.

**Layer Purpose**: Generate detailed trading performance reports and analytics
**Primary Agent**: Report Agent
**Access Rights**: Read-only for all layers, Write to Reporting Layer only

## 2. Input Interface

### 2.1 Order History (Required)

Primary input data for all reporting functions.

```python
# DataFrame Structure
order_history = pd.DataFrame({
    'ticker': str,              # Stock ticker symbol (e.g., 'AAPL')
    'order_type': str,          # 'BUY' or 'SELL'
    'order_date': datetime,     # Order execution date/time
    'execution_price': float,   # Actual execution price
    'quantity': int,            # Number of shares
    'commission': float,        # Trading commission (optional, default: 0)
    'order_id': str            # Unique order identifier (optional)
})
```

**Validation Rules**:
- `ticker`: Non-empty string
- `order_type`: Must be 'BUY' or 'SELL'
- `order_date`: Valid datetime, not future date
- `execution_price`: Positive float
- `quantity`: Positive integer
- `commission`: Non-negative float

### 2.2 Market Prices (Optional)

Current market prices for portfolio valuation.

```python
# DataFrame Structure
market_prices = pd.DataFrame({
    'ticker': str,              # Stock ticker symbol
    'date': datetime,           # Price date
    'close': float             # Closing price
})
```

### 2.3 Request Parameters

```python
{
    'action': str,              # Action to perform
    'data': {
        'order_history': DataFrame,
        'market_prices': DataFrame  # Optional
    },
    'params': {
        'report_type': str,     # 'full', 'pl', 'balance', 'summary', 'gap'
        'format': str,          # 'json' or 'text'
        'filepath': str         # For save_report action
    }
}
```

## 3. Output Interface

### 3.1 Report Structure

All reports follow this base structure:

```python
{
    'agent': 'Report Agent',
    'version': str,
    'report_type': str,
    'generated_at': str,        # ISO format datetime
    'data': {
        # Report-specific data
    }
}
```

### 3.2 P/L Analysis Output

```python
{
    'pl_analysis': {
        'summary': {
            'total_trades': int,
            'winning_trades': int,
            'losing_trades': int,
            'win_rate': float,      # Percentage
            'total_gross_pnl': float,
            'total_commission': float,
            'total_net_pnl': float,
            'avg_pnl_per_trade': float,
            'avg_return_pct': float,
            'avg_holding_days': float,
            'best_trade': float,
            'worst_trade': float,
            'best_return_pct': float,
            'worst_return_pct': float
        },
        'performance_metrics': {
            'average_win': float,
            'average_loss': float,
            'risk_reward_ratio': float,
            'profit_factor': float,
            'expectancy': float,
            'sharpe_ratio': float,
            'median_pnl': float,
            'std_pnl': float,
            'skewness': float,
            'kurtosis': float
        },
        'trade_distribution': {
            'pnl_distribution': dict,       # P/L bins
            'holding_period_distribution': dict
        },
        'time_analysis': {
            'monthly_performance': dict,
            'day_of_week_performance': dict
        },
        'ticker_performance': {
            'ticker_statistics': dict,
            'top_5_profitable_tickers': dict,
            'worst_5_losing_tickers': dict
        },
        'risk_metrics': {
            'max_drawdown': float,
            'max_drawdown_pct': float,
            'value_at_risk_95': float,
            'conditional_value_at_risk_95': float,
            'recovery_factor': float
        },
        'streak_analysis': {
            'max_consecutive_wins': int,
            'max_consecutive_losses': int,
            'current_streak_type': str,     # 'win' or 'loss'
            'current_streak_length': int
        }
    }
}
```

### 3.3 Balance Analysis Output

```python
{
    'balance_analysis': {
        'summary': {
            'initial_balance': float,
            'current_balance': float,
            'peak_balance': float,
            'trough_balance': float,
            'peak_date': str,
            'trough_date': str,
            'total_return': float,
            'total_return_pct': float,
            'days_tracked': int,
            'current_cash': float,
            'current_portfolio_value': float,
            'current_positions': int
        },
        'growth_metrics': {
            'cagr': float,                  # Compound Annual Growth Rate
            'annual_return': float,
            'annual_volatility': float,
            'sharpe_ratio': float,
            'avg_daily_return': float,
            'best_day_return': float,
            'worst_day_return': float,
            'positive_days': int,
            'negative_days': int,
            'win_rate_days': float,
            'avg_monthly_return': float,
            'best_month_return': float,
            'worst_month_return': float
        },
        'volatility_metrics': {
            'daily_volatility': float,
            'annual_volatility': float,
            'current_30d_volatility': float,
            'max_30d_volatility': float,
            'min_30d_volatility': float,
            'downside_deviation': float,
            'sortino_ratio': float,
            'value_at_risk_95': float,
            'value_at_risk_99': float,
            'skewness': float,
            'kurtosis': float
        },
        'drawdown_analysis': {
            'max_drawdown': float,
            'max_drawdown_pct': float,
            'current_drawdown': dict or None,
            'num_drawdowns': int,
            'avg_drawdown_pct': float,
            'avg_recovery_days': float,
            'longest_drawdown': dict or None,
            'drawdown_periods': list       # Top 5 drawdowns
        },
        'cash_utilization': {
            'avg_cash_percentage': float,
            'avg_invested_percentage': float,
            'max_invested_percentage': float,
            'min_cash_balance': float,
            'current_cash_percentage': float,
            'days_high_cash': int,
            'days_low_cash': int,
            'cash_efficiency': float,
            'avg_positions_held': float,
            'max_positions_held': int
        },
        'period_analysis': {
            'monthly_returns': dict,
            'quarterly_returns': dict,
            'last_7d_return': float,
            'last_30d_return': float,
            'last_90d_return': float,
            'ytd_return': float,
            'best_quarter': str,
            'worst_quarter': str
        },
        'milestone_analysis': {
            'milestones_reached': list,
            'time_to_double_days': int or None,
            'next_milestone': float or None
        },
        'health_indicators': {
            'health_score': float,          # 0-100
            'is_overleveraged': bool,
            'cash_cushion_pct': float,
            'trend_direction': str,         # 'up' or 'down'
            'trend_strength': float,
            'distance_from_peak_pct': float,
            'risk_level': str,              # 'Low', 'Moderate', 'High', 'Critical'
            'recommended_actions': list
        },
        'forecast': {
            'projections': {
                '30_days': dict,
                '90_days': dict,
                '180_days': dict,
                '365_days': dict
            },
            'assumptions': dict
        }
    }
}
```

### 3.4 Executive Summary Output

Generated for 'full' report type:

```python
{
    'executive_summary': {
        'performance_grade': str,       # 'A', 'B', 'C', 'D', 'F'
        'key_metrics': {
            'total_trades': int,
            'win_rate': float,
            'total_pnl': float,
            'avg_pnl': float,
            'total_return_pct': float,
            'sharpe_ratio': float,
            'max_drawdown_pct': float
        },
        'strengths': list,              # List of strength points
        'weaknesses': list,             # List of weakness points
        'trend': str                    # 'strongly positive', 'positive', 'neutral', 'negative', 'strongly negative'
    }
}
```

### 3.5 Insights and Recommendations

Generated for 'full' report type:

```python
{
    'insights': [
        str,  # Up to 5 actionable insights
        ...
    ],
    'recommendations': [
        str,  # Up to 5 specific recommendations
        ...
    ]
}
```

### 3.6 GAP Analysis Output (Future Implementation)

```python
{
    'gap_analysis': {
        'status': 'Not implemented',
        'message': str,
        'planned_features': list,
        'report_generated': str
    }
}
```

## 4. Error Handling

### 4.1 Error Response Structure

```python
{
    'status': 'error',
    'error': str,                      # Error message
    'metadata': {
        'router': 'Report Agent Router',
        'timestamp': str,               # ISO format
        'request_id': int
    }
}
```

### 4.2 Common Error Codes

- `MISSING_DATA`: Required data not provided
- `INVALID_FORMAT`: Data format invalid
- `EMPTY_HISTORY`: Order history empty
- `INVALID_ACTION`: Unknown action requested
- `SAVE_FAILED`: Failed to save report
- `CALCULATION_ERROR`: Error during calculations

## 5. Examples

### 5.1 Generate Full Report

```python
# Request
request = {
    'action': 'generate_report',
    'data': {
        'order_history': pd.DataFrame({
            'ticker': ['AAPL', 'AAPL'],
            'order_type': ['BUY', 'SELL'],
            'order_date': ['2024-01-01', '2024-01-10'],
            'execution_price': [150.0, 155.0],
            'quantity': [100, 100],
            'commission': [1.0, 1.0]
        })
    },
    'params': {
        'report_type': 'full'
    }
}

# Response
response = {
    'status': 'success',
    'data': {
        'agent': 'Report Agent',
        'version': '1.0.0',
        'report_type': 'full',
        'generated_at': '2024-01-15T10:30:00',
        'data': {
            'pl_analysis': {...},
            'balance_analysis': {...},
            'executive_summary': {...},
            'insights': [...],
            'recommendations': [...]
        }
    },
    'metadata': {...}
}
```

### 5.2 Generate P/L Report Only

```python
# Request
request = {
    'action': 'generate_pl_report',
    'data': {
        'order_history': order_df
    }
}

# Response includes only P/L analysis
```

### 5.3 Save Report to File

```python
# Request
request = {
    'action': 'save_report',
    'params': {
        'filepath': 'reports/trading_report_20240115.json',
        'format': 'json'
    }
}

# Response
response = {
    'status': 'success',
    'data': {
        'message': 'Report saved to reports/trading_report_20240115.json'
    },
    'metadata': {...}
}
```

## 6. Dependencies

### Required Libraries
- pandas >= 1.3.0
- numpy >= 1.21.0
- datetime (built-in)
- logging (built-in)
- json (built-in)

### Internal Dependencies
- `project/reporting/pl_analyzer.py`
- `project/reporting/balance_analyzer.py`
- `project/reporting/gap_analyzer.py`

## 7. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-14 | Initial implementation with P/L and Balance analyzers |
| Future | TBD | GAP analyzer implementation |

## 8. Performance Considerations

### Data Size Limits
- Maximum order history: 100,000 records
- Maximum market price history: 1,000,000 records

### Optimization Tips
- Cache reports for repeated access
- Use batch processing for large datasets
- Consider parallel processing for independent calculations

### Response Time Expectations
- Small dataset (<1,000 orders): < 1 second
- Medium dataset (<10,000 orders): < 5 seconds
- Large dataset (<100,000 orders): < 30 seconds

## 9. Future Enhancements

1. **GAP Analyzer Full Implementation**
   - Slippage analysis
   - Market impact measurement
   - Signal fidelity tracking

2. **Additional Report Types**
   - Multi-strategy comparison
   - Cross-market analysis
   - Time-series forecasting

3. **Enhanced Visualizations**
   - HTML report generation
   - Interactive dashboards
   - Chart generation

4. **Real-time Reporting**
   - Live performance tracking
   - Streaming analytics
   - Alert generation

## 10. Support and Maintenance

**Responsible Agent**: Report Agent
**Maintainer**: Report Agent Team
**Update Frequency**: Monthly
**Contact**: Via Orchestrator Agent