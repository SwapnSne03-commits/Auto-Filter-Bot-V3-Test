from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS
from setting import get_settings

@Client.on_chat_join_request()
async def join_reqs(client, message: ChatJoinRequest):

    settings = await get_settings(message.chat.id)
    req_channel = settings.get("req_fsub_id")

    if not req_channel:
        return

    if message.chat.id != req_channel:
        return

    if not await db.find_join_req(message.from_user.id, message.chat.id):
        await db.add_join_req(message.from_user.id, message.chat.id)

@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
