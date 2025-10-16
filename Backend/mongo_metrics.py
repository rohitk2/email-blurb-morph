from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, unquote
import random
from datetime import datetime

def insert_tracing(tokens_used, latency):
    """
    Insert a tracing document into the MailMorph.metrics collection.
    Uses the same env/URI handling as mongo_caching.py.
    """
    # Load env and read URI
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)
    raw_uri = os.getenv("Mongo_DB_URI")
    if not raw_uri:
        raise SystemExit("Mongo_DB_URI missing in Backend/.env")

    # Safely rebuild URI to avoid double-encoding or invalid escaping
    try:
        scheme, rest = raw_uri.split("://", 1)
        auth, host_and_query = rest.rsplit("@", 1)  # last '@' separates host
        if ":" in auth:
            username, password = auth.split(":", 1)
            safe_user = quote_plus(unquote(username))
            safe_pass = quote_plus(unquote(password))
            safe_uri = f"{scheme}://{safe_user}:{safe_pass}@{host_and_query}"
        else:
            safe_auth = quote_plus(unquote(auth))
            safe_uri = f"{scheme}://{safe_auth}@{host_and_query}"
    except Exception:
        safe_uri = raw_uri

    client = MongoClient(safe_uri, server_api=ServerApi('1'))
    client.admin.command('ping')

    db = client["MailMorph"]
    coll = db["metrics"]  # use metrics collection instead of cache

    doc = {
        "tokens_used": int(tokens_used),
        "latency": latency,
        "timestamp": datetime.utcnow(),
    }
    result = coll.insert_one(doc)
    print(f"Inserted metrics id: {result.inserted_id}")
    return str(result.inserted_id)

def get_metrics():
    """
    Fetch up to 200 most recent metric documents and return as a Python list.
    Normalizes _id to str and timestamp to ISO string for easy serialization.
    """
    # Load env and read URI
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)
    raw_uri = os.getenv("Mongo_DB_URI")
    if not raw_uri:
        raise SystemExit("Mongo_DB_URI missing in Backend/.env")

    # Safely rebuild URI to avoid double-encoding or invalid escaping
    try:
        scheme, rest = raw_uri.split("://", 1)
        auth, host_and_query = rest.rsplit("@", 1)  # last '@' separates host
        if ":" in auth:
            username, password = auth.split(":", 1)
            safe_user = quote_plus(unquote(username))
            safe_pass = quote_plus(unquote(password))
            safe_uri = f"{scheme}://{safe_user}:{safe_pass}@{host_and_query}"
        else:
            safe_auth = quote_plus(unquote(auth))
            safe_uri = f"{scheme}://{safe_auth}@{host_and_query}"
    except Exception:
        safe_uri = raw_uri

    client = MongoClient(safe_uri, server_api=ServerApi('1'))
    db = client["MailMorph"]
    coll = db["metrics"]

    # Latest first; cap at 200
    cursor = coll.find({}).sort("timestamp", -1).limit(200)

    items = []
    for doc in cursor:
        ts = doc.get("timestamp")
        items.append({
            "tokens_used": int(doc.get("tokens_used", 0)),
            "latency": float(doc.get("latency", 0)),
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else (str(ts) if ts is not None else None),
        })
    return items

if __name__ == "__main__":
    tokens_used = random.randint(50, 2500)
    latency = round(random.uniform(5.0, 1000.0), 2)
    inserted_id = insert_tracing(tokens_used=tokens_used, latency=latency)
    print(f"Inserted metrics id: {inserted_id}")

    # Fetch and print metrics (first 200, show top 5)
    try:
        latest = get_metrics()
        print(f"Fetched {len(latest)} metrics records.")
        for i, m in enumerate(latest[:5], start=1):
            print(
                f"{i}. _id={m.get('_id')}, tokens_used={m.get('tokens_used')}, "
                f"latency={m.get('latency')}, timestamp={m.get('timestamp')}"
            )
    except Exception as e:
        print(f"Error fetching metrics: {e}")