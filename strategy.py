import pandas as pd
import sl
import numpy as np
from Universe import Universe

class myStrategy():
    # Constructor: Initializes the strategy with universe, stock selection method, position strategy, etc.
    # You can specify the stock selection function, position strategy, leverage limit, and date range.
    def __init__(self, Universe, stock_select='default', n=10, position_strategy='default', leverage_limit=0.5, start='2018-12-28', end='2024-07-30'):
        self.UNI = Universe
        self.tick_posi = None
        self.stock_number = n  # Number of stocks to select
        self.dates = [date for date in Universe.dict_ticker[list(Universe.dict_ticker.keys())[0]].index.tolist() if date >= start and date <= end]
        self.leverage_limit = leverage_limit  # Maximum leverage allowed

        # Stock selection method assignment (default or custom)
        # Note that if you use the custom strategy, the output of your function should be a dictionary like this: {'2019-01-01':['AAPL','NVDA']}
        if stock_select == 'default':
            self.stock_select_func = self.__stock_select1
        elif callable(stock_select):
            self.stock_select_func = stock_select
        else:
            raise ValueError("Invalid stock_select. Must be a callable function.")
        
        # Position strategy method assignment (default, uniform, risk parity, or custom)
        # Note that if you use the custom strategy, the output of your function should be a dictionary like this: {'2019-01-01':{'AAPL':0.3, 'NVDA': 0.5}}
        if position_strategy == 'default':
            self.position_func = self.__default_daily_position
        elif position_strategy == 'uniform':
            self.position_func = self.__uniform
        elif position_strategy == 'rp':
            self.position_func = self.__riskparity
        elif callable(position_strategy):
            self.position_func = position_strategy
        else:
            raise ValueError("Invalid position_strategy. Must be a callable function.")

        self.position_dict = {}  # Dictionary to store calculated positions

    # Default stock selection method: selects top N stocks by Sharpe ratio for each date.
    def __stock_select1(self):
        short = {}
        long = {}
        total_selection = {}
        for date in self.dates:
            total_selection[date] = self.UNI.dict_date[date]['sharpe_ratio'].nlargest(self.stock_number).index.tolist()
        return total_selection

    # Default position strategy: assigns positions based on a normalized ranking of stocks.
    # Leverage is distributed proportionally across positions.
    def __default_daily_position(self, stock_selection, leverage):
        position_dict = {}
        for date in self.dates:
            posi_ori = np.arange(len(stock_selection[date]), 0, -1)
            posi = (posi_ori - np.mean(posi_ori)) / np.std(posi_ori)
            k = leverage / sum([abs(p) for p in posi])
            position_dict[date] = dict(zip(stock_selection[date], posi * k))
        return position_dict

    # Uniform position strategy: equally allocates leverage across all selected stocks.
    def __uniform(self, stock_selection, leverage):
        position_dict = {}
        for date in self.dates:
            posi = np.ones(len(stock_selection[date]))  
            k = leverage / sum([abs(p) for p in posi])
            position_dict[date] = dict(zip(stock_selection[date], posi * k))
        return position_dict

    # Risk parity position strategy: positions are sized inversely to the rolling volatility of the stocks.
    # THIS METHOD SHOULD BE REFINED.
    def __riskparity(self, stock_selection, leverage):
        position_dict = {}

        for ticker in self.UNI.symbol_list:
            self.UNI.dict_ticker[ticker]['rolling_std'] = self.UNI.dict_ticker[ticker]['close'].rolling(window=180).std()

        # Calculate position weights based on the inverse of the standard deviation
        for current_date in self.dates:
            std_devs = []
            for ticker in stock_selection[current_date]:
                std_dev = self.UNI.dict_ticker[ticker]['rolling_std'].loc[current_date]
                std_devs.append(std_dev)
            inverse_std_devs = 1 / np.array(std_devs)
            normalized_weights = inverse_std_devs / inverse_std_devs.sum() * leverage
            position_dict[current_date] = dict(zip(stock_selection[current_date], normalized_weights))
        return position_dict

    # Method to calculate stock selection and positions based on the selected strategy.
    def calculate(self):
        total_selection = self.stock_select_func()  # Get selected stocks
        self.position_dict = self.position_func(total_selection, self.leverage_limit)  # Calculate positions
        return



if __name__ == '__main__':
    # Example of default stock selection and risk parity position strategy
    U1 = sl.load_dict('U1_test.pkl')
    S1 = myStrategy(Universe=U1, stock_select='default', position_strategy='rp', start='2019-01-03', end='2019-01-30')
    S1.calculate()
    print(S1.position_dict)

