import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# 1. ENVIRONMENT + GEMINI CONFIG
load_dotenv()

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found. Check Streamlit Secrets or .env file.")
    st.stop()

genai.configure(api_key=api_key)

MODEL_CANDIDATES = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
]


def generate_content_safe(prompt: str):
    """
    Tries each model in MODEL_CANDIDATES in order.
    Returns (response, model_used).
    Raises the last error if every model fails.
    """
    last_error = None

for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response, model_name

        except Exception as e:

            last_error = e

            # If it's specifically a 404 (model not found / not available
            # for this key), just move on and try the next model.
            if "404" in str(e) or "NOT_FOUND" in str(e):
                continue

            # For any other kind of error (bad key, network, quota, etc.)
            # no point trying other models — raise immediately.
            raise

    # If we reach here, every model in the list 404'd.
    raise last_error


# =========================================================
# 2. STREAMLIT PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 3. JARVIS EYES
# =========================================================

try:
    with open("jarvis_eyes.html", "r", encoding="utf-8") as f:
        html_code = f.read()

    components.html(
        html_code,
        height=180
    )

except Exception:
    pass


# =========================================================
# 4. MAIN TITLE
# =========================================================

st.title("🤖 JARVIS AI")
st.caption("Self-Healing Agentic Data Analyst")
st.caption("⚡ Built by Byte Force")


# =========================================================
# 5. CUSTOM CSS
# =========================================================

st.markdown(
    """
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

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .stDeployButton {
        display: none;
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
    """,
    unsafe_allow_html=True
)


# =========================================================
# 6. SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "eda_report" not in st.session_state:
    st.session_state.eda_report = None

if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = None


# =========================================================
# 7. SIDEBAR - CSV UPLOAD
# =========================================================

st.sidebar.header("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload your Datathon CSV file here:",
    type=["csv"]
)


# =========================================================
# 8. PROCESS DATASET
# =========================================================

if uploaded_file is not None:

    try:

        df = pd.read_csv(uploaded_file)

        st.session_state.dataset_name = uploaded_file.name

        st.sidebar.success("✅ Dataset successfully loaded!")

        st.sidebar.caption(
            f"📄 {uploaded_file.name}"
        )

        st.sidebar.caption(
            f"Rows: {df.shape[0]} | Columns: {df.shape[1]}"
        )

    except Exception as e:

        st.sidebar.error(
            f"❌ Could not read CSV: {e}"
        )

        st.stop()


    # =====================================================
    # 9. DATASET PREVIEW
    # =====================================================

    with st.expander("📊 View Dataset Preview & Schema"):

        col1, col2 = st.columns(2)

        with col1:

            st.write("### First 5 Rows")

            st.dataframe(
                df.head(),
                use_container_width=True
            )

        with col2:

            st.write("### Dataset Schema")

            schema_df = pd.DataFrame(
                {
                    "Column Name": df.columns,
                    "Data Type": df.dtypes.astype(str),
                    "Missing Values": df.isnull().sum().values
                }
            )

            st.dataframe(
                schema_df,
                use_container_width=True
            )


    # =====================================================
    # 10. BASIC DATASET INFORMATION
    # =====================================================

    st.write("### 📌 Dataset Overview")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Rows",
            df.shape[0]
        )

    with c2:
        st.metric(
            "Columns",
            df.shape[1]
        )

    with c3:
        st.metric(
            "Missing Values",
            int(df.isnull().sum().sum())
        )

    with c4:
        st.metric(
            "Duplicate Rows",
            int(df.duplicated().sum())
        )


    # =====================================================
    # 11. AUTOMATIC EDA
    # =====================================================

    if st.session_state.eda_report is None:

        with st.spinner(
            "🤖 JARVIS is analyzing your dataset..."
        ):

            columns_info = (
                f"Columns: {list(df.columns)}\n"
                f"Types:\n{df.dtypes.to_string()}"
            )

            try:

                summary_stats = (
                    df.describe(
                        include="all"
                    ).to_string()
                )

            except Exception:

                summary_stats = (
                    df.describe().to_string()
                )


            eda_prompt = f"""
You are JARVIS, an expert Data Scientist AI.

Analyze the following dataset metadata and statistics.

DATASET COLUMNS:
{columns_info}

SUMMARY STATISTICS:
{summary_stats}

DATASET SHAPE:
Rows = {df.shape[0]}
Columns = {df.shape[1]}

MISSING VALUES:
{df.isnull().sum().to_string()}

DUPLICATE ROWS:
{df.duplicated().sum()}

Provide:

1. A short explanation of what this dataset appears to represent.
2. The 5 most important insights.
3. Important anomalies or data-quality issues.
4. Important columns.
5. Useful business/data-science questions that can be asked.
6. Recommended visualizations.

Keep the response professional, clear and actionable.
"""


            try:

                response, used_model = generate_content_safe(eda_prompt)

                st.session_state.eda_report = (
                    response.text
                    if response.text
                    else "No analysis returned."
                )

            except Exception as e:

                st.session_state.eda_report = (
                    f"⚠️ Gemini could not generate Auto-EDA.\n\n"
                    f"Error: {e}\n\n"
                    f"You can still use the JARVIS chat below."
                )


    # =====================================================
    # 12. DISPLAY AUTO-EDA
    # =====================================================

    st.info("### 🧠 JARVIS's Automatic Dataset Analysis")

    st.markdown(
        st.session_state.eda_report
    )

    st.write("---")


    # =====================================================
    # 13. CHAT TITLE
    # =====================================================

    st.write("## 🤖 Chat with JARVIS")


    # =====================================================
    # 14. DISPLAY OLD CHAT
    # =====================================================

    for msg in st.session_state.messages:

        with st.chat_message(
            msg["role"]
        ):

            st.markdown(
                msg["content"]
            )

            if "code" in msg:

                with st.expander(
                    "🔍 View Executed Code"
                ):

                    st.code(
                        msg["code"],
                        language="python"
                    )


    # =====================================================
    # 15. USER QUERY
    # =====================================================

    user_query = st.chat_input(
        "Ask JARVIS anything about your dataset... "
        "(Example: Plot a correlation heatmap)"
    )


    # =====================================================
    # 16. HANDLE USER QUERY
    # =====================================================

    if user_query:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_query
            }
        )


        with st.chat_message("user"):

            st.markdown(
                user_query
            )


        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 JARVIS is planning, coding, and testing..."
            ):

                columns_info = (
                    f"Columns: {list(df.columns)}\n"
                    f"Types:\n{df.dtypes.to_string()}"
                )

                max_retries = 3

                code_to_run = ""

                execution_error = ""

                success = False


                # =================================================
                # SELF HEALING LOOP
                # =================================================

                for attempt in range(max_retries):

                    retry_context = ""

                    if execution_error:

                        retry_context = f"""
The previous generated Python code failed.

ERROR:
{execution_error}

Fix the Python code.

Do not repeat the same mistake.
"""


                    agent_prompt = f"""
You are JARVIS, an expert Data Scientist AI Agent.

A pandas DataFrame named `df` is already loaded.

DO NOT reload the CSV.
DO NOT redefine df.

DATASET METADATA:
{columns_info}

USER REQUEST:
{user_query}

{retry_context}

Your task is to generate Python code that solves the user's request.

AVAILABLE LIBRARIES:

pandas as pd
matplotlib.pyplot as plt
streamlit as st

RULES:

1. Output ONLY Python code.
2. Do not explain anything outside the code.
3. Do not use markdown.
4. Do not redefine df.
5. For plots use:

fig, ax = plt.subplots()

Then use:

st.pyplot(fig)

6. For tables use:

st.dataframe(...)

7. For text use:

st.write(...)

8. Make the code directly executable.
"""


                    # =============================================
                    # 17. GEMINI CODE GENERATION
                    # =============================================

                    try:

                        response, used_model = generate_content_safe(agent_prompt)

                        raw_response = (
                            response.text
                            if response.text
                            else ""
                        )


                        if "```python" in raw_response:

                            code_to_run = (
                                raw_response
                                .split("```python", 1)[1]
                                .split("```", 1)[0]
                                .strip()
                            )

                        elif "```" in raw_response:

                            code_to_run = (
                                raw_response
                                .split("```", 1)[1]
                                .split("```", 1)[0]
                                .strip()
                            )

                        else:

                            code_to_run = (
                                raw_response.strip()
                            )


                        if not code_to_run:

                            raise ValueError(
                                "Gemini returned empty Python code."
                            )


                    except Exception as api_error:

                        execution_error = str(
                            api_error
                        )

                        st.error(
                            "❌ Gemini API error"
                        )

                        st.code(
                            execution_error
                        )

                        st.info(
                            "CSV is loaded correctly. "
                            "Try again after a few seconds."
                        )

                        break


                    # =============================================
                    # 18. EXECUTE GENERATED CODE
                    # =============================================

                    try:

                        plt.close("all")

                        local_vars = {
                            "df": df,
                            "st": st,
                            "plt": plt,
                            "pd": pd
                        }

                        exec(
                            code_to_run,
                            {},
                            local_vars
                        )

                        success = True

                        break


                    except Exception as code_error:

                        execution_error = str(
                            code_error
                        )

                        if attempt < max_retries - 1:

                            st.warning(
                                f"⚠️ Attempt {attempt + 1} failed. "
                                "JARVIS is self-healing the code..."
                            )

                        else:

                            st.error(
                                "❌ Python execution failed."
                            )

                            st.code(
                                execution_error
                            )


                # =================================================
                # 19. SUCCESS
                # =================================================

                if success:

                    st.success(
                        "✅ Solution executed successfully!"
                    )

                    with st.expander(
                        "🔍 View JARVIS's Generated Code"
                    ):

                        st.code(
                            code_to_run,
                            language="python"
                        )


                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                f"✅ Successfully completed: "
                                f"**{user_query}**"
                            ),
                            "code": code_to_run
                        }
                    )


                # =================================================
                # 20. FAILURE
                # =================================================

                elif execution_error:

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                "❌ JARVIS could not complete "
                                "the request.\n\n"
                                f"Error: `{execution_error}`"
                            )
                        }
                    )


else:

    st.info(
        "👋 Welcome! Upload a CSV file in the sidebar "
        "to start JARVIS Data Analysis."
    )
