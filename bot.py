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

# Store search results for emoji reactions
search_results_cache = {}  # {message_id: [(url, title), (url, title), ...]}
search_result_emojis = ['1️⃣', '2️⃣', '3️⃣']
reaction_to_song = {}  # {(message_id, emoji): (url, title)} - track what each emoji selection added

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

async def search_youtube(query):
    """Search YouTube and return first 3 results"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just extract info
            'default_search': 'ytsearch3'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch3:{query}", download=False)
        
        results = []
        if 'entries' in info:
            for entry in info['entries'][:3]:
                # Build proper YouTube URL from video ID
                video_id = entry.get('id')
                if not video_id:
                    url = entry.get('url')
                else:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                
                title = entry.get('title', 'Unknown')
                results.append((url, title))
        return results
    except Exception as e:
        logging.error(f'Error searching YouTube: {e}')
        return []

async def fetch_audio_url(url):
    """Fetch the actual audio URL and title from a YouTube URL"""
    try:
        # Try bestaudio first, but fallback to best if not available
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title', 'Unknown')
            return audio_url, title
    except Exception as e:
        logging.error(f'Error fetching audio: {e}')
        return None, None

@bot.tree.command(name="ping", description="Test if bot is responsive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="play", description="Add a track to the queue or search for one")
async def play(interaction: discord.Interaction, query: str = None):
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
    
    # If no query provided, search YouTube
    if query is None:
        await interaction.followup.send("❌ Please provide a song name or URL. Usage: `/play <song name or URL>`")
        return
    
    # Check if it's a URL or a search query
    is_url = query.startswith('http://') or query.startswith('https://')
    
    if is_url:
        # Direct URL provided, fetch audio
        audio_url, title = await fetch_audio_url(query)
        if audio_url is None:
            return await interaction.followup.send(f"❌ Error fetching audio from URL")
        
        queue_per_guild[guild_id].append((audio_url, title))
        await interaction.followup.send(f"📥 Added to queue: **{title}**")
        
        if not vc.is_playing() and not vc.is_paused():
            await play_next(guild_id, vc)
    else:
        # Search query provided, show search results
        await interaction.followup.send("🔍 Searching YouTube...")
        
        results = await search_youtube(query)
        if not results:
            return await interaction.followup.send("❌ No results found for that search.")
        
        # Build search results message
        search_msg = "**Search Results:**\n"
        for idx, (url, title) in enumerate(results, 1):
            search_msg += f"{search_result_emojis[idx-1]} **{title}**\n"
        search_msg += "\nReact with the emoji to select a song!"
        
        # Send the message with search results
        result_msg = await interaction.followup.send(search_msg)
        
        # Store search results in cache
        search_results_cache[result_msg.id] = results
        
        # Add emoji reactions to the message
        for emoji in search_result_emojis[:len(results)]:
            await result_msg.add_reaction(emoji)

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

# Reaction handler for search results
@bot.event
async def on_reaction_add(reaction, user):
    """Handle emoji reactions on search result messages"""
    # Ignore bot reactions
    if user.bot:
        return
    
    # Check if this is a search result message
    if reaction.message.id not in search_results_cache:
        return
    
    # Get the emoji and map to index
    emoji = str(reaction.emoji)
    try:
        idx = search_result_emojis.index(emoji)
    except ValueError:
        return  # Not a valid search result emoji
    
    # Get the selected result
    results = search_results_cache[reaction.message.id]
    if idx >= len(results):
        return
    
    selected_url, selected_title = results[idx]
    guild_id = reaction.message.guild.id
    
    # Get voice client
    vc = reaction.message.guild.voice_client
    if not vc or not vc.is_connected():
        await reaction.message.reply("❌ Bot is not in a voice channel.")
        return
    
    # Ensure queue exists
    if guild_id not in queue_per_guild:
        queue_per_guild[guild_id] = deque()
    
    # Check if song is already in queue (prevent duplicates)
    queue = list(queue_per_guild[guild_id])
    for queued_url, queued_title in queue:
        if queued_url == selected_url:
            await reaction.message.reply(f"⚠️ **{selected_title}** is already in the queue!")
            return
    
    # Fetch audio from the selected URL
    audio_url, title = await fetch_audio_url(selected_url)
    if audio_url is None:
        await reaction.message.reply("❌ Error fetching audio for the selected song.")
        return
    
    # Add to queue
    queue_per_guild[guild_id].append((audio_url, title))
    await reaction.message.reply(f"✅ Added to queue: **{title}**")
    
    # Store this reaction -> song mapping for potential removal later
    reaction_to_song[(reaction.message.id, emoji)] = (audio_url, title)
    
    # If nothing playing, start
    if not vc.is_playing() and not vc.is_paused():
        await play_next(guild_id, vc)
    
    # Keep cache alive for more selections - don't delete here

# Reaction removal handler
@bot.event
async def on_reaction_remove(reaction, user):
    """Handle emoji reaction removal from search result messages"""
    # Ignore bot reactions
    if user.bot:
        return
    
    # Check if this is a tracked reaction
    emoji = str(reaction.emoji)
    reaction_key = (reaction.message.id, emoji)
    
    if reaction_key not in reaction_to_song:
        return
    
    # Get the song that was added for this emoji
    audio_url, title = reaction_to_song[reaction_key]
    guild_id = reaction.message.guild.id
    
    # Get voice client
    vc = reaction.message.guild.voice_client
    if not vc or not vc.is_connected():
        return
    
    # Ensure queue exists
    if guild_id not in queue_per_guild:
        return
    
    queue = list(queue_per_guild[guild_id])
    
    # Find the song in the queue
    removed = False
    for idx, (queued_url, queued_title) in enumerate(queue):
        if queued_url == audio_url and queued_title == title:
            # Don't remove if it's currently playing
            if idx == 0 and vc.is_playing():
                await reaction.message.reply(f"⚠️ Cannot remove **{title}** - it's currently playing!")
                break
            
            # Remove from queue
            queue.pop(idx)
            queue_per_guild[guild_id] = deque(queue)
            await reaction.message.reply(f"🗑️ Removed from queue: **{title}**")
            removed = True
            break
    
    # Clean up the reaction mapping
    del reaction_to_song[reaction_key]

bot.run(TOKEN)
