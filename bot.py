import os
import logging
import httpx
import time
import json
import asyncio
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
active_attacks = {}

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
    
    # ========== بخش افزودن اکانت ==========
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
    
    # ========== بخش تنظیمات ==========
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
    
    # ========== بخش حمله ==========
    elif query.data == 'attack':
        keyboard = [
            [InlineKeyboardButton("👥 حمله به گروه", callback_data='attack_group')],
            [InlineKeyboardButton("⏹️ پایان حمله", callback_data='stop_attack')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        await query.edit_message_text(
            "💥 <b>بخش حمله</b>\n\n"
            "◄ لطفاً نوع حمله رو انتخاب کنید:\n\n"
            "🔹 <b>حمله به گروه:</b> جوین شده و در ویس چت پخش میکنه\n"
            "🔹 <b>پایان حمله:</b> متوقف کردن پخش و خروج از گروه\n\n"
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
            "🎵 <b>انتخاب رسانه برای پخش در گروه</b>\n\n"
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
                f"✅ <b>رسانه انتخاب شد:</b> {mp3_files[index].get('name', 'MP3')}\n\n"
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
                f"✅ <b>رسانه انتخاب شد:</b> {mp4_files[index].get('name', 'MP4')}\n\n"
                "◄ لطفاً <b>لینک گروه</b> را وارد کنید.\n"
                "◂ مثال: <code>https://t.me/joinchat/abc123</code>\n"
                "◂ یا: <code>https://t.me/groupusername</code>\n\n"
                "⚠️ <b>توجه:</b> گروه باید ویس چت فعال داشته باشه!\n\n"
                "⫸ برای لغو: /cancel",
                parse_mode='HTML'
            )
    
    elif query.data == 'stop_attack':
        await query.edit_message_text(
            "⏹️ <b>پایان حمله</b>\n\n"
            "◄ در حال متوقف کردن تمام حمله‌ها و خروج از گروه‌ها...",
            parse_mode='HTML'
        )
        
        await stop_all_attacks(update, context)
    
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

async def stop_all_attacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """متوقف کردن تمام حمله‌ها و خروج از گروه‌ها"""
    try:
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
                
                # خروج از همه گروه‌ها
                async for dialog in app.get_dialogs():
                    if dialog.chat.type in ["group", "supergroup"]:
                        try:
                            await app.leave_chat(dialog.chat.id)
                        except:
                            pass
                
                await app.disconnect()
            except:
                pass
        
        await update.message.reply_text(
            "✅ <b>حمله با موفقیت متوقف شد!</b>\n\n"
            "◄ تمام اکانت‌ها از گروه‌ها خارج شدند.",
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در توقف حمله: {str(e)}")

async def join_voice_chat_and_play(app, chat_id, media_path, is_mp3=True):
    """وارد شدن به ویس چت و پخش رسانه"""
    try:
        from pytgcalls import PyTgCalls
        from pytgcalls.types import AudioQuality, VideoQuality
        from pytgcalls.types.input_stream import AudioStream, VideoStream, InputAudioStream, InputVideoStream
        
        call = PyTgCalls(app)
        await call.start()
        
        if is_mp3:
            # پخش MP3
            await call.join_group_call(
                chat_id,
                AudioStream(
                    InputAudioStream(
                        media_path,
                        audio_parameters=AudioQuality.HIGH
                    )
                )
            )
        else:
            # پخش MP4
            await call.join_group_call(
                chat_id,
                VideoStream(
                    InputVideoStream(
                        media_path,
                        video_parameters=VideoQuality.HIGH
                    )
                )
            )
        
        return True
    except Exception as e:
        print(f"خطا در ورود به ویس چت: {e}")
        return False

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
            # دانلود کامل فایل
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
            # دانلود کامل فایل
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
    
    # ========== حمله به گروه (ورود به ویس چت و پخش) ==========
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'attack_group_link':
        link = update.message.text.strip()
        
        # دریافت رسانه انتخاب شده
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
        media_type = "MP3" if is_mp3 else "MP4"
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
            f"🔄 <b>در حال اجرای حمله به گروه...</b>\n\n"
            f"🔗 لینک: {link}\n"
            f"🎵 رسانه: {media_file.get('name', 'Unknown')}\n"
            f"📊 تعداد اکانت‌ها: {len(accounts)}\n\n"
            "⏳ لطفاً صبر کنید...",
            parse_mode='HTML'
        )
        
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
                
                # جوین شدن در گروه
                try:
                    chat = await app.join_chat(link)
                    chat_id = chat.id
                except:
                    # اگر لینک خصوصی بود
                    chat = await app.get_chat(link)
                    chat_id = chat.id
                    await app.join_chat(chat_id)
                
                # وارد شدن به ویس چت و پخش رسانه (با مدیریت خطا)
                try:
                    from pytgcalls import PyTgCalls
                    from pytgcalls.types import AudioQuality
                    from pytgcalls.types.input_stream import AudioStream, InputAudioStream
                    
                    call = PyTgCalls(app)
                    await call.start()
                    
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
                    else:
                        from pytgcalls.types import VideoQuality
                        from pytgcalls.types.input_stream import VideoStream, InputVideoStream
                        await call.join_group_call(
                            chat_id,
                            VideoStream(
                                InputVideoStream(
                                    media_path,
                                    video_parameters=VideoQuality.HIGH
                                )
                            )
                        )
                    
                    await call.stop()
                    success_count += 1
                except Exception as e:
                    print(f"خطا در پخش: {e}")
                    fail_count += 1
                
                await app.disconnect()
            except Exception as e:
                fail_count += 1
                print(f"خطا در اکانت {acc.get('phone')}: {e}")
        
        await update.message.reply_text(
            f"✅ <b>عملیات حمله به گروه کامل شد!</b>\n\n"
            f"🔗 <b>لینک:</b> {link}\n"
            f"🎵 <b>رسانه:</b> {media_file.get('name', 'Unknown')}\n"
            f"✅ <b>موفق:</b> {success_count} اکانت\n"
            f"❌ <b>ناموفق:</b> {fail_count} اکانت\n"
            f"📊 <b>مجموع:</b> {len(accounts)} اکانت\n\n"
            "🎵 <b>رسانه در ویس چت پخش شد!</b>",
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
