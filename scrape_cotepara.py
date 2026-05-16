import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import html as ihtml

BASE = "https://cotepara.ma"
OUTPUT = "products_cotepara.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def clean_text(x):
    if not x:
        return ""
    return re.sub(r"\s+", " ", str(x)).strip()

def get_meta(soup, attr, value):
    tag = soup.find("meta", attrs={attr: value})
    if tag:
        return clean_text(tag.get("content", ""))
    return ""

def get_product_sitemaps():
    print("Reading sitemap index...")
    url = f"{BASE}/sitemap_index.xml"
    r = requests.get(url, headers=HEADERS, timeout=60)

    sitemaps = re.findall(r"<loc>(.*?)</loc>", r.text)
    sitemaps = [ihtml.unescape(x) for x in sitemaps]

    product_sitemaps = [x for x in sitemaps if "product-sitemap" in x]

    print("Product sitemaps:", len(product_sitemaps))
    return product_sitemaps

def get_product_urls():
    urls = []

    for sm in get_product_sitemaps():
        print("Reading:", sm)

        try:
            r = requests.get(sm, headers=HEADERS, timeout=60)
            found = re.findall(r"<loc>(.*?)</loc>", r.text)

            for u in found:
                u = ihtml.unescape(u).strip()
                if u.startswith(BASE):
                    urls.append(u)

        except Exception as e:
            print("SITEMAP ERROR:", sm, e)

        time.sleep(0.5)

    urls = list(dict.fromkeys(urls))

    print("FOUND PRODUCT URLS:", len(urls))
    return urls

def scrape_product(url):
    r = requests.get(url, headers=HEADERS, timeout=60)
    soup = BeautifulSoup(r.text, "lxml")
    text = soup.get_text(" ", strip=True)

    title = get_meta(soup, "property", "og:title")
    title = title.split(" - Côté Para")[0].strip()

    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else ""

    description = get_meta(soup, "name", "description")
    image = get_meta(soup, "property", "og:image")
    brand = get_meta(soup, "property", "product:brand")
    price = get_meta(soup, "property", "product:price:amount")
    availability = get_meta(soup, "property", "product:availability")
    stock_text = get_meta(soup, "name", "twitter:data2")

    barcode = ""

    m = re.search(r"Référence\s*:\s*(\d{8,14})", text)
    if m:
        barcode = m.group(1)

    if not barcode:
        nums = re.findall(r"\b\d{8,14}\b", image + " " + url + " " + title)
        if nums:
            barcode = nums[-1]

    regular_price = price
    sale_price = ""

    return {
        "Type": "simple",
        "SKU": barcode,
        "Code barres": barcode,
        "Name": title,
        "Published": 1,
        "Short description": description,
        "Description": description,
        "Regular price": regular_price,
        "Sale price": sale_price,
        "Brand": brand,
        "Stock text": stock_text,
        "Availability": availability,
        "Categories": "",
        "Images": image,
        "Source URL": url
    }

urls = get_product_urls()

rows = []

for i, url in enumerate(urls, 1):
    try:
        print(f"{i}/{len(urls)} - {url}")
        row = scrape_product(url)
        rows.append(row)

        if i % 50 == 0:
            pd.DataFrame(rows).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
            print("Saved checkpoint:", len(rows))

        time.sleep(0.5)

    except Exception as e:
        print("ERROR:", url, e)

df = pd.DataFrame(rows)
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("DONE:", len(df), "products")
print("FILE:", OUTPUT)
