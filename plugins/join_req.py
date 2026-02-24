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

        groups = await db.get_all_groups()

        for grp in groups:
            settings = await get_settings(grp["group_id"])
            req_channels = settings.get("req_fsub_id")

            if not req_channels:
                continue

            if not isinstance(req_channels, list):
                req_channels = [req_channels]

            if channel_id in req_channels:

                # 🔹 prevent duplicate insert
                if not await db.find_join_req(user_id, channel_id):
                    await db.add_join_req(user_id, channel_id)

                return  # stop after first match

    except Exception as e:
        LOGGER.error(f"Join Req Error: {e}")

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
