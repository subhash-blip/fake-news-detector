from flask import Flask, request, render_template
from textblob import TextBlob
import nltk
import requests
from bs4 import BeautifulSoup
import validators

app = Flask(__name__)

# Initialize NLP resources
nltk.download('punkt', quiet=True)

def extract_text_from_url(url):
    """Simplified URL content extractor without newspaper3k"""
    try:
        if not validators.url(url):
            return ""
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()
            
        return ' '.join(p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip())
    except Exception as e:
        print(f"URL extraction error: {e}")
        return ""

def analyze_credibility(text):
    """Analyze text credibility using TextBlob"""
    if not text.strip():
        return 0.5  # Neutral score for empty text
    
    analysis = TextBlob(text)
    # Calculate score (0-1 range)
    score = 1 - (abs(analysis.sentiment.polarity) * 0.6 + analysis.sentiment.subjectivity * 0.4)
    return max(0.1, min(0.9, score))  # Keep within 10%-90% range

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    analysis_text = ""
    score = 0.5  # Default neutral score
    
    if 'url' in request.form and request.form['url']:
        # URL analysis mode
        url = request.form['url']
        analysis_text = extract_text_from_url(url)
        if analysis_text:
            score = analyze_credibility(analysis_text)
            return render_template('result.html', 
                               score=f"{score:.0%}",
                               source=f"URL: {url}",
                               text=analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text)
        else:
            return render_template('error.html', message="Invalid URL or couldn't extract content")
    
    elif 'text' in request.form and request.form['text']:
        # Direct text analysis mode
        analysis_text = request.form['text']
        score = analyze_credibility(analysis_text)
        return render_template('result.html',
                           score=f"{score:.0%}",
                           source="Text Input",
                           text=analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text)
    
    return render_template('error.html', message="No input provided")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)