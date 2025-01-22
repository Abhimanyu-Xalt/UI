from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import random

# from strategies import strategy_1,strategy_2,strategy_3
# from strategies.strategy_1 import strategy_1
# from strategies.strategy_2 import strategy_2
from particular_match_fetch import particular_match_fetch
from strategies.strategy_1 import strategy_1
from strategies.strategy_2 import strategy_2
from strategies.strategy_3 import strategy_3
from utils import *
from flask_cors import CORS
from db import Database

db_object = Database()
# db_object.deleteAllData()
# db_object.showAllData()
# db_object.updateData("676a4b05a8217e9896d6287f",100)
# db_object.showAllData()

data = db_object.showAllData()
match_data = db_object.showMatchStatusData()


success_bets = []
# success_back_bets_dict = {
#     "_id": 373082211155,
#     "Match": "Player K vs Player L",
#     "strategy": "Hybrid Back-Lay Strategy",
#     "Amount": 80,
#     "Type": "Back",
#     "Odds": 2.7,
#     "Status": "Successful",
#     "Player": "Player L",
#     "Profit/Loss": ""
# }

# # Example 1
# success_back_bets_dict_1 = {
#     "_id": 374114274928,
#     "Match": "Duckworth v Dom Stricker",
#     "strategy": "Strategy_3",
#     "Amount": 2.50,
#     "Type": "Lay",
#     "Odds": 1.71,
#     "Status": "",
#     "Player": "James Duckworth",
#     "Profit/Loss": 0
# }

# # Example 2
# success_back_bets_dict_2 = {
#     "_id": 374114196355,
#     "Match": "A Muller v Borges",
#     "strategy": "Strategy_1",
#     "Amount": 4.85,
#     "Type": "Back",
#     "Odds": 1.71,
#     "Status": "",
#     "Player": "Nuno Borges",
#     "Profit/Loss": 0
# }

# # Example 3
# success_back_bets_dict_3 = {
    # "_id": 374118453273,
    # "Match": "A Muller v Borges",
    # "strategy": "Strategy_1",
    # "Amount": 5.00,
    # "Type": "Lay",
    # "Odds": 1.6,
    # "Status": "",
    # "Player": "Nuno Borges",
    # "Profit/Loss": 0
# }


# success_bets.append(success_back_bets_dict_1)
# success_bets.append(success_back_bets_dict_2)
# success_bets.append(success_back_bets_dict_3)

# success_bets=[[{    "_id": 1234,
#     "Match": "Adhar VS Ayush",
#     "strategy": "Strategy_1",
#     "Amount": 5.00,
#     "Type": "Lay",
#     "Odds": 1.6,
#     "Status": "",
#     "Player": "Adhar",
#     "Profit/Loss": 0}]]

# print('success_bets : ',success_bets)
# db_object.insertData(success_bets)

print('==========================================================')
# db_object.showAllData()

app = Flask(__name__)
CORS(app)
SSOID = login() 

if SSOID == None:
    print("Request Failed !!")

@app.route('/')
def home():
    return "Welcome Carlos!"

@app.route('/get_tournament')
def get_tournament(): 
    tournaments = list_tournaments(SSOID)
    return jsonify({"tournaments":tournaments})

@app.route('/get_amount')
def get_amount():
    amount = show_amount(SSOID)
    return jsonify({"amount" : amount})

@app.route('/retrieve_matches',methods=["POST"])
def retrieve_matches():
    # global surface 
    # surface = request.json['surface']
    tournament = request.json['tournament']
    # strategy = request.json['strategy']
    amount = request.json['amount']
    market_catalogue = show_matches(tournament,amount,SSOID)
    return jsonify({"market_catalogue":market_catalogue})

@app.route('/fetch_particular_match',methods=["POST"])
def particular_match_fetch_route():
    winner_data = []
    filtered_market = request.json['data']
    for match in filtered_market["market_catalogue"]:
        winner_data.append(match)
    winning_player_data = particular_match_fetch('Hard',winner_data,SSOID)
    return jsonify({"winning_player_data":winning_player_data})

@app.route('/get_pnl')
def get_pnl_route():
    pnl_data = get_settled_data(SSOID)
    del_status = 0  
    # print('pnl_data' , pnl_data)
    for pnl in pnl_data:
        bet_id = pnl['betId']
        profit = pnl['profit']
        status = 'MATCHED'
        res = db_object.updateData(int(bet_id), profit , status)
        if res != 0:
            data = db_object.showAllData()
            match_data = db_object.showMatchStatusData()            
            for match in match_data:
                # print('In 1st loop')
                for record in data:
                    # print('In 2nd loop')
                    if match['matches'] == record['Match']:
                        del_status = db_object.deleteMatchStatusData(match['matches'])    
                        print('Update Successfull in Match Status DB!!!!!!!!!!')  

    return jsonify({"status" : res , "del_status" : del_status})


@app.route('/get_unmatched_pnl')
def get_unmatched_pnl_route():
    unmatched_data = get_unmatched_data(SSOID)
    del_status = 0
    # print('Unmatched Data' , unmatched_data)
    for dt in unmatched_data:
        bet_id = dt['betId']
        profit = 0
        status = 'UNMATCHED'
        res = db_object.updateData(int(bet_id), profit , status)
        if res != 0:
            data = db_object.showAllData()
            match_data = db_object.showMatchStatusData()            
            for match in match_data:
                # print('In 1st loop')
                for record in data:
                    # print('In 2nd loop')
                    if match['matches'] == record['Match']:
                        del_status = db_object.deleteMatchStatusData(match['matches'])    
                        print('Update Successfull in Match Status DB!!!!!!!!!!')  
    return jsonify({"status" : res , "del_status" : del_status})

@app.route('/show_data')
def show_data_route():
   data = db_object.showAllData() 
#    print("data" ,data)
   return jsonify({"data" : data})

@app.route('/show_match_data')
def showMatchStatusData_route():
    match_status_data = db_object.showMatchStatusData()
    return jsonify({"match_status_data" : match_status_data})

@app.route('/home_fetch_data')
def home_fetch_data_route():
    profits = {"strategy_1_pnl" : 0 , "strategy_2_pnl" : 0 , "strategy_3_pnl" : 0 , 'overall_pnl' : 0 , 'total_bp' : 0 , 'total_M' : 0 , 'total_UM' : 0}
    count = 0
    data = db_object.showAllData() 
    for d in data:
        data1 = []
        # print('strategy' , d['strategy'] , type(d['strategy']))
        # print('Profit/Loss' , d['Profit/Loss'] , type(d['Profit/Loss']))

        if d['Status'] == 'MATCHED' or d['Status'] == 'Matched':
            profits['total_M'] += 1
        if d['Status'] == 'UNMATCHED' or d['Status'] == 'Unmatched':
            profits['total_UM'] += 1

        profits['overall_pnl'] += d['Profit/Loss']
        if d['strategy'] == 'Strategy_1' or d['strategy'] == 'Strategy 1' :
            profits['strategy_1_pnl'] += d['Profit/Loss']
        if d['strategy'] == 'Strategy_2' or d['strategy'] == 'Strategy 2':
            profits['strategy_2_pnl'] += d['Profit/Loss']
        if d['strategy'] == 'Strategy_3' or d['strategy'] == 'Strategy 3':
            profits['strategy_3_pnl'] += d['Profit/Loss']
        count += 1

        profits['total_bp'] = count
        data1.append(profits)
    

    return jsonify({'data' : data1})


@app.route('/filtered_market',methods=["POST"])
def filter_market():

    strategy_1_list =  []
    strategy_2_list =  []
    strategy_3_list =  []
    success_bets = []
    fail_bets = []

    filtered_market = request.json['data']

    filtered_market["market_catalogue"] = [
    {
        **match,
        "marketStartTime": datetime.datetime.strptime(match["marketStartTime"], "%d-%m-%Y %I:%M %p")
        .astimezone(datetime.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    for match in filtered_market["market_catalogue"]
]


    for match in filtered_market["market_catalogue"]:




        if match["strategies"] == "strategy_1":
            strategy_1_list.append(match)
        elif match["strategies"] == "strategy_2":
            strategy_2_list.append(match)
        elif match["strategies"] == "strategy_3":
            strategy_3_list.append(match)

    # print("Strategy 1:", strategy_1_list)
    # print("Strategy 2:", strategy_2_list)
    # print("Strategy 3:", strategy_3_list)
    # print('surface',surface)
    if len(strategy_1_list) != 0:
        # print('Execute Strategy_1 Function here!')
        success_bets_1 , fail_bets_1 = strategy_1('Hard',strategy_1_list,SSOID)
        success_bets.append(success_bets_1)
        fail_bets.append(fail_bets_1)

    if len(strategy_2_list) != 0:
        # print('Execute Startegy_2 Function here!')
        success_bets_2 , fail_bets_2 = strategy_2('Hard',strategy_2_list,SSOID)
        success_bets.append(success_bets_2)
        fail_bets.append(fail_bets_2)

    if len(strategy_3_list) != 0:
        # print('Execute Strategy_3 Function here!')
        success_bets_3 , fail_bets_3 = strategy_3(strategy_3_list,SSOID)
        success_bets.append(success_bets_3)
        fail_bets.append(fail_bets_3)       
    
    db_object.insertData(success_bets)
    
    # success_bets
# for bet in success_bets:
#     for s_list in bet:
#         if s_list['Status'] == 'SUCCESS':
#             query = f"""
#             UPDATE match_status 
#             SET column1 = 
#             WHERE condition_column = ?;
#             """
    print('Insert Successfull in History DB !!!!!!!!!!')
    
    data = db_object.showAllData()
    match_data = db_object.showMatchStatusData()
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    for match in match_data:
        # print('In 1st loop')
        for record in data:
            # print('In 2nd loop')
            if match['date'] == current_date and record['date'] == current_date and match['matches'] == record['Match']:
                # print('In If statement')
                # print('Matches', match['matches'])
                db_object.updateMatchData(match['matches'] , 'MATCHED')    
                print('Update Successfull in Match Status DB!!!!!!!!!!')               


    return jsonify({"success_bets" : success_bets , "fail_bets" : fail_bets})    


@app.route('/fetch_market_status',methods=["POST"])
def market_status():
    # data = request.get_json()
    market_status_list = []
    filtered_market = request.json['data']
    for match in filtered_market["market_catalogue"]:
        success_bets_1 = {"matches": "","strategies": "","Type": "","Player": "","odds": 0,"amount": 0 , 'status' : '' , '_id' : random.randint(1000, 9999)}
        success_bets_2 = {"matches": "","strategies": "","Type": "","Player": "","odds": 0,"amount": 0, 'status' : '' , '_id' : random.randint(1000, 9999)}
        
        if match['layOdds'] != 0:
            match['TypeL'] = 'Lay'

        player1_name = match['runners'][0]['runnerName']
        player2_name = match['runners'][1]['runnerName']
        matches = f'{player1_name} VS {player2_name}'
        success_bets_1['matches'] = matches
        success_bets_2['matches'] = matches
        
        success_bets_1['strategies'] = match['strategies']
        success_bets_2['strategies'] = match['strategies']

        success_bets_1['Type'] = match['Type']
        success_bets_2['Type'] = match['TypeL']

        success_bets_1['odds'] = match['backOdds']
        success_bets_2['odds'] = match['layOdds']

        winner_name = match['winner']
        # print('winner' , winner_name)
        if "No historical data found for" in winner_name:
            winner_name = winner_name.replace("No historical data found for", "").strip()
        else:
            winner_name = winner_name

        # print('winner' , winner_name)

        success_bets_1['Player'] = winner_name
        success_bets_2['Player'] = winner_name
        
        if match['Type'] == 'Back':
            success_bets_1['status'] = 'Matched'

        if match['TypeL'] == 'Lay':
            success_bets_2['status'] = 'To Be Matched'


        if match['strategies'] == 'strategy_1':
            success_bets_1['amount'] = match['amount'] / 2
            success_bets_2['amount'] = match['amount'] / 2
        if match['strategies'] == 'strategy_3':
            if match['Type'] == 'Back':
                back_stake = round(((match['layOdds']) * (match['amount'] / 2)) / match['backOdds'] , 2 )
                success_bets_1['amount'] = back_stake
            if match['TypeL'] == 'Lay':
                success_bets_2['amount'] = match['amount'] / 2
        if match['strategies'] == 'strategy_2':
            success_bets_1['amount'] = match['amount']
            del success_bets_2

        if match['strategies'] != 'strategy_2':
            market_status_list.append(success_bets_1)
            market_status_list.append(success_bets_2)
        else :
            market_status_list.append(success_bets_1)   
    # print('market_status_list' , market_status_list)
    db_object.insert_match_data(market_status_list)
    print('Insert Successfull in Match Status DB !!!!!!!!!!')
    # print('market_status_list ------------- ' , market_status_list)

    return jsonify(market_status_list)


def scheduled_task():
    print("Running scheduled task...")
    pnl_data = get_settled_data(SSOID)
    for pnl in pnl_data:
        bet_id = pnl['betId']
        profit = pnl['profit']
        status = 'Matched'
        res = db_object.updateData(int(bet_id), profit , status)
        if res != 0:
            data = db_object.showAllData()
            match_data = db_object.showMatchStatusData()            
            for match in match_data:
                # print('In 1st loop')
                for record in data:
                    # print('In 2nd loop')
                    if match['matches'] == record['Match']:
                        del_status = db_object.deleteMatchStatusData(match['matches'])
                        if del_status == 1:    
                            print('Update Successfull in Match Status DB!!!!!!!!!!')  
    unmatched_data = get_unmatched_data(SSOID)
    for dt in unmatched_data:
        bet_id = dt['betId']
        profit = 0
        status = 'UNMATCHED'
        res = db_object.updateData(int(bet_id), profit , status)
        if res != 0:
            data = db_object.showAllData()
            match_data = db_object.showMatchStatusData()            
            for match in match_data:
                # print('In 1st loop')
                for record in data:
                    # print('In 2nd loop')
                    if match['matches'] == record['Match']:
                        del_status = db_object.deleteMatchStatusData(match['matches'])   
                        if del_status == 1:     
                            print('Update Successfull in Match Status DB!!!!!!!!!!') 


def keep_session_alive(session_token, app_key):
    url = "https://identitysso.betfair.com/api/keepAlive"
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print("Session extended successfully")
    else:
        print("Failed to extend session:", response.json())

    print('session_token : ' , session_token)

print('SSOID: ' , SSOID)


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', hours = 2)
    scheduler.add_job(keep_session_alive, 'interval', hours = 6, args=[SSOID, 'M90yVlWTGZfS7rEi'],misfire_grace_time=3600)
    scheduler.start()
    app.run(debug=False) 






