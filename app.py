from flask import Flask, request, render_template
from textblob import TextBlob
from newspaper import Article
import nltk

nltk.download('punkt')  # Required for article parsing

app = Flask(__name__)

def analyze_credibility(text):
    blob = TextBlob(text)
    # Simple scoring: less subjective + neutral polarity = more credible
    subjectivity_penalty = blob.sentiment.subjectivity * 0.6  # 60% weight
    polarity_penalty = abs(blob.sentiment.polarity) * 0.4    # 40% weight
    return max(0, 1 - (subjectivity_penalty + polarity_penalty))  # 0-1 scale

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'url' in request.form:
        # URL analysis
        article = Article(request.form['url'])
        article.download()
        article.parse()
        article.nlp()
        score = analyze_credibility(article.text)
        return render_template('result.html', 
                           text=article.summary,
                           score=score,
                           title=article.title)
    else:
        # Direct text analysis
        text = request.form['text']
        score = analyze_credibility(text)
        return render_template('result.html', 
                           text=text,
                           score=score,
                           title="Custom Text Analysis")

if __name__ == '__main__':
    app.run(debug=True)