# Architecture

![Architecture Diagram](https://github.com/rohitk2/email-blurb-morph/blob/main/Architecture.jpg)

**System Overview**
- Frontend (`Vite + React`) posts email blurbs to the backend for extraction.
- Backend (`FastAPI`) drives the parsing flow, caching, logging, and metrics.
- MongoDB stores:
  - `Caching`: extracted fields + confidences (and optionally hashed PII).
  - `Logging`: request metadata (`source_hash`, `latency`, `cache_hit`).
  - `Metrics`: tokens used + latency for performance tracking.
- Optional PII encryption via `ENCRYPTION_ON` using a reversible XOR + Base64 scheme with `HASH_SECRET_KEY`.

---

## Request Flow

- Regex fallback (`regex_fallback.py`) can replace low-confidence `email` and `address`.
- Confidence thresholds are applied before deciding to use fallbacks.

---

## Components & Responsibilities

- `Backend/main.py`
  - `/health`, `/extract`, `/logging`, `/metrics` endpoints.
  - Orchestrates cache lookup, agent parsing, fallbacks, logging, metrics.
- `Backend/email_parser_agent.py`
  - Encapsulates the LLM-based extractor and prompt(s).
  - Provider selection via environment (`LLM_PROVIDER`), model/API keys via `.env`.
- `Backend/mongo_caching.py`
  - Reads/writes the `Caching` collection.
  - Conditional hashing of PII (`ENCRYPTION_ON=1`).
- `Backend/mongo_logging.py`
  - Inserts into `Logging` collection:
    - `source_hash` (hashed or plaintext per `ENCRYPTION_ON`),
    - `latency`,
    - `cache_hit`.
- `Backend/mongo_metrics.py`
  - Inserts into `Metrics` collection:
    - `tokens_used` (from agent),
    - `latency`.
- `Backend/email_blurb_hashing.py`
  - Reversible obfuscation: XOR with repeating key + Base64.
  - Key sourced from `.env` (`HASH_SECRET_KEY`).
- `Backend/regex_fallback.py`
  - `get_signature`, `get_email`, `get_address` helpers.
- `langgraph.json`
  - Configuration for prompt and trace exploration in LangGraph/LangSmith Studio.
- `runbook.md`
  - Ops notes: key rotation, prompt tuning, debugging workflow.

---

## Data Contracts

**ExtractRequest**
```json
{ "text": "string" }
```

**ExtractResponse**
```json
{
  "broker_name": "string",
  "broker_email": "string",
  "brokerage": "string",
  "complete_address": "string",
  "broker_name_confidence": 0.0,
  "broker_email_confidence": 0.0,
  "brokerage_confidence": 0.0,
  "complete_address_confidence": 0.0
}
```

---

## Mongo Collections

**Caching (PII optionally encrypted via `ENCRYPTION_ON=1`)**
```json
{
  "_id": "ObjectId",
  "email_blurb": "string|hashed",
  "broker_name": "string|hashed",
  "broker_email": "string|hashed",
  "brokerage": "string|hashed",
  "complete_address": "string|hashed",
  "broker_name_confidence": 0.92,
  "broker_email_confidence": 0.85,
  "brokerage_confidence": 0.77,
  "complete_address_confidence": 0.81,
  "created_at": "ISO-8601"
}
```

**Logging**
```json
{
  "_id": "ObjectId",
  "source_hash": "hashed|plaintext",
  "latency": 152.4,
  "cache_hit": true,
  "created_at": "ISO-8601"
}
```

**Metrics**
```json
{
  "_id": "ObjectId",
  "tokens_used": 231,
  "latency": 152.4,
  "created_at": "ISO-8601"
}
```

---

## Security & Encryption

- Algorithm: XOR cipher with a repeating secret key over the plaintext, then Base64 encode.
- Key source: `.env` → `HASH_SECRET_KEY`.
- Toggle: `.env` → `ENCRYPTION_ON=1` to hash/unhash PII (0 to disable).
- Intended for local obfuscation only (not cryptographic security). Use KMS/Secrets Manager in production.

---

## Configuration

Set these in `Backend/.env`:



---

## Local Development

Run the API:
```bash
python Backend/main.py
```

Or with Uvicorn:
```bash
uvicorn Backend.main:app --reload --port 8000
```

Test the endpoint:
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Your email blurb here"}'
```

---

## Prompt Tuning & Debugging

- Prompts and agent logic live in `email_parser_agent.py`. Update the system prompt and re-run.
- Use LangGraph/LangSmith Studio to iterate quickly on prompts and inspect traces [2].
- Regex fallback utilities let you probe deterministic extraction paths for emails/addresses.

---

## Future Considerations

- High-volume logging/metrics:
  - Move to write-optimized stores (e.g., Splunk for logs, Prometheus for metrics).
- Secrets & rotation:
  - Adopt AWS KMS and Secrets Manager for managed rotation and secure retrieval.
- Model strategy:
  - Improve accuracy by provider/model selection and multi-pass parsing.
  - Choose models based on task complexity and cost constraints.

---

## References

- Architecture diagram: https://github.com/rohitk2/email-blurb-morph/blob/main/Architecture.jpg [0]
- Prompt details: https://github.com/rohitk2/email-blurb-morph/blob/main/Prompts.pdf [1]
- Studio workflow overview: https://www.youtube.com/watch?v=Mi1gSlHwZLM&t=468s [2]