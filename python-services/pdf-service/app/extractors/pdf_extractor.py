"""
PDF Extraction Engine

Uses pdfplumber for digital PDFs and Tesseract OCR for scanned PDFs.
Extracts text, tables, images, headers, footers, and structured fields.
"""
import io
from dataclasses import dataclass, field
from typing import Any
import structlog

logger = structlog.get_logger()


@dataclass
class PDFPage:
    page_number: int
    text: str
    tables: list[list[list[str]]]
    images: list[dict]
    width: float
    height: float


@dataclass
class PDFExtractionResult:
    pages: list[PDFPage]
    full_text: str
    all_tables: list[list[list[str]]]
    metadata: dict[str, Any]
    is_scanned: bool
    page_count: int
    extraction_method: str  # "pdfplumber" | "ocr" | "pymupdf"


class PDFExtractor:
    """Multi-strategy PDF extraction with automatic fallback to OCR."""

    def extract(self, pdf_bytes: bytes) -> PDFExtractionResult:
        """Extract content from PDF bytes."""
        # Try pdfplumber first (best for digital PDFs)
        result = self._extract_with_pdfplumber(pdf_bytes)

        # If minimal text extracted, try OCR (scanned PDF)
        if len(result.full_text.strip()) < 50:
            logger.info("pdf_fallback_to_ocr", text_length=len(result.full_text))
            result = self._extract_with_ocr(pdf_bytes)

        return result

    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> PDFExtractionResult:
        import pdfplumber

        pages = []
        all_tables = []
        full_text_parts = []
        metadata = {}

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            metadata = pdf.metadata or {}
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                full_text_parts.append(text)
                all_tables.extend(tables)
                pages.append(PDFPage(
                    page_number=page_num,
                    text=text,
                    tables=tables,
                    images=[],
                    width=page.width,
                    height=page.height,
                ))

        return PDFExtractionResult(
            pages=pages,
            full_text="\n".join(full_text_parts),
            all_tables=all_tables,
            metadata=metadata,
            is_scanned=False,
            page_count=len(pages),
            extraction_method="pdfplumber",
        )

    def _extract_with_ocr(self, pdf_bytes: bytes) -> PDFExtractionResult:
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            from app.core.config import settings

            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            images = convert_from_bytes(pdf_bytes, dpi=300)

            pages = []
            full_text_parts = []

            for page_num, img in enumerate(images, 1):
                text = pytesseract.image_to_string(img, lang=settings.OCR_LANGUAGE)
                full_text_parts.append(text)
                pages.append(PDFPage(
                    page_number=page_num,
                    text=text,
                    tables=[],
                    images=[],
                    width=img.width,
                    height=img.height,
                ))

            return PDFExtractionResult(
                pages=pages,
                full_text="\n".join(full_text_parts),
                all_tables=[],
                metadata={},
                is_scanned=True,
                page_count=len(pages),
                extraction_method="ocr",
            )
        except Exception as e:
            logger.error("ocr_extraction_failed", error=str(e))
            return PDFExtractionResult(
                pages=[], full_text="", all_tables={}, metadata={},
                is_scanned=True, page_count=0, extraction_method="failed",
            )

    def tables_to_records(self, tables: list[list[list[str]]]) -> list[dict[str, Any]]:
        """Convert extracted tables to list of dicts."""
        records = []
        for table in tables:
            if not table or len(table) < 2:
                continue
            headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(table[0])]
            for row in table[1:]:
                if any(cell for cell in row):
                    record = {headers[i]: (row[i].strip() if i < len(row) and row[i] else None)
                              for i in range(len(headers))}
                    records.append(record)
        return records
