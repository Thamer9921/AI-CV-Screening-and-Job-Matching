import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import json
import sqlite3

import streamlit as st

from agents.cv_agent import analyze_cv
from agents.job_agent import load_jobs
from agents.match_agent import analyze_all_jobs
from agents.recommendation_agent import generate_recommendations
from auth_db import (
    register_user,
    login_user,
    load_user_profile,
    save_user_profile,
    save_user_cv,
    load_user_cv,
    delete_user_cv,
)
from database.db import (
    init_db,
    save_analysis,
    load_analysis_history,
    delete_analysis_history,
)


st.set_page_config(
    page_title="AI Match",
    page_icon="🔎",
    layout="wide",
)

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2rem;}
h1, h2, h3 {color: #0F172A;}
.stButton > button {border-radius: 10px;}
[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 16px;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

try:
    init_db()
except sqlite3.Error:
    st.error("Could not open the local database.")
    st.stop()


LOCATIONS = ["", "Riyadh", "Jeddah", "Abha", "Dammam", "Medina", "Remote"]
JOB_TYPES = ["", "Full-time", "Part-time", "Internship", "Freelance"]
FIELDS = [
    "",
    "Artificial Intelligence",
    "Data Science",
    "Web Development",
    "Software Engineering",
    "Cloud Computing",
    "Cybersecurity",
    "Mobile Development",
    "DevOps",
]


def clear_results():
    for key in ("results", "analysis_meta", "detected_skills"):
        st.session_state.pop(key, None)


def logout():
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


def preference_input(label, options, value, key):
    choices = list(options)
    if value and value not in choices:
        choices.append(value)
    return st.selectbox(
        label,
        choices,
        index=choices.index(value) if value in choices else 0,
        format_func=lambda item: item or "Any",
        key=key,
    )


def render_results(results, key_prefix):
    if not results:
        st.info("No results to display.")
        return

    st.caption(
        "Match scores are heuristic indicators, not acceptance probabilities. "
        "Ranking points include preferences and can exceed 100."
    )

    rows = [
        {
            "Job": job["title"],
            "Location": job["location"],
            "Match / 100": job["final_score"],
            "Preference points": job["preference_points"],
            "Ranking points": job["ranking_score"],
        }
        for job in results
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Top recommendations")
    recommendations = generate_recommendations(results, top_n=3)

    for position, job in enumerate(recommendations, start=1):
        with st.container(border=True):
            st.subheader(f"{position}. {job['title']}")
            st.text(
                f"{job['company']} | {job['location']} | "
                f"{job.get('job_type', '')} | {job.get('work_mode', '')}"
            )
            if job.get("is_demo"):
                st.caption("DEMO JOB — not a verified vacancy.")

            c1, c2, c3 = st.columns(3)
            c1.metric("Match score", f"{job['final_score']:.2f} / 100")
            c2.metric("Preference bonus", job["preference_points"])
            c3.metric("Ranking points", job["ranking_score"])

            st.write(job["fit_label"])
            st.write(job["reason"])
            st.write(job["tip"])
            st.caption(job["preference_reason"])

            with st.expander("Score breakdown and job description"):
                st.write(job["score_basis"])
                st.write("Semantic similarity:", job["semantic_score"])
                st.write("Lexical similarity:", job["similarity_score"])
                st.write("Skill coverage:", job["skill_score"])
                st.write(
                    "Detected matching skills:",
                    ", ".join(job["matched_skills"]) or "None",
                )
                st.write(
                    "Skills not detected:",
                    ", ".join(job["missing_skills"]) or "None",
                )
                st.text(job["description"])

    st.download_button(
        "Download results as JSON",
        data=json.dumps(results, ensure_ascii=False, indent=2),
        file_name="ai_match_results.json",
        mime="application/json",
        key=f"{key_prefix}_download",
    )


def auth_page():
    st.title("AI Match")
    st.write("CV screening and job matching, running locally.")
    st.caption(
        "Accounts are stored on this computer. "
        "No email verification or external account connection is used."
    )

    sign_in, sign_up = st.tabs(["Sign in", "Create account"])

    with sign_in:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input(
                "Password", type="password", key="login_password"
            )
            submitted = st.form_submit_button("Sign in", type="primary")

        if submitted:
            ok, message = login_user(email, password)
            if ok:
                for key in list(st.session_state):
                    del st.session_state[key]
                st.session_state.user_email = email.strip().lower()
                st.rerun()
            else:
                st.error(message)

    with sign_up:
        with st.form("register_form"):
            name = st.text_input("Full name", max_chars=120)
            email = st.text_input("Email", key="register_email")
            password = st.text_input(
                "Password", type="password", key="register_password"
            )
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, message = register_user(name, email, password)
                if ok:
                    st.success("Account created. Open Sign in to continue.")
                else:
                    st.error(message)


def home_page():
    st.title("Find the fit. Understand the gaps.")
    st.write(
        "Compare your CV with technical roles, inspect matching skills, "
        "and rank opportunities using your preferences."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Demo roles", len(load_jobs()))
    c2.metric("CV formats", "PDF · DOCX · TXT")
    c3.metric("Processing", "Local")

    st.subheader("How to use AI Match")
    st.write(
        "1. Set your preferences in Profile.\n"
        "2. Open Dashboard and upload a text-based CV.\n"
        "3. Compare demo jobs or paste a job description.\n"
        "4. Review the scores and skill gaps."
    )
    st.info(
        "Use English CVs and job descriptions for this version. "
        "Scanned PDFs require OCR, which is not included."
    )


def dashboard_page(email, profile):
    st.title("CV Analysis Dashboard")

    saved_name, saved_bytes = load_user_cv(email)

    with st.form("analysis_form"):
        source_options = ["Upload a CV"]
        if saved_bytes is not None:
            source_options.insert(0, "Use saved CV")

        source = st.radio("CV source", source_options)
        if saved_name:
            st.text(f"Saved CV: {saved_name}")

        uploaded = st.file_uploader(
            "Upload PDF, DOCX or TXT",
            type=["pdf", "docx", "txt"],
        )
        keep_cv = st.checkbox("Save uploaded CV to my local account")

        mode = st.radio(
            "Jobs to compare",
            ["Demo jobs", "Paste a job description"],
        )

        with st.expander("Custom job details"):
            title = st.text_input("Job title")
            company = st.text_input("Company (optional)")
            description = st.text_area("Job description", height=180)
            location = st.selectbox(
                "Job location", ["Unspecified", *LOCATIONS[1:]]
            )
            job_type = st.selectbox(
                "Job type", ["Unspecified", *JOB_TYPES[1:]]
            )
            work_mode = st.selectbox(
                "Work mode", ["Unspecified", "On-site", "Hybrid", "Remote"]
            )
            field = st.selectbox(
                "Job field", ["Unspecified", *FIELDS[1:]]
            )

        st.caption(
            "Preferences are taken from Profile. "
            "They add ranking points rather than filtering out other jobs."
        )
        submitted = st.form_submit_button("Analyze Match", type="primary")

    if submitted:
        clear_results()

        try:
            if source == "Use saved CV":
                filename, file_bytes = saved_name, saved_bytes
            elif uploaded is not None:
                filename, file_bytes = uploaded.name, uploaded.getvalue()
            else:
                raise ValueError("Upload a CV first.")

            if mode == "Demo jobs":
                jobs = load_jobs()
            else:
                if not title.strip() or not description.strip():
                    raise ValueError("Enter the job title and description.")
                jobs = [{
                    "id": "custom-job",
                    "title": title.strip(),
                    "company": company.strip() or "User-provided",
                    "location": location,
                    "job_type": job_type,
                    "work_mode": work_mode,
                    "field": field,
                    "description": description.strip(),
                    "url": "",
                    "source": "manual",
                    "is_demo": False,
                }]

            with st.spinner("Analyzing locally..."):
                cv_data = analyze_cv(filename, file_bytes)
                results = analyze_all_jobs(cv_data, jobs, profile)

                if source == "Upload a CV" and keep_cv:
                    save_user_cv(email, filename, file_bytes)

                save_analysis(email, filename, results)

            st.session_state.results = results
            st.session_state.detected_skills = cv_data["skills"]
            st.session_state.analysis_meta = {
                "filename": filename,
                "mode": mode,
            }
            st.success("Analysis completed and saved locally.")

        except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
            st.error(str(exc))

    if "results" in st.session_state:
        meta = st.session_state.analysis_meta
        st.divider()
        st.text(f"Last analysis: {meta['filename']} | {meta['mode']}")
        st.caption("Input changes take effect after you click Analyze Match.")

        with st.expander("Skills detected in the CV"):
            st.write(
                ", ".join(st.session_state.detected_skills)
                or "No skills from the current vocabulary were detected."
            )

        render_results(st.session_state.results, "dashboard")


def profile_page(email, profile):
    st.title("My Profile")
    st.text(email)

    with st.form("profile_form"):
        name = st.text_input("Full name", value=profile["full_name"])
        location = preference_input(
            "Preferred location", LOCATIONS,
            profile["preferred_location"], "profile_location"
        )
        job_type = preference_input(
            "Preferred job type", JOB_TYPES,
            profile["job_type"], "profile_job_type"
        )
        field = preference_input(
            "Field of interest", FIELDS,
            profile["field_of_interest"], "profile_field"
        )
        submitted = st.form_submit_button("Save profile", type="primary")

    if submitted:
        try:
            save_user_profile(email, name, location, job_type, field)
            clear_results()
            st.success("Profile saved. Run a new analysis to apply preferences.")
        except (ValueError, sqlite3.Error) as exc:
            st.error(str(exc))

    st.subheader("Saved CV")
    filename, file_bytes = load_user_cv(email)

    if filename:
        st.text(filename)
        st.download_button(
            "Download saved CV",
            data=file_bytes,
            file_name=filename,
            mime="application/octet-stream",
        )
        confirm = st.checkbox("Confirm deletion of my saved CV")
        if st.button("Delete saved CV", disabled=not confirm):
            delete_user_cv(email)
            clear_results()
            st.rerun()
        st.caption(
            "Deleting the CV does not delete previous analysis results. "
            "You can remove those from History."
        )
    else:
        st.info("No saved CV. You can save one from Dashboard.")


def history_page(email):
    st.title("Analysis History")
    history = load_analysis_history(email)

    if not history:
        st.info("No saved analyses yet.")
        return

    st.caption("Showing up to 20 recent analyses. Times are UTC.")
    for item in history:
        label = (
            f"#{item['id']} | {item['cv_filename']} | {item['created_at']}"
        )
        with st.expander(label):
            render_results(item["results"], f"history_{item['id']}")

    st.divider()
    confirm = st.checkbox("Confirm deletion of all my analysis history")
    if st.button("Delete history", disabled=not confirm):
        delete_analysis_history(email)
        clear_results()
        st.rerun()


def about_page():
    st.title("About AI Match")
    st.write(
        "A university project for comparing CVs with job descriptions "
        "and explaining detected skill gaps."
    )
    st.subheader("How matching works")
    st.write(
        "Sentence Transformers and FAISS provide semantic similarity. "
        "TF-IDF measures lexical overlap. A predefined skill vocabulary "
        "identifies recognised skills."
    )
    st.write(
        "The match score uses 60% skill coverage, 25% semantic similarity "
        "and 15% lexical similarity. If no job skills are detected, "
        "the fallback uses 75% semantic and 25% lexical similarity."
    )
    st.write(
        "Preference bonuses: location +10, job type +8, field +12. "
        "These affect ranking points without changing the match score."
    )
    st.subheader("Limits and data")
    st.write(
        "- The weights and labels are heuristic and not calibrated hiring decisions.\n"
        "- The model is intended here for English text and may truncate long inputs.\n"
        "- Skill mentions do not prove proficiency, experience, or qualifications.\n"
        "- Demo jobs are fictional and custom descriptions are user-provided.\n"
        "- Uploaded files, accounts and history stay on the local computer.\n"
        "- Passwords are hashed; CV files and result data are not encrypted at rest.\n"
        "- This version has no external API calls or email sending."
    )


if not st.session_state.get("user_email"):
    auth_page()
    st.stop()

email = st.session_state.user_email

try:
    profile = load_user_profile(email)
except ValueError:
    logout()

with st.sidebar:
    st.title("AI Match")
    st.text(profile["full_name"])
    st.caption("Local workspace")
    page = st.radio(
        "Navigation",
        ["Home", "Dashboard", "Profile", "History", "About"],
    )
    st.divider()
    if st.button("Sign out", use_container_width=True):
        logout()

try:
    if page == "Home":
        home_page()
    elif page == "Dashboard":
        dashboard_page(email, profile)
    elif page == "Profile":
        profile_page(email, profile)
    elif page == "History":
        history_page(email)
    else:
        about_page()
except sqlite3.Error:
    st.error("A local database operation failed. Please try again.")