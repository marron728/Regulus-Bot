import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os

DATA_FILE = "data/rs_data.json"

class RSEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    # ---------- RS初期設定 ----------
    @app_commands.command(name="rs-event-setup", description="RSイベントの設定を開始します。")
    @app_commands.describe(category="Bot用カテゴリを選択してください。")
    async def rs_event_setup(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        guild_id = str(interaction.guild_id)

        entry_channel = await category.create_text_channel("rs-entry")
        admin_channel = await category.create_text_channel("rs-admin")

        self.data[guild_id] = {
            "entry_channel": entry_channel.id,
            "admin_channel": admin_channel.id,
            "common_role": None,
            "entries": {},
            "team_roles": {}
        }
        self.save_data()

        embed = discord.Embed(
            title="✅ RSイベント初期設定が完了しました！",
            description=f"{entry_channel.mention} と {admin_channel.mention} を作成しました。\n`/rs-commonrole` コマンドで共通ロールを設定してください。",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------- 共通ロール設定 ----------
    @app_commands.command(name="rs-commonrole", description="RSイベント用の共通ロールを設定します。")
    async def rs_commonrole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.data:
            await interaction.response.send_message("❌ まず `/rs-event-setup` を実行してください。", ephemeral=True)
            return

        self.data[guild_id]["common_role"] = role.id
        self.save_data()
        await interaction.response.send_message(f"🏁 共通ロールを {role.mention} に設定しました。", ephemeral=True)

    # ---------- エントリーメッセージ送信 ----------
    @app_commands.command(name="rs-entrypost", description="RSイベント用のエントリーメッセージを投稿します。")
    async def rs_entrypost(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = self.data.get(guild_id)
        if not data:
            await interaction.response.send_message("❌ まず `/rs-event-setup` を実行してください。", ephemeral=True)
            return

        entry_channel = interaction.guild.get_channel(data["entry_channel"])
        if not entry_channel:
            await interaction.response.send_message("❌ エントリーチャンネルが見つかりません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="💎 RSイベントがまたやってきました！",
            description=(
                "私たちの勇敢さを銀河に轟かせ、クリスタルを持ち帰ろう！\n"
                "皆さんのアクティビティと予想Ptsを入力してください🙋\n\n"
                "1️⃣ 50万pts 以上\n"
                "2️⃣ 50万〜25万pts\n"
                "3️⃣ 25万〜10万pts\n"
                "4️⃣ 10万〜5万pts\n"
                "5️⃣ 5万pts 以下"
            ),
            color=discord.Color.blue()
        )
        view = RSButtons(self)
        await entry_channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ RSエントリーメッセージを送信しました。", ephemeral=True)

    # ---------- 参加登録 ----------
    async def register_rs_entry(self, interaction: discord.Interaction, level: int):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        data = self.data.setdefault(guild_id, {"entries": {}})

        # pts入力ダイアログ表示
        modal = RSPointsModal(self, guild_id, user_id, level)
        await interaction.response.send_modal(modal)

    # ---------- 管理者用一覧 ----------
    @app_commands.command(name="rs-list", description="RSイベント参加者一覧を表示します。")
    @commands.has_permissions(administrator=True)
    async def rs_list(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        if guild_id not in self.data or not self.data[guild_id]["entries"]:
            await interaction.response.send_message("📭 登録された参加者はいません。", ephemeral=True)
            return

        entries = sorted(
            self.data[guild_id]["entries"].values(),
            key=lambda x: x["points"],
            reverse=True
        )
        total_points = sum([int(e["points"]) for e in entries])

        desc = "\n".join([
            f"{i+1}. {e['name']} - {e['points']} pts"
            for i, e in enumerate(entries)
        ])
        embed = discord.Embed(
            title="🏆 RSイベント参加者ランキング",
            description=desc,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"参加者数: {len(entries)} | 合計Pts: {total_points}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RSEvent(bot))

# ---------- UIクラス群 ----------

class RSButtons(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.primary)
    async def one(self, interaction, button):
        await self.cog.register_rs_entry(interaction, 1)

    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.primary)
    async def two(self, interaction, button):
        await self.cog.register_rs_entry(interaction, 2)

    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.primary)
    async def three(self, interaction, button):
        await self.cog.register_rs_entry(interaction, 3)

    @discord.ui.button(label="4️⃣", style=discord.ButtonStyle.primary)
    async def four(self, interaction, button):
        await self.cog.register_rs_entry(interaction, 4)

    @discord.ui.button(label="5️⃣", style=discord.ButtonStyle.primary)
    async def five(self, interaction, button):
        await self.cog.register_rs_entry(interaction, 5)

class RSPointsModal(discord.ui.Modal, title="RSイベント：予想Ptsを入力"):
    def __init__(self, cog, guild_id, user_id, level):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.level = level

        self.points = ui.TextInput(
            label="予想Ptsを入力してください",
            placeholder="例: 250000",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.points)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pts = int(self.points.value)
        except ValueError:
            await interaction.response.send_message("⚠️ 数字を入力してください。", ephemeral=True)
            return

        member = interaction.user
        name = member.display_name
        self.cog.data[self.guild_id]["entries"][self.user_id] = {
            "name": name,
            "level": self.level,
            "points": pts
        }

        # 共通ロールを付与
        common_id = self.cog.data[self.guild_id].get("common_role")
        if common_id:
            role = interaction.guild.get_role(common_id)
            if role:
                await member.add_roles(role)

        self.cog.save_data()
        await interaction.response.send_message(f"✅ {pts:,} pts を登録しました！", ephemeral=True)
