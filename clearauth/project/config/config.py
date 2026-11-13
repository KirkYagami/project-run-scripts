import os
from decimal import Decimal

RAW_AUTHORISATION_HISTORY_TRAIN_FILE = "data/authorisation_history_train.csv"
RAW_AUTHORISATION_HISTORY_EVAL_FILE = "data/authorisation_history_eval.csv"
RAW_SURGICAL_STAYS_TRAIN_FILE = "data/surgical_stays_train.csv"
RAW_SURGICAL_STAYS_EVAL_FILE = "data/surgical_stays_eval.csv"
RAW_CLINICAL_NOTE_SENTENCES_FILE = "data/clinical_note_sentences.csv"

CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE = "processed/authorisation_history_train_clean.csv"
CLEAN_AUTHORISATION_HISTORY_EVAL_FILE = "processed/authorisation_history_eval_clean.csv"
CLEAN_SURGICAL_STAYS_TRAIN_FILE = "processed/surgical_stays_train_clean.csv"
CLEAN_SURGICAL_STAYS_EVAL_FILE = "processed/surgical_stays_eval_clean.csv"
CLEAN_CLINICAL_NOTE_SENTENCES_FILE = "processed/clinical_note_sentences_clean.csv"

DATA_QUALITY_REPORT_FILE = "output/data_quality_report.json"
TARGET_SHARE_DECIMALS = 4
DATASET_NAME_WIDTH = 32
ROW_COUNT_WIDTH = 6


NULL_TOKENS = ["", "n/a", "na", "-", "unknown", "not recorded"]


BOOLEAN_YES = "Yes"
BOOLEAN_NO = "No"

BOOLEAN_MAPPING = {
    "yes": BOOLEAN_YES,
    "y": BOOLEAN_YES,
    "true": BOOLEAN_YES,
    "no": BOOLEAN_NO,
    "n": BOOLEAN_NO,
    "false": BOOLEAN_NO,
}


CHANNEL_MAPPING = {
    "portal": "Portal",
    "provider portal": "Portal",
    "fax": "Fax",
    "facsimile": "Fax",
    "electronic": "Electronic",
    "edi": "Electronic",
}

URGENCY_MAPPING = {
    "standard": "Standard",
    "routine": "Standard",
    "urgent": "Urgent",
    "expedited": "Urgent",
}

MEMBER_SEX_MAPPING = {
    "female": "Female",
    "f": "Female",
    "male": "Male",
    "m": "Male",
}

NETWORK_STATUS_MAPPING = {
    "in network": "In network",
    "in-network": "In network",
    "out of network": "Out of network",
    "out-of-network": "Out of network",
}

PLAN_CODE_MAPPING = {
    "bw-sel": "BW-SEL",
    "bw-ess": "BW-ESS",
    "bw-sen": "BW-SEN",
    "bw-fam": "BW-FAM",
}

REGION_MAPPING = {
    "northdale": "Northdale",
    "eastmoor": "Eastmoor",
    "southvale": "Southvale",
    "westbridge": "Westbridge",
    "central": "Central",
}

PROVIDER_SPECIALTY_MAPPING = {
    "family medicine": "Family medicine",
    "orthopaedic surgery": "Orthopaedic surgery",
    "neurology": "Neurology",
    "pain medicine": "Pain medicine",
    "physical medicine and rehabilitation": "Physical medicine and rehabilitation",
    "bariatric surgery": "Bariatric surgery",
    "general surgery": "General surgery",
    "sleep medicine": "Sleep medicine",
    "pulmonology": "Pulmonology",
}

SURGICAL_SERVICE_CODE_MAPPING = {
    "ort-tkr": "ORT-TKR",
    "ort tkr": "ORT-TKR",
    "bar-wls": "BAR-WLS",
    "bar wls": "BAR-WLS",
}
SERVICE_CODE_MAPPING = {
    "rad-lsm": "RAD-LSM",
    "rad lsm": "RAD-LSM",
    "rad-csm": "RAD-CSM",
    "rad csm": "RAD-CSM",
    **SURGICAL_SERVICE_CODE_MAPPING,
    "slp-psg": "SLP-PSG",
    "slp psg": "SLP-PSG",
}

SERVICE_NAME_MAPPING = {
    "mri of the lumbar spine": "MRI of the lumbar spine",
    "mri of the cervical spine": "MRI of the cervical spine",
    "total knee replacement": "Total knee replacement",
    "bariatric surgery": "Bariatric surgery",
    "in-laboratory sleep study": "In-laboratory sleep study",
}

SITE_OF_SERVICE_MAPPING = {
    "independent imaging centre": "Independent imaging centre",
    "hospital outpatient department": "Hospital outpatient department",
    "hospital inpatient": "Hospital inpatient",
    "ambulatory surgery centre": "Ambulatory surgery centre",
    "sleep laboratory": "Sleep laboratory",
}

PROCEDURE_DETAIL_MAPPING = {
    "unilateral": "Unilateral",
    "single knee": "Unilateral",
    "bilateral": "Bilateral",
    "both knees": "Bilateral",
    "sleeve gastrectomy": "Sleeve gastrectomy",
    "laparoscopic sleeve gastrectomy": "Sleeve gastrectomy",
    "sleeve": "Sleeve gastrectomy",
    "gastric bypass": "Gastric bypass",
    "roux-en-y gastric bypass": "Gastric bypass",
    "rygb": "Gastric bypass",
}

WEEKDAY_MAPPING = {
    "monday": "Monday",
    "mon": "Monday",
    "tuesday": "Tuesday",
    "tue": "Tuesday",
    "tues": "Tuesday",
    "wednesday": "Wednesday",
    "wed": "Wednesday",
    "thursday": "Thursday",
    "thu": "Thursday",
    "thurs": "Thursday",
    "friday": "Friday",
    "fri": "Friday",
}

SMOKING_STATUS_MAPPING = {
    "never": "Never",
    "never smoked": "Never",
    "non-smoker": "Never",
    "former": "Former",
    "ex-smoker": "Former",
    "quit": "Former",
    "current": "Current",
    "current smoker": "Current",
    "smoker": "Current",
}

RED_FLAG_NAME_MAPPING = {
    "bowel or bladder dysfunction": "Bowel or bladder dysfunction",
    "bladder or bowel dysfunction": "Bowel or bladder dysfunction",
    "saddle anaesthesia": "Saddle anaesthesia",
    "saddle anesthesia": "Saddle anaesthesia",
    "progressive neurological deficit": "Progressive neurological deficit",
    "progressive neuro deficit": "Progressive neurological deficit",
    "suspected malignancy": "Suspected malignancy",
    "suspected cancer": "Suspected malignancy",
    "suspected infection": "Suspected infection",
    "significant trauma": "Significant trauma",
}
NO_RED_FLAG = "No red flag"
RED_FLAG_MAPPING = {
    "no red flag": NO_RED_FLAG,
    "no red flags": NO_RED_FLAG,
    "none": NO_RED_FLAG,
    "none reported": NO_RED_FLAG,
    "nil": NO_RED_FLAG,
    **RED_FLAG_NAME_MAPPING,
}

PSYCHOLOGICAL_ASSESSMENT_MAPPING = {
    "completed": "Completed",
    "yes - completed": "Completed",
    "done": "Completed",
    "not completed": "Not completed",
    "not done": "Not completed",
    "pending": "Not completed",
    "booked": "Not completed",
}

HOME_SLEEP_TEST_MAPPING = {
    "not done": "Not done",
    "not performed": "Not done",
    "none done": "Not done",
    "inconclusive": "Inconclusive",
    "equivocal": "Inconclusive",
    "negative": "Negative",
    "normal": "Negative",
    "positive": "Positive",
    "abnormal": "Positive",
}

REVIEWER_LEVEL_MAPPING = {
    "nurse": "Nurse",
    "nurse reviewer": "Nurse",
    "physician": "Physician",
    "physician reviewer": "Physician",
}

APPROVAL_DECISION_MAPPING = {
    "approved": "Approved",
    "approve": "Approved",
    "denied": "Denied",
    "not approved": "Denied",
}

DISCHARGE_DESTINATION_MAPPING = {
    "home": "Home",
    "home with support": "Home with support",
    "rehabilitation facility": "Rehabilitation facility",
    "rehab facility": "Rehabilitation facility",
}

DOCUMENT_TYPE_MAPPING = {
    "specialist letter": "Specialist letter",
    "family physician letter": "Family physician letter",
    "physiotherapy report": "Physiotherapy report",
    "imaging report": "Imaging report",
    "sleep clinic letter": "Sleep clinic letter",
    "surgical pre-assessment": "Surgical pre-assessment",
    "dietitian report": "Dietitian report",
    "psychology report": "Psychology report",
}

EVIDENCE_TYPE_MAPPING = {
    "conservative treatment": "Conservative treatment",
    "failed medication": "Failed medication",
    "red-flag symptom": "Red-flag symptom",
    "red flag symptom": "Red-flag symptom",
    "functional limitation": "Functional limitation",
    "prior investigation": "Prior investigation",
    "weight-management programme": "Weight-management programme",
    "weight management programme": "Weight-management programme",
    "other condition": "Other condition",
    "ruled out": "Ruled out",
    "background": "Background",
}


CONDITION_MAPPING = {
    "asthma": "Asthma",
    "chronic obstructive pulmonary disease": "Chronic obstructive pulmonary disease",
    "copd": "Chronic obstructive pulmonary disease",
    "depression": "Depression",
    "gastro-oesophageal reflux disease": "Gastro-oesophageal reflux disease",
    "gord": "Gastro-oesophageal reflux disease",
    "gerd": "Gastro-oesophageal reflux disease",
    "reflux disease": "Gastro-oesophageal reflux disease",
    "heart failure": "Heart failure",
    "congestive heart failure": "Heart failure",
    "chf": "Heart failure",
    "hyperlipidaemia": "Hyperlipidaemia",
    "hyperlipidemia": "Hyperlipidaemia",
    "high cholesterol": "Hyperlipidaemia",
    "hypertension": "Hypertension",
    "high blood pressure": "Hypertension",
    "htn": "Hypertension",
    "hypothyroidism": "Hypothyroidism",
    "underactive thyroid": "Hypothyroidism",
    "neuromuscular disease": "Neuromuscular disease",
    "nmd": "Neuromuscular disease",
    "obstructive sleep apnoea": "Obstructive sleep apnoea",
    "obstructive sleep apnea": "Obstructive sleep apnoea",
    "osa": "Obstructive sleep apnoea",
    "osteoarthritis": "Osteoarthritis",
    "oa": "Osteoarthritis",
    "type 2 diabetes": "Type 2 diabetes",
    "type ii diabetes": "Type 2 diabetes",
    "diabetes type 2": "Type 2 diabetes",
    "t2dm": "Type 2 diabetes",
}
NO_OTHER_CONDITIONS = "No other conditions"
NO_OTHER_CONDITIONS_SPELLINGS = ["no other conditions", "no conditions", "none", "nil"]
CONDITION_SEPARATOR = "; "
CONDITION_LIST_SEPARATOR_PATTERN = r"; ?|, | / | and "


MEMBER_NUMBER_PATTERN = r"^(?:BWH-|BWH |BWH|bwh-)?(?P<member_digits>[0-9]{7})$"
CANONICAL_MEMBER_NUMBER_FORMAT = r"BWH-\g<member_digits>"
CANONICAL_MEMBER_NUMBER_PATTERN = r"^BWH-[0-9]{7}$"

DIAGNOSIS_CODE_PATTERN = r"^(?P<category>[A-Z][0-9]{2})\.?(?P<subcategory>[0-9A-Z]{1,4})$"
CANONICAL_DIAGNOSIS_CODE_FORMAT = r"\g<category>.\g<subcategory>"
CANONICAL_DIAGNOSIS_CODE_PATTERN = r"^[A-Z][0-9]{2}\.[0-9A-Z]{1,4}$"

REQUEST_REFERENCE_PATTERN = r"^(?:PA-|pa-|PA |PA)?(?P<reference_digits>[0-9]{6})$"
CANONICAL_REQUEST_REFERENCE_FORMAT = r"PA-\g<reference_digits>"
CANONICAL_REQUEST_REFERENCE_PATTERN = r"^PA-[0-9]{6}$"


CENTIMETRES_PER_INCH = Decimal("2.54")
INCHES_PER_FOOT = 12
CENTIMETRES_PER_METRE = 100
KILOGRAMS_PER_POUND = Decimal("0.45359237")
POUNDS_PER_STONE = 14
MEASUREMENT_STEP = Decimal("0.1")

HEIGHT_NOTATIONS = {
    "feet and inches": r"^(?P<feet>[0-9]) ft (?P<inches>[0-9]|1[01]) in$",
    "metres": r"^(?P<metres>[0-9]\.[0-9]{2}) m$",
    "centimetres": r"^(?P<centimetres>[0-9]{2,3}(?:\.[0-9])?)(?: cm)?$",
}
CENTIMETRES_PER_HEIGHT_UNIT = {
    "feet": INCHES_PER_FOOT * CENTIMETRES_PER_INCH,
    "inches": CENTIMETRES_PER_INCH,
    "metres": Decimal(CENTIMETRES_PER_METRE),
    "centimetres": Decimal(1),
}

WEIGHT_NOTATIONS = {
    "stones and pounds": r"^(?P<stones>[0-9]{1,2}) st (?P<pounds>[0-9]|1[0-3]) lb$",
    "pounds": r"^(?P<pounds>[0-9]{2,3}) lb$",
    "kilograms": r"^(?P<kilograms>[0-9]{2,3}(?:\.[0-9])?)(?: kg)?$",
}
KILOGRAMS_PER_WEIGHT_UNIT = {
    "stones": POUNDS_PER_STONE * KILOGRAMS_PER_POUND,
    "pounds": KILOGRAMS_PER_POUND,
    "kilograms": Decimal(1),
}

DAYS_PER_WEEK = 7
TREATMENT_WEEKS_PART = "weeks"
TREATMENT_DAYS_PART = "days"
TREATMENT_DURATION_PATTERN = (rf"^(?:(?P<{TREATMENT_WEEKS_PART}>[0-9]+)(?: weeks| wks)?"
                              rf"|(?P<{TREATMENT_DAYS_PART}>[0-9]+) days)$")

ASA_CLASS_PATTERN = r"^(?:ASA )?([IV]+|[0-9]+)$"
ASA_CLASS_NUMBERS = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}


XRAY_GRADE_MAXIMUM = 4
KNEE_FUNCTION_SCORE_MAXIMUM = 48
SLEEPINESS_SCORE_MAXIMUM = 24
PERCENTAGE_MAXIMUM = 100
TURNAROUND_DAYS_MINIMUM = 0
BODY_MASS_INDEX_MINIMUM = 10
BODY_MASS_INDEX_MAXIMUM = 100
STAY_NIGHTS_MINIMUM = 1

PLAIN_NUMBER_PATTERN = r"^-?[0-9]+(?:\.[0-9]+)?$"
WHOLE_NUMBER_PATTERN = r"^([0-9]+)$"
POSITIVE_WHOLE_NUMBER_PATTERN = r"^([1-9][0-9]*)$"
PERCENTAGE_PATTERN = r"^([0-9]+(?:\.[0-9])?)(?: ?%)?$"
TURNAROUND_DAYS_PATTERN = r"^(-?[0-9]+)(?: days)?$"
INPATIENT_DAYS_PATTERN = r"^([0-9]+)(?: days| nights)?$"
STAY_NIGHTS_PATTERN = r"^(-?[0-9]+)(?: days| nights)?$"
MONTHS_COUNT_PATTERN = r"^([0-9]+)(?: months| mo)?$"
XRAY_GRADE_PATTERN = r"^(?:KL grade |KL |Grade )?([0-9]+)$"
KNEE_FUNCTION_SCORE_PATTERN = rf"^([0-9]+)(?:/{KNEE_FUNCTION_SCORE_MAXIMUM})?$"
SLEEPINESS_SCORE_PATTERN = rf"^([0-9]+)(?:/{SLEEPINESS_SCORE_MAXIMUM})?$"
BODY_MASS_INDEX_PATTERN = r"^([0-9]+(?:\.[0-9])?)(?: kg/m2)?$"


MARKUP_PATTERN = r"</?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?/?>"
ENCODING_ARTIFACT_PATTERN = r"&[#a-z0-9]+;|\xa0"
WHITESPACE_RUN_PATTERN = r"[\s\xa0]+"
MINIMUM_SENTENCE_WORDS = 3


REQUEST_REFERENCE_COLUMN = "request_reference"
SUBMISSION_SEQUENCE_COLUMN = "submission_sequence"
MEMBER_NUMBER_COLUMN = "member_number"
DIAGNOSIS_CODE_COLUMN = "diagnosis_code"
ASA_CLASS_COLUMN = "asa_physical_status"
TREATMENT_WEEKS_COLUMN = "conservative_treatment_weeks"
HEIGHT_COLUMN = "height_cm"
WEIGHT_COLUMN = "weight_kg"
OTHER_CONDITIONS_COLUMN = "other_conditions"
REQUEST_NAME_COLUMNS = ["provider_name", "planned_facility_name"]

REQUEST_VALUE_MAPPINGS = {
    "received_channel": CHANNEL_MAPPING,
    "urgency": URGENCY_MAPPING,
    "member_sex": MEMBER_SEX_MAPPING,
    "member_region": REGION_MAPPING,
    "plan_code": PLAN_CODE_MAPPING,
    "provider_specialty": PROVIDER_SPECIALTY_MAPPING,
    "provider_network_status": NETWORK_STATUS_MAPPING,
    "service_code": SERVICE_CODE_MAPPING,
    "service_name": SERVICE_NAME_MAPPING,
    "site_of_service": SITE_OF_SERVICE_MAPPING,
    "procedure_detail": PROCEDURE_DETAIL_MAPPING,
    "enhanced_recovery_programme": BOOLEAN_MAPPING,
    "surgery_weekday": WEEKDAY_MAPPING,
    "smoking_status": SMOKING_STATUS_MAPPING,
    "red_flag_symptom": RED_FLAG_MAPPING,
    "previous_scan_of_region": BOOLEAN_MAPPING,
    "new_neurological_symptoms": BOOLEAN_MAPPING,
    "psychological_assessment": PSYCHOLOGICAL_ASSESSMENT_MAPPING,
    "home_sleep_test_result": HOME_SLEEP_TEST_MAPPING,
}

REQUEST_WHOLE_NUMBER_PATTERNS = {
    "submission_sequence": POSITIVE_WHOLE_NUMBER_PATTERN,
    "member_age": WHOLE_NUMBER_PATTERN,
    "requested_inpatient_days": INPATIENT_DAYS_PATTERN,
    "supporting_document_count": WHOLE_NUMBER_PATTERN,
    "months_since_last_scan": MONTHS_COUNT_PATTERN,
    "xray_grade": XRAY_GRADE_PATTERN,
    "knee_function_score": KNEE_FUNCTION_SCORE_PATTERN,
    "weight_programme_months": MONTHS_COUNT_PATTERN,
    "sleepiness_score": SLEEPINESS_SCORE_PATTERN,
}

REQUEST_DECIMAL_NUMBER_PATTERNS = {
    "provider_prior_approval_rate_pct": PERCENTAGE_PATTERN,
}

REQUEST_MAXIMUM_VALUES = {
    "provider_prior_approval_rate_pct": PERCENTAGE_MAXIMUM,
    "xray_grade": XRAY_GRADE_MAXIMUM,
    "knee_function_score": KNEE_FUNCTION_SCORE_MAXIMUM,
    "sleepiness_score": SLEEPINESS_SCORE_MAXIMUM,
}


HISTORY_TARGET_COLUMN = "approval_decision"

HISTORY_VALUE_MAPPINGS = {
    **REQUEST_VALUE_MAPPINGS,
    "information_requested": BOOLEAN_MAPPING,
    "reviewer_level": REVIEWER_LEVEL_MAPPING,
    "approval_decision": APPROVAL_DECISION_MAPPING,
}

HISTORY_WHOLE_NUMBER_PATTERNS = {
    **REQUEST_WHOLE_NUMBER_PATTERNS,
    "decision_turnaround_days": TURNAROUND_DAYS_PATTERN,
}

HISTORY_MINIMUM_VALUES = {
    "decision_turnaround_days": TURNAROUND_DAYS_MINIMUM,
}


STAY_TARGET_COLUMN = "length_of_stay_days"
ADMISSION_REFERENCE_COLUMN = "admission_reference"
STAY_NAME_COLUMNS = ["hospital_name"]

STAY_VALUE_MAPPINGS = {
    "member_sex": MEMBER_SEX_MAPPING,
    "member_region": REGION_MAPPING,
    "plan_code": PLAN_CODE_MAPPING,
    "service_code": SURGICAL_SERVICE_CODE_MAPPING,
    "procedure_detail": PROCEDURE_DETAIL_MAPPING,
    "diabetes_recorded": BOOLEAN_MAPPING,
    "smoking_status": SMOKING_STATUS_MAPPING,
    "enhanced_recovery_programme": BOOLEAN_MAPPING,
    "surgery_weekday": WEEKDAY_MAPPING,
    "complication_recorded": BOOLEAN_MAPPING,
    "discharge_destination": DISCHARGE_DESTINATION_MAPPING,
    "readmission_recorded": BOOLEAN_MAPPING,
}

STAY_WHOLE_NUMBER_PATTERNS = {
    "member_age": WHOLE_NUMBER_PATTERN,
    "comorbidity_count": WHOLE_NUMBER_PATTERN,
    "length_of_stay_days": STAY_NIGHTS_PATTERN,
}

STAY_DECIMAL_NUMBER_PATTERNS = {
    "body_mass_index": BODY_MASS_INDEX_PATTERN,
}

STAY_MINIMUM_VALUES = {
    "body_mass_index": BODY_MASS_INDEX_MINIMUM,
    "length_of_stay_days": STAY_NIGHTS_MINIMUM,
}

STAY_MAXIMUM_VALUES = {
    "body_mass_index": BODY_MASS_INDEX_MAXIMUM,
}


SENTENCE_TARGET_COLUMN = "evidence_type"
SENTENCE_ID_COLUMN = "sentence_id"
SENTENCE_TEXT_COLUMN = "sentence_text"
SENTENCE_LENGTH_COLUMN = "sentence_length_characters"

SENTENCE_VALUE_MAPPINGS = {
    "service_code": SERVICE_CODE_MAPPING,
    "source_document_type": DOCUMENT_TYPE_MAPPING,
    "evidence_type": EVIDENCE_TYPE_MAPPING,
}

SENTENCE_WHOLE_NUMBER_PATTERNS = {
    "sentence_number": POSITIVE_WHOLE_NUMBER_PATTERN,
}


DOCS_DIRECTORY = "data/docs"
PDF_FILE_SUFFIX = ".pdf"

DATABASE_DIRECTORY = "database"
VECTOR_STORE_DIRECTORY = f"{DATABASE_DIRECTORY}/chroma_store"
VECTOR_STORE_FILE_NAME = "chroma.sqlite3"
VECTOR_COLLECTION_NAME = "authorisation_documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"
VECTOR_DISTANCE_METRIC = "cosine"
CHUNK_SIZE_CHARACTERS = 700
CHUNK_OVERLAP_CHARACTERS = 120
DOCUMENT_HEADER_PATTERN = (r"Document\s+[A-Za-z0-9 ]+\|\s*Issue\s*[0-9]+"
                           r".*?Review cycle:\s*[A-Za-z ]+")
SECTION_HEADING_PATTERN = r"(?m)^([0-9]{1,2})\. [A-Z]"
SENTENCE_BOUNDARY_PATTERN = r"(?<=[.:;])(?<![0-9]\.)\s+"
INDEX_HOLDS_NO_CHUNKS_MESSAGE = "The index holds no chunks of {document_name}"
DOCUMENTATION_QUESTION = "What documentation should the requesting office send with the request?"
DOCUMENTATION_SECTION_HEADING = "6. Documentation to send"

SERVICE_POLICY_DOCUMENTS = {
    "RAD-LSM": "Medical-Policy-Lumbar-Spine-MRI.pdf",
    "RAD-CSM": "Medical-Policy-Cervical-Spine-MRI.pdf",
    "ORT-TKR": "Medical-Policy-Total-Knee-Replacement.pdf",
    "BAR-WLS": "Medical-Policy-Bariatric-Surgery.pdf",
    "SLP-PSG": "Medical-Policy-In-Laboratory-Sleep-Study.pdf",
}
NO_POLICY_CONFIGURED_MESSAGE = "No medical policy is configured for {service_code}"
NO_SERVICE_CODE_MESSAGE = ("Request {request_reference} gives no service code, so it cannot be "
                           "screened")
POLICY_OF_ANOTHER_SERVICE_MESSAGE = ("Request {request_reference} is for {service_code}, so "
                                     "{document_name} does not apply to it")
POLICY_SERVICE_CODE_PATTERN = r"service code ([A-Z]{3}-[A-Z]{3})\b"

CRITERIA_SECTION_PATTERN = (r"4\. Coverage criteria (.+?) A criterion is never met by a figure in "
                            r"a letter, and never waived except as it says itself\. "
                            r"5\. Reading the criteria")
CRITERION_NUMBER_PATTERN = r"(?:^|(?<=[:.]) )([1-9]) (?=[A-Z])"
CRITERION_NAME_PART = "criterion_name"
CRITERION_SENTENCE_PART = "criterion_sentence"
CRITERION_NAME_PATTERN = rf"(?P<{CRITERION_NAME_PART}>[A-Z][A-Za-z-]*(?: [A-Za-z-]+)*)\. "

MINIMUM_AGE_CRITERION = "minimum_age"
CONSERVATIVE_TREATMENT_CRITERION = "conservative_treatment"
CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION = "conservative_treatment_or_red_flag"
REPEAT_IMAGING_CRITERION = "repeat_imaging"
RADIOGRAPHIC_SEVERITY_CRITERION = "radiographic_severity"
KNEE_FUNCTION_CRITERION = "knee_function"
BODY_MASS_INDEX_BELOW_CRITERION = "body_mass_index_below"
BODY_MASS_INDEX_WITH_CONDITION_CRITERION = "body_mass_index_with_condition"
WEIGHT_PROGRAMME_CRITERION = "weight_management_programme"
PSYCHOLOGICAL_ASSESSMENT_CRITERION = "psychological_assessment"
DAYTIME_SLEEPINESS_CRITERION = "daytime_sleepiness"
LABORATORY_NEED_CRITERION = "laboratory_need"

MINIMUM_AGE_RULE = "minimum_age"
MINIMUM_TREATMENT_WEEKS_RULE = "minimum_treatment_weeks"
LISTED_RED_FLAGS_RULE = "listed_red_flags"
REPEAT_SCAN_MONTHS_RULE = "repeat_scan_months"
MINIMUM_XRAY_GRADE_RULE = "minimum_xray_grade"
MAXIMUM_KNEE_FUNCTION_SCORE_RULE = "maximum_knee_function_score"
BODY_MASS_INDEX_BELOW_RULE = "body_mass_index_below"
MINIMUM_BODY_MASS_INDEX_RULE = "minimum_body_mass_index"
MINIMUM_BODY_MASS_INDEX_WITH_CONDITION_RULE = "minimum_body_mass_index_with_listed_condition"
LISTED_CONDITIONS_RULE = "listed_conditions"
MINIMUM_PROGRAMME_MONTHS_RULE = "minimum_programme_months"
MINIMUM_SLEEPINESS_SCORE_RULE = "minimum_sleepiness_score"

CRITERION_SENTENCE_PATTERNS = {
    MINIMUM_AGE_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The member is aged (?P<{MINIMUM_AGE_RULE}>[0-9]+) years or over\.)"),
    CONSERVATIVE_TREATMENT_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The member has completed at least (?P<{MINIMUM_TREATMENT_WEEKS_RULE}>[0-9]+) "
        r"whole weeks of conservative treatment\.)"),
    CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The member has completed at least (?P<{MINIMUM_TREATMENT_WEEKS_RULE}>[0-9]+) "
        r"whole weeks of conservative treatment, or a red flag symptom is reported\.)"),
    REPEAT_IMAGING_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"A scan of the same region less than (?P<{REPEAT_SCAN_MONTHS_RULE}>[0-9]+) months ago "
        r"is repeated only when new neurological symptoms are reported\.)"),
    RADIOGRAPHIC_SEVERITY_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        r"A weight-bearing X-ray shows Kellgren-Lawrence grade "
        rf"(?P<{MINIMUM_XRAY_GRADE_RULE}>[0-9]) or higher\.)"),
    KNEE_FUNCTION_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The Oxford Knee Score is (?P<{MAXIMUM_KNEE_FUNCTION_SCORE_RULE}>[0-9]+) or lower\.)"),
    BODY_MASS_INDEX_BELOW_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The body mass index is below (?P<{BODY_MASS_INDEX_BELOW_RULE}>[0-9]+\.[0-9])\.)"),
    BODY_MASS_INDEX_WITH_CONDITION_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The body mass index is (?P<{MINIMUM_BODY_MASS_INDEX_RULE}>[0-9]+\.[0-9]) or higher, "
        rf"or (?P<{MINIMUM_BODY_MASS_INDEX_WITH_CONDITION_RULE}>[0-9]+\.[0-9]) or higher "
        r"with a listed condition\. "
        rf"The listed conditions are (?P<{LISTED_CONDITIONS_RULE}>[a-z0-9 ,-]+?)\.)"),
    WEIGHT_PROGRAMME_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        rf"The member has spent at least (?P<{MINIMUM_PROGRAMME_MONTHS_RULE}>[0-9]+) months "
        r"in a supervised weight-management programme\.)"),
    PSYCHOLOGICAL_ASSESSMENT_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        r"A pre-operative psychological assessment has been completed\.)"),
    DAYTIME_SLEEPINESS_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        r"The Epworth Sleepiness Scale score is "
        rf"(?P<{MINIMUM_SLEEPINESS_SCORE_RULE}>[0-9]+) or higher\.)"),
    LABORATORY_NEED_CRITERION: (
        CRITERION_NAME_PATTERN + rf"(?P<{CRITERION_SENTENCE_PART}>"
        r"A laboratory study is needed because the member has a listed condition "
        r"or a home sleep apnoea test was inconclusive or negative\. "
        rf"The listed conditions are (?P<{LISTED_CONDITIONS_RULE}>[a-z0-9 ,-]+?)\.)"),
}

WHOLE_NUMBER_RULES = [MINIMUM_AGE_RULE, MINIMUM_TREATMENT_WEEKS_RULE, REPEAT_SCAN_MONTHS_RULE,
                      MINIMUM_XRAY_GRADE_RULE, MAXIMUM_KNEE_FUNCTION_SCORE_RULE,
                      MINIMUM_PROGRAMME_MONTHS_RULE, MINIMUM_SLEEPINESS_SCORE_RULE]
BODY_MASS_INDEX_RULES = [BODY_MASS_INDEX_BELOW_RULE, MINIMUM_BODY_MASS_INDEX_RULE,
                         MINIMUM_BODY_MASS_INDEX_WITH_CONDITION_RULE]
RED_FLAG_LIST_PATTERN = r"A red flag symptom is one of ([a-z]+): ([a-z ,]+)\."
LISTED_NAME_MAPPINGS = {
    LISTED_CONDITIONS_RULE: CONDITION_MAPPING,
    LISTED_RED_FLAGS_RULE: RED_FLAG_NAME_MAPPING,
}
LISTED_NAME_SEPARATOR_PATTERN = r", | (?:and|or) (?!.*, )"


CRITERION_MET = "Met"
CRITERION_NOT_MET = "Not met"
CRITERION_NOT_DOCUMENTED = "Not documented"

DECISION_APPROVE = "APPROVE"
DECISION_REQUEST_INFORMATION = "REQUEST MORE INFORMATION"
DECISION_REFER = "REFER TO PHYSICIAN"
DECISIONS_OPEN = {
    DECISION_APPROVE: [DECISION_APPROVE, DECISION_REFER],
    DECISION_REQUEST_INFORMATION: [DECISION_REQUEST_INFORMATION, DECISION_REFER],
    DECISION_REFER: [DECISION_REFER],
}

PSYCHOLOGY_COMPLETED = PSYCHOLOGICAL_ASSESSMENT_MAPPING["completed"]
HOME_TESTS_SHOWING_LABORATORY_NEED = [HOME_SLEEP_TEST_MAPPING["inconclusive"],
                                      HOME_SLEEP_TEST_MAPPING["negative"]]

SERVICE_CODE_COLUMN = "service_code"
MEMBER_AGE_COLUMN = "member_age"
RED_FLAG_COLUMN = "red_flag_symptom"
PREVIOUS_SCAN_COLUMN = "previous_scan_of_region"
MONTHS_SINCE_SCAN_COLUMN = "months_since_last_scan"
NEW_NEUROLOGICAL_SYMPTOMS_COLUMN = "new_neurological_symptoms"
XRAY_GRADE_COLUMN = "xray_grade"
KNEE_FUNCTION_SCORE_COLUMN = "knee_function_score"
PROGRAMME_MONTHS_COLUMN = "weight_programme_months"
PSYCHOLOGICAL_ASSESSMENT_COLUMN = "psychological_assessment"
SLEEPINESS_SCORE_COLUMN = "sleepiness_score"
HOME_SLEEP_TEST_COLUMN = "home_sleep_test_result"
SCREENING_ANSWER_COLUMNS = [MEMBER_AGE_COLUMN, TREATMENT_WEEKS_COLUMN, RED_FLAG_COLUMN,
                            PREVIOUS_SCAN_COLUMN, MONTHS_SINCE_SCAN_COLUMN,
                            NEW_NEUROLOGICAL_SYMPTOMS_COLUMN, XRAY_GRADE_COLUMN,
                            KNEE_FUNCTION_SCORE_COLUMN, HEIGHT_COLUMN, WEIGHT_COLUMN,
                            OTHER_CONDITIONS_COLUMN, PROGRAMME_MONTHS_COLUMN,
                            PSYCHOLOGICAL_ASSESSMENT_COLUMN, SLEEPINESS_SCORE_COLUMN,
                            HOME_SLEEP_TEST_COLUMN]

CRITERIA_MET_COUNT_COLUMN = "criteria_met_count"
CRITERIA_NOT_MET_COUNT_COLUMN = "criteria_not_met_count"
CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN = "criteria_not_documented_count"
CRITERIA_COUNT_COLUMNS = [CRITERIA_MET_COUNT_COLUMN, CRITERIA_NOT_MET_COUNT_COLUMN,
                          CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN]


RANDOM_SEED = 42
SENTENCE_HELD_OUT_SHARE = 0.2
METRIC_DECIMALS = 4
JSON_INDENT = 2
MODEL_FILE_COMPRESSION = 3
MODEL_STEP_NAME = "estimator"
NUMBER_FILL_STRATEGY = "median"
CATEGORY_FILL_STRATEGY = "most_frequent"
APPROVAL_FOREST_TREES = 200
APPROVAL_FOREST_LEAF_MINIMUM = 30
APPROVAL_FOREST_FEATURE_SHARE = 0.5
STAY_FOREST_TREES = 200
STAY_FOREST_LEAF_MINIMUM = 20
EVIDENCE_MODEL_MAXIMUM_ITERATIONS = 1000

APPROVAL_MODEL_FILE = "output/models/approval_model.pkl"
STAY_MODEL_FILE = "output/models/stay_model.pkl"
EVIDENCE_MODEL_FILE = "output/models/evidence_model.pkl"
APPROVAL_SCHEMA_FILE = "output/models/approval_features.json"
STAY_SCHEMA_FILE = "output/models/stay_features.json"
MODEL_METRICS_FILE = "output/model_metrics.json"

APPROVAL_TARGET_ENCODING = {
    APPROVAL_DECISION_MAPPING["approved"]: 1,
    APPROVAL_DECISION_MAPPING["denied"]: 0,
}

APPROVAL_NUMERIC_FEATURES = [
    "member_age", "provider_prior_approval_rate_pct", "supporting_document_count",
    CRITERIA_MET_COUNT_COLUMN, CRITERIA_NOT_MET_COUNT_COLUMN, CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN,
]

APPROVAL_CATEGORICAL_FEATURES = [
    "service_code", "received_channel", "urgency", "provider_specialty", "provider_network_status",
    "site_of_service",
]

STAY_NUMERIC_FEATURES = [
    "member_age", "asa_physical_status", "body_mass_index", "comorbidity_count",
]

STAY_CATEGORICAL_FEATURES = [
    "procedure_detail", "diabetes_recorded", "smoking_status", "enhanced_recovery_programme",
    "surgery_weekday",
]

MINIMUM_APPROVAL_ROC_AUC = 0.89
MINIMUM_STAY_R2 = 0.65
MINIMUM_EVIDENCE_MACRO_F1 = 0.90


OPEN_REQUESTS_FILE = "data/input/open_requests.csv"
REQUEST_NOTES_FILE = "data/input/request_notes.csv"

NOTE_ID_COLUMN = "note_id"
NOTE_NUMBER_COLUMN = "note_number"
NOTE_AUTHOR_ROLE_COLUMN = "note_author_role"
NOTE_TEXT_COLUMN = "note_text"
NOTE_VALUE_MAPPINGS = {NOTE_AUTHOR_ROLE_COLUMN: DOCUMENT_TYPE_MAPPING}
NOTE_WHOLE_NUMBER_PATTERNS = {NOTE_NUMBER_COLUMN: POSITIVE_WHOLE_NUMBER_PATTERN}
SUPPORTING_DOCUMENT_COUNT_COLUMN = "supporting_document_count"
URGENCY_COLUMN = "urgency"
URGENT = URGENCY_MAPPING["urgent"]
UNKNOWN_REQUEST_MESSAGE = "No open request has the reference {request_reference}"

CRITERION_ANSWER_COLUMNS = {
    MINIMUM_AGE_CRITERION: [MEMBER_AGE_COLUMN],
    CONSERVATIVE_TREATMENT_CRITERION: [TREATMENT_WEEKS_COLUMN],
    CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION: [TREATMENT_WEEKS_COLUMN, RED_FLAG_COLUMN],
    REPEAT_IMAGING_CRITERION: [PREVIOUS_SCAN_COLUMN, MONTHS_SINCE_SCAN_COLUMN,
                               NEW_NEUROLOGICAL_SYMPTOMS_COLUMN],
    RADIOGRAPHIC_SEVERITY_CRITERION: [XRAY_GRADE_COLUMN],
    KNEE_FUNCTION_CRITERION: [KNEE_FUNCTION_SCORE_COLUMN],
    BODY_MASS_INDEX_BELOW_CRITERION: [HEIGHT_COLUMN, WEIGHT_COLUMN],
    BODY_MASS_INDEX_WITH_CONDITION_CRITERION: [HEIGHT_COLUMN, WEIGHT_COLUMN,
                                               OTHER_CONDITIONS_COLUMN],
    WEIGHT_PROGRAMME_CRITERION: [PROGRAMME_MONTHS_COLUMN],
    PSYCHOLOGICAL_ASSESSMENT_CRITERION: [PSYCHOLOGICAL_ASSESSMENT_COLUMN],
    DAYTIME_SLEEPINESS_CRITERION: [SLEEPINESS_SCORE_COLUMN],
    LABORATORY_NEED_CRITERION: [OTHER_CONDITIONS_COLUMN, HOME_SLEEP_TEST_COLUMN],
}

DOCUMENT_SENTENCE_PATTERN = r"(?<=[.!?])\s+(?=[A-Za-z0-9])"
CONSERVATIVE_TREATMENT_EVIDENCE = EVIDENCE_TYPE_MAPPING["conservative treatment"]
STATED_WEEKS_PATTERN = r"\b([0-9]+(?:\.[0-9]+)?|(?:[a-z]+[- ])?[a-z]+)[- ]weeks?\b(?! ago\b)"
NUMBER_WORD_SEPARATOR_PATTERN = r"[- ]"
NUMBER_WORD_VALUES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
TENS_WORDS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
UNIT_WORDS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
DISAGREES_WITH_QUESTIONNAIRE = "The document gives other weeks of treatment than the questionnaire"
DESCRIBES_BLANK_ANSWER = "The document gives weeks of treatment the questionnaire left blank"
DISAGREEMENT_TEMPLATE = ("{flag}: {note_id} gives {stated_weeks} weeks, the questionnaire "
                         "{questionnaire_weeks}.")
DISAGREEMENT_WITH_BLANK_ANSWER_TEMPLATE = "{flag}: {note_id} gives {stated_weeks} weeks."
DISAGREEMENT_WEEKS_SEPARATOR = ", "

SCREENING_OF_ANOTHER_REQUEST_MESSAGE = ("The screening of {screening_reference} cannot be used "
                                        "for request {request_reference}")
LIKELIHOOD_DECIMALS = 4
HIGH_APPROVAL_MINIMUM = 0.80
MEDIUM_APPROVAL_MINIMUM = 0.50
HIGH_APPROVAL_BAND = "HIGH"
MEDIUM_APPROVAL_BAND = "MEDIUM"
LOW_APPROVAL_BAND = "LOW"

SITE_OF_SERVICE_COLUMN = "site_of_service"
INPATIENT_SITE = SITE_OF_SERVICE_MAPPING["hospital inpatient"]
REQUESTED_INPATIENT_DAYS_COLUMN = "requested_inpatient_days"
BODY_MASS_INDEX_COLUMN = "body_mass_index"
COMORBIDITY_COUNT_COLUMN = "comorbidity_count"
DIABETES_RECORDED_COLUMN = "diabetes_recorded"
DIABETES_CONDITION = CONDITION_MAPPING["type 2 diabetes"]
STAY_DECIMALS = 1
LONGER_STAY_MARGIN_DAYS = 1
NOT_AN_INPATIENT_OPERATION_MESSAGE = ("Request {request_reference} is for {site_of_service}, "
                                      "not an inpatient operation")
NO_SITE_OF_SERVICE_MESSAGE = "Request {request_reference} gives no site of service"
STAY_WITHOUT_SITE_TEXT = "not worked out, as the request gives no site of service"
STAY_NOT_INPATIENT_TEXT = "not worked out, as this is not an inpatient operation"
STAY_WITHOUT_REQUESTED_DAYS_TEMPLATE = ("{expected_stay} days; the request does not give the "
                                        "inpatient days requested, so no longer stay is noted")
LONGER_STAY_TEMPLATE = ("{expected_stay} days against {requested_days} requested: a longer stay "
                        "is expected")
NO_LONGER_STAY_TEMPLATE = ("{expected_stay} days against {requested_days} requested: a longer stay "
                           "is not expected")

EVIDENCE_GUIDE_DOCUMENTS = {
    EVIDENCE_TYPE_MAPPING["conservative treatment"]: "Evidence-Guide-Conservative-Treatment.pdf",
    EVIDENCE_TYPE_MAPPING["failed medication"]: "Evidence-Guide-Failed-Medication.pdf",
    EVIDENCE_TYPE_MAPPING["red-flag symptom"]: "Evidence-Guide-Red-Flag-Symptom.pdf",
    EVIDENCE_TYPE_MAPPING["functional limitation"]: "Evidence-Guide-Functional-Limitation.pdf",
    EVIDENCE_TYPE_MAPPING["prior investigation"]: "Evidence-Guide-Prior-Investigation.pdf",
    EVIDENCE_TYPE_MAPPING["weight-management programme"]:
        "Evidence-Guide-Weight-Management-Programme.pdf",
    EVIDENCE_TYPE_MAPPING["other condition"]: "Evidence-Guide-Other-Condition.pdf",
    EVIDENCE_TYPE_MAPPING["ruled out"]: "Evidence-Guide-Ruled-Out.pdf",
}
NO_EVIDENCE_GUIDE_MESSAGE = "No evidence guide is configured for {evidence_type}"
EVIDENCE_CRITERION_KINDS = {
    EVIDENCE_TYPE_MAPPING["conservative treatment"]: [CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION,
                                                      CONSERVATIVE_TREATMENT_CRITERION],
    EVIDENCE_TYPE_MAPPING["failed medication"]: [CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION,
                                                 CONSERVATIVE_TREATMENT_CRITERION,
                                                 WEIGHT_PROGRAMME_CRITERION],
    EVIDENCE_TYPE_MAPPING["red-flag symptom"]: [CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION],
    EVIDENCE_TYPE_MAPPING["functional limitation"]: [KNEE_FUNCTION_CRITERION,
                                                     DAYTIME_SLEEPINESS_CRITERION],
    EVIDENCE_TYPE_MAPPING["prior investigation"]: [REPEAT_IMAGING_CRITERION,
                                                   RADIOGRAPHIC_SEVERITY_CRITERION,
                                                   PSYCHOLOGICAL_ASSESSMENT_CRITERION,
                                                   LABORATORY_NEED_CRITERION],
    EVIDENCE_TYPE_MAPPING["weight-management programme"]: [WEIGHT_PROGRAMME_CRITERION],
    EVIDENCE_TYPE_MAPPING["other condition"]: [BODY_MASS_INDEX_WITH_CONDITION_CRITERION,
                                               LABORATORY_NEED_CRITERION],
    EVIDENCE_TYPE_MAPPING["ruled out"]: [CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION,
                                         LABORATORY_NEED_CRITERION],
    EVIDENCE_TYPE_MAPPING["background"]: [],
}
NO_EVIDENCE_CRITERIA_MESSAGE = "No criteria are configured for the evidence type {evidence_type}"
REVIEWER_CHECKS_QUESTION = "Which checks does the reviewer make, in order?"
REVIEWER_CHECKS_SECTION_HEADING = "3. What the reviewer checks"
OFFICE_MESSAGE_QUESTION = "What should the requesting office be told?"
OFFICE_MESSAGE_SECTION_HEADING = "6. What to tell the requesting office"
PASSAGE_OF_ANOTHER_SECTION_MESSAGE = ("The passage {document_name} gives for \"{question}\" is "
                                      "not its \"{section_heading}\" section")


ORGANISATION_NAME = "Brightwater Health Plan"
NOT_GIVEN_TEXT = "not given"

SERVICE_NAMES = {
    "RAD-LSM": SERVICE_NAME_MAPPING["mri of the lumbar spine"],
    "RAD-CSM": SERVICE_NAME_MAPPING["mri of the cervical spine"],
    "ORT-TKR": SERVICE_NAME_MAPPING["total knee replacement"],
    "BAR-WLS": SERVICE_NAME_MAPPING["bariatric surgery"],
    "SLP-PSG": SERVICE_NAME_MAPPING["in-laboratory sleep study"],
}
PROVIDER_NAME_COLUMN = "provider_name"
PROVIDER_SPECIALTY_COLUMN = "provider_specialty"
NETWORK_STATUS_COLUMN = "provider_network_status"
RECEIVED_CHANNEL_COLUMN = "received_channel"
PROCEDURE_DETAIL_COLUMN = "procedure_detail"
PLANNED_FACILITY_COLUMN = "planned_facility_name"

QUESTIONNAIRE_ANSWER_LABELS = {
    MEMBER_AGE_COLUMN: "the member's age in years",
    TREATMENT_WEEKS_COLUMN: "the length of conservative treatment, in whole weeks",
    RED_FLAG_COLUMN: "the red flag symptom reported, or that there is none",
    PREVIOUS_SCAN_COLUMN: "whether the same region has been scanned before",
    MONTHS_SINCE_SCAN_COLUMN: "how many whole months ago that scan was done",
    NEW_NEUROLOGICAL_SYMPTOMS_COLUMN: "whether there are new neurological symptoms since that scan",
    XRAY_GRADE_COLUMN: "the Kellgren-Lawrence grade of the knee on X-ray",
    KNEE_FUNCTION_SCORE_COLUMN: "the Oxford Knee Score",
    HEIGHT_COLUMN: "the member's height, in centimetres",
    WEIGHT_COLUMN: "the member's weight, in kilograms",
    OTHER_CONDITIONS_COLUMN: "every long-term condition the member has, or that there is none",
    PROGRAMME_MONTHS_COLUMN: "the whole months of the supervised weight-management programme",
    PSYCHOLOGICAL_ASSESSMENT_COLUMN: ("whether the pre-operative psychological assessment is "
                                      "completed"),
    SLEEPINESS_SCORE_COLUMN: "the Epworth Sleepiness Scale score",
    HOME_SLEEP_TEST_COLUMN: "the result of any home sleep apnoea test, or that none was done",
}
APPROVAL_INPUT_LABELS = {
    MEMBER_AGE_COLUMN: "the member's age",
    "provider_prior_approval_rate_pct": "the practice's prior approval rate, in percent",
    SUPPORTING_DOCUMENT_COUNT_COLUMN: "documents sent",
    CRITERIA_MET_COUNT_COLUMN: "criteria Met",
    CRITERIA_NOT_MET_COUNT_COLUMN: "criteria Not met",
    CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN: "criteria Not documented",
    SERVICE_CODE_COLUMN: "service",
    RECEIVED_CHANNEL_COLUMN: "channel",
    URGENCY_COLUMN: "urgency",
    PROVIDER_SPECIALTY_COLUMN: "the practice's specialty",
    NETWORK_STATUS_COLUMN: "network status",
    SITE_OF_SERVICE_COLUMN: "site of service",
}
STAY_INPUT_LABELS = {
    MEMBER_AGE_COLUMN: "the member's age",
    ASA_CLASS_COLUMN: "ASA physical status class",
    BODY_MASS_INDEX_COLUMN: "body mass index",
    OTHER_CONDITIONS_COLUMN: "other long-term conditions",
    PROCEDURE_DETAIL_COLUMN: "operation",
    "smoking_status": "smoking status",
    "enhanced_recovery_programme": "enhanced recovery programme at the planned hospital",
    "surgery_weekday": "planned weekday",
}

DECISIONS = [DECISION_APPROVE, DECISION_REQUEST_INFORMATION, DECISION_REFER]
DECISION_DESCRIPTIONS = {
    DECISION_APPROVE: ("the request is authorised as requested, and a provider authorisation "
                       "letter, showing the site of service and, for an inpatient operation, the "
                       "inpatient days requested, and then a member notice are written"),
    DECISION_REQUEST_INFORMATION: ("the requesting office is asked, in an information request "
                                   "letter, for the answers the questionnaire left out"),
    DECISION_REFER: ("the request goes to a Physician Reviewer with its review and a referral "
                     "summary, and the Physician Reviewer decides it"),
}
DECISION_OPEN_CONDITIONS = {
    DECISION_APPROVE: "It is open only when every criterion is Met.",
    DECISION_REQUEST_INFORMATION: ("It is open only when no criterion is Not met and at least "
                                   "one is Not documented."),
    DECISION_REFER: ("It is always open. A criterion that is not documented is never on its own "
                     "a reason to refer: the missing answer is asked for first. A request whose "
                     "criteria are all met may be referred when the clinical documents raise a "
                     "concern the criteria do not cover."),
}
SCREENING_CLOSED_REASONS = {
    DECISION_APPROVE: "every criterion is Met, so no answer is missing",
    DECISION_REQUEST_INFORMATION: "a criterion is Not documented",
    DECISION_REFER: "a criterion is Not met",
}
DECISION_RECORD_FIELDS = ["decision", "decided_by", "decided_by_role", "decision_reason"]
ROLE_COORDINATOR = "Intake Coordinator"
ROLE_NURSE = "UM Nurse Reviewer"
ROLE_REPRESENTATIVE = "Provider Services Representative"
DECISION_FIELDS_MISSING_MESSAGE = "The decision on request {request_reference} gives no {fields}"
DECIDING_ROLE_MESSAGE = ("The role {role} may not decide request {request_reference}: only a "
                         "{nurse_role} decides a review")
OWN_REVIEW_MESSAGE = ("{decided_by} opened the review of request {request_reference} and may not "
                      "decide it")
AUTHORISATION_ANSWER_LABELS = {
    SITE_OF_SERVICE_COLUMN: "site of service",
    REQUESTED_INPATIENT_DAYS_COLUMN: "inpatient days requested",
}
APPROVAL_LETTER_INCOMPLETE_MESSAGE = ("APPROVE cannot be recorded for request {request_reference}: "
                                      "the request gives no {answers}, which the provider "
                                      "authorisation letter must show")
UNKNOWN_DECISION_MESSAGE = ("{decision} is not one of the decisions on request "
                            "{request_reference}: {decisions}")
DECISION_NOT_OPEN_MESSAGE = "{decision} is not open for request {request_reference}: {reason}"

REVIEW_STATUS_AWAITING = "AWAITING_REVIEW"
REVIEW_STATUS_APPROVED = "APPROVED"
REVIEW_STATUS_INFORMATION_REQUESTED = "INFORMATION_REQUESTED"
REVIEW_STATUS_REFERRED = "REFERRED_TO_PHYSICIAN_REVIEW"
REVIEW_STATUS_BY_DECISION = {
    DECISION_APPROVE: REVIEW_STATUS_APPROVED,
    DECISION_REQUEST_INFORMATION: REVIEW_STATUS_INFORMATION_REQUESTED,
    DECISION_REFER: REVIEW_STATUS_REFERRED,
}

REQUEST_REFERENCE_DETAIL = "Request reference"
MEMBER_NUMBER_DETAIL = "Member number"
SERVICE_DETAIL = "Service"
SITE_OF_SERVICE_DETAIL = "Site of service"
MEDICAL_POLICY_DETAIL = "Medical policy"
INPATIENT_DAYS_DETAIL = "Inpatient days authorised"
CRITERIA_NOT_DOCUMENTED_DETAIL = "Criteria not documented, with the answers each needs"
DOCUMENTATION_TO_SEND_DETAIL = "Documentation to send"
REPLY_WITHIN_DETAIL = "Reply within"
UNANSWERED_REQUEST_DETAIL = "If the answers do not arrive in that time"
SERVICE_WITH_CODE_FORMAT = "{service_name} ({service_code})"
STANDARD_REPLY_TEXT = "14 calendar days"
URGENT_REPLY_TEXT = "one day, as the request is urgent"
UNANSWERED_REQUEST_TEXT = ("the request is referred to a Physician Reviewer, who decides it on "
                           "what was received")

LETTER_KINDS = {
    DECISION_APPROVE: "provider authorisation letter",
    DECISION_REQUEST_INFORMATION: "information request letter",
}
LETTER_GUIDANCE = {
    DECISION_APPROVE: ("The letter tells the requesting office that the service is authorised as "
                       "requested, under the medical policy named in the details."),
    DECISION_REQUEST_INFORMATION: ("The letter tells the requesting office which criteria were not "
                                   "documented and the questionnaire answers each needs, what "
                                   "documentation to send, and how long the office has to reply."),
}
NOTICE_GUIDANCE = ("The notice tells the member, in plain words, that the service is authorised "
                   "and where it is given. It contains no clinical detail beyond the name of the "
                   "service.")
LETTER_FORBIDDEN_TERMS = ["likelihood", "probability", "expected stay", "denied", "denial"]
LETTER_SIGN_OFF = f"Utilisation Management, {ORGANISATION_NAME}"
TEMPLATE_SLOT_CHARACTERS = ["[", "]"]
SIGN_OFF_SPACING_PATTERN = r"[\W_]+"
BODY_MASS_INDEX_CRITERIA = [BODY_MASS_INDEX_BELOW_CRITERION,
                            BODY_MASS_INDEX_WITH_CONDITION_CRITERION]
NOTICE_WITHHELD_COLUMNS = [DIAGNOSIS_CODE_COLUMN, PROCEDURE_DETAIL_COLUMN]
EVIDENCE_EXTRA_ANSWER_COLUMNS = [OTHER_CONDITIONS_COLUMN]
BLANK_INPUT_RULE_TEXT = ("An input shown as not given is filled as the model's training filled "
                         "it: a number with the median of the training data and an answer in "
                         "words with its most common value.")

APPLICATION_DATABASE_FILE = f"{DATABASE_DIRECTORY}/clearauth.db"
APPLICATION_DATABASE_URL = f"sqlite:///./{APPLICATION_DATABASE_FILE}"

RUN_ID_PREFIX = "RUN-"
REVIEW_ID_PREFIX = "REV-"
IDENTIFIER_HEX_LENGTH = 12

ENV_FILE = ".env"
GEMINI_API_KEY_VARIABLE = "GEMINI_API_KEY"
GEMINI_MODEL_VARIABLE = "GEMINI_MODEL"
GEMINI_MAX_OUTPUT_TOKENS = 8192
GEMINI_TEMPERATURE = 0.2
MILLISECONDS_PER_SECOND = 1000

AGENT_NAME_PLANNER = "review_planner"
AGENT_NAME_CRITERIA = "criteria_analyst"
AGENT_NAME_EVIDENCE = "evidence_analyst"
AGENT_NAME_PREDICTIONS = "likelihood_analyst"
AGENT_NAME_WRITER = "review_writer"
AGENT_NAME_LETTER = "office_letter_agent"
AGENT_NAME_NOTICE = "member_notice_agent"

RESPONSE_DECORATION_CHARACTERS = "*#`_~ \t:"
RESPONSE_DECORATION_EDGE_PATTERN = r"^[\W_]+|[\W_]+$"

AGENT_RUN_STATUS_RUNNING = "RUNNING"
AGENT_RUN_STATUS_AWAITING_DECISION = "AWAITING_DECISION"
AGENT_RUN_STATUS_COMPLETE = "COMPLETE"
AGENT_RUN_STATUS_FAILED = "FAILED"
AGENT_RUN_FINISHED_STATUSES = [AGENT_RUN_STATUS_COMPLETE, AGENT_RUN_STATUS_FAILED]


CHECKPOINT_DATABASE_FILE = f"{DATABASE_DIRECTORY}/checkpoint.db"

LLM_CALLS_BEFORE_DECISION = 5
LLM_CALLS_BY_DECISION = {
    DECISION_APPROVE: 7,
    DECISION_REQUEST_INFORMATION: 6,
    DECISION_REFER: 5,
}

REVIEW_STATUS_LABELS = {
    REVIEW_STATUS_AWAITING: "Awaiting review",
    REVIEW_STATUS_APPROVED: "Approved",
    REVIEW_STATUS_INFORMATION_REQUESTED: "Information requested",
    REVIEW_STATUS_REFERRED: "Referred to physician review",
}
REVIEW_STATUS_OPTIONS = list(REVIEW_STATUS_LABELS)
DECIDED_REVIEW_STATUSES = [REVIEW_STATUS_APPROVED, REVIEW_STATUS_INFORMATION_REQUESTED,
                           REVIEW_STATUS_REFERRED]
DECISION_OUTCOME_TEXTS = {
    DECISION_APPROVE: "the provider authorisation letter and the member notice are written",
    DECISION_REQUEST_INFORMATION: "the information request letter is written",
    DECISION_REFER: "the referral summary is recorded for a Physician Reviewer",
}
QUEUE_SERVICE_ALL = "All"
QUEUE_SERVICE_LABELS = {QUEUE_SERVICE_ALL: "All services", **SERVICE_NAMES}
QUEUE_SERVICE_OPTIONS = list(QUEUE_SERVICE_LABELS)

COORDINATOR_REQUEST_MINIMUM_CHARACTERS = 5
COORDINATOR_REQUEST_MAXIMUM_CHARACTERS = 1000
DECISION_REASON_MINIMUM_CHARACTERS = 10
DECISION_REASON_MAXIMUM_CHARACTERS = 1000

ROLES_SEEING_EVERY_REVIEW = [ROLE_COORDINATOR, ROLE_NURSE]

PAGE_QUEUE = "Review queue"
PAGE_DETAIL = "Request detail"
PAGE_DECISION = "Decision queue"
PAGE_AUDIT = "Audit trail"
PAGE_CHAT = "Authorisation chat"

ROLE_PAGE_ACCESS = {
    ROLE_NURSE: [PAGE_QUEUE, PAGE_DETAIL, PAGE_DECISION, PAGE_AUDIT, PAGE_CHAT],
    ROLE_COORDINATOR: [PAGE_QUEUE, PAGE_DETAIL, PAGE_AUDIT, PAGE_CHAT],
    ROLE_REPRESENTATIVE: [PAGE_CHAT],
}

AREA_INTAKE = "intake"
AREA_REVIEW = "review"
AREA_DECISION = "decision"
AREA_AUDIT = "audit"
AREA_CHAT = "chat"

ROLE_AREA_ACCESS = {
    ROLE_NURSE: [AREA_INTAKE, AREA_REVIEW, AREA_DECISION, AREA_AUDIT, AREA_CHAT],
    ROLE_COORDINATOR: [AREA_INTAKE, AREA_REVIEW, AREA_AUDIT, AREA_CHAT],
    ROLE_REPRESENTATIVE: [AREA_CHAT],
}

AREA_BY_ROUTE = {
    ("GET", "/queue"): AREA_INTAKE,
    ("GET", "/queue/{request_reference}"): AREA_INTAKE,
    ("POST", "/reviews"): AREA_REVIEW,
    ("GET", "/reviews"): AREA_AUDIT,
    ("POST", "/reviews/{review_id}/decision"): AREA_DECISION,
    ("GET", "/reviews/{review_id}/calls"): AREA_AUDIT,
    ("POST", "/chat/ask"): AREA_CHAT,
    ("GET", "/chat/turns"): AREA_CHAT,
    ("GET", "/audit/chat-turns"): AREA_AUDIT,
}

SEED_USER_ACCOUNTS = [
    {"username": "maria", "display_name": "Maria Okafor", "role": ROLE_NURSE,
     "password": "11111111"},
    {"username": "james", "display_name": "James Whitfield", "role": ROLE_NURSE,
     "password": "11111111"},
    {"username": "leena", "display_name": "Leena Sharma", "role": ROLE_NURSE,
     "password": "11111111"},
    {"username": "carlos", "display_name": "Carlos Mendes", "role": ROLE_COORDINATOR,
     "password": "22222222"},
    {"username": "hannah", "display_name": "Hannah Price", "role": ROLE_COORDINATOR,
     "password": "22222222"},
    {"username": "yusuf", "display_name": "Yusuf Demir", "role": ROLE_COORDINATOR,
     "password": "22222222"},
    {"username": "erin", "display_name": "Erin Walsh", "role": ROLE_COORDINATOR,
     "password": "22222222"},
    {"username": "kofi", "display_name": "Kofi Mensah", "role": ROLE_COORDINATOR,
     "password": "22222222"},
    {"username": "isla", "display_name": "Isla Fraser", "role": ROLE_COORDINATOR,
     "password": "22222222"},
    {"username": "ravi", "display_name": "Ravi Iyer", "role": ROLE_REPRESENTATIVE,
     "password": "33333333"},
    {"username": "chloe", "display_name": "Chloe Martin", "role": ROLE_REPRESENTATIVE,
     "password": "33333333"},
    {"username": "tomasz", "display_name": "Tomasz Lewandowski", "role": ROLE_REPRESENTATIVE,
     "password": "33333333"},
    {"username": "amara", "display_name": "Amara Nwosu", "role": ROLE_REPRESENTATIVE,
     "password": "33333333"},
    {"username": "dylan", "display_name": "Dylan Hughes", "role": ROLE_REPRESENTATIVE,
     "password": "33333333"},
]

USERNAME_WIDTH = 8
DISPLAY_NAME_WIDTH = 20

PASSWORD_HASH_ALGORITHM = "sha256"
PASSWORD_HASH_ROUNDS = 200000
PASSWORD_SALT_BYTES = 16
SESSION_TOKEN_BYTES = 24

SESSION_TOKEN_HEADER = "X-Session-Token"
SIGN_IN_FAILED_MESSAGE = "Username or password is not correct"
SIGN_IN_REQUIRED_MESSAGE = "Sign in first"
SESSION_ENDED_MESSAGE = ("Your session ended: this account has signed in somewhere else or "
                         "signed out. Sign in again to carry on.")
AREA_REFUSED_MESSAGE = "The {role} role does not include the {area} area"
REVIEW_NOT_FOUND_MESSAGE = "No authorisation review has that identifier"
REQUEST_ALREADY_REVIEWED_MESSAGE = ("Request {request_reference} has already been reviewed; a "
                                    "request in the queue is reviewed once")
ALREADY_DECIDED_MESSAGE = "This review has already been decided"
DECISION_IN_PROGRESS_MESSAGE = ("{decided_by} has sent {decision} for this review and it is still "
                                "being recorded; only {decided_by} can finish it, by sending the "
                                "same decision and reason again")

AGENT_NAME_AUTHORISATION_ASSISTANT = "authorisation_assistant"

CHAT_TYPE_MEDICAL_POLICY = "MEDICAL POLICY"
CHAT_TYPE_REVIEW_RULES = "REVIEW RULES"
CHAT_TYPE_EVIDENCE_GUIDANCE = "EVIDENCE GUIDANCE"
CHAT_TYPE_REQUEST_STATUS = "REQUEST STATUS"
CHAT_TYPE_OUTCOME_PREDICTION = "OUTCOME PREDICTION"
CHAT_TYPE_OUT_OF_SCOPE = "OUT OF SCOPE"
CHAT_TYPE_OPTIONS = [CHAT_TYPE_MEDICAL_POLICY, CHAT_TYPE_REVIEW_RULES, CHAT_TYPE_EVIDENCE_GUIDANCE,
                     CHAT_TYPE_REQUEST_STATUS, CHAT_TYPE_OUTCOME_PREDICTION,
                     CHAT_TYPE_OUT_OF_SCOPE]
CHAT_ANSWERED_TYPES = [CHAT_TYPE_MEDICAL_POLICY, CHAT_TYPE_REVIEW_RULES,
                       CHAT_TYPE_EVIDENCE_GUIDANCE]
CHAT_RECORD_TYPES = [CHAT_TYPE_REQUEST_STATUS, CHAT_TYPE_OUTCOME_PREDICTION]

CHAT_QUESTION_MINIMUM_CHARACTERS = 3
CHAT_QUESTION_MAXIMUM_CHARACTERS = 1000
CHAT_EXCLUDED_DOCUMENTS = ["Past-Reviews-Casebook.pdf"]
CHAT_RETRIEVAL_RESULT_COUNT = 4
CHAT_MAX_RELEVANCE_DISTANCE = 0.65
CHAT_HISTORY_TURN_LIMIT = 3
CHAT_PAGE_TURN_LIMIT = 20
CHAT_AUDIT_MAX_ROWS = 200
CHAT_NO_VALUE_REPLY = "none"
CHAT_RECORD_ANSWER_IN_HISTORY = "(answered from the review records, which are not repeated here)"

MEMBER_NUMBER_IN_TEXT_PATTERN = (r"(?i)(?<![0-9])(?:bwh[- ]?)?"
                                 r"(?P<member_digits>[0-9]{3}[- ]?[0-9]{4})(?![0-9])")
REQUEST_REFERENCE_IN_TEXT_PATTERN = r"(?i)(?<![0-9A-Za-z-])(?:pa[- ]?)?[0-9]{6}(?![0-9])"
CHAT_MEMBER_NUMBER_WITHHELD_TEXT = "[member number withheld]"

CHAT_REFUSAL_MESSAGE = ("I can only answer from the medical policies, the Utilisation Management "
                        "Policy, the Prior Authorisation Rules and the evidence guides of "
                        f"{ORGANISATION_NAME}, and I could not find anything in them that "
                        "answers that.")
CLINICAL_DETERMINATION_LINE = ("A prior authorisation outcome is decided by clinical "
                               "determination, and Provider Services cannot predict or "
                               "estimate it.")
CHAT_NO_CONFIRMATION_TEMPLATE = "No request can be confirmed for reference {request_reference}."
CHAT_REQUEST_NOT_NAMED_MESSAGE = ("Give the request reference, PA- and six digits, and the member "
                                  "number on that request.")
CHAT_REQUEST_CONFIRMED_TEMPLATE = "Request {request_reference}, {service}: {status}."
CHAT_ANSWERS_ASKED_FOR_TEXT = "The answers asked for:"
CHAT_REVIEW_NOT_NAMED_MESSAGE = "Name the request by its reference, PA- and six digits."
CHAT_NO_REVIEW_TEMPLATE = "No review of request {request_reference} has been recorded."
CHAT_REVIEW_TEMPLATE = ("{review_id}, request {request_reference}, {service}, reviewed under "
                        "{policy_document} and opened by {coordinator_id}: {status}.")
CHAT_SCREENING_TEMPLATE = ("Screening {screening}: {criteria}. The decisions open: "
                           "{decisions_open}.")
CHAT_FIGURES_TEMPLATE = ("Approval likelihood {approval_likelihood}, {approval_band}; expected "
                         "stay {expected_stay}.")
CHAT_EVIDENCE_TEMPLATE = ("Evidence: {sentence_count} sentences read ({evidence_counts}); "
                          "disagreements flagged: {disagreement_count}.")
CHAT_NO_DOCUMENTS_TEXT = "no document was sent"
CHAT_AWAITING_DECISION_TEMPLATE = ("It waits for a UM Nurse Reviewer's decision; the review "
                                   "recommends {recommended_decision}.")
CHAT_DECIDED_TEMPLATE = ('{decided_by}, {decided_by_role}, decided {decision}. The reason given: '
                         '"{decision_reason}"')

API_HOST = os.environ.get("CLEARAUTH_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("CLEARAUTH_API_PORT", "8081"))
API_TITLE = "ClearAuth AI API"
API_BASE_URL = f"http://localhost:{API_PORT}"
API_REQUEST_TIMEOUT_SECONDS = 300

DASHBOARD_TITLE = "ClearAuth AI"
DASHBOARD_SUBTITLE = f"{ORGANISATION_NAME} | prior authorisation review"
DECISION_BADGE_COLOURS = {DECISION_APPROVE: "green", DECISION_REQUEST_INFORMATION: "orange",
                          DECISION_REFER: "violet"}
STATUS_BADGE_COLOURS = {REVIEW_STATUS_AWAITING: "blue", REVIEW_STATUS_APPROVED: "green",
                        REVIEW_STATUS_INFORMATION_REQUESTED: "orange",
                        REVIEW_STATUS_REFERRED: "violet"}
APPROVAL_BAND_BADGE_COLOURS = {HIGH_APPROVAL_BAND: "green", MEDIUM_APPROVAL_BAND: "yellow",
                               LOW_APPROVAL_BAND: "gray"}
CHAT_TYPE_BADGE_COLOURS = {CHAT_TYPE_MEDICAL_POLICY: "blue", CHAT_TYPE_REVIEW_RULES: "violet",
                           CHAT_TYPE_EVIDENCE_GUIDANCE: "green",
                           CHAT_TYPE_REQUEST_STATUS: "orange",
                           CHAT_TYPE_OUTCOME_PREDICTION: "yellow", CHAT_TYPE_OUT_OF_SCOPE: "gray"}
NEUTRAL_BADGE_COLOUR = "gray"
URGENT_BADGE_COLOUR = "red"
EVIDENCE_BADGE_COLOUR = "blue"
SCREENING_NODE = "screening"
DECISION_NODE = "decision"
SCREENING_FILL_COLOURS = {CRITERION_MET: "#dcfce7", CRITERION_NOT_MET: "#fee2e2",
                          CRITERION_NOT_DOCUMENTED: "#fef3c7", SCREENING_NODE: "#ccfbf1",
                          DECISION_NODE: "#e0f2fe"}
SCREENING_LINE_COLOURS = {CRITERION_MET: "#15803d", CRITERION_NOT_MET: "#b91c1c",
                          CRITERION_NOT_DOCUMENTED: "#b45309", SCREENING_NODE: "#0f766e",
                          DECISION_NODE: "#0369a1"}
SCREENING_TEXT_COLOUR = "#10241f"
SCREENING_EDGE_COLOUR = "#5b7069"
SCREENING_GRAPH_FONT = "Helvetica"
EVIDENCE_CHART_COLOUR = "#0f766e"
EVIDENCE_NO_CRITERION_COLOUR = "#7f948d"
STAY_METRIC_NOT_WORKED_OUT = "Not worked out"
LATENCY_SECONDS_DECIMALS = 1
