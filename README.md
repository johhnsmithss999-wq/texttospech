# texttospech

# VoxCPM2 Telegram Voice Clone TTS Bot 🎙️🤖

Telegram Bot សម្រាប់បម្លែង **Text to Speech (TTS)** ដោយប្រើបច្ចេកវិទ្យា **Voice Cloning** ជាមួយ **VoxCPM2 (OpenBMB)**។

---

## ✨ លក្ខណៈពិសេស (Features)

1. **កន្លែងដាក់សំឡេងសម្រាប់ Clone (Voice Cloning Upload):**
   - គ្រាន់តែថត **Voice Note (Voice Message)** ឬផ្ញើ **Audio File (.wav, .mp3, .m4a)** ទៅកាន់ Bot
   - Bot នឹងបម្លែង និងរក្សាទុកជាគំរូសំឡេងរបស់អ្នកដោយស្វ័យប្រវត្តិ
2. **Text to Speech with Cloned Voice:**
   - វាយអត្ថបទជាអក្សរ (Text) ផ្ញើទៅកាន់ Bot
   - Bot នឹងបម្លែងជាសំឡេងនិយាយដោយប្រើ **សំឡេងផ្ទាល់ខ្លួនរបស់អ្នក** ដែលបាន Clone រួច
3. **Hi-Fi Continuation & Zero-Shot Timbre Cloning:**
   - គាំទ្រការផ្ញើ Audio ធម្មតា (Timbre Clone)
   - គាំទ្រការសរសេរ Caption ជាអត្ថបទនៃសំឡេងនោះ ដើម្បីទទួលបានកម្រិតច្បាស់ខ្ពស់បំផុត (Hi-Fi Mode)
4. **ការគ្រប់គ្រងសំឡេង និងការកំណត់ (Management & Settings):**
   - `/myvoice`: ស្តាប់សំឡេងដែលបានកំណត់បច្ចុប្បន្ន
   - `/clearvoice`: លុបសំឡេងចាស់ ដើម្បីដាក់សំឡេងថ្មី
   - `/settings`: កែសម្រួលល្បឿន និងគុណភាព (Inference Steps & CFG scale)
   - `/help`: មើលការណែនាំលម្អិត

---

## 🛠️ ការដំឡើង និងការប្រើប្រាស់ (Setup & How to Run)

### ជំហានទី 1: យក Telegram Bot Token
1. បើកកម្មវិធី Telegram ហើយស្វែងរក **@BotFather**
2. វាយ `/newbot` រួចធ្វើតាមការណែនាំដើម្បីបង្កើត Bot ថ្មី
3. ចម្លងយក **API Token**

### ជំហានទី 2: បញ្ចូល Token ក្នុង File `.env`
ចម្លង `.env.example` ទៅជា `.env` ហើយបិទភ្ជាប់ Token របស់អ្នក៖
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

### ជំហានទី 3: ដំណើរការ Bot
អ្នកអាចដំណើរការតាមវិធី 2 យ៉ាង៖
- **វិធីទី 1:** Double-click លើ file `run.bat`
- **វិធីទី 2:** ដំណើរការតាម Terminal / PowerShell:
  ```bash
  python bot.py
  ```
