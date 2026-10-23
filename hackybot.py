import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1560299078355783713

STAFF_CHANNEL_ID = 1560299078355783713

intents = discord.Intents.default()
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)


class AppealForm(discord.ui.Modal, title="HackyCat Appeals"):
    reason = discord.ui.TextInput(
        label="Why should we unban you?",
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(STAFF_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message(
                "Appeal channel not found.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="New Ban Appeal",
            description=str(self.reason),
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})")

        await channel.send(embed=embed, view=ReviewButtons(interaction.user.id))
        await interaction.response.send_message(
            "Your appeal was sent to staff.", ephemeral=True
        )


class AppealButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit Appeal", style=discord.ButtonStyle.green,
                       custom_id="submit_appeal")
    async def submit(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        await interaction.response.send_modal(AppealForm())


class ReviewButtons(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "You need Ban Members permission.", ephemeral=True
            )
            return

        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            await interaction.response.send_message("Server not found.", ephemeral=True)
            return

        try:
            user = await bot.fetch_user(self.user_id)
            await guild.unban(user, reason="Ban appeal approved")
            await interaction.response.send_message("Appeal approved; user unbanned.")
            button.disabled = True
        except discord.NotFound:
            await interaction.response.send_message(
                "User is not currently banned.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "Bot lacks permission to unban this user.", ephemeral=True
            )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(
                "You need Ban Members permission.", ephemeral=True
            )
            return
        try:
            user = await bot.fetch_user(self.user_id)
            await user.send("Your HackyCat Appeals request was rejected.")
        except discord.HTTPException:
            pass

        await interaction.response.send_message("Appeal rejected.")


@bot.event
async def on_ready():
    bot.add_view(AppealButton())
    print(f"Logged in as {bot.user}")


@bot.event
async def on_member_ban(guild, user):
    if guild.id != GUILD_ID:
        return

    try:
        await user.send(
            f"You were banned from **{guild.name}**. You can submit an appeal below.",
            view=AppealButton()
        )
    except discord.HTTPException:
        print(f"Could not DM banned user {user.id}")


@bot.command()
@commands.has_permissions(administrator=True)
async def appeal_setup(ctx):
    await ctx.send("Click below to submit a ban appeal.", view=AppealButton())


if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your environment variables.")

bot.run(TOKEN)
