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

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    TOKEN = "8860863617:AAFizT8wFBJFt4uq7U9NpGfK_jwahrA35_o"

OWNER_ID = 7803165903
API_ID = 37160656
API_HASH = "c75ef3eadae1ffb6cad9d6736d0e2323"

user_sessions = {}

# پاک کردن Webhook با چند بار تلاش
def delete_webhook():
    for i in range(5):
        try:
            response = httpx.post(
                f"https://api.telegram.org/bot{TOKEN}/deleteWebhook",
                json={"drop_pending_updates": True},
                timeout=30
            )
            if response.json().get('ok'):
                print(f"✅ Webhook پاک شد (تلاش {i+1})")
                return True
        except Exception as e:
            print(f"⚠️ تلاش {i+1} ناموفق: {e}")
        time.sleep(2)
    return False

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
        await query.edit_message_text(
            "📱 شماره تلفن خود را ارسال کنید:\nمثال: +989123456789\n\nبرای لغو: /cancel",
            parse_mode='HTML'
        )
    elif query.data == 'settings':
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
            "⚙️ تنظیمات در حال توسعه...",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == 'attack':
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
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
        await query.edit_message_text(
            OWNER_START_TEXT,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID or user_id not in user_sessions:
        return
    
    text = update.message.text
    step = user_sessions[user_id]['step']
    
    if step == 'phone':
        if not text.startswith('+') or not text[1:].isdigit():
            await update.message.reply_text("❌ فرمت شماره نامعتبر! مثال: +989123456789")
            return
        
        user_sessions[user_id]['phone'] = text
        user_sessions[user_id]['step'] = 'code'
        
        try:
            from pyrogram import Client
            app = Client(f"session_{user_id}", api_id=API_ID, api_hash=API_HASH, phone_number=text)
            await app.connect()
            sent_code = await app.send_code(text)
            user_sessions[user_id]['client'] = app
            user_sessions[user_id]['phone_code_hash'] = sent_code.phone_code_hash
            await update.message.reply_text(f"📨 کد تایید به {text} ارسال شد. کد ۵ رقمی را وارد کنید.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            del user_sessions[user_id]
    
    elif step == 'code':
        if not text.isdigit() or len(text) != 5:
            await update.message.reply_text("❌ کد باید ۵ رقم باشد!")
            return
        
        try:
            phone = user_sessions[user_id]['phone']
            phone_code_hash = user_sessions[user_id]['phone_code_hash']
            app = user_sessions[user_id]['client']
            
            await app.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=text)
            session_string = await app.export_session_string()
            
            with open(f"session_{phone}.txt", "w") as f:
                f.write(session_string)
            
            await update.message.reply_text(
                f"✅ سشن ساخته شد!\n\n📱 شماره: {phone}\n\n🔑 سشن:\n<code>{session_string}</code>",
                parse_mode='HTML'
            )
            
            await app.disconnect()
            del user_sessions[user_id]
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ساخت سشن: {str(e)}")
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
        await update.message.reply_text("❌ عملیات لغو شد!")
    else:
        await update.message.reply_text("ℹ️ هیچ عملیاتی وجود ندارد!")

if __name__ == '__main__':
    try:
        # پاک کردن Webhook با چند بار تلاش
        delete_webhook()
        time.sleep(3)
        
        print("🚀 ربات در حال راه‌اندازی...")
        
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print(f"✅ ربات با موفقیت راه‌اندازی شد!")
        print(f"👤 سازنده: {OWNER_ID}")
        
        # استفاده از run_polling با تنظیمات خاص
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        print(f"❌ خطا: {e}")
