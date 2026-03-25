"""PDF parser for Sequence of Operation documents.

This module provides PDF text extraction functionality with OCR support for
scanned documents. It supports multiple PDF libraries with automatic fallback:
1. PyMuPDF (fitz) - fastest and most accurate
2. pdfplumber - good for structured content
3. PyPDF2 - basic extraction, widely available

For scanned PDFs, OCR is performed using Tesseract OCR.

Install dependencies:
    pip install pymupdf pytesseract Pillow

    For Windows, also install Tesseract OCR:
    winget install UB-Mannheim.TesseractOCR
"""

import io
import os
from typing import Optional


class PDFParser:
    """Parser for extracting text from PDF documents with OCR support."""

    def __init__(self):
        self._parser_name: Optional[str] = None
        self._ocr_available: bool = False
        self._check_available_libraries()
        self._check_ocr_support()

    def _check_available_libraries(self) -> None:
        """Check which PDF library is available."""
        try:
            import fitz
            self._parser_name = "pymupdf"
            return
        except ImportError:
            pass

        try:
            import pdfplumber
            self._parser_name = "pdfplumber"
            return
        except ImportError:
            pass

        try:
            import PyPDF2
            self._parser_name = "pypdf2"
            return
        except ImportError:
            pass

        self._parser_name = None

    def _check_ocr_support(self) -> None:
        """Check if OCR support is available."""
        try:
            import pytesseract
            from PIL import Image

            # Check if Tesseract executable exists
            tesseract_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
            ]

            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self._ocr_available = True
                    return

            # Try to run tesseract to see if it's in PATH
            try:
                pytesseract.get_tesseract_version()
                self._ocr_available = True
            except Exception:
                self._ocr_available = False

        except ImportError:
            self._ocr_available = False

    @property
    def is_available(self) -> bool:
        """Check if PDF parsing is available."""
        return self._parser_name is not None

    @property
    def ocr_available(self) -> bool:
        """Check if OCR is available for scanned PDFs."""
        return self._ocr_available

    @property
    def parser_name(self) -> Optional[str]:
        """Get the name of the active PDF parser."""
        return self._parser_name

    def extract_text(self, pdf_data: bytes, use_ocr: bool = True) -> str:
        """Extract text from PDF binary data.

        Args:
            pdf_data: Raw PDF file bytes
            use_ocr: Whether to use OCR for pages with no text (scanned docs)

        Returns:
            Extracted text content

        Raises:
            RuntimeError: If no PDF library is available
            ValueError: If PDF parsing fails
        """
        if not self.is_available:
            raise RuntimeError(
                "No PDF library available. Install one of: "
                "pymupdf, pdfplumber, or pypdf2\n"
                "Run: pip install pymupdf"
            )

        if self._parser_name == "pymupdf":
            return self._extract_with_pymupdf(pdf_data, use_ocr)
        elif self._parser_name == "pdfplumber":
            return self._extract_with_pdfplumber(pdf_data)
        elif self._parser_name == "pypdf2":
            return self._extract_with_pypdf2(pdf_data)
        else:
            raise RuntimeError("No PDF parser configured")

    def _extract_with_pymupdf(self, pdf_data: bytes, use_ocr: bool = True) -> str:
        """Extract text using PyMuPDF (fitz) with OCR fallback."""
        import fitz

        text_parts = []
        pages_needing_ocr = []

        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            total_pages = len(doc)
            print(f"[PDF] Processing {total_pages} pages...")

            for page_num, page in enumerate(doc):
                page_text = page.get_text()

                if page_text.strip():
                    text_parts.append(f"# Page {page_num + 1}\n\n{page_text}")
                else:
                    pages_needing_ocr.append(page_num)

            # If we have pages needing OCR and OCR is available
            if pages_needing_ocr and use_ocr and self._ocr_available:
                print(f"[PDF] Running OCR on {len(pages_needing_ocr)} scanned pages...")

                import pytesseract
                from PIL import Image

                for page_num in pages_needing_ocr:
                    page = doc[page_num]

                    # Render page to image at higher resolution for better OCR
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)

                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # Run OCR
                    try:
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text.strip():
                            text_parts.append(f"# Page {page_num + 1}\n\n{ocr_text}")
                            print(f"[PDF] Page {page_num + 1}: OCR extracted {len(ocr_text)} chars")
                    except Exception as e:
                        print(f"[PDF] Page {page_num + 1}: OCR failed - {e}")

            elif pages_needing_ocr and use_ocr and not self._ocr_available:
                print(f"[PDF] Warning: {len(pages_needing_ocr)} pages are scanned but OCR is not available.")
                print("[PDF] Install Tesseract OCR: winget install UB-Mannheim.TesseractOCR")

        # Sort text_parts by page number
        text_parts.sort(key=lambda x: int(x.split('\n')[0].replace('# Page ', '')))

        return "\n\n".join(text_parts)

    def _extract_with_pdfplumber(self, pdf_data: bytes) -> str:
        """Extract text using pdfplumber."""
        import pdfplumber

        text_parts = []

        with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(f"# Page {page_num + 1}\n\n{page_text}")

        return "\n\n".join(text_parts)

    def _extract_with_pypdf2(self, pdf_data: bytes) -> str:
        """Extract text using PyPDF2."""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            from PyPDF2 import PdfFileReader as PdfReader

        text_parts = []

        reader = PdfReader(io.BytesIO(pdf_data))

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_parts.append(f"# Page {page_num + 1}\n\n{page_text}")

        return "\n\n".join(text_parts)

    def extract_text_from_file(self, file_path: str, use_ocr: bool = True) -> str:
        """Extract text from a PDF file path.

        Args:
            file_path: Path to the PDF file
            use_ocr: Whether to use OCR for scanned pages

        Returns:
            Extracted text content
        """
        with open(file_path, 'rb') as f:
            return self.extract_text(f.read(), use_ocr)


def get_pdf_parser() -> PDFParser:
    """Get a configured PDF parser instance."""
    return PDFParser()


def check_pdf_support() -> tuple[bool, str]:
    """Check if PDF support is available.

    Returns:
        Tuple of (is_available, message)
    """
    parser = PDFParser()
    if parser.is_available:
        ocr_status = "with OCR" if parser.ocr_available else "without OCR (scanned PDFs won't work)"
        return True, f"PDF support enabled using {parser.parser_name} {ocr_status}"
    else:
        return False, (
            "PDF support not available. Install a PDF library:\n"
            "  pip install pymupdf    (recommended)\n"
            "  pip install pdfplumber\n"
            "  pip install pypdf2"
        )

