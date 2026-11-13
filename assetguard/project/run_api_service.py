"""Entry point 5: start the AssetGuard AI service, the only thing the dashboard talks to."""

import uvicorn

from config import config

if __name__ == "__main__":
    print("Starting " + config.API_TITLE)
    print("Docs available at http://localhost:" + str(config.API_PORT) + "/docs")

    # Imported after the messages above: loading the models and the index takes a few seconds.
    from api.routes import create_api_application

    uvicorn.run(create_api_application(config.API_TITLE), host=config.API_HOST, port=config.API_PORT)
