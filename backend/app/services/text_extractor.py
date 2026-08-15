import io
import logging
from typing import Optional

logger = logging.getLogger("flowpilot.text_extractor")


class TextExtractor:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """Extract clean text from PDF, Markdown, TXT, or Notes files."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        if ext == "pdf":
            return TextExtractor._extract_pdf_text(file_bytes)
        else:
            # Plain text, Markdown, Notes
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")

    @staticmethod
    def _extract_pdf_text(file_bytes: bytes) -> str:
        """Extract text from PDF file bytes."""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(f"--- Page {i + 1} ---\n{page_text}")
            return "\n\n".join(extracted_pages) if extracted_pages else "Empty PDF content."
        except Exception as e:
            logger.warning(f"pypdf extraction failed, attempting fallback parser: {str(e)}")
            # Simple fallback string scanner for raw PDF stream
            raw_str = file_bytes.decode("ascii", errors="ignore")
            lines = [line.strip() for line in raw_str.split("\n") if len(line.strip()) > 20 and not line.startswith("%")]
            return "\n".join(lines[:100]) if lines else f"PDF text extraction fallback completed ({len(file_bytes)} bytes)."
