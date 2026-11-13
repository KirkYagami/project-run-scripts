import re
from pathlib import Path
from decimal import Decimal
from config import config as c
from .pdf_extraction import extract_document_text


def read_medical_policy(service_code):
    if service_code not in c.SERVICE_POLICY_DOCUMENTS:
        raise ValueError(
            c.NO_POLICY_CONFIGURED_MESSAGE.format(service_code=service_code)
        )
    name = c.SERVICE_POLICY_DOCUMENTS[service_code]
    t = re.sub(
        c.WHITESPACE_RUN_PATTERN,
        " ",
        extract_document_text(str(Path(c.DOCS_DIRECTORY) / name)),
    ).strip()

    def fail(why):
        raise ValueError(f"{name}: {why}")

    if re.findall(c.POLICY_SERVICE_CODE_PATTERN, t) != [service_code]:
        fail("wrong service code")
    section = re.search(c.CRITERIA_SECTION_PATTERN, t)
    if not section:
        fail("coverage criteria missing")
    split = re.split(c.CRITERION_NUMBER_PATTERN, section.group(1))
    numbers = [int(x) for x in split[1::2]]
    if not numbers or numbers != list(range(1, len(numbers) + 1)):
        fail(f"criterion numbers {numbers}")
    criteria = []
    seen = set()
    for content in split[2::2]:
        matches = [
            (kind, re.fullmatch(p, content.strip()))
            for kind, p in c.CRITERION_SENTENCE_PATTERNS.items()
        ]
        matches = [(k, m) for k, m in matches if m]
        if len(matches) != 1:
            fail(f"unknown criterion {content}")
        kind, m = matches[0]
        if kind in seen:
            fail(f"duplicate kind {kind}")
        seen.add(kind)
        g = m.groupdict()
        rules = {}
        for key, value in g.items():
            if key in [c.CRITERION_NAME_PART, c.CRITERION_SENTENCE_PART]:
                continue
            if key in c.WHOLE_NUMBER_RULES:
                rules[key] = int(value)
            elif key in c.BODY_MASS_INDEX_RULES:
                rules[key] = Decimal(value)
            elif key in c.LISTED_NAME_MAPPINGS:
                try:
                    rules[key] = [
                        c.LISTED_NAME_MAPPINGS[key][x.lower()]
                        for x in re.split(c.LISTED_NAME_SEPARATOR_PATTERN, value)
                    ]
                except KeyError:
                    fail(f"unknown listed name {value}")
            else:
                fail(f"unknown rule {key}")
        if kind == c.CONSERVATIVE_TREATMENT_OR_RED_FLAG_CRITERION:
            flags = re.findall(c.RED_FLAG_LIST_PATTERN, t)
            if len(flags) != 1:
                fail("red flag list missing or repeated")
            count, names = flags[0]
            try:
                rules[c.LISTED_RED_FLAGS_RULE] = [
                    c.RED_FLAG_NAME_MAPPING[x]
                    for x in re.split(c.LISTED_NAME_SEPARATOR_PATTERN, names)
                ]
            except KeyError:
                fail("unknown red flag")
            if c.NUMBER_WORD_VALUES.get(count) != len(rules[c.LISTED_RED_FLAGS_RULE]):
                fail("red flag count")
        criteria.append(
            dict(
                criterion_kind=kind,
                criterion_name=g[c.CRITERION_NAME_PART],
                criterion_sentence=g[c.CRITERION_SENTENCE_PART],
                rules=rules,
            )
        )
    return dict(service_code=service_code, document_name=name, criteria=criteria)
