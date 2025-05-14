# from flask import Flask, render_template, jsonify, send_file
# from flask_cors import CORS
# import psycopg2
# import gridfs
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# import io
#
# app = Flask(__name__, static_folder='static', template_folder='templates')
# CORS(app)
#
# pg_conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123654', database='fashion_db')
# pg_cursor = pg_conn.cursor()
#
# mongo_client = MongoClient('mongodb://localhost:27017/')
# mongo_db = mongo_client['fashion_db']
# mongo_fs = gridfs.GridFS(mongo_db)
#
# @app.route('/api/metadata/<item_id>', methods=['GET'])
# def get_metadata(item_id):
#     pg_cursor.execute("SELECT * FROM fashion_items WHERE item_id = %s", (item_id,))
#     row = pg_cursor.fetchone()
#     if row:
#         colnames = [desc[0] for desc in pg_cursor.description]
#         return jsonify(dict(zip(colnames, row)))
#     else:
#         return jsonify({"error": "Item not found"}), 404
#
# @app.route('/api/glb/<item_id>', methods=['GET'])
# def get_glb(item_id):
#     file_doc = mongo_db['fs.files'].find_one({"metadata.item_id": item_id, "filename": {"$regex": ".*\\.glb$"}})
#     if not file_doc:
#         return jsonify({"error": "GLB file not found"}), 404
#
#     file_id = file_doc['_id']
#     file_data = mongo_fs.get(ObjectId(file_id)).read()
#     return send_file(io.BytesIO(file_data), download_name=file_doc['filename'], mimetype='model/gltf-binary')
#
# @app.route('/viewer')
# def viewer():
#     return render_template('index.html')
#
# if __name__ == '__main__':
#     app.run(debug=True)
