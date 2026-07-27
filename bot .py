import os
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# گرفتن توکن از محیط
TOKEN = os.getenv('TOKEN')

# اگر توکن در محیط نیست
if not TOKEN:
    TOKEN = "8860863617:AAFizT8wFBJFt4uq7U9NpGfK_jwahrA35_o"

# شناسه عددی سازنده ربات (فقط این کاربر می‌تونه از ربات استفاده کنه)
OWNER_ID = 7803165903  # ✅ ایدی شما تنظیم شد

# 🔑 اطلاعات API خود را از my.telegram.org بگیرید
API_ID = 37160656  # API ID خود را اینجا بگذارید
API_HASH = "c75ef3eadae1ffb6cad9d6736d0e2323"  # API HASH خود را اینجا بگذارید

# متغیرهای ذخیره موقت برای فرآیند ساخت سشن
user_sessions = {}

# پاک کردن Webhook قبلی
try:
    response = httpx.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    if response.json().get('ok'):
        print("✅ Webhook قبلی پاک شد")
except Exception as e:
    print(f"⚠️ خطا در پاک کردن Webhook: {e}")

# متن استارت برای سازنده ربات
OWNER_START_TEXT = """
🌟 <b>سازنده ربات عزیز به ربات ZX خوش آمدید!</b> 🌹

⫸ لطفاً از منوی زیر کار خودتون رو انتخاب کنید:

🔹 <b>افزودن اکانت:</b> برای ساخت سشن تلگرام جهت اتصال به ویس چت
🔹 <b>تنظیمات:</b> برای تغییر تنظیمات ربات
🔹 <b>حمله:</b> برای انجام عملیات حمله (در حال توسعه)

⚡ <b>وضعیت ربات:</b> فعال ✅
🔄 <b>نسخه:</b> 2.0.0

【 <b>Licenced By 🆉︎🆇︎</b> 】
"""

# متن استارت برای کاربران عادی (هیچی بهشون نشون نمیده)
NORMAL_START_TEXT = """
⛔ <b>دسترسی محدود!</b>

شما اجازه استفاده از این ربات را ندارید.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر /start با تشخیص سازنده"""
    user = update.effective_user
    user_id = user.id
    
    # بررسی اینکه آیا کاربر سازنده ربات است
    if user_id == OWNER_ID:
        # نمایش منوی اصلی برای سازنده
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        # برای کاربران عادی هیچی نشون نده
        await update.message.reply_text(
            NORMAL_START_TEXT,
            parse_mode='HTML'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک روی دکمه‌ها"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # فقط سازنده می‌تواند از دکمه‌ها استفاده کند
    if user_id != OWNER_ID:
        await query.answer("⛔ شما دسترسی به این بخش را ندارید!", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'add_account':
        # شروع فرآیند ساخت سشن
        user_sessions[user_id] = {'step': 'phone'}
        
        await query.edit_message_text(
            "📱 <b>افزودن اکانت جدید</b>\n\n"
            "◄ لطفاً <b>شماره تلفن</b> اکانت تلگرام خود را به همراه کد کشور ارسال کنید.\n\n"
            "◂ مثال: <code>+989123456789</code>\n\n"
            "⫸ برای لغو عملیات، دستور /cancel را ارسال کنید.",
            parse_mode='HTML'
        )
    
    elif query.data == 'settings':
        # منوی تنظیمات
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ <b>تنظیمات ربات</b>\n\n"
            "🔹 <b>API ID:</b> تنظیم نشده\n"
            "🔹 <b>API HASH:</b> تنظیم نشده\n"
            "🔹 <b>حالت ربات:</b> فعال\n\n"
            "📍 تنظیمات در حال توسعه...",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == 'attack':
        # منوی حمله
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💥 <b>بخش حمله</b>\n\n"
            "🔹 این بخش در حال توسعه می‌باشد.\n"
            "🔹 به زودی قابلیت‌های حمله اضافه می‌شوند.\n\n"
            "📍 در حال توسعه...",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == 'back_to_menu':
        # بازگشت به منوی اصلی
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های دریافتی برای فرآیند ساخت سشن"""
    user_id = update.effective_user.id
    
    # فقط سازنده می‌تواند از این فرآیند استفاده کند
    if user_id != OWNER_ID:
        return
    
    # بررسی اینکه کاربر در فرآیند ساخت سشن است
    if user_id not in user_sessions:
        return
    
    text = update.message.text
    step = user_sessions[user_id]['step']
    
    if step == 'phone':
        # دریافت شماره تلفن
        phone = text.strip()
        
        # اعتبارسنجی ساده شماره
        if not phone.startswith('+') or not phone[1:].isdigit():
            await update.message.reply_text(
                "❌ <b>فرمت شماره تلفن نامعتبر!</b>\n\n"
                "◄ لطفاً شماره را به همراه کد کشور و با فرمت صحیح ارسال کنید.\n"
                "◂ مثال: <code>+989123456789</code>",
                parse_mode='HTML'
            )
            return
        
        # ذخیره شماره و ارسال کد تایید
        user_sessions[user_id]['phone'] = phone
        user_sessions[user_id]['step'] = 'code'
        
        # ارسال کد تایید به شماره کاربر
        await send_verification_code(update, user_id, phone)
    
    elif step == 'code':
        # دریافت کد تایید
        code = text.strip()
        
        if not code.isdigit() or len(code) != 5:
            await update.message.reply_text(
                "❌ <b>کد وارد شده نامعتبر!</b>\n\n"
                "◄ لطفاً کد عددی ۵ رقمی ارسال شده را وارد کنید.",
                parse_mode='HTML'
            )
            return
        
        # تایید کد و ساخت سشن
        await verify_code_and_create_session(update, user_id, code)

async def send_verification_code(update: Update, user_id: int, phone: str):
    """ارسال کد تایید به شماره کاربر با استفاده از pyrogram"""
    try:
        from pyrogram import Client
        
        # استفاده از API_ID و API_HASH تعریف شده در بالا
        app = Client(
            f"session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=phone
        )
        
        await app.connect()
        sent_code = await app.send_code(phone)
        
        # ذخیره اطلاعات برای مرحله بعد
        user_sessions[user_id]['client'] = app
        user_sessions[user_id]['phone_code_hash'] = sent_code.phone_code_hash
        
        await update.message.reply_text(
            f"📨 <b>کد تایید ارسال شد!</b>\n\n"
            f"◄ کد ۵ رقمی به شماره <code>{phone}</code> ارسال شد.\n"
            f"◂ لطفاً کد دریافتی را وارد کنید.\n\n"
            f"⫸ برای لغو عملیات، دستور /cancel را ارسال کنید.",
            parse_mode='HTML'
        )
        
        user_sessions[user_id]['step'] = 'code'
        
    except ImportError:
        await update.message.reply_text(
            "❌ <b>کتابخانه pyrogram نصب نیست!</b>\n\n"
            "◄ لطفاً ابتدا pyrogram را نصب کنید:\n"
            "◂ <code>pip install pyrogram</code>",
            parse_mode='HTML'
        )
        if user_id in user_sessions:
            del user_sessions[user_id]
            
    except Exception as e:
        error_msg = str(e)
        if "API_ID_INVALID" in error_msg:
            await update.message.reply_text(
                f"❌ <b>خطا در ارسال کد!</b>\n\n"
                f"◄ خطا: <code>{error_msg}</code>\n\n"
                "◂ <b>API_ID و API_HASH</b> نامعتبر هستند!\n"
                "◄ لطفاً از سایت <a href='https://my.telegram.org'>my.telegram.org</a> مقادیر جدید بگیرید.\n"
                "◂ مطمئن شوید با شماره‌ای که میخواهید سشن بسازید وارد شده‌اید.\n"
                "⫸ برای شروع مجدد، روی دکمه افزودن اکانت کلیک کنید.",
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text(
                f"❌ <b>خطا در ارسال کد!</b>\n\n"
                f"◄ خطا: <code>{error_msg}</code>\n\n"
                "◂ لطفاً شماره و API را بررسی کنید.\n"
                "⫸ برای شروع مجدد، روی دکمه افزودن اکانت کلیک کنید.",
                parse_mode='HTML'
            )
        # پاک کردن جلسه در صورت خطا
        if user_id in user_sessions:
            del user_sessions[user_id]

async def verify_code_and_create_session(update: Update, user_id: int, code: str):
    """تایید کد و ساخت سشن"""
    try:
        from pyrogram import Client
        
        # دریافت اطلاعات از جلسه
        phone = user_sessions[user_id]['phone']
        phone_code_hash = user_sessions[user_id]['phone_code_hash']
        app = user_sessions[user_id]['client']
        
        # تایید کد
        await app.sign_in(
            phone_number=phone,
            phone_code_hash=phone_code_hash,
            phone_code=code
        )
        
        # ساخت سشن استرینگ
        session_string = await app.export_session_string()
        
        # ذخیره سشن در فایل (اختیاری)
        with open(f"session_{phone}.txt", "w") as f:
            f.write(session_string)
        
        await update.message.reply_text(
            f"✅ <b>سشن با موفقیت ساخته شد!</b>\n\n"
            f"📱 <b>شماره:</b> <code>{phone}</code>\n\n"
            f"🔑 <b>سشن استرینگ:</b>\n"
            f"<code>{session_string}</code>\n\n"
            f"◄ سشن در فایل <code>session_{phone}.txt</code> ذخیره شد.\n"
            f"◂ این سشن برای پخش موزیک در ویس چت استفاده خواهد شد.\n\n"
            f"⫸ برای بازگشت به منوی اصلی، /start را بزنید.",
            parse_mode='HTML'
        )
        
        await app.disconnect()
        
        # پاک کردن جلسه کاربر
        if user_id in user_sessions:
            del user_sessions[user_id]
        
    except Exception as e:
        error_msg = str(e)
        await update.message.reply_text(
            f"❌ <b>خطا در ساخت سشن!</b>\n\n"
            f"◄ خطا: <code>{error_msg}</code>\n\n"
            "◂ لطفاً کد وارد شده را بررسی کنید و دوباره تلاش کنید.\n"
            "⫸ برای شروع مجدد، روی دکمه افزودن اکانت کلیک کنید.",
            parse_mode='HTML'
        )
        
        # پاک کردن جلسه در صورت خطا
        if user_id in user_sessions:
            # قطع اتصال کلاینت
            if 'client' in user_sessions[user_id]:
                try:
                    await user_sessions[user_id]['client'].disconnect()
                except:
                    pass
            del user_sessions[user_id]

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر /cancel برای لغو عملیات"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        # پاک کردن کلاینت در صورت وجود
        if 'client' in user_sessions[user_id]:
            try:
                await user_sessions[user_id]['client'].disconnect()
            except:
                pass
        
        del user_sessions[user_id]
        
        await update.message.reply_text(
            "❌ <b>عملیات لغو شد!</b>\n\n"
            "◄ فرآیند ساخت سشن با موفقیت لغو شد.\n"
            "◂ برای بازگشت به منوی اصلی، /start را ارسال کنید.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "ℹ️ <b>هیچ عملیات فعالی برای لغو وجود ندارد!</b>",
            parse_mode='HTML'
        )

if __name__ == '__main__':
    try:
        # ساخت اپلیکیشن
        application = ApplicationBuilder().token(TOKEN).build()
        
        # اضافه کردن هندلرها
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print(f"🚀 ربات در حال روشن شدن با Polling...")
        print(f"✅ Webhook قبلی پاک شده")
        print(f"👤 سازنده ربات: {OWNER_ID}")
        print(f"🔑 API_ID: {API_ID}")
        
        # راه‌اندازی با Polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        print(f"❌ خطا: {e}")
