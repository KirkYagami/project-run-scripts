RAW_DISPUTES_TRAIN_FILE = "data/billing_disputes_train.csv"
RAW_DISPUTES_EVAL_FILE = "data/billing_disputes_eval.csv"
RAW_EFFORT_TRAIN_FILE = "data/resolution_effort_train.csv"
RAW_EFFORT_EVAL_FILE = "data/resolution_effort_eval.csv"
RAW_CONTACT_NOTES_FILE = "data/customer_contact_notes.csv"


CLEAN_DISPUTES_TRAIN_FILE = "processed/billing_disputes_train_clean.csv"
CLEAN_DISPUTES_EVAL_FILE = "processed/billing_disputes_eval_clean.csv"
CLEAN_EFFORT_TRAIN_FILE = "processed/resolution_effort_train_clean.csv"
CLEAN_EFFORT_EVAL_FILE = "processed/resolution_effort_eval_clean.csv"
CLEAN_CONTACT_NOTES_FILE = "processed/customer_contact_notes_clean.csv"


DATA_QUALITY_REPORT_FILE = "output/data_quality_report.json"


NULL_TOKENS = ["", "-", "n/a", "none", "?", "not recorded"]


BOOLEAN_YES = "Yes"
BOOLEAN_NO = "No"

BOOLEAN_MAPPING = {
    "yes": BOOLEAN_YES,
    "y": BOOLEAN_YES,
    "true": BOOLEAN_YES,
    "1": BOOLEAN_YES,
    "no": BOOLEAN_NO,
    "n": BOOLEAN_NO,
    "false": BOOLEAN_NO,
    "0": BOOLEAN_NO,
}


PRICE_YEAR_MONTHS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar",
                     "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
PRICE_YEAR_MONTH_LENGTHS = [31, 30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30]

PRICE_YEAR_DATES = [f"{day_of_month:02d} {month_name}"
                    for month_name, month_length in zip(PRICE_YEAR_MONTHS,
                                                        PRICE_YEAR_MONTH_LENGTHS)
                    for day_of_month in range(1, month_length + 1)]
DAY_NUMBER_BY_PRICE_YEAR_DATE = {date_text: day_number for day_number, date_text
                                 in enumerate(PRICE_YEAR_DATES, start=1)}
PRICE_YEAR_DATE_BY_DAY_NUMBER = dict(enumerate(PRICE_YEAR_DATES, start=1))

MONTH_BY_NUMBER = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

MONTH_NAME_MAPPING = {
    "oct": "Oct", "october": "Oct",
    "nov": "Nov", "november": "Nov",
    "dec": "Dec", "december": "Dec",
    "jan": "Jan", "january": "Jan",
    "feb": "Feb", "february": "Feb",
    "mar": "Mar", "march": "Mar",
    "apr": "Apr", "april": "Apr",
    "may": "May",
    "jun": "Jun", "june": "Jun",
    "jul": "Jul", "july": "Jul",
    "aug": "Aug", "august": "Aug",
    "sep": "Sep", "september": "Sep",
}

BILLING_SYSTEM_COLUMN = "billing_system"
MONTH_FIRST_BY_BILLING_SYSTEM = {
    "Calderwell CIS": False,
    "Severn Billing": False,
    "Clyde Billing": False,
    "Meridian Utility Billing": True,
}

NUMERIC_DATE_PATTERN = r"^(\d{1,2})/(\d{1,2})$"
WORDED_DATE_PATTERN = r"^(\d{1,2})[ -]([a-z]+)$"
STANDARD_DATE_PATTERN = r"^\d{2} [A-Z][a-z]{2}$"
STANDARD_TIMESTAMP_PATTERN = r"^\d{2} [A-Z][a-z]{2} \d{2}:\d{2}$"
TIMESTAMP_PARTS_PATTERN = (r"^(?P<note_written_date>.+?)\s+"
                           r"(?P<note_written_time>(?:[01]\d|2[0-3]):[0-5]\d)$")
NOTE_DATE_PART = "note_written_date"
NOTE_TIME_PART = "note_written_time"


PLAIN_NUMBER_PATTERN = r"^-?\d+(?:\.\d+)?$"
AMOUNT_PATTERN = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
MONEY_NOTATION_PATTERN = (rf"^(?:-?{AMOUNT_PATTERN}|£{AMOUNT_PATTERN}|{AMOUNT_PATTERN} gbp"
                          rf"|gbp {AMOUNT_PATTERN}|£{AMOUNT_PATTERN} cr|\(£{AMOUNT_PATTERN}\))$")
MONEY_SYMBOL_PATTERN = r"£|gbp|cr|[(),\s]"
CREDIT_NOTATION_PATTERN = r" cr$|^\(.*\)$"

DIGIT_GROUPING_SEPARATOR = ","
ENERGY_READING_PATTERN = rf"^(-?{AMOUNT_PATTERN})(?: (mwh|kwh|wh))?$"
ENERGY_UNIT_FACTORS = {"mwh": 1000.0, "kwh": 1.0, "wh": 0.001}
UNIT_CONVERSION_DECIMALS = 6

HOURS_AND_MINUTES_PATTERN = r"^(\d+)h\s*(\d+)m$"
MINUTES_UNIT_PATTERN = r"^(\d+(?:\.\d+)?)\s*min$"
HOURS_UNIT_PATTERN = r"^(\d+(?:\.\d+)?)\s*h$"
MINUTES_PER_HOUR = 60



MARKUP_PATTERN = r"<[^>]+>"
ENCODING_ARTIFACT_PATTERN = r"&[#a-z0-9]+;|\xa0"
NO_BREAK_SPACE = "\xa0"
WHITESPACE_RUN_PATTERN = r"\s+"
MINIMUM_NOTE_WORDS = 6


BILLING_SYSTEM_MAPPING = {
    "calderwell cis": "Calderwell CIS",
    "severn billing": "Severn Billing",
    "clyde billing": "Clyde Billing",
    "meridian utility billing": "Meridian Utility Billing",
}

BILLING_CENTRE_MAPPING = {
    "leeds": "Leeds",
    "lds": "Leeds",
    "cardiff": "Cardiff",
    "caerdydd": "Cardiff",
    "cdf": "Cardiff",
    "glasgow": "Glasgow",
    "glasgow city": "Glasgow",
    "gla": "Glasgow",
    "norwich": "Norwich",
    "nrw": "Norwich",
}

CONTACT_CHANNEL_MAPPING = {
    "phone": "Phone",
    "email": "Email",
    "web form": "Web form",
    "letter": "Letter",
    "social media": "Social media",
}

BILLING_FREQUENCY_MAPPING = {
    "monthly": "Monthly",
    "quarterly": "Quarterly",
}

TARIFF_MAPPING = {
    "standard variable": "Standard Variable",
    "svt": "Standard Variable",
    "std var": "Standard Variable",
    "standard variable tariff": "Standard Variable",
    "fixed 12": "Fixed 12",
    "fixed12": "Fixed 12",
    "fix12": "Fixed 12",
    "fixed 12m": "Fixed 12",
    "fixed 24": "Fixed 24",
    "fixed24": "Fixed 24",
    "fix24": "Fixed 24",
    "fixed 24m": "Fixed 24",
    "economy two-rate": "Economy Two-Rate",
    "e2r": "Economy Two-Rate",
    "e7": "Economy Two-Rate",
    "economy 7": "Economy Two-Rate",
    "prepayment": "Prepayment",
    "ppm": "Prepayment",
    "prepay": "Prepayment",
    "pre-payment": "Prepayment",
}

METER_TYPE_MAPPING = {
    "single-rate": "Single-rate",
    "single rate": "Single-rate",
    "sr": "Single-rate",
    "two-rate": "Two-rate",
    "two rate": "Two-rate",
    "dual rate": "Two-rate",
    "tr": "Two-rate",
}

READ_TYPE_MAPPING = {
    "actual": "Actual",
    "a": "Actual",
    "act": "Actual",
    "estimated": "Estimated",
    "e": "Estimated",
    "est.": "Estimated",
    "est": "Estimated",
    "customer": "Customer",
    "c": "Customer",
    "cust": "Customer",
}

PAYMENT_METHOD_MAPPING = {
    "direct debit": "Direct debit",
    "dd": "Direct debit",
    "pay on receipt": "Pay on receipt",
    "por": "Pay on receipt",
    "cash/cheque": "Pay on receipt",
    "prepayment": "Prepayment",
    "ppm": "Prepayment",
    "prepay": "Prepayment",
}

DISPUTE_CATEGORY_MAPPING = {
    "estimated read billed": "Estimated read billed",
    "estimated reading": "Estimated read billed",
    "estimated bill": "Estimated read billed",
    "meter fault suspected": "Meter fault suspected",
    "faulty meter": "Meter fault suspected",
    "meter fault": "Meter fault suspected",
    "wrong tariff applied": "Wrong tariff applied",
    "wrong tariff": "Wrong tariff applied",
    "incorrect tariff": "Wrong tariff applied",
    "price change on the wrong date": "Price change on the wrong date",
    "price change date": "Price change on the wrong date",
    "price change wrong date": "Price change on the wrong date",
    "payment not credited": "Payment not credited",
    "missing payment": "Payment not credited",
    "payment missing": "Payment not credited",
    "change of tenancy read": "Change of tenancy read",
    "change of tenancy": "Change of tenancy read",
    "cot read": "Change of tenancy read",
    "direct debit amount": "Direct debit amount",
    "dd amount": "Direct debit amount",
    "crossed meters": "Crossed meters",
    "crossed meter": "Crossed meters",
    "meters crossed": "Crossed meters",
}

ANALYST_GRADE_MAPPING = {
    "associate analyst": "Associate Analyst",
    "assoc. analyst": "Associate Analyst",
    "associate": "Associate Analyst",
    "billing analyst": "Billing Analyst",
    "analyst": "Billing Analyst",
    "senior billing analyst": "Senior Billing Analyst",
    "sr billing analyst": "Senior Billing Analyst",
    "senior analyst": "Senior Billing Analyst",
    "team leader": "Team Leader",
    "team lead": "Team Leader",
    "tl": "Team Leader",
}

REBILL_BAND_MAPPING = {
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}

NOTE_SOURCE_MAPPING = {
    "first contact": "First contact",
    "follow-up": "Follow-up",
    "analyst update": "Analyst update",
    "callback": "Callback",
    "closure note": "Closure note",
}


DISPUTE_TARGET_COLUMN = "bill_corrected"
BILL_START_COLUMN = "bill_start_date"
BILL_END_COLUMN = "bill_end_date"
DAYS_BILLED_COLUMN = "days_billed"
REGISTER_DIGITS_COLUMN = "meter_register_digits"
OPENING_READ_COLUMN = "opening_read"
CLOSING_READ_COLUMN = "closing_read"
NIGHT_OPENING_READ_COLUMN = "night_opening_read"
NIGHT_CLOSING_READ_COLUMN = "night_closing_read"
BILLED_UNITS_COLUMN = "billed_units_kwh"
METER_TYPE_COLUMN = "meter_type"
SINGLE_RATE_METER_TYPE = "Single-rate"
TWO_RATE_METER_TYPE = "Two-rate"
REGISTER_NUMBER_BASE = 10

DISPUTE_VALUE_MAPPINGS = {
    "billing_centre": BILLING_CENTRE_MAPPING,
    BILLING_SYSTEM_COLUMN: BILLING_SYSTEM_MAPPING,
    "contact_channel": CONTACT_CHANNEL_MAPPING,
    "billing_frequency": BILLING_FREQUENCY_MAPPING,
    "billed_tariff": TARIFF_MAPPING,
    "entitled_tariff": TARIFF_MAPPING,
    METER_TYPE_COLUMN: METER_TYPE_MAPPING,
    "smart_meter_flag": BOOLEAN_MAPPING,
    "opening_read_type": READ_TYPE_MAPPING,
    "closing_read_type": READ_TYPE_MAPPING,
    "payment_method": PAYMENT_METHOD_MAPPING,
    "change_of_tenancy_flag": BOOLEAN_MAPPING,
    "priority_services_flag": BOOLEAN_MAPPING,
    DISPUTE_TARGET_COLUMN: BOOLEAN_MAPPING,
}

DISPUTE_DATE_COLUMNS = [BILL_START_COLUMN, BILL_END_COLUMN, "fixed_term_last_day"]

DISPUTE_MONEY_COLUMNS = ["amount_billed_gbp", "direct_debit_monthly_gbp",
                         "balance_owed_before_bill_gbp"]

DISPUTE_ENERGY_COLUMNS = [BILLED_UNITS_COLUMN]

DISPUTE_WHOLE_NUMBER_COLUMNS = [
    DAYS_BILLED_COLUMN, REGISTER_DIGITS_COLUMN, OPENING_READ_COLUMN, CLOSING_READ_COLUMN,
    NIGHT_OPENING_READ_COLUMN, NIGHT_CLOSING_READ_COLUMN, "consecutive_estimated_bills",
    "days_since_last_actual_read", "usage_change_vs_last_year_pct", "tariff_changes_in_bill",
    "fixed_term_days_cut_short", "price_changes_in_bill", "prior_disputes_12m",
    "account_age_months", "estimated_annual_usage_kwh",
]

DISPUTE_RANGE_LIMITS = {
    REGISTER_DIGITS_COLUMN: (4, 7),
    "account_age_months": (0, 600),
    "days_since_last_actual_read": (0, 3650),
    "estimated_annual_usage_kwh": (100, 60000),
}


EFFORT_TARGET_COLUMN = "resolution_hours"

EFFORT_VALUE_MAPPINGS = {
    "analyst_grade": ANALYST_GRADE_MAPPING,
    "billing_centre": BILLING_CENTRE_MAPPING,
    "contact_channel": CONTACT_CHANNEL_MAPPING,
    "dispute_category": DISPUTE_CATEGORY_MAPPING,
    "rebill_band": REBILL_BAND_MAPPING,
    "meter_type": METER_TYPE_MAPPING,
    "smart_meter_flag": BOOLEAN_MAPPING,
    "verified_reads_obtained_flag": BOOLEAN_MAPPING,
    "site_visit_required_flag": BOOLEAN_MAPPING,
    "meter_test_required_flag": BOOLEAN_MAPPING,
    "meter_operator_involved_flag": BOOLEAN_MAPPING,
    "priority_services_flag": BOOLEAN_MAPPING,
    "complaint_escalated_flag": BOOLEAN_MAPPING,
}

EFFORT_DATE_COLUMNS = ["resolution_started_date"]

EFFORT_MONEY_COLUMNS = ["amount_at_stake_gbp"]

EFFORT_DURATION_COLUMNS = [EFFORT_TARGET_COLUMN]

EFFORT_COUNT_WITH_UNIT_PATTERNS = {
    "letters_sent_count": r"^(\d+)(?: letters?)?$",
    "calls_made_count": r"^(\d+)(?: calls?)?$",
}

EFFORT_WHOLE_NUMBER_COLUMNS = ["bill_pieces_count", "tariffs_involved_count",
                               "analyst_open_disputes_count"]

EFFORT_RANGE_LIMITS = {
    EFFORT_TARGET_COLUMN: (0.25, 100.0),
    "letters_sent_count": (0, 20),
    "calls_made_count": (0, 40),
    "analyst_open_disputes_count": (0, 60),
}


NOTE_TARGET_COLUMN = "dispute_category"
NOTE_TEXT_COLUMN = "note_text"
NOTE_LENGTH_COLUMN = "note_length_chars"
NOTE_TIMESTAMP_COLUMN = "note_written_at"

NOTE_VALUE_MAPPINGS = {
    "billing_centre": BILLING_CENTRE_MAPPING,
    "contact_channel": CONTACT_CHANNEL_MAPPING,
    "note_source": NOTE_SOURCE_MAPPING,
    NOTE_TARGET_COLUMN: DISPUTE_CATEGORY_MAPPING,
}


RANDOM_SEED = 42
NOTE_HELD_OUT_SHARE = 0.2

REBILL_MODEL_FILE = "output/models/rebill_model.pkl"
EFFORT_MODEL_FILE = "output/models/effort_model.pkl"
CAUSE_MODEL_FILE = "output/models/cause_model.pkl"
REBILL_SCHEMA_FILE = "output/models/rebill_features.json"
EFFORT_SCHEMA_FILE = "output/models/effort_features.json"
MODEL_METRICS_FILE = "output/model_metrics.json"

DISPUTE_TARGET_ENCODING = {BOOLEAN_YES: 1, BOOLEAN_NO: 0}

REBILL_NUMERIC_FEATURES = [
    DAYS_BILLED_COLUMN, REGISTER_DIGITS_COLUMN, BILLED_UNITS_COLUMN, "amount_billed_gbp",
    "consecutive_estimated_bills", "days_since_last_actual_read", "usage_change_vs_last_year_pct",
    "tariff_changes_in_bill", "fixed_term_days_cut_short", "price_changes_in_bill",
    "prior_disputes_12m", "account_age_months", "estimated_annual_usage_kwh",
    "direct_debit_monthly_gbp", "balance_owed_before_bill_gbp",
]

REBILL_CATEGORICAL_FEATURES = [
    "billing_centre", BILLING_SYSTEM_COLUMN, "contact_channel", "billing_frequency",
    "billed_tariff", "entitled_tariff", METER_TYPE_COLUMN, "smart_meter_flag", "opening_read_type",
    "closing_read_type", "payment_method", "change_of_tenancy_flag", "priority_services_flag",
]

EFFORT_NUMERIC_FEATURES = [
    "bill_pieces_count", "tariffs_involved_count", "amount_at_stake_gbp", "letters_sent_count",
    "calls_made_count", "analyst_open_disputes_count",
]

EFFORT_CATEGORICAL_FEATURES = [
    "analyst_grade", "billing_centre", "contact_channel", "dispute_category", "rebill_band",
    "meter_type", "smart_meter_flag", "verified_reads_obtained_flag", "site_visit_required_flag",
    "meter_test_required_flag", "meter_operator_involved_flag", "priority_services_flag",
    "complaint_escalated_flag",
]

MINIMUM_REBILL_ROC_AUC = 0.75
MINIMUM_EFFORT_R2 = 0.60
MINIMUM_CAUSE_MACRO_F1 = 0.75


DOCS_DIRECTORY = "data/docs"
VECTOR_STORE_DIRECTORY = "database/chroma_store"
VECTOR_COLLECTION_NAME = "billing_dispute_documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"

CHUNK_SIZE_CHARACTERS = 700
CHUNK_OVERLAP_CHARACTERS = 120
DOCUMENT_HEADER_PATTERN = r"Document\s+[A-Za-z0-9 ]+\|\s*Issue\s*\d+.*?Review cycle:\s*[A-Za-z ]+"
SECTION_HEADING_PATTERN = r"(?m)^(\d{1,2})\. [A-Z]"
CONTROL_CHARACTER_PATTERN = r"[\x00-\x08\x0e-\x1f\x7f]"
SENTENCE_BOUNDARY_PATTERN = r"(?<=[.:;])(?<![0-9]\.)\s+"

TARIFF_DOCUMENT_BY_TARIFF = {
    "Standard Variable": "Tariff-Standard-Variable.pdf",
    "Fixed 12": "Tariff-Fixed-12.pdf",
    "Fixed 24": "Tariff-Fixed-24.pdf",
    "Economy Two-Rate": "Tariff-Economy-Two-Rate.pdf",
    "Prepayment": "Tariff-Prepayment.pdf",
}
STANDARDS_DOCUMENT = "Guaranteed-Standards-Of-Service.pdf"

SINGLE_RATE_PRICE_PATTERN = (r"From (\d{1,2}) ([A-Z][a-z]+) the unit rate is (\d+\.\d{2})p "
                             r"per kWh and the standing charge is (\d+\.\d{2})p per day\.")
TWO_RATE_PRICE_PATTERN = (r"From (\d{1,2}) ([A-Z][a-z]+) the day unit rate is (\d+\.\d{2})p "
                          r"per kWh, the night unit rate is (\d+\.\d{2})p per kWh and the "
                          r"standing charge is (\d+\.\d{2})p per day\.")
ROLL_OVER_PATTERN = r"When the term ends, the account moves to the ([A-Za-z0-9 -]+?) tariff\."
NO_FIXED_TERM_PATTERN = r"This tariff has no fixed term\."
STANDARD_PAYMENT_PATTERN = r"When ([^.]+?), Calderwell pays the customer £(\d+\.\d{2})\."

GUARANTEED_STANDARD_BREACH_PHRASES = {
    "GS1": "an agreed tariff is not applied",
    "GS2": "bills are estimated without an attempt to read the meter",
    "GS3": "a suspected meter fault is not investigated in time",
}


DISPUTE_REFERENCE_COLUMN = "dispute_reference"
BILLING_CENTRE_COLUMN = "billing_centre"
NOTE_SEQUENCE_COLUMN = "note_sequence"
DISPUTE_NOT_IN_QUEUE_MESSAGE = "Dispute {dispute_reference} is not in the open queue."
DISPUTE_WITHOUT_NOTES_MESSAGE = "Dispute {dispute_reference} has no contact notes."

REBILL_BAND_HIGH = "HIGH"
REBILL_BAND_MEDIUM = "MEDIUM"
REBILL_BAND_LOW = "LOW"
REBILL_BAND_HIGH_THRESHOLD = 0.60
REBILL_BAND_MEDIUM_THRESHOLD = 0.30
PROBABILITY_DECIMALS = 4
EFFORT_HOURS_DECIMALS = 2

VERIFIED_READ_SOURCE_COLUMN = "verified_read_source"
VERIFIED_READ_SOURCES = ["Field visit", "Smart meter", "Customer photo", "Meter test"]
SITE_VISIT_READ_SOURCES = ["Field visit"]
METER_TEST_READ_SOURCES = ["Meter test"]
METER_OPERATOR_READ_SOURCES = ["Field visit", "Meter test"]
EFFORT_PLANNING_ASSUMPTIONS = {
    "analyst_grade": "Billing Analyst",
    "letters_sent_count": 2,
    "calls_made_count": 2,
    "complaint_escalated_flag": BOOLEAN_NO,
    "analyst_open_disputes_count": 9,
}
PRIORITY_SERVICES_COLUMN = "priority_services_flag"
PRIORITY_SERVICES_EFFORT_MULTIPLIER = 1.5
SENIOR_REVIEW_THRESHOLD_HOURS = 6

AMOUNT_BILLED_COLUMN = "amount_billed_gbp"
BILLED_TARIFF_COLUMN = "billed_tariff"
ENTITLED_TARIFF_COLUMN = "entitled_tariff"
FIXED_TERM_LAST_DAY_COLUMN = "fixed_term_last_day"
VERIFIED_OPENING_READ_COLUMN = "verified_opening_read"
VERIFIED_CLOSING_READ_COLUMN = "verified_closing_read"
VERIFIED_NIGHT_OPENING_READ_COLUMN = "verified_night_opening_read"
VERIFIED_NIGHT_CLOSING_READ_COLUMN = "verified_night_closing_read"

PENCE_PER_POUND = 100
PENNY = "0.01"
PIECE_DISPLAY_QUANTUM = "0.01"
REBILL_THRESHOLD_GBP = "1.00"
OVERCHARGED = "Overcharged"
UNDERCHARGED = "Undercharged"
BILLED_CORRECTLY = "Billed correctly"

GUARANTEED_STANDARD_BREACH_COLUMNS = {
    "GS1": "agreed_tariff_not_applied_flag",
    "GS2": "estimated_without_read_attempt_flag",
    "GS3": "meter_fault_not_investigated_flag",
}

GUIDE_DOCUMENT_BY_CATEGORY = {
    "Estimated read billed": "Guide-Estimated-Reads.pdf",
    "Meter fault suspected": "Guide-Meter-Faults.pdf",
    "Wrong tariff applied": "Guide-Wrong-Tariff.pdf",
    "Price change on the wrong date": "Guide-Price-Change-Dates.pdf",
    "Payment not credited": "Guide-Payments-Not-Credited.pdf",
    "Change of tenancy read": "Guide-Change-Of-Tenancy.pdf",
    "Direct debit amount": "Guide-Direct-Debit-Amounts.pdf",
    "Crossed meters": "Guide-Crossed-Meters.pdf",
}
CUSTOMER_STEPS_QUESTION = "What should the customer do, and what steps does the letter give them?"
CUSTOMER_STEPS_RESULT_COUNT = 1


ORGANISATION_NAME = "Calderwell Energy"

OPEN_DISPUTES_FILE = "data/input/open_disputes.csv"
OPEN_DISPUTE_NOTES_FILE = "data/input/open_dispute_notes.csv"
DISPUTE_CATEGORIES = list(GUIDE_DOCUMENT_BY_CATEGORY)

DATABASE_DIRECTORY = "database"
APPLICATION_DATABASE_FILE = "database/billright.db"
APPLICATION_DATABASE_URL = f"sqlite:///./{APPLICATION_DATABASE_FILE}"

RUN_ID_PREFIX = "RUN-"
ASSESSMENT_ID_PREFIX = "ASM-"
IDENTIFIER_HEX_LENGTH = 12

GEMINI_API_KEY_VARIABLE = "GEMINI_API_KEY"
GEMINI_MODEL_VARIABLE = "GEMINI_MODEL"
GEMINI_MAX_OUTPUT_TOKENS = 8192
GEMINI_TEMPERATURE = 0.2

AGENT_NAME_PLANNER = "dispute_intake_planner"
AGENT_NAME_REBILL = "rebill_analyst"
AGENT_NAME_CAUSE = "cause_analyst"
AGENT_NAME_TARIFF = "tariff_advisor"
AGENT_NAME_WRITER = "dispute_writer"
AGENT_NAME_REDRESS_LETTER = "redress_letter_agent"
AGENT_NAME_REBILL_STATEMENT = "rebill_statement_agent"

RESPONSE_DECORATION_CHARACTERS = "*#`_~ \t-–—•>:[]"
BOOLEAN_LABELS = {True: BOOLEAN_YES, False: BOOLEAN_NO}

AGENT_RUN_STATUS_RUNNING = "RUNNING"
AGENT_RUN_STATUS_AWAITING_DECISION = "AWAITING_DECISION"
AGENT_RUN_STATUS_COMPLETE = "COMPLETE"
AGENT_RUN_STATUS_FAILED = "FAILED"
AGENT_RUN_FINISHED_STATUSES = [AGENT_RUN_STATUS_COMPLETE, AGENT_RUN_STATUS_FAILED]

DECISION_UPHOLD_BILL = "UPHOLD BILL"
DECISION_REBILL = "REBILL"
DECISION_REBILL_AND_COMPENSATE = "REBILL AND COMPENSATE"
DECISION_OPTIONS = [DECISION_UPHOLD_BILL, DECISION_REBILL, DECISION_REBILL_AND_COMPENSATE]
SETTLEMENT_CREDITED = "credited to the account"
SETTLEMENT_PAYABLE = "payable by the customer"
SETTLEMENT_NOTHING_DUE = "nothing to settle"

DISPUTE_STATUS_PENDING = "PENDING_DECISION"
DISPUTE_STATUS_UPHELD = "UPHELD"
DISPUTE_STATUS_REBILLED = "REBILLED"
DISPUTE_STATUS_REBILLED_AND_COMPENSATED = "REBILLED_AND_COMPENSATED"
DISPUTE_STATUS_BY_DECISION = {
    DECISION_UPHOLD_BILL: DISPUTE_STATUS_UPHELD,
    DECISION_REBILL: DISPUTE_STATUS_REBILLED,
    DECISION_REBILL_AND_COMPENSATE: DISPUTE_STATUS_REBILLED_AND_COMPENSATED,
}


CHECKPOINT_DATABASE_FILE = "database/checkpoint.db"

LLM_CALLS_BEFORE_DECISION = 5
LLM_CALLS_BY_DECISION = {
    DECISION_UPHOLD_BILL: 5,
    DECISION_REBILL: 6,
    DECISION_REBILL_AND_COMPENSATE: 7,
}

DISPUTE_STATUS_OPTIONS = [DISPUTE_STATUS_PENDING, DISPUTE_STATUS_UPHELD, DISPUTE_STATUS_REBILLED,
                          DISPUTE_STATUS_REBILLED_AND_COMPENSATED]
DECIDED_DISPUTE_STATUSES = [DISPUTE_STATUS_UPHELD, DISPUTE_STATUS_REBILLED,
                            DISPUTE_STATUS_REBILLED_AND_COMPENSATED]
QUEUE_DIRECTION_ALL = "All"
QUEUE_DIRECTION_OPTIONS = [QUEUE_DIRECTION_ALL, OVERCHARGED, UNDERCHARGED, BILLED_CORRECTLY]

ANALYST_REQUEST_MINIMUM_CHARACTERS = 5
DECISION_REASON_MINIMUM_CHARACTERS = 10

ROLE_ANALYST = "Billing Analyst"
ROLE_CONTROLLER = "Revenue Controller"
ROLE_CONTACT_CENTRE = "Contact Centre Agent"

PAGE_QUEUE = "Dispute queue"
PAGE_DISPUTE = "Dispute detail"
PAGE_DECISION = "Decision queue"
PAGE_AUDIT = "Audit trail"
PAGE_CHAT = "Billing chat"

ROLE_PAGE_ACCESS = {
    ROLE_CONTROLLER: [PAGE_QUEUE, PAGE_DISPUTE, PAGE_DECISION, PAGE_AUDIT, PAGE_CHAT],
    ROLE_ANALYST: [PAGE_QUEUE, PAGE_DISPUTE, PAGE_AUDIT, PAGE_CHAT],
    ROLE_CONTACT_CENTRE: [PAGE_CHAT],
}

AREA_INTAKE = "intake"
AREA_ASSESSMENT = "assessment"
AREA_DECISION = "decision"
AREA_AUDIT = "audit"
AREA_CHAT = "chat"

ROLE_AREA_ACCESS = {
    ROLE_CONTROLLER: [AREA_INTAKE, AREA_ASSESSMENT, AREA_DECISION, AREA_AUDIT, AREA_CHAT],
    ROLE_ANALYST: [AREA_INTAKE, AREA_ASSESSMENT, AREA_AUDIT, AREA_CHAT],
    ROLE_CONTACT_CENTRE: [AREA_CHAT],
}

AREA_BY_PATH_START = {
    "/queue": AREA_INTAKE,
    "/assessments": AREA_ASSESSMENT,
    "/disputes": AREA_AUDIT,
    "/audit": AREA_AUDIT,
    "/chat": AREA_CHAT,
}
DECISION_PATH_ENDING = "/decision"

SEED_USER_ACCOUNTS = [
    {"username": "fiona", "display_name": "Fiona MacLeod", "role": ROLE_CONTROLLER, "password": "11111111"},
    {"username": "gareth", "display_name": "Gareth Pryce", "role": ROLE_CONTROLLER, "password": "11111111"},
    {"username": "amara", "display_name": "Amara Okafor", "role": ROLE_CONTROLLER, "password": "11111111"},
    {"username": "hamish", "display_name": "Hamish Kerr", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "bethan", "display_name": "Bethan Lloyd", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "imran", "display_name": "Imran Qureshi", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "chloe", "display_name": "Chloe Hartley", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "declan", "display_name": "Declan Byrne", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "sian", "display_name": "Sian Morgan", "role": ROLE_ANALYST, "password": "22222222"},
    {"username": "megan", "display_name": "Megan Walsh", "role": ROLE_CONTACT_CENTRE, "password": "33333333"},
    {"username": "kofi", "display_name": "Kofi Mensah", "role": ROLE_CONTACT_CENTRE, "password": "33333333"},
    {"username": "ellie", "display_name": "Ellie Thompson", "role": ROLE_CONTACT_CENTRE, "password": "33333333"},
    {"username": "rhys", "display_name": "Rhys Evans", "role": ROLE_CONTACT_CENTRE, "password": "33333333"},
    {"username": "leah", "display_name": "Leah Patel", "role": ROLE_CONTACT_CENTRE, "password": "33333333"},
    {"username": "callum", "display_name": "Callum Reid", "role": ROLE_CONTACT_CENTRE, "password": "33333333"},
]

PASSWORD_HASH_ALGORITHM = "sha256"
PASSWORD_HASH_ROUNDS = 200000
PASSWORD_SALT_BYTES = 16
SESSION_TOKEN_BYTES = 24

SESSION_TOKEN_HEADER = "X-Session-Token"
SIGN_IN_FAILED_MESSAGE = "Username or password is not correct"
SIGN_IN_REQUIRED_MESSAGE = "Sign in first"
AREA_REFUSED_MESSAGE = "A {role} may not use the {area} area"
ASSESSMENT_NOT_FOUND_MESSAGE = "No assessment has that identifier"
ALREADY_DECIDED_MESSAGE = "This assessment has already been decided"
DECISION_IN_PROGRESS_MESSAGE = ("A decision of {decision} is already being recorded on this "
                                "assessment; send that decision again to finish recording it")
OWN_ASSESSMENT_REFUSED_MESSAGE = ("The person who opened an assessment may not decide it; another "
                                  "Revenue Controller records the decision, because the Billing "
                                  "Disputes Policy separates investigating a dispute from "
                                  "approving its correction")

AGENT_NAME_BILLING_ASSISTANT = "billing_assistant"

CHAT_TYPE_TARIFF = "TARIFF"
CHAT_TYPE_BILLING_RULES = "BILLING RULES"
CHAT_TYPE_CUSTOMER_ADVICE = "CUSTOMER ADVICE"
CHAT_TYPE_DISPUTE_STATUS = "DISPUTE STATUS"
CHAT_TYPE_OUT_OF_SCOPE = "OUT OF SCOPE"
CHAT_TYPE_OPTIONS = [CHAT_TYPE_TARIFF, CHAT_TYPE_BILLING_RULES, CHAT_TYPE_CUSTOMER_ADVICE,
                     CHAT_TYPE_DISPUTE_STATUS, CHAT_TYPE_OUT_OF_SCOPE]
CHAT_ANSWERED_TYPES = [CHAT_TYPE_TARIFF, CHAT_TYPE_BILLING_RULES, CHAT_TYPE_CUSTOMER_ADVICE]

CHAT_QUESTION_MINIMUM_CHARACTERS = 3
CHAT_EXCLUDED_DOCUMENTS = ["Past-Disputes-Casebook.pdf"]
CHAT_RETRIEVAL_RESULT_COUNT = 4
CHAT_MAX_RELEVANCE_DISTANCE = 0.6
CHAT_HISTORY_TURN_LIMIT = 3
CHAT_PAGE_TURN_LIMIT = 20
CHAT_AUDIT_MAX_ROWS = 200
DISPUTE_REFERENCE_PATTERN = r"\bDSP-(?:LDS|CDF|GLA|NRW)-\d{7}\b"
CHAT_STATUS_ANSWER_IN_HISTORY = "(answered from the dispute's record, which is not repeated here)"

CHAT_FIGURE_ROLES = [ROLE_ANALYST, ROLE_CONTROLLER]
CHAT_REFUSAL_MESSAGE = ("I can only answer from Calderwell Energy's tariff schedules, policies, "
                        "standards and resolution guides, and I could not find anything in them "
                        "that answers that.")
CHAT_UNKNOWN_DISPUTE_MESSAGE = ("I could not find that dispute in the open queue. Name it by its "
                                "reference, in the form DSP-LDS-1234567.")
CHAT_NOT_ASSESSED_TEMPLATE = ("{dispute_reference} is in the open queue and has not been assessed "
                              "yet.")
CHAT_STATUS_TEMPLATE = "{dispute_reference} {status_phrase}. Its status last changed on {changed_on}."
CHAT_STATUS_PHRASES = {
    DISPUTE_STATUS_PENDING: "is under review",
    DISPUTE_STATUS_UPHELD: "is resolved, and the bill stands",
    DISPUTE_STATUS_REBILLED: "is resolved, and a corrected bill has been issued",
    DISPUTE_STATUS_REBILLED_AND_COMPENSATED: ("is resolved, a corrected bill has been issued and "
                                              "the customer has been written to"),
}
CHAT_AMOUNTS_IN_WRITING_MESSAGE = "Amounts are confirmed to the customer in writing."
STATUS_CHANGE_TIME_FORMAT = "%d %b at %H:%M UTC"

API_HOST = "0.0.0.0"
API_PORT = 8081
API_TITLE = "BillRight AI API"
API_BASE_URL = "http://localhost:8081"
API_REQUEST_TIMEOUT_SECONDS = 180
SLOW_PAGE_NOTICE_SECONDS = 10
PAGE_LOAD_STARTED_AT_KEY = "_page_load_started_at"

DASHBOARD_TITLE = "BillRight AI"
DASHBOARD_SUBTITLE = f"{ORGANISATION_NAME} · billing disputes desk"
DIRECTION_BADGE_COLOURS = {OVERCHARGED: "orange", UNDERCHARGED: "violet", BILLED_CORRECTLY: "green"}
REBILL_BAND_BADGE_COLOURS = {REBILL_BAND_HIGH: "red", REBILL_BAND_MEDIUM: "orange",
                             REBILL_BAND_LOW: "green"}
DECISION_BADGE_COLOURS = {DECISION_UPHOLD_BILL: "gray", DECISION_REBILL: "blue",
                          DECISION_REBILL_AND_COMPENSATE: "violet"}
STATUS_BADGE_COLOURS = {DISPUTE_STATUS_PENDING: "orange", DISPUTE_STATUS_UPHELD: "gray",
                        DISPUTE_STATUS_REBILLED: "blue",
                        DISPUTE_STATUS_REBILLED_AND_COMPENSATED: "violet"}
CHAT_TYPE_BADGE_COLOURS = {CHAT_TYPE_TARIFF: "blue", CHAT_TYPE_BILLING_RULES: "violet",
                           CHAT_TYPE_CUSTOMER_ADVICE: "green", CHAT_TYPE_DISPUTE_STATUS: "orange",
                           CHAT_TYPE_OUT_OF_SCOPE: "gray"}
