# app.py
from flask import Flask, jsonify, request
import pandas as pd  # Example: external lib
import initial_stock_list
import momentum_stocks

app = Flask(__name__)

@app.route('/get_stocks', methods=['POST'])
def process():
    try:
        req_data = request.get_json()
        stock_count = req_data.get('stock_count',15)
        data = initial_stock_list.get_initial_stock_list(stock_count)
        summary = data.to_dict()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_momentum_stocks', methods=['POST'])
def get_momentum_stocks():
    try:
        req_data = request.get_json()
        initial_stock_list = req_data[0]['stocks']
        momentum_list = momentum_stocks.run_momentum_stocks(initial_stock_list)
        summary = pd.DataFrame(momentum_list)
        summary = summary.to_dict(orient='records')
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
