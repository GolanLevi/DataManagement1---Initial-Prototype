import os
import trimesh

class TrimeshConverter:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _fix_missing_texture(self, obj_path):
        mtl_path = obj_path.replace(".obj", ".mtl")
        if not os.path.exists(mtl_path):
            return

        with open(mtl_path, 'r') as f:
            lines = f.readlines()

        folder = os.path.dirname(obj_path)
        updated_lines = []
        for line in lines:
            if line.startswith("map_Kd"):
                texture_file = line.strip().split()[-1]
                texture_path = os.path.join(folder, texture_file)
                if not os.path.exists(texture_path):
                    print(f"⚠️ Texture {texture_file} not found for: {obj_path}")
            updated_lines.append(line)

        with open(mtl_path, 'w') as f:
            f.writelines(updated_lines)

    def convert(self, obj_path):
        self._fix_missing_texture(obj_path)

        try:
            mesh = trimesh.load(obj_path, force='scene')

            # צבע ברירת מחדל אם אין חומר עם טקסטורה
            if hasattr(mesh, 'geometry'):
                for name, geom in mesh.geometry.items():
                    if not hasattr(geom.visual, 'material') or geom.visual.material.image is None:
                        geom.visual.material = trimesh.visual.material.SimpleMaterial(color=[220, 220, 220, 255])

            output_path = os.path.join(self.output_dir, os.path.basename(obj_path).replace(".obj", ".glb"))
            mesh.export(output_path)
            print(f"✅ נוצר GLB: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ שגיאה בהמרת {obj_path}: {e}")
            return None
