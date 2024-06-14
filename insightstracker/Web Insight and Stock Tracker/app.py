from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import string
import yfinance as yf

nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)

def extract_text_from_url(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    text = ' '.join([para.get_text() for para in paragraphs])
    return text

def extract_key_points(text, num_points=5):
    stop_words = set(stopwords.words('english') + list(string.punctuation))
    words = word_tokenize(text.lower())
    words = [word for word in words if word not in stop_words]
    
    freq_table = {}
    for word in words:
        if word in freq_table:
            freq_table[word] += 1
        else:
            freq_table[word] = 1
    
    sentences = sent_tokenize(text)
    sentence_value = {}
    for sentence in sentences:
        for word, freq in freq_table.items():
            if word in sentence.lower():
                if sentence in sentence_value:
                    sentence_value[sentence] += freq
                else:
                    sentence_value[sentence] = freq

    sorted_sentences = sorted(sentence_value.items(), key=lambda kv: kv[1], reverse=True)
    summary_sentences = [sentence for sentence, value in sorted_sentences[:num_points]]
    
    return summary_sentences

@app.route('/', methods=['GET', 'POST'])
def index():
    url = ''
    summary = []
    stock_info = {}
    if request.method == 'POST':
        url = request.form['url']
        text = extract_text_from_url(url)
        summary = extract_key_points(text, num_points=5)
        ticker = request.form['ticker']
        if ticker:
            try:
                stock = yf.Ticker(ticker)
                stock_info = {
                    'Company Name': stock.info['longName'],
                    'Current Price': stock.history(period='1d')['Close'].iloc[-1],
                    'Market Cap': stock.info['marketCap'],
                    'PE Ratio': stock.info['trailingPE'],
                    'Dividend Yield': stock.info['dividendYield']
                }
            except Exception as e:
                error_message = f"Error fetching stock information: {str(e)}"
                print(error_message)
                stock_info = {'Error': error_message}
    return render_template('index.html', url=url, summary=summary, stock_info=stock_info)

if __name__ == '__main__':
    app.run(debug=True)
