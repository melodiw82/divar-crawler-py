# Divar Crawler

This project is a web crawler designed to scrape data from Divar.ir, a popular online classifieds website. It extracts information about various listings, processes the data, and saves it into structured JSON files.

## Features

-   Crawls specified categories and cities on Divar.
-   Extracts detailed information from each listing card.
-   Saves the crawled data in a well-organized JSON format.
-   Handles potential crawling errors and logs progress.

## How It Works

The crawler navigates through Divar's category and city pages, identifying individual listings. For each listing, it extracts key details such as the title, price, description, and other specific attributes. This data is then cleaned and stored in JSON files, which are named according to the category and city they belong to.

## Data Structure

The crawled data is organized into JSON files within the `json_data/` directory. Each file contains a list of objects, where each object represents a single scraped listing. The filenames are formatted as `[city]_[category].json` (e.g., `isfahan_car.json`) or `[category].json` for listings from all cities.

This structure makes it easy to access and analyze the data for specific categories or locations.

### Example Data (`isfahan_car.json`)

Here is an example of a single object from one of the JSON files, representing a car listing:

```json
{
    "href": "https://divar.ir/v/%D8%AF%D9%86%D8%A7-%D9%BE%D9%84%D8%A7%D8%B3-%DB%B9%DB%B8/Aa53BZyd",
    "title": "دنا پلاس ۹۸",
    "bottom_red_text": null,
    "subtitle": "دقایقی پیش در اصفهان، جلفا، خ دو",
    "کارکرد": "۱۰۰٬۰۰۰",
    "مدل (سال تولید)": "۱۳۹۸",
    "رنگ": "سفید",
    "مهلت بیمهٔ شخص ثالث": "۱۰ ماه",
    "گیربکس": "دنده‌ای",
    "نوع سوخت": "بنزینی",
    "قیمت پایه": "۷۵۰،۰۰۰،۰۰۰ تومان",
    "توضیحات": "با سلام .دنا پلاس مدل ۹۸ .ی لکه رنگ پایین درب شاگرد . تمام مصرفی ها عوض شده .دینام و باطری نو. لاستیک جلو خارجی ۱۰۰ درصد و لاستیک عقب ۸۰ درصد. فنی بدون ایراد به هر مکانیک که دوست داشتید ببرید نشون بدید . شیشه دودی. ماشین اسب زین شده بدون یک ریال خرج",
    "مایل به معاوضه": null
}
```


