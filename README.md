# Discord Music Bot

A lightweight Discord music bot built in Python. It supports queueing, playback controls, and can be extended with additional features.

## Features
- Queue management (add, view, remove)
- Playback controls: play, pause, resume, stop, skip
- Simple command syntax
- Modular command architecture

## Installation
```bash
git clone https://github.com/bvoelz/discord-music-bot.git
cd discord-music-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration
Create a `.env` file:
```
DISCORD_TOKEN=your-bot-token
```

## Running
```bash
python bot.py
```
