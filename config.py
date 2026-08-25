import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

# Discord Configuration
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
EVENT_GUILD_ID: int = int(os.getenv("EVENT_GUILD_ID", 0))
EVENT_CHANNEL_ID: int = int(os.getenv("EVENT_CHANNEL_ID", 0))
PARTNER_CHANNEL_ID: int = int(os.getenv("PARTNER_CHANNEL_ID", 0))
MOD_CHANNEL_ID: int = int(os.getenv("MOD_CHANNEL_ID", 0))
APPLICATION_CATEGORY_ID: int = int(os.getenv("APPLICATION_CATEGORY_ID", 0))
MOD_ROLE_ID: int = int(os.getenv("MOD_ROLE_ID", 0))
EVENT_ROLE_ID: int = int(os.getenv("EVENT_ROLE_ID", 0))

# Event Scheduling
EVENT_TIMEZONE: str = os.getenv("EVENT_TIMEZONE", "Europe/Berlin")
EVENT_DAY: int = int(os.getenv("EVENT_DAY", 0))  # 0 = Monday
EVENT_HOUR: int = int(os.getenv("EVENT_HOUR", 20))
EVENT_MINUTE: int = int(os.getenv("EVENT_MINUTE", 0))

# Activity Points
MESSAGE_POINTS: int = int(os.getenv("MESSAGE_POINTS", 1))
MESSAGE_COOLDOWN: int = int(os.getenv("MESSAGE_COOLDOWN", 300))  # seconds
JOIN_POINTS: int = int(os.getenv("JOIN_POINTS", 2))
RETENTION_POINTS: int = int(os.getenv("RETENTION_POINTS", 3))
RETENTION_HOURS: int = int(os.getenv("RETENTION_HOURS", 24))
ACTIVE_USER_POINTS: int = int(os.getenv("ACTIVE_USER_POINTS", 5))
VOICE_POINTS: int = int(os.getenv("VOICE_POINTS", 1))
VOICE_INTERVAL: int = int(os.getenv("VOICE_INTERVAL", 300))  # seconds
VOICE_MAX_WEEKLY: int = int(os.getenv("VOICE_MAX_WEEKLY", 120))  # minutes per week

# GIFs
ELIMINATION_GIFS_STR: str = os.getenv("ELIMINATION_GIFS", "")
ELIMINATION_GIFS: List[str] = [
    gif.strip() for gif in ELIMINATION_GIFS_STR.split(",") if gif.strip()
] if ELIMINATION_GIFS_STR else []

# Database
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/bot.db")

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Game Settings
RISK_ELIMINATION_CHANCE: float = 1.0 / 7.0  # 1 in 7
SAFE_ZONE_PERCENTAGE: float = 0.70  # Top 70%
RISK_ZONE_PERCENTAGE: float = 0.30  # Bottom 30%
STARTING_LIVES: int = 3

# Validation
def validate_config():
    """Validate that all required config values are set."""
    required = [
        ("DISCORD_TOKEN", DISCORD_TOKEN),
        ("EVENT_GUILD_ID", EVENT_GUILD_ID),
        ("EVENT_CHANNEL_ID", EVENT_CHANNEL_ID),
        ("PARTNER_CHANNEL_ID", PARTNER_CHANNEL_ID),
        ("MOD_CHANNEL_ID", MOD_CHANNEL_ID),
        ("MOD_ROLE_ID", MOD_ROLE_ID),
    ]
    
    missing = [name for name, value in required if not value]
    if missing:
        raise ValueError(f"Missing required config values: {', '.join(missing)}")
