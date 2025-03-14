from flask import Flask, request, render_template
from bs4 import BeautifulSoup
import requests
from collections import Counter

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form['url']
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        word_count = len(text.split())
        avg_word_length = sum(len(word) for word in text.split()) / word_count
        top_words = get_top_words(text, 10)
        return render_template('results.html', text=text, word_count=word_count, avg_word_length=avg_word_length, top_words=top_words)
    return render_template('index.html')

def get_top_words(text, n):
    words = text.lower().split()
    word_counts = Counter(words)
    return word_counts.most_common(n)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
