from utils import load_categories, build_category_list, show_menu
from card_extractor import crawl_divar
# from card_extractor_bs4 import crawl_divar_bs

file_path = "data/divar_categories.json"
categories = load_categories(file_path)

city = input("\nInput city name (like divar website): ")
category_list = build_category_list(categories)
show_menu(category_list)
choice = int(input("Choose one of the categories by selecting the number: "))
selected_href = category_list[choice - 1][1]
url = f"https://divar.ir/s/{city}/{selected_href.strip()}"

print("\nSelected URL:", url)

# headless = input("Do you want to be headless? (y/n): ")
# headless = True if headless.lower() == "y" else False
#
# incognito = input("Do you want to be incognito? (y/n): ")
# incognito = True if incognito.lower() == "y" else False

contact_info = input("Do you want to contact info (it may take some time)? (y/n): ")
contact_info = True if contact_info.lower() == "y" else False

headless = input("Do you want it to be headless? (y/n): ")
headless = True if headless.lower() == "y" else False

print("\nScraping Started...")

crawl_divar(url, f"{selected_href}.csv", contact_info, headless)
# crawl_divar_bs(url, f"{selected_href}.csv")
