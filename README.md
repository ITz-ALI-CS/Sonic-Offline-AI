# ⚡ Sonic — Offline AI Assistant

A fully offline desktop chatbot powered by a custom fine-tuned GPT-2 model. No internet, no API keys, no cloud — everything runs locally on your machine.

## ✨ Features

- 🔒 **100% Offline** — no internet connection required, no data leaves your PC
- 💬 **Persistent Chat History** — conversations saved locally via SQLite
- 🌓 **Dark / Light Theme Toggle**
- 🔍 **Search Past Conversations**
- 📋 **Copy Last Response** to clipboard in one click
- 🔁 **Regenerate** the last answer
- 📤 **Export Chat** to `.txt` or `.md`
- 🔠 **Adjustable Font Size**
- 📌 **Always-on-Top** mode
- ⌨️ **Keyboard Shortcuts** — `Ctrl+L` clear, `Ctrl+E` export, `Ctrl+N` new session, `Esc` focus input

## 🛠️ Tech Stack

- **Python 3** — core language
- **Tkinter** — GUI
- **Hugging Face Transformers + PyTorch** — runs the fine-tuned GPT-2 model
- **SQLite3** — local chat history storage

## 📦 Setup

1. **Clone the repo**
```bash
   git clone https://github.com/ITz-ALI-CS/Sonic-Offline-AI.git
   cd Sonic-Offline-AI
```

2. **Install dependencies**
```bash
   pip install -r requirements.txt
```

3. **Download the model**
   The fine-tuned model file (`model.safetensors`, ~486MB) is too large for GitHub — download it from Google Drive and place it in the same folder as the other files.

4. **Update the paths**
   Open `sonic_gui.py` and update these lines near the top to match your model folder location:
```python
   MODEL_PATH = r"C:\sonic_model_v7"
   DB_PATH = r"C:\sonic_model_v7\sonic_history.db"
   ICON_PATH = r"C:\sonic_model_v7\icon.ico"
```

5. **Run it**
```bash
   python sonic_gui.py
```

## 📁 Project Structure
