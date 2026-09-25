import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from transformers import AutoTokenizer, GPT2LMHeadModel
import torch
import threading
import sqlite3
from datetime import datetime
import os

MODEL_PATH = r"C:\sonic_model_v7"
DB_PATH = r"C:\sonic_model_v7\sonic_history.db"
ICON_PATH = r"C:\sonic_model_v7\icon.ico"

torch.set_num_threads(os.cpu_count())

THEMES = {
    "dark": {
        "bg": "#0b0d13", "panel": "#12151f", "chat_bg": "#0b0d13",
        "user_text": "#4fd1e8", "sonic_text": "#c9a8ff",
        "accent": "#00d4ff", "accent2": "#a259ff", "muted": "#5b5f6e",
        "entry_bg": "#181c28", "entry_fg": "#eef0f5", "border": "#232838"
    },
    "light": {
        "bg": "#f4f6fb", "panel": "#ffffff", "chat_bg": "#fafbff",
        "user_text": "#0077a3", "sonic_text": "#6b21d6",
        "accent": "#0077a3", "accent2": "#6b21d6", "muted": "#8b8fa3",
        "entry_bg": "#ffffff", "entry_fg": "#111111", "border": "#e2e5ee"
    }
}
current_theme = "dark"
show_timestamps = True
font_size = 10

def T():
    return THEMES[current_theme]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, message TEXT, timestamp TEXT)""")
    conn.commit()
    conn.close()

def save_message(role, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (role, message, timestamp) VALUES (?, ?, ?)",
                   (role, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def load_history(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, message, timestamp FROM chat_history ORDER BY id ASC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    total = cursor.fetchone()[0]
    conn.close()
    return total

init_db()

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)
model.eval()

conversation_history = []
last_question = ""
last_response = ""
MAX_HISTORY = 3

def build_prompt(question):
    context = ""
    for q, a in conversation_history[-MAX_HISTORY:]:
        context += f"Q: {q}\nA: {a}\n"
    context += f"Q: {question}\nA:"
    return context

def ask_sonic(question, max_new_tokens=30):
    prompt = build_prompt(question)
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                 repetition_penalty=1.3, pad_token_id=tokenizer.eos_token_id)
    full_text = tokenizer.decode(output[0], skip_special_tokens=True)
    answer = full_text[len(prompt):].split("Q:")[0].strip()
    for punct in [".", "!", "?"]:
        idx = answer.find(punct)
        if idx != -1:
            answer = answer[:idx+1]
            break
    return answer

def insert_bubble(sender, text, timestamp=None):
    ts = timestamp or datetime.now().strftime("%H:%M")
    tag = "user_msg" if sender == "You" else "sonic_msg"
    chat_area.insert(tk.END, f"{sender}  ", (f"{tag}_name",))
    if show_timestamps:
        chat_area.insert(tk.END, f"{ts}\n", ("timestamp",))
    else:
        chat_area.insert(tk.END, "\n")
    chat_area.insert(tk.END, f"{text}\n\n", (tag,))
    chat_area.see(tk.END)
    update_stats()

def update_stats():
    total = get_stats()
    stats_label.config(text=f"{total} messages saved")

def send_message(event=None):
    global last_question, last_response
    user_text = entry.get().strip()
    if not user_text:
        return
    entry.delete(0, tk.END)
    insert_bubble("You", user_text)
    save_message("user", user_text)
    last_question = user_text
    conversation_history.append((user_text, ""))

    status_label.config(text="Sonic is thinking...")
    send_btn.config(state=tk.DISABLED)
    regen_btn.config(state=tk.DISABLED)

    def get_response():
        global last_response
        response = ask_sonic(user_text)
        last_response = response
        conversation_history[-1] = (user_text, response)
        insert_bubble("Sonic", response)
        save_message("sonic", response)
        status_label.config(text="Online - Offline AI")
        send_btn.config(state=tk.NORMAL)
        regen_btn.config(state=tk.NORMAL)

    threading.Thread(target=get_response).start()

def regenerate_last():
    if not last_question:
        return
    status_label.config(text="Regenerating...")
    def get_response():
        global last_response
        response = ask_sonic(last_question)
        last_response = response
        insert_bubble("Sonic", f"(regenerated) {response}")
        save_message("sonic", response)
        status_label.config(text="Online - Offline AI")
    threading.Thread(target=get_response).start()

def clear_chat():
    if messagebox.askyesno("Clear Chat", "Clear the visible chat? (Saved history stays intact)"):
        chat_area.delete(1.0, tk.END)
        conversation_history.clear()
        insert_bubble("Sonic", "Chat cleared. Let's start fresh.")

def new_session():
    if messagebox.askyesno("New Session", "Start a brand new conversation?"):
        chat_area.delete(1.0, tk.END)
        conversation_history.clear()
        save_message("system", "--- New Session Started ---")
        insert_bubble("Sonic", "Starting a new session. What's up?")

def export_chat():
    path = filedialog.asksaveasfilename(defaultextension=".txt",
                                        filetypes=[("Text files", "*.txt"), ("Markdown", "*.md")])
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(chat_area.get(1.0, tk.END))
        messagebox.showinfo("Exported", "Chat exported successfully!")

def copy_last_response():
    if last_response:
        root.clipboard_clear()
        root.clipboard_append(last_response)
        status_label.config(text="Copied last response!")
        root.after(2000, lambda: status_label.config(text="Online - Offline AI"))

def search_history():
    query = search_entry.get().strip().lower()
    if not query:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, message, timestamp FROM chat_history WHERE LOWER(message) LIKE ? ORDER BY id DESC LIMIT 20",
                   (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()
    chat_area.delete(1.0, tk.END)
    if results:
        insert_bubble("Sonic", f"Found {len(results)} match(es) for '{query}':")
        for role, message, ts in reversed(results):
            sender = "You" if role == "user" else "Sonic"
            insert_bubble(sender, message, ts.split(" ")[1][:5] if " " in ts else "")
    else:
        insert_bubble("Sonic", f"No matches found for '{query}'.")

def toggle_timestamps():
    global show_timestamps
    show_timestamps = not show_timestamps
    status_label.config(text=f"Timestamps {'on' if show_timestamps else 'off'}")

def change_font_size(delta):
    global font_size
    font_size = max(8, min(16, font_size + delta))
    apply_theme()

def toggle_always_on_top():
    is_on = root.attributes("-topmost")
    root.attributes("-topmost", not is_on)
    status_label.config(text=f"Always on top: {'ON' if not is_on else 'OFF'}")

def toggle_theme():
    global current_theme
    current_theme = "light" if current_theme == "dark" else "dark"
    apply_theme()

def apply_theme():
    t = T()
    root.configure(bg=t["bg"])
    header.configure(bg=t["panel"])
    title_label.configure(bg=t["panel"], fg=t["accent"])
    subtitle_label.configure(bg=t["panel"], fg=t["muted"])
    toolbar.configure(bg=t["panel"])
    search_frame.configure(bg=t["panel"])
    chat_area.configure(bg=t["chat_bg"], font=("Segoe UI", font_size))
    chat_area.tag_configure("user_msg_name", foreground=t["user_text"], font=("Segoe UI", font_size-1, "bold"))
    chat_area.tag_configure("sonic_msg_name", foreground=t["accent2"], font=("Segoe UI", font_size-1, "bold"))
    chat_area.tag_configure("timestamp", foreground=t["muted"], font=("Segoe UI", font_size-2))
    chat_area.tag_configure("user_msg", foreground=t["user_text"], font=("Segoe UI", font_size))
    chat_area.tag_configure("sonic_msg", foreground=t["sonic_text"], font=("Segoe UI", font_size))
    bottom_bar.configure(bg=t["bg"])
    entry_frame.configure(bg=t["bg"])
    entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["entry_fg"])
    search_entry.configure(bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["entry_fg"])
    status_bar.configure(bg=t["panel"])
    status_label.configure(bg=t["panel"], fg=t["muted"])
    stats_label.configure(bg=t["panel"], fg=t["muted"])
    for btn in [clear_btn, export_btn, copy_btn, theme_btn, newsession_btn, ts_btn, fontup_btn, fontdown_btn, ontop_btn, search_btn, regen_btn]:
        btn.configure(bg=t["panel"], fg=t["accent"], activebackground=t["entry_bg"], relief=tk.FLAT, bd=0)
    send_btn.configure(bg=t["accent"], fg="#000000", relief=tk.FLAT, bd=0)

root = tk.Tk()
root.title("Sonic - Offline AI Assistant")
root.geometry("560x720")
root.minsize(440, 520)
if os.path.exists(ICON_PATH):
    try:
        root.iconbitmap(ICON_PATH)
    except Exception:
        pass

header = tk.Frame(root, height=90)
header.pack(fill=tk.X)
header.pack_propagate(False)
title_label = tk.Label(header, text="⚡ SONIC", font=("Segoe UI", 18, "bold"))
title_label.pack(anchor="w", padx=15, pady=(10,0))
subtitle_label = tk.Label(header, text="Offline AI Assistant - No Internet Needed", font=("Segoe UI", 9))
subtitle_label.pack(anchor="w", padx=15)

toolbar = tk.Frame(header)
toolbar.pack(fill=tk.X, padx=15, pady=(6,0))
theme_btn = tk.Button(toolbar, text="🌓", command=toggle_theme, font=("Segoe UI", 10), width=3)
theme_btn.pack(side=tk.LEFT, padx=1)
newsession_btn = tk.Button(toolbar, text="New", command=new_session, font=("Segoe UI", 9), width=5)
newsession_btn.pack(side=tk.LEFT, padx=1)
export_btn = tk.Button(toolbar, text="Export", command=export_chat, font=("Segoe UI", 9), width=6)
export_btn.pack(side=tk.LEFT, padx=1)
copy_btn = tk.Button(toolbar, text="Copy", command=copy_last_response, font=("Segoe UI", 9), width=5)
copy_btn.pack(side=tk.LEFT, padx=1)
regen_btn = tk.Button(toolbar, text="Regen", command=regenerate_last, font=("Segoe UI", 9), width=6)
regen_btn.pack(side=tk.LEFT, padx=1)
clear_btn = tk.Button(toolbar, text="Clear", command=clear_chat, font=("Segoe UI", 9), width=5)
clear_btn.pack(side=tk.LEFT, padx=1)
ts_btn = tk.Button(toolbar, text="⏱", command=toggle_timestamps, font=("Segoe UI", 9), width=3)
ts_btn.pack(side=tk.LEFT, padx=1)
fontdown_btn = tk.Button(toolbar, text="A-", command=lambda: change_font_size(-1), font=("Segoe UI", 9), width=3)
fontdown_btn.pack(side=tk.LEFT, padx=1)
fontup_btn = tk.Button(toolbar, text="A+", command=lambda: change_font_size(1), font=("Segoe UI", 9), width=3)
fontup_btn.pack(side=tk.LEFT, padx=1)
ontop_btn = tk.Button(toolbar, text="📌", command=toggle_always_on_top, font=("Segoe UI", 9), width=3)
ontop_btn.pack(side=tk.LEFT, padx=1)

search_frame = tk.Frame(header)
search_frame.pack(fill=tk.X, padx=15, pady=(6,8))
search_entry = tk.Entry(search_frame, font=("Segoe UI", 9), bd=0)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
search_entry.bind("<Return>", lambda e: search_history())
search_btn = tk.Button(search_frame, text="🔍 Search", command=search_history, font=("Segoe UI", 9))
search_btn.pack(side=tk.RIGHT, padx=(5,0))

chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, bd=0, padx=15, pady=10)
chat_area.pack(padx=10, pady=(5,0), fill=tk.BOTH, expand=True)

# Status bar (created BEFORE loading history, so update_stats() works)
status_bar = tk.Frame(root, height=28)
status_bar.pack(fill=tk.X)
status_bar.pack_propagate(False)
status_label = tk.Label(status_bar, text="Online - Offline AI", font=("Segoe UI", 8))
status_label.pack(side=tk.LEFT, padx=15)
stats_label = tk.Label(status_bar, text="", font=("Segoe UI", 8))
stats_label.pack(side=tk.RIGHT, padx=15)

past_messages = load_history()
if past_messages:
    for role, message, ts in past_messages:
        if role == "system":
            continue
        sender = "You" if role == "user" else "Sonic"
        insert_bubble(sender, message, ts.split(" ")[1][:5] if " " in ts else "")
else:
    insert_bubble("Sonic", "Hi! I'm ready to chat, fully offline.")

bottom_bar = tk.Frame(root)
bottom_bar.pack(fill=tk.X)

entry_frame = tk.Frame(bottom_bar)
entry_frame.pack(padx=10, pady=10, fill=tk.X)

entry = tk.Entry(entry_frame, font=("Segoe UI", 12), bd=0, relief=tk.FLAT)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,8))
entry.bind("<Return>", send_message)

send_btn = tk.Button(entry_frame, text="Send", command=send_message, font=("Segoe UI", 10, "bold"), width=8)
send_btn.pack(side=tk.RIGHT)

root.bind("<Control-l>", lambda e: clear_chat())
root.bind("<Control-e>", lambda e: export_chat())
root.bind("<Control-n>", lambda e: new_session())
root.bind("<Escape>", lambda e: entry.focus())

apply_theme()
update_stats()
entry.focus()
root.mainloop()