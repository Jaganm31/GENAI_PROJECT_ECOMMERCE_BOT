import os
import google.generativeai as genai
from dotenv import load_dotenv
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- RAG Components Configuration ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # A good balance of performance and size
FAISS_INDEX_PATH = 'faiss_index.bin'
CONTEXT_DATA_PATH = 'context_data.json'

embedding_model = None
faiss_index = None
context_texts = []

def initialize_rag_components():
    """
    Initializes the SentenceTransformer model and FAISS index.
    Loads from disk if available, otherwise creates and saves.
    """
    global embedding_model, faiss_index, context_texts
    
    # Initialize embedding model
    if embedding_model is None:
        logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        try:
            embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        except Exception as e:
            logging.error(f"Failed to load SentenceTransformer model: {e}")
            logging.error("Please ensure you have an active internet connection or the model is cached locally.")
            # Fallback or raise error
            raise RuntimeError(f"Could not load embedding model: {e}")

    # Initialize FAISS index and context data
    if faiss_index is None:
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CONTEXT_DATA_PATH):
            logging.info("Loading FAISS index and context data from disk.")
            try:
                faiss_index = faiss.read_index(FAISS_INDEX_PATH)
                with open(CONTEXT_DATA_PATH, 'r') as f:
                    context_texts = json.load(f)
                logging.info(f"Loaded {len(context_texts)} context items.")
            except Exception as e:
                logging.error(f"Failed to load FAISS index or context data: {e}. Rebuilding index.")
                faiss_index = None # Reset to rebuild
                context_texts = []
        
        if faiss_index is None: # If not loaded, create new
            logging.info("Creating new FAISS index and context data.")
            # Define your knowledge base documents for RAG.
            # These are pieces of information the LLM can retrieve to answer questions.
            knowledge_base_documents = [
                # --- Schema Descriptions (Crucial) ---
                "Table: sales_summary, Columns: date (date), item_id (numeric ID), total_sales (numeric), total_units_ordered (numeric). Describes daily sales and units for items. Use for questions about sales, units, or item performance.",
                "Table: ad_data, Columns: date (date), item_id (numeric ID), ad_sales (numeric), impressions (numeric), ad_spend (numeric), clicks (numeric), units_sold (numeric). Contains advertising performance metrics. Use for questions about ads, spend, impressions, clicks, or ad-related sales.",
                "Table: eligibility_status, Columns: eligibility_datetime_utc (datetime), item_id (numeric ID), eligibility (text/boolean), message (text). Tracks item eligibility status. Use for questions about eligibility or status.",

                # --- Example Questions & SQL (from your original prompt, but also for RAG) ---
                "Q: What is the total revenue? A: SELECT SUM(total_sales) FROM sales_summary;",
                "Q: Show all ad-related metrics. A: SELECT * FROM ad_data;",
                "Q: Show eligibility status of items. A: SELECT item_id, eligibility, message FROM eligibility_status;",
                "Q: What is the highest CPC? A: SELECT MAX(ad_spend / clicks) FROM ad_data WHERE clicks > 0;", # Added division by zero prevention
                "Q: What is the total sales for each item? A: SELECT item_id, SUM(total_sales) AS total_sales_per_item FROM sales_summary GROUP BY item_id ORDER BY total_sales_per_item DESC;",
                "Q: Show me monthly ad spend over time. A: SELECT TO_CHAR(date, 'YYYY-MM') AS month, SUM(ad_spend) AS monthly_ad_spend FROM ad_data GROUP BY TO_CHAR(date, 'YYYY-MM') ORDER BY TO_CHAR(date, 'YYYY-MM');", # Ensure group by matches select
                "Q: Compare ad spend vs. ad sales for different items. A: SELECT item_id, SUM(ad_spend) AS total_ad_spend, SUM(ad_sales) AS total_ad_sales FROM ad_data GROUP BY item_id;",
                "Q: What is the average daily units ordered? A: SELECT AVG(total_units_ordered) FROM sales_summary;",
                "Q: Which item has the most impressions? A: SELECT item_id, SUM(impressions) AS total_impressions FROM ad_data GROUP BY item_id ORDER BY total_impressions DESC LIMIT 1;",
                "Q: How many items are currently eligible? A: SELECT COUNT(DISTINCT item_id) FROM eligibility_status WHERE eligibility = 'true';", # Assuming 'true' is a common eligibility value

                # --- Column-specific details / Calculations ---
                "Column: total_sales (sales_summary) - monetary value of sales.",
                "Column: total_units_ordered (sales_summary) - quantity of items sold.",
                "Column: ad_spend (ad_data) - money spent on advertising campaigns.",
                "Column: ad_sales (ad_data) - sales directly generated from ads.",
                "Column: clicks (ad_data) - number of times ads were clicked.",
                "Column: impressions (ad_data) - number of times ads were shown.",
                "Column: units_sold (ad_data) - quantity of units sold through advertising.",
                "Column: eligibility (eligibility_status) - status of an item's eligibility (e.g., 'true', 'false', 'eligible', 'not eligible').",
                "Calculation: ROAS (Return on Ad Spend) = SUM(ad_sales) / SUM(ad_spend).",
                "Calculation: CPC (Cost Per Click) = ad_spend / clicks.",
                "Calculation: CTR (Click-Through Rate) = clicks / impressions.",
                "Always use TO_CHAR(date_column, 'YYYY-MM') for monthly grouping in PostgreSQL."
            ]
            context_texts = knowledge_base_documents
            
            # Encode documents to get embeddings
            embeddings = embedding_model.encode(knowledge_base_documents)
            dimension = embeddings.shape[1] # Dimension of the embeddings

            # Create FAISS index (L2 distance is common for semantic similarity)
            faiss_index = faiss.IndexFlatL2(dimension)
            faiss_index.add(np.array(embeddings).astype('float32')) # FAISS expects float32

            # Save the index and context data for future use
            faiss.write_index(faiss_index, FAISS_INDEX_PATH)
            with open(CONTEXT_DATA_PATH, 'w') as f:
                json.dump(context_texts, f)
            logging.info(f"Created and saved FAISS index with {len(context_texts)} items.")

# Initialize RAG components when the module is loaded
# This ensures they are ready before any Flask route tries to use get_sql_from_question
initialize_rag_components()

# SYSTEM_PROMPT now includes a placeholder for retrieved context
SYSTEM_PROMPT_TEMPLATE = """
You are a helpful and precise assistant that converts user questions into valid PostgreSQL SELECT queries.

You are working with a PostgreSQL database called `ecommerce_data` containing these **exact tables and columns**:

📌 Table: `sales_summary`
- date
- item_id
- total_sales
- total_units_ordered

📌 Table: `ad_data`
- date
- item_id
- ad_sales
- impressions
- ad_spend
- clicks
- units_sold

📌 Table: `eligibility_status`
- eligibility_datetime_utc
- item_id
- eligibility
- message

⚠️ Use these **exact table names**: `sales_summary`, `ad_data`, `eligibility_status`. Do NOT invent or singularize them (e.g., do NOT use `ad_sale` or `total_sale`).

🧠 Rules:
- Only return valid **PostgreSQL** SELECT statements.
- Avoid division by zero. Use WHERE clause or CASE WHEN to prevent it.
- Do not explain or format output.
- Return pure SQL (no ```sql or comments).
- Do not add LIMIT unless explicitly asked.

{retrieved_context}

Here are some examples:
Q: What is the total revenue?
A: SELECT SUM(total_sales) FROM sales_summary;

Q: Show all ad-related metrics.
A: SELECT * FROM ad_data;

Q: Show eligibility status of items.
A: SELECT item_id, eligibility, message FROM eligibility_status;

Now convert the user's question to a valid SQL query.
"""

model = genai.GenerativeModel("models/gemini-1.5-flash")

# ✅ Convert question to SQL with RAG
def get_sql_from_question(question: str) -> str:
    """
    Generates a SQL query from a natural language question using RAG.
    Retrieves relevant context from a FAISS index to augment the LLM prompt.
    """
    try:
        # Ensure RAG components are initialized (redundant call, but safe)
        if embedding_model is None or faiss_index is None:
            initialize_rag_components()

        # Retrieve relevant context using FAISS
        query_embedding = embedding_model.encode([question]).astype('float32')
        # Search for top K (e.g., 3) most similar documents
        distances, indices = faiss_index.search(query_embedding, k=3)

        retrieved_context_str = "\n\nRelevant Context for your question:\n"
        # Add retrieved documents to the context string
        for i, idx in enumerate(indices[0]):
            retrieved_context_str += f"- {context_texts[idx]}\n"

        # Augment the system prompt using the template and retrieved context
        final_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(retrieved_context=retrieved_context_str)

        # Construct the full prompt for Gemini
        prompt = f"{final_system_prompt}\n\nUser Question: {question}\nSQL Query:"
        
        logging.info(f"Sending prompt to Gemini:\n{prompt[:500]}...") # Log part of the prompt

        response = model.generate_content(prompt)
        sql_query = response.text.strip().strip("```sql").strip("```").strip()
        
        logging.info(f"Received SQL from Gemini: {sql_query}")
        return sql_query
    except Exception as e:
        logging.error(f"❌ Error generating SQL with RAG: {str(e)}", exc_info=True) # Log full traceback
        return f"❌ Error generating SQL: {str(e)}"