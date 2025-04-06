import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def check_amazon_discounts(html_content, top_n=10):
    """
    Parses the HTML content to find the top N product details on Amazon's webpage.

    Args:
        html_content (str): The HTML content of the Amazon webpage.
        top_n (int): The number of top discounted products to retrieve. Defaults to 10.

    Returns:
        list: A list of dictionaries, where each dictionary contains product details
              including name, price, description, image list, and discount percentage.
              The list is sorted by discount percentage in descending order and limited to the top N products.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    product_list = soup.find_all('div', class_='a-section a-spacing-medium')  # Adjust this selector based on Amazon's structure
    products = []

    for product in product_list:
        try:
            # Extract product information
            title_element = product.find('span', class_='a-size-medium')
            price_element = product.find('span', class_='a-price-whole')
            discount_element = product.find('span', class_='a-text-price')
            image_element = product.find('img', class_='s-image')

            if title_element and price_element:
                product_info = {
                    'product_name': title_element.get_text(strip=True),
                    'price': price_element.get_text(strip=True),
                    'discount_price': discount_element.get_text(strip=True) if discount_element else 'N/A',
                    'image_url': image_element['src'] if image_element else 'N/A',
                }
                products.append(product_info)
        except Exception as e:
            print(f"Error parsing product: {e}")

    return products[:top_n]  # Limit to the top N products

def save_product_data(product, base_folder="amazon_discounts"):
    """Saves all product information including images."""
    safe_name = re.sub(r'[\\/*?:"<>|]', "", product['product_name']).strip()
    folder_name = safe_name[:200]
    product_folder = os.path.join(base_folder, folder_name)
    
    os.makedirs(product_folder, exist_ok=True)
    
    # Save text data
    text_file = os.path.join(product_folder, "product_details.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"Product: {product['product_name']}\n")
        f.write(f"Price: {product['price']} EUR\n")
        f.write(f"Discount Price: {product['discount_price']}\n")
        f.write(f"Image URL: {product['image_url']}\n")

def fetch_amazon_page(url):
    """Fetches the dynamically loaded Amazon page using Selenium."""
    service = Service('path_to_chromedriver')  # Update with your chromedriver path
    driver = webdriver.Chrome(service=service)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "s-main-slot"))
        )
        html_content = driver.page_source
    finally:
        driver.quit()

    return html_content

# Fetch HTML content from the specified URL
url = "https://www.amazon.nl/events/springdealdays?ref_=nav_cs_gb_td_ss_dt_cr"
html_content = fetch_amazon_page(url)

products = check_amazon_discounts(html_content)

if products:
    print(f"Found {len(products)} products")
    for product in products:
        save_product_data(product)
        print(f"Saved: {product['product_name']}")
else:
    print("No products found")
