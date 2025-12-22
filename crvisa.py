import re
import random
import time
from datetime import datetime, timedelta
from faker import Faker
from telebot import types

# استيراد البوت من ملف visa.py للوصول إليه
try:
    from visa import bot
except ImportError:
    print("Error: 'visa.py' not found. Make sure it's in the same directory.")
    bot = None

# تهيئة Faker
fake = Faker()

# --- وظائف مساعدة ذكية ---

def is_luhn_valid(card_number: str) -> bool:
    """التحقق من صحة رقم البطاقة باستخدام خوارزمية Luhn."""
    try:
        digits = [int(d) for d in card_number]
        odd_sum = sum(digits[-1::-2])
        even_sum = sum([sum(divmod(2 * d, 10)) for d in digits[-2::-2]])
        total = odd_sum + even_sum
        return total % 10 == 0
    except:
        return False

def generate_luhn_valid_number(prefix: str, length: int) -> str:
    """توليد رقم بطاقة صحيح باستخدام خوارزمية Luhn."""
    # التأكد من أن البادئة لا تتجاوز الطول المطلوب
    if len(prefix) >= length:
        return None

    number = prefix
    while len(number) < length - 1:
        number += str(random.randint(0, 9))

    # حساب وتوليد رقم التحقق
    digits = [int(d) for d in number]
    odd_sum = sum(digits[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in digits[-2::-2]])
    total = odd_sum + even_sum
    check_digit = (10 - (total % 10)) % 10
    number += str(check_digit)

    return number

def smart_generate_expiry_date(range_str=None):
    """
    توليد تاريخ انتهاء ذكي وواقعي.
    - إذا تم تحديد نطاق (مثل 2025-2028)، سيتم الاختيار منه.
    - إذا لم يتم تحديد نطاق، سيتم استخدام توزيع مرجح للسنوات القادمة.
    """
    current_year = datetime.now().year % 100

    if range_str and '-' in range_str:
        try:
            start_yy, end_yy = map(int, range_str.split('-'))
            start_yy, end_yy = start_yy % 100, end_yy % 100
            year = random.randint(start_yy, end_yy)
        except (ValueError, TypeError):
            year = (current_year + random.randint(1, 5)) % 100
    else:
        # توزيع مرجح: معظم البطاقات تنتهي خلال 2-4 سنوات
        years = list(range((current_year + 1) % 100, (current_year + 6) % 100))
        weights = [5, 4, 3, 2, 1] # أوزان للسنوات (الأقرب للأعلى وزن)
        year = random.choices(years, weights=weights)[0]

    month = f"{random.randint(1, 12):02d}"
    yy = f"{year:02d}"
    return month, yy

def parse_smart_command(text: str) -> dict:
    """
    تحليل الأمر المرن لاستخلاص جميع الخيارات.
    يدعم صيغ مثل:
    /gtp 537308334 1000
    /gtp 537308334 1000 range 2025-2028
    /gtp 537308334 1000 output file
    /gtp 537308334 1000 range 2025-2028 output file
    """
    parts = text.split()
    if len(parts) < 3 or parts[0].lower() != '/gtp':
        return None

    options = {
        'bin': parts[1],
        'limit': 0,
        'mode': 'random',
        'range': None,
        'output': None
    }

    try:
        options['limit'] = int(parts[2])
    except (ValueError, IndexError):
        return None

    # البحث عن الخيارات الإضافية
    for i, part in enumerate(parts[3:]):
        if part.lower() == 'range' and i + 1 < len(parts):
            options['range'] = parts[i+1]
        elif part.lower() == 'output' and i + 1 < len(parts):
            options['output'] = parts[i+1]

    return options

def generate_smart_cards(options: dict) -> list:
    """
    توليد البطاقات بناءً على الخيارات الذكية.
    """
    cards = []
    bin_prefix = options['bin']
    limit = options['limit']

    # التأكد من أن البادئة (BIN) هي 6 أو 8 أرقام على الأقل
    if len(bin_prefix) < 6:
        bin_prefix = bin_prefix.ljust(6, '0')[:6]

    # تحديد طول البطاقة بناءً على البادئة (عادة 16 رقم)
    card_length = 16
    if len(bin_prefix) > 6:
        card_length = 16 # يمكن تعديله لاحقًا لبطاقات أطول

    print(f"🧠 Starting smart generation of {limit} cards with BIN: {bin_prefix[:6]}...")

    for i in range(limit):
        # توليد التاريخ الذكي
        mm, yy = smart_generate_expiry_date(options.get('range'))

        # توليد رقم البطاقة الصحيح
        card_number = generate_luhn_valid_number(bin_prefix, card_length)
        if not card_number:
            continue # تخطي في حالة فشل التوليد (نادر جدًا)

        # توليد CVC ذكي
        if card_number.startswith('34') or card_number.startswith('37'): # American Express
            cvc = f"{random.randint(1000, 9999)}"
        else:
            cvc = f"{random.randint(0, 999):03d}"

        cards.append(f"{card_number}|{mm}|{yy}|{cvc}")

        if (i + 1) % 10000 == 0:
            print(f"🧠 Generated {i + 1}/{limit} cards...")

    print(f"✅ Smart generation completed. Total valid cards: {len(cards)}")
    return cards

# --- معالجات التيليجرام ---

def send_with_choice(chat_id, cards: list, base_filename: str):
    """
    إرسال البطاقات مع خيار التحميل أو الإرسال في الدردشة.
    """
    count = len(cards)
    message_text = f"✅ تم توليد {count:,} فيزة بنجاح!\n\nاختر كيفية استلامها:"

    # إنشاء لوحة مفاتيح تفاعلية
    markup = types.InlineKeyboardMarkup(row_width=1)
    download_btn = types.InlineKeyboardButton("📁 تحميل كملف .txt", callback_data=f'download|{base_filename}')
    send_btn = types.InlineKeyboardButton("📤 إرسال في الدردشة", callback_data=f'send|{base_filename}')
    markup.add(download_btn, send_btn)

    bot.send_message(chat_id, message_text, reply_markup=markup)

def handle_download_callback(call):
    """معالجة طلب التحميل."""
    _, filename = call.data.split('|', 1)
    user_id = call.from_user.id

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cards = f.read()

        bot.send_document(call.message.chat.id, cards.encode('utf-8'), visible_file_name=f"{filename.split('_')[-1]}.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال الملف بنجاح!")
    except FileNotFoundError:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الملف. الرجاء إعادة التوليد.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ حدث خطأ: {e}", show_alert=True)

def handle_send_callback(call):
    """معالجة طلب الإرسال في الدردشة."""
    _, filename = call.data.split('|', 1)
    user_id = call.from_user.id

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cards = f.read().splitlines()

        # تقسيم الرسالة إذا كانت طويلة جدًا (تيليجرام لديه حد 4096 حرفًا)
        max_message_length = 4000
        if len(cards) == 0:
            bot.answer_callback_query(call.id, "❌ الملف فارغ.", show_alert=True)
            return

        header = f"📤 قائمة الفيزات المولدة ({len(cards)} بطاقة):\n\n"
        current_message = header

        bot.answer_callback_query(call.id, "🚀 بدء الإرسال في الدردشة...")

        for i, card in enumerate(cards):
            card_line = f"{card}\n"
            if len(current_message) + len(card_line) > max_message_length:
                bot.send_message(call.message.chat.id, current_message)
                time.sleep(1) # تأخير قصير لتجنب الحظر
                current_message = ""
            current_message += card_line

        if current_message != header:
            bot.send_message(call.message.chat.id, current_message)

    except FileNotFoundError:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الملف. الرجاء إعادة التوليد.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ حدث خطأ أثناء الإرسال: {e}", show_alert=True)


# --- المعالج الرئيسي للأمر ---

def handle_generate_command(message):
    """معالجة أمر التوليد الرئيسي."""
    if not bot:
        message.reply("❌ لم يتمكن العثور على البوت. تأكد من أن 'visa.py' و 'crvisa.py' في نفس المجلد.")
        return

    options = parse_smart_command(message.text)
    if not options:
        help_text = """
📝 **كيفية استخدام الأمر الذكي:**

`/gtp [BIN] [العدد] (خيارات)`

**الخيارات الإضافية:**
- `range [YYYY-YYYY]` : لتحديد نطاق سنوات الانتهاء.
  *مثال:* `range 2025-2028`
- `output [file/chat]` : لتحديد طريقة الإرسال مباشرةً.
  *مثال:* `output file`

**أمثلة عملية:**
`/gtp 537308334 1000`
`/gtp 537308334 5000 range 2025-2028 output file`
`/gtp 537308334 10000 range 2025-2030`
        """
        bot.reply_to(message, help_text)
        return

    limit = options['limit']
    if limit > 1000000:
        bot.reply_to(message, "⚠️ الحد الأقصى للتوليد هو 1,000,000 بطاقة.")
        return

    # حفظ البطاقات في ملف مؤقت
    user_id = message.from_user.id
    filename = f"generated_{user_id}_{int(time.time())}.txt"

    # توليد البطاقات
    generated_cards = generate_smart_cards(options)

    if not generated_cards:
        bot.reply_to(message, "❌ فشل توليد أي بطاقات صالحة. تحقق من المدخلات.")
        return

    # حفظ في الملف
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(generated_cards))

    # إرسال مع الخيارات
    send_with_choice(message.chat.id, generated_cards, filename)

# --- تسجيل معالجات الأزرار التفاعلية ---

def register_handlers():
    """تسجيل المعالجات مع البوت."""
    if not bot:
        return

    @bot.message_handler(commands=['gtp'])
    def _handle(message):
        handle_generate_command(message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('download|'))
    def _handle_download(call):
        handle_download_callback(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('send|'))
    def _handle_send(call):
        handle_send_callback(call)

# تشغيل التسجيل عند استيراد الملف
if bot:
    register_handlers()
