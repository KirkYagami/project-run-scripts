from config import config as c


def fake(prompt_text, agent_name):
    import json

    facts = (
        json.loads(prompt_text.split("ESTABLISHED FACTS:\n")[-1])
        if agent_name != c.AGENT_NAME_AUTHORISATION_ASSISTANT
        else json.loads(prompt_text[prompt_text.index('{"question":') :])
    )
    outputs = {
        c.AGENT_NAME_PLANNER: "PRIORITY: Review the supplied questionnaire under its own medical policy.\nCHECKS: Confirm the documented answers and evidence without replacing any answer.\nRATIONALE: Every result is established by deterministic tools before independent review.",
        c.AGENT_NAME_CRITERIA: "CRITERIA MET: Use the supplied criterion results exactly as established.\nCRITERIA NOT MET: Use only the established failed criteria in the screening.\nNOT DOCUMENTED: Ask for the blank answers required by the policy.\nCRITERIA SUMMARY: No questionnaire answer is filled from a document.",
        c.AGENT_NAME_EVIDENCE: "EVIDENCE FOUND: Read each submitted sentence and its linked criteria in order.\nDISAGREEMENTS: Flag only the supplied disagreements for the nurse to review.\nCHECKS TO MAKE: Use the supplied evidence guides and checks.\nEVIDENCE SUMMARY: Documents do not replace or fill questionnaire answers.",
        c.AGENT_NAME_PREDICTIONS: "LIKELIHOOD: Interpret the supplied likelihood as a historical estimate only.\nEXPECTED STAY: Use the supplied stay description without inventing any figure.\nPREDICTION SUMMARY: Neither figure is a reason for the decision on this request.",
    }
    if agent_name == c.AGENT_NAME_WRITER:
        outputs[agent_name] = (
            "RECOMMENDATION: Review the established screening and evidence before recording an independent nurse decision.\nRECOMMENDED DECISION: "
            + facts["screening"]["screening"]
        )
    if agent_name == c.AGENT_NAME_LETTER:
        details = facts["details"]
        ref = details[c.REQUEST_REFERENCE_DETAIL]
        service = details[c.SERVICE_DETAIL]
        outputs[agent_name] = (
            f"SUBJECT: {ref} {service}\nLETTER: The clinical review team has recorded the supplied decision for this request. Please read the following details and retain this correspondence for your records.\n"
            + "\n".join(
                k + ": " + ("; ".join(v) if isinstance(v, list) else str(v))
                for k, v in details.items()
            )
            + "\n"
            + c.LETTER_SIGN_OFF
        )
    if agent_name == c.AGENT_NAME_NOTICE:
        outputs[agent_name] = (
            f"HEADLINE: Your {facts['service']} is authorised\nNOTICE: Your {facts['service']} is authorised at {facts['place']}. Please contact your requesting office to arrange the service and discuss the next steps for your appointment.\n{c.LETTER_SIGN_OFF}"
        )
    if agent_name == c.AGENT_NAME_AUTHORISATION_ASSISTANT:
        outputs[agent_name] = (
            "QUESTION TYPE: MEDICAL POLICY\nREQUEST: none\nANSWER: "
            + " ".join(
                x["criterion_sentence"]
                for x in facts["policies"]["ORT-TKR"]["criteria"]
            )
        )
    text = outputs[agent_name]
    return dict(
        response_text=text,
        call_record=dict(
            agent_name=agent_name,
            model_name="offline-test-double",
            prompt_characters=len(prompt_text),
            response_characters=len(text),
            latency_milliseconds=0,
        ),
    )
