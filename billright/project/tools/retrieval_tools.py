"""Reads the advice a resolution guide gives the customer."""
from config import config
from knowledge.vector_index import search_document


def read_customer_steps(collection, dispute_category):
    """Give the redress letter the steps the customer should take, from the category's own guide."""
    if dispute_category not in config.GUIDE_DOCUMENT_BY_CATEGORY:
        raise ValueError(f"'{dispute_category}' is not one of the dispute categories")
    return search_document(collection, config.CUSTOMER_STEPS_QUESTION,
                           config.GUIDE_DOCUMENT_BY_CATEGORY[dispute_category],
                           config.CUSTOMER_STEPS_RESULT_COUNT)
