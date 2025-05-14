# import sys
# import os
#
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#
# from better_converter import BetterConverter
# from uploader import PostgresUploader, MongoUploader
# from processor import DatasetProcessor
#
# POSTGRES = {
#     "host": "localhost",
#     "port": 5432,
#     "user": "postgres",
#     "password": "123654",
#     "database": "fashion_db"
# }
#
# MONGO_URI = "mongodb://localhost:27017/"
# MONGO_DB = "fashion_db"
#
# DATASET_DIRS = [
#     r"C:\Users\97250\Desktop\Studies\Third year\Final Project\ClothesNetData\ClothesNetData\ClothesNetM",
#     r"C:\Users\97250\Desktop\Studies\Third year\Final Project\ClothesNetData\ClothesNetData\Other_clothes"
# ]
#
# OUTPUT_DIR = r"C:\Users\97250\Desktop\Studies\Third year\Final Project\converted_glb"
# BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
#
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
# pg_uploader = PostgresUploader(POSTGRES)
# pg_uploader.reset_table()
#
# mongo_uploader = MongoUploader(MONGO_URI, MONGO_DB)
# mongo_uploader.reset()
#
# converter = BetterConverter(OUTPUT_DIR, BLENDER_PATH)
# processor = DatasetProcessor(DATASET_DIRS, OUTPUT_DIR, converter, pg_uploader, mongo_uploader)
#
# report, inserted, failed = processor.process()
#
# print(f"Inserted: {inserted} | Failed: {failed}")
# mongo_uploader.print_summary()
