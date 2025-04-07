import os
import json
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URI = 'mysql+pymysql://root:Admin01!@localhost:3307/discount_scraper'
engine = create_engine(DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Define Deal model (with URL column added)
class Deal(Base):
    __tablename__ = 'deals'

    id = Column(Integer, primary_key=True)
    product_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    old_price = Column(Float)
    discount_percentage = Column(Integer)
    description = Column(Text)
    image_url = Column(String(255))
    canonical_path = Column(String(255))
    url = Column(String(255))  # Full URL for the deal

# Ensure the table exists with updated schema
Base.metadata.create_all(engine)

def wipe_database():
    """
    Deletes all existing records from the deals table.
    """
    try:
        num_deleted = session.query(Deal).delete()
        session.commit()
        print(f"Successfully deleted {num_deleted} existing deals!")
    except Exception as e:
        session.rollback()
        print(f"Error wiping database: {e}")

def fetch_html(url):
    """
    Fetches HTML content from the given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP issues
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def parse_deals(html_content, top_n=10):
    """
    Parses the HTML content to find the top N product details on Lidl's website.
    """
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

                    # Extract product information
                    canonical_path = grid_data.get('canonicalPath', 'N/A')
                    full_url = f"https://www.lidl.nl{canonical_path}"  # Construct full URL

                    product_info = {
                        'product_name': grid_data.get('fullTitle', 'N/A'),
                        'price': price_info.get('price', 0),
                        'old_price': price_info.get('oldPrice', None),
                        'discount_percentage': percentage_discount,
                        'description': grid_data.get('keyfacts', {}).get('supplementalDescription', 'N/A'),
                        'image_url': grid_data.get('imageList', [])[0] if grid_data.get('imageList') else None,
                        'canonical_path': canonical_path,
                        'url': full_url  # Add full URL here
                    }

                    products.append(product_info)

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")

    # Sort products by discount percentage in descending order
    products.sort(key=lambda x: x['discount_percentage'], reverse=True)
    return products[:top_n]  # Limit to the top N products

def upload_to_database(products):
    """
    Uploads extracted product data to the database.
    """
    for product in products:
        new_deal = Deal(
            product_name=product['product_name'],
            price=product['price'],
            old_price=product['old_price'],
            discount_percentage=product['discount_percentage'],
            description=product['description'],
            image_url=product['image_url'],
            canonical_path=product['canonical_path'],
            url=product['url']  # Save URL in database
        )
        session.add(new_deal)
        print(f"Uploaded: {product['product_name']}")

    session.commit()

# Fetch HTML content from Lidl's website
url = "https://www.lidl.nl/q/query/parkside-producten?sort=percentageDiscount-desc&brand=parkside&brand=parkside+performance"
html_content = fetch_html(url)

if html_content:
    # Wipe database before processing new data
    wipe_database()

    products = parse_deals(html_content)

    if products:
        print(f"Found {len(products)} products")
        upload_to_database(products)
    else:
        print("No products found")
else:
    print("Failed to fetch HTML content")
