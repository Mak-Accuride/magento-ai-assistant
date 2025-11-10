import os
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("MAGENTO_BASE_URL")
CONSUMER_KEY = os.getenv("MAGENTO_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MAGENTO_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("MAGENTO_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("MAGENTO_ACCESS_TOKEN_SECRET")

def fetch_products(limit=10):
    url = f"{BASE_URL}/V1/products"
    auth = OAuth1(
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET,
        signature_method='HMAC-SHA256'
    )
    params = {
        "searchCriteria[pageSize]": limit,
        "searchCriteria[currentPage]": 1
    }

    response = requests.get(url, auth=auth, params=params)

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"✅ Retrieved {len(items)} products:\n")
        for i, item in enumerate(items, start=1):
            print(f"{i}. {item.get('name', 'Unnamed Product')} (SKU: {item.get('sku')})")
    else:
        print(f"❌ Failed ({response.status_code}) - {response.text}")

if __name__ == "__main__":
    fetch_products()
