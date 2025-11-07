import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os

DATA_FILE = "data/ws_data.json"

class WSEvent(commands.Cog):
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

    # ---------- WS初期設定 ----------
    @app_commands.command(name="ws-setup", description="WSイベント用のチャンネルを設定します。")
    @app_commands.describe(category="Bot用カテゴリを選択してください。")
    async def ws_setup(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        guild_id = str(interaction.guild_id)

        # 2つのチャンネルを自動生成
        entry_channel = await category.create_text_channel("ws-entry")
        admin_channel = await category.create_text_channel("ws-admin")

        self.data[guild_id] = {
            "entry_channel": entry_channel.id,
            "admin_channel": admin_channel.id,
            "common_role": None,
            "teams": {},
            "entries": {}
        }
        self.save_data()

        embed = discord.Embed(
            title="✅ WSイベントセットアップ完了",
            description=f"{entry_channel.mention} と {admin_channel.mention} を作成しました。\n次に `/ws-commonrole` や `/ws-team-add` で設定を行ってください。",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------- 共通ロール設定 ----------
    @app_commands.command(name="ws-commonrole", description="共通ロール（今週のWSパイロット）を設定します。")
    async def ws_commonrole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild_id)
        self.data[guild_id]["common_role"] = role.id
        self.save_data()
        await interaction.response.send_message(f"🛰️ 共通ロールを {role.mention} に設定しました。", ephemeral=True)

    # ---------- チーム追加 ----------
    @app_commands.command(name="ws-team-add", description="チームを追加します（最大8まで）。")
    async def ws_team_add(self, interaction: discord.Interaction, team_name: str, role: discord.Role):
        guild_id = str(interaction.guild_id)
        if len(self.data[guild_id]["teams"]) >= 8:
            await interaction.response.send_message("⚠️ チームは最大8つまでです。", ephemeral=True)
            return

        self.data[guild_id]["teams"][team_name] = role.id
        self.save_data()
        await interaction.response.send_message(f"✅ チーム `{team_name}` を追加しました。", ephemeral=True)

    # ---------- エントリーメッセージ送信 ----------
    @app_commands.command(name="ws-entrypost", description="エントリーメッセージを投稿します。")
    async def ws_entrypost(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = self.data.get(guild_id)
        if not data:
            await interaction.response.send_message("❌ まず `/ws-setup` を実行してください。", ephemeral=True)
            return

        entry_channel = interaction.guild.get_channel(data["entry_channel"])
        if not entry_channel:
            await interaction.response.send_message("❌ エントリーチャンネルが見つかりません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚙️ アクティビティを申告して、WSサインアップをしてください！",
            description=(
                "⭐️キャプテン：戦術や戦略に興味があり関わりたい。ゲームを指揮することに興味がある。wskillやレリック計算等も出来る。\n\n"
                "1️⃣スーパーマン：自主的に頻繁にWSをチェックする。素早い反応、反応時間30分〜2時間以内。\n\n"
                "2️⃣アクティブ：素早くpingに反応できる。反応時間2〜4時間以内。\n\n"
                "3️⃣カジュアル：1日4回程度チェックイン。反応時間4〜6時間。\n\n"
                "4️⃣リラックス：朝晩2回程度チェックイン。リラックスしたWSを楽しみたい。"
            ),
            color=discord.Color.blurple()
        )
        view = WSButtons(self)
        await entry_channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ エントリーメッセージを送信しました。", ephemeral=True)

    # ---------- エントリー登録 ----------
    async def register_entry(self, interaction: discord.Interaction, activity_level: str):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)

        if guild_id not in self.data:
            await interaction.response.send_message("❌ イベントデータがありません。", ephemeral=True)
            return

        if user_id in self.data[guild_id]["entries"]:
            old = self.data[guild_id]["entries"][user_id]["activity"]
            self.data[guild_id]["entries"][user_id]["activity"] = activity_level
            msg = f"🔁 更新しました。以前: {old} → 現在: {activity_level}"
        else:
            self.data[guild_id]["entries"][user_id] = {
                "name": interaction.user.display_name,
                "activity": activity_level
            }
            msg = f"✅ 登録しました: {activity_level}"

        # 共通ロール付与
        common_id = self.data[guild_id].get("common_role")
        if common_id:
            role = interaction.guild.get_role(common_id)
            if role:
                await interaction.user.add_roles(role)

        self.save_data()
        await interaction.response.send_message(msg, ephemeral=True)

    # ---------- All Delete ----------
    @app_commands.command(name="ws-all-delete", description="全員のチームロール・共通ロールをリセットします。")
    @commands.has_permissions(administrator=True)
    async def ws_all_delete(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        data = self.data[guild_id]
        guild = interaction.guild

        roles = []
        if data.get("common_role"):
            r = guild.get_role(data["common_role"])
            if r: roles.append(r)
        for rid in data["teams"].values():
            r = guild.get_role(rid)
            if r: roles.append(r)

        if not roles:
            await interaction.response.send_message("❌ リセット対象のロールがありません。", ephemeral=True)
            return

        view = WSResetConfirmView(roles, self, interaction.user)
        await interaction.response.send_message("🗑️ リセットするロールを選んでください：", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WSEvent(bot))

# ---------- UIクラス群 ----------

class WSButtons(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="⭐️", style=discord.ButtonStyle.primary)
    async def star(self, interaction, button):
        await self.cog.register_entry(interaction, "⭐️キャプテン")

    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.success)
    async def one(self, interaction, button):
        await self.cog.register_entry(interaction, "スーパーマン")

    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.success)
    async def two(self, interaction, button):
        await self.cog.register_entry(interaction, "アクティブ")

    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.success)
    async def three(self, interaction, button):
        await self.cog.register_entry(interaction, "カジュアル")

    @discord.ui.button(label="4️⃣", style=discord.ButtonStyle.success)
    async def four(self, interaction, button):
        await self.cog.register_entry(interaction, "リラックス")

class WSResetConfirmView(discord.ui.View):
    def __init__(self, roles, cog, user):
        super().__init__(timeout=60)
        self.roles = roles
        self.cog = cog
        self.user = user
        for r in roles:
            self.add_item(WSRoleSelectButton(r, self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

class WSRoleSelectButton(discord.ui.Button):
    def __init__(self, role, parent_view):
        super().__init__(label=role.name, style=discord.ButtonStyle.danger)
        self.role = role
        self.parent_view = parent_view

    async def callback(self, interaction):
        if interaction.user != self.parent_view.user:
            await interaction.response.send_message("❌ あなたはこの操作を実行できません。", ephemeral=True)
            return
        removed = 0
        for m in self.role.members:
            await m.remove_roles(self.role)
            removed += 1
        await interaction.response.send_message(f"🧹 {self.role.name} から {removed} 人を削除しました。", ephemeral=True)
