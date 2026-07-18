"""AI Service API endpoints."""
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.document_intelligence import DocumentIntelligenceService
from app.services.rag_service import RAGService
from app.services.anomaly_detection import AnomalyDetectionService
from app.services.auto_mapping import AutoMappingService

router = APIRouter()


class DocumentAnalysisRequest(BaseModel):
    text: str
    document_type: str | None = None


class RAGIndexRequest(BaseModel):
    documents: list[str]
    metadatas: list[dict[str, Any]]
    collection_name: str = "platform_docs"


class RAGQueryRequest(BaseModel):
    question: str
    collection_name: str = "platform_docs"
    n_results: int = 5


class AnomalyDetectionRequest(BaseModel):
    records: list[dict[str, Any]]
    numeric_fields: list[str] = []
    detect_fraud: bool = False


class AutoMappingRequest(BaseModel):
    source_fields: list[str]
    target_schema: dict[str, str]


@router.post("/document/analyze")
async def analyze_document(request: DocumentAnalysisRequest):
    """Classify and extract entities from a document."""
    service = DocumentIntelligenceService()
    result = await service.process(request.text)
    return {
        "classification": {
            "document_type": result.classification.document_type,
            "confidence": result.classification.confidence,
        },
        "entities": [
            {"type": e.entity_type, "value": e.value, "confidence": e.confidence}
            for e in result.entities
        ],
        "extracted_fields": result.extracted_fields,
        "confidence_score": result.confidence_score,
    }


@router.post("/rag/index")
async def index_documents(request: RAGIndexRequest):
    """Index documents into the vector database for RAG."""
    service = RAGService()
    count = await service.index_documents(
        documents=request.documents,
        metadatas=request.metadatas,
        collection_name=request.collection_name,
    )
    return {"indexed": count, "collection": request.collection_name}


@router.post("/rag/query")
async def query_rag(request: RAGQueryRequest):
    """Query the RAG pipeline with a natural language question."""
    service = RAGService()
    result = await service.query(
        question=request.question,
        collection_name=request.collection_name,
        n_results=request.n_results,
    )
    return result


@router.post("/anomaly/detect")
async def detect_anomalies(request: AnomalyDetectionRequest):
    """Detect anomalies and fraud indicators in a dataset."""
    service = AnomalyDetectionService()
    anomalies = service.detect_numeric_anomalies(request.records, request.numeric_fields)
    fraud = []
    if request.detect_fraud:
        fraud = service.detect_fraud_indicators(request.records)
    return {
        "anomalies": [a.__dict__ for a in anomalies],
        "fraud_indicators": [f.__dict__ for f in fraud],
        "total_anomalies": len(anomalies),
        "total_fraud_indicators": len(fraud),
    }


@router.post("/mapping/auto")
async def auto_map_fields(request: AutoMappingRequest):
    """Automatically map source fields to target schema using AI."""
    service = AutoMappingService()
    mapping = await service.map_fields(request.source_fields, request.target_schema)
    return {"mapping": mapping}
