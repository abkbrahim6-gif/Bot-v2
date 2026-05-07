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

if not API_TOKEN:
    print("❌ BOT_TOKEN NOT FOUND")
    exit()

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

CHECK_INTERVAL = 3

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
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

    try:

        response = session.get(
            API_URL,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:

            print(f"❌ API STATUS: {response.status_code}")

            return []

        data = response.json()

        if not isinstance(data, list):

            print("❌ INVALID API DATA")

            return []

        return data

    except Exception as e:

        print("❌ GET DATA ERROR:", e)

        return []

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
# MESSAGES
# ====================================

START_MSG = f"""
{BOT_NAME}

🔔 بوت مراقبة حجز الأضاحي في الجزائر

⚡ تنبيهات فورية
📡 مراقبة سريعة
🌐 ربط مباشر بالموقع الرسمي

اختر الخدمة من الأسفل.
"""

HELP_MSG = """
🛠 المساعدة

إذا واجهت أي مشكلة داخل البوت يمكنك التواصل مع المطور.
"""

OPEN_MSG = """
🚨 تم فتح الحجز

📍 الولاية: {wilaya}

⚡ الحجز متوفر حالياً.
"""

CLOSE_MSG = """
🔴 تم غلق الحجز

📍 الولاية: {wilaya}

⌛ الحجز غير متوفر حالياً.
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
            "📋 عرض الولايات المتاحة",
            callback_data="available"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🔎 فحص ولايتي",
            callback_data="my_wilaya"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "👥 عدد المستخدمين",
            callback_data="count_users"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🛠 المساعدة",
            callback_data="help"
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
# HELP
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_menu(call):

    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "📩 التواصل مع المطور",
            url="https://t.me/Brahim_Abk"
        )
    )

    bot.send_message(
        call.message.chat.id,
        HELP_MSG,
        reply_markup=markup
    )

# ====================================
# USERS COUNT
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "count_users")
def count_users(call):

    bot.answer_callback_query(call.id)

    if call.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        call.message.chat.id,
        f"👥 عدد مستخدمي البوت: {len(user_db)}"
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
# SAVE USER
# ====================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("w_"))
def save(call):

    bot.answer_callback_query(
        call.id,
        "✅ تم حفظ الولاية"
    )

    wilaya = call.data.replace("w_", "").strip()

    uid = str(call.from_user.id)

    if uid not in user_db:

        user_db[uid] = {}

    user_db[uid]["wilaya"] = wilaya
    user_db[uid]["name"] = call.from_user.first_name
    user_db[uid]["username"] = call.from_user.username

    save_users()

    current_status = False

    data = get_data()

    for item in data:

        api_wilaya = str(
            item.get("wilayaNameAr", "")
        ).strip()

        if api_wilaya == wilaya:

            current_status = item.get(
                "available",
                False
            )

            break

    status_text = (
        "🟢 الحجز متوفر حالياً"
        if current_status
        else "🔴 الحجز مغلق حالياً"
    )

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "🌐 الدخول للموقع",
            url=SITE_URL
        )
    )

    bot.send_message(
        call.message.chat.id,
        f"""
✅ تم اختيار ولايتك

📍 {wilaya}

{status_text}

🔔 التنبيهات مفعلة الآن.
""",
        reply_markup=markup
    )

# ====================================
# CHECK ALL
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "check_all")
def check_all(call):

    bot.answer_callback_query(
        call.id,
        "⏳ جاري الفحص..."
    )

    data = get_data()

    if not data:

        bot.send_message(
            call.message.chat.id,
            "⚠️ تعذر الاتصال بالموقع حالياً"
        )

        return

    text = "🌍 حالة جميع الولايات:\n\n"

    for item in data:

        wilaya = item.get("wilayaNameAr")
        available = item.get("available")

        status = "🟢 متوفر" if available else "🔴 مغلق"

        text += f"{wilaya} : {status}\n"

    for i in range(0, len(text), 4000):

        bot.send_message(
            call.message.chat.id,
            text[i:i+4000]
        )

# ====================================
# AVAILABLE
# ====================================

@bot.callback_query_handler(func=lambda c: c.data == "available")
def available(call):

    bot.answer_callback_query(
        call.id,
        "🔍 جاري الفحص..."
    )

    data = get_data()

    if not data:

        bot.send_message(
            call.message.chat.id,
            "⚠️ تعذر الاتصال بالموقع حالياً"
        )

        return

    available_list = []

    for item in data:

        if item.get("available"):

            available_list.append(
                item.get("wilayaNameAr")
            )

    if available_list:

        text = "🟢 الولايات المتاحة حالياً:\n\n"

        for w in available_list:

            text += f"• {w}\n"

    else:

        text = "🔴 لا توجد ولايات متاحة حالياً"

    bot.send_message(
        call.message.chat.id,
        text
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

    my_w = user_db[uid].get("wilaya", "")

    if not my_w:

        bot.send_message(
            call.message.chat.id,
            "❌ اختر ولايتك أولاً"
        )

        return

    data = get_data()

    if not data:

        bot.send_message(
            call.message.chat.id,
            "⚠️ تعذر الاتصال بالموقع حالياً"
        )

        return

    for item in data:

        if item.get("wilayaNameAr") == my_w:

            available = item.get("available")

            status = (
                "🟢 متوفر"
                if available
                else "🔴 مغلق"
            )

            bot.send_message(
                call.message.chat.id,
                f"""
📍 ولايتك: {my_w}

الحالة الحالية:
{status}
"""
            )

            return

# ====================================
# REMOVE BLOCKED USER
# ====================================

def remove_blocked_user(uid):

    try:

        if uid in user_db:

            del user_db[uid]

            save_users()

            print(f"❌ USER REMOVED: {uid}")

    except Exception as e:

        print("REMOVE ERROR:", e)

# ====================================
# MONITOR
# ====================================

def monitor():

    print("🚀 Monitoring Started")

    previous_status = {}

    while True:

        try:

            data = get_data()

            if not data:

                time.sleep(5)
                continue

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

                    print(f"🟢 OPEN DETECTED: {wilaya}")

                    for uid, data_user in list(user_db.items()):

                        if data_user.get("wilaya") == wilaya:

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
                                    OPEN_MSG.format(
                                        wilaya=wilaya
                                    ),
                                    reply_markup=markup
                                )

                            except Exception as e:

                                print("SEND ERROR:", e)

                                if "403" in str(e):

                                    remove_blocked_user(uid)

                elif not available and previous_status[wilaya] == True:

                    print(f"🔴 CLOSED DETECTED: {wilaya}")

                    for uid, data_user in list(user_db.items()):

                        if data_user.get("wilaya") == wilaya:

                            try:

                                bot.send_message(
                                    int(uid),
                                    CLOSE_MSG.format(
                                        wilaya=wilaya
                                    )
                                )

                            except Exception as e:

                                print("CLOSE ERROR:", e)

                                if "403" in str(e):

                                    remove_blocked_user(uid)

                previous_status[wilaya] = available

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            print("MONITOR ERROR:", e)

            time.sleep(3)

# ====================================
# THREAD
# ====================================

threading.Thread(
    target=monitor,
    daemon=True
).start()

print("🤖 BOT RUNNING")
print("✅ BOT STARTED SUCCESSFULLY")

# ====================================
# RUN BOT
# ====================================

while True:

    try:

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            skip_pending=False
        )

    except Exception as e:

        print("POLLING ERROR:", e)

        time.sleep(3)
