import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

products = []

# sitemap index
sitemap_index = "https://cotepara.ma/sitemap_index.xml"

xml = requests.get(sitemap_index, headers=HEADERS).text

# استخراج روابط product sitemap
sitemaps = re.findall(r'https://cotepara.ma/product-sitemap.*?\.xml', xml)

print("FOUND SITEMAPS:", len(sitemaps))

product_urls = []

# استخراج روابط المنتجات
for sitemap in sitemaps:
    print("READING:", sitemap)

    try:
        data = requests.get(sitemap, headers=HEADERS, timeout=30).text

        urls = re.findall(r'<loc>(.*?)</loc>', data)

        for u in urls:
            if "/product/" in u:
                product_urls.append(u)

    except Exception as e:
        print("ERROR:", e)

print("FOUND PRODUCT URLS:", len(product_urls))

# scraping products
for i, url in enumerate(product_urls):

    print(f"{i+1}/{len(product_urls)}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)

        soup = BeautifulSoup(r.text, "html.parser")

        title = ""

        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        short_desc = ""
        short_div = soup.find(class_="woocommerce-product-details__short-description")
        if short_div:
            short_desc = short_div.get_text(" ", strip=True)

        description = ""
        tabs = soup.find(id="tab-description")
        if tabs:
            description = tabs.get_text(" ", strip=True)

        barcode = ""

        txt = soup.get_text(" ", strip=True)

        match = re.search(r'Référence\s*[:\-]?\s*(\d+)', txt)

        if match:
            barcode = match.group(1)

        image = ""

        img = soup.find("img")

        if img and img.get("src"):
            image = img["src"]

        products.append({
            "name": title,
            "short_description": short_desc,
            "description": description,
            "barcode": barcode,
            "image": image,
            "url": url
        })

        time.sleep(1)

    except Exception as e:
        print("ERROR PRODUCT:", e)

df = pd.DataFrame(products)

df.to_csv("products_cotepara.csv", index=False, encoding="utf-8-sig")

print("DONE:", len(products), "products")
