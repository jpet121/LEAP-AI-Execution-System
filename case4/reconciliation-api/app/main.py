"""uvicorn app.main:create_app --factory; settings loaded at process startup."""
from .api import create_app as create_app
