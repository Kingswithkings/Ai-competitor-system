import os

import requests
import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def get_api_base() -> str:
    try:
        configured_url = st.secrets.get("API_BASE_URL", None)
    except StreamlitSecretNotFoundError:
        configured_url = None

    configured_url = configured_url or os.getenv("API_BASE_URL")
    return (configured_url or "http://127.0.0.1:8000").rstrip("/")


API_BASE = get_api_base()


def run_audit_request(payload: dict):
    response = requests.post(
        f"{API_BASE}/audit",
        json=payload,
        timeout=240,
    )
    response.raise_for_status()
    return response.json()


def load_audit_history():
    response = requests.get(f"{API_BASE}/audits", timeout=30)
    response.raise_for_status()
    return response.json()


def load_audit_detail(audit_id: int):
    response = requests.get(f"{API_BASE}/audits/{audit_id}", timeout=30)
    response.raise_for_status()
    return response.json()


def show_ai_tool_recommendations(ai_tools: list):
    st.subheader("Recommended AI Tools")

    if not ai_tools:
        st.write("No AI tool recommendations available.")
        return

    tool_df = pd.DataFrame(ai_tools)
    preferred_order = [
        "business_need",
        "tool_category",
        "suggested_tools",
        "priority",
        "implementation_type",
        "reason",
    ]
    existing_columns = [c for c in preferred_order if c in tool_df.columns]
    tool_df = tool_df[existing_columns].copy()

    if "suggested_tools" in tool_df.columns:
        tool_df["suggested_tools"] = tool_df["suggested_tools"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else str(x)
        )

    st.dataframe(tool_df, use_container_width=True)


st.set_page_config(page_title="1stkings AI Business Audit", layout="wide")

st.title("🚀 1stkings AI Business Audit")
st.caption("Competitor analysis, scoring, AI recommendations, and client-ready reports.")

tab1, tab2 = st.tabs(["Run Audit", "Audit History"])

with tab1:
    st.subheader("Run New Audit")

    business_name = st.text_input("Business Name (optional)", placeholder="Example Ltd")
    website = st.text_input("Business Website", placeholder="https://example.com")
    industry = st.text_input("Industry", placeholder="e.g. logistics, restaurant, retail")
    location = st.text_input("Location (optional)", placeholder="e.g. London, UK")

    if st.button("Run Analysis", type="primary"):
        if not website.strip() or not industry.strip():
            st.warning("Please enter at least website and industry.")
        else:
            try:
                with st.spinner("Running audit..."):
                    payload = run_audit_request({
                        "business_name": business_name.strip() or None,
                        "website": website.strip(),
                        "industry": industry.strip(),
                        "location": location.strip() or None,
                    })

                audit_id = payload.get("audit_id")
                result = payload.get("result", {})

                target = result.get("target_business", {})
                market_summary = result.get("market_summary", {})
                candidate_competitors = result.get("candidate_competitors", [])
                competitors = result.get("competitors", [])
                insights = result.get("insights", [])
                recommendations = result.get("recommendations", [])
                ai_tool_recommendations = result.get("ai_tool_recommendations", [])
                target_metrics = result.get("target_metrics", {})
                collected_pages = result.get("collected_pages", [])

                st.success(f"Audit completed successfully. Audit ID: {audit_id}")

                st.subheader("Target Business")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Business Name:** {target.get('business_name', 'N/A')}")
                    st.write(f"**Website:** {target.get('website', 'N/A')}")
                    st.write(f"**Industry:** {target.get('industry', 'N/A')}")
                    st.write(f"**Location:** {target.get('location', 'N/A')}")
                with c2:
                    st.write(f"**Summary:** {target.get('summary', 'N/A')}")
                    st.write(f"**Core Offer:** {target.get('core_offer', 'N/A')}")

                st.subheader("Market Summary")
                m1, m2, m3 = st.columns(3)
                m1.metric("Average Score", market_summary.get("average_score", 0))
                m2.metric("Top Score", market_summary.get("top_score", 0))
                m3.metric("Average Grade", market_summary.get("average_grade", "N/A"))

                st.subheader("Target Metrics")
                st.json(target_metrics)

                st.subheader("Collected Pages")
                if collected_pages:
                    pages_df = pd.DataFrame(collected_pages)
                    st.dataframe(pages_df, use_container_width=True)
                else:
                    st.info("No pages collected.")

                st.subheader("Candidate Competitors Found by Search")
                if candidate_competitors:
                    st.dataframe(pd.DataFrame(candidate_competitors), use_container_width=True)
                else:
                    st.info("No candidate competitors were found.")

                st.subheader("Selected Competitor Scores")
                if competitors:
                    score_df = pd.DataFrame(competitors)
                    preferred_order = [
                        "name",
                        "website",
                        "presence",
                        "engagement",
                        "automation",
                        "weighted_score",
                        "grade",
                        "strength",
                    ]
                    existing = [c for c in preferred_order if c in score_df.columns]
                    st.dataframe(score_df[existing], use_container_width=True)
                else:
                    st.info("No final competitors were selected.")

                st.subheader("Insights")
                if insights:
                    for item in insights:
                        st.write(f"- {item}")
                else:
                    st.write("No insights available.")

                st.subheader("Recommendations")
                if recommendations:
                    for item in recommendations:
                        st.write(f"- {item}")
                else:
                    st.write("No recommendations available.")

                show_ai_tool_recommendations(ai_tool_recommendations)

                if audit_id:
                    st.markdown(f"[Download PDF Report]({API_BASE}/audits/{audit_id}/pdf)")

            except requests.exceptions.ConnectionError:
                st.error(
                    f"Could not connect to the backend API at {API_BASE}. "
                    "If this app is deployed, set API_BASE_URL to your public FastAPI URL."
                )
            except requests.exceptions.HTTPError as e:
                try:
                    st.error(f"API error: {e.response.json()}")
                except Exception:
                    st.error(f"API error: {e.response.text}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

with tab2:
    st.subheader("Saved Audit History")

    try:
        audits = load_audit_history()
        if not audits:
            st.info("No saved audits yet.")
        else:
            history_df = pd.DataFrame(audits)
            st.dataframe(history_df, use_container_width=True)

            audit_ids = history_df["id"].tolist()
            selected_audit_id = st.selectbox("Select an Audit ID", audit_ids)

            if selected_audit_id:
                detail = load_audit_detail(int(selected_audit_id))
                result = detail.get("result_json", {})

                target = result.get("target_business", {})
                market_summary = result.get("market_summary", {})
                competitors = result.get("competitors", [])
                insights = result.get("insights", [])
                recommendations = result.get("recommendations", [])
                ai_tool_recommendations = result.get("ai_tool_recommendations", [])

                st.markdown("---")
                st.subheader(f"Audit Detail: {selected_audit_id}")
                st.write(f"**Business Name:** {target.get('business_name', detail.get('business_name', 'N/A'))}")
                st.write(f"**Website:** {target.get('website', detail.get('website', 'N/A'))}")
                st.write(f"**Industry:** {target.get('industry', detail.get('industry', 'N/A'))}")
                st.write(f"**Location:** {target.get('location', detail.get('location', 'N/A'))}")
                st.write(f"**Created At:** {detail.get('created_at', 'N/A')}")

                d1, d2, d3 = st.columns(3)
                d1.metric("Average Score", market_summary.get("average_score", 0))
                d2.metric("Top Score", market_summary.get("top_score", 0))
                d3.metric("Average Grade", market_summary.get("average_grade", "N/A"))

                if competitors:
                    st.dataframe(pd.DataFrame(competitors), use_container_width=True)

                st.subheader("Insights")
                for item in insights:
                    st.write(f"- {item}")

                st.subheader("Recommendations")
                for item in recommendations:
                    st.write(f"- {item}")

                show_ai_tool_recommendations(ai_tool_recommendations)

                st.markdown(f"[Download PDF Report for Audit {selected_audit_id}]({API_BASE}/audits/{selected_audit_id}/pdf)")

    except requests.exceptions.ConnectionError:
        st.error(
            f"Could not connect to the backend API at {API_BASE}. "
            "If this app is deployed, set API_BASE_URL to your public FastAPI URL."
        )
    except Exception as e:
        st.error(f"Unexpected error while loading history: {str(e)}")
