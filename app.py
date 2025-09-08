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

logger.debug("Creating upload folder")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

def save_articles(articles):
    logger.debug(f"Saving articles to {ARTICLES_FILE}")
    try:
        with open(ARTICLES_FILE, 'w') as f:
            json.dump(articles, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving articles: {e}")

def calculate_engagement_score(metadata):
    logger.debug(f"Calculating engagement score for metadata: {metadata}")
    score = 0
    abstract_len = len(metadata.get('abstract', '').split()) if metadata.get('abstract') != 'Unknown' else 0
    score += min(abstract_len / 100, 1) * 30
    keyword_count = len(metadata.get('keywords', [])) if metadata.get('keywords') != ['Unknown'] else 0
    score += min(keyword_count / 5, 1) * 20
    citation_count = metadata.get('citation_count', 0)
    score += min(citation_count / 50, 1) * 30
    score += 20 if metadata.get('open_access', False) else 0
    logger.debug(f"Engagement score components: abstract_len={abstract_len}, keywords={keyword_count}, citations={citation_count}, open_access={metadata.get('open_access', False)}, score={score}")
    return round(score, 1)

logger.debug("Functions defined")

@app.route('/')
def index():
    logger.debug("Accessing index route")
    articles = load_articles()
    logger.debug(f"Loaded articles: {articles}")
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

        logger.debug(f"Extracting DOI from {pdf_path}")
        doi = extract_doi(pdf_path)
        if not doi:
            if saved_pdf_path and os.path.exists(saved_pdf_path):
                os.remove(saved_pdf_path)
            return jsonify({'error': 'DOI not found in the PDF.'}), 400

        logger.debug(f"Fetching metadata for DOI {doi}")
        metadata = fetch_metadata(doi, pdf_path)
        if not metadata:
            if saved_pdf_path and os.path.exists(saved_pdf_path):
                os.remove(saved_pdf_path)
            return jsonify({'error': f'Failed to fetch metadata for DOI {doi}.'}), 400

        logger.debug("Extracting text for summarization")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            if saved_pdf_path and os.path.exists(saved_pdf_path):
                os.remove(saved_pdf_path)
            return jsonify({'error': 'Failed to extract text from the PDF.'}), 400

        logger.debug("Generating summary")
        summary, summary_status = summarize_text(text)

        logger.debug("Calculating engagement score")
        engagement_score = calculate_engagement_score(metadata)

        logger.debug("Storing article")
        articles = load_articles()
        article = {
            'doi': doi,
            'metadata': metadata,
            'summary': summary,
            'pdf_path': saved_pdf_path,
            'engagement_score': engagement_score
        }
        articles.append(article)
        save_articles(articles)

        logger.debug(f"Returning response: {article}")
        return jsonify({
            'metadata': metadata,
            'summary': summary,
            'summary_status': summary_status,
            'pdf_path': saved_pdf_path,
            'engagement_score': engagement_score
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

if __name__ == '__main__':
    # app.run(debug=True) avoided for implementing huggingface port
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)    
    logger.debug(f"Starting Flask app on port {port}")