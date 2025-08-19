import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting app.py")

from flask import Flask, request, render_template, jsonify
from pdf_processor import extract_doi, extract_text_from_pdf
from metadata_fetcher import fetch_metadata
from summarizer import summarize_text
import os
import requests
from urllib.parse import urlparse
import json

logger.debug("Imports completed")

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ARTICLES_FILE = 'articles.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
logger.debug("Creating upload folder")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load existing articles
def load_articles():
    logger.debug(f"Loading articles from {ARTICLES_FILE}")
    try:
        if os.path.exists(ARTICLES_FILE):
            with open(ARTICLES_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading articles: {e}")
        return []

# Save articles to JSON
def save_articles(articles):
    logger.debug(f"Saving articles to {ARTICLES_FILE}")
    try:
        with open(ARTICLES_FILE, 'w') as f:
            json.dump(articles, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving articles: {e}")

logger.debug("Functions defined")

@app.route('/')
def index():
    logger.debug("Accessing index route")
    articles = load_articles()
    return render_template('index.html', articles=articles)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    logger.debug("Accessing upload route")
    try:
        pdf_path = None
        saved_pdf_path = None
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if file.filename.endswith('.pdf'):
                saved_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(saved_pdf_path)
                pdf_path = saved_pdf_path
            else:
                return jsonify({'error': 'Invalid file format. Please upload a PDF.'}), 400
        elif 'url' in request.form and request.form['url']:
            url = request.form['url']
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                filename = os.path.basename(urlparse(url).path) or 'downloaded.pdf'
                saved_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(saved_pdf_path, 'wb') as f:
                    f.write(response.content)
                pdf_path = saved_pdf_path
            except requests.RequestException as e:
                return jsonify({'error': f'Failed to download PDF from URL: {str(e)}'}), 400

        if not pdf_path:
            return jsonify({'error': 'No file or URL provided.'}), 400

        # Extract DOI
        logger.debug(f"Extracting DOI from {pdf_path}")
        doi = extract_doi(pdf_path)
        if not doi:
            if saved_pdf_path and os.path.exists(saved_pdf_path):
                os.remove(saved_pdf_path)
            return jsonify({'error': 'DOI not found in the PDF.'}), 400

        # Fetch metadata
        logger.debug(f"Fetching metadata for DOI {doi}")
        metadata = fetch_metadata(doi, pdf_path)
        if not metadata:
            if saved_pdf_path and os.path.exists(saved_pdf_path):
                os.remove(saved_pdf_path)
            return jsonify({'error': f'Failed to fetch metadata for DOI {doi}.'}), 400

        # Extract text for summarization
        logger.debug("Extracting text for summarization")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            if saved_pdf_path and os.path.exists(saved_pdf_path):
                os.remove(saved_pdf_path)
            return jsonify({'error': 'Failed to extract text from the PDF.'}), 400

        # Generate summary
        logger.debug("Generating summary")
        summary, summary_status = summarize_text(text)

        # Store article
        logger.debug("Storing article")
        articles = load_articles()
        article = {
            'doi': doi,
            'metadata': metadata,
            'summary': summary,
            'pdf_path': saved_pdf_path
        }
        articles.append(article)
        save_articles(articles)

        logger.debug("Returning response")
        return jsonify({
            'metadata': metadata,
            'summary': summary,
            'summary_status': summary_status,
            'pdf_path': saved_pdf_path
        })

    except Exception as e:
        if saved_pdf_path and os.path.exists(saved_pdf_path):
            os.remove(saved_pdf_path)
        logger.error(f"Error in upload: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/add_article', methods=['POST'])
def add_article():
    logger.debug("Accessing add_article route")
    try:
        article = request.get_json()
        articles = load_articles()
        if not any(a['doi'] == article['doi'] for a in articles):
            articles.append(article)
            save_articles(articles)
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error adding article: {e}")
        return jsonify({'error': f'Failed to add article: {str(e)}'}), 500

logger.debug("Starting Flask app")
if __name__ == '__main__':
    app.run(debug=True)