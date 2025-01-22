import os
import socket
import threading
import pandas as pd
from api import bet_url
from concurrent.futures import ThreadPoolExecutor

# from utils import getMarketBookBestOffers, getMarketStartTime, getRunnersInfo, placeBackBet, placeLayBet

def strategy_1(surface,market_catalogue,SSOID):
    import datetime
    import requests
    import http.client
    import time
    import pytz
    import urllib , json
    success_bets = []
    threads = []
    fail_bets = []
    strategy_name = 'Strategy 1'
    market_catalogue = [
    match for match in market_catalogue
    if all('/' not in runner['runnerName'] for runner in match['runners'])
    # and match['totalMatched'] > 1000
]
    headers = {'X-Application': 'M90yVlWTGZfS7rEi', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}

    target_date = datetime.datetime.now()    
    marketStartTime = target_date.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%SZ')
    # print('marketStartTime: ', marketStartTime)
    
    def getMarketStartTime(market_dict):
        
        # Extract 'marketStartTime' from the dictionary
        utc_time_str = market_dict.get('marketStartTime')
        if not utc_time_str:
            raise ValueError("The key 'marketStartTime' is missing in the input dictionary.")

        utc_time = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")

        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone()

        return local_time.replace(tzinfo=None)


    def getRunnersInfo(market):
        # Extract the runners from the market dictionary
        runners = market.get('runners', [])
        
        # Check if there are at least two runners in the list
        if len(runners) >= 2:
            runner1_name = runners[0]['runnerName']
            runner1_selectionID = runners[0]['selectionId']
            runner2_name = runners[1]['runnerName']
            runner2_selectionID = runners[1]['selectionId']
            return runner1_name, runner1_selectionID, runner2_name, runner2_selectionID
        else:
            return None, None, None, None


    def getMarketBookBestOffers(marketId):
        # print ('Calling listMarketBook to read prices for the Market with ID :' + marketId)
        market_book_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"marketIds":["' + marketId + '"],"priceProjection":{"priceData":["EX_ALL_OFFERS"]}}, "id": 1}'
        """
        print  (market_book_req)
        """
        req = urllib.request.Request(bet_url , market_book_req.encode('utf-8'), headers)
        response = urllib.request.urlopen(req)
        jsonResponse = response.read()
        market_book_response = jsonResponse.decode('utf-8')
        """
        print (market_book_response)
        """
        market_book_loads = json.loads(market_book_response)
        try:
            market_book_result = market_book_loads['result']
            return market_book_result
        except:
            print  ('Exception from API-NG' + str(market_book_result['error']))
            exit()


    def placeBackBet(marketId, selectionId, price, size):
        # print(price)
        side = 'BACK'
        
        if( marketId is not None and selectionId is not None):
            # print ('Calling placeOrder for marketId :' + marketId + ' with selection id :' + str(selectionId) + ' on Odds :' + str(price))
            place_order_Req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"' + marketId + '","instructions":'\
                                                                                                                                    '[{"selectionId":"' + str(selectionId) + '","handicap":"0","side":"' + str(side) + '","orderType":"LIMIT","limitOrder":{"size":"' + str(size) + '","price":"' + str(price) + '","persistenceType":"PERSIST"}}]}, "id": 1}'
            # print (place_order_Req)

            req = urllib.request.Request(bet_url , place_order_Req.encode('utf-8'), headers)
            response = urllib.request.urlopen(req)
            jsonResponse = response.read()
            place_order_Response = jsonResponse.decode('utf-8')
            print('place_order_Response : ' , place_order_Response)
            place_order_load = json.loads(place_order_Response)
            try:
                place_order_result = place_order_load['result']
                print ('Place order status is ' + place_order_result['status'])

                if place_order_result['status'] == 'FAILURE':
                    print ('Place order error status is ' + place_order_result['errorCode'])
                    print ('Reason for Place order failure is ' + place_order_result['instructionReports'][0]['errorCode'])
                    error_code = place_order_result['instructionReports'][0]['errorCode']
                    bet_id = None
                else:
                    error_code = ''    
                    bet_id = place_order_result['instructionReports'][0].get('betId', None)
            except:
                print  ('Exception from API-NG' + str(place_order_result['error']))
                bet_id = None

            return (place_order_result['status'],error_code, side, price, bet_id)        
        # if place_order_result['status'] == 'FAILURE':
        #     return False
        # else :
        #     return True


    def placeLayBet(marketId, selectionId, price, size):
        # print(price)
        side = 'LAY'
        
        if( marketId is not None and selectionId is not None):
            # print ('Calling placeOrder for marketId :' + marketId + ' with selection id :' + str(selectionId) + ' on Odds :' + str(price))
            place_order_Req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId":"' + marketId + '","instructions":'\
                                                                                                                                    '[{"selectionId":"' + str(selectionId) + '","handicap":"0","side":"' + str(side) + '","orderType":"LIMIT","limitOrder":{"size":"' + str(size) + '","price":"' + str(price) + '","persistenceType":"PERSIST"}}]}, "id": 1}'
            # print (place_order_Req)

            req = urllib.request.Request(bet_url , place_order_Req.encode('utf-8'), headers)
            response = urllib.request.urlopen(req)
            jsonResponse = response.read()
            place_order_Response = jsonResponse.decode('utf-8')

            place_order_load = json.loads(place_order_Response)
            try:
                place_order_result = place_order_load['result']
                
                print ('Place order status is ' + place_order_result['status'])
                if place_order_result['status'] == 'FAILURE':
                    print ('Place order error status is ' + place_order_result['errorCode'])
                    print ('Reason for Place order failure is ' + place_order_result['instructionReports'][0]['errorCode'])
                    error_code = place_order_result['instructionReports'][0]['errorCode']
                    bet_id = None
                else:
                    error_code = ''
                    bet_id = place_order_result['instructionReports'][0].get('betId', None)
            except:
                print  ('Exception from API-NG' + str(place_order_result['error']))
                bet_id = None

            return (place_order_result['status'],error_code, side, price, bet_id)




#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def getMarketId(market):
        return market['marketId']
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def getAmount(market):
        return market['amount']
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def getBothPrice(market_book, selection_id):
        # Loop through each market in the market_book list
        for market in market_book:
            # Loop through each runner in the 'runners' list of the market
            for runner in market['runners']:
                # Check if the runner's selectionId matches the provided selection_id
                if runner['selectionId'] == selection_id:
                    # Get the first price from availableToBack if it exists
                    available_to_back = runner.get('ex', {}).get('availableToBack')
                    back_price = available_to_back[0].get('price') if available_to_back else None

                    # Get the first price from availableToLay if it exists
                    available_to_lay = runner.get('ex', {}).get('availableToLay')
                    lay_price = available_to_lay[0].get('price') if available_to_lay else None

                    # Return both back and lay prices as a tuple
                    return back_price, lay_price

        # If no matching runner is found, return None for both prices
        return None, None
#-------------------------------------------------------------------------------------------------------------------------------------------------------    
    def threaded_function(market, market_id, runner1_name, runner2_name, selection_id, match_start_time, last_price_traded, lay_bet_price, lay_stake, lay_bet_list, index):
        # # Define the file path for the Excel file
        # file_name = f"{runner1_name} vs {runner2_name} for strategy 1"
        # file_path = f"odds_data\{file_name}.xlsx"
        
        # # Check if the file exists, if not, create it with the correct header
        # if not os.path.exists(file_path):
        #     df = pd.DataFrame(columns=["current_time", "current_lay_bet_price"])
        #     df.to_excel(file_path, index=False)
        
        while True:
            try:
                current_time = datetime.datetime.now()  # Keep as datetime object
                back_bet_price = last_price_traded
                time.sleep(30)
                print('strategy 1')
                market_book = getMarketBookBestOffers(market_id)
                # print(market_book)
                current_back_bet_price, current_lay_bet_price = getBothPrice(market_book, selection_id)
                print('back_bet_price: ', back_bet_price)
                print('lay_bet_price: ', lay_bet_price)
                print('current_back_bet_price: ', current_back_bet_price)
                print('current_lay_bet_price: ', current_lay_bet_price)
                
                # Append the current_lay_bet_price and current_time to the Excel file
                # new_data = pd.DataFrame([[current_time, current_lay_bet_price]], columns=["current_time", "current_lay_bet_price"])
                # existing_data = pd.read_excel(file_path)
                # updated_data = pd.concat([existing_data, new_data], ignore_index=True)
                # updated_data.to_excel(file_path, index=False)
                
                if current_lay_bet_price < back_bet_price - 0.01 and lay_bet_list[index] != current_lay_bet_price:
                    lay_bet_list.append(current_lay_bet_price)
                    index = index + 1

                print('lay_bet_list : ', lay_bet_list)
                print('index : ', index)
                if lay_bet_list[index - 5] < lay_bet_list[index]:
                    # place Lay order
                    print('lay_bet_list[index - 5] < lay_bet_list[index]')
                    LayBet_status, Lay_bet_reason, type, odds, LayBet_id = placeLayBet(market_id, selection_id, lay_bet_list[index], lay_stake)
                    success_lay_bets_dict['_id'] = int(LayBet_id)
                    success_lay_bets_dict['Match'] = match
                    success_lay_bets_dict['strategy'] = strategy_name
                    success_lay_bets_dict['Type'] = type
                    success_lay_bets_dict['Amount'] = lay_stake
                    success_lay_bets_dict['Odds'] = odds
                    success_lay_bets_dict['Status'] = LayBet_status
                    success_back_bets_dict['Profit/Loss'] = 0
                    break

                if back_bet_price > 1.5:
                    if lay_bet_list[index] < back_bet_price - 0.1:
                        # place Lay Order
                        print('lay_bet_list[index] < back_bet_price - 0.1')
                        LayBet_status, Lay_bet_reason, type, odds, LayBet_id = placeLayBet(market_id, selection_id, lay_bet_list[index], lay_stake)
                        success_lay_bets_dict['_id'] = int(LayBet_id)
                        success_lay_bets_dict['Match'] = match
                        success_lay_bets_dict['strategy'] = strategy_name
                        success_lay_bets_dict['Type'] = type
                        success_lay_bets_dict['Amount'] = lay_stake
                        success_lay_bets_dict['Odds'] = odds
                        success_lay_bets_dict['Status'] = LayBet_status
                        success_back_bets_dict['Profit/Loss'] = 0
                        break
                else:
                    if lay_bet_list[index] < back_bet_price - 0.05:
                        # place Lay Order
                        print('lay_bet_list[index] < back_bet_price - 0.05')
                        LayBet_status, Lay_bet_reason, type, odds, LayBet_id = placeLayBet(market_id, selection_id, lay_bet_list[index], lay_stake)
                        success_lay_bets_dict['_id'] = int(LayBet_id)
                        success_lay_bets_dict['Match'] = match
                        success_lay_bets_dict['strategy'] = strategy_name
                        success_lay_bets_dict['Type'] = type
                        success_lay_bets_dict['Amount'] = lay_stake
                        success_lay_bets_dict['Odds'] = odds
                        success_lay_bets_dict['Status'] = LayBet_status
                        success_back_bets_dict['Profit/Loss'] = 0
                        break
                print('current_time : ', current_time)
                print('match_start_time : ', match_start_time)
                print('match_start_time - datetime.timedelta(minutes=10) : ', match_start_time - datetime.timedelta(minutes=10))

                if lay_bet_list[index] == lay_bet_price:
                    print('lay_bet_list[index] == lay_bet_price')
                    LayBet_status, Lay_bet_reason, type, odds, LayBet_id = placeLayBet(market_id, selection_id, lay_bet_list[index], lay_stake)
                    success_lay_bets_dict['_id'] = int(LayBet_id)
                    success_lay_bets_dict['Match'] = match
                    success_lay_bets_dict['strategy'] = strategy_name
                    success_lay_bets_dict['Type'] = type
                    success_lay_bets_dict['Amount'] = lay_stake
                    success_lay_bets_dict['Odds'] = odds
                    success_lay_bets_dict['Status'] = LayBet_status
                    success_back_bets_dict['Profit/Loss'] = 0 
                    break

            except http.client.RemoteDisconnected as e:
                print("RemoteDisconnected: Remote end closed connection without response. Retrying...")
                continue
            except ConnectionAbortedError as e:
                print("ConnectionAbortedError: Connection aborted by host. Retrying...")
                continue
            except socket.gaierror as e:
                print(f"socket.gaierror: {e}. Retrying...")
                continue
            except urllib.error.URLError as e:
                print(f"URLError: {e.reason}. Retrying...")
                continue
            except Exception as e:
                print(f'Other Exception L {e}. Retrying ...')
                continue

        return success_lay_bets_dict
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def tennis_prediction(surface, tourney_date, player1_name, player2_name, best_of, round_):
        import pandas as pd
        import numpy as np
        import seaborn as sns
        import matplotlib.pyplot as plt 
        import warnings
        warnings.filterwarnings('ignore')
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import AdaBoostClassifier
        from sklearn.neural_network import MLPClassifier
        from xgboost import XGBClassifier
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.preprocessing import LabelEncoder
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.metrics import roc_auc_score
        from sklearn.ensemble import ExtraTreesClassifier
        from catboost import CatBoostClassifier
        from scipy.stats import gaussian_kde
        from scipy.integrate import quad
        
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        #------------------------------------------------------------------------------------------------------------------------------------------------
        # Fetching Input Data
        train_df = pd.read_csv('strategies\model data\Train_data.csv')
        df = pd.DataFrame(columns= train_df.columns)
        
        df['surface'] = [surface]
        df['tourney_date'] = [tourney_date]
        df['player1_name'] = [player1_name]
        df['player2_name'] = [player2_name]
        df['best_of'] = [best_of]
        df['round'] = [round_]

        #-------------------------------------------------------------------------------------------------------------------------------------------------
    
        rounds_proirity = {'R128' : 0 , 'R64' : 1, 'R32' :2, 'R16' :3,  'QF':4, 'SF' :5 ,  'F':6}
        for index, row in df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
            date = row['tourney_date']
            
            # Filter train_df to find matches where player1_name is either in player1_name or player2_name
            temp_df_p1 = train_df[(train_df['player1_name'] == player1_name) | (train_df['player2_name'] == player1_name)]
            temp_df_p2 = train_df[(train_df['player1_name'] == player2_name) | (train_df['player2_name'] == player2_name)]
        
            #### For Player 1
            if not temp_df_p1.empty:
                latest_date_p1 = temp_df_p1['tourney_date'].max()
                latest_date_row_p1 = temp_df_p1[temp_df_p1['tourney_date'] == latest_date_p1]
                
                if latest_date_row_p1.shape[0] > 1:
                    latest_date_row_p1['temp'] = latest_date_row_p1['round'].map(rounds_proirity)
                    df_sorted_p1 = latest_date_row_p1.sort_values('temp').drop(columns = 'temp').reset_index(drop=True)
                    latest_row_p1 = df_sorted_p1.tail(1)
                else :
                    latest_row_p1 = latest_date_row_p1
                
                if latest_row_p1['player1_name'].values == player1_name :
                    df.at[index, 'player1_hand'] = latest_row_p1['player1_hand'].values
                    df.at[index, 'player1_ht'] = latest_row_p1['player1_ht'].values
                    df.at[index, 'player1_rank'] = latest_row_p1['player1_rank'].values
                    df.at[index, 'player1_rank_points'] = latest_row_p1['player1_rank_points'].values
                    df.at[index, 'player1_ace_avg'] = latest_row_p1['player1_ace_avg'].values
                    df.at[index, 'player1_df_avg'] = latest_row_p1['player1_df_avg'].values
                    df.at[index, 'player1_1stIn_avg'] = latest_row_p1['player1_1stIn_avg'].values
                    df.at[index, 'player1_1stWon_avg'] = latest_row_p1['player1_1stWon_avg'].values
                    df.at[index, 'player1_2ndWon_avg'] = latest_row_p1['player1_2ndWon_avg'].values
                    df.at[index, 'player1_SvGms_avg'] = latest_row_p1['player1_SvGms_avg'].values
                    df.at[index, 'player1_bpSaved_avg'] = latest_row_p1['player1_bpSaved_avg'].values
                    df.at[index, 'player1_bpFaced_avg'] = latest_row_p1['player1_bpFaced_avg'].values            
                else : 
                    df.at[index, 'player1_hand'] = latest_row_p1['player2_hand'].values
                    df.at[index, 'player1_ht'] = latest_row_p1['player2_ht'].values
                    df.at[index, 'player1_rank'] = latest_row_p1['player2_rank'].values
                    df.at[index, 'player1_rank_points'] = latest_row_p1['player2_rank_points'].values   
                    df.at[index, 'player1_ace_avg'] = latest_row_p1['player2_ace_avg'].values
                    df.at[index, 'player1_df_avg'] = latest_row_p1['player2_df_avg'].values
                    df.at[index, 'player1_1stIn_avg'] = latest_row_p1['player2_1stIn_avg'].values
                    df.at[index, 'player1_1stWon_avg'] = latest_row_p1['player2_1stWon_avg'].values
                    df.at[index, 'player1_2ndWon_avg'] = latest_row_p1['player2_2ndWon_avg'].values
                    df.at[index, 'player1_SvGms_avg'] = latest_row_p1['player2_SvGms_avg'].values
                    df.at[index, 'player1_bpSaved_avg'] = latest_row_p1['player2_bpSaved_avg'].values
                    df.at[index, 'player1_bpFaced_avg'] = latest_row_p1['player2_bpFaced_avg'].values                  
            else : 
                # print('Player 1 not found!!!!!')
                # print(player1_name)
                return []
            
            #### For Player 2
            if not temp_df_p2.empty:
                latest_date_p2 = temp_df_p2['tourney_date'].max()
                latest_date_row_p2 = temp_df_p2[temp_df_p2['tourney_date'] == latest_date_p2]
                
                if latest_date_row_p2.shape[0] > 1:
                    latest_date_row_p2['temp'] = latest_date_row_p2['round'].map(rounds_proirity)
                    df_sorted_p2 = latest_date_row_p2.sort_values('temp').drop(columns = 'temp').reset_index(drop=True)
                    latest_row_p2 = df_sorted_p2.tail(1)
                else :
                    latest_row_p2 = latest_date_row_p2
                
                if latest_row_p2['player1_name'].values == player2_name :
                    df.at[index, 'player2_hand'] = latest_row_p2['player1_hand'].values
                    df.at[index, 'player2_ht'] = latest_row_p2['player1_ht'].values
                    df.at[index, 'player2_rank'] = latest_row_p2['player1_rank'].values
                    df.at[index, 'player2_rank_points'] = latest_row_p2['player1_rank_points'].values
                    df.at[index, 'player2_ace_avg'] = latest_row_p2['player1_ace_avg'].values
                    df.at[index, 'player2_df_avg'] = latest_row_p2['player1_df_avg'].values
                    df.at[index, 'player2_1stIn_avg'] = latest_row_p2['player1_1stIn_avg'].values
                    df.at[index, 'player2_1stWon_avg'] = latest_row_p2['player1_1stWon_avg'].values
                    df.at[index, 'player2_2ndWon_avg'] = latest_row_p2['player1_2ndWon_avg'].values
                    df.at[index, 'player2_SvGms_avg'] = latest_row_p2['player1_SvGms_avg'].values
                    df.at[index, 'player2_bpSaved_avg'] = latest_row_p2['player1_bpSaved_avg'].values
                    df.at[index, 'player2_bpFaced_avg'] = latest_row_p2['player1_bpFaced_avg'].values            
                else : 
                    df.at[index, 'player2_hand'] = latest_row_p2['player2_hand'].values
                    df.at[index, 'player2_ht'] = latest_row_p2['player2_ht'].values
                    df.at[index, 'player2_rank'] = latest_row_p2['player2_rank'].values
                    df.at[index, 'player2_rank_points'] = latest_row_p2['player2_rank_points'].values   
                    df.at[index, 'player2_ace_avg'] = latest_row_p2['player2_ace_avg'].values
                    df.at[index, 'player2_df_avg'] = latest_row_p2['player2_df_avg'].values
                    df.at[index, 'player2_1stIn_avg'] = latest_row_p2['player2_1stIn_avg'].values
                    df.at[index, 'player2_1stWon_avg'] = latest_row_p2['player2_1stWon_avg'].values
                    df.at[index, 'player2_2ndWon_avg'] = latest_row_p2['player2_2ndWon_avg'].values
                    df.at[index, 'player2_SvGms_avg'] = latest_row_p2['player2_SvGms_avg'].values
                    df.at[index, 'player2_bpSaved_avg'] = latest_row_p2['player2_bpSaved_avg'].values
                    df.at[index, 'player2_bpFaced_avg'] = latest_row_p2['player2_bpFaced_avg'].values                  
            else : 
                # print('Player 2 not found!!!!!!!!')
                # print(player2_name)
                return []   
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Player Match History Data
        import json
        
        # Specify the path to your JSON file
        file_path = 'strategies\model data\player_match_history.json'
        
        # Open the file and load the content
        with open(file_path, 'r') as file:
            player_match_history = json.load(file)
        
        for index, row in df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
        
            # Update the DataFrame with the last 10 matches win/loss
            player1_last10 = player_match_history[player1_name][-10:]
            player2_last10 = player_match_history[player2_name][-10:]
            
            df.loc[row.name, 'player1_last10_wins'] = sum(1 for match in player1_last10 if match == 'win')
            # df.loc[row.name, 'player1_last10_losses'] = sum(1 for match in player1_last10 if match == 'loss')
            df.loc[row.name, 'player2_last10_wins'] = sum(1 for match in player2_last10 if match == 'win')
            # df.loc[row.name, 'player2_last10_losses'] = sum(1 for match in player2_last10 if match == 'loss')
            
            # Calculate win ratios
            player1_total_matches = len(player1_last10)
            player2_total_matches = len(player2_last10)
            
            df.loc[row.name, 'player1_last10_win_ratio'] = (
                df.loc[row.name, 'player1_last10_wins'] / player1_total_matches if player1_total_matches > 0 else 0.0
            )
            df.loc[row.name, 'player2_last10_win_ratio'] = (
                df.loc[row.name, 'player2_last10_wins'] / player2_total_matches if player2_total_matches > 0 else 0.0
            )
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Player Surface Win/Loss Data
        import json
        
        # Specify the path to your JSON file
        file_path = 'strategies\model data\surface_win_loss.json'
        
        # Open the file and load the content
        with open(file_path, 'r') as file:
            surface_win_loss = json.load(file)
        
        
        surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
        
        for index, row in df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
            surface = row['surface']
        # Update the DataFrame with the historical win/loss by surface
            for s in surfaces:
                if player1_name in surface_win_loss[s]:
                    df.loc[row.name, f'player1_{s}_wins'] = surface_win_loss[s][player1_name]['wins']
                    df.loc[row.name, f'player1_{s}_losses'] = surface_win_loss[s][player1_name]['losses']
                    # Calculate the win ratio for player 1
                    total_matches_player1 = surface_win_loss[s][player1_name]['wins'] + surface_win_loss[s][player1_name]['losses']
                    if total_matches_player1 > 0:
                        df.loc[row.name, f'player1_{s}_win_ratio'] = surface_win_loss[s][player1_name]['wins'] / total_matches_player1
        
                if player2_name in surface_win_loss[s]:
                    df.loc[row.name, f'player2_{s}_wins'] = surface_win_loss[s][player2_name]['wins']
                    df.loc[row.name, f'player2_{s}_losses'] = surface_win_loss[s][player2_name]['losses']
                    # Calculate the win ratio for player 2
                    total_matches_player2 = surface_win_loss[s][player2_name]['wins'] + surface_win_loss[s][player2_name]['losses']
                    if total_matches_player2 > 0:
                        df.loc[row.name, f'player2_{s}_win_ratio'] = surface_win_loss[s][player2_name]['wins'] / total_matches_player2
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Player Surface Win/Loss last 10 Data
        import json
        
        # Specify the path to your JSON file
        file_path = 'strategies\model data\surface_win_loss_last10.json'
        
        # Open the file and load the content
        with open(file_path, 'r') as file:
            surface_win_loss_last10 = json.load(file)
        
        
        surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']
        
        for index, row in df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
            surface = row['surface']
        
            for s in surfaces:
                player1_wins = sum(1 for result in surface_win_loss_last10[s][player1_name] if result == 'W')
                player1_losses = sum(1 for result in surface_win_loss_last10[s][player1_name] if result == 'L')
                player2_wins = sum(1 for result in surface_win_loss_last10[s][player2_name] if result == 'W')
                player2_losses = sum(1 for result in surface_win_loss_last10[s][player2_name] if result == 'L')
        
                df.loc[row.name, f'player1_{s}_last10_wins'] = player1_wins
                df.loc[row.name, f'player1_{s}_last10_losses'] = player1_losses
                df.loc[row.name, f'player2_{s}_last10_wins'] = player2_wins
                df.loc[row.name, f'player2_{s}_last10_losses'] = player2_losses
        
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Player Overall Match Win/Loss
        import json
        
        # Specify the path to your JSON file
        file_path = 'strategies\model data\player_match_history_overall.json'
        
        # Open the file and load the content
        with open(file_path, 'r') as file:
            player_match_history_overall = json.load(file)
        
        
        for index, row in df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
        
            # Update the DataFrame with the overall wins/losses
            df.loc[row.name, 'player1_overall_wins'] = sum(1 for match in player_match_history_overall[player1_name] if match == 'win')
            df.loc[row.name, 'player1_overall_losses'] = sum(1 for match in player_match_history_overall[player1_name] if match == 'loss')
            df.loc[row.name, 'player2_overall_wins'] = sum(1 for match in player_match_history_overall[player2_name] if match == 'win')
            df.loc[row.name, 'player2_overall_losses'] = sum(1 for match in player_match_history_overall[player2_name] if match == 'loss')
        
            # Calculate the win ratios
            player1_total_matches = df.loc[row.name, 'player1_overall_wins'] + df.loc[row.name, 'player1_overall_losses']
            player2_total_matches = df.loc[row.name, 'player2_overall_wins'] + df.loc[row.name, 'player2_overall_losses']
            
            df.loc[row.name, 'player1_overall_win_ratio'] = df.loc[row.name, 'player1_overall_wins'] / player1_total_matches if player1_total_matches > 0 else 0
            df.loc[row.name, 'player2_overall_win_ratio'] = df.loc[row.name, 'player2_overall_wins'] / player2_total_matches if player2_total_matches > 0 else 0
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Players Head to Head Data
        import json
        
        # Specify the path to your JSON file
        file_path = 'strategies\model data\h2h_dict.json'
        
        # Open the file and load the content
        with open(file_path, 'r') as file:
            h2h_dict = json.load(file)
        
        # Now, 'data' is a Python dictionary containing the JSON data
        # print(data)
        
        
        for index, row in df.iterrows():
            player1 = row['player1_name']
            player2 = row['player2_name']
            # print(player1)
            # print(player2)
            
            flag = True
            if player1 in h2h_dict and player2 in h2h_dict[player1]:
                wins = h2h_dict[player1][player2]['wins']
                losses = h2h_dict[player1][player2]['losses']
                df.at[index, 'player1_h2h_wins'] = wins
                df.at[index, 'player1_h2h_losses'] = losses
                df.at[index, 'player1_h2h_win_ratio'] = wins / (wins + losses) if (wins + losses) > 0 else 0
                flag = False
            if player2 in h2h_dict and player1 in h2h_dict[player2]:
                wins = h2h_dict[player2][player1]['wins']
                losses = h2h_dict[player2][player1]['losses']
                df.at[index, 'player2_h2h_wins'] = wins
                df.at[index, 'player2_h2h_losses'] = losses
                df.at[index, 'player2_h2h_win_ratio'] = wins / (wins + losses) if (wins + losses) > 0 else 0
        
            if flag:
                # print(f'{player1} and {player2} Never Played Together before this Match')
                df.at[index, 'player1_h2h_wins'] = 0
                df.at[index, 'player1_h2h_losses'] = 0
                df.at[index, 'player1_h2h_win_ratio'] = 0    
                df.at[index, 'player2_h2h_wins'] = 0
                df.at[index, 'player2_h2h_losses'] = 0
                df.at[index, 'player2_h2h_win_ratio'] = 0    
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Player Surface Head to Head Data
        import json
        
        # Specify the path to your JSON file
        file_path = 'strategies\model data\surface_h2h_dict.json'
        
        # Open the file and load the content
        with open(file_path, 'r') as file:
            surface_h2h_dict = json.load(file)
        
        # Now, 'data' is a Python dictionary containing the JSON data
        # print(data)
        
        
        for index, row in df.iterrows():
            player1 = row['player1_name']
            player2 = row['player2_name']
            surface = row['surface']
            flag = True
            # Update wins, losses, and win ratios for player1
            if surface in surface_h2h_dict:
                
                if player1 in surface_h2h_dict[surface] and player2 in surface_h2h_dict[surface][player1]:
                    player1_wins = surface_h2h_dict[surface][player1][player2]['wins']
                    player1_losses = surface_h2h_dict[surface][player1][player2]['losses']
                    df.at[index, 'player1_surface_h2h_wins'] = player1_wins
                    df.at[index, 'player1_surface_h2h_losses'] = player1_losses
                    df.at[index, 'player1_surface_h2h_win_ratio'] = player1_wins / (player1_wins + player1_losses) if (player1_wins + player1_losses) > 0 else 0.0
                    flag = False
                # Update wins, losses, and win ratios for player2
                if player2 in surface_h2h_dict[surface] and player1 in surface_h2h_dict[surface][player2]:
                    player2_wins = surface_h2h_dict[surface][player2][player1]['wins']
                    player2_losses = surface_h2h_dict[surface][player2][player1]['losses']
                    df.at[index, 'player2_surface_h2h_wins'] = player2_wins
                    df.at[index, 'player2_surface_h2h_losses'] = player2_losses
                    df.at[index, 'player2_surface_h2h_win_ratio'] = player2_wins / (player2_wins + player2_losses) if (player2_wins + player2_losses) > 0 else 0.0
        
            if flag:
                # print(f'{player1} and {player2} Never Played Together before this Match')
                df.at[index, 'player1_surface_h2h_wins'] = 0
                df.at[index, 'player1_surface_h2h_losses'] = 0
                df.at[index, 'player1_surface_h2h_win_ratio'] = 0    
                df.at[index, 'player2_surface_h2h_wins'] = 0
                df.at[index, 'player2_surface_h2h_losses'] = 0
                df.at[index, 'player2_surface_h2h_win_ratio'] = 0            
        
        df.fillna(0 , inplace=True)
        
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Final Prediction
        dff = df.drop(columns=['Winner', 'tourney_date','score', 'player1_name', 'player2_name','Winner_name','player1_Grass_last10_losses','player2_Grass_last10_losses', 'player1_set_wins', 'player2_set_wins',
               'set_diff', 'total_games'])
        
        import pickle
        
        dff[['player1_hand', 'player2_hand']] = dff[['player1_hand', 'player2_hand']].astype(str)
        
        with open('strategies\model data\one_hot_encoder.pkl', 'rb') as file:
            loaded_encoder = pickle.load(file)
        
        encoded_columns = loaded_encoder.transform(dff[['player1_hand', 'player2_hand', 'round', 'surface']])
        
        encoded_column_names = loaded_encoder.get_feature_names_out(['player1_hand', 'player2_hand', 'round', 'surface'])
        
        # Print column names to debug
        # print("Encoded column names:", encoded_column_names)
        
        # Create a dataframe with the encoded columns
        encoded_df = pd.DataFrame(encoded_columns, columns=encoded_column_names)
        
        # Concatenate the encoded columns with the original dataframe
        dff = pd.concat([dff.drop(['player1_hand', 'player2_hand', 'round', 'surface'], axis=1), encoded_df], axis=1)
        
        
        import pickle
        
        # Load the scaler from a file
        with open('strategies\model data\minmax_scaler.pkl', 'rb') as file:
            scaler = pickle.load(file)
        
        # Now you can use the scaler to transform your data
        scaled_df = scaler.transform(dff)
        
        # Load the model
        loaded_model = CatBoostClassifier()
        loaded_model.load_model('strategies\model data\catboost_model.pkl')
        
        # You can then use the loaded model for predictions
        y_test_pred_loaded = loaded_model.predict(scaled_df)
        y_test_pred_proba = loaded_model.predict_proba(scaled_df)
        
        prediction_df = pd.DataFrame(y_test_pred_loaded,columns=['Prediction'])
        predict_prob_df = pd.DataFrame(y_test_pred_proba , columns =['Player1_Win_prob (0)','Player2_Win_prob (1)'])
        actual_df = df[['tourney_date','player1_name', 'player2_name','surface','round','best_of']]
        Final_df = pd.concat([actual_df, prediction_df,predict_prob_df], axis=1)
    
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # MoneyLine Odds
    
        # Create new columns for betting odds
        Final_df['Player1_Fair_Odds'] = 1 / Final_df['Player1_Win_prob (0)']
        Final_df['Player2_Fair_Odds'] = 1 / Final_df['Player2_Win_prob (1)']
        
        # Optional: round the odds to 2 decimal places
        Final_df['Player1_Fair_Odds'] = Final_df['Player1_Fair_Odds'].round(2)
        Final_df['Player2_Fair_Odds'] = Final_df['Player2_Fair_Odds'].round(2)
        
        # Apply desired margin (e.g., 10%)
        margin = 1.10
        
        # Final_df['overround'] = (1/Final_df['Player1_Fair_Odds']) + (1/Final_df['Player2_Fair_Odds'])
        
        # Calculate adjusted odds with the margin
        Final_df['Player1_adjusted_Odds'] = Final_df['Player1_Fair_Odds'] / margin
        Final_df['Player2_adjusted_Odds'] = Final_df['Player2_Fair_Odds'] / margin
        
        # Optionally round the odds
        Final_df['Player1_adjusted_Odds'] = Final_df['Player1_adjusted_Odds'].round(2)
        Final_df['Player2_adjusted_Odds'] = Final_df['Player2_adjusted_Odds'].round(2)
    
        #-------------------------------------------------------------------------------------------------------------------------------------------------
        # Point Spread (Handicap) Odds
        Final_df['probability_at_0_5'] = np.nan
        # # Final_df['probability_at_minus_0_5'] = np.nan
        Final_df['probability_at_1_5'] = np.nan
        # Final_df['probability_at_minus_1_5'] = np.nan
        Final_df['probability_at_2_5'] = np.nan
        # Final_df['probability_at_minus_2_5'] = np.nan
        
        for index, row in Final_df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
            best_of = row['best_of']  
        
            # Find matching rows in the main dataframe train_df
            temp_df = train_df[(((train_df['player1_name'] == player1_name) & 
                                (train_df['player2_name'] == player2_name)) | 
                               ((train_df['player1_name'] == player2_name) & 
                                (train_df['player2_name'] == player1_name))) & 
                              (train_df['best_of'] == best_of)]
            # If temp_df is empty, skip this iteration
            # print(temp_df.shape)
            if temp_df.empty | temp_df.shape[0] == 1:
                continue
            
            # Extract set_diff column
            set_diff = temp_df['set_diff']
            # if set_diff.nunique() == 1:
            #     continue
                        
            # Create a Gaussian KDE for the data
            kde = gaussian_kde(set_diff, bw_method=0.5)  # bw_method controls the bandwidth
                
            # Integrate the KDE from the minimum to specific points to get the CDF values
            probability_at_0_5, _ = quad(kde, -np.inf, 0.5)
            probability_at_1_5, _ = quad(kde, -np.inf, 1.5)
            probability_at_2_5, _ = quad(kde, -np.inf, 2.5)
                
            # Round the probabilities to 4 decimal places
            # print(probability_at_0_5)
            
            probability_at_0_5 = round(probability_at_0_5, 4)
            probability_at_1_5 = round(probability_at_1_5, 4)
            probability_at_2_5 = round(probability_at_2_5, 4)
            
            # Store the probabilities in the Final_df
            Final_df.at[index, 'probability_at_0_5'] = probability_at_0_5
            Final_df.at[index, 'probability_at_1_5'] = probability_at_1_5
            Final_df.at[index, 'probability_at_2_5'] = probability_at_2_5
                        
        for index, row in Final_df.iterrows():
            player1_name = row['player1_name']
            player2_name = row['player2_name']
            best_of = row['best_of']  
            
            # Find matching rows in the main dataframe train_df
            temp_df = train_df[(((train_df['player1_name'] == player1_name) & 
                                (train_df['player2_name'] == player2_name)) | 
                               ((train_df['player1_name'] == player2_name) & 
                                (train_df['player2_name'] == player1_name))) & 
                              (train_df['best_of'] == best_of)]
            
            # If temp_df is empty, skip this iteration
            # print(temp_df.shape)
            if temp_df.empty | temp_df.shape[0] == 1:
                continue
            
            # Extract set_diff column
            total_games = temp_df['total_games']
            if total_games.nunique() == 1:
                continue
            
            # Step 1: Calculate the mean of the 'total_games' column
            # print(player1_name , ',' ,player2_name)
            # print(total_games)
            mean_total_games = total_games.mean()
            # print(mean_total_games)
            def round_replace_and_convert(value):
                # Step 1: Round the value to 2 decimal points
                rounded_value = round(value, 2)
                            
                # Step 2: Convert the rounded value to a string
                value_str = f"{rounded_value:.2f}"
                                                                                
                # Step 3: Replace the digit after the decimal with '5' if it's not already '5'
                if value_str[3] != '5':
                    value_str = f"{value_str[:3]}5"
                                                                                                                                                                                                        
                # Step 4: Convert the modified string to an integer
                # Convert to float first to handle cases where the number might have decimals
                final_value = float(value_str)
                        
                return final_value
                
            processed_mean_total_games = round_replace_and_convert(mean_total_games)
            processed_mean_total_games_minus_1 = processed_mean_total_games - 1
            processed_mean_total_games_plus_1 = processed_mean_total_games + 1

        margin = 1.10
        
        Final_df.fillna(0 , inplace=True)
        
        return Final_df
    
#--------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # size = 0
    
    # Process each filtered market to extract and analyze match details
    for market in market_catalogue:
        success_back_bets_dict = {"_id" : 0, "Match": '',"strategy": '',"Amount": 0,"Type": '',"Odds": 0, "Status": '', "Player": '' , "Profit/Loss": 0}
        success_lay_bets_dict = {"_id": 0, "Match": '',"strategy": '',"Amount": 0,"Type": '',"Odds": 0, "Status": '', "Player": '', "Profit/Loss": 0}
        fail_bets_dict = {"Match": '',"strategy": '',"reason":'', "Player": '' ,'Status': ''}  
        lay_bet_list = [100 , 100 , 100 , 100 , 100 , 100]
        index = 5
        # Display market details and extract market ID and runner information
        # print(market)
        market_id = getMarketId(market)
        runner1_name, runner1_selectionID, runner2_name, runner2_selectionID = getRunnersInfo(market)
        match = runner1_name + ' VS ' + runner2_name
        # print('market_id :', market_id)
        # print('runner1_name :', runner1_name)
        # print('runner1_selectionID :', runner1_selectionID)
        # print('runner2_name :', runner2_name)
        # print('runner2_selectionID :', runner2_selectionID)
        size = getAmount(market)
        match_start_time = getMarketStartTime(market)
        print('match_start_time :' , match_start_time)
        # Define match-specific parameters for prediction
        surface = surface.title()  
        tourney_date = datetime.datetime.strptime(marketStartTime, '%Y-%m-%dT%H:%M:%SZ').date()
        player1_name = runner1_name.title()
        player2_name = runner2_name.title()
        best_of = 3 
        round_ = 'R128' 
        
        # if market['totalMatched'] < 1000:
        #     fail_bets_dict["Match"] = match
        #     fail_bets_dict["strategy"] = strategy_name
        #     fail_bets_dict['reason'] = 'Volume Low'
        #     fail_bets_dict['Status'] = 'FAILURE'
        #     fail_bets.append(fail_bets_dict)  
        #     continue
    
        # Make a prediction based on match and player details
        final_df = tennis_prediction(surface, tourney_date, player1_name, player2_name, best_of, round_)
    
        # Check if the prediction DataFrame is empty
        if len(final_df) == 0:
            fail_bets_dict["Match"] = match
            fail_bets_dict["strategy"] = strategy_name
            fail_bets_dict['reason'] = 'Player Not Found!!!!!'
            fail_bets_dict['Status'] = 'FAILURE'
            fail_bets.append(fail_bets_dict)            
            continue  # Skip to the next iteration if no prediction data is available
        else:       
            # Determine the predicted winner based on the model's output
            if final_df['Prediction'].values == 0:
                # print('in IF')
                prob = final_df['Player1_Win_prob (0)'].values[0]
                print('Winner Predicted According to our Model: ' + runner1_name + ' with probability of: ' + str(prob.round(2)))
                selection_id = runner1_selectionID
                success_back_bets_dict['Player'] = runner1_name
                success_lay_bets_dict['Player'] = runner1_name
                fail_bets_dict['Player'] = runner1_name
            else:
                # print('in ELSE')
                prob = final_df['Player2_Win_prob (1)'].values[0]
                print('Winner Predicted According to our Model: ' + runner2_name + ' with probability of: ' + str(prob.round(2)))
                selection_id = runner2_selectionID
                success_back_bets_dict['Player'] = runner2_name
                success_lay_bets_dict['Player'] = runner2_name
                fail_bets_dict['Player'] = runner2_name
    
        # Print the selection ID for the predicted winner
        # print(selection_id)
        
        # Get the latest market book data and retrieve the last traded price for the predicted winner
        market_book = getMarketBookBestOffers(market_id)
        last_price_traded, original_lay_bet_price = getBothPrice(market_book, selection_id)
        if last_price_traded == None:
            reason = 'Price Not found!!!!!!!!!'
            # print(reason)
            fail_bets_dict["Match"] = match
            fail_bets_dict["strategy"] = strategy_name
            fail_bets_dict['reason'] = reason
            fail_bets_dict['Status'] = 'FAILURE'
            fail_bets.append(fail_bets_dict)
            continue

        if last_price_traded <= 1.1:
            reason = 'Back Bet price is Very Low'
            # print(reason)
            fail_bets_dict["Match"] = match
            fail_bets_dict["strategy"] = strategy_name
            fail_bets_dict['reason'] = reason
            fail_bets_dict['Status'] = 'FAILURE'
            fail_bets.append(fail_bets_dict)
            continue    

        if last_price_traded <= 1.2:
            lay_bet_price = round(last_price_traded - 0.05 , 2)
        elif last_price_traded > 1.2  :
            lay_bet_price = round(last_price_traded - 0.1 , 2)

        if lay_bet_price < 1.05:
            lay_bet_price = 1.05
        # print(market_book)
        # print('Back Bet Price: ',last_price_traded)
        # print('Lay Bet Price: ',lay_bet_price)
        size = round(size)
        back_stake = size/2
        lay_stake = size/2

        # print('Back Stake: ', back_stake)
        # print('Lay Stake: ', lay_stake)

        # Place a bet based on the model's prediction 
        print('Back Bet')
        BackBet_status,Back_bet_reason,type,odds,BackBet_id = placeBackBet(market_id, selection_id, last_price_traded, back_stake)
        # BackBet_status = 'SUCCESS'
        # print(BackBet_status)
        if BackBet_status != 'SUCCESS':
            fail_bets_dict["Match"] = match
            fail_bets_dict["strategy"] = strategy_name
            fail_bets_dict['Status'] = BackBet_status
            fail_bets_dict['reason'] = Back_bet_reason
            fail_bets.append(fail_bets_dict)        
        print('-----------------------------------------------')
        if BackBet_status == 'SUCCESS':
            success_back_bets_dict['_id'] = int(BackBet_id)
            success_back_bets_dict['Match'] = match
            success_back_bets_dict['strategy'] = strategy_name
            success_back_bets_dict['Type'] = type
            success_back_bets_dict['Amount'] = back_stake
            success_back_bets_dict['Odds'] = odds
            success_back_bets_dict['Status'] = BackBet_status
            success_back_bets_dict['Profit/Loss'] = 0
            success_bets.append(success_back_bets_dict)

            # thread = threading.Thread(target=threaded_function, args=(market, market_id, runner1_name, runner2_name, selection_id, match_start_time, last_price_traded, lay_bet_price, lay_stake, lay_bet_list, index,))
            # threads.append(thread)
            # thread.start()  

            # for thread in threads:
            #     thread.join()  

            # print("All threads have completed.")  

        # List to hold input parameters for each thread
            thread_params = [
                (market, market_id, runner1_name, runner2_name, selection_id, match_start_time, 
                last_price_traded, lay_bet_price, lay_stake, lay_bet_list, index)
                # Add more tuples for additional threads
            ]

            def execute_threaded_functions(thread_params):
                success_lay_bets_dict = {}

                def process_thread(params):
                    return threaded_function(*params)
                
                with ThreadPoolExecutor() as executor:
                    future_to_params = {executor.submit(process_thread, params): params for params in thread_params}
                    
                    for future in future_to_params:
                        params = future_to_params[future]
                        market_id = params[1]  # Assuming `market_id` is the second element in params
                        try:
                            success_lay_bets_dict[market_id] = future.result()
                        except Exception as e:
                            success_lay_bets_dict[market_id] = f"Error processing market {market_id}: {e}"

                print("All threads have completed.")
                return success_lay_bets_dict

            # Execute the threaded functions and collect results
            success_lay_bets_dict = execute_threaded_functions(thread_params)

        # Print the collected results
        print(success_lay_bets_dict)

        for market_id, bet_data in success_lay_bets_dict.items():
            # Add the market_id to the bet_data for context
            if isinstance(bet_data, dict):  # Only append successful bets
                bet_data['market_id'] = market_id
                success_bets.append(bet_data)




            # print('Lay Bet')
            # LayBet_status,Lay_bet_reason,type,odds = placeLayBet(market_id , selection_id, lay_bet_price, lay_stake)
            # if LayBet_status == 'SUCCESS':
            #     success_lay_bets_dict['Match'] = match
            #     success_lay_bets_dict['strategy'] = strategy_name
            #     success_lay_bets_dict['Type'] = type
            #     success_lay_bets_dict['Amount'] = lay_stake
            #     success_lay_bets_dict['Odds'] = odds
            #     success_lay_bets_dict['Status'] = LayBet_status
            #     success_bets.append(success_lay_bets_dict)
            # else : 
            #     fail_bets_dict["Match"] = match
            #     fail_bets_dict["strategy"] = strategy_name
            #     fail_bets_dict['Status'] = BackBet_status
            #     fail_bets_dict['reason'] = Lay_bet_reason
            #     fail_bets.append(fail_bets_dict)        
        
        # Separator for readability in the output
        # print('============================================================================================')

    return (success_bets , fail_bets)