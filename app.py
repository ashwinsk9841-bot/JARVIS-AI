import os
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

# Load Environment and Gemini Setup
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Dei Tony! .env file-la GEMINI_API_KEY set pannala, check pannu!")
    st.stop()
client=genai.Client(api_key=api_key)
MODEL_NAME="gemini-flash-latest"
# UI Configurations
st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🤖 JARVIS AI")
st.caption("Self-Healing Agentic Data Analyst")
st.caption("⚡ Built by Byte Force")

# Custom Dark Neon CSS & Hiding Streamlit Watermarks
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    [data-testid="stSidebar"] {
        background-color: #1a1c23;
        border-right: 1px solid #30363d;
    }
    .stChatInput {
        border-radius: 20px;
        border: 1px solid #00d2ff !important;
    }
    h1 {
        color: #00d2ff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 0px 0px 10px rgba(0, 210, 255, 0.3);
    }
    #MainMenu {visibility: hidden;}          
    footer {visibility: hidden;}             
    header {visibility: hidden;}             
    .stDeployButton {display: none;} 
            #MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

[data-testid="stToolbar"] {
    display: none;
}

[data-testid="stDecoration"] {
    display: none;
}

[data-testid="stStatusWidget"] {
    display: none;
} 
button[kind="header"] {
    display: none !important;
}

[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}       
    </style>
""", unsafe_allow_html=True)

# Sidebar - Dataset Upload
st.sidebar.header("📂 Upload Dataset")
uploaded_file = st.sidebar.file_uploader("Upload your Datathon CSV file here:", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("Dataset successfully loaded!")
    
    # Dataset Preview Section
    with st.expander("📊 View Dataset Preview & Schema"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**First 5 Rows:**")
            st.dataframe(df.head())
        with col2:
            st.write("**Dataset Schema (Metadata):**")
            schema_df = pd.DataFrame({
                "Column Name": df.columns,
                "Data Type": df.dtypes.astype(str),
                "Missing Values": df.isnull().sum().values
            })
            st.dataframe(schema_df)

    # Autonomous Auto-EDA Generation
    if "eda_report" not in st.session_state:
        with st.spinner("🤖 Jarvis is running automatic EDA on your dataset..."):
            columns_info = f"Columns: {list(df.columns)}\nTypes:\n{df.dtypes.to_string()}"
            summary_stats = df.describe(include='all').to_string()
            
            eda_prompt = f"""
            You are an expert data scientist. Analyze this dataset metadata and write a high-level executive summary.
            
            Metadata:
            {columns_info}
            
            Summary Statistics:
            {summary_stats}
            
            Provide:
            1. A 3-sentence summary of what this dataset represents.
            2. 3 critical insights or anomalies noticed.
            3. 3 smart business questions the user can ask you.
            Keep it professional, crisp, and actionable.
            """
            try:
                response=client.models.generate_content(model=MODEL_NAME,contents=eda_prompt,)
                st.session_state.eda_report=response.text
            except Exception as e:
                st.session_state.eda_report = f"Could not generate Auto-EDA: {e}"

    # Display Auto-EDA Report
    st.info("### 🧠 Jarvis's Automatic Dataset Analysis")
    st.markdown(st.session_state.eda_report)
    st.write("---")

    # Chat System Setup (Agentic Core)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "code" in msg:
                with st.expander("🔍 View Executed Code"):
                    st.code(msg["code"], language="python")

    # User Input Input Box
    # User Input Input Box
st.write("## 🤖 Chat with JARVIS")


user_query = st.chat_input(
    "Ask Jarvis anything about your dataset... (Example: Plot a correlation heatmap)"
)

if user_query:
    st.session_state.messages.append({
        "role": "user",
        "content": user_query
    })

    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Jarvis is planning, coding, and testing execution..."):
                columns_info = f"Columns: {list(df.columns)}\nTypes:\n{df.dtypes.to_string()}"
                
                # Self-correction loop settings (3 retries)
                max_retries = 3
                code_to_run = ""
                execution_error = ""
                success = False

                for attempt in range(max_retries):
                    retry_context = ""
                    if execution_error:
                        retry_context = f"""
                        Your previous Python code failed with this error:
                        Error: {execution_error}
                        
                        Please analyze the error, fix your logic, and output the corrected Python code.
                        """

                    agent_prompt = f"""
                    You are an expert Data Scientist AI Agent.
                    The pandas DataFrame is already loaded and available in memory as the variable `df`.
                    
                    Metadata:
                    {columns_info}
                    
                    User Goal: {user_query}
                    {retry_context}
                    
                    Task: Write executable Python code using pandas, matplotlib, or seaborn to solve the user's goal.
                    - To display plots, ALWAYS use streamlit's `st.pyplot(fig)` by creating `fig, ax = plt.subplots()`.
                    - To display tables, dataframes, or texts, use `st.write()` or `st.markdown()`.
                    
                    Rules:
                    1. Output ONLY clean, executable Python code block starting with ```python and ending with ```.
                    2. Do not write text explanations or notes outside the code block.
                    3. Do not redefine or reload `df`. Assume it's pre-loaded.
                    """

                    try:
                        response = client.models.generate_content(model=MODEL_NAME, contents=agent_prompt)
                        raw_response=response.text
                        # Extract code block
                        if "```python" in raw_response:
                            code_to_run = raw_response.split("```python")[1].split("```")[0].strip()
                        else:
                            code_to_run = raw_response.strip()

                        plt.clf()

                        local_vars = {
                            "df": df, 
                            "st": st, 
                            "plt": plt, 
                            "sns": sns, 
                            "pd": pd
                        }
                        
                        exec(code_to_run, globals(), local_vars)
                        success = True
                        break 
                        
                    except Exception as e:
                        execution_error = str(e)
                        st.warning(f"⚠️ Attempt {attempt+1} failed. Agent is self-healing the error...")

                # Output formatting
                if success:
                    st.success("✅ Solution executed successfully!")
                    with st.expander("🔍 View Agent's Self-Healed Code"):
                        st.code(code_to_run, language="python")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Successfully completed the task: '{user_query}'",
                        "code": code_to_run
                    })
                else:
                    st.error(f"❌ Agent failed to solve after {max_retries} attempts. Last error: {execution_error}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"I tried to solve your request but faced persistent errors: `{execution_error}`"
                    })
else:
    st.info("👋 Welcome Tony! Upload a CSV file in the sidebar to kick off the Datathon Agent.")