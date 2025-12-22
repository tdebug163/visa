import re
import random
import time
from datetime import datetime, timedelta
from faker import Faker
from telebot import types

# استيراد البوت للوصول إليه
try:
    from visa import bot
except ImportError:
    print("Error: 'visa.py' not found. Make sure it's in the same directory.")
    bot = None

# تهيئة Faker
fake = Faker()

# لتخزين طلبات التوليد المعلقة
pending_generations = {}

# --- خوارزميات التوليد الذكية ---

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
    if len(prefix) >= length:
        return None
        
    number = prefix
    while len(number) < length - 1:
        # تجنب الأنماط المتكررة
        number += str(random.randint(1, 9)) # تبدأ من 1 لتجنب الأصفار المتكررة في البداية
        
    # حساب وتوليد رقم التحقق
    digits = [int(d) for d in number]
    odd_sum = sum(digits[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in digits[-2::-2]])
    total = odd_sum + even_sum
    check_digit = (10 - (total % 10)) % 10
    number += str(check_digit)
    
    # فحص أخير
    if is_luhn_valid(number):
        return number
    else:
        # في حالة نادرة للغاية، أعد المحاولة
        return generate_luhn_valid_number(prefix, length)

def smart_generate_expiry_date():
    """
    توليد تاريخ انتهاء ذكي وواقعي.
    معظم البطاقات تنتهي خلال 2-3 سنوات القادمة.
    """
    current_year = datetime.now().year % 100
    
    # توزيع مرجح للسنوات (أقرب سنة لها فرصة أعلى)
    years = list(range((current_year + 1) % 100, (current_year + 6) % 100))
    weights = [35, 30, 20, 10, 5] # أوزان للسنوات
    year = random.choices(years, weights=weights)[0]
        
    month = f"{random.randint(1, 12):02d}"
    yy = f"{year:02d}"
    return month, yy

def smart_generate_cvc(card_prefix: str) -> str:
    """توليد CVC ذكي."""
    if card_prefix.startswith('34') or card_prefix.startswith('37'): # American Express
        return f"{random.randint(1000, 9999)}"
    else:
        return f"{random.randint(100, 999)}"

# --- وظائف معالجة الأوامر والتفاعل ---

def parse_generation_input(input_str: str) -> dict:
    """
    تحليل مدخل الأمر لاستخلاص جميع البيانات الممكنة.
    يدعم صيغ مثل:
    - 37246235 (BIN فقط)
    - 472747733 10 2025 123 (BIN، شهر، سنة، CVC)
    - 472747733|10|2025|123 (BIN، شهر، سنة، CVC)
    """
    # البحث عن جميع الأرقام في النص
    numbers = re.findall(r'\d+', input_str)
    if not numbers:
        return None

    data = {'bin': '', 'mm': '', 'yy': '', 'cvc': ''}
    
    # إذا كان الرقم الأول هو 6 أرقام، فهو BIN
    if len(numbers[0]) >= 6:
        data['bin'] = numbers[0][:6]
        
        # إذا كانت هناك أرقام أخرى، حاول استخلاص التاريخ و CVC
        if len(numbers) > 1:
            # افتراض: الرقم التالي هو الشهر
            if len(numbers[1]) >= 2:
                data['mm'] = numbers[1][:2]
            
            # البحث عن سنة (رقم مكون من 4 أو رقمين)
            potential_year = None
            for num in numbers[2:]:
                if 22 <= len(num) <= 24: # سنة من 4 أرقام
                    potential_year = num[-2:]
                elif 22 <= int(num) <= 99 if num.isdigit() else 0: # سنة من رقمين
                    potential_year = num[-2:]
            
            if potential_year:
                data['yy'] = potential_year

            # البحث عن CVC (آخر رقم مكون من 3 أو 4 أرقام)
            potential_cvc = None
            for num in reversed(numbers):
                if 3 <= len(num) <= 4:
                    potential_cvc = num
                    break
            
            if potential_cvc:
                data['cvc'] = potential_cvc

    return data

def handle_generate_command(message):
    """معالجة أمر التوليد الأولي."""
    if not bot:
        return

    # التعامل مع مختلف صيغ الأمر
    command_text = message.text.strip().lower()
    if not (command_text.startswith('/gtp') or command_text.startswith('gtp') or command_text.startswith('gtp,')):
        return

    parts = command_text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ خطأ في صيغة الأمر.\n\n📝 **كيفية الاستخدام:**\n`/gtp 37246235` (للتوليد العشوائي)\n`/gtp 472747733 10 2025 123` (للتوليد المحدد)")
        return

    input_data = ' '.join(parts[1:])
    parsed_data = parse_generation_input(input_data)
    
    if not parsed_data or not parsed_data['bin']:
        bot.reply_to(message, "❌ لم أتمكن من فهم البيانات المدخلة. تأكد من صحة BIN أو البيانات.")
        return

    user_id = message.from_user.id
    # تخزين البيانات المفحصة للخطوة التالية
    pending_generations[user_id] = parsed_data
    
    # إنشاء لوحة مفاتيح تفاعلية
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    quantities = [
        ("5", "gen_5"), ("10", "gen_10"), ("50", "gen_50"),
        ("100", "gen_100"), ("500", "gen_500"), ("1000", "gen_1000"),
        ("5000", "gen_5000"), ("10000", "gen_10000"), ("100000", "gen_100000"),
        ("1000000", "gen_1000000")
    ]
    
    for text, callback_data in quantities:
        markup.add(types.InlineKeyboardButton(text=text, callback_data=callback_data))
        
    # زر للمزيد من الخيارات
    markup.add(types.InlineKeyboardButton("... خيارات المزيد", callback_data="gen_info"))

    # عرض معلومات التوليد
    info_text = f"✅ تم تحليل البيانات بنجاح!\n\n"
    info_text += f"🔹 **BIN:** `{parsed_data['bin'][:6]}...`\n"
    if parsed_data['mm']:
        info_text += f"🔹 **الشهر:** `{parsed_data['mm']}`\n"
    if parsed_data['yy']:
        info_text += f"🔹 **السنة:** `{parsed_data['yy']}`\n"
    if parsed_data['cvc']:
        info_text += f"🔹 **CVC:** `{parsed_data['cvc']}`\n"
        
    info_text += "\n🔢 **اختر الكمية المراد توليدها:**"

    bot.reply_to(message, info_text, reply_markup=markup)

def generate_cards_from_data(data: dict, limit: int) -> list:
    """
    توليد البطاقات بناءً على البيانات المفحصة والحد المطلوب.
    """
    cards = []
    bin_prefix = data['bin']
    
    # التأكد من أن البادئة (BIN) هي 6 أرقام على الأقل
    if len(bin_prefix) < 6:
        bin_prefix = bin_prefix.ljust(6, '0')[:6]

    print(f"🧠 بدء التوليد الذكي لـ {limit} بطاقة بـ BIN: {bin_prefix[:6]}...")

    for i in range(limit):
        # توليد التاريخ والـ CVC إذا لم يتم تحديدهما
        if not data['mm'] or not data['yy']:
            mm, yy = smart_generate_expiry_date()
        else:
            mm = data['mm']
            yy = data['yy'][-2:]
            
        if not data['cvc']:
            cvc = smart_generate_cvc(bin_prefix)
        else:
            cvc = data['cvc']
            
        # توليد رقم البطاقة الصحيح
        card_number = generate_luhn_valid_number(bin_prefix, 16)
        if not card_number:
            continue # تخطي في حالة فشل نادر للتوليد

        cards.append(f"{card_number}|{mm}|{yy}|{cvc}")
        
        # عرض التقدم كل 10000 بطاقة
        if (i + 1) % 10000 == 0:
            print(f"🧠 تم توليد {i + 1}/{limit} بطاقة...")

    print(f"✅ اكتمل التوليد الذكي. العدد الإجمالي: {len(cards)} بطاقة صالحة.")
    return cards

# --- معالجات الأزرار التفاعلية ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('gen_'))
def handle_generation_quantity(call):
    """معالجة اختيار كمية التوليد."""
    if not bot:
        return
        
    user_id = call.from_user.id
    try:
        _, quantity_str = call.data.split('_')
        limit = int(quantity_str)
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "❌ خيار غير صالح.", show_alert=True)
        return

    # استرجاع البيانات المخزنة
    data = pending_generations.get(user_id)
    if not data:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الجلسة. يرجى إعادة الأمر.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🚀 جاري التوليد...")

    # توليد البطاقات
    generated_cards = generate_cards_from_data(data, limit)
    
    if not generated_cards:
        bot.answer_callback_query(call.id, "❌ فشل توليد أي بطاقات صالحة.", show_alert=True)
        return

    # حفظ البطاقات في ملف
    filename = f"generated_{user_id}_{int(time.time())}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(generated_cards))
        
        # إرسال الملف
        with open(filename, 'rb') as f:
            bot.send_document(
                call.message.chat.id,
                f,
                visible_file_name=f"cards_{limit}.txt",
                caption=f"✅ تم توليد {len(generated_cards):,} بطاقة بنجاح!\n\n🔹 BIN: `{data['bin'][:6]}...`\n🔹 الكمية: `{limit:,}`"
            )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ حدث خطأ أثناء حفظ الملف: {e}", show_alert=True)
        return
    finally:
        # تنظيف البيانات المخزنة
        if user_id in pending_generations:
            del pending_generations[user_id]

@bot.callback_query_handler(func=lambda call: call.data == 'gen_info')
def handle_generation_info(call):
    """عرض معلومات إضافية حول التوليد الذكي."""
    info_text = """
🧠 **معلومات التوليد الذكي:**

• يتم استخدام خوارزمية Luhn لضمان صحة أرقام البطاقات.
• تواريخ الانتهاء يتم توليدها بذكاء لتكون واقعية (معظم البطاقات تنتهي خلال 2-3 سنوات).
• يتم تحديد طول الـ CVC تلقائيًا بناءً على نوع البطاقة (Amex = 4 أرقام).
• يتم تجنب الأنماط المتكررة في أرقام البطاقات لزيادة الواقعية.

🔧 **الأوامر المدعومة:**
• `/gtp 37246235` : توليد عشوائي.
• `/gtp 472747733 10 2025 123` : توليد محدد.
• `gtp 472747733|10|2025|123` : صيغة أخرى.
    """
    bot.answer_callback_query(call.id, info_text, show_alert=True)

# --- تسجيل المعالجات مع البوت ---

def register_handlers():
    """تسجيل جميع معالجات التوليد مع البوت."""
    if not bot:
        print("⚠️ Cannot register handlers: 'bot' object not available.")
        return

    # تسجيل معالج الأمر الرئيسي
    @bot.message_handler(func=lambda message: message.text.lower().startswith('/gtp') or message.text.lower().startswith('gtp') or message.text.lower().startswith('gtp,'))
    def _handle(message):
        handle_generate_command(message)

    # معالجات الأزرار تم تسجيلها بالفعل كـ @bot.callback_query_handler
    print("✅ تم تسجيل معالجات التوليد التفاعلية بنجاح.")

# تشغيل التسجيل عند استيراد الملف
if bot:
    register_handlers()