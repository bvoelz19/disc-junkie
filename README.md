# 🎵 Discord Music Bot

A feature-rich Discord music bot built with Python & discord.py. Stream YouTube audio directly into voice channels with intelligent search, queue management, and real-time playback control.

---

## ✨ Core Features

### 🔍 YouTube Search & Selection
- **Smart Search:** Type a song name → bot searches YouTube automatically
- **Multi-Result Display:** Shows top 3 results with emoji reactions (1️⃣ 2️⃣ 3️⃣)
- **One-Click Selection:** Just click an emoji to add to queue
- **Multi-Select:** Click multiple emojis to queue multiple songs from one search
- **Direct URLs:** Also supports direct YouTube URLs

### 🎶 Queue Management
- **Real-Time Display:** `/queue` shows current status with live progress
- **Duration Tracking:** All songs display length in HH:MM:SS format
- **Smart Removal:** Remove songs by unreacting emojis (protection: can't remove now-playing)
- **Duplicate Prevention:** Can't add same song twice to queue
- **Live Progress:** Shows elapsed / total time that updates in real-time

### 🎚️ Playback Controls
- **Skip:** `/skip` → Jump to next song (auto-plays if queue has songs)
- **Stop:** `/stop` → Stop playback and clear queue
- **Volume:** `/volume <0-100>` → Precise volume control
- **Auto-Play:** Songs auto-queue and play seamlessly

### 🏠 Queue Operations
- **Add via URL:** `/play <YouTube URL>`
- **Search & Add:** `/play <song name>`
- **View Queue:** `/queue` → Shows now playing + queue with durations
- **Emoji Management:** Add/remove songs via emoji reactions on search results

---

## 🛠️ Technical Details

### Tech Stack
- **Language:** Python 3.14+
- **Discord Library:** discord.py 2.6.4
- **Audio:** FFmpeg, PyNaCl for voice
- **YouTube:** yt-dlp for metadata extraction

### Commands
```
/ping           - Test bot responsiveness
/play <query>   - Search & queue songs (or provide YouTube URL)
/queue          - Show now playing + queue with timestamps
/skip           - Skip to next song
/volume <0-100> - Set playback volume percentage
/stop           - Stop all playback & clear queue
```

### Key Architecture
- **Per-Guild Queues:** Separate queue for each server (`queue_per_guild`)
- **Playback Tracking:** Real-time tracking of current song & start time
- **Emoji Reactions:** Dynamic reaction system with cleanup
- **Error Recovery:** Graceful handling of failed format requests & missing songs

---

## 📊 Features Breakdown

| Feature | Complexity | Status |
|---------|-----------|--------|
| YouTube Search | ⭐⭐⭐ | ✅ |
| Emoji Reactions | ⭐⭐⭐ | ✅ |
| Queue Management | ⭐⭐⭐⭐ | ✅ |
| Duration Tracking | ⭐⭐ | ✅ |
| Real-Time Progress | ⭐⭐⭐ | ✅ |
| Duplicate Prevention | ⭐⭐ | ✅ |
| Volume Control | ⭐ | ✅ |

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.14+
- FFmpeg installed (`brew install ffmpeg` on macOS)
- Discord bot token

### Quick Start
```bash
# Clone repo
git clone https://github.com/bvoelz19/disc-junkie.git
cd discord-music-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
echo "DISCORD_TOKEN=your-token-here" > .env

# Run
python bot.py
```

### Invite Bot to Server
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create/select your bot
3. OAuth2 → URL Generator
4. Scopes: `bot`
5. Permissions: `Send Messages`, `Use Slash Commands`, `Connect`, `Speak`
6. Copy generated URL and open in browser

---

## 💡 Usage Examples

### Search & Queue
```
User: /play deadmau5
Bot: Shows 3 results with emoji reactions
User: Clicks 1️⃣
Bot: ✅ Added to queue: Deadmau5 - Superliminal (3:45)
```

### Queue Inspection
```
User: /queue
Bot: 
🎵 Now Playing: Song Title
⏱️  1:23 / 3:45

Queue:
1. Next Song (4:12)
2. Another Track (2:58)
```

### Emoji Management
```
User: /play edm
Bot: Shows 3 results
User: Clicks 1️⃣, 2️⃣, 3️⃣ (adds all three)
Bot: ✅ Added songs to queue (3 total)
User: Unreacts 2️⃣
Bot: 🗑️ Removed from queue: Song 2
```

---

## 🐛 Known Limitations & Future Improvements

### Current Limitations
- No shuffle mode
- No repeat/loop
- No playlists
- Single bot per server

### Planned Features
- [ ] Shuffle mode
- [ ] Loop/repeat controls
- [ ] Playlist support
- [ ] Play history
- [ ] User permissions system

---

## 🔧 Development

### Project Structure
```
discord-music-bot/
├── bot.py              # Main bot logic & commands
├── requirements.txt    # Python dependencies
├── .env               # Configuration (token)
├── logs/              # Bot logs
└── venv/              # Virtual environment
```

### Recent Updates
- ✅ YouTube search with emoji selection
- ✅ Multi-select from search results
- ✅ Queue with real-time duration tracking
- ✅ Emoji-based queue management
- ✅ Duplicate prevention
- ✅ Auto-play between songs
- ✅ Volume control
- ✅ HH:MM:SS time format

---

## 📝 Requirements
```
discord.py==2.6.4
python-dotenv==1.2.1
yt-dlp==2026.2.4
PyNaCl==1.6.2
```

---

## 📄 License
MIT

---

## 🤝 Contributing
Feel free to fork, submit PRs, or open issues for bugs/features!

---

**Built with ❤️ for Discord music lovers** 🎶
