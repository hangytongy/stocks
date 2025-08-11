from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/extract_text', methods=['POST'])
def extract_text():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Please provide JSON body with 'url' field"}), 400

    url = data["url"]

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        article_text = "\n".join(p.get_text() for p in paragraphs)

        return jsonify({"article_text": article_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

