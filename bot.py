import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
import asyncio

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
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

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
    source = discord.FFmpegPCMAudio(audio_url)
    vc.play(source, after=lambda e: asyncio.create_task(on_track_end(e, guild_id, vc)))
    # Inform channel via channel id stored in interaction? We'll send via a stored channel dict; for now ignore

async def on_track_end(error, guild_id, vc):
    if error:
        print(f"Error finished playing: {error}")
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
