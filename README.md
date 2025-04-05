# Akıllı Alışveriş Asistanı

Kullanıcı tercihlerine ve arama geçmişine dayalı kişiselleştirilmiş alışveriş önerileri sunan bir web uygulaması.

## Özellikler

- 🛍️ Kişiselleştirilmiş ürün önerileri
- 👤 Çoklu kullanıcı desteği
- 📊 Kullanıcı tercihleri analizi
- 🕒 Arama geçmişi takibi
- 💬 Sohbet arayüzü
- 📱 Responsive tasarım

## Teknolojiler

- Python 3.8+
- FastAPI
- SQLite
- Bootstrap 5.3
- HTML/CSS/JavaScript

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/yourusername/shopping-assistant.git
cd shopping-assistant
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac için
# veya
venv\Scripts\activate  # Windows için
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Çevre değişkenlerini ayarlayın:
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

5. Uygulamayı çalıştırın:
```bash
uvicorn main:app --reload
```

6. Tarayıcınızda şu adresi açın: `http://localhost:8000`

## API Endpoints

- `POST /chat`: Kullanıcı mesajlarını işler
- `GET /user/preferences`: Kullanıcı tercihlerini getirir
- `GET /user/preferences/analysis`: Kullanıcı tercih analizini getirir
- `GET /user/search-history`: Kullanıcı arama geçmişini getirir

## Kullanıcı Tipleri

1. Spor Kullanıcısı (user1)
   - Spor ekipmanları ve giyim odaklı
   - Nike markası tercihi
   - 0-1500 TL fiyat aralığı

2. Teknoloji Kullanıcısı (user2)
   - Elektronik ürünler odaklı
   - Apple ve Samsung marka tercihi
   - 0-20000 TL fiyat aralığı

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing`)
3. Değişikliklerinizi commit edin (`git commit -am 'Harika özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/amazing`)
5. Pull Request oluşturun

