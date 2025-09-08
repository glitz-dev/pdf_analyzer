
---
title : pdf analyzer
sdk: docker
app_file: app.py
pinned: false
---

# PDF Analyzer
This Flask-based web application analyzes PDF articles by extracting metadata (Title, Authors, Affiliations, Abstract, Keywords, Publication Date, Journal, DOI, Publisher, Open Access Status, Figures & Tables Count, Reference Count), generating summaries using a transformer model, and storing articles in an accordion-style collection. It uses the Unpaywall API (with CrossRef fallback) for metadata and supports uploading PDFs or URLs.

This README provides instructions to set up the project locally, push to GitHub, deploy on PythonAnywhere, and share a public URL (e.g., `gadepallivs.pythonanywhere.com`) with testers. Testers can access existing articles or upload new ones without any setup.

## Project Structure
```
pdf_analyzer/
├── app.py                  # Flask app with routes
├── pdf_processor.py        # Extracts DOI and text from PDFs
├── metadata_fetcher.py     # Fetches metadata from Unpaywall/CrossRef and PDFs
├── summarizer.py           # Generates summaries using t5-small
├── templates/
│   └── index.html          # Frontend with upload form and accordion
├── static/
│   └── styles.css          # CSS for styling
├── uploads/                # Stores uploaded PDFs
├── articles.json           # Datastore for article metadata and summaries
└── README.md               # This file
```

## Prerequisites
- Python 3.8+ (tested with 3.8, adjust as needed)
- Git
- PythonAnywhere account (free tier, e.g., username: `gadepallivs`)
- GitHub account (repository: `github.com/gadepallivs/pdf_analyzer`)
- Internet access for API calls (Unpaywall, CrossRef) and PDF downloads

## Local Setup

### 1. Clone the Repository
Clone the project from GitHub:
```bash
git clone https://github.com/gadepallivs/pdf_analyzer.git
cd pdf_analyzer
```
For a private repository:
- Generate an SSH key:
  ```bash
  ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
  ```
  Press Enter for defaults (no passphrase).
- Copy the public key:
  ```bash
  cat ~/.ssh/id_rsa.pub
  ```
- Add to GitHub:
  - Go to GitHub → Settings → SSH and GPG keys → New SSH key.
  - Paste the key and save.
- Clone with SSH:
  ```bash
  git clone git@github.com:gadepallivs/pdf_analyzer.git
  ```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows
```

### 3. Install Dependencies
```bash
pip install flask pypdf2 pdfplumber requests transformers torch
```
- Dependencies: `flask` (web framework), `pypdf2` and `pdfplumber` (PDF processing), `requests` (API calls), `transformers` and `torch` (summarization with `t5-small`).

### 4. Initialize Files
- Create `uploads/` folder:
  ```bash
  mkdir uploads
  ```
- Create `articles.json`:
  ```bash
  echo '[]' > articles.json
  ```

### 5. Run Locally
```bash
python app.py
```
- Access at `http://127.0.0.1:5000`.
- Test with a PDF (e.g., DOI `10.1161/CIRCULATIONAHA.110.972828`) or URL (e.g., `https://www.ahajournals.org/doi/pdf/10.1161/CIRCULATIONAHA.110.972828`).
- Verify: Upload form loads, metadata displays, summary generates, and articles appear in the accordion.

## GitHub Setup and Push

### 1. Initialize Local Repository (If Not Cloned)
If starting from scratch:
```bash
cd /path/to/pdf_analyzer
git init
git add .
git commit -m "Initial commit"
```

### 2. Link to GitHub
```bash
git remote add origin https://github.com/gadepallivs/pdf_analyzer.git
```

### 3. Resolve Divergent Branches
If you get errors like:
```
! [rejected] main -> main (fetch first)
error: failed to push some refs to 'github.com:gadepallivs/pdf_analyzer.git'
```
Or:
```
fatal: Need to specify how to reconcile divergent branches.
```
This occurs because the GitHub repository has a `README.md` (from initialization) not present locally.

#### Merge Remote and Local Changes
```bash
git pull origin main --allow-unrelated-histories
```
- Resolve conflicts (e.g., in `README.md`) by editing files in a text editor (keep both versions if needed).
- Then:
  ```bash
  git add .
  git commit -m "Merge remote README with local changes"
  ```

#### Alternative: Overwrite Remote
If you don’t need the remote `README.md`:
```bash
git push origin main --force
```
**Warning**: This deletes remote files (e.g., `README.md`).

### 4. Push to GitHub
```bash
git push origin main
```
- If prompted, use your GitHub username and a personal access token (PAT):
  - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token.
  - Select `repo` scope, generate, and use the token as the password.
- Verify on `github.com/gadepallivs/pdf_analyzer` that all files are present.

## Deploy to PythonAnywhere

### 1. Log in to PythonAnywhere
- Go to https://www.pythonanywhere.com, log in (e.g., username: `gadepallivs`).

### 2. Clone the Repository
- Open a **Bash console** (Consoles tab → New console → Bash).
- Clone:
  ```bash
  git clone https://github.com/gadepallivs/pdf_analyzer.git /home/gadepallivs/pdf_analyzer
  ```
- For a private repository, use SSH (see **Local Setup** for SSH key setup).

### 3. Create a Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.8 pdf_analyzer_venv
```
- Adjust Python version if needed (e.g., `/usr/bin/python3.10`).

### 4. Install Dependencies
```bash
pip install flask pypdf2 pdfplumber requests transformers torch
```

### 5. Initialize Files
- Create `articles.json`:
  ```bash
  echo '[]' > /home/gadepallivs/pdf_analyzer/articles.json
  ```
- Create `uploads/`:
  ```bash
  mkdir /home/gadepallivs/pdf_analyzer/uploads
  ```

### 6. Configure the Web App
- Go to **Web** tab → “Add a new web app” → Manual configuration → Python 3.8.
- Set domain: `gadepallivs.pythonanywhere.com`.
- **Code** section:
  - **Source code**: `/home/gadepallivs/pdf_analyzer`.
  - **Working directory**: `/home/gadepallivs/pdf_analyzer`.
- **Virtualenv** section:
  - Enter `pdf_analyzer_venv` (auto-completes to `/home/gadepallivs/.virtualenvs/pdf_analyzer_venv`).
- Edit WSGI file (`/var/www/gadepallivs_pythonanywhere_com_wsgi.py`):
  ```python
  import sys
  import os

  path = '/home/gadepallivs/pdf_analyzer'
  if path not in sys.path:
      sys.path.append(path)

  from app import app as application
  ```
- **Static files** section:
  - Add:
    - **URL**: `/static/`
    - **Path**: `/home/gadepallivs/pdf_analyzer/static`
- Click “Reload”.

### 7. Test the App
- Visit `http://gadepallivs.pythonanywhere.com`.
- Verify:
  - Interface loads with upload form and accordion (shows articles from `articles.json`, e.g., DOI `10.1161/CIRCULATIONAHA.110.972828`).
  - Upload a PDF/URL, check metadata (Title, Authors, Affiliations, etc.), summary, and “Add to Collection” button.
- Check **Error log** in **Web** tab if issues arise.

### 8. Update Code
To update after local changes:
```bash
git add .
git commit -m "Update app"
git push origin main
```
On PythonAnywhere:
```bash
workon pdf_analyzer_venv
cd /home/gadepallivs/pdf_analyzer
git pull origin main
```
Reload web app (**Web** tab → “Reload”).

### 9. Automate Updates with Webhooks (Optional)
- Install GitPython:
  ```bash
  workon pdf_analyzer_venv
  pip install GitPython
  ```
- Add webhook route to `app.py` (before `if __name__ == '__main__':`):
  ```python
  from git import Repo
  from flask import request

  @app.route('/update_server', methods=['POST'])
  def webhook():
      if request.method == 'POST':
          repo = Repo('/home/gadepallivs/pdf_analyzer')
          origin = repo.remotes.origin
          origin.pull()
          return 'Updated PythonAnywhere successfully', 200
      return 'Wrong event type', 400
  ```
- Add GitHub webhook:
  - GitHub → `github.com/gadepallivs/pdf_analyzer` → Settings → Webhooks → Add webhook.
  - **Payload URL**: `http://gadepallivs.pythonanywhere.com/update_server`.
  - **Content type**: `application/json`.
  - **Events**: “Just the push event”.
  - Click “Add webhook”.
- Reload web app (**Web** tab → “Reload”).

### 10. Share with Testers
- Share `http://gadepallivs.pythonanywhere.com`.
- Testers can:
  - View articles in `articles.json` (e.g., DOI `10.1161/CIRCULATIONAHA.110.972828`).
  - Upload PDFs/URLs, saving to `/home/gadepallivs/pdf_analyzer/uploads/` and updating `articles.json`.
  - No downloads or setup needed—just a browser.
- If public, testers can view code at `github.com/gadepallivs/pdf_analyzer`.

## Alternative: Local Testing with ngrok
To share locally without PythonAnywhere:
1. **Install ngrok**:
   - Download from https://ngrok.com/download (free tier).
   - Unzip and move `ngrok` to `/usr/local/bin` (macOS/Linux) or add to PATH (Windows).
   - (Optional) Sign up at https://ngrok.com, get authtoken, and run:
     ```bash
     ngrok config add-authtoken <your-authtoken>
     ```
2. **Run Flask App**:
   ```bash
   source venv/bin/activate  # macOS/Linux
   .\venv\Scripts\activate   # Windows
   python app.py
   ```
3. **Start ngrok**:
   ```bash
   ngrok http 5000
   ```
   - Copy the public URL (e.g., `https://abcd1234.ngrok-free.app`).
   - Share with testers (works only while your machine is running).
4. **Test**:
   - Testers access the URL, view articles, and upload PDFs/URLs.
   - Free ngrok URLs change per session (2-hour limit).

## Using the Unpaywall API
- **Email**: Uses `sundar_gv@yahoo.com` in `metadata_fetcher.py` for API requests.
- **URL Format**: `https://api.unpaywall.org/v2/{DOI}?email=sundar_gv%40yahoo.com`.
- **Test API**:
  ```bash
  curl "https://api.unpaywall.org/v2/10.1161/CIRCULATIONAHA.110.972828?email=sundar_gv@yahoo.com"
  ```
  - Expected: Metadata like Title, Authors, Publisher, etc.
- **Fallback**: Uses CrossRef if Unpaywall fails (404).
- **PDF Extraction**: Fallback for Abstract, Keywords, Figures, Tables, References if APIs lack data.

## Troubleshooting

### Git Push Issues
- **Divergent Branches**:
  ```bash
  git pull origin main --allow-unrelated-histories
  git add .
  git commit -m "Resolve conflicts"
  git push origin main
  ```
- **Force Push** (if remote files unneeded):
  ```bash
  git push origin main --force
  ```
- **Fresh Clone**:
  ```bash
  git clone https://github.com/gadepallivs/pdf_analyzer.git temp
  cd temp
  cp -r /path/to/pdf_analyzer/* .
  git add .
  git commit -m "Add project files"
  git push origin main
  ```

### PythonAnywhere Issues
- **App Not Loading**:
  - Check **Error log** in **Web** tab.
  - Verify WSGI path: `/home/gadepallivs/pdf_analyzer`.
  - Reinstall dependencies:
    ```bash
    workon pdf_analyzer_venv
    pip install flask pypdf2 pdfplumber requests transformers torch
    ```
- **File Permissions**:
  ```bash
  chmod -R u+rw /home/gadepallivs/pdf_analyzer/uploads /home/gadepallivs/pdf_analyzer/articles.json
  ```

### Summarization Slow
- Reduce `chunk_size` to 200 or limit to 1 chunk in `summarizer.py`:
  ```python
  chunk_size = 200
  chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)][:1]
  ```
- Test:
  ```python
  from summarizer import summarize_text
  text = "Test sentence for summarization."
  summary, status = summarize_text(text)
  print(summary, status)
  ```

### Unpaywall 404
- Ensure DOI has no trailing period:
  ```bash
  curl "https://api.unpaywall.org/v2/10.1161/CIRCULATIONAHA.110.972828?email=sundar_gv@yahoo.com"
  ```
- Check logs in `metadata_fetcher.py`.

## Notes
- **PythonAnywhere Free Tier**: 512 MB storage. Monitor `uploads/` size.
- **Summarization**: Uses `t5-small` for speed. For faster results, use a GPU with `torch` CUDA:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```
- **Security**: Use a private GitHub repository with SSH for sensitive code.
- **Testing**: Test with DOI `10.1161/CIRCULATIONAHA.110.972828` to verify metadata, summary, and accordion.

---

### Next Steps
1. Save this as `README.md` in your `pdf_analyzer/` folder.
2. Push to GitHub:
   ```bash
   git add README.md
   git commit -m "Add README with setup instructions"
   git push origin main
   ```
3. Pull on PythonAnywhere:
   ```bash
   workon pdf_analyzer_venv
   cd /home/gadepallivs/pdf_analyzer
   git pull origin main
   ```
   Reload the web app (**Web** tab → “Reload”).
4. Share `http://gadepallivs.pythonanywhere.com` with testers.