from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, unquote

def empty_tables():
    # Load env and read URI (same approach as other backend modules)
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

    # Clear all three collections
    collections = ["cache", "Logging", "metrics"]
    for coll_name in collections:
        result = db[coll_name].delete_many({})
        print(f"Cleared '{coll_name}': deleted {result.deleted_count} documents.")

if __name__ == "__main__":
    empty_tables()