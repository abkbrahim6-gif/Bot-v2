import telebot
from telebot import types
import requests
import threading
import time
import json
import os

# ====================================
# CONFIGURATION
# ====================================
API_TOKEN = "8068196784:AAHhNIxzdpYBMLj7WOQ3Kb-926ZwYXxWjeA"
bot = telebot.TeleBot(API_TOKEN)

ADMIN_ID = 5206513380
API_URL = "https://adhahi.dz/api/v1/public/wilaya-quotas"
SITE_URL = "https://adhahi.dz"
CHECK_INTERVAL = 40  # زيادة الوقت قليلاً لتجنب حظر السيرفر
USERS_FILE = "users.json"
BOT_NAME = "🐑 بوت تنبيهات الأضاحي"

# إعداد الجلسة مع طلبات هيدرز احترافية
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://adhahi.dz/",
    "Origin": "https://adhahi.dz"
}

# ====================================
# DATABASE FUNCTIONS
# ====================================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading users: {e}")
            return {}
    return {}

user_db = load_users()

def save_users():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(user_db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Error saving users: {e}")

# ====================================
# CORE FUNCTIONS
# ====================================
def get_data():
    try:
        # استخدام timeout طويل (30 ثانية) كما اقترحنا لحل مشكلة ConnectionPool
        response = session.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"🌐 Site Connection Error: {e}")
        return None

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
# BOT HANDLERS
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
        f"مرحباً بك في {BOT_NAME}\n\nيرجى اختيار ولايتك لتفعيل التنبيهات:", 
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda c: c.data == "choose_wilaya")
def choose_wilaya(call):
    bot.answer_callback_query(call.id) # الرد فوراً
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(w, callback_data=f"w_{w}") for w in WILAYAS]
    markup.add(*buttons)
    bot.edit_message_text("📍 اختر ولايتك من القائمة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("w_"))
def save_wilaya(call):
    try:
        # إصلاح الخطأ: الرد على الكولباك أولاً بدون نص طويل لتجنب الـ Timeout
        bot.answer_callback_query(call.id)
        
        wilaya = call.data.replace("w_", "").strip()
        uid = str(call.from_user.id)

        user_db[uid] = {
            "wilaya": wilaya,
            "name": call.from_user.first_name,
            "username": call.from_user.username
        }
        save_users()

        bot.send_message(call.message.chat.id, f"✅ تم حفظ ولايتك: {wilaya}\nسأرسل لك تنبيهاً فور توفر الحجز.")
    except Exception as e:
        print(f"Error in save_wilaya: {e}")

@bot.callback_query_handler(func=lambda c: c.data == "check_all")
def check_all(call):
    bot.answer_callback_query(call.id, "جاري الفحص...")
    data = get_data()
    if not data:
        bot.send_message(call.message.chat.id, "⚠️ الموقع لا يستجيب حالياً.")
        return
    
    text = "🌍 حالة الولايات حالياً:\n\n"
    for item in data[:15]: # عرض عينة فقط لتجنب طول الرسالة
        status = "🟢" if item.get("available") else "🔴"
        text += f"{status} {item.get('wilayaNameAr')}\n"
    
    bot.send_message(call.message.chat.id, text + "\n(تم عرض أول 15 ولاية فقط)")

@bot.callback_query_handler(func=lambda c: c.data == "my_wilaya")
def my_wilaya(call):
    bot.answer_callback_query(call.id)
    uid = str(call.from_user.id)
    user_wilaya = user_db.get(uid, {}).get("wilaya")

    if not user_wilaya:
        bot.send_message(call.message.chat.id, "❌ لم تقم باختيار ولاية بعد.")
        return

    data = get_data()
    if data:
        for item in data:
            if item.get("wilayaNameAr") == user_wilaya:
                status = "🟢 متوفر الآن!" if item.get("available") else "🔴 غير متوفر حالياً."
                bot.send_message(call.message.chat.id, f"📍 ولايتك: {user_wilaya}\nالحالة: {status}")
                return
    bot.send_message(call.message.chat.id, "⚠️ تعذر جلب البيانات.")

# ====================================
# MONITORING THREAD
# ====================================
def monitor():
    print("🚀 Monitoring Thread Active...")
    previous_status = {}
    
    while True:
        try:
            data = get_data()
            if data:
                for item in data:
                    wilaya = item.get("wilayaNameAr", "").strip()
                    current_avail = item.get("available", False)

                    if wilaya in previous_status:
                        # تنبيه عند الفتح
                        if current_avail and not previous_status[wilaya]:
                            for uid, info in list(user_db.items()):
                                if info.get("wilaya") == wilaya:
                                    try:
                                        bot.send_message(int(uid), f"🚨 عاجل: تم فتح الحجز في ولاية {wilaya}!")
                                    except: pass
                        # تنبيه عند الغلق
                        elif not current_avail and previous_status[wilaya]:
                            for uid, info in list(user_db.items()):
                                if info.get("wilaya") == wilaya:
                                    try:
                                        bot.send_message(int(uid), f"🔴 تنبيه: تم غلق الحجز في ولاية {wilaya}.")
                                    except: pass

                    previous_status[wilaya] = current_avail
            
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Monitor Error: {e}")
            time.sleep(15)

# ====================================
# RUN BOT
# ====================================
if __name__ == "__main__":
    # تشغيل خيط المراقبة
    threading.Thread(target=monitor, daemon=True).start()
    
    print("✅ BOT IS DEPLOYED ON RAILWAY")

    while True:
        try:
            # استخدام skip_pending لتفادي تراكم الرسائل القديمة عند إعادة التشغيل
            bot.infinity_polling(timeout=60, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            print(f"❌ Polling Error: {e}")
            time.sleep(10)
    
