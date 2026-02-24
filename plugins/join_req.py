from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS
from plugins.settings import *

@Client.on_chat_join_request()
async def join_reqs(client, message: ChatJoinRequest):

    try:
        channel_id = message.chat.id
        user_id = message.from_user.id

        # 🔹 Prevent duplicate insert
        if not await db.find_join_req(user_id, channel_id):
            await db.add_join_req(user_id, channel_id)

    except Exception as e:
        LOGGER.error(f"Join Req Error: {e}")

@Client.on_message(filters.command("cleanfsub") & filters.private & filters.user(ADMINS))
async def clean_force_sub_db(client, message):

    deleted = await db.del_join_req()

    await message.reply(
        f"✅ Force Sub Request DB Cleaned Successfully.\n\n"
        f"🧹 Total Records Removed: {deleted}"
    )

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):

    deleted = await db.del_join_req()

    await message.reply(
        f"⚙ Force Sub DB Cleaned Successfully.\n\n"
        f"🧹 Total Records Removed: {deleted}"
    )
