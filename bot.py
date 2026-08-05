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
joined_groups = []

DATA_FILE = "data.json"

def load_data():
    global accounts, mp3_files, mp4_files, joined_groups
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                accounts = data.get('accounts', [])
                mp3_files = data.get('mp3_files', [])
                mp4_files = data.get('mp4_files', [])
                joined_groups = data.get('joined_groups', [])
    except:
        pass

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'accounts': accounts,
                'mp3_files': mp3_files,
                'mp4_files': mp4_files,
                'joined_groups': joined_groups
            }, f)
    except:
        pass

load_data()

OWNER_START_TEXT = """
🌟 <b>به ربات ZX خوش آمدید</b>

💎 <b>سازنده محترم</b>، لطفاً یکی از گزینه‌های زیر را انتخاب کنید:

➕ <b>افزودن اکانت</b> • ایجاد سشن تلگرام
⚙️ <b>تنظیمات</b> • مدیریت فایل‌ها و اطلاعات
💥 <b>حمله</b> • مدیریت گروه‌ها و پخش در ویس چت
"""

NORMAL_START_TEXT = "⛔ <b>دسترسی محدود</b>"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        text = OWNER_START_TEXT + f"\n\n📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n📁 <b>تعداد گروه‌ها:</b> {len(joined_groups)}"
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
        await query.answer("⛔ دسترسی محدود", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'add_account':
        user_sessions[user_id] = {'step': 'phone', 'api_id': API_ID, 'api_hash': API_HASH}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]
        await query.edit_message_text(
            "📱 <b>ایجاد سشن جدید</b>\n\n"
            "🔹 لطفاً شماره تلفن اکانت تلگرام خود را وارد کنید\n"
            "🔹 مثال: <code>+989123456789</code>\n\n"
            f"🔑 API_ID: <code>{API_ID}</code>\n"
            f"🔑 API_HASH: <code>{API_HASH}</code>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🎵 افزودن MP3", callback_data='add_mp3')],
            [InlineKeyboardButton("🎬 افزودن MP4", callback_data='add_mp4')],
            [InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data='list_accounts')],
            [InlineKeyboardButton("🎵 لیست MP3", callback_data='list_mp3')],
            [InlineKeyboardButton("🎬 لیست MP4", callback_data='list_mp4')],
            [InlineKeyboardButton("📁 لیست گروه‌ها", callback_data='list_groups')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        
        text = f"⚙️ <b>تنظیمات</b>\n\n"
        text += f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n"
        text += f"🎵 <b>تعداد MP3:</b> {len(mp3_files)}\n"
        text += f"🎬 <b>تعداد MP4:</b> {len(mp4_files)}\n"
        text += f"📁 <b>تعداد گروه‌ها:</b> {len(joined_groups)}"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'list_groups':
        if not joined_groups:
            await query.edit_message_text(
                "📁 <b>لیست گروه‌ها</b>\n\n❌ هیچ گروهی یافت نشد",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "📁 <b>گروه‌های جوین شده</b>\n\n"
            for i, group in enumerate(joined_groups, 1):
                text += f"{i}. {group.get('name', 'نامشخص')}\n"
                text += f"🆔 {group.get('link', '')}\n\n"
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
    
    elif query.data == 'list_accounts':
        if not accounts:
            await query.edit_message_text(
                "📋 <b>لیست اکانت‌ها</b>\n\n❌ هیچ اکانتی یافت نشد",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "📋 <b>لیست اکانت‌ها</b>\n\n"
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
                "🎵 <b>لیست MP3</b>\n\n❌ هیچ فایل MP3 یافت نشد",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "🎵 <b>لیست فایل‌های MP3</b>\n\n"
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
                "🎬 <b>لیست MP4</b>\n\n❌ هیچ فایل MP4 یافت نشد",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
        else:
            text = "🎬 <b>لیست فایل‌های MP4</b>\n\n"
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
            "🎵 <b>افزودن فایل MP3</b>\n\n"
            "🔹 لطفاً فایل MP3 خود را ارسال کنید\n"
            "🔹 فایل در سرور ذخیره خواهد شد",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'add_mp4':
        user_sessions[user_id] = {'step': 'mp4'}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]]
        await query.edit_message_text(
            "🎬 <b>افزودن فایل MP4</b>\n\n"
            "🔹 لطفاً فایل MP4 خود را ارسال کنید\n"
            "🔹 فایل در سرور ذخیره خواهد شد",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'attack':
        keyboard = [
            [InlineKeyboardButton("👥 جوین شدن در گروه", callback_data='join_group')],
            [InlineKeyboardButton("🎵 پخش در ویس چت", callback_data='play_voice')],
            [InlineKeyboardButton("⏹️ توقف پخش", callback_data='stop_playback')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
        ]
        await query.edit_message_text(
            "💥 <b>مدیریت حمله</b>\n\n"
            "🔹 <b>جوین شدن در گروه:</b> ورود به گروه جدید\n"
            "🔹 <b>پخش در ویس چت:</b> انتخاب گروه و پخش رسانه\n"
            "🔹 <b>توقف پخش:</b> پایان پخش در تمام گروه‌ها\n\n"
            f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n"
            f"🎵 <b>MP3:</b> {len(mp3_files)} | 🎬 <b>MP4:</b> {len(mp4_files)}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == 'join_group':
        if len(accounts) == 0:
            await query.edit_message_text(
                "❌ <b>هیچ اکانتی وجود ندارد</b>\n\n"
                "🔹 لطفاً ابتدا از بخش <b>افزودن اکانت</b> یک اکانت اضافه کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
            )
            return
        
        user_sessions[user_id] = {'step': 'join_group_link'}
        await query.edit_message_text(
            "👥 <b>جوین شدن در گروه</b>\n\n"
            "🔹 لطفاً لینک گروه را وارد کنید\n"
            "🔹 مثال: <code>https://t.me/joinchat/abc123</code>\n\n"
            f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}",
            parse_mode='HTML'
        )
    
    elif query.data == 'play_voice':
        if len(accounts) == 0:
            await query.edit_message_text(
                "❌ <b>هیچ اکانتی وجود ندارد</b>\n\n"
                "🔹 لطفاً ابتدا از بخش <b>افزودن اکانت</b> یک اکانت اضافه کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
            )
            return
        
        if len(mp3_files) == 0 and len(mp4_files) == 0:
            await query.edit_message_text(
                "❌ <b>هیچ فایل رسانه‌ای وجود ندارد</b>\n\n"
                "🔹 لطفاً ابتدا از بخش <b>تنظیمات</b> فایل MP3 یا MP4 اضافه کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
            )
            return
        
        if len(joined_groups) == 0:
            await query.edit_message_text(
                "❌ <b>هیچ گروهی وجود ندارد</b>\n\n"
                "🔹 لطفاً ابتدا از بخش <b>جوین شدن در گروه</b> یک گروه اضافه کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
            )
            return
        
        keyboard = []
        for i, group in enumerate(joined_groups):
            keyboard.append([InlineKeyboardButton(f"📁 {group.get('name', f'گروه {i+1}')}", callback_data=f'play_group_{i}')])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='attack')])
        
        user_sessions[user_id] = {'step': 'play_select_group'}
        await query.edit_message_text(
            "🎵 <b>انتخاب گروه</b>\n\n"
            "🔹 لطفاً گروه مورد نظر را انتخاب کنید",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith('play_group_'):
        index = int(query.data.split('_')[2])
        if index < len(joined_groups):
            user_sessions[user_id]['selected_group'] = index
            user_sessions[user_id]['step'] = 'play_select_media'
            
            keyboard = []
            for i, mp3 in enumerate(mp3_files):
                keyboard.append([InlineKeyboardButton(f"🎵 {mp3.get('name', f'MP3 {i+1}')}", callback_data=f'play_file_mp3_{i}')])
            for i, mp4 in enumerate(mp4_files):
                keyboard.append([InlineKeyboardButton(f"🎬 {mp4.get('name', f'MP4 {i+1}')}", callback_data=f'play_file_mp4_{i}')])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='play_voice')])
            
            group_name = joined_groups[index].get('name', 'گروه')
            await query.edit_message_text(
                f"🎵 <b>انتخاب رسانه</b>\n\n"
                f"🔹 لطفاً رسانه مورد نظر را برای پخش در {group_name} انتخاب کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data.startswith('play_file_mp3_'):
        index = int(query.data.split('_')[3])
        if index < len(mp3_files):
            user_sessions[user_id]['selected_file'] = index
            user_sessions[user_id]['is_mp3'] = True
            user_sessions[user_id]['step'] = 'play_start'
            await start_playback(update, context, user_id)
    
    elif query.data.startswith('play_file_mp4_'):
        index = int(query.data.split('_')[3])
        if index < len(mp4_files):
            user_sessions[user_id]['selected_file'] = index
            user_sessions[user_id]['is_mp3'] = False
            user_sessions[user_id]['step'] = 'play_start'
            await start_playback(update, context, user_id)
    
    elif query.data == 'stop_playback':
        await query.edit_message_text(
            "⏹️ <b>توقف پخش</b>\n\n"
            "🔄 در حال توقف پخش در تمام گروه‌ها...",
            parse_mode='HTML'
        )
        await stop_all_playbacks(update, context)
    
    elif query.data == 'back_to_menu':
        keyboard = [
            [InlineKeyboardButton("➕ افزودن اکانت", callback_data='add_account')],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data='settings')],
            [InlineKeyboardButton("💥 حمله", callback_data='attack')]
        ]
        text = OWNER_START_TEXT + f"\n\n📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n📁 <b>تعداد گروه‌ها:</b> {len(joined_groups)}"
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def start_playback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    query = update.callback_query
    
    group_index = user_sessions[user_id]['selected_group']
    group_info = joined_groups[group_index]
    group_link = group_info['link']
    group_name = group_info.get('name', 'گروه')
    
    is_mp3 = user_sessions[user_id]['is_mp3']
    file_index = user_sessions[user_id]['selected_file']
    
    if is_mp3:
        media_file = mp3_files[file_index]
    else:
        media_file = mp4_files[file_index]
    
    media_path = media_file.get('path')
    
    if not media_path or not os.path.exists(media_path):
        await query.edit_message_text(
            f"❌ <b>فایل رسانه یافت نشد</b>\n\n"
            f"🔹 مسیر: {media_path}\n"
            "🔹 لطفاً دوباره رسانه را اضافه کنید",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='play_voice')]])
        )
        del user_sessions[user_id]
        return
    
    await query.edit_message_text(
        f"🔄 <b>در حال پخش</b>\n\n"
        f"📁 <b>گروه:</b> {group_name}\n"
        f"🎵 <b>رسانه:</b> {media_file.get('name', 'Unknown')}\n"
        f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n\n"
        "⏳ لطفاً صبر کنید...",
        parse_mode='HTML'
    )
    
    success_count = 0
    fail_count = 0
    error_details = []
    
    for acc in accounts:
        try:
            from pyrogram import Client
            from tgcaller import TgCaller
            
            app = Client(
                f"play_session_{acc['id']}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=acc['session']
            )
            await app.connect()
            
            try:
                chat = await app.join_chat(group_link)
                chat_id = chat.id
            except Exception as e1:
                try:
                    if 'joinchat/' in group_link:
                        invite_code = group_link.split('joinchat/')[-1]
                    elif '+' in group_link:
                        invite_code = group_link.split('+')[-1]
                    else:
                        invite_code = group_link.replace('https://t.me/', '').replace('@', '')
                    
                    if invite_code and not invite_code.startswith('+'):
                        chat = await app.join_chat(invite_code)
                        chat_id = chat.id
                    else:
                        chat = await app.get_chat(group_link)
                        chat_id = chat.id
                        await app.join_chat(chat_id)
                except Exception as e2:
                    error_details.append(f"اکانت {acc.get('phone')}: جوین نشد - {e2}")
                    fail_count += 1
                    await app.disconnect()
                    continue
            
            try:
                caller = TgCaller(app)
                await caller.join_call(chat_id)
                await caller.play(media_path)
                success_count += 1
            except Exception as e3:
                error_details.append(f"اکانت {acc.get('phone')}: پخش نشد - {e3}")
                fail_count += 1
                await app.disconnect()
            
        except Exception as e:
            error_details.append(f"اکانت {acc.get('phone')}: {e}")
            fail_count += 1
    
    result_text = f"✅ <b>عملیات پخش کامل شد</b>\n\n"
    result_text += f"📁 <b>گروه:</b> {group_name}\n"
    result_text += f"🎵 <b>رسانه:</b> {media_file.get('name', 'Unknown')}\n"
    result_text += f"✅ <b>موفق:</b> {success_count} اکانت\n"
    result_text += f"❌ <b>ناموفق:</b> {fail_count} اکانت\n"
    result_text += f"📊 <b>مجموع:</b> {len(accounts)} اکانت\n"
    
    if error_details:
        result_text += f"\n⚠️ <b>خطاها:</b>\n"
        for err in error_details[:3]:
            result_text += f"🔹 {err[:100]}...\n"
    
    await query.edit_message_text(
        result_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='play_voice')]])
    )
    
    if user_id in user_sessions:
        del user_sessions[user_id]

async def stop_all_playbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from pyrogram import Client
        from tgcaller import TgCaller
        
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
                
                caller = TgCaller(app)
                await caller.leave_all_calls()
                stopped_count += 1
                
                await app.disconnect()
            except:
                pass
        
        await update.message.reply_text(
            f"✅ <b>پخش متوقف شد</b>\n\n"
            f"🔹 پخش در {stopped_count} گروه متوقف شد",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>خطا در توقف پخش</b>\n\n🔹 {str(e)}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'phone':
        if not text.startswith('+') or not text[1:].isdigit():
            await update.message.reply_text(
                "❌ <b>فرمت شماره نامعتبر</b>\n\n🔹 مثال: +989123456789",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_account')]])
            )
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
                f"📨 <b>کد تایید ارسال شد</b>\n\n"
                f"🔹 کد ۵ رقمی به شماره <code>{text}</code> ارسال شد\n"
                f"🔹 لطفاً کد دریافتی را وارد کنید\n"
                f"⚠️ <b>توجه:</b> کد تنها ۵ دقیقه اعتبار دارد",
                parse_mode='HTML'
            )
        except Exception as e:
            error_msg = str(e)
            if "FLOOD_WAIT" in error_msg:
                await update.message.reply_text(
                    f"❌ <b>تعداد درخواست زیاد</b>\n\n"
                    f"🔹 {error_msg}\n"
                    "🔹 لطفاً چند دقیقه صبر کنید",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_account')]])
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>خطا در ارسال کد</b>\n\n"
                    f"🔹 {error_msg}",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
                )
            if user_id in user_sessions:
                del user_sessions[user_id]
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'code':
        if not text.isdigit() or len(text) != 5:
            await update.message.reply_text(
                "❌ <b>کد نامعتبر</b>\n\n🔹 کد باید ۵ رقم باشد",
                parse_mode='HTML'
            )
            return
        
        code_sent_time = user_sessions[user_id].get('code_sent_time', 0)
        if time.time() - code_sent_time > 300:
            await update.message.reply_text(
                "❌ <b>کد منقضی شده</b>\n\n"
                "🔹 زمان ۵ دقیقه به پایان رسیده است\n"
                "🔹 لطفاً دوباره از ابتدا شروع کنید",
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
            
            try:
                await app.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=text)
            except Exception as sign_in_error:
                error_msg = str(sign_in_error)
                if "SESSION_PASSWORD_NEEDED" in error_msg:
                    user_sessions[user_id]['step'] = 'password'
                    await update.message.reply_text(
                        "🔐 <b>تایید دو مرحله‌ای</b>\n\n"
                        "🔹 این اکانت دارای تایید دو مرحله‌ای است\n"
                        "🔹 لطفاً پسورد اکانت خود را وارد کنید",
                        parse_mode='HTML'
                    )
                    return
                else:
                    raise sign_in_error
            
            session_string = await app.export_session_string()
            
            account_info = {
                'phone': phone,
                'session': session_string,
                'id': len(accounts) + 1
            }
            accounts.append(account_info)
            save_data()
            
            await update.message.reply_text(
                f"✅ <b>سشن ایجاد شد</b>\n\n"
                f"📱 <b>شماره:</b> <code>{phone}</code>\n"
                f"🆔 <b>شناسه:</b> {len(accounts)}\n\n"
                f"📊 <b>تعداد کل اکانت‌ها:</b> {len(accounts)}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
            
            await app.disconnect()
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except Exception as e:
            error_msg = str(e)
            if "PHONE_CODE_EXPIRED" in error_msg:
                await update.message.reply_text(
                    "❌ <b>کد منقضی شده</b>\n\n"
                    "🔹 لطفاً دوباره از ابتدا شروع کنید",
                    parse_mode='HTML'
                )
            elif "FLOOD_WAIT" in error_msg:
                await update.message.reply_text(
                    f"❌ <b>تعداد درخواست زیاد</b>\n\n🔹 {error_msg}",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>خطا در ایجاد سشن</b>\n\n🔹 {error_msg}",
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
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'password':
        password = text
        
        try:
            phone = user_sessions[user_id]['phone']
            app = user_sessions[user_id]['client']
            
            await app.check_password(password)
            
            session_string = await app.export_session_string()
            
            account_info = {
                'phone': phone,
                'session': session_string,
                'id': len(accounts) + 1
            }
            accounts.append(account_info)
            save_data()
            
            await update.message.reply_text(
                f"✅ <b>سشن ایجاد شد</b>\n\n"
                f"📱 <b>شماره:</b> <code>{phone}</code>\n"
                f"🆔 <b>شناسه:</b> {len(accounts)}\n\n"
                f"📊 <b>تعداد کل اکانت‌ها:</b> {len(accounts)}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
            
            await app.disconnect()
            if user_id in user_sessions:
                del user_sessions[user_id]
                
        except Exception as e:
            error_msg = str(e)
            if "PASSWORD_HASH_INVALID" in error_msg:
                await update.message.reply_text(
                    "❌ <b>پسورد اشتباه است</b>\n\n"
                    "🔹 لطفاً پسورد صحیح را وارد کنید",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>خطا در تایید پسورد</b>\n\n🔹 {error_msg}",
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
                f"✅ <b>فایل MP3 اضافه شد</b>\n\n"
                f"🎵 <b>نام:</b> {file_info['name']}\n"
                f"⏱️ <b>مدت:</b> {file_info['duration']} ثانیه\n"
                f"💾 <b>حجم:</b> {file_info['size']} بایت\n"
                f"📊 <b>تعداد کل MP3:</b> {len(mp3_files)}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
            del user_sessions[user_id]
        else:
            await update.message.reply_text(
                "❌ <b>فرمت فایل نامعتبر</b>\n\n🔹 لطفاً یک فایل MP3 ارسال کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_mp3')]])
            )
        return
    
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
                f"✅ <b>فایل MP4 اضافه شد</b>\n\n"
                f"🎬 <b>نام:</b> {file_info['name']}\n"
                f"⏱️ <b>مدت:</b> {file_info['duration']} ثانیه\n"
                f"💾 <b>حجم:</b> {file_info['size']} بایت\n"
                f"📊 <b>تعداد کل MP4:</b> {len(mp4_files)}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='settings')]])
            )
            del user_sessions[user_id]
        else:
            await update.message.reply_text(
                "❌ <b>فرمت فایل نامعتبر</b>\n\n🔹 لطفاً یک فایل MP4 ارسال کنید",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='add_mp4')]])
            )
        return
    
    if user_id in user_sessions and user_sessions[user_id].get('step') == 'join_group_link':
        link = text
        
        await update.message.reply_text(
            f"🔄 <b>در حال جوین شدن</b>\n\n"
            f"🔗 <b>لینک:</b> {link}\n"
            f"📊 <b>تعداد اکانت‌ها:</b> {len(accounts)}\n\n"
            "⏳ لطفاً صبر کنید...",
            parse_mode='HTML'
        )
        
        success_count = 0
        fail_count = 0
        group_name = "نامشخص"
        
        for acc in accounts:
            try:
                from pyrogram import Client
                
                app = Client(
                    f"join_session_{acc['id']}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=acc['session']
                )
                await app.connect()
                
                try:
                    chat = await app.join_chat(link)
                    chat_id = chat.id
                    group_name = chat.title or "نامشخص"
                except Exception as e1:
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
                            group_name = chat.title or "نامشخص"
                        else:
                            chat = await app.get_chat(link)
                            chat_id = chat.id
                            group_name = chat.title or "نامشخص"
                            await app.join_chat(chat_id)
                    except Exception as e2:
                        fail_count += 1
                        await app.disconnect()
                        continue
                
                success_count += 1
                await app.disconnect()
                
            except Exception as e:
                fail_count += 1
        
        if success_count > 0:
            exists = False
            for g in joined_groups:
                if g.get('link') == link:
                    exists = True
                    break
            if not exists:
                joined_groups.append({
                    'name': group_name,
                    'link': link,
                    'joined_at': time.time()
                })
                save_data()
        
        result_text = f"✅ <b>عملیات جوین شدن کامل شد</b>\n\n"
        result_text += f"📁 <b>گروه:</b> {group_name}\n"
        result_text += f"🔗 <b>لینک:</b> {link}\n"
        result_text += f"✅ <b>موفق:</b> {success_count} اکانت\n"
        result_text += f"❌ <b>ناموفق:</b> {fail_count} اکانت\n"
        result_text += f"📊 <b>مجموع:</b> {len(accounts)} اکانت\n"
        
        await update.message.reply_text(
            result_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='attack')]])
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
        await update.message.reply_text(
            "❌ <b>عملیات لغو شد</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    else:
        await update.message.reply_text(
            "ℹ️ <b>هیچ عملیات فعالی وجود ندارد</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )

if __name__ == '__main__':
    try:
        print("🔄 در حال راه‌اندازی...")
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
        print(f"📁 تعداد گروه‌ها: {len(joined_groups)}")
        
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
