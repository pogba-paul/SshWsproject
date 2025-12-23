import os
import telebot
import subprocess
import time
import logging
import re
from threading import Thread
from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# --- إضافة كود Flask لضمان بقاء السيرفر حياً (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running 24/7!"

def run_flask():
    # Hugging Face يستخدم المنفذ 7860 افتراضياً
    port = int(os.environ.get("PORT", 7860)) 
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# --- نهاية كود Flask ---

try:
    current_script_path = os.path.abspath(__file__)
    os.chmod(current_script_path, 0o600)
except Exception as e:
    logging.warning(f"Could not secure current script file permissions: {e}")

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_USERNAME = "@PharaohNetArab"
ADMIN_ID = 7083438415

BASE_UPLOAD_DIR = 'user_files'   
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
os.chmod(BASE_UPLOAD_DIR, 0o700) 

TEMP_DANGEROUS_DIR = 'temp_dangerous'
os.makedirs(TEMP_DANGEROUS_DIR, exist_ok=True)
os.chmod(TEMP_DANGEROUS_DIR, 0o700)

POINTS_FILE = 'user_points.txt'
REF_LINKS_FILE = 'user_ref_links.txt'
BANNED_USERS_FILE = 'banned_users.txt'  

for sensitive_file in [POINTS_FILE, REF_LINKS_FILE, BANNED_USERS_FILE]:
    if os.path.exists(sensitive_file):
        try:
            os.chmod(sensitive_file, 0o600)
        except Exception as e:
            logging.warning(f"Could not secure sensitive file {sensitive_file}: {e}")

# قوائم الكلمات الممنوعة المحسنة
FORBIDDEN_WORDS_AR = [
    'اختراق', 'هكر', 'تهكير', 'اخترق', 'هك', 'تسريب', 'استضافة', 'hosting', 'hack', 'cracker',
    'تهكير', 'هكرز', 'كراك', 'اختراق حسابات', 'بوت اختراق', 'جلب بيانات',
    'تجسس', 'سرقة', 'قرصنة', 'هجمات الحرمان', 'هجمات الرفض', 'سرقة بيانات', 'رفع ملفات', 'تحميل ملفات',
    'سحب ملفات',
]

FORBIDDEN_WORDS_EN = [
    'hack', 'hacker', 'hacking', 'crack', 'hosting', 'shell',
    'reverse_shell', 'bind_shell', 'rm -rf', 'shred',
    'hosting bot', 'telegram host', 'discord host', 'os walk', 'os listdir',
]

ALL_FORBIDDEN_KEYWORDS = FORBIDDEN_WORDS_AR + FORBIDDEN_WORDS_EN

def load_banned_users():
    banned = set()
    if os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().isdigit():
                    banned.add(int(line.strip()))
    return banned

def save_banned_users(banned_set):
    with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
        for uid in banned_set:
            f.write(f"{uid}\n")
    try:
        os.chmod(BANNED_USERS_FILE, 0o600)
    except: pass

banned_users = load_banned_users()

def is_user_banned(user_id):
    return user_id in banned_users

def ban_user(user_id):
    banned_users.add(user_id)
    save_banned_users(banned_users)

def unban_user(user_id):
    if user_id in banned_users:
        banned_users.remove(user_id)
        save_banned_users(banned_users)

# دالة فحص الملفات (Security Check) المحسنة
def is_script_dangerous(file_path, filename):
    filename_lower = filename.lower()
    
    if os.path.getsize(file_path) > 1048576:
        return True, "حجم الملف كبير جداً (أكثر من 1MB) وغير مسموح به لأسباب أمنية"
    
    found_in_filename = [word for word in ALL_FORBIDDEN_KEYWORDS if word.lower() in filename_lower]
    if found_in_filename:
        return True, f"اسم الملف يحتوي على كلمات ممنوعة: {', '.join(found_in_filename[:5])}"

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()

        found_words = []
        for word in ALL_FORBIDDEN_KEYWORDS:
            if word.lower() in content or word.lower() in filename_lower:
                found_words.append(word)
        
        if found_words:
            return True, f"تم اكتشاف كلمات ممنوعة داخل السكربت: {', '.join(found_words[:5])}"

        dangerous_patterns = [
            r'os\.system\s*\(.*rm\s+-rf',
            r'subprocess.*call.*[\'"]sudo',
            r'subprocess.*call.*[\'"]rm\s+-rf',
            r'__import__.*os.*system',
            r'eval\s*\(.*input',
            r'exec\s*\(.*input',
            r'open\s*\([^\)]*w.*\/etc\/',
            r'shutil\.rmtree\s*\(',
            r'curl.*-o.*[\'"]\/tmp',
            r'wget.*-O.*[\'"]\/tmp',
            r'base64\.b64decode\s*\(',
            r'exec\s*\(',
            r'eval\s*\(',
            r'subprocess\.Popen\s*\(.*shell=True',
            r'os\.popen\s*\(',
            r'requests\.get\s*\(.*url.*exec',
            r'import\s+socket.*connect.*reverse',
            r'os\.listdir\s*\(',
            r'os\.walk\s*\(',
            r'subprocess.*(rm|cp|mv|chmod|chown|mkdir|rmdir)',
            r'open\s*\([^,]*,\s*["\']rb["\'].*os\.',
            r'requests\.(post|get)\s*\([^)]*file',
            r'paramiko.*connect',
            r'ftplib.*connect',
            r'scp.*copy',
            r'socket\.(connect|sendto).*(while|for\s+in\s*range)',
            r'while\s+True:.*socket\.send',
            r'import\s+scapy',
            r'stratum\s*\+\=',
            r'xmrig.*start',
            r'with\s+open\s*\([^)]*,\s*["\']a["\'].*os\.',
            r'shutil\.(copytree|move).*\/(etc|home|root)',
            r'glob\.glob\s*\([^)]*[\*\/]\.',
            r'import\s+zipfile.*extract',
            r'urllib\.request\.urlretrieve.*exec'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True, "تم اكتشاف أوامر خطيرة تهدد أمان السيرفر"

        if 'import os' in content and ('os.system' in content or 'os.popen' in content):
            return True, "تم اكتشاف استخدام os.system أو os.popen بشكل مشبوه"

        bot_patterns = [
            r'telebot\.TeleBot.*while\s+True',
            r'aiogram.*asyncio\.run.*loop.*flood',
            r'discord\.Client.*on_message.*send.*rate_limit',
            r'requests\.post.*https://api\.telegram\.org.*loop'
        ]
        for pattern in bot_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True, "تم اكتشاف سكريبت بوت استضافة ضار"

    except Exception as e:
        return True, f"فشل في قراءة الملف: {str(e)}"

    return False, "آمن"

# المكتبات والوظائف المساعدة
TELEGRAM_LIB_MAPPING = {
    'telebot': 'pyTelegramBotAPI',
    'requests': 'requests',
    'urllib3': 'requests',
    'certifi': 'requests',
    'charset_normalizer': 'requests',
    'telegram': 'python-telegram-bot',
    'httpx': 'python-telegram-bot',
    'aiohttp': 'python-telegram-bot',
    'APScheduler': 'python-telegram-bot',
    'aiogram': 'aiogram',
    'aiofiles': 'aiogram',
    'magic_filter': 'aiogram',
    'pydantic': None,
}

STDLIB_MODULES = {
    'os', 'sys', 'time', 'json', 'random', 'math', 'datetime', 're', 'subprocess',
    'threading', 'logging', 'collections', 'socket', 'urllib', 'urllib.parse',
    'html', 'http', 'asyncio', 'functools', 'pathlib', 'shutil', 'base64', 'hashlib'
}

LIBRARY_MAPPING = {
    'telebot': 'pyTelegramBotAPI',
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'discord': 'discord.py',
    'sklearn': 'scikit-learn',
    'bs4': 'beautifulsoup4',
    'telegram': 'python-telegram-bot',
    'dotenv': 'python-dotenv',
    'dns': 'dnspython',
    'yaml': 'PyYAML',
    'dateutil': 'python-dateutil',
    'aiogram': 'aiogram',
}

def load_dict(filename):
    d = {}
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    uid, val = line.strip().split(':', 1)
                    d[int(uid)] = val
    return d

def save_dict(filename, d):
    with open(filename, 'w', encoding='utf-8') as f:
        for uid, val in d.items():
            f.write(f"{uid}:{val}\n")
    try:
        os.chmod(filename, 0o600)
    except Exception as e:
        logging.warning(f"Failed to secure {filename} after save: {e}")

user_points = load_dict(POINTS_FILE)
user_ref_links = load_dict(REF_LINKS_FILE)

def get_or_create_ref_link(user_id):
    try:
        bot_username = bot.get_me().username
    except:
        bot_username = "Bot"
    if user_id not in user_ref_links:
        link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        user_ref_links[user_id] = link
        save_dict(REF_LINKS_FILE, user_ref_links)
    return user_ref_links[user_id]

def add_points_from_ref(ref_id):
    if ref_id.isdigit():
        rid = int(ref_id)
        current_points = int(user_points.get(rid, '0'))
        user_points[rid] = str(current_points + 1)
        save_dict(POINTS_FILE, user_points)

def get_user_dir(user_id):
    relative_path = os.path.join(BASE_UPLOAD_DIR, str(user_id))
    full_path = os.path.abspath(relative_path)
    os.makedirs(full_path, exist_ok=True)
    try:
        os.chmod(full_path, 0o700)
    except Exception as e:
        logging.warning(f"Failed to secure user directory {full_path}: {e}")
    return full_path

def get_all_users():
    users = []
    for folder in os.listdir(BASE_UPLOAD_DIR):
        folder_path = os.path.join(BASE_UPLOAD_DIR, folder)
        if os.path.isdir(folder_path) and folder.isdigit():
            users.append(int(folder))
    return users

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
bot = telebot.TeleBot(BOT_TOKEN)
try:
    bot.set_my_commands([
        BotCommand("start", "Start Bot"), 
        BotCommand("antihack", "إدارة المحظورين (للأدمن فقط)")
    ])
    print("Commands set successfully!")
except Exception as e:
    logging.error(f"⚠️ فشل الاتصال بتيليجرام لضبط الأوامر: {e}")


admin_broadcasting = False

# نظام المشتركين والأدمن
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def check_subscription(func):
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id == ADMIN_ID:
            return func(message, *args, **kwargs)
        if is_user_banned(user_id):
            bot.send_message(message.chat.id, "⛔ تم حظرك من استخدام البوت بسبب محاولة رفع سكربت ضار.\nإذا كنت تعتقد أن هذا خطأ، تواصل مع الأدمن.")
            return
        if not is_user_member(user_id):
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("انضم إلى القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
            markup.add(InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub"))
            bot.send_message(message.chat.id, f"⚠️ مرحبا! لاستخدام البوت، يجب الانضمام للقناة أولاً:\n{CHANNEL_USERNAME}\n\nبعد الانضمام، اضغط على زر التحقق للمتابعة.", reply_markup=markup)
            return
        return func(message, *args, **kwargs)
    return wrapper

# معالجات Callback
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def handle_check_sub(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.answer_callback_query(call.id, "تم التحقق! يمكنك الآن استخدام البوت.")
        dummy_message = type('obj', (object,), {'from_user': call.from_user, 'chat': call.message.chat, 'text': '/start'})()
        send_welcome(dummy_message)
    else:
        bot.answer_callback_query(call.id, "ما زلت غير مشترك. انضم أولاً ثم جرب مرة أخرى.")

@bot.message_handler(commands=['antihack'])
def admin_antihack_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not banned_users:
        bot.send_message(message.chat.id, "✅ لا يوجد مستخدمين محظورين حالياً.")
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for uid in banned_users:
        username = "غير معروف"
        try:
            user = bot.get_chat(uid)
            username = f"@{user.username}" if user.username else user.first_name
        except:
            username = "غير متاح"
        markup.add(InlineKeyboardButton(f"🆔 {uid} • {username}", callback_data=f"unban_{uid}"))
    
    bot.send_message(message.chat.id, "🚫 قائمة المستخدمين المحظورين بسبب محاولة رفع سكربتات ضارة:\nاضغط على المستخدم لفك الحظر عنه:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('unban_'))
def unban_user_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split('_')[1])
    unban_user(uid)
    bot.answer_callback_query(call.id, "تم فك الحظر عن المستخدم")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ تم فك الحظر عن المستخدم {uid} بنجاح."
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('unban_only_'))
def unban_only_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split('_')[2])
    unban_user(uid)
    bot.answer_callback_query(call.id, "تم فك الحظر عن المستخدم")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ تم فك الحظر عن المستخدم {uid} بنجاح بدون رفع الملف."
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_'))
def accept_script_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split('_', 2)
    uid = int(parts[1])
    fname = parts[2]
    temp_dangerous_path = os.path.join(TEMP_DANGEROUS_DIR, f"{uid}_{fname}")
    if not os.path.exists(temp_dangerous_path):
        bot.answer_callback_query(call.id, "الملف المؤقت غير موجود.")
        return
    user_dir = get_user_dir(uid)
    file_full_path = os.path.join(user_dir, fname)
    try:
        os.rename(temp_dangerous_path, file_full_path)
        os.chmod(file_full_path, 0o600)
        unban_user(uid)
        bot.send_message(uid, f"✅ تم مراجعة ملفك {fname} من قبل الأدمن وكان خطأ في الفحص الأمني. تم قبوله ورفعه الآن!")
        bot.answer_callback_query(call.id, "تم قبول السكريبت ورفعه بنجاح.")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ تم قبول السكريبت {fname} للمستخدم {uid} ورفعه وفك الحظر."
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"فشل في رفع الملف: {str(e)}")

def create_main_keyboard(is_admin=False):
    kb = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)  
    kb.add(KeyboardButton('📤 رفع ملف'), KeyboardButton('🗑️ حذف ملف'))
    kb.add(KeyboardButton('📂عرض الملفات'), KeyboardButton('▶تشغيل سكربت'), KeyboardButton('⛔إيقاف سكربت'))  
    kb.add(KeyboardButton('📝 السجلات'))
    if is_admin:
        kb.add(KeyboardButton('📥 رفع ملف من الاستضافة'))
        kb.add(KeyboardButton('📢 إرسال إذاعة'))
    return kb

# وظائف الكشف الذكي للمكتبات
def smart_detect_telegram_libs(script_path):
    detected = set()
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        imports = re.findall(r'^\s*import\s+([^\s#]+)', content, re.MULTILINE)
        from_imports = re.findall(r'^\s*from\s+([^\s#]+)', content, re.MULTILINE)
        all_imports = {imp.split('.')[0] for imp in imports + from_imports}

        for lib in all_imports:
            if lib in STDLIB_MODULES:
                continue
            if lib in TELEGRAM_LIB_MAPPING:
                main_lib = TELEGRAM_LIB_MAPPING[lib]
                if main_lib:
                    detected.add(main_lib)
            elif lib in LIBRARY_MAPPING:
                detected.add(LIBRARY_MAPPING[lib])
            else:
                detected.add(lib)

    except Exception as e:
        logging.error(f"Error in smart_detect_telegram_libs: {e}")
    return list(detected)

def extract_py_name_from_cmd(cmd):
    if not cmd:
        return ''
    m = re.search(r'([A-Za-z0-9_\-./\\]+\.py)', cmd)
    if m:
        return os.path.basename(m.group(1))
    parts = cmd.split()
    for i, p in enumerate(parts):
        lower = p.lower()
        if 'python' in lower:
            if i + 1 < len(parts) and parts[i+1].endswith('.py'):
                return os.path.basename(parts[i+1])
    for p in parts:
        if p.endswith('.py'):
            return os.path.basename(p)
    return ''

# دالة تشغيل السكربت المحسنة
def execute_script_setup_and_run(user_id, chat_id, user_dir, script_name):
    venv_path = os.path.join(user_dir, 'venv')
    venv_bin = os.path.join(venv_path, 'bin')
    pip_path = os.path.join(venv_bin, 'pip')
    python_path = os.path.join(venv_bin, 'python')
    script_full_path = os.path.join(user_dir, script_name)
    
    bot.send_message(chat_id, f"🚀 جاري تحليل السكربت {script_name} وتشغيله (سيتم إنشاء بيئة افتراضية وتثبيت المكتبات اللازمة إذا لزم الأمر)...", parse_mode='HTML')
    
    try:
        subprocess.run(['python3', '-m', 'venv', venv_path], capture_output=True, text=True, timeout=60)
        os.chmod(venv_path, 0o700)
    except: pass

    if not os.path.exists(pip_path):
        bot.send_message(chat_id, "❌ خطأ: فشل في إنشاء البيئة الافتراضية (venv).")
        return

    env = os.environ.copy()
    env["PATH"] = f"{venv_bin}:{env['PATH']}"
    env["VIRTUAL_ENV"] = venv_path

    final_libs = set()
    final_libs.add('requests')
    
    detected = smart_detect_telegram_libs(script_full_path)
    if detected:
        bot.send_message(chat_id, f"🔍 تم اكتشاف المكتبات الرئيسية المطلوبة: {', '.join(detected)}")
        final_libs.update(detected)
    
    req_path = os.path.join(user_dir, 'requirements.txt')
    if os.path.exists(req_path):
        try:
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip().split('#')[0].strip()
                    if line and '==' in line:
                        line = line.split('==')[0]
                    if line:
                        final_libs.add(line)
        except: pass

    if final_libs:
        bot.send_message(chat_id, f"📦 جاري تثبيت {len(final_libs)} مكتبة رئيسية...")
        failed_libs = []
        for lib in final_libs:
            try:
                cmd = f'"{pip_path}" install "{lib}" --no-cache-dir --timeout=60'
                res = subprocess.run(cmd, shell=True, cwd=user_dir, env=env, capture_output=True, text=True)
                if res.returncode != 0:
                    failed_libs.append(lib)
            except Exception as e:
                failed_libs.append(lib)
        
        if failed_libs:
            bot.send_message(chat_id, f"⚠️ فشل تثبيت: {', '.join(failed_libs)}\nجاري المتابعة...")
        else:
            bot.send_message(chat_id, "✅ تم تثبيت جميع المكتبات بنجاح.")
    else:
        bot.send_message(chat_id, "✅ لا حاجة لمكتبات إضافية، جاري التشغيل...")

    log_file = f"bot_{script_name}.log"
    log_path = os.path.join(user_dir, log_file)
    if os.path.exists(log_path):
        try: os.remove(log_path)
        except: pass

    nohup_cmd = f"nohup {python_path} \"{script_name}\" > \"{log_file}\" 2>&1 &"
    try:
        subprocess.Popen(nohup_cmd, shell=True, cwd=user_dir, env=env)
        time.sleep(1.5)
        try:
            os.chmod(log_path, 0o600)
        except: pass

        bot.send_message(chat_id, f"🎉 تم تشغيل السكربت بنجاح!\nالسجل: <code>{log_file}</code>\nاستخدم زر \"📝 السجلات\" لرؤية الإخراج.", parse_mode='HTML')
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء التشغيل: {e}")

# نظام السجلات
def show_logs_handler(message):
    user_dir = get_user_dir(message.from_user.id)
    log_files = [f for f in os.listdir(user_dir) if f.startswith('bot_') and f.endswith('.log')]
    py_files = [f for f in os.listdir(user_dir) if f.endswith('.py')]

    if not log_files:
        bot.send_message(message.chat.id, "📝 لا توجد سجلات متاحة حالياً.")
        return

    msg = "📝 اختر السكربت لعرض سجل التشغيل (آخر 50 سطر):\n\n"
    script_to_log = {}
    for log_file in log_files:
        script_name = log_file.replace('bot_', '').replace('.log', '')
        if script_name in py_files or any(script_name in py for py in py_files):
            display_name = script_name
            msg += f"• {display_name}\n"
            script_to_log[display_name] = log_file

    if not script_to_log:
        bot.send_message(message.chat.id, "📝 لا توجد سجلات مرتبطة بسكربتاتك.")
        return

    markup = InlineKeyboardMarkup(row_width=1)
    for name in script_to_log.keys():
        markup.add(InlineKeyboardButton(name, callback_data=f"log_{script_to_log[name]}"))
    
    bot.send_message(message.chat.id, msg + "\nاضغط على اسم السكربت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('log_'))
def send_log_file(call):
    log_filename = call.data.split('_', 1)[1]
    user_dir = get_user_dir(call.from_user.id)
    log_path = os.path.join(user_dir, log_filename)

    if not os.path.exists(log_path):
        bot.answer_callback_query(call.id, "السجل غير موجود أو تم حذفه.")
        return

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-50:]
            log_text = ''.join(lines) or "لا يوجد إخراج بعد."

        if len(log_text) > 3500:
            log_text = log_text[-3500:]

        bot.send_message(
            call.message.chat.id,
            f"📝 سجل التشغيل <code>{log_filename}</code> (آخر 50 سطر):\n\n<pre>{log_text}</pre>",
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id, "تم تحميل السجل")
    except Exception as e:
        bot.answer_callback_query(call.id, "فشل في قراءة السجل")

# عرض الملفات مع الأزرار
def show_files_with_buttons(message, action_type):
    user_id = message.from_user.id
    user_dir = get_user_dir(user_id)
    files = [f for f in os.listdir(user_dir) if f.endswith('.py')]
    
    if not files:
        bot.send_message(message.chat.id, f"❌ لا توجد ملفات سكربت بايثون مرفوعة لديك حالياً.")
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for file in files:
        if action_type == "run":
            callback_data = f"run_{file}"
            button_text = f"🚀 تشغيل {file}"
        elif action_type == "delete":
            callback_data = f"delete_{file}"
            button_text = f"🗑️ حذف {file}"
        elif action_type == "stop":
            callback_data = f"stop_{file}"
            button_text = f"⛔ إيقاف {file}"
        else:
            callback_data = f"view_{file}"
            button_text = f"📂 {file}"
        
        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    
    action_texts = {
        "run": "🚀 اختر السكربت الذي تريد تشغيله:",
        "delete": "🗑️ اختر السكربت الذي تريد حذفه:",
        "stop": "⛔ اختر السكربت الذي تريد إيقافه:",
        "view": "📂 سكربتاتك المرفوعة:"
    }
    
    bot.send_message(message.chat.id, action_texts.get(action_type, "اختر الإجراء:"), reply_markup=markup)

# معالجات Callback للملفات
@bot.callback_query_handler(func=lambda call: call.data.startswith(('run_', 'delete_', 'stop_')))
def handle_file_actions(call):
    user_id = call.from_user.id
    user_dir = get_user_dir(user_id)
    
    if call.data.startswith('run_'):
        script_name = call.data.split('_', 1)[1]
        files_count = len([f for f in os.listdir(user_dir) if f.endswith('.py')])
        points = int(user_points.get(user_id, '0'))
        
        if user_id != ADMIN_ID and files_count > 2:
            if points < 20:
                bot.answer_callback_query(call.id, "❌ نقاطك غير كافية لتشغيل سكربت إضافي (تحتاج إلى 20 نقطة على الأقل).")
                return
            user_points[user_id] = str(points - 20)
            save_dict(POINTS_FILE, user_points)
            bot.send_message(call.message.chat.id, "💰 تم خصم 20 نقطة من رصيدك لتشغيل هذا السكربت الإضافي.")
        
        execute_script_setup_and_run(user_id, call.message.chat.id, user_dir, script_name)
        bot.answer_callback_query(call.id, f"جاري تشغيل {script_name}")
        
    elif call.data.startswith('delete_'):
        script_name = call.data.split('_', 1)[1]
        file_path = os.path.join(user_dir, script_name)
        try:
            os.remove(file_path)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"✅ تم حذف السكربت {script_name} بنجاح."
            )
            bot.answer_callback_query(call.id, "تم الحذف بنجاح")
        except Exception as e:
            bot.answer_callback_query(call.id, "❌ فشل في حذف الملف")
            
    elif call.data.startswith('stop_'):
        script_name = call.data.split('_', 1)[1]
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if user_dir in line and script_name in line and 'python' in line:
                    parts = line.split()
                    pid = parts[1]
                    subprocess.run(['kill', '-9', pid])
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=f"✅ تم إيقاف السكربت {script_name} بنجاح (PID: {pid})."
                    )
                    bot.answer_callback_query(call.id, "تم الإيقاف بنجاح")
                    return
            bot.answer_callback_query(call.id, "❌ السكربت غير قيد التشغيل")
        except Exception as e:
            bot.answer_callback_query(call.id, "❌ فشل في إيقاف السكربت")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_menu(call):
    user_id = call.from_user.id
    is_admin = user_id == ADMIN_ID
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "🔙 العودة للقائمة الرئيسية:", reply_markup=create_main_keyboard(is_admin))

# إيقاف السكربت
def stop_script_handler(message):
    user_dir = get_user_dir(message.from_user.id)
    running_scripts = []
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if user_dir in line and '.py' in line and 'python' in line:
                parts = line.split()
                pid = parts[1]
                cmd = ' '.join(parts[10:]) if len(parts) > 10 else ' '.join(parts[11:]) if len(parts) > 11 else ' '.join(parts[9:]) 
                script_name = extract_py_name_from_cmd(cmd)
                if not script_name:
                    m = re.search(r'([A-Za-z0-9_\-./\\]+\.py)', line)
                    if m:
                        script_name = os.path.basename(m.group(1))
                running_scripts.append((pid, script_name or 'unknown'))
    except:
        pass

    if not running_scripts:
        bot.send_message(message.chat.id, "⚠️ لا توجد سكربتات جارية حالياً في حسابك.")
        return

    show_files_with_buttons(message, "stop")

# وظائف الأدمن
def admin_show_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = []
    for folder in os.listdir(BASE_UPLOAD_DIR):
        folder_path = os.path.join(BASE_UPLOAD_DIR, folder)
        if os.path.isdir(folder_path) and folder.isdigit():
            py_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
            if py_files:
                users.append((folder, len(py_files)))
    
    if not users:
        bot.send_message(message.chat.id, "لا يوجد مستخدمين لديهم سكربتات حالياً.")
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for uid, count in users:
        markup.add(InlineKeyboardButton(f"🆔 {uid} ({count} سكربت)", callback_data=f"user_{uid}"))
    bot.send_message(message.chat.id, "👥 اختر المستخدم:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('user_'))
def admin_show_user_files(call):
    if call.from_user.id != ADMIN_ID:
        return
    user_id = call.data.split('_')[1]
    user_dir = get_user_dir(int(user_id))
    files = [f for f in os.listdir(user_dir) if f.endswith('.py')]
    
    markup = InlineKeyboardMarkup(row_width=1)
    for file in files:
        markup.add(InlineKeyboardButton(file, callback_data=f"file_{user_id}_{file}"))
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_users"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"📂 سكربتات المستخدم {user_id}:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('file_'))
def admin_send_user_file(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split('_', 2)
    user_id = parts[1]
    filename = parts[2]
    file_path = os.path.join(BASE_UPLOAD_DIR, user_id, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            bot.send_document(
                call.message.chat.id,
                document=f,
                caption=f"الملف: {filename}\nالمستخدم: {user_id}"
            )
        bot.answer_callback_query(call.id, "تم الإرسال!")
    else:
        bot.answer_callback_query(call.id, "الملف غير موجود!")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_users")
def back_to_user_list(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.delete_message(call.message.chat.id, call.message.message_id)
    dummy_msg = type('obj', (), {'from_user': call.from_user, 'chat': call.message.chat})()
    admin_show_users(dummy_msg)

# أمر Start الرئيسي
@bot.message_handler(commands=['start'])
@check_subscription
def send_welcome(message):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        ref_id = args[1].split('_')[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            add_points_from_ref(ref_id)
            bot.send_message(user_id, "🎉 لقد حصلت على نقطة إضافية من خلال رابط الدعوة! شكراً لك.")
    
    pts = user_points.get(user_id, '0')
    link = get_or_create_ref_link(user_id)
    bot.send_message(message.chat.id, f"🎉 <b>مرحباً بك في بوت استضافة سكربتات بايثون!</b> 🎉\n\n"
        "هذا البوت يسمح لك برفع سكربت بايثون الخاص بك وتشغيله 24/7 مجاناً على السيرفر!\n\n"
        "🔹 يمكنك رفع ملفين .py اثنين مجاناً\n"  
        "🔹 لرفع أكثر من سكربت تحتاج نقاط (كل سكربت إضافي = 20 نقطة)\n"
        "🔹 احصل على نقاط مجانية بدعوة أصدقائك!\n\n"
        f"💰 نقاطك الحالية: <b>{pts}</b>\n"
        f"🔗 رابط دعوتك: <code>{link}</code>\n\n"
        "اختر من الأزرار أدناه ما تريد فعله 👇", reply_markup=create_main_keyboard(is_admin), parse_mode='HTML')

# معالجة الأزرار
@bot.message_handler(func=lambda m: True)
@check_subscription
def handle_buttons(message):
    global admin_broadcasting
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    user_dir = get_user_dir(user_id)

    if user_id == ADMIN_ID and admin_broadcasting:
        users = get_all_users()
        sent_count = 0
        for uid in users:
            try:
                bot.send_message(uid, text)
                sent_count += 1
            except:
                pass
        admin_broadcasting = False
        bot.send_message(chat_id, f"✅ تم إرسال الرسالة إلى {sent_count} مستخدم بنجاح.")
        return

    if text == '📤 رفع ملف':
        bot.send_message(chat_id, "<b>📤 أرسل لي ملف بايثون (.py)🐍 لرفعه إلى حسابك</b>\n<blockquote>📌البوت قادر على اكتشاف المكتبات من السكربت لا داعي لملف requirements.txt و ايضا يمكنك رفعه ان اردت</blockquote>",
        parse_mode='HTML')
    elif text == '▶تشغيل سكربت':
        show_files_with_buttons(message, "run")
    elif text == '📂عرض الملفات':
        files = [f for f in os.listdir(user_dir) if f.endswith('.py')]
        if not files:
            bot.send_message(chat_id, "📂 لا توجد ملفات سكربت بايثون مرفوعة لديك حالياً.")
            return

        running_names = set()
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if user_dir in line and '.py' in line and 'python' in line:
                    script_name = extract_py_name_from_cmd(line)
                    if script_name:
                        running_names.add(script_name)
        except:
            pass

        msg = "📂 قائمة السكربتات المرفوعة لديك (🟢 تعمل، 🔴 متوقفة):\n\n"
        for i, f in enumerate(files):
            status = "🟢" if f in running_names else "🔴"
            msg += f"{i+1}. {f} {status}\n"
        bot.send_message(chat_id, msg)
    elif text == '🗑️ حذف ملف':
        show_files_with_buttons(message, "delete")
    elif text == '⛔إيقاف سكربت':
        stop_script_handler(message)
    elif text == '📝 السجلات':
        show_logs_handler(message)
    elif text == '📥 رفع ملف من الاستضافة' and user_id == ADMIN_ID:
        admin_show_users(message)
    elif text == '📢 إرسال إذاعة' and user_id == ADMIN_ID:
        admin_broadcasting = True
        bot.send_message(chat_id, "📢 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين.")

# معالجة رفع الملفات
@bot.message_handler(content_types=['document'])
@check_subscription
def handle_docs(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "⛔ أنت محظور من رفع الملفات بسبب انتهاك سابق.")
        return

    if message.document.file_size > 1048576:
        bot.send_message(message.chat.id, "❌ حجم الملف كبير جداً (أكثر من 1MB) وغير مسموح به لأسباب أمنية.")
        return

    user_dir = get_user_dir(user_id)
    fname = message.document.file_name

    if fname.lower() in ['venv', 'bin', 'include', 'lib', 'pyvenv.cfg', 'pip', 'python']:
         bot.send_message(message.chat.id, "❌ خطأ في اسم الملف. يرجى اختيار اسم غير محجوز.")
         return
    
    file_full_path = os.path.join(user_dir, fname)

    finfo = bot.get_file(message.document.file_id)
    data = bot.download_file(finfo.file_path)
    
    temp_path = file_full_path + ".tmp"
    with open(temp_path, 'wb') as f:
        f.write(data)

    if user_id == ADMIN_ID:
        checking_msg = bot.send_message(message.chat.id, "📤 جاري رفع الملف للأدمن...")
        os.rename(temp_path, file_full_path)
        try:
            os.chmod(file_full_path, 0o600)
        except: pass
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=checking_msg.message_id,
            text=f"✅ <b>تم رفع الملف بنجاح للأدمن:</b> <code>{fname}</code>",
            parse_mode='HTML'
        )
        return

    checking_msg = bot.send_message(message.chat.id, "🔍 جاري فحص أمان الملف المرفوع...\nهذه العملية قد تستغرق بضع ثوانٍ، يرجى الانتظار.")

    is_dangerous, reason = is_script_dangerous(temp_path, fname)

    if is_dangerous:
        temp_dangerous_path = os.path.join(TEMP_DANGEROUS_DIR, f"{user_id}_{fname}")
        os.rename(temp_path, temp_dangerous_path)
        
        try:
            with open(temp_dangerous_path, 'rb') as dangerous_file:
                username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
                full_name = message.from_user.full_name or "غير معروف"
                
                bot.send_document(
                    ADMIN_ID,
                    dangerous_file,
                    caption=f"🚨 تنبيه أمان! - سكربت ضار تم اكتشافه\n\n"
                           f"🆔 معرف المستخدم: {user_id}\n"
                           f"👤 الاسم: {full_name}\n"
                           f"📛 يوزر: {username}\n"
                           f"📄 اسم الملف: {fname}\n"
                           f"⚠️ السبب: {reason}\n\n"
                           f"تم اكتشاف سكربت ضار وحظر المستخدم تلقائياً."
                )
                logging.info(f"تم إرسال السكربت الضار إلى الأدمن: {fname}")
        except Exception as e:
            logging.error(f"فشل إرسال السكربت الضار للأدمن: {e}")
            
            bot.send_message(
                ADMIN_ID,
                f"🚨 تنبيه أمان! - فشل إرسال السكربت الضار\n\n"
                f"🆔 معرف المستخدم: {user_id}\n"
                f"👤 الاسم: {full_name}\n"
                f"📛 يوزر: {username}\n"
                f"📄 اسم الملف: {fname}\n"
                f"⚠️ السبب: {reason}\n"
                f"❌ خطأ الإرسال: {str(e)}"
            )

        ban_user(user_id)
        logging.info(f"تم حظر المستخدم: {user_id}")

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=checking_msg.message_id,
            text="🚨 <b>تم رفض رفع الملف وحذفه فوراً!</b>\n\n"
                 "🔴 تم اكتشاف محتوى ضار أو مشبوه في السكربت.\n"
                 "⛔ <b>تم حظرك نهائياً</b> من استخدام البوت لمحاولة رفع سكربت ضار.\n"
                 "هذا الإجراء لحماية السيرفر والمستخدمين الآخرين.\n\n"
                 "إذا كنت تعتقد أن هذا خطأ، تواصل مع الأدمن.",
            parse_mode='HTML'
        )

        try:
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(InlineKeyboardButton("فك الحظر فقط", callback_data=f"unban_only_{user_id}"))
            markup.add(InlineKeyboardButton("قبول السكريبت", callback_data=f"accept_{user_id}_{fname}"))
            
            bot.send_message(
                ADMIN_ID,
                f"🚨 <b>تنبيه أمان عاجل!</b>\n\n"
                f"المستخدم حاول رفع سكربت ضار:\n"
                f"🆔 معرف: {user_id}\n"
                f"👤 الاسم: {full_name}\n"
                f"📛 يوزر: {username}\n"
                f"📄 اسم الملف: {fname}\n"
                f"⚠️ السبب: {reason}\n\n"
                f"تم حظره تلقائياً.\n"
                f"تم إرسال نسخة من السكربت الضار في الرسالة السابقة.\n"
                f"اختر: فك الحظر فقط، أو قبول السكريبت (سيرفع الملف ويفك الحظر ويرسل إشعار للمستخدم).",
                reply_markup=markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"فشل إرسال تنبيه الأدمن: {e}")

    else:
        os.rename(temp_path, file_full_path)
        try:
            os.chmod(file_full_path, 0o600)
        except: pass

        if fname.endswith('.py'):
            current = [f for f in os.listdir(user_dir) if f.endswith('.py') and f != fname]
            if user_id != ADMIN_ID and len(current) >= 2 and int(user_points.get(user_id, '0')) < 20:
                os.remove(file_full_path)
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=checking_msg.message_id,
                    text="❌ نقاطك غير كافية لرفع سكربت إضافي (تحتاج 20 نقطة على الأقل)."
                )
                return

            if user_id != ADMIN_ID and len(current) >= 2:
                user_points[user_id] = str(int(user_points.get(user_id, '0')) - 20)
                save_dict(POINTS_FILE, user_points)

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=checking_msg.message_id,
            text=f"✅ <b>تم فحص الملف وهو آمن تماماً!</b>\n"
                 f"📤 تم رفع الملف بنجاح: <code>{fname}</code>\n"
                 "يمكنك الآن تشغيله من القائمة.",
            parse_mode='HTML'
        )

# --- تعديل جزء التشغيل ليتوافق مع الاستضافات السحابية ---
if __name__ == '__main__':
    # تشغيل Flask في الخلفية
    keep_alive()
    
    print("🚀 Bot is starting...")
    
    # محاولة ضبط الأوامر مع معالجة الخطأ إذا فشل الاتصال
    try:
        bot.set_my_commands([
            BotCommand("start", "Start Bot"), 
            BotCommand("antihack", "إدارة المحظورين")
        ])
        print("✅ Commands set successfully.")
    except Exception as e:
        print(f"⚠️ Could not set commands (Network issue): {e}")

    # حلقة تشغيل البوت مع إعادة المحاولة التلقائية عند انقطاع الإنترنت
    while True:
        try:
            print("Connect to Telegram API...")
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception as e:
            logging.error(f"❌ Polling Error: {e}")
            time.sleep(10)  # الانتظار 10 ثوانٍ قبل إعادة المحاولة
 
