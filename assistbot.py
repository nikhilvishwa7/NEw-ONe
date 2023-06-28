from pyrogram import Client
from info import API_ID, API_HASH, BOT_TOKEN

#ASSISTANT_TOKEN = "5725740361:AAGmC9u2jW8EHEHJEJEpNoEzD7xm2CpCx66cVa9MQg0"

assist = Client(name="clone-assist",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN,             
             workers=300
             )
