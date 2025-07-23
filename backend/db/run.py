from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from urllib.parse import quote_plus

# Import the RAG-enabled SQL generation function
from gemini_utils import get_sql_from_question

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)
CORS(app)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# ✅ Encode password
encoded_password = quote_plus(DB_PASSWORD)
# Ensure the database connection string is correct for PostgreSQL
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}")

VALID_TABLES = ["sales_summary", "ad_data", "eligibility_status"]

# ✅ Root route
@app.route('/')
def index():
    return "✅ GenAI E-commerce Agent is running!"

# ✅ Route: Load specific table data (no change needed)
@app.route('/api/data/<table_name>', methods=['GET'])
def get_table_data(table_name):
    if table_name not in VALID_TABLES:
        return jsonify({"error": "Invalid table name."}), 400
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = [dict(row._mapping) for row in result]
        return jsonify(rows)
    except Exception as e:
        logging.error("❌ Error fetching table: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        question = data.get('question')

        if not question:
            return jsonify({"error": "No question provided."}), 400

        # ✅ Get SQL from Gemini (now with RAG internally)
        sql_query = get_sql_from_question(question)
        logging.info("🔍 Generated SQL:\n%s", sql_query)

        # Handle potential error from get_sql_from_question
        if sql_query.startswith("❌ Error"):
            return jsonify({"error": sql_query}), 500

        # ✅ Run query
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            # Convert SQLAlchemy Row objects to dictionaries
            rows = [dict(row._mapping) for row in result]

        return jsonify({
            "question": question,
            "sql": sql_query,
            "result": rows
        })

    except Exception as e:
        logging.error("❌ Error in /api/ask: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)