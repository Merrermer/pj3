import mysql.connector
import pandas as pd
import sl
import clean

##################################################################################
# This module if for data retrieving and preparing. 
# These functions are deprecated in version 1.0 and later.
##################################################################################


def load_all(n = None): # Concat all ohlc data of each stock into one file
    engine = sl.get_engine()

    df = sl.read_csv('symbol_list_correct.csv')
    symbol_list = [symbol[0] for symbol in df.values.tolist()][0:n]
    dataframes = [sl.mpretrieve(code, engine) for code in symbol_list]
    dataframes_normalized = [clean.process(df) for df in dataframes]

    dataframes_normalized = [df for df in dataframes_normalized if df is not None]

    combined_df = pd.concat(dataframes_normalized, ignore_index=True)
    engine.dispose()

    return combined_df
    

def dict_date(df): # This function creates a dictionary where the keys are unique dates from the dataframe, and the values are dataframes filtered by those dates.
    d = {date: df[df['Date'] == date] for date in df['Date'].unique()}
    return d
def dict_ticker(df): # This function creates a dictionary where the keys are unique tickers from the dataframe, and the values are dataframes filtered by those tickers.
    return {ticker: df[df['Ticker'] == ticker] for ticker in df['Ticker'].unique()}


if __name__ == '__main__':
    df = load_all()
    sl.save_to_csv(df, 'all_normalized.csv')
    
    df = sl.read_csv('all_normalized.csv')
    d_date = dict_date(df)
    sl.save_dict(d_date, 'd_date.pkl')
    d_ticker = dict_ticker(df)
    sl.save_dict(d_ticker, 'd_ticker.pkl')



