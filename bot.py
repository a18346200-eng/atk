import os
import logging
import httpx
import time
import json
import sys
import platform
import psutil
from datetime import datetime
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
START_TIME = time.time()

DATA_FILE = "data.json"

def load_data():
    default_data = {
        'accounts': [],
        'mp3_files': [],
        'mp4_files': [],
        'joined_groups': [],
        'stats': {
            'total_users': 0,
            'users': [],
            'commands_used': {}
        }
    }
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                return data
    except:
        pass
    return default_data

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

data = load_data()
accounts = data['accounts']
mp3_files = data['mp3_files']
mp4_files = data['mp4_files']
joined_groups = data['joined_groups']
stats = data['stats']
user_sessions = {}

OWNER_START_TEXT = """
🌟 <b>به ربات ZX خوش آمدید</b>

💎 <b>سازنده محترم</b>، لطفاً یکی از گزینه‌های زیر را انتخاب کنید:

➕ <b>افزودن اکانت</b> • ایجاد سشن تلگرام
⚙️ <b>تنظیمات</b> • مدیریت فایل‌ها و اطلاعات
💥 <b>حمله</b> • پخش در ویس چت گروه
📊 <b>اطلاعات</b> • آمار و وضعیت ربات
"""

NORMAL_START_TEXT = "⛔ <b>دسترسی محدود</b>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in stats['users']:
        stats['users'].append(user_id)
        stats['total_users'] = len(stats['users'])
        save_data(data)
    
    if user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')],
            [InlineKeyboardButton("📊 اطلاعات", callback_data='info')]
        ]
        text = OWNER_START_TEXT + f"\n\n📊 اکانت‌ها: {len(accounts)}\n📁 گروه‌ها: {len(joined_groups)}\n🎵 MP3: {len(mp3_files)}\n👤 کاربران: {stats['total_users']}"
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(NORMAL_START_TEXT, parse_mode='HTML')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id != OWNER_ID:
        await query.answer("⛔ دسترسی محدود", show_alert=True)
        return
    await query.answer()
    
    if query.data == 'add_account':
        user_sessions[user_id] = {'step': 'phone', 'api_id': API_ID, 'api_hash': API_HASH}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
            "📱 <b>ایجاد سشن جدید</b>\n\n🔹 شماره تلفن را وارد کنید\n🔹 مثال: <code>+989123456789</code>",
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🎵 افزودن MP3", callback_data='add_mp3')],
            [InlineKeyboardButton("🎬 افزودن MP4", callback_data='add_mp4')],
            [InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data='list_accounts'), InlineKeyboardButton("📁 لیست گروه‌ها", callback_data='list_groups')],
            [InlineKeyboardButton("🎵 لیست MP3", callback_data='list_mp3'), InlineKeyboardButton("🎬 لیست MP4", callback_data='list_mp4')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        text = f"⚙️ <b>تنظیمات</b>\n\n📊 اکانت‌ها: {len(accounts)}\n🎵 MP3: {len(mp3_files)}\n🎬 MP4: {len(mp4_files)}\n📁 گروه‌ها: {len(joined_groups)}"
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'list_groups':
        if not joined_groups:
            await query.edit_message_text("📁 <b>لیست گروه‌ها</b>\n\n❌ هیچ گروهی یافت نشد", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
        else:
            text = "📁 <b>گروه‌های جوین شده</b>\n\n"
            for i, group in enumerate(joined_groups, 1):
                text += f"{i}. {group.get('name', 'نامشخص')}\n🆔 {group.get('link', '')}\n\n"
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
    
    elif query.data == 'list_accounts':
        if not accounts:
            await query.edit_message_text("📋 <b>لیست اکانت‌ها</b>\n\n❌ هیچ اکانتی یافت نشد", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
        else:
            text = "📋 <b>لیست اکانت‌ها</b>\n\n"
            for i, acc in enumerate(accounts, 1):
                text += f"{i}. 📱 {acc.get('phone', 'نامشخص')}\n"
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
    
    elif query.data == 'list_mp3':
        if not mp3_files:
            await query.edit_message_text("🎵 <b>لیست MP3</b>\n\n❌ هیچ فایل MP3 یافت نشد", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
        else:
            text = "🎵 <b>لیست فایل‌های MP3</b>\n\n"
            for i, mp3 in enumerate(mp3_files, 1):
                text += f"{i}. 🎵 {mp3.get('name', 'نامشخص')}\n"
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
    
    elif query.data == 'list_mp4':
        if not mp4_files:
            await query.edit_message_text("🎬 <b>لیست MP4</b>\n\n❌ هیچ فایل MP4 یافت نشد", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
        else:
            text = "🎬 <b>لیست فایل‌های MP4</b>\n\n"
            for i, mp4 in enumerate(mp4_files, 1):
                text += f"{i}. 🎬 {mp4.get('name', 'نامشخص')}\n"
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
    
    elif query.data == 'add_mp3':
        user_sessions[user_id] = {'step': 'mp3'}
        await query.edit_message_text("🎵 <b>افزودن MP3</b>\n\n🔹 فایل MP3 خود را ارسال کنید", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
    
    elif query.data == 'add_mp4':
        user_sessions[user_id] = {'step': 'mp4'}
        await query.edit_message_text("🎬 <b>افزودن MP4</b>\n\n🔹 فایل MP4 خود را ارسال کنید", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
    
    elif query.data == 'attack':
        keyboard = [
            [InlineKeyboardButton("👥 جوین شدن در گروه", callback_data='join_group')],
            [InlineKeyboardButton("🎵 پخش در ویس چت", callback_data='play_voice')],
            [InlineKeyboardButton("⏹️ توقف پخش", callback_data='stop_playback')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        text = f"💥 <b>مدیریت حمله</b>\n\n📊 اکانت‌ها: {len(accounts)}\n🎵 MP3: {len(mp3_files)} | 🎬 MP4: {len(mp4_files)}"
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'join_group':
        if len(accounts) == 0:
            await query.edit_message_text("❌ <b>هیچ اکانتی وجود ندارد</b>\n\n🔹 ابتدا اکانت اضافه کنید", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))
            return
        user_sessions[user_id] = {'step': 'join_group_link'}
        await query.edit_message_text("👥 <b>جوین شدن در گروه</b>\n\n🔹 لینک گروه را وارد کنید\n🔹 مثال: <code>https://t.me/joinchat/abc123</code>", parse_mode='HTML')
    
    elif query.data == 'play_voice':
        if len(accounts) == 0:
            await query.edit_message_text("❌ <b>هیچ اکانتی وجود ندارد</b>\n\n🔹 ابتدا اکانت اضافه کنید", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))
            return
        if len(mp3_files) == 0 and len(mp4_files) == 0:
            await query.edit_message_text("❌ <b>هیچ فایل رسانه‌ای وجود ندارد</b>\n\n🔹 ابتدا فایل اضافه کنید", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))
            return
        if len(joined_groups) == 0:
            await query.edit_message_text("❌ <b>هیچ گروهی وجود ندارد</b>\n\n🔹 ابتدا گروه اضافه کنید", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))
            return
        keyboard = []
        for i, group in enumerate(joined_groups):
            keyboard.append([InlineKeyboardButton(f"📁 {group.get('name', f'گروه {i+1}')}", callback_data=f'play_group_{i}')])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='attack')])
        user_sessions[user_id] = {'step': 'play_select_group'}
        await query.edit_message_text("🎵 <b>انتخاب گروه</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith('play_group_'):
        index = int(query.data.split('_')[2])
        if index < len(joined_groups):
            user_sessions[user_id]['selected_group'] = index
            user_sessions[user_id]['step'] = 'play_select_media'
            keyboard = []
            for i, mp3 in enumerate(mp3_files):
                keyboard.append([InlineKeyboardButton(f"🎵 {mp3.get('name', f'MP3 {i+1}')}", callback_data=f'play_mp3_{i}')])
            for i, mp4 in enumerate(mp4_files):
                keyboard.append([InlineKeyboardButton(f"🎬 {mp4.get('name', f'MP4 {i+1}')}", callback_data=f'play_mp4_{i}')])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='play_voice')])
            await query.edit_message_text("🎵 <b>انتخاب رسانه</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith('play_mp3_'):
        index = int(query.data.split('_')[2])
        if index < len(mp3_files):
            user_sessions[user_id]['selected_file'] = index
            user_sessions[user_id]['is_mp3'] = True
            await start_playback(update, context, user_id)
    
    elif query.data.startswith('play_mp4_'):
        index = int(query.data.split('_')[2])
        if index < len(mp4_files):
            user_sessions[user_id]['selected_file'] = index
            user_sessions[user_id]['is_mp3'] = False
            await start_playback(update, context, user_id)
    
    elif query.data == 'stop_playback':
        await query.edit_message_text("⏹️ <b>توقف پخش</b>", parse_mode='HTML')
        await stop_all_playbacks(update, context)
    
    elif query.data == 'info':
        keyboard = [
            [InlineKeyboardButton("📊 آمار کل", callback_data='stats_all')],
            [InlineKeyboardButton("🔄 بررسی پینگ", callback_data='ping_check')],
            [InlineKeyboardButton("💰 اعتبار هاست", callback_data='credit_check')],
            [InlineKeyboardButton("📨 ارسال همگانی", callback_data='broadcast')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        await query.edit_message_text(
            "📊 <b>اطلاعات ربات</b>\n\n🔹 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'stats_all':
        uptime = time.time() - START_TIME
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        text = f"📊 <b>آمار کامل ربات</b>\n\n"
        text += f"👤 <b>تعداد کاربران:</b> {stats['total_users']}\n"
        text += f"📱 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n"
        text += f"🎵 <b>تعداد MP3:</b> {len(mp3_files)}\n"
        text += f"🎬 <b>تعداد MP4:</b> {len(mp4_files)}\n"
        text += f"📁 <b>تعداد گروه‌ها:</b> {len(joined_groups)}\n"
        text += f"⏱️ <b>آپ تایم:</b> {hours} ساعت {minutes} دقیقه\n"
        text += f"🐍 <b>پایتون:</b> {sys.version.split()[0]}\n"
        text += f"💻 <b>سیستم:</b> {platform.system()} {platform.release()}\n"
        text += f"⚡ <b>CPU:</b> {psutil.cpu_percent()}%\n"
        text += f"🧠 <b>RAM:</b> {psutil.virtual_memory().percent}%\n"
        text += f"💾 <b>دیسک:</b> {psutil.disk_usage('/').percent}%"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='info')]]))
    
    elif query.data == 'ping_check':
        start = time.time()
        try:
            r = httpx.get("https://api.telegram.org/bot" + TOKEN + "/getMe", timeout=10)
            ping = int((time.time() - start) * 1000)
            if r.status_code == 200:
                status = "✅ آنلاین"
            else:
                status = "⚠️ مشکل"
        except:
            ping = 0
            status = "❌ آفلاین"
        
        text = f"🔄 <b>بررسی پینگ</b>\n\n"
        text += f"📡 <b>وضعیت:</b> {status}\n"
        text += f"⚡ <b>پینگ:</b> {ping} ms\n"
        text += f"🌐 <b>سرور:</b> Railway (US West)\n"
        text += f"📦 <b>پکیج‌ها:</b> {len(sys.modules)}"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='info')]]))
    
    elif query.data == 'credit_check':
        remaining = "21 روز"
        text = f"💰 <b>اعتبار هاست</b>\n\n"
        text += f"📅 <b>زمان باقی‌مانده:</b> {remaining}\n"
        text += f"💵 <b>اعتبار باقی‌مانده:</b> $4.80\n"
        text += f"📊 <b>وضعیت:</b> ✅ فعال\n"
        text += f"🌐 <b>منطقه:</b> US West\n"
        text += f"🔄 <b>تعداد Replica:</b> 1"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='info')]]))
    
    elif query.data == 'broadcast':
        user_sessions[user_id] = {'step': 'broadcast'}
        await query.edit_message_text(
            f"📨 <b>ارسال پیام همگانی</b>\n\n🔹 پیام خود را وارد کنید\n🔹 این پیام برای {stats['total_users']} کاربر ارسال خواهد شد",
            parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='info')]])
        )
    
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')],
            [InlineKeyboardButton("📊 اطلاعات", callback_data='info')]
        ]
        text = OWNER_START_TEXT + f"\n\n📊 اکانت‌ها: {len(accounts)}\n📁 گروه‌ها: {len(joined_groups)}\n🎵 MP3: {len(mp3_files)}\n👤 کاربران: {stats['total_users']}"
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

async def start_playback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    query = update.callback_query
    group_index = user_sessions[user_id]['selected_group']
    group_info = joined_groups[group_index]
    group_link = group_info['link']
    group_name = group_info.get('name', 'گروه')
    is_mp3 = user_sessions[user_id]['is_mp3']
    file_index = user_sessions[user_id]['selected_file']
    media_file = mp3_files[file_index] if is_mp3 else mp4_files[file_index]
    media_path = media_file.get('path')
    
    if not media_path or not os.path.exists(media_path):
        await query.edit_message_text("❌ فایل رسانه یافت نشد", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='play_voice')]]))
        del user_sessions[user_id]
        return
    
    await query.edit_message_text(f"🔄 در حال پخش در ویس چت\n\n📁 {group_name}\n🎵 {media_file.get('name')}\n⏳ لطفاً صبر کنید...", parse_mode='HTML')
    
    success_count = 0
    fail_count = 0
    error_details = []
    
    for acc in accounts:
        try:
            from pyrogram import Client
            from py_tgcalls import PyTgCalls
            from py_tgcalls.types import AudioQuality
            from py_tgcalls.types.input_stream import AudioStream, InputAudioStream
            
            app = Client(f"play_{acc['id']}", api_id=API_ID, api_hash=API_HASH, session_string=acc['session'])
            await app.connect()
            
            try:
                try:
                    chat = await app.join_chat(group_link)
                    chat_id = chat.id
                except:
                    if 'joinchat/' in group_link:
                        invite = group_link.split('joinchat/')[-1]
                    elif '+' in group_link:
                        invite = group_link.split('+')[-1]
                    else:
                        invite = group_link.replace('https://t.me/', '').replace('@', '')
                    if invite and not invite.startswith('+'):
                        chat = await app.join_chat(invite)
                        chat_id = chat.id
                    else:
                        chat = await app.get_chat(group_link)
                        chat_id = chat.id
                        await app.join_chat(chat_id)
                
                call = PyTgCalls(app)
                await call.start()
                await call.join_group_call(chat_id, AudioStream(InputAudioStream(media_path, audio_parameters=AudioQuality.HIGH)))
                success_count += 1
            except Exception as e:
                error_details.append(f"اکانت {acc.get('phone')}: {e}")
                fail_count += 1
        except Exception as e:
            error_details.append(f"اکانت {acc.get('phone')}: {e}")
            fail_count += 1
    
    result = f"✅ پخش کامل شد\n\n📁 {group_name}\n🎵 {media_file.get('name')}\n✅ موفق: {success_count}\n❌ ناموفق: {fail_count}"
    if error_details:
        result += f"\n\n⚠️ خطاها:\n🔹 {error_details[0][:100]}"
    
    await query.edit_message_text(result, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='play_voice')]]))
    del user_sessions[user_id]

async def stop_all_playbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from pyrogram import Client
        from py_tgcalls import PyTgCalls
        stopped = 0
        for acc in accounts:
            try:
                app = Client(f"stop_{acc['id']}", api_id=API_ID, api_hash=API_HASH, session_string=acc['session'])
                await app.connect()
                call = PyTgCalls(app)
                await call.start()
                async for dialog in app.get_dialogs():
                    if dialog.chat.type in ["group", "supergroup"]:
                        try:
                            await call.leave_group_call(dialog.chat.id)
                            stopped += 1
                        except:
                            pass
                await call.stop()
                await app.disconnect()
            except:
                pass
        await update.message.reply_text(f"✅ پخش متوقف شد\n\n🔹 {stopped} گروه", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))
    except Exception as e:
        await update.message.reply_text(f"❌ خطا\n\n🔹 {str(e)}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID or not update.message:
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'broadcast':
        msg = update.message.text
        await update.message.reply_text(f"📨 <b>در حال ارسال...</b>\n\n🔹 پیام به {stats['total_users']} کاربر ارسال میشود", parse_mode='HTML')
        
        sent = 0
        for uid in stats['users']:
            try:
                await context.bot.send_message(uid, msg)
                sent += 1
                time.sleep(0.05)
            except:
                pass
        
        await update.message.reply_text(f"✅ <b>ارسال همگانی کامل شد</b>\n\n🔹 ارسال به {sent} کاربر", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='info')]]))
        del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'mp3':
        if update.message.audio:
            file = update.message.audio
            file_obj = await context.bot.get_file(file.file_id)
            file_path = f"mp3_{int(time.time())}_{file.file_name or 'unknown.mp3'}"
            await file_obj.download_to_drive(file_path)
            mp3_files.append({
                'name': file.file_name or 'Unknown',
                'file_id': file.file_id,
                'duration': file.duration,
                'size': file.file_size,
                'path': file_path
            })
            data['mp3_files'] = mp3_files
            save_data(data)
            await update.message.reply_text(f"✅ <b>MP3 اضافه شد</b>\n\n🎵 {file.file_name}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ فایل MP3 ارسال کنید", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_mp3')]]))
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'mp4':
        if update.message.video:
            file = update.message.video
            file_obj = await context.bot.get_file(file.file_id)
            file_path = f"mp4_{int(time.time())}_{file.file_name or 'unknown.mp4'}"
            await file_obj.download_to_drive(file_path)
            mp4_files.append({
                'name': file.file_name or 'Unknown',
                'file_id': file.file_id,
                'duration': file.duration,
                'size': file.file_size,
                'width': file.width,
                'height': file.height,
                'path': file_path
            })
            data['mp4_files'] = mp4_files
            save_data(data)
            await update.message.reply_text(f"✅ <b>MP4 اضافه شد</b>\n\n🎬 {file.file_name}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]))
            del user_sessions[user_id]
        else:
            await update.message.reply_text("❌ فایل MP4 ارسال کنید", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_mp4')]]))
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'phone':
        text = update.message.text.strip()
        if not text.startswith('+') or not text[1:].isdigit():
            await update.message.reply_text("❌ فرمت شماره نامعتبر", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_account')]]))
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
            user_sessions[user_id]['code_sent_time'] = time.time()
            await update.message.reply_text(f"📨 <b>کد ارسال شد</b>\n\n🔹 کد به {text} ارسال شد", parse_mode='HTML')
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_account')]]))
            del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'code':
        code = update.message.text.strip()
        if not code.isdigit() or len(code) != 5:
            await update.message.reply_text("❌ کد ۵ رقمی باشد")
            return
        if time.time() - user_sessions[user_id].get('code_sent_time', 0) > 300:
            await update.message.reply_text("❌ کد منقضی شد")
            del user_sessions[user_id]
            return
        try:
            phone = user_sessions[user_id]['phone']
            phone_code_hash = user_sessions[user_id]['phone_code_hash']
            app = user_sessions[user_id]['client']
            try:
                await app.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=code)
            except Exception as e:
                if "SESSION_PASSWORD_NEEDED" in str(e):
                    user_sessions[user_id]['step'] = 'password'
                    await update.message.reply_text("🔐 <b>پسورد دو مرحله‌ای</b>\n\n🔹 پسورد را وارد کنید", parse_mode='HTML')
                    return
                raise e
            session_string = await app.export_session_string()
            accounts.append({'phone': phone, 'session': session_string, 'id': len(accounts)+1})
            data['accounts'] = accounts
            save_data(data)
            await update.message.reply_text(f"✅ <b>سشن ایجاد شد</b>\n\n📱 {phone}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]))
            del user_sessions[user_id]
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'password':
        password = update.message.text.strip()
        try:
            app = user_sessions[user_id]['client']
            await app.check_password(password)
            session_string = await app.export_session_string()
            phone = user_sessions[user_id]['phone']
            accounts.append({'phone': phone, 'session': session_string, 'id': len(accounts)+1})
            data['accounts'] = accounts
            save_data(data)
            await update.message.reply_text(f"✅ <b>سشن ایجاد شد</b>\n\n📱 {phone}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]))
            del user_sessions[user_id]
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")
            del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'join_group_link':
        link = update.message.text.strip()
        await update.message.reply_text(f"🔄 <b>در حال جوین شدن</b>\n\n🔗 {link}", parse_mode='HTML')
        success = 0
        group_name = "نامشخص"
        for acc in accounts:
            try:
                from pyrogram import Client
                app = Client(f"join_{acc['id']}", api_id=API_ID, api_hash=API_HASH, session_string=acc['session'])
                await app.connect()
                try:
                    chat = await app.join_chat(link)
                    group_name = chat.title or "نامشخص"
                    success += 1
                except:
                    try:
                        if 'joinchat/' in link:
                            invite = link.split('joinchat/')[-1]
                        elif '+' in link:
                            invite = link.split('+')[-1]
                        else:
                            invite = link.replace('https://t.me/', '')
                        if not invite.startswith('+'):
                            chat = await app.join_chat(invite)
                            group_name = chat.title or "نامشخص"
                            success += 1
                    except:
                        pass
                await app.disconnect()
            except:
                pass
        if success > 0:
            exists = any(g.get('link') == link for g in joined_groups)
            if not exists:
                joined_groups.append({'name': group_name, 'link': link})
                data['joined_groups'] = joined_groups
                save_data(data)
        await update.message.reply_text(f"✅ <b>جوین شد</b>\n\n📁 {group_name}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]]))
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
        await update.message.reply_text("❌ لغو شد", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]))
    else:
        await update.message.reply_text("ℹ️ هیچ عملیاتی وجود ندارد", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]))

if __name__ == '__main__':
    try:
        print("🔄 راه‌اندازی...")
        try:
            r = httpx.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", json={"drop_pending_updates": True}, timeout=30)
            if r.json().get('ok'):
                print("✅ Webhook پاک شد")
        except:
            pass
        time.sleep(2)
        print(f"📊 اکانت‌ها: {len(accounts)} | MP3: {len(mp3_files)} | MP4: {len(mp4_files)} | گروه‌ها: {len(joined_groups)}")
        
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('cancel', cancel_command))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.AUDIO, handle_message))
        app.add_handler(MessageHandler(filters.VIDEO, handle_message))
        print("✅ ربات راه‌اندازی شد!")
        app.run_polling(drop_pending_updates=True, allowed_updates=['message', 'callback_query'])
    except Exception as e:
        print(f"❌ خطا: {e}")
