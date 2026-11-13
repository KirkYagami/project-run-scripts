from pathlib import Path
from config import config as c

REQUIRED_BEFORE_STARTING = [
    (p, "run_model_training.py")
    for p in [
        c.APPROVAL_MODEL_FILE,
        c.STAY_MODEL_FILE,
        c.EVIDENCE_MODEL_FILE,
        c.APPROVAL_SCHEMA_FILE,
        c.STAY_SCHEMA_FILE,
    ]
] + [
    (c.OPEN_REQUESTS_FILE, "supplied live data"),
    (c.REQUEST_NOTES_FILE, "supplied live data"),
    (c.DOCS_DIRECTORY, "supplied policy documents"),
    (
        str(Path(c.VECTOR_STORE_DIRECTORY) / c.VECTOR_STORE_FILE_NAME),
        "run_knowledge_indexing.py",
    ),
    (c.APPLICATION_DATABASE_FILE, "run_database_setup.py"),
]


def main():
    missing = [
        (path, source)
        for path, source in REQUIRED_BEFORE_STARTING
        if not Path(path).exists()
    ]
    if missing:
        print("The service cannot start.")
        for path, source in missing:
            print(path, "is missing; it comes from", source)
        return 1
    import uvicorn
    from api.routes import service_application

    print(
        f"Starting ClearAuth AI API on port {c.API_PORT}. Interactive documentation: http://localhost:{c.API_PORT}/docs"
    )
    uvicorn.run(service_application, host=c.API_HOST, port=c.API_PORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
