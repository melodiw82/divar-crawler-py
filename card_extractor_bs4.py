import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


def crawl_divar_bs(selected_url: str, output_file: str = "divar_crawler.csv"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36"
    }

    session = requests.Session()
    session.headers.update(headers)
    session.cookies.set("disable_map_view", "true", domain=".divar.ir")

    resp = session.get(selected_url)
    if resp.status_code != 200:
        print(f"Failed to load {selected_url}")
        return None

    time.sleep(1)
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("div[class^=widget-col-]")

    if not cards:
        print("No cards found on first page.")
        return None

    data = []
    for card in cards:
        link_tag = card.select_one("a[class^=kt-post-card__action]")
        title_tag = card.select_one("h2[class^=kt-post-card__title]")
        red_text_tag = card.select_one("span[class^=kt-post-card__red-text]")

        link = link_tag["href"] if link_tag else None
        if link and link.startswith("/"):
            link = "https://divar.ir" + link  # make absolute link

        title = title_tag.get_text(strip=True) if title_tag else None
        bottom_red_text = red_text_tag.get_text(strip=True) if red_text_tag else None

        data.append({
            "href": link,
            "title": title,
            "bottom_red_text": bottom_red_text,
            "meta_data": {}
        })

    df = pd.DataFrame(data)
    print("Number of cards extracted:", len(df))

    # ================================================

    # scrape details for each link
    for i, link in enumerate(df["href"]):
        if not link:
            continue

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36"
        }
        session = requests.Session()
        session.headers.update(headers)
        r = session.get(link)

        print("Status Code: ", r.status_code)
        print(r.text[:1000])
        if r.status_code != 200:
            print(f"[{i}] Failed to fetch {link}")
            continue

        time.sleep(1.5)

        page = BeautifulSoup(r.text, "html.parser")
        info = {}

        # subtitle
        subtitle = page.select_one(".kt-page-title__subtitle")
        if subtitle:
            info["subtitle"] = subtitle.get_text(strip=True)

        # table headers/values
        headers = page.select(".kt-group-row__header th span")
        values = page.select(".kt-group-row__data-row td")
        for h, v in zip(headers, values):
            info[h.get_text(strip=True)] = v.get_text(strip=True)

        # expandable rows
        rows = page.select(".kt-unexpandable-row")
        for row in rows:
            key = row.select_one(".kt-unexpandable-row__title")
            value = row.select_one(".kt-unexpandable-row__value")
            if key and value:
                info[key.get_text(strip=True)] = value.get_text(strip=True)

        # description
        desc = page.select_one("p.kt-description-row__text--primary")
        if desc:
            info["توضیحات"] = desc.get_text(strip=True)

        df.at[i, "meta_data"] = info
        print(f"[{i}] Done: {len(info)} fields")

        input()

    meta_df = df["meta_data"].apply(pd.Series)
    result = pd.concat([df.drop(columns=["meta_data"]), meta_df], axis=1)

    result.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\nSaved to {output_file}\n")
    return result
