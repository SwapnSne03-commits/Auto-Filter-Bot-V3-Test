import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
lock = asyncio.Lock()
from database.users_chats_db import db
from database.refer import referdb
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import *
from fuzzywuzzy import process
from database.users_chats_db import db
from database.ia_filterdb import Media, Media2, get_file_details, get_search_results, get_bad_files
from logging_helper import LOGGER
from urllib.parse import quote_plus
from Lucia.util.file_properties import get_name, get_hash, get_media_file_size
from database.topdb import silentdb
import requests
import string
import tracemalloc

tracemalloc.start()

TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    bot_id = client.me.id

    if message.text and message.text.lower().startswith(("#request", "/request")):
        return
		
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text(f"ɪ ᴀᴍ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ 🛠️. ɪ ᴡɪʟʟ ʙᴇ ʙᴀᴄᴋ ꜱᴏᴏɴ 🔜", disable_web_page_preview=True)
        return
    await silentdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        if settings['auto_ffilter']:
            if re.search(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
                if await is_check_admin(client, message.chat.id, message.from_user.id):
                    return
                return await message.delete()   
            await auto_filter(client, message)
    else:
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ✅\n\n📂 ꜰɪʟᴇꜱ ꜰᴏᴜɴᴅ : {str(total_results)}\n🔍 ꜱᴇᴀʀᴄʜ :</b> <code>{search}</code>\n\n<b>‼️ ᴛʜɪs ɪs ᴀ <u>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</u> sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...\n\n📝 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ : 👇</b>",   
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ᴊᴏɪɴ ᴀɴᴅ ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)]]))


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    bot_id = bot.me.id
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text(f"ɪ ᴀᴍ ᴄᴜʀʀᴇɴᴛʟʏ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ 🛠️. ɪ ᴡɪʟʟ ʙᴇ ʙᴀᴄᴋ ꜱᴏᴏɴ 🔜", disable_web_page_preview=True)
        return
    if content.startswith(("/", "#")):
        return  
    try:
        await silentdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        if pm_search:
            await auto_filter(bot, message)
        else:
            await message.reply_text(
             text=f"<b><i>Sᴏʀʀʏ! Yᴏᴜ Cᴀɴɴ'ᴛ Sᴇᴀʀᴄʜ Hᴇʀᴇ 🚫.\nJᴏɪɴ Tʜᴇ Rᴇǫᴜᴇsᴛ Gʀᴏᴜᴘ Fʀᴏᴍ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴ Aɴᴅ Sᴇᴀʀᴄʜ Tʜᴇʀᴇ !</i></b>",   
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Rᴇǫᴜᴇsᴛ Gʀᴏᴜᴘ ", url=GRP_LNK)]])
            )
    except Exception as e:
        LOGGER.error(f"An error occurred: {str(e)}")


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('ɪɴᴠɪᴛᴇ ɪɪɴᴋ', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='premium')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await bot.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto("https://i.ibb.co/spyQ29ry/photo-2025-12-12-14-23-10-7582976923882487832.jpg")
        )
    await query.message.edit_text(
        text=f'Hay Your refer link:\n\nhttps://t.me/{bot.me.username}?start=reff_{query.from_user.id}\n\nShare this link with your friends, Each time they join,  you will get 10 refferal points and after 100 points you will get 1 month premium subscription.',
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
        )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        try:
            offset = int(offset)
        except:
            offset = 0
        if BUTTONS.get(key)!=None:
            search = BUTTONS.get(key)
        else:
            search = FRESH.get(key)
        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return
        active = temp.ACTIVE_FILTER.get(key)
        settings = await get_settings(query.message.chat.id)
        per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)
        #active = temp.ACTIVE_FILTER.get(key)

        if active:
            # 🔹 FILTERED PAGINATION MODE
            all_files = temp.GETALL.get(key, [])

            if active["type"] == "quality":
                data = [
                    f for f in all_files
                    if active["value"].lower() in (f.file_name or "").lower()
                ]

            elif active["type"] == "season":
                data = [
                    f for f in all_files
                    if active["value"].lower() in (f.file_name or "").lower()
                ]

            elif active["type"] == "language":
                aliases = SMART_LANG_MAP.get(active["value"], {}).get("aliases", [])
                data = [
                    f for f in all_files
                    if any(a in (f.file_name or "").lower() for a in aliases)
                ]

            total = len(data)
            files = data[offset: offset + per_page]

            if total > offset + per_page:
                n_offset = offset + per_page
            else:
                n_offset = 0

        else:
            # 🔹 NORMAL HOMEPAGE PAGINATION MODE
            files, n_offset, total = await get_search_results(
                query.message.chat.id, search, offset=offset, filter=True
            )

            # normalize n_offset
        try:
            n_offset = int(n_offset)
        except:
            n_offset = 0

        if not files:
            return
        #temp.GETALL[key] = files
        temp.SHORT[query.from_user.id] = query.message.chat.id
        settings = await get_settings(query.message.chat.id)
        if settings.get('button'):
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                    ),
                ]
                for file in files
            ]
            btn.insert(0, 
                [ 
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            
        else:
            btn = []
            btn.insert(0, 
                [
                    InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                    InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
                ]
            )
            
        try:
            if settings['max_btn']:
                if 0 < offset <= 10:
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - 10
                if n_offset == 0:
                    btn.append(
                        [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                    )
                elif off_set is None:
                    btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                            InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                            InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                        ],
                    )
            else:
                if 0 < offset <= int(MAX_B_TN):
                    off_set = 0
                elif offset == 0:
                    off_set = None
                else:
                    off_set = offset - int(MAX_B_TN)
                if n_offset == 0:
                    btn.append(
                        [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                    )
                elif off_set is None:
                    btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
                else:
                    btn.append(
                        [
                            InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                            InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                            InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                        ],
                    )
        except KeyError:
            await save_group_settings(query.message.chat.id, 'max_btn', True)
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ ⋟", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        if not settings.get('button'):
            cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
            time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
            remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
            cap = await get_cap(settings, remaining_seconds, files, query, total, search, offset)
            try:
                await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            except MessageNotModified:
                pass
        else:
            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except MessageNotModified:
                pass
        await query.answer()
    except Exception as e:
        LOGGER.error(f"Error In Next Funtion - {e}")

# ================= OLD QUALITY CALLBACK =================
async def old_qualities_cb(client: Client, query: CallbackQuery):
    try:
        try:
            if int(query.from_user.id) not in [
                query.message.reply_to_message.from_user.id, 0
            ]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\n"
                    f"ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\n"
                    f"ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass

        _, key, offset = query.data.split("#")
        search = FRESH.get(key)
        search = search.replace(" ", "_")
        offset = int(offset)

        btn = []
        for i in range(0, len(QUALITIES) - 1, 2):
            btn.append([
                InlineKeyboardButton(
                    text=QUALITIES[i].title(),
                    callback_data=f"fq#{QUALITIES[i].lower()}#{key}#{offset}"
                ),
                InlineKeyboardButton(
                    text=QUALITIES[i + 1].title(),
                    callback_data=f"fq#{QUALITIES[i + 1].lower()}#{key}#{offset}"
                ),
            ])

        btn.insert(0, [
            InlineKeyboardButton(
                text="⇊ ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ ⇊",
                callback_data="ident"
            )
        ])

        btn.append([
            InlineKeyboardButton(
                text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭",
                callback_data=f"fq#homepage#{key}#0"
            )
        ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        LOGGER.error(f"Error In Old Quality Callback - {e}")


# ================= SMART QUALITY CALLBACK =================
# ================= SMART QUALITY CALLBACK =================
async def smart_qualities_cb(client: Client, query: CallbackQuery):
    try:
        _, key, offset = query.data.split("#")
        offset = int(offset)

        # 🔐 STRICT OWNERSHIP CHECK (ADD HERE)
        owner_id = int(key.split("-")[1])
        if query.from_user.id != owner_id:
            return await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʙᴜᴅᴅʏ !!",
                show_alert=True
			)
        if key not in temp.SMART_FILTERS:
            return await query.answer(
                "❌ Session expired, please search again",
                show_alert=True
            )

        qualities = temp.SMART_FILTERS[key].get("qualities", [])
        all_files = temp.GETALL.get(key, [])

        if not qualities:
            return await query.answer(
                "❌ No quality available",
                show_alert=True
            )

        # 🔹 Only button view (no filter yet)
        btn = []
        for i in range(0, len(qualities), 2):
            row = [
                InlineKeyboardButton(
                    qualities[i].upper(),
                    callback_data=f"fq#{qualities[i]}#{key}#0"
                )
            ]
            if i + 1 < len(qualities):
                row.append(
                    InlineKeyboardButton(
                        qualities[i + 1].upper(),
                        callback_data=f"fq#{qualities[i + 1]}#{key}#0"
                    )
                )
            btn.append(row)

        btn.insert(0, [
            InlineKeyboardButton("⇊ ꜱᴇʟᴇᴄᴛ ǫᴜᴀʟɪᴛʏ ⇊", callback_data="ident")
        ])

        btn.append([
            InlineKeyboardButton("⋞ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs", callback_data=f"fq#homepage#{key}#0")
        ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        LOGGER.error(f"Error In Smart Quality Callback - {e}")

# ================= QUALITY ROUTER =================
@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_router(client: Client, query: CallbackQuery):
    if SMART_SELECTION_MODE:
        return await smart_qualities_cb(client, query)
    return await old_qualities_cb(client, query)

@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, qual, key, _ = query.data.split("#")
        offset = 0

         # 🔐 STRICT OWNERSHIP CHECK (ADD HERE)
        owner_id = int(key.split("-")[1])
        if query.from_user.id != owner_id:
            return await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʙᴜᴅᴅʏ !!",
                show_alert=True
			)

        message = query.message
        chat_id = message.chat.id
        req = query.from_user.id

        # 🔐 Ownership check
        try:
            if int(query.from_user.id) not in [message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ Hello {query.from_user.first_name}, this is not your request.",
                    show_alert=True,
                )
        except:
            pass

        search = FRESH.get(key, "").replace("_", " ")
        BUTTONS[key] = search
        # ================= SAVE ACTIVE FILTER STATE =================
        if not hasattr(temp, "ACTIVE_FILTER"):
            temp.ACTIVE_FILTER = {}

        if qual == "homepage":
            # homepage এ গেলে filter clear
            temp.ACTIVE_FILTER.pop(key, None)
        else:
            # quality filter active
            temp.ACTIVE_FILTER[key] = {
                "type": "quality",
                "value": qual
            }
# ============================================================
        # ================= SMART MODE =================
        if SMART_SELECTION_MODE:
            offset = 0   # ⬅️ IMPORTANT
            all_files = temp.GETALL.get(key, [])

            # 🔁 BACK TO MAIN FILE LIST
            if qual == "homepage":
                files = all_files

                # 🔄 restore pagination state
                state = temp.PAGE_STATE.get(key, {})
                per_page = state.get("per_page", 10)
                total_results = state.get("total_results", len(all_files))

                files = files[offset: offset + per_page]

                if total_results > offset + per_page:
                    n_offset = offset + per_page
                else:
                    n_offset = ""
            # 🔍 FILTER MODE (quality selected)
            else:
                offset = 0
                # 1️⃣ সব ফাইল থেকে filter করো
                filtered_files = [
                    f for f in all_files
                    if qual.lower() in (f.file_name or "").lower()
                ]

                total_results = len(filtered_files)

                settings = await get_settings(chat_id)
                per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)

                # 2️⃣ filter করলে সবসময় first page থেকে শুরু
                offset = 0
                files = filtered_files[:per_page]

                # ⭐⭐⭐ EXACTLY HERE ⭐⭐⭐
                temp.PAGE_STATE[key] = {
                    "total_results": total_results,
                    "per_page": per_page,
                    "current_offset": offset
	            }
                # 3️⃣ pagination decide করো
                if total_results > per_page:
                    n_offset = per_page
                else:
                    n_offset = ""   # 👈 এইখানেই "no more page available" trigger হবে   # ❌ no pagination in filter mode

            if not files:
                # 🔁 homepage এ গেলে popup না দেখাও
                if SMART_SELECTION_MODE and qual == "homepage":
                    files = all_files
                else:
                    return await query.answer(
                        "🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                        show_alert=True
					)

        # ================= OLD MODE =================
        else:
            if qual != "homepage":
                search = f"{search} {qual}"

            files, n_offset, total_results = await get_search_results(
                chat_id,
                search,
                offset=offset,
                filter=True
            )

            if not files:
                return await query.answer(
                    "🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                    show_alert=True
                )


        # ================= BUILD FILE BUTTONS =================
        settings = await get_settings(chat_id)

        btn = [
            [
                InlineKeyboardButton(
                    text=f"{silent_size(f.file_size)} | {extract_tag(f.file_name)} {clean_filename(f.file_name)}",
                    callback_data=f"file#{f.file_id}"
                )
            ]
            for f in files
        ]

        # 🔝 Top filter buttons
        btn.insert(0, [
            InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#0"),
        ])

        # 🔽 Pagination (old mode OR restored homepage)
        if n_offset != "":
            try:
                per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)
                current_page = (offset // per_page) + 1
                total_pages = math.ceil(total_results / per_page)
                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"),
                    InlineKeyboardButton(
                        text=f"{current_page}/{total_pages}",
                        callback_data="pages"
                    ),
                    InlineKeyboardButton(
                        "ɴᴇxᴛ ⋟",
                        callback_data=f"next_{req}_{key}_{n_offset}"
                    )
                ])
            except:
                pass
        else:
            # ℹ️ single page info
            btn.append([
                InlineKeyboardButton(
                    text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",
                    callback_data="pages"
                )
            ])

        # ================= SEND UPDATE =================
        try:
            if settings.get("button"):
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            else:
                cap = await get_cap(
                    settings,
                    "0",
                    files,
                    query,
                    total_results,
                    search,
                    offset
                )
                await query.message.edit_text(
                    text=cap,
                    reply_markup=InlineKeyboardMarkup(btn),
                    disable_web_page_preview=True,
                    parse_mode=enums.ParseMode.HTML
                )
        except MessageNotModified:
            pass

        await query.answer()

    except Exception as e:
        LOGGER.error(f"Error In Quality Filter - {e}")
# ================= OLD LANGUAGE CALLBACK =================
# ================= OLD LANGUAGE CALLBACK =================
async def old_languages_cb(client: Client, query: CallbackQuery):
    try:
        try:
            if int(query.from_user.id) not in [
                query.message.reply_to_message.from_user.id, 0
            ]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\n"
                    f"ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\n"
                    f"ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass

        _, key, offset = query.data.split("#")
        search = FRESH.get(key)
        if not search:
            return await query.answer(
                "❌ Session expired, please search again",
                show_alert=True
            )

        offset = int(offset)

        btn = []
        for i in range(0, len(LANGUAGES) - 1, 2):
            btn.append([
                InlineKeyboardButton(
                    text=LANGUAGES[i].title(),
                    callback_data=f"fl#{LANGUAGES[i].lower()}#{key}#{offset}"
                ),
                InlineKeyboardButton(
                    text=LANGUAGES[i + 1].title(),
                    callback_data=f"fl#{LANGUAGES[i + 1].lower()}#{key}#{offset}"
                ),
            ])

        btn.insert(0, [
            InlineKeyboardButton(
                text="⇊ ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ ⇊",
                callback_data="ident"
            )
        ])

        btn.append([
            InlineKeyboardButton(
                text="⋞ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs",
                callback_data=f"fl#homepage#{key}#0"
            )
        ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        LOGGER.error(f"Error In Old Language Callback - {e}")


# ================= SMART LANGUAGE CALLBACK =================
async def smart_languages_cb(client: Client, query: CallbackQuery):
    try:
        _, key, offset = query.data.split("#")
        offset = int(offset)

        # 🔐 STRICT OWNERSHIP CHECK (ADD HERE)
        owner_id = int(key.split("-")[1])
        if query.from_user.id != owner_id:
            return await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʙᴜᴅᴅʏ !!",
                show_alert=True
			)
        if key not in temp.SMART_FILTERS:
            return await query.answer(
                "❌ Session expired, please search again",
                show_alert=True
            )

        languages = temp.SMART_FILTERS[key].get("languages", [])

        if not languages:
            return await query.answer(
                "❌ No language available",
                show_alert=True
            )

        btn = []
        for i in range(0, len(languages), 2):
            row = [
                InlineKeyboardButton(
                    SMART_LANG_MAP[languages[i]]["label"],
                    callback_data=f"fl#{languages[i]}#{key}#{offset}"
                )
            ]
            if i + 1 < len(languages):
                row.append(
                    InlineKeyboardButton(
                        SMART_LANG_MAP[languages[i + 1]]["label"],
                        callback_data=f"fl#{languages[i + 1]}#{key}#{offset}"
                    )
                )
            btn.append(row)

        btn.insert(0, [
            InlineKeyboardButton(
                text="⇊ ꜱᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ ⇊",
                callback_data="ident"
            )
        ])

        btn.append([
            InlineKeyboardButton(
                text="⋞ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs",
                callback_data=f"fl#homepage#{key}#0"
            )
        ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        LOGGER.error(f"Error In Smart Language Callback - {e}")


# ================= LANGUAGE ROUTER =================
@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_router(client: Client, query: CallbackQuery):
    if SMART_SELECTION_MODE:
        return await smart_languages_cb(client, query)
    return await old_languages_cb(client, query)

@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_language_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, lang, key, _ = query.data.split("#")
        offset = 0

        # 🔐 STRICT OWNERSHIP CHECK (ADD HERE)
        owner_id = int(key.split("-")[1])
        if query.from_user.id != owner_id:
            return await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʙᴜᴅᴅʏ !!",
                show_alert=True
			)

        message = query.message
        chat_id = message.chat.id
        req = query.from_user.id

        # 🔐 Ownership check
        try:
            if int(query.from_user.id) not in [message.reply_to_message.from_user.id, 0]:
                return await query.answer(
                    f"⚠️ Hello {query.from_user.first_name}, this is not your request.",
                    show_alert=True,
                )
        except:
            pass
        # ================= SAVE ACTIVE FILTER STATE =================
        if not hasattr(temp, "ACTIVE_FILTER"):
            temp.ACTIVE_FILTER = {}

        if lang == "homepage":
            temp.ACTIVE_FILTER.pop(key, None)
        else:
            temp.ACTIVE_FILTER[key] = {
                "type": "language",
                "value": lang
			}
        search = FRESH.get(key, "").replace("_", " ")
        BUTTONS[key] = search

        # ================= SMART MODE =================
        if SMART_SELECTION_MODE:
            offset = 0   # ⬅️ IMPORTANT
            all_files = temp.GETALL.get(key, [])

            # 🔁 BACK TO MAIN FILE LIST
            if lang == "homepage":
                files = all_files

                # 🔄 restore pagination state
                state = temp.PAGE_STATE.get(key, {})
                per_page = state.get("per_page", 10)
                total_results = state.get("total_results", len(all_files))
                #offset = state.get("current_offset", 0)

                files = files[offset: offset + per_page]

                if total_results > offset + per_page:
                    n_offset = offset + per_page
                else:
                    n_offset = ""
            # 🔍 FILTER MODE (quality selected)
            else:
                offset = 0
                aliases = SMART_LANG_MAP.get(lang, {}).get("aliases", [])
                # 1️⃣ সব ফাইল থেকে filter করো
                filtered_files = [
                    f for f in all_files
                    if any(alias in (f.file_name or "").lower() for alias in aliases)
				]

                total_results = len(filtered_files)

                settings = await get_settings(chat_id)
                per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)

                # 2️⃣ filter করলে সবসময় first page থেকে শুরু
                offset = 0
                files = filtered_files[:per_page]

                # ⭐⭐⭐ EXACTLY HERE ⭐⭐⭐
                temp.PAGE_STATE[key] = {
                    "total_results": total_results,
                    "per_page": per_page,
                    "current_offset": offset
				}
                # 3️⃣ pagination decide করো
                if total_results > per_page:
                    n_offset = per_page
                else:
                    n_offset = ""   # 👈 এইখানেই "no more page available" trigger হবে   # ❌ no pagination in filter mode
            if not files:
                # 🔁 homepage এ গেলে popup না দেখাও
                if SMART_SELECTION_MODE and lang == "homepage":
                    files = all_files
                else:
                    return await query.answer(
                        "🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                        show_alert=True
					)
            
   # ❌ no pagination in filter mode

            #if not files:
                #return await query.answer(
                    #"🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                    #show_alert=True
                #)

        # ================= OLD MODE =================
        else:
            if lang != "homepage":
                search = f"{search} {lang}"

            files, n_offset, total_results = await get_search_results(
                chat_id,
                search,
                offset=offset,
                filter=True
            )

            if not files:
                return await query.answer(
                    "🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                    show_alert=True
                )


        # ================= BUILD FILE BUTTONS =================
        settings = await get_settings(chat_id)

        btn = [
            [
                InlineKeyboardButton(
                    text=f"{silent_size(f.file_size)} | {extract_tag(f.file_name)} {clean_filename(f.file_name)}",
                    callback_data=f"file#{f.file_id}"
                )
            ]
            for f in files
        ]

        # 🔝 Top filter buttons
        btn.insert(0, [
            InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#0"),
        ])

        # 🔽 Pagination (ONLY old mode OR restored homepage)
        # 🔽 Pagination
        if n_offset != "":
            try:
                per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)

                current_page = (offset // per_page) + 1
                total_pages = math.ceil(total_results / per_page)

                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"),
                    InlineKeyboardButton(
                        text=f"{current_page}/{total_pages}",
                        callback_data="pages"
                    ),
                    InlineKeyboardButton(
                        "ɴᴇxᴛ ⋟",
                        callback_data=f"next_{req}_{key}_{n_offset}"
                    )
                ])
            except:
                pass
        else:
            btn.append([
                InlineKeyboardButton(
                    text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",
                    callback_data="pages"
                )
            ])
        # ================= SEND UPDATE =================
        try:
            if settings.get("button"):
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            else:
                cap = await get_cap(
                    settings,
                    "0",
                    files,
                    query,
                    total_results,
                    search,
                    offset
                )
                await query.message.edit_text(
                    text=cap,
                    reply_markup=InlineKeyboardMarkup(btn),
                    disable_web_page_preview=True,
                    parse_mode=enums.ParseMode.HTML
                )
        except MessageNotModified:
            pass

        await query.answer()

    except Exception as e:
        LOGGER.error(f"Error In Language Filter - {e}")

# ================= OLD SEASON CALLBACK =================
async def old_seasons_cb(client: Client, query: CallbackQuery):
    try:
        try:
            if int(query.from_user.id) not in [
                query.message.reply_to_message.from_user.id, 0
            ]:
                return await query.answer(
                    f"⚠️ ʜᴇʟʟᴏ {query.from_user.first_name},\n"
                    f"ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ,\n"
                    f"ʀᴇǫᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
                    show_alert=True,
                )
        except:
            pass

        _, key, offset = query.data.split("#")
        search = FRESH.get(key)
        search = search.replace(" ", "_")
        offset = int(offset)

        btn = []
        for i in range(0, len(SEASONS) - 1, 2):
            btn.append([
                InlineKeyboardButton(
                    text=SEASONS[i].title(),
                    callback_data=f"fs#{SEASONS[i].lower()}#{key}#{offset}"
                ),
                InlineKeyboardButton(
                    text=SEASONS[i + 1].title(),
                    callback_data=f"fs#{SEASONS[i + 1].lower()}#{key}#{offset}"
                ),
            ])

        btn.insert(0, [
            InlineKeyboardButton(
                text="⇊ ꜱᴇʟᴇᴄᴛ Sᴇᴀsᴏɴ ⇊",
                callback_data="ident"
            )
        ])

        btn.append([
            InlineKeyboardButton(
                text="⋞ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs",
                callback_data=f"fl#homepage#{key}#0"
            )
        ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        LOGGER.error(f"Error In Old Season Callback - {e}")


# ================= SMART SEASON CALLBACK =================
# ================= SMART SEASON CALLBACK =================
async def smart_seasons_cb(client: Client, query: CallbackQuery):
    try:
        _, key, offset = query.data.split("#")
        offset = int(offset)

        # 🔐 STRICT OWNERSHIP CHECK (ADD HERE)
        owner_id = int(key.split("-")[1])
        if query.from_user.id != owner_id:
            return await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʙᴜᴅᴅʏ !!",
                show_alert=True
			)
        if key not in temp.SMART_FILTERS:
            return await query.answer(
                "❌ Session expired, please search again",
                show_alert=True
            )

        data = temp.SMART_FILTERS[key].get("seasons", [])

        if not data:
            return await query.answer(
                "❌ No season available",
                show_alert=True
            )

        btn = []
        for i in range(0, len(data), 2):
            row = [
                InlineKeyboardButton(
                    data[i],
                    callback_data=f"fs#{data[i].lower()}#{key}#{offset}"
                )
            ]
            if i + 1 < len(data):
                row.append(
                    InlineKeyboardButton(
                        data[i + 1],
                        callback_data=f"fs#{data[i + 1].lower()}#{key}#{offset}"
                    )
                )
            btn.append(row)

        btn.insert(0, [
            InlineKeyboardButton(
                "⇊ ꜱᴇʟᴇᴄᴛ Sᴇᴀꜱᴏɴ ⇊",
                callback_data="ident"
            )
        ])

        btn.append([
            InlineKeyboardButton(
                "↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ↭",
                callback_data=f"fl#homepage#{key}#0"
            )
        ])

        await query.edit_message_reply_markup(
            InlineKeyboardMarkup(btn)
        )

    except Exception as e:
        LOGGER.error(f"Error In Smart Season Callback - {e}")


# ================= SEASON ROUTER =================
@Client.on_callback_query(filters.regex(r"^seasons#"))
async def seasons_router(client: Client, query: CallbackQuery):
    if SMART_SELECTION_MODE:
        return await smart_seasons_cb(client, query)
    return await old_seasons_cb(client, query)


@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_season_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, seas, key, _ = query.data.split("#")
        offset = 0

        # 🔐 STRICT OWNERSHIP CHECK (ADD HERE)
        owner_id = int(key.split("-")[1])
        if query.from_user.id != owner_id:
            return await query.answer(
                "🚫 ɴᴏᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ʙᴜᴅᴅʏ !!",
                show_alert=True
			)

        message = query.message
        chat_id = message.chat.id
        req = query.from_user.id

        # 🔐 Ownership check
        try:
            if int(query.from_user.id) not in [
                message.reply_to_message.from_user.id, 0
            ]:
                return await query.answer(
                    f"⚠️ Hello {query.from_user.first_name}, this is not your request.",
                    show_alert=True,
                )
        except:
            pass

        # ================= SAVE ACTIVE FILTER STATE =================
        if not hasattr(temp, "ACTIVE_FILTER"):
            temp.ACTIVE_FILTER = {}

        if seas == "homepage":
            temp.ACTIVE_FILTER.pop(key, None)
        else:
            temp.ACTIVE_FILTER[key] = {
                "type": "season",
                "value": seas
            }
# ============================================================
        search = FRESH.get(key, "").replace("_", " ")
        BUTTONS[key] = search

        # ================= SMART MODE =================
        if SMART_SELECTION_MODE:
            offset = 0   # ⬅️ IMPORTANT
            all_files = temp.GETALL.get(key, [])
            settings = await get_settings(chat_id)
            # 🔁 BACK TO MAIN FILE LIST
            if seas == "homepage":
                files = all_files

                # ✅ restore pagination state
                state = temp.PAGE_STATE.get(key, {})
                per_page = state.get("per_page", 10)
                total_results = state.get("total_results", len(all_files))
                #offset = state.get("current_offset", 0)

                files = files[offset: offset + per_page]

                if total_results > offset + per_page:
                    n_offset = offset + per_page
                else:
                    n_offset = ""
            # 🔍 FILTER MODE (season selected)
            else:
                offset = 0
                filtered_files = [
                    f for f in all_files
                    if seas.lower() in (f.file_name or "").lower()
                ]

                total_results = len(filtered_files)

                per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)

                offset = 0
                files = filtered_files[:per_page]

                temp.PAGE_STATE[key] = {
                    "total_results": total_results,
                    "per_page": per_page,
                    "current_offset": offset
				}
                if total_results > per_page:
                    n_offset = per_page
                else:
                    n_offset = ""   # ❌ no pagination in filter mode

            if not files:
                # 🔁 homepage এ গেলে popup না দেখাও
                if SMART_SELECTION_MODE and seas == "homepage":
                    files = all_files
                else:
                    return await query.answer(
                        "🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                        show_alert=True
		            )

        # ================= OLD MODE =================
        else:
            if seas != "homepage":
                search = f"{search} {seas}"

            files, n_offset, total_results = await get_search_results(
                chat_id,
                search,
                offset=offset,
                filter=True
            )

            if not files:
                return await query.answer(
                    "🚫 ɴᴏ ꜰɪʟᴇꜱ ᴡᴇʀᴇ ꜰᴏᴜɴᴅ 🚫",
                    show_alert=True
                )

        # ================= BUILD RESULT BUTTONS =================
        settings = await get_settings(chat_id)

        btn = [
            [
                InlineKeyboardButton(
                    text=f"{silent_size(f.file_size)} | "
                         f"{extract_tag(f.file_name)} "
                         f"{clean_filename(f.file_name)}",
                    callback_data=f"file#{f.file_id}"
                )
            ]
            for f in files
        ]

        # 🔝 Top filter buttons
        btn.insert(0, [
            InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
            InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
            InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#0"),
        ])

        # 🔽 Pagination handling (ONLY old mode)
        # 🔽 Pagination
        if n_offset != "":
            try:
                per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)

                current_page = (offset // per_page) + 1
                total_pages = math.ceil(total_results / per_page)

                btn.append([
                    InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"),
                    InlineKeyboardButton(
                        text=f"{current_page}/{total_pages}",
                        callback_data="pages"
                    ),
                    InlineKeyboardButton(
                        "ɴᴇxᴛ ⋟",
                        callback_data=f"next_{req}_{key}_{n_offset}"
                    )
                ])
            except:
                pass
        else:
            btn.append([
                InlineKeyboardButton(
                    text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",
                    callback_data="pages"
                )
            ])

        # ================= SEND UPDATE =================
        try:
            if settings.get("button"):
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            else:
                cap = await get_cap(
                    settings,
                    "0",
                    files,
                    query,
                    total_results,
                    search,
                    offset
                )
                await query.message.edit_text(
                    text=cap,
                    reply_markup=InlineKeyboardMarkup(btn),
                    disable_web_page_preview=True,
                    parse_mode=enums.ParseMode.HTML
                )
        except MessageNotModified:
            pass

        await query.answer()

    except Exception as e:
        LOGGER.error(f"Error In Season Filter - {e}")

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movies = await get_poster(id, id=True)
    movie = movies.get('title')
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        reqstr = await bot.get_users(reqstr1)
        if NO_RESULTS_MSG:
            await bot.send_message(chat_id=BIN_CHANNEL,text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie))
        contact_admin_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔰 Cʟɪᴄᴋ Hᴇʀᴇ & Rᴇǫᴜᴇsᴛ Tᴏ Aᴅᴍɪɴ🔰", url=SUPPORT_GRP)]])
        k = await query.message.edit(script.MVE_NT_FND,reply_markup=contact_admin_button)
        await asyncio.sleep(10)
        await k.delete()
                
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    lazyData = query.data
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
    except:
        pass
    if query.data == "close_data":
        await query.message.delete()     
        
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        user = None
        if query.message.reply_to_message and query.message.reply_to_message.from_user:
            user = query.message.reply_to_message.from_user.id
        if user and query.from_user.id != int(user):
            await query.answer(
                script.ALRT_TXT.format(query.from_user.first_name),
                show_alert=True
            )
            return
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")          
                            
    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#") 
        settings = await get_settings(query.message.chat.id)
        try:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{query.message.chat.id}_{key}")
            return
        except UserIsBlocked:
            await query.answer('Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴍᴀʜɴ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            LOGGER.exception("Error in delete callback")
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")
            
    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                LOGGER.error(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")

    elif query.data == "pages":
        await query.answer()    
    
    elif query.data.startswith("killfilesdq"):
        _, keyword = query.data.split("#")

        if query.from_user.id not in ADMINS:
            return await query.answer("❌ Not allowed", show_alert=True)

        await query.answer("⏳ Processing...", show_alert=False)
        try:
            await query.message.edit_text(
                f"<b>Fetching files for: <code>{keyword}</code></b>"
            )
        except MessageNotModified:
            pass

        files, total = await get_bad_files(keyword)

        if not files:
            try:
                return await query.message.edit_text("<b>No files found.</b>")
            except MessageNotModified:
                return

        try:
            await query.message.edit_text(
                f"<b>Found {len(files)} files.\nDeleting in 3 seconds...</b>"
            )
        except MessageNotModified:
            pass

        await asyncio.sleep(3)

        try:
            file_ids = [file.file_id for file in files]

            result1 = await Media.collection.delete_many({"_id": {"$in": file_ids}})
            deleted = result1.deleted_count if result1 else 0

            if MULTIPLE_DB:
                result2 = await Media2.collection.delete_many({"_id": {"$in": file_ids}})
                deleted += result2.deleted_count if result2 else 0

            LOGGER.info(f"Deleted {deleted} files for keyword: {keyword}")

            try:
                await query.message.edit_text(
                    f"<b>✅ Successfully deleted {deleted} files\nfor query: <code>{keyword}</code></b>"
                )
            except MessageNotModified:
                pass

        except Exception as e:
            LOGGER.exception("Error in killfilesdq")
            try:
                await query.message.edit_text(
                    "<b>❌ Error occurred while deleting files.</b>"
                )
            except MessageNotModified:
                pass 

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("• ᴜᴘʟᴏᴀᴅᴇᴅ •", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("• ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"already_available#{from_user}")
             ],[
                InlineKeyboardButton("• ɴᴏᴛ ʀᴇʟᴇᴀꜱᴇᴅ •", callback_data=f"Not_Released#{from_user}"),
                InlineKeyboardButton("• Type Correct Spelling •", callback_data=f"Type_Correct_Spelling#{from_user}")
             ],[
                InlineKeyboardButton("• Not Available In The Hindi •", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
             ]]
        btn2 = [[
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [
            [InlineKeyboardButton("• ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"unalert#{from_user}")]
        ]
        btn2 = [
            [InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
            InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")]
        ]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=f"<b>Hᴇʏ {user.mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️",
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=f"<b>Hᴇʏ {user.mention},</b>\n\n<u>{content}</u> Hᴀs Bᴇᴇɴ Mᴀʀᴋᴇᴅ Aᴅ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ...💔\n\n#Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️\n\n<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>",
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
   
    elif query.data.startswith("Not_Released"):
        ident, from_user = query.data.split("#")
        btn = [[InlineKeyboardButton("📌 Not Released 📌", callback_data=f"nralert#{from_user}")]]
        btn2 = [[
            InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
            InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
        ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention}\n\n"
                        f"<code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ\n\n"
                        f"#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>Hᴇʏ {user.mention}</u>\n\n"
                        f"<b><code>{content}</code>, ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ɴᴏᴛ ʙᴇᴇɴ ʀᴇʟᴇᴀꜱᴇᴅ ʏᴇᴛ\n\n"
                        f"#CᴏᴍɪɴɢSᴏᴏɴ...🕊️✌️\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Type_Correct_Spelling"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("♨️ Type Correct Spelling ♨️", callback_data=f"wsalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Cᴏʀʀᴇᴄᴛ Sᴘᴇʟʟɪɴɢ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention}\n\n"
                        f"Wᴇ Dᴇᴄʟɪɴᴇᴅ Yᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢\n\n"
                        f"#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>Hᴇʏ {user.mention}</u>\n\n"
                        f"<b><code>{content}</code>, Bᴇᴄᴀᴜsᴇ Yᴏᴜʀ Sᴘᴇʟʟɪɴɢ Wᴀs Wʀᴏɴɢ 😢\n\n"
                        f"#Wʀᴏɴɢ_Sᴘᴇʟʟɪɴɢ 😑\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("Not_Available_In_The_Hindi"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton(" Not Available In The Hindi ", callback_data=f"hnalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ Iɴ Hɪɴᴅɪ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention}\n\n"
                        f"Yᴏᴜʀ Rᴇǫᴜᴇsᴛ <code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ\n\n"
                        f"#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>Hᴇʏ {user.mention}</u>\n\n"
                        f"<b><code>{content}</code> ɪs Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ʀɪɢʜᴛ ɴᴏᴡ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ\n\n"
                        f"#Hɪɴᴅɪ_ɴᴏᴛ_ᴀᴠᴀɪʟᴀʙʟᴇ ❌\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴜᴘʟᴏᴀᴅᴇᴅ •", callback_data=f"upalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uᴘʟᴏᴀᴅᴇᴅ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention},\n\n"
                        f"<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.\n"
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Uᴘʟᴏᴀᴅᴇᴅ✅"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<u>{content}</u>\n\n"
                        f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs."
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Uᴘʟᴏᴀᴅᴇᴅ✅\n\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ •", callback_data=f"alalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                 InlineKeyboardButton("ᴠɪᴇᴡ ꜱᴛᴀᴛᴜꜱ", url=f"{query.message.link}")
               ],[
                 InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ʜᴇʀᴇ 🔎", url=GRP_LNK)
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !")
            content = extract_request_content(query.message.text)
            try:
                await client.send_message(
                    chat_id=int(from_user),
                    text=(
                        f"<b>Hᴇʏ {user.mention},\n\n"
                        f"<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\n"
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Aᴠᴀɪʟᴀʙʟᴇ 💗"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
            except UserIsBlocked:
                await client.send_message(
                    chat_id=int(SUPPORT_CHAT_ID),
                    text=(
                        f"<b>Hᴇʏ {user.mention},\n\n"
                        f"<u>{content}</u> Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴏᴜʀ ʙᴏᴛ'ꜱ ᴅᴀᴛᴀʙᴀꜱᴇ.\n"
                        f"Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ɪɴ ᴏᴜʀ Gʀᴏᴜᴘ.</b>\n\n"
                        f"#Aᴠᴀɪʟᴀʙʟᴇ 💗\n"
                        f"<small>Bʟᴏᴄᴋᴇᴅ? Uɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ᴍᴇꜱꜱᴀɢᴇꜱ.</small></i>"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn2)
                )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
            
    
    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ ✅",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Uᴘʟᴏᴀᴅᴇᴅ 🔼",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ɪꜱ Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴇɴᴛ ʀɪɢʜᴛs ᴛᴏ ᴅᴏ ᴛʜɪs ❌", show_alert=True)

    elif query.data.startswith("hnalert"):
        ident, from_user = query.data.split("#")  # Hindi Not Available
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Tʜɪꜱ ɪꜱ Nᴏᴛ Aᴠᴀɪʟᴀʙʟᴇ ɪɴ Hɪɴᴅɪ ❌",
                show_alert=True
            )
        else:
            await query.answer("Nᴏᴛ ᴀʟʟᴏᴡᴇᴅ — ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ʀᴇǫᴜᴇꜱᴛᴇʀ ❌", show_alert=True)

    elif query.data.startswith("nralert"):
        ident, from_user = query.data.split("#")  # Not Released
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Tʜᴇ Mᴏᴠɪᴇ/ꜱʜᴏᴡ ɪꜱ Nᴏᴛ Rᴇʟᴇᴀꜱᴇᴅ Yᴇᴛ 🆕",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴄᴀɴ'ᴛ ᴅᴏ ᴛʜɪꜱ ᴀꜱ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ʀᴇǫᴜᴇꜱᴛᴇʀ ❌", show_alert=True)

    elif query.data.startswith("wsalert"):
        ident, from_user = query.data.split("#")  # Wrong Spelling
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(
                f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇǫᴜᴇꜱᴛ ᴡᴀꜱ ʀᴇᴊᴇᴄᴛᴇᴅ ᴅᴜᴇ ᴛᴏ ᴡʀᴏɴɢ sᴘᴇʟʟɪɴɢ ❗",
                show_alert=True
            )
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇᴇ ᴛʜɪꜱ ❌", show_alert=True)

    
    elif lazyData.startswith("streamfile"):
        _, file_id = lazyData.split(":")
        try:
            user_id = query.from_user.id
            is_premium_user = await db.has_premium_access(user_id)
            if PAID_STREAM and not is_premium_user:
                premiumbtn = [[InlineKeyboardButton("𝖡𝗎𝗒 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 ♻️", callback_data='buy')]]
                await query.answer("<b>📌 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ</b>", show_alert=True)
                await query.message.reply("<b>📌 ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ. ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ ᴀᴄᴄᴇꜱꜱ ᴛʜɪꜱ ꜰᴇᴀᴛᴜʀᴇ ✅</b>", reply_markup=InlineKeyboardMarkup(premiumbtn))
                return
            username =  query.from_user.mention 
            silent_msg = await client.send_cached_media(
                chat_id=BIN_CHANNEL,
                file_id=file_id,
            )
            fileName = {quote_plus(get_name(silent_msg))}
            silent_stream = f"{URL}watch/{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            silent_download = f"{URL}{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            btn= [[
                InlineKeyboardButton("𝖲𝗍𝗋𝖾𝖺𝗆", url=silent_stream),
                InlineKeyboardButton("𝖣𝗈𝗐𝗇𝗅𝗈𝖺𝖽", url=silent_download)        
	    ]]
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
	    )
            await silent_msg.reply_text(
                text=f"•• ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ꜰᴏʀ ɪᴅ #{user_id} \n•• ᴜꜱᴇʀɴᴀᴍᴇ : {username} \n\n•• ᖴᎥᒪᗴ Nᗩᗰᗴ : {fileName}",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(btn)
	    )                
        except Exception as e:
            LOGGER.error(e)
            await query.answer(f"⚠️ SOMETHING WENT WRONG \n\n{e}", show_alert=True)
            return
           
    
    elif query.data == "pagesn1":
        await query.answer(text=script.PAGE_TXT, show_alert=True)

    elif query.data == "start":
        await query.answer()
        buttons = get_main_buttons()

        current_time = datetime.now(pytz.timezone(TIMEZONE))
        hour = current_time.hour

        if hour < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ"
        elif hour < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ"
        elif hour < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ"

        try:
            await query.edit_message_media(
                InputMediaPhoto(
                    media=random.choice(PICS),
                    caption=script.START_TXT.format(
                        user=query.from_user.mention,
                        greet=gtxt
                    ),
                    parse_mode=enums.ParseMode.HTML
                )
            )
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except:
            await query.edit_message_text(
                text=script.START_TXT.format(
                    user=query.from_user.mention,
                    greet=gtxt
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
			)
  
    elif query.data == "give_trial":
        try:
            user_id = query.from_user.id
            has_free_trial = await db.check_trial_status(user_id)
            if has_free_trial:
                await query.answer("🚸 ʏᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ᴛʀɪᴀʟ ᴏɴᴄᴇ !\n\n📌 ᴄʜᴇᴄᴋᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ ʙʏ : /plan", show_alert=True)
                return
            else:            
                await db.give_free_trial(user_id)
                await query.message.reply_text(
                    text="<b>🥳 ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴꜱ\n\n🎉 ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ <u>5 ᴍɪɴᴜᴛᴇs</u> ꜰʀᴏᴍ ɴᴏᴡ !</b>",
                    quote=False,
                    disable_web_page_preview=True,                  
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💸", callback_data='seeplans')]]))
                return    
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "free":
        await query.answer()
        buttons = [[
            InlineKeyboardButton('⚜️ ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ꜰʀᴇᴇ ᴛʀɪᴀʟ', callback_data="give_trial")
        ],[
            InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='other'),
            InlineKeyboardButton('7 / 7', callback_data='pagesn1'),
            InlineKeyboardButton('ɴᴇxᴛ ⋟', callback_data='bronze')
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='premium')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FREE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "premium":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton("Rᴇғғᴇʀ Tᴏ Gᴇᴛ Pʀᴇᴍɪᴜᴍ", callback_data="reffff")
            ],
            [
                InlineKeyboardButton("Bʀᴏɴᴢᴇ", callback_data="bronze"),
                InlineKeyboardButton("Sɪʟᴠᴇʀ", callback_data="silver")
            ],
            [
                InlineKeyboardButton("Gᴏʟᴅ", callback_data="gold"),
                InlineKeyboardButton("Pʟᴀᴛɪɴᴜᴍ", callback_data="platinum")
            ],
            [
                InlineKeyboardButton("Dɪᴀᴍᴏɴᴅ", callback_data="diamond"),
                InlineKeyboardButton("Oᴛʜᴇʀ", callback_data="other")
            ],
            [
                InlineKeyboardButton("Gᴇᴛ A Free Tʀɪᴀʟ Fᴏʀ 5 Mɪɴᴜᴛᴇs 🫣", callback_data="free")
            ],
            [
                InlineKeyboardButton("⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋", callback_data="home")
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media=random.choice(PICS),
                caption=script.BPREMIUM_TXT,
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "bronze":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton("🔐 Click here to buy premium", callback_data="buy")
            ],
            [
                InlineKeyboardButton("⋞ Back", callback_data="free"),
                InlineKeyboardButton("1 / 7", callback_data="pagesn1"),
                InlineKeyboardButton("Next ⋟", callback_data="silver")
            ],
            [
                InlineKeyboardButton("⇋ Back ⇋", callback_data="premium")
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media="https://graph.org/file/670f6df9f755dc2c9a00a.jpg",
                caption=script.BRONZE_TXT.format(query.from_user.mention),
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "silver":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton("🔐 Click here to buy premium", callback_data="buy")
            ],
            [
                InlineKeyboardButton("⋞ Back", callback_data="bronze"),
                InlineKeyboardButton("2 / 7", callback_data="pagesn1"),
                InlineKeyboardButton("Next ⋟", callback_data="gold")
            ],
            [
                InlineKeyboardButton("⇋ Back ⇋", callback_data="premium")
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media="https://graph.org/file/670f6df9f755dc2c9a00a.jpg",
                caption=script.SILVER_TXT.format(query.from_user.mention),
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "gold":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton("🔐 Click here to buy premium", callback_data="buy")
            ],
            [
                InlineKeyboardButton("⋞ Back", callback_data="silver"),
                InlineKeyboardButton("3 / 7", callback_data="pagesn1"),
                InlineKeyboardButton("Next ⋟", callback_data="platinum")
            ],
            [
                InlineKeyboardButton("⇋ Back ⇋", callback_data="premium")
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media="https://graph.org/file/670f6df9f755dc2c9a00a.jpg",
                caption=script.GOLD_TXT.format(query.from_user.mention),
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "platinum":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton(
                    "🔐 Click here to buy premium",
                    callback_data="buy"
                )
            ],
            [
                InlineKeyboardButton(
                    "⋞ Back",
                    callback_data="gold"
                ),
                InlineKeyboardButton(
                    "4 / 7",
                    callback_data="pagesn1"
                ),
                InlineKeyboardButton(
                    "Next ⋟",
                    callback_data="diamond"
                )
            ],
            [
                InlineKeyboardButton(
                    "⇋ Back ⇋",
                    callback_data="premium"
                )
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media="https://graph.org/file/670f6df9f755dc2c9a00a.jpg",
                caption=script.PLATINUM_TXT.format(
                    query.from_user.mention
                ),
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "diamond":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton("🔐 Click here to buy premium", callback_data="buy")
            ],
            [
                InlineKeyboardButton("⋞ Back", callback_data="platinum"),
                InlineKeyboardButton("5 / 7", callback_data="pagesn1"),
                InlineKeyboardButton("Next ⋟", callback_data="other")
            ],
            [
                InlineKeyboardButton("⇋ Back ⇋", callback_data="premium")
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media="https://graph.org/file/670f6df9f755dc2c9a00a.jpg",
                caption=script.DIAMOND_TXT.format(query.from_user.mention),
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
	    )

    elif query.data == "other":
        await query.answer()

        buttons = [
            [
                InlineKeyboardButton("☎️ Contact Owner", url=OWNER_LNK)
            ],
            [
                InlineKeyboardButton("⋞ Back", callback_data="diamond"),
                InlineKeyboardButton("6 / 7", callback_data="pagesn1"),
                InlineKeyboardButton("Next ⋟", callback_data="free")
            ],
            [
                InlineKeyboardButton("⇋ Back ⇋", callback_data="premium")
            ]
        ]

        await query.message.edit_media(
            InputMediaPhoto(
                media="https://graph.org/file/670f6df9f755dc2c9a00a.jpg",
                caption=script.OTHER_TXT.format(query.from_user.mention),
                parse_mode=enums.ParseMode.HTML
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif query.data == "buy":
        try:
            btn = [[InlineKeyboardButton('🌟 ᴘᴀʏ ᴠɪᴀ ᴛᴇʟᴇɢʀᴀᴍ sᴛᴀʀ 🌟', callback_data='star')],[InlineKeyboardButton('💸 ᴘᴀʏ ᴠɪᴀ ᴜᴘɪ/ǫʀ ᴄᴏᴅᴇ 💸', callback_data='upi')],[InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='premium')]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(SUBSCRIPTION)
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "upi":
        try:
            btn = [[ 
                InlineKeyboardButton('📱 ꜱᴇɴᴅ  ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ', url=OWNER_LNK),
            ],[
                InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='buy')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(SUBSCRIPTION)
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_UPI_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "star":
        try:
            btn = [
                InlineKeyboardButton(f"{stars}⭐", callback_data=f"buy_{stars}")
                for stars, days in STAR_PREMIUM_PLANS.items()
            ]
            buttons = [btn[i:i + 2] for i in range(0, len(btn), 2)]
            buttons.append([InlineKeyboardButton("⋞ ʙᴀᴄᴋ", callback_data="buy")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_STAR_TEXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
	    )
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "earn":
        try:
            btn = [[ 
                InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=script.EARN_INFO.format(temp.B_LINK),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)
                    
    elif query.data == "me":
        buttons = [[
            InlineKeyboardButton ('❤️‍🔥 Sᴏᴜʀᴄᴇ', callback_data='source'),
        ],[
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ᴛᴏ ʜᴏᴍᴇ ⇋', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('☠︎︎ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ ☠︎︎', url='https://t.me/Graduate_Movies'),
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='me')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "ref_point":
        await query.answer(f'You Have: {referdb.get_refer_points(query.from_user.id)} Refferal points.', show_alert=True)
    
    
    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="start")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
            )
			
        
async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    # ================= SMART MODE INIT =================
    if SMART_SELECTION_MODE:
        if not hasattr(temp, "SMART_FILTERS"):
            temp.SMART_FILTERS = {}
    # ==================================================
    if not spoll:
        message = msg
        if message.text.startswith("/"): return
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = await replace_words(message.text)		
            search = search.lower()
            search = search.replace("-", " ")
            search = search.replace(":","")
            search = search.replace("'","")
            search = re.sub(r'\s+', ' ', search).strip()
            m=await message.reply_text(f'<b>Wait {message.from_user.mention} Searching Your Query: <i>{search}...</i></b>', reply_to_message_id=message.id)
            files, offset, total_results = await get_search_results(message.chat.id ,search, offset=0, filter=True)
            uid = message.from_user.id if message.from_user else 0
            key = f"{message.chat.id}-{uid}"
            settings = await get_settings(message.chat.id)

            if not hasattr(temp, "PAGE_STATE"):
                temp.PAGE_STATE = {}

            per_page = 10 if settings.get("max_btn") else int(MAX_B_TN)

            temp.PAGE_STATE[key] = {
                "total_results": total_results,
                "per_page": per_page,
                "current_offset": 0,
			} # normally 0
            # ================= SMART MODE DETECTION =================
            # ================= SMART MODE: COLLECT ALL FILES =================
            if SMART_SELECTION_MODE:
                smart_languages = set()
                smart_seasons = set()
                smart_qualities = set()

                # 🔹 start with first page files
                all_files = list(files)

                # 🔹 collect remaining pages
                next_offset = offset
                while next_offset:
                    more_files, next_offset, _ = await get_search_results(
                        message.chat.id,
                        search,
                        offset=next_offset,
                        filter=True
                    )
                    if not more_files:
                        break
                    all_files.extend(more_files)

                # 🔹 analyze ALL files (not only 1st page)
                for file in all_files:
                    name = (file.file_name or "").lower()

                    # 🔤 Language detection
                    for lang_key, data in SMART_LANG_MAP.items():
                        for alias in data["aliases"]:
                            if re.search(rf"(^|[.\s_-]){alias}([.\s_-]|$)", name):
                                smart_languages.add(lang_key)
                                break

                    # 📺 Season detection
                    for pattern in SMART_SEASON_REGEX:
                        match = re.search(pattern, name)
                        if match:
                            num = re.search(r"\d{1,2}", match.group())
                            if num:
                                smart_seasons.add(f"S{int(num.group()):02d}")
                            break

                    # 🎞 Quality detection
                    q = re.search(SMART_QUALITY_REGEX, name)
                    if q:
                        smart_qualities.add(q.group())


                # 🔹 store EVERYTHING for smart filters
                temp.GETALL[key] = all_files
                temp.SMART_FILTERS[key] = {
                    "languages": sorted(smart_languages),
                    "seasons": sorted(smart_seasons),
                    "qualities": sorted(smart_qualities)
				    }
            # ========================================================
            if not files:
                if settings["spell_check"]:
                    ai_sts = await m.edit('🤖 ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ, ᴀɪ ɪꜱ ᴄʜᴇᴄᴋɪɴɢ ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ...')
                    is_misspelled = await ai_spell_check(chat_id = message.chat.id,wrong_name=search)
                    if is_misspelled:
                        await ai_sts.edit(f'<b>✅Aɪ Sᴜɢɢᴇsᴛᴇᴅ ᴍᴇ<code> {is_misspelled}</code> \nSᴏ Iᴍ Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ <code>{is_misspelled}</code></b>')
                        await asyncio.sleep(2)
                        message.text = is_misspelled
                        await ai_sts.delete()
                        return await auto_filter(client, message)
                    await ai_sts.delete()
                    return await advantage_spell_chok(client, message)
        else:
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
        m=await message.reply_text(f'<b>Wᴀɪᴛ {message.from_user.mention} Sᴇᴀʀᴄʜɪɴɢ Yᴏᴜʀ Qᴜᴇʀʏ :<i>{search}...</i></b>', reply_to_message_id=message.id)
        settings = await get_settings(message.chat.id)
        await msg.message.delete()
    key = f"{message.chat.id}-{message.from_user.id}"
    FRESH[key] = search
    if SMART_SELECTION_MODE:
        # already stored full result earlier, do nothing
        pass
    else:
        temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    if settings.get('button'):
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}", callback_data=f'file#{file.file_id}'
                ),
            ]
            for file in files
        ]
        btn.insert(0, 
            [
                InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
            ]
        )
        
    else:
        btn = []
        btn.insert(0, 
            [
                InlineKeyboardButton("ᴘɪxᴇʟ", callback_data=f"qualities#{key}#0"),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#0"),
                InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ",  callback_data=f"seasons#{key}#0")
            ]
        )
        
    if offset != "":
        req = message.from_user.id if message.from_user else 0
        try:
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', True)
            btn.append(
                [InlineKeyboardButton("ᴘᴀɢᴇ", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ ⋟",callback_data=f"next_{req}_{key}_{offset}")]
            )
    else:
        btn.append(
            [InlineKeyboardButton(text="↭ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ↭",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    DELETE_TIME = settings.get("auto_del_time", AUTO_DELETE_TIME)
    TEMPLATE = script.IMDB_TEMPLATE_TXT    
    poster_url = None
    if imdb:
        poster_url = imdb.get('poster')

        if not poster_url:
            tmdb_data = await fetch_tmdb_data(search, imdb.get('year'))

            if tmdb_data:
                poster_url = await get_best_visual(tmdb_data)
    if imdb:
        cap = TEMPLATE.format(
            qurey=search,
            #qurey=search,
            title=imdb.get("title", "N/A"),
            votes=imdb.get("votes") or imdb.get("vote_count") or "N/A",
            aka=imdb.get("aka", "N/A"),
            seasons=imdb.get("seasons", "N/A"),
            box_office=imdb.get("box_office", "N/A"),
            localized_title=imdb.get("localized_title", "N/A"),
            kind=imdb.get("kind", "N/A"),
            imdb_id=imdb.get("imdb_id", "N/A"),
            cast=imdb.get("cast", "N/A"),
            runtime=imdb.get("runtime", "N/A"),
            countries=imdb.get("countries", "N/A"),
            certificates=imdb.get("certificates", "N/A"),
            languages=imdb.get("languages", "N/A"),
            director=imdb.get("director", "N/A"),
            writer=imdb.get("writer", "N/A"),
            producer=imdb.get("producer", "N/A"),
            composer=imdb.get("composer", "N/A"),
            cinematographer=imdb.get("cinematographer", "N/A"),
            music_team=imdb.get("music_team", "N/A"),
            distributors=imdb.get("distributors", "N/A"),
            release_date=imdb.get("release_date", "N/A"),
            year=imdb.get("year", "N/A"),
            genres=imdb.get("genres", "N/A"),
            poster=poster_url,
            plot=imdb.get("plot", "N/A"),
            rating=imdb.get("rating", "N/A"),
            url=imdb.get("url", "N/A"),
            **locals()
        )
        temp.IMDB_CAP[message.from_user.id] = cap
        if not settings.get('button'):
            for file_num, file in enumerate(files, start=1):
                cap += f"\n\n<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}</a></b>"
    else:
        if settings.get('button'):
            cap = f"<b><blockquote>Hᴇʏ,{message.from_user.mention}</blockquote>\n\n📂 Hᴇʀᴇ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"
        else:
            cap = f"<b><blockquote>Hᴇʏ,{message.from_user.mention}</blockquote>\n\n📂 Hᴇʀᴇ I Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Sᴇᴀʀᴄʜ <code>{search}</code></b>\n\n"            
            for file_num, file in enumerate(files, start=1):
                cap += f"<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}\n\n</a></b>"                
    try:
        if imdb and (poster_url or imdb.get("poster")):
            try:
                imdb_poster = imdb.get("poster") if imdb else None
                final_poster = imdb_poster or poster_url
                hehe = await message.reply_photo(
                    photo=final_poster,
                    caption=cap, 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                await m.delete()
                if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await hehe.delete()
                    await message.delete()
            except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                pic = imdb.get('poster')
                if pic:
                    poster = pic.replace('.jpg', "._V1_UX360.jpg")
                    hmm = await message.reply_photo(
                        photo=poster, 
                        caption=cap, 
                        reply_markup=InlineKeyboardMarkup(btn), 
                        parse_mode=enums.ParseMode.HTML
                    )
                    await m.delete()
                    if settings['auto_delete']:
                        await asyncio.sleep(DELETE_TIME)
                        await hmm.delete()
                        await message.delete()
                else:
                    fek = await m.edit_text(
                        text=cap, 
                        reply_markup=InlineKeyboardMarkup(btn), 
                        parse_mode=enums.ParseMode.HTML
                    )
                    if settings['auto_delete']:
                        await asyncio.sleep(DELETE_TIME)
                        await fek.delete()
                        await message.delete()
            except Exception as e:
                LOGGER.error(e)
                fek = await m.edit_text(
                    text=cap, 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await fek.delete()
                    await message.delete()
        else:
            fuk = await m.edit_text(
                text=cap, 
                reply_markup=InlineKeyboardMarkup(btn), 
                disable_web_page_preview=True, 
                parse_mode=enums.ParseMode.HTML
            )
            if settings['auto_delete']:
                await asyncio.sleep(DELETE_TIME)
                await fuk.delete()
                await message.delete()
    except KeyError:
        await save_group_settings(message.chat.id, 'auto_delete', True)
        pass
		
async def ai_spell_check(chat_id, wrong_name):
    if re.search(r'\bS\d{1,2}\b|\bSeason\s*\d+', wrong_name, re.I):
        return None
    async def search_movie(wrong_name):
        search_results = imdb.search_movie(wrong_name)
        movie_list = [movie.title for movie in search_results.titles]
        return movie_list
    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return 
        movie = closest_match[0]
        result = await get_search_results(chat_id=chat_id, query=movie)

        # 🔒 SAFETY GUARD (MOST IMPORTANT)
        if not result or len(result) != 3:
            movie_list.remove(movie)
            continue

        files, offset, total_results = result

        if files:
            return movie

        movie_list.remove(movie)

    return None
async def advantage_spell_chok(client, message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(search, bulk=True)
    except:
        k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    if not movies:
        google = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 Cʜᴇᴄᴋ Sᴘᴇʟʟɪɴɢ Oɴ Gᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")
        ]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[
        InlineKeyboardButton(text=movie.title, callback_data=f"spol#{movie.imdb_id}#{user}")
    ]
        for movie in movies
    ]
    buttons.append(
        [InlineKeyboardButton(text="🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data')]
    )
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(60)
    await d.delete()
    try:
        await message.delete()
    except:
        pass
