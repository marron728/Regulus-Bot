import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import json
import os

SCHEDULE_FILE = "data/schedules.json"

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_schedules()
        self.schedule_task.start()

    def load_schedules(self):
        if not os.path.exists(SCHEDULE_FILE):
            self.schedules = {}
            return
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            self.schedules = json.load(f)

    def save_schedules(self):
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.schedules, f, ensure_ascii=False, indent=4)

    async def send_scheduled_message(self, guild_id, schedule_id, schedule_data):
        channel = self.bot.get_channel(schedule_data["channel_id"])
        if not channel:
            return
        content = schedule_data["message"]
        await channel.send(content)
        schedule_data["last_post"] = int(datetime.datetime.now().timestamp())
        self.save_schedules()

    @tasks.loop(minutes=1)
    async def schedule_task(self):
        now = datetime.datetime.now()
        for guild_id, schedules in list(self.schedules.items()):
            for sid, data in schedules.items():
                if data["type"] == "daily":
                    target = datetime.time.fromisoformat(data["time"])
                    if now.hour == target.hour and now.minute == target.minute:
                        await self.send_scheduled_message(guild_id, sid, data)

                elif data["type"] == "weekly":
                    target = datetime.time.fromisoformat(data["time"])
                    if now.weekday() == data["weekday"] and now.hour == target.hour and now.minute == target.minute:
                        await self.send_scheduled_message(guild_id, sid, data)

                elif data["type"] == "monthly":
                    target = datetime.time.fromisoformat(data["time"])
                    if now.day == data["day"] and now.hour == target.hour and now.minute == target.minute:
                        await self.send_scheduled_message(guild_id, sid, data)

                elif data["type"] == "interval":
                    last = datetime.datetime.fromtimestamp(data.get("last_post", 0))
                    delta_days = (now - last).days
                    if delta_days >= data["interval_days"]:
                        await self.send_scheduled_message(guild_id, sid, data)

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Scheduler started")

    @commands.hybrid_command(name="schedule_add", description="新しい定期投稿を追加します。")
    @commands.has_permissions(administrator=True)
    async def schedule_add(self, ctx, schedule_type: str, channel: discord.TextChannel, *, message: str):
        """使用例: /schedule_add daily #general おはようございます！"""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.schedules:
            self.schedules[guild_id] = {}

        sid = str(len(self.schedules[guild_id]) + 1)
        self.schedules[guild_id][sid] = {
            "type": schedule_type,
            "channel_id": channel.id,
            "message": message,
            "created": int(datetime.datetime.now().timestamp())
        }
        self.save_schedules()
        await ctx.send(f"🆕 定期投稿を追加しました: `{schedule_type}` → {channel.mention}")

    @commands.hybrid_command(name="schedule_list", description="登録済みの定期投稿を一覧表示します。")
    @commands.has_permissions(administrator=True)
    async def schedule_list(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.schedules or not self.schedules[guild_id]:
            await ctx.send("📭 登録済みのスケジュールはありません。")
            return

        embed = discord.Embed(title="🗓 登録済みスケジュール一覧", color=discord.Color.green())
        for sid, s in self.schedules[guild_id].items():
            t = s["type"]
            ts = s.get("last_post", "未実行")
            if isinstance(ts, int):
                ts = f"<t:{ts}:F>"
            embed.add_field(
                name=f"ID {sid} | {t}",
                value=f"投稿先: <#{s['channel_id']}>\n内容: {s['message'][:50]}...\n前回投稿: {ts}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="schedule_remove", description="指定した定期投稿を削除します。")
    @commands.has_permissions(administrator=True)
    async def schedule_remove(self, ctx, schedule_id: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.schedules or schedule_id not in self.schedules[guild_id]:
            await ctx.send("❌ 該当するスケジュールが見つかりません。")
            return

        del self.schedules[guild_id][schedule_id]
        self.save_schedules()
        await ctx.send(f"🗑 ID `{schedule_id}` のスケジュールを削除しました。")

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
