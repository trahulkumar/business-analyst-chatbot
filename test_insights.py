import pandas as pd
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
import google.generativeai as genai
import duckdb
import os
import sys

# ... (Dummy Data setup remains same) ...
# Load Real Data
print("Loading real data from Excel files...")
try:
    revenue_path = r"C:\Users\trahu\Documents\Git\Revenue Commitment dashboard\metadata\Revenue Data.xlsx"
    backlog_path = r"C:\Users\trahu\Documents\Git\Revenue Commitment dashboard\metadata\Backlog Data.xlsx"
    target_path = r"C:\Users\trahu\Documents\Git\Revenue Commitment dashboard\metadata\Target Data.xlsx"

    revenue_df = pd.read_excel(revenue_path)
    backlog_df = pd.read_excel(backlog_path)
    target_df = pd.read_excel(target_path)
    
    print("Data loaded successfully.")
    print(f"Revenue: {revenue_df.shape}")
    print(f"Backlog: {backlog_df.shape}")
    print(f"Targets: {target_df.shape}")

except Exception as e:
    print(f"Error loading data: {e}")
    sys.exit(1)

# Initialize DuckDB
print("Initializing DuckDB...")
con = duckdb.connect(database=':memory:')
con.register('revenue', revenue_df)
con.register('backlog', backlog_df)
con.register('targets', target_df)

duckdb_tools = DuckDbTools(connection=con)

# Get API Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        print("Please set GOOGLE_API_KEY environment variable or pass it as an argument.")
        sys.exit(1)

# Discover Models
print("Discovering available models...")
genai.configure(api_key=api_key)
available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            print(f" - {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
    sys.exit(1)

# Select Model
selected_model_id = None
# Prefer flash
for m in available_models:
    if "flash" in m.lower():
        selected_model_id = m.replace("models/", "")
        break

# Fallback to pro
if not selected_model_id:
    for m in available_models:
        if "pro" in m.lower():
            selected_model_id = m.replace("models/", "")
            break

# Fallback to first available
if not selected_model_id and available_models:
    selected_model_id = available_models[0].replace("models/", "")

if not selected_model_id:
    print("No suitable models found.")
    sys.exit(1)

print(f"Selected Model: {selected_model_id}")

print("Initializing Agent...")
agent = Agent(
    model=Gemini(id=selected_model_id, api_key=api_key),
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

print("Testing Model Connectivity...")
try:
    # Simple check
    response = agent.run("Hello, are you ready?")
    print(f"Connectivity Check: {response.content}")
except Exception as e:
    print(f"Connectivity Failed: {e}")
    sys.exit(1)

prompt = """
Analyze the provided data (Revenue, Backlog, Targets) and provide a comprehensive executive summary.
Include:
1. Total Revenue vs Target (and % achievement)
2. Top 3 performing business units
3. Backlog summary (Total value and aging risks)
4. Any significant anomalies or risks
Format as a clean markdown report.
"""

print("\nRunning Insights Generation...")
try:
    response = agent.run(prompt)
    print("\n--- Response ---\n")
    print(response.content)
except Exception as e:
    print(f"\nError: {e}")
