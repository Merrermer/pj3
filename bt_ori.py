import sl
import numpy as np
import pandas as pd
import strategy_ori as strategy
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

##############################
# This is the backtest module. Deprecated in V 1.0 and later
##############################


def search(df, date=None, ticker=None): # This function searches the dataframe 'df' for rows based on the provided date and/or ticker.
    if date is None:
        result_row = df[(df['Ticker'] == ticker)]
    elif ticker is None:
        df[(df['Date'] == date)]
    else:
        result_row = df[(df['Date'] == date) & (df['Ticker'] == ticker)]
    return result_row




def backtest(d, position_long, position_short, long, short): # This function simulates a portfolio's performance over time.
    portfolio = {'2019-01-02': 1}  # Initial portfolio value
    net_value = {'2019-01-02': 0}  # Initial net value

    day = 0  # Day counter for tracking progression
    temp_date = None  # Temporary variable to hold the current date
    
    # Iterate over the dates in the position_long dictionary
    for date in position_long.keys():
        # Ensure the sum of long and short positions is equal (market-neutral strategy)
        assert sum(position_long[date]) == sum(position_short[date])
        
        if day == 0 or day == 1:
            temp_date = date
            day += 1
            continue
        
        long_tickers = long[temp_date]
        short_tickers = short[temp_date]

        # Calculate percentage change for long and short tickers
        pct_chg_long = np.array([search(df=d[temp_date], date=None, ticker=i)['tomorrow_pctchg'] for i in long_tickers]).flatten()
        pct_chg_short = np.array([search(df=d[temp_date], date=None, ticker=i)['tomorrow_pctchg'] for i in short_tickers]).flatten()

        print(temp_date, long_tickers, pct_chg_long)

        # Calculate portfolio percentage change based on long and short positions
        portfolio_pct_chg = np.dot(pct_chg_long, position_long[date]) - np.dot(pct_chg_short, position_short[date])

        # Update the portfolio value
        new_portfolio = (list(portfolio.values())[-1] * portfolio_pct_chg) + list(portfolio.values())[-1]
        
        # Calculate new net value based on the sum of long and short positions
        new_net_value = (np.sum(position_long[date]) + np.sum(position_short[date])) * new_portfolio

        # Apply trading cost (currently 0.3%)
        cost = new_net_value * 0.003
        new_portfolio -= cost
        new_portfolio = max(new_portfolio, 0)  # Ensure the portfolio doesn't go negative

        # Update portfolio and net value dictionaries with the new values
        net_value.update({date: new_net_value})
        portfolio.update({date: new_portfolio})

        temp_date = date
        day += 1

        # Limit the backtest to 800 days
        if day == 800:
            break

    # Calculate portfolio returns (cash) as percentage change in portfolio value
    cash = pd.DataFrame(portfolio.values()).pct_change()
    sharpe = np.average(cash) / np.std(cash)
    
    return sharpe, portfolio

if __name__ == '__main__':
    df = sl.read_csv('all_normalized.csv')
    d = sl.load_dict('d_date.pkl')
    short, long = strategy.stock_select(df)
    position_long, position_short = strategy.position(long), strategy.position(short)
    sharpe, portfolio = backtest(d, position_long, position_short, long, short)
    print(sharpe)
    
    dates = list(short.keys())[:len(portfolio)]
    date_obj = [mdates.datestr2num(date) for date in portfolio.keys()]
    plt.figure(figsize = (10, 5))
    plt.plot_date(date_obj, portfolio.values(), linestyle='solid', marker=None)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.gcf().autofmt_xdate() # Rotation
    plt.title('Date vs Values')
    plt.xlabel('Date')
    plt.ylabel('Values')
    plt.show()
    print()