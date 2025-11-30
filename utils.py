import json
import requests
import os


def load_categories(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        categories = json.load(f)
    return categories


def build_category_list(categories):
    category_list = []
    for main in categories:
        for sub in main["subs"]:
            if sub["children"]:
                for child in sub["children"]:
                    category_list.append((f"{main['main']} > {sub['name']} > {child['name']}", f"{child['href']}"))
            else:
                category_list.append((f"{main['main']} > {sub['name']}", f"{sub['href']}"))
    return category_list


def show_menu(category_list):
    for i, (name, href) in enumerate(category_list, start=1):
        print(f"{i}. {name}")


def get_contact_uuid(api_url: str):
    url = f"https://api.divar.ir/v8/posts-v2/web/{api_url}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers)
    contact_uuid = response.json().get("contact", {}).get("contact_uuid")
    return contact_uuid


def get_contact_info(api_url, contact_uuid,
                     access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiJkZWRkMWY3Ny05N2JmLTRiYTUtYTc2My04MTNiYmFjMjFkMTEiLCJ1aWQiOiJmNmMxMmVjZi1hZTNkLTRhMzgtOGUwNS00NmFiNDM3ODQ2YjQiLCJ1c2VyIjoiMDkzNTc4ODAyNjQiLCJ2ZXJpZmllZF90aW1lIjoxNzU3NzUxOTMzLCJpc3MiOiJhdXRoIiwidXNlci10eXBlIjoicGVyc29uYWwiLCJ1c2VyLXR5cGUtZmEiOiLZvtmG2YQg2LTYrti124wiLCJleHAiOjE3NjAzNDM5MzMsImlhdCI6MTc1Nzc1MTkzM30.j4T18S0y6hG3grsxx-VIw7Go7Ojv_g0XimSZRFNs3k8"
                     , method="POST"):
    url = f"https://api.divar.ir/v8/postcontact/web/contact_info_v2/{api_url}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }
    payload = {"contact_uuid": contact_uuid}

    try:
        # print(url)
        resp = requests.request(method, url, headers=headers, json=payload, timeout=10)
        if not resp.text.strip():
            print(f"[Warning] Empty response for {api_url}")
            return None
        # print(resp.json())
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error] Request failed for {api_url}: {e}")
        return None
    except ValueError as e:
        print(f"[Error] Invalid JSON for {api_url}: {resp.text[:200]}")
        return None

    for widget in data.get("widget_list", []):
        if widget.get("data", {}).get("title") == "شمارهٔ موبایل":
            return widget["data"]["value"]
    return None
