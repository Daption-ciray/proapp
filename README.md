# AI Powered Product Search API

Modern bir ürün arama API'si. FastAPI, GraphQL, Elasticsearch ve OpenAI entegrasyonu ile gelişmiş arama ve öneri özellikleri sunar.

## Özellikler

- ✨ GraphQL API
- 🔍 Elasticsearch ile güçlü arama
- 🤖 OpenAI destekli alışveriş asistanı
- 🔐 Rate limiting ve güvenlik önlemleri
- 📝 300,000+ ürün veritabanı
- 🌈 Türkçe dil desteği

## Kurulum

1. Gereksinimleri yükleyin:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. `.env` dosyasını oluşturun:
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

3. Docker ile Elasticsearch'ü başlatın:
```bash
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.12.0
```

4. Veritabanını ve indeksi oluşturun:
```bash
python -m app.scripts.sync_data
```

5. Uygulamayı başlatın:
```bash
uvicorn app.main:app --reload
```

## API Kullanımı

GraphQL endpoint: `http://localhost:8000/graphql`

Örnek sorgular:

```graphql
# Ürün araması
query {
  searchProducts(
    query: "spor ayakkabı"
    minPrice: 500
    maxPrice: 2000
  ) {
    brand
    model
    price
    description
  }
}

# Otomatik tamamlama
query {
  suggestProducts(prefix: "nik") {
    suggestions
  }
}
```

## Geliştirme

- Python 3.8+
- FastAPI
- Elasticsearch 8.12.0
- PostgreSQL
- GraphQL (Strawberry)

## Lisans

MIT
