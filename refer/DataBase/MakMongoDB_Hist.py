import pymongo
from Path import MainPath
import Helper.KIS.KIS_Common as Common 
from DataBase.CalMongoDB import MongoDB
import yaml

class ColMongoHistDB:

    def __init__(self):
         with open(MainPath + 'myStockInfo.yaml', encoding='UTF-8') as f:
            self.stock_info = yaml.load(f, Loader=yaml.FullLoader)
 
    ######################################################################

    def MakeMongoDB_Accnt(self, mode, Account_dict):

        Common.SetChangeMode(mode)
        
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                       username=self.stock_info["MONGODB_ID"],
                                       password=self.stock_info["MONGODB_PW"],
                                       maxIdleTimeMS=120000,
                                       serverSelectionTimeoutMS=30000)
        DB = MongoDB(DB_addres = "MONGODB_NAS")

        #// 데이터베이스 정보를 가져온다
        str_database_name = 'AccntDataBase'
        db = conn.get_database(str_database_name)
        collection = db.get_collection(mode)

        ####################################   
        updated_date = Account_dict['Date']

        list_of_collections = db.list_collection_names()
                
        # MongoDB에 저장된 마지막 날짜 가져오기
        if mode in list_of_collections:
            
            collection = db.get_collection(mode)
            
            try:
                previous_date = collection.find_one(sort=[('Date', -1)])['Date']          

                #####################################

                if previous_date.date() != Account_dict['Date'].date():

                    print(f"## UPDATE : {mode} - {updated_date}")
                    collection.insert_one(Account_dict)
                            
                else:
                    print(f"## EXIST : {mode} - {updated_date}")
                    
            except Exception as e:
                print(e)
                print(f"## EXCEPTION : {mode} - {e}")
                
        else:
            collection = db.get_collection(mode)
            
            print(f"## NEW : {mode} - {updated_date}")
            collection.insert_one(Account_dict)


    def MakeMongoDB_Trade(self, mode, Account_dict):

        Common.SetChangeMode(mode)
        
        conn = pymongo.MongoClient(host=self.stock_info["MONGODB_NAS"], port=self.stock_info["MONGODB_PORT"], \
                                       username=self.stock_info["MONGODB_ID"],
                                       password=self.stock_info["MONGODB_PW"],
                                       maxIdleTimeMS=120000,
                                       serverSelectionTimeoutMS=30000)
        DB = MongoDB(DB_addres = "MONGODB_NAS")

        #// 데이터베이스 정보를 가져온다
        str_database_name = 'AccntDataBase_Trade'
        db = conn.get_database(str_database_name)

        ####################################   
        updated_date = Account_dict['Date']

        list_of_collections = db.list_collection_names()
                
        # MongoDB에 저장된 마지막 날짜 가져오기
        if mode in list_of_collections:
            
            collection = db.get_collection(mode)
            
            try:
                previous_date = collection.find_one(sort=[('Date', -1)])['Date']          

                print(previous_date.date(), Account_dict['Date'].date())
                #####################################

                if previous_date.date() != Account_dict['Date'].date():

                    print(f"## UPDATE : {mode} - {updated_date}")
                    collection.insert_one(Account_dict)
                            
                else:
                    print(f"## EXIST : {mode} - {updated_date}")
                    
            except Exception as e:
                print(e)
                print(f"## EXCEPTION : {mode} - {e}")
                
        else:
            collection = db.get_collection(mode)
            
            print(f"## NEW : {mode} - {updated_date}")
            collection.insert_one(Account_dict)
            