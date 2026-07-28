import os
import logging
import httpx
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    TOKEN = "8860863617:AAFizT8wFBJFt4uq7U9NpGfK_jwahrA35_o"

OWNER_ID = 7803165903
API_ID = 37160656
API_HASH = "c75ef3eadae1ffb6cad9d6736d0e2323"

user_sessions = {}

# پاک کردن Webhook
try:
    httpx.post(
        f"https://api.telegram.org/bot{TOKEN}/deleteWebhook",
        json={"drop_pending_updates": True},
        timeout=30
    )
    print("✅ Webhook پاک شد")
except:
    pass

time.sleep(2)

OWNER_START_TEXT = """
🌟 <b>سازنده ربات عزیز به ربات ZX خوش آمدید!</b> 🌹

⫸ لطفاً از منوی زیر کار خودتون رو انتخاب کنید:

🔹 <b>افزودن اکانت:</b> برای ساخت سشن تلگرام
🔹 <b>تنظیمات:</b> برای تغییر تنظیمات ربات
🔹 <b>حمله:</b> برای انجام عملیات حمله

⚡ <b>وضعیت ربات:</b> فعال ✅
"""

NORMAL_START_TEXT = "⛔ <b>دسترسی محدود!</b>"

def start(update, context):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        update.message.reply_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(NORMAL_START_TEXT, parse_mode='HTML')

def button_callback(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != OWNER_ID:
        query.answer("⛔ دسترسی ندارید!", show_alert=True)
        return
    
    query.answer()
    
    if query.data == 'add_account':
        user_sessions[user_id] = {'step': 'phone'}
        query.edit_message_text(
            "📱 شماره تلفن خود را ارسال کنید:\nمثال: +989123456789\n\nبرای لغو: /cancel",
            parse_mode='HTML'
        )
    elif query.data == 'settings':
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        query.edit_message_text(
            "⚙️ تنظیمات در حال توسعه...",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'attack':
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        query.edit_message_text(
            "💥 بخش حمله در حال توسعه...",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        query.edit_message_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def handle_message(update, context):
    user_id = update.effective_user.id
    if user_id != OWNER_ID or user_id not in user_sessions:
        return
    
    text = update.message.text
    step = user_sessions[user_id]['step']
    
    if step == 'phone':
        if not text.startswith('+') or not text[1:].isdigit():
            update.message.reply_text("❌ فرمت شماره نامعتبر! مثال: +989123456789")
            return
        
        user_sessions[user_id]['phone'] = text
        user_sessions[user_id]['step'] = 'code'
        
        try:
            from pyrogram import Client
            app = Client(f"session_{user_id}", api_id=API_ID, api_hash=API_HASH, phone_number=text)
            app.connect()
            sent_code = app.send_code(text)
            user_sessions[user_id]['client'] = app
            user_sessions[user_id]['phone_code_hash'] = sent_code.phone_code_hash
            update.message.reply_text(f"📨 کد تایید به {text} ارسال شد. کد ۵ رقمی را وارد کنید.")
        except Exception as e:
            update.message.reply_text(f"❌ خطا: {str(e)}")
            del user_sessions[user_id]
    
    elif step == 'code':
        if not text.isdigit() or len(text) != 5:
            update.message.reply_text("❌ کد باید ۵ رقم باشد!")
            return
        
        try:
            phone = user_sessions[user_id]['phone']
            phone_code_hash = user_sessions[user_id]['phone_code_hash']
            app = user_sessions[user_id]['client']
            
            app.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=text)
            session_string = app.export_session_string()
            
            with open(f"session_{phone}.txt", "w") as f:
                f.write(session_string)
            
            update.message.reply_text(
                f"✅ سشن ساخته شد!\n\n📱 شماره: {phone}\n\n🔑 سشن:\n<code>{session_string}</code>",
                parse_mode='HTML'
            )
            
            app.disconnect()
            del user_sessions[user_id]
        except Exception as e:
            update.message.reply_text(f"❌ خطا در ساخت سشن: {str(e)}")
            if user_id in user_sessions:
                if 'client' in user_sessions[user_id]:
                    try:
                        user_sessions[user_id]['client'].disconnect()
                    except:
                        pass
                del user_sessions[user_id]

def cancel_command(update, context):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        if 'client' in user_sessions[user_id]:
            try:
                user_sessions[user_id]['client'].disconnect()
            except:
                pass
        del user_sessions[user_id]
        update.message.reply_text("❌ عملیات لغو شد!")
    else:
        update.message.reply_text("ℹ️ هیچ عملیاتی وجود ندارد!")

if __name__ == '__main__':
    try:
        print("🚀 ربات در حال راه‌اندازی...")
        
        updater = Updater(token=TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler('start', start))
        dp.add_handler(CommandHandler('cancel', cancel_command))
        dp.add_handler(CallbackQueryHandler(button_callback))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        print(f"✅ ربات با موفقیت راه‌اندازی شد!")
        print(f"👤 سازنده: {OWNER_ID}")
        
        updater.start_polling(drop_pending_updates=True)
        updater.idle()
        
    except Exception as e:
        print(f"❌ خطا: {e}")
