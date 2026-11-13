from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from config import config as c

def screen_request(request,policy):
    if request[c.SERVICE_CODE_COLUMN]!=policy['service_code']:
        raise ValueError(c.POLICY_OF_ANOTHER_SERVICE_MESSAGE.format(request_reference=request[c.REQUEST_REFERENCE_COLUMN],service_code=request[c.SERVICE_CODE_COLUMN],document_name=policy['document_name']))
    def val(k):
        x=request.get(k)
        return None if x is None or pd.isna(x) else x
    h,w=val(c.HEIGHT_COLUMN),val(c.WEIGHT_COLUMN)
    bmi=None if h is None or w is None else (Decimal(str(w))/(Decimal(str(h))/Decimal(c.CENTIMETRES_PER_METRE))**2).quantize(c.MEASUREMENT_STEP,rounding=ROUND_HALF_UP)
    def compare(k,n,op):
        v=val(k)
        return None if v is None else op(v,n)
    def atleast(k,n):return compare(k,n,lambda a,b:a>=b)
    def either(*values):return True if True in values else (None if None in values else False)
    conditions=val(c.OTHER_CONDITIONS_COLUMN)
    def listed(names):return None if conditions is None else bool(set(str(conditions).split(c.CONDITION_SEPARATOR))&set(names))
    criteria=[]
    for criterion in policy['criteria']:
        k=criterion['criterion_kind'];r=criterion['rules']
        if k==c.MINIMUM_AGE_CRITERION:result=atleast(c.MEMBER_AGE_COLUMN,r[c.MINIMUM_AGE_RULE])
        elif k==c.CONSERVATIVE_TREATMENT_CRITERION:result=atleast(c.TREATMENT_WEEKS_COLUMN,r[c.MINIMUM_TREATMENT_WEEKS_RULE])
        elif k==c.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION:
            red=val(c.RED_FLAG_COLUMN)
            result=either(atleast(c.TREATMENT_WEEKS_COLUMN,r[c.MINIMUM_TREATMENT_WEEKS_RULE]),None if red is None else red in r[c.LISTED_RED_FLAGS_RULE])
        elif k==c.REPEAT_IMAGING_CRITERION:
            scan=val(c.PREVIOUS_SCAN_COLUMN);months=val(c.MONTHS_SINCE_SCAN_COLUMN);new=val(c.NEW_NEUROLOGICAL_SYMPTOMS_COLUMN)
            result=either(None if scan is None else scan==c.BOOLEAN_NO,None if months is None else months>=r[c.REPEAT_SCAN_MONTHS_RULE],None if new is None else new==c.BOOLEAN_YES)
        elif k==c.RADIOGRAPHIC_SEVERITY_CRITERION:result=atleast(c.XRAY_GRADE_COLUMN,r[c.MINIMUM_XRAY_GRADE_RULE])
        elif k==c.KNEE_FUNCTION_CRITERION:result=compare(c.KNEE_FUNCTION_SCORE_COLUMN,r[c.MAXIMUM_KNEE_FUNCTION_SCORE_RULE],lambda a,b:a<=b)
        elif k==c.BODY_MASS_INDEX_BELOW_CRITERION:result=None if bmi is None else bmi<r[c.BODY_MASS_INDEX_BELOW_RULE]
        elif k==c.BODY_MASS_INDEX_WITH_CONDITION_CRITERION:
            if bmi is None:result=None
            elif bmi>=r[c.MINIMUM_BODY_MASS_INDEX_RULE]:result=True
            elif bmi<r[c.MINIMUM_BODY_MASS_INDEX_WITH_CONDITION_RULE]:result=False
            else:result=listed(r[c.LISTED_CONDITIONS_RULE])
        elif k==c.WEIGHT_PROGRAMME_CRITERION:result=atleast(c.PROGRAMME_MONTHS_COLUMN,r[c.MINIMUM_PROGRAMME_MONTHS_RULE])
        elif k==c.PSYCHOLOGICAL_ASSESSMENT_CRITERION:result=None if val(c.PSYCHOLOGICAL_ASSESSMENT_COLUMN) is None else val(c.PSYCHOLOGICAL_ASSESSMENT_COLUMN)==c.PSYCHOLOGY_COMPLETED
        elif k==c.DAYTIME_SLEEPINESS_CRITERION:result=atleast(c.SLEEPINESS_SCORE_COLUMN,r[c.MINIMUM_SLEEPINESS_SCORE_RULE])
        elif k==c.LABORATORY_NEED_CRITERION:
            home=val(c.HOME_SLEEP_TEST_COLUMN)
            result=either(listed(r[c.LISTED_CONDITIONS_RULE]),None if home is None else home in c.HOME_TESTS_SHOWING_LABORATORY_NEED)
        else:raise ValueError(f"{policy['document_name']}: unknown kind {k}")
        outcome=c.CRITERION_NOT_DOCUMENTED if result is None else c.CRITERION_MET if result else c.CRITERION_NOT_MET
        criteria.append({key:criterion[key] for key in ['criterion_kind','criterion_name','criterion_sentence']}|dict(result=outcome,missing_answers=[key for key in c.CRITERION_ANSWER_COLUMNS[k] if val(key) is None] if result is None else []))
    counts=[sum(x['result']==label for x in criteria) for label in [c.CRITERION_MET,c.CRITERION_NOT_MET,c.CRITERION_NOT_DOCUMENTED]]
    screening=c.DECISION_REFER if counts[1] else c.DECISION_REQUEST_INFORMATION if counts[2] else c.DECISION_APPROVE
    return dict(request_reference=request[c.REQUEST_REFERENCE_COLUMN],service_code=policy['service_code'],policy_document=policy['document_name'],body_mass_index=bmi,criteria=criteria,screening=screening,decisions_open=list(c.DECISIONS_OPEN[screening]),**dict(zip(c.CRITERIA_COUNT_COLUMNS,counts)))
