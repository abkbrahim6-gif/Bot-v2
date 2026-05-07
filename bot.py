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

API_TOKEN = "8068196784:AAHhNIxzdpYBMLj7WOQ3Kb-926ZwYXxWjeA"

bot = telebot.TeleBot(API_TOKEN)

# ====================================
# ADMIN
# ====================================

ADMIN_ID = 5206513380

# ====================================
# SESSION
# ====================================

session = requests.Session()

# ====================================
# API
# ====================================

API_URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"

# ====================================
# SITE
# ====================================

SITE_URL = "https://adhahi.dz"

# ====================================
# SETTINGS
# ====================================

CHECK_INTERVAL = 15

BOT_NAME = "🐑 بوت تنبيهات الأضاحي"

# ====================================
# FILE
# ====================================

USERS_FILE = "users.json"

# ====================================
# LOAD USERS
# ====================================

try:

    if os.path.exists(USERS_FILE):

        with open(USERS_FILE, "r", encoding="utf-8") as f:

            old_data = json.load(f)

            user_db = {}

            for uid, value in old_data.items():

                if isinstance(value, str):

                    user_db[uid] = {
                        "wilaya": value,
                        "name": "",
                        "username": ""
                    }

                else:

                    user_db[uid] = value

    else:

        user_db = {}

except Exception as e:

    print("LOAD USERS ERROR:", e)

    user_db = {}

# ====================================
# SAVE USERS
# ====================================

def save_users():

    try:

        with open(USERS_FILE, "w", encoding="utf-8") as f:

            json.dump(
                user_db,
                f,
                ensure_ascii=False,
                indent=4
            )

    except Exception as e:

        print("SAVE USERS ERROR:", e)

# ====================================
# GET DATA
# ====================================

def get_data():

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Referer": "https://adhahi.dz/",
        "Origin": "https://adhahi.dz"
    }

    response = session.get(
        API_URL,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    return response.json()

# ====================================
# WILAYAS
# ====================================

WILAYAS = [
    "أدرار","الشلف","الأغواط","أم البواقي","باتنة","بجاية","بسكرة","بشار",
    "البليدة","البويرة","تمنراست","تبسة","تلمسان","تيارت","تيزي وزو","الجزائر",
    "الجلفة","جيجل","سطيف","سعيدة","سكيكدة","سيدي بلعباس","عنابة","قالمة",
    "قسنطينة","المدية","مستغانم","المسيلة","معسكر","ورقلة","وهران","البيض",
    "إليزي","برج بوعريريج","بومرداس","الطارف","تندوف","تيسمسيلت","الوادي",
    "خنشلة","سوق أهراس","تيبازة","ميلة","عين الدفلة","النعامة","عين تموشنت",
    "غرداية","غليزان","تيميمون","برج باجي مختار","أولاد جلال","بني عباس",
    "عين صالح","إن قزام","تقرت","جانت","المغير","المنيعة"
]

# ====================================
# START MESSAGE
# ====================================

START_MSG = f"""
{BOT_NAME}

🔔 بوت مراقبة حجز الأضاحي

⚡ تنبيهات فورية
📡 مراقبة مستمرة
🌐 ربط مباشر بالموقع الرسمي

اختر من القائمة:
"""

# ====================================
# MAIN MENU
# ====================================

def main_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "📍 اختيار ولايتي",
            callback_data="choose_wilaya"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🌍 فحص كل الولايات",
            callback_data="check_all"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "📋 الولايات المتاحة",
            callback_data="available"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🔎 فحص ولايتي",
            callback_data="my_wilaya"
        )
    )

    return markup

# ====================================
# START
# ====================================

@bot.message_handler(commands=['start'])
def start(message):

    uid = str(message.from_user.id)

    if uid not in user_db:

        user_db[uid] = {
            "wilaya": "",
            "name": message.from_user.first_name,
            "username": message.from_user.username
        }

        save_users()

    bot.send_message(
        message.chat.id,
        START_MSG,
        reply_markup=main_menu()
    )

# ====================================
# CHOOSE WILAYA
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "choose_wilaya")
def choose_wilaya(call):

    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = []

    for wilaya in WILAYAS:

        buttons.append(
            types.InlineKeyboardButton(
                wilaya,
                callback_data=f"w_{wilaya}"
            )
        )

    markup.add(*buttons)

    bot.send_message(
        call.message.chat.id,
        "📍 اختر ولايتك:",
        reply_markup=markup
    )

# ====================================
# SAVE WILAYA
# ====================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("w_"))
def save_wilaya(call):

    bot.answer_callback_query(
        call.id,
        "✅ تم حفظ ولايتك"
    )

    wilaya = call.data.replace("w_", "").strip()

    uid = str(call.from_user.id)

    user_db[uid] = {
        "wilaya": wilaya,
        "name": call.from_user.first_name,
        "username": call.from_user.username
    }

    save_users()

    bot.send_message(
        call.message.chat.id,
        f"""
✅ تم اختيار ولايتك

📍 {wilaya}

🔔 التنبيهات مفعلة الآن.
"""
    )

# ====================================
# CHECK ALL
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "check_all")
def check_all(call):

    bot.answer_callback_query(call.id)

    try:

        data = get_data()

        text = "🌍 حالة جميع الولايات:\n\n"

        for item in data:

            wilaya = item.get("wilayaNameAr")

            available = item.get("available")

            status = (
                "🟢 متوفر"
                if available
                else "🔴 مغلق"
            )

            text += f"{wilaya} : {status}\n"

        bot.send_message(
            call.message.chat.id,
            text
        )

    except Exception as e:

        print("CHECK ALL ERROR:", e)

        bot.send_message(
            call.message.chat.id,
            "⚠️ تعذر الاتصال بالموقع حالياً"
        )

# ====================================
# AVAILABLE
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "available")
def available(call):

    bot.answer_callback_query(call.id)

    try:

        data = get_data()

        available_list = []

        for item in data:

            if item.get("available"):

                available_list.append(
                    item.get("wilayaNameAr")
                )

        if available_list:

            text = "🟢 الولايات المتاحة:\n\n"

            for w in available_list:

                text += f"• {w}\n"

        else:

            text = "🔴 لا توجد ولايات متاحة حالياً"

        bot.send_message(
            call.message.chat.id,
            text
        )

    except Exception as e:

        print("AVAILABLE ERROR:", e)

        bot.send_message(
            call.message.chat.id,
            "⚠️ تعذر الاتصال بالموقع حالياً"
        )

# ====================================
# MY WILAYA
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "my_wilaya")
def my_wilaya(call):

    bot.answer_callback_query(call.id)

    uid = str(call.from_user.id)

    if uid not in user_db:

        bot.send_message(
            call.message.chat.id,
            "❌ اختر ولايتك أولاً"
        )

        return

    wilaya = user_db[uid].get("wilaya")

    try:

        data = get_data()

        for item in data:

            if item.get("wilayaNameAr") == wilaya:

                available = item.get("available")

                status = (
                    "🟢 الحجز متوفر"
                    if available
                    else "🔴 الحجز مغلق"
                )

                bot.send_message(
                    call.message.chat.id,
                    f"""
📍 ولايتك: {wilaya}

{status}
"""
                )

                return

    except Exception as e:

        print("MY WILAYA ERROR:", e)

        bot.send_message(
            call.message.chat.id,
            "⚠️ تعذر الاتصال بالموقع حالياً"
        )

# ====================================
# MONITOR
# ====================================

def monitor():

    print("🚀 Monitoring Started")

    previous_status = {}

    while True:

        try:

            data = get_data()

            for item in data:

                wilaya = str(
                    item.get("wilayaNameAr", "")
                ).strip()

                available = item.get(
                    "available",
                    False
                )

                if wilaya not in previous_status:

                    previous_status[wilaya] = available
                    continue

                if available and previous_status[wilaya] == False:

                    print(f"🟢 OPEN: {wilaya}")

                    for uid, user_data in list(user_db.items()):

                        if user_data.get("wilaya") == wilaya:

                            try:

                                markup = types.InlineKeyboardMarkup()

                                markup.add(
                                    types.InlineKeyboardButton(
                                        "🌐 الدخول للموقع",
                                        url=SITE_URL
                                    )
                                )

                                bot.send_message(
                                    int(uid),
                                    f"""
🚨 تم فتح الحجز

📍 {wilaya}

⚡ الحجز متوفر الآن
""",
                                    reply_markup=markup
                                )

                            except Exception as e:

                                print("SEND ERROR:", e)

                elif not available and previous_status[wilaya] == True:

                    print(f"🔴 CLOSED: {wilaya}")

                    for uid, user_data in list(user_db.items()):

                        if user_data.get("wilaya") == wilaya:

                            try:

                                bot.send_message(
                                    int(uid),
                                    f"""
🔴 تم غلق الحجز

📍 {wilaya}
"""
                                )

                            except Exception as e:

                                print("CLOSE ERROR:", e)

                previous_status[wilaya] = available

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            print("❌ GET DATA ERROR:", e)

            time.sleep(5)

# ====================================
# THREAD
# ====================================

threading.Thread(
    target=monitor,
    daemon=True
).start()

print("✅ BOT STARTED SUCCESSFULLY")

# ====================================
# RUN
# ====================================

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            skip_pending=True
        )

    except Exception as e:

        print("❌ POLLING ERROR:", e)

        time.sleep(5)
