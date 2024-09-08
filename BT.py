import pandas as pd
import numpy as np
from strategy import myStrategy
import matplotlib.pyplot as plt
import math

# Class: TransactionCost
# This class calculates transaction costs based on different models.
# Models supported: 'default', 'fixed', or custom callable models.
class TransactionCost:
    def __init__(self, model=['default'], data=None, amount=0, **kwargs):
        self.data = data
        self.amount = amount
        self.model = model
        if self.model[0] == 'default':
            self.value = self.model1(**kwargs)
        elif self.model[0] == "fixed":
            self.value = self.model2(**kwargs)
        else:
            if callable(self.model[0]):
                self.value = model(**kwargs)
            else:
                self.value = 0
    
    # Model 1: Calculates transaction cost using a formula provided on Multi-Period Trading via Convex Optimization.
    def model1(self, a=0.0005, b=1, c=0, **kwargs):
        if self.data.empty:
            return 0
        x = self.amount
        volume = self.data['valuevolume'] * self.data['close']
        if volume == 0:
            return 0
        sigma = self.data['rolling_std'] 
        cost = a * abs(x) + b * sigma / np.sqrt(volume) * abs(x)**(3/2) + c * x
        cost = cost / self.data['close']

        if math.isnan(cost):
            return 0
        
        return cost
    
    # Model 2: Fixed transaction cost model, calculates the cost as a fixed rate of the amount traded.
    def model2(self, **kwargs):
        fee_rate = self.model[1]
        return self.amount * fee_rate



# This class simulates a backtest using a given strategy, tracking portfolio value over time and incorporating transaction costs and holding fees. It can generate backtest statistics and visualizations.
class BacktestModule:
    def __init__(self, strategy_instance, t_cost=['default'], start=None, end=None, holding_feerate=0.03, initial_cash=100_0000):
        self.strategy = strategy_instance
        self.price_data = self.strategy.UNI.dict_ticker

        # Filter dates based on the specified start and end dates
        self.dates = [date for date in self.strategy.dates if date >= start and date <= end]
        self.cash = initial_cash
        self.portfolio_value = {start: initial_cash}
        self.holdings = {}

        self.tcost_model = t_cost  # Transaction cost model
        self.holding_feerate = holding_feerate  # Holding fee rate (annual)
        self.start = start
        self.end = end


    # This method rebalances the portfolio on the given date, adjusting holdings and applying transaction costs and holding fees.
    def rebalance(self, current_date):
        if math.isnan(self.cash) or self.cash == 0:
            self.portfolio_value[current_date] = 0
            return

        # Get new positions from the strategy for the current date
        new_positions = self.strategy.position_dict.get(current_date, {})
        tickers_to_change = set(self.holdings.keys()) | set(new_positions.keys())
        
        returns = 0
        transaction_cost = 0
        holding_cost = self.holding_fee()

        for ticker in tickers_to_change:
            temp = self.price_data[ticker].loc[current_date]
            position_change = abs(self.holdings.get(ticker, 0) - new_positions.get(ticker, 0)) 
            amount = abs(position_change) * self.cash
            
            # Calculate transaction cost
            transaction_cost += TransactionCost(model=self.tcost_model, a=0.0005, b=1, data=temp, amount=amount).value

            # Calculate returns
            if self.holdings.get(ticker, 0) != 0:
                returns += (temp['pctChg'] * self.holdings[ticker] * self.cash)

            # Update holdings
            if new_positions.get(ticker, 0) == 0:
                del self.holdings[ticker]
            else:
                self.holdings[ticker] = new_positions[ticker]
        
        # Update cash after returns, transaction costs, and holding fees
        self.cash += returns - transaction_cost - holding_cost
        self.cash = max(self.cash, 0)
        self.portfolio_value[current_date] = self.cash
        return

    # This method calculates the holding cost for short positions based on the annual holding fee rate.
    def holding_fee(self):
        holding_cost = 0
        for ticker, position in self.holdings.items():
            if position < 0:  # Only applies to short positions
                amount = abs(position) * self.cash
                holding_cost += amount * (1 + self.holding_feerate)**(1/252) - amount
        return holding_cost

    # This method runs the backtest by rebalancing the portfolio on each date in the specified date range.
    def run_backtest(self):
        for date in self.dates:
            self.rebalance(date)
        return

    # This method calculates and prints key statistics from the backtest.
    def statistics(self):
        values = list(self.portfolio_value.values())
        daily_returns = np.diff(values) / values[:-1]
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        risk_free_rate = (1.02)**(1/252) - 1
        total_return = values[-1] / values[0]
        years = len(values) / 252
        cagr = (1 + total_return)**(1 / years) - 1
        sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(252)
        hwm = [max(values[0:i+1]) for i in range(len(values))]
        dd = [1 - values[i] / hwm[i] for i in range(len(values))]
        
        print('Sharpe ratio: ' + str(sharpe) + '\n')
        print('Average drawdown: ' + str(np.mean(dd)) + '\n')
        print('Max drawdown: ' + str(max(dd)) + '\n')
        print('CAGR: ' + str(cagr) + '\n')
        return values


    # This method plots the portfolio value over time.
    def plot(self, ax=None, label=None):
        if ax is None:
            ax = plt.gca()
        ax.plot(list(self.portfolio_value.keys()), list(self.portfolio_value.values()), label=label)
        return ax


if __name__ == '__main__':
    import sl
    U1 = sl.load_dict('U1_test.pkl')
    # We choose our default strategy which is pick 10 stocks with largest rolling Sharpe ratio and rebalance every day with risk parity position strategy.
    S1 = myStrategy(Universe=U1, stock_select='default', position_strategy='rp', start='2019-01-05', end='2024-07-30')
    S1.calculate()

    # Initialize and run the backtest
    # We set the initial_cash to be 1 million, strategy is already set, and the transaction cost is calculated by the formula mentioned previously.
    # If you want to change the transaction cost to a fixed model, put t_cost = ['fixed', you_chosen_rate] 
    backtest = BacktestModule(initial_cash=100_0000, strategy_instance=S1, start='2019-01-05', end='2024-02-25', t_cost=['default', 0.000])
    backtest.run_backtest()

    # Plot the backtest results
    backtest.plot()
    plt.show()
