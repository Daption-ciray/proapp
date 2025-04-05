from typing import Tuple

def classify_message(message: str) -> Tuple[str, float]:
    """
    Mesajın türünü belirler: ürün araması mı yoksa genel sohbet mi?
    
    Args:
        message: Kullanıcı mesajı
        
    Returns:
        tuple: (mesaj_türü, güven_skoru)
        mesaj_türü: "product_search" veya "general_chat"
    """
    # Ürün araması ile ilgili anahtar kelimeler
    product_keywords = [
        'fiyat', 'ürün', 'ara', 'bul', 'kaç', 'tl', 'lira', 'marka',
        'model', 'satın', 'almak', 'alışveriş', 'indirim', 'kampanya',
        'ne kadar', 'var mı', 'stok'
    ]
    
    # Genel sohbet ile ilgili anahtar kelimeler
    chat_keywords = [
        'merhaba', 'selam', 'nasılsın', 'iyiyim', 'günaydın', 'iyi akşamlar',
        'teşekkür', 'rica', 'görüşürüz', 'bay', 'hoşça kal', 'naber',
        'ne haber', 'nasıl gidiyor'
    ]
    
    message = message.lower()
    
    # Anahtar kelime sayılarını hesapla
    product_count = sum(1 for keyword in product_keywords if keyword in message)
    chat_count = sum(1 for keyword in chat_keywords if keyword in message)
    
    # Eğer her iki kategoride de anahtar kelime yoksa
    if product_count == 0 and chat_count == 0:
        return "general_chat", 0.6  # Varsayılan olarak genel sohbet
        
    # Hangi kategoride daha çok anahtar kelime varsa o kategoriyi seç
    if product_count > chat_count:
        confidence = min(1.0, 0.6 + (product_count * 0.1))
        return "product_search", confidence
    else:
        confidence = min(1.0, 0.6 + (chat_count * 0.1))
        return "general_chat", confidence 