import requests, re, time, html
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://cotepara.ma"
OUTPUT = "products_cotepara.csv"

headers = {"User-Agent": "Mozilla/5.0"}

def clean(x):
    if not x: return ""
    return re.sub(r"\s+", " ", BeautifulSoup(str(x), "html.parser").get_text(" ", strip=True)).strip()

def get_product_urls():
    urls = set()
    sitemap_urls = [
        f"{BASE}/product-sitemap.xml",
        f"{BASE}/wp-sitemap-posts-product-1.xml",
        f"{BASE}/sitemap_index.xml",
        f"{BASE}/sitemap.xml",
    ]

    for sm in sitemap_urls:
        try:
            r = requests.get(sm, headers=headers, timeout=30)
            txt = r.text
            found = re.findall(r"<loc>(.*?)</loc>", txt)
            for u in found:
                u = html.unescape(u)
                if "/product/" in u or "/produit/" in u:
                    urls.add(u)
                if "sitemap" in u and u not in sitemap_urls:
                    try:
                        rr = requests.get(u, headers=headers, timeout=30)
                        for uu in re.findall(r"<loc>(.*?)</loc>", rr.text):
                            uu = html.unescape(uu)
                            if "/product/" in uu or "/produit/" in uu:
                                urls.add(uu)
                    except:
                        pass
        except:
            pass

    return list(urls)

def scrape_product(url):
    r = requests.get(url, headers=headers, timeout=40)
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    name = clean(soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "")

    ref = ""
    m = re.search(r"Référence\s*:\s*(\d{8,14})", text)
    if m:
        ref = m.group(1)

    price = ""
    sale = ""
    prices = re.findall(r"(\d+[,.]?\d*)\s*MAD", text)
    if prices:
        price = prices[0].replace(",", ".")
        if len(prices) > 1:
            sale = prices[0].replace(",", ".")
            price = prices[1].replace(",", ".")

    img = ""
    og = soup.find("meta", property="og:image")
    if og:
        img = og.get("content", "")

    if not img:
        im = soup.select_one(".woocommerce-product-gallery img, img.wp-post-image, img")
        if im:
            img = im.get("data-src") or im.get("src") or ""

    if img:
        img = urljoin(url, img)
        img = re.sub(r"-\d+x\d+(?=\.)", "", img)

    short_desc = ""
    sd = soup.select_one(".woocommerce-product-details__short-description")
    if sd:
        short_desc = clean(sd.get_text(" ", strip=True))

    desc = ""
    d = soup.select_one("#tab-description, .woocommerce-Tabs-panel--description")
    if d:
        desc = clean(d.get_text(" ", strip=True))

    if not desc:
        desc = short_desc

    cats = []
    for c in soup.select(".posted_in a, .breadcrumb a"):
        t = clean(c.get_text())
        if t and t.lower() not in ["accueil", "home"]:
            cats.append(t)

    return {
        "Type": "simple",
        "SKU": ref,
        "Code barres": ref,
        "Name": name,
        "Published": 1,
        "Short description": short_desc,
        "Description": desc,
        "Regular price": price,
        "Sale price": sale,
        "Categories": " > ".join(dict.fromkeys(cats)),
        "Images": img,
        "Source URL": url
    }

urls = get_product_urls()
print("FOUND URLS:", len(urls))

rows = []

for i, url in enumerate(urls, 1):
    try:
        print(i, "/", len(urls), url)
        rows.append(scrape_product(url))
        if i % 20 == 0:
            pd.DataFrame(rows).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        time.sleep(1)
    except Exception as e:
        print("ERROR:", url, e)

pd.DataFrame(rows).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
print("DONE:", len(rows), OUTPUT)
