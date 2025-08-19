import requests
from urllib.parse import urlencode
import pdfplumber
import re
from rake_nltk import Rake
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from textstat import flesch_kincaid_grade
import logging

logger = logging.getLogger(__name__)

def extract_pdf_metadata(pdf_path):
    logger.debug(f"Extracting metadata from PDF: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            sections = []
            section_headers = ['abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']
            for page in pdf.pages:
                page_text = page.extract_text() or ''
                text += page_text + '\n'
                for header in section_headers:
                    if re.search(rf'(?i)^{header}\s*(?:\n|$)', page_text):
                        sections.append(header.capitalize())
            clean_text = ' '.join(text.split())
            if not clean_text:
                logger.warning("No text extracted from PDF")
                return {
                    'abstract': 'Unknown',
                    'keywords': ['Unknown'],
                    'sections': ['None'],
                    'readability_score': 'Unknown',
                    'figures_count': 0,
                    'tables_count': 0,
                    'references_count': 0,
                    'wordcloud_path': None
                }
            # RAKE keywords
            rake = Rake()
            rake.extract_keywords_from_text(clean_text)
            keywords = rake.get_ranked_phrases()[:5]
            logger.debug(f"RAKE keywords: {keywords}")
            # Readability score
            readability = flesch_kincaid_grade(clean_text)
            logger.debug(f"Readability score: {readability}")
            # Counts
            figures = len(re.findall(r'(?i)figure\s*\d+', text))
            tables = len(re.findall(r'(?i)table\s*\d+', text))
            references = len(re.findall(r'\[\d+\]', text))
            # Word cloud
            wordcloud_path = None
            try:
                wordcloud = WordCloud(width=400, height=200, background_color='white').generate(clean_text)
                wordcloud_filename = f"wordcloud_{os.path.basename(pdf_path).replace('.pdf', '')}.png"
                wordcloud_path = os.path.join('static', wordcloud_filename)
                os.makedirs('static', exist_ok=True)
                wordcloud.to_file(wordcloud_path)
                logger.debug(f"Word cloud saved to: {wordcloud_path}")
            except Exception as e:
                logger.error(f"Failed to generate word cloud: {e}")
            return {
                'abstract': re.search(r'(?i)abstract\s*[:\n](.*?)(?=\n\s*(introduction|methods|keywords|\Z))', text, re.DOTALL).group(1).strip() if re.search(r'(?i)abstract\s*[:\n]', text) else 'Unknown',
                'keywords': keywords if keywords else ['Unknown'],
                'sections': sections if sections else ['None'],
                'readability_score': round(readability, 1) if readability else 'Unknown',
                'figures_count': figures,
                'tables_count': tables,
                'references_count': references,
                'wordcloud_path': wordcloud_path
            }
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
        return {
            'abstract': 'Unknown',
            'keywords': ['Unknown'],
            'sections': ['None'],
            'readability_score': 'Unknown',
            'figures_count': 0,
            'tables_count': 0,
            'references_count': 0,
            'wordcloud_path': None
        }

def fetch_metadata(doi, pdf_path):
    logger.debug(f"Fetching metadata for DOI: {doi}")
    doi = doi.strip().rstrip('.')
    pdf_metadata = extract_pdf_metadata(pdf_path)
    try:
        params = {'email': 'sundar_gv@yahoo.com'}
        unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?{urlencode(params)}"
        logger.debug(f"Unpaywall URL: {unpaywall_url}")
        headers = {'User-Agent': 'PDFAnalyzer/1.0 (mailto:sundar_gv@yahoo.com)'}
        response = requests.get(unpaywall_url, headers=headers, timeout=10)
        logger.debug(f"Unpaywall response status: {response.status_code}")
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
            'abstract': data.get('abstract', pdf_metadata['abstract']),
            'keywords': pdf_metadata['keywords'],
            'publisher': data.get('publisher', 'Unknown'),
            'publication_date': data.get('published_date', 'Unknown'),
            'journal': data.get('journal_name', 'Unknown'),
            'doi': doi,
            'open_access': data.get('is_oa', False),
            'figures_count': pdf_metadata['figures_count'],
            'tables_count': pdf_metadata['tables_count'],
            'references_count': pdf_metadata['references_count'],
            'sections': pdf_metadata['sections'],
            'readability_score': pdf_metadata['readability_score'],
            'wordcloud_path': pdf_metadata['wordcloud_path'],
            'citation_count': data.get('cited_by_count', 0)
        }
        logger.debug(f"Unpaywall metadata: {metadata}")
        return metadata
    except requests.HTTPError as e:
        logger.warning(f"Unpaywall HTTP error: {e}, trying CrossRef...")
        try:
            crossref_url = f"https://api.crossref.org/works/{doi}"
            logger.debug(f"CrossRef URL: {crossref_url}")
            headers = {'User-Agent': 'PDFAnalyzer/1.0 (mailto:sundar_gv@yahoo.com)'}
            response = requests.get(crossref_url, headers=headers, timeout=10)
            logger.debug(f"CrossRef response status: {response.status_code}")
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
                'keywords': pdf_metadata['keywords'],
                'publisher': data.get('publisher', 'Unknown'),
                'publication_date': data.get('published', {}).get('date-parts', [[None]])[0][0] or 'Unknown',
                'journal': data.get('container-title', ['Unknown'])[0] or 'Unknown',
                'doi': doi,
                'open_access': data.get('is-referenced-by-count', 0) > 0,
                'figures_count': pdf_metadata['figures_count'],
                'tables_count': pdf_metadata['tables_count'],
                'references_count': pdf_metadata['references_count'],
                'sections': pdf_metadata['sections'],
                'readability_score': pdf_metadata['readability_score'],
                'wordcloud_path': pdf_metadata['wordcloud_path'],
                'citation_count': data.get('is-referenced-by-count', 0)
            }
            logger.debug(f"CrossRef metadata: {metadata}")
            return metadata
        except requests.HTTPError as e:
            logger.error(f"CrossRef HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"CrossRef general error: {e}")
            return None
    except Exception as e:
        logger.error(f"Unpaywall general error: {e}")
        return None