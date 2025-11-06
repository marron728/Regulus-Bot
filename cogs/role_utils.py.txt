import discord
from discord.ext import commands
from discord import app_commands

class RoleUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ロールをメンションするコマンド
    @app_commands.command(name="pingrole", description="指定したロールの全メンバーを@silentでメンションします。")
    @app_commands.describe(role="メンションしたいロールを選択してください。")
    @commands.has_permissions(administrator=True)
    async def pingrole(self, interaction: discord.Interaction, role: discord.Role):
        members = [m for m in role.members if not m.bot]
        if not members:
            await interaction.response.send_message(f"⚠️ ロール {role.name} にメンバーはいません。", ephemeral=True)
            return

        mentions = " ".join([m.mention for m in members])
        message = f"@silent {mentions}"
        await interaction.response.send_message(message)

    # ロールに含まれるメンバーをリストアップ
    @app_commands.command(name="listrole", description="指定したロールに含まれるメンバーをリスト表示します。")
    @app_commands.describe(role="リストアップするロールを選択してください。")
    @commands.has_permissions(administrator=True)
    async def listrole(self, interaction: discord.Interaction, role: discord.Role):
        members = [m for m in role.members if not m.bot]
        if not members:
            await interaction.response.send_message(f"📭 ロール {role.name} に該当するメンバーはいません。", ephemeral=True)
            return

        member_names = "\n".join([f"・{m.display_name}" for m in members])
        embed = discord.Embed(
            title=f"📋 ロール「{role.name}」のメンバー一覧",
            description=member_names,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"合計 {len(members)} 名")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleUtils(bot))
