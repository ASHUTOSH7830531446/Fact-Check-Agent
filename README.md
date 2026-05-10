# Fact-Check Agent: Automated Truth Layer

This web application automates claim verification by reading a PDF, identifying specific claims (stats, dates, financial figures), and cross-referencing them against live web data using Google Search and Gemini AI.

## Features
*   **Automated Extraction:** Uses Gemini 2.0 Flash to identify verifiable facts from PDF documents.
*   **Live Web Verification:** Queries the Google Custom Search API for real-time data.
*   **Structured Reporting:** Flags claims as **Verified**, **Inaccurate**, or **False** with detailed explanations and corrected facts.

## Prerequisites
To run or deploy this app, you need:
1.  **Gemini API Key:** Get it from [Google AI Studio](https://aistudio.google.com/).
2.  **Google Search API Key:** Get it from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
3.  **Google Search Engine ID (CX):** Create a search engine at [Programmable Search Engine](https://programmablesearchengine.google.com/). *Ensure "Search the entire web" is enabled.*

## Local Setup
1.  Clone this repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file based on `.env.example` and add your API keys.
4.  Run the app:
    ```bash
    streamlit run app.py
    ```

## Deployment Instructions (Streamlit Community Cloud)
1.  Push this code to a public GitHub repository.
2.  Go to [Streamlit Community Cloud](https://share.streamlit.io/) and click **"New app"**.
3.  Select your repository, branch, and main file (`app.py`).
4.  **Crucial:** Click **"Advanced settings..."** and add your API keys under the **Secrets** section:
    ```toml
    GEMINI_API_KEY = "your_key"
    GOOGLE_SEARCH_API_KEY = "your_key"
    GOOGLE_SEARCH_ENGINE_ID = "your_id"
    ```
5.  Click **"Deploy!"**.

## Evaluation Criteria
The app is designed to catch:
*   **Outdated Stats:** By checking live web data.
*   **Hallucinations/Lies:** By strictly comparing claim text against search result snippets.
*   **Missing Evidence:** Flagging claims as False if no corroborating search results are found.


<img width="1919" height="826" alt="image" src="https://github.com/user-attachments/assets/89bc9c52-f16e-4d22-a3e6-cae96afdfac2" />
