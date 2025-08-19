import PyPDF2
import pdfplumber
import re

def extract_doi(pdf_path):
    """Extract DOI from PDF using text and metadata."""
    try:
        # Try extracting from text
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ''
                doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', text, re.IGNORECASE)
                if doi_match:
                    return doi_match.group(0)

        # Try extracting from metadata
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            metadata = reader.metadata
            for key, value in metadata.items():
                doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', str(value), re.IGNORECASE)
                if doi_match:
                    return doi_match.group(0)
        return None
    except Exception as e:
        print(f"Error extracting DOI: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF for summarization."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                page_text = page.extract_text() or ''
                text += page_text + '\n'
            return text.strip()
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None