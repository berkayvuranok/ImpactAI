"""Application entry point."""

import uvicorn

from code_impact.infrastructure.config.settings import get_settings
from code_impact.presentation.api.app import create_app

app = create_app(get_settings())

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "code_impact.presentation.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
