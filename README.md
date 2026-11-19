# 🎬 Smart Video Trimmer (Drag & Paste)

Hızlı, kayıpsız ve pratik bir Windows video kırpma aracı. Videonun istediğiniz bölümünü timeline üzerinden seçip, doğrudan **Masaüstüne / Dosya Gezgini'ne sürükleyip bırakarak** veya **Ctrl+C / Ctrl+V** ile yapıştırarak yeni bir dosya olarak kaydedebilirsiniz.

---

## ✨ Özellikler

- ⚡ **Işık Hızında & Kayıpsız Kesim (Lossless Stream Copy):** FFmpeg altyapısı sayesinde yeniden encode etmez (`-c copy`), saniyeler içinde kalite kaybı olmadan keser.
- 🖱️ **Masaüstüne / Klasöre Sürükle-Bırak (Drag-Out):** Timeline'da seçtiğiniz aralığı fareyle tutup doğrudan masaüstüne veya herhangi bir klasöre sürükleyip bırakabilirsiniz.
- 📋 **Kopyala / Yapıştır (Ctrl+C & Ctrl+V):** Seçtiğiniz aralığı kopyalayıp istediğiniz klasörde yapıştırarak anında yeni video parçası oluşturabilirsiniz.
- 🎯 **Kolay Video Yükleme:** İstediğiniz videoyu doğrudan pencereye sürükleyip bırakmanız yeterlidir.
- 🕒 **Milisaniye Hassasiyetinde Zaman Çizelgesi:** Hassas başlangıç ve bitiş tutamaçları ile tam istediğiniz anı yakalayın.

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) (PATH ortam değişkenine ekli olmalıdır)

### 1. Repoyu Klonlayın
```bash
git clone https://github.com/KULLANICI_ADINIZ/video-trimmer.git
cd video-trimmer
```

### 2. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 3. Çalıştırın
```bash
python app.py
```
*(Veya Windows'ta doğrudan `run.bat` dosyasına çift tıklayabilirsiniz.)*

---

## 📖 Kullanım Kılavuzu

1. **Video Aç:** Videoyu pencereye sürükleyip bırakın veya `📁 Video Aç...` butonuna tıklayın.
2. **Aralık Seç:** 
   - Timeline üzerinde **Sağ Tık ile basılı tutup sürükleyerek** aralığı seçin (Shift + Sol tık da desteklenir).
   - Sarı alanın sağ/sol kollarından tutarak süreyi ince ayar yapabilirsiniz.
3. **Dışa Aktar:**
   - **Yöntem 1:** Sarı seçili alanı fareyle tutup Windows Gezgini'ndeki bir klasöre veya Masaüstüne sürükleyin.
   - **Yöntem 2:** `Ctrl+C` yapın, ardından istediğiniz klasöre gidip `Ctrl+V` ile yapıştırın.
   - **Yöntem 3:** `✂ Farklı Kaydet...` butonuna tıklayın.

---

## 📄 Lisans
MIT License. Dilediğiniz gibi kullanabilir ve geliştirebilirsiniz.
