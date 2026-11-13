import pytest


@pytest.fixture(scope="session")
def processed_frames():
    import pandas as pd

    from config import config

    loaded = {"problem": None}
    try:
        for file_path in [config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE,
                          config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE,
                          config.CLEAN_SURGICAL_STAYS_TRAIN_FILE,
                          config.CLEAN_SURGICAL_STAYS_EVAL_FILE,
                          config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE]:
            loaded[file_path] = pd.read_csv(file_path, keep_default_na=False, na_values=[""],
                                            low_memory=False)
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The cleaned extracts could not be read ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Every check on cleaning, features and models reads the files the data "
            "pipeline writes, so the pipeline has to have run and written all five."
        )
    return loaded


@pytest.fixture(scope="session")
def raw_frames():
    import pandas as pd

    from config import config

    loaded = {"problem": None}
    try:
        for file_path in [config.RAW_AUTHORISATION_HISTORY_TRAIN_FILE,
                          config.RAW_AUTHORISATION_HISTORY_EVAL_FILE,
                          config.RAW_SURGICAL_STAYS_TRAIN_FILE,
                          config.RAW_SURGICAL_STAYS_EVAL_FILE,
                          config.RAW_CLINICAL_NOTE_SENTENCES_FILE]:
            loaded[file_path] = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The raw extracts supplied with the project could not be read ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). The data folder has to stay as it was supplied."
        )
    return loaded


@pytest.fixture(scope="session")
def saved_models():
    from config import config

    loaded = {"problem": None}
    try:
        from modeling.model_registry import load_feature_schema, load_model

        loaded.update({
            "approval": load_model(config.APPROVAL_MODEL_FILE),
            "stay": load_model(config.STAY_MODEL_FILE),
            "evidence": load_model(config.EVIDENCE_MODEL_FILE),
            "approval_schema": list(load_feature_schema(config.APPROVAL_SCHEMA_FILE)),
            "stay_schema": list(load_feature_schema(config.STAY_SCHEMA_FILE)),
        })
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The saved models and their feature schemas could not be loaded ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Model training saves them, and every check on the models scores what "
            "training saved."
        )
    return loaded


@pytest.fixture(scope="session")
def live_files():
    from config import config

    loaded = {"problem": None}
    try:
        from data_pipeline.dataset_loader import load_raw_dataset
        from tools.request_data_tools import load_open_requests, load_request_notes

        loaded.update({
            "raw_requests": load_raw_dataset(config.OPEN_REQUESTS_FILE),
            "raw_notes": load_raw_dataset(config.REQUEST_NOTES_FILE),
            "requests": load_open_requests(),
            "notes": load_request_notes(),
        })
        for name, column_name in [("raw_requests", config.REQUEST_REFERENCE_COLUMN),
                                  ("raw_notes", config.NOTE_ID_COLUMN),
                                  ("requests", config.SERVICE_CODE_COLUMN),
                                  ("notes", config.NOTE_TEXT_COLUMN)]:
            assert column_name in getattr(loaded[name], "columns", []), (
                "The live "
                + name.replace("_", " ")
                + " came back as "
                + type(loaded[name]).__name__
                + " where they are a table holding the column "
                + column_name
                + "."
            )
    except (Exception, SystemExit) as error:
        loaded["problem"] = (
            "The live files could not be loaded ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). The queue, the screening of a live request and the workflow all start from "
            "the open requests and the documents sent with them, read through the same "
            "cleaning as the extracts."
        )
    return loaded


@pytest.fixture(scope="session")
def knowledge_collection():
    from config import config

    opened = {"problem": None}
    try:
        from knowledge.vector_index import open_vector_index

        opened["collection"] = open_vector_index(config.VECTOR_STORE_DIRECTORY)
    except (Exception, SystemExit) as error:
        opened["problem"] = (
            "The vector store could not be opened ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Knowledge indexing builds it, and every check on retrieval reads it."
        )
    return opened


@pytest.fixture(scope="session")
def document_texts():
    from config import config

    read = {"problem": None}
    try:
        from knowledge.pdf_extraction import extract_text_from_directory

        read["documents"] = extract_text_from_directory(config.DOCS_DIRECTORY)
    except (Exception, SystemExit) as error:
        read["problem"] = (
            "The document folder could not be read ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Every check on the knowledge base starts from the text of the sixteen "
            "documents."
        )
    return read


@pytest.fixture(scope="session")
def document_passages(document_texts):
    cut = {"problem": document_texts["problem"]}
    if cut["problem"] is not None:
        return cut
    try:
        from knowledge.chunk_splitting import build_chunk_records, split_documents_into_sections

        cut["documents"] = document_texts["documents"]
        cut["sections"] = split_documents_into_sections(cut["documents"])
        cut["chunks"] = build_chunk_records(cut["sections"])
    except (Exception, SystemExit) as error:
        cut["problem"] = (
            "The documents could not be split into sections and cut into passages ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Every check on the knowledge base starts from the passages the sixteen "
            "documents are cut into."
        )
    return cut


@pytest.fixture(scope="session")
def medical_policies():
    from config import config

    read = {"problem": None, "policies": {}}
    try:
        from knowledge.policy_reading import read_medical_policy

        for service_code in config.SERVICE_POLICY_DOCUMENTS:
            read["policies"][service_code] = read_medical_policy(service_code)
    except (Exception, SystemExit) as error:
        read["problem"] = (
            "The medical policies could not be read ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Each service is screened against the criteria of its own medical policy, "
            "read from that policy's document."
        )
    return read


@pytest.fixture(scope="session")
def service_client():
    service = {"problem": None}
    try:
        from fastapi.testclient import TestClient

        from api.routes import service_application

        service["client"] = TestClient(service_application, raise_server_exceptions=False)
    except (Exception, SystemExit) as error:
        service["problem"] = (
            "The REST service could not be started ("
            + type(error).__name__
            + ": "
            + str(error)[:300]
            + "). Every check on sign-in, access, the queue, the workflow and the chat goes "
            "through it."
        )
    return service


@pytest.fixture(scope="session")
def staff(service_client):
    from config import config

    signed_in = {"problem": service_client["problem"]}
    if signed_in["problem"] is not None:
        return signed_in
    try:
        nurses = [account for account in config.SEED_USER_ACCOUNTS
                  if account["role"] == config.ROLE_NURSE]
        coordinators = [account for account in config.SEED_USER_ACCOUNTS
                        if account["role"] == config.ROLE_COORDINATOR]
        representatives = [account for account in config.SEED_USER_ACCOUNTS
                           if account["role"] == config.ROLE_REPRESENTATIVE]
        for staff_key, account in [("opener", nurses[0]), ("decider", nurses[-1]),
                                   ("coordinator", coordinators[0]),
                                   ("representative", representatives[0])]:
            reply = service_client["client"].post(
                "/auth/signin",
                json={"username": account["username"], "password": account["password"]})
            assert reply.status_code == 200, (
                "Signing in as "
                + account["username"]
                + " with the password the configuration seeds returned "
                + str(reply.status_code)
                + ", so no check that needs a signed-in "
                + account["role"]
                + " can run."
            )
            signed_in[staff_key] = dict(reply.json(), headers={
                config.SESSION_TOKEN_HEADER: reply.json()["session_token"]})
    except (Exception, SystemExit) as error:
        signed_in["problem"] = (
            "The seeded staff could not be signed in ("
            + type(error).__name__
            + ": "
            + str(error)[:400]
            + "). The accounts are the ones the configuration seeds through the database "
            "setup, and a sign-in answers with the user's display name, role and a session "
            "token."
        )
    return signed_in


@pytest.fixture(scope="session")
def saved_run(service_client, staff):
    from config import config

    run = {"problem": service_client["problem"] or staff["problem"], "decision_problem": None}
    if run["problem"] is not None:
        return run
    client = service_client["client"]
    coordinator = staff["coordinator"]
    opener = staff["opener"]
    decider = staff["decider"]
    run["coordinator_request"] = ("Are the criteria met on the questionnaire, and does any "
                                  "document disagree with it?")
    run["decision_reason"] = ("Every criterion is met on the questionnaire and the documents "
                              "agree with it, so the service is authorised as requested.")
    run["opener"] = opener
    run["decider"] = decider
    for name in ["calls_at_gate", "short_reason", "unknown_decision", "decided", "final_calls",
                 "final_record", "second_review", "short_request"]:
        run[name] = {"status": None, "body": "never requested"}
    for name in ["own_decision", "closed_decision"]:
        run[name] = {"status": None, "body": "never requested", "calls_before": None,
                     "calls_after": None}
    run["run_record"] = {"problem": "never read"}
    run["heard_at_gate"] = {"problem": "never asked"}
    run["heard_after"] = {"problem": "never asked"}
    try:
        queue = client.get("/queue", params={"service_code": config.QUEUE_SERVICE_ALL},
                           headers=coordinator["headers"])
        assert queue.status_code == 200 and isinstance(queue.json(), list), (
            "The review queue returned "
            + str(queue.status_code)
            + " with "
            + queue.text[:300]
            + ", so no request could be chosen to review."
        )
        reviewed = client.get("/reviews", params={"status_value": config.REVIEW_STATUS_OPTIONS},
                              headers=coordinator["headers"])
        assert reviewed.status_code == 200, (
            "Listing the authorisation reviews returned "
            + str(reviewed.status_code)
            + " with "
            + reviewed.text[:300]
            + ", so a request nobody has reviewed yet could not be chosen."
        )
        already_reviewed = {record["request_reference"] for record in reviewed.json()}
        details = {}
        choices = []
        for queue_row in queue.json():
            if (queue_row["screening"] != config.DECISION_APPROVE
                    or queue_row["request_reference"] in already_reviewed):
                continue
            reply = client.get("/queue/" + queue_row["request_reference"],
                               headers=coordinator["headers"])
            assert reply.status_code == 200, (
                "The detail of "
                + queue_row["request_reference"]
                + " returned "
                + str(reply.status_code)
                + " with "
                + reply.text[:300]
                + ", so its site of service cannot be read."
            )
            request = reply.json()["request"]
            site = request[config.SITE_OF_SERVICE_COLUMN]
            if site == config.NOT_GIVEN_TEXT or (
                    site == config.INPATIENT_SITE
                    and request[config.REQUESTED_INPATIENT_DAYS_COLUMN] == config.NOT_GIVEN_TEXT):
                continue
            details[queue_row["request_reference"]] = reply.json()
            choices.append((queue_row["document_count"], queue_row["request_reference"]))
        assert len(choices) > 0, (
            "No request in the queue that screens APPROVE, with the site of service and any "
            "inpatient days an authorisation letter shows, is left unreviewed, so the one "
            "review run cannot be opened. Start again from an empty database."
        )
        run["request_reference"] = sorted(choices)[0][1]
        run["detail"] = details[run["request_reference"]]
        run["member_number"] = run["detail"]["request"][config.MEMBER_NUMBER_COLUMN]
        opened = client.post("/reviews",
                             json={"request_reference": run["request_reference"],
                                   "coordinator_request": run["coordinator_request"]},
                             headers=opener["headers"])
        assert opened.status_code == 201, (
            "Opening a review of "
            + run["request_reference"]
            + " returned "
            + str(opened.status_code)
            + " with "
            + opened.text[:400]
            + ", so the workflow never reached a UM Nurse Reviewer."
        )
        run["at_gate"] = opened.json()
        review_id = run["at_gate"]["review_id"]
    except (Exception, SystemExit) as error:
        run["problem"] = (
            "The one review run that the agent, workflow and record checks read could not be "
            "opened ("
            + type(error).__name__
            + ": "
            + str(error)[:600]
            + ")."
        )
        return run

    calls_path = "/reviews/" + review_id + "/calls"
    decision_path = "/reviews/" + review_id + "/decision"
    try:
        reply = client.get(calls_path, headers=coordinator["headers"])
        run["calls_at_gate"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        run["calls_at_gate"]["body"] = type(error).__name__ + ": " + str(error)[:300]

    try:
        from chat.request_status_answer import answer_request_status
        from persistence.database import session_factory
        from tools.request_data_tools import load_open_requests

        open_requests = load_open_requests()
        other_members = sorted(set(open_requests[config.MEMBER_NUMBER_COLUMN].dropna())
                               - {run["member_number"]})
        run["other_member_number"] = other_members[0]
        heard = {"problem": None}
        with session_factory() as session:
            for heard_key, question_type, member_number in [
                    ("with_member_number", config.CHAT_TYPE_REQUEST_STATUS, run["member_number"]),
                    ("with_another_member_number", config.CHAT_TYPE_REQUEST_STATUS,
                     run["other_member_number"]),
                    ("without_member_number", config.CHAT_TYPE_REQUEST_STATUS, None),
                    ("prediction", config.CHAT_TYPE_OUTCOME_PREDICTION, run["member_number"])]:
                heard[heard_key] = answer_request_status(
                    session, staff["representative"], open_requests, question_type,
                    run["request_reference"], member_number)
        run["heard_at_gate"] = heard
    except (Exception, SystemExit) as error:
        run["heard_at_gate"] = {"problem": (
            "What a Provider Services Representative hears about the request at the pause "
            "could not be worked out (" + type(error).__name__ + ": " + str(error)[:300] + ")."
        )}

    try:
        for refusal_key, decision, headers in [
                ("own_decision", config.DECISION_APPROVE, opener["headers"]),
                ("closed_decision", config.DECISION_REQUEST_INFORMATION, decider["headers"])]:
            before = client.get(calls_path, headers=coordinator["headers"]).json()
            reply = client.post(decision_path, json={"decision": decision,
                                                     "decision_reason": run["decision_reason"]},
                                headers=headers)
            after = client.get(calls_path, headers=coordinator["headers"]).json()
            run[refusal_key] = {"status": reply.status_code, "body": reply.json(),
                                "calls_before": before.get("call_count"),
                                "calls_after": after.get("call_count")}
        for refusal_key, payload in [
                ("short_reason", {"decision": config.DECISION_APPROVE, "decision_reason": "Fine."}),
                ("unknown_decision", {"decision": "ACCEPT",
                                      "decision_reason": run["decision_reason"]})]:
            reply = client.post(decision_path, json=payload, headers=decider["headers"])
            run[refusal_key] = {"status": reply.status_code, "body": reply.json()}
        reply = client.post(decision_path, json={"decision": config.DECISION_APPROVE,
                                                 "decision_reason": run["decision_reason"]},
                            headers=decider["headers"])
        run["decided"] = {"status": reply.status_code, "body": reply.json()}
        assert reply.status_code == 200, (
            "Approving the review as "
            + decider["username"]
            + ", a UM Nurse Reviewer who did not open it, returned "
            + str(reply.status_code)
            + " with "
            + reply.text[:400]
            + "."
        )
    except (Exception, SystemExit) as error:
        run["decision_problem"] = (
            "The decision on the one review run could not be recorded ("
            + type(error).__name__
            + ": "
            + str(error)[:600]
            + ")."
        )

    try:
        reply = client.get(calls_path, headers=coordinator["headers"])
        run["final_calls"] = {"status": reply.status_code, "body": reply.json()}
        reply = client.get("/reviews", params={"status_value": config.REVIEW_STATUS_OPTIONS},
                           headers=coordinator["headers"])
        matching = [record for record in reply.json() if record["review_id"] == review_id]
        run["final_record"] = {"status": reply.status_code, "body": matching}
        reply = client.post("/reviews", json={"request_reference": run["request_reference"],
                                              "coordinator_request": run["coordinator_request"]},
                            headers=coordinator["headers"])
        run["second_review"] = {"status": reply.status_code, "body": reply.json()}
        reply = client.post("/reviews", json={"request_reference": run["request_reference"],
                                              "coordinator_request": "ok"},
                            headers=coordinator["headers"])
        run["short_request"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        run["final_record"]["body"] = type(error).__name__ + ": " + str(error)[:300]

    try:
        from persistence.database import session_factory
        from persistence.models import AgentRun

        with session_factory() as session:
            stored_run = session.get(AgentRun, run["at_gate"]["run_id"])
            run["run_record"] = {"problem": None, "status": stored_run.status,
                                 "llm_call_count": stored_run.llm_call_count,
                                 "thread_id": stored_run.thread_id,
                                 "coordinator_id": stored_run.coordinator_id}
    except (Exception, SystemExit) as error:
        run["run_record"] = {"problem": (
            "The run's own record could not be read (" + type(error).__name__ + ": "
            + str(error)[:300] + ")."
        )}

    try:
        from chat.request_status_answer import answer_request_status
        from persistence.database import session_factory
        from tools.request_data_tools import load_open_requests

        open_requests = load_open_requests()
        heard = {"problem": None}
        with session_factory() as session:
            for heard_key, question_type, member_number in [
                    ("with_member_number", config.CHAT_TYPE_REQUEST_STATUS, run["member_number"]),
                    ("with_another_member_number", config.CHAT_TYPE_REQUEST_STATUS,
                     run["other_member_number"]),
                    ("prediction", config.CHAT_TYPE_OUTCOME_PREDICTION, run["member_number"]),
                    ("staff", config.CHAT_TYPE_REQUEST_STATUS, None)]:
                asker = staff["representative"]
                if heard_key == "staff":
                    asker = staff["coordinator"]
                heard[heard_key] = answer_request_status(
                    session, asker, open_requests, question_type, run["request_reference"],
                    member_number)
        run["heard_after"] = heard
    except (Exception, SystemExit) as error:
        run["heard_after"] = {"problem": (
            "What is heard about the request after the decision could not be worked out ("
            + type(error).__name__ + ": " + str(error)[:300] + ")."
        )}
    return run


@pytest.fixture(scope="session")
def chat_replies(service_client, staff):
    replies = {"problem": service_client["problem"] or staff["problem"],
               "policy_question": ("What does the medical policy for a total knee replacement "
                                   "ask for before it is authorised?"),
               "policy": {"status": None, "body": "never asked"},
               "turns": {"status": None, "body": "never read"},
               "latest_turn_before": 0}
    if replies["problem"] is not None:
        return replies
    client = service_client["client"]
    asker = staff["coordinator"]
    replies["asker"] = asker["username"]
    replies["someone_else"] = staff["representative"]["username"]
    try:
        earlier = client.get("/chat/turns", params={"turn_limit": 1}, headers=asker["headers"])
        if earlier.status_code == 200:
            replies["latest_turn_before"] = max([turn["turn_id"] for turn in earlier.json()]
                                                + [0])
        reply = client.post("/chat/ask", json={"question": replies["policy_question"]},
                            headers=asker["headers"])
        replies["policy"] = {"status": reply.status_code, "body": reply.json()}
        reply = client.get("/chat/turns", params={"turn_limit": 5}, headers=asker["headers"])
        replies["turns"] = {"status": reply.status_code, "body": reply.json()}
    except (Exception, SystemExit) as error:
        replies["policy"]["body"] = type(error).__name__ + ": " + str(error)[:300]
    return replies


def test_cleaning_keeps_each_request_once_at_its_latest_submission_and_only_with_a_decision(
        raw_frames, processed_frames, tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.dataset_loader import load_raw_dataset, save_processed_dataset
    from data_pipeline.history_cleaning import clean_history_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    rebuilt_path = str(tmp_path / "authorisation_history_eval_cleaned_again.csv")
    save_processed_dataset(
        clean_history_dataset(load_raw_dataset(config.RAW_AUTHORISATION_HISTORY_EVAL_FILE)),
        rebuilt_path)
    rebuilt = pd.read_csv(rebuilt_path, keep_default_na=False, na_values=[""], low_memory=False)
    saved = processed_frames[config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE]
    assert rebuilt.shape == saved.shape and rebuilt.equals(saved), (
        "Cleaning "
        + config.RAW_AUTHORISATION_HISTORY_EVAL_FILE
        + " again gives "
        + str(rebuilt.shape)
        + " rows and columns where "
        + config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE
        + " holds "
        + str(saved.shape)
        + ", or the same shape with different values. Every check reads the cleaned files, "
        "so they have to be what the cleaning code produces now: run the data pipeline "
        "again after changing it."
    )
    for raw_path, clean_path in [
            (config.RAW_AUTHORISATION_HISTORY_TRAIN_FILE,
             config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE),
            (config.RAW_AUTHORISATION_HISTORY_EVAL_FILE,
             config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE)]:
        raw_frame = raw_frames[raw_path]
        clean_frame = processed_frames[clean_path]
        written_digits = raw_frame[config.REQUEST_REFERENCE_COLUMN].str.extract(
            r"([0-9]{6})", expand=False)
        submissions = pd.DataFrame({
            "reference": "PA-" + written_digits,
            "sequence": raw_frame[config.SUBMISSION_SEQUENCE_COLUMN].astype(int),
            "answered": ~raw_frame[config.HISTORY_TARGET_COLUMN].str.strip().str.lower().isin(
                config.NULL_TOKENS),
        })
        latest = submissions.sort_values("sequence", kind="stable").drop_duplicates(
            "reference", keep="last").set_index("reference")
        repeated = int(clean_frame[config.REQUEST_REFERENCE_COLUMN].duplicated().sum())
        assert repeated == 0, (
            clean_path
            + " still holds "
            + str(repeated)
            + " rows whose request reference appears on another row. A request submitted again "
            "is one request, and a model fitted on it twice weighs it twice."
        )
        expected_kept = sorted(latest.index[latest["answered"]])
        kept = sorted(clean_frame[config.REQUEST_REFERENCE_COLUMN].astype(str))
        assert kept == expected_kept, (
            clean_path
            + " keeps "
            + str(len(kept))
            + " requests where "
            + raw_path
            + " holds "
            + str(len(expected_kept))
            + " whose latest submission gives a decision, for example it keeps "
            + str(sorted(set(kept) - set(expected_kept))[:3])
            + " and leaves out "
            + str(sorted(set(expected_kept) - set(kept))[:3])
            + ". A request is kept once, at its highest submission sequence, and only when that "
            "submission gives the decision; a decision is never taken from an earlier one."
        )
        resubmitted = submissions["reference"].value_counts()
        resubmitted = sorted(set(resubmitted.index[resubmitted > 1]) & set(kept))
        kept_rows = clean_frame.set_index(config.REQUEST_REFERENCE_COLUMN)
        wrong_sequence = [reference for reference in resubmitted
                          if int(kept_rows.loc[reference, config.SUBMISSION_SEQUENCE_COLUMN])
                          != int(latest.loc[reference, "sequence"])]
        assert len(resubmitted) > 0 and len(wrong_sequence) == 0, (
            clean_path
            + " keeps an earlier submission of "
            + str(len(wrong_sequence))
            + " of the "
            + str(len(resubmitted))
            + " requests submitted more than once, for example "
            + str(wrong_sequence[:3])
            + ". The submission with the highest sequence is the request, wherever it stands "
            "among the rows."
        )
        decisions = sorted(clean_frame[config.HISTORY_TARGET_COLUMN].astype(str).unique())
        assert decisions == sorted(config.APPROVAL_TARGET_ENCODING), (
            "The decision column of "
            + clean_path
            + " holds "
            + str(decisions[:6])
            + " where every spelling is folded onto "
            + str(sorted(config.APPROVAL_TARGET_ENCODING))
            + " and no row is kept without one."
        )


def test_heights_and_weights_in_the_offices_notations_become_centimetres_and_kilograms(
        raw_frames, tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.dataset_loader import load_raw_dataset
    from data_pipeline.history_cleaning import clean_history_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    raw_frame = raw_frames[config.RAW_AUTHORISATION_HISTORY_EVAL_FILE]
    answered = ~raw_frame[config.HISTORY_TARGET_COLUMN].str.strip().str.lower().isin(
        config.NULL_TOKENS)
    templates = raw_frame[answered].drop_duplicates(config.REQUEST_REFERENCE_COLUMN).head(12)
    templates = templates.reset_index(drop=True)
    planted = [("5 ft 8 in", 172.7, "186 lb", 84.4), ("6 ft 0 in", 182.9, "13 st 4 lb", 84.4),
               ("5 ft 10 in", 177.8, "15 st 7 lb", 98.4), ("1.72 m", 172.0, "84.3 kg", 84.3),
               ("172 cm", 172.0, "84", 84.0), ("168.5", 168.5, "262 lb", 118.8),
               ("4 ft 11 in", 149.9, "9 st 0 lb", 57.2), ("1.65 m", 165.0, "100 lb", 45.4)]
    rows = templates.head(len(planted)).copy()
    for position, measurements in enumerate(planted):
        rows.loc[position, config.REQUEST_REFERENCE_COLUMN] = "PA-9" + str(10001 + position)
        rows.loc[position, config.SUBMISSION_SEQUENCE_COLUMN] = "1"
        rows.loc[position, config.HEIGHT_COLUMN] = measurements[0]
        rows.loc[position, config.WEIGHT_COLUMN] = measurements[2]
    planted_path = str(tmp_path / "planted_measurements.csv")
    rows.to_csv(planted_path, index=False)
    cleaned = clean_history_dataset(load_raw_dataset(planted_path)).set_index(
        config.REQUEST_REFERENCE_COLUMN)
    wrong = []
    for position, (height, height_cm, weight, weight_kg) in enumerate(planted):
        reference = "PA-9" + str(10001 + position)
        got_height = cleaned.loc[reference, config.HEIGHT_COLUMN]
        got_weight = cleaned.loc[reference, config.WEIGHT_COLUMN]
        if pd.isna(got_height) or abs(float(got_height) - height_cm) > 1e-9:
            wrong.append(height + " read as " + str(got_height) + " cm, not " + str(height_cm))
        if pd.isna(got_weight) or abs(float(got_weight) - weight_kg) > 1e-9:
            wrong.append(weight + " read as " + str(got_weight) + " kg, not " + str(weight_kg))
    assert len(wrong) == 0, (
        "Heights and weights are not converted as the Prior Authorisation Rules set out: "
        + "; ".join(wrong[:6])
        + ". A height in feet and inches or metres becomes centimetres, a weight in stones and "
        "pounds or pounds becomes kilograms, each worked out exactly and kept to one decimal, "
        "half up."
    )
    for column_name, written in [(config.HEIGHT_COLUMN, "5 ft 12 in"),
                                 (config.HEIGHT_COLUMN, "1.7 m"),
                                 (config.HEIGHT_COLUMN, "5 feet 8 inches"),
                                 (config.WEIGHT_COLUMN, "13 st 14 lb"),
                                 (config.WEIGHT_COLUMN, "186 pounds"),
                                 (config.WEIGHT_COLUMN, "0 lb")]:
        unreadable = templates.head(1).copy()
        unreadable.loc[0, column_name] = written
        unreadable_path = str(tmp_path / "unreadable_measurement.csv")
        unreadable.to_csv(unreadable_path, index=False)
        refusal = None
        try:
            clean_history_dataset(load_raw_dataset(unreadable_path))
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and column_name in refusal and written in refusal, (
            "Cleaning a "
            + column_name
            + " written "
            + written
            + " gave "
            + str(refusal)
            + ". A measurement outside the notations the offices write, or of nought, is "
            "refused with a ValueError naming the column and the value as written, never "
            "guessed at or left blank."
        )


def test_request_references_member_numbers_and_diagnosis_codes_are_made_canonical(
        raw_frames, processed_frames, tmp_path):
    from config import config
    from data_pipeline.dataset_loader import load_raw_dataset
    from data_pipeline.history_cleaning import clean_history_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    raw_frame = raw_frames[config.RAW_AUTHORISATION_HISTORY_EVAL_FILE]
    answered = ~raw_frame[config.HISTORY_TARGET_COLUMN].str.strip().str.lower().isin(
        config.NULL_TOKENS)
    templates = raw_frame[answered].drop_duplicates(config.REQUEST_REFERENCE_COLUMN).head(6)
    templates = templates.reset_index(drop=True)
    planted = [("pa-910101", "PA-910101", "bwh-4100001", "BWH-4100001", "M5450", "M54.50"),
               ("PA 910102", "PA-910102", "BWH4100002", "BWH-4100002", "M17.11", "M17.11"),
               ("PA910103", "PA-910103", "BWH 4100003", "BWH-4100003", "G4733", "G47.33"),
               ("910104", "PA-910104", "4100004", "BWH-4100004", "E669", "E66.9")]
    rows = templates.head(len(planted)).copy()
    for position, identifiers in enumerate(planted):
        rows.loc[position, config.REQUEST_REFERENCE_COLUMN] = identifiers[0]
        rows.loc[position, config.SUBMISSION_SEQUENCE_COLUMN] = "1"
        rows.loc[position, config.MEMBER_NUMBER_COLUMN] = identifiers[2]
        rows.loc[position, config.DIAGNOSIS_CODE_COLUMN] = identifiers[4]
    planted_path = str(tmp_path / "planted_identifiers.csv")
    rows.to_csv(planted_path, index=False)
    cleaned = clean_history_dataset(load_raw_dataset(planted_path))
    got = sorted(zip(cleaned[config.REQUEST_REFERENCE_COLUMN],
                     cleaned[config.MEMBER_NUMBER_COLUMN], cleaned[config.DIAGNOSIS_CODE_COLUMN],
                     strict=True))
    expected = sorted((identifiers[1], identifiers[3], identifiers[5]) for identifiers in planted)
    assert got == expected, (
        "The identifiers cleaned to "
        + str(got)
        + " where the Rules read them as "
        + str(expected)
        + ". A request reference written in lower case, with a space, without the hyphen or as "
        "six digits is PA- and the six digits; a member number from any channel is BWH- and the "
        "seven digits; an ICD-10-CM code sent without its dot gets the dot back after the third "
        "character."
    )
    for column_name, written in [(config.REQUEST_REFERENCE_COLUMN, "PA-91010"),
                                 (config.REQUEST_REFERENCE_COLUMN, "QA-910105"),
                                 (config.MEMBER_NUMBER_COLUMN, "BWH-410000"),
                                 (config.MEMBER_NUMBER_COLUMN, "BWX-4100005"),
                                 (config.DIAGNOSIS_CODE_COLUMN, "5450")]:
        unreadable = templates.head(1).copy()
        unreadable.loc[0, column_name] = written
        unreadable_path = str(tmp_path / "unreadable_identifier.csv")
        unreadable.to_csv(unreadable_path, index=False)
        refusal = None
        try:
            clean_history_dataset(load_raw_dataset(unreadable_path))
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and column_name in refusal and written in refusal, (
            "Cleaning a "
            + column_name
            + " written "
            + written
            + " gave "
            + str(refusal)
            + ". An identifier in no notation the Rules allow is refused with a ValueError "
            "naming the column and the value."
        )
    for clean_path in [config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE,
                       config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE]:
        clean_frame = processed_frames[clean_path]
        for column_name, pattern in [
                (config.REQUEST_REFERENCE_COLUMN, config.CANONICAL_REQUEST_REFERENCE_PATTERN),
                (config.MEMBER_NUMBER_COLUMN, config.CANONICAL_MEMBER_NUMBER_PATTERN),
                (config.DIAGNOSIS_CODE_COLUMN, config.CANONICAL_DIAGNOSIS_CODE_PATTERN)]:
            values = clean_frame[column_name].dropna().astype(str)
            stray = sorted(values[~values.str.fullmatch(pattern)].unique())
            assert len(values) > 0 and len(stray) == 0, (
                clean_path
                + " holds "
                + str(len(stray))
                + " "
                + column_name
                + " values that are not canonical, for example "
                + str(stray[:3])
                + "."
            )


def test_answers_in_words_take_one_spelling_and_durations_scores_and_classes_are_read(
        raw_frames, processed_frames, tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.dataset_loader import load_raw_dataset
    from data_pipeline.history_cleaning import clean_history_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    for clean_path, value_mappings in [
            (config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE, config.HISTORY_VALUE_MAPPINGS),
            (config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE, config.HISTORY_VALUE_MAPPINGS),
            (config.CLEAN_SURGICAL_STAYS_TRAIN_FILE, config.STAY_VALUE_MAPPINGS),
            (config.CLEAN_SURGICAL_STAYS_EVAL_FILE, config.STAY_VALUE_MAPPINGS),
            (config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE, config.SENTENCE_VALUE_MAPPINGS)]:
        clean_frame = processed_frames[clean_path]
        for column_name, value_mapping in value_mappings.items():
            found = set(clean_frame[column_name].dropna().astype(str))
            stray = sorted(found - set(value_mapping.values()))
            assert len(stray) == 0, (
                column_name
                + " in "
                + clean_path
                + " holds "
                + str(stray[:5])
                + ", which are not among its canonical values "
                + str(sorted(set(value_mapping.values()))[:6])
                + ". Every spelling an office writes is folded onto one."
            )
    raw_frame = raw_frames[config.RAW_AUTHORISATION_HISTORY_EVAL_FILE]
    answered = ~raw_frame[config.HISTORY_TARGET_COLUMN].str.strip().str.lower().isin(
        config.NULL_TOKENS)
    template = raw_frame[answered].drop_duplicates(config.REQUEST_REFERENCE_COLUMN).head(1)
    planted = [
        ({"received_channel": "EDI", "urgency": "Routine", "previous_scan_of_region": "y",
          "conservative_treatment_weeks": "47 days", "knee_function_score": "22/48",
          "xray_grade": "KL grade 3", "asa_physical_status": "ASA II",
          "months_since_last_scan": "14 mo", "other_conditions": "HTN, OSA"},
         {"received_channel": "Electronic", "urgency": "Standard",
          "previous_scan_of_region": config.BOOLEAN_YES, "conservative_treatment_weeks": 6,
          "knee_function_score": 22, "xray_grade": 3, "asa_physical_status": 2,
          "months_since_last_scan": 14,
          "other_conditions": "Hypertension; Obstructive sleep apnoea"}),
        ({"received_channel": "facsimile", "urgency": "EXPEDITED",
          "previous_scan_of_region": "False", "conservative_treatment_weeks": "49 days",
          "knee_function_score": "48", "xray_grade": "Grade 0", "asa_physical_status": "IV",
          "months_since_last_scan": "1 months", "other_conditions": "none"},
         {"received_channel": "Fax", "urgency": "Urgent",
          "previous_scan_of_region": config.BOOLEAN_NO, "conservative_treatment_weeks": 7,
          "knee_function_score": 48, "xray_grade": 0, "asa_physical_status": 4,
          "months_since_last_scan": 1, "other_conditions": config.NO_OTHER_CONDITIONS}),
        ({"received_channel": "Provider Portal", "urgency": "standard",
          "previous_scan_of_region": "No", "conservative_treatment_weeks": "6 wks",
          "knee_function_score": "0/48", "xray_grade": "KL 4", "asa_physical_status": "ASA 3",
          "months_since_last_scan": "0", "other_conditions": "Type II diabetes; asthma"},
         {"received_channel": "Portal", "urgency": "Standard",
          "previous_scan_of_region": config.BOOLEAN_NO, "conservative_treatment_weeks": 6,
          "knee_function_score": 0, "xray_grade": 4, "asa_physical_status": 3,
          "months_since_last_scan": 0, "other_conditions": "Asthma; Type 2 diabetes"})]
    rows = pd.concat([template] * len(planted), ignore_index=True)
    for position, answers in enumerate(planted):
        rows.loc[position, config.REQUEST_REFERENCE_COLUMN] = "PA-92000" + str(position)
        rows.loc[position, config.SUBMISSION_SEQUENCE_COLUMN] = "1"
        for column_name, value in answers[0].items():
            rows.loc[position, column_name] = value
    planted_path = str(tmp_path / "planted_answers.csv")
    rows.to_csv(planted_path, index=False)
    cleaned = clean_history_dataset(load_raw_dataset(planted_path)).set_index(
        config.REQUEST_REFERENCE_COLUMN)
    wrong = []
    for position, (written, expected) in enumerate(planted):
        for column_name, wanted in expected.items():
            got = cleaned.loc["PA-92000" + str(position), column_name]
            if isinstance(wanted, int):
                matches = not pd.isna(got) and float(got) == wanted
            else:
                matches = got == wanted
            if not matches:
                wrong.append(column_name + " " + repr(written[column_name]) + " read as "
                             + repr(got) + ", not " + repr(wanted))
    assert len(wrong) == 0, (
        "Answers are not read as the Prior Authorisation Rules set out: "
        + "; ".join(wrong[:6])
        + ". Answers in words take their canonical spelling, days of treatment become whole "
        "weeks rounded down, a score written over its scale top keeps its score, an X-ray "
        "grade and an ASA class are read in every way an office writes them, and a list of "
        "conditions becomes its canonical names, sorted and joined."
    )
    for column_name, written in [(config.URGENCY_COLUMN, "Soon"),
                                 (config.TREATMENT_WEEKS_COLUMN, "six weeks"),
                                 (config.ASA_CLASS_COLUMN, "ASA V"),
                                 (config.OTHER_CONDITIONS_COLUMN, "Hypertension; Gout")]:
        unreadable = template.copy()
        unreadable[column_name] = written
        unreadable_path = str(tmp_path / "unreadable_answer.csv")
        unreadable.to_csv(unreadable_path, index=False)
        refusal = None
        try:
            clean_history_dataset(load_raw_dataset(unreadable_path))
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and column_name in refusal and written in refusal, (
            "Cleaning a "
            + column_name
            + " written "
            + written
            + " gave "
            + str(refusal)
            + ". A value with no canonical reading is refused with a ValueError naming the "
            "column and the value."
        )


def test_impossible_readings_become_missing_and_blank_or_repeated_keys_are_refused(
        raw_frames, tmp_path):
    import pandas as pd

    from config import config
    from data_pipeline.dataset_loader import load_raw_dataset
    from data_pipeline.history_cleaning import clean_history_dataset
    from data_pipeline.sentence_cleaning import clean_sentence_dataset
    from data_pipeline.stay_cleaning import clean_stay_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    raw_history = raw_frames[config.RAW_AUTHORISATION_HISTORY_EVAL_FILE]
    answered = ~raw_history[config.HISTORY_TARGET_COLUMN].str.strip().str.lower().isin(
        config.NULL_TOKENS)
    template = raw_history[answered].drop_duplicates(config.REQUEST_REFERENCE_COLUMN).head(1)
    rows = pd.concat([template] * 3, ignore_index=True)
    planted = [("xray_grade", "5"), ("knee_function_score", "49/48"),
               ("sleepiness_score", "25"), ("provider_prior_approval_rate_pct", "101 %"),
               ("decision_turnaround_days", "-2 days")]
    for position in range(3):
        rows.loc[position, config.REQUEST_REFERENCE_COLUMN] = "PA-93000" + str(position)
        rows.loc[position, config.SUBMISSION_SEQUENCE_COLUMN] = "1"
    for column_name, written in planted:
        rows.loc[0, column_name] = written
    for position, blank_token in [(1, "N/A"), (2, "Not recorded")]:
        rows.loc[position, config.RED_FLAG_COLUMN] = blank_token
        rows.loc[position, config.HEIGHT_COLUMN] = " " + blank_token.lower() + " "
    planted_path = str(tmp_path / "planted_impossible.csv")
    rows.to_csv(planted_path, index=False)
    cleaned = clean_history_dataset(load_raw_dataset(planted_path)).set_index(
        config.REQUEST_REFERENCE_COLUMN)
    still_read = [column_name + " " + written for column_name, written in planted
                  if not pd.isna(cleaned.loc["PA-930000", column_name])]
    assert len(cleaned) == 3 and len(still_read) == 0, (
        "Readings that cannot be true were kept: "
        + str(still_read)
        + ". A grade above 4, a score above its scale top, a percentage above 100 or a "
        "turnaround below nought cannot be true, so the reading becomes missing and the row "
        "stays."
    )
    unblanked = [str(position) for position in [1, 2]
                 if not pd.isna(cleaned.loc["PA-93000" + str(position), config.RED_FLAG_COLUMN])
                 or not pd.isna(cleaned.loc["PA-93000" + str(position), config.HEIGHT_COLUMN])]
    assert len(unblanked) == 0, (
        "An answer written as N/A or Not recorded, with spaces around it or in small letters, "
        "was read as a value on planted rows "
        + str(unblanked)
        + ". The Rules treat N/A, NA, n/a, -, unknown and Not recorded as no answer: the item "
        "is blank."
    )
    raw_stays = raw_frames[config.RAW_SURGICAL_STAYS_EVAL_FILE]
    stay_template = raw_stays.drop_duplicates(config.ADMISSION_REFERENCE_COLUMN).head(2)
    stay_rows = stay_template.reset_index(drop=True).copy()
    stay_rows.loc[0, config.ADMISSION_REFERENCE_COLUMN] = "ADM-9400001"
    stay_rows.loc[0, config.BODY_MASS_INDEX_COLUMN] = "120"
    stay_rows.loc[0, config.STAY_TARGET_COLUMN] = "3 nights"
    stay_rows.loc[1, config.ADMISSION_REFERENCE_COLUMN] = "ADM-9400002"
    stay_rows.loc[1, config.STAY_TARGET_COLUMN] = "0"
    stay_path = str(tmp_path / "planted_stays.csv")
    stay_rows.to_csv(stay_path, index=False)
    cleaned_stays = clean_stay_dataset(load_raw_dataset(stay_path))
    kept = cleaned_stays[config.ADMISSION_REFERENCE_COLUMN].astype(str).tolist()
    assert (kept == ["ADM-9400001"]
            and pd.isna(cleaned_stays[config.BODY_MASS_INDEX_COLUMN].iloc[0])), (
        "Two planted stays cleaned to "
        + str(cleaned_stays[[config.ADMISSION_REFERENCE_COLUMN, config.BODY_MASS_INDEX_COLUMN,
                             config.STAY_TARGET_COLUMN]].to_dict("records"))
        + ". A body mass index of 120 cannot be true and becomes missing, keeping the stay; a "
        "stay of nought nights is no stay, so its length becomes missing and, being the "
        "answer, takes the row with it."
    )
    raw_sentences = raw_frames[config.RAW_CLINICAL_NOTE_SENTENCES_FILE]
    for label, cleaner, frame, column_name, value in [
            ("a stay with no admission reference", clean_stay_dataset, stay_template,
             config.ADMISSION_REFERENCE_COLUMN, ""),
            ("two stays sharing an admission reference", clean_stay_dataset, stay_template,
             config.ADMISSION_REFERENCE_COLUMN, "ADM-9400003"),
            ("a sentence with no identifier", clean_sentence_dataset, raw_sentences.head(2),
             config.SENTENCE_ID_COLUMN, ""),
            ("two sentences sharing an identifier", clean_sentence_dataset, raw_sentences.head(2),
             config.SENTENCE_ID_COLUMN, "SEN-9400004")]:
        keyed = frame.reset_index(drop=True).copy()
        keyed[column_name] = value
        keyed_path = str(tmp_path / "keyed.csv")
        keyed.to_csv(keyed_path, index=False)
        refusal = None
        try:
            cleaner(load_raw_dataset(keyed_path))
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and column_name in refusal and (value in refusal), (
            "Cleaning "
            + label
            + " gave "
            + str(refusal)
            + ". Every admission and every sentence is named and appears once: a blank or "
            "repeated identifier is refused with a ValueError naming the column (and the "
            "repeated value), never dropped or numbered quietly."
        )


def test_saved_schemas_leave_out_the_answer_every_identifier_and_what_follows_the_decision(
        saved_models):
    from config import config

    assert saved_models["problem"] is None, saved_models["problem"]
    approval_schema = saved_models["approval_schema"]
    stay_schema = saved_models["stay_schema"]
    for schema_name, schema, configured in [
            ("approval", approval_schema,
             config.APPROVAL_NUMERIC_FEATURES + config.APPROVAL_CATEGORICAL_FEATURES),
            ("stay", stay_schema, config.STAY_NUMERIC_FEATURES + config.STAY_CATEGORICAL_FEATURES)]:
        assert len(schema) == len(set(schema)) and sorted(schema) == sorted(configured), (
            "The saved "
            + schema_name
            + " schema names "
            + str(schema)
            + " where the configuration's features are "
            + str(configured)
            + ", each once."
        )
    approval_never = [config.HISTORY_TARGET_COLUMN, config.REQUEST_REFERENCE_COLUMN,
                      config.SUBMISSION_SEQUENCE_COLUMN, config.MEMBER_NUMBER_COLUMN,
                      "provider_id", config.PROVIDER_NAME_COLUMN, config.PLANNED_FACILITY_COLUMN,
                      config.DIAGNOSIS_CODE_COLUMN, "information_requested", "reviewer_level",
                      "decision_turnaround_days", "member_sex", "member_region", "plan_code"]
    stay_never = [config.STAY_TARGET_COLUMN, config.ADMISSION_REFERENCE_COLUMN,
                  config.MEMBER_NUMBER_COLUMN, "hospital_id", "hospital_name",
                  "complication_recorded", "discharge_destination", "readmission_recorded",
                  "member_sex", "member_region", "plan_code"]
    for schema_name, schema, never in [("approval", approval_schema, approval_never),
                                       ("stay", stay_schema, stay_never)]:
        leaked = sorted(set(schema) & set(never))
        assert len(leaked) == 0, (
            "The saved "
            + schema_name
            + " schema feeds the model "
            + str(leaked)
            + ". The answer, an identifier, anything recorded only once the decision was "
            "taken or the stay was over, and the member's sex, region and plan are never "
            "features: a model fed them learns what it cannot know at the time, or learns "
            "who the member is rather than what was asked."
        )
    counts_used = [column_name for column_name in config.CRITERIA_COUNT_COLUMNS
                   if column_name in approval_schema]
    assert counts_used == config.CRITERIA_COUNT_COLUMNS, (
        "The approval schema uses the criteria counts "
        + str(counts_used)
        + " where the model is fed all three - criteria Met, Not met and Not documented - so "
        "it learns from the screening a live request is shown with."
    )


def test_the_approval_features_count_each_requests_criteria_under_its_own_policy(
        processed_frames, medical_policies):
    from config import config
    from data_pipeline.feature_builder import add_criteria_counts
    from tools.screening_tools import screen_request

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    policies = medical_policies["policies"]
    history = processed_frames[config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE]
    sample = history.groupby(config.SERVICE_CODE_COLUMN, group_keys=False).head(40)
    sample = sample.reset_index(drop=True)
    counted = add_criteria_counts(sample, policies)
    missing = [column_name for column_name in config.CRITERIA_COUNT_COLUMNS
               if column_name not in counted.columns]
    assert len(missing) == 0 and len(counted) == len(sample), (
        "add_criteria_counts returned "
        + str(len(counted))
        + " rows of the "
        + str(len(sample))
        + " it was given, without the columns "
        + str(missing)
        + "."
    )
    assert list(counted[config.REQUEST_REFERENCE_COLUMN]) == list(
        sample[config.REQUEST_REFERENCE_COLUMN]), (
        "add_criteria_counts returned the requests in another order, so each row's counts no "
        "longer sit beside its own answers."
    )
    wrong = []
    for request, counted_row in zip(sample.to_dict("records"), counted.to_dict("records"),
                                    strict=True):
        screening = screen_request(request, policies[request[config.SERVICE_CODE_COLUMN]])
        expected = [screening[column_name] for column_name in config.CRITERIA_COUNT_COLUMNS]
        got = [int(counted_row[column_name]) for column_name in config.CRITERIA_COUNT_COLUMNS]
        criteria_count = len(policies[request[config.SERVICE_CODE_COLUMN]]["criteria"])
        if got != expected or sum(got) != criteria_count:
            wrong.append(request[config.REQUEST_REFERENCE_COLUMN] + " counted " + str(got)
                         + " where its own policy's screening gives " + str(expected))
    assert len(wrong) == 0, (
        "The criteria counts disagree with the screening under each request's own policy: "
        + "; ".join(wrong[:4])
        + ". Each history request is screened against the medical policy of its own service, as "
        "a live request is, and its criteria Met, Not met and Not documented add up to that "
        "policy's criteria."
    )
    crossed = dict(policies)
    crossed["RAD-CSM"] = policies["RAD-LSM"]
    cervical = sample[sample[config.SERVICE_CODE_COLUMN] == "RAD-CSM"].head(1)
    refusal = None
    try:
        add_criteria_counts(cervical, crossed)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and cervical[config.REQUEST_REFERENCE_COLUMN].iloc[0] in refusal, (
        "A cervical spine request screened with the lumbar spine policy handed over under its "
        "service code gave "
        + str(refusal)
        + ". A policy written for another service is refused, naming the request, never used "
        "to screen it."
    )
    without_policy = dict(policies)
    del without_policy["SLP-PSG"]
    sleep_study = sample[sample[config.SERVICE_CODE_COLUMN] == "SLP-PSG"].head(1)
    refusal = None
    try:
        add_criteria_counts(sleep_study, without_policy)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and "SLP-PSG" in refusal, (
        "A sleep study request with no policy handed over for its service gave "
        + str(refusal)
        + ". A request whose service has no policy cannot be screened and is refused, naming "
        "the service."
    )


def test_model_inputs_are_built_in_the_saved_schema_order_with_gaps_left_as_gaps(
        processed_frames, saved_models, medical_policies):
    import numpy as np

    from config import config
    from data_pipeline.feature_builder import add_criteria_counts, build_feature_frame

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    history = processed_frames[config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE].head(60)
    history = add_criteria_counts(history, medical_policies["policies"])
    stays = processed_frames[config.CLEAN_SURGICAL_STAYS_EVAL_FILE].head(60)
    for name, frame, numeric_columns, categorical_columns, schema in [
            ("approval", history, config.APPROVAL_NUMERIC_FEATURES,
             config.APPROVAL_CATEGORICAL_FEATURES, saved_models["approval_schema"]),
            ("stay", stays, config.STAY_NUMERIC_FEATURES, config.STAY_CATEGORICAL_FEATURES,
             saved_models["stay_schema"])]:
        frame = frame.copy()
        for column_name in numeric_columns:
            frame[column_name] = frame[column_name].astype(float)
            frame.loc[frame.index[0], column_name] = float("nan")
        for column_name in categorical_columns:
            frame[column_name] = frame[column_name].astype(object)
            frame.loc[frame.index[1], column_name] = None
        shuffled = frame[list(reversed(list(frame.columns)))]
        features = build_feature_frame(shuffled, numeric_columns, categorical_columns)
        assert list(features.columns) == schema, (
            "The "
            + name
            + " inputs are built in the order "
            + str(list(features.columns))
            + " where the saved schema reads "
            + str(schema)
            + ". The model takes its inputs in the order it was trained on, whatever order the "
            "table it is given holds them in."
        )
        assert len(features) == len(frame) and list(features.index) == list(frame.index), (
            "build_feature_frame returned "
            + str(len(features))
            + " rows for "
            + str(len(frame))
            + ", or in another order."
        )
        for column_name in numeric_columns:
            same = np.allclose(features[column_name].to_numpy(dtype=float),
                               frame[column_name].to_numpy(dtype=float), equal_nan=True)
            assert same, (
                column_name
                + " is changed on its way into the "
                + name
                + " model. A number goes in as it was cleaned, a gap as a gap."
            )
        for column_name in categorical_columns:
            gaps = frame[column_name].isna()
            built = features[column_name]
            assert bool(built[gaps].isna().all()) and list(built[~gaps]) == list(
                frame.loc[~gaps, column_name]), (
                column_name
                + " is changed on its way into the "
                + name
                + " model: a gap became "
                + str(sorted(set(built[gaps].astype(str)))[:3])
                + ". An answer in words goes in as cleaned and a gap stays a gap for the model's "
                "own imputer, never the text 'nan' or an empty string."
            )


def test_saved_models_were_fitted_on_their_schemas_and_fill_a_gap_as_training_did(
        processed_frames, saved_models, medical_policies):
    import numpy as np

    from config import config
    from data_pipeline.feature_builder import add_criteria_counts, build_feature_frame

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    for name, schema in [("approval", saved_models["approval_schema"]),
                         ("stay", saved_models["stay_schema"])]:
        fitted_on = list(getattr(saved_models[name], "feature_names_in_", []))
        assert fitted_on == schema, (
            "The saved "
            + name
            + " model was fitted on "
            + str(fitted_on)
            + " while its schema names "
            + str(schema)
            + ". A model saved beside a schema it was not fitted on scores live requests on "
            "the wrong columns."
        )
    history_train = processed_frames[config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE]
    history = add_criteria_counts(processed_frames[config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE]
                                  .dropna(subset=["member_age", config.URGENCY_COLUMN]).head(25),
                                  medical_policies["policies"])
    features = build_feature_frame(history, config.APPROVAL_NUMERIC_FEATURES,
                                   config.APPROVAL_CATEGORICAL_FEATURES)
    with_gaps = features.copy()
    with_gaps["member_age"] = np.nan
    with_gaps[config.URGENCY_COLUMN] = np.nan
    filled = features.copy()
    filled["member_age"] = float(history_train["member_age"].median())
    filled[config.URGENCY_COLUMN] = history_train[config.URGENCY_COLUMN].mode().iloc[0]
    gap_scores = saved_models["approval"].predict_proba(with_gaps)[:, 1]
    filled_scores = saved_models["approval"].predict_proba(filled)[:, 1]
    assert np.isfinite(gap_scores).all() and np.allclose(gap_scores, filled_scores), (
        "A request with its age and urgency left blank scores "
        + str(np.round(gap_scores[:3], 4))
        + " where the same request with the training median age and the commonest urgency "
        "scores "
        + str(np.round(filled_scores[:3], 4))
        + ". A blank input is filled as training filled it - a number with the median of the "
        "training data, an answer in words with its most common value - so a live request "
        "with a gap is still scored."
    )
    stays_train = processed_frames[config.CLEAN_SURGICAL_STAYS_TRAIN_FILE]
    stays = processed_frames[config.CLEAN_SURGICAL_STAYS_EVAL_FILE].dropna(
        subset=[config.BODY_MASS_INDEX_COLUMN, "smoking_status"]).head(25)
    stay_features = build_feature_frame(stays, config.STAY_NUMERIC_FEATURES,
                                        config.STAY_CATEGORICAL_FEATURES)
    stay_gaps = stay_features.copy()
    stay_gaps[config.BODY_MASS_INDEX_COLUMN] = np.nan
    stay_gaps["smoking_status"] = np.nan
    stay_filled = stay_features.copy()
    stay_filled[config.BODY_MASS_INDEX_COLUMN] = float(
        stays_train[config.BODY_MASS_INDEX_COLUMN].median())
    stay_filled["smoking_status"] = stays_train["smoking_status"].mode().iloc[0]
    gap_stays = saved_models["stay"].predict(stay_gaps)
    filled_stays = saved_models["stay"].predict(stay_filled)
    assert np.isfinite(gap_stays).all() and np.allclose(gap_stays, filled_stays), (
        "A stay with its body mass index and smoking status left blank is estimated at "
        + str(np.round(gap_stays[:3], 2))
        + " nights where the same stay filled as training filled it gives "
        + str(np.round(filled_stays[:3], 2))
        + "."
    )


def test_the_quality_report_accounts_for_every_row_it_received(raw_frames, processed_frames):
    import json

    from config import config
    from data_pipeline.dataset_loader import load_raw_dataset

    assert raw_frames["problem"] is None, raw_frames["problem"]
    assert processed_frames["problem"] is None, processed_frames["problem"]
    with open(config.DATA_QUALITY_REPORT_FILE, encoding="utf-8") as report_file:
        report = json.load(report_file)
    datasets = [
        ("authorisation_history_train", config.RAW_AUTHORISATION_HISTORY_TRAIN_FILE,
         config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE, config.HISTORY_TARGET_COLUMN),
        ("authorisation_history_eval", config.RAW_AUTHORISATION_HISTORY_EVAL_FILE,
         config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE, config.HISTORY_TARGET_COLUMN),
        ("surgical_stays_train", config.RAW_SURGICAL_STAYS_TRAIN_FILE,
         config.CLEAN_SURGICAL_STAYS_TRAIN_FILE, config.STAY_TARGET_COLUMN),
        ("surgical_stays_eval", config.RAW_SURGICAL_STAYS_EVAL_FILE,
         config.CLEAN_SURGICAL_STAYS_EVAL_FILE, config.STAY_TARGET_COLUMN),
        ("clinical_note_sentences", config.RAW_CLINICAL_NOTE_SENTENCES_FILE,
         config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE, config.SENTENCE_TARGET_COLUMN)]
    assert sorted(report) == sorted(dataset[0] for dataset in datasets), (
        config.DATA_QUALITY_REPORT_FILE
        + " profiles "
        + str(sorted(report))
        + " where it profiles each of the five extracts under its own name."
    )
    reasons = ["duplicate_rows", "rows_missing_target", "answered_earlier_submissions_removed",
               "rows_with_impossible_target", "rows_with_too_few_words"]
    for name, raw_path, clean_path, target_column in datasets:
        profile = report[name]
        received = load_raw_dataset(raw_path)
        first_copies = received[~received.duplicated()]
        expected = {
            "rows_received": len(raw_frames[raw_path]),
            "rows_kept": len(processed_frames[clean_path]),
            "rows_removed": len(raw_frames[raw_path]) - len(processed_frames[clean_path]),
            "duplicate_rows": int(received.duplicated().sum()),
            "rows_missing_target": int(first_copies[target_column].isna().sum()),
            "columns": int(processed_frames[clean_path].shape[1]),
        }
        got = {key: profile.get(key) for key in expected}
        assert got == expected, (
            "The quality report gives "
            + name
            + " as "
            + str(got)
            + " where the files give "
            + str(expected)
            + ". Rows received are the raw rows, rows kept the cleaned rows, repeats the exact "
            "repeats, and rows missing the answer are counted among the first copies."
        )
        explained = sum(int(profile.get(reason, 0)) for reason in reasons)
        assert explained == expected["rows_removed"], (
            "The quality report's reasons for "
            + name
            + " add up to "
            + str(explained)
            + " rows where "
            + str(expected["rows_removed"])
            + " were removed: "
            + str({reason: profile.get(reason) for reason in reasons if reason in profile})
            + ". Every removed row is a repeat, a row with no answer, an earlier submission, "
            "an answer that cannot be true or a sentence too short to read."
        )


def test_approval_model_ranks_held_out_requests_above_the_minimum_and_its_scores_are_calibrated(
        processed_frames, saved_models, medical_policies):
    import copy

    from sklearn.metrics import roc_auc_score

    from config import config
    from data_pipeline.feature_builder import add_criteria_counts, build_feature_frame
    from modeling.model_evaluation import evaluate_classifier

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    policies = medical_policies["policies"]
    held_out = add_criteria_counts(processed_frames[config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE],
                                   policies)
    trained_on = add_criteria_counts(
        processed_frames[config.CLEAN_AUTHORISATION_HISTORY_TRAIN_FILE].head(3000), policies)
    held_out_features = build_feature_frame(held_out, config.APPROVAL_NUMERIC_FEATURES,
                                            config.APPROVAL_CATEGORICAL_FEATURES)
    train_features = build_feature_frame(trained_on, config.APPROVAL_NUMERIC_FEATURES,
                                         config.APPROVAL_CATEGORICAL_FEATURES)
    held_out_answers = held_out[config.HISTORY_TARGET_COLUMN].map(config.APPROVAL_TARGET_ENCODING)
    train_answers = trained_on[config.HISTORY_TARGET_COLUMN].map(config.APPROVAL_TARGET_ENCODING)
    model = saved_models["approval"]
    scores = model.predict_proba(held_out_features)[:, 1]
    measured = roc_auc_score(held_out_answers, scores)
    assert measured >= config.MINIMUM_APPROVAL_ROC_AUC, (
        "The approval model ranks the held-out requests with a ROC AUC of "
        + str(round(measured, 4))
        + ", below the "
        + str(config.MINIMUM_APPROVAL_ROC_AUC)
        + " the configuration sets. It is scored on the later requests, which it never saw, "
        "with the criteria counts worked out under each request's own policy."
    )
    assert abs(float(scores.mean()) - float(held_out_answers.mean())) <= 0.03, (
        "The approval model's scores average "
        + str(round(float(scores.mean()), 4))
        + " on the held-out requests, where "
        + str(round(float(held_out_answers.mean()), 4))
        + " of them were approved. A likelihood is read as a share of requests like this one "
        "that are approved, so the scores average the share approved."
    )
    evaluation = evaluate_classifier(copy.deepcopy(model), train_features, train_answers,
                                     held_out_features, held_out_answers)
    missing = sorted({"train_roc_auc", "held_out_roc_auc", "generalisation_gap"}
                     - set(evaluation))
    assert len(missing) == 0, (
        "evaluate_classifier returned no "
        + str(missing)
        + ", so the approval model's scores cannot be read."
    )
    train_measured = roc_auc_score(train_answers, model.predict_proba(train_features)[:, 1])
    assert (abs(evaluation["held_out_roc_auc"] - measured) < 0.006
            and abs(evaluation["train_roc_auc"] - train_measured) < 0.006
            and abs(evaluation["generalisation_gap"]
                    - (evaluation["train_roc_auc"] - evaluation["held_out_roc_auc"])) < 0.011), (
        "The evaluation reports a held-out ROC AUC of "
        + str(evaluation["held_out_roc_auc"])
        + ", a training ROC AUC of "
        + str(evaluation["train_roc_auc"])
        + " and a gap of "
        + str(evaluation["generalisation_gap"])
        + ", where the model's own scores give "
        + str(round(measured, 4))
        + " and "
        + str(round(train_measured, 4))
        + ". evaluate_classifier scores the fitted model it is given, without fitting it "
        "again, and the gap is the training score less the held-out one."
    )


def test_stay_model_explains_held_out_stays_above_the_minimum_and_never_forecasts_below_a_night(
        processed_frames, saved_models):
    import copy

    from sklearn.metrics import mean_absolute_error, r2_score

    from config import config
    from data_pipeline.feature_builder import build_feature_frame
    from modeling.model_evaluation import evaluate_regressor

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    held_out = processed_frames[config.CLEAN_SURGICAL_STAYS_EVAL_FILE]
    trained_on = processed_frames[config.CLEAN_SURGICAL_STAYS_TRAIN_FILE].head(3000)
    held_out_features = build_feature_frame(held_out, config.STAY_NUMERIC_FEATURES,
                                            config.STAY_CATEGORICAL_FEATURES)
    train_features = build_feature_frame(trained_on, config.STAY_NUMERIC_FEATURES,
                                         config.STAY_CATEGORICAL_FEATURES)
    model = saved_models["stay"]
    forecast = model.predict(held_out_features)
    measured = r2_score(held_out[config.STAY_TARGET_COLUMN], forecast)
    assert measured >= config.MINIMUM_STAY_R2, (
        "The stay model explains the held-out stays with an R2 of "
        + str(round(measured, 4))
        + ", below the "
        + str(config.MINIMUM_STAY_R2)
        + " the configuration sets."
    )
    assert float(forecast.min()) >= config.STAY_NIGHTS_MINIMUM, (
        "The stay model forecasts a stay of "
        + str(round(float(forecast.min()), 2))
        + " nights for a held-out admission. An inpatient operation is at least "
        + str(config.STAY_NIGHTS_MINIMUM)
        + " night, and no stay of fewer was kept to learn from."
    )
    training_average = float(
        processed_frames[config.CLEAN_SURGICAL_STAYS_TRAIN_FILE][config.STAY_TARGET_COLUMN].mean())
    average_error = mean_absolute_error(held_out[config.STAY_TARGET_COLUMN],
                                        [training_average] * len(held_out))
    model_error = mean_absolute_error(held_out[config.STAY_TARGET_COLUMN], forecast)
    assert model_error < 0.75 * average_error, (
        "The stay model is off by "
        + str(round(model_error, 3))
        + " nights on average, against "
        + str(round(average_error, 3))
        + " for the average stay given to everyone. A forecast that does little better than "
        "the average tells the nurse nothing about this member."
    )
    evaluation = evaluate_regressor(copy.deepcopy(model), train_features,
                                    trained_on[config.STAY_TARGET_COLUMN], held_out_features,
                                    held_out[config.STAY_TARGET_COLUMN])
    missing = sorted({"train_r2", "held_out_r2", "generalisation_gap"} - set(evaluation))
    assert len(missing) == 0 and abs(evaluation["held_out_r2"] - measured) < 0.006, (
        "evaluate_regressor reports "
        + str({key: evaluation.get(key) for key in ["train_r2", "held_out_r2",
                                                    "generalisation_gap"]})
        + " where the model's own forecasts give a held-out R2 of "
        + str(round(measured, 4))
        + ". It scores the fitted model it is given, without fitting it again."
    )


def test_the_approval_score_rises_when_a_criterion_is_met_rather_than_not(
        processed_frames, saved_models, medical_policies):
    from config import config
    from data_pipeline.feature_builder import add_criteria_counts, build_feature_frame

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    held_out = add_criteria_counts(processed_frames[config.CLEAN_AUTHORISATION_HISTORY_EVAL_FILE],
                                   medical_policies["policies"])
    features = build_feature_frame(held_out, config.APPROVAL_NUMERIC_FEATURES,
                                   config.APPROVAL_CATEGORICAL_FEATURES)
    model = saved_models["approval"]
    for count_column, result_name, least_share in [
            (config.CRITERIA_NOT_MET_COUNT_COLUMN, config.CRITERION_NOT_MET, 0.95),
            (config.CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN, config.CRITERION_NOT_DOCUMENTED, 0.8)]:
        before = features[features[count_column] >= 1]
        after = before.copy()
        after[count_column] = after[count_column] - 1
        after[config.CRITERIA_MET_COUNT_COLUMN] = after[config.CRITERIA_MET_COUNT_COLUMN] + 1
        before_scores = model.predict_proba(before)[:, 1]
        after_scores = model.predict_proba(after)[:, 1]
        rising = float((after_scores > before_scores).mean())
        assert len(before) > 50 and rising >= least_share and (
                after_scores.mean() - before_scores.mean()) >= 0.1, (
            "Turning one criterion from "
            + result_name
            + " to Met raises the approval score for "
            + str(round(100 * rising, 1))
            + "% of the "
            + str(len(before))
            + " held-out requests it applies to, and moves the average from "
            + str(round(float(before_scores.mean()), 4))
            + " to "
            + str(round(float(after_scores.mean()), 4))
            + ". A request that meets more of its policy's criteria is the more likely to be "
            "approved, so the model must have learned from the screening counts."
        )


def test_the_expected_stay_lengthens_with_the_class_the_operation_and_no_enhanced_recovery(
        processed_frames, saved_models):
    from config import config
    from data_pipeline.feature_builder import build_feature_frame

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    stays = processed_frames[config.CLEAN_SURGICAL_STAYS_EVAL_FILE]
    features = build_feature_frame(stays, config.STAY_NUMERIC_FEATURES,
                                   config.STAY_CATEGORICAL_FEATURES)
    knees = features[stays[config.SERVICE_CODE_COLUMN] == "ORT-TKR"]
    model = saved_models["stay"]
    for label, frame, column_name, shorter_value, longer_value, least_nights in [
            ("an ASA class of 4 rather than 2", features, config.ASA_CLASS_COLUMN, 2, 4, 1.0),
            ("both knees rather than one", knees, config.PROCEDURE_DETAIL_COLUMN,
             config.PROCEDURE_DETAIL_MAPPING["unilateral"],
             config.PROCEDURE_DETAIL_MAPPING["bilateral"], 1.0),
            ("a hospital without an enhanced recovery programme", features,
             "enhanced_recovery_programme", config.BOOLEAN_YES, config.BOOLEAN_NO, 0.5)]:
        shorter = frame.copy()
        shorter[column_name] = shorter_value
        longer = frame.copy()
        longer[column_name] = longer_value
        shorter_stays = model.predict(shorter)
        longer_stays = model.predict(longer)
        lengthened = float((longer_stays > shorter_stays).mean())
        assert lengthened >= 0.9 and (longer_stays.mean() - shorter_stays.mean()) >= least_nights, (
            "With "
            + label
            + ", the expected stay lengthens for "
            + str(round(100 * lengthened, 1))
            + "% of the held-out admissions and on average from "
            + str(round(float(shorter_stays.mean()), 2))
            + " to "
            + str(round(float(longer_stays.mean()), 2))
            + " nights. A sicker member, a bigger operation and a hospital without enhanced "
            "recovery all keep a member in longer, and the model is fed each of them."
        )


def test_likelihood_bands_and_longer_stays_follow_the_configured_thresholds(
        live_files, saved_models, medical_policies):
    import pandas as pd

    from config import config
    from data_pipeline.feature_builder import build_feature_frame
    from tools.prediction_tools import estimate_approval_likelihood, estimate_expected_stay
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    policies = medical_policies["policies"]
    bands = {config.HIGH_APPROVAL_BAND: 0, config.MEDIUM_APPROVAL_BAND: 0,
             config.LOW_APPROVAL_BAND: 0}
    inpatient = []
    records = []
    given = []
    for request in live_files["requests"].to_dict("records"):
        screening = screen_request(request, policies[request[config.SERVICE_CODE_COLUMN]])
        likelihood = estimate_approval_likelihood(saved_models["approval"],
                                                  saved_models["approval_schema"], request,
                                                  screening)
        record = dict(request)
        for count_column in config.CRITERIA_COUNT_COLUMNS:
            record[count_column] = screening[count_column]
        records.append(record)
        given.append((request, likelihood))
        if request[config.SITE_OF_SERVICE_COLUMN] == config.INPATIENT_SITE:
            inpatient.append((request, screening))
    features = build_feature_frame(pd.DataFrame(records), config.APPROVAL_NUMERIC_FEATURES,
                                   config.APPROVAL_CATEGORICAL_FEATURES)
    scores = saved_models["approval"].predict_proba(features)[:, 1]
    for (request, likelihood), score in zip(given, scores, strict=True):
        expected_figure = round(float(score), config.LIKELIHOOD_DECIMALS)
        figure = likelihood["approval_likelihood"]
        if figure >= config.HIGH_APPROVAL_MINIMUM:
            expected_band = config.HIGH_APPROVAL_BAND
        elif figure >= config.MEDIUM_APPROVAL_MINIMUM:
            expected_band = config.MEDIUM_APPROVAL_BAND
        else:
            expected_band = config.LOW_APPROVAL_BAND
        assert figure == expected_figure and likelihood["approval_band"] == expected_band, (
            request[config.REQUEST_REFERENCE_COLUMN]
            + " is given a likelihood of "
            + str(figure)
            + ", band "
            + str(likelihood["approval_band"])
            + ", where its saved model's score to "
            + str(config.LIKELIHOOD_DECIMALS)
            + " decimals is "
            + str(expected_figure)
            + ", band "
            + expected_band
            + ". The band is cut on the figure shown: HIGH from "
            + str(config.HIGH_APPROVAL_MINIMUM)
            + ", MEDIUM from "
            + str(config.MEDIUM_APPROVAL_MINIMUM)
            + ", LOW below."
        )
        bands[expected_band] += 1
    assert min(bands.values()) > 0, (
        "The live queue's likelihoods fall only in the bands "
        + str(bands)
        + ", so the bands cannot all be told apart."
    )
    assert len(inpatient) > 0, "No live request is an inpatient operation, so no stay is checked."
    for request, screening in inpatient:
        stay = estimate_expected_stay(saved_models["stay"], saved_models["stay_schema"], request,
                                      screening)
        requested = request[config.REQUESTED_INPATIENT_DAYS_COLUMN]
        if pd.isna(requested):
            expected_flag = None
        else:
            expected_flag = (stay["expected_stay_days"]
                             > int(requested) + config.LONGER_STAY_MARGIN_DAYS)
        assert (stay["expected_stay_days"]
                == round(stay["expected_stay_days"], config.STAY_DECIMALS)
                and stay["expected_stay_days"] >= config.STAY_NIGHTS_MINIMUM
                and stay["longer_stay_expected"] == expected_flag), (
            request[config.REQUEST_REFERENCE_COLUMN]
            + " is expected to stay "
            + str(stay["expected_stay_days"])
            + " nights against "
            + str(requested)
            + " requested, with a longer stay flagged as "
            + str(stay["longer_stay_expected"])
            + ". The stay is given to "
            + str(config.STAY_DECIMALS)
            + " decimal, and a longer stay is flagged only when it is more than "
            + str(config.LONGER_STAY_MARGIN_DAYS)
            + " day above the days requested."
        )
        unrequested = dict(request)
        unrequested[config.REQUESTED_INPATIENT_DAYS_COLUMN] = float("nan")
        unflagged = estimate_expected_stay(saved_models["stay"], saved_models["stay_schema"],
                                           unrequested, screening)
        assert (unflagged["longer_stay_expected"] is None
                and unflagged["requested_inpatient_days"] is None), (
            "A stay with no inpatient days requested is flagged "
            + str(unflagged["longer_stay_expected"])
            + ". With nothing requested, there is nothing to compare: no longer stay is noted."
        )
    first_request, first_screening = inpatient[0]
    other_request = live_files["requests"][live_files["requests"][
        config.REQUEST_REFERENCE_COLUMN] != first_request[config.REQUEST_REFERENCE_COLUMN]]
    other_request = other_request.iloc[0].to_dict()
    outpatient = live_files["requests"][live_files["requests"][config.SITE_OF_SERVICE_COLUMN]
                                        != config.INPATIENT_SITE].iloc[0].to_dict()
    refusal = None
    try:
        estimate_approval_likelihood(saved_models["approval"], saved_models["approval_schema"],
                                     other_request, first_screening)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and first_request[config.REQUEST_REFERENCE_COLUMN] in refusal, (
        "A likelihood worked out for "
        + other_request[config.REQUEST_REFERENCE_COLUMN]
        + " with the screening of "
        + first_request[config.REQUEST_REFERENCE_COLUMN]
        + " gave "
        + str(refusal)
        + ". A screening belongs to one request and is refused for any other, naming it."
    )
    outpatient_screening = screen_request(outpatient,
                                          policies[outpatient[config.SERVICE_CODE_COLUMN]])
    refusal = None
    try:
        estimate_expected_stay(saved_models["stay"], saved_models["stay_schema"], outpatient,
                               outpatient_screening)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and outpatient[config.SITE_OF_SERVICE_COLUMN] in refusal, (
        "A stay worked out for "
        + outpatient[config.REQUEST_REFERENCE_COLUMN]
        + ", which is given at "
        + str(outpatient[config.SITE_OF_SERVICE_COLUMN])
        + ", gave "
        + str(refusal)
        + ". Only an inpatient operation has a stay to expect; any other request is refused, "
        "naming its site of service."
    )


def test_evidence_model_clears_the_configured_macro_f1_on_held_out_sentences(
        processed_frames, saved_models):
    import copy

    from sklearn.metrics import f1_score
    from sklearn.model_selection import train_test_split

    from config import config
    from modeling.model_evaluation import evaluate_text_classifier

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    sentences = processed_frames[config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE]
    train_text, held_out_text, train_answers, held_out_answers = train_test_split(
        sentences[config.SENTENCE_TEXT_COLUMN], sentences[config.SENTENCE_TARGET_COLUMN],
        test_size=config.SENTENCE_HELD_OUT_SHARE,
        stratify=sentences[config.SENTENCE_TARGET_COLUMN], random_state=config.RANDOM_SEED)
    model = saved_models["evidence"]
    measured = f1_score(held_out_answers, model.predict(held_out_text), average="macro")
    assert measured >= config.MINIMUM_EVIDENCE_MACRO_F1, (
        "The evidence model scored "
        + str(round(measured, 4))
        + " macro F1 on the held-out sentences, below the "
        + str(config.MINIMUM_EVIDENCE_MACRO_F1)
        + " the configuration sets. Macro F1 weighs the rarest kind of evidence as much as the "
        "commonest: a red-flag symptom read as background hides the one sentence that waives "
        "the treatment length."
    )
    evaluation = evaluate_text_classifier(copy.deepcopy(model), train_text.head(3000),
                                          train_answers.head(3000), held_out_text,
                                          held_out_answers)
    missing = sorted({"held_out_macro_f1", "train_macro_f1", "generalisation_gap",
                      "per_class_f1"} - set(evaluation))
    assert len(missing) == 0, (
        "evaluate_text_classifier returned no "
        + str(missing)
        + ", so the evidence model's scores cannot be read."
    )
    trained_on = f1_score(train_answers.head(3000), model.predict(train_text.head(3000)),
                          average="macro")
    assert (abs(evaluation["held_out_macro_f1"] - measured) < 0.006
            and abs(evaluation["train_macro_f1"] - trained_on) < 0.006
            and abs(evaluation["generalisation_gap"]
                    - (evaluation["train_macro_f1"] - evaluation["held_out_macro_f1"])) < 0.011), (
        "The evaluation reports macro F1 "
        + str(evaluation["held_out_macro_f1"])
        + " held out and "
        + str(evaluation["train_macro_f1"])
        + " on training, with a gap of "
        + str(evaluation["generalisation_gap"])
        + ", but the model's own predictions give "
        + str(round(measured, 4))
        + " and "
        + str(round(trained_on, 4))
        + ". evaluate_text_classifier scores the fitted model it is given, without fitting it "
        "again."
    )


def test_evidence_predictions_stay_inside_the_vocabulary_and_reach_every_kind(
        processed_frames, saved_models):
    from sklearn.model_selection import train_test_split

    from config import config

    assert processed_frames["problem"] is None, processed_frames["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    vocabulary = sorted(set(config.EVIDENCE_TYPE_MAPPING.values()))
    sentences = processed_frames[config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE]
    found_kinds = sorted(sentences[config.SENTENCE_TARGET_COLUMN].astype(str).unique())
    assert found_kinds == vocabulary, (
        "The cleaned sentences are labelled "
        + str(found_kinds)
        + " where the evidence types are "
        + str(vocabulary)
        + "."
    )
    model = saved_models["evidence"]
    learned = sorted(str(label) for label in getattr(model, "classes_", []))
    assert learned == vocabulary, (
        "The evidence model knows the classes "
        + str(learned)
        + " where the evidence types are "
        + str(vocabulary)
        + ". A kind of evidence the model cannot predict is a kind no nurse ever sees."
    )
    split = train_test_split(
        sentences[config.SENTENCE_TEXT_COLUMN], sentences[config.SENTENCE_TARGET_COLUMN],
        test_size=config.SENTENCE_HELD_OUT_SHARE,
        stratify=sentences[config.SENTENCE_TARGET_COLUMN], random_state=config.RANDOM_SEED)
    held_out_text, held_out_answers = split[1], split[3]
    predicted = [str(label) for label in model.predict(held_out_text)]
    stray = sorted(set(predicted) - set(vocabulary))
    unreached = sorted(set(vocabulary) - set(predicted))
    assert len(stray) == 0 and len(unreached) == 0, (
        "On the held-out sentences the evidence model predicts "
        + str(stray)
        + " outside the vocabulary and never predicts "
        + str(unreached)
        + "."
    )
    for kind in vocabulary:
        shown = held_out_text[held_out_answers == kind]
        right = sum(1 for label in model.predict(shown) if str(label) == kind)
        assert right >= 0.75 * len(shown), (
            "Of the "
            + str(len(shown))
            + " held-out sentences labelled "
            + kind
            + ", the model reads "
            + str(right)
            + " as that kind. Every kind of evidence is told apart, not only the common ones."
        )
    unseen = [str(label) for label in model.predict(["Zzq wvx plorth.",
                                                     "No words of this sort were ever written."])]
    assert all(label in vocabulary for label in unseen), (
        "Sentences of words never seen in training were read as "
        + str(unseen)
        + ", outside the evidence types."
    )


def test_clinical_text_cleaning_leaves_plain_words_whatever_markup_or_capitals_it_came_in(
        processed_frames):
    import html

    import pandas as pd

    from config import config
    from data_pipeline.common_cleaning import clean_clinical_text

    assert processed_frames["problem"] is None, processed_frames["problem"]
    sentences = processed_frames[config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE]
    texts = sentences[config.SENTENCE_TEXT_COLUMN].astype(str)
    left_markup = int(texts.str.contains(r"</?[A-Za-z][A-Za-z0-9]*[ />]", regex=True).sum())
    left_entities = int(texts.str.contains(r"&[#a-z0-9]+;|\xa0", regex=True).sum())
    doubled_spaces = int(texts.str.contains(r"\s{2,}|^\s|\s$", regex=True).sum())
    assert left_markup == 0 and left_entities == 0 and doubled_spaces == 0, (
        config.CLEAN_CLINICAL_NOTE_SENTENCES_FILE
        + " still holds "
        + str(left_markup)
        + " sentences with markup, "
        + str(left_entities)
        + " with escaped characters and "
        + str(doubled_spaces)
        + " with stray spaces. A sentence is read as plain words."
    )
    plain = texts[texts.str.contains("[A-Z]", regex=True)
                  & texts.str.contains("[a-z]", regex=True)
                  & ~texts.str.contains("[&<>]", regex=True)].head(40).reset_index(drop=True)
    expected = clean_clinical_text(plain)
    variants = {
        "wrapped in markup": "<p>" + plain.str.replace(" ", " <br/> ", n=1, regex=False)
                             + "</p>",
        "with its characters escaped": plain.map(html.escape).str.replace(" ", "&nbsp;", n=1,
                                                                          regex=False),
        "with extra spaces": "  " + plain.str.replace(" ", "   ", regex=False) + " ",
    }
    for label, written in variants.items():
        cleaned = clean_clinical_text(pd.Series(written))
        differing = [(written.iloc[position], cleaned.iloc[position])
                     for position in range(len(plain))
                     if cleaned.iloc[position] != expected.iloc[position]]
        assert len(differing) == 0, (
            "A sentence "
            + label
            + " cleans to something else than the plain sentence does, for example "
            + str(differing[:2])
            + ". Markup, escaped characters and runs of spaces are taken out, leaving the "
            "words the writer meant."
        )
    shouted = clean_clinical_text(plain.str.upper())
    differing = [(plain.iloc[position], shouted.iloc[position]) for position in range(len(plain))
                 if shouted.iloc[position] != expected.iloc[position].lower()]
    assert len(differing) == 0, (
        "A sentence written in capitals cleans to something other than the plain sentence in "
        "small letters, for example "
        + str(differing[:2])
        + ". Capitals carry no meaning the model was trained on, and the case cannot be "
        "restored further than small letters."
    )
    kept_case = clean_clinical_text(plain)
    assert list(kept_case) == list(plain), (
        "A plain sentence written in mixed case is changed by cleaning, for example "
        + str([(plain.iloc[position], kept_case.iloc[position]) for position in range(len(plain))
               if kept_case.iloc[position] != plain.iloc[position]][:2])
        + ". Only a sentence written wholly in capitals is lowered."
    )


def test_each_document_is_split_into_its_sentences_in_order_and_each_is_read(
        live_files, saved_models):
    import re

    from config import config
    from tools.evidence_tools import read_document_evidence
    from tools.request_data_tools import fetch_request_documents

    assert live_files["problem"] is None, live_files["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    vocabulary = set(config.EVIDENCE_TYPE_MAPPING.values())
    requests = live_files["requests"].to_dict("records")
    read_requests = 0
    for request in requests[:8]:
        documents = fetch_request_documents(live_files["notes"], request)
        own_notes = live_files["notes"][live_files["notes"][config.REQUEST_REFERENCE_COLUMN]
                                        == request[config.REQUEST_REFERENCE_COLUMN]]
        numbered = list(own_notes.sort_values(config.NOTE_NUMBER_COLUMN)[config.NOTE_ID_COLUMN])
        fetched = [document[config.NOTE_ID_COLUMN] for document in documents]
        assert fetched == numbered, (
            "The documents of "
            + request[config.REQUEST_REFERENCE_COLUMN]
            + " were fetched as "
            + str(fetched)
            + " where, by their note numbers, they run "
            + str(numbered)
            + ". The documents sent with a request are read in the order the office numbered "
            "them, whatever order they stand in the file."
        )
        findings = read_document_evidence(saved_models["evidence"], documents)
        read_requests += 1
        expected_notes = []
        for document in documents:
            sentence_count = len(re.split(config.DOCUMENT_SENTENCE_PATTERN,
                                          document[config.NOTE_TEXT_COLUMN]))
            expected_notes.extend([document[config.NOTE_ID_COLUMN]] * sentence_count)
        got_notes = [finding.get("note_id") for finding in findings]
        assert got_notes == expected_notes, (
            "The documents of "
            + request[config.REQUEST_REFERENCE_COLUMN]
            + " give sentences from "
            + str(got_notes)
            + " where, split at the end of each sentence, they hold "
            + str(expected_notes)
            + ". Each document is split into its sentences in the order it was written, and "
            "the documents are read in their own order."
        )
        for document in documents:
            own = [finding["sentence"] for finding in findings
                   if finding["note_id"] == document[config.NOTE_ID_COLUMN]]
            assert " ".join(own) == document[config.NOTE_TEXT_COLUMN], (
                "The sentences read from "
                + document[config.NOTE_ID_COLUMN]
                + " join back to "
                + repr(" ".join(own)[:200])
                + " instead of the document's own text. A sentence is kept whole, as written."
            )
        for finding in findings:
            assert (finding.get("evidence_type") in vocabulary
                    and finding.get("note_author_role") == [
                        document[config.NOTE_AUTHOR_ROLE_COLUMN] for document in documents
                        if document[config.NOTE_ID_COLUMN] == finding["note_id"]][0]), (
                "A sentence of "
                + str(finding.get("note_id"))
                + " is read as "
                + repr(finding.get("evidence_type"))
                + " written by "
                + repr(finding.get("note_author_role"))
                + ". Each sentence carries the kind of evidence the model reads in it and the "
                "author of its document."
            )
    assert read_requests == 8, "Fewer than eight live requests could be read."
    assert read_document_evidence(saved_models["evidence"], []) == [], (
        "A request sent with no document gives evidence. With nothing sent, nothing is read."
    )
    capitals = {config.NOTE_ID_COLUMN: "NTE-990001", config.NOTE_AUTHOR_ROLE_COLUMN:
                "Specialist letter", config.NOTE_TEXT_COLUMN:
                "mrs ayodele has completed ten weeks of supervised physiotherapy. the pain is "
                "no better. she cannot climb stairs."}
    lowered = read_document_evidence(saved_models["evidence"], [capitals])
    assert [finding["sentence"] for finding in lowered] == [
            "mrs ayodele has completed ten weeks of supervised physiotherapy.",
            "the pain is no better.", "she cannot climb stairs."], (
        "A document written in capitals, lowered by cleaning, is split into "
        + str([finding["sentence"] for finding in lowered])
        + ". A sentence ends at its full stop whatever the case of the next word."
    )


def test_each_sentence_records_the_criteria_its_evidence_bears_on_under_the_requests_policy(
        live_files, saved_models, medical_policies):
    from config import config
    from tools.evidence_tools import link_evidence_to_criteria, read_document_evidence
    from tools.request_data_tools import fetch_request_documents
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    policies = medical_policies["policies"]
    seen_services = set()
    seen_kinds = set()
    for request in live_files["requests"].to_dict("records"):
        if request[config.SERVICE_CODE_COLUMN] in seen_services:
            continue
        seen_services.add(request[config.SERVICE_CODE_COLUMN])
        screening = screen_request(request, policies[request[config.SERVICE_CODE_COLUMN]])
        findings = read_document_evidence(
            saved_models["evidence"], fetch_request_documents(live_files["notes"], request))
        linked = link_evidence_to_criteria(findings, screening)
        assert len(linked) == len(findings), (
            "link_evidence_to_criteria returned "
            + str(len(linked))
            + " findings for the "
            + str(len(findings))
            + " sentences of "
            + request[config.REQUEST_REFERENCE_COLUMN]
            + "."
        )
        for finding, linked_finding in zip(findings, linked, strict=True):
            kinds = config.EVIDENCE_CRITERION_KINDS[finding["evidence_type"]]
            expected = [criterion["criterion_name"] for criterion in screening["criteria"]
                        if criterion["criterion_kind"] in kinds]
            seen_kinds.add(finding["evidence_type"])
            assert (linked_finding.get("criteria_borne_on") == expected
                    and linked_finding.get("sentence") == finding["sentence"]
                    and linked_finding.get("evidence_type") == finding["evidence_type"]), (
                "A sentence of "
                + request[config.REQUEST_REFERENCE_COLUMN]
                + " read as "
                + finding["evidence_type"]
                + " bears on "
                + str(linked_finding.get("criteria_borne_on"))
                + " where, under "
                + screening["policy_document"]
                + ", it bears on "
                + str(expected)
                + ". Each kind of evidence bears on the criteria its evidence guide names, and "
                "only on those this request's own policy has."
            )
    assert seen_services == set(config.SERVICE_POLICY_DOCUMENTS) and len(seen_kinds) >= 4, (
        "The live requests read covered the services "
        + str(sorted(seen_services))
        + " and the kinds "
        + str(sorted(seen_kinds))
        + "."
    )
    background = link_evidence_to_criteria(
        [{"note_id": "NTE-990002", "note_author_role": "Specialist letter",
          "sentence": "She lives with her daughter.", "evidence_type": "Background"}],
        screening)
    assert background[0].get("criteria_borne_on") == [], (
        "A background sentence bears on "
        + str(background[0].get("criteria_borne_on"))
        + ". Background bears on no criterion."
    )
    refusal = None
    try:
        link_evidence_to_criteria(
            [{"note_id": "NTE-990003", "note_author_role": "Specialist letter",
              "sentence": "A sentence of a kind nobody configured.", "evidence_type": "Rumour"}],
            screening)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and "Rumour" in refusal, (
        "A sentence of an evidence type the configuration gives no criteria for gave "
        + str(refusal)
        + ". It is refused with a ValueError naming the type."
    )


def test_every_document_gives_up_its_text(document_texts, tmp_path):
    import os
    import shutil

    import pypdf

    from config import config
    from knowledge.pdf_extraction import extract_text_from_directory

    assert document_texts["problem"] is None, document_texts["problem"]
    in_folder = sorted(name for name in os.listdir(config.DOCS_DIRECTORY)
                       if name.lower().endswith(".pdf"))
    documents = document_texts["documents"]
    assert len(documents) > 0 and {"document_name", "document_text"} <= set(documents[0]), (
        "Reading the document folder returned "
        + str(len(documents))
        + " entries"
        + ("" if len(documents) == 0 else ", the first keyed " + str(sorted(documents[0])))
        + ", where every entry names its document and carries its text."
    )
    names = sorted(document["document_name"] for document in documents)
    assert names == in_folder, (
        "Reading the document folder returned "
        + str(names)
        + " where the folder holds "
        + str(in_folder)
        + ". A document never read is a question answered from general knowledge instead."
    )
    for document in documents:
        assert len(document["document_text"].split()) > 250, (
            document["document_name"]
            + " gave up only "
            + str(len(document["document_text"].split()))
            + " words. A PDF that will not give up its text is indexed as an empty passage."
        )
    for required in (list(config.SERVICE_POLICY_DOCUMENTS.values())
                     + list(config.EVIDENCE_GUIDE_DOCUMENTS.values())):
        assert required in names, (
            required
            + " was not read, and the configuration sends questions to it by name."
        )
    folder = tmp_path / "mixed_folder"
    folder.mkdir()
    policy_document = config.SERVICE_POLICY_DOCUMENTS["ORT-TKR"]
    guide_document = config.EVIDENCE_GUIDE_DOCUMENTS["Ruled out"]
    for name in [policy_document, guide_document]:
        shutil.copy(os.path.join(config.DOCS_DIRECTORY, name), str(folder / name))
    (folder / "reading-list.txt").write_text("Not a document of the utilisation management team.")
    (folder / "scan.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    mixed_names = None
    try:
        mixed_names = sorted(entry["document_name"]
                             for entry in extract_text_from_directory(str(folder)))
    except Exception as error:
        mixed_names = type(error).__name__ + ": " + str(error)[:200]
    assert mixed_names == sorted([policy_document, guide_document]), (
        "A folder holding two PDFs, a text file and an image was read as "
        + str(mixed_names)
        + ". Only the PDFs are the plan's documents; anything else in the folder is passed over."
    )
    blank_folder = tmp_path / "blank_page_folder"
    blank_folder.mkdir()
    writer = pypdf.PdfWriter()
    writer.add_page(pypdf.PdfReader(os.path.join(config.DOCS_DIRECTORY,
                                                 policy_document)).pages[0])
    writer.add_blank_page()
    with open(str(blank_folder / "Policy-With-A-Blank-Page.pdf"), "wb") as blank_file:
        writer.write(blank_file)
    empty_folder = tmp_path / "empty_folder"
    empty_folder.mkdir()
    (empty_folder / "notes.txt").write_text("No PDF here.")
    for label, folder_path, named in [
            ("A PDF whose second page gives up no text", blank_folder,
             "Policy-With-A-Blank-Page.pdf"),
            ("A folder with no PDF in it", empty_folder, str(empty_folder))]:
        refusal = None
        try:
            extract_text_from_directory(str(folder_path))
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and named in refusal, (
            label
            + " gave "
            + str(refusal)
            + ". A page that cannot be read may be the one that states a criterion, and a "
            "folder with no document has nothing to answer from, so each is refused with a "
            "ValueError naming the file or the folder."
        )


def test_documents_are_cut_into_numbered_sections_and_passages_of_the_configured_size(
        document_passages, medical_policies):
    import re

    from config import config
    from knowledge.chunk_splitting import build_chunk_records, split_documents_into_sections

    assert document_passages["problem"] is None, document_passages["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    documents = document_passages["documents"]
    sections = document_passages["sections"]
    chunks = document_passages["chunks"]
    assert len(chunks) > 0 and {"chunk_id", "chunk_text", "document_name"} <= set(chunks[0]), (
        "Cutting the documents returned "
        + str(len(chunks))
        + " passages"
        + ("" if len(chunks) == 0 else ", the first keyed " + str(sorted(chunks[0])))
        + ", where every passage carries its identifier, its text and its document."
    )
    assert len(sections) > 5 * len(documents), (
        str(len(documents))
        + " documents split into "
        + str(len(sections))
        + " sections. Each document is written in numbered sections, and a section is the unit "
        "a question is usually about."
    )
    with_header = [chunk["chunk_id"] for chunk in chunks
                   if re.search(config.DOCUMENT_HEADER_PATTERN, chunk["chunk_text"])]
    assert len(with_header) == 0, (
        "These passages still carry the document header: "
        + str(with_header[:5])
        + ". The header repeats the same words in every document, so it matches every question "
        "equally and pushes the passages that answer it out of the results."
    )
    lengths = [len(chunk["chunk_text"]) for chunk in chunks]
    average = sum(lengths) / len(lengths)
    assert (config.CHUNK_SIZE_CHARACTERS / 5 <= average <= config.CHUNK_SIZE_CHARACTERS
            and max(lengths) <= config.CHUNK_SIZE_CHARACTERS), (
        "Passages average "
        + str(int(average))
        + " characters, the longest "
        + str(max(lengths))
        + ", where the configuration asks for passages of up to "
        + str(config.CHUNK_SIZE_CHARACTERS)
        + ". Passages far longer return a whole document for every question; far shorter lose "
        "the sentence that gave them their meaning."
    )
    identifiers = [chunk["chunk_id"] for chunk in chunks]
    assert len(identifiers) == len(set(identifiers)), (
        "Passage identifiers repeat, so storing them would overwrite one passage with another."
    )
    words_by_document = {document["document_name"]: set(document["document_text"].split())
                         for document in documents}
    for chunk in chunks:
        words = chunk["chunk_text"].split()
        foreign = [word for word in words
                   if word not in words_by_document.get(chunk["document_name"], set())]
        assert len(words) > 0 and len(foreign) <= len(words) // 10, (
            "Passage "
            + str(chunk["chunk_id"])
            + " says it comes from "
            + str(chunk["document_name"])
            + " but "
            + str(len(foreign))
            + " of its "
            + str(len(words))
            + " words are not in that document, for example "
            + str(foreign[:5])
            + ". A passage has to cite the document it was cut from."
        )
    for service_code, policy in medical_policies["policies"].items():
        own_chunks = [re.sub(r"\s+", " ", chunk["chunk_text"]) for chunk in chunks
                      if chunk["document_name"] == config.SERVICE_POLICY_DOCUMENTS[service_code]]
        broken = [criterion["criterion_sentence"] for criterion in policy["criteria"]
                  if not any(criterion["criterion_sentence"] in chunk_text
                             for chunk_text in own_chunks)]
        assert len(broken) == 0, (
            "These criteria of "
            + config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " are not whole inside any one of its passages: "
            + str(broken[:3])
            + ". A criterion cut across two passages can no longer be read from either."
        )
    header = ("Document Policy 99 | Issue 1 | Owner: Utilisation Management | Review cycle: "
              "every six months")
    lines = []
    for first in "abcdefgh":
        for second in "abcdefg":
            lines.append("Reading " + first + second + " of the overlap check names break "
                         + first + second + ".")
    synthetic = [{"document_name": "Overlap-Check.pdf",
                  "document_text": "BRIGHTWATER HEALTH PLAN\nOverlap Check\n" + header
                                   + "\n1. Overlap check\n" + " ".join(lines)}]
    pieces = [str(chunk["chunk_text"]) for chunk in build_chunk_records(
        split_documents_into_sections(synthetic))]
    assert len(pieces) >= 3, (
        "One numbered section of "
        + str(len(" ".join(lines)))
        + " characters was cut into "
        + str(len(pieces))
        + " passages, where passages of up to "
        + str(config.CHUNK_SIZE_CHARACTERS)
        + " characters need at least three."
    )
    unshared = [position for position in range(1, len(pieces))
                if pieces[position].strip()[:20] not in pieces[position - 1]]
    assert len(unshared) == 0, (
        "Passages "
        + str(unshared)
        + " of one long section open with text the passage before them does not carry. "
        "Neighbouring passages of a section overlap by up to "
        + str(config.CHUNK_OVERLAP_CHARACTERS)
        + " characters, so a sentence cut at a boundary is still whole in one of them."
    )
    for description, document_text in [
            ("no header line", "BRIGHTWATER HEALTH PLAN\n1. Overlap check\n" + " ".join(lines)),
            ("two header lines", header + "\n" + header + "\n1. Overlap check\n"
             + " ".join(lines)),
            ("sections numbered from 2", header + "\n2. Overlap check\n" + " ".join(lines))]:
        refusal = None
        try:
            split_documents_into_sections([{"document_name": "Broken-Layout.pdf",
                                            "document_text": document_text}])
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and "Broken-Layout.pdf" in refusal, (
            "A document with "
            + description
            + " was split, giving "
            + str(refusal)
            + ". Every document carries one header line and sections numbered from 1, so a "
            "document laid out otherwise has been read wrongly and is refused, naming it."
        )


def test_the_index_holds_every_passage_once_with_the_document_it_came_from(
        knowledge_collection, document_passages):
    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    assert document_passages["problem"] is None, document_passages["problem"]
    collection = knowledge_collection["collection"]
    documents = document_passages["documents"]
    chunks = document_passages["chunks"]
    stored = collection.get(include=["metadatas", "documents"])
    assert collection.count() == len(chunks) == len(stored["ids"]), (
        "The vector store holds "
        + str(collection.count())
        + " passages where cutting the documents gives "
        + str(len(chunks))
        + ". More means the index was added to twice and repeats itself in every result; fewer "
        "means passages no search can reach."
    )
    assert len(set(stored["ids"])) == len(stored["ids"]), (
        "Stored passage identifiers repeat, so one passage has overwritten another and its text "
        "can no longer be found."
    )
    names = {document["document_name"] for document in documents}
    cited = [(metadata or {}).get("document_name") for metadata in stored["metadatas"]]
    unnamed = [value for value in cited if value not in names]
    assert len(unnamed) == 0, (
        str(len(unnamed))
        + " stored passages name no document from the folder, for example "
        + str(unnamed[:3])
        + ". The name is what lets an answer cite its source and a section be read from its "
        "own document alone."
    )
    by_document = {}
    for chunk in chunks:
        by_document[chunk["document_name"]] = by_document.get(chunk["document_name"], 0) + 1
    stored_by_document = {name: cited.count(name) for name in names}
    assert stored_by_document == by_document, (
        "Passages stored per document "
        + str(stored_by_document)
        + " differ from passages cut per document "
        + str(by_document)
        + ". A document with passages missing answers less than it says."
    )
    assert sorted(stored["documents"]) == sorted(chunk["chunk_text"] for chunk in chunks), (
        "The texts in the vector store are not the passages the documents are cut into, so a "
        "section read from the store is not the section the document states."
    )
    for chunk_id, text, metadata in zip(stored["ids"], stored["documents"], stored["metadatas"],
                                        strict=True):
        twins = [chunk for chunk in chunks if chunk["chunk_id"] == chunk_id]
        assert (len(twins) == 1 and twins[0]["chunk_text"] == text
                and twins[0]["document_name"] == (metadata or {}).get("document_name")), (
            "The stored passage "
            + str(chunk_id)
            + " does not carry the text and document of the passage cut under that identifier."
        )


def test_each_section_the_tools_read_is_its_own_documents_section_whole(
        knowledge_collection, document_passages):
    from config import config
    from tools.retrieval_tools import (read_documentation_to_send, read_office_guidance,
                                       read_reviewer_checks)

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    assert document_passages["problem"] is None, document_passages["problem"]
    collection = knowledge_collection["collection"]
    wanted = []
    for service_code, document_name in config.SERVICE_POLICY_DOCUMENTS.items():
        wanted.append(("the documentation to send for " + service_code, document_name,
                       config.DOCUMENTATION_SECTION_HEADING,
                       read_documentation_to_send(collection, service_code)))
    for evidence_type, document_name in config.EVIDENCE_GUIDE_DOCUMENTS.items():
        wanted.append(("the reviewer's checks for " + evidence_type, document_name,
                       config.REVIEWER_CHECKS_SECTION_HEADING,
                       read_reviewer_checks(collection, evidence_type)))
        wanted.append(("what to tell the requesting office about " + evidence_type,
                       document_name, config.OFFICE_MESSAGE_SECTION_HEADING,
                       read_office_guidance(collection, evidence_type)))
    for label, document_name, heading, passage in wanted:
        sections = [section["section_text"] for section in document_passages["sections"]
                    if section["document_name"] == document_name
                    and section["section_text"].startswith(heading + " ")]
        assert len(sections) == 1, (
            document_name
            + " holds "
            + str(len(sections))
            + " sections headed "
            + repr(heading)
            + " where it holds one."
        )
        expected = sections[0][len(heading) + 1:]
        assert passage == expected, (
            "Reading "
            + label
            + " gave "
            + repr(str(passage)[:160])
            + " where "
            + document_name
            + "'s section "
            + repr(heading)
            + " reads "
            + repr(expected[:160])
            + ". The tools read that section whole, from that document alone, without its "
            "heading."
        )
    for label, call_name, unknown in [("a service with no policy", "documentation", "XYZ-ABC"),
                                      ("an evidence type with no guide", "checks", "Rumour"),
                                      ("an evidence type with no guide", "office", "Hearsay")]:
        refusal = None
        try:
            if call_name == "documentation":
                read_documentation_to_send(collection, unknown)
            elif call_name == "checks":
                read_reviewer_checks(collection, unknown)
            else:
                read_office_guidance(collection, unknown)
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and unknown in refusal, (
            "Asking for a section of "
            + label
            + ", "
            + unknown
            + ", gave "
            + str(refusal)
            + ". It is refused with a ValueError naming it, never answered from another "
            "document."
        )


def test_the_chat_search_leaves_out_the_casebook_and_returns_the_nearest_passages_first(
        knowledge_collection):
    from config import config
    from knowledge.vector_index import search_documents

    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    collection = knowledge_collection["collection"]
    casebook_passages = []
    for document_name in config.CHAT_EXCLUDED_DOCUMENTS:
        casebook_passages.extend(collection.get(where={"document_name": document_name})["ids"])
    assert len(casebook_passages) > 0, (
        "The index holds no passage of "
        + str(config.CHAT_EXCLUDED_DOCUMENTS)
        + ", which is indexed with the other documents and left out of the chat's search only."
    )
    questions = []
    for service_code, document_name in config.SERVICE_POLICY_DOCUMENTS.items():
        questions.append(("What are the coverage criteria for "
                          + config.SERVICE_NAMES[service_code].lower() + "?", document_name))
    questions.append(("Mr Whitlock, aged 44, was referred for an MRI scan of the lumbar spine "
                      "after physiotherapy.", None))
    results = search_documents(collection, [pair[0] for pair in questions])
    assert len(results) == len(questions), (
        "search_documents answered "
        + str(len(results))
        + " lists for "
        + str(len(questions))
        + " questions, where it answers one list of passages a question, in order."
    )
    for (question, own_document), passages in zip(questions, results, strict=True):
        assert len(passages) == config.CHAT_RETRIEVAL_RESULT_COUNT and all(
                {"chunk_id", "chunk_text", "document_name", "distance"} <= set(passage)
                for passage in passages), (
            "The search for "
            + repr(question)
            + " returned "
            + str(len(passages))
            + " passages where it returns "
            + str(config.CHAT_RETRIEVAL_RESULT_COUNT)
            + ", each with its identifier, text, document and distance."
        )
        distances = [float(passage["distance"]) for passage in passages]
        found = [passage["document_name"] for passage in passages]
        assert distances == sorted(distances) and all(0 <= value <= 2 for value in distances), (
            "The search for "
            + repr(question)
            + " returned distances "
            + str([round(value, 3) for value in distances])
            + ". Passages come nearest first, at cosine distances between 0 and 2."
        )
        excluded = [name for name in found if name in config.CHAT_EXCLUDED_DOCUMENTS]
        assert len(excluded) == 0, (
            "The search for "
            + repr(question)
            + " returned passages of "
            + str(excluded)
            + ". The casebook names members and practices and is never quoted by the chat, "
            "however close its passages are."
        )
        if own_document is not None:
            assert own_document in found, (
                "The search for "
                + repr(question)
                + " found "
                + str(found)
                + " and not "
                + own_document
                + ", the policy that states those criteria."
            )


def test_each_service_is_read_from_its_own_medical_policy_criterion_by_criterion(
        medical_policies):
    from config import config

    assert medical_policies["problem"] is None, medical_policies["problem"]
    policies = medical_policies["policies"]
    stated = {
        "RAD-LSM": [("Minimum age", config.MINIMUM_AGE_CRITERION),
                    ("Conservative treatment or red flag",
                     config.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION),
                    ("Repeat imaging interval", config.REPEAT_IMAGING_CRITERION)],
        "RAD-CSM": [("Minimum age", config.MINIMUM_AGE_CRITERION),
                    ("Conservative treatment or red flag",
                     config.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION),
                    ("Repeat imaging interval", config.REPEAT_IMAGING_CRITERION)],
        "ORT-TKR": [("Minimum age", config.MINIMUM_AGE_CRITERION),
                    ("Radiographic severity", config.RADIOGRAPHIC_SEVERITY_CRITERION),
                    ("Conservative treatment", config.CONSERVATIVE_TREATMENT_CRITERION),
                    ("Knee function", config.KNEE_FUNCTION_CRITERION),
                    ("Body mass index", config.BODY_MASS_INDEX_BELOW_CRITERION)],
        "BAR-WLS": [("Minimum age", config.MINIMUM_AGE_CRITERION),
                    ("Body mass index", config.BODY_MASS_INDEX_WITH_CONDITION_CRITERION),
                    ("Weight-management programme", config.WEIGHT_PROGRAMME_CRITERION),
                    ("Psychological assessment", config.PSYCHOLOGICAL_ASSESSMENT_CRITERION)],
        "SLP-PSG": [("Minimum age", config.MINIMUM_AGE_CRITERION),
                    ("Daytime sleepiness", config.DAYTIME_SLEEPINESS_CRITERION),
                    ("In-laboratory need", config.LABORATORY_NEED_CRITERION)],
    }
    assert sorted(policies) == sorted(stated), (
        "Policies were read for "
        + str(sorted(policies))
        + " where every one of the five services has its own."
    )
    for service_code, criteria in stated.items():
        policy = policies[service_code]
        assert (policy.get("service_code") == service_code
                and policy.get("document_name") == config.SERVICE_POLICY_DOCUMENTS[service_code]), (
            "The policy read for "
            + service_code
            + " names the service "
            + repr(policy.get("service_code"))
            + " and the document "
            + repr(policy.get("document_name"))
            + ". A policy is read from the document configured for its own service and names "
            "both."
        )
        read = [(criterion.get("criterion_name"), criterion.get("criterion_kind"))
                for criterion in policy.get("criteria", [])]
        assert read == criteria, (
            config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " was read as the criteria "
            + str(read)
            + " where its section 4 states "
            + str(criteria)
            + ", in that order. Each numbered criterion is read whole, named as the policy names "
            "it, and a criterion of another policy is never added."
        )


def test_each_criterion_keeps_the_sentence_it_was_read_from_and_its_own_thresholds(
        medical_policies, document_texts):
    import re
    from decimal import Decimal

    from config import config

    assert medical_policies["problem"] is None, medical_policies["problem"]
    assert document_texts["problem"] is None, document_texts["problem"]
    texts = {document["document_name"]: re.sub(r"\s+", " ", document["document_text"])
             for document in document_texts["documents"]}
    stated = {
        "RAD-LSM": [{config.MINIMUM_AGE_RULE: 18}, {config.MINIMUM_TREATMENT_WEEKS_RULE: 6},
                    {config.REPEAT_SCAN_MONTHS_RULE: 12}],
        "RAD-CSM": [{config.MINIMUM_AGE_RULE: 18}, {config.MINIMUM_TREATMENT_WEEKS_RULE: 4},
                    {config.REPEAT_SCAN_MONTHS_RULE: 12}],
        "ORT-TKR": [{config.MINIMUM_AGE_RULE: 18}, {config.MINIMUM_XRAY_GRADE_RULE: 3},
                    {config.MINIMUM_TREATMENT_WEEKS_RULE: 12},
                    {config.MAXIMUM_KNEE_FUNCTION_SCORE_RULE: 26},
                    {config.BODY_MASS_INDEX_BELOW_RULE: Decimal("40.0")}],
        "BAR-WLS": [{config.MINIMUM_AGE_RULE: 18},
                    {config.MINIMUM_BODY_MASS_INDEX_RULE: Decimal("40.0"),
                     config.MINIMUM_BODY_MASS_INDEX_WITH_CONDITION_RULE: Decimal("35.0")},
                    {config.MINIMUM_PROGRAMME_MONTHS_RULE: 6}, {}],
        "SLP-PSG": [{config.MINIMUM_AGE_RULE: 18}, {config.MINIMUM_SLEEPINESS_SCORE_RULE: 10},
                    {}],
    }
    for service_code, thresholds in stated.items():
        document_name = config.SERVICE_POLICY_DOCUMENTS[service_code]
        criteria = medical_policies["policies"][service_code]["criteria"]
        section_start = texts[document_name].find("4. Coverage criteria")
        section_end = texts[document_name].find("5. Reading the criteria")
        section = texts[document_name][section_start:section_end]
        assert len(criteria) == len(thresholds) and section_start >= 0, (
            document_name
            + " was read as "
            + str(len(criteria))
            + " criteria where it states "
            + str(len(thresholds))
            + "."
        )
        for criterion, wanted in zip(criteria, thresholds, strict=True):
            sentence = str(criterion.get("criterion_sentence"))
            assert len(sentence) > 20 and sentence in section, (
                "The criterion "
                + str(criterion.get("criterion_name"))
                + " of "
                + document_name
                + " keeps the sentence "
                + repr(sentence[:160])
                + ", which is not written in section 4 of that policy. A criterion keeps the "
                "sentence it was read from, word for word, so the nurse and the letter quote "
                "the policy itself."
            )
            rules = criterion.get("rules", {})
            got = {rule_name: rules.get(rule_name) for rule_name in wanted}
            assert got == wanted, (
                "The criterion "
                + str(criterion.get("criterion_name"))
                + " of "
                + document_name
                + " was read with the thresholds "
                + str(got)
                + " where its sentence states "
                + str(wanted)
                + ". Each criterion keeps its own figures, read from its own policy, exactly."
            )


def test_the_red_flags_that_waive_the_treatment_length_are_those_each_policy_lists(
        medical_policies, document_texts):
    import re

    from config import config

    assert medical_policies["problem"] is None, medical_policies["problem"]
    assert document_texts["problem"] is None, document_texts["problem"]
    every_flag = sorted(set(config.RED_FLAG_NAME_MAPPING.values()))
    stated = {
        "RAD-LSM": ["Bowel or bladder dysfunction", "Saddle anaesthesia",
                    "Progressive neurological deficit", "Suspected malignancy",
                    "Suspected infection", "Significant trauma"],
        "RAD-CSM": ["Bowel or bladder dysfunction", "Progressive neurological deficit",
                    "Suspected malignancy", "Suspected infection", "Significant trauma"],
    }
    texts = {document["document_name"]: re.sub(r"\s+", " ", document["document_text"])
             for document in document_texts["documents"]}
    for service_code, flags in stated.items():
        criteria = [criterion for criterion in medical_policies["policies"][service_code][
            "criteria"] if criterion.get("criterion_kind")
            == config.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION]
        assert len(criteria) == 1, (
            config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " was read with "
            + str(len(criteria))
            + " criteria of conservative treatment or a red flag, where it states one."
        )
        listed = criteria[0].get("rules", {}).get(config.LISTED_RED_FLAGS_RULE)
        assert sorted(listed or []) == sorted(flags) and len(listed) == len(set(listed)), (
            "The red flags read from "
            + config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " are "
            + str(listed)
            + " where it lists "
            + str(flags)
            + ". A red flag waives the treatment length only under the policy that lists it: "
            "the cervical spine policy leaves saddle anaesthesia out."
        )
        assert set(listed) <= set(every_flag), (
            "The red flags read from "
            + config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " are "
            + str(listed)
            + ", not all of them the canonical names "
            + str(every_flag)
            + " the questionnaire's answers are cleaned to, so a reported flag could never "
            "match."
        )
        assert "red flag symptom is one of" in texts[config.SERVICE_POLICY_DOCUMENTS[
            service_code]], (
            config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " no longer states its list of red flags, so the list cannot have been read from it."
        )
    for service_code in ["ORT-TKR", "BAR-WLS", "SLP-PSG"]:
        flagged = [criterion.get("criterion_name") for criterion in medical_policies["policies"][
            service_code]["criteria"] if config.LISTED_RED_FLAGS_RULE in criterion.get("rules",
                                                                                        {})]
        assert len(flagged) == 0, (
            config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " was read with red flags under "
            + str(flagged)
            + ", though it lists none. A red flag of one policy never waives a criterion of "
            "another."
        )


def test_the_listed_conditions_are_read_as_the_canonical_names_each_policy_lists(
        medical_policies):
    from config import config

    assert medical_policies["problem"] is None, medical_policies["problem"]
    stated = {
        ("BAR-WLS", config.BODY_MASS_INDEX_WITH_CONDITION_CRITERION):
            ["Hypertension", "Obstructive sleep apnoea", "Type 2 diabetes"],
        ("SLP-PSG", config.LABORATORY_NEED_CRITERION):
            ["Chronic obstructive pulmonary disease", "Heart failure", "Neuromuscular disease"],
    }
    canonical = set(config.CONDITION_MAPPING.values())
    for (service_code, criterion_kind), conditions in stated.items():
        criteria = [criterion for criterion in medical_policies["policies"][service_code][
            "criteria"] if criterion.get("criterion_kind") == criterion_kind]
        assert len(criteria) == 1, (
            config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " was read with "
            + str(len(criteria))
            + " criteria of the kind "
            + criterion_kind
            + ", where it states one."
        )
        listed = criteria[0].get("rules", {}).get(config.LISTED_CONDITIONS_RULE)
        assert sorted(listed or []) == sorted(conditions), (
            "The listed conditions read from "
            + config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " are "
            + str(listed)
            + " where it lists "
            + str(conditions)
            + ". The conditions are read as written in the policy and turned into the canonical "
            "names the questionnaire's answers are cleaned to."
        )
        assert set(listed) <= canonical, (
            "The listed conditions "
            + str(listed)
            + " are not all canonical condition names, so a member's condition could never match."
        )
    for service_code in ["RAD-LSM", "RAD-CSM", "ORT-TKR"]:
        listing = [criterion.get("criterion_name") for criterion in medical_policies["policies"][
            service_code]["criteria"] if config.LISTED_CONDITIONS_RULE in criterion.get("rules",
                                                                                         {})]
        assert len(listing) == 0, (
            config.SERVICE_POLICY_DOCUMENTS[service_code]
            + " was read with listed conditions under "
            + str(listing)
            + ", though it lists none."
        )


def test_a_service_with_no_policy_is_refused_and_a_policy_reads_the_same_every_time(
        medical_policies):
    from config import config
    from knowledge.policy_reading import read_medical_policy

    assert medical_policies["problem"] is None, medical_policies["problem"]
    refusal = None
    try:
        read_medical_policy("XYZ-ABC")
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and "XYZ-ABC" in refusal, (
        "Reading the policy of a service with none configured gave "
        + str(refusal)
        + ". A service with no medical policy has no criteria to screen against, and is refused "
        "with a ValueError naming it."
    )
    for service_code in config.SERVICE_POLICY_DOCUMENTS:
        again = read_medical_policy(service_code)
        assert again == medical_policies["policies"][service_code], (
            "The policy of "
            + service_code
            + " reads differently the second time. A policy is read from its document, the "
            "same way every time."
        )


def test_each_criterion_is_met_at_its_own_boundary_and_not_met_just_past_it(live_files):
    from config import config
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    requests = live_files["requests"]
    templates = {}
    for service_code in ["RAD-LSM", "ORT-TKR", "BAR-WLS", "SLP-PSG"]:
        templates[service_code] = requests[requests[config.SERVICE_CODE_COLUMN]
                                           == service_code].iloc[0].to_dict()
    invented = {
        "RAD-LSM": [(config.MINIMUM_AGE_CRITERION, "Minimum age", {config.MINIMUM_AGE_RULE: 23}),
                    (config.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION,
                     "Conservative treatment or red flag",
                     {config.MINIMUM_TREATMENT_WEEKS_RULE: 9,
                      config.LISTED_RED_FLAGS_RULE: ["Significant trauma"]}),
                    (config.REPEAT_IMAGING_CRITERION, "Repeat imaging interval",
                     {config.REPEAT_SCAN_MONTHS_RULE: 7})],
        "ORT-TKR": [(config.RADIOGRAPHIC_SEVERITY_CRITERION, "Radiographic severity",
                     {config.MINIMUM_XRAY_GRADE_RULE: 2}),
                    (config.CONSERVATIVE_TREATMENT_CRITERION, "Conservative treatment",
                     {config.MINIMUM_TREATMENT_WEEKS_RULE: 15}),
                    (config.KNEE_FUNCTION_CRITERION, "Knee function",
                     {config.MAXIMUM_KNEE_FUNCTION_SCORE_RULE: 31})],
        "BAR-WLS": [(config.WEIGHT_PROGRAMME_CRITERION, "Weight-management programme",
                     {config.MINIMUM_PROGRAMME_MONTHS_RULE: 9}),
                    (config.PSYCHOLOGICAL_ASSESSMENT_CRITERION, "Psychological assessment", {})],
        "SLP-PSG": [(config.DAYTIME_SLEEPINESS_CRITERION, "Daytime sleepiness",
                     {config.MINIMUM_SLEEPINESS_SCORE_RULE: 14})],
    }
    cases = [
        ("RAD-LSM", "Minimum age", {config.MEMBER_AGE_COLUMN: 23}, config.CRITERION_MET),
        ("RAD-LSM", "Minimum age", {config.MEMBER_AGE_COLUMN: 22}, config.CRITERION_NOT_MET),
        ("RAD-LSM", "Conservative treatment or red flag",
         {config.TREATMENT_WEEKS_COLUMN: 9, config.RED_FLAG_COLUMN: config.NO_RED_FLAG},
         config.CRITERION_MET),
        ("RAD-LSM", "Conservative treatment or red flag",
         {config.TREATMENT_WEEKS_COLUMN: 8, config.RED_FLAG_COLUMN: config.NO_RED_FLAG},
         config.CRITERION_NOT_MET),
        ("RAD-LSM", "Repeat imaging interval",
         {config.PREVIOUS_SCAN_COLUMN: config.BOOLEAN_YES, config.MONTHS_SINCE_SCAN_COLUMN: 7,
          config.NEW_NEUROLOGICAL_SYMPTOMS_COLUMN: config.BOOLEAN_NO}, config.CRITERION_MET),
        ("RAD-LSM", "Repeat imaging interval",
         {config.PREVIOUS_SCAN_COLUMN: config.BOOLEAN_YES, config.MONTHS_SINCE_SCAN_COLUMN: 6,
          config.NEW_NEUROLOGICAL_SYMPTOMS_COLUMN: config.BOOLEAN_NO}, config.CRITERION_NOT_MET),
        ("ORT-TKR", "Radiographic severity", {config.XRAY_GRADE_COLUMN: 2}, config.CRITERION_MET),
        ("ORT-TKR", "Radiographic severity", {config.XRAY_GRADE_COLUMN: 1},
         config.CRITERION_NOT_MET),
        ("ORT-TKR", "Conservative treatment", {config.TREATMENT_WEEKS_COLUMN: 15},
         config.CRITERION_MET),
        ("ORT-TKR", "Conservative treatment", {config.TREATMENT_WEEKS_COLUMN: 14},
         config.CRITERION_NOT_MET),
        ("ORT-TKR", "Knee function", {config.KNEE_FUNCTION_SCORE_COLUMN: 31},
         config.CRITERION_MET),
        ("ORT-TKR", "Knee function", {config.KNEE_FUNCTION_SCORE_COLUMN: 32},
         config.CRITERION_NOT_MET),
        ("BAR-WLS", "Weight-management programme", {config.PROGRAMME_MONTHS_COLUMN: 9},
         config.CRITERION_MET),
        ("BAR-WLS", "Weight-management programme", {config.PROGRAMME_MONTHS_COLUMN: 8},
         config.CRITERION_NOT_MET),
        ("BAR-WLS", "Psychological assessment",
         {config.PSYCHOLOGICAL_ASSESSMENT_COLUMN: config.PSYCHOLOGY_COMPLETED},
         config.CRITERION_MET),
        ("BAR-WLS", "Psychological assessment",
         {config.PSYCHOLOGICAL_ASSESSMENT_COLUMN: config.PSYCHOLOGICAL_ASSESSMENT_MAPPING[
             "not completed"]}, config.CRITERION_NOT_MET),
        ("SLP-PSG", "Daytime sleepiness", {config.SLEEPINESS_SCORE_COLUMN: 14},
         config.CRITERION_MET),
        ("SLP-PSG", "Daytime sleepiness", {config.SLEEPINESS_SCORE_COLUMN: 13},
         config.CRITERION_NOT_MET),
    ]
    wrong = []
    for service_code, criterion_name, answers, expected in cases:
        policy = {"service_code": service_code,
                  "document_name": "Invented-" + service_code + "-Policy.pdf",
                  "criteria": [{"criterion_kind": kind, "criterion_name": name,
                                "criterion_sentence": "An invented criterion: " + name + ".",
                                "rules": rules}
                               for kind, name, rules in invented[service_code]]}
        request = dict(templates[service_code])
        request[config.REQUEST_REFERENCE_COLUMN] = "PA-950001"
        request.update(answers)
        screening = screen_request(request, policy)
        results = {criterion.get("criterion_name"): criterion.get("result")
                   for criterion in screening.get("criteria", [])}
        if results.get(criterion_name) != expected:
            wrong.append(criterion_name + " with " + str(answers) + " is "
                         + str(results.get(criterion_name)) + ", not " + expected)
    assert len(wrong) == 0, (
        "Under invented policies whose figures no Brightwater policy uses, the screening "
        "misplaces boundaries: "
        + "; ".join(wrong[:5])
        + ". A minimum is met at the figure itself, a maximum likewise, and every figure comes "
        "from the policy handed over, never from a figure written into the code."
    )


def test_a_criterion_met_two_ways_is_met_by_either_and_not_documented_only_when_undecided(
        live_files):
    from decimal import Decimal

    from config import config
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    requests = live_files["requests"]
    blank = float("nan")
    invented = {
        "RAD-CSM": (config.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION,
                    "Conservative treatment or red flag",
                    {config.MINIMUM_TREATMENT_WEEKS_RULE: 10,
                     config.LISTED_RED_FLAGS_RULE: ["Suspected infection", "Significant trauma"]}),
        "RAD-LSM": (config.REPEAT_IMAGING_CRITERION, "Repeat imaging interval",
                    {config.REPEAT_SCAN_MONTHS_RULE: 9}),
        "SLP-PSG": (config.LABORATORY_NEED_CRITERION, "In-laboratory need",
                    {config.LISTED_CONDITIONS_RULE: ["Heart failure"]}),
        "BAR-WLS": (config.BODY_MASS_INDEX_WITH_CONDITION_CRITERION, "Body mass index",
                    {config.MINIMUM_BODY_MASS_INDEX_RULE: Decimal("42.0"),
                     config.MINIMUM_BODY_MASS_INDEX_WITH_CONDITION_RULE: Decimal("37.0"),
                     config.LISTED_CONDITIONS_RULE: ["Hypertension"]}),
    }
    weeks, flag = config.TREATMENT_WEEKS_COLUMN, config.RED_FLAG_COLUMN
    scan, months = config.PREVIOUS_SCAN_COLUMN, config.MONTHS_SINCE_SCAN_COLUMN
    symptoms = config.NEW_NEUROLOGICAL_SYMPTOMS_COLUMN
    conditions, home_test = config.OTHER_CONDITIONS_COLUMN, config.HOME_SLEEP_TEST_COLUMN
    height, weight = config.HEIGHT_COLUMN, config.WEIGHT_COLUMN
    met, not_met = config.CRITERION_MET, config.CRITERION_NOT_MET
    undocumented = config.CRITERION_NOT_DOCUMENTED
    cases = [
        ("RAD-CSM", {weeks: blank, flag: "Significant trauma"}, met),
        ("RAD-CSM", {weeks: 10, flag: blank}, met),
        ("RAD-CSM", {weeks: 3, flag: "Saddle anaesthesia"}, not_met),
        ("RAD-CSM", {weeks: 3, flag: config.NO_RED_FLAG}, not_met),
        ("RAD-CSM", {weeks: 3, flag: blank}, undocumented),
        ("RAD-CSM", {weeks: blank, flag: config.NO_RED_FLAG}, undocumented),
        ("RAD-LSM", {scan: config.BOOLEAN_NO, months: blank, symptoms: blank}, met),
        ("RAD-LSM", {scan: config.BOOLEAN_YES, months: 9, symptoms: blank}, met),
        ("RAD-LSM", {scan: config.BOOLEAN_YES, months: 2, symptoms: config.BOOLEAN_YES}, met),
        ("RAD-LSM", {scan: config.BOOLEAN_YES, months: 2, symptoms: config.BOOLEAN_NO}, not_met),
        ("RAD-LSM", {scan: config.BOOLEAN_YES, months: blank, symptoms: config.BOOLEAN_NO},
         undocumented),
        ("RAD-LSM", {scan: blank, months: blank, symptoms: blank}, undocumented),
        ("SLP-PSG", {conditions: "Heart failure; Hypertension", home_test: blank}, met),
        ("SLP-PSG", {conditions: blank, home_test: "Inconclusive"}, met),
        ("SLP-PSG", {conditions: config.NO_OTHER_CONDITIONS, home_test: "Negative"}, met),
        ("SLP-PSG", {conditions: config.NO_OTHER_CONDITIONS, home_test: "Positive"}, not_met),
        ("SLP-PSG", {conditions: blank, home_test: "Positive"}, undocumented),
        ("SLP-PSG", {conditions: "Hypertension", home_test: blank}, undocumented),
        ("BAR-WLS", {height: 160.0, weight: 110.0, conditions: blank}, met),
        ("BAR-WLS", {height: 160.0, weight: 97.0, conditions: "Asthma; Hypertension"}, met),
        ("BAR-WLS", {height: 160.0, weight: 97.0, conditions: config.NO_OTHER_CONDITIONS},
         not_met),
        ("BAR-WLS", {height: 160.0, weight: 97.0, conditions: blank}, undocumented),
        ("BAR-WLS", {height: 160.0, weight: 90.0, conditions: "Hypertension"}, not_met),
        ("BAR-WLS", {height: blank, weight: 110.0, conditions: "Hypertension"}, undocumented),
    ]
    wrong = []
    for service_code, answers, expected in cases:
        kind, name, rules = invented[service_code]
        policy = {"service_code": service_code,
                  "document_name": "Invented-" + service_code + "-Policy.pdf",
                  "criteria": [{"criterion_kind": kind, "criterion_name": name,
                                "criterion_sentence": "An invented criterion: " + name + ".",
                                "rules": rules}]}
        request = requests[requests[config.SERVICE_CODE_COLUMN] == service_code].iloc[0].to_dict()
        request[config.REQUEST_REFERENCE_COLUMN] = "PA-950002"
        request.update(answers)
        screening = screen_request(request, policy)
        result = screening["criteria"][0].get("result")
        if result != expected:
            wrong.append(name + " with " + str(answers) + " is " + str(result) + ", not "
                         + expected)
    assert len(wrong) == 0, (
        "Criteria that can be met in two ways are screened wrongly: "
        + "; ".join(wrong[:5])
        + ". Either way being met is enough, even with the other way's answer blank; the "
        "criterion is Not met only when neither way is met and both can be read, and Not "
        "documented when a blank answer leaves it undecided."
    )


def test_the_body_mass_index_is_worked_out_exactly_and_kept_half_up(live_files):
    from decimal import Decimal

    from config import config
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    requests = live_files["requests"]
    knee = requests[requests[config.SERVICE_CODE_COLUMN] == "ORT-TKR"].iloc[0].to_dict()
    policy = {"service_code": "ORT-TKR", "document_name": "Invented-Knee-Policy.pdf",
              "criteria": [{"criterion_kind": config.BODY_MASS_INDEX_BELOW_CRITERION,
                            "criterion_name": "Body mass index",
                            "criterion_sentence": "The body mass index is below 36.3.",
                            "rules": {config.BODY_MASS_INDEX_BELOW_RULE: Decimal("36.3")}}]}
    cases = [(160.0, 92.8, 36.3, config.CRITERION_NOT_MET),
             (160.0, 92.7, 36.2, config.CRITERION_MET),
             (152.0, 72.2, 31.3, config.CRITERION_MET),
             (160.0, 80.0, 31.3, config.CRITERION_MET),
             (177.8, 98.4, 31.1, config.CRITERION_MET),
             (150.0, 81.8, 36.4, config.CRITERION_NOT_MET)]
    wrong = []
    for height, weight, expected_index, expected_result in cases:
        request = dict(knee)
        request[config.REQUEST_REFERENCE_COLUMN] = "PA-950003"
        request[config.HEIGHT_COLUMN] = height
        request[config.WEIGHT_COLUMN] = weight
        screening = screen_request(request, policy)
        index = screening.get("body_mass_index")
        result = screening["criteria"][0].get("result")
        if index is None or abs(float(index) - expected_index) > 1e-9 or result != expected_result:
            wrong.append(str(weight) + " kg at " + str(height) + " cm gives " + str(index) + ", "
                         + str(result) + ", not " + str(expected_index) + ", " + expected_result)
    assert len(wrong) == 0, (
        "The body mass index is not worked out as the Prior Authorisation Rules set out: "
        + "; ".join(wrong[:4])
        + ". The weight in kilograms is divided by the square of the height in metres exactly, "
        "and only then kept to one decimal, half up: 92.8 kg at 160 cm is 36.25, kept as 36.3, "
        "which is not below 36.3. Arithmetic in binary fractions makes it 36.2499... and keeps "
        "36.2."
    )
    request = dict(knee)
    request[config.REQUEST_REFERENCE_COLUMN] = "PA-950004"
    request[config.WEIGHT_COLUMN] = float("nan")
    screening = screen_request(request, policy)
    assert (screening.get("body_mass_index") is None
            and screening["criteria"][0].get("result") == config.CRITERION_NOT_DOCUMENTED), (
        "With the weight left blank the body mass index is "
        + str(screening.get("body_mass_index"))
        + " and the criterion "
        + str(screening["criteria"][0].get("result"))
        + ". A body mass index cannot be worked out without both answers, so there is none and "
        "the criterion is Not documented."
    )


def test_the_screening_and_the_decisions_open_follow_the_criteria_results(live_files):
    from config import config
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    requests = live_files["requests"]
    knee = requests[requests[config.SERVICE_CODE_COLUMN] == "ORT-TKR"].iloc[0].to_dict()
    policy = {"service_code": "ORT-TKR", "document_name": "Invented-Knee-Policy.pdf",
              "criteria": [
                  {"criterion_kind": config.MINIMUM_AGE_CRITERION, "criterion_name": "Minimum age",
                   "criterion_sentence": "The member is aged 40 years or over.",
                   "rules": {config.MINIMUM_AGE_RULE: 40}},
                  {"criterion_kind": config.RADIOGRAPHIC_SEVERITY_CRITERION,
                   "criterion_name": "Radiographic severity",
                   "criterion_sentence": "A weight-bearing X-ray shows grade 2 or higher.",
                   "rules": {config.MINIMUM_XRAY_GRADE_RULE: 2}},
                  {"criterion_kind": config.KNEE_FUNCTION_CRITERION,
                   "criterion_name": "Knee function",
                   "criterion_sentence": "The Oxford Knee Score is 30 or lower.",
                   "rules": {config.MAXIMUM_KNEE_FUNCTION_SCORE_RULE: 30}}]}
    blank = float("nan")
    age, grade = config.MEMBER_AGE_COLUMN, config.XRAY_GRADE_COLUMN
    score = config.KNEE_FUNCTION_SCORE_COLUMN
    approve, inform = config.DECISION_APPROVE, config.DECISION_REQUEST_INFORMATION
    refer = config.DECISION_REFER
    cases = [
        ({age: 60, grade: 3, score: 20}, approve, [3, 0, 0], [approve, refer]),
        ({age: 60, grade: blank, score: 20}, inform, [2, 0, 1], [inform, refer]),
        ({age: blank, grade: blank, score: 20}, inform, [1, 0, 2], [inform, refer]),
        ({age: 30, grade: 3, score: 20}, refer, [2, 1, 0], [refer]),
        ({age: 30, grade: blank, score: 40}, refer, [0, 2, 1], [refer]),
    ]
    count_columns = config.CRITERIA_COUNT_COLUMNS
    for answers, expected_screening, expected_counts, expected_open in cases:
        request = dict(knee)
        request[config.REQUEST_REFERENCE_COLUMN] = "PA-950005"
        request.update(answers)
        screening = screen_request(request, policy)
        counts = [screening.get(column_name) for column_name in count_columns]
        assert (screening.get("screening") == expected_screening and counts == expected_counts
                and list(screening.get("decisions_open", [])) == expected_open
                and screening.get("request_reference") == "PA-950005"
                and screening.get("policy_document") == "Invented-Knee-Policy.pdf"), (
            "A request with "
            + str(answers)
            + " screens as "
            + str(screening.get("screening"))
            + " with counts "
            + str(counts)
            + " and the decisions open "
            + str(screening.get("decisions_open"))
            + ", where the Rules give "
            + expected_screening
            + ", "
            + str(expected_counts)
            + " and "
            + str(expected_open)
            + ". Any criterion Not met screens as REFER TO PHYSICIAN, the only decision open; "
            "otherwise any Not documented screens as REQUEST MORE INFORMATION, with referral "
            "still open; only every criterion Met screens as APPROVE, with referral still open."
        )
    cervical = requests[requests[config.SERVICE_CODE_COLUMN] == "RAD-CSM"].iloc[0].to_dict()
    refusal = None
    try:
        screen_request(cervical, policy)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and cervical[config.REQUEST_REFERENCE_COLUMN] in refusal, (
        "A cervical spine request screened against a knee policy gave "
        + str(refusal)
        + ". A request is screened only against the policy of its own service; any other is "
        "refused, naming the request."
    )


def test_each_criterion_not_documented_names_its_blank_answers_and_the_worked_example_holds(
        live_files):
    from decimal import Decimal

    from config import config
    from data_pipeline.request_cleaning import clean_request_records
    from tools.screening_tools import screen_request

    assert live_files["problem"] is None, live_files["problem"]
    requests = live_files["requests"]
    policy = {"service_code": "RAD-LSM", "document_name": "Worked-Example-Policy.pdf",
              "criteria": [
                  {"criterion_kind": config.MINIMUM_AGE_CRITERION, "criterion_name": "Minimum age",
                   "criterion_sentence": "The member is aged 21 years or over.",
                   "rules": {config.MINIMUM_AGE_RULE: 21}},
                  {"criterion_kind": config.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION,
                   "criterion_name": "Conservative treatment or red flag",
                   "criterion_sentence": ("The member has completed at least 8 whole weeks of "
                                          "conservative treatment, or a red flag symptom is "
                                          "reported."),
                   "rules": {config.MINIMUM_TREATMENT_WEEKS_RULE: 8,
                             config.LISTED_RED_FLAGS_RULE: sorted(set(
                                 config.RED_FLAG_NAME_MAPPING.values()))}},
                  {"criterion_kind": config.BODY_MASS_INDEX_BELOW_CRITERION,
                   "criterion_name": "Body mass index",
                   "criterion_sentence": "The body mass index is below 38.0.",
                   "rules": {config.BODY_MASS_INDEX_BELOW_RULE: Decimal("38.0")}}]}
    lumbar = requests[requests[config.SERVICE_CODE_COLUMN] == "RAD-LSM"].iloc[0].to_dict()
    blank = float("nan")
    request = dict(lumbar)
    request[config.REQUEST_REFERENCE_COLUMN] = "PA-950006"
    request.update({config.MEMBER_AGE_COLUMN: blank, config.TREATMENT_WEEKS_COLUMN: 3,
                    config.RED_FLAG_COLUMN: blank, config.HEIGHT_COLUMN: blank,
                    config.WEIGHT_COLUMN: 80.0})
    screening = screen_request(request, policy)
    named = {criterion.get("criterion_name"): list(criterion.get("missing_answers", []))
             for criterion in screening["criteria"]}
    expected = {"Minimum age": [config.MEMBER_AGE_COLUMN],
                "Conservative treatment or red flag": [config.RED_FLAG_COLUMN],
                "Body mass index": [config.HEIGHT_COLUMN]}
    assert named == expected, (
        "The criteria Not documented name the blank answers "
        + str(named)
        + " where the answers each needs and lacks are "
        + str(expected)
        + ". Each criterion Not documented names exactly the questionnaire answers left blank "
        "that it needs, for the letter asking for them; a criterion that can be decided names "
        "none."
    )
    raw = live_files["raw_requests"]
    written_codes = raw[config.SERVICE_CODE_COLUMN].str.lower().str.replace(" ", "-")
    written = raw[written_codes == "rad-lsm"].head(1).copy()
    written[config.REQUEST_REFERENCE_COLUMN] = "PA-950007"
    written[config.SUBMISSION_SEQUENCE_COLUMN] = "1"
    written[config.MEMBER_AGE_COLUMN] = "57"
    written[config.TREATMENT_WEEKS_COLUMN] = "52 days"
    written[config.RED_FLAG_COLUMN] = "Nil"
    written[config.HEIGHT_COLUMN] = "5 ft 10 in"
    written[config.WEIGHT_COLUMN] = "15 st 7 lb"
    outcomes = {}
    for label, treatment, red_flag in [("as faxed", "52 days", "Nil"),
                                       ("with 56 days", "56 days", "Nil"),
                                       ("with the red flag blank", "52 days", None)]:
        variant = written.copy()
        variant[config.TREATMENT_WEEKS_COLUMN] = treatment
        variant[config.RED_FLAG_COLUMN] = red_flag
        cleaned = clean_request_records(variant.reset_index(drop=True),
                                        config.REQUEST_VALUE_MAPPINGS,
                                        config.REQUEST_WHOLE_NUMBER_PATTERNS)
        outcome = screen_request(cleaned.iloc[0].to_dict(), policy)
        outcomes[label] = (outcome.get("screening"),
                           [criterion.get("result") for criterion in outcome["criteria"]],
                           None if outcome.get("body_mass_index") is None
                           else float(outcome["body_mass_index"]),
                           list(outcome.get("decisions_open", [])))
    met, not_met = config.CRITERION_MET, config.CRITERION_NOT_MET
    expected_outcomes = {
        "as faxed": (config.DECISION_REFER, [met, not_met, met], 31.1, [config.DECISION_REFER]),
        "with 56 days": (config.DECISION_APPROVE, [met, met, met], 31.1,
                         [config.DECISION_APPROVE, config.DECISION_REFER]),
        "with the red flag blank": (config.DECISION_REQUEST_INFORMATION,
                                    [met, config.CRITERION_NOT_DOCUMENTED, met], 31.1,
                                    [config.DECISION_REQUEST_INFORMATION, config.DECISION_REFER]),
    }
    assert outcomes == expected_outcomes, (
        "The worked example of the Prior Authorisation Rules, section 12, screens as "
        + str(outcomes)
        + " where the Rules give "
        + str(expected_outcomes)
        + ": 52 days is 7 whole weeks, short of 8, with Nil read as no red flag, so the "
        "treatment criterion is Not met; 5 ft 10 in and 15 st 7 lb give a body mass index of "
        "31.1; had the fax given 56 days every criterion would be Met, and had it left the red "
        "flag blank the screening would be REQUEST MORE INFORMATION."
    )


def test_each_reviewing_agent_was_called_once_and_in_order(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    listed = saved_run["calls_at_gate"]
    assert (listed["status"] == 200 and isinstance(listed["body"], dict)
            and {"calls", "call_count", "expected_call_count"} <= set(listed["body"])
            and all("agent_name" in call for call in listed["body"]["calls"])), (
        "Reading the run's model calls at the pause returned "
        + str(listed["status"])
        + " with "
        + str(listed["body"])[:300]
        + ", where the audit area lists every call under the agent that made it, with their "
        "count and the count expected."
    )
    at_gate = listed["body"]
    reviewing = [config.AGENT_NAME_PLANNER, config.AGENT_NAME_CRITERIA,
                 config.AGENT_NAME_EVIDENCE, config.AGENT_NAME_PREDICTIONS,
                 config.AGENT_NAME_WRITER]
    called = [call["agent_name"] for call in at_gate["calls"]]
    assert at_gate["call_count"] == len(at_gate["calls"]) == config.LLM_CALLS_BEFORE_DECISION, (
        "Reaching the UM Nurse Reviewer recorded a call count of "
        + str(at_gate["call_count"])
        + " and listed "
        + str(len(at_gate["calls"]))
        + " language model calls where the workflow allows "
        + str(config.LLM_CALLS_BEFORE_DECISION)
        + ", one per reviewing agent. More means an agent ran twice; fewer, that one never ran."
    )
    assert called == reviewing, (
        "The agents ran in the order "
        + str(called)
        + ". Each one reads what the one before it concluded: the criteria are explained "
        "against the plan, the evidence is reviewed against it, the figures are weighed with "
        "the plan in hand, and the recommendation draws on all of them."
    )
    assert at_gate["expected_call_count"] == config.LLM_CALLS_BEFORE_DECISION, (
        "Before any decision the service expected "
        + str(at_gate["expected_call_count"])
        + " calls. Until a decision is taken only the reviewing agents' calls are expected."
    )
    assert saved_run["at_gate"].get("llm_call_count") == config.LLM_CALLS_BEFORE_DECISION, (
        "The review record at the pause counts "
        + str(saved_run["at_gate"].get("llm_call_count"))
        + " calls where five were made."
    )


def test_every_model_call_is_recorded_with_what_it_cost(saved_run):
    from config import config
    from persistence.database import session_factory
    from persistence.models import LlmCall

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    final_calls = saved_run["final_calls"]
    assert final_calls["status"] == 200 and isinstance(final_calls["body"], dict), (
        "Reading the run's model calls after the decision returned "
        + str(final_calls["status"])
        + " with "
        + str(final_calls["body"])[:300]
        + "."
    )
    calls = final_calls["body"]["calls"]
    called = [call.get("agent_name") for call in calls]
    added_agents = [config.AGENT_NAME_LETTER, config.AGENT_NAME_NOTICE]
    expected_count = config.LLM_CALLS_BEFORE_DECISION + len(added_agents)
    assert (called[config.LLM_CALLS_BEFORE_DECISION:] == added_agents
            and final_calls["body"]["call_count"] == len(calls) == expected_count
            and final_calls["body"]["expected_call_count"]
            == config.LLM_CALLS_BY_DECISION[config.DECISION_APPROVE]), (
        "After the approval the run lists the calls "
        + str(called)
        + " ("
        + str(final_calls["body"].get("call_count"))
        + " of "
        + str(final_calls["body"].get("expected_call_count"))
        + " expected) where an approval adds the provider authorisation letter and then the "
        "member notice to the five reviewing calls."
    )
    for call in calls:
        assert (isinstance(call.get("prompt_characters"), int) and call["prompt_characters"] > 200
                and isinstance(call.get("response_characters"), int)
                and call["response_characters"] > 0
                and isinstance(call.get("latency_milliseconds"), int)
                and call["latency_milliseconds"] >= 0
                and isinstance(call.get("model_name"), str) and call["model_name"]), (
            "The call of "
            + str(call.get("agent_name"))
            + " is recorded as "
            + str({key: call.get(key) for key in ["model_name", "prompt_characters",
                                                  "response_characters",
                                                  "latency_milliseconds"]})
            + ". Every call is recorded with the model that answered, the characters sent and "
            "received, and the milliseconds it took, which is what it cost."
        )
    assert final_calls["body"]["total_latency_milliseconds"] == sum(
            call["latency_milliseconds"] for call in calls), (
        "The run's total latency of "
        + str(final_calls["body"]["total_latency_milliseconds"])
        + " milliseconds is not the sum of its calls'."
    )
    with session_factory() as session:
        stored = session.query(LlmCall).filter(
            LlmCall.run_id == saved_run["at_gate"]["run_id"]).all()
    assert len(stored) == expected_count and sorted(
            row.agent_name for row in stored) == sorted(called), (
        "The llm_calls table holds "
        + str(len(stored))
        + " calls for the run, by "
        + str(sorted(row.agent_name for row in stored))
        + ", where the run made "
        + str(expected_count)
        + ", by "
        + str(sorted(called))
        + ". Each call is recorded once, under the run that made it."
    )


def test_the_review_reaches_the_nurse_as_a_recommendation_among_the_decisions_open(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    at_gate = saved_run["at_gate"]
    detail = saved_run["detail"]
    assert at_gate.get("decisions_open") == detail["screening"]["decisions_open"], (
        "The review offers the decisions "
        + str(at_gate.get("decisions_open"))
        + " where the screening of "
        + saved_run["request_reference"]
        + " leaves "
        + str(detail["screening"]["decisions_open"])
        + " open."
    )
    assert at_gate.get("recommended_decision") in at_gate.get("decisions_open", []), (
        "The review recommends "
        + repr(at_gate.get("recommended_decision"))
        + ", which is not among the decisions open "
        + str(at_gate.get("decisions_open"))
        + ". A recommendation the screening does not allow could never be taken."
    )
    write_ups = {key: str(at_gate.get(key) or "") for key in
                 ["review_plan_text", "criteria_analysis_text", "evidence_review_text",
                  "prediction_analysis_text", "recommendation_text"]}
    short = [key for key, text in write_ups.items() if len(text.split()) < 8]
    assert len(short) == 0, (
        "The review stores "
        + str(short)
        + " with fewer than eight words. Every reviewing agent's write-up is kept with the "
        "review for the nurse to read."
    )
    assert len(set(write_ups.values())) == len(write_ups), (
        "Two of the review's write-ups are the same text. Each agent writes its own part of "
        "the review."
    )
    assert (at_gate.get("coordinator_request") == saved_run["coordinator_request"]
            and at_gate.get("coordinator_id") == saved_run["opener"]["username"]), (
        "The review records the request "
        + repr(at_gate.get("coordinator_request"))
        + " opened by "
        + repr(at_gate.get("coordinator_id"))
        + " where "
        + saved_run["opener"]["username"]
        + " asked "
        + repr(saved_run["coordinator_request"])
        + "."
    )
    assert at_gate.get("status") == config.REVIEW_STATUS_AWAITING, (
        "The review was stored as "
        + repr(at_gate.get("status"))
        + " at the pause, where it waits as "
        + config.REVIEW_STATUS_AWAITING
        + "."
    )


def test_a_reply_decorated_the_way_models_write_is_read_back_whole():
    from agentic.agents import parse_labelled_response

    labels = ["PRIORITY", "CHECKS", "RATIONALE"]
    decorated = ("Here is the plan you asked for.\n"
                 "**PRIORITY:** The conservative treatment criterion.\n"
                 "## Checks: 1. Confirm the weeks against the letter.\n"
                 "2. Confirm the red flag answer.\n"
                 "- RATIONALE: The questionnaire decides; the documents are evidence.\n"
                 "rationale: The answers are read as the Rules set out.")
    parsed = parse_labelled_response(decorated, labels, "review_planner")
    assert sorted(parsed) == sorted(labels), (
        "Parsing a decorated reply returned the fields "
        + str(sorted(parsed))
        + " where it returns exactly "
        + str(labels)
        + "."
    )
    assert (parsed["PRIORITY"] == "The conservative treatment criterion."
            and parsed["CHECKS"] == ("1. Confirm the weeks against the letter.\n"
                                     "2. Confirm the red flag answer.")
            and "The answers are read as the Rules set out." in parsed["RATIONALE"]
            and "The questionnaire decides" in parsed["RATIONALE"]), (
        "A reply with labels in bold or as headings, a field running over two lines and a "
        "label written twice was read as "
        + str(parsed)
        + ". Decoration around a label is not part of it, a line with no label belongs to the "
        "field above it, and a label written again adds to its field."
    )
    for reply, missing in [("PRIORITY: The criteria.\nCHECKS: The weeks.", "RATIONALE"),
                           ("PRIORITY: The criteria.\nCHECKS:\nRATIONALE: Because.", "CHECKS")]:
        refusal = None
        try:
            parse_labelled_response(reply, labels, "review_planner")
        except ValueError as error:
            refusal = str(error)
        except Exception as error:
            refusal = type(error).__name__ + " instead of a ValueError"
        assert refusal is not None and missing in refusal and "review_planner" in refusal, (
            "A reply that leaves "
            + missing
            + " out or empty gave "
            + str(refusal)
            + ". A reply missing a field is refused with a ValueError naming the agent and the "
            "field, never stored with a gap."
        )


def test_an_approval_writes_the_letter_with_the_tools_details_and_then_a_plain_notice(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    final = saved_run["final_record"]
    assert final["status"] == 200 and len(final["body"]) == 1, (
        "The approved review could not be read back: "
        + str(final["body"])[:300]
    )
    record = final["body"][0]
    request = saved_run["detail"]["request"]
    details = record.get("letter_details") or {}
    expected = {
        config.REQUEST_REFERENCE_DETAIL: saved_run["request_reference"],
        config.MEMBER_NUMBER_DETAIL: request[config.MEMBER_NUMBER_COLUMN],
        config.SERVICE_DETAIL: config.SERVICE_WITH_CODE_FORMAT.format(
            service_name=config.SERVICE_NAMES[request[config.SERVICE_CODE_COLUMN]],
            service_code=request[config.SERVICE_CODE_COLUMN]),
        config.SITE_OF_SERVICE_DETAIL: request[config.SITE_OF_SERVICE_COLUMN],
        config.MEDICAL_POLICY_DETAIL: config.SERVICE_POLICY_DOCUMENTS[
            request[config.SERVICE_CODE_COLUMN]],
    }
    if request[config.SITE_OF_SERVICE_COLUMN] == config.INPATIENT_SITE:
        expected[config.INPATIENT_DAYS_DETAIL] = request[config.REQUESTED_INPATIENT_DAYS_COLUMN]
    assert details == expected, (
        "The provider authorisation letter carries the details "
        + str(details)
        + " where the request gives "
        + str(expected)
        + ". The reference, member number, service and code, site of service, medical policy "
        "and any inpatient days are added from the request itself, never written by the model."
    )
    letter = str(record.get("letter_text") or "")
    notice = str(record.get("notice_text") or "")
    assert len(letter.split()) > 20 and len(notice.split()) > 15 and letter != notice, (
        "The approval stored a letter of "
        + str(len(letter.split()))
        + " words and a notice of "
        + str(len(notice.split()))
        + ". An approval writes a provider authorisation letter and then a member notice, two "
        "different texts."
    )
    written = (letter + "\n" + notice).lower()
    forbidden = [term for term in config.LETTER_FORBIDDEN_TERMS if term in written]
    assert len(forbidden) == 0, (
        "The letter or the notice speaks of "
        + str(forbidden)
        + ". The figures that decide nothing and the language of refusal stay out of what the "
        "office and the member read."
    )
    withheld = [str(request[column_name]) for column_name in config.NOTICE_WITHHELD_COLUMNS
                if request[column_name] != config.NOT_GIVEN_TEXT
                and str(request[column_name]).lower() in notice.lower()]
    assert len(withheld) == 0, (
        "The member notice mentions "
        + str(withheld)
        + ". The notice tells the member, in plain words, that the service is authorised and "
        "where; it carries no clinical detail beyond the service's name."
    )
    assert record.get("referral_summary") is None and record.get("status") == (
            config.REVIEW_STATUS_APPROVED), (
        "The approved review is stored as "
        + repr(record.get("status"))
        + " with a referral summary of "
        + str(record.get("referral_summary"))[:120]
        + ". An approval is recorded as "
        + config.REVIEW_STATUS_APPROVED
        + " and refers nothing to a Physician Reviewer."
    )


def test_the_workflow_has_ten_reachable_nodes_and_sends_each_decision_down_its_own_path(tmp_path):
    from agentic.graph import build_workflow
    from agentic.state import AuthorisationReviewState
    from config import config

    compiled = build_workflow(str(tmp_path / "workflow_check.db"))
    node_names = sorted(str(name) for name in compiled.builder.nodes)
    expected_nodes = sorted(["load_request_context", "plan_review", "assess_criteria",
                             "review_evidence", "weigh_predictions",
                             "compose_review_recommendation", "request_review_decision",
                             "draft_office_letter", "draft_member_notice",
                             "record_review_outcome"])
    assert node_names == expected_nodes, (
        "The workflow declares the nodes "
        + str(node_names)
        + " where the design has "
        + str(expected_nodes)
        + "."
    )
    destinations = {}
    for gate in ["request_review_decision", "draft_office_letter"]:
        branches = compiled.builder.branches.get(gate, {})
        assert len(branches) == 1, (
            "The node "
            + gate
            + " has "
            + str(len(branches))
            + " conditional branches where it has one, choosing the path from the decision."
        )
        branch = list(branches.values())[0]
        decisions = config.DECISIONS
        if gate == "draft_office_letter":
            decisions = [config.DECISION_APPROVE, config.DECISION_REQUEST_INFORMATION]
        for decision in decisions:
            state = {key: None for key in AuthorisationReviewState.__annotations__}
            state["review_decision"] = {"decision": decision, "decided_by": "routing.check",
                                        "decided_by_role": config.ROLE_NURSE,
                                        "decision_reason": "Routing is being checked."}
            routed = branch.path.invoke(state)
            if isinstance(routed, (list, tuple)) and len(routed) == 1:
                routed = routed[0]
            destinations[(gate, decision)] = branch.ends[routed] if branch.ends else routed
    expected_paths = {
        ("request_review_decision", config.DECISION_APPROVE): "draft_office_letter",
        ("request_review_decision", config.DECISION_REQUEST_INFORMATION): "draft_office_letter",
        ("request_review_decision", config.DECISION_REFER): "record_review_outcome",
        ("draft_office_letter", config.DECISION_APPROVE): "draft_member_notice",
        ("draft_office_letter", config.DECISION_REQUEST_INFORMATION): "record_review_outcome",
    }
    assert destinations == expected_paths, (
        "The decisions route to "
        + str(destinations)
        + ". An approval writes the provider authorisation letter and then the member notice; "
        "a request for more information writes the information request letter alone; a "
        "referral writes nothing and goes straight to the record."
    )
    edges = {(str(source), str(target)) for source, target in compiled.builder.edges}
    edges |= {(route[0], str(target)) for route, target in destinations.items()}
    reached = {"__start__"}
    grew = True
    while grew:
        grew = False
        for source, target in edges:
            if source in reached and target not in reached:
                reached.add(target)
                grew = True
    unreachable = sorted(set(node_names) - reached)
    assert len(unreachable) == 0, (
        "These nodes cannot be reached from the start: "
        + str(unreachable)
        + ". A node with no way in never runs, whatever it contains."
    )
    for source, target, reason in [
            ("__start__", "load_request_context",
             "every review starts from the tools' findings, before any agent runs"),
            ("compose_review_recommendation", "request_review_decision",
             "the review is stored before the run waits for a UM Nurse Reviewer"),
            ("draft_member_notice", "record_review_outcome",
             "what was written has to reach the record"),
            ("record_review_outcome", "__end__", "the run ends once the outcome is recorded")]:
        assert (source, target) in edges, (
            "Nothing leads from " + source + " to " + target + ": " + reason + "."
        )


def test_the_run_waits_for_a_nurse_who_did_not_open_it_before_anything_is_written(saved_run):
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    at_gate = saved_run["at_gate"]
    undecided = ["decision", "decided_by", "decided_by_role", "decision_reason", "letter_text",
                 "letter_details", "notice_text", "referral_summary"]
    written = [field for field in undecided if at_gate.get(field) is not None]
    assert len(written) == 0 and at_gate.get("status") == config.REVIEW_STATUS_AWAITING, (
        "At the pause the review already holds "
        + str(written)
        + " with the status "
        + repr(at_gate.get("status"))
        + ". Nothing is decided, written or referred until a UM Nurse Reviewer decides."
    )
    own = saved_run["own_decision"]
    expected_refusal = config.OWN_REVIEW_MESSAGE.format(
        decided_by=saved_run["opener"]["username"],
        request_reference=saved_run["request_reference"])
    assert (own["status"] == 409 and isinstance(own["body"], dict)
            and own["body"].get("detail") == expected_refusal), (
        "The nurse who opened the review, deciding it herself, was answered "
        + str(own["status"])
        + " with "
        + str(own["body"])[:300]
        + ", where the service refuses with 409 and the configuration's words: "
        + repr(expected_refusal)
        + ". The Utilisation Management Policy has another nurse decide."
    )
    assert own["calls_before"] == own["calls_after"] == config.LLM_CALLS_BEFORE_DECISION, (
        "The refused decision moved the call count from "
        + str(own["calls_before"])
        + " to "
        + str(own["calls_after"])
        + ". A decision is checked before the run resumes, so a refused one spends no call."
    )


def test_resuming_finished_the_run_from_its_checkpoint_on_disk_and_closed_it_complete(saved_run):
    import os

    from agentic.graph import build_workflow
    from config import config

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    stored_run = saved_run["run_record"]
    assert stored_run["problem"] is None, stored_run["problem"]
    expected_calls = config.LLM_CALLS_BY_DECISION[config.DECISION_APPROVE]
    assert (stored_run["status"] == config.AGENT_RUN_STATUS_COMPLETE
            and stored_run["llm_call_count"] == expected_calls), (
        "After the approval the run is recorded as "
        + str(stored_run["status"])
        + " with "
        + str(stored_run["llm_call_count"])
        + " calls, where it closes "
        + config.AGENT_RUN_STATUS_COMPLETE
        + " with "
        + str(expected_calls)
        + "."
    )
    assert os.path.isfile(config.CHECKPOINT_DATABASE_FILE), (
        "There is no checkpoint at "
        + config.CHECKPOINT_DATABASE_FILE
        + ". A paused run waits on disk, so a decision taken later, or after the service "
        "restarts, finishes it."
    )
    reopened = build_workflow(config.CHECKPOINT_DATABASE_FILE)
    snapshot = reopened.get_state(
        {"configurable": {"thread_id": saved_run["at_gate"]["thread_id"]}})
    values = snapshot.values
    decision = values.get("review_decision") or {}
    assert (len(snapshot.next) == 0 and decision.get("decision") == config.DECISION_APPROVE
            and decision.get("decided_by") == saved_run["decider"]["username"]
            and values.get("llm_call_count") == expected_calls), (
        "A workflow built afresh on the checkpoint file reads the run as waiting for "
        + str(list(snapshot.next))
        + " with the decision "
        + str(decision)
        + " and "
        + str(values.get("llm_call_count"))
        + " calls. The run was resumed from that file and finished there, with the nurse's "
        "decision kept in its state."
    )
    assert (values.get("review_id") == saved_run["at_gate"]["review_id"]
            and values.get("request_reference") == saved_run["request_reference"]
            and stored_run["thread_id"] == saved_run["at_gate"]["thread_id"]), (
        "The checkpoint's state belongs to "
        + str(values.get("review_id"))
        + " and "
        + str(values.get("request_reference"))
        + ", not to the review that was decided."
    )


def test_the_decision_is_recorded_once_and_every_refusal_comes_before_a_call_is_spent(
        saved_run, service_client):
    from config import config
    from persistence.database import session_factory
    from persistence.models import ReviewDecision

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    closed = saved_run["closed_decision"]
    expected_refusal = config.DECISION_NOT_OPEN_MESSAGE.format(
        decision=config.DECISION_REQUEST_INFORMATION,
        request_reference=saved_run["request_reference"],
        reason=config.SCREENING_CLOSED_REASONS[config.DECISION_APPROVE])
    assert (closed["status"] == 409 and isinstance(closed["body"], dict)
            and closed["body"].get("detail") == expected_refusal
            and closed["calls_before"] == closed["calls_after"]), (
        "Asking for more information on a request whose every criterion is met was answered "
        + str(closed["status"])
        + " with "
        + str(closed["body"])[:300]
        + ", the calls going from "
        + str(closed["calls_before"])
        + " to "
        + str(closed["calls_after"])
        + ". A decision the screening does not leave open is refused with 409 and "
        + repr(expected_refusal)
        + ", before a call is spent."
    )
    for name, meaning in [("short_reason", "a reason of five characters"),
                          ("unknown_decision", "a decision that is none of the three"),
                          ("short_request", "a coordinator's request of two characters")]:
        assert saved_run[name]["status"] == 422, (
            "Sending "
            + meaning
            + " was answered "
            + str(saved_run[name]["status"])
            + " with "
            + str(saved_run[name]["body"])[:200]
            + ". The request's schema refuses it with 422 before anything is looked up."
        )
    second = saved_run["second_review"]
    expected_second = config.REQUEST_ALREADY_REVIEWED_MESSAGE.format(
        request_reference=saved_run["request_reference"])
    assert second["status"] == 409 and second["body"].get("detail") == expected_second, (
        "Opening a second review of "
        + saved_run["request_reference"]
        + " was answered "
        + str(second["status"])
        + " with "
        + str(second["body"])[:200]
        + ". A request in the queue is reviewed once: "
        + repr(expected_second)
    )
    decided = saved_run["decided"]["body"]
    assert (decided.get("decision") == config.DECISION_APPROVE
            and decided.get("decided_by") == saved_run["decider"]["username"]
            and decided.get("decided_by_role") == config.ROLE_NURSE
            and decided.get("decision_reason") == saved_run["decision_reason"]
            and decided.get("status") == config.REVIEW_STATUS_APPROVED), (
        "The approval came back recorded as "
        + str({key: decided.get(key) for key in ["decision", "decided_by", "decided_by_role",
                                                 "decision_reason", "status"]})
        + ", which is not the decision the nurse sent."
    )
    review_id = saved_run["at_gate"]["review_id"]
    again = service_client["client"].post(
        "/reviews/" + review_id + "/decision",
        json={"decision": config.DECISION_APPROVE, "decision_reason": saved_run["decision_reason"]},
        headers=saved_run["decider"]["headers"])
    assert (again.status_code == 409
            and again.json().get("detail") == config.ALREADY_DECIDED_MESSAGE), (
        "Deciding the review a second time was answered "
        + str(again.status_code)
        + " with "
        + again.text[:200]
        + ". A review is decided once: "
        + repr(config.ALREADY_DECIDED_MESSAGE)
    )
    with session_factory() as session:
        stored = session.query(ReviewDecision).filter(ReviewDecision.review_id == review_id).all()
    assert len(stored) == 1 and stored[0].decision == config.DECISION_APPROVE, (
        "The review_decisions table holds "
        + str(len(stored))
        + " decisions for the review where it holds the one decision taken."
    )


def test_the_stored_review_agrees_with_the_tools_that_produced_it(saved_run, saved_models,
                                                                   medical_policies):
    from config import config
    from tools.prediction_tools import estimate_approval_likelihood
    from tools.request_data_tools import fetch_request, load_open_requests
    from tools.screening_tools import screen_request

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    record = saved_run["final_record"]["body"][0]
    detail = saved_run["detail"]
    screening = detail["screening"]
    stay = detail["stay"] or {}
    pairs = {
        "criteria": (record.get("criteria"), screening["criteria"]),
        "screening": (record.get("screening"), screening["screening"]),
        "decisions_open": (record.get("decisions_open"), screening["decisions_open"]),
        "service_code": (record.get("service_code"), screening["service_code"]),
        "policy_document": (record.get("policy_document"), screening["policy_document"]),
        "body_mass_index": (record.get("body_mass_index"), screening["body_mass_index"]),
        "evidence": (record.get("evidence"), detail["evidence_findings"]),
        "disagreements": (record.get("disagreements"), detail["disagreements"]),
        "approval_likelihood": (record.get("approval_likelihood"),
                                detail["likelihood"]["approval_likelihood"]),
        "approval_band": (record.get("approval_band"), detail["likelihood"]["approval_band"]),
        "expected_stay_days": (record.get("expected_stay_days"), stay.get("expected_stay_days")),
        "longer_stay_expected": (record.get("longer_stay_expected"),
                                 stay.get("longer_stay_expected")),
        "stay_text": (record.get("stay_text"), detail["stay_text"]),
    }
    differing = {name: pair for name, pair in pairs.items() if pair[0] != pair[1]}
    assert len(differing) == 0, (
        "The stored review differs from the tools' findings for "
        + saved_run["request_reference"]
        + " in "
        + str({name: (str(pair[0])[:80], str(pair[1])[:80]) for name, pair in
               differing.items()})
        + ". The review records the screening, the evidence, the disagreements, the likelihood "
        "and the stay the tools worked out, never the agents' retelling of them."
    )
    request = fetch_request(load_open_requests(), saved_run["request_reference"])
    own_screening = screen_request(request, medical_policies["policies"][
        request[config.SERVICE_CODE_COLUMN]])
    likelihood = estimate_approval_likelihood(saved_models["approval"],
                                              saved_models["approval_schema"], request,
                                              own_screening)
    assert (likelihood["approval_likelihood"] == record.get("approval_likelihood")
            and own_screening["screening"] == record.get("screening")), (
        "Worked out again from the live files, the saved model and the request's own policy, "
        + saved_run["request_reference"]
        + " screens as "
        + own_screening["screening"]
        + " with a likelihood of "
        + str(likelihood["approval_likelihood"])
        + ", where the review stored "
        + str(record.get("screening"))
        + " and "
        + str(record.get("approval_likelihood"))
        + "."
    )


def test_signing_in_and_out_decides_who_the_service_will_serve(service_client):
    from access.password_security import hash_password
    from config import config
    from persistence.database import session_factory
    from persistence.models import UserAccount
    from persistence.repository import fetch_user_account

    assert service_client["problem"] is None, service_client["problem"]
    client = service_client["client"]
    coordinators = [account for account in config.SEED_USER_ACCOUNTS
                    if account["role"] == config.ROLE_COORDINATOR]
    account = coordinators[1]
    other_account = coordinators[2]
    credentials = {"username": account["username"], "password": account["password"]}
    signed_in = client.post("/auth/signin", json=credentials)
    body = signed_in.json() if signed_in.status_code == 200 else {}
    assert ({"username", "display_name", "role", "session_token"} <= set(body)
            and len(str(body["session_token"]).strip()) > 0), (
        "Signing in as "
        + account["username"]
        + " with the password the configuration seeds returned "
        + str(signed_in.status_code)
        + " with "
        + signed_in.text[:200]
        + ", where a sign-in answers with the user's name, display name, role and a session "
        "token."
    )
    assert (body["username"] == account["username"] and body["role"] == account["role"]
            and body["display_name"] == account["display_name"]), (
        "Signing in as "
        + account["username"]
        + " answered with the name "
        + repr(body["username"])
        + ", the display name "
        + repr(body["display_name"])
        + " and the role "
        + repr(body["role"])
        + ", which are not those of the account the configuration seeds."
    )
    wrong = client.post("/auth/signin", json={"username": account["username"],
                                              "password": "wrong-" + account["password"]})
    stranger = client.post("/auth/signin", json={"username": "no-such-person",
                                                 "password": account["password"]})
    assert (wrong.status_code == 401 and stranger.status_code == 401
            and wrong.json() == stranger.json() == {"detail": config.SIGN_IN_FAILED_MESSAGE}), (
        "A wrong password was answered "
        + str(wrong.status_code)
        + " with "
        + wrong.text[:200]
        + " and an unknown username "
        + str(stranger.status_code)
        + " with "
        + stranger.text[:200]
        + ". Both are refused with 401 and the same words, "
        + repr(config.SIGN_IN_FAILED_MESSAGE)
        + ", so a stranger cannot tell which usernames exist."
    )
    parameters = {"service_code": config.QUEUE_SERVICE_ALL}
    first_headers = {config.SESSION_TOKEN_HEADER: body["session_token"]}
    accepted = client.get("/queue", params=parameters, headers=first_headers)
    assert accepted.status_code == 200, (
        "The token just given to "
        + account["username"]
        + " was answered "
        + str(accepted.status_code)
        + " by the queue. A fresh session token opens the areas its role is granted."
    )
    for meaning, headers in [("with no token", None),
                             ("with a token nobody was given",
                              {config.SESSION_TOKEN_HEADER: "not-a-token-anyone-was-given"})]:
        refused = client.get("/queue", params=parameters, headers=headers)
        assert (refused.status_code == 401
                and refused.json() == {"detail": config.SIGN_IN_REQUIRED_MESSAGE}), (
            "The queue answered a request "
            + meaning
            + " with "
            + str(refused.status_code)
            + " and "
            + refused.text[:200]
            + ". Only a signed-in user is served; anyone else is refused with 401 and "
            + repr(config.SIGN_IN_REQUIRED_MESSAGE)
            + "."
        )
    again = client.post("/auth/signin", json=credentials)
    second_token = again.json().get("session_token") if again.status_code == 200 else None
    second_headers = {config.SESSION_TOKEN_HEADER: str(second_token)}
    replaced = client.get("/queue", params=parameters, headers=first_headers)
    current = client.get("/queue", params=parameters, headers=second_headers)
    assert (again.status_code == 200 and replaced.status_code == 401
            and current.status_code == 200), (
        "After "
        + account["username"]
        + " signed in a second time, answered "
        + str(again.status_code)
        + ", the first token got "
        + str(replaced.status_code)
        + " from the queue and the second "
        + str(current.status_code)
        + ". An account holds one session: signing in somewhere else ends the session before "
        "it."
    )
    signed_out = client.post("/auth/signout", headers=second_headers)
    after = client.get("/queue", params=parameters, headers=second_headers)
    twice = client.post("/auth/signout", headers=second_headers)
    assert (signed_out.status_code == 200
            and signed_out.json() == {"username": account["username"], "signed_out": True}
            and after.status_code == 401 and twice.status_code == 401), (
        "Signing out answered "
        + str(signed_out.status_code)
        + " with "
        + signed_out.text[:200]
        + "; the token then got "
        + str(after.status_code)
        + " from the queue and "
        + str(twice.status_code)
        + " when it signed out again. Signing out answers with the username and signed_out "
        "true, and the token it ends opens nothing afterwards."
    )
    with session_factory() as session:
        stored = fetch_user_account(session, UserAccount.username == account["username"])
        other = fetch_user_account(session, UserAccount.username == other_account["username"])
    missing = sorted({"password_hash", "password_salt"}
                     - (set(stored if isinstance(stored, dict) else {})
                        & set(other if isinstance(other, dict) else {})))
    assert len(missing) == 0, (
        "fetch_user_account read "
        + account["username"]
        + " and "
        + other_account["username"]
        + " back without "
        + str(missing)
        + ", so how their passwords are kept cannot be read."
    )
    assert (stored["password_hash"] != account["password"]
            and stored["password_hash"] == hash_password(account["password"],
                                                         stored["password_salt"])), (
        "The password stored for "
        + account["username"]
        + " is not the salted hash of the password. A password kept as written is read by "
        "anyone who can open the database."
    )
    assert (stored["password_salt"] != other["password_salt"]
            and stored["password_hash"] != other["password_hash"]), (
        account["username"]
        + " and "
        + other_account["username"]
        + " share a password and are stored with the same salt or the same hash, so one "
        "cracked hash opens both accounts."
    )


def test_every_role_reaches_exactly_the_areas_it_is_granted(service_client):
    from config import config

    assert service_client["problem"] is None, service_client["problem"]
    client = service_client["client"]
    signed_in = {}
    for role_name, position in [(config.ROLE_NURSE, 1), (config.ROLE_COORDINATOR, 3),
                                (config.ROLE_REPRESENTATIVE, 1)]:
        accounts = [account for account in config.SEED_USER_ACCOUNTS
                    if account["role"] == role_name]
        account = accounts[position]
        reply = client.post("/auth/signin", json={"username": account["username"],
                                                  "password": account["password"]})
        body = reply.json() if reply.status_code == 200 else {}
        assert {"session_token", "pages", "areas"} <= set(body), (
            "Signing in as "
            + account["username"]
            + " returned "
            + str(reply.status_code)
            + " with "
            + reply.text[:200]
            + ", where a sign-in answers with a session token and the pages and areas of the "
            "user's role."
        )
        assert (sorted(body["pages"]) == sorted(config.ROLE_PAGE_ACCESS[role_name])
                and sorted(body["areas"]) == sorted(config.ROLE_AREA_ACCESS[role_name])), (
            "Signing in as a "
            + role_name
            + " answered with the pages "
            + str(body["pages"])
            + " and the areas "
            + str(body["areas"])
            + ", where the configuration grants that role the pages "
            + str(config.ROLE_PAGE_ACCESS[role_name])
            + " and the areas "
            + str(config.ROLE_AREA_ACCESS[role_name])
            + "."
        )
        signed_in[role_name] = {config.SESSION_TOKEN_HEADER: body["session_token"]}
    unknown_review = config.REVIEW_ID_PREFIX + "DOES-NOT-EXIST"
    probes = [
        (config.AREA_INTAKE, "GET", "/queue", {"service_code": config.QUEUE_SERVICE_ALL}, None,
         200),
        (config.AREA_REVIEW, "POST", "/reviews", None,
         {"request_reference": "PA-000000",
          "coordinator_request": "Are the criteria met on the questionnaire?"}, 404),
        (config.AREA_DECISION, "POST", "/reviews/" + unknown_review + "/decision", None,
         {"decision": config.DECISION_REFER,
          "decision_reason": "The documents raise a concern the criteria do not cover."}, 404),
        (config.AREA_AUDIT, "GET", "/reviews",
         {"status_value": [config.REVIEW_STATUS_AWAITING]}, None, 200),
        (config.AREA_AUDIT, "GET", "/reviews/" + unknown_review + "/calls", None, None, 404),
        (config.AREA_AUDIT, "GET", "/audit/chat-turns", {"turn_limit": 1}, None, 200),
        (config.AREA_CHAT, "GET", "/chat/turns", {"turn_limit": 1}, None, 200),
    ]
    for role_name, role_headers in signed_in.items():
        for area_name, method, path, parameters, payload, status_when_granted in probes:
            reply = client.request(method, path, params=parameters, json=payload,
                                   headers=role_headers)
            granted = area_name in config.ROLE_AREA_ACCESS[role_name]
            if granted:
                assert reply.status_code == status_when_granted, (
                    "A signed-in "
                    + role_name
                    + " calling "
                    + method
                    + " "
                    + path
                    + " got "
                    + str(reply.status_code)
                    + " with "
                    + reply.text[:200]
                    + " where it gets "
                    + str(status_when_granted)
                    + ". The "
                    + area_name
                    + " area is granted to that role, so the guard lets it through and the "
                    "endpoint answers: a request or a review that does not exist is answered "
                    "404, before any language model call."
                )
            else:
                expected_refusal = config.AREA_REFUSED_MESSAGE.format(role=role_name,
                                                                      area=area_name)
                assert (reply.status_code == 403
                        and reply.json().get("detail") == expected_refusal), (
                    "A signed-in "
                    + role_name
                    + " calling "
                    + method
                    + " "
                    + path
                    + " got "
                    + str(reply.status_code)
                    + " with "
                    + reply.text[:200]
                    + ". The "
                    + area_name
                    + " area is not granted to that role, so the guard refuses it with 403 and "
                    "the configuration's words, "
                    + repr(expected_refusal)
                    + ", whether or not the thing asked for exists."
                )


def test_the_queue_puts_urgent_requests_first_and_each_row_agrees_with_its_detail(
        service_client, staff, live_files, saved_models, medical_policies):
    import re

    from config import config
    from tools.prediction_tools import estimate_approval_likelihood
    from tools.request_data_tools import fetch_request, rank_review_queue
    from tools.screening_tools import screen_request

    assert staff["problem"] is None, staff["problem"]
    assert live_files["problem"] is None, live_files["problem"]
    assert saved_models["problem"] is None, saved_models["problem"]
    assert medical_policies["problem"] is None, medical_policies["problem"]
    standard = config.URGENCY_MAPPING["standard"]
    planted = live_files["requests"].head(5).copy()
    planted[config.REQUEST_REFERENCE_COLUMN] = ["PA-500004", "PA-500002", "PA-500001",
                                                "PA-500003", "PA-500000"]
    planted[config.URGENCY_COLUMN] = [standard, config.URGENT, standard, config.URGENT, standard]
    ranked = list(rank_review_queue(planted))
    assert ranked == ["PA-500002", "PA-500003", "PA-500000", "PA-500001", "PA-500004"], (
        "rank_review_queue put planted requests, standard PA-500004, urgent PA-500002, standard "
        "PA-500001, urgent PA-500003 and standard PA-500000, in the order "
        + str(ranked)
        + ". Urgent requests come first, and each group runs by request reference."
    )
    client = service_client["client"]
    headers = staff["coordinator"]["headers"]
    reply = client.get("/queue", params={"service_code": config.QUEUE_SERVICE_ALL},
                       headers=headers)
    assert reply.status_code == 200 and isinstance(reply.json(), list), (
        "The queue returned "
        + str(reply.status_code)
        + " with "
        + reply.text[:200]
        + " to a signed-in Intake Coordinator."
    )
    everything = reply.json()
    missing = sorted({"queue_position", "request_reference", "service_code", "service_name",
                      "urgency", "site_of_service", "document_count", "criteria_met_count",
                      "criteria_not_met_count", "criteria_not_documented_count", "screening",
                      "decisions_open", "approval_likelihood", "approval_band",
                      "disagreement_count"} - set(everything[0] if everything else {}))
    assert len(missing) == 0, (
        "A queue row carries no "
        + str(missing)
        + ", so the queue cannot be ordered, filtered or read."
    )
    references = [row["request_reference"] for row in everything]
    supplied = set()
    for written_reference in live_files["raw_requests"][config.REQUEST_REFERENCE_COLUMN].dropna():
        supplied.add("PA-" + re.search(r"[0-9]{6}", written_reference).group())
    assert sorted(references) == sorted(supplied), (
        "The queue holds "
        + str(len(references))
        + " rows for "
        + str(len(set(references)))
        + " requests, where the open requests file holds "
        + str(len(supplied))
        + " requests, some of them sent more than once. Every open request is in the queue "
        "exactly once."
    )
    open_requests = live_files["requests"]
    urgent_requests = set(open_requests.loc[open_requests[config.URGENCY_COLUMN] == config.URGENT,
                                            config.REQUEST_REFERENCE_COLUMN])
    keys = [(row["urgency"] != config.URGENT, row["request_reference"]) for row in everything]
    out_of_order = [(references[position], references[position + 1])
                    for position in range(len(keys) - 1) if keys[position] > keys[position + 1]]
    shown_urgent = {row["request_reference"] for row in everything
                    if row["urgency"] == config.URGENT}
    assert (len(out_of_order) == 0 and len(urgent_requests) > 0
            and shown_urgent == urgent_requests), (
        "The queue shows "
        + str(sorted(shown_urgent))
        + " as urgent, where the open requests hold "
        + str(sorted(urgent_requests))
        + ", and is out of order at "
        + str(out_of_order[:3])
        + ". Urgent requests come first and then the rest, each group by request reference, "
        "so the nurses work the queue from the top."
    )
    assert [row["queue_position"] for row in everything] == list(range(1, len(everything) + 1)), (
        "The queue positions run "
        + str([row["queue_position"] for row in everything][:10])
        + " ... where they count from 1 down the queue."
    )
    notes = live_files["notes"]
    checked_against_tools = [references[0], references[len(references) // 2], references[-1]]
    differing = {}
    for row in everything:
        detail_reply = client.get("/queue/" + row["request_reference"], headers=headers)
        detail = detail_reply.json() if detail_reply.status_code == 200 else {}
        described = detail.get("request", {})
        shown = detail.get("screening", {})
        shown_likelihood = detail.get("likelihood", {})
        expected = {
            "queue_position": detail.get("queue_position"),
            "service_code": shown.get("service_code"),
            "service_name": config.SERVICE_NAMES.get(shown.get("service_code")),
            "urgency": described.get(config.URGENCY_COLUMN),
            "site_of_service": described.get(config.SITE_OF_SERVICE_COLUMN),
            "document_count": int((notes[config.REQUEST_REFERENCE_COLUMN]
                                   == row["request_reference"]).sum()),
            "criteria_met_count": shown.get(config.CRITERIA_MET_COUNT_COLUMN),
            "criteria_not_met_count": shown.get(config.CRITERIA_NOT_MET_COUNT_COLUMN),
            "criteria_not_documented_count": shown.get(config.CRITERIA_NOT_DOCUMENTED_COUNT_COLUMN),
            "screening": shown.get("screening"),
            "decisions_open": shown.get("decisions_open"),
            "approval_likelihood": shown_likelihood.get("approval_likelihood"),
            "approval_band": shown_likelihood.get("approval_band"),
            "disagreement_count": len(detail.get("disagreements", [])),
        }
        for key, value in expected.items():
            if row[key] != value:
                differing[row["request_reference"]] = (key + " is " + str(row[key])[:60]
                                                       + " where its detail gives "
                                                       + str(value)[:60])
        if row["request_reference"] in checked_against_tools:
            request = fetch_request(open_requests, row["request_reference"])
            screening = screen_request(request, medical_policies["policies"][
                request[config.SERVICE_CODE_COLUMN]])
            likelihood = estimate_approval_likelihood(saved_models["approval"],
                                                      saved_models["approval_schema"], request,
                                                      screening)
            for key in ["service_code", "criteria", "screening", "decisions_open"]:
                if shown.get(key) != screening[key]:
                    differing[row["request_reference"]] = ("the detail's " + key
                                                           + " is not the tools' own")
            if shown_likelihood != likelihood:
                differing[row["request_reference"]] = ("the detail's likelihood is not the "
                                                       "saved approval model's")
    assert len(differing) == 0, (
        str(len(differing))
        + " rows of the queue differ from their detail or from the tools, for example "
        + str(dict(list(differing.items())[:3]))
        + ". Each row shows what its detail shows: its request's own screening under its "
        "service's policy, the likelihood the saved approval model gives it, the documents "
        "that arrived with it and the disagreements found in them."
    )
    for service_code in config.QUEUE_SERVICE_OPTIONS[1:]:
        filtered_reply = client.get("/queue", params={"service_code": service_code},
                                    headers=headers)
        filtered = filtered_reply.json() if filtered_reply.status_code == 200 else []
        assert len(filtered) > 0 and filtered == [row for row in everything
                                                  if row["service_code"] == service_code], (
            "Filtering the queue to "
            + service_code
            + " did not return exactly the "
            + service_code
            + " requests of the full queue, in the same order and with the same positions."
        )
    for meaning, parameters in [("a service Brightwater Health Plan does not screen",
                                 {"service_code": "XYZ-ABC"}), ("no service at all", None)]:
        refused = client.get("/queue", params=parameters, headers=headers)
        assert refused.status_code == 422, (
            "Asking for the queue with "
            + meaning
            + " returned "
            + str(refused.status_code)
            + " rather than 422. The filter takes a service the configuration names, or all "
            "of them, and nothing else."
        )
    unknown = client.get("/queue/PA-000000", headers=headers)
    expected_unknown = config.UNKNOWN_REQUEST_MESSAGE.format(request_reference="PA-000000")
    assert unknown.status_code == 404 and unknown.json().get("detail") == expected_unknown, (
        "The detail of PA-000000, which is not an open request, returned "
        + str(unknown.status_code)
        + " with "
        + unknown.text[:200]
        + " where it is 404 with "
        + repr(expected_unknown)
        + "."
    )


def test_a_policy_question_is_answered_from_the_documents_and_remembered_by_the_asker_alone(
        chat_replies, knowledge_collection, tmp_path):
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from chat.conversation_memory import recall_conversation
    from config import config
    from knowledge.vector_index import search_documents
    from persistence.database import session_factory
    from persistence.models import Base
    from persistence.repository import insert_chat_turn

    assert chat_replies["problem"] is None, chat_replies["problem"]
    assert knowledge_collection["problem"] is None, knowledge_collection["problem"]
    for name, meaning in [("policy", "Asking the authorisation assistant what the knee "
                                     "replacement policy asks for"),
                          ("turns", "Reading back the Intake Coordinator's own chat turns")]:
        assert chat_replies[name]["status"] == 200, (
            meaning
            + " returned "
            + str(chat_replies[name]["status"])
            + " with "
            + str(chat_replies[name]["body"])[:300]
            + "."
        )
    reply = chat_replies["policy"]["body"]
    missing = sorted({"question_type", "request_reference", "answer", "source_documents",
                      "was_refused"} - set(reply))
    assert len(missing) == 0, (
        "The assistant's reply carries no "
        + str(missing)
        + ", so what it answered and where from cannot be read."
    )
    assert (reply["was_refused"] is False and reply["question_type"] in config.CHAT_ANSWERED_TYPES
            and reply["request_reference"] is None), (
        "Asking what the knee replacement policy asks for was answered as "
        + str(reply["question_type"])
        + " about the request "
        + str(reply["request_reference"])
        + (" and refused" if reply["was_refused"] else "")
        + ". The policy answers it, so the question is answered from the documents, names no "
        "request and is not refused."
    )
    folder = {name for name in os.listdir(config.DOCS_DIRECTORY) if name.lower().endswith(".pdf")}
    cited = reply["source_documents"]
    searched = search_documents(knowledge_collection["collection"],
                                [chat_replies["policy_question"]])
    grounding = (searched[0][0].get("document_name")
                 if len(searched) > 0 and len(searched[0]) > 0 else None)
    assert len(cited) > 0 and set(cited) <= folder and grounding in cited, (
        "The answer cites "
        + str(cited)
        + ". An answer names the documents it came from, each of them in the document folder, "
        "and among them the one holding the passage search_documents finds closest to the "
        "question, "
        + repr(grounding)
        + "; an answer that cannot is an answer from general knowledge."
    )
    assert not set(cited) & set(config.CHAT_EXCLUDED_DOCUMENTS), (
        "The answer cites "
        + str(sorted(set(cited) & set(config.CHAT_EXCLUDED_DOCUMENTS)))
        + ", which the assistant never quotes: it records past reviews of named members, not "
        "what the policies say."
    )
    assert len(reply["answer"].strip()) > 0 and reply["answer"] != config.CHAT_REFUSAL_MESSAGE, (
        "The answer given was "
        + repr(reply["answer"][:120])
        + ", which answers nothing."
    )
    turns = chat_replies["turns"]["body"]
    missing = sorted({"turn_id", "username", "user_role", "question_text", "question_type",
                      "request_reference", "answer_text", "source_documents",
                      "closest_distance", "was_refused"}
                     - set(turns[0] if len(turns) > 0 else {}))
    assert len(turns) > 0 and len(missing) == 0, (
        "The Intake Coordinator's chat turns read back as "
        + str(len(turns))
        + " turns"
        + ("" if len(turns) == 0 else ", the first without " + str(missing))
        + ", where each turn read back carries its identifier, who asked and in which role, "
        "the question, its type, its request, the answer, the documents it cites, its closest "
        "distance and whether it was refused."
    )
    asked = [turn for turn in turns if turn["question_text"] == chat_replies["policy_question"]
             and turn["turn_id"] > chat_replies["latest_turn_before"]]
    assert len(asked) > 0, (
        "The Intake Coordinator's latest turns read back as "
        + str([turn["question_text"] for turn in turns])
        + ", which do not include the question just answered, so the audit trail and the chat "
        "page lose it."
    )
    latest = asked[0]
    assert (latest["question_type"] == reply["question_type"] and latest["was_refused"] is False
            and latest["answer_text"] == reply["answer"] and latest["request_reference"] is None
            and latest["username"] == chat_replies["asker"]
            and latest["user_role"] == config.ROLE_COORDINATOR), (
        "The stored turn is "
        + str({key: latest[key] for key in ["username", "user_role", "question_type",
                                            "request_reference", "was_refused"]})
        + ", which is not who asked or how the question was just answered."
    )
    assert latest["closest_distance"] <= config.CHAT_MAX_RELEVANCE_DISTANCE, (
        "An answered question is stored with its closest passage "
        + str(latest["closest_distance"])
        + " away, beyond the "
        + str(config.CHAT_MAX_RELEVANCE_DISTANCE)
        + " within which an answer counts as found in the documents."
    )
    assert all(name in latest["source_documents"] for name in cited), (
        "The stored turn cites "
        + repr(latest["source_documents"][:300])
        + " where the answer cited "
        + str(cited)
        + ". The audit trail shows where each answer came from."
    )
    follow_up = "And how many weeks of treatment does it ask for?"
    with session_factory() as session:
        remembered = recall_conversation(session, chat_replies["asker"], follow_up)
        someone_else = recall_conversation(session, chat_replies["someone_else"], follow_up)
    missing = sorted({"history_text", "search_text"}
                     - set(remembered if isinstance(remembered, dict) else {}))
    assert len(missing) == 0, (
        "recall_conversation returned no "
        + str(missing)
        + ", so what the next prompt is told and what is searched for it cannot be read."
    )
    assert (chat_replies["policy_question"] in remembered["history_text"]
            and reply["answer"] in remembered["history_text"]), (
        "The conversation recalled for the Intake Coordinator's next question does not hold "
        "the question just asked and its answer, so a follow-up such as "
        + repr(follow_up)
        + " would be read with no idea what it follows."
    )
    assert (follow_up in remembered["search_text"]
            and chat_replies["policy_question"] in remembered["search_text"]), (
        "The text searched for the follow-up is "
        + repr(remembered["search_text"][:200])
        + ". It carries the new question and the question asked just before it."
    )
    assert (chat_replies["policy_question"] not in someone_else["history_text"]
            and chat_replies["policy_question"] not in someone_else["search_text"]), (
        "The conversation recalled for a Provider Services Representative carries the Intake "
        "Coordinator's question "
        + repr(chat_replies["policy_question"])
        + ". Each user's memory is their own last exchanges."
    )
    planted_turns = [
        (config.CHAT_TYPE_MEDICAL_POLICY, "What does the cervical spine policy ask for first?",
         "The weeks of conservative treatment that policy states, unless a red flag is reported.",
         None),
        (config.CHAT_TYPE_REQUEST_STATUS, "What is the status of PA-500001?",
         "REV-PLANTED00001, request PA-500001, opened by carlos: Approved. leena, UM Nurse "
         "Reviewer, decided APPROVE.", "PA-500001"),
        (config.CHAT_TYPE_REVIEW_RULES, "Who decides a review?",
         "A UM Nurse Reviewer who did not open the review decides it.", None),
        (config.CHAT_TYPE_OUTCOME_PREDICTION, "How likely is PA-500001 to be approved?",
         "Approval likelihood 0.9312, HIGH.", "PA-500001"),
    ]
    planted_engine = create_engine("sqlite:///" + str(tmp_path / "planted_chat.db"))
    Base.metadata.create_all(planted_engine)
    with sessionmaker(bind=planted_engine)() as session:
        for question_type, question_text, answer_text, request_reference in planted_turns:
            insert_chat_turn(session, {
                "username": chat_replies["asker"], "user_role": config.ROLE_COORDINATOR,
                "question_text": question_text, "question_type": question_type,
                "request_reference": request_reference, "answer_text": answer_text,
                "source_documents": "", "closest_distance": 0.5, "was_refused": False})
        recalled = recall_conversation(session, chat_replies["asker"], "And who opened it?")
    planted_engine.dispose()
    history = recalled["history_text"]
    kept = planted_turns[-config.CHAT_HISTORY_TURN_LIMIT:]
    dropped = planted_turns[:-config.CHAT_HISTORY_TURN_LIMIT]
    positions = [history.find(turn[1]) for turn in kept]
    assert (min(positions) >= 0 and positions == sorted(positions)
            and all(turn[1] not in history for turn in dropped)), (
        "After four planted exchanges, the conversation recalled is "
        + repr(history[:500])
        + ". It holds the last "
        + str(config.CHAT_HISTORY_TURN_LIMIT)
        + " exchanges, oldest first, and nothing before them."
    )
    carried = [fact for fact in ["REV-PLANTED00001", "leena", "0.9312"] if fact in history]
    record_turns = [turn for turn in kept if turn[0] in config.CHAT_RECORD_TYPES]
    assert (len(carried) == 0
            and history.count(config.CHAT_RECORD_ANSWER_IN_HISTORY) == len(record_turns)
            and all(turn[2] in history for turn in kept if turn not in record_turns)), (
        "After an Intake Coordinator was told a request's status and its likelihood, the "
        "conversation recalled for the next question carries "
        + str(carried)
        + " and "
        + str(history.count(config.CHAT_RECORD_ANSWER_IN_HISTORY))
        + " times "
        + repr(config.CHAT_RECORD_ANSWER_IN_HISTORY)
        + ". The recalled conversation goes into the next prompt, and nothing from the review "
        "records is ever put in front of the language model: an answer from the records is "
        "replaced by those words, while an answer from the documents is replayed as given."
    )


def test_a_representative_hears_a_request_only_with_its_member_number_and_never_a_prediction(
        saved_run, staff):
    from chat.request_status_answer import answer_request_status
    from config import config
    from persistence.database import session_factory
    from tools.request_data_tools import load_open_requests

    assert saved_run["problem"] is None, saved_run["problem"]
    assert saved_run["decision_problem"] is None, saved_run["decision_problem"]
    assert saved_run["heard_at_gate"]["problem"] is None, saved_run["heard_at_gate"]["problem"]
    assert saved_run["heard_after"]["problem"] is None, saved_run["heard_after"]["problem"]
    reference = saved_run["request_reference"]
    at_gate = saved_run["at_gate"]
    service = config.SERVICE_WITH_CODE_FORMAT.format(
        service_name=config.SERVICE_NAMES[at_gate["service_code"]],
        service_code=at_gate["service_code"])
    unconfirmed = config.CHAT_NO_CONFIRMATION_TEMPLATE.format(request_reference=reference)
    heard = [
        ("while the review waited, giving the request's member number",
         saved_run["heard_at_gate"]["with_member_number"],
         config.CHAT_REQUEST_CONFIRMED_TEMPLATE.format(
             request_reference=reference, service=service,
             status=config.REVIEW_STATUS_LABELS[config.REVIEW_STATUS_AWAITING].lower())),
        ("after the approval, giving the request's member number",
         saved_run["heard_after"]["with_member_number"],
         config.CHAT_REQUEST_CONFIRMED_TEMPLATE.format(
             request_reference=reference, service=service,
             status=config.REVIEW_STATUS_LABELS[config.REVIEW_STATUS_APPROVED].lower())),
        ("while the review waited, giving another request's member number",
         saved_run["heard_at_gate"]["with_another_member_number"], unconfirmed),
        ("after the approval, giving another request's member number",
         saved_run["heard_after"]["with_another_member_number"], unconfirmed),
        ("while the review waited, giving no member number",
         saved_run["heard_at_gate"]["without_member_number"], unconfirmed),
        ("while the review waited, asking whether it will be approved",
         saved_run["heard_at_gate"]["prediction"], config.CLINICAL_DETERMINATION_LINE),
        ("after the approval, asking whether it will be approved",
         saved_run["heard_after"]["prediction"], config.CLINICAL_DETERMINATION_LINE),
    ]
    for moment, answer, expected in heard:
        assert answer == expected, (
            "A Provider Services Representative asking about "
            + reference
            + " "
            + moment
            + " was told "
            + repr(str(answer)[:300])
            + " where they hear exactly "
            + repr(expected)
            + ". A representative hears the service and the status of a request only when the "
            "question gives its reference and the member number on it, never a prediction, and "
            "otherwise the configuration's words, the same whether the request was reviewed or "
            "not."
        )
    review_line = config.CHAT_REVIEW_TEMPLATE.format(
        review_id=at_gate["review_id"], request_reference=reference, service=service,
        policy_document=at_gate["policy_document"], coordinator_id=at_gate["coordinator_id"],
        status=config.REVIEW_STATUS_LABELS[config.REVIEW_STATUS_APPROVED])
    figures_line = config.CHAT_FIGURES_TEMPLATE.format(
        approval_likelihood=format(at_gate["approval_likelihood"],
                                   "." + str(config.LIKELIHOOD_DECIMALS) + "f"),
        approval_band=at_gate["approval_band"], expected_stay=at_gate["stay_text"])
    decided_line = config.CHAT_DECIDED_TEMPLATE.format(
        decided_by=saved_run["decider"]["username"], decided_by_role=config.ROLE_NURSE,
        decision=config.DECISION_APPROVE, decision_reason=saved_run["decision_reason"])
    staff_lines = str(saved_run["heard_after"]["staff"]).split("\n")
    assert (staff_lines[0] == review_line and figures_line in staff_lines
            and decided_line in staff_lines), (
        "An Intake Coordinator asking about "
        + reference
        + " after the approval was told "
        + repr(str(saved_run["heard_after"]["staff"])[:600])
        + ". The utilisation management team hears, in the configuration's words, the review "
        + repr(review_line[:200])
        + " first, the figures "
        + repr(figures_line[:200])
        + " and the decision "
        + repr(decided_line[:200])
        + "."
    )
    open_requests = load_open_requests()
    representative = staff["representative"]
    coordinator = staff["coordinator"]
    with session_factory() as session:
        direct = [
            ("a representative naming no request",
             answer_request_status(session, representative, open_requests,
                                   config.CHAT_TYPE_REQUEST_STATUS, None,
                                   saved_run["member_number"]),
             config.CHAT_REQUEST_NOT_NAMED_MESSAGE),
            ("a representative naming PA-999999, which is not an open request",
             answer_request_status(session, representative, open_requests,
                                   config.CHAT_TYPE_REQUEST_STATUS, "PA-999999",
                                   saved_run["member_number"]),
             config.CHAT_NO_CONFIRMATION_TEMPLATE.format(request_reference="PA-999999")),
            ("an Intake Coordinator naming no request",
             answer_request_status(session, coordinator, open_requests,
                                   config.CHAT_TYPE_REQUEST_STATUS, None, None),
             config.CHAT_REVIEW_NOT_NAMED_MESSAGE),
            ("an Intake Coordinator naming PA-999999, which nobody has reviewed",
             answer_request_status(session, coordinator, open_requests,
                                   config.CHAT_TYPE_OUTCOME_PREDICTION, "PA-999999", None),
             config.CHAT_NO_REVIEW_TEMPLATE.format(request_reference="PA-999999")),
        ]
    for meaning, answer, expected in direct:
        assert answer == expected, (
            "answer_request_status told "
            + meaning
            + " "
            + repr(str(answer)[:300])
            + " where it answers exactly "
            + repr(expected)
            + "."
        )
    refusal = None
    try:
        with session_factory() as session:
            answer_request_status(session, coordinator, open_requests,
                                  config.CHAT_TYPE_MEDICAL_POLICY, reference, None)
    except ValueError as error:
        refusal = str(error)
    except Exception as error:
        refusal = type(error).__name__ + " instead of a ValueError"
    assert refusal is not None and config.CHAT_TYPE_MEDICAL_POLICY in refusal, (
        "answer_request_status, asked to answer a "
        + config.CHAT_TYPE_MEDICAL_POLICY
        + " question from the review records, gave "
        + str(refusal)
        + ". Only a request's status or a prediction is answered from the records; any other "
        "type is refused with a ValueError naming it."
    )
