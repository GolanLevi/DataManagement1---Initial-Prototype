from flask import Flask, send_file, abort
from pymongo import MongoClient
import gridfs
import io
import os

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["fashion_db"]
fs = gridfs.GridFS(db)

@app.route("/api/glb/<item_id>")
def download_glb(item_id):
    file = db['fs.files'].find_one({
        "metadata.item_id": item_id,
        "filename": {"$regex": ".*\\.glb$"}
    })

    if not file:
        return abort(404, description="GLB not found for item_id")

    content = fs.get(file["_id"]).read()
    return send_file(
        io.BytesIO(content),
        download_name=file["filename"],
        as_attachment=True,
        mimetype="model/gltf-binary"
    )

if __name__ == "__main__":
    # שלב 1: ניקוי ספריית GLB
    glb_dir = r"C:\Users\97250\Desktop\Studies\Third year\Final Project\converted_glb"
    for f in os.listdir(glb_dir):
        if f.endswith(".glb"):
            os.remove(os.path.join(glb_dir, f))
    print("✅ Cleaned old GLB files")

    # שלב 2: מחיקת נתונים קודמים מהבסיסים
    from uploader import PostgresUploader, MongoUploader
    from processor import DatasetProcessor
    from converters.trimesh_converter import TrimeshConverter

    POSTGRES = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "123654",
        "database": "fashion_db"
    }
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "fashion_db"

    DATASET_DIRS = [
        r"C:\Users\97250\Desktop\Studies\Third year\Final Project\ClothesNetData\ClothesNetData\ClothesNetM",
        r"C:\Users\97250\Desktop\Studies\Third year\Final Project\ClothesNetData\ClothesNetData\Other_clothes"
    ]

    pg_uploader = PostgresUploader(POSTGRES)
    pg_uploader.reset_table()

    mongo_uploader = MongoUploader(MONGO_URI, MONGO_DB)
    mongo_uploader.reset()

    print("✅ Cleared old records from PostgreSQL and MongoDB")

    # שלב 3: המרה וטעינה מחדש של 10 פריטים מתיקייה
    converter = TrimeshConverter(glb_dir)
    processor = DatasetProcessor(DATASET_DIRS, glb_dir, converter, pg_uploader, mongo_uploader, max_per_category=2)

    report, inserted, failed = processor.process()
    print(f"✅ Inserted: {inserted}, Failed: {failed}")

    # שלב 4: הרצת Flask כרגיל
    app.run(debug=True)
