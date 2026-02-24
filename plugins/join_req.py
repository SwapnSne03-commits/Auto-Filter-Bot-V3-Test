from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS
from setting import get_settings

@Client.on_chat_join_request()
async def join_reqs(client, message: ChatJoinRequest):

    try:
        channel_id = message.chat.id

        # 🔹 সব group settings check করতে হবে
        groups = await db.get_all_groups()  # তোমার db function অনুযায়ী adjust করো

        for grp in groups:
            settings = await get_settings(grp["group_id"])
            req_channel = settings.get("req_fsub_id")

            if req_channel and req_channel == channel_id:

                if not await db.find_join_req(message.from_user.id, channel_id):
                    await db.add_join_req(message.from_user.id, channel_id)

                break

    except Exception as e:
        print(f"Join Req Error: {e}")

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
