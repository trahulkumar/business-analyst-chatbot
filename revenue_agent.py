import streamlit as st
import pandas as pd
import os
import sys
import subprocess
from typing import List, Optional, Any, Dict

# Auto-activate virtual environment
def activate_venv():
    """Activates the virtual environment if it exists and is not currently active."""
    venv_dir = os.path.join(os.getcwd(), ".venv")
    if os.path.exists(venv_dir):
        # Check if we are running inside the venv
        if sys.prefix != venv_dir:
            print(f"Restarting in virtual environment: {venv_dir}")
            if sys.platform == "win32":
                python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
                streamlit_executable = os.path.join(venv_dir, "Scripts", "streamlit.exe")
            else:
                python_executable = os.path.join(venv_dir, "bin", "python")
                streamlit_executable = os.path.join(venv_dir, "bin", "streamlit")
            
            # Always restart with streamlit run from the venv
            if os.path.exists(streamlit_executable):
                # Use subprocess to run streamlit
                # We use the absolute path to the current script
                script_path = os.path.abspath(__file__)
                subprocess.run([streamlit_executable, "run", script_path] + sys.argv[1:])
                sys.exit()
            
            # Fallback to python if streamlit is not found (unlikely)
            elif os.path.exists(python_executable):
                 os.execv(python_executable, [python_executable] + sys.argv)

activate_venv()

import duckdb
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools
import openai
import google.generativeai as genai

# Page Configuration
st.set_page_config(
    page_title="Revenue Operations Co-Pilot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reduce whitespace
st.markdown("""
    <style>
           .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 5rem;
                padding-right: 5rem;
            }
    </style>
    """, unsafe_allow_html=True)

# Title and Subtitle
st.title("📈 Revenue Operations Co-Pilot")
st.markdown("Your AI partner for revenue tracking, backlog analysis, and business unit performance.")

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "backlog_df" not in st.session_state:
    st.session_state.backlog_df = None
if "revenue_df" not in st.session_state:
    st.session_state.revenue_df = None
if "target_df" not in st.session_state:
    st.session_state.target_df = None

# Helper functions for model fetching
def get_openai_models(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        # Filter for gpt models to keep the list relevant
        return [m.id for m in models.data if "gpt" in m.id]
    except Exception as e:
        st.error(f"Error fetching OpenAI models: {e}")
        return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"] # Fallback

def get_gemini_models(api_key):
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        return [m.name.replace("models/", "") for m in models if "generateContent" in m.supported_generation_methods]
    except Exception as e:
        st.error(f"Error fetching Gemini models: {e}")
        return ["gemini-1.5-flash", "gemini-1.5-pro"] # Fallback

# ... (UI code) ...

# Sidebar Configuration
with st.sidebar:
    st.header("How to Use")
    st.markdown("""
    1. **Configure API**: Enter your API key and select a model.
    2. **Upload Data**: Upload your daily CSV/XLSX exports in the main area.
    3. **Ask Questions**: Use the chat interface to query revenue, backlog, and anomalies.
    4. **Get Insights**: Switch to the Insights tab for automated analysis.
    """)

# Helper function to load data
@st.cache_data(ttl="2h")
def load_data(file) -> pd.DataFrame:
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error loading {file.name}: {e}")
        return None

# Main Area - Configuration
with st.expander("⚙️ Configuration", expanded=not "api_key" in st.session_state):
    # Provider Selection
    provider = st.selectbox(
        "Select Provider",
        ["OpenAI", "Google Gemini"],
        key="provider_selector"
    )
    
    # API Key Input
    if provider == "OpenAI":
        api_key_label = "Enter OpenAI API Key"
    else:
        api_key_label = "Enter Google Gemini API Key"
        
    api_key = st.text_input(api_key_label, type="password", key="api_key_input")
    
    selected_model = None
    if api_key:
        st.session_state.api_key = api_key
        st.session_state.provider = provider
        
        # Model Selection
        if provider == "OpenAI":
            models = get_openai_models(api_key)
            default_index = models.index("gpt-4o") if "gpt-4o" in models else 0
        else:
            models = get_gemini_models(api_key)
            default_index = 0
            
        selected_model = st.selectbox("Select Model", models, index=default_index, key="model_selector")
        st.session_state.selected_model = selected_model
        
        st.success(f"Connected to {provider}")

# Main Area - File Uploads
with st.expander("📂 Data Uploads", expanded=not st.session_state.data_loaded):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        backlog_file = st.file_uploader("Upload Backlog Data", type=["csv", "xlsx"], key="backlog_uploader")
    with col2:
        revenue_file = st.file_uploader("Upload Revenue Data", type=["csv", "xlsx"], key="revenue_uploader")
    with col3:
        target_file = st.file_uploader("Upload Target Data", type=["csv", "xlsx"], key="target_uploader")
        
    if backlog_file and revenue_file and target_file:
        if st.button("Process Data", type="primary"):
            with st.spinner("Processing data..."):
                st.session_state.backlog_df = load_data(backlog_file)
                st.session_state.revenue_df = load_data(revenue_file)
                st.session_state.target_df = load_data(target_file)
                
                if st.session_state.backlog_df is not None and \
                   st.session_state.revenue_df is not None and \
                   st.session_state.target_df is not None:
                    st.session_state.data_loaded = True
                    st.success("Data loaded successfully!")
                    st.rerun()

# Agent Initialization
def get_agent(model_id, provider, api_key, dfs):
    if provider == "OpenAI":
        model = OpenAIChat(id=model_id, api_key=api_key)
    else:
        model = Gemini(id=model_id, api_key=api_key)
    
    # Initialize DuckDB and register dataframes
    con = duckdb.connect(database=':memory:')
    for name, df in dfs.items():
        con.register(name, df)
    
    duckdb_tools = DuckDbTools(connection=con)
    
    return Agent(
        model=model,
        tools=[duckdb_tools],
        markdown=True,
        instructions=[
            "You are a Revenue Operations expert.", 
            "You have access to the following SQL tables: 'backlog', 'revenue', 'targets'.",
            "Use the `duckdb_tools` to query this data.",
            "To calculate metrics, use `run_query`.",
            "Always verify your data sources.",
            "When asked for insights, provide actionable bullet points.",
            "If you cannot calculate a metric, explain why."
        ]
    )

# Main Content Area - Tabs
tab_chat, tab_insights, tab_data = st.tabs(["💬 Chat", "💡 Insights", "📊 Data Preview"])

# 1. Chat Interface
with tab_chat:
    st.subheader("Chat with Co-Pilot")
    
    # Chat Input at the Top
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input("Ask a question:", placeholder="Ask about revenue, backlog, or anomalies...", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button("Send", type="primary")
            
    if submit_button and user_input:
        if not st.session_state.data_loaded:
            st.error("Please upload all required data files first.")
        elif "api_key" not in st.session_state:
            st.error("Please configure your API key in the sidebar.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    # Prepare DFs
                    dfs = {
                        "backlog": st.session_state.backlog_df,
                        "revenue": st.session_state.revenue_df,
                        "targets": st.session_state.target_df
                    }
                    
                    # Initialize Agent
                    agent = get_agent(
                        st.session_state.selected_model,
                        st.session_state.provider,
                        st.session_state.api_key,
                        dfs
                    )
                    
                    # Run Agent
                    start_time = pd.Timestamp.now()
                    response_obj = agent.run(user_input)
                    end_time = pd.Timestamp.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    response_text = response_obj.content
                    
                    # Add to history
                    st.session_state.history.append({
                        "query": user_input,
                        "response": response_text,
                        "duration": duration
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.history.append({
                        "query": user_input,
                        "response": f"Error: {str(e)}"
                    })

    # Display History (Newest First)
    st.markdown("---")
    for item in reversed(st.session_state.history):
        with st.chat_message("user"):
            st.markdown(item["query"])
        with st.chat_message("assistant"):
            st.markdown(item["response"])
            if "duration" in item:
                st.caption(f"⏱️ {item['duration']:.2f}s")

# 2. Insights Tab
with tab_insights:
    st.subheader("Automated Insights")
    
    if not st.session_state.data_loaded:
        st.info("Upload data to generate insights.")
    else:
        if st.button("Generate", type="primary"):
            with st.spinner("Generating insights..."):
                try:
                    dfs = {
                        "backlog": st.session_state.backlog_df,
                        "revenue": st.session_state.revenue_df,
                        "targets": st.session_state.target_df
                    }
                    agent = get_agent(
                        st.session_state.selected_model,
                        st.session_state.provider,
                        st.session_state.api_key,
                        dfs
                    )
                    
                    prompt = """
                    Analyze the provided data (Revenue, Backlog, Targets) and provide a comprehensive executive summary.
                    Include:
                    1. Total Revenue vs Target (and % achievement)
                    2. Top 3 performing business units
                    3. Backlog summary (Total value and aging risks)
                    4. Any significant anomalies or risks
                    Format as a clean markdown report.
                    """
                    
                    start_time = pd.Timestamp.now()
                    response = agent.run(prompt)
                    end_time = pd.Timestamp.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    st.markdown(response.content)
                    st.caption(f"⏱️ Generated in {duration:.2f}s")
                    
                except Exception as e:
                    st.error(f"Error generating insights: {e}")

# 3. Data Preview Tab
with tab_data:
    if st.session_state.data_loaded:
        t1, t2, t3 = st.tabs(["Backlog", "Revenue", "Targets"])
        with t1:
            st.dataframe(st.session_state.backlog_df.head())
        with t2:
            st.dataframe(st.session_state.revenue_df.head())
        with t3:
            st.dataframe(st.session_state.target_df.head())
    else:
        st.info("No data loaded.")
