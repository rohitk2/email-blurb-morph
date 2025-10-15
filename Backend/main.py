from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import re
import uvicorn
from email_parser_agent import EmailParserAgent, EmailAgentRequest, EmailAgentResponse
from mongo_caching import cache_insert, cache_hit

app = FastAPI()

# ---- Models ----
class ExtractRequest(BaseModel):
    text: str

class ExtractResponse(BaseModel):
    broker_name: str = ""
    broker_name_confidence: float = 0.0
    broker_email: str = ""
    broker_email_confidence: float = 0.0
    brokerage: str = ""
    brokerage_confidence: float = 0.0
    complete_address: str = ""
    complete_address_confidence: float = 0.0

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

@app.post("/extract", response_model=EmailAgentResponse)
async def extract_text(req: ExtractRequest) -> EmailAgentResponse:
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
        return EmailAgentResponse(
            broker_name=cached["broker_name"],
            broker_name_confidence=cached["broker_name_confidence"],
            broker_email=cached["broker_email"],
            broker_email_confidence=cached["broker_email_confidence"],
            brokerage=cached["brokerage"],
            brokerage_confidence=cached["brokerage_confidence"],
            complete_address=cached["complete_address"],
            complete_address_confidence=cached["complete_address_confidence"],
        )

    # (2B) No hit → original flow: run agent, insert, return
    try:
        res = await agent.parse(EmailAgentRequest(email_blurb=req.text))

        # Persist the parsed result to MongoDB
        try:
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
        except Exception as db_err:
            print(f"Mongo insert failed: {db_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    return EmailAgentResponse(
        broker_name=res.broker_name,
        broker_name_confidence=res.broker_name_confidence,
        broker_email=res.broker_email,
        broker_email_confidence=res.broker_email_confidence,
        brokerage=res.brokerage,
        brokerage_confidence=res.brokerage_confidence,
        complete_address=res.complete_address,
        complete_address_confidence=res.complete_address_confidence,
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)