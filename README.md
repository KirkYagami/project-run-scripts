# Project run scripts

Shell scripts that recreate and run the LoanServe and MeterMind projects.

| Script | What it does |
| --- | --- |
| `loanserve/create_loanserve.sh` | Writes every LoanServe source file (overwrites existing ones). |
| `loanserve/run_loanserve.sh` | Sets up `.venv`, builds missing artefacts, runs the tests, starts the API. |
| `metermind/create_metermind.sh` | Writes every MeterMind source file (overwrites existing ones). |
| `metermind/run_metermind.sh` | Sets up `.venv`, builds missing artefacts, runs the tests, starts the API. |

## Usage

Copy the scripts into the project folder (the one holding `data/`) and run them from there:

```bash
bash create_loanserve.sh   # recreate the code
bash run_loanserve.sh      # install, build, test, serve -> http://127.0.0.1:8000/docs
```

`run_*.sh` options: `--rebuild` (redo every artefact), `--skip-tests`, `--no-serve`,
and `HOST=` / `PORT=` to change where the API listens.

Data files (`data/`) and `.env` are not part of this repo and are never overwritten.
MeterMind's language-model steps run only when `GEMINI_API_KEY` is set.
