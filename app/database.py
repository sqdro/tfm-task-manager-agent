from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["tfm_agent"]
projects_collection = db["projects"]
tasks_collection = db["tasks"]