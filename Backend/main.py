from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import re
import uvicorn
import time
from email_parser_agent import EmailParserAgent, EmailAgentRequest, EmailAgentResponse
from mongo_caching import cache_insert, cache_hit
from mongo_metrics import insert_tracing
from mongo_metrics import get_metrics as get_metrics_db
from mongo_logging import get_logging as get_logging_db
from mongo_logging import insert_log
from regex_fallback import get_broker_info

app = FastAPI()

# ---- Models ----
class ExtractRequest(BaseModel):
    text: str

class ExtractResponse(BaseModel):
    broker_name: str = ""
    broker_email: str = ""
    brokerage: str = ""
    complete_address: str = ""


# ---- Utilities ----
def generate_localhost_origins(start_port: int, end_port: int) -> List[str]:
    origins: List[str] = []
    for port in range(start_port, end_port + 1):
        origins.append(f"http://localhost:{port}")
        origins.append(f"http://127.0.0.1:{port}")
    return origins

# Include Vite dev port (8080) and common ports (3000) in addition to 5173–6200
front_end_ports = [8080, 3000]
origins = generate_localhost_origins(5173, 6200) + \
          [f"http://localhost:{p}" for p in front_end_ports] + \
          [f"http://127.0.0.1:{p}" for p in front_end_ports]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ----
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

agent = EmailParserAgent()

@app.post("/extract", response_model=ExtractResponse)
async def extract_text(req: ExtractRequest):
    start_time = time.perf_counter()
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # (1) Cache lookup
    cached = None
    try:
        cached = cache_hit(req.text)
    except Exception as cache_err:
        print(f"Cache lookup failed: {cache_err}")

    # (2A) Cache hit → return cached values
    if cached:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        insert_log(
            source_hash=req.text,
            cache_hit=True,
            latency=latency_ms,
        )
        try:
            insert_tracing(tokens_used=0, latency=latency_ms)
        except Exception as metrics_err:
            print(f"Metrics insert failed: {metrics_err}")

        use_email_fallback = float(cached.get("broker_email_confidence", 0.0)) < 0.8
        use_address_fallback = float(cached.get("complete_address_confidence", 0.0)) < 0.8
        broker_info = get_broker_info(req.text) if (use_email_fallback or use_address_fallback) else None
        fallback_email = broker_info.get("broker_email", "") if broker_info else ""
        fallback_address = broker_info.get("complete_address", "") if broker_info else ""

        return ExtractResponse(
            broker_name=cached["broker_name"],
            broker_email=(fallback_email if (use_email_fallback and fallback_email) else cached["broker_email"]),
            brokerage=cached["brokerage"],
            complete_address=(fallback_address if (use_address_fallback and fallback_address) else cached["complete_address"]),
        )

    # (2B) No hit → original flow: run agent, insert cache, log metrics, return
    try:
        res = await agent.parse(EmailAgentRequest(email_blurb=req.text))
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        insert_log(
            source_hash=req.text,
            cache_hit=False,
            latency=latency_ms,
        )

        cache_insert(
            email_blurb=req.text,  
            broker_name=res.broker_name,
            broker_email=res.broker_email,
            brokerage=res.brokerage,
            complete_address=res.complete_address,
            broker_name_confidence=res.broker_name_confidence,
            broker_email_confidence=res.broker_email_confidence,
            brokerage_confidence=res.brokerage_confidence,
            complete_address_confidence=res.complete_address_confidence,
        )

        insert_tracing(tokens_used=res.tokens_used, latency=latency_ms)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    use_email_fallback = float(getattr(res, "broker_email_confidence", 0.0)) < 0.8
    use_address_fallback = float(getattr(res, "complete_address_confidence", 0.0)) < 0.8
    broker_info = get_broker_info(req.text) if (use_email_fallback or use_address_fallback) else None
    fallback_email = broker_info.get("broker_email", "") if broker_info else ""
    fallback_address = broker_info.get("complete_address", "") if broker_info else ""

    return ExtractResponse(
        broker_name=res.broker_name,
        broker_email=(fallback_email if (use_email_fallback and fallback_email) else res.broker_email),
        brokerage=res.brokerage,
        complete_address=(fallback_address if (use_address_fallback and fallback_address) else res.complete_address),
    )

# HTTP route: return latest logging entries
@app.post("/logging")
def get_logging():
    try:
        items = get_logging_db()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {e}")

# HTTP route: return latest metrics list
@app.post("/metrics")
def get_metrics():
    try:
        items = get_metrics_db()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)