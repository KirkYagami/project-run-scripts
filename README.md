# Project run scripts

Shell scripts that recreate and run the LoanServe and MeterMind projects.

| Script | What it does |
| --- | --- |
| `loanserve/create_loanserve.sh` | Writes every LoanServe source file (overwrites existing ones). |
| `loanserve/run_loanserve.sh` | Installs requirements into the local Python, builds missing artefacts, runs the tests, starts the API. |
| `metermind/create_metermind.sh` | Writes every MeterMind source file (overwrites existing ones). |
| `metermind/run_metermind.sh` | Installs requirements into the local Python, builds missing artefacts, runs the tests, starts the API. |

## Usage

Copy the scripts into the project folder (the one holding `data/`) and run them from there:

```bash
bash create_loanserve.sh   # recreate the code
bash run_loanserve.sh      # install, build, test, serve -> http://127.0.0.1:8000/docs
```

`run_*.sh` options: `--rebuild` (redo every artefact), `--skip-tests`, `--no-serve`,
and `HOST=` / `PORT=` to change where the API listens.

No virtual environment is created: requirements are installed with `pip` into the
Python on the machine (`python3` by default, or `PYTHON=/path/to/python`), which suits
a lab environment such as VS Code. If that Python is externally managed (PEP 668),
the install is retried with `--break-system-packages`. Python 3.11+ is required.

### Behind a lab proxy (VS Code / code-server)

If the lab opens the app at a URL like `https://<lab-host>/proxy/3001/`, the app has to know
that prefix or Swagger loads blank. The scripts read it from `VSCODE_PROXY_URI` when the lab
sets it; otherwise pass it yourself:

```bash
PORT=3001 ROOT_PATH=/proxy/3001 bash run_metermind.sh --skip-tests
# then open https://<lab-host>/proxy/3001/docs
```

Data files (`data/`) and `.env` are not part of this repo and are never overwritten.
MeterMind's language-model steps run only when `GEMINI_API_KEY` is set.
