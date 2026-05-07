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

USERS_FILE = "users.json"

# ====================================
# LOAD USERS
# ====================================

try:

    if os.path.exists(USERS_FILE):

        with open(USERS_FILE, "r", encoding="utf-8") as f:

            user_db = json.load(f)

    else:

        user_db = {}

except:

    user_db = {}

# ====================================
# SAVE USERS
# ====================================

def save_users():

    with open(USERS_FILE, "w", encoding="utf-8") as f:

        json.dump(
            user_db,
            f,
            ensure_ascii=False,
            indent=4
        )

# ====================================
# GET DATA
# ====================================

def get_data():

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://adhahi.dz/",
        "Origin": "https://adhahi.dz",
        "Connection": "keep-alive"
    }

    response = session.get(
        API_URL,
        headers=headers,
        timeout=30
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
# START
# ====================================

@bot.message_handler(commands=['start'])
def start(message):

    uid = str(message.from_user.id)

    if uid not in user_db:

        user_db[uid] = {
            "wilaya": ""
        }

        save_users()

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "📍 اختيار ولايتي",
            callback_data="choose"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🌍 فحص كل الولايات",
            callback_data="all"
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
            callback_data="my"
        )
    )

    bot.send_message(
        message.chat.id,
        f"""
{BOT_NAME}

⚡ مراقبة مباشرة لموقع الأضاحي
🔔 تنبيهات فورية عند فتح الحجز
""",
        reply_markup=markup
    )

# ====================================
# CHOOSE
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "choose")
def choose(call):

    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = []

    for w in WILAYAS:

        buttons.append(
            types.InlineKeyboardButton(
                w,
                callback_data=f"w_{w}"
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

    wilaya = call.data.replace("w_", "")

    uid = str(call.from_user.id)

    user_db[uid]["wilaya"] = wilaya

    save_users()

    bot.answer_callback_query(
        call.id,
        "✅ تم حفظ الولاية"
    )

    bot.send_message(
        call.message.chat.id,
        f"""
✅ تم اختيار ولايتك

📍 {wilaya}

🔔 التنبيهات مفعلة
"""
    )

# ====================================
# MY WILAYA
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "my")
def my_wilaya(call):

    uid = str(call.from_user.id)

    if uid not in user_db:

        bot.send_message(
            call.message.chat.id,
            "❌ اختر ولايتك أولاً"
        )

        return

    wilaya = user_db[uid]["wilaya"]

    try:

        data = get_data()

        for item in data:

            if item.get("wilayaNameAr") == wilaya:

                available = (
                    item.get("available") == True
                    or item.get("quota", 0) > 0
                )

                status = (
                    "🟢 الحجز متوفر"
                    if available
                    else "🔴 الحجز مغلق"
                )

                bot.send_message(
                    call.message.chat.id,
                    f"""
📍 {wilaya}

{status}
"""
                )

                return

    except Exception as e:

        print(e)

# ====================================
# AVAILABLE
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "available")
def available(call):

    try:

        data = get_data()

        text = "🟢 الولايات المتاحة:\n\n"

        found = False

        for item in data:

            available = (
                item.get("available") == True
                or item.get("quota", 0) > 0
            )

            if available:

                found = True

                text += f"• {item.get('wilayaNameAr')}\n"

        if not found:

            text = "🔴 لا توجد ولايات متاحة"

        bot.send_message(
            call.message.chat.id,
            text
        )

    except Exception as e:

        print(e)

# ====================================
# CHECK ALL
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "all")
def all_wilayas(call):

    try:

        data = get_data()

        text = "🌍 حالة الولايات:\n\n"

        for item in data:

            available = (
                item.get("available") == True
                or item.get("quota", 0) > 0
            )

            status = (
                "🟢 متوفر"
                if available
                else "🔴 مغلق"
            )

            text += f"{item.get('wilayaNameAr')} : {status}\n"

        bot.send_message(
            call.message.chat.id,
            text
        )

    except Exception as e:

        print(e)

# ====================================
# MONITOR
# ====================================

def monitor():

    print("🚀 MONITOR STARTED")

    previous = {}

    while True:

        try:

            data = get_data()

            for item in data:

                wilaya = item.get("wilayaNameAr")

                available = (
                    item.get("available") == True
                    or item.get("quota", 0) > 0
                )

                if wilaya not in previous:

                    previous[wilaya] = available

                    continue

                if available and previous[wilaya] == False:

                    print(f"🟢 OPEN: {wilaya}")

                    for uid, info in user_db.items():

                        if info.get("wilaya") == wilaya:

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

                                print(e)

                previous[wilaya] = available

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            print("GET DATA ERROR:", e)

            time.sleep(5)

# ====================================
# START THREAD
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

        print("POLLING ERROR:", e)

        time.sleep(5)
