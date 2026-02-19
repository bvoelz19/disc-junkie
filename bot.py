import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

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

@bot.tree.command(name="play", description="Play music from a YouTube URL")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    
    # Check if the user is in a voice channel
    if not interaction.user.voice:
        return await interaction.followup.send("You must be in a voice channel!")

    voice_channel = interaction.user.voice.channel

    # Connect to the voice channel
    if interaction.guild.voice_client is None:
        await voice_channel.connect()
    elif interaction.guild.voice_client.channel != voice_channel:
        await interaction.guild.voice_client.move_to(voice_channel)

    # Play the music
    voice = interaction.guild.voice_client
    
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                ydl_opts['default_search'] = 'ytsearch'
                info = ydl.extract_info(f"ytsearch:{url}", download=False)
            
            if 'entries' in info:
                info = info['entries'][0]
            
            audio_url = info['url']
            title = info.get('title', 'Unknown')
        
        voice.play(discord.FFmpegPCMAudio(audio_url))
        await interaction.followup.send(f"🎵 Now playing: **{title}**")
    
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

bot.run(TOKEN)
