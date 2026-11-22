
import csv
import io
import os
import sys
import time
from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st

# --------------------------------------------------
# PROJECT PATHS AND BACKEND IMPORTS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"

# Support either project-root modules or a src folder.
sys.path.insert(0, str(PROJECT_DIR))
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from classifier import classify, GeminiQuotaExhausted
from validator import is_valid
from safety import apply_safety, check_red_flags


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Clinic Visit Sorter",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    [data-testid="stMetric"] {
        background: #f5f7fb;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e9f0;
    }

    .main-heading {
        font-size: 2rem;
        font-weight: 700;
        color: #172554;
        margin-bottom: 0;
    }

    .sub-heading {
        color: #64748b;
        margin-top: 5px;
        margin-bottom: 25px;
    }

    .notice {
        background: #fff7ed;
        border-left: 4px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 6px;
        color: #7c2d12;
        margin: 12px 0;
    }

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 42px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

REQUIRED_COLUMNS = ["id", "arrival_time", "note"]

PRIORITY_ORDER = {
    "see_now": 1,
    "today": 2,
    "routine": 3
}


def find_default_csv():
    """Find the project's existing visits CSV."""
    candidates = [
        PROJECT_DIR / "data" / "visits.csv",
        PROJECT_DIR / "visits.csv"
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def load_uploaded_csv(uploaded_file):
    """Read and validate an uploaded CSV."""
    try:
        dataframe = pd.read_csv(uploaded_file)
    except Exception as error:
        raise ValueError(f"Could not read the CSV: {error}")

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            "Your CSV is missing these required columns: "
            + ", ".join(missing)
        )

    if dataframe.empty:
        raise ValueError("The CSV contains no visits.")

    dataframe = dataframe.fillna("")
    return dataframe.to_dict(orient="records")


def load_default_csv():
    """Load the existing project dataset."""
    path = find_default_csv()

    if path is None:
        raise FileNotFoundError(
            "Could not find data/visits.csv or visits.csv."
        )

    dataframe = pd.read_csv(path).fillna("")

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing:
        raise ValueError(
            "The project's CSV is missing: " + ", ".join(missing)
        )

    if dataframe.empty:
        raise ValueError("The project's CSV contains no visits.")

    return dataframe.to_dict(orient="records"), path


def process_visits(visits):
    """
    Process every visit.

    When Gemini quota is exhausted, remaining visits are
    marked as fallback and require human review.
    """

    processed = []
    gemini_available = True
    quota_exhausted = False

    progress = st.progress(0)
    status = st.empty()

    total = len(visits)

    for index, original_visit in enumerate(visits):

        visit = dict(original_visit)
        note = str(visit.get("note", "")).strip()

        status.info(
            f"Processing visit {index + 1} of {total} "
            f"— Visit ID: {visit.get('id', index + 1)}"
        )

        result = None
        classification_source = "fallback"

        if gemini_available:
            try:
                result = classify(note)

                if result is not None and is_valid(result):
                    classification_source = "AI"

                else:
                    # Avoid repeatedly calling a failing service.
                    gemini_available = False

            except GeminiQuotaExhausted:
                gemini_available = False
                quota_exhausted = True

        if classification_source == "fallback":
            result = {
                "category": "other",
                "priority": "today",
                "summary": "Classification unavailable"
            }

        visit.update(result)

        # Unknown cases must not be shown as routine.
        if (
            visit["category"] == "other"
            and visit["priority"] == "routine"
        ):
            visit["priority"] = "today"

        # Check safety keywords independently of AI classification.
        safety_flag = check_red_flags(note)

        # Apply the existing project's safety escalation.
        visit["priority"] = apply_safety(
            note,
            visit["priority"]
        )

        visit["classification_source"] = classification_source
        visit["needs_review"] = classification_source == "fallback"
        visit["safety_flag"] = safety_flag

        processed.append(visit)

        progress.progress((index + 1) / total)

        # Keep the existing API delay while Gemini is available.
        if (
            gemini_available
            and classification_source == "AI"
            and index < total - 1
        ):
            time.sleep(13)

    status.success("Processing finished.")

    if quota_exhausted:
        st.warning(
            "Gemini quota was exhausted. Remaining visits were "
            "processed in fallback mode and marked for human review."
        )

    return processed


def sort_visits(visits):
    """Sort urgent visits first, then by arrival time."""
    return sorted(
        visits,
        key=lambda visit: (
            PRIORITY_ORDER.get(visit.get("priority"), 2),
            str(visit.get("arrival_time", ""))
        )
    )


def create_csv_report(visits):
    """Create a downloadable CSV report in memory."""
    fields = [
        "id",
        "arrival_time",
        "note",
        "category",
        "priority",
        "summary",
        "classification_source",
        "needs_review",
        "safety_flag"
    ]

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fields,
        extrasaction="ignore"
    )

    writer.writeheader()
    writer.writerows(sort_visits(visits))

    return output.getvalue().encode("utf-8-sig")


def create_summary_report(visits):
    """Create a downloadable text summary."""
    priority_counts = Counter(
        visit.get("priority", "today") for visit in visits
    )

    category_counts = Counter(
        visit.get("category", "other") for visit in visits
    )

    ai_count = sum(
        visit.get("classification_source") == "AI"
        for visit in visits
    )

    review_count = sum(
        visit.get("needs_review", False)
        for visit in visits
    )

    safety_count = sum(
        visit.get("safety_flag", False)
        for visit in visits
    )

    lines = [
        "CLINIC VISIT SORTER — SESSION REPORT",
        "=" * 40,
        "",
        f"Total visits: {len(visits)}",
        f"AI classified: {ai_count}",
        f"Needs human review: {review_count}",
        f"Safety keyword flags: {safety_count}",
        "",
        "PRIORITY COUNTS",
        "-" * 20
    ]

    for key, value in priority_counts.items():
        lines.append(f"{key}: {value}")

    lines.extend(["", "CATEGORY COUNTS", "-" * 20])

    for key, value in category_counts.items():
        lines.append(f"{key}: {value}")

    lines.extend([
        "",
        "IMPORTANT",
        "This is an educational prototype, not a clinically",
        "validated triage system. Human review is required.",
    ])

    return "\n".join(lines)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "visits" not in st.session_state:
    st.session_state.visits = []

if "processed" not in st.session_state:
    st.session_state.processed = False

if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = ""


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.title("🏥 Clinic Sorter")
    st.caption("Visit management dashboard")

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Priority Queue",
            "Data Management",
            "Reports"
        ]
    )

    st.divider()

    st.caption("PROJECT STATUS")
    st.write("Prototype version")
    st.write("AI: Gemini API")
    st.write("Review: Human required")


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<p class="main-heading">Clinic Visit Sorter</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="sub-heading">'
    'A simple dashboard for organizing incoming clinic visits.'
    '</p>',
    unsafe_allow_html=True
)

st.warning(
    "Educational prototype only. This tool is not medically "
    "validated and must not make clinical decisions. A qualified "
    "human must review every visit, especially safety flags and "
    "unclassified visits."
)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

if page == "Dashboard":

    st.subheader("Dashboard")

    visits = st.session_state.visits

    if not st.session_state.processed or not visits:
        st.info(
            "No processed visits yet. Go to Data Management "
            "to load a dataset and start processing."
        )

    else:
        total = len(visits)

        urgent = sum(
            visit["priority"] == "see_now"
            for visit in visits
        )

        review = sum(
            visit.get("needs_review", False)
            for visit in visits
        )

        ai_count = sum(
            visit.get("classification_source") == "AI"
            for visit in visits
        )

        safety_count = sum(
            visit.get("safety_flag", False)
            for visit in visits
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total visits", total)
        c2.metric("Safety keyword flags", safety_count)
        c3.metric("Needs human review", review)
        c4.metric("AI classified", ai_count)

        st.divider()

        left, right = st.columns(2)

        with left:
            st.markdown("#### Queue priority")

            priority_counts = Counter(
                visit["priority"] for visit in visits
            )

            priority_data = pd.DataFrame({
                "Priority": ["see_now", "today", "routine"],
                "Visits": [
                    priority_counts.get("see_now", 0),
                    priority_counts.get("today", 0),
                    priority_counts.get("routine", 0)
                ]
            })

            st.bar_chart(
                priority_data.set_index("Priority")
            )

        with right:
            st.markdown("#### Classification status")

            status_data = pd.DataFrame({
                "Status": ["AI classified", "Needs review"],
                "Visits": [
                    ai_count,
                    review
                ]
            })

            st.bar_chart(
                status_data.set_index("Status")
            )

        st.divider()
        st.markdown("#### Recent visits")

        preview = sort_visits(visits)[:5]

        preview_data = []

        for visit in preview:
            if visit.get("safety_flag"):
                status_label = "Safety flag — urgent human review"
            elif visit.get("needs_review"):
                status_label = "Fallback — needs review"
            else:
                status_label = "AI classified"

            preview_data.append({
                "Visit ID": visit.get("id", ""),
                "Arrival": visit.get("arrival_time", ""),
                "Status": status_label,
                "Summary": visit.get("summary", "")
            })

        st.dataframe(
            pd.DataFrame(preview_data),
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# PRIORITY QUEUE
# --------------------------------------------------

elif page == "Priority Queue":

    st.subheader("Priority Queue")

    visits = st.session_state.visits

    if not st.session_state.processed or not visits:
        st.info("Process a dataset before viewing the queue.")

    else:
        filter_option = st.selectbox(
            "Filter visits",
            [
                "All visits",
                "Safety keyword flags",
                "Needs human review",
                "AI classified",
                "SEE NOW",
                "TODAY",
                "ROUTINE"
            ]
        )

        filtered = sort_visits(visits)

        if filter_option == "Safety keyword flags":
            filtered = [
                v for v in filtered if v.get("safety_flag")
            ]

        elif filter_option == "Needs human review":
            filtered = [
                v for v in filtered if v.get("needs_review")
            ]

        elif filter_option == "AI classified":
            filtered = [
                v for v in filtered
                if v.get("classification_source") == "AI"
            ]

        elif filter_option in ["SEE NOW", "TODAY", "ROUTINE"]:
            filtered = [
                v for v in filtered
                if v.get("priority") == filter_option.lower()
            ]

        st.caption(f"Showing {len(filtered)} visits")

        for visit in filtered:

            visit_id = visit.get("id", "Unknown")
            arrival = visit.get("arrival_time", "—")

            if visit.get("safety_flag"):
                title_status = "⚠️ SAFETY KEYWORD FLAG — HUMAN REVIEW"
            elif visit.get("needs_review"):
                title_status = "🟠 FALLBACK — NEEDS REVIEW"
            else:
                title_status = "AI CLASSIFIED"

            with st.expander(
                f"Visit {visit_id}  |  {arrival}  |  {title_status}"
            ):
                a, b = st.columns(2)

                a.write("**Category**")
                a.write(visit.get("category", "other"))

                b.write("**Queue priority**")
                b.write(visit.get("priority", "today").upper())

                st.write("**Original note**")
                st.write(visit.get("note", ""))

                st.write("**Summary**")
                st.write(visit.get("summary", ""))

                st.write(
                    "**Classification source:** "
                    + visit.get("classification_source", "Unknown")
                )

                if visit.get("safety_flag"):
                    st.error(
                        "A safety keyword was detected. "
                        "This is a warning for immediate human review, "
                        "not a medical diagnosis."
                    )

                if visit.get("needs_review"):
                    st.warning(
                        "AI classification was unavailable. "
                        "Do not rely on the fallback category or priority. "
                        "Human review is required."
                    )


# --------------------------------------------------
# DATA MANAGEMENT
# --------------------------------------------------

elif page == "Data Management":

    st.subheader("Data Management")

    st.write(
        "Choose your existing project dataset or upload a new CSV file."
    )

    data_source = st.radio(
        "Select data source",
        [
            "Use existing project CSV",
            "Upload a CSV file"
        ]
    )

    selected_visits = None
    selected_name = ""

    if data_source == "Use existing project CSV":

        default_path = find_default_csv()

        if default_path:
            st.success(f"Dataset found: {default_path.name}")
            st.caption(f"Location: {default_path}")
        else:
            st.error(
                "No default dataset found. Expected "
                "data/visits.csv or visits.csv."
            )

    else:
        uploaded_file = st.file_uploader(
            "Upload visits CSV",
            type=["csv"],
            help="Required columns: id, arrival_time, note"
        )

        if uploaded_file is not None:
            try:
                selected_visits = load_uploaded_csv(uploaded_file)
                selected_name = uploaded_file.name

                st.success(
                    f"Loaded {len(selected_visits)} visits."
                )

                st.dataframe(
                    pd.DataFrame(selected_visits),
                    use_container_width=True,
                    hide_index=True
                )

            except ValueError as error:
                st.error(str(error))

    if st.button(
        "Load and process visits",
        type="primary",
        use_container_width=True
    ):

        try:
            if data_source == "Use existing project CSV":
                selected_visits, path = load_default_csv()
                selected_name = path.name

            if not selected_visits:
                st.error("Please select a valid dataset first.")
            else:
                st.session_state.processed = False
                st.session_state.visits = []

                st.write("### Processing")

                results = process_visits(selected_visits)

                st.session_state.visits = results
                st.session_state.processed = True
                st.session_state.dataset_name = selected_name

                st.success(
                    f"Successfully processed {len(results)} visits."
                )

                st.rerun()

        except Exception as error:
            st.error(f"Processing failed: {error}")


# --------------------------------------------------
# REPORTS
# --------------------------------------------------

elif page == "Reports":

    st.subheader("Reports")

    visits = st.session_state.visits

    if not st.session_state.processed or not visits:
        st.info("Process a dataset to generate reports.")

    else:
        st.success(
            f"Reports are ready for {len(visits)} visits."
        )

        csv_data = create_csv_report(visits)
        summary_data = create_summary_report(visits)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### Nurse queue CSV")

            st.download_button(
                "Download nurse_queue.csv",
                data=csv_data,
                file_name="nurse_queue.csv",
                mime="text/csv",
                use_container_width=True
            )

        with c2:
            st.markdown("#### Session summary")

            st.download_button(
                "Download summary.txt",
                data=summary_data,
                file_name="summary.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.divider()

        st.markdown("#### Report preview")
        st.code(summary_data, language="text")
