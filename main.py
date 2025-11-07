import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# .envファイルからTOKENを読み込む（ローカル動作用）
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Bot設定
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Flaskサーバー設定
app = Flask(__name__)

@app.route('/')
def home():
    return "Regulus-Bot is running!", 200

def run_flask_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def start_bot_and_server():
    t = Thread(target=run_flask_server)
    t.start()
    bot.run(TOKEN)

if __name__ == '__main__':
    start_bot_and_server()
