import json
import os
import re
import time
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(
    "http://127.0.0.1:9200",
    request_timeout=60,
    max_retries=10,
    retry_on_timeout=True
)

index_name = "divar_final"
data_dir = r"E:\uni\divar_crawler\json_data"

PERSIAN_MAP = {
    ord('ي'): 'ی', ord('ك'): 'ک', ord('ة'): 'ه',
    ord('۰'): '0', ord('۱'): '1', ord('۲'): '2', ord('۳'): '3', ord('۴'): '4',
    ord('۵'): '5', ord('۶'): '6', ord('۷'): '7', ord('۸'): '8', ord('۹'): '9'
}


def clean_text(text):
    if not isinstance(text, str): return text
    if not text: return ""
    text = text.translate(PERSIAN_MAP)
    text = text.replace('\u200c', ' ')
    text = re.sub(r'[!@#%^&*()_{}\[\]<>,?/~`]', ' ', text)
    return " ".join(text.split())


if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

settings = {
    "settings": {
        "analysis": {
            "filter": {
                "my_shingle_filter": {
                    "type": "shingle",
                    "min_shingle_size": 2,
                    "max_shingle_size": 3,
                    "output_unigrams": True
                }
            },
            "analyzer": {
                "persian_custom": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "arabic_normalization", "persian_normalization"]
                },
                "trigram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "arabic_normalization", "my_shingle_filter"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "persian_custom",
                "fields": {
                    "trigram": {
                        "type": "text",
                        "analyzer": "trigram_analyzer"
                    }
                }
            },
            # N-gram برای توضیحات هم فعال است
            "description": {
                "type": "text",
                "analyzer": "persian_custom",
                "fields": {
                    "trigram": {
                        "type": "text",
                        "analyzer": "trigram_analyzer"
                    }
                }
            },
            "category": {"type": "keyword"},
            "city": {"type": "keyword"},
            "url": {"type": "keyword"},
            "price": {"type": "keyword"}
        }
    }
}

es.indices.create(index=index_name, **settings)
print(f"Index '{index_name}' created successfully.")

json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
total_files_count = len(json_files)
total_size_bytes = sum(os.path.getsize(os.path.join(data_dir, f)) for f in json_files)
total_size_mb = total_size_bytes / (1024 * 1024)


def generate_docs():
    for filename in json_files:
        city = "یزد"
        if filename.startswith("isfahan_"):
            city = "اصفهان"
        elif filename.startswith("tehran_"):
            city = "تهران"
        elif filename.startswith("mashhad_"):
            city = "مشهد"

        cat_slug = filename.replace(".json", "").replace("isfahan_", "").replace("tehran_", "").replace("mashhad_", "")
        file_path = os.path.join(data_dir, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict): data = [data]

                for item in data:
                    standard_fields = ["title", "href", "subtitle", "قیمت", "توضیحات", "bottom_red_text"]
                    details = {}
                    for k, v in item.items():
                        if k not in standard_fields and v is not None:
                            details[k] = clean_text(v)

                    doc = {
                        "_index": index_name,
                        "_source": {
                            "title": clean_text(item.get("title")),
                            "description": clean_text(item.get("توضیحات", "")),
                            "price": clean_text(item.get("قیمت", "توافقی")),
                            "subtitle": clean_text(item.get("subtitle")),
                            "url": item.get("href"),
                            "city": city,
                            "category": cat_slug,
                            "details": details
                        }
                    }
                    yield doc
        except Exception as e:
            print(f"Error reading {filename}: {e}")


print("Indexing started...")
start_time = time.time()

success, failed = helpers.bulk(es, generate_docs())

end_time = time.time()
elapsed_time = end_time - start_time

print("\n" + "=" * 30)
print("      INDEXING REPORT      ")
print("=" * 30)
print(f"Docs Indexed : {success}")
print(f"Files Read   : {total_files_count}")
print(f"Total Size   : {total_size_mb:.2f} MB")
print(f"Time Taken   : {elapsed_time:.2f} seconds")
print(f"Avg Speed    : {success / elapsed_time:.0f} docs/sec")
print("=" * 30)
