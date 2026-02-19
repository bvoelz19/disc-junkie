import logging
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp
import asyncio

# Setup logging
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
logging.basicConfig(filename=os.path.join(logs_dir, "bot.log"), level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
# Queue storage per guild
from collections import deque
queue_per_guild = {}

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    try:
        # Sync globally first
        synced_global = await bot.tree.sync()
        logging.info(f'Synced {len(synced_global)} command(s) globally')
        for cmd in synced_global:
            logging.info(f'  - {cmd.name}')
        
        # Also sync to each guild for immediate availability
        for guild in bot.guilds:
            try:
                synced_guild = await bot.tree.sync(guild=guild)
                logging.info(f'Synced {len(synced_guild)} command(s) to guild {guild.name} ({guild.id})')
            except Exception as e:
                logging.error(f'Failed to sync to guild {guild.name}: {e}')
    except Exception as e:
        logging.error(f'Failed to sync commands: {e}')

@bot.tree.command(name="ping", description="Test if bot is responsive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="play", description="Add a track to the queue")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    guild_id = interaction.guild.id
    if not interaction.user.voice:
        return await interaction.followup.send("You must be in a voice channel!")
    voice_channel = interaction.user.voice.channel
    # Connect or move
    vc = interaction.guild.voice_client
    if vc is None:
        vc = await voice_channel.connect()
    elif vc.channel != voice_channel:
        await vc.move_to(voice_channel)
    # Ensure queue exists
    if guild_id not in queue_per_guild:
        queue_per_guild[guild_id] = deque()
    # Fetch audio info
    ydl_opts = { 'format': 'bestaudio', 'quiet': True, 'no_warnings': True }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception:
                ydl_opts['default_search'] = 'ytsearch'
                info = ydl.extract_info(f"ytsearch:{url}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            audio_url = info['url']
            title = info.get('title', 'Unknown')
    except Exception as e:
        logging.error(f'Error fetching audio: {e}')
        return await interaction.followup.send(f"❌ Error fetching audio: {e}")
    # Add to queue
    queue_per_guild[guild_id].append((audio_url, title))
    await interaction.followup.send(f"📥 Added to queue: **{title}**")
    # If nothing playing, start
    if not vc.is_playing() and not vc.is_paused():
        await play_next(guild_id, vc)

async def play_next(guild_id, vc):
    if guild_id not in queue_per_guild or not queue_per_guild[guild_id]:
        await vc.disconnect()
        return
    audio_url, title = queue_per_guild[guild_id].popleft()
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_url))
    vc.play(source, after=lambda e: asyncio.create_task(on_track_end(e, guild_id, vc)))
    # Inform channel via channel id stored in interaction? We'll send via a stored channel dict; for now ignore

async def on_track_end(error, guild_id, vc):
    if error:
        logging.error(f"Error finished playing: {error}")
    # Start next
    await play_next(guild_id, vc)

# Add queue command
@bot.tree.command(name="queue", description="Show the current song queue")
async def queue_cmd(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if guild_id not in queue_per_guild or not queue_per_guild[guild_id]:
        return await interaction.response.send_message("Queue is empty.")
    queue = list(queue_per_guild[guild_id])
    msg = "**Queue:**\n"
    for idx, (_, title) in enumerate(queue, start=1):
        msg += f"{idx}. {title}\n"
    await interaction.response.send_message(msg)

# Skip command
@bot.tree.command(name="skip", description="Skip the current track")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏭ Skipped current track.")
    else:
        await interaction.response.send_message("No track is playing.")

# Volume command
@bot.tree.command(name="volume", description="Set playback volume")
async def volume(interaction: discord.Interaction, percent: int):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_connected():
        return await interaction.response.send_message("I'm not in a voice channel.")
    if not 0 <= percent <= 100:
        return await interaction.response.send_message("Please provide a percentage between 0 and 100.")
    volume_level = percent / 100
    if hasattr(vc.source, "volume"):
        vc.source.volume = volume_level
        await interaction.response.send_message(f"✅ Volume set to {percent}%.")
    else:
        await interaction.response.send_message("Cannot adjust volume: source does not support volume.")

# Stop command
@bot.tree.command(name="stop", description="Stop playback and clear queue")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    vc = interaction.guild.voice_client
    if vc:
        vc.stop()
        vc.disconnect()
    queue_per_guild[guild_id] = deque()
    await interaction.response.send_message("🛑 Stopped playback and cleared queue.")

bot.run(TOKEN)
