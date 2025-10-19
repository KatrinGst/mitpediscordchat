import os
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from agent import run_agent

# ---------- Configuration ----------
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
APP_ID = os.getenv("DISCORD_APP_ID")
TEST_GUILD_ID = os.getenv("DISCORD_PUBLIC_GUILD_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sofja")

intents = discord.Intents.default()
intents.message_content = True  # enable in Developer Portal → Bot → Privileged Gateway Intents
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Events ----------
@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        if TEST_GUILD_ID:
            guild = discord.Object(id=int(TEST_GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            logger.info(f"🔁 Synced commands to guild {TEST_GUILD_ID}")
        else:
            await bot.tree.sync()
            logger.info("🌍 Synced global commands (this may take up to an hour)")
    except Exception as e:
        logger.exception("Error syncing commands: %s", e)

# ---------- Respond to $hello ----------
@bot.event
async def on_message(message: discord.Message):
    # Ignore the bot's own messages
    if message.author == bot.user:
        return

    # Reply to $hello
    if message.content.strip().lower().startswith("$hello"):
        await message.channel.send("Hello! 👋")
        return  # stop further processing for this message

    # Allow other commands to be processed (e.g., prefix commands)
    await bot.process_commands(message)

# ---------- Slash Commands ----------
@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓", ephemeral=True)

@bot.tree.command(name="agent", description="Ask a question to the Sofja agent")
@app_commands.describe(query="Your question for the agent")
async def agent_cmd(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    try:
        answer = await run_agent(query=query, user=str(interaction.user))
        await interaction.followup.send(answer)
    except Exception as e:
        logger.exception("Agent error: %s", e)
        await interaction.followup.send("😕 An error occurred in the agent. Please check the logs.", ephemeral=True)

# ---------- Run the bot ----------
def main():
    if not TOKEN:
        raise RuntimeError("❌ DISCORD_BOT_TOKEN not found. Set it in .env or environment variables.")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
