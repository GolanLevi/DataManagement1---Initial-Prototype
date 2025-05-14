import os
from dotenv import load_dotenv
from converters.trimesh_converter import TrimeshConverter
from uploader import PostgresUploader, MongoUploader
from processor import DatasetProcessor

load_dotenv()

# הגדרות חיבור למסדי נתונים
POSTGRES = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT")),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB")
}

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

# נתיבי קלט/פלט
DATASET_DIRS = [
    r"C:\Users\97250\Desktop\Studies\Third year\Final Project\ClothesNetData\ClothesNetData\ClothesNetM",
    r"C:\Users\97250\Desktop\Studies\Third year\Final Project\ClothesNetData\ClothesNetData\Other_clothes"
]
OUTPUT_DIR = r"C:\Users\97250\Desktop\Studies\Third year\Final Project\converted_glb"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# יצירת מופעים
pg_uploader = PostgresUploader(POSTGRES)
pg_uploader.reset_table()

mongo_uploader = MongoUploader(MONGO_URI, MONGO_DB)
mongo_uploader.reset()

converter = TrimeshConverter(OUTPUT_DIR)
processor = DatasetProcessor(DATASET_DIRS, OUTPUT_DIR, converter, pg_uploader, mongo_uploader, max_per_category=2)

# ביצוע עיבוד
report, inserted, failed = processor.process()

# דיווח
print("✅ Conversion complete")
print(f"Inserted: {inserted} | Failed: {failed}")
mongo_uploader.print_summary()
