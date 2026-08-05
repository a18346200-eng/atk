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
accounts = []
mp3_files = []
mp4_files = []

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
🔹 <b>حمله:</b> برای جوین شدن در گروه و پخش در ویس چت

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
        text = OWNER_START_TEXT + f"\n📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}"
        await update.message.reply_text(
            text,
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
        user_sessions[user_id] = {'step': 'phone', 'api_id': API_ID, 'api_hash': API_HASH}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
            "📱 <b>مرحله ۱: وارد کردن شماره تلفن</b>\n\n"
            "◄ لطفاً <b>شماره تلفن</b> اکانت تلگرام خود را وارد کنید.\n"
            "◂ مثال: <code>+989123456789</code>\n\n"
            f"🔑 API_ID: <code>{API_ID}</code>\n"
            f"🔑 API_HASH: <code>{API_HASH}</code>\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🎵 افزودن MP3", callback_data='add_mp3')],
            [InlineKeyboardButton("🎬 افزودن MP4", callback_data='add_mp4')],
            [InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data='list_accounts')],
            [InlineKeyboardButton("📋 لیست MP3", callback_data='list_mp3')],
            [InlineKeyboardButton("📋 لیست MP4", callback_data='list_mp4')],
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
                "📋 <b>لیست اکانت‌ها</b>\n\n❌ هنوز هیچ اکانتی اضافه نشده!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "📋 <b>لیست اکانت‌های اضافه شده:</b>\n\n"
            for i, acc in enumerate(accounts, 1):
                text += f"{i}. 📱 {acc.get('phone', 'نامشخص')}\n"
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
    
    elif query.data == 'list_mp3':
        if not mp3_files:
            await query.edit_message_text(
                "📋 <b>لیست MP3</b>\n\n❌ هیچ MP3 ای اضافه نشده!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "🎵 <b>لیست MP3های اضافه شده:</b>\n\n"
            for i, mp3 in enumerate(mp3_files, 1):
                text += f"{i}. 🎵 {mp3.get('name', 'نامشخص')}\n"
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
    
    elif query.data == 'list_mp4':
        if not mp4_files:
            await query.edit_message_text(
                "📋 <b>لیست MP4</b>\n\n❌ هیچ MP4 ای اضافه نشده!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "🎬 <b>لیست MP4های اضافه شده:</b>\n\n"
            for i, mp4 in enumerate(mp4_files, 1):
                text += f"{i}. 🎬 {mp4.get('name', 'نامشخص')}\n"
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
    
    elif query.data == 'add_mp3':
        user_sessions[user_id] = {'step': 'mp3'}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]
        await query.edit_message_text(
            "🎵 <b>افزودن MP3</b>\n\n"
            "◄ لطفاً فایل <b>MP3</b> خود را ارسال کنید.\n"
            "◂ ربات فایل را کامل ذخیره کرده و برای پخش استفاده خواهد کرد.\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'add_mp4':
        user_sessions[user_id] = {'step': 'mp4'}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]
        await query.edit_message_text(
            "🎬 <b>افزودن MP4</b>\n\n"
            "◄ لطفاً فایل <b>MP4</b> خود را ارسال کنید.\n"
            "◂ ربات فایل را کامل ذخیره کرده و برای پخش استفاده خواهد کرد.\n\n"
            "⫸ برای لغو: /cancel",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'attack':
        keyboard = [
            [InlineKeyboardButton("👥 پخش در ویس چت گروه", callback_data='attack_group')],
            [InlineKeyboardButton("⏹️ توقف پخش", callback_data='stop_playback')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        await query.edit_message_text(
            "💥 <b>بخش پخش در ویس چت</b>\n\n"
            "◄ لطفاً عملیات مورد نظر رو انتخاب کنید:\n\n"
            "🔹 <b>پخش در ویس چت:</b> جوین شده و در ویس چت پخش میکنه\n"
            "🔹 <b>توقف پخش:</b> متوقف کردن پخش در همه گروه‌ها\n\n"
            f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n"
            f"🎵 <b>MP3:</b> {len(mp3_files)} | 🎬 <b>MP4:</b> {len(mp4_files)}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'attack_group':
        if len(accounts) == 0:
            await query.edit_message_text(
                "❌ <b>هیچ اکانتی وجود ندارد!</b>\n\n"
                "◄ لطفاً ابتدا از بخش <b>افزودن اکانت</b> یک اکانت اضافه کنید.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
            )
            return
        
        if len(mp3_files) == 0 and len(mp4_files) == 0:
            await query.edit_message_text(
                "❌ <b>هیچ فایل رسانه‌ای وجود ندارد!</b>\n\n"
                "◄ لطفاً ابتدا از بخش <b>تنظیمات</b> فایل MP3 یا MP4 اضافه کنید.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
            )
            return
        
        keyboard = []
        for i, mp3 in enumerate(mp3_files, 1):
            keyboard.append([InlineKeyboardButton(f"🎵 {mp3.get('name', f'MP3 {i}')}", callback_data=f'play_mp3_{i-1}')])
        for i, mp4 in enumerate(mp4_files, 1):
            keyboard.append([InlineKeyboardButton(f"🎬 {mp4.get('name', f'MP4 {i}')}", callback_data=f'play_mp4_{i-1}')])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='attack')])
        
        user_sessions[user_id] = {'step': 'attack_group_select'}
        await query.edit_message_text(
            "🎵 <b>انتخاب رسانه برای پخش در ویس چت</b>\n\n"
            "◄ لطفاً یکی از رسانه‌های زیر رو انتخاب کنید:\n\n"
            f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith('play_mp3_'):
        index = int(query.data.split('_')[2])
        if index < len(mp3_files):
            user_sessions[user_id]['selected_mp3'] = index
            user_sessions[user_id]['step'] = 'attack_group_link'
            
            await query.edit_message_text(
                f"✅ <b>MP3 انتخاب شد:</b> {mp3_files[index].get('name', 'MP3')}\n\n"
                "◄ لطفاً <b>لینک گروه</b> را وارد کنید.\n"
                "◂ مثال: <code>https://t.me/joinchat/abc123</code>\n"
                "◂ یا: <code>https://t.me/groupusername</code>\n\n"
                "⚠️ <b>توجه:</b> گروه باید ویس چت فعال داشته باشه!\n\n"
                "⫸ برای لغو: /cancel",
                parse_mode='HTML'
            )
    
    elif query.data.startswith('play_mp4_'):
        index = int(query.data.split('_')[2])
        if index < len(mp4_files):
            user_sessions[user_id]['selected_mp4'] = index
            user_sessions[user_id]['step'] = 'attack_group_link'
            
            await query.edit_message_text(
                f"✅ <b>MP4 انتخاب شد:</b> {mp4_files[index].get('name', 'MP4')}\n\n"
                "◄ لطفاً <b>لینک گروه</b> را وارد کنید.\n"
                "◂ مثال: <code>https://t.me/joinchat/abc123</code>\n"
                "◂ یا: <code>https://t.me/groupusername</code>\n\n"
                "⚠️ <b>توجه:</b> گروه باید ویس چت فعال داشته باشه!\n\n"
                "⫸ برای لغو: /cancel",
                parse_mode='HTML'
            )
    
    elif query.data == 'stop_playback':
        await query.edit_message_text(
            "⏹️ <b>در حال توقف پخش...</b>\n\n"
            "◄ لطفاً صبر کنید...",
            parse_mode='HTML'
        )
        
        await stop_all_playbacks(update, context)
    
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        text = OWNER_START_TEXT + f"\n📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}"
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def stop_all_playbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """متوقف کردن پخش در همه گروه‌ها"""
    try:
        from pyrogram import Client
        from py_tgcalls import PyTgCalls
        
        stopped_count = 0
        for acc in accounts:
            try:
                app = Client(
                    f"stop_session_{acc['id']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=acc['session']
                )
                await app.connect()
                
                call = PyTgCalls(app)
                await call.start()
                
                async for dialog in app.get_dialogs():
                    if dialog.chat.type in ["group", "supergroup"]:
                        try:
                            await call.leave_group_call(dialog.chat.id)
                            stopped_count += 1
                        except:
                            pass
                
                await call.stop()
                await app.disconnect()
            except:
                pass
        
        await update.message.reply_text(
            f"✅ <b>پخش در {stopped_count} گروه متوقف شد!</b>\n\n"
            "◄ تمام اکانت‌ها از ویس چت خارج شدند.",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در توقف پخش: {str(e)}")

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
            
            user_sessions[user_id]['code_sent_time'] = time.time()
            
            await update.message.reply_text(
                f"📨 <b>کد تایید ارسال شد!</b>\n\n"
                f"◄ کد ۵ رقمی به شماره <code>{text}</code> ارسال شد.\n"
                f"◂ لطفاً کد دریافتی را وارد کنید.\n"
                f"⚠️ <b>توجه:</b> کد فقط ۵ دقیقه اعتبار داره!\n\n"
                f"⫸ برای لغو: /cancel",
                parse_mode='HTML'
            )
        except Exception as e:
            error_msg = str(e)
            if "FLOOD_WAIT" in error_msg:
                await update.message.reply_text(
                    f"❌ <b>زیاد درخواست دادی!</b>\n\n"
                    f"◄ خطا: <code>{error_msg}</code>\n"
                    "◄ لطفاً چند دقیقه صبر کن و دوباره تلاش کن.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>خطا در ارسال کد!</b>\n\n"
                    f"◄ خطا: <code>{error_msg}</code>\n\n"
                    "◄ لطفاً شماره و API را بررسی کن.\n"
                    "⫸ برای شروع مجدد /start را بزن.",
                    parse_mode='HTML'
                )
            if user_id in user_sessions:
                del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'code':
        code = update.message.text.strip()
        if not code.isdigit() or len(code) != 5:
            await update.message.reply_text("❌ کد باید ۵ رقم باشد!")
            return
        
        code_sent_time = user_sessions[user_id].get('code_sent_time', 0)
        if time.time() - code_sent_time > 300:
            await update.message.reply_text(
                "❌ <b>کد منقضی شده!</b>\n\n"
                "◄ زمان ۵ دقیقه تمام شده.\n"
                "◄ لطفاً دوباره از اول شروع کن.\n"
                "⫸ /start را بزن و دوباره تلاش کن.",
                parse_mode='HTML'
            )
            if user_id in user_sessions:
                if 'client' in user_sessions[user_id]:
                    try:
                        await user_sessions[user_id]['client'].disconnect()
                    except:
                        pass
                del user_sessions[user_id]
            return
        
        try:
            phone = user_sessions[user_id]['phone']
            phone_code_hash = user_sessions[user_id]['phone_code_hash']
            app = user_sessions[user_id]['client']
            
            # امتحان ورود با کد
            try:
                await app.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=code)
            except Exception as sign_in_error:
                error_msg = str(sign_in_error)
                # اگر پسورد دو مرحله‌ای نیاز بود
                if "SESSION_PASSWORD_NEEDED" in error_msg:
                    user_sessions[user_id]['step'] = 'password'
                    await update.message.reply_text(
                        "🔐 <b>مرحله ۴: وارد کردن پسورد دو مرحله‌ای</b>\n\n"
                        "◄ این اکانت دارای <b>تایید دو مرحله‌ای</b> است.\n"
                        "◂ لطفاً <b>پسورد</b> اکانت تلگرام خود را وارد کنید.\n\n"
                        "⫸ برای لغو: /cancel",
                        parse_mode='HTML'
                    )
                    return
                else:
                    raise sign_in_error
            
            # اگر ورود موفق بود
            session_string = await app.export_session_string()
            
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
                f"📊 <b>تعداد کل اکانت‌ها:</b> {len(accounts)}",
                parse_mode='HTML'
            )
            
            await app.disconnect()
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except Exception as e:
            error_msg = str(e)
            if "PHONE_CODE_EXPIRED" in error_msg:
                await update.message.reply_text(
                    f"❌ <b>کد منقضی شده!</b>\n\n"
                    "◄ کد وارد شده معتبر نیست.\n"
                    "◄ لطفاً دوباره از اول شروع کن.\n"
                    "⫸ /start را بزن و دوباره تلاش کن.",
                    parse_mode='HTML'
                )
            elif "FLOOD_WAIT" in error_msg:
                await update.message.reply_text(
                    f"❌ <b>زیاد درخواست دادی!</b>\n\n"
                    f"◄ خطا: <code>{error_msg}</code>\n"
                    "◄ لطفاً چند دقیقه صبر کن و دوباره تلاش کن.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>خطا در ساخت سشن!</b>\n\n"
                    f"◄ خطا: <code>{error_msg}</code>\n"
                    "⫸ /start را بزن و دوباره تلاش کن.",
                    parse_mode='HTML'
                )
            if user_id in user_sessions:
                if 'client' in user_sessions[user_id]:
                    try:
                        await user_sessions[user_id]['client'].disconnect()
                    except:
                        pass
                del user_sessions[user_id]
        return
    
    # ========== مرحله ۴: دریافت پسورد دو مرحله‌ای ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'password':
        password = update.message.text.strip()
        
        try:
            phone = user_sessions[user_id]['phone']
            app = user_sessions[user_id]['client']
            
            # ورود با پسورد
            await app.check_password(password)
            
            # ساخت سشن
            session_string = await app.export_session_string()
            
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
                f"📊 <b>تعداد کل اکانت‌ها:</b> {len(accounts)}",
                parse_mode='HTML'
            )
            
            await app.disconnect()
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except Exception as e:
            error_msg = str(e)
            if "PASSWORD_HASH_INVALID" in error_msg:
                await update.message.reply_text(
                    "❌ <b>پسورد اشتباه است!</b>\n\n"
                    "◄ لطفاً پسورد صحیح را وارد کنید.\n"
                    "⫸ برای لغو: /cancel",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>خطا در تایید پسورد!</b>\n\n"
                    f"◄ خطا: <code>{error_msg}</code>\n"
                    "⫸ /start را بزن و دوباره تلاش کن.",
                    parse_mode='HTML'
                )
                if user_id in user_sessions:
                    if 'client' in user_sessions[user_id]:
                        try:
                            await user_sessions[user_id]['client'].disconnect()
                        except:
                            pass
                    del user_sessions[user_id]
        return
    
    # ========== افزودن MP3 ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'mp3':
        if update.message.audio:
            file = update.message.audio
            file_obj = await context.bot.get_file(file.file_id)
            file_path = f"mp3_{int(time.time())}_{file.file_name or 'unknown.mp3'}"
            await file_obj.download_to_drive(file_path)
            
            file_info = {
                'name': file.file_name or 'Unknown',
                'file_id': file.file_id,
                'duration': file.duration,
                'size': file.file_size,
                'path': file_path
            }
            mp3_files.append(file_info)
            save_data()
            await update.message.reply_text(
                f"✅ <b>MP3 با موفقیت اضافه شد!</b>\n\n"
                f"🎵 <b>نام:</b> {file_info['name']}\n"
                f"⏱️ <b>مدت:</b> {file_info['duration']} ثانیه\n"
                f"💾 <b>حجم:</b> {file_info['size']} بایت\n"
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
            file_obj = await context.bot.get_file(file.file_id)
            file_path = f"mp4_{int(time.time())}_{file.file_name or 'unknown.mp4'}"
            await file_obj.download_to_drive(file_path)
            
            file_info = {
                'name': file.file_name or 'Unknown',
                'file_id': file.file_id,
                'duration': file.duration,
                'size': file.file_size,
                'width': file.width,
                'height': file.height,
                'path': file_path
            }
            mp4_files.append(file_info)
            save_data()
            await update.message.reply_text(
                f"✅ <b>MP4 با موفقیت اضافه شد!</b>\n\n"
                f"🎬 <b>نام:</b> {file_info['name']}\n"
                f"⏱️ <b>مدت:</b> {file_info['duration']} ثانیه\n"
                f"💾 <b>حجم:</b> {file_info['size']} بایت\n"
                f"📊 <b>تعداد کل MP4:</b> {len(mp4_files)}",
                parse_mode='HTML'
            )
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ لطفاً یک فایل MP4 ارسال کنید!")
        return
    
    # ========== پخش در ویس چت گروه ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'attack_group_link':
        link = update.message.text.strip()
        
        media_index = user_sessions[user_id].get('selected_mp3')
        is_mp3 = True
        if media_index is None:
            media_index = user_sessions[user_id].get('selected_mp4')
            is_mp3 = False
        
        if media_index is None:
            await update.message.reply_text("❌ رسانه‌ای انتخاب نشده! دوباره تلاش کنید.")
            del user_sessions[user_id]
            return
        
        media_file = mp3_files[media_index] if is_mp3 else mp4_files[media_index]
        media_path = media_file.get('path')
        
        if not media_path or not os.path.exists(media_path):
            await update.message.reply_text(
                f"❌ <b>فایل رسانه پیدا نشد!</b>\n\n"
                f"◄ مسیر فایل: {media_path}\n"
                "◄ لطفاً دوباره رسانه رو اضافه کنید.",
                parse_mode='HTML'
            )
            del user_sessions[user_id]
            return
        
        await update.message.reply_text(
            f"🔄 <b>در حال پخش در ویس چت گروه...</b>\n\n"
            f"🔗 لینک: {link}\n"
            f"🎵 رسانه: {media_file.get('name', 'Unknown')}\n"
            f"📊 تعداد اکانت‌ها: {len(accounts)}\n\n"
            "⏳ لطفاً صبر کنید...",
            parse_mode='HTML'
        )
        
        success_count = 0
        fail_count = 0
        error_details = []
        
        for acc in accounts:
            try:
                from pyrogram import Client
                from py_tgcalls import PyTgCalls
                from py_tgcalls.types import AudioQuality, VideoQuality
                from py_tgcalls.types.input_stream import AudioStream, VideoStream, InputAudioStream, InputVideoStream
                
                print(f"🔄 شروع با اکانت: {acc.get('phone')}")
                
                app = Client(
                    f"play_session_{acc['id']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=acc['session']
                )
                await app.connect()
                print(f"✅ اکانت {acc.get('phone')} متصل شد")
                
                # ===== جوین شدن در گروه =====
                try:
                    chat = await app.join_chat(link)
                    chat_id = chat.id
                    print(f"✅ جوین شد با لینک: {chat_id}")
                except Exception as e1:
                    print(f"⚠️ خطا در جوین با لینک: {e1}")
                    try:
                        if 'joinchat/' in link:
                            invite_code = link.split('joinchat/')[-1]
                        elif '+' in link:
                            invite_code = link.split('+')[-1]
                        else:
                            invite_code = link.replace('https://t.me/', '').replace('@', '')
                        
                        if invite_code and not invite_code.startswith('+'):
                            chat = await app.join_chat(invite_code)
                            chat_id = chat.id
                        else:
                            chat = await app.get_chat(link)
                            chat_id = chat.id
                            await app.join_chat(chat_id)
                        print(f"✅ جوین شد با روش جایگزین: {chat_id}")
                    except Exception as e2:
                        print(f"❌ خطا در جوین: {e2}")
                        error_details.append(f"اکانت {acc.get('phone')}: جوین نشد - {e2}")
                        fail_count += 1
                        await app.disconnect()
                        continue
                
                # ===== پخش در ویس چت =====
                try:
                    call = PyTgCalls(app)
                    await call.start()
                    print(f"✅ تماس شروع شد برای اکانت {acc.get('phone')}")
                    
                    if is_mp3:
                        await call.join_group_call(
                            chat_id,
                            AudioStream(
                                InputAudioStream(
                                    media_path,
                                    audio_parameters=AudioQuality.HIGH
                                )
                            )
                        )
                        print(f"✅ MP3 پخش شد در اکانت {acc.get('phone')}")
                    else:
                        await call.join_group_call(
                            chat_id,
                            VideoStream(
                                InputVideoStream(
                                    media_path,
                                    video_parameters=VideoQuality.HIGH
                                )
                            )
                        )
                        print(f"✅ MP4 پخش شد در اکانت {acc.get('phone')}")
                    
                    success_count += 1
                    
                except Exception as e3:
                    print(f"❌ خطا در پخش: {e3}")
                    error_details.append(f"اکانت {acc.get('phone')}: پخش نشد - {e3}")
                    fail_count += 1
                    await app.disconnect()
                
            except Exception as e:
                print(f"❌ خطای کلی: {e}")
                error_details.append(f"اکانت {acc.get('phone')}: {e}")
                fail_count += 1
        
        result_text = f"✅ <b>عملیات پخش در ویس چت کامل شد!</b>\n\n"
        result_text += f"🔗 <b>لینک:</b> {link}\n"
        result_text += f"🎵 <b>رسانه:</b> {media_file.get('name', 'Unknown')}\n"
        result_text += f"✅ <b>موفق:</b> {success_count} اکانت\n"
        result_text += f"❌ <b>ناموفق:</b> {fail_count} اکانت\n"
        result_text += f"📊 <b>مجموع:</b> {len(accounts)} اکانت\n"
        
        if error_details:
            result_text += f"\n⚠️ <b>خطاها:</b>\n"
            for err in error_details[:3]:
                result_text += f"◄ {err[:100]}...\n"
        
        await update.message.reply_text(
            result_text,
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
        print("🔄 در حال پاک کردن Webhook...")
        try:
            response = httpx.post(
                f"https://api.telegram.org/bot{TOKEN}/deleteWebhook",
                json={"drop_pending_updates": True},
                timeout=30
            )
            if response.json().get('ok'):
                print("✅ Webhook پاک شد")
        except Exception as e:
            print(f"⚠️ خطا: {e}")
        
        time.sleep(2)
        
        print("🚀 ربات در حال راه‌اندازی...")
        print(f"🔑 API_ID: {API_ID}")
        print(f"📊 تعداد اکانت‌ها: {len(accounts)}")
        print(f"🎵 تعداد MP3: {len(mp3_files)}")
        print(f"🎬 تعداد MP4: {len(mp4_files)}")
        
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
