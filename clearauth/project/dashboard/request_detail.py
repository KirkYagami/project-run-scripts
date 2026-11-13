import html
from collections import Counter
import pandas as pd
import streamlit as st
from config import config as c
from .api_client import call_service
from .components import badge, show_review


def _screening_wireframe(s):
    # Native SVG keeps the diagram editable and avoids a Graphviz/.dot dependency.
    n = len(s["criteria"])
    width = 1000
    height = 130 + n * 66
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Criteria screening flow">'
    ]
    for i, r in enumerate(s["criteria"]):
        y = 10 + i * 66
        fill = c.SCREENING_FILL_COLOURS[r["result"]]
        line = c.SCREENING_LINE_COLOURS[r["result"]]
        parts.append(
            f'<rect x="10" y="{y}" width="620" height="50" rx="6" fill="{fill}" stroke="{line}"/><text x="25" y="{y+30}" font-family="{c.SCREENING_GRAPH_FONT}" font-size="17" fill="{c.SCREENING_TEXT_COLOUR}">{html.escape(r["criterion_name"]+": "+r["result"])}</text><path d="M 630 {y+25} H 680 V {height-80} H 720" stroke="{c.SCREENING_EDGE_COLOUR}" fill="none"/>'
        )
    y = height - 110
    parts.append(
        f'<rect x="720" y="{y}" width="270" height="85" rx="6" fill="{c.SCREENING_FILL_COLOURS[c.SCREENING_NODE]}" stroke="{c.SCREENING_LINE_COLOURS[c.SCREENING_NODE]}"/>'
    )
    for j, line in enumerate(s["screening"].split(" ", 1)):
        parts.append(
            f'<text x="735" y="{y+30+j*25}" font-size="16" font-family="{c.SCREENING_GRAPH_FONT}" fill="{c.SCREENING_TEXT_COLOUR}">{html.escape(line)}</text>'
        )
    parts.append("</svg>")
    st.html("".join(parts))


def render_request_detail_page():
    st.title(c.PAGE_DETAIL)
    queue = call_service("GET", "/queue", query={"service_code": c.QUEUE_SERVICE_ALL})
    refs = [r["request_reference"] for r in queue]
    if not refs:
        st.info("No open requests.")
        return
    selected = st.session_state.get("selected_request")
    ref = st.selectbox(
        "Request", refs, index=refs.index(selected) if selected in refs else 0
    )
    st.session_state["selected_request"] = ref
    d = call_service("GET", "/queue/" + ref)
    r = d["request"]
    s = d["screening"]
    st.subheader(
        c.SERVICE_WITH_CODE_FORMAT.format(
            service_name=c.SERVICE_NAMES[r[c.SERVICE_CODE_COLUMN]],
            service_code=r[c.SERVICE_CODE_COLUMN],
        )
    )
    if r[c.URGENCY_COLUMN] == c.URGENT:
        st.badge(c.URGENT, color=c.URGENT_BADGE_COLOUR)
    badge(s["screening"], c.DECISION_BADGE_COLOURS)
    badge(d["likelihood"]["approval_band"], c.APPROVAL_BAND_BADGE_COLOURS)
    st.caption(f"Queue position {d['queue_position']} · {s['policy_document']}")
    st.write(
        {
            k: r[k]
            for k in [
                c.PROVIDER_NAME_COLUMN,
                c.PROVIDER_SPECIALTY_COLUMN,
                c.NETWORK_STATUS_COLUMN,
                c.RECEIVED_CHANNEL_COLUMN,
                c.SITE_OF_SERVICE_COLUMN,
                c.SUPPORTING_DOCUMENT_COUNT_COLUMN,
            ]
        }
    )
    cols = st.columns(5)
    for col, label, value in zip(
        cols,
        [
            "Criteria met",
            "Not met",
            "Not documented",
            "Approval likelihood",
            "Expected stay",
        ],
        [
            f"{s[c.CRITERIA_MET_COUNT_COLUMN]} / {len(s['criteria'])}",
            s[c.CRITERIA_NOT_MET_COUNT_COLUMN],
            s[c.CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN],
            f"{d['likelihood']['approval_likelihood']:.4f}",
            d["stay"].get("expected_stay_days", c.STAY_METRIC_NOT_WORKED_OUT),
        ],
    ):
        col.metric(label, value)
    st.caption(d["stay_text"])
    tabs = st.tabs(["Screening", "Evidence", "Questionnaire", "Review"])
    with tabs[0]:
        _screening_wireframe(s)
        st.write("Decisions open: " + ", ".join(s["decisions_open"]))
        if s["body_mass_index"] is not None:
            st.write("Body mass index:", s["body_mass_index"])
        for cr in s["criteria"]:
            with st.expander(cr["criterion_name"] + " — " + cr["result"]):
                st.write(cr["criterion_sentence"])
                st.write(
                    "Answers missing:",
                    [c.QUESTIONNAIRE_ANSWER_LABELS[k] for k in cr["missing_answers"]],
                )
    with tabs[1]:
        for conflict in d["disagreements"]:
            st.warning(conflict["disagreement_text"])
            st.write(conflict["sentence"])
        counts = Counter()
        for finding in d["evidence_findings"]:
            for name in finding["criteria_borne_on"] or ["No criterion"]:
                counts[name] += 1
        if counts:
            st.bar_chart(
                pd.DataFrame({"Sentences": dict(counts)}), color=c.EVIDENCE_CHART_COLOUR
            )
        if not d["request_documents"]:
            st.info("No document was sent.")
        for doc in d["request_documents"]:
            with st.expander(
                doc[c.NOTE_ID_COLUMN] + " · " + doc[c.NOTE_AUTHOR_ROLE_COLUMN]
            ):
                for finding in d["evidence_findings"]:
                    if finding["note_id"] == doc[c.NOTE_ID_COLUMN]:
                        st.badge(
                            finding["evidence_type"], color=c.EVIDENCE_BADGE_COLOUR
                        )
                        st.write(finding["sentence"])
                        st.caption(
                            ", ".join(finding["criteria_borne_on"])
                            or "Bears on no criterion"
                        )
    with tabs[2]:
        for cr in s["criteria"]:
            st.write(cr["criterion_name"])
            st.table(
                pd.DataFrame(
                    [
                        {"Answer": c.QUESTIONNAIRE_ANSWER_LABELS[k], "Value": r[k]}
                        for k in c.CRITERION_ANSWER_COLUMNS[cr["criterion_kind"]]
                    ]
                )
            )
    with tabs[3]:
        reviews = call_service(
            "GET", "/reviews", query={"status_value": c.REVIEW_STATUS_OPTIONS}
        )
        matching = [v for v in reviews if v["request_reference"] == ref]
        if matching:
            show_review(matching[0], full=True)
        else:
            with st.form("start_review"):
                question = st.text_area(
                    "What should the review look at?",
                    max_chars=c.COORDINATOR_REQUEST_MAXIMUM_CHARACTERS,
                )
                submit = st.form_submit_button("Prepare review", type="primary")
            if submit:
                if len(question.strip()) < c.COORDINATOR_REQUEST_MINIMUM_CHARACTERS:
                    st.error("Please describe what to review.")
                    return
                result = call_service(
                    "POST",
                    "/reviews",
                    payload=dict(
                        request_reference=ref, coordinator_request=question.strip()
                    ),
                    waiting_message=f"Preparing review: {c.LLM_CALLS_BEFORE_DECISION} model calls",
                )
                st.success("Review is waiting for an independent nurse decision.")
                show_review(result, full=True)
