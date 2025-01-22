from polygon import RESTClient
import requests
import datetime
import pandas as pd
import numpy as np
from itertools import compress
import matplotlib.pyplot as plt
import json
import joblib
from datetime import datetime, timedelta
from helper import *
import threading
from typing import Dict, List, Optional
import logging
import time
from dataclasses import dataclass
import queue
from statsmodels.tsa.statespace.sarimax import SARIMAXResults
import warnings
warnings.filterwarnings('ignore')

from Class import DataPreprocessor,ForecastingModel
dataPreprocessor = DataPreprocessor.DataProcessor()
forecaster = ForecastingModel.Forecasting()

client = RESTClient(api_key="9uVdPAECzAY_bSx2gRy1G3YJZVb0w92m")

class ETFSDataLoader:
    def __init__(self, symbol1: str, symbol2: str, model_path: str, scaler_path: str,window_size: int, beta: float, long_threshold: float, short_threshold: float):
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.window_size = window_size
        self.beta = beta
        self.long_threshold = long_threshold
        self.short_threshold = short_threshold
        self.last_date = None
        self.data1 = None
        self.data2 = None
        self.lock = threading.Lock()  # Ensure thread safety
        self.trade_queue = queue.Queue()


class ETFSDataTrigger:
    def __init__(self):
        self.is_running = True
        self.pair_data: Dict[str, ETFSDataLoader] = {}
        self.threads: List[threading.Thread] = []
        self.load_stock_to_trade("ETFs_for_trade.json")
        self.add_pair()
        self.signal_processing_url = "http://127.0.0.1:5000/process_signals"
        self.load_map_dict("map_dict1.json")
        self.load_models()
        self.load_scalers()

    def load_map_dict(self, filepath):
        with open(filepath, 'r') as file:
            self.map_dict = json.load(file)

    def load_stock_to_trade(self, filepath: str):
        with open(filepath, 'r') as file:
            self.pair_json = json.load(file)

    def add_pair(self):
        for pair, data in self.pair_json.items():
            self.pair_data[pair] = ETFSDataLoader(
                data["symbol1"],
                data["symbol2"],
                data['model_path'],
                data['scaler_path'],
                data["window_size"],
                data['beta'],
                data['long_threshold'],
                data['short_threshold']
            )
            logging.info(f"Added pair {pair} for monitoring")
    
    def load_models(self):
        model_dict = {}
        for symbol, data1 in self.pair_data.items():
            logging.info(f"Loading model for {symbol} from {data1.model_path}")
            model_path = data1.model_path
            model_dict[symbol] = SARIMAXResults.load(model_path)
        self.models = model_dict
    
    def load_scalers(self):
        scaler_dict={}
        for symbol, data1 in self.pair_data.items():
            scaler_path = data1.scaler_path
            scaler_dict[symbol]=joblib.load(scaler_path)
        self.scalers = scaler_dict
    
    def data_cleaning(self, df_price: pd.DataFrame):
        # Check for duplicate rows and print the count (not used further)
        duplicates_count = df_price.duplicated().sum()
        if duplicates_count > 0:
            print("Data contain duplicate value")
        else:
            print("Data does not contain duplicate value")
        # Check for null values in the price data
        null_values = dataPreprocessor.check_nan_in_individual_cols(df_price)
        null_threshold = 10000

        # Identify columns to drop based on a null value threshold
        columns_to_drop = [col for col, null_count in null_values if null_count > null_threshold]
        df_price.drop(columns=columns_to_drop, inplace=True)
        
        # Handle null values in training and testing datasets
        if len(null_values) > 0:
            # print("Handling null values")
            train_df = dataPreprocessor.random_and_interpolate_strategy(df_price, interpolate_limit=5)

            # Check for remaining null values
            train_null_value = dataPreprocessor.check_null_after_filling_nan(train_df)
            if len(train_null_value):
                print("No valid values left in the data")

        # Detect and handle outliers in training and testing datasets
        outliers, desc_df = dataPreprocessor.detect_outlier(train_df)
        threshold = 10.0  # Define an outlier threshold
        if len(outliers) > 0:
            train_df = dataPreprocessor.handle_outlier(desc_df, outliers, train_df, threshold=threshold)
        return train_df
    
    def predict_with_model(self, model_name, symbol1, symbol2, test_df, beta, long_threshold, short_threshold):
        try:
            model=self.models[model_name]
            scaler=self.scalers[model_name]
            test_df['spread'] = test_df[symbol2] - beta*test_df[symbol1]
            test_df.drop(columns=[symbol1,symbol2],inplace=True)

            model_pred_len = len(model.predict())
            test_df = forecaster.create_features(test_df, lag_values=2, window_size=3)
            test_df = forecaster.create_data(test_df)
            target_test = test_df['next_spread']
            to_scale_df = test_df.drop(columns='next_spread')
            scaled_test = scaler.transform(to_scale_df)
            scaled_test = pd.DataFrame(data=scaled_test, index=to_scale_df.index, columns=to_scale_df.columns)
            scaled_test['next_spread'] = target_test
            test_df = scaled_test

            exog_test = test_df[['spread',
                                'lag1',
                                'lag2',
                                'ma',
                                'rsi',
                                'derivative',
                                'second_derivative',
                                'EMA12',
                                'EMA26',
                                'MACD',
                                'Signal_Line']]
            
            predictions = model.predict(start=model_pred_len, end=model_pred_len + len(test_df) - 1, exog=exog_test)
            pred_spread = np.array(predictions.tolist())
            # inverse-transform
            s = scaler.inverse_transform(exog_test)
            res = pd.DataFrame(data=s, index=exog_test.index, columns=exog_test.columns)
            res['next_spread'] = target_test
            act = res['spread'].tolist()
            pct_change1 = ((pred_spread - act) / act) * 100            

            signal = forecaster.get_long_short_signal(
                                                    short_threshold=short_threshold,
                                                    long_threshold=long_threshold,
                                                    pct_change=pct_change1)
            return signal
        except Exception as e:
            logging.error(f"Error in prediction function:- {e}")

    def trigger(self, pair: str, merged_data: pd.DataFrame):
        
        merged_data = self.data_cleaning(merged_data)
        model_name = pair
        symbol1 = self.pair_data[pair].symbol1
        symbol2 = self.pair_data[pair].symbol2
        beta = self.pair_data[pair].beta
        long_threshold = self.pair_data[pair].long_threshold
        short_threshold = self.pair_data[pair].short_threshold
        signal = self.predict_with_model(model_name, symbol1, symbol2, merged_data, beta, long_threshold, short_threshold)

        # Prepare the payload
        payload = {
            "ETF_Pair":pair,
            "symbol1": self.map_dict[symbol1],
            "symbol2": self.map_dict[symbol2],
            "signal": signal
        }
        # Send the payload
        response = requests.post(self.signal_processing_url, json=payload)
        if response.status_code != 200:
            logging.error(f"Trigger failed for pair {pair}: {response.json()}")


    def get_data_training(self, symbol: str, to_date: pd.Timestamp):
        # Fetch data for a single symbol
        try:
            print('inside get_data_training function',symbol,to_date)
            client = RESTClient(api_key="9uVdPAECzAY_bSx2gRy1G3YJZVb0w92m") 
            # to_date = (to_date - timedelta(minutes=5)).floor('5min')
            aggs = []
            from_date = (to_date - timedelta(days=7)).date()
            for agg in client.list_aggs(ticker=symbol, multiplier=5, timespan="minute", from_=from_date, to=to_date):
                aggs.append(agg)

            data_dicts = [
                {
                    'Open': agg.open,
                    'High': agg.high,
                    'Low': agg.low,
                    'Close': agg.close,
                    'Volume': agg.volume,
                    'timestamp': agg.timestamp
                }
                for agg in aggs
            ]

            df = pd.DataFrame(data_dicts)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert('America/New_York')
            # df = df[(df['timestamp'].dt.time >= pd.Timestamp('09:30:00').time()) & (df['timestamp'].dt.time <= pd.Timestamp('16:00:00').time())]
            df=df[['timestamp','Close']]
            df.rename(columns={
                        "Close": symbol
                    }, inplace=True)
            df.set_index('timestamp', inplace=True)
            df.sort_values("timestamp", inplace=True)
            
            return df
        except Exception as e:
            logging.error(f"Error in fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def monitor_trades(self, pair: str):
        pair_data = self.pair_data[pair]
        print(f"Monitoring {pair} for data updates...")
        while self.is_running:
            try:
                to_date = pd.Timestamp.now(tz='UTC').floor('S').tz_localize(None)
                print('to_date now --->',to_date)
                to_date = (to_date - timedelta(minutes=15)).floor('5min')
                print(f"Fetching data for pair {pair} at {to_date}")
                time.sleep(1)
                data1 = self.get_data_training(pair_data.symbol1, to_date)
                data2 = self.get_data_training(pair_data.symbol2, to_date)
                if data1.empty or data2.empty:
                    print(f"No data available for pair {pair} at {to_date}")
                    continue
                merged_data = pd.merge_asof(data1, data2, on="timestamp")
                merged_data.set_index('timestamp', inplace=True)
                if not merged_data.empty:
                    # Update last_date and return data if new data is found
                    current_last_date = merged_data.index[-1]
                    previous_last_date = self.pair_data[pair].last_date
                    print('current_last_date------>',current_last_date)
                    print('previous_last_date------>',previous_last_date)
            
                    if not previous_last_date or current_last_date > previous_last_date:
                        print("New data found, updating last_date and triggering signal")
                        self.pair_data[pair].last_date = current_last_date
                        if len(merged_data) >= self.pair_json[pair]["window_size"]:
                            print("data get successfully")
                            self.trigger(pair, merged_data)
                    else:
                        print("No new data since last update")
            except Exception as e:
                logging.error(f"Error while monitoring pair {pair}: {e}")
    
    # def monitor_trades(self, pair: str):
    #     pair_data = self.pair_data[pair]
    #     print(f"Monitoring {pair} for data updates...")
    #     while self.is_running:
    #         try:
    #             # to_date= "2024-12-02 09:30:00"
    #             # to_date = pd.Timestamp(to_date)
    #             # to_date = pd.Timestamp.now(tz='UTC').floor('S').tz_localize(None)
    #             base_date = pd.Timestamp("2024-12-16 13:25:00")
    #             for zz in range(5, 500001, 5): 
    #                 # Calculate the total timedelta in minutes
    #                 time_delta = timedelta(minutes=zz)
    #                 to_date = base_date + time_delta  # Increment base date by the time delta
    #                 print('to date---->',to_date)
    #                 to_date = (to_date - timedelta(minutes=5)).floor('5min')
    #                 print(f"Fetching data for pair {pair} at {to_date}")
    #                 time.sleep(1)
    #                 data1 = self.get_data_training(pair_data.symbol1, to_date)
    #                 data2 = self.get_data_training(pair_data.symbol2, to_date)
    #                 if data1.empty or data2.empty:
    #                     print(f"No data available for pair {pair} at {to_date}")
    #                     continue
    #                 merged_data = pd.merge_asof(data1, data2, on="timestamp")
    #                 merged_data.set_index('timestamp', inplace=True)
    #                 if not merged_data.empty:
    #                     # Update last_date and return data if new data is found
    #                     current_last_date = merged_data.index[-1]
    #                     previous_last_date = self.pair_data[pair].last_date
    #                     print('current_last_date------>',current_last_date)
    #                     print('previous_last_date------>',previous_last_date)
                
    #                     if not previous_last_date or current_last_date > previous_last_date:
    #                         print("New data found, updating last_date and triggering signal")
    #                         self.pair_data[pair].last_date = current_last_date
    #                         if len(merged_data) >= self.pair_json[pair]["window_size"]:
    #                             print("data get successfully")
    #                             self.trigger(pair, merged_data)
    #                     else:
    #                         print("No new data since last update")
    #         except Exception as e:
    #             logging.error(f"Error while monitoring pair {pair}: {e}")

    def start(self):
        self.is_running = True
        for pair in self.pair_json.keys():
            thread = threading.Thread(target=self.monitor_trades, args=(pair,))
            thread.start()
            self.threads.append(thread)

    def stop(self):
        self.is_running = False
        for thread in self.threads:
            thread.join()

