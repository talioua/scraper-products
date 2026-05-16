import requests
import re
import pandas as pd
from bs4 import BeautifulSoup

SITEMAP = "https://cotepara.ma/product-sitemap1.xml"
HEADERS = {"User-Agent": "Mozilla/5.0"}

xml = requests.get(SITEMAP, headers=HEADERS, timeout=60).text
urls = re.findall(r"<loc>(.*?)</loc>", xml)

print("FOUND URLS:", len(urls))

products = []

for i, url in enumerate(urls[:100], 1):
    print(i, url)

    try:
        html = requests.get(url, headers=HEADERS, timeout=30).text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        name = ""
        h1 = soup.find("h1")
        if h1:
            name = h1.get_text(" ", strip=True)

        barcode = ""
        m = re.search(r"Référence\s*:\s*(\d{8,14})", text)
        if m:
            barcode = m.group(1)

        image = ""
        og = soup.find("meta", property="og:image")
        if og:
            image = og.get("content", "")

        price = ""
        mp = soup.find("meta", property="product:price:amount")
        if mp:
            price = mp.get("content", "")

        desc = ""
        md = soup.find("meta", attrs={"name": "description"})
        if md:
            desc = md.get("content", "")

        products.append({
            "name": name,
            "description": desc,
            "barcode": barcode,
            "price": price,
            "image": image,
            "url": url
        })

    except Exception as e:
        print("ERROR:", e)

df = pd.DataFrame(products)
df.to_csv("products_cotepara_v2.csv", index=False, encoding="utf-8-sig")

print("DONE:", len(products), "products")
