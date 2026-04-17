from __future__ import annotations

import json
import os
import re
from io import BytesIO
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

try:
    from api.runtime import API_BASE_PREFIX
except ImportError:  # pragma: no cover - local script fallback
    from runtime import API_BASE_PREFIX

try:
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:  # pragma: no cover - compatibility fallback
    from langchain.output_parsers import PydanticOutputParser

try:
    from langchain_core.prompts import PromptTemplate
except ImportError:  # pragma: no cover - compatibility fallback
    from langchain.prompts import PromptTemplate

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover - lightweight compatibility fallback
    class RecursiveCharacterTextSplitter:
        def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str) -> List[str]:
            if not text:
                return []

            step = max(1, self.chunk_size - self.chunk_overlap)
            chunks: List[str] = []
            start = 0

            while start < len(text):
                end = start + self.chunk_size
                chunks.append(text[start:end])
                start += step

            return chunks

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency at runtime
    ChatOpenAI = None


router = APIRouter(tags=["report-risk"])


class RiskFinding(BaseModel):
    title: str = Field(..., description="Short risk label.")
    rationale: str = Field(..., description="Why this risk matters based on the filing.")


class RiskAssessmentMatrix(BaseModel):
    financial_risks: List[RiskFinding] = Field(..., min_length=2, max_length=2)
    operational_risks: List[RiskFinding] = Field(..., min_length=2, max_length=2)
    overall_risk_severity_score: int = Field(..., ge=1, le=10)


PROMPT_TEMPLATE = """
You are a Chief Risk Officer. Read this corporate filing excerpt and extract a "Risk Assessment Matrix". Identify:
1. Top 2 Financial Risks (liquidity, debt).
2. Top 2 Operational Risks (supply chain, management).
3. Assign an overall Risk Severity Score (1-10).

{format_instructions}

Corporate filing excerpt:
{excerpt}
"""

FINANCIAL_RULES = [
    (
        "Liquidity pressure",
        ("liquidity", "cash flow", "working capital", "credit facility", "refinancing"),
        "The filing points to pressure on cash generation or access to funding.",
    ),
    (
        "Debt servicing strain",
        ("debt", "interest expense", "covenant", "leverage", "borrowings"),
        "The filing highlights debt load, covenant pressure, or borrowing costs.",
    ),
    (
        "Margin compression",
        ("gross margin", "operating margin", "impairment", "cost inflation"),
        "The filing suggests profitability could weaken if costs stay elevated.",
    ),
]
OPERATIONAL_RULES = [
    (
        "Supply chain disruption",
        ("supply chain", "supplier", "inventory", "logistics", "shortage"),
        "The filing references supplier concentration, shortages, or logistics bottlenecks.",
    ),
    (
        "Management execution risk",
        ("management", "leadership", "turnover", "restructuring", "integration"),
        "The filing raises concerns about execution, leadership continuity, or restructuring complexity.",
    ),
    (
        "Regulatory and compliance drag",
        ("regulatory", "compliance", "litigation", "investigation", "cybersecurity"),
        "The filing signals legal, compliance, or cyber issues that may disrupt operations.",
    ),
]
SEVERITY_TERMS = (
    "material weakness",
    "substantial doubt",
    "default",
    "bankruptcy",
    "impairment",
    "shortage",
    "litigation",
    "investigation",
)


def clean_text(raw_text: str) -> str:
    return re.sub(r"\s+", " ", raw_text).strip()


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text_segments = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            text_segments.append(page_text)

    return clean_text(" ".join(text_segments))


def build_excerpt(source_text: str) -> str:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1800, chunk_overlap=250)
    chunks = splitter.split_text(source_text)
    return "\n\n".join(chunks[:4])


def select_risks(text: str, rules: List[tuple[str, tuple[str, ...], str]]) -> List[RiskFinding]:
    matches: List[tuple[int, RiskFinding]] = []

    for title, keywords, rationale in rules:
        score = sum(keyword in text for keyword in keywords)
        if score:
            matches.append(
                (
                    score,
                    RiskFinding(
                        title=title,
                        rationale=rationale,
                    ),
                )
            )

    if not matches:
        fallback_title = rules[0][0]
        fallback_rationale = rules[0][2]
        matches.append((1, RiskFinding(title=fallback_title, rationale=fallback_rationale)))

    ordered = [finding for _, finding in sorted(matches, key=lambda item: item[0], reverse=True)]
    while len(ordered) < 2:
        default_rule = rules[len(ordered)]
        ordered.append(RiskFinding(title=default_rule[0], rationale=default_rule[2]))

    return ordered[:2]


def heuristic_risk_matrix(source_text: str) -> RiskAssessmentMatrix:
    lowered = source_text.lower()
    financial_risks = select_risks(lowered, FINANCIAL_RULES)
    operational_risks = select_risks(lowered, OPERATIONAL_RULES)

    severity = 4
    severity += min(3, sum(term in lowered for term in SEVERITY_TERMS))
    severity += 1 if any(keyword in lowered for keyword in ("liquidity", "debt", "supply chain")) else 0
    severity += 1 if any(keyword in lowered for keyword in ("turnover", "restructuring", "investigation")) else 0
    severity = max(1, min(10, severity))

    return RiskAssessmentMatrix(
        financial_risks=financial_risks,
        operational_risks=operational_risks,
        overall_risk_severity_score=severity,
    )


async def generate_matrix_with_llm(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or ChatOpenAI is None:
        raise RuntimeError("No hosted LLM is configured.")

    llm = ChatOpenAI(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )
    response = await llm.ainvoke(prompt)
    return getattr(response, "content", str(response))


@router.post(
    f"{API_BASE_PREFIX}/v1/analyze-report-risk",
    response_model=RiskAssessmentMatrix,
)
async def analyze_report_risk(file: UploadFile = File(...)) -> RiskAssessmentMatrix:
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf uploads are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    try:
        extracted_text = extract_pdf_text(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unreadable PDF. Please upload a text-based PDF filing.") from exc

    if not extracted_text:
        raise HTTPException(status_code=400, detail="Unreadable PDF or no extractable text was found.")

    excerpt = build_excerpt(extracted_text)
    parser = PydanticOutputParser(pydantic_object=RiskAssessmentMatrix)
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE).format(
        format_instructions=parser.get_format_instructions(),
        excerpt=excerpt,
    )

    try:
        llm_output = await generate_matrix_with_llm(prompt)
        return parser.parse(llm_output)
    except Exception:
        heuristic_output = heuristic_risk_matrix(excerpt)
        # Force the response through the parser so the same schema gate is always applied.
        return parser.parse(json.dumps(heuristic_output.model_dump()))
