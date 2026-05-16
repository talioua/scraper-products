import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE = "https://cotepara.ma"

# sitemap
sitemap = requests.get(
    BASE + "/product-sitemap1.xml",
    headers=HEADERS
).text

urls = re.findall(r'<loc>(.*?)</loc>', sitemap)

products = []

print("FOUND URLS:", len(urls))

for i, url in enumerate(urls):

    try:
        print(i + 1, url)

        r = requests.get(url, headers=HEADERS, timeout=30)

        soup = BeautifulSoup(r.text, "html.parser")

        title = ""

        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        text = soup.get_text(" ", strip=True)

        barcode = ""

        m = re.search(r'Référence\s*:\s*(\d+)', text)

        if m:
            barcode = m.group(1)

        image = ""

        img = soup.find("img")

        if img and img.get("src"):
            image = img["src"]

        products.append({
            "name": title,
            "barcode": barcode,
            "image": image,
            "url": url
        })

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)

df = pd.DataFrame(products)

df.to_csv(
    "products_cotepara.csv",
    index=False,
    encoding="utf-8-sig"
)

print("DONE:", len(products))
