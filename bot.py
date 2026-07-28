import os
import logging
import httpx
import time
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8576876988:AAGBLHEz9IAQa9NwgG6L8tWZnUQjUifxu10"
OWNER_ID = 7803165903
API_ID = 29811798
API_HASH = "ef5847a43a978d6883b97b0caeb81736"

user_sessions = {}
accounts = []  # لیست اکانت‌های ساخته شده
mp3_files = []  # لیست فایل‌های MP3
mp4_files = []  # لیست فایل‌های MP4

# ذخیره و بارگذاری داده‌ها
DATA_FILE = "data.json"

def load_data():
    global accounts, mp3_files, mp4_files
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                accounts = data.get('accounts', [])
                mp3_files = data.get('mp3_files', [])
                mp4_files = data.get('mp4_files', [])
    except:
        pass

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'accounts': accounts,
                'mp3_files': mp3_files,
                'mp4_files': mp4_files
            }, f)
    except:
        pass

load_data()

OWNER_START_TEXT = """
🌟 <b>سازنده ربات عزیز به ربات ZX خوش آمدید!</b> 🌹

⫸ لطفاً از منوی زیر کار خودتون رو انتخاب کنید:

🔹 <b>افزودن اکانت:</b> برای ساخت سشن تلگرام
🔹 <b>تنظیمات:</b> مدیریت فایل‌های MP3 و MP4
🔹 <b>حمله:</b> برای جوین شدن در گروه یا کانال

⚡ <b>وضعیت ربات:</b> فعال ✅
📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}
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
            OWNER_START_TEXT.format(len(accounts)),
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
    
    # ========== بخش افزودن اکانت ==========
    if query.data == 'add_account':
        user_sessions[user_id] = {'step': 'phone', 'api_id': API_ID, 'api_hash': API_HASH}
        await query.edit_message_text(
            "📱 <b>مرحله ۱: وارد کردن شماره تلفن</b>\n\n"
            "◄ لطفاً <b>شماره تلفن</b> اکانت تلگرام خود را وارد کنید.\n"
            "◂ مثال: <code>+989123456789</code>\n\n"
            f"🔑 API_ID: <code>{API_ID}</code>\n"
            f"🔑 API_HASH: <code>{API_HASH}</code>\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    
    # ========== بخش تنظیمات ==========
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🎵 افزودن MP3", callback_data='add_mp3')],
            [InlineKeyboardButton("🎬 افزودن MP4", callback_data='add_mp4')],
            [InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data='list_accounts')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        
        text = f"⚙️ <b>تنظیمات ربات</b>\n\n"
        text += f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n"
        text += f"🎵 <b>تعداد MP3:</b> {len(mp3_files)}\n"
        text += f"🎬 <b>تعداد MP4:</b> {len(mp4_files)}\n\n"
        text += "📍 لطفاً یکی از گزینه‌ها رو انتخاب کنید:"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'list_accounts':
        if not accounts:
            await query.edit_message_text(
                "📋 <b>لیست اکانت‌ها</b>\n\n"
                "❌ هنوز هیچ اکانتی اضافه نشده!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "📋 <b>لیست اکانت‌های اضافه شده:</b>\n\n"
            for i, acc in enumerate(accounts, 1):
                text += f"{i}. 📱 {acc.get('phone', 'نامشخص')}\n"
                text += f"   🆔 ID: {acc.get('id', 'نامشخص')}\n\n"
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
    
    elif query.data == 'add_mp3':
        user_sessions[user_id] = {'step': 'mp3'}
        await query.edit_message_text(
            "🎵 <b>افزودن MP3</b>\n\n"
            "◄ لطفاً فایل <b>MP3</b> خود را ارسال کنید.\n"
            "◂ ربات فایل را ذخیره کرده و به سشن‌ها ارسال خواهد کرد.\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    
    elif query.data == 'add_mp4':
        user_sessions[user_id] = {'step': 'mp4'}
        await query.edit_message_text(
            "🎬 <b>افزودن MP4</b>\n\n"
            "◄ لطفاً فایل <b>MP4</b> خود را ارسال کنید.\n"
            "◂ ربات فایل را ذخیره کرده و به سشن‌ها ارسال خواهد کرد.\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    
    # ========== بخش حمله ==========
    elif query.data == 'attack':
        keyboard = [
            [InlineKeyboardButton("👥 حمله به گروه", callback_data='attack_group')],
            [InlineKeyboardButton("📢 حمله به کانال", callback_data='attack_channel')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        await query.edit_message_text(
            "💥 <b>بخش حمله</b>\n\n"
            "◄ لطفاً نوع حمله رو انتخاب کنید:\n\n"
            "🔹 <b>حمله به گروه:</b> سشن وارد گروه میشه\n"
            "🔹 <b>حمله به کانال:</b> سشن وارد کانال میشه\n\n"
            "⚠️ <b>توجه:</b> فقط اکانت‌های اضافه شده قابلیت جوین شدن دارن.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'attack_group':
        user_sessions[user_id] = {'step': 'attack_group'}
        await query.edit_message_text(
            "👥 <b>حمله به گروه</b>\n\n"
            "◄ لطفاً <b>لینک گروه</b> را وارد کنید.\n"
            "◂ چه لینک عمومی و چه لینک خصوصی فرقی نداره.\n\n"
            "◂ مثال: <code>https://t.me/joinchat/abc123</code>\n"
            "◂ یا: <code>https://t.me/groupusername</code>\n\n"
            f"📊 <b>تعداد اکانت‌های موجود:</b> {len(accounts)}\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    
    elif query.data == 'attack_channel':
        user_sessions[user_id] = {'step': 'attack_channel'}
        await query.edit_message_text(
            "📢 <b>حمله به کانال</b>\n\n"
            "◄ لطفاً <b>لینک کانال</b> را وارد کنید.\n"
            "◂ چه لینک عمومی و چه لینک خصوصی فرقی نداره.\n\n"
            "◂ مثال: <code>https://t.me/joinchat/abc123</code>\n"
            "◂ یا: <code>https://t.me/channelusername</code>\n\n"
            f"📊 <b>تعداد اکانت‌های موجود:</b> {len(accounts)}\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML'
        )
    
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        await query.edit_message_text(
            OWNER_START_TEXT.format(len(accounts)),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    # ========== ساخت اکانت ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'phone':
        text = update.message.text.strip()
        if not text.startswith('+') or not text[1:].isdigit():
            await update.message.reply_text("❌ فرمت شماره نامعتبر! مثال: +989123456789")
            return
        
        user_sessions[user_id]['phone'] = text
        user_sessions[user_id]['step'] = 'code'
        
        try:
            from pyrogram import Client
            app = Client(
                f"session_{user_id}",
                api_id=user_sessions[user_id]['api_id'],
                api_hash=user_sessions[user_id]['api_hash'],
                phone_number=text
            )
            await app.connect()
            sent_code = await app.send_code(text)
            user_sessions[user_id]['client'] = app
            user_sessions[user_id]['phone_code_hash'] = sent_code.phone_code_hash
            await update.message.reply_text(f"📨 کد تایید به {text} ارسال شد. کد ۵ رقمی را وارد کنید:")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'code':
        code = update.message.text.strip()
        if not code.isdigit() or len(code) != 5:
            await update.message.reply_text("❌ کد باید ۵ رقم باشد!")
            return
        
        try:
            phone = user_sessions[user_id]['phone']
            phone_code_hash = user_sessions[user_id]['phone_code_hash']
            app = user_sessions[user_id]['client']
            
            await app.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=code)
            session_string = await app.export_session_string()
            
            # ذخیره اطلاعات اکانت
            account_info = {
                'phone': phone,
                'session': session_string,
                'id': len(accounts) + 1
            }
            accounts.append(account_info)
            save_data()
            
            await update.message.reply_text(
                f"✅ <b>سشن ساخته شد!</b>\n\n"
                f"📱 <b>شماره:</b> <code>{phone}</code>\n"
                f"🆔 <b>شناسه:</b> {len(accounts)}\n\n"
                f"🔑 <b>سشن:</b>\n<code>{session_string}</code>\n\n"
                f"📊 <b>تعداد کل اکانت‌ها:</b> {len(accounts)}",
                parse_mode='HTML'
            )
            
            await app.disconnect()
            del user_sessions[user_id]
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ساخت سشن: {str(e)}")
            if user_id in user_sessions:
                del user_sessions[user_id]
        return
    
    # ========== افزودن MP3 ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'mp3':
        if update.message.audio:
            file = update.message.audio
            file_info = {
                'name': file.file_name or 'Unknown',
                'file_id': file.file_id,
                'duration': file.duration,
                'size': file.file_size
            }
            mp3_files.append(file_info)
            save_data()
            await update.message.reply_text(
                f"✅ <b>MP3 با موفقیت اضافه شد!</b>\n\n"
                f"🎵 <b>نام:</b> {file_info['name']}\n"
                f"⏱️ <b>مدت:</b> {file_info['duration']} ثانیه\n"
                f"📊 <b>تعداد کل MP3:</b> {len(mp3_files)}",
                parse_mode='HTML'
            )
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ لطفاً یک فایل MP3 ارسال کنید!")
        return
    
    # ========== افزودن MP4 ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'mp4':
        if update.message.video:
            file = update.message.video
            file_info = {
                'name': file.file_name or 'Unknown',
                'file_id': file.file_id,
                'duration': file.duration,
                'size': file.file_size,
                'width': file.width,
                'height': file.height
            }
            mp4_files.append(file_info)
            save_data()
            await update.message.reply_text(
                f"✅ <b>MP4 با موفقیت اضافه شد!</b>\n\n"
                f"🎬 <b>نام:</b> {file_info['name']}\n"
                f"⏱️ <b>مدت:</b> {file_info['duration']} ثانیه\n"
                f"📊 <b>تعداد کل MP4:</b> {len(mp4_files)}",
                parse_mode='HTML'
            )
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ لطفاً یک فایل MP4 ارسال کنید!")
        return
    
    # ========== حمله به گروه ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'attack_group':
        link = update.message.text.strip()
        
        if not accounts:
            await update.message.reply_text("❌ هیچ اکانتی برای حمله وجود ندارد! ابتدا اکانت اضافه کنید.")
            del user_sessions[user_id]
            return
        
        await update.message.reply_text(
            f"🔄 <b>در حال پردازش...</b>\n\n"
            f"🔗 لینک: {link}\n"
            f"📊 تعداد اکانت‌ها: {len(accounts)}\n\n"
            "⏳ لطفاً صبر کنید...",
            parse_mode='HTML'
        )
        
        # جوین شدن با همه اکانت‌ها
        success_count = 0
        fail_count = 0
        
        for acc in accounts:
            try:
                from pyrogram import Client
                app = Client(
                    f"temp_session_{acc['id']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=acc['session']
                )
                await app.connect()
                await app.join_chat(link)
                await app.disconnect()
                success_count += 1
            except Exception as e:
                fail_count += 1
        
        await update.message.reply_text(
            f"✅ <b>عملیات حمله به گروه کامل شد!</b>\n\n"
            f"🔗 <b>لینک:</b> {link}\n"
            f"✅ <b>موفق:</b> {success_count} اکانت\n"
            f"❌ <b>ناموفق:</b> {fail_count} اکانت\n"
            f"📊 <b>مجموع:</b> {len(accounts)} اکانت",
            parse_mode='HTML'
        )
        
        del user_sessions[user_id]
        return
    
    # ========== حمله به کانال ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'attack_channel':
        link = update.message.text.strip()
        
        if not accounts:
            await update.message.reply_text("❌ هیچ اکانتی برای حمله وجود ندارد! ابتدا اکانت اضافه کنید.")
            del user_sessions[user_id]
            return
        
        await update.message.reply_text(
            f"🔄 <b>در حال پردازش...</b>\n\n"
            f"🔗 لینک: {link}\n"
            f"📊 تعداد اکانت‌ها: {len(accounts)}\n\n"
            "⏳ لطفاً صبر کنید...",
            parse_mode='HTML'
        )
        
        # جوین شدن با همه اکانت‌ها
        success_count = 0
        fail_count = 0
        
        for acc in accounts:
            try:
                from pyrogram import Client
                app = Client(
                    f"temp_session_{acc['id']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=acc['session']
                )
                await app.connect()
                await app.join_chat(link)
                await app.disconnect()
                success_count += 1
            except Exception as e:
                fail_count += 1
        
        await update.message.reply_text(
            f"✅ <b>عملیات حمله به کانال کامل شد!</b>\n\n"
            f"🔗 <b>لینک:</b> {link}\n"
            f"✅ <b>موفق:</b> {success_count} اکانت\n"
            f"❌ <b>ناموفق:</b> {fail_count} اکانت\n"
            f"📊 <b>مجموع:</b> {len(accounts)} اکانت",
            parse_mode='HTML'
        )
        
        del user_sessions[user_id]
        return

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
        print("🚀 ربات در حال راه‌اندازی...")
        print(f"🔑 API_ID: {API_ID}")
        print(f"🔑 API_HASH: {API_HASH}")
        print(f"📊 تعداد اکانت‌ها: {len(accounts)}")
        
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.AUDIO, handle_message))
        application.add_handler(MessageHandler(filters.VIDEO, handle_message))
        
        print(f"✅ ربات با موفقیت راه‌اندازی شد!")
        print(f"👤 سازنده: {OWNER_ID}")
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        print(f"❌ خطا: {e}")
