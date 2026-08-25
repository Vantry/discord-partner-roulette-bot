import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import os

logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for the Discord Partner Roulette Bot."""
    
    def __init__(self, db_path: str = "./data/bot.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        
    async def initialize(self):
        """Initialize the database and create all required tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
            -- Partners table
            CREATE TABLE IF NOT EXISTS partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                guild_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                lives INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                terminated_at TIMESTAMP,
                partner_message_id INTEGER,
                partner_channel_id INTEGER,
                application_data TEXT
            );
            
            -- Partner invites table
            CREATE TABLE IF NOT EXISTS partner_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                uses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            );
            
            -- User attribution table
            CREATE TABLE IF NOT EXISTS user_attribution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                partner_id INTEGER NOT NULL,
                invite_code TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            );
            
            -- Activity tracking table
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                category TEXT NOT NULL,
                points INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            );
            
            -- Weekly scores table
            CREATE TABLE IF NOT EXISTS weekly_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                rank INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id),
                UNIQUE(partner_id, week)
            );
            
            -- Roulette results table
            CREATE TABLE IF NOT EXISTS roulette_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                roll REAL NOT NULL,
                hit INTEGER NOT NULL,
                lives_before INTEGER NOT NULL,
                lives_after INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            );
            
            -- Message tracking for retention bonuses
            CREATE TABLE IF NOT EXISTS user_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                message_count INTEGER DEFAULT 0,
                last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, partner_id, week)
            );
            
            -- Voice time tracking
            CREATE TABLE IF NOT EXISTS voice_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                duration_minutes INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, partner_id, week)
            );
            
            -- Retention tracking (user must be active after 24h of join)
            CREATE TABLE IF NOT EXISTS retention_bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, partner_id)
            );
            
            -- Active user bonuses (weekly)
            CREATE TABLE IF NOT EXISTS active_user_bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                week INTEGER NOT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, partner_id, week)
            );
            
            -- Message cooldown tracking
            CREATE TABLE IF NOT EXISTS message_cooldown (
                user_id INTEGER PRIMARY KEY,
                last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_partners_status ON partners(status);
            CREATE INDEX IF NOT EXISTS idx_partner_invites_code ON partner_invites(invite_code);
            CREATE INDEX IF NOT EXISTS idx_user_attribution_user ON user_attribution(user_id);
            CREATE INDEX IF NOT EXISTS idx_activity_user_week ON activity(user_id, week);
            CREATE INDEX IF NOT EXISTS idx_weekly_scores_week ON weekly_scores(week);
            """)
            
            await db.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    # ============ PARTNER MANAGEMENT ============
    
    async def create_partner(self, guild_id: int, guild_name: str, application_data: str) -> int:
        """Create a new partner application."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO partners (guild_id, guild_name, status, application_data)
                   VALUES (?, ?, 'pending', ?)""",
                (guild_id, guild_name, application_data)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def approve_partner(self, partner_id: int) -> bool:
        """Approve a partner application."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE partners 
                   SET status = 'active', lives = ?, approved_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (3, partner_id)
            )
            await db.commit()
            return True
    
    async def get_partner(self, partner_id: int) -> Optional[Dict]:
        """Get partner by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM partners WHERE id = ?",
                (partner_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_partner_by_guild(self, guild_id: int) -> Optional[Dict]:
        """Get partner by guild ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM partners WHERE guild_id = ?",
                (guild_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_all_active_partners(self) -> List[Dict]:
        """Get all active partners."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM partners WHERE status = 'active' ORDER BY id ASC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def terminate_partner(self, partner_id: int) -> bool:
        """Terminate a partnership."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE partners 
                   SET status = 'terminated', terminated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (partner_id,)
            )
            await db.commit()
            return True
    
    async def update_partner_lives(self, partner_id: int, lives: int) -> bool:
        """Update partner lives."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE partners SET lives = ? WHERE id = ?",
                (lives, partner_id)
            )
            await db.commit()
            return True
    
    async def update_partner_message(self, partner_id: int, message_id: int, channel_id: int) -> bool:
        """Update partner message IDs."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE partners 
                   SET partner_message_id = ?, partner_channel_id = ?
                   WHERE id = ?""",
                (message_id, channel_id, partner_id)
            )
            await db.commit()
            return True
    
    # ============ INVITE MANAGEMENT ============
    
    async def create_invite(self, partner_id: int, invite_code: str) -> bool:
        """Create a partner invite."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO partner_invites (partner_id, invite_code) VALUES (?, ?)",
                (partner_id, invite_code)
            )
            await db.commit()
            return True
    
    async def get_invite_by_code(self, invite_code: str) -> Optional[Dict]:
        """Get invite info by code."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM partner_invites WHERE invite_code = ?",
                (invite_code,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_invites_by_partner(self, partner_id: int) -> List[Dict]:
        """Get all invites for a partner."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM partner_invites WHERE partner_id = ?",
                (partner_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_invite_uses(self, invite_code: str, uses: int) -> bool:
        """Update invite uses count."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE partner_invites SET uses = ? WHERE invite_code = ?",
                (uses, invite_code)
            )
            await db.commit()
            return True
    
    # ============ USER ATTRIBUTION ============
    
    async def attribute_user(self, user_id: int, partner_id: int, invite_code: str) -> bool:
        """Attribute a user to a partner."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """INSERT INTO user_attribution (user_id, partner_id, invite_code)
                       VALUES (?, ?, ?)""",
                    (user_id, partner_id, invite_code)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                logger.warning(f"User {user_id} already attributed")
                return False
    
    async def get_user_attribution(self, user_id: int) -> Optional[Dict]:
        """Get user's partner attribution."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_attribution WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_attributed_users(self, partner_id: int, week: int) -> List[int]:
        """Get all users attributed to a partner in a week."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT user_id FROM user_attribution WHERE partner_id = ?",
                (partner_id,)
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # ============ ACTIVITY TRACKING ============
    
    async def add_activity(self, user_id: int, partner_id: int, week: int, category: str, points: int) -> bool:
        """Add activity points."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO activity (user_id, partner_id, week, category, points)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, partner_id, week, category, points)
            )
            await db.commit()
            return True
    
    async def get_activity_summary(self, partner_id: int, week: int) -> int:
        """Get total activity points for a partner in a week."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT COALESCE(SUM(points), 0) as total 
                   FROM activity WHERE partner_id = ? AND week = ?""",
                (partner_id, week)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    async def get_user_activity_in_week(self, user_id: int, partner_id: int, week: int, category: str) -> int:
        """Get user's activity count in a specific category for a week."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT COALESCE(COUNT(*), 0) as count
                   FROM activity WHERE user_id = ? AND partner_id = ? AND week = ? AND category = ?""",
                (user_id, partner_id, week, category)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    # ============ WEEKLY SCORES ============
    
    async def save_weekly_score(self, partner_id: int, week: int, points: int, rank: int, status: str) -> bool:
        """Save weekly score for a partner."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO weekly_scores (partner_id, week, points, rank, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (partner_id, week, points, rank, status)
            )
            await db.commit()
            return True
    
    async def get_weekly_score(self, partner_id: int, week: int) -> Optional[Dict]:
        """Get weekly score for a partner."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM weekly_scores WHERE partner_id = ? AND week = ?",
                (partner_id, week)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_weekly_ranking(self, week: int) -> List[Dict]:
        """Get full ranking for a week."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT ws.*, p.guild_name 
                   FROM weekly_scores ws
                   JOIN partners p ON ws.partner_id = p.id
                   WHERE ws.week = ?
                   ORDER BY ws.points DESC""",
                (week,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def reset_weekly_scores(self, week: int) -> bool:
        """Reset all weekly scores for a new week."""
        async with aiosqlite.connect(self.db_path) as db:
            # Initialize all active partners with 0 points
            await db.execute(
                """INSERT INTO weekly_scores (partner_id, week, points, rank, status)
                   SELECT id, ?, 0, NULL, NULL FROM partners WHERE status = 'active'""",
                (week,)
            )
            await db.commit()
            return True
    
    # ============ ROULETTE RESULTS ============
    
    async def save_roulette_result(self, partner_id: int, week: int, roll: float, hit: bool, lives_before: int, lives_after: int) -> bool:
        """Save roulette result."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO roulette_results (partner_id, week, roll, hit, lives_before, lives_after)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (partner_id, week, roll, 1 if hit else 0, lives_before, lives_after)
            )
            await db.commit()
            return True
    
    async def get_roulette_result(self, partner_id: int, week: int) -> Optional[Dict]:
        """Get roulette result for a partner in a week."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM roulette_results WHERE partner_id = ? AND week = ?",
                (partner_id, week)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # ============ RETENTION & BONUSES ============
    
    async def grant_retention_bonus(self, user_id: int, partner_id: int) -> bool:
        """Grant retention bonus (only once per user/partner)."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO retention_bonuses (user_id, partner_id) VALUES (?, ?)",
                    (user_id, partner_id)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False
    
    async def has_retention_bonus(self, user_id: int, partner_id: int) -> bool:
        """Check if user already received retention bonus."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM retention_bonuses WHERE user_id = ? AND partner_id = ?",
                (user_id, partner_id)
            )
            row = await cursor.fetchone()
            return row is not None
    
    async def grant_active_bonus(self, user_id: int, partner_id: int, week: int) -> bool:
        """Grant active user bonus (once per user per week)."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO active_user_bonuses (user_id, partner_id, week) VALUES (?, ?, ?)",
                    (user_id, partner_id, week)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False
    
    async def has_active_bonus(self, user_id: int, partner_id: int, week: int) -> bool:
        """Check if user already received active bonus for week."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM active_user_bonuses WHERE user_id = ? AND partner_id = ? AND week = ?",
                (user_id, partner_id, week)
            )
            row = await cursor.fetchone()
            return row is not None
    
    # ============ MESSAGE COOLDOWN ============
    
    async def can_grant_message_points(self, user_id: int, cooldown_seconds: int) -> bool:
        """Check if user can receive message points (cooldown check)."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT last_message_time FROM message_cooldown WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return True
            
            last_time = datetime.fromisoformat(row[0])
            time_passed = (datetime.utcnow() - last_time).total_seconds()
            return time_passed >= cooldown_seconds
    
    async def update_message_cooldown(self, user_id: int) -> bool:
        """Update message cooldown timestamp."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO message_cooldown (user_id, last_message_time)
                   VALUES (?, CURRENT_TIMESTAMP)""",
                (user_id,)
            )
            await db.commit()
            return True
    
    # ============ VOICE TRACKING ============
    
    async def add_voice_time(self, user_id: int, partner_id: int, week: int, minutes: int) -> bool:
        """Add voice time minutes."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO voice_activity (user_id, partner_id, week, duration_minutes)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, partner_id, week) 
                   DO UPDATE SET duration_minutes = duration_minutes + ?, last_active = CURRENT_TIMESTAMP""",
                (user_id, partner_id, week, minutes, minutes)
            )
            await db.commit()
            return True
    
    async def get_voice_time(self, user_id: int, partner_id: int, week: int) -> int:
        """Get total voice time for user in week."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT COALESCE(duration_minutes, 0) FROM voice_activity 
                   WHERE user_id = ? AND partner_id = ? AND week = ?""",
                (user_id, partner_id, week)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    # ============ UTILITY ============
    
    async def get_current_week(self) -> int:
        """Get current week number (ISO week)."""
        return datetime.utcnow().isocalendar()[1]
    
    async def close(self):
        """Close database connection."""
        pass
