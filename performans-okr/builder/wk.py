"""Ad-hoc yardımcı: API anahtarını .env'den okuyup WorkiomClient döndürür."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workiom.client import WorkiomClient

def client(verbose=False):
    key = os.environ.get("API_KEY")
    if not key:
        for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
            if line.startswith("API_KEY="):
                key = line.split("=", 1)[1].strip()
    c = WorkiomClient(key, verbose=verbose)
    c.MIN_REQUEST_INTERVAL = 0.35
    return c

def show(x, n=3000):
    print(json.dumps(x, ensure_ascii=False, default=str)[:n])
