from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, unquote
from email_blurb_hashing import hash as blurb_hash, unhash as blurb_unhash

def cache_hit(email_blurb: str):
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
    coll = db["cache"]

    # Encryption toggle: 1 means on, else off
    enc_on = os.getenv("ENCRYPTION_ON", "0") == "1"

    print(f"enc_on: {enc_on}")
    # (2) Hash before querying if encryption is on
    query_blurb = blurb_hash(email_blurb) if enc_on else email_blurb

    # Try to find a matching document by email_blurb
    doc = coll.find_one({"email_blurb": query_blurb})
    if not doc:
        return False

    # (3) Unhash PII before returning if encryption is on
    return {
        "broker_name": (blurb_unhash(doc.get("broker_name", "")) if enc_on else doc.get("broker_name", "")),
        "broker_email": (blurb_unhash(doc.get("broker_email", "")) if enc_on else doc.get("broker_email", "")),
        "brokerage": (blurb_unhash(doc.get("brokerage", "")) if enc_on else doc.get("brokerage", "")),
        "complete_address": (blurb_unhash(doc.get("complete_address", "")) if enc_on else doc.get("complete_address", "")),
        "broker_name_confidence": float(doc.get("broker_name_confidence", 0.0)),
        "broker_email_confidence": float(doc.get("broker_email_confidence", 0.0)),
        "brokerage_confidence": float(doc.get("brokerage_confidence", 0.0)),
        "complete_address_confidence": float(doc.get("complete_address_confidence", 0.0)),
    }

def cache_insert(
    email_blurb: str,
    broker_name: str,
    broker_email: str,
    brokerage: str,
    complete_address: str,
    broker_name_confidence: float,
    broker_email_confidence: float,
    brokerage_confidence: float,
    complete_address_confidence: float,
):
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
    coll = db["cache"]

    # Encryption toggle: 1 means on, else off
    enc_on = os.getenv("ENCRYPTION_ON", "0") == "1"
    print(f"enc_on: {enc_on}")

    # (1) Hash PII before inserting if encryption is on
    doc = {
        "email_blurb": (blurb_hash(email_blurb) if enc_on else email_blurb),
        "broker_name": (blurb_hash(broker_name) if enc_on else broker_name),
        "broker_email": (blurb_hash(broker_email) if enc_on else broker_email),
        "brokerage": (blurb_hash(brokerage) if enc_on else brokerage),
        "complete_address": (blurb_hash(complete_address) if enc_on else complete_address),
        "broker_name_confidence": broker_name_confidence,
        "broker_email_confidence": broker_email_confidence,
        "brokerage_confidence": brokerage_confidence,
        "complete_address_confidence": complete_address_confidence,
    }
    # Insert only once to avoid duplicate _id errors
    result = coll.insert_one(doc)
    print(f"Inserted document id: {result.inserted_id}")
    return str(result.inserted_id)

if __name__ == "__main__":
    email_blurb = "Hello, I am Bob. I am a broker at Bob Inc. My email is bob@gmail.com. My address is 123 Main St, Los Angeles, CA 90001."
    broker_name = "Bob"
    broker_email = "bob@gmail.com"
    brokerage = "Bob Inc."
    complete_address = "123 Main St, Los Angeles, CA 90001"

    broker_name_confidence = 0.95
    broker_email_confidence = 0.98
    brokerage_confidence = 0.9
    complete_address_confidence = 0.88


    cache_insert(
        email_blurb=email_blurb,
        broker_name=broker_name,
        broker_email=broker_email,
        brokerage=brokerage,
        complete_address=complete_address,
        broker_name_confidence=broker_name_confidence,
        broker_email_confidence=broker_email_confidence,
        brokerage_confidence=brokerage_confidence,
        complete_address_confidence=complete_address_confidence,
    )
    # After you insert, test the cache hit using the same blurb
    hit = cache_hit(email_blurb)
    print("Cache hit:", hit)

    hit = cache_hit("Should not work")
    print("Cache hit:", hit)