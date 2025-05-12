from flask import Flask, request, render_template
from textblob import TextBlob
import nltk
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib3.exceptions import HTTPError

app = Flask(__name__)

# Initialize NLP resources
nltk.download('punkt', quiet=True)

def is_valid_url(url):
    """Basic URL validation without external dependencies"""
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except:
        return False

def extract_text_from_url(url):
    """Robust URL content extractor with error handling"""
    try:
        if not is_valid_url(url):
            return None
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml'
        }
        
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True,
            verify=True
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
            element.decompose()
            
        # Get clean text from paragraphs
        text = ' '.join(
            p.get_text().strip() 
            for p in soup.find_all('p') 
            if p.get_text().strip()
        )
        
        return text if text else None
        
    except (HTTPError, requests.exceptions.RequestException) as e:
        print(f"URL Error: {str(e)}")
        return None
    except Exception as e:
        print(f"Processing Error: {str(e)}")
        return None

def analyze_credibility(text):
    """Enhanced text analysis with safety checks"""
    if not text or not isinstance(text, str) or len(text.strip()) < 20:
        return 0.5  # Neutral for short/invalid text
    
    try:
        analysis = TextBlob(text)
        # Weighted score calculation
        score = 1 - (
            0.6 * abs(analysis.sentiment.polarity) + 
            0.4 * analysis.sentiment.subjectivity
        )
        return max(0.1, min(0.9, score))  # Keep within 10%-90% range
    except:
        return 0.5  # Fallback neutral score

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'url' in request.form and request.form['url']:
        # URL analysis path
        url = request.form['url'].strip()
        text = extract_text_from_url(url)
        
        if text:
            score = analyze_credibility(text)
            return render_template(
                'result.html',
                score=f"{score:.0%}",
                source=f"URL: {url}",
                text=text[:500] + "..." if len(text) > 500 else text
            )
        return render_template(
            'error.html',
            message="Could not analyze that URL. Please try another."
        )
    
    elif 'text' in request.form and request.form['text']:
        # Direct text analysis path
        text = request.form['text'].strip()
        if len(text) < 20:
            return render_template(
                'error.html',
                message="Please enter at least 20 characters for analysis"
            )
            
        score = analyze_credibility(text)
        return render_template(
            'result.html',
            score=f"{score:.0%}",
            source="Text Input",
            text=text[:500] + "..." if len(text) > 500 else text
        )
    
    return render_template(
        'error.html',
        message="No input provided. Please enter text or a URL."
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)