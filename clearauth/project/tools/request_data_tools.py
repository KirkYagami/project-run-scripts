import pandas as pd
from config import config as c
from data_pipeline.dataset_loader import load_raw_dataset
from data_pipeline.request_cleaning import clean_request_records
from data_pipeline.note_cleaning import clean_note_records
from data_pipeline.common_cleaning import refuse_missing_values,refuse_repeated_references
import re
def load_open_requests():return clean_request_records(load_raw_dataset(c.OPEN_REQUESTS_FILE),c.REQUEST_VALUE_MAPPINGS,c.REQUEST_WHOLE_NUMBER_PATTERNS)
def load_request_notes():
    f=clean_note_records(load_raw_dataset(c.REQUEST_NOTES_FILE),c.NOTE_VALUE_MAPPINGS,c.NOTE_WHOLE_NUMBER_PATTERNS,c.NOTE_ID_COLUMN,c.NOTE_TEXT_COLUMN)
    refuse_missing_values(f,[c.NOTE_NUMBER_COLUMN]);refuse_repeated_references(f,[c.REQUEST_REFERENCE_COLUMN,c.NOTE_NUMBER_COLUMN]);return f
def fetch_request(open_requests,request_reference):
    f=open_requests[open_requests[c.REQUEST_REFERENCE_COLUMN]==request_reference]
    if f.empty:raise ValueError(c.UNKNOWN_REQUEST_MESSAGE.format(request_reference=request_reference))
    r=f.iloc[0].to_dict()
    if pd.isna(r[c.SERVICE_CODE_COLUMN]):raise ValueError(c.NO_SERVICE_CODE_MESSAGE.format(request_reference=request_reference))
    return r
def fetch_request_documents(request_notes,request):
    docs=request_notes[request_notes[c.REQUEST_REFERENCE_COLUMN]==request[c.REQUEST_REFERENCE_COLUMN]].sort_values(c.NOTE_NUMBER_COLUMN).to_dict('records')
    n=request[c.SUPPORTING_DOCUMENT_COUNT_COLUMN]
    if pd.notna(n) and len(docs)!=n:raise ValueError(f"{request[c.REQUEST_REFERENCE_COLUMN]}: {n} documents expected, {len(docs)} received")
    return docs
def rank_review_queue(open_requests):
    return open_requests.assign(_urgent=open_requests[c.URGENCY_COLUMN].eq(c.URGENT).fillna(False)).sort_values(['_urgent',c.REQUEST_REFERENCE_COLUMN],ascending=[False,True])[c.REQUEST_REFERENCE_COLUMN].tolist()
def canonical_request_reference(written_reference):
    m=re.fullmatch(c.REQUEST_REFERENCE_PATTERN,written_reference)
    return m.expand(c.CANONICAL_REQUEST_REFERENCE_FORMAT) if m else written_reference
def describe_request(request):return {k:c.NOT_GIVEN_TEXT if pd.isna(v) else str(v) for k,v in request.items()}
