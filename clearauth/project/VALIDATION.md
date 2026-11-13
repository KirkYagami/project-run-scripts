# Validation record

Implementation verified on 10 November 2026 with Python 3.12 and the versions in `requirements-lock.txt`.

## Supplied test suite

- **40/40 tests not requiring Gemini: passed**, against real processed data, fitted models, vector retrieval, database, API and permissions.
- **50/50 supplied tests in offline contract mode: passed** (12.30 seconds), with only the external language-model response function replaced by the explicitly enabled `verification.offline_plugin`. This result does not validate the live Google Gemini response path.
- Additional offline checks pass for all three outcome branches, exact 7/6/5 call budgets, checkpoint reopening, completed state, and duplicate-decision refusal.
- Streamlit AppTest checks pass for all five page renderers, calling the real API through a local TestClient.
- Raw inputs, supplied tests and complete configuration were not altered. No `.dot` file was generated.

## Held-out model results

| Model | Metric | Achieved | Required |
| --- | --- | --- | --- |
| Approval | ROC-AUC | 0.9232 | 0.89 |
| Stay | R-squared | 0.7057 | 0.65 |
| Evidence | Macro-F1 | 0.9399 | 0.90 |

The supplied sensitivity, calibration, imputation, feature-order and class-coverage tests pass. Full metrics remain in `output/model_metrics.json`.

## Build results

The five cleaned dataset row counts match the expected 29,842 / 7,467 / 29,782 / 7,436 / 35,695. Quality removal reasons balance. Sixteen documents yield 145 sections and 205 passages; each service's documentation section is read back from its own policy.

## Live validation pending

The supplied p7 `.env` contains a placeholder Gemini key. Automatic approval review rejected the proposed use of p1 credentials for live tests because the calls would send supplied p7 clinical/member request data to Gemini without explicit approval for that data transfer and cross-project credential use. No such calls were made. Explicit user approval or locally configured credentials and authorised execution are needed to validate the unmocked suite.

## Repeat without affecting records

```sh
python verify.py --offline
```

For live Gemini validation, after configuring `.env` and authorising the data transfer:

```sh
python verify.py
```

Both modes isolate test application records from normal application records. The live mode uses no model double. Building the data, model and knowledge artifacts is a prerequisite for either mode.
