from pymongo.mongo_client import MongoClient
from datetime import datetime

class Database:
    def __init__(self):
        self.DB_STRING = "mongodb+srv://bhumeesethi31:2vl7AuYvCVG1pSMb@adharcluster.x2jvc.mongodb.net/?retryWrites=true&w=majority&appName=adharCluster"
        self.client = MongoClient(self.DB_STRING)
        self.db = self.client["sample_mflix"]
        self.gp_collection = self.db["GP"]
        self.match_status_collection = self.db["match_status"]
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB! ",self.client)
        except Exception as e:
            print("Here is Exception bro: ",str(e))

    def insertData(self, success_bets):
        for bet in success_bets:
            for s_list in bet :
                s_list['date'] = datetime.now().strftime('%Y-%m-%d')
            self.gp_collection.insert_many(bet)


    def insert_match_data(self , market_status_list):
        for market in market_status_list:
            market['date'] = datetime.now().strftime('%Y-%m-%d')
        # print('market_status_list :::::: ' , market_status_list)
        self.match_status_collection.insert_many(market_status_list)




    def updateData(self, bet_id, pnl, status):
        result = self.gp_collection.update_one(
                                        {"_id": bet_id},  # Filter
                                        {"$set": {"Profit/Loss": pnl, "Status": status}},  # Update operation
                                        upsert=False
                                    )
        return result.modified_count
    

    def updateMatchData(self, matches, status):
        data = list(self.match_status_collection.find({"matches": matches}))
        # print('DATA ::::::::' , data)
        result = self.match_status_collection.update_many(
                                        {"matches": matches},  # Filter
                                        {"$set": {"status": status}},  # Update operation
                                        upsert=False
                                    )
        return result.modified_count
    



    def showAllData(self):
        data = list(self.gp_collection.find({}))
        # print("data: ",data)
        return data
    
    def showMatchStatusData(self):
        data = list(self.match_status_collection.find({}))
        # print("data: ",data)
        return data
    
    def deleteAllData(self):
        self.gp_collection.delete_many({})

    def deleteMatchStatusData(self , match):
        result = self.match_status_collection.delete_many({ 'matches': match })
        return result.deleted_count

    