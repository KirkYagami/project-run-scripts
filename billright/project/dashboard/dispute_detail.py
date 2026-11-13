"""The dispute detail page and the form that opens an assessment."""
import streamlit as st

from config import config
from dashboard.api_client import call_service


def _money(value):
    return f"GBP {value}"


def render_dispute_detail_page():
    """Show everything established about one dispute, and let an analyst start the assessment."""
    st.header(config.PAGE_DISPUTE)
    queue = call_service("GET", "/queue", {"direction": config.QUEUE_DIRECTION_ALL}, None, None)
    references = [row["dispute_reference"] for row in queue]
    remembered = st.session_state.get("chosen_dispute")
    index = references.index(remembered) if remembered in references else 0
    reference = st.selectbox("Dispute", references, index=index)
    detail = call_service("GET", f"/queue/{reference}", None, None, None)
    profile, rebill, cause = detail["profile"], detail["rebill"], detail["cause"]
    comparison, redress = detail["charge"]["comparison"], detail["charge"]["redress"]

    head = st.columns(4)
    head[0].metric("Direction", comparison["direction"])
    head[1].metric("Rebill score", f"{rebill['rebill_probability']} ({rebill['rebill_band']})")
    head[2].metric("Category", cause["dispute_category"])
    head[3].metric("Centre", profile["billing_centre"])
    st.caption(f"Account {profile['account_number']}")
    money = st.columns(5)
    money[0].metric("Amount billed", _money(comparison["amount_billed_gbp"]))
    money[1].metric("Corrected charge", _money(comparison["corrected_charge_gbp"]))
    money[2].metric("Difference", _money(comparison["difference_gbp"]))
    money[3].metric("Standard payments", _money(redress["redress_gbp"]))
    money[4].metric("Effort", f"{detail['effort']['effort_needed_hours']} hours")

    st.subheader("The corrected bill, piece by piece")
    for number, piece in enumerate(detail["charge"]["pieces"], start=1):
        window = piece["price_window"]
        if "unit_rate_pence" in window:
            prices = (f"{window['unit_rate_pence']}p per kWh, {window['standing_charge_pence']}p per day; "
                      f"usage {piece['units_kwh']} kWh")
        else:
            prices = (f"day {window['day_unit_rate_pence']}p, night {window['night_unit_rate_pence']}p, "
                      f"{window['standing_charge_pence']}p per day; usage day {piece['day_units_kwh']} kWh, "
                      f"night {piece['night_units_kwh']} kWh")
        st.write(f"**{number}. {piece['first_day']} to {piece['last_day']}** ({piece['days']} days), "
                 f"{piece['tariff']}: {prices}; charge {piece['charge_pence']}p")
    st.subheader("Schedules read")
    for tariff, schedule in detail["charge"]["tariff_schedules"].items():
        with st.expander(f"{tariff}: {config.TARIFF_DOCUMENT_BY_TARIFF[tariff]}"):
            st.json(schedule)
    if redress["breached_standards"]:
        st.subheader("Standards broken")
        for item in redress["breached_standards"]:
            st.write(f"{item['standard_code']}: GBP {item['payment_gbp']}")

    with st.expander("The account, the reads and the models' readings"):
        st.write("The account and the reads on the bill beside the verified reads")
        st.json(profile)
        st.write("Notes, oldest first")
        for note in detail["note_texts"]:
            st.write("- " + note)
        st.write("Rebill facts"); st.json(rebill)
        st.write("Cause facts"); st.json(cause)
        st.write("Effort estimate"); st.json(detail["effort"])

    st.subheader("Open an assessment")
    request_text = st.text_area("What should be looked at?", key=f"request_{reference}")
    ready = len(request_text.strip()) >= config.ANALYST_REQUEST_MINIMUM_CHARACTERS
    in_progress_key = f"assessment_in_progress_{reference}"
    assessment_in_progress = st.session_state.get(in_progress_key, False)
    if st.button("Start the assessment", disabled=not ready or assessment_in_progress):
        # Keep a per-dispute lock while the synchronous LangGraph request is running,
        # so a repeated click cannot open a duplicate assessment.
        st.session_state[in_progress_key] = True
        try:
            result = call_service("POST", "/assessments",
                                  None, {"dispute_reference": reference, "analyst_request": request_text},
                                  "Five agents are assessing the dispute")
        finally:
            # This also releases the button after the API client's timeout/failure path.
            st.session_state[in_progress_key] = False
        st.success(f"Assessment {result['assessment_id']} is {result['status']}, waiting for a Revenue "
                   f"Controller. Recommendation: {result['recommended_decision']}")
        st.write(result["assessment_text"])
