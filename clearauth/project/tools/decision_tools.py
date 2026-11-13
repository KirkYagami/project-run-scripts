import pandas as pd
from config import config as c
def find_decision_refusal(review_decision,screening,request,coordinator_id):
    ref=request[c.REQUEST_REFERENCE_COLUMN];d=review_decision
    missing=[k for k in c.DECISION_RECORD_FIELDS if not isinstance(d.get(k),str) or not d[k].strip()]
    if missing:return c.DECISION_FIELDS_MISSING_MESSAGE.format(request_reference=ref,fields=', '.join(missing))
    decision=d['decision']
    if decision not in c.DECISIONS:return c.UNKNOWN_DECISION_MESSAGE.format(decision=decision,request_reference=ref,decisions=', '.join(c.DECISIONS))
    if d['decided_by_role']!=c.ROLE_NURSE:return c.DECIDING_ROLE_MESSAGE.format(role=d['decided_by_role'],request_reference=ref,nurse_role=c.ROLE_NURSE)
    if d['decided_by'].strip().lower()==coordinator_id.strip().lower():return c.OWN_REVIEW_MESSAGE.format(decided_by=d['decided_by'],request_reference=ref)
    if decision not in screening['decisions_open']:return c.DECISION_NOT_OPEN_MESSAGE.format(decision=decision,request_reference=ref,reason=c.SCREENING_CLOSED_REASONS[screening['screening']])
    if decision==c.DECISION_APPROVE:
        keys=[c.SITE_OF_SERVICE_COLUMN]+([c.REQUESTED_INPATIENT_DAYS_COLUMN] if request.get(c.SITE_OF_SERVICE_COLUMN)==c.INPATIENT_SITE else [])
        missing=[c.AUTHORISATION_ANSWER_LABELS[k] for k in keys if pd.isna(request.get(k))]
        if missing:return c.APPROVAL_LETTER_INCOMPLETE_MESSAGE.format(request_reference=ref,answers=' or '.join(missing))
    return None
