import uuid

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from utils import get_contact_uuid, get_contact_info
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
import os


def crawl_divar(selected_url: str, output_file: str = "divar_crawler.json", contact_info=False,
                headless: bool = False, incognita: bool = False):
    try:
        # disable proxy
        for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
            os.environ.pop(key, None)

        options = Options()
        options.add_argument("--no-proxy-server")

        # if proxy:
        #     options.add_argument(f"--proxy-server={proxy}")

        if headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--remote-debugging-port=9222")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/114.0.0.0 Safari/537.36")
            # disable automation detection
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
        if incognita:
            options.add_argument("--incognito")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
        driver.get(selected_url)

        # uncomment cookie
        # driver.add_cookie({
        #     "name": "disable_map_view",
        #     "value": "true",
        #     "domain": ".divar.ir",
        #     "path": "/",
        #     "expires/max-age": "2026-10-20T09:51:27.354Z",
        #     "size": 20,
        #     "secure": False,
        #     "httpOnly": False,
        #     "sameSite": "Lax",
        #     "partitionKeySite": None,
        #     "crossSite": False,
        #     "priority": "medium",
        # })
        #
        # driver.add_cookie({
        #     "name": "token",
        #     "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI5OGQ1OWU4NC03NTc2LTQwMTItYmI0OC0zMGU5ZTNkYzJmMjUiLCJ1aWQiOiJmNmMxMmVjZi1hZTNkLTRhMzgtOGUwNS00NmFiNDM3ODQ2YjQiLCJ1c2VyIjoiMDkzNTc4ODAyNjQiLCJ2ZXJpZmllZF90aW1lIjoxNzU3NzUwMjc5LCJpc3MiOiJhdXRoIiwidXNlci10eXBlIjoicGVyc29uYWwiLCJ1c2VyLXR5cGUtZmEiOiLZvtmG2YQg2LTYrti124wiLCJleHAiOjE3NjAzNDIyNzksImlhdCI6MTc1Nzc1MDI3OX0.CT9eVApmLz7_f068Xh40faB2pW0EjTDrUvH9eH3XkJE",
        #     "domain": ".divar.ir",
        #     "path": "/",
        #     "expires/max-age": "2026-10-18T09:09:52.000Z",
        #     "size": 409,
        #     "secure": False,
        #     "httpOnly": True,
        #     "sameSite": "Lax",
        #     "partitionKeySite": None,
        #     "crossSite": False,
        #     "priority": "medium",
        # })
        # print("Cookies had been added.")
        # driver.refresh()
        # time.sleep(0.5)

        # Scroll down a bit to load more cards
        driver.execute_script("window.scrollBy(0, 12000);")
        print("Scrolled down.")

        if headless:
            print(driver.title)
            driver.set_window_size(1920, 1080)
            time.sleep(0.5)

        try:
            if headless:
                cards = WebDriverWait(driver, 15).until(
                    EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div[class^=widget-col-]"))
                )
            else:
                cards = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class^=widget-col-]"))
                )
        except Exception as e:
            print("Timeout: No cards loaded", str(e))
            print(repr(e))
            cards = []

        if not cards:
            print("No cards found on first page.")
            return None

        data = []
        for card in cards:
            try:
                link = card.find_element(By.CSS_SELECTOR, "a[class^=kt-post-card__action]").get_attribute("href")
            except:
                link = None
            try:
                title = card.find_element(By.CSS_SELECTOR, "h2[class^=kt-post-card__title]").text
            except:
                title = None
            try:
                bottom_red_text = card.find_element(By.CSS_SELECTOR, "span[class^=kt-post-card__red-text]").text
            except:
                bottom_red_text = None

            data.append({"href": link, "title": title, "bottom_red_text": bottom_red_text, "meta_data": {}})

        df = pd.DataFrame(data)

        print("df:\n", df.head())
        print("Number of cards extracted", len(df))

        # ==================================================
        # load a driver
        # disable proxy
        # print("\nLaunching driver..")
        # for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        #     os.environ.pop(key, None)
        #
        # options = Options()
        # options.add_argument("--no-proxy-server")
        # if headless:
        #     options.add_argument("--headless")
        #     options.add_argument("--disable-gpu")
        #     options.add_argument("--window-size=1920,1080")
        #     options.add_argument("--disable-dev-shm-usage")
        #     options.add_argument("--no-sandbox")
        #     options.add_argument("--remote-debugging-port=9222")
        #     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        #                          "AppleWebKit/537.36 (KHTML, like Gecko) "
        #                          "Chrome/114.0.0.0 Safari/537.36")
        #     # disable automation detection
        #     options.add_argument("--disable-blink-features=AutomationControlled")
        #     options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #     options.add_experimental_option('useAutomationExtension', False)
        # if incognita:
        #     options.add_argument("--incognito")
        #
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # driver.maximize_window()
        # print("\nDriver launched.\n")

        # ==================================================

        # scrape details for each link (selenium)
        for i, link in enumerate(df["href"]):
            try:
                if not link:
                    continue

                response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    html_content = response.text
                    # Save to file if needed
                    with open(f"html_data/page_{uuid.uuid4()}.html", "w", encoding="utf-8") as f:
                        f.write(html_content)
                else:
                    print(f"Failed to fetch {link}: Status {response.status_code}")
            except Exception as e:
                print(f"Error fetching {link}: {e}")

            driver.get(link)
            # instead of time.sleep(2)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".kt-page-title__subtitle"))
                )
            except:
                print(f"Page {link} did not load in time")

            info = {}

            # subtitle
            try:
                subtitle = driver.find_element(By.CSS_SELECTOR, ".kt-page-title__subtitle").text.strip()
                info["subtitle"] = subtitle
            except:
                pass

            # table headers/values
            try:
                headers = driver.find_elements(By.CSS_SELECTOR, ".kt-group-row__header th span")
                values = driver.find_elements(By.CSS_SELECTOR, ".kt-group-row__data-row td")
                for h, v in zip(headers, values):
                    info[h.text.strip()] = v.text.strip()
            except:
                pass

            # expandable rows
            rows = driver.find_elements(By.CSS_SELECTOR, ".kt-unexpandable-row")
            for row in rows:
                try:
                    key = row.find_element(By.CSS_SELECTOR, ".kt-unexpandable-row__title").text.strip()
                    value = row.find_element(By.CSS_SELECTOR, ".kt-unexpandable-row__value").text.strip()
                    info[key] = value
                except:
                    pass

            # description
            try:
                desc = driver.find_element(By.CSS_SELECTOR, "p.kt-description-row__text--primary").text.strip()
                info["توضیحات"] = desc
            except:
                pass

            df.at[i, "meta_data"] = info
            print(f"[{i + 1}] Done: {len(info)} fields")

        driver.quit()

        meta_df = df["meta_data"].apply(pd.Series)
        # df["api_url"] = df["href"].apply(lambda x: x.rstrip("/").split("/")[-1])

        # print("\ngetting contact uuids..")
        # df["contact_uuid"] = df["api_url"].apply(get_contact_uuid)

        if contact_info:
            print("\ngetting contact info..")
            phone_numbers = []
            for idx, row in df.iterrows():
                contact_uuid = row.get("contact_uuid")
                api_url = row.get("api_url")
                if contact_uuid and api_url:
                    print(f"Getting contact info for {api_url}...")
                    phone_number = get_contact_info(api_url, contact_uuid)
                    phone_numbers.append(phone_number)
                    time.sleep(1.5)  # to avoid captcha
                else:
                    phone_numbers.append(None)

            df["phone_number"] = phone_numbers

        result = pd.concat([df.drop(columns=["meta_data"]), meta_df], axis=1)

        result.to_json(output_file, orient="records", indent=4, lines=False, force_ascii=False)

        print(f"\nSaved to {output_file}\n")

    except Exception as e:
        print(f"[Error] An exception occurred: {e}")
        try:
            if not df.empty:
                df.to_csv(output_file, index=False, encoding="utf-8-sig")
                print(f"Partial data saved to {output_file}")
        except Exception as save_err:
            print(f"[Error] Failed to save partial data: {save_err}")
