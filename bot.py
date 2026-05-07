import telebot
from telebot import types
import requests
import threading
import time
import json
import os

# ====================================
# TOKEN
# ====================================

API_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

# ====================================
# ADMIN
# ====================================

ADMIN_ID = 5206513380

# ====================================
# API
# ====================================

API_URL = "https://adhahi.dz/api/offer/list"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# ====================================
# SETTINGS
# ====================================

CHECK_INTERVAL = 15

# ====================================
# STORAGE
# ====================================

users_file = "users.json"

if os.path.exists(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

# ====================================
# SAVE USERS
# ====================================

def save_users():
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# ====================================
# GET DATA
# ====================================

session = requests.Session()

def get_data():

    try:

        response = session.get(
            API_URL,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:
        print("API ERROR:", e)
        return None

# ====================================
# GET STATUS
# ====================================

def get_wilaya_status(wilaya):

    data = get_data()

    if not data:
        return None

    try:

        for item in data:

            name = str(item.get("name", "")).strip()

            if name == wilaya:

                quantity = item.get("quantity", 0)

                if quantity and int(quantity) > 0:
                    return "open"

                return "closed"

    except Exception as e:
        print("STATUS ERROR:", e)

    return None

# ====================================
# START
# ====================================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    if user_id not in users:
        users[user_id] = {
            "wilaya": None,
            "notify": False
        }

    save_users()

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    wilayas = [
        "أدرار", "الشلف", "الأغواط", "أم البواقي",
        "باتنة", "بجاية", "بسكرة", "بشار",
        "البليدة", "البويرة", "تمنراست", "تبسة",
        "تلمسان", "تيارت", "تيزي وزو", "الجزائر",
        "الجلفة", "جيجل", "سطيف", "سعيدة",
        "سكيكدة", "سيدي بلعباس", "عنابة", "قالمة",
        "قسنطينة", "المدية", "مستغانم", "المسيلة",
        "معسكر", "ورقلة", "وهران", "البيض",
        "إليزي", "برج بوعريريج", "بومرداس", "الطارف",
        "تندوف", "تيسمسيلت", "الوادي", "خنشلة",
        "سوق أهراس", "تيبازة", "ميلة", "عين الدفلى",
        "النعامة", "عين تموشنت", "غرداية", "غليزان",
        "تيميمون", "برج باجي مختار", "أولاد جلال", "بني عباس",
        "إن قزام", "جانت", "المغير", "المنيعة"
    ]

    for wilaya in wilayas:

        keyboard.add(
            types.InlineKeyboardButton(
                wilaya,
                callback_data=f"wilaya_{wilaya}"
            )
        )

    bot.send_message(
        message.chat.id,
        "📍 اختر ولايتك:",
        reply_markup=keyboard
    )

# ====================================
# BUTTONS
# ====================================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    try:

        user_id = str(call.message.chat.id)

        if call.data.startswith("wilaya_"):

            wilaya = call.data.replace("wilaya_", "")

            if user_id not in users:
                users[user_id] = {}

            users[user_id]["wilaya"] = wilaya
            users[user_id]["notify"] = True

            save_users()

            status = get_wilaya_status(wilaya)

            if status == "open":

                text = (
                    f"✅ تم اختيار ولايتك\n\n"
                    f"📍 {wilaya}\n\n"
                    f"🟢 الحجز متاح حالياً\n"
                    f"🔔 التنبيهات مفعلة."
                )

            elif status == "closed":

                text = (
                    f"✅ تم اختيار ولايتك\n\n"
                    f"📍 {wilaya}\n\n"
                    f"🔴 الحجز مغلق حالياً\n"
                    f"🔔 التنبيهات مفعلة."
                )

            else:

                text = (
                    f"✅ تم اختيار ولايتك\n\n"
                    f"📍 {wilaya}\n\n"
                    f"⚠️ تعذر الاتصال بالموقع حالياً.\n"
                    f"🔔 التنبيهات مفعلة."
                )

            keyboard = types.InlineKeyboardMarkup()

            keyboard.add(
                types.InlineKeyboardButton(
                    "🌐 الدخول للموقع",
                    url="https://adhahi.dz"
                )
            )

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=keyboard
            )

    except Exception as e:
        print("BUTTON ERROR:", e)

# ====================================
# USERS COUNT
# ====================================

@bot.message_handler(commands=['users'])
def users_count(message):

    if message.chat.id != ADMIN_ID:
        return

    bot.send_message(
        message.chat.id,
        f"👥 عدد مستخدمي البوت: {len(users)}"
    )

# ====================================
# MONITOR
# ====================================

last_states = {}

def monitor():

    while True:

        try:

            for user_id, info in users.items():

                wilaya = info.get("wilaya")
                notify = info.get("notify")

                if not wilaya or not notify:
                    continue

                status = get_wilaya_status(wilaya)

                if not status:
                    continue

                previous = last_states.get(wilaya)

                if previous != status:

                    last_states[wilaya] = status

                    if status == "open":

                        try:

                            bot.send_message(
                                int(user_id),
                                f"🚨 تنبيه جديد!\n\n"
                                f"✅ تم فتح الحجز في ولاية:\n"
                                f"📍 {wilaya}\n\n"
                                f"⏳ سارع بالحجز قبل الغلق."
                            )

                        except Exception as e:
                            print("SEND ERROR:", e)

                time.sleep(0.2)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            print("MONITOR ERROR:", e)
            time.sleep(10)

# ====================================
# THREAD
# ====================================

threading.Thread(target=monitor).start()

# ====================================
# RUN
# ====================================

print("BOT RUNNING...")

while True:

    try:

        bot.infinity_polling(
            timeout=20,
            long_polling_timeout=20
        )

    except Exception as e:

        print("POLLING ERROR:", e)
        time.sleep(5)
