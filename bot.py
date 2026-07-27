import os
import logging
import httpx
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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

# شناسه عددی سازنده ربات
OWNER_ID = 7803165903  # ✅ ایدی شما

# 🔑 اطلاعات API
API_ID = 37160656
API_HASH = "c75ef3eadae1ffb6cad9d6736d0e2323"

# متغیرهای ذخیره موقت
user_sessions = {}

# پاک کردن Webhook قبلی
print("🔄 در حال پاک کردن Webhook قبلی...")
for attempt in range(3):
    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{TOKEN}/deleteWebhook",
            json={"drop_pending_updates": True},
            timeout=30
        )
        if response.json().get('ok'):
            print("✅ Webhook قبلی با موفقیت پاک شد")
            break
    except Exception as e:
        print(f"⚠️ تلاش {attempt + 1}: خطا - {e}")
    time.sleep(2)

time.sleep(3)

# متن استارت برای سازنده
OWNER_START_TEXT = """
🌟 <b>سازنده ربات عزیز به ربات ZX خوش آمدید!</b> 🌹

⫸ لطفاً از منوی زیر کار خودتون رو انتخاب کنید:

🔹 <b>افزودن اکانت:</b> برای ساخت سشن تلگرام
🔹 <b>تنظیمات:</b> برای تغییر تنظیمات ربات
🔹 <b>حمله:</b> برای انجام عملیات حمله

⚡ <b>وضعیت ربات:</b> فعال ✅

【 <b>Licenced By 🆉︎🆇︎</b> 】
"""

# متن برای کاربران عادی
NORMAL_START_TEXT = """
⛔ <b>دسترسی محدود!</b>
شما اجازه استفاده از این ربات را ندارید.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر /start"""
    user = update.effective_user
    user_id = user.id
    
    if user_id == OWNER_ID:
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
        await update.message.reply_text(
            NORMAL_START_TEXT,
            parse_mode='HTML'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌ها"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != OWNER_ID:
        await query.answer("⛔ شما دسترسی ندارید!", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'add_account':
        user_sessions[user_id] = {'step': 'phone'}
        
        await query.edit_message_text(
            "📱 <b>افزودن اکانت جدید</b>\n\n"
            "◄ لطفاً <b>شماره تلفن</b> خود را ارسال کنید.\n"
            "◂ مثال: <code>+989123456789</code>\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ <b>تنظیمات ربات</b>\n\n"
            "📍 در حال توسعه...",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == 'attack':
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💥 <b>بخش حمله</b>\n\n"
            "📍 در حال توسعه...",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == 'back_to_menu':
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
    """مدیریت پیام‌ها"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        return
    
    if user_id not in user_sessions:
        return
    
    text = update.message.text
    step = user_sessions[user_id]['step']
    
    if step == 'phone':
        phone = text.strip()
        
        if not phone.startswith('+') or not phone[1:].isdigit():
            await update.message.reply_text(
                "❌ <b>فرمت شماره نامعتبر!</b>\n\n"
                "◄ مثال: <code>+989123456789</code>",
                parse_mode='HTML'
            )
            return
        
        user_sessions[user_id]['phone'] = phone
        user_sessions[user_id]['step'] = 'code'
        
        await send_verification_code(update, user_id, phone)
    
    elif step == 'code':
        code = text.strip()
        
        if not code.isdigit() or len(code) != 5:
            await update.message.reply_text(
                "❌ <b>کد نامعتبر!</b>\n\n"
                "◄ کد ۵ رقمی را وارد کنید.",
                parse_mode='HTML'
            )
            return
        
        await verify_code_and_create_session(update, user_id, code)

async def send_verification_code(update: Update, user_id: int, phone: str):
    """ارسال کد تایید"""
    try:
        from pyrogram import Client
        
        app = Client(
            f"session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=phone
        )
        
        await app.connect()
        sent_code = await app.send_code(phone)
        
        user_sessions[user_id]['client'] = app
        user_sessions[user_id]['phone_code_hash'] = sent_code.phone_code_hash
        
        await update.message.reply_text(
            f"📨 <b>کد تایید ارسال شد!</b>\n\n"
            f"◄ کد به شماره <code>{phone}</code> ارسال شد.\n"
            f"◂ کد ۵ رقمی را وارد کنید.",
            parse_mode='HTML'
        )
        
    except Exception as e:
        error_msg = str(e)
        await update.message.reply_text(
            f"❌ <b>خطا!</b>\n\n"
            f"◄ خطا: <code>{error_msg}</code>",
            parse_mode='HTML'
        )
        if user_id in user_sessions:
            del user_sessions[user_id]

async def verify_code_and_create_session(update: Update, user_id: int, code: str):
    """تایید کد و ساخت سشن"""
    try:
        from pyrogram import Client
        
        phone = user_sessions[user_id]['phone']
        phone_code_hash = user_sessions[user_id]['phone_code_hash']
        app = user_sessions[user_id]['client']
        
        await app.sign_in(
            phone_number=phone,
            phone_code_hash=phone_code_hash,
            phone_code=code
        )
        
        session_string = await app.export_session_string()
        
        with open(f"session_{phone}.txt", "w") as f:
            f.write(session_string)
        
        await update.message.reply_text(
            f"✅ <b>سشن ساخته شد!</b>\n\n"
            f"📱 <b>شماره:</b> <code>{phone}</code>\n\n"
            f"🔑 <b>سشن:</b>\n"
            f"<code>{session_string}</code>\n\n"
            f"◄ در فایل <code>session_{phone}.txt</code> ذخیره شد.",
            parse_mode='HTML'
        )
        
        await app.disconnect()
        
        if user_id in user_sessions:
            del user_sessions[user_id]
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>خطا در ساخت سشن!</b>\n\n"
            f"◄ خطا: <code>{str(e)}</code>",
            parse_mode='HTML'
        )
        
        if user_id in user_sessions:
            if 'client' in user_sessions[user_id]:
                try:
                    await user_sessions[user_id]['client'].disconnect()
                except:
                    pass
            del user_sessions[user_id]

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        if 'client' in user_sessions[user_id]:
            try:
                await user_sessions[user_id]['client'].disconnect()
            except:
                pass
        
        del user_sessions[user_id]
        
        await update.message.reply_text(
            "❌ <b>عملیات لغو شد!</b>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "ℹ️ <b>هیچ عملیاتی وجود ندارد!</b>",
            parse_mode='HTML'
        )

if __name__ == '__main__':
    try:
        print("🚀 ربات در حال راه‌اندازی...")
        
        # ساخت اپلیکیشن
        application = ApplicationBuilder().token(TOKEN).build()
        
        # اضافه کردن هندلرها
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print(f"✅ ربات با موفقیت راه‌اندازی شد!")
        print(f"👤 سازنده ربات: {OWNER_ID}")
        
        # شروع Polling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        print(f"❌ خطا: {e}")
