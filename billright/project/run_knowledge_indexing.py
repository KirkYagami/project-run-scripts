"""Builds the knowledge base and reads it back, to prove every price can be read."""
from config import config
from knowledge.chunk_splitting import build_chunk_records, split_documents_into_sections
from knowledge.pdf_extraction import extract_text_from_directory
from knowledge.tariff_reading import read_standard_payments, read_tariff_schedule
from knowledge.vector_index import build_vector_index, open_vector_index


def _describe_window(window):
    standing = f"standing charge {window['standing_charge_pence']}p per day"
    if "unit_rate_pence" in window:
        return f"{window['unit_rate_pence']}p per kWh, {standing}"
    return (f"day {window['day_unit_rate_pence']}p and night {window['night_unit_rate_pence']}p "
            f"per kWh, {standing}")


def main():
    """Build the store from the documents, then read every schedule and payment back."""
    print("building the billing knowledge index")
    documents = extract_text_from_directory(config.DOCS_DIRECTORY)
    sections = split_documents_into_sections(documents)
    chunks = build_chunk_records(sections, config.CHUNK_SIZE_CHARACTERS,
                                 config.CHUNK_OVERLAP_CHARACTERS)
    stored = build_vector_index(chunks, config.VECTOR_STORE_DIRECTORY,
                                config.VECTOR_COLLECTION_NAME)
    print(f"    documents read: {len(documents)}")
    print(f"    sections found: {len(sections)}")
    print(f"    chunks stored:   {stored}")
    print(f"    store location: {config.VECTOR_STORE_DIRECTORY}")

    collection = open_vector_index(config.VECTOR_STORE_DIRECTORY, config.VECTOR_COLLECTION_NAME)

    print("\nprices read from each tariff's own schedule")
    for tariff_name, document_name in config.TARIFF_DOCUMENT_BY_TARIFF.items():
        schedule = read_tariff_schedule(collection, tariff_name)
        print(f"  {tariff_name:<18} {document_name}")
        for window in schedule["price_windows"]:
            print(f"      from {window['opens_on']}: {_describe_window(window)}")
        if schedule["rolls_onto"]:
            print(f"      when the term ends the account moves to {schedule['rolls_onto']}")

    print(f"\nguaranteed standard payments              {config.STANDARDS_DOCUMENT}")
    for code, payment in read_standard_payments(collection).items():
        print(f"  {code} GBP {payment}")


if __name__ == "__main__":
    main()
