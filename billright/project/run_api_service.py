"""Starts the REST service, after checking that everything it needs is already on disk."""
import os
import sys

from config import config

REQUIRED_BEFORE_STARTING = [
    (config.APPLICATION_DATABASE_FILE, "run_database_setup.py"),
    (config.REBILL_MODEL_FILE, "run_model_training.py"),
    (config.EFFORT_MODEL_FILE, "run_model_training.py"),
    (config.CAUSE_MODEL_FILE, "run_model_training.py"),
    (config.REBILL_SCHEMA_FILE, "run_model_training.py"),
    (config.EFFORT_SCHEMA_FILE, "run_model_training.py"),
    (config.VECTOR_STORE_DIRECTORY, "run_knowledge_indexing.py"),
]


def main():
    """Start the service, or explain what must be run first. Returns the exit status."""
    missing = [(path, producer) for path, producer in REQUIRED_BEFORE_STARTING
               if not os.path.exists(path)]
    if missing:
        print("The service cannot start. Missing:")
        for path, producer in missing:
            print(f"  {path}  (produced by {producer})")
        return 1

    import uvicorn
    from api.routes import service_application

    print(f"Interactive documentation: http://localhost:{config.API_PORT}/docs")
    uvicorn.run(service_application, host=config.API_HOST, port=config.API_PORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
