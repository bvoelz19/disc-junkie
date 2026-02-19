import discord
from discord.ext import commands
import unittest
import os
import yt_dlp

class TestBotFunctionality(unittest.TestCase):

    def setUp(self):
        self.bot = commands.Bot(command_prefix='!')

    def test_play_command(self):
        @self.bot.tree.command(name="play", description="Play music from a YouTube URL")
        async def play(interaction: discord.Interaction, url: str):
            # Check if the user is in a voice channel
            if not interaction.user.voice:
                return await interaction.response.send_message("You must be in a voice channel!")

            voice_channel = interaction.user.voice.channel

            # Connect to the voice channel
            if self.bot.guilds[0].voice_clients:
                voice_client = self.bot.guilds[0].voice_clients[0]
            else:
                voice_client = await voice_channel.connect()

            # Play the music
            ydl_opts = {'format': 'bestaudio'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            audio_url = info['formats'][0]['url']
            voice_client.play(discord.FFmpegPCMAudio(audio_url))

        self.assertEqual(play, self.bot.tree.get_command("play"))

    def test_play_audio(self):
        # Test that the audio is playing
        voice_client = self.bot.guilds[0].voice_clients[0]
        self.assertTrue(voice_client.is_playing())

if __name__ == "__main__":
    unittest.main()
