"""PDF processing API endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.extractors.pdf_extractor import PDFExtractor

router = APIRouter()


@router.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    """
    Extract text, tables, and metadata from a PDF file.
    Automatically uses OCR for scanned PDFs.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    extractor = PDFExtractor()
    result = extractor.extract(content)

    return {
        "file_name": file.filename,
        "page_count": result.page_count,
        "is_scanned": result.is_scanned,
        "extraction_method": result.extraction_method,
        "full_text": result.full_text[:5000],  # Truncate for response
        "text_length": len(result.full_text),
        "table_count": len(result.all_tables),
        "metadata": result.metadata,
        "pages": [
            {
                "page_number": p.page_number,
                "text_preview": p.text[:500],
                "table_count": len(p.tables),
            }
            for p in result.pages
        ],
    }


@router.post("/extract/tables")
async def extract_tables(file: UploadFile = File(...)):
    """Extract tables from PDF and return as structured records."""
    content = await file.read()
    extractor = PDFExtractor()
    result = extractor.extract(content)
    records = extractor.tables_to_records(result.all_tables)

    return {
        "file_name": file.filename,
        "table_count": len(result.all_tables),
        "record_count": len(records),
        "records": records,
    }
