import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re

products = []

page = 1

while True:

    url = f"https://cotepara.ma/wp-json/wc/store/v1/products?per_page=100&page={page}"

    print("Reading:", url)

    r = requests.get(url, timeout=60)

    if r.status_code != 200:
        break

    data = r.json()

    if not data:
        break

    for p in data:

        name = p.get("name", "")
        short_desc = p.get("short_description", "")
        description = p.get("description", "")

        prices = p.get("prices", {})

        regular_price = prices.get("regular_price", "")
        sale_price = prices.get("sale_price", "")

        try:
            regular_price = float(regular_price) / 100
        except:
            regular_price = ""

        try:
            sale_price = float(sale_price) / 100
        except:
            sale_price = ""

        images = p.get("images", [])

        image_hd = ""
        all_images = []

        for img in images:
            src = img.get("src", "")

            if src:
                all_images.append(src)

            if not image_hd and src:
                image_hd = src

        categories = []

        for c in p.get("categories", []):
            categories.append(c.get("name", ""))

        tags = []

        for t in p.get("tags", []):
            tags.append(t.get("name", ""))

        permalink = p.get("permalink", "")

        barcode = ""

        try:
            html = requests.get(permalink, timeout=60).text

            soup = BeautifulSoup(html, "lxml")

            text = soup.get_text(" ", strip=True)

            m = re.search(r"Référence\s*[:\-]?\s*(\d{8,14})", text)

            if m:
                barcode = m.group(1)

        except:
            pass

        products.append({
            "nom": name,
            "description_courte": short_desc,
            "description": description,
            "tarif_regular": regular_price,
            "tarif_promo": sale_price,
            "barcode": barcode,
            "categorie": ", ".join(categories),
            "tags": ", ".join(tags),
            "image_hd": image_hd,
            "all_images": ", ".join(all_images),
            "url": permalink
        })

        time.sleep(1)

    page += 1

df = pd.DataFrame(products)

df.to_csv("cotepara_products.csv", index=False, encoding="utf-8-sig")

print("DONE:", len(df), "products")