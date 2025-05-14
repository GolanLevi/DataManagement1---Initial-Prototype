import os
import gridfs
import trimesh
from pymongo import MongoClient
from bson.objectid import ObjectId

class Fashion3DDataLoader:
    def __init__(self, mongo_uri, db_name, batch_size=8):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)
        self.batch_size = batch_size

    def list_available_items(self):
        return self.db['fs.files'].distinct("metadata.item_id")

    def load_batch(self, item_ids):
        batch = []
        for item_id in item_ids:
            glb_file = self.db['fs.files'].find_one({"metadata.item_id": item_id, "filename": {"$regex": ".*\.glb$"}})
            if not glb_file:
                print(f"No GLB file found for item_id: {item_id}")
                continue

            file_id = glb_file['_id']
            file_data = self.fs.get(ObjectId(file_id)).read()

            temp_path = f"temp_{item_id}.glb"
            with open(temp_path, 'wb') as f:
                f.write(file_data)

            try:
                mesh = trimesh.load(temp_path, force='mesh')
                batch.append({
                    "item_id": item_id,
                    "mesh": mesh
                })
            except Exception as e:
                print(f"Failed to load GLB mesh for {item_id}: {e}")
            finally:
                os.remove(temp_path)

        return batch

    def get_batches(self):
        item_ids = self.list_available_items()
        for i in range(0, len(item_ids), self.batch_size):
            yield self.load_batch(item_ids[i:i+self.batch_size])
