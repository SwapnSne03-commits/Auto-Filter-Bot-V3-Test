import os
import asyncio
import tempfile
import aiofiles
import pycountry   # ✅ NEW (only addition)
import time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegraph import Telegraph
from pymediainfo import MediaInfo


telegraph = Telegraph()
telegraph.create_account(short_name="FileInfoBot")

# ======================================
# 🔥 click cooldown cache
# user_id : last_click_time
# ======================================
CLICK_CACHE = {}
COOLDOWN = 20  # seconds

# ======================================
# 🔥 language formatter (fast + safe)
# ======================================


LOCAL_NAMES = {
    "Bengali": "বাংলা",
    "Bangla": "বাংলা",
    "Hindi": "हिन्दी",
    "Tamil": "தமிழ்",
    "Telugu": "తెలుగు",
    "Punjabi": "ਪੰਜਾਬੀ",
    "Panjabi": "ਪੰਜਾਬੀ",
    "Malayalam": "മലയാളം",
    "Kannada": "ಕನ್ನಡ",
    "Urdu": "اردو",
    "Arabic": "العربية",
    "Chinese": "中文",
    "Japanese": "日本語",
    "Korean": "한국어",
    "Thai": "ไทย"
}


def fmt(code):
    if not code:
        return "Unknown"

    code = str(code).lower()

    try:
        lang = (
            pycountry.languages.get(alpha_2=code)
            or pycountry.languages.get(alpha_3=code)
        )

        if not lang:
            return code.upper()

        name = lang.name.replace(" (macrolanguage)", "").replace(" (Macrolanguage)", "")
        local = LOCAL_NAMES.get(name)

        if local:
            return f"{name} ({local})"

        return name

    except:
        return code.upper()

# ======================================
# CALLBACK (unchanged logic)
# ======================================
@Client.on_callback_query(filters.regex("^trackinfo$"))
async def telegraph_file_info(client, query):

    now = time.time()
    uid = query.from_user.id

    last = CLICK_CACHE.get(uid, 0)

    # 🔥 cooldown check
    if now - last < COOLDOWN:
        return await query.answer("⏳ ʜᴏʟᴅ ᴏɴ, ɪ'ᴍ ᴀʟʀᴇᴀᴅʏ sᴄᴀɴɴɪɴɢ...", show_alert=False)

    CLICK_CACHE[uid] = now
    if len(CLICK_CACHE) > 1000:
        CLICK_CACHE.clear()

    await query.answer("🔍 sᴄᴀɴɴɪɴɢ ʏᴏᴜʀ ғɪʟᴇ, ᴘʟᴢ ᴡᴀɪᴛ...")

    tmp = os.path.join(tempfile.gettempdir(), f"info_{query.id}.tmp")

    try:
        # 🔥 only few MB download (VERY FAST)
        async with aiofiles.open(tmp, "wb") as f:
            file_msg = query.message.reply_to_message or query.message

            async for chunk in client.stream_media(file_msg, limit=4):
                await f.write(chunk)

        media = await asyncio.to_thread(MediaInfo.parse, tmp)

        audios = []
        subs = []
        video = []

        for t in media.tracks:

            if t.track_type == "Video":
                vcodec = t.format or ""
                vres = f"{t.width}x{t.height}" if t.width and t.height else ""
                vbit = f"{int(t.bit_rate)//1000}kbps" if t.bit_rate else ""

                video_label = " ".join(filter(None, [vcodec, vres, vbit]))
                video.append(video_label)

            elif t.track_type == "Audio":

                lang = fmt(t.language)

                #codec = t.format or ""
                codec = (t.format or "").replace("E-AC-3", "DDP").replace("AC-3", "DD")
                channels = t.channel_s or t.channels or ""
                bitrate = ""

                # 🔹 Channel formatting
                if channels:
                    try:
                        ch = float(channels)
                        if ch == 6:
                            channels = "5.1"
                        elif ch == 2:
                            channels = "2.0"
                        else:
                            channels = str(channels)
                    except:
                        pass

                # 🔹 Bitrate formatting
                if t.bit_rate:
                    try:
                        kbps = int(t.bit_rate) // 1000
                        bitrate = f"{kbps}kbps"
                    except:
                        pass

                # 🔹 Build label safely
                label = lang

                details = []

                if codec:
                    if channels:
                        details.append(f"{codec}{channels}")
                    else:
                        details.append(codec)

                if bitrate:
                    details.append(bitrate)

                if details:
                    label = f"{lang} ~ {' - '.join(details)}"

                audios.append(label)   # ✅ only change

            elif t.track_type in ("Text", "Subtitle"):
                subs.append(fmt(t.language))     # ✅ only change


        # =================================
        # TELEGRAPH PAGE BUILD (same UI)
        # =================================
        html = "🔻 <b>All Tracks Details</b><hr><br> 🔻"

        if video:
            html += "🎬 <u><b>Video Track</b></u>"
            for v in video:
                html += f"<blockquote>• <code>{v}</code></blockquote>"

        if audios:
            html += f"<br>🔊 <u><b>Audio Tracks ({len(audios)})</b></u>"
            for a in dict.fromkeys(audios):
                html += f"<blockquote>• <code>{a}</code></blockquote>"

        if subs:
            html += f"<br>💬 <u><b>Subtitle Tracks ({len(subs)})</b></u>"
            for s in dict.fromkeys(subs):
                html += f"<blockquote>• <code>{s}</code></blockquote>"

            html += """
            <br>
            <i>
            🔺 Provided By
            <b><a href="https://t.me/Graduate_Movies">Graduate Movies</a></b> 🔺
            </i>
            """
        page = telegraph.create_page(
            title="File Information",
            html_content=html
        )

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴠɪᴇᴡ ғɪʟᴇ ᴅᴇᴛᴀɪʟs 📑", url=page["url"])]
            ])
        )

    except Exception:
        await query.answer("❌ Failed to read info", show_alert=True)

    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
