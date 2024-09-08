import pandas as pd
import numpy as np
import sl

class result(object):
    def __init__(self, data, risk_free_rate) -> None:
        self.df = data
        self.rf = (1+risk_free_rate)**(1/252)
        self.cumulative_returns = (1+self.df.cumprod())
    
    def stats(self):
        sharpe_ratio = (np.mean(self.df)-self.rf)/np.std(self.df)
        CAGR = (self.cumulative_returns.iloc[-1])**(1/(len(self.df)/252))-1
        hwm = [max(self.cumulative_returns[0:i+1]) for i in range(len(self.cumulative_returns))]
        dd = [1-self.cumulative_returns[i]/hwm[i] for i in range(len(self.cumulative_returns))]
        maxdd = max(dd)
        print(sharpe_ratio, CAGR, maxdd)
        return
