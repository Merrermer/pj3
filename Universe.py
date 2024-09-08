import cvxportfolio as cvx
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory
import sl


# This class represents a collection of stocks and handles data preparation for backtesting.
# Here all data is put into hash table form, which greatly speeds up the backtest and strategy calculationl.
class Universe:
    def __init__(self, symbol_list, start='2018-01-03', end='2024-07-30') -> None:
        self.symbol_list = symbol_list  # List of stock tickers
        self.dataframe = pd.DataFrame()  # Main dataframe to hold stock data
        self.start = start  # Start date for the stock data
        self.end = end  # End date for the stock data
        self.dict_date = {}  # Dictionary to store stock data organized by date
        self.dict_ticker = {}  # Dictionary to store stock data organized by ticker

    # This method resets the universe by reinitializing the class.
    def clear(self):
        self.__init__(self, self.symbol_list)
        return

    # This method fetches stock data from Yahoo Finance for the specified tickers and date range.
    # It cleans and processes the data, calculates percentage changes, and organizes the data into dictionaries.
    def prepare(self):
        rawdatalist = []
        for i in self.symbol_list:
            # Attempt to fetch stock data from Yahoo Finance with retries
            for attemps in range(3):
                try:
                    df = cvx.YahooFinance(i).data
                    break
                except Exception as e:
                    print(e, i, attemps)

            # Clean and filter the stock data by the date range
            df.index = pd.to_datetime(df.index)
            cvx_cleaned = df.loc[self.start: self.end]
            cvx_cleaned['Ticker'] = i
            self.dict_ticker[i] = cvx_cleaned  # Store data by ticker

            # Reset index and process the dataframe
            cvx_cleaned = cvx_cleaned.reset_index()
            cvx_cleaned.rename(columns={'index': 'Date'}, inplace=True)
            cvx_cleaned['Date'] = cvx_cleaned['Date'].dt.strftime('%Y-%m-%d')
            cvx_cleaned['pctChg'] = cvx_cleaned['close'].pct_change()  # Calculate percentage change
            rawdatalist.append(cvx_cleaned)

        # Concatenate all stock data into one dataframe and store it
        DF = pd.concat(rawdatalist, ignore_index=True)
        self.dataframe = DF.set_index(['Date', 'Ticker'])
        self.symbol_list_qualified = list(DF['Ticker'].unique())  # List of qualified tickers

        # Organize the data by date
        for date in DF['Date'].unique():
            self.dict_date[date] = self.dataframe.loc[date]
        
        return


    # This method organizes the stock data into dictionaries based on both ticker and date, resetting the dataframe and updating the `dict_ticker` and `dict_date` dictionaries.
    def coordinate(self):
        DF = self.dataframe.reset_index()

        # Organize data by ticker
        for ticker in DF['Ticker'].unique():
            self.dict_ticker[ticker] = DF[DF['Ticker'] == ticker].set_index('Date')

        # Organize data by date
        for date in DF['Date'].unique():
            self.dict_date[date] = DF[DF['Date'] == date].set_index('Ticker')
        
        self.symbol_list = list(DF['Ticker'].unique())  # Update list of tickers
        self.symbol_list_qualified = self.symbol_list  # Update list of qualified tickers
        return
    

        
if __name__ == '__main__':
    # This is a test to generate a universe
    df = sl.read_csv('symbol_list_correct.csv')
    symbol_list = [symbol[0] for symbol in df.values.tolist()]
    U = Universe(symbol_list=symbol_list)
    U.prepare()
    sl.save_dict(U, 'Universe_test.pkl')
    # Generate an investable universe with filtered stocks. These stocks are filtered according to their daily volume > 500M and min closed price > 2
    filtered_tickers = ['ADVANC.BK',
                        'AOT.BK',
                        'BANPU.BK',
                        'BBL.BK',
                        'BDMS.BK',
                        'CPALL.BK',
                        'DELTA.BK',
                        'EA.BK',
                        'GPSC.BK',
                        'IVL.BK',
                        'KBANK.BK',
                        'PTT.BK',
                        'PTTEP.BK',
                        'PTTGC.BK',
                        'SCC.BK']
    U_new = Universe(symbol_list=filtered_tickers)
    U_new.prepare()
    sl.save_dict(U_new, 'U1_test.pkl')
    
        
