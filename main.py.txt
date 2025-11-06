import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# .envファイルからTOKENなどを読み込む
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Botの設定
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# 起動時の処理
@bot.event
async def on_ready():
    print(f"✅ {bot.user} としてログインしました。")
    await bot.change_presence(activity=discord.Game(name="WS・RSイベント管理中"))

    # Cogsをロード
    initial_extensions = [
        "cogs.ws_module",
        "cogs.rs_module",
        "cogs.role_utils",
        "cogs.scheduler",
        "cogs.setup_utils"
    ]
    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"📦 {ext} をロードしました。")
        except Exception as e:
            print(f"❌ {ext} のロード中にエラー: {e}")

# エラー処理
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⚠️ 権限が不足しています。管理者のみ実行可能です。")
    else:
        await ctx.send(f"❌ エラーが発生しました: {error}")

# Botを起動
if __name__ == "__main__":
    if not TOKEN:
        print("❌ DISCORD_TOKEN が設定されていません。")
    else:
        bot.run(TOKEN)
