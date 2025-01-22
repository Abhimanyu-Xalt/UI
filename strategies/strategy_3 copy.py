
import threading
from api import bet_url

def strategy_3(market_catalogue,SSOID):
    
    import datetime
    import pytz
    import time
    import requests
    import http.client
    import urllib , json
    threads = []
    success_bets = []
    fail_bets = []
    strategy_name = 'Strategy 3'
    headers = {'X-Application': 'UrL3pOSMAWKhpIvL', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}
    print('market_catalogue : ', market_catalogue)
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def getMarketStartTime(market_dict):
        # Extract 'marketStartTime' from the dictionary
        utc_time_str = market_dict.get('marketStartTime')
        if not utc_time_str:
            raise ValueError("The key 'marketStartTime' is missing in the input dictionary.")

        utc_time = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")

        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone()

        return local_time.replace(tzinfo=None)
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def getMarketId(market):
        # print('getMarketId')
        return market['marketId']
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    def getAmount(market):
        return market['amount']
#-------------------------------------------------------------------------------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------------------------------------------------------------------------------
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
        # print('market_book_loads' , market_book_loads)
        try:
            market_book_result = market_book_loads['result']
            return market_book_result
        except:
            print  ('Exception from API-NG' + str(market_book_result['error']))
            exit()
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
#-------------------------------------------------------------------------------------------------------------------------------------------------------    
    def threaded_function(market, market_id, runner1_name, runner2_name, selection_id, match_start_time, last_price_traded, lay_bet_price, lay_stake, lay_bet_list, index):
        while True:
            try:
                current_time = datetime.datetime.now()  # Keep as datetime object
                back_bet_price = last_price_traded
                time.sleep(30)
                market_book = getMarketBookBestOffers(market_id)
                # print(market_book)
                current_back_bet_price, current_lay_bet_price = getBothPrice(market_book, selection_id)
                print('back_bet_price: ', back_bet_price)
                print('lay_bet_price: ', lay_bet_price)
                print('current_back_bet_price: ', current_back_bet_price)
                print('current_lay_bet_price: ', current_lay_bet_price)

                if current_lay_bet_price < back_bet_price and lay_bet_list[index] != current_lay_bet_price:
                    lay_bet_list.append(current_lay_bet_price)
                    index = index + 1

                print('lay_bet_list : ' , lay_bet_list)
                print('index : ' , index)
                if lay_bet_list[index - 3] < lay_bet_list[index]:
                    # place Lay order
                    print('lay_bet_list[index - 2] < lay_bet_list[index]')
                    # LayBet_status,Lay_bet_reason,type,odds,LayBet_id = placeLayBet(market_id , selection_id, lay_bet_list[index], lay_stake) 
                    break

                if lay_bet_list[index - 1] < lay_bet_list[index]:
                    if current_time < match_start_time - datetime.timedelta(minutes=20):
                        continue
                    else:
                        # place Lay Order
                        print('lay_bet_list[index - 1] < lay_bet_list[index]')
                        # LayBet_status,Lay_bet_reason,type,odds,LayBet_id = placeLayBet(market_id , selection_id, lay_bet_list[index], lay_stake)
                        break
                        
                if lay_bet_list[index] < back_bet_price - 0.05:
                    # place Lay Order
                    print('lay_bet_list[index] < back_bet_price - 0.05')
                    # LayBet_status,Lay_bet_reason,type,odds,LayBet_id = placeLayBet(market_id , selection_id, lay_bet_list[index], lay_stake)
                    break
                print('current_time : ' , current_time)
                print('match_start_time : ' , match_start_time)
                print('match_start_time - datetime.timedelta(minutes=10) : ' , match_start_time - datetime.timedelta(minutes=10))
                # if current_time >= (match_start_time - datetime.timedelta(minutes=10)): 
                    # print('current_time >= (match_start_time - datetime.timedelta(minutes=10))')
                    # LayBet_status,Lay_bet_reason,type,odds,LayBet_id = placeLayBet(market_id , selection_id, back_bet_price-0.1, lay_stake)
                    # break
                if lay_bet_list[index] == lay_bet_price:
                    print('lay_bet_list[index] == lay_bet_price')
                    break         

            except http.client.RemoteDisconnected as e:
                print("RemoteDisconnected: Remote end closed connection without response. Retrying...")
                continue 
#-------------------------------------------------------------------------------------------------------------------------------------------------------    
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
    def back_stake_calculator(lay_stake,lay_bet_price,back_bet_price):
        back_stake = (lay_stake * lay_bet_price)/back_bet_price
        back_stake = round(back_stake,2)
        return back_stake
#-------------------------------------------------------------------------------------------------------------------------------------------------------
    for market in market_catalogue:
        success_back_bets_dict = {"Match": '',"strategy": '',"Amount": 0,"Type": '',"Odds": 0, "Status": '', "Player": ''}
        success_lay_bets_dict = {"Match": '',"strategy": '',"Amount": 0,"Type": '',"Odds": 0, "Status": '', "Player": ''}
        fail_bets_dict = {"Match": '',"strategy": '',"reason":'', "Player": '' , "Status" : ''}
        lay_bet_list = [100 , 100 , 100 , 100]
        index = 3
        # Display market details and extract market ID and runner information
        
        print(market)
        market_id = getMarketId(market)
        runner1_name, runner1_selectionID, runner2_name, runner2_selectionID = getRunnersInfo(market)
        match = runner1_name + ' VS ' + runner2_name
        size = getAmount(market)
        match_start_time = getMarketStartTime(market)
        print('match_start_time :' , match_start_time)
        # print('market_id :', market_id)
        # print('runner1_name :', runner1_name)
        # print('runner1_selectionID :', runner1_selectionID)
        # print('runner2_name :', runner2_name)
        # print('runner2_selectionID :', runner2_selectionID)
        # print('amount :', size)
        
        # if market['totalMatched'] < 1000:
        #     fail_bets_dict["Match"] = match
        #     fail_bets_dict["strategy"] = strategy_name
        #     fail_bets_dict['reason'] = 'Volume Low'
        #     fail_bets_dict['Status'] = 'FAILURE'
        #     fail_bets.append(fail_bets_dict)  
        #     continue        
        
        # Get the latest market book data and retrieve the last traded price for the predicted winner
        market_book = getMarketBookBestOffers(market_id)
        Player1_Back_Price, Player1_Lay_Price = getBothPrice(market_book, runner1_selectionID)
        Player2_Back_Price, Player2_Lay_Price = getBothPrice(market_book, runner2_selectionID)

        if Player1_Back_Price > Player2_Back_Price:
            # print(Player2_Back_Price)
            last_price_traded = Player2_Back_Price
            selection_id = runner2_selectionID
            success_back_bets_dict['Player'] = runner2_name
            success_lay_bets_dict['Player'] = runner2_name
            fail_bets_dict['Player'] = runner2_name
        else : 
            # print(Player1_Back_Price)
            last_price_traded = Player1_Back_Price
            selection_id = runner1_selectionID
            success_back_bets_dict['Player'] = runner1_name
            success_lay_bets_dict['Player'] = runner1_name
            fail_bets_dict['Player'] = runner1_name

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
        elif last_price_traded > 1.2 and last_price_traded <= 1.5 :
            lay_bet_price = round(last_price_traded - 0.1 , 2)
        elif(last_price_traded > 1.5):
            lay_bet_price = round(last_price_traded - 0.2 , 2)

        if lay_bet_price < 1.05:
            lay_bet_price = 1.05

        # print('Market Book: ' , market_book)
        # print('Back Odds: ' , last_price_traded)
        # print('Lay Odds: ' , lay_bet_price)

        lay_stake = round(size/2,1)
        back_stake = back_stake = back_stake_calculator(lay_stake,lay_bet_price,last_price_traded)
        # print('Lay Stake: ',lay_stake)
        # print('Back Stake: ',back_stake)
        # Place a bet based on the model's prediction 

        print('Back Bet')
        # BackBet_status,Back_bet_reason,type,odds,BackBet_id = placeBackBet(market_id, selection_id, last_price_traded, back_stake)
        BackBet_status = 'SUCCESS'
        # BackBet_status = 'SUCCESS'
        # BackBet_status,Back_bet_reason,type,odds = 'SUCCESS','','Back',1.7
        # if BackBet_status != 'SUCCESS':
        #     fail_bets_dict["Match"] = match
        #     fail_bets_dict["strategy"] = strategy_name
        #     fail_bets_dict['Status'] = BackBet_status
        #     fail_bets_dict['reason'] = Back_bet_reason
        #     fail_bets.append(fail_bets_dict)
        # print(BackBet_status)
        # print('-----------------------------------------------')
        if BackBet_status == 'SUCCESS':
            # success_back_bets_dict['Match'] = match
            # success_back_bets_dict['strategy'] = strategy_name
            # success_back_bets_dict['Type'] = type
            # success_back_bets_dict['Amount'] = back_stake
            # success_back_bets_dict['Odds'] = odds
            # success_back_bets_dict['Status'] = BackBet_status
            # success_bets.append(success_back_bets_dict)

            thread = threading.Thread(target=threaded_function, args=(i,))
            threads.append(thread)
            thread.start()  

            for thread in threads:
                thread.join()          

            # print('Lay Bet')
            # LayBet_status,Lay_bet_reason,type,odds,LayBet_id = placeLayBet(market_id , selection_id, lay_bet_price, lay_stake)
            # LayBet_status,Lay_bet_reason,type,odds = 'SUCCESS','','Lay',1.5
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
    