import os
import json
import time
from typing import Dict, TypedDict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from types import SimpleNamespace

# Load environment variables (expects GEMINI_API_KEY)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)


class EmailAgentRequest(BaseModel):
    email_blurb: str


class EmailAgentResponse(BaseModel):
    broker_name: str = ""
    broker_name_confidence: float = 0.0
    broker_email: str = ""
    broker_email_confidence: float = 0.0
    brokerage: str = ""
    brokerage_confidence: float = 0.0
    complete_address: str = ""
    complete_address_confidence: float = 0.0
    tokens_used: str = ""


class EmailParserAgent:
    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise SystemExit(
                "GROQ_API_KEY not set. Add it to Backend/.env (GROQ_API_KEY=...) and restart."
            )

        # Use a supported Groq model, overridable via env
        model_id = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.llm = ChatGroq(
            model=model_id,
            groq_api_key=groq_key,
            temperature=0.1,
        )

        # Strong system prompt to enforce strict JSON
        self.system_prompt = """You are an Email Agent that extracts structured broker information from raw email text.

Return ONLY a valid JSON object with these EXACT keys:
- broker_name (string)
- broker_name_confidence (number between 0 and 1)
- broker_email (string)
- broker_email_confidence (number between 0 and 1)
- brokerage (string)
- brokerage_confidence (number between 0 and 1)
- complete_address (string)
- complete_address_confidence (number between 0 and 1)

Note this is for INSURANCE brokers, not real estate agents, not wholesalers.

Each email may have one or more signatures. The signature itself should have most of the info you need.
When there are multiple signatures (e.g., one from a real estate agent/wholesaler and one from the insurance broker),
prefer the information from the insurance broker.

Example of wholesaler (do NOT use):
Jerry Smith | Associate Broker, Property resident license: 1190929
direct: 111111111 | mobile: 111112111 | jerry@abc.com
ABC Company | 123 Building Avenue, City, State | Top 10 Largest P&C Wholesaler | Five-Star Wholesale Broker | Best Places to Work in Insurance | Top Insurance Employers

Example of insurance agent (use this type when appropriate):
Harry Smith, AINS
Clearance Specialist
ABC Insurance Company
123 Building Avenue, City, State
Direct: 11111111111

Rules:
- Prefer explicit names/emails/addresses found in the text. Do NOT hallucinate.
- broker_email must be a plausible email format if present; otherwise empty string.
- Confidence values must be decimals between 0 and 1 inclusive, reflecting how certain you are.
- If multiple plausible candidates appear, choose the best one and set a lower confidence accordingly.
- Return ONLY the JSON with these exact keys; no commentary, markdown, code fences, or extra keys.
"""

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{email_blurb}"),
            ]
        )

        # Chain: prompt -> llm
        self.chain = self.prompt | self.llm

    async def parse(self, request: EmailAgentRequest) -> EmailAgentResponse:
        """Run the agent and produce the structured response."""
        start_time = time.perf_counter()
        result = await self.chain.ainvoke({"email_blurb": request.email_blurb})

        tokens_used = None
        try:
            meta = getattr(result, "response_metadata", {}) or {}
            token_usage = meta.get("token_usage") or meta.get("usage") or {}
            if isinstance(token_usage, dict):
                total = token_usage.get("total_tokens")
                if total is None:
                    total = token_usage.get("total")
                if total is None:
                    inp = token_usage.get("input_tokens") or token_usage.get("prompt_tokens") or 0
                    out = token_usage.get("output_tokens") or token_usage.get("completion_tokens") or 0
                    total = inp + out
                tokens_used = total
        except Exception:
            tokens_used = None

        print(f"Tokens Used: {tokens_used}")

        raw = result.content or ""

        # Try to recover JSON if the model includes extra text/fences
        json_str = self._extract_json_str(raw)
        data: Dict[str, str] = {}
        try:
            data = json.loads(json_str)
        except Exception:
            # Fallback: return empty fields when parse fails
            data = {}

        # Normalize and ensure all keys exist
        return EmailAgentResponse(
            broker_name=str(data.get("broker_name", "")),
            broker_email=str(data.get("broker_email", "")),
            brokerage=str(data.get("brokerage", "")),
            complete_address=str(data.get("complete_address", "")),
            broker_name_confidence=self._to_conf(data.get("broker_name_confidence", 0)),
            broker_email_confidence=self._to_conf(data.get("broker_email_confidence", 0)),
            brokerage_confidence=self._to_conf(data.get("brokerage_confidence", 0)),
            complete_address_confidence=self._to_conf(data.get("complete_address_confidence", 0)),
            tokens_used=str(tokens_used) if tokens_used is not None else ""
        )

    def _extract_json_str(self, text: str) -> str:
        """Extract the first {...} block to reduce chances of fence/markdown noise."""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return "{}"

    def _to_conf(self, val) -> float:
        try:
            f = float(val)
        except Exception:
            return 0.0
        if f < 0.0:
            return 0.0
        if f > 1.0:
            return 1.0
        return f


# Input-only state for LangGraph Dev UI
class EmailState(TypedDict):
    email_blurb: str

agent = EmailParserAgent()

async def parse_node(state: EmailState) -> dict:
    try:
        req = EmailAgentRequest(email_blurb=state["email_blurb"])
        res = await agent.parse(req)
        return {
            "broker_name": res.broker_name,
            "broker_name_confidence": res.broker_name_confidence,
            "broker_email": res.broker_email,
            "broker_email_confidence": res.broker_email_confidence,
            "brokerage": res.brokerage,
            "brokerage_confidence": res.brokerage_confidence,
            "complete_address": res.complete_address,
            "complete_address_confidence": res.complete_address_confidence,
            "tokens_used": res.tokens_used,
        }
    except Exception as e:
        return {"error": str(e)}

builder = StateGraph(EmailState)
builder.add_node("parse", parse_node)
builder.add_edge(START, "parse")
builder.add_edge("parse", END)

graph = builder.compile()

if __name__ == "__main__":
    import asyncio

    sample_inputs = [
        # Insurance broker-style signature (should be used)
        "Hi team,\n\nCopying the broker for context.\n\nHarry Smith, AINS\nClearance Specialist\nABC Insurance Company\n123 Building Avenue, Chicago, IL 60601\nDirect: (312) 555-0100\nEmail: harry.smith@abcinsurance.com",
        # Wholesaler-style signature (should NOT be preferred)
        "Jerry Smith | Associate Broker, Property resident license: 1190929\nDirect: 111-111-1111 | Mobile: 111-112-1111 | jerry@abc.com\nABC Company | 123 Building Avenue, City, State | Top 10 Largest P&C Wholesaler | Five-Star Wholesale Broker | Best Places to Work in Insurance | Top Insurance Employers",
        # Another broker-style signature
        "Regards,\nSusan Miller\nMiller Insurance Group\n555 Market St, San Francisco, CA 94103\nsusan@millerins.com\nOffice: 415-555-0101",
    ]

    async def run_tests():
        for i, email in enumerate(sample_inputs, 1):
            print(f"\n=== Sample {i} ===")
            req = EmailAgentRequest(email_blurb=email)
            res = await agent.parse(req)
            print("Parsed JSON:")
            print(json.dumps({
                "broker_name": res.broker_name,
                "broker_name_confidence": res.broker_name_confidence,
                "broker_email": res.broker_email,
                "broker_email_confidence": res.broker_email_confidence,
                "brokerage": res.brokerage,
                "brokerage_confidence": res.brokerage_confidence,
                "complete_address": res.complete_address,
                "complete_address_confidence": res.complete_address_confidence,
                "tokens_used": res.tokens_used,
            }, indent=2))
    asyncio.run(run_tests())