import os

class DatasetProcessor:
    def __init__(self, dataset_dirs, output_dir, converter, pg_uploader, mongo_uploader, max_per_category=2):
        self.dataset_dirs = dataset_dirs
        self.output_dir = output_dir
        self.converter = converter
        self.pg_uploader = pg_uploader
        self.mongo_uploader = mongo_uploader
        self.max_per_category = max_per_category
        self.category_counter = {}
        self.report = []

    def analyze_folder(self, folder_path):
        files = os.listdir(folder_path)
        return {
            "item_id": os.path.basename(folder_path),
            "path": folder_path,
            "has_obj": any(f.endswith(".obj") and not f.startswith("border") for f in files),
            "has_mtl": any(f.endswith(".mtl") for f in files),
            "has_pcd": any(f.endswith(".pcd") and not f.startswith("kp_") for f in files),
            "has_keypoints": any(f.startswith("kp_") and f.endswith(".pcd") for f in files),
            "has_border": any(f.startswith("border") and f.endswith(".obj") for f in files),
            "textures": [f for f in files if f.endswith(".png")],
            "all_files": files,
            "category": os.path.basename(os.path.dirname(folder_path)),
            "source_format": "obj",
            "converted_to": "glb",
            "metadata_notes": None
        }

    def process(self):
        count_inserted = 0
        count_failed = 0

        for base_dir in self.dataset_dirs:
            for root, dirs, files in os.walk(base_dir):
                if any(f.endswith(".obj") for f in files):
                    category = os.path.basename(os.path.dirname(root))
                    self.category_counter.setdefault(category, 0)
                    if self.category_counter[category] >= self.max_per_category:
                        continue

                    try:
                        meta = self.analyze_folder(root)

                        for f in meta['all_files']:
                            if f.endswith(".obj") and not f.startswith("border"):
                                obj_path = os.path.join(meta['path'], f)
                                glb_path = self.converter.convert(obj_path)
                                if glb_path:
                                    try:
                                        meta['path'] = glb_path
                                        self.pg_uploader.upload(meta, glb_path)
                                        self.mongo_uploader.upload(meta, glb_path)
                                        self.category_counter[category] += 1
                                        meta['status'] = 'OK'
                                        count_inserted += 1
                                    except Exception as upload_error:
                                        meta['status'] = f'FAIL: Upload failed: {upload_error}'
                                        print(f"Upload failed for {meta['item_id']}: {upload_error}")
                                        count_failed += 1
                                else:
                                    meta['status'] = 'FAIL: GLB conversion failed'
                                    count_failed += 1
                        self.report.append(meta)

                    except Exception as e:
                        meta = {"item_id": os.path.basename(root), "path": root, "status": f'FAIL: {str(e)}'}
                        print(f"Error processing {meta['item_id']}: {e}")
                        self.report.append(meta)
                        count_failed += 1

        return self.report, count_inserted, count_failed
