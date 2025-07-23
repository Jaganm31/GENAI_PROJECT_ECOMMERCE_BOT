

---

## 📦 Project Structure



# 🧠 GenAI E-commerce Assistant Bot

An intelligent AI-powered agent that answers natural language questions related to e-commerce data — powered by Google Gemini AI, PostgreSQL, FAISS, and Streamlit.

> 🔍 Ask anything like “What is my total sales?” or “Which product had the highest CPC?” and get smart insights, generated SQL queries, and interactive visualizations.

---

## 🚀 Features


✅ **Natural Language to SQL:** Converts user questions into valid PostgreSQL `SELECT` queries.

✅ **Gemini 1.5 Flash LLM Integration:** Leverages Google's powerful large language model for understanding and query generation.

✅ **Retrieval-Augmented Generation (RAG):** Integrates FAISS and Sentence Transformers to retrieve relevant context (database schema, column descriptions, example queries) for the LLM, significantly improving SQL generation accuracy.

✅ **Robust Data Preprocessing:** Cleans and transforms raw CSV data (handling missing values, cleaning numeric strings, converting data types, forcing categorical IDs to string type) before loading into PostgreSQL.

✅ **Dynamic Data Visualization:** Automatically identifies numeric, categorical, and datetime columns from query results to enable interactive charts (Bar, Pie, Line, Treemap, Scatter, Box, Histogram) using Plotly and Matplotlib.

✅ **Interactive Frontend:** A clean Streamlit dashboard for seamless interaction.

✅ **Chat History:** Maintains a history of questions and generated responses for easy review.

✅ **Detailed Output:** Displays the generated SQL query and the raw data table alongside the bot's answer.


---


## 📦 Project Structure

GenAI_Ecommerce_Project/
│
├── backend/                  # Flask API + Gemini integration
│   ├── run.py                # Main Flask application
│   ├── gemini_utils.py       # Handles Gemini API calls, RAG (FAISS), and prompt construction
│   └── route.py      # Backend Python dependencies
│
├── frontend/                 # Streamlit AI Dashboard
│   ├── app.py                # Streamlit application code
│ 
│
├── data_loader/              # Data preprocessing and loading scripts
│   ├── load_data.py          # Script to preprocess CSVs and load into PostgreSQL
│   
│
├── datasets/                 # Raw CSV datasets
│   ├── Product-Level Total Sales and Metrics (mapped).csv
│   ├── Product-Level Ad Sales and Metrics (mapped).csv
│   └── Product-Level Eligibility Table (mapped).csv
│
├── .env.example              # Example environment variables file (for backend/frontend)
├── requirements.txt
└── README.md                 # Project README file


## 🧠 Tech Stack

-   **Frontend:** Streamlit, Plotly Express, Matplotlib, Requests
-   **Backend:** Flask, SQLAlchemy, Google Gemini API, FAISS, Sentence Transformers, Pandas, python-dotenv
-   **Database:** PostgreSQL
-   **LLM Used:** Gemini 1.5 Flash

---

## 📊 Datasets Used

The following CSV files were converted into SQL tables:

1. `sales_summary` - Product-level total sales metrics  
2. `ad_data` - Product-level ad spend & performance  
3. `eligibility_status` - Product eligibility status (e.g., free delivery)

---

## 🧪 Example Questions

These are supported and tested:

| Question | Response Example |
|----------|------------------|
| What is my total sales? | ₹1,004,904.56 |
| Calculate the RoAS (Return on Ad Spend) | RoAS = 2.85 |
| Which product had the highest CPC? | Product ID = 22 |
| What is the average CPC by product? | [Bar Chart shown] |
| How many customers are eligible for free delivery? | 204 customers |

---

## ⚙️ How to Run Locally

### 1️⃣ Clone the Repo

```bash
git clone https://github.com/your-username/GenAI_Ecommerce_Project.git
cd GenAI_Project1
```

### 2️⃣ Setup Backend (Flask API)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r db/requirements.txt
```

Create a `.env` file inside `backend/db/` and add:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=genai_sales
GEMINI_API_KEY=your_api_key_here
```

Then run:

```bash
python run.py
```

Flask should run at `http://127.0.0.1:5000`

---

### 3️⃣ Setup Frontend (Streamlit)

In another terminal:

```bash
cd frontend
streamlit run app.py
```

---

## 🔐 How to Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Copy and paste it in `.env` under `GEMINI_API_KEY=`

> 🛑 If your key exceeds the free limit, generate a new one.

---

## 📽️ Demo Preview

> 🎥 [Video Link Here](https://drive.google.com/your-video-link)  
> 📂 [GitHub Repo Link](https://github.com/Jaganm31/GENAI_PROJECT_ECOMMERCE_BOT)

---

## 🎁 Bonus Implementations

✅ Streaming text output (live typing effect)  
✅ Beautiful and interactive Streamlit UI  
✅ Chat-like answer rendering (like: “Your total sales is ₹1,004,904.56”)  
✅ Auto-detected tables used from SQL  
✅ Theme toggle & animated interface  

---

## 🧠 Credits

Built as part of the **GenAI Intern Project** for [Anarx.ai].  

---



