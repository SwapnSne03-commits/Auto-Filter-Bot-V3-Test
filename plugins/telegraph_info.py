import os
import asyncio
import tempfile
import aiofiles
import pycountry
import time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegraph import Telegraph
from pymediainfo import MediaInfo


# ======================================
# Telegraph init
# ======================================
telegraph = Telegraph()
telegraph.create_account(short_name="FileInfoBot")


# ======================================
# 🔥 click cooldown cache
# ======================================
CLICK_CACHE = {}
COOLDOWN = 20  # seconds


# ======================================
# 🔥 language local names
# ======================================
LOCAL_NAMES = {
    "Bengali": "বাংলা",
    "Hindi": "हिन्दी",
    "Tamil": "தமிழ்",
    "Telugu": "తెలుగు",
    "Punjabi": "ਪੰਜਾਬੀ",
    "Malayalam": "മലയാളം",
    "Kannada": "ಕನ್ನಡ",
    "Urdu": "اردو",
    "Arabic": "العربية",
    "Chinese": "中文",
    "Japanese": "日本語",
    "Korean": "한국어",
    "Thai": "ไทย"
}


# ======================================
# 🔥 language formatter (fast + safe)
# ======================================
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

        # remove (macrolanguage)
        name = lang.name.replace(" (macrolanguage)", "").replace(" (Macrolanguage)", "")

        local = LOCAL_NAMES.get(name)

        if local:
            return f"{name} ({local})"

        return name

    except:
        return code.upper()


# ======================================
# 🔥 CALLBACK
# ======================================
@Client.on_callback_query(filters.regex("^trackinfo$"))
async def telegraph_file_info(client, query):

    now = time.time()
    uid = query.from_user.id

    last = CLICK_CACHE.get(uid, 0)

    # =========================
    # cooldown protection
    # =========================
    if now - last < COOLDOWN:
        return await query.answer("⏳ Please wait few seconds...", show_alert=False)

    CLICK_CACHE[uid] = now

    # prevent memory grow
    if len(CLICK_CACHE) > 1000:
        CLICK_CACHE.clear()

    await query.answer("🔍 Scanning file...")

    tmp = os.path.join(tempfile.gettempdir(), f"info_{query.id}.tmp")

    try:
        # =================================
        # 🔥 partial stream download (FAST)
        # =================================
        async with aiofiles.open(tmp, "wb") as f:
            async for chunk in client.stream_media(query.message, limit=4):
                await f.write(chunk)

        media = await asyncio.to_thread(MediaInfo.parse, tmp)

        audios = []
        subs = []
        video = []

        for t in media.tracks:

            if t.track_type == "Video":
                video.append(f"{t.format} {t.width}x{t.height}")

            elif t.track_type == "Audio":
                audios.append(fmt(t.language))

            elif t.track_type in ("Text", "Subtitle"):
                subs.append(fmt(t.language))


        # remove duplicate but keep order
        audios = list(dict.fromkeys(audios))
        subs = list(dict.fromkeys(subs))


        # =================================
        # TELEGRAPH PAGE BUILD (clean UI)
        # =================================
        html = "<h2>📊 <b>File Tracks Information</b></h2><br>"

        # Video
        if video:
            html += "<h3>🎬 <u><b>Video Track</b></u></h3>"
            for v in video:
                html += f"<blockquote>• <code>{v}</code></blockquote>"

        # Audio
        html += f"<br><h3>🔊 <u><b>Audio Tracks ({len(audios)})</b></u></h3>"
        if audios:
            for a in audios:
                html += f"<blockquote>• <code>{a}</code></blockquote>"
        else:
            html += "<blockquote>• None</blockquote>"

        # Subtitles
        html += f"<br><h3>💬 <u><b>Subtitle Tracks ({len(subs)})</b></u></h3>"
        if subs:
            for s in subs:
                html += f"<blockquote>• <code>{s}</code></blockquote>"
        else:
            html += "<blockquote>• None</blockquote>"


        page = telegraph.create_page(
            title="File Info",
            html_content=html
        )


        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View File Info", url=page["url"])]
            ])
        )

    except Exception:
        await query.answer("❌ Failed to read info", show_alert=True)

    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
