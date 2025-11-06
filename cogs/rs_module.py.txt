import discord
from discord.ext import commands
from discord import app_commands

class RSEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rs_data = {}  # {guild_id: {button_number: [member_ids]}}
        self.rs_points = {}  # {guild_id: {member_id: pts}}
        self.rs_role_name = "今月のRSイベントランナー"

    # エントリーセットアップ
    @app_commands.command(name="rs-event-setup", description="RSイベント用エントリーメッセージを送信します。")
    @commands.has_permissions(administrator=True)
    async def rs_event_setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 RSイベントサインアップ",
            description=(
                "RSイベントがまたやってきました！\n"
                "私たちの勇敢さを銀河に轟かせ、クリスタルを持ち帰ろう！\n"
                "皆さんのアクティビティと予想Ptsを入力してください🙋\n\n"
                "1️⃣ 50万pts ↑\n"
                "2️⃣ 50万pts〜25万pts\n"
                "3️⃣ 25万pts〜10万pts\n"
                "4️⃣ 10万pts〜5万pts\n"
                "5️⃣ 5万ptsより下です"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="あなたの予想ポイントを選択してください。")

        view = RSButtonView(self)
        await interaction.response.send_message(embed=embed, view=view)
        await interaction.followup.send("✅ RSエントリー画面を作成しました。", ephemeral=True)

    # 管理者用 — 申告者リストを表示
    @app_commands.command(name="rs-show", description="RSイベントの申告一覧を表示します。")
    @commands.has_permissions(administrator=True)
    async def rs_show(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self.rs_points or len(self.rs_points[guild_id]) == 0:
            await interaction.response.send_message("📭 まだエントリーがありません。", ephemeral=True)
            return

        members_pts = self.rs_points[guild_id]
        sorted_members = sorted(members_pts.items(), key=lambda x: x[1], reverse=True)

        total_pts = sum(members_pts.values())
        embed = discord.Embed(title="💫 RSイベント参加者リスト", color=discord.Color.purple())

        rank_lines = []
        for member_id, pts in sorted_members:
            member = interaction.guild.get_member(member_id)
            if member:
                rank_lines.append(f"・{member.display_name} — **{pts:,} pts**")

        embed.description = "\n".join(rank_lines)
        embed.add_field(name="📊 参加者数", value=f"{len(sorted_members)} 名", inline=True)
        embed.add_field(name="💎 合計Pts", value=f"{total_pts:,}", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------------------
# RSボタンビュー
# -------------------------------
class RSButtonView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        for num in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]:
            self.add_item(RSButton(num))

class RSButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(label=label, style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        member = interaction.user
        cog = self.view.cog

        # ロール付与
        rs_role = discord.utils.get(interaction.guild.roles, name=cog.rs_role_name)
        if rs_role is None:
            rs_role = await interaction.guild.create_role(name=cog.rs_role_name)
        await member.add_roles(rs_role)

        # pts入力
        modal = RSPointModal(self.label, cog)
        await interaction.response.send_modal(modal)

class RSPointModal(discord.ui.Modal, title="RSイベントPTS申告"):
    pts_input = discord.ui.TextInput(label="あなたの予想PTSを入力してください", placeholder="例: 350000", required=True)

    def __init__(self, label, cog):
        super().__init__()
        self.label = label
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pts = int(str(self.pts_input.value).replace(",", "").strip())
        except ValueError:
            await interaction.response.send_message("❌ 数字を入力してください。", ephemeral=True)
            return

        guild_id = interaction.guild_id
        member = interaction.user

        if guild_id not in self.cog.rs_points:
            self.cog.rs_points[guild_id] = {}
        self.cog.rs_points[guild_id][member.id] = pts

        # ボタンごとの登録
        if guild_id not in self.cog.rs_data:
            self.cog.rs_data[guild_id] = {num: [] for num in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]}
        self.cog.rs_data[guild_id][self.label].append(member.id)

        await interaction.response.send_message(f"✅ {pts:,} pts を申告しました！", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RSEvent(bot))
