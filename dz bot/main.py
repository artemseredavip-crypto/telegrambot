import telebot
import sqlite3
import datetime
import threading
import time

TOKEN = "8382276088:AAE3ppduJpyvZ1Cs-wHgCokjl2hkkL58gso"
bot = telebot.TeleBot(TOKEN)

# --- Ініціалізація та очищення бази даних ---
def init_db():
    conn = sqlite3.connect("homework.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS homework")  # Очищуємо старі дані
    cur.execute("""
        CREATE TABLE homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            date TEXT,
            UNIQUE(user_id, date) ON CONFLICT REPLACE
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Додавання ДЗ ---
@bot.message_handler(commands=["add"])
def add_homework(message):
    bot.send_message(message.chat.id, "Введи завдання у форматі:\nтекст;ДД.ММ.РРРР")

@bot.message_handler(func=lambda m: ";" in m.text)
def save_homework(message):
    try:
        text, date_str = message.text.split(";")
        date_obj = datetime.datetime.strptime(date_str.strip(), "%d.%m.%Y").date()

        conn = sqlite3.connect("homework.db")
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO homework (user_id, text, date) VALUES (?, ?, ?)",
                    (message.chat.id, text.strip(), str(date_obj)))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"✅ Завдання на {date_obj} збережено/оновлено")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Неправильний формат. Спробуй так: Текст;01.10.2025")

# --- Перегляд всіх ДЗ ---
@bot.message_handler(commands=["list"])
def list_homework(message):
    conn = sqlite3.connect("homework.db")
    cur = conn.cursor()
    cur.execute("SELECT text, date FROM homework WHERE user_id=? ORDER BY date", (message.chat.id,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "📭 У тебе немає завдань")
    else:
        msg = "📚 Твої завдання:\n"
        for text, date in rows:
            msg += f"🔹 {text} (до {date})\n"
        bot.send_message(message.chat.id, msg)

# --- Завдання на сьогодні ---
@bot.message_handler(commands=["today"])
def today_homework(message):
    today = datetime.date.today()
    conn = sqlite3.connect("homework.db")
    cur = conn.cursor()
    cur.execute("SELECT text FROM homework WHERE user_id=? AND date=?", (message.chat.id, str(today)))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "📭 Сьогодні завдань немає")
    else:
        msg = f"📅 Завдання на сьогодні ({today}):\n"
        for text, in rows:
            msg += f"🔹 {text}\n"
        bot.send_message(message.chat.id, msg)

# --- Завдання на конкретну дату ---
@bot.message_handler(commands=["date"])
def date_homework(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError
        date_obj = datetime.datetime.strptime(parts[1], "%d.%m.%Y").date()

        conn = sqlite3.connect("homework.db")
        cur = conn.cursor()
        cur.execute("SELECT text FROM homework WHERE user_id=? AND date=?", (message.chat.id, str(date_obj)))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            bot.send_message(message.chat.id, f"📭 На {date_obj} завдань немає")
        else:
            msg = f"📅 Завдання на {date_obj}:\n"
            for text, in rows:
                msg += f"🔹 {text}\n"
            bot.send_message(message.chat.id, msg)
    except Exception:
        bot.send_message(message.chat.id, "❌ Неправильний формат. Використовуй: /date ДД.ММ.РРРР")

# --- Фонова перевірка на сьогоднішні завдання ---
def check_homework():
    while True:
        today = datetime.date.today()
        conn = sqlite3.connect("homework.db")
        cur = conn.cursor()
        cur.execute("SELECT user_id, text FROM homework WHERE date=?", (str(today),))
        rows = cur.fetchall()
        conn.close()

        for user_id, text in rows:
            bot.send_message(user_id, f"📌 Нагадування! Сьогодні потрібно: {text}")

        time.sleep(3600)  # перевірка щогодини

threading.Thread(target=check_homework, daemon=True).start()

# --- Запуск бота ---
bot.polling(none_stop=True)
