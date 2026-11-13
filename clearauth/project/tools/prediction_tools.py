import pandas as pd
from config import config as c
from data_pipeline.feature_builder import build_feature_frame

def _check(request,screening):
    if screening['request_reference']!=request[c.REQUEST_REFERENCE_COLUMN]:raise ValueError(c.SCREENING_OF_ANOTHER_REQUEST_MESSAGE.format(screening_reference=screening['request_reference'],request_reference=request[c.REQUEST_REFERENCE_COLUMN]))
def _features(record,names,nums,cats):
    f=build_feature_frame(pd.DataFrame([record]),nums,cats)
    if list(f.columns)!=list(names):raise ValueError(f'feature schema {list(f.columns)} does not match {names}')
    return f
def estimate_approval_likelihood(approval_model,feature_names,request,screening):
    _check(request,screening);record=request|{k:screening[k] for k in c.CRITERIA_COUNT_COLUMNS}
    p=round(float(approval_model.predict_proba(_features(record,feature_names,c.APPROVAL_NUMERIC_FEATURES,c.APPROVAL_CATEGORICAL_FEATURES))[0,1]),c.LIKELIHOOD_DECIMALS)
    return dict(approval_likelihood=p,approval_band=c.HIGH_APPROVAL_BAND if p>=c.HIGH_APPROVAL_MINIMUM else c.MEDIUM_APPROVAL_BAND if p>=c.MEDIUM_APPROVAL_MINIMUM else c.LOW_APPROVAL_BAND)
def estimate_expected_stay(stay_model,feature_names,request,screening):
    _check(request,screening);ref=request[c.REQUEST_REFERENCE_COLUMN];site=request.get(c.SITE_OF_SERVICE_COLUMN)
    if pd.isna(site):raise ValueError(c.NO_SITE_OF_SERVICE_MESSAGE.format(request_reference=ref))
    if site!=c.INPATIENT_SITE:raise ValueError(c.NOT_AN_INPATIENT_OPERATION_MESSAGE.format(request_reference=ref,site_of_service=site))
    conditions=request.get(c.OTHER_CONDITIONS_COLUMN)
    count=diabetes=None
    if pd.notna(conditions):
        values=[] if conditions==c.NO_OTHER_CONDITIONS else conditions.split(c.CONDITION_SEPARATOR)
        count=len(values);diabetes=c.BOOLEAN_YES if c.DIABETES_CONDITION in values else c.BOOLEAN_NO
    record=request|{c.BODY_MASS_INDEX_COLUMN:screening['body_mass_index'],c.COMORBIDITY_COUNT_COLUMN:count,c.DIABETES_RECORDED_COLUMN:diabetes}
    estimate=round(float(stay_model.predict(_features(record,feature_names,c.STAY_NUMERIC_FEATURES,c.STAY_CATEGORICAL_FEATURES))[0]),c.STAY_DECIMALS)
    days=request.get(c.REQUESTED_INPATIENT_DAYS_COLUMN);days=None if pd.isna(days) else int(days)
    return dict(expected_stay_days=estimate,requested_inpatient_days=days,longer_stay_expected=None if days is None else estimate>days+c.LONGER_STAY_MARGIN_DAYS)
def describe_expected_stay(stay,site_of_service):
    if pd.isna(site_of_service):return c.STAY_WITHOUT_SITE_TEXT
    if not stay:return c.STAY_NOT_INPATIENT_TEXT
    t=c.STAY_WITHOUT_REQUESTED_DAYS_TEMPLATE if stay['requested_inpatient_days'] is None else c.LONGER_STAY_TEMPLATE if stay['longer_stay_expected'] else c.NO_LONGER_STAY_TEMPLATE
    return t.format(expected_stay=f"{stay['expected_stay_days']:.{c.STAY_DECIMALS}f}",requested_days=stay['requested_inpatient_days'])
