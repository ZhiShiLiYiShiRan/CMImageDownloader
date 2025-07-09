from pymongo import MongoClient

client = MongoClient("")  # 可复制你.env 中的 URI
db = client["chillmartTemp"]
collection = db["qa_bot"]

doc = {"test": "这是测试", "status": "OK"}
result = collection.insert_one(doc)
print("✅ 插入成功 ID:", result.inserted_id)
