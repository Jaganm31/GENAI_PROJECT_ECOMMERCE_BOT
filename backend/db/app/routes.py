from flask import jsonify, request
from app.utils import fetch_table_data

def register_routes(app):
    @app.route('/')
    def home():
        return jsonify({"message": "🧠 GenAI Ecommerce Backend Running!"})

    @app.route('/api/data/<table_name>', methods=['GET'])
    def get_table_data(table_name):
        try:
            data = fetch_table_data(table_name)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
