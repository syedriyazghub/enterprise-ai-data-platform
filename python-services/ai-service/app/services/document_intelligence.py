"""
Document Intelligence Service

Classifies documents, extracts entities, and understands
invoices, contracts, medical reports, and financial statements.
"""
from dataclasses import dataclass, field
from typing import Any
import structlog

from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class DocumentClassification:
    document_type: str
    confidence: float
    sub_type: str = ""
    language: str = "en"


@dataclass
class ExtractedEntity:
    entity_type: str
    value: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class DocumentIntelligenceResult:
    classification: DocumentClassification
    entities: list[ExtractedEntity] = field(default_factory=list)
    extracted_fields: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    confidence_score: float = 0.0
    raw_text: str = ""


DOCUMENT_TYPES = {
    "invoice": ["invoice number", "bill to", "amount due", "payment terms", "tax", "total"],
    "contract": ["agreement", "parties", "terms", "obligations", "termination", "governing law"],
    "medical_report": ["patient", "diagnosis", "prescription", "doctor", "hospital", "icd"],
    "bank_statement": ["account number", "balance", "transaction", "debit", "credit", "statement"],
    "insurance_claim": ["claim number", "policy", "insured", "coverage", "premium", "deductible"],
    "purchase_order": ["po number", "vendor", "ship to", "quantity", "unit price", "delivery"],
}


class DocumentIntelligenceService:
    """AI-powered document understanding using LLM + rule-based extraction."""

    def __init__(self):
        self._llm_available = bool(settings.OPENAI_API_KEY)

    def classify_document(self, text: str) -> DocumentClassification:
        """Classify document type using keyword scoring."""
        text_lower = text.lower()
        scores = {}
        for doc_type, keywords in DOCUMENT_TYPES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = score / len(keywords)

        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        if confidence < 0.1:
            best_type = "unknown"
            confidence = 0.0

        return DocumentClassification(
            document_type=best_type,
            confidence=round(confidence, 3),
        )

    def extract_entities(self, text: str) -> list[ExtractedEntity]:
        """Extract named entities using regex patterns."""
        import re
        entities = []

        patterns = {
            "email": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}\b",
            "date": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b",
            "amount": r"\b(?:USD|INR|EUR|GBP|₹|\$|€|£)?\s*[\d,]+\.?\d*\b",
            "invoice_number": r"\b(?:INV|INVOICE|BILL)[-\s]?[A-Z0-9]{4,15}\b",
            "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            "gst": r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b",
        }

        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_type=entity_type,
                    value=match.group(),
                    confidence=0.85,
                    start_pos=match.start(),
                    end_pos=match.end(),
                ))

        return entities

    async def analyze_with_llm(self, text: str, doc_type: str) -> dict[str, Any]:
        """Use LLM to extract structured fields from document."""
        if not self._llm_available:
            return {"error": "LLM not configured", "fields": {}}

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompts = {
            "invoice": "Extract: invoice_number, date, vendor_name, customer_name, line_items (list), subtotal, tax, total, payment_terms, due_date",
            "contract": "Extract: parties (list), effective_date, expiry_date, governing_law, key_obligations (list), termination_clauses",
            "medical_report": "Extract: patient_name, patient_id, date, doctor_name, diagnosis, medications (list), icd_codes (list)",
            "bank_statement": "Extract: account_number, account_holder, period, opening_balance, closing_balance, transactions (list with date/description/amount)",
        }

        prompt = prompts.get(doc_type, "Extract all key fields as JSON")
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"You are a document extraction expert. {prompt}. Return valid JSON only."},
                {"role": "user", "content": text[:4000]},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content)

    async def process(self, text: str) -> DocumentIntelligenceResult:
        """Full document intelligence pipeline."""
        classification = self.classify_document(text)
        entities = self.extract_entities(text)

        extracted_fields = {}
        if self._llm_available:
            extracted_fields = await self.analyze_with_llm(text, classification.document_type)

        return DocumentIntelligenceResult(
            classification=classification,
            entities=entities,
            extracted_fields=extracted_fields,
            confidence_score=classification.confidence,
            raw_text=text[:500],
        )
