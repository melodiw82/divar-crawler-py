from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
import pandas as pd
import time
import os
import json

for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(key, None)

options = Options()
options.add_argument("--no-proxy-server")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options,
                          )
driver.maximize_window()
driver.get("https://divar.ir/s/tehran")
# ===================================================

try:
    drop_down_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.kt-dropdown-button.kt-dropdown-button--medium.kt-dropdown-button--inlined")
        )
    )
    drop_down_button.click()
    print("Clicked on menu.")
except Exception as e:
    print("Could not click on menu:", e)

# ===================================================

wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

MAIN_SEL = "a[class*='category-menu-selector']"
PANEL_SEL = "div[class*='category-menu-content-panel']"
GROUP_SEL = "div[class*='category-menu-group']"
ITEM_SEL = "a[class*='category-menu-item']"
ARROW_SEL = "button[class*='kt-fab-button']"  # the left arrow to expand

categories = []

main_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, MAIN_SEL)))

for main_el in main_elements:
    main_name = main_el.text.strip()
    main_href = main_el.get_attribute("href") or ""

    # Skip همه آگهی‌ها
    if "همهٔ آگهی‌ها" in main_name:
        continue

    if "همهٔ آگهی‌های استخدام و کاریابی" in main_name:
        continue

    print("Main:", main_name)

    # hover to show first-level menu
    actions.move_to_element(main_el).perform()
    time.sleep(0.6)

    # if there’s an arrow (like in خانه و آشپزخانه), click it to expand
    try:
        arrow_btn = main_el.find_element(By.XPATH, "following-sibling::button")
        if arrow_btn.is_displayed():
            arrow_btn.click()
            print("Expanded submenu for", main_name)
            time.sleep(0.7)
    except:
        pass  # no arrow → normal category

    # wait for content panel
    try:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, PANEL_SEL)))
    except:
        time.sleep(0.5)

    entry = {"main": main_name, "main_href": main_href, "subs": []}

    groups = driver.find_elements(By.CSS_SELECTOR, GROUP_SEL)
    for grp in groups:
        links = grp.find_elements(By.CSS_SELECTOR, ITEM_SEL)
        if not links:
            continue

        first_cls = (links[0].get_attribute("class") or "")
        if "category-menu-item--parent" in first_cls:
            parent = links[0]
            parent_name = parent.text.strip()
            parent_href = parent.get_attribute("href")
            children = []
            for child in links[1:]:
                children.append({
                    "name": child.text.strip(),
                    "href": child.get_attribute("href")
                })
            entry["subs"].append({
                "name": parent_name,
                "href": parent_href,
                "children": children
            })
        else:
            for link in links:
                entry["subs"].append({
                    "name": link.text.strip(),
                    "href": link.get_attribute("href"),
                    "children": []
                })

    categories.append(entry)

# save results
with open("../data/divar_categories.json", "w", encoding="utf-8") as fh:
    json.dump(categories, fh, ensure_ascii=False, indent=2)

print("Saved categories to divar_categories.json")

# ===================================================
