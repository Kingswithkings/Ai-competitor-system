import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000/audit"

st.set_page_config(page_title="1stkings AI Business Audit", layout="wide")

st.title("🚀 1stkings AI Business Audit")
st.write("Search-based competitor discovery with grounded website analysis.")

website = st.text_input("Business Website", placeholder="https://example.com")
industry = st.text_input("Industry", placeholder="e.g. restaurant, logistics, retail")

if st.button("Run Analysis"):
    if not website or not industry:
        st.warning("Please enter both website and industry.")
    else:
        with st.spinner("Running analysis..."):
            response = requests.post(API_URL, json={
                "website": website,
                "industry": industry
            })

        if response.status_code != 200:
            st.error(response.text)
        else:
            result = response.json()

            st.subheader("Target Business")
            tb = result["target_business"]
            st.write(f"**Business Name:** {tb.get('business_name', '')}")
            st.write(f"**Website:** {tb.get('website', '')}")
            st.write(f"**Industry:** {tb.get('industry', '')}")
            st.write(f"**Summary:** {tb.get('summary', '')}")
            st.write(f"**Core Offer:** {tb.get('core_offer', '')}")

            st.subheader("Candidate Competitors Found by Search")
            candidate_df = pd.DataFrame(result.get("candidate_competitors", []))
            if not candidate_df.empty:
                st.dataframe(candidate_df, use_container_width=True)
            else:
                st.info("No candidate competitors were found.")

            st.subheader("Selected Competitor Scores")
            score_df = pd.DataFrame(result.get("competitors", []))
            if not score_df.empty:
                st.dataframe(score_df, use_container_width=True)
            else:
                st.info("No final competitors were selected.")

            st.subheader("Insights")
            for insight in result.get("insights", []):
                st.write(f"- {insight}")

            st.subheader("Recommendations")
            for rec in result.get("recommendations", []):
                st.write(f"- {rec}")