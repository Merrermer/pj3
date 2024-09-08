import sl
import numpy as np
import pandas as pd
import strategy
import matplotlib.pyplot as plt
import matplotlib.dates as mdates



def search(df, date = None, ticker = None):
    if date is None:
        result_row =  df[(df['Ticker'] == ticker)]
    elif ticker is None:
        df[(df['Date'] == date)]
    else:
        result_row = df[(df['Date'] == date) & (df['Ticker'] == ticker)]
    return result_row


def backtest(d, position_dict):
    portfolio = {'2019-01-02': 1}
    net_value = {'2019-01-02': 0}

    day = 0
    temp_date = None
    for date in position_dict.keys():
        if day == 0 or day == 1:
            temp_date = date
            day+=1
            continue
        
        tickers = list(position_dict[temp_date].keys())
        positions = list(position_dict[temp_date].values())

        pct_chg= np.array([search(df = d[temp_date], date = None, ticker = i)['tomorrow_pctchg'] for i in tickers]).flatten()

        portfolio_pct_chg = np.dot(pct_chg, positions)
        
        new_portfolio = (list(portfolio.values())[-1] * (portfolio_pct_chg-0.003*0.6) + list(portfolio.values())[-1])
        new_net_value = list(portfolio.values())[-1] * sum([abs(i) for i in positions])

        cost = new_net_value*0.0001
        new_portfolio -= cost
        new_portfolio = max(new_portfolio,0)


        net_value.update({date: new_net_value})
        portfolio.update({date: new_portfolio})

        temp_date = date
        day+=1


    cash = pd.DataFrame(portfolio.values()).pct_change()
    
    sharpe = np.average(cash)/np.std(cash)
    return sharpe, portfolio

if __name__ == '__main__':
    from strategy import myStrategy
    df = sl.read_csv('all_normalized.csv')
    d = sl.load_dict('d_date.pkl')
    data = sl.load_dict('d_date.pkl')
    S0 = myStrategy(data, leverage_limit=0.5, n=10)
    S0.calculate()
    position_dict = S0.position_dict
    
    sharpe, portfolio = backtest(d, position_dict)
    
    dates = list(position_dict.keys())[:len(portfolio)]
    plt.figure(figsize = (10, 5))
    plt.plot(portfolio.keys(), portfolio.values(), linestyle='solid', marker=None)

    plt.title('Date vs Values')
    plt.xlabel('Date')
    plt.ylabel('Values')
    plt.show()
    print()