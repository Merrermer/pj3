import pandas as pd
import sl  # Custom module 'sl' - likely used for reading data
import numpy as np

##################################################################################
# This module contains functions related to stock selection and position allocation.
# These functions are deprecated in version 1.0 and later.
##################################################################################

# This function selects the top 10 and bottom 10 stocks based on the 'normalized_Close' column
# and returns them as separate dictionaries for long (bottom 10) and short (top 10) positions.
def stock_select(df):

    df_sorted = df.sort_values(by=['Date', 'normalized_Close'], ascending=[True, False])
    df_Date = df_sorted.groupby('Date')

    # Select the top 10 stocks (for short positions) and bottom 10 stocks (for long positions) by date
    top_10 = df_Date.head(10)[['Ticker', 'Date']]
    tail_10 = df_Date.tail(10)[['Ticker', 'Date']]

    # Convert the top 10 and bottom 10 stocks into dictionaries with date as key and tickers as values
    short = top_10.groupby('Date')['Ticker'].apply(list).to_dict()  # Short positions
    long = tail_10.groupby('Date')['Ticker'].apply(list).to_dict()  # Long positions

    return short, long

# This function returns a standardized weight vector for the top 10 positions.
def daily_position():
    posi_ori = np.arange(20, 0, -1)
    posi = (posi_ori - np.mean(posi_ori)) / np.std(posi_ori)
    
    return posi[0:10] / sum(posi[0:10]) * 0.3 # Here we choose the leverage as 0.3

# This function creates a dictionary of position allocations for a given dictionary of stock lists.
def position(d):
    position_dict = {}
    for key in d.keys():
        posi = daily_position()
        position_dict[key] = posi
    
    return position_dict


if __name__ == '__main__':
    df = sl.read_csv('all_normalized.csv')
    short, long = stock_select(df)
    print(long)
