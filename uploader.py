import os
import gridfs
import trimesh
from pymongo import MongoClient
import psycopg2
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
                path TEXT,
                has_obj BOOLEAN,
                has_mtl BOOLEAN,
                has_pcd BOOLEAN,
                has_keypoints BOOLEAN,
                has_border BOOLEAN,
                texture_count INTEGER,
                polygon_count INTEGER,
                file_size_kb INTEGER,
                category TEXT,
                source_format TEXT,
                converted_to TEXT,
                mesh_density FLOAT,
                num_mesh_parts INTEGER,
                num_materials INTEGER,
                num_uv_maps INTEGER,
                metadata_notes TEXT,
                avg_edge_length FLOAT,
                bounding_box_volume FLOAT,
                is_closed BOOLEAN,
                genus INTEGER,
                surface_area FLOAT,
                analysis_success BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def analyze_mesh(self, glb_path):
        try:
            mesh = trimesh.load(glb_path, force='mesh')
            return {
                'polygon_count': len(mesh.faces),
                'file_size_kb': int(os.path.getsize(glb_path) / 1024),
                'avg_edge_length': float(mesh.edges_unique_length.mean()) if mesh.edges_unique_length.size > 0 else None,
                'bounding_box_volume': float(mesh.bounding_box_oriented.volume),
                'is_closed': bool(mesh.is_watertight),
                'genus': int(mesh.euler_number),
                'surface_area': float(mesh.area),
                'mesh_density': float(len(mesh.faces) / mesh.area) if mesh.area > 0 else None,
                'num_mesh_parts': len(mesh.split(only_watertight=False)) if hasattr(mesh, 'split') else 1,
                'num_materials': len(mesh.visual.materials) if hasattr(mesh.visual, 'materials') else 1,
                'num_uv_maps': 1 if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None else 0,
                'analysis_success': True
            }
        except Exception as e:
            print(f"[Error] Failed to analyze mesh {glb_path}: {e}")
            return {'analysis_success': False}

    def upload(self, meta, glb_path):
        try:
            analysis = self.analyze_mesh(glb_path)
            meta.update(analysis)
            self.cursor.execute("""
                INSERT INTO fashion_items (
                    item_id, path, has_obj, has_mtl, has_pcd, has_keypoints, has_border,
                    texture_count, polygon_count, file_size_kb, category, source_format,
                    converted_to, mesh_density, num_mesh_parts, num_materials, num_uv_maps,
                    metadata_notes, avg_edge_length, bounding_box_volume, is_closed,
                    genus, surface_area, analysis_success
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    mesh_density = EXCLUDED.mesh_density,
                    num_mesh_parts = EXCLUDED.num_mesh_parts,
                    num_materials = EXCLUDED.num_materials,
                    num_uv_maps = EXCLUDED.num_uv_maps,
                    metadata_notes = EXCLUDED.metadata_notes,
                    avg_edge_length = EXCLUDED.avg_edge_length,
                    bounding_box_volume = EXCLUDED.bounding_box_volume,
                    is_closed = EXCLUDED.is_closed,
                    genus = EXCLUDED.genus,
                    surface_area = EXCLUDED.surface_area,
                    analysis_success = EXCLUDED.analysis_success;
            """, (
                meta['item_id'], meta['path'], meta['has_obj'], meta['has_mtl'], meta['has_pcd'],
                meta['has_keypoints'], meta['has_border'], len(meta['textures']),
                meta.get('polygon_count'), meta.get('file_size_kb'), meta.get('category'),
                meta.get('source_format'), meta.get('converted_to'), meta.get('mesh_density'),
                meta.get('num_mesh_parts'), meta.get('num_materials'), meta.get('num_uv_maps'),
                meta.get('metadata_notes'), meta.get('avg_edge_length'), meta.get('bounding_box_volume'),
                meta.get('is_closed'), meta.get('genus'), meta.get('surface_area'), meta.get('analysis_success')
            ))
            self.conn.commit()
        except Exception as e:
            print(f"[Error] Failed to upload to Postgres for {meta['item_id']}: {e}")
            self.conn.rollback()


class MongoUploader:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)
        self.deleted_count = 0
        self.uploaded_count = 0
        self.failed_count = 0

    def reset(self):
        self.db['fs.files'].delete_many({})
        self.db['fs.chunks'].delete_many({})

    def upload(self, meta, glb_path):
        if not os.path.exists(glb_path):
            print(f"[Skip] File does not exist: {glb_path}")
            self.failed_count += 1
            return

        fname = os.path.basename(glb_path)

        try:
            existing_file = self.db['fs.files'].find_one({"filename": fname, "metadata.item_id": meta['item_id']})
            if existing_file:
                self.fs.delete(existing_file['_id'])
                print(f"[Deleted] Existing GLB file for item_id: {meta['item_id']} (filename: {fname})")
                self.deleted_count += 1

            print(f"[Uploading] {fname} for item_id: {meta['item_id']}")
            with open(glb_path, 'rb') as f:
                self.fs.put(f, filename=fname, metadata={"item_id": meta['item_id'], "folder": meta['path']})

            print(f"[Success] Uploaded {fname} for item_id: {meta['item_id']}")
            self.uploaded_count += 1

        except Exception as e:
            print(f"[Failed] Could not upload {fname} for item_id {meta['item_id']}: {e}")
            self.failed_count += 1

    def print_summary(self):
        print("\n===== MongoDB Upload Summary =====")
        print(f"Uploaded files: {self.uploaded_count}")
        print(f"Replaced (deleted old and uploaded new): {self.deleted_count}")
        print(f"Failed uploads: {self.failed_count}")
        print("===================================")