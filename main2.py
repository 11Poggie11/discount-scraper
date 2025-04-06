import os
import re
import json
import requests
from bs4 import BeautifulSoup

def check_lidl_discounts(html_content):
    """
    Parses the HTML content to find product details on Lidl's website.
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
                    # Extract product information
                    product_info = {
                        'product_name': grid_data.get('fullTitle', 'N/A'),
                        'price_info': grid_data.get('price', {}),
                        'description': grid_data.get('keyfacts', {}).get('description', 'N/A'),
                        'image_list': grid_data.get('imageList', []),
                        'canonical_path': grid_data.get('canonicalPath', 'N/A')
                    }
                    
                    # Clean up HTML tags from description
                    product_info['description'] = BeautifulSoup(
                        product_info['description'], 'html.parser'
                    ).get_text(separator='\n').strip()
                    
                    products.append(product_info)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
    return products

def download_image(url, folder_path, image_num):
    """Downloads and saves an image from a URL"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            extension = os.path.splitext(url)[1]
            image_path = os.path.join(folder_path, f"image{image_num}{extension}")
            with open(image_path, 'wb') as f:
                for chunk in response:
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading image: {e}")
    return False

def save_product_data(product, base_folder="discounts"):
    """Saves all product information including images"""
    price_info = product['price_info']
    discount_info = price_info.get('discount', {})
    percentage_discount = discount_info.get('percentageDiscount', 0)
    
    # Create folder structure
    safe_name = re.sub(r'[\\/*?:"<>|]', "", product['product_name']).strip()
    folder_name = f"{percentage_discount}% - {safe_name}"[:200]
    parkside_folder = os.path.join(base_folder, "Parkside")
    product_folder = os.path.join(parkside_folder, folder_name)
    image_folder = os.path.join(product_folder, "images")
    
    os.makedirs(image_folder, exist_ok=True)
    
    # Save text data
    text_file = os.path.join(product_folder, "product_details.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"Product: {product['product_name']}\n")
        f.write(f"Old Price: {price_info.get('oldPrice', 'N/A')} EUR\n")
        f.write(f"New Price: {price_info.get('price', 'N/A')} EUR\n")
        f.write(f"Discount: {percentage_discount}%\n")
        f.write(f"Link: https://www.lidl.nl{product['canonical_path']}\n")
        f.write("\nDescription:\n" + product['description'])
    
    # Download images
    if product['image_list']:
        print(f"Downloading {len(product['image_list'])} images...")
        for idx, img_url in enumerate(product['image_list'], 1):
            download_image(img_url, image_folder, idx)

# Load and process HTML
with open("paginabron.txt", "r", encoding="utf-8") as file:
    html_content = file.read()

products = check_lidl_discounts(html_content)

if products:
    print(f"Found {len(products)} products")
    for product in products:
        save_product_data(product)
        print(f"Saved: {product['product_name']}")
else:
    print("No products found")
