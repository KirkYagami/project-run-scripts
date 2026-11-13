import os

# ---------------------------------------------------------------- folders
DOCS_DIRECTORY = "data/docs"
PROCESSED_DIRECTORY = "processed"
# Where the two SQLite files live. Docker points this at a volume; the vector
# store below stays in database/ because it ships inside the image.
DATABASE_DIRECTORY = os.getenv("STATE_DIRECTORY", "database")
OUTPUT_DIRECTORY = "output"
MODEL_DIRECTORY = "output/models"

# ---------------------------------------------------------------- raw input files
RAW_BREAKDOWN_TRAIN_FILE = "data/machine_breakdown_train.csv"
RAW_BREAKDOWN_EVAL_FILE = "data/machine_breakdown_eval.csv"
RAW_DOWNTIME_TRAIN_FILE = "data/repair_downtime_train.csv"
RAW_DOWNTIME_EVAL_FILE = "data/repair_downtime_eval.csv"
RAW_TECHNICIAN_NOTES_FILE = "data/technician_notes.csv"

# ---------------------------------------------------------------- live fleet input
# Live machines served by the application. No answer column.
CURRENT_FLEET_FILE = "data/input/current_fleet.csv"

# ---------------------------------------------------------------- cleaned output files
CLEAN_BREAKDOWN_TRAIN_FILE = "processed/machine_breakdown_train_clean.csv"
CLEAN_BREAKDOWN_EVAL_FILE = "processed/machine_breakdown_eval_clean.csv"
CLEAN_DOWNTIME_TRAIN_FILE = "processed/repair_downtime_train_clean.csv"
CLEAN_DOWNTIME_EVAL_FILE = "processed/repair_downtime_eval_clean.csv"
CLEAN_TECHNICIAN_NOTES_FILE = "processed/technician_notes_clean.csv"

# ---------------------------------------------------------------- saved model files
BREAKDOWN_MODEL_FILE = "output/models/breakdown_model.pkl"
DOWNTIME_MODEL_FILE = "output/models/downtime_model.pkl"
PROBLEM_TYPE_MODEL_FILE = "output/models/problem_type_model.pkl"
TEXT_VECTORIZER_FILE = "output/models/text_vectorizer.pkl"
BREAKDOWN_SCHEMA_FILE = "output/models/breakdown_features.json"
DOWNTIME_SCHEMA_FILE = "output/models/downtime_features.json"

# ---------------------------------------------------------------- report files
DATA_QUALITY_REPORT_FILE = "output/data_quality_report.json"
MODEL_METRICS_FILE = "output/model_metrics.json"

# ---------------------------------------------------------------- databases
APPLICATION_DATABASE_FILE = DATABASE_DIRECTORY + "/assetguard.db"
APPLICATION_DATABASE_URL = "sqlite:///" + ("" if DATABASE_DIRECTORY.startswith("/") else "./") + APPLICATION_DATABASE_FILE
CHECKPOINT_DATABASE_FILE = DATABASE_DIRECTORY + "/checkpoint.db"
VECTOR_STORE_DIRECTORY = "database/chroma_store"
VECTOR_COLLECTION_NAME = "machine_manuals"

# ---------------------------------------------------------------- missing value tokens
# Every way "missing" is written in the raw files.
NULL_TOKEN_LIST = [
    "", " ", "  ", "   ", "NA", "N/A", "n/a", "null", "NULL",
    "-", "?", "NaN", "nan", "none", "None",
]

# ---------------------------------------------------------------- spelling corrections
# Messy value in lower case, mapped to the correct value.
MACHINE_TYPE_MAPPING = {
    "water pump": "Water Pump",
    "wtr pump": "Water Pump",
    "air compressor": "Air Compressor",
    "air comp": "Air Compressor",
    "belt conveyor": "Belt Conveyor",
    "belt conv.": "Belt Conveyor",
    "electric motor": "Electric Motor",
    "elec motor": "Electric Motor",
    "cooling unit": "Cooling Unit",
    "unit-cooling": "Cooling Unit",
    "gear unit": "Gear Unit",
    "gearunit": "Gear Unit",
}

IMPORTANCE_MAPPING = {
    "critical": "Critical", "class critical": "Critical", "level-critical": "Critical",
    "important": "Important", "class important": "Important", "level-important": "Important",
    "standard": "Standard", "class standard": "Standard", "level-standard": "Standard",
}

USAGE_PATTERN_MAPPING = {
    "always on": "Always On", "alwa": "Always On",
    "on and off": "On And Off", "on a": "On And Off",
    "backup": "Backup", "back": "Backup",
}

FACTORY_NAME_MAPPING = {
    "pune": "Pune",
    "chennai": "Chennai",
    "vadodara": "Vadodara",
    "jamshedpur": "Jamshedpur",
}

# Values that count as True. Everything else is False.
BOOLEAN_TRUE_TOKENS = ["y", "yes", "true", "t", "1"]

VALID_PROBLEM_TYPES = [
    "Bearing Wear",
    "Seal Leak",
    "Overheating",
    "Shaft Misalignment",
    "Poor Lubrication",
    "Electrical Fault",
    "Blade Damage",
    "Belt Wear",
]

# ---------------------------------------------------------------- number repair rules
# Numbers stored as text with a unit attached, such as "45.2 mm/s".
UNIT_SUFFIX_PATTERN = r"\s*(mm/s|INR|bar|hrs?|kwh|kWh)\s*"
THOUSANDS_AND_PERCENT_PATTERN = r"[,%]"

# A temperature reading above this value was recorded in Fahrenheit.
FAHRENHEIT_DETECTION_LIMIT = 110.0

# Interquartile range multiplier used to identify a sensor spike.
OUTLIER_IQR_MULTIPLIER = 3.0

# Values outside these limits are impossible, including placeholder codes.
BREAKDOWN_RANGE_LIMITS = {
    "average_load_pct": (0.0, 100.0),
    "room_humidity_pct": (0.0, 100.0),
    "running_hours_per_week": (0.0, 168.0),
    "total_running_hours": (0.0, 400000.0),
    "days_since_oil_check": (0.0, 400.0),
    "alarms_this_week": (0.0, 200.0),
    "machine_age_months": (0.0, 400.0),
}

DOWNTIME_RANGE_LIMITS = {
    "actual_downtime_hours": (0.1, 400.0),
    "longest_part_wait_days": (0.0, 400.0),
    "technicians_assigned": (1.0, 20.0),
    "approval_delay_hours": (0.0, 200.0),
    "parts_needed_count": (0.0, 50.0),
    "repairs_last_year": (0.0, 50.0),
    "machine_age_months": (0.0, 400.0),
}

TECHNICIAN_NOTE_RANGE_LIMITS = {
    "note_length_chars": (6.0, 2000.0),
}

MINIMUM_NOTE_LENGTH = 6

# Written into a text column when the original cell was empty.
UNKNOWN_CATEGORY_VALUE = "Unknown"

# ---------------------------------------------------------------- breakdown columns
BREAKDOWN_TARGET_COLUMN = "breakdown_next_30_days"

# Identifiers. Never model inputs.
BREAKDOWN_IDENTIFIER_COLUMNS = [
    "reading_id",
    "machine_id",
    "machine_code",
    "manufacturer",
    "model_number",
    "serial_number",
    "cost_center",
    "installed_date",
    "warranty_end_date",
    "reading_week_start",
    "last_technician_id",
]

BREAKDOWN_DATE_COLUMNS = [
    "installed_date",
    "warranty_end_date",
    "reading_week_start",
]

BREAKDOWN_CATEGORY_COLUMNS = [
    "machine_type",
    "factory_name",
    "production_line",
    "importance",
    "usage_pattern",
    "service_contract",
]

BREAKDOWN_NUMERIC_COLUMNS = [
    "power_rating_kw",
    "machine_age_months",
    "running_hours_per_week",
    "total_running_hours",
    "starts_per_week",
    "average_load_pct",
    "average_vibration",
    "highest_vibration",
    "vibration_change_pct",
    "average_temperature_c",
    "highest_temperature_c",
    "average_current_amp",
    "average_pressure_bar",
    "oil_dirtiness_score",
    "days_since_oil_check",
    "alarms_this_week",
    "room_temperature_c",
    "room_humidity_pct",
    "days_since_last_service",
    "services_last_year",
    "breakdowns_last_year",
    "last_inspection_score",
    "paint_condition_score",
    "operators_assigned",
    "energy_used_per_week_kwh",
    "breakdown_next_30_days",
]

TEMPERATURE_COLUMNS = [
    "average_temperature_c",
    "highest_temperature_c",
]

VIBRATION_COLUMNS = [
    "average_vibration",
    "highest_vibration",
]

# ---------------------------------------------------------------- downtime columns
DOWNTIME_TARGET_COLUMN = "actual_downtime_hours"

DOWNTIME_IDENTIFIER_COLUMNS = [
    "repair_job_id",
    "machine_id",
    "machine_code",
    "cost_center",
    "reported_date",
    "reported_by_employee_id",
]

DOWNTIME_DATE_COLUMNS = ["reported_date"]

DOWNTIME_BOOLEAN_COLUMNS = [
    "power_lockout_needed",
    "spare_in_store",
    "contractor_used",
    "is_weekend_job",
]

DOWNTIME_CATEGORY_COLUMNS = [
    "machine_type",
    "manufacturer",
    "factory_name",
    "production_line",
    "importance",
    "usage_pattern",
    "job_type",
    "priority",
    "found_by",
    "problem_type",
    "severity",
    "access_level",
    "technician_grade",
    "work_shift",
    "weather",
]

DOWNTIME_NUMERIC_COLUMNS = [
    "power_rating_kw",
    "technicians_assigned",
    "approval_delay_hours",
    "parts_needed_count",
    "longest_part_wait_days",
    "parts_cost_inr",
    "machine_age_months",
    "repairs_last_year",
    "room_temperature_c",
    "actual_downtime_hours",
]

CURRENCY_COLUMNS = ["parts_cost_inr"]

# ---------------------------------------------------------------- technician note columns
NOTE_TEXT_COLUMN = "note_text"
NOTE_TARGET_COLUMN = "problem_type"
NOTE_IDENTIFIER_COLUMN = "note_id"
NOTE_DATE_COLUMNS = ["note_date"]

# Leftover web markup in the note text.
MARKUP_PATTERN = r"<[^>]+>"
ENCODING_ARTIFACT_LIST = ["Â", "&amp;"]

# ---------------------------------------------------------------- business rules
# Policy 01.
HIGH_RISK_THRESHOLD = 0.60
MEDIUM_RISK_THRESHOLD = 0.30
RISK_BAND_HIGH = "HIGH"
RISK_BAND_MEDIUM = "MEDIUM"
RISK_BAND_LOW = "LOW"
# Asking for every band at once rather than filtering to one of them.
RISK_BAND_ALL = "ALL"

# Policy 01. Importance and risk band decide the priority.
PRIORITY_MATRIX = {
    ("Critical", "HIGH"): "Urgent", ("Critical", "MEDIUM"): "High", ("Critical", "LOW"): "Normal",
    ("Important", "HIGH"): "High", ("Important", "MEDIUM"): "Normal", ("Important", "LOW"): "Normal",
    ("Standard", "HIGH"): "Normal", ("Standard", "MEDIUM"): "Low", ("Standard", "LOW"): "Low",
}

# Safety Rule 03.
TIGHT_SPACE_DURATION_FACTOR = 1.6

# Stand-in values for a job not yet carried out, confirmed by the supervisor at review.
REPAIR_JOB_PLANNING_ASSUMPTIONS = {
    "job_type": "Repair",
    "found_by": "Sensor Alert",
    "technician_grade": "Skilled",
    "work_shift": "Morning",
    "is_weekend_job": 0,
    "approval_delay_hours": 4.0,
    "parts_cost_inr": 12000.0,
    "spare_in_store": 1,
    "longest_part_wait_days": 0.0,
    "contractor_used": 0,
    "weather": "Clear",
    "room_temperature_c": 30.0,
    "technicians_assigned": 2.0,
    "power_lockout_needed": 1,
    "parts_needed_count": 2.0,
}

# Severity recorded against each risk band.
SEVERITY_BY_RISK_BAND = {"HIGH": "Severe", "MEDIUM": "Major", "LOW": "Moderate"}

# Safety Rule 02.
STANDARD_SHUTDOWN_WINDOW = "Sunday 06:00-18:00"

# Safety Rule 02.
REVIEW_DECISION_APPROVE = "APPROVE"
REVIEW_DECISION_MODIFY = "MODIFY"
REVIEW_DECISION_REJECT = "REJECT"
REVIEW_DECISION_OPTIONS = [
    REVIEW_DECISION_APPROVE,
    REVIEW_DECISION_MODIFY,
    REVIEW_DECISION_REJECT,
]

# Safety Rule 03. Classified by the planner when the repair job is raised.
ACCESS_LEVEL_OPTIONS = ["Easy", "Normal", "Tight Space"]
ACCESS_LEVEL_TIGHT_SPACE = "Tight Space"
# The access level the downtime model is asked to assume. The tight space penalty
# belongs to Safety Rule 03 and is applied once, by the rule, on top of this.
ACCESS_LEVEL_BASELINE = "Normal"

REPAIR_JOB_STATUS_PENDING = "PENDING_REVIEW"
REPAIR_JOB_STATUS_APPROVED = "APPROVED"
REPAIR_JOB_STATUS_REJECTED = "REJECTED"
REPAIR_JOB_STATUS_OPTIONS = [
    REPAIR_JOB_STATUS_PENDING,
    REPAIR_JOB_STATUS_APPROVED,
    REPAIR_JOB_STATUS_REJECTED,
]

AGENT_RUN_STATUS_RUNNING = "RUNNING"
AGENT_RUN_STATUS_AWAITING_REVIEW = "AWAITING_REVIEW"
AGENT_RUN_STATUS_COMPLETE = "COMPLETE"

# ---------------------------------------------------------------- roles and access
ROLE_SUPERVISOR = "Supervisor"
ROLE_ENGINEER = "Engineer"
ROLE_TECHNICIAN = "Technician"
ROLE_OPTIONS = [ROLE_SUPERVISOR, ROLE_ENGINEER, ROLE_TECHNICIAN]

# Dashboard page names. The sidebar shows only the pages the signed in role allows.
PAGE_FLEET = "Fleet overview"
PAGE_MACHINE = "Machine detail"
PAGE_REVIEW = "Review queue"
PAGE_AUDIT = "Audit trail"
PAGE_CHAT = "Manual chat"

ROLE_PAGE_ACCESS = {
    ROLE_SUPERVISOR: [PAGE_FLEET, PAGE_MACHINE, PAGE_REVIEW, PAGE_AUDIT, PAGE_CHAT],
    ROLE_ENGINEER: [PAGE_FLEET, PAGE_MACHINE, PAGE_AUDIT],
    ROLE_TECHNICIAN: [PAGE_CHAT],
}

# Every endpoint belongs to one area. Hiding a page is a convenience; refusing the
# area is the control, and the service applies it whatever the dashboard shows.
AREA_FLEET = "fleet"
AREA_ADVISORY = "advisory"
AREA_REVIEW = "review"
AREA_AUDIT = "audit"
AREA_CHAT = "chat"

# Safety Rule 02. Whoever raises a shutdown request may not approve it, so the
# Engineer can open an advisory run but never reaches the review area.
ROLE_AREA_ACCESS = {
    ROLE_SUPERVISOR: [AREA_FLEET, AREA_ADVISORY, AREA_REVIEW, AREA_AUDIT, AREA_CHAT],
    ROLE_ENGINEER: [AREA_FLEET, AREA_ADVISORY, AREA_AUDIT],
    ROLE_TECHNICIAN: [AREA_CHAT],
}

# Which area each endpoint belongs to, decided by the start of its path.
AREA_BY_PATH_START = {
    "/machines": AREA_FLEET,
    "/fleet": AREA_FLEET,
    "/advisories": AREA_ADVISORY,
    "/repairjobs": AREA_AUDIT,
    "/runs": AREA_AUDIT,
    "/audit": AREA_AUDIT,
    "/chat": AREA_CHAT,
}

# The one exception to the table above. Submitting a decision is the review area
# whatever path it sits under, because that is the action Safety Rule 02 restricts.
REVIEW_PATH_ENDING = "/review"

# ---------------------------------------------------------------- sign in
# Accounts created by run_database_setup.py. Usernames are one word and passwords
# are eight digits, because they are typed by hand on the sign in form. They are
# deliberately simple: what is being demonstrated is how a password is stored and
# checked, not how hard it is to guess.
#
# The plain password is only ever read here, at setup. The database stores a
# salted hash and nothing else.
SEED_USER_ACCOUNTS = [
    {"username": "sunita", "display_name": "Sunita Rao", "role": ROLE_SUPERVISOR, "password": "11111111"},
    {"username": "deepak", "display_name": "Deepak Mehta", "role": ROLE_SUPERVISOR, "password": "11111111"},
    {"username": "anita", "display_name": "Anita Iyer", "role": ROLE_ENGINEER, "password": "22222222"},
    {"username": "rehan", "display_name": "Rehan Khan", "role": ROLE_ENGINEER, "password": "22222222"},
    {"username": "priya", "display_name": "Priya Das", "role": ROLE_ENGINEER, "password": "22222222"},
    {"username": "manoj", "display_name": "Manoj Joshi", "role": ROLE_TECHNICIAN, "password": "33333333"},
    {"username": "kavya", "display_name": "Kavya Nair", "role": ROLE_TECHNICIAN, "password": "33333333"},
    {"username": "vikram", "display_name": "Vikram Patel", "role": ROLE_TECHNICIAN, "password": "33333333"},
]

PASSWORD_HASH_ALGORITHM = "sha256"
PASSWORD_HASH_ROUNDS = 200000
PASSWORD_SALT_BYTES = 16
SESSION_TOKEN_BYTES = 24

# Sent by the dashboard on every request so the service knows who is asking.
SESSION_TOKEN_HEADER = "X-Session-Token"
SIGN_IN_FAILED_MESSAGE = "Username or password is not correct"

# ---------------------------------------------------------------- manual chat
# The five kinds of question the assistant recognises. The list is closed, so a
# reply outside it is a fault rather than a new category.
CHAT_TYPE_PROCEDURE = "PROCEDURE"
CHAT_TYPE_SAFETY = "SAFETY"
CHAT_TYPE_PARTS = "PARTS"
CHAT_TYPE_MACHINE_STATUS = "MACHINE STATUS"
CHAT_TYPE_OUT_OF_SCOPE = "OUT OF SCOPE"
CHAT_TYPE_OPTIONS = [
    CHAT_TYPE_PROCEDURE,
    CHAT_TYPE_SAFETY,
    CHAT_TYPE_PARTS,
    CHAT_TYPE_MACHINE_STATUS,
    CHAT_TYPE_OUT_OF_SCOPE,
]

# How many earlier exchanges travel with a question. Three is enough for "and what
# torque for that one?" to still find the right manual, and short enough that the
# prompt does not fill up with old conversation.
CHAT_HISTORY_TURN_LIMIT = 3

# A retrieved passage further away than this does not really answer the question.
# The reply is refused rather than answered from general knowledge, because an
# instruction that is not in a Meridian document must never reach a technician.
CHAT_MAX_RELEVANCE_DISTANCE = 0.75

CHAT_REFUSAL_MESSAGE = (
    "I can only answer from the Meridian machine manuals, safety rules and "
    "policies. I could not find anything in them that answers that."
)
CHAT_UNKNOWN_MACHINE_MESSAGE = "That machine code is not in the current fleet file."

# Most chat rows the audit page may ask for in one go.
CHAT_AUDIT_MAX_ROWS = 200

# How many the audit trail page asks for.
CHAT_AUDIT_RECENT_ROWS = 25

# ---------------------------------------------------------------- document retrieval
CHUNK_SIZE_CHARACTERS = 700
CHUNK_OVERLAP_CHARACTERS = 120
RETRIEVAL_RESULT_COUNT = 4

# Downloaded and cached on first use.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"

# ---------------------------------------------------------------- language model
GEMINI_API_KEY_VARIABLE = "GEMINI_API_KEY"
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_MAX_OUTPUT_TOKENS = 900
GEMINI_TEMPERATURE = 0.2

AGENT_NAME_PLANNER = "work_planner"
AGENT_NAME_CONDITION = "condition_analyst"
AGENT_NAME_PROBLEM = "problem_analyst"
AGENT_NAME_PROCEDURE = "procedure_advisor"
AGENT_NAME_WRITER = "repair_job_writer"
AGENT_NAME_FINALIZER = "repair_job_finalizer"
AGENT_NAME_MANUAL_ASSISTANT = "manual_assistant"

# Language model calls in one full advisory run.
EXPECTED_LLM_CALLS_PER_RUN = 6

# ---------------------------------------------------------------- passing scores
# The lowest score a trained model may reach and still be considered working. Each
# one is set well below what a sound solution reaches, so that a different but
# reasonable modelling choice is not failed, while a model that has learned almost
# nothing is. They live here rather than in the tests so the bar is part of the
# specification a student can read.
MINIMUM_BREAKDOWN_ROC_AUC = 0.80
MINIMUM_DOWNTIME_R2 = 0.55
MINIMUM_PROBLEM_TYPE_ACCURACY = 0.60

# ---------------------------------------------------------------- services
API_HOST = "0.0.0.0"
API_PORT = int(os.getenv("API_PORT", "8081"))
API_TITLE = "AssetGuard AI API"

# The dashboard reads everything from this service.
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8081")
API_REQUEST_TIMEOUT_SECONDS = 180

DASHBOARD_TITLE = "AssetGuard AI"
DASHBOARD_SUBTITLE = "Meridian Heavy Industries - Maintenance Control"

# Badge colours used by the dashboard.
RISK_BAND_BADGE_COLOURS = {
    RISK_BAND_HIGH: "red",
    RISK_BAND_MEDIUM: "orange",
    RISK_BAND_LOW: "green",
}
REVIEW_DECISION_BADGE_COLOURS = {
    REVIEW_DECISION_APPROVE: "green",
    REVIEW_DECISION_MODIFY: "blue",
    REVIEW_DECISION_REJECT: "red",
}

# ---------------------------------------------------------------- reproducibility
RANDOM_SEED = 42
VALIDATION_SPLIT_RATIO = 0.2
