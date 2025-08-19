import requests
from urllib.parse import urlencode
import pdfplumber
import re

def extract_pdf_metadata(pdf_path):
    """Extract additional metadata (abstract, keywords, figures, tables, references) from PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
            
            # Extract Abstract
            abstract_match = re.search(r'(?i)abstract\s*[:\n](.*?)(?=\n\s*(introduction|methods|keywords|\Z))', text, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else 'Unknown'
            
            # Extract Keywords
            keywords_match = re.search(r'(?i)keywords\s*[:\n](.*?)(?=\n\s*(introduction|methods|abstract|\Z))', text, re.DOTALL)
            keywords = keywords_match.group(1).strip().split(',') if keywords_match else ['Unknown']
            keywords = [kw.strip() for kw in keywords]
            
            # Count Figures and Tables
            figures = len(re.findall(r'(?i)figure\s*\d+', text))
            tables = len(re.findall(r'(?i)table\s*\d+', text))
            
            # Count References
            references = len(re.findall(r'\[\d+\]', text))  # Simple heuristic for numbered references
            
            return {
                'abstract': abstract,
                'keywords': keywords,
                'figures_count': figures,
                'tables_count': tables,
                'references_count': references
            }
    except Exception as e:
        print(f"Error extracting PDF metadata: {e}")
        return {
            'abstract': 'Unknown',
            'keywords': ['Unknown'],
            'figures_count': 0,
            'tables_count': 0,
            'references_count': 0
        }

def fetch_metadata(doi, pdf_path):
    """Fetch metadata using Unpaywall API with CrossRef as fallback, and PDF for additional fields."""
    doi = doi.strip().rstrip('.')
    print(f"Cleaned DOI: {doi}")

    # Extract PDF-specific metadata
    pdf_metadata = extract_pdf_metadata(pdf_path)

    try:
        # Try Unpaywall
        params = {'email': 'sundar_gv@yahoo.com'}
        unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?{urlencode(params)}"
        print(f"Constructed Unpaywall URL: {unpaywall_url}")
        headers = {'User-Agent': 'PDFAnalyzer/1.0 (mailto:sundar_gv@yahoo.com)'}
        response = requests.get(unpaywall_url, headers=headers, timeout=10)
        print(f"Unpaywall response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        affiliations = [
            author.get('raw_affiliation_strings', ['Unknown'])[0]
            for author in data.get('z_authors', [])
        ]
        metadata = {
            'title': data.get('title', 'Unknown'),
            'authors': ', '.join(
                author.get('raw_author_name', '') for author in data.get('z_authors', [])
            ) or 'Unknown',
            'affiliations': affiliations if any(aff != 'Unknown' for aff in affiliations) else ['Unknown'],
            'abstract': data.get('abstract', pdf_metadata['abstract']),  # Fallback to PDF
            'keywords': data.get('keywords', pdf_metadata['keywords']),  # Fallback to PDF
            'publisher': data.get('publisher', 'Unknown'),
            'publication_date': data.get('published_date', 'Unknown'),
            'journal': data.get('journal_name', 'Unknown'),
            'doi': doi,
            'open_access': data.get('is_oa', False),
            'figures_count': pdf_metadata['figures_count'],
            'tables_count': pdf_metadata['tables_count'],
            'references_count': pdf_metadata['references_count']
        }
        print(f"Unpaywall metadata: {metadata}")
        return metadata

    except requests.HTTPError as e:
        print(f"Unpaywall HTTP error: {e}, trying CrossRef...")
        try:
            crossref_url = f"https://api.crossref.org/works/{doi}"
            print(f"Constructed CrossRef URL: {crossref_url}")
            headers = {'User-Agent': 'PDFAnalyzer/1.0 (mailto:sundar_gv@yahoo.com)'}
            response = requests.get(crossref_url, headers=headers, timeout=10)
            print(f"CrossRef response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()['message']
            affiliations = [
                author.get('affiliation', [{'name': 'Unknown'}])[0].get('name', 'Unknown')
                for author in data.get('author', [])
            ]
            metadata = {
                'title': data.get('title', [''])[0] or 'Unknown',
                'authors': ', '.join(
                    author.get('given', '') + ' ' + author.get('family', '')
                    for author in data.get('author', [])
                ) or 'Unknown',
                'affiliations': affiliations if any(aff != 'Unknown' for aff in affiliations) else ['Unknown'],
                'abstract': data.get('abstract', pdf_metadata['abstract']),
                'keywords': data.get('keywords', pdf_metadata['keywords']),
                'publisher': data.get('publisher', 'Unknown'),
                'publication_date': data.get('published', {}).get('date-parts', [[None]])[0][0] or 'Unknown',
                'journal': data.get('container-title', ['Unknown'])[0] or 'Unknown',
                'doi': doi,
                'open_access': data.get('is-referenced-by-count', 0) > 0,
                'figures_count': pdf_metadata['figures_count'],
                'tables_count': pdf_metadata['tables_count'],
                'references_count': pdf_metadata['references_count']
            }
            print(f"CrossRef metadata: {metadata}")
            return metadata
        except requests.HTTPError as e:
            print(f"CrossRef HTTP error: {e}")
            return None
        except Exception as e:
            print(f"CrossRef general error: {e}")
            return None
    except Exception as e:
        print(f"Unpaywall general error: {e}")
        return None