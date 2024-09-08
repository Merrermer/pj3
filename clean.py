import pandas as pd
import logging
import numpy as np
import sl


##################################################################################
# This module if for data cleaning. 
# These functions are deprecated in version 1.0 and later.
##################################################################################

logging.basicConfig(filename='datacleaning',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

# This function adjusts the close prices for stock splits and cumulative dividends.
# It calculates a split-adjusted price by considering cumulative dividends and stock splits over time.
def adj_close(df):
    df['split_adjustment'] = df['splits'].replace(0, 1).cumprod()
    df['cum_dividends'] = df['dividends'][::-1].cumsum()[::-1] / df['split_adjustment']
    df['adjusted_close'] = (df['close'] - df['cum_dividends']) / df['split_adjustment']
    return df

# This function fills forward any NaN values in the DataFrame and drops any remaining rows with NaNs.
# It ensures the dataset is clean without missing values
def findNaNs(df):
    df.ffill(inplace=True)
    df.dropna(inplace=True)
    return df

# This function removes rows where the 'Volume' column is zero, filtering out non-trading days.
def drop_zero_volume(df):
    return df[df['Volume'] != 0]

# This function identifies outliers in the 'Open' price column based on a 30-day moving average and standard deviation.
# It flags days where the price deviates significantly from the rolling average (4 standard deviations).
def outliers(df0, code):
    df = df0.copy()
    #for tag in ['Open', 'High', 'Low', 'Close']:
    for tag in ['Open']:
        df['30d_MA'+tag] = df[tag].rolling(window=30).mean()
        df['30d_STD'+tag] = df[tag].rolling(window=30).std()
        df['outliers'+tag] = np.abs(df[tag] - df['30d_MA'+tag]) > (4 * df['30d_STD'+tag])
        outliers = df[df.index >= df.index[29]]
        outliers = outliers[outliers['outliers'+tag] == True]
        print(outliers['Date'])

def pct_chg(df):
    df['pct_chg'] = df['Close'].pct_change()
    df['tomorrow_pctchg'] = df['pct_chg'].shift(-1)
    return df

# This function normalizes the 'Open', 'Close', 'High', and 'Low' columns using a 245-day rolling mean and standard deviation.
# It creates normalized versions of these columns as well as their rolling mean and standard deviation.
def normalize(df_original):
    df = df_original.copy()
    tags = ['Open', 'Close', 'High', 'Low']
    window_size = 245
    rolling_mean = df[tags].rolling(window=window_size, min_periods=window_size).mean()
    rolling_std = df[tags].rolling(window=window_size, min_periods=window_size).std()
    for tag in tags:
        normalized_column_name = f'normalized_{tag}'
        normalized_column_name_1 = f'mean_{tag}'
        normalized_column_name_2 = f'std_{tag}'
        
        df[normalized_column_name] = (df[tag] - rolling_mean[tag]) / rolling_std[tag]
        df[normalized_column_name_1] = rolling_mean[tag]
        df[normalized_column_name_2] =rolling_std[tag]
    return df

# This function filters out stocks with low liquidity and price, and applies data cleaning (handles NaNs, zero volumes, etc.), and normalizes the data.
# If the stock fails liquidity checks or has insufficient data, it logs the stock as disqualified or omitted.
def process(df):
    code = df['Ticker'].values.tolist()[0]
    if (df['Volume'].mean())* (df['Close'].mean()) < 1000_0000 or min(df['Close'])<1:
        logging.info(f'{code} disqualified')
        return None
    df = drop_zero_volume(findNaNs(pct_chg(normalize(df))))
    
    if len(df)<1323: 
        logging.info(f'Data omitted in {code}')
        return None
    return  df

if __name__=='__main__':
    df = sl.retrieve('ADVANC.BK')
    sl.save_to_csv(process(df), 'temp.csv')
    print(len(sl.read_csv('temp.csv')))
