# BillRight AI: how to run it

Run everything from this `Project` folder.

1. `pip install -r requirements.txt`
2. Put your key and model name in `.env` (`GEMINI_API_KEY`, `GEMINI_MODEL`).
3. Run the six entry points in order:
   - `python run_database_setup.py`
   - `python run_data_pipeline.py`
   - `python run_model_training.py`
   - `python run_knowledge_indexing.py`   (first run downloads the embedding model)
   - `python run_api_service.py`           (interactive docs at http://localhost:8081/docs)
   - `streamlit run run_dashboard.py`      (http://localhost:8080)
4. Sign in with a seeded account, for example `fiona` / `11111111` (Revenue Controller),
   `hamish` / `22222222` (Billing Analyst), `megan` / `33333333` (Contact Centre Agent).
5. `pytest tests.py`
