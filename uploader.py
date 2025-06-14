import os
import gridfs
import trimesh
import psycopg2
from pymongo import MongoClient
from bson.objectid import ObjectId

class PostgresUploader:
    def __init__(self, config):
        self.conn = psycopg2.connect(**config)
        self.cursor = self.conn.cursor()

    def reset_table(self):
        self.cursor.execute("""
            DROP TABLE IF EXISTS fashion_items;
        """)
        self.cursor.execute("""
            CREATE TABLE fashion_items (
                item_id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                has_obj BOOLEAN NOT NULL,
                has_mtl BOOLEAN NOT NULL,
                has_pcd BOOLEAN NOT NULL,
                has_keypoints BOOLEAN NOT NULL,
                has_border BOOLEAN NOT NULL,
                texture_count INTEGER NOT NULL,
                polygon_count INTEGER,
                file_size_kb INTEGER,
                category TEXT NOT NULL,
                source_format TEXT NOT NULL,
                converted_to TEXT NOT NULL,
                analysis_success BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def analyze_mesh(self, glb_path):
        try:
            mesh = None
            try:
                mesh = trimesh.load(glb_path, force='mesh')
            except Exception:
                try:
                    scene = trimesh.load(glb_path, force='scene')
                    mesh = scene.dump().sum()
                except Exception:
                    raise RuntimeError("Mesh could not be loaded from scene or mesh mode")

            polygon_count = len(mesh.faces) if hasattr(mesh, 'faces') else 0
            file_size_kb = int(os.path.getsize(glb_path) / 1024) if os.path.exists(glb_path) else 0

            has_texture = False
            if hasattr(mesh.visual, 'material'):
                mat = mesh.visual.material
                if hasattr(mat, 'image') and mat.image is not None:
                    has_texture = True
                elif hasattr(mat, 'baseColorTexture') and mat.baseColorTexture is not None:
                    has_texture = True

            return {
                'polygon_count': polygon_count,
                'file_size_kb': file_size_kb,
                'analysis_success': has_texture
            }

        except Exception as e:
            print(f"[Warning] Analysis failed for {glb_path}: {e}. Attempting partial recovery.")
            try:
                file_size_kb = int(os.path.getsize(glb_path) / 1024) if os.path.exists(glb_path) else 0
            except:
                file_size_kb = 0

            return {
                'polygon_count': 0,
                'file_size_kb': file_size_kb,
                'analysis_success': False
            }

    def upload(self, meta, glb_path):
        try:
            analysis = self.analyze_mesh(glb_path)
            meta.update(analysis)

            self.cursor.execute("""
                INSERT INTO fashion_items (
                    item_id, path, has_obj, has_mtl, has_pcd, has_keypoints, has_border,
                    texture_count, polygon_count, file_size_kb, category, source_format,
                    converted_to, analysis_success
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_id) DO UPDATE SET
                    path = EXCLUDED.path,
                    has_obj = EXCLUDED.has_obj,
                    has_mtl = EXCLUDED.has_mtl,
                    has_pcd = EXCLUDED.has_pcd,
                    has_keypoints = EXCLUDED.has_keypoints,
                    has_border = EXCLUDED.has_border,
                    texture_count = EXCLUDED.texture_count,
                    polygon_count = EXCLUDED.polygon_count,
                    file_size_kb = EXCLUDED.file_size_kb,
                    category = EXCLUDED.category,
                    source_format = EXCLUDED.source_format,
                    converted_to = EXCLUDED.converted_to,
                    analysis_success = EXCLUDED.analysis_success;
            """, (
                meta['item_id'], meta['path'], meta['has_obj'], meta['has_mtl'], meta['has_pcd'],
                meta['has_keypoints'], meta['has_border'], len(meta['textures']),
                meta['polygon_count'], meta['file_size_kb'], meta['category'],
                meta['source_format'], meta['converted_to'], meta['analysis_success']
            ))
            self.conn.commit()
        except Exception as e:
            print(f"[Error] Failed to upload to Postgres for {meta['item_id']}: {e}")
            self.conn.rollback()


class MongoUploader:
    def __init__(self, mongo_uri, db_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)
        self.collection = self.db["fashion_items"]

    def reset(self):
        self.db.drop_collection("fashion_items")
        self.db.drop_collection("fs.files")
        self.db.drop_collection("fs.chunks")

    def upload(self, meta, glb_path):
        with open(glb_path, "rb") as f:
            file_id = self.fs.put(f, filename=os.path.basename(glb_path), metadata=meta)
            self.collection.replace_one({"_id": meta["item_id"]}, {"_id": meta["item_id"], "file_id": file_id, **meta}, upsert=True)

    def print_summary(self):
        count = self.collection.count_documents({})
        print(f"✅ MongoDB contains {count} documents")
