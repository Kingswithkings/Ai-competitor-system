import requests
import pandas as pd
import streamlit as st


API_BASE = "http://127.0.0.1:8000"


def run_audit_request(website: str, industry: str):
    response = requests.post(
        f"{API_BASE}/audit",
        json={"website": website, "industry": industry},
        timeout=180,
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


st.set_page_config(page_title="1stkings AI Business Audit", layout="wide")

st.title("🚀 1stkings AI Business Audit")
st.caption("Search-based competitor discovery with grounded website analysis.")

tab1, tab2 = st.tabs(["Run Audit", "Audit History"])

with tab1:
    st.subheader("Run New Audit")

    website = st.text_input(
        "Business Website",
        placeholder="https://example.com",
    )

    industry = st.text_input(
        "Industry",
        placeholder="e.g. logistics, restaurant, retail",
    )

    run_button = st.button("Run Analysis", type="primary")

    if run_button:
        if not website.strip() or not industry.strip():
            st.warning("Please enter both website and industry.")
        else:
            try:
                with st.spinner("Running audit..."):
                    payload = run_audit_request(website.strip(), industry.strip())

                audit_id = payload.get("audit_id")
                result = payload.get("result", {})
                target = result.get("target_business", {})
                market_summary = result.get("market_summary", {})
                candidate_competitors = result.get("candidate_competitors", [])
                competitors = result.get("competitors", [])
                insights = result.get("insights", [])
                recommendations = result.get("recommendations", [])

                st.success(f"Audit completed successfully. Audit ID: {audit_id}")

                st.subheader("Target Business")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Business Name:** {target.get('business_name', 'N/A')}")
                    st.write(f"**Website:** {target.get('website', 'N/A')}")
                    st.write(f"**Industry:** {target.get('industry', 'N/A')}")
                with col2:
                    st.write(f"**Summary:** {target.get('summary', 'N/A')}")
                    st.write(f"**Core Offer:** {target.get('core_offer', 'N/A')}")

                st.subheader("Market Summary")
                m1, m2, m3 = st.columns(3)
                m1.metric("Average Score", market_summary.get("average_score", 0))
                m2.metric("Top Score", market_summary.get("top_score", 0))
                m3.metric("Average Grade", market_summary.get("average_grade", "N/A"))

                st.subheader("Candidate Competitors Found by Search")
                if candidate_competitors:
                    candidate_df = pd.DataFrame(candidate_competitors)
                    st.dataframe(candidate_df, use_container_width=True)
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
                    existing_columns = [col for col in preferred_order if col in score_df.columns]
                    score_df = score_df[existing_columns]
                    st.dataframe(score_df, use_container_width=True)
                else:
                    st.info("No final competitors were selected.")

                st.subheader("Insights")
                if insights:
                    for insight in insights:
                        st.write(f"- {insight}")
                else:
                    st.write("No insights available.")

                st.subheader("Recommendations")
                if recommendations:
                    for rec in recommendations:
                        st.write(f"- {rec}")
                else:
                    st.write("No recommendations available.")

                if audit_id:
                    pdf_url = f"{API_BASE}/audits/{audit_id}/pdf"
                    st.markdown(f"[Download PDF Report]({pdf_url})")

            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend API. Make sure FastAPI is running on http://127.0.0.1:8000.")
            except requests.exceptions.HTTPError as e:
                try:
                    detail = e.response.json()
                    st.error(f"API error: {detail}")
                except Exception:
                    st.error(f"API error: {e.response.text}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

with tab2:
    st.subheader("Saved Audit History")

    refresh = st.button("Refresh History")

    try:
        audits = load_audit_history()

        if not audits:
            st.info("No saved audits yet.")
        else:
            history_df = pd.DataFrame(audits)
            st.dataframe(history_df, use_container_width=True)

            audit_ids = history_df["id"].tolist()
            selected_audit_id = st.selectbox("Select an Audit ID to inspect", audit_ids)

            if selected_audit_id:
                detail = load_audit_detail(int(selected_audit_id))
                result = detail.get("result_json", {})
                target = result.get("target_business", {})
                market_summary = result.get("market_summary", {})
                competitors = result.get("competitors", [])
                insights = result.get("insights", [])
                recommendations = result.get("recommendations", [])

                st.markdown("---")
                st.subheader(f"Audit Detail: {selected_audit_id}")

                st.write(f"**Business Name:** {target.get('business_name', detail.get('business_name', 'N/A'))}")
                st.write(f"**Website:** {target.get('website', detail.get('website', 'N/A'))}")
                st.write(f"**Industry:** {target.get('industry', detail.get('industry', 'N/A'))}")
                st.write(f"**Created At:** {detail.get('created_at', 'N/A')}")

                st.subheader("Market Summary")
                d1, d2, d3 = st.columns(3)
                d1.metric("Average Score", market_summary.get("average_score", 0))
                d2.metric("Top Score", market_summary.get("top_score", 0))
                d3.metric("Average Grade", market_summary.get("average_grade", "N/A"))

                st.subheader("Competitor Scores")
                if competitors:
                    detail_df = pd.DataFrame(competitors)
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
                    existing_columns = [col for col in preferred_order if col in detail_df.columns]
                    detail_df = detail_df[existing_columns]
                    st.dataframe(detail_df, use_container_width=True)
                else:
                    st.info("No competitor data saved for this audit.")

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

                pdf_url = f"{API_BASE}/audits/{selected_audit_id}/pdf"
                st.markdown(f"[Download PDF Report for Audit {selected_audit_id}]({pdf_url})")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend API. Start FastAPI first.")
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json()
            st.error(f"API error: {detail}")
        except Exception:
            st.error(f"API error: {e.response.text}")
    except Exception as e:
        st.error(f"Unexpected error while loading history: {str(e)}")