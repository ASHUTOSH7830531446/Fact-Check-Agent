import streamlit as st
import os
from dotenv import load_dotenv
from utils import extract_text_from_pdf, extract_claims, google_search, verify_claim
import tempfile
import time

load_dotenv()

st.set_page_config(page_title="Fact-Check Agent", page_icon="🔍", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-verified {
        color: #28a745;
        font-weight: bold;
    }
    .status-inaccurate {
        color: #ffc107;
        font-weight: bold;
    }
    .status-false {
        color: #dc3545;
        font-weight: bold;
    }
    .source-link {
        font-size: 0.9em;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Fact-Check Agent: Automated Truth Layer")
st.markdown("""
Upload a PDF document to automatically verify its claims (stats, dates, financial figures) against the live web.
""")

# Sidebar for Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password", help="Get your key at aistudio.google.com")
    google_search_api_key = st.text_input("Google Search API Key", value=os.getenv("GOOGLE_SEARCH_API_KEY", ""), type="password")
    google_search_engine_id = st.text_input("Google Search Engine ID", value=os.getenv("GOOGLE_SEARCH_ENGINE_ID", ""), type="password")
    
    if not (gemini_api_key and google_search_api_key and google_search_engine_id):
        st.warning("⚠️ Please provide all API keys to start.")

uploaded_file = st.file_uploader("📂 Upload a PDF document", type="pdf")

if uploaded_file and gemini_api_key and google_search_api_key and google_search_engine_id:
    if st.button("🚀 Start Fact-Checking", use_container_width=True):
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            with st.status("🔍 Processing Document...", expanded=True) as status:
                st.write("📄 Extracting text from PDF...")
                text = extract_text_from_pdf(tmp_path)
                
                st.write("🕵️ Identifying verifiable claims...")
                claims = extract_claims(text, gemini_api_key)
                st.write(f"✅ Found {len(claims)} claims.")
                
                results = []
                for i, claim in enumerate(claims):
                    st.write(f"⏳ Verifying claim {i+1}/{len(claims)}: *{claim.text}*")

                    max_retries = 3
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            # Search
                            search_results = google_search(f"{claim.text} {claim.context}", google_search_api_key, google_search_engine_id)
                            # Verify
                            verification = verify_claim(claim, search_results, gemini_api_key)
                            results.append(verification)
                            # Success, break the retry loop
                            break
                        except Exception as e:
                            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                                retry_count += 1
                                if retry_count < max_retries:
                                    wait_time = 60  # Wait 60 seconds for quota reset
                                    st.warning(f"⚠️ API Quota reached. Waiting {wait_time}s before retry {retry_count}/{max_retries}...")
                                    time.sleep(wait_time)
                                else:
                                    st.error("❌ Quota exhausted after multiple retries. Please check your Gemini API plan.")
                                    raise e
                            else:
                                raise e

                    # Respect free tier rate limits (15 RPM for Gemini 2.0 Flash Free)
                    time.sleep(5) 

                
                status.update(label="✨ Fact-checking complete!", state="complete", expanded=False)

            # --- Display Results ---
            st.divider()
            
            # Summary Metrics Dashboard
            st.header("📊 Verification Summary")
            v_count = sum(1 for r in results if r.status == "Verified")
            i_count = sum(1 for r in results if r.status == "Inaccurate")
            f_count = sum(1 for r in results if r.status == "False")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Verified ✅", v_count)
            m2.metric("Inaccurate ⚠️", i_count)
            m3.metric("False ❌", f_count)
            
            st.divider()
            st.header("📑 Detailed Verification Report")
            
            for res in results:
                icon = "✅" if res.status == "Verified" else "⚠️" if res.status == "Inaccurate" else "❌"
                status_class = "status-verified" if res.status == "Verified" else "status-inaccurate" if res.status == "Inaccurate" else "status-false"
                
                with st.expander(f"{icon} {res.status}: {res.claim}", expanded=(res.status != "Verified")):
                    st.markdown(f"**Claim:** {res.claim}")
                    st.markdown(f"**Status:** <span class='{status_class}'>{res.status}</span>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**💡 Explanation:** {res.explanation}")
                        if res.real_fact:
                            st.info(f"**🎯 Correct Fact:** {res.real_fact}")
                    with col2:
                        st.write("**🔗 Sources:**")
                        for source in res.sources:
                            st.markdown(f"<a href='{source}' class='source-link'>{source}</a>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
        finally:
            os.remove(tmp_path)
else:
    if not uploaded_file:
        st.info("ℹ️ Upload a PDF to begin.")
