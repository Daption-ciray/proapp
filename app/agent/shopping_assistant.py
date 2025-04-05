from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv
import os
import json
from ..elasticsearch.indexer import search_products, get_suggestions
from ..models.user_preferences import UserPreferencesManager
from ..database.database import SessionLocal

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
        self.db = SessionLocal()
        self.prefs_manager = UserPreferencesManager(self.db)
        
    def _create_system_prompt(self, user_id: Optional[str] = None) -> str:
        base_prompt = """Sen hem bir alışveriş asistanı hem de arkadaş canlısı bir sohbet arkadaşısın. 
        
        GÖREVLER:
        1. Kullanıcıyla doğal ve samimi bir şekilde sohbet et
        2. Günlük konuşmalara (hal hatır sorma, selamlaşma vb.) doğal yanıtlar ver
        3. Alışveriş ile ilgili konularda profesyonel önerilerde bulun
        4. Kullanıcının ruh haline ve konuşma tarzına uyum sağla
        
        KONUŞMA TARZI:
        - Samimi ve arkadaş canlısı ol
        - Türkçe karakterleri doğru kullan
        - Emojiler ve günlük konuşma dili kullanabilirsin
        - Kısa ve öz cevaplar ver
        """

        if user_id:
            # Kullanıcı tercihlerini al
            prefs = self.prefs_manager.get_user_preferences(user_id)
            recent_searches = self.prefs_manager.get_recent_searches(user_id, limit=5)
            analysis = self.prefs_manager.analyze_user_preferences(user_id)

            # Tercihleri prompt'a ekle
            preferences_context = f"""
            Kullanıcı Tercihleri:
            - Favori Kategoriler: {', '.join(prefs['favorite_categories']) if prefs['favorite_categories'] else 'Henüz belirlenmedi'}
            - Tercih Edilen Markalar: {', '.join(prefs['preferred_brands']) if prefs['preferred_brands'] else 'Henüz belirlenmedi'}
            - Tipik Fiyat Aralığı: {prefs['price_range'].get('min', 'Belirsiz')} TL - {prefs['price_range'].get('max', 'Belirsiz')} TL

            Son Aramalar:
            {chr(10).join(f"- {search['query']} (Filtreler: {json.dumps(search['filters'], ensure_ascii=False)})" for search in recent_searches)}

            Analiz:
            - En Çok Aranan Kategoriler: {', '.join(item['category'] for item in analysis['top_categories'])}
            - En Çok Aranan Markalar: {', '.join(item['brand'] for item in analysis['top_brands'])}
            - Ortalama Fiyat Aralığı: {analysis['average_price_range']['min']} TL - {analysis['average_price_range']['max']} TL
            """
            base_prompt += preferences_context

        base_prompt += """
        ÖRNEKLER:

        Kullanıcı: "Nasılsın?"
        Asistan: "İyiyim, teşekkür ederim! Sen nasılsın? 😊"

        Kullanıcı: "Spor ayakkabı arıyorum, bütçem 500 TL"
        Context: "İşte size uygun olabilecek ürünler:
        1. Nike Air Max, Fiyat: 450 TL, Kategori: Ayakkabı
        2. Adidas Runner, Fiyat: 480 TL, Kategori: Ayakkabı"
        Asistan: Bütçenize uygun spor ayakkabıları buldum. Nike Air Max (450 TL) ve Adidas Runner (480 TL) mevcut. Her ikisi de 500 TL bütçenizin altında. Nike Air Max biraz daha ekonomik bir seçenek.

        ÖNEMLİ KURALLAR:
        1. Alışveriş önerilerinde SADECE context'te verilen ürünleri önerebilirsin
        2. Context'te olmayan ürünleri ASLA önerme
        3. Fiyatları ve özellikleri değiştirme
        4. Context'teki ürün listesini aynen kullan
        5. Kendi kafandan ürün uydurma
        6. Günlük sohbetlerde doğal ve samimi ol
        """
        return base_prompt

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
                            "color": null,
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

                    - "Kırmızı renkli converse" ->
                    {
                        "query": "ayakkabı",
                        "filters": {
                            "brand": "Converse",
                            "color": "kırmızı",
                            "category": "Ayakkabı"
                        }
                    }
                    
                    Önemli:
                    - Fiyatları her zaman sayısal değer olarak döndür (string değil)
                    - Fiyat aralığı belirtilmişse min_price ve max_price kullan
                    - Sadece bütçe belirtilmişse max_price olarak kullan
                    - Boş değerleri null olarak bırak, boş string kullanma
                    - Renk belirtilmişse color parametresini ekle
                    - Marka belirtilmişse brand parametresini ekle
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
            return """Üzgünüm, arama kriterlerinize uygun ürün bulamadım. Size daha iyi yardımcı olabilmem için:

1. Fiyat aralığınızı biraz genişletebilirsiniz
2. Farklı markalar deneyebilirsiniz
3. Benzer kategorilerde arama yapabiliriz
4. Arama kriterlerinizi değiştirebilirsiniz

Ne yapmak istersiniz? Size yardımcı olmaktan memnuniyet duyarım! 😊"""
        
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

    async def process_message(self, user_message: str, user_id: Optional[str] = None) -> str:
        """Kullanıcı mesajını işle ve yanıt üret"""
        try:
            # Önce mesajın alışveriş ile ilgili olup olmadığını kontrol et
            is_shopping_related = await self._is_shopping_query(user_message)
            
            if not is_shopping_related:
                # Genel sohbet yanıtı oluştur
                messages = [
                    {
                        "role": "system", 
                        "content": self._create_system_prompt(user_id)
                    },
                    {"role": "user", "content": user_message}
                ]
                
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800
                )
                
                return completion.choices[0].message['content']
            
            # Alışveriş ile ilgili mesaj ise normal akışa devam et
            search_params = self._extract_search_parameters(user_message)
            print(f"[DEBUG] Search parameters: {json.dumps(search_params, indent=2, ensure_ascii=False)}")
            
            if user_id:
                prefs = self.prefs_manager.get_user_preferences(user_id)
                if not search_params.get("filters"):
                    search_params["filters"] = {}
                if prefs["preferred_brands"] and not search_params["filters"].get("brand"):
                    search_params["filters"]["preferred_brands"] = prefs["preferred_brands"]
                if prefs["favorite_categories"] and not search_params["filters"].get("category"):
                    search_params["filters"]["preferred_categories"] = prefs["favorite_categories"]

            # İlk aramayı yap
            products = search_products(
                query=search_params["query"],
                filters=search_params.get("filters", {}),
                size=100
            )
            
            print(f"[DEBUG] Found {len(products)} products")
            
            # Ürün bulunamadıysa, filtreleri gevşeterek tekrar dene
            if not products:
                # Kullanıcının orijinal arama terimlerini sakla
                original_query = search_params["query"]
                original_filters = search_params.get("filters", {}).copy()
                
                # Renk filtresi varsa kaldır ve tekrar dene
                if "color" in search_params.get("filters", {}):
                    search_params["filters"].pop("color")
                    products = search_products(
                        query=search_params["query"],
                        filters=search_params.get("filters", {}),
                        size=100
                    )
                    
                    if products:
                        response = f"""Üzgünüm, tam olarak istediğiniz renkte ürün bulamadım. Ancak aradığınız ürünün diğer renk seçenekleri mevcut:

{self._format_product_suggestions(products)}

İsterseniz:
1. Farklı bir renk seçebilirsiniz
2. Başka bir marka deneyebiliriz
3. Benzer ürünlere bakabiliriz

Size nasıl yardımcı olabilirim?"""
                        return response

                # Marka spesifik arama yap
                if "brand" in search_params.get("filters", {}):
                    brand_name = search_params["filters"]["brand"]
                    similar_products = search_products(
                        query=brand_name,
                        filters={},
                        size=10
                    )
                    
                    if similar_products:
                        response = f"""Üzgünüm, aradığınız spesifik {brand_name} ürününü bulamadım, ancak bu markadan başka ürünler mevcut:

{self._format_product_suggestions(similar_products)}

İsterseniz:
1. Bu ürünlerden birini inceleyebilirsiniz
2. Farklı bir marka deneyebiliriz
3. Benzer ürünlere bakabiliriz

Nasıl devam etmek istersiniz?"""
                        return response

            if user_id:
                self.prefs_manager.add_search_history(
                    user_id=user_id,
                    query=search_params["query"],
                    filters=search_params.get("filters", {}),
                    results_count=len(products)
                )
            
            product_suggestions = self._format_product_suggestions(products)
            
            messages = [
                {
                    "role": "system", 
                    "content": self._create_system_prompt(user_id)
                },
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": "İşte arama sonuçlarında bulunan ürünler:"},
                {"role": "system", "content": product_suggestions}
            ]
            
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.2,
                max_tokens=800
            )
            
            response = completion.choices[0].message['content']
            if not products:
                response += "\n\nBaşka bir şey sormak isterseniz, size yardımcı olmaktan memnuniyet duyarım."
            return response
            
        except Exception as e:
            print(f"[DEBUG] Error processing message: {e}")
            return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

    async def _is_shopping_query(self, message: str) -> bool:
        """Mesajın alışveriş ile ilgili olup olmadığını kontrol et"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """Verilen mesajın alışveriş/ürün araması ile ilgili olup olmadığını belirle.
                    Sadece "true" veya "false" yanıtı ver.
                    
                    Örnekler:
                    - "Nasılsın?" -> false
                    - "Spor ayakkabı arıyorum" -> true
                    - "İyi günler!" -> false
                    - "Laptop fiyatları ne kadar?" -> true
                    """
                },
                {"role": "user", "content": message}
            ]
            
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1,
                max_tokens=10
            )
            
            result = completion.choices[0].message['content'].lower().strip()
            return result == "true"
            
        except Exception as e:
            print(f"[DEBUG] Error in is_shopping_query: {e}")
            return True  # Hata durumunda varsayılan olarak alışveriş sorgusu kabul et

    def reset_conversation(self, user_id: Optional[str] = None):
        """Sohbet geçmişini temizle"""
        self.conversation_history = [] 