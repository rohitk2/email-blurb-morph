from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, unquote
import random
from datetime import datetime


def insert_log(source_hash: str, cache_hit: bool, latency: float) -> str:
    """
    Insert a log document into the MailMorph.Logging collection.
    Mirrors mongo_metrics.py but targets the 'Logging' collection.
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
    coll = db["Logging"]  # use Logging collection

    doc = {
        "source_hash": str(source_hash),
        "cache_hit": bool(cache_hit),
        "latency": float(latency),
        # Store timestamp for sorting, but we won’t return it from get_logging()
        "timestamp": datetime.utcnow(),
    }
    result = coll.insert_one(doc)
    print(f"Inserted log id: {result.inserted_id}")
    return str(result.inserted_id)


def get_logging():
    """
    Fetch up to 200 most recent log documents and return as a Python list.
    Returns dictionaries with: request_id (str), source_hash (str),
    cache_hit (bool), latency (float). Timestamp is omitted.
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
    coll = db["Logging"]

    # Latest first; cap at 200
    cursor = coll.find({}).sort("timestamp", -1).limit(200)

    items = []
    for doc in cursor:
        ts = doc.get("timestamp")
        items.append({
            "request_id": str(doc.get("_id")),
            "source_hash": str(doc.get("source_hash", "")),
            "cache_hit": bool(doc.get("cache_hit", False)),
            "latency": float(doc.get("latency", 0.0)),
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else (str(ts) if ts is not None else None),
        })
    return items


if __name__ == "__main__":
    # Insert 5 random logs
    for _ in range(5):
        request_id = f"req-{random.randint(100000, 999999)}"
        source_hash = f"src-{random.randint(100000, 999999)}"
        cache_hit = random.choice([True, False])
        latency = round(random.uniform(5.0, 1000.0), 2)

        inserted_id = insert_log(
            source_hash=source_hash,
            cache_hit=cache_hit,
            latency=latency,
        )
        print(f"Inserted log id: {inserted_id}")

    # Fetch and print logs (first 200, show top 5)
    try:
        latest = get_logging()
        print(f"Fetched {len(latest)} log records.")
        for i, m in enumerate(latest[:5], start=1):
            print(
                f"{i}. request_id={m.get('request_id')}, source_hash={m.get('source_hash')}, "
                f"cache_hit={m.get('cache_hit')}, latency={m.get('latency')}"
            )
    except Exception as e:
        print(f"Error fetching logs: {e}")