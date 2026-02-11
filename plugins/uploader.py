import os
import asyncio
import tempfile
import requests
from PIL import Image

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegraph import Telegraph
from info import IMGBB_API_KEY, LOG_CHANNEL


MAX_SIZE = 5 * 1024 * 1024
MAX_BATCH = 10

telegraph = Telegraph()
telegraph.create_account(short_name="SilentXBot")


# =================================
# 🔹 compress image
# =================================
def compress_image(path):
    if os.path.getsize(path) <= MAX_SIZE:
        return path

    img = Image.open(path)
    new_path = path + "_cmp.jpg"
    img.save(new_path, "JPEG", quality=65, optimize=True)
    return new_path


# =================================
# 🔹 progress
# =================================
async def progress(msg, text):
    try:
        await msg.edit_text(text)
    except:
        pass


# =================================
# 🔹 collect photos only
# =================================
async def collect_media(client, message):

    ask = await message.reply_text(
        f"📤 **𝙎𝙚𝙣𝙙 𝙥𝙝𝙤𝙩𝙤𝙨 (max {MAX_BATCH})**\n🛑 /done 𝙬𝙝𝙚𝙣 𝙛𝙞𝙣𝙞𝙨𝙝𝙚𝙙"
    )

    paths = []

    while len(paths) < MAX_BATCH:
        try:
            reply = await client.listen(
                chat_id=message.chat.id,
                filters=filters.photo | filters.command("done"),
                timeout=120
            )
        except asyncio.TimeoutError:
            break

        if reply.text and reply.text.lower() == "/done":
            break

        if not reply.photo:
            continue

        path = os.path.join(tempfile.gettempdir(), f"{reply.id}.jpg")
        await reply.download(path)
        path = compress_image(path)

        paths.append(path)

        await progress(ask, f"✅ 𝘼𝙙𝙙𝙚𝙙 {len(paths)} 𝙞𝙢𝙖𝙜𝙚(s)")

    return paths, ask


# =================================
# 🔹 hosts
# =================================
def upload_imgbb(path):
    if not IMGBB_API_KEY:
        return None

    with open(path, "rb") as f:
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY},
            files={"image": f},
            timeout=30
        ).json()

    return r["data"]["url"]


def upload_catbox(path):
    with open(path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
            timeout=30
        )
    return r.text.strip()


def upload_telegraph(path):
    with open(path, "rb") as f:
        r = telegraph.upload_file(f)
    return f"https://telegra.ph{r[0]}"


# =================================
# 🔥 smart fallback (BEST ORDER)
# =================================
async def smart_upload(path):

    for func in [upload_imgbb, upload_catbox, upload_telegraph]:
        try:
            url = await asyncio.to_thread(func, path)
            if url:
                return url
        except:
            continue

    return None


# =================================
# 🔥 MAIN COMMAND
# =================================
@Client.on_message(filters.command("upload") & filters.private)
async def smart_uploader(client, message):

    paths, ask = await collect_media(client, message)

    if not paths:
        return await ask.edit_text("❌ 𝙉𝙤 𝙞𝙢𝙖𝙜𝙚𝙨 𝙧𝙚𝙘𝙚𝙞𝙫𝙚𝙙")

    links = []

    for i, path in enumerate(paths, start=1):

        await progress(ask, f"⬆️ 𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 {i}/{len(paths)} ...")

        try:
            url = await smart_upload(path)
            if url:
                links.append(url)
        finally:
            if os.path.exists(path):
                os.remove(path)

    if not links:
        return await ask.edit_text("❌ 𝙐𝙥𝙡𝙤𝙖𝙙 𝙛𝙖𝙞𝙡𝙚𝙙 𝙤𝙣 𝙖𝙡𝙡 𝙝𝙤𝙨𝙩𝙨")

    # =================================
    # 🔹 LOG CHANNEL
    # =================================
    try:
        log_text = (
            f"🖼 **Image Upload Log**\n\n"
            f"👤 User : {message.from_user.mention}\n"
            f"🆔 ID : `{message.from_user.id}`\n"
            f"📦 Files : {len(links)}\n\n" +
            "\n".join(links)
        )

        await client.send_message(LOG_CHANNEL, log_text, disable_web_page_preview=True)
    except:
        pass

    # =================================
    # 🔹 USER MESSAGE
    # =================================
    await ask.edit_text(
        "✅ **𝙐𝙥𝙡𝙤𝙖𝙙 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!** 🎉\n\n" + "\n".join(links),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 𝙊𝙥𝙚𝙣 𝙁𝙞𝙧𝙨𝙩", url=links[0])]
        ])
        )
