import pandas as pd
import csv
import os 
from sqlalchemy import create_engine, text, Table, MetaData
import logging
import yfinance as yf
import concurrent.futures
from sqlalchemy.orm import sessionmaker

MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
SYS_DB = os.getenv('SYS_DB')

DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

logging.basicConfig(filename='username',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def save_to_csv(data, filename):
    """
    Save a list or pandas DataFrame to a CSV file.
    """
    if isinstance(data, pd.DataFrame):
        data.to_csv(filename, index=False)
    elif isinstance(data, list):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
    else:
        raise TypeError("Data must be a list or a pandas DataFrame")

    print(f"Data has been written to {filename}")

def read_csv(filename):
    df = pd.read_csv(filename)
    return df

import pickle

def save_dict(dictionary, file_path):
    with open(file_path, 'wb') as pickle_file:
        pickle.dump(dictionary, pickle_file)

def load_dict(file_path):
    with open(file_path, 'rb') as pickle_file:
        return pickle.load(pickle_file)
#####################################################


#####################################################
def get_engine(**kwargs):
    engine = create_engine(DATABASE_URL, **kwargs)
    return engine

def create_database(database_name):
    engine = create_engine(f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{SYS_DB}")
    with engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE {database_name}"))
        logging.info(f"Database {database_name} created successfully")

def ohlc_save_to_db(dataframe, code):
    engine = create_engine(DATABASE_URL)
    try:
        dataframe.to_sql(code.lower(), engine, if_exists='replace', index=True, index_label='Date')
        logging.info(f"Data saved to {code} table successfully.")
    except:
        try:
            dataframe.to_sql(code.lower(), engine, if_exists='replace', index = False)
        except Exception as e:
            logging.error(f"Error saving {code} to database: {str(e)}")
    engine.dispose()



########################################
def mpchunk_save(df, name, chunk_size = 1000):
    engine = get_engine(pool_size=24, max_overflow=24, pool_recycle=3600, pool_timeout=30)
    Session = sessionmaker(bind=engine)
    def upload_chunk(df_slice, table_name):
        session = Session()
        try:
            df_slice.to_sql(table_name, con=session.bind, if_exists='append', index=False, method='multi')
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error occurred: {e}")
        finally:
            session.close()
        return

    df_chunks = (df.iloc[i:i + chunk_size] for i in range(0, df.shape[0], chunk_size))
    print(df.shape[0])

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(upload_chunk, chunk, name) for chunk in df_chunks]
        concurrent.futures.wait(futures)
    return
########################################


########################################
def retrieve_data(query):
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = pd.read_sql(query, connection)
        connection.close()
    engine.dispose()
    return result

def retrieve(code):
    query  = f'select * from `{str(code)}`'
    try:
        data = retrieve_data(query)
    except Exception as e:
        logging.error(f"Error retrieving {code} from database: {str(e)}")
        return None
    return data

def mpretrieve(code, engine):
    query  = f'select * from `{str(code)}`'
    with engine.connect() as connection:
        try:
            data = pd.read_sql(query, connection)
        except Exception as e:
            logging.error(f"Error retrieving {code} from database: {str(e)}")
            return None
        connection.close()
    return data

def mpretrieve2(table_codes):
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    results = {}
    metadata = MetaData()

    for table_code in table_codes:
        table = Table(table_code, metadata, autoload_with=engine)
        query = session.query(table).all()
        results[table_code] = query
    return results


if __name__ =='__main__':
    create_database('pjthai')
    # import load_data
    # df = read_csv('all.csv')
    # print('load completed')
    # df.to_sql('all-data', con=get_engine(), if_exists='append', index=False, chunksize=10000)