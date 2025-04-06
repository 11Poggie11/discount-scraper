import os
import re
from bs4 import BeautifulSoup
import json

def check_lidl_discounts(html_content):
    """
    Parses the HTML content to find product discounts on Lidl's website.

    Args:
        html_content (str): The HTML content of the Lidl webpage.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              product name, old price, new price, discount percentage, and product link
              for discounted products. Returns an empty list if no discounts
              are found.
    """

    soup = BeautifulSoup(html_content, 'html.parser')
    product_list = soup.find_all('li', class_='s-grid__item')
    discounts = []

    for product in product_list:
        # Extract product data from the grid item
        grid_data_element = product.find('div', class_='s-grid__fragment-item')
        if grid_data_element:
            grid_data_str = grid_data_element.get('data-grid-data')
            if grid_data_str:
                try:
                    grid_data = json.loads(grid_data_str)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    continue

                # Extract the necessary information
                product_name = grid_data.get('fullTitle', 'N/A')
                price_info = grid_data.get('price', {})
                old_price = price_info.get('oldPrice', 'N/A')
                new_price = price_info.get('price', 'N/A')
                discount_info = price_info.get('discount', {})
                percentage_discount = discount_info.get('percentageDiscount', 0)
                canonical_path = grid_data.get('canonicalPath', 'N/A')
                product_link = f"https://www.lidl.nl{canonical_path}" if canonical_path != 'N/A' else 'N/A'


                # Check if it is a valid discount and the discount is a number
                if percentage_discount and isinstance(percentage_discount, (int, float)):
                    discounts.append({
                        'product_name': product_name,
                        'old_price': old_price,
                        'new_price': new_price,
                        'discount_percentage': int(percentage_discount),  # Convert to int for cleaner output
                        'product_link': product_link
                    })
    return discounts

def save_discount_to_folder(discount, base_folder="discounts"):
    """
    Saves the discount information to a folder named after the discount percentage and product name,
    organized under "Discounts > Parkside".  Includes the product link in the text file.

    Args:
        discount (dict): A dictionary containing the discount information
                         (product_name, old_price, new_price, discount_percentage, product_link).
        base_folder (str): The name of the main folder where "Parkside" folder
                           will be created. Defaults to "discounts".
    """

    discount_percentage = discount['discount_percentage']
    product_name = discount['product_name']
    product_link = discount['product_link']

    # Sanitize the product name for creating a valid folder name
    safe_product_name = re.sub(r'[\\/*?:"<>|]', "", product_name).strip()
    folder_name = f"{discount_percentage}% - {safe_product_name}"
    folder_name = folder_name[:200]  # Limit folder name length
    parkside_folder = os.path.join(base_folder, "Parkside")
    folder_path = os.path.join(parkside_folder, folder_name)

    # Create the base folder if it doesn't exist
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)

    # Create the "Parkside" folder if it doesn't exist
    if not os.path.exists(parkside_folder):
        os.makedirs(parkside_folder)

    # Create the product folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Create a text file inside the product folder with discount details
    file_path = os.path.join(folder_path, "discount_details.txt")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(f"Product: {product_name}\n")
        file.write(f"Old Price: {discount['old_price']} EUR\n")
        file.write(f"New Price: {discount['new_price']} EUR\n")
        file.write(f"Discount: {discount_percentage}%\n")
        file.write(f"Link: {product_link}\n")

# Load the HTML content from the file
with open("paginabron.txt", "r", encoding="utf-8") as file:
    html_content = file.read()

# Check for discounts
discounts = check_lidl_discounts(html_content)

# Process and save each discount
if discounts:
    print("Saving Parkside product discounts...")
    for discount in discounts:
        save_discount_to_folder(discount)
        print(f"  Saved discount for: {discount['product_name']}")
    print("Discounts saved successfully!")
else:
    print("No Parkside product discounts found on the page.")
