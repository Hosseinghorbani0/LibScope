"""
API Entrypoint runner.
"""
import uvicorn
from libscope.api.main import app
from libscope.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "libscope.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

