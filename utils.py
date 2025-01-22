import datetime
import urllib , json
import requests
import pytz
from api import *


def login():
    resp = requests.post(login_api, data=payload, cert=(r'certs\BetfairApp1.crt' , r'certs\client-2048.pem'), headers=headers)
    if resp.status_code == 200:
        resp_json = resp.json()  
        print (resp_json['loginStatus'])
        print (resp_json['sessionToken'])
        SSOID = resp_json['sessionToken']
        return SSOID
    else:
        return None

def list_tournaments(SSOID):
    headers = {'X-Application': 'M90yVlWTGZfS7rEi', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}
    # tournaments = ['ATP Finals 2024']
    eventTypeID = '["2"]'
    marketStartTime = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
    # marketStartTime = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    marketEndTime = (datetime.datetime.now() + datetime.timedelta(hours=24))
    marketEndTime = marketEndTime.strftime('%Y-%m-%dT%H:%M:%SZ')
    locale = '"en"'
    maxResults = 100
    comp_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCompetitions", "params": {"filter":{"eventTypeIds":' + str(eventTypeID) + ',"marketStartTime":{"from":"' + marketStartTime + '" , "to": "' + marketEndTime + '"}},"locale":' + str(locale) + ',"maxResults":"'+ str(maxResults) +'"}, "id": 1}'        
    
    req = urllib.request.Request(bet_url , comp_req.encode('utf-8'), headers)
    response = urllib.request.urlopen(req)
    jsonResponse = response.read()
    pkg = jsonResponse.decode('utf-8')
    Results = json.loads(pkg)
    comp_catalogue = Results['result']

    # tournaments = [item['competition']['name'] for item in comp_catalogue if 'ATP' in item['competition']['name']]
    tournaments = [item['competition']['name'] for item in comp_catalogue]
    return tournaments


def show_matches(tournaments,amount,SSOID):

    headers = {'X-Application': 'M90yVlWTGZfS7rEi', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}
    print(tournaments)
    print(amount)
    eventTypeID = '["2"]'
    target_date = datetime.datetime.now()
    print(target_date)
    marketStartTime = target_date.strftime('%Y-%m-%dT%H:%M:%S')
    marketEndTime = (target_date + datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
    locale = '"en"'
    maxResults = 100
    comp_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listCompetitions", "params": {"filter":{"eventTypeIds":' + str(eventTypeID) + ',"marketStartTime":{"from":"' + marketStartTime + '" , "to": "' + marketEndTime + '"}},"locale":' + str(locale) + ',"maxResults":"'+ str(maxResults) +'"}, "id": 1}'        
    
    req = urllib.request.Request(bet_url , comp_req.encode('utf-8'), headers)
    response = urllib.request.urlopen(req)
    jsonResponse = response.read()
    pkg = jsonResponse.decode('utf-8')
    Results = json.loads(pkg)
    comp_catalogue = Results['result']
    
    competition_ids = [
        item['competition']['id']
        for item in comp_catalogue
        if item['competition']['name'] in tournaments
    ]
    
    competition_ids = json.dumps(competition_ids)
    
    eventTypeID = '["2"]'
    # countryCode = '["AU"]'
    target_date = datetime.datetime.now() 
    print(target_date)
    marketStartTime = target_date.replace(hour=0, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S')
    marketEndTime = (target_date + datetime.timedelta(hours=24)).replace(hour=23, minute=59, second=0).strftime('%Y-%m-%dT%H:%M:%S')
    # marketStartTime = (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
    # marketEndTime = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
    print('marketStartTime', marketStartTime)
    print('marketEndTime', marketEndTime)
    maxResults = 200
    # competition_ids = '["12702183"]'
    inPlayOnly = "false" # "true"
    locale = '"en"'
    sort = '"FIRST_TO_START"' # '"MAXIMUM_TRADED"'
    marketProjection = '["RUNNER_METADATA" , "COMPETITION" , "MARKET_START_TIME"]'
    
    user_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", "params": {"filter":{"eventTypeIds":' + str(eventTypeID) + ',"competitionIds":' + str(competition_ids) + ',"inPlayOnly":' + str(inPlayOnly) + ',"marketTypeCodes":["MATCH_ODDS"],"marketStartTime":{"from":"' + marketStartTime + '" , "to": "' + marketEndTime + '"}},"locale":' + str(locale) + ',"sort": ' + str(sort) + ',"marketProjection":' + str(marketProjection) +',"maxResults":"'+ str(maxResults) +'"}, "id": 1}'
    
    req = urllib.request.Request(bet_url, user_req.encode('utf-8'), headers)
    response = urllib.request.urlopen(req)
    jsonResponse = response.read()
    pkg = jsonResponse.decode('utf-8')
    Results = json.loads(pkg)
    market_catalogue = Results['result']
    
    # Filter out single tennis matches
    market_catalogue = [
        match for match in market_catalogue
        if all('/' not in runner['runnerName'] for runner in match['runners'])
        and all(
            runner.update({'runnerName': 'Christopher OConnell'}) or True
            if runner['runnerName'] == 'Christopher O\'Connell' else True
            for runner in match['runners']
        )
        # and match['totalMatched'] > 1000
    ]
    for market in market_catalogue:
        market['strategies'] = 'strategy_1'
        market['amount'] = amount
    
    market_catalogue = [
        {
            **match,
            "marketStartTime": datetime.datetime.fromisoformat(match["marketStartTime"].replace("Z", "+00:00"))
            .astimezone()
            .strftime("%d-%m-%Y %I:%M %p"),
        }
        for match in market_catalogue
    ]



    return market_catalogue


def show_amount(SSOID):
    headers = {'X-Application': 'M90yVlWTGZfS7rEi', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}
    amount_req = '{"jsonrpc": "2.0", "method": "AccountAPING/v1.0/getAccountFunds", "params": {}, "id": 1}'
    req = urllib.request.Request(acc_url , amount_req.encode('utf-8'), headers)
    response = urllib.request.urlopen(req)
    jsonResponse = response.read()
    pkg = jsonResponse.decode('utf-8')
    Results = json.loads(pkg)
    amount = Results['result']['availableToBetBalance']
    return amount        

def get_settled_data(SSOID):
    headers = {'X-Application': 'M90yVlWTGZfS7rEi', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=2)
    tomorrow = today + datetime.timedelta(days=2)

    # Format dates as ISO 8601 strings
    start_date = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Properly format the JSON string with settledDateRange
    list_order_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listClearedOrders", "params": {'
        '"betStatus": "' + "SETTLED" + '", '
        '"groupBy": "' + "BET" + '", '
        '"settledDateRange": {"from": "' + start_date + '", "to": "' + end_date + '"}'
        '}, "id": 1}'
    )    
    req = urllib.request.Request(bet_url, list_order_req.encode('utf-8'), headers)
    response = urllib.request.urlopen(req)
    jsonResponse = response.read()
    list_order_Response = jsonResponse.decode('utf-8')
    Results = json.loads(list_order_Response)
    pnl_data = Results['result']['clearedOrders']
    return pnl_data


def get_unmatched_data(SSOID):
    headers = {'X-Application': 'M90yVlWTGZfS7rEi', 'X-Authentication': SSOID , 'Content-Type': 'application/json'}
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=2)
    tomorrow = today + datetime.timedelta(days=2)

    # Format dates as ISO 8601 strings
    start_date = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Properly format the JSON string with settledDateRange
    list_order_req = (
        '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listClearedOrders", "params": {'
        '"betStatus": "' + "LAPSED" + '", '
        '"groupBy": "' + "BET" + '", '
        '"settledDateRange": {"from": "' + start_date + '", "to": "' + end_date + '"}'
        '}, "id": 1}'
    )    
    req = urllib.request.Request(bet_url, list_order_req.encode('utf-8'), headers)
    response = urllib.request.urlopen(req)
    jsonResponse = response.read()
    list_order_Response = jsonResponse.decode('utf-8')
    Results = json.loads(list_order_Response)
    unmatched_data = Results['result']['clearedOrders']
    return unmatched_data




