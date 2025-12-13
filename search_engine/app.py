from flask import Flask, request, render_template
from elasticsearch import Elasticsearch
import time
import json
import os
import re

app = Flask(__name__)

es = Elasticsearch(
    "http://127.0.0.1:9200",
    request_timeout=60,
    max_retries=10,
    retry_on_timeout=True
)

index_name = "divar_final"

try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '..', 'data', 'divar_categories.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        CATEGORY_TREE = json.load(f)
except:
    CATEGORY_TREE = []

PERSIAN_MAP = {ord('ي'): 'ی', ord('ك'): 'ک', ord('۰'): '0', ord('۱'): '1', ord('۲'): '2', ord('۳'): '3', ord('۴'): '4',
               ord('۵'): '5', ord('۶'): '6', ord('۷'): '7', ord('۸'): '8', ord('۹'): '9'}


def normalize_query(text):
    if not text: return ""
    text = re.sub(r'[.;,+\*\-\)\(]', ' ', text)
    return text.translate(PERSIAN_MAP).strip()


def get_smart_suggestion(text):
    body = {
        "suggest": {
            "text": text,
            # 1. پیشنهاد دهنده روی تایتل (اولویت اصلی)
            "suggest_title": {
                "phrase": {
                    "field": "title.trigram",
                    "size": 1,
                    "gram_size": 3,
                    "direct_generator": [{
                        "field": "title",
                        "suggest_mode": "always",
                        "min_word_length": 3,
                        "prefix_length": 0,
                        "max_edits": 2,
                    }],
                    "collate": {
                        "query": {"source": {"match": {"title": {"query": "{{suggestion}}", "operator": "and"}}}},
                        "prune": True
                    }
                }
            },
            # 2. پیشنهاد دهنده روی توضیحات (اگر در تایتل نبود)
            "suggest_desc": {
                "phrase": {
                    "field": "description.trigram",
                    "size": 1,
                    "gram_size": 3,
                    "direct_generator": [{
                        "field": "description",
                        "suggest_mode": "always",
                        "min_word_length": 3,
                        "prefix_length": 0,
                        "max_edits": 2,
                    }],
                    "collate": {
                        # چک کن ببین اگر این پیشنهاد رو بدیم، آیا در توضیحات نتیجه‌ای داره؟
                        "query": {"source": {"match": {"description": {"query": "{{suggestion}}", "operator": "and"}}}},
                        "prune": True
                    }
                }
            }
        }
    }

    try:
        res = es.search(index=index_name, **body)

        # اول چک میکنیم ببینیم تایتل پیشنهادی داره؟
        suggestions_title = res['suggest']['suggest_title'][0]['options']
        if suggestions_title and suggestions_title[0].get('collate_match', False):
            return suggestions_title[0]['text']

        # اگر تایتل نداشت، میریم سراغ توضیحات
        suggestions_desc = res['suggest']['suggest_desc'][0]['options']
        if suggestions_desc and suggestions_desc[0].get('collate_match', False):
            print(f"Found suggestion in Description: {suggestions_desc[0]['text']}")  # برای دیباگ
            return suggestions_desc[0]['text']

    except Exception as e:
        print(f"Suggestion Logic Error: {e}")

    return None


def build_search_body(query, filter_clause, from_offset, results_per_page, fuzziness=None):
    must_clauses = []

    if query:
        if fuzziness:
            # ===  (Optimized Strict Fuzzy) ===
            must_clauses.append({
                "bool": {
                    "should": [
                        # 1. جستجو در تایتل
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^5"],
                                "fuzziness": fuzziness,
                                "operator": "and",
                                "prefix_length": 0,
                                "max_expansions": 20
                            }
                        },
                        # 2. جستجو در توضیحات
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["description", "details.*"],
                                "fuzziness": fuzziness,
                                "operator": "and",
                                "prefix_length": 1,  #
                                "max_expansions": 10
                            }
                        }
                    ]
                }
            })
        else:
            # ===  (Smart Ranking با N-gram توضیحات) ===
            should_clauses = [
                # 1. سوپر اولویت: تایتل دقیق (100)
                {
                    "match_phrase": {
                        "title": {"query": query, "slop": 0, "boost": 100.0}
                    }
                },

                # 2. اولویت دوم: تایتل N-gram (برای جملات دقیق در تایتل) - امتیاز 60
                {
                    "match": {
                        "title.trigram": {"query": query, "operator": "and", "boost": 60.0}
                    }
                },

                # 3. اولویت سوم: تایتل معمولی (40)
                {
                    "match": {
                        "title": {"query": query, "operator": "and", "boost": 40.0}
                    }
                },

                # === اولویت چهارم: عبارت دقیق در توضیحات (با استفاده از Trigram) ===
                {
                    "match": {
                        "description.trigram": {
                            "query": query,
                            "operator": "and",
                            "boost": 20.0  # امتیاز برای عبارت دقیق در توضیحات
                        }
                    }
                },

                # 5. اولویت پنجم: توضیحات معمولی (15)
                {
                    "match_phrase": {
                        "description": {"query": query, "slop": 0, "boost": 15.0}
                    }
                },

                # 6. جستجوی کلی
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["description", "details.*"],
                        "operator": "and",
                        "boost": 2.0
                    }
                }
            ]
            must_clauses.append({"bool": {"should": should_clauses}})

    else:
        must_clauses.append({"match_all": {}})

    body = {
        "from": from_offset,
        "size": results_per_page,
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clause
            }
        },
        "highlight": {
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "fields": {
                "title": {"number_of_fragments": 0},
                "description": {"fragment_size": 150}
            }
        },
        "sort": ["_score"]
    }
    return body


@app.route('/', methods=['GET'])
def search():
    raw_query = request.args.get('q', '')
    query = normalize_query(raw_query)
    original_query = None

    city = request.args.get('city', '')
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))

    results_per_page = 10
    from_offset = (page - 1) * results_per_page

    # لندینگ پیج
    if not query and not city and not category:
        return render_template('index.html', results=[], query="", meta={"total": 0, "took": 0, "page": 1, "pages": 0},
                               filters={"city": "", "cat": ""}, categories=CATEGORY_TREE, suggestion=None,
                               is_landing=True)

    filter_clause = []
    if city: filter_clause.append({"term": {"city": city}})
    if category: filter_clause.append({"term": {"category": category}})

    start_time = time.time()

    # 1. جستجوی دقیق (Exact)
    es_query = build_search_body(query, filter_clause, from_offset, results_per_page, fuzziness=None)
    res = es.search(index=index_name, **es_query)
    total_hits = res['hits']['total']['value']

    suggestion_text = None

    # 2. اگر دقیق پیدا نشد
    if query and total_hits == 0:

        corrected_query = None
        if page == 1:
            corrected_query = get_smart_suggestion(query)

        if corrected_query:
            # اگر پیشنهاد داشتیم، کلمه را عوض می‌کنیم
            original_query = query
            query = corrected_query

            suggestion_text = f"نتایج برای <b>{query}</b> نمایش داده می‌شود."
            if original_query:
                suggestion_text += f" آیا منظور شما <a href='/?q={original_query}&city={city}&category={category}'>{original_query}</a> بود؟"

            # جستجوی مجدد با کلمه صحیح
            es_query_retry = build_search_body(query, filter_clause, from_offset, results_per_page, fuzziness=None)
            res = es.search(index=index_name, **es_query_retry)
            total_hits = res['hits']['total']['value']

        else:
            # ب) سناریوی فازی (وقتی هوش مصنوعی چیزی پیدا نکرد یا صفحه > 1 بود)
            es_query_fuzzy = build_search_body(query, filter_clause, from_offset, results_per_page, fuzziness="AUTO")
            res = es.search(index=index_name, **es_query_fuzzy)
            total_hits = res['hits']['total']['value']

            if total_hits > 0 and page == 1:
                suggestion_text = f"نتایج دقیق برای <b>{query}</b> یافت نشد، موارد مشابه:"

    took = (time.time() - start_time) * 1000

    results = []
    for hit in res['hits']['hits']:
        src = hit['_source']
        full_description = src.get('description', '').replace("\n", "<br>")

        display_title = src.get('title')
        if 'highlight' in hit and 'title' in hit['highlight']:
            display_title = hit['highlight']['title'][0]

        if 'highlight' in hit and 'description' in hit['highlight']:
            display_desc = hit['highlight']['description'][0]
        else:
            raw_desc = src.get('description', '')
            display_desc = raw_desc[:150] + "..." if len(raw_desc) > 150 else raw_desc

        results.append({
            "title": display_title,
            "desc": display_desc,
            "full_desc": full_description,
            "price": src.get('price'),
            "city": src.get('city'),
            "cat": src.get('category'),
            "url": src.get('url'),
            "details": src.get('details', {})
        })

    total_pages = (total_hits + results_per_page - 1) // results_per_page

    return render_template('index.html',
                           results=results,
                           query=query,
                           original_query=original_query,
                           suggestion=suggestion_text,
                           meta={"total": total_hits, "took": round(took, 2), "page": page, "pages": total_pages},
                           filters={"city": city, "cat": category},
                           categories=CATEGORY_TREE,
                           is_landing=False)


if __name__ == '__main__':
    app.run(debug=True)
