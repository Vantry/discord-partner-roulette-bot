import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import discord
from discord import Embed, Color

logger = logging.getLogger(__name__)


class ActivityCategory(str, Enum):
    """Activity categories for tracking."""
    MESSAGE = "message"
    JOIN = "join"
    RETENTION = "retention"
    ACTIVE_USER = "active_user"
    VOICE = "voice"


class PartnerStatus(str, Enum):
    """Partner status states."""
    PENDING = "pending"
    ACTIVE = "active"
    RISK = "risk"
    SAFE = "safe"
    TERMINATED = "terminated"


class Utils:
    """Utility functions for the bot."""
    
    @staticmethod
    def get_current_week() -> int:
        """Get current ISO week number."""
        return datetime.utcnow().isocalendar()[1]
    
    @staticmethod
    def get_week_date_range(week: int, year: int = None) -> tuple:
        """Get start and end date of a week."""
        if year is None:
            year = datetime.utcnow().year
        
        jan4 = datetime(year, 1, 4)
        week_one_monday = jan4 - timedelta(days=jan4.weekday())
        week_start = week_one_monday + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)
        
        return week_start, week_end
    
    @staticmethod
    def create_partner_embed(partner_data: Dict, week: int, score: int, rank: Optional[int] = None, status: Optional[str] = None) -> Embed:
        """Create a partner info embed."""
        embed = Embed(
            title=f"🕯️ PARTNER",
            description=f"**{partner_data['guild_name']}**",
            color=Color.dark_theme()
        )
        
        # Parse application data
        try:
            app_data = json.loads(partner_data['application_data']) if isinstance(partner_data['application_data'], str) else partner_data['application_data']
            if 'theme' in app_data:
                embed.add_field(name="🎮", value=app_data['theme'], inline=True)
            if 'description' in app_data:
                embed.add_field(name="📝", value=app_data['description'][:200], inline=False)
            if 'members' in app_data:
                embed.add_field(name="👥", value=f"{app_data['members']} Members", inline=True)
        except:
            pass
        
        # Lives display
        lives = partner_data.get('lives', 3)
        hearts = "❤️" * lives + "🖤" * (3 - lives)
        embed.add_field(name="Lives", value=hearts, inline=True)
        
        # Score display
        embed.add_field(name=f"📊 Week {week}", value=f"{score} XP", inline=True)
        
        # Rank and status
        if rank:
            embed.add_field(name="🏆", value=f"Platz #{rank}", inline=True)
        
        if status:
            status_emoji = "🟢" if status == "safe" else "🔴"
            embed.add_field(name="Status", value=f"{status_emoji} {status.upper()}", inline=True)
        
        embed.set_footer(text="Partner Roulette System")
        embed.timestamp = datetime.utcnow()
        
        return embed
    
    @staticmethod
    def create_lives_bar(lives: int, max_lives: int = 3) -> str:
        """Create a visual representation of lives."""
        hearts = "❤️" * lives + "🖤" * (max_lives - lives)
        return hearts
    
    @staticmethod
    def calculate_safe_risk_zones(partners: List[Dict]) -> tuple:
        """Calculate safe and risk zones based on 70/30 rule."""
        if not partners:
            return [], []
        
        safe_count = max(1, int(len(partners) * 0.70))
        
        safe = partners[:safe_count]
        risk = partners[safe_count:]
        
        return safe, risk
    
    @staticmethod
    async def log_moderation_action(mod_id: int, action: str, target: str, reason: str = "", mod_channel=None):
        """Log a moderation action."""
        logger.info(f"MOD ACTION: {action} | Target: {target} | Mod: {mod_id} | Reason: {reason}")
        
        if mod_channel:
            try:
                embed = Embed(
                    title="🔨 Moderation Action",
                    color=Color.red()
                )
                embed.add_field(name="Action", value=action, inline=False)
                embed.add_field(name="Target", value=target, inline=False)
                if reason:
                    embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Moderator", value=f"<@{mod_id}>", inline=False)
                embed.timestamp = datetime.utcnow()
                
                await mod_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to log moderation action: {e}")
    
    @staticmethod
    def create_ranking_embed(week: int, safe_partners: List[Dict], risk_partners: List[Dict]) -> Embed:
        """Create a ranking embed for the event."""
        embed = Embed(
            title="🛡️ WEEKLY RANKING",
            color=Color.dark_theme()
        )
        
        # Safe zone
        safe_text = ""
        for i, partner in enumerate(safe_partners[:7], 1):
            safe_text += f"#{i} **{partner['guild_name']}** - {partner['points']} XP\n"
        
        if safe_text:
            embed.add_field(name="🟢 SAFE ZONE (Top 70%)", value=safe_text, inline=False)
        
        # Risk zone
        risk_text = ""
        for i, partner in enumerate(risk_partners, 1):
            rank_num = len(safe_partners) + i
            risk_text += f"#{rank_num} **{partner['guild_name']}** - {partner['points']} XP\n"
        
        if risk_text:
            embed.add_field(name="🔴 RISK ZONE (Bottom 30%)", value=risk_text, inline=False)
        
        embed.timestamp = datetime.utcnow()
        return embed
    
    @staticmethod
    def create_countdown_embed(seconds: int) -> Embed:
        """Create countdown embed."""
        embed = Embed(
            title="🔫 SYSTEM ARMED",
            description=f"```\n{seconds:02d}\n```",
            color=Color.dark_red()
        )
        return embed
    
    @staticmethod
    def create_roulette_intro_embed(partner_count: int, risk_count: int) -> Embed:
        """Create roulette intro embed."""
        embed = Embed(
            title="🕯️ PARTNER ROULETTE",
            description="The weekly reckoning begins.\n\n"
                       f"{partner_count} PARTNERS\n"
                       "3 LIVES\n"
                       f"{risk_count} IN RISK\n\n"
                       "The game is about to begin.",
            color=Color.dark_theme()
        )
        return embed
    
    @staticmethod
    def create_lockdown_embed() -> Embed:
        """Create lockdown embed."""
        embed = Embed(
            title="🔒 RISK ZONE LOCKED",
            description="The rankings are final.\n\n"
                       "No further changes.\n\n"
                       "The system is armed.",
            color=Color.dark_red()
        )
        return embed
    
    @staticmethod
    def create_click_embed() -> Embed:
        """Create click embed."""
        embed = Embed(
            title="🔫 CLICK.",
            color=Color.dark_red()
        )
        return embed
    
    @staticmethod
    def create_miss_embed(partner_name: str) -> Embed:
        """Create miss result embed."""
        embed = Embed(
            title=f"🎯 {partner_name.upper()}",
            description="CLICK.\n\n😮‍💨 MISS.\n\n"
                       f"{partner_name} survives.",
            color=Color.green()
        )
        return embed
    
    @staticmethod
    def create_hit_embed(partner_name: str) -> Embed:
        """Create hit result embed."""
        embed = Embed(
            title=f"🎯 {partner_name.upper()}",
            description="CLICK.\n\n…",
            color=Color.red()
        )
        return embed
    
    @staticmethod
    def create_life_lost_embed(partner_name: str, lives_remaining: int) -> Embed:
        """Create life lost embed."""
        hearts = "❤️" * lives_remaining + "🖤" * (3 - lives_remaining)
        embed = Embed(
            title="☠️ LIFE LOST",
            description=f"{partner_name}\n\n"
                       f"{hearts}\n\n"
                       f"{lives_remaining} LIVES REMAIN",
            color=Color.dark_red()
        )
        return embed
    
    @staticmethod
    def create_final_life_embed(partner_name: str) -> Embed:
        """Create final life lost embed."""
        embed = Embed(
            title="☠️ FINAL LIFE LOST",
            description=f"{partner_name}\n\n"
                       "💥 BOOM.\n\n"
                       "The partnership has ended.\n\n"
                       "0 LIVES REMAIN.",
            color=Color.dark_red()
        )
        return embed
    
    @staticmethod
    def create_application_review_embed(app_data: Dict) -> Embed:
        """Create application review embed for moderators."""
        embed = Embed(
            title="🕯️ PARTNER APPLICATION",
            color=Color.gold()
        )
        
        embed.add_field(name="Server Name", value=app_data.get('server_name', 'N/A'), inline=False)
        embed.add_field(name="Server ID", value=app_data.get('server_id', 'N/A'), inline=True)
        embed.add_field(name="Members", value=app_data.get('members', 'N/A'), inline=True)
        embed.add_field(name="Theme", value=app_data.get('theme', 'N/A'), inline=False)
        embed.add_field(name="Description", value=app_data.get('description', 'N/A')[:300], inline=False)
        embed.add_field(name="Why Partner?", value=app_data.get('why_partner', 'N/A')[:300], inline=False)
        
        if 'website' in app_data and app_data['website']:
            embed.add_field(name="Website", value=app_data['website'], inline=True)
        
        embed.set_footer(text="Use Accept/Reject buttons below")
        embed.timestamp = datetime.utcnow()
        
        return embed


class RouletteMath:
    """Mathematical functions for roulette system."""
    
    @staticmethod
    def calculate_elimination_chance() -> float:
        """1 in 7 chance."""
        return 1.0 / 7.0
    
    @staticmethod
    def simulate_roulette_spin() -> float:
        """Simulate a roulette spin (0.0 to 1.0)."""
        import random
        return random.random()
    
    @staticmethod
    def check_hit(roll: float, chance: float = 1.0/7.0) -> bool:
        """Check if roll results in a hit."""
        return roll < chance
    
    @staticmethod
    def calculate_voice_points(minutes: int, interval: int = 300, points_per_interval: int = 1) -> int:
        """Calculate voice points based on duration."""
        # 300 seconds (5 min) = 1 point
        intervals = minutes * 60 // interval
        return min(intervals * points_per_interval, 120)  # Cap at 120 points per week


class Validators:
    """Validation utilities."""
    
    @staticmethod
    def is_valid_discord_id(user_id) -> bool:
        """Validate Discord ID format."""
        try:
            return int(user_id) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_application_data(data: Dict) -> bool:
        """Validate partner application data."""
        required_fields = ['server_name', 'server_id', 'members', 'theme', 'description', 'why_partner']
        return all(field in data and data[field] for field in required_fields)
    
    @staticmethod
    def validate_invite_code(code: str) -> bool:
        """Validate Discord invite code format."""
        if not code or len(code) < 2:
            return False
        return all(c.isalnum() or c in '-_' for c in code)


class ErrorHandler:
    """Error handling utilities."""
    
    @staticmethod
    async def safe_delete_message(message: discord.Message):
        """Safely delete a message without crashing."""
        try:
            if message:
                await message.delete()
                logger.info(f"Deleted message {message.id}")
        except discord.NotFound:
            logger.warning(f"Message {message.id} not found (already deleted)")
        except discord.Forbidden:
            logger.error(f"No permission to delete message {message.id}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
    
    @staticmethod
    async def safe_edit_message(message: discord.Message, **kwargs):
        """Safely edit a message without crashing."""
        try:
            if message:
                await message.edit(**kwargs)
                logger.info(f"Edited message {message.id}")
        except discord.NotFound:
            logger.warning(f"Message {message.id} not found (cannot edit)")
        except discord.Forbidden:
            logger.error(f"No permission to edit message {message.id}")
        except Exception as e:
            logger.error(f"Error editing message: {e}")
    
    @staticmethod
    async def safe_get_invite(bot, invite_code: str) -> Optional[discord.Invite]:
        """Safely get an invite without crashing."""
        try:
            invite = await bot.fetch_invite(invite_code)
            return invite
        except discord.NotFound:
            logger.warning(f"Invite {invite_code} not found")
            return None
        except discord.Forbidden:
            logger.error(f"No permission to fetch invite {invite_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching invite {invite_code}: {e}")
            return None
    
    @staticmethod
    async def safe_send_embed(channel: discord.TextChannel, embed: discord.Embed) -> Optional[discord.Message]:
        """Safely send an embed."""
        try:
            if channel:
                return await channel.send(embed=embed)
        except discord.Forbidden:
            logger.error(f"No permission to send message in {channel.id}")
        except Exception as e:
            logger.error(f"Error sending embed: {e}")
        return None
