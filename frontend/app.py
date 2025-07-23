import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import io # For capturing matplotlib figures

# --- PAGE SETTINGS ---
st.set_page_config(page_title="🤖 E-commerce Assistant Bot", layout="wide", initial_sidebar_state="expanded")

# --- CSS ---
st.markdown("""
<style>
.big-title {
    font-size: 38px !important;
    font-weight: bold;
    color: #4CAF50; /* Green */
    text-align: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #eee;
}
.subtle {
    color: #666;
    font-size: 18px;
    text-align: center;
    margin-bottom: 30px;
}
.bot-box {
    background-color: #e6ffe6; /* Light green for bot answers */
    padding: 20px;
    border-radius: 12px;
    font-size: 19px;
    font-weight: 500;
    color: #2e7d32; /* Darker green text */
    margin-top: 15px;
    margin-bottom: 20px;
    border: 1px solid #c8e6c9;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    white-space: pre-wrap;
    word-break: break-word; /* Ensure long words break */
}
.dark .bot-box {
    background-color: #384238; /* Darker green for dark mode */
    color: #c8e6c9;
    border: 1px solid #5a6b5a;
}
.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size: 1.15rem; /* Larger tab labels */
    font-weight: bold;
}
.stButton>button {
    background-color: #4CAF50; /* Green button */
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 18px;
    font-weight: bold;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background-color: #45a049; /* Darker green on hover */
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
}
.stTextInput>div>div>input {
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="big-title">🧠 E-commerce Assistant Bot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Ask any business question and get insights powered by AI</div>', unsafe_allow_html=True)

# --- EXAMPLES ---
with st.expander("💡 Example Questions", expanded=False):
    st.markdown("""
    - 💰 *What is my total sales?*
    - 🎯 *Which product had the highest CPC?*
    - 🚚 *How many customers are eligible for free delivery?*
    - 📉 *What is my RoAS (Return on Ad Spend)?*
    - 📈 *Show me monthly sales trends over the last year.*
    - 📊 *Compare average order value by customer segment.*
    - **New!** Show total sales for each item.
    """)

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_question_input" not in st.session_state:
    st.session_state.current_question_input = ""

API_URL = "http://127.0.0.1:5000/api/ask" # Ensure your backend Flask app is running here
st.markdown("---")

# --- INPUT ---
question = st.text_input(
    "💬 Ask your e-commerce data question here:",
    placeholder="e.g. Show average CPC by product...",
    key="user_question_input",
    value=st.session_state.current_question_input
)

col_ask_button, col_clear_button = st.columns([0.2, 0.8])
with col_ask_button:
    if st.button("🚀 Ask Bot", key="ask_button"):
        if not question.strip():
            st.warning("⚠️ Please enter a question.")
        else:
            with st.spinner("🤖 Bot is thinking..."):
                try:
                    response = requests.post(API_URL, json={"question": question})
                    data = response.json()

                    if 'error' in data:
                        st.error("❌ " + data['error'])
                    else:
                        st.success("✅ Bot answered your question!") # Keep this general success message
                        result = data.get("result", None)
                        sql = data.get("sql", "No SQL generated.")

                        # Smart answer formatting (modified to remove the specific "data table" message)
                        answer_text = "⚠️ No meaningful result returned."
                        if isinstance(result, list) and result and isinstance(result[0], dict):
                            # Check if it's a single value result (e.g., total sales)
                            if len(result) == 1 and len(result[0]) == 1:
                                value = list(result[0].values())[0]
                                try:
                                    if isinstance(value, (int, float)):
                                        answer_text = f"💰 Your result: **₹{value:,.2f}**"
                                    else:
                                        answer_text = f"📢 Result: **{value}**"
                                except (ValueError, TypeError):
                                    answer_text = f"📢 Result: **{value}**"
                            else:
                                # For multi-row results, just indicate success, the tabs below show the data
                                answer_text = "✅ Your data is ready! Explore the visualizations and table below. 📊"
                        elif isinstance(result, str):
                            answer_text = result
                        elif result is None:
                            answer_text = "ℹ️ The bot processed your request but returned no specific data or a textual response."

                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": answer_text,
                            "sql": sql,
                            "data": result
                        })
                        st.session_state.current_question_input = ""

                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to the API. Please ensure the backend is running at `http://127.0.0.1:5000`.")
                except Exception as e:
                    st.error(f"❌ An unexpected error occurred: {str(e)}")
with col_clear_button:
    if st.button("🗑️ Clear History", key="clear_history_button"):
        st.session_state.chat_history = []
        st.session_state.current_question_input = ""
        st.success("Chat history cleared!")

# --- CHAT HISTORY ---
st.sidebar.markdown("### 📜 Chat History")
if st.session_state.chat_history:
    for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
        with st.sidebar.expander(f"Q{len(st.session_state.chat_history) - i + 1}: {chat['question'][:40]}...", expanded=False):
            st.markdown(f"**Question:** {chat['question']}")
            st.markdown(f"**Answer:** {chat['answer']}")
            if st.checkbox(f"🔍 Show SQL", key=f"sql_sidebar_{len(st.session_state.chat_history) - i + 1}"):
                st.code(chat["sql"], language="sql")
else:
    st.sidebar.info("No chat history yet. Ask a question to start!")

st.markdown("---")

# --- DISPLAY LATEST RESPONSE ---
if st.session_state.chat_history:
    latest = st.session_state.chat_history[-1]
    result = latest["data"]
    sql = latest["sql"]

    st.markdown("### 🤖 Bot's Response:")
    st.markdown(f'<div class="bot-box">{latest["answer"]}</div>', unsafe_allow_html=True)

    st.markdown("### 🧾 SQL Query Used")
    st.code(sql, language="sql")

    # --- VISUALIZATION & TABLE ---
    if isinstance(result, list) and result:
        df = pd.DataFrame(result)

        # --- IMPORTANT: Data Type Conversion for Robust Visualization ---
        # Define columns that should *always* be treated as categorical, even if they look numeric
        # Add any other ID columns (like customer_id, product_category_id if they are categories)
        known_categorical_id_cols = ['item_id']

        for col in df.columns:
            # First, attempt to convert to numeric for all columns
            # This covers sales, spend, etc., and also *numeric-like* IDs before we force them to string
            try:
                # Clean potential non-numeric characters if it's an object type (string)
                if df[col].dtype == 'object':
                    cleaned_col = df[col].astype(str).str.replace(r'[₹$,% ]', '', regex=True)
                    df[col] = pd.to_numeric(cleaned_col, errors='coerce')
                # If not an object type, still try to convert to numeric (e.g., bools)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass # Silently ignore if numeric conversion fails

            # Then, attempt datetime conversion for 'object' types that remain after numeric attempts
            # This is important if a column is like 'YYYY-MM-DD'
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
                except Exception:
                    pass # Silently ignore if datetime conversion fails
        
        # --- NEW: Explicitly convert known ID columns to string AFTER all other conversions ---
        # This ensures they are definitively treated as categorical and not re-converted to numeric.
        for col in known_categorical_id_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                # Only convert if it's currently numeric, meaning it passed the numeric check
                df[col] = df[col].astype(str)


        # Re-identify columns after all potential type conversions
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        category_cols = df.select_dtypes(include=['object', 'category']).columns.tolist() # Ensure 'category' dtype is included
        datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()

        # Filter out columns that are all NaN after conversion
        numeric_cols = [col for col in numeric_cols if not df[col].isnull().all()]
        category_cols = [col for col in category_cols if not df[col].isnull().all()]
        datetime_cols = [col for col in datetime_cols if not df[col].isnull().all()]

        if not df.empty:
            st.markdown("---")
            st.markdown("### 📊 Data Overview & Visualization")

            col_total_rows, col_avg_value = st.columns(2)
            with col_total_rows:
                st.metric("📌 Total Rows", len(df))
            with col_avg_value:
                if numeric_cols:
                    suitable_numeric_col = next((col for col in numeric_cols if df[col].sum() != 0 and not df[col].isnull().all()), None)
                    if suitable_numeric_col:
                        st.metric(f"📊 Avg {suitable_numeric_col}", f"{df[suitable_numeric_col].mean():,.2f}")
                    else:
                        st.metric("📊 Avg Numeric Value", "N/A (All zeros, NaN, or no suitable numeric columns)")
                else:
                    st.metric("📊 Avg Numeric Value", "N/A (No numeric columns)")

            tab1, tab2, tab3 = st.tabs(["📊 Visual Creator", "📋 Data Table", "📘 Explanation"])

            with tab1:
                if df.shape[0] < 1:
                    st.info("ℹ️ No data to visualize, or only header rows present.")
                else:
                    st.markdown("#### Configure Your Chart")
                    viz_lib = st.radio("Choose visualization library:", ["Plotly", "Matplotlib"], horizontal=True, key="viz_lib_main")

                    x_axis_options = ["--- Select X-axis ---"]
                    if datetime_cols: x_axis_options.extend(datetime_cols)
                    if category_cols: x_axis_options.extend(category_cols)
                    if numeric_cols: x_axis_options.extend(numeric_cols)

                    y_axis_options = ["--- Select Y-axis ---"]
                    if numeric_cols: y_axis_options.extend(numeric_cols)

                    col_x_select, col_y_select = st.columns(2)
                    with col_x_select:
                        x_axis = st.selectbox("X-axis (e.g., Category, Date, or Numeric)", x_axis_options, key="x_axis_select")
                    with col_y_select:
                        y_axis = st.selectbox("Y-axis (e.g., Sales, Price, Count - usually Numeric)", y_axis_options, key="y_axis_select")

                    chart_type_options = ["--- Select Chart Type ---"]

                    x_is_categorical = x_axis in category_cols
                    x_is_datetime = x_axis in datetime_cols
                    x_is_numeric = x_axis in numeric_cols
                    y_is_numeric = y_axis in numeric_cols

                    if y_is_numeric:
                        if x_is_categorical or x_is_datetime:
                            chart_type_options.extend(["Bar Chart", "Line Chart", "Box Plot"])
                            if x_is_categorical and len(df[x_axis].dropna().unique()) <= 20:
                                chart_type_options.append("Pie Chart")
                            if x_is_categorical:
                                chart_type_options.append("Treemap")
                        elif x_is_numeric:
                            chart_type_options.extend(["Scatter Plot", "Line Chart"])
                        else:
                            chart_type_options.append("Histogram")
                    else:
                        if x_is_categorical and len(category_cols) > 0:
                            st.info("💡 Select a numeric column for Y-axis to see more chart options.")

                    chart_type = st.selectbox("Chart Type", chart_type_options, key="chart_type_select")

                    if st.button("Generate Chart 📈", key="generate_chart_button_final"):
                        if chart_type == "--- Select Chart Type ---":
                            st.warning("⚠️ Please select a chart type.")
                        elif chart_type != "Histogram" and (y_axis == "--- Select Y-axis ---" or y_axis not in numeric_cols):
                            st.warning("⚠️ For most charts (Bar, Line, Scatter, Pie, Box, Treemap), a valid **numeric Y-axis** is required.")
                        elif chart_type == "Histogram" and (y_axis == "--- Select Y-axis ---" or y_axis not in numeric_cols):
                            st.warning("⚠️ A Histogram requires a valid **numeric Y-axis**.")
                        elif chart_type in ["Bar Chart", "Line Chart", "Pie Chart", "Box Plot", "Treemap"] and x_axis == "--- Select X-axis ---":
                            st.warning(f"⚠️ A {chart_type} typically requires a valid **X-axis** (categorical or date) in addition to a numeric Y-axis.")
                        elif chart_type == "Scatter Plot" and (x_axis == "--- Select X-axis ---" or y_axis == "--- Select Y-axis ---" or x_axis not in numeric_cols or y_axis not in numeric_cols):
                            st.warning("⚠️ A Scatter Plot typically requires **two numeric axes** (X and Y).")
                        else:
                            fig = None
                            try:
                                plotly_common_args = {"title": f"{y_axis} by {x_axis}" if x_axis != "--- Select X-axis ---" else f"Distribution of {y_axis}"}

                                if viz_lib == "Plotly":
                                    if chart_type == "Bar Chart":
                                        fig = px.bar(df, x=x_axis, y=y_axis, **plotly_common_args, text_auto=True)
                                    elif chart_type == "Line Chart":
                                        # Sort by X for line plots, especially if X is numeric but represents categories
                                        plot_df = df.sort_values(by=x_axis)
                                        fig = px.line(plot_df, x=x_axis, y=y_axis, **plotly_common_args, markers=True)
                                    elif chart_type == "Pie Chart":
                                        if x_is_categorical and y_is_numeric:
                                            fig = px.pie(df, names=x_axis, values=y_axis, title=f"{y_axis} Distribution by {x_axis}")
                                        else: st.error("Pie chart needs categorical X-axis and numeric Y-axis.")
                                    elif chart_type == "Scatter Plot":
                                        if x_is_numeric and y_is_numeric:
                                            fig = px.scatter(df, x=x_axis, y=y_axis, **plotly_common_args, hover_data=df.columns)
                                        else: st.error("Scatter plot needs two numeric axes (X and Y).")
                                    elif chart_type == "Treemap":
                                        if x_is_categorical and y_is_numeric:
                                            fig = px.treemap(df, path=[x_axis], values=y_axis, title=f"{y_axis} by {x_axis} Treemap")
                                        else: st.error("Treemap needs categorical X-axis (path) and numeric Y-axis (values).")
                                    elif chart_type == "Box Plot":
                                        fig = px.box(df, x=x_axis if x_axis != "--- Select X-axis ---" else None, y=y_axis,
                                                     title=f"{y_axis} Distribution {'by ' + x_axis if x_axis != '--- Select X-axis ---' else ''}")
                                    elif chart_type == "Histogram":
                                        fig = px.histogram(df, x=y_axis, title=f"Distribution of {y_axis}", marginal="box", nbins=20)

                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.error("❌ Plotly chart could not be generated with the selected options. Please ensure axis types match chart requirements.")

                                elif viz_lib == "Matplotlib":
                                    fig, ax = plt.subplots(figsize=(10, 6))
                                    if chart_type == "Bar Chart":
                                        if x_is_categorical and y_is_numeric:
                                            df_plot = df.groupby(x_axis)[y_axis].sum().sort_values(ascending=False) # Sort for better bar charts
                                            df_plot.plot(kind="bar", ax=ax, color='skyblue')
                                            ax.set_title(f"{y_axis} by {x_axis}")
                                            ax.set_ylabel(y_axis)
                                            ax.set_xlabel(x_axis)
                                            plt.xticks(rotation=45, ha='right')
                                        else: st.error("Matplotlib Bar Chart needs categorical X and numeric Y.")
                                    elif chart_type == "Line Chart":
                                        if (x_is_categorical or x_is_datetime or x_is_numeric) and y_is_numeric:
                                            plot_df = df.sort_values(by=x_axis) # Sort for sensible line plot
                                            plot_df.plot(kind="line", x=x_axis, y=y_axis, ax=ax, marker='o')
                                            ax.set_title(f"{y_axis} over {x_axis}")
                                            ax.set_ylabel(y_axis)
                                            ax.set_xlabel(x_axis)
                                            plt.xticks(rotation=45, ha='right')
                                        else: st.error("Matplotlib Line Chart needs numeric Y and (categorical, datetime, or numeric) X.")
                                    elif chart_type == "Box Plot":
                                        if y_is_numeric:
                                            if x_is_categorical:
                                                df.boxplot(column=y_axis, by=x_axis, ax=ax)
                                                ax.set_title(f"{y_axis} Distribution by {x_axis}")
                                                plt.suptitle('')
                                                ax.set_ylabel(y_axis)
                                                ax.set_xlabel(x_axis)
                                            else:
                                                df[y_axis].plot(kind="box", ax=ax)
                                                ax.set_title(f"Box Plot of {y_axis}")
                                                ax.set_ylabel(y_axis)
                                        else: st.error("Matplotlib Box Plot needs a numeric Y-axis.")
                                    elif chart_type == "Scatter Plot":
                                        if x_is_numeric and y_is_numeric:
                                            ax.scatter(df[x_axis], df[y_axis], alpha=0.7)
                                            ax.set_xlabel(x_axis)
                                            ax.set_ylabel(y_axis)
                                            ax.set_title(f"{y_axis} vs {x_axis}")
                                        else: st.error("Matplotlib Scatter Plot needs two numeric axes (X and Y).")
                                    elif chart_type == "Histogram":
                                        if y_is_numeric:
                                            ax.hist(df[y_axis], bins=20, edgecolor='black', alpha=0.7)
                                            ax.set_xlabel(y_axis)
                                            ax.set_ylabel("Frequency")
                                            ax.set_title(f"Distribution of {y_axis}")
                                        else: st.error("Matplotlib Histogram needs a numeric Y-axis.")
                                    elif chart_type == "Treemap" or chart_type == "Pie Chart":
                                        st.error("⚠️ Matplotlib does not have built-in Treemap or Pie chart functions that align well with Streamlit's dynamic axis selection. Please use **Plotly** for these chart types.")
                                    else:
                                        st.warning("⚠️ Matplotlib can't create this chart type with the selected axes or it's not implemented yet. Try Plotly.")

                                    if fig:
                                        st.pyplot(fig)
                                    plt.close(fig)

                            except Exception as e:
                                st.error(f"❌ Visualization failed: {e}. Please ensure selected columns are appropriate for the chart type and library.")
                                st.exception(e)

            with tab2:
                st.markdown("#### Raw Data Table")
                st.dataframe(df, use_container_width=True)
                st.markdown("---")
                st.markdown("##### Data Types after Conversion:")
                st.dataframe(pd.DataFrame(df.dtypes, columns=['Dtype']), use_container_width=True)

            with tab3:
                st.markdown("#### Understanding the Result")
                st.markdown("""
                This section helps you interpret the bot's response and the data presented.

                -   **Bot's Answer:** The AI's natural language interpretation of your question and the key takeaway from the query result.
                -   **SQL Query Used:** The exact SQL query generated by the AI and executed against the database. This is useful for auditing and understanding how the AI interpreted your request.
                -   **Data Table:** The raw tabular data returned by the SQL query. This is the source for all visualizations.
                -   **Visual Creator:** An interactive tool to help you visualize trends, distributions, and relationships within your data. Experiment with different chart types and axes to gain insights.
                """)
                st.info("💡 **Tip:** If your query returns a date-like column, ensure it's in a standard format (e.g., YYYY-MM-DD) for better time-series visualizations. The bot attempts to convert column types automatically for better plotting.")

        else:
            st.info("ℹ️ The query returned an empty dataset. No data to show in the table or visualize.")
    elif isinstance(result, str):
        st.info("ℹ️ The bot returned a textual answer. No structured data to visualize directly in the 'Visual' or 'Table' tabs.")
    else:
        st.info("ℹ️ No structured data received for visualization. The bot might have provided a single value or a specific message.")