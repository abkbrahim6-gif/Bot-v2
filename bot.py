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
# SETTINGS & API
# ====================================
ADMIN_ID = 5206513380
API_URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"
SITE_URL = "https://adhahi.dz"
CHECK_INTERVAL = 30  # يفضل زيادة الوقت قليلاً لتجنب حظر IP السيرفر
USERS_FILE = "users.json"
BOT_NAME = "🐑 بوت تنبيهات الأضاحي"

# استخدام Session واحد وتجهيز الـ Headers
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://adhahi.dz/",
    "Origin": "https://adhahi.dz"
}

# ====================================
# LOAD/SAVE USERS
# ====================================
user_db = {}
if os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            user_db = json.load(f)
    except:
        user_db = {}

def save_users():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(user_db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"SAVE ERROR: {e}")

# ====================================
# GET DATA (المحسنة)
# ====================================
def get_data():
    try:
        # وضع timeout 30 ثانية لتجنب أخطاء ConnectionPool
        response = session.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"🌐 Site Error: {e}")
        return None

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
# KEYBOARDS
# ====================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📍 اختيار ولايتي", callback_data="choose_wilaya"),
        types.InlineKeyboardButton("🌍 فحص كل الولايات", callback_data="check_all"),
        types.InlineKeyboardButton("📋 الولايات المتاحة", callback_data="available"),
        types.InlineKeyboardButton("🔎 فحص ولايتي", callback_data="my_wilaya")
    )
    return markup

# ====================================
# HANDLERS
# ====================================
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in user_db:
        user_db[uid] = {"wilaya": "", "name": message.from_user.first_name}
        save_users()
    bot.send_message(message.chat.id, f"{BOT_NAME}\n\nاختر من القائمة:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "choose_wilaya")
def choose_wilaya(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(w, callback_data=f"w_{w}") for w in WILAYAS]
    markup.add(*buttons)
    bot.edit_message_text("📍 اختر ولايتك:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("w_"))
def save_wilaya(call):
    wilaya = call.data.replace("w_", "").strip()
    uid = str(call.from_user.id)
    user_db[uid] = {"wilaya": wilaya, "name": call.from_user.first_name}
    save_users()
    bot.answer_callback_query(call.id, f"تم اختيار {wilaya}")
    bot.send_message(call.message.chat.id, f"✅ تم حفظ ولايتك: {wilaya}\nسأقوم بتنبيهك فور توفر الحجز.")

@bot.callback_query_handler(func=lambda c: c.data == "check_all")
def check_all(call):
    data = get_data()
    if not data:
        bot.answer_callback_query(call.id, "⚠️ الموقع لا يستجيب")
        return
    text = "🌍 حالة الولايات:\n"
    for item in data[:20]: # عرض جزء فقط لتجنب طول الرسالة
        status = "🟢" if item.get("available") else "🔴"
        text += f"{status} {item.get('wilayaNameAr')}\n"
    bot.send_message(call.message.chat.id, text)

# ====================================
# MONITORING THREAD
# ====================================
def monitor():
    print("🚀 Monitoring Started...")
    previous_status = {}
    while True:
        try:
            data = get_data()
            if data:
                for item in data:
                    wilaya = item.get("wilayaNameAr", "").strip()
                    is_available = item.get("available", False)

                    if wilaya in previous_status:
                        # حالة الفتح
                        if is_available and not previous_status[wilaya]:
                            for uid, info in user_db.items():
                                if info.get("wilaya") == wilaya:
                                    try:
                                        bot.send_message(int(uid), f"🚨 عاجل: تم فتح الحجز في ولاية {wilaya}!")
                                    except: pass
                        # حالة الغلق
                        elif not is_available and previous_status[wilaya]:
                            for uid, info in user_db.items():
                                if info.get("wilaya") == wilaya:
                                    try:
                                        bot.send_message(int(uid), f"🔴 للأسف: تم غلق الحجز في ولاية {wilaya}.")
                                    except: pass

                    previous_status[wilaya] = is_available
            
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Monitor Loop Error: {e}")
            time.sleep(10)

# ====================================
# START BOT
# ====================================
threading.Thread(target=monitor, daemon=True).start()

print("✅ Bot is running...")
while True:
    try:
        # إعدادات الـ Polling لتناسب Railway
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"Polling Error: {e}")
        time.sleep(10)
                        
