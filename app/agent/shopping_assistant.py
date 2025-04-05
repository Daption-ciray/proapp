from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv
import os
import json
from ..elasticsearch.indexer import search_products, get_suggestions

# Load environment variables
load_dotenv()

# OpenAI API configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

print("OpenAI API key loaded successfully")

class ShoppingAssistant:
    def __init__(self):
        self.conversation_history = []
        
    def _create_system_prompt(self) -> str:
        return """Sen bir alışveriş asistanısın. Kullanıcıların isteklerini anlayıp onlara en uygun ürünleri önermelisin.
        Önerilerini yaparken şu noktalara dikkat et:
        - Kullanıcının bütçesini sor ve buna uygun ürünler öner
        - Kullanıcının tercih ettiği markaları ve kategorileri dikkate al
        - Ürünlerin özelliklerini detaylı bir şekilde açıkla
        - Kullanıcıya nazik ve yardımcı ol
        - Türkçe yanıt ver
        """

    def _extract_search_parameters(self, user_message: str) -> Dict[str, Any]:
        """Kullanıcı mesajından arama parametrelerini çıkar"""
        try:
            print(f"[DEBUG] Extracting search parameters from message: {user_message}")
            messages = [
                {
                    "role": "system", 
                    "content": """Kullanıcı mesajından arama parametrelerini çıkar ve JSON formatında döndür.
                    Format:
                    {
                        "query": "spor ayakkabı",
                        "filters": {
                            "category": null,
                            "min_price": null,
                            "max_price": null,
                            "brand": null,
                            "target_audience": null
                        }
                    }
                    
                    Örnekler:
                    - "2000tl bütçem var spor ayakkabı arıyorum" ->
                    {
                        "query": "spor ayakkabı",
                        "filters": {
                            "max_price": 2000,
                            "category": "Ayakkabı"
                        }
                    }
                    
                    - "Nike marka 1000-3000 TL arası ayakkabı" ->
                    {
                        "query": "ayakkabı",
                        "filters": {
                            "brand": "Nike",
                            "min_price": 1000,
                            "max_price": 3000,
                            "category": "Ayakkabı"
                        }
                    }
                    
                    Önemli:
                    - Fiyatları her zaman sayısal değer olarak döndür (string değil)
                    - Fiyat aralığı belirtilmişse min_price ve max_price kullan
                    - Sadece bütçe belirtilmişse max_price olarak kullan
                    - Boş değerleri null olarak bırak, boş string kullanma
                    - Eğer spesifik bir ürün sorgusu yoksa query'i null bırak"""
                },
                {"role": "user", "content": user_message}
            ]
            
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1  # Daha tutarlı sonuçlar için
            )
            
            result = completion.choices[0].message['content']
            print(f"[DEBUG] Extracted parameters: {result}")
            
            try:
                params = json.loads(result)
                # Query null ise "*" olarak ayarla
                if not params.get("query"):
                    params["query"] = "*"
                print(f"[DEBUG] Parsed parameters: {json.dumps(params, indent=2, ensure_ascii=False)}")
                return params
            except json.JSONDecodeError:
                print("[DEBUG] Failed to parse JSON response, using default parameters")
                return {"query": "*", "filters": {}}
                
        except Exception as e:
            print(f"[DEBUG] Parameter extraction error: {e}")
            return {"query": "*", "filters": {}}

    def _format_product_suggestions(self, products: List[Dict]) -> str:
        """Ürün önerilerini formatla"""
        if not products:
            return "Maalesef arama kriterlerinize uygun ürün bulamadım. Farklı bir arama yapmak ister misiniz?"
        
        # En fazla 10 ürün göster
        products = sorted(products[:10], key=lambda x: x["price"])
        
        result = []
        result.append("İşte size uygun olabilecek ürünler:\n")
        
        for i, product in enumerate(products, 1):
            result.extend([
                f"{i}. {product['brand']} {product['model']}",
                f"   Fiyat: {product['price']} TL",
                f"   Kategori: {product['category']}",
                f"   {product.get('description', '')}\n"
            ])
        
        return "\n".join(result)

    async def process_message(self, user_message: str) -> str:
        """Kullanıcı mesajını işle ve yanıt üret"""
        try:
            # Arama parametrelerini çıkar
            search_params = self._extract_search_parameters(user_message)
            print(f"[DEBUG] Search parameters: {json.dumps(search_params, indent=2, ensure_ascii=False)}")
            
            # Elasticsearch'te arama yap
            products = search_products(
                query=search_params["query"],
                filters=search_params.get("filters", {}),
                size=100  # Performans için ilk 100 sonuç yeterli
            )
            
            print(f"[DEBUG] Found {len(products)} products")
            if products:
                print(f"[DEBUG] First product: {json.dumps(products[0], indent=2, ensure_ascii=False)}")
            
            # Ürün önerilerini formatla
            product_suggestions = self._format_product_suggestions(products)
            print(f"[DEBUG] Formatted suggestions length: {len(product_suggestions)}")
            
            # RAG için optimize edilmiş sistem prompt'u
            system_prompt = """Sen bir alışveriş asistanısın. Görevin, kullanıcının isteklerine göre ürün önermek.

ÖRNEKLER:

Kullanıcı: "Spor ayakkabı arıyorum, bütçem 500 TL"
Context: "İşte size uygun olabilecek ürünler:
1. Nike Air Max, Fiyat: 450 TL, Kategori: Ayakkabı
2. Adidas Runner, Fiyat: 480 TL, Kategori: Ayakkabı"
Asistan: Bütçenize uygun spor ayakkabıları buldum. Nike Air Max (450 TL) ve Adidas Runner (480 TL) mevcut. Her ikisi de 500 TL bütçenizin altında. Nike Air Max biraz daha ekonomik bir seçenek.

Kullanıcı: "2000 TL'ye laptop var mı?"
Context: "Maalesef arama kriterlerinize uygun ürün bulamadım. Farklı bir arama yapmak ister misiniz?"
Asistan: Maalesef 2000 TL bütçe ile uygun bir laptop bulamadım. Bütçenizi biraz artırmanızı veya ikinci el seçenekleri değerlendirmenizi öneririm.

ÖNEMLİ KURALLAR:
1. SADECE context'te verilen ürünleri önerebilirsin
2. Context'te olmayan ürünleri ASLA önerme
3. Fiyatları ve özellikleri değiştirme
4. Context'teki ürün listesini aynen kullan
5. Kendi kafandan ürün uydurma

KULLANICI MESAJI:
{user_message}

CONTEXT (SADECE BU ÜRÜNLERİ ÖNEREBİLİRSİN):
{product_suggestions}

Yukarıdaki context'te verilen ürün listesini kullanarak kullanıcıya yardımcı ol. SADECE bu listedeki ürünleri kullanabilirsin!"""
            
            # OpenAI ile yanıt oluştur
            messages = [
                {
                    "role": "system", 
                    "content": system_prompt.format(
                        user_message=user_message,
                        product_suggestions=product_suggestions
                    )
                }
            ]
            
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,  # Daha da tutarlı yanıtlar için
                max_tokens=800
            )
            
            response = completion.choices[0].message['content']
            print(f"[DEBUG] Final response length: {len(response)}")
            return response
            
        except Exception as e:
            print(f"[DEBUG] Error processing message: {e}")
            return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

    def reset_conversation(self):
        """Sohbet geçmişini temizle"""
        self.conversation_history = [] 