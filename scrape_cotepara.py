import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://cotepara.ma"

headers = {
    "User-Agent": "Mozilla/5.0"
}

products = []

# صفحات الكاتيجوري
category_urls = [
    "https://cotepara.ma/12-visage",
    "https://cotepara.ma/13-corps",
    "https://cotepara.ma/14-capillaire",
    "https://cotepara.ma/15-hygiene",
]

for category in category_urls:

    page = 1

    while True:

        url = f"{category}?page={page}"

        print("READ CATEGORY:", url)

        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        product_links = []

        for a in soup.find_all("a", href=True):

            href = a["href"]

            if "/product/" in href:
                if href not in product_links:
                    product_links.append(href)

        if len(product_links) == 0:
            break

        for link in product_links:

            try:

                print("PRODUCT:", link)

                rr = requests.get(link, headers=headers)

                ss = BeautifulSoup(rr.text, "html.parser")

                title = ""

                h1 = ss.find("h1")

                if h1:
                    title = h1.get_text(strip=True)

                description = ""

                desc = ss.find("div", class_="product-description")

                if desc:
                    description = desc.get_text(" ", strip=True)

                short_desc = ""

                meta = ss.find("meta", attrs={"name": "description"})

                if meta:
                    short_desc = meta.get("content", "")

                image = ""

                img = ss.find("img")

                if img:
                    image = img.get("src", "")

                barcode = ""

                text = ss.get_text(" ", strip=True)

                import re

                m = re.search(r"Référence[: ]+([0-9]{8,14})", text)

                if m:
                    barcode = m.group(1)

                products.append({
                    "name": title,
                    "short_description": short_desc,
                    "description": description,
                    "image": image,
                    "barcode": barcode,
                    "url": link
                })

                print("OK:", title)

                time.sleep(1)

            except Exception as e:
                print("ERROR:", e)

        page += 1

df = pd.DataFrame(products)

df.to_csv("products.csv", index=False, encoding="utf-8-sig")

print("DONE:", len(products), "products")
