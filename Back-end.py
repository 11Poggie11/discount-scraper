from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

def fetch_lidl_deals():
    url = "https://www.lidl.nl/q/query/parkside-producten?sort=percentageDiscount-desc&brand=parkside&brand=parkside+performance"
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        product_list = soup.find_all('li', class_='s-grid__item')
        products = []

        for product in product_list:
            grid_data_element = product.find('div', class_='s-grid__fragment-item')
            if grid_data_element:
                grid_data_str = grid_data_element.get('data-grid-data')
                if grid_data_str:
                    try:
                        grid_data = json.loads(grid_data_str)
                        price_info = grid_data.get('price', {})
                        discount_info = price_info.get('discount', {})
                        percentage_discount = discount_info.get('percentageDiscount', 0)

                        product_info = {
                            'product_name': grid_data.get('fullTitle', 'N/A'),
                            'price': price_info.get('price', 'N/A'),
                            'old_price': price_info.get('oldPrice', 'N/A'),
                            'discount_percentage': percentage_discount,
                            'image': grid_data.get('imageList', [])[0] if grid_data.get('imageList') else None,
                            'link': f"https://www.lidl.nl{grid_data.get('canonicalPath', '')}"
                        }
                        products.append(product_info)
                    except json.JSONDecodeError:
                        continue

        return products
    return []

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/deals')
def get_deals():
    deals = fetch_lidl_deals()
    return jsonify(deals)

if __name__ == '__main__':
    app.run(debug=True)
