import re
import ast
import math
import random

from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, PICS
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from plugins.Mods.clone import clonedme
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}

SPELL_MODE = True

SPELL_TXT = """➼ 𝑯𝒆𝒚 {mention}
𝚄𝚛 𝚛𝚎𝚚𝚞𝚎𝚜𝚝𝚎𝚍 𝚖𝚘𝚟𝚒𝚎𝚜 𝚜𝚙𝚎𝚕𝚕𝚒𝚗𝚐 𝚒𝚜 𝚒𝚗𝚌𝚘𝚛𝚛𝚎𝚌𝚝 𝚝𝚑𝚎 𝚌𝚘𝚛𝚛𝚎𝚌𝚝 𝚜𝚙𝚎𝚕𝚕𝚒𝚗𝚐𝚜 𝚒𝚜 𝚐𝚒𝚟𝚎𝚗 𝚋𝚎𝚕𝚕𝚘𝚠
➣ 𝚜𝚙𝚎𝚕𝚕𝚒𝚗𝚐: {title}
➣ 𝙳𝚊𝚝𝚎: {year}
𝐘𝐨𝐮𝐫 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐌𝐨𝐯𝐢𝐞 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠 𝐈𝐬 𝐈𝐧𝐜𝐨𝐫𝐫𝐞𝐜𝐭 𝐂𝐡𝐞𝐜𝐤 𝐒𝐩𝐞𝐥𝐥𝐢𝐧𝐠 𝐀𝐧𝐝 𝐀𝐬𝐤 𝐀𝐠𝐚𝐢𝐧 𝐎𝐑 𝐂𝐡𝐞𝐜𝐤 𝐓𝐡𝐢𝐬 𝐌𝐨𝐯𝐢𝐞 𝐎𝐭𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞 𝐎𝐫 𝐍𝐨𝐭
"""

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    await auto_filter(client, message)
        
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        me = await client.get_me()
        user_nme = me.username
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{file_name}"
        try:
            if (AUTH_CHANNEL) and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{clonedme.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{clonedme.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('Cʜᴇᴄᴋ PM, I ʜᴀᴠᴇ sᴇɴᴛ ғɪʟᴇs ɪɴ ᴘᴍ', show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{user_nme}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{user_nme}?start={ident}_{file_id}")
            
async def auto_filter(client, msg, spoll=False):
    if not spoll:        
        message = msg        
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(message.chat.id ,search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.chat.id)
        message = message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
        
    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT →", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap =f"<b>🍿 ᴛɪᴛɪʟᴇ {search}\n\n┏ 🤴 ᴀsᴋᴇᴅ ʙʏ : {message.from_user.mention}\n┣ ⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : 𝐀𝐧𝐧𝐚_𝐁𝐞𝐧\n┗ 🍁 𝐏𝐚𝐫𝐫𝐞𝐧𝐭: @botechs_bot\n\n𝐘𝐨𝐮𝐫 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐅𝐢𝐥𝐞𝐬 𝐀𝐫𝐞 𝐑𝐞𝐚𝐝𝐲 𝐓𝐨 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐂𝐥𝐢𝐜𝐤 𝐘𝐨𝐮𝐫 𝐏𝐫𝐨𝐩𝐞𝐫 𝐅𝐢𝐥𝐞 𝐁𝐮𝐭𝐭𝐨𝐧 𝐀𝐍𝐝 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐦𝐨𝐯𝐢𝐞𝐬\n\n🗂️𝑭𝒐𝒖𝒏𝒅𝒆𝒅 𝑭𝒊𝒍𝒆𝒔 -☼︎-<code>{total_results}</code>\n\n✫ 𝐏𝐎𝐖𝐄𝐑𝐃 𝐁𝐘 ✫\n⍟{message.chat.title}</b>"
    if imdb and imdb.get('poster'):
        await message.delete()
        try:
            await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    else:        
        await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn))
    if spoll:
        await message.delete()
