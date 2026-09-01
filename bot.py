import os
import logging

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from mcrcon import MCRcon

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
ALLOWED_ROLE_ID = int(os.environ["ALLOWED_ROLE_ID"])

RCON_HOST = os.environ["RCON_HOST"]
RCON_PORT = int(os.environ.get("RCON_PORT", 25575))
RCON_PASSWORD = os.environ["RCON_PASSWORD"]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("whitelist-bot")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def mojang_lookup(username: str):
    """Return the canonical (correctly-cased) Minecraft username, or None if it doesn't exist."""
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("name")


def rcon_whitelist_add(username: str) -> str:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT, timeout=5) as mcr:
        return mcr.command(f"whitelist add {username}")


def rcon_whitelist_remove(username: str) -> str:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT, timeout=5) as mcr:
        return mcr.command(f"whitelist remove {username}")


def has_allowed_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            return False
        return any(role.id == ALLOWED_ROLE_ID for role in member.roles)
    return app_commands.check(predicate)


@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    synced = await bot.tree.sync(guild=guild)
    log.info(f"Logged in as {bot.user}. Synced {len(synced)} command(s) to guild {GUILD_ID}.")


@bot.tree.command(
    name="whitelist",
    description="Add your Minecraft username to the server whitelist",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(username="Your exact Minecraft (Java) username")
@has_allowed_role()
async def whitelist(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)

    canonical_name = await mojang_lookup(username)
    if canonical_name is None:
        await interaction.followup.send(
            f"`{username}` doesn't look like a real Minecraft (Java) account. Double-check the spelling.",
            ephemeral=True,
        )
        return

    try:
        result = rcon_whitelist_add(canonical_name)
    except Exception:
        log.exception("RCON error while whitelisting")
        await interaction.followup.send(
            "Couldn't reach the Minecraft server right now. Try again in a bit, or ping an admin.",
            ephemeral=True,
        )
        return

    log.info(f"{interaction.user} ({interaction.user.id}) whitelisted '{canonical_name}': {result}")
    await interaction.followup.send(
        f"`{canonical_name}` has been added to the whitelist. See you in-game.",
        ephemeral=True,
    )


@bot.tree.command(
    name="unwhitelist",
    description="[Admin] Remove a Minecraft username from the whitelist",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(username="Minecraft username to remove")
@commands.has_permissions(administrator=True)
async def unwhitelist(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    try:
        result = rcon_whitelist_remove(username)
    except Exception:
        log.exception("RCON error while un-whitelisting")
        await interaction.followup.send("Couldn't reach the Minecraft server.", ephemeral=True)
        return

    log.info(f"{interaction.user} removed '{username}' from whitelist: {result}")
    await interaction.followup.send(f"Removed `{username}` from the whitelist.", ephemeral=True)


@whitelist.error
async def whitelist_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "You don't have the required role to whitelist yourself. Ask an admin.",
            ephemeral=True,
        )
    else:
        log.exception("Unhandled error in /whitelist")
        if not interaction.response.is_done():
            await interaction.response.send_message("Something went wrong.", ephemeral=True)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
