from fastapi.testclient import TestClient

from naples import schemas as s

from naples.config import config

from .test_data import TestData

CFG = config("testing")
