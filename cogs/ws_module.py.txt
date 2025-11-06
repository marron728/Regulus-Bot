import discord
from discord.ext import commands
from discord import app_commands

class WSEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.team_data = {}  # {guild_id: {button_number: [member_ids]}}
        self.ws_role_name = "今週のWSパイロット"
        self.max_team_members = 10
        self.team_roles = {}  # チーム名→Roleオブジェクト

    # WSのサインアップメッセージを送信
    @app_commands.command(name="ws-entry-setup", description="WSイベント用エントリーメッセージを送信します。")
    @commands.has_permissions(administrator=True)
    async def ws_entry_setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🪐 WSサインアップ",
            description=(
                "アクティビティを申告して、WSサインアップをしてください！\n\n"
                "⭐️キャプテン：戦術や戦略に興味があり関わりたい。ゲームを指揮することに興味がある。wskillやレリック計算等も出来る(アクティビティとは関係なく押してください)\n"
                "1️⃣スーパーマン：自主的に頻繁にWSをチェックする。素早い反応、反応時間30分〜2時間以内。\n"
                "2️⃣アクティブ：素早くpingに反応できる。起きている場合、テレポートやリープ着地の時にゲームを見るように努力。\n"
                "3️⃣カジュアル：1日4回程度のチェックイン。pingがあればゲームを見る。反応時間 4〜6時間。\n"
                "4️⃣リラックス：朝晩 2回程度のチェックイン。リラックスしたWSを楽しみたい。"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="参加したい番号を押してください。")

        view = WSButtonView(self)
        await interaction.response.send_message(embed=embed, view=view)
        await interaction.followup.send("✅ エントリーメッセージを作成しました。", ephemeral=True)

    # WS管理用：全ロールリセット
    @app_commands.command(name="ws-all-delete", description="WS関連ロールを全てリセットします。")
    @commands.has_permissions(administrator=True)
    async def ws_all_delete(self, interaction: discord.Interaction):
        guild = interaction.guild
        roles_to_reset = [r for r in guild.roles if r.name == self.ws_role_name or r.name in self.team_roles]

        options = [
            discord.SelectOption(label=role.name, description="このロールをリセット", value=str(role.id))
            for role in roles_to_reset
        ]

        select = discord.ui.Select(placeholder="リセットするロールを選択", options=options, min_values=1, max_values=len(options))
        view = discord.ui.View()
        view.add_item(select)

        async def confirm(interaction_select: discord.Interaction):
            selected_ids = select.values
            count = 0
            for role_id in selected_ids:
                role = guild.get_role(int(role_id))
                for member in role.members:
                    await member.remove_roles(role)
                    count += 1
            await interaction_select.response.send_message(f"✅ {count}名を対象ロールから削除しました。", ephemeral=True)

        select.callback = confirm
        await interaction.response.send_message("リセットするロールを選択してください。", view=view, ephemeral=True)

# -------------------------------
# ボタン操作クラス
# -------------------------------
class WSButtonView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

        self.add_item(WSButton("⭐️", "captain"))
        for num in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]:
            self.add_item(WSButton(num, num))

class WSButton(discord.ui.Button):
    def __init__(self, label, value):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        member = interaction.user
        cog = self.view.cog

        # ロール付与
        ws_role = discord.utils.get(interaction.guild.roles, name=cog.ws_role_name)
        if ws_role is None:
            ws_role = await interaction.guild.create_role(name=cog.ws_role_name)
        await member.add_roles(ws_role)

        # サインアップ登録
        if guild_id not in cog.team_data:
            cog.team_data[guild_id] = {num: [] for num in ["⭐️", "1️⃣", "2️⃣", "3️⃣", "4️⃣"]}
        cog.team_data[guild_id][self.label].append(member.id)

        await interaction.response.send_message(f"{member.display_name} さんを {self.label} チームに登録しました！", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WSEvent(bot))
