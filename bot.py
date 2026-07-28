import os
import logging
import httpx
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# توکن جدید
TOKEN = "8576876988:AAGBLHEz9IAQa9NwgG6L8tWZnUQjUifxu10"
OWNER_ID = 7803165903

# ✅ API_ID و API_HASH جدید
API_ID = 29811798
API_HASH = "ef5847a43a978d6883b97b0caeb81736"

user_sessions = {}

OWNER_START_TEXT = """
🌟 <b>سازنده ربات عزیز به ربات ZX خوش آمدید!</b> 🌹

⫸ لطفاً از منوی زیر کار خودتون رو انتخاب کنید:

🔹 <b>افزودن اکانت:</b> برای ساخت سشن تلگرام
🔹 <b>تنظیمات:</b> برای تغییر تنظیمات ربات
🔹 <b>حمله:</b> برای انجام عملیات حمله

⚡ <b>وضعیت ربات:</b> فعال ✅
"""

NORMAL_START_TEXT = "⛔ <b>دسترسی محدود!</b>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        await update.message.reply_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(NORMAL_START_TEXT, parse_mode='HTML')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != OWNER_ID:
        await query.answer("⛔ دسترسی ندارید!", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'add_account':
        user_sessions[user_id] = {'step': 'phone'}
        
        # استفاده از API_ID و API_HASH جدید به صورت پیش‌فرض
        user_sessions[user_id]['api_id'] = API_ID
        user_sessions[user_id]['api_hash'] = API_HASH
        
        await query.edit_message_text(
            "📱 <b>مرحله ۱: وارد کردن شماره تلفن</b>\n\n"
            "◄ لطفاً <b>شماره تلفن</b> اکانت تلگرام خود را وارد کنید.\n"
            "◂ مثال: <code>+989123456789</code>\n\n"
            "💡 <b>نکته:</b> از API_ID و API_HASH جدید استفاده میشه:\n"
            f"🔑 API_ID: <code>{API_ID}</code>\n"
            f"🔑 API_HASH: <code>{API_HASH}</code>\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    elif query.data == 'settings':
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
            "⚙️ <b>تنظیمات ربات</b>\n\n"
            f"🔑 API_ID: <code>{API_ID}</code>\n"
            f"🔑 API_HASH: <code>{API_HASH}</code>\n\n"
            "📍 در حال توسعه...",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'attack':
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
            "💥 <b>بخش حمله</b>\n\n"
            "📍 در حال توسعه...",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        await query.edit_message_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID or user_id not in user_sessions:
        return
    
    text = update.message.text.strip()
    step = user_sessions[user_id]['step']
    
    # مرحله ۱: دریافت شماره تلفن
    if step == 'phone':
        if not text.startswith('+') or not text[1:].isdigit():
            await update.message.reply_text(
                "❌ فرمت شماره نامعتبر! مثال: +989123456789\n\n"
                "◄ لطفاً شماره را با کد کشور وارد کنید.",
                parse_mode='HTML'
            )
            return
        
        user_sessions[user_id]['phone'] = text
        user_sessions[user_id]['step'] = 'code'
        
        # ارسال کد تایید با API جدید
        try:
            from pyrogram import Client
            
            api_id = user_sessions[user_id]['api_id']
            api_hash = user_sessions[user_id]['api_hash']
            
            app = Client(
                f"session_{user_id}",
                api_id=api_id,
                api_hash=api_hash,
                phone_number=text
            )
            
            await app.connect()
            sent_code = await app.send_code(text)
            
            user_sessions[user_id]['client'] = app
            user_sessions[user_id]['phone_code_hash'] = sent_code.phone_code_hash
            
            await update.message.reply_text(
                f"📨 <b>کد تایید ارسال شد!</b>\n\n"
                f"◄ کد ۵ رقمی به شماره <code>{text}</code> ارسال شد.\n"
                f"◂ لطفاً کد دریافتی را وارد کنید.\n\n"
                f"⫸ برای لغو: /cancel",
                parse_mode='HTML'
            )
            
        except Exception as e:
            error_msg = str(e)
            await update.message.reply_text(
                f"❌ <b>خطا در ارسال کد!</b>\n\n"
                f"◄ خطا: <code>{error_msg}</code>\n\n"
                "◂ لطفاً اطلاعات زیر رو بررسی کن:\n"
                f"🔑 API_ID: <code>{user_sessions[user_id]['api_id']}</code>\n"
                f"🔑 API_HASH: <code>{user_sessions[user_id]['api_hash']}</code>\n\n"
                "◄ مطمئن شوید API_ID و API_HASH درست هستن.\n"
                "⫸ برای شروع مجدد /start را بزنید.",
                parse_mode='HTML'
            )
            if user_id in user_sessions:
                del user_sessions[user_id]
    
    # مرحله ۲: دریافت کد تایید
    elif step == 'code':
        if not text.isdigit() or len(text) != 5:
            await update.message.reply_text(
                "❌ کد باید ۵ رقم باشد! دوباره وارد کنید:",
                parse_mode='HTML'
            )
            return
        
        try:
            phone = user_sessions[user_id]['phone']
            phone_code_hash = user_sessions[user_id]['phone_code_hash']
            app = user_sessions[user_id]['client']
            
            # تایید کد
            await app.sign_in(
                phone_number=phone,
                phone_code_hash=phone_code_hash,
                phone_code=text
            )
            
            # ساخت سشن
            session_string = await app.export_session_string()
            
            # ذخیره سشن در فایل
            with open(f"session_{phone}.txt", "w") as f:
                f.write(session_string)
            
            await update.message.reply_text(
                f"✅ <b>سشن با موفقیت ساخته شد!</b>\n\n"
                f"📱 <b>شماره:</b> <code>{phone}</code>\n\n"
                f"🔑 <b>سشن استرینگ:</b>\n"
                f"<code>{session_string}</code>\n\n"
                f"◄ سشن در فایل <code>session_{phone}.txt</code> ذخیره شد.\n\n"
                f"⫸ برای بازگشت به منوی اصلی /start را بزنید.",
                parse_mode='HTML'
            )
            
            await app.disconnect()
            
            if user_id in user_sessions:
                del user_sessions[user_id]
            
        except Exception as e:
            error_msg = str(e)
            await update.message.reply_text(
                f"❌ <b>خطا در ساخت سشن!</b>\n\n"
                f"◄ خطا: <code>{error_msg}</code>\n\n"
                "◂ لطفاً کد وارد شده را بررسی کنید.\n"
                "⫸ برای شروع مجدد /start را بزنید.",
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
    user_id = update.effective_user.id
    if user_id in user_sessions:
        if 'client' in user_sessions[user_id]:
            try:
                await user_sessions[user_id]['client'].disconnect()
            except:
                pass
        del user_sessions[user_id]
        await update.message.reply_text(
            "❌ <b>عملیات لغو شد!</b>\n\n"
            "◄ برای شروع مجدد /start را بزنید.",
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
        print(f"🔑 API_ID: {API_ID}")
        print(f"🔑 API_HASH: {API_HASH}")
        
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print(f"✅ ربات با موفقیت راه‌اندازی شد!")
        print(f"👤 سازنده: {OWNER_ID}")
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        print(f"❌ خطا: {e}")
