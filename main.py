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

# ==============================
# Cog（スラッシュコマンド群）の読み込み設定
# ==============================
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"✅ Loaded cog: {filename}")

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

# ==============================
# Flaskサーバー設定（Koyeb/Render対策）
# ==============================
app = Flask(__name__)

@app.route('/')
def home():
    return "Regulus-Bot is running!", 200

def run_flask_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==============================
# 並行起動（Bot + Webサーバー）
# ==============================
def start_bot_and_server():
    t = Thread(target=run_flask_server)
    t.start()
    asyncio.run(load_cogs())  # 🔹 Cogファイルを読み込み
    bot.run(TOKEN)

if __name__ == '__main__':
    start_bot_and_server()


