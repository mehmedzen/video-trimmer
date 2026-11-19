# 🎬 Smart Video Trimmer (Drag & Paste)

Smart Video Trimmer, video içerik üreticileri ve hızlıca video kesmek isteyenler için tasarlanmış **hafif, kayıpsız ve ultra pratik** bir Windows masaüstü aracıdır.

Videoyu tekrar encode edip dakikalarca beklemek yerine **FFmpeg Stream Copy** teknolojisiyle kalite kaybı yaşamadan **1 saniyede** keser.

---

![Smart Video Trimmer Önizleme](preview.jpg)

---

## 🌟 Neden Farklı? (Öne Çıkan Özellikler)

- 🖱️ **Klasöre / Masaüstüne Sürükle-Bırak (Drag-to-Save):**  
  Timeline üzerinde belirlediğiniz aralığı fareyle tutup doğrudan Windows Dosya Gezgini'ndeki bir klasöre veya masaüstüne sürükleyin. Parça anında oraya kaydedilir!
- 📋 **Panoya Kopyala & Yapıştır (Ctrl+C & Ctrl+V):**  
  Aralığı seçip `Ctrl+C` yapın; bilgisayarınızdaki herhangi bir klasöre gidip `Ctrl+V` yaptığınızda kesilmiş video dosyanız hazır.
- ⚡ **Kayıpsız & Işık Hızında (Lossless):**  
  Videonun formatını yeniden kodlamaz (`-c copy`), bu sayede 4K videolar bile saniyeler içinde kesilir ve orijinal görüntü kalitesi %100 korunur.
- 🎯 **Kolay Video Yükleme:**  
  İstediğiniz videoyu doğrudan uygulamanın üzerine sürükleyip bırakın.
- ⏱️ **Milisaniyelik Hassasiyet:**  
  Sağ tıkla aralık seçimi ve ayarlanabilir hassas tutamaçlar (handles).

---

## 📥 İndir & Çalıştır (Kurulumsuz .EXE)

Herhangi bir Python veya ek kütüphane kurmanıza gerek yoktur:

1. [Releases](../../releases) bölümünden en güncel **`SmartVideoTrimmer.exe`** dosyasını indirin.
2. Çift tıklayarak doğrudan kullanmaya başlayın!

---

## 🛠️ Kaynak Koddan Çalıştırma (Geliştiriciler İçin)

Python ile çalıştırmak veya projeye katkı sunmak isterseniz:

```bash
# 1. Repoyu klonlayın
git clone https://github.com/KULLANICI_ADINIZ/video-trimmer.git
cd video-trimmer

# 2. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 3. Başlatın
python app.py
```

---

## 🎮 Kısayollar ve Kullanım

| Eylem | Nasıl Yapılır? |
|---|---|
| **Video Aç** | Pencereye video sürükleyin veya `Ctrl+O` |
| **Oynat / Duraklat** | `Boşluk (Space)` tuşu |
| **Aralık Seç** | Timeline üzerinde **Sağ Tık ile basılı tutup sürükleyin** (veya `Shift + Sol Tık`) |
| **Parçayı Kopyala** | `Ctrl + C` (sonra klasörde `Ctrl + V`) |
| **Doğrudan Klasöre Bırak** | Seçilen sarı alandan tutup masaüstüne/klasöre sürükleyin |
| **Farklı Kaydet** | `✂ Farklı Kaydet...` butonu |

---

## 📄 Lisans
Bu proje [MIT](LICENSE) lisansı altındadır.
