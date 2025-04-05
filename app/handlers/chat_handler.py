from typing import Dict, Any, Optional
import openai
from app.config import settings
from app.services.product_service import ProductService
from app.services.user_service import UserService

class ChatHandler:
    def __init__(self):
        self.product_service = ProductService()
        self.user_service = UserService()
        openai.api_key = settings.OPENAI_API_KEY
        
    async def handle_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Kullanıcı mesajını işler ve uygun yanıtı döndürür.
        user_id None ise genel sohbet modunda çalışır.
        """
        try:
            if user_id:
                return await self._handle_user_message(message, user_id)
            else:
                return await self._handle_general_chat(message)
        except Exception as e:
            return {
                "response": "Üzgünüm, şu anda bir teknik sorun yaşıyorum. Birazdan tekrar deneyebilir misiniz?"
            }

    async def _handle_user_message(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Belirli bir kullanıcı için mesajı işler.
        """
        # Kullanıcı bilgilerini al
        user_info = await self.user_service.get_user_info(user_id)
        
        # OpenAI için sistem mesajını hazırla
        system_message = f"""
        Sen bir alışveriş asistanısın. Görevlerin:

        1. Kullanıcıyla doğal ve samimi bir şekilde sohbet et. Her türlü konuda konuşabilirsin:
           - Selamlaşma ve hal hatır sorma
           - Günlük sohbetler
           - Hava durumu, spor, güncel konular
           - Ve tabii ki alışveriş!

        2. Eğer kullanıcı ürün sorarsa veya alışverişle ilgili bir konu açarsa, onun tercihlerine göre öneriler sun.

        Kullanıcı profili:
        - Tip: {user_info['type']}
        - İlgilendiği kategoriler: {', '.join(user_info['favorite_categories'])}
        - Tercih ettiği markalar: {', '.join(user_info['preferred_brands'])}
        
        Önemli kurallar:
        - Her zaman Türkçe konuş
        - Samimi ve doğal ol, gerçek bir arkadaş gibi davran
        - Kullanıcının ilgi alanlarına göre sohbeti yönlendir
        - Asla "yapamam", "konuşamam" gibi kısıtlayıcı cevaplar verme
        - Her konuda sohbet edebilirsin, sadece alışverişle sınırlı değilsin
        """
        
        # OpenAI'dan yanıt al
        chat_response = await openai.ChatCompletion.acreate(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            max_tokens=settings.MAX_TOKENS,
            temperature=0.7
        )
        
        ai_response = chat_response.choices[0].message.content
        
        # Eğer mesaj ürün aramasıyla ilgiliyse, ürün bilgilerini ekle
        if any(keyword in message.lower() for keyword in ['fiyat', 'ürün', 'kaç', 'tl', 'lira', 'satın', 'almak', 'ne kadar']):
            search_results = await self.product_service.search_products(
                query=message,
                user_preferences=await self.user_service.get_preferences(user_id)
            )
            
            # Arama geçmişini güncelle
            await self.user_service.update_search_history(user_id, message, len(search_results))
            
            # Ürün sonuçlarını AI yanıtına ekle
            if search_results:
                product_info = "\n\nBulduğum ürünler:\n"
                for i, product in enumerate(search_results[:5], 1):
                    product_info += f"\n{i}. {product['name']}"
                    product_info += f"\n   Fiyat: {product['price']} TL"
                    product_info += f"\n   Marka: {product['brand']}"
                    product_info += f"\n   Satıcı: {product['seller']}\n"
                
                if len(search_results) > 5:
                    product_info += f"\nToplam {len(search_results)} ürün bulundu. Size ilk 5 tanesini gösteriyorum."
                
                ai_response += product_info
        
        return {
            "response": ai_response
        }

    async def _handle_general_chat(self, message: str) -> Dict[str, Any]:
        """
        Genel sohbet modu - kullanıcı bilgisi olmadan çalışır.
        """
        system_message = """
        Sen yardımsever ve arkadaş canlısı bir sohbet asistanısın. Görevlerin:

        1. Her türlü konuda doğal ve samimi sohbet etmek:
           - Selamlaşma ve hal hatır sorma
           - Günlük konular
           - Genel sorular
           - Yardım ve tavsiye

        2. Eğer alışveriş ile ilgili bir soru gelirse, genel öneriler sunmak
           (kullanıcı profili olmadığı için genel tavsiyeler ver)

        Önemli kurallar:
        - Her zaman Türkçe konuş
        - Samimi ve doğal ol, gerçek bir arkadaş gibi davran
        - Her konuda sohbet edebilirsin
        - Asla "yapamam", "konuşamam" gibi kısıtlayıcı cevaplar verme
        - Alışveriş sorularında genel öneriler sun
        """

        # OpenAI'dan yanıt al
        chat_response = await openai.ChatCompletion.acreate(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            max_tokens=settings.MAX_TOKENS,
            temperature=0.7
        )
        
        return {
            "response": chat_response.choices[0].message.content
        } 