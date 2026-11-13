from config import config as c
from knowledge.vector_index import find_section_passage
def read_documentation_to_send(collection,service_code):
    if service_code not in c.SERVICE_POLICY_DOCUMENTS:raise ValueError(c.NO_POLICY_CONFIGURED_MESSAGE.format(service_code=service_code))
    return find_section_passage(collection,c.DOCUMENTATION_QUESTION,c.SERVICE_POLICY_DOCUMENTS[service_code],c.DOCUMENTATION_SECTION_HEADING)
def read_reviewer_checks(collection,evidence_type):
    if evidence_type not in c.EVIDENCE_GUIDE_DOCUMENTS:raise ValueError(c.NO_EVIDENCE_GUIDE_MESSAGE.format(evidence_type=evidence_type))
    return find_section_passage(collection,c.REVIEWER_CHECKS_QUESTION,c.EVIDENCE_GUIDE_DOCUMENTS[evidence_type],c.REVIEWER_CHECKS_SECTION_HEADING)
def read_office_guidance(collection,evidence_type):
    if evidence_type not in c.EVIDENCE_GUIDE_DOCUMENTS:raise ValueError(c.NO_EVIDENCE_GUIDE_MESSAGE.format(evidence_type=evidence_type))
    return find_section_passage(collection,c.OFFICE_MESSAGE_QUESTION,c.EVIDENCE_GUIDE_DOCUMENTS[evidence_type],c.OFFICE_MESSAGE_SECTION_HEADING)
