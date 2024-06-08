from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf
import random
import requests
import json
import os
from dotenv import load_dotenv
import csv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY")
csv_file = 'nifty500.csv'  # Update this with the path to your CSV file
column_index = 2  # Index 2 corresponds to the third column (0-based indexing)

    
def read_csv_column(csv_file, column_index):
    data = []
    with open(csv_file, newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) > column_index:
                data.append(row[column_index]+ ".NS")
    return data

def get_nifty_500_stocks():
    # A static list of Nifty 500 stocks for demonstration
    # Replace this with the actual fetching method in a real-world scenario

   

    nifty_500_stocks = read_csv_column(csv_file, column_index)
    print(len(nifty_500_stocks))
    return nifty_500_stocks

def select_random_stocks(investment_amount,stock_list, num_stocks=10):
    selected_stocks = random.sample(stock_list, num_stocks)
    live_prices = fetch_live_prices(selected_stocks)
    investment_per_stock =  investment_amount/ num_stocks  # Assuming an investment of 100000 for demonstration

    # Check if any stock has zero quantity and regenerate the list if needed
    while any(price >= (investment_amount / 10) for price in live_prices.values()) or not all(price > 0 for price in live_prices.values()):
        selected_stocks = random.sample(stock_list, num_stocks)
        live_prices = fetch_live_prices(selected_stocks)

    return selected_stocks

def fetch_live_prices(stock_list):
    prices = {}
    for stock in stock_list:
        try:
            ticker = yf.Ticker(stock)
            price = ticker.history(period='1d')['Close'][0]
            prices[stock] = price
        except Exception as e:
            print(f"Error fetching price for {stock}: {e}")
    return prices

def allocate_investment(investment_amount, num_stocks):
    investment_per_stock = investment_amount / num_stocks
    return investment_per_stock

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        investment_amount = float(request.form['investment_amount'])
        num_stocks = 10

        nifty_500_stocks = get_nifty_500_stocks()
        selected_stocks = select_random_stocks(investment_amount,nifty_500_stocks, num_stocks)
        live_prices = fetch_live_prices(selected_stocks)
        investment_per_stock = allocate_investment(investment_amount, num_stocks)

        orders = []
        total_investment = 0
        for stock in selected_stocks:
            price = live_prices.get(stock, 0)
            shares = int(investment_per_stock / price) if price != 0 else 0
            total_investment += shares * price
            orders.append({
                "stock": stock,
                "shares": shares,
                "price": price
            })

        return render_template('index.html', orders=orders, total_investment=total_investment)

    return render_template('index.html')

@app.route('/buy', methods=['POST'])
def buy_stocks():
    orders = json.loads(request.form['result'])
    for order in orders:
        response = place_order(order)
        print(f"Order response: {response}")
    
    return redirect(url_for('index'))

def place_order(order):
    api_url = "https://api.kite.trade/orders/regular"
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {ZERODHA_API_KEY}"
    }
    response = requests.post(api_url, headers=headers, json=order)
    return response.json()

if __name__ == '__main__':
    app.run(debug=True, port=8000)
