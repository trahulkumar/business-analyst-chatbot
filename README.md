# 📈 Revenue Operations Co-Pilot

Your AI partner for revenue tracking, backlog analysis, and business unit performance. This application leverages **Agno** agents and **DuckDB** to provide accurate, SQL-driven insights from your Excel/CSV data.

## Features

-   **Dynamic AI Model Selection**: Support for **OpenAI** (GPT-4o, etc.) and **Google Gemini** (Flash, Pro). Automatically discovers available models based on your API key.
-   **Secure Data Analysis**: Uses **DuckDB** to query your data locally. Data is processed in-memory and not sent to external training sets.
-   **Interactive Chat**: Ask natural language questions about your Revenue, Backlog, and Targets. The agent converts them into precise SQL queries.
-   **Automated Insights**: One-click generation of executive summaries, identifying top performers, backlog risks, and anomalies.
-   **Visual Data Preview**: Inspect your uploaded dataframes directly within the app.

## Prerequisites

-   Python 3.10+
-   An API Key for **OpenAI** or **Google Gemini**.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/trahulkumar/business-analyst-chatbot.git
    cd business-analyst-chatbot
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application**:
    ```bash
    streamlit run revenue_agent.py
    ```

2.  **Configure the Agent**:
    -   Open the **Configuration** expander.
    -   Select your provider (OpenAI or Google Gemini).
    -   Enter your API Key.
    -   Select your preferred model (e.g., `gemini-1.5-flash` or `gpt-4o`).

3.  **Upload Data**:
    -   Open the **Data Uploads** expander.
    -   Upload your `Backlog`, `Revenue`, and `Targets` files (CSV or Excel).
    -   Click **Process Data**.

4.  **Get Insights**:
    -   **Chat**: Type questions like "What is the total revenue for the Software business unit?" or "Show me backlog items delayed by more than 30 days."
    -   **Insights Tab**: Click **Generate** to get a comprehensive executive summary.

## Project Structure

-   `revenue_agent.py`: Main application logic.
-   `test_insights.py`: Standalone script for testing agent logic and model connectivity.
-   `.venv/`: Virtual environment (not committed).

## Troubleshooting

-   **API Errors**: Ensure your API key has access to the selected model. The app attempts to auto-discover available models.
-   **Data Loading**: Ensure your Excel/CSV files have clean headers.
-   **Session State**: If the app behaves unexpectedly, try refreshing the page to reset the session state.
