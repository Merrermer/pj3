import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
import logging
import sl
import multiprocessing as mp
import pandas as pd
import yfinance as yf
import logging

#####################################################
# This module is for data downloading and preparing.
# These functions are deprecated after V 1.0
#####################################################

for s in ['yfinance', 'peewee', 'urllib3.connectionpool']:
    logger = logging.getLogger(s)
    logger.disabled = True
    logger.propagate = False

load_dotenv()

logging.basicConfig(filename='username',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')

DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"


lock = mp.Lock()
def download(code, start = '2018-01-01'):
    try:
        proxies ={'http':'http://127.0.0.1:7890', 'https':'http://127.0.0.1:7890',}
        temp = yf.Ticker(code,proxy=proxies)
        df = temp.history(start)
        df['Ticker'] = code
        return df
    except Exception as e:
        logging.error(f"Error downloading data for {code}: {str(e)}")
        return None
    
def process(code):
    data = download(code)
    if data is None:
        logging.error(f"{code} doesn't meet the requirement")
        return
    if len(data)<1595:  #change this according to your chosen time span
        logging.error(f"{code} doesn't meet the requirement")
        return
    sl.ohlc_save_to_db(data, code)
    return

df = sl.read_csv('symbol_list.csv')

def get_info(symbol_list = [symbol[0] for symbol in df.values.tolist()]):
    pool = mp.Pool(12)
    pool.map(process, symbol_list)
    pool.close()
    pool.join()
    print('complete')
    return

if __name__=='__main__':
    get_info()