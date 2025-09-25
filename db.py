from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


mongo_client = MongoClient(os.getenv("ADS_URI"))

ad_manager_db = mongo_client["ad_manager_db"]

ads_collection = ad_manager_db["advert"]

users_collection = ad_manager_db["users"]