import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError


load_dotenv(ROOT_DIR / ".env")


def get_secret(name: str):
    try:
        return st.secrets.get(name, None)
    except StreamlitSecretNotFoundError:
        return None


def configure_secret_env() -> None:
    for name in ("OPENAI_API_KEY",):
        if not os.getenv(name):
            secret_value = get_secret(name)
            if secret_value:
                os.environ[name] = secret_value


def get_api_base() -> str | None:
    configured_url = get_secret("API_BASE_URL") or os.getenv("API_BASE_URL")
    return configured_url.rstrip("/") if configured_url else None


API_BASE = get_api_base()
USE_API_BACKEND = API_BASE is not None


def run_audit_request(payload: dict):
    if not USE_API_BACKEND:
        configure_secret_env()

        from app.ai_engine import analyze_business
        from app.database import init_db, save_audit
        from app.pdf_report import generate_pdf_report

        init_db()

        result = analyze_business(
            website=payload["website"],
            industry=payload["industry"],
            business_name=payload.get("business_name"),
            location=payload.get("location"),
        )

        target = result.get("target_business", {})

        audit_id = save_audit(
            business_name=target.get("business_name", ""),
            website=target.get("website", payload["website"]),
            industry=target.get("industry", payload["industry"]),
            location=target.get("location", payload.get("location") or ""),
            summary=target.get("summary", ""),
            result=result,
        )

        pdf_path = generate_pdf_report(audit_id, result)

        return {
            "audit_id": audit_id,
            "pdf_path": pdf_path,
            "result": result,
        }

    response = requests.post(
        f"{API_BASE}/audit",
        json=payload,
        timeout=240,
    )
    response.raise_for_status()
    return response.json()


def load_audit_history():
    if not USE_API_BACKEND:
        from app.database import init_db, list_audits

        init_db()
        return list_audits()

    response = requests.get(f"{API_BASE}/audits", timeout=30)
    response.raise_for_status()
    return response.json()


def load_audit_detail(audit_id: int):
    if not USE_API_BACKEND:
        from app.database import init_db, get_audit

        init_db()
        return get_audit(audit_id)

    response = requests.get(f"{API_BASE}/audits/{audit_id}", timeout=30)
    response.raise_for_status()
    return response.json()


def show_pdf_download(audit_id: int, audit_data: dict, label: str):
    if USE_API_BACKEND:
        try:
            response = requests.get(f"{API_BASE}/audits/{audit_id}/pdf", timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            st.error(f"PDF report could not be downloaded: {exc}")
            return

        if not response.content:
            st.warning("PDF report was empty.")
            return

        st.download_button(
            label=label,
            data=response.content,
            file_name=f"audit_{audit_id}.pdf",
            mime="application/pdf",
        )
        return

    try:
        from app.pdf_report import generate_pdf_report

        pdf_path = Path(generate_pdf_report(audit_id, audit_data))
    except ModuleNotFoundError:
        st.error(
            "PDF generation is unavailable because fpdf2 is not installed. "
            "Run the app from the project virtual environment or install requirements.txt."
        )
        return
    except Exception as exc:
        st.error(f"PDF report could not be generated: {exc}")
        return

    if not pdf_path.exists():
        st.warning("PDF report could not be found.")
        return

    pdf_bytes = pdf_path.read_bytes()
    if not pdf_bytes:
        st.warning("PDF report was empty.")
        return

    st.download_button(
        label=label,
        data=pdf_bytes,
        file_name=pdf_path.name,
        mime="application/pdf",
    )


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

if USE_API_BACKEND:
    st.info(f"Using backend API: {API_BASE}")
else:
    st.info("Running in direct Streamlit mode. No external FastAPI backend is configured.")

tab1, tab2 = st.tabs(["Run Audit", "Audit History"])


with tab1:
    st.subheader("Run New Audit")

    business_name = st.text_input(
        "Business Name (optional)",
        placeholder="Example Ltd",
    )

    website = st.text_input(
        "Business Website",
        placeholder="https://example.com",
    )

    industry = st.text_input(
        "Industry",
        placeholder="e.g. logistics, restaurant, retail",
    )

    location = st.text_input(
        "Location (optional)",
        placeholder="e.g. London, UK",
    )

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
                    show_pdf_download(audit_id, result, "Download PDF Report")

            except requests.exceptions.ConnectionError:
                st.error(
                    f"Could not connect to the backend API at {API_BASE}. "
                    "Check that API_BASE_URL points to a reachable FastAPI URL."
                )
            except requests.exceptions.HTTPError as e:
                try:
                    st.error(f"API error: {e.response.json()}")
                except Exception:
                    st.error(f"API error: {e.response.text}")
            except ModuleNotFoundError as e:
                st.error(
                    f"Module import error: {str(e)}. "
                    "Make sure your GitHub repo contains the app/ folder and app/__init__.py."
                )
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

            if "id" not in history_df.columns:
                st.warning("Audit history exists, but no ID column was found.")
            else:
                audit_ids = history_df["id"].tolist()
                selected_audit_id = st.selectbox("Select an Audit ID", audit_ids)

                if selected_audit_id:
                    detail = load_audit_detail(int(selected_audit_id))

                    if not detail:
                        st.warning("Selected audit could not be loaded.")
                    else:
                        result = detail.get("result_json", {})

                        target = result.get("target_business", {})
                        market_summary = result.get("market_summary", {})
                        competitors = result.get("competitors", [])
                        insights = result.get("insights", [])
                        recommendations = result.get("recommendations", [])
                        ai_tool_recommendations = result.get("ai_tool_recommendations", [])

                        st.markdown("---")
                        st.subheader(f"Audit Detail: {selected_audit_id}")

                        st.write(
                            f"**Business Name:** "
                            f"{target.get('business_name', detail.get('business_name', 'N/A'))}"
                        )
                        st.write(
                            f"**Website:** "
                            f"{target.get('website', detail.get('website', 'N/A'))}"
                        )
                        st.write(
                            f"**Industry:** "
                            f"{target.get('industry', detail.get('industry', 'N/A'))}"
                        )
                        st.write(
                            f"**Location:** "
                            f"{target.get('location', detail.get('location', 'N/A'))}"
                        )
                        st.write(f"**Created At:** {detail.get('created_at', 'N/A')}")

                        d1, d2, d3 = st.columns(3)
                        d1.metric("Average Score", market_summary.get("average_score", 0))
                        d2.metric("Top Score", market_summary.get("top_score", 0))
                        d3.metric("Average Grade", market_summary.get("average_grade", "N/A"))

                        st.subheader("Competitor Scores")

                        if competitors:
                            st.dataframe(pd.DataFrame(competitors), use_container_width=True)
                        else:
                            st.info("No competitor data available.")

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

                        show_pdf_download(
                            int(selected_audit_id),
                            result,
                            f"Download PDF Report for Audit {selected_audit_id}",
                        )

    except requests.exceptions.ConnectionError:
        st.error(
            f"Could not connect to the backend API at {API_BASE}. "
            "Check that API_BASE_URL points to a reachable FastAPI URL."
        )
    except ModuleNotFoundError as e:
        st.error(
            f"Module import error: {str(e)}. "
            "Make sure your GitHub repo contains the app/ folder and app/__init__.py."
        )
    except requests.exceptions.HTTPError as e:
        try:
            st.error(f"API error: {e.response.json()}")
        except Exception:
            st.error(f"API error: {e.response.text}")
    except Exception as e:
        st.error(f"Unexpected error while loading history: {str(e)}")
