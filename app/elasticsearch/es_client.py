from elasticsearch import Elasticsearch
from typing import Optional
from dotenv import load_dotenv
import os

# Force reload environment variables
load_dotenv(override=True)

# Elasticsearch connection settings
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://172.17.0.2:9200")
print(f"Loaded ELASTICSEARCH_URL from env: {ELASTICSEARCH_URL}")

def get_es_client() -> Optional[Elasticsearch]:
    try:
        print(f"Trying to connect to Elasticsearch at: {ELASTICSEARCH_URL}")
        es = Elasticsearch(
            ELASTICSEARCH_URL,
            verify_certs=False,
            request_timeout=60
        )
        if es.ping():
            print("Successfully connected to Elasticsearch")
            return es
        print("Failed to ping Elasticsearch")
        return None
    except Exception as e:
        print(f"Elasticsearch connection error (detailed): {str(e)}")
        return None

# Product index settings
PRODUCT_INDEX = "products"
PRODUCT_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "30s",
        "index": {
            "max_result_window": 300000
        },
        "analysis": {
            "analyzer": {
                "turkish_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "turkish_stop",
                        "turkish_stemmer",
                        "asciifolding"
                    ]
                }
            },
            "filter": {
                "turkish_stop": {
                    "type": "stop",
                    "stopwords": "_turkish_"
                },
                "turkish_stemmer": {
                    "type": "stemmer",
                    "language": "turkish"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "brand": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256},
                    "text": {
                        "type": "text",
                        "analyzer": "turkish_analyzer"
                    }
                }
            },
            "model": {
                "type": "text",
                "analyzer": "turkish_analyzer",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "price": {
                "type": "double",
                "coerce": True
            },
            "category": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256},
                    "text": {
                        "type": "text",
                        "analyzer": "turkish_analyzer"
                    }
                }
            },
            "target_audience": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "description": {
                "type": "text",
                "analyzer": "turkish_analyzer"
            },
            "suggest": {
                "type": "completion",
                "analyzer": "turkish_analyzer"
            }
        }
    }
} 