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
            print(f"Extracting search parameters from message: {user_message}")
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
                    - Boş değerleri null olarak bırak, boş string kullanma"""
                },
                {"role": "user", "content": user_message}
            ]
            
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            result = completion.choices[0].message['content']
            print(f"Extracted parameters: {result}")
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                print("Failed to parse JSON response, using default parameters")
                return {"query": user_message, "filters": {}}
                
        except Exception as e:
            print(f"Parameter extraction error: {e}")
            return {"query": user_message, "filters": {}}

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
            
            # Elasticsearch'te arama yap
            products = search_products(
                query=search_params["query"],
                filters=search_params.get("filters", {}),
                size=100  # Performans için ilk 100 sonuç yeterli
            )
            
            # Ürün önerilerini formatla
            product_suggestions = self._format_product_suggestions(products)
            
            # Optimize edilmiş sistem prompt'u
            system_prompt = """Sen bir alışveriş asistanısın. Kullanıcıya kısa ve öz yanıtlar ver.
            - Ürünleri fiyat ve özelliklerine göre karşılaştır
            - Kullanıcının bütçesine uygun ürünleri öner
            - Türkçe yanıt ver"""
            
            # OpenAI ile yanıt oluştur
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {"role": "system", "content": product_suggestions}
            ]
            
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300  # Yanıt uzunluğunu sınırla
            )
            
            return completion.choices[0].message['content']
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

    def reset_conversation(self):
        """Sohbet geçmişini temizle"""
        self.conversation_history = [] 