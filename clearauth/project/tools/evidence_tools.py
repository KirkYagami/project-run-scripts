import re
import pandas as pd
from config import config as c
def read_document_evidence(evidence_model,documents):
    out=[]
    for d in documents:
        t=d[c.NOTE_TEXT_COLUMN]
        if pd.isna(t) or not str(t).strip():raise ValueError(f"{d[c.NOTE_ID_COLUMN]}: no document text")
        sentences=re.split(c.DOCUMENT_SENTENCE_PATTERN,t)
        predictions=evidence_model.predict(sentences)
        out.extend(dict(note_id=str(d[c.NOTE_ID_COLUMN]),note_author_role=str(d[c.NOTE_AUTHOR_ROLE_COLUMN]),sentence=s,evidence_type=str(p)) for s,p in zip(sentences,predictions))
    return out
def link_evidence_to_criteria(evidence_findings,screening):
    out=[]
    for f in evidence_findings:
        t=f['evidence_type']
        if t not in c.EVIDENCE_CRITERION_KINDS:raise ValueError(c.NO_EVIDENCE_CRITERIA_MESSAGE.format(evidence_type=t))
        out.append(f|dict(criteria_borne_on=[r['criterion_name'] for r in screening['criteria'] if r['criterion_kind'] in c.EVIDENCE_CRITERION_KINDS[t]]))
    return out
def flag_document_disagreements(evidence_findings,request,policy):
    if request[c.SERVICE_CODE_COLUMN]!=policy['service_code']:raise ValueError(c.POLICY_OF_ANOTHER_SERVICE_MESSAGE.format(request_reference=request[c.REQUEST_REFERENCE_COLUMN],service_code=request[c.SERVICE_CODE_COLUMN],document_name=policy['document_name']))
    if not any(c.MINIMUM_TREATMENT_WEEKS_RULE in x['rules'] for x in policy['criteria']):return []
    out=[];q=request.get(c.TREATMENT_WEEKS_COLUMN);q=None if pd.isna(q) else int(q)
    for f in evidence_findings:
        if f['evidence_type']!=c.CONSERVATIVE_TREATMENT_EVIDENCE:continue
        weeks=[]
        for written in re.findall(c.STATED_WEEKS_PATTERN,f['sentence'],flags=re.I):
            try:w=int(float(written))
            except ValueError:
                words=re.split(c.NUMBER_WORD_SEPARATOR_PATTERN,written.lower())
                if words[-1] not in c.NUMBER_WORD_VALUES:continue
                w=c.NUMBER_WORD_VALUES[words[-1]]
                if len(words)>1 and words[-2] in c.TENS_WORDS and words[-1] in c.UNIT_WORDS:w+=c.NUMBER_WORD_VALUES[words[-2]]
            if w not in weeks:weeks.append(w)
        if not weeks or q in weeks:continue
        flag=c.DESCRIBES_BLANK_ANSWER if q is None else c.DISAGREES_WITH_QUESTIONNAIRE
        template=c.DISAGREEMENT_WITH_BLANK_ANSWER_TEMPLATE if q is None else c.DISAGREEMENT_TEMPLATE
        out.append(f|dict(stated_weeks=weeks,questionnaire_weeks=q,flag=flag,disagreement_text=template.format(flag=flag,note_id=f['note_id'],stated_weeks=c.DISAGREEMENT_WEEKS_SEPARATOR.join(map(str,weeks)),questionnaire_weeks=q)))
    return out
