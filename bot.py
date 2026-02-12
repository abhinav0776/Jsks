import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import aiohttp
from collections import defaultdict
import time

# Bot Configuration
PREFIX = "+"
INTENTS = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=INTENTS, help_command=None)

# Global Data Storage
USER_DATA_FILE = "user_data.json"
MATCH_DATA_FILE = "match_data.json"
GUILD_SETTINGS_FILE = "guild_settings.json"

# In-memory storage
user_data = {}
active_matches = {}
guild_settings = {}
pending_challenges = {}
match_history = {}
pending_4v4_teams = {}
pending_2v2_teams = {}
pending_gauntlet = {}
pending_rumble = {}

# Rate limit tracking
command_cooldowns = defaultdict(lambda: defaultdict(float))
COOLDOWN_TIMES = {
    "chall": 5,
    "2v2": 10,
    "4v4": 10,
    "gauntlet": 15,
    "royalrumble": 20,
    "daily": 86400,  # 24 hours
    "give": 30
}

# Constants
MATCH_TIMEOUT = 50  # seconds per turn
WARNING_INTERVALS = [45, 40, 35, 30, 25, 20, 15, 10, 5]  # countdown warnings
DEFAULT_STARTING_COINS = 1000
MATCH_REWARDS = {
    "1v1": {"winner": 100, "loser": 25},
    "2v2": {"winner": 150, "loser": 40},
    "4v4": {"winner": 200, "loser": 50},
    "gauntlet": {"winner": 500, "participant": 100},
    "royal_rumble": {"winner": 1000, "top3": 500, "participant": 150}
}

# WWE Wrestler Database
WWE_WRESTLERS = [
    "John Cena", "AJ Styles", "Roman Reigns", "Seth Rollins", "The Rock",
    "Stone Cold Steve Austin", "The Undertaker", "Randy Orton", "Triple H",
    "Shawn Michaels", "Brock Lesnar", "CM Punk", "Edge", "Batista",
    "Rey Mysterio", "Eddie Guerrero", "Chris Jericho", "Kurt Angle",
    "Hulk Hogan", "Ric Flair", "Bret Hart", "Goldberg", "Kevin Owens",
    "Sami Zayn", "Finn Balor", "Drew McIntyre", "Bobby Lashley", "Becky Lynch",
    "Charlotte Flair", "Sasha Banks", "Bayley", "Asuka", "Rhea Ripley",
    "Bianca Belair", "Cody Rhodes", "LA Knight", "Gunther", "Damian Priest",
    "Dominik Mysterio", "Jey Uso", "Jimmy Uso", "Xavier Woods", "Kofi Kingston"
]

# Move Categories for validation
WWE_MOVES = {
    "strikes": ["punch", "kick", "elbow", "knee", "headbutt", "chop", "slap"],
    "grapples": ["suplex", "slam", "powerbomb", "piledriver", "ddt", "neckbreaker"],
    "submissions": ["armbar", "leg lock", "sleeper", "crossface", "sharpshooter"],
    "aerials": ["dive", "splash", "moonsault", "450", "frog splash", "senton"],
    "signature": ["spear", "rko", "stunner", "pedigree", "f5", "aa", "calf crusher"]
}

# ============================================================================
# RATE LIMIT FUNCTIONS
# ============================================================================

def check_cooldown(user_id: int, command_name: str) -> Tuple[bool, float]:
    """Check if user is on cooldown for a command"""
    if command_name not in COOLDOWN_TIMES:
        return True, 0
    
    current_time = time.time()
    last_used = command_cooldowns[user_id][command_name]
    cooldown_duration = COOLDOWN_TIMES[command_name]
    
    if current_time - last_used < cooldown_duration:
        remaining = cooldown_duration - (current_time - last_used)
        return False, remaining
    
    return True, 0

def set_cooldown(user_id: int, command_name: str):
    """Set cooldown for a command"""
    command_cooldowns[user_id][command_name] = time.time()

async def safe_send(channel, *args, **kwargs):
    """Send message with rate limit handling"""
    try:
        return await channel.send(*args, **kwargs)
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limited
            retry_after = e.retry_after if hasattr(e, 'retry_after') else 1
            await asyncio.sleep(retry_after)
            return await channel.send(*args, **kwargs)
        raise

async def safe_add_reaction(message, emoji):
    """Add reaction with rate limit handling"""
    try:
        await message.add_reaction(emoji)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            retry_after = e.retry_after if hasattr(e, 'retry_after') else 1
            await asyncio.sleep(retry_after)
            await message.add_reaction(emoji)
    except:
        pass

async def safe_edit(message, *args, **kwargs):
    """Edit message with rate limit handling"""
    try:
        return await message.edit(*args, **kwargs)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            retry_after = e.retry_after if hasattr(e, 'retry_after') else 1
            await asyncio.sleep(retry_after)
            return await message.edit(*args, **kwargs)
        raise

# ============================================================================
# DATA PERSISTENCE FUNCTIONS
# ============================================================================

def load_data():
    """Load all persistent data from JSON files"""
    global user_data, match_history, guild_settings
    
    # Load user data
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                user_data = json.load(f)
        except:
            user_data = {}
    
    # Load match history
    if os.path.exists(MATCH_DATA_FILE):
        try:
            with open(MATCH_DATA_FILE, 'r') as f:
                match_history = json.load(f)
        except:
            match_history = {}
    
    # Load guild settings
    if os.path.exists(GUILD_SETTINGS_FILE):
        try:
            with open(GUILD_SETTINGS_FILE, 'r') as f:
                guild_settings = json.load(f)
        except:
            guild_settings = {}

def save_data():
    """Save all persistent data to JSON files"""
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(user_data, f, indent=4)
        
        with open(MATCH_DATA_FILE, 'w') as f:
            json.dump(match_history, f, indent=4)
        
        with open(GUILD_SETTINGS_FILE, 'w') as f:
            json.dump(guild_settings, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

# ============================================================================
# USER PROFILE MANAGEMENT
# ============================================================================

def get_user_profile(user_id: str):
    """Get or create user profile"""
    if user_id not in user_data:
        user_data[user_id] = {
            "coins": DEFAULT_STARTING_COINS,
            "wins": 0,
            "losses": 0,
            "total_matches": 0,
            "win_streak": 0,
            "best_streak": 0,
            "matches_played": {
                "1v1": 0,
                "2v2": 0,
                "4v4": 0,
                "gauntlet": 0,
                "royal_rumble": 0
            },
            "wins_by_mode": {
                "1v1": 0,
                "2v2": 0,
                "4v4": 0,
                "gauntlet": 0,
                "royal_rumble": 0
            },
            "achievements": [],
            "favorite_wrestler": None,
            "created_at": str(datetime.now()),
            "last_active": str(datetime.now()),
            "last_daily_claim": None
        }
        save_data()
    
    # Update last active
    user_data[user_id]["last_active"] = str(datetime.now())
    return user_data[user_id]

def update_user_stats(user_id: str, won: bool, match_type: str, coins_earned: int):
    """Update user statistics after a match"""
    profile = get_user_profile(user_id)
    
    profile["total_matches"] += 1
    profile["matches_played"][match_type] += 1
    profile["coins"] += coins_earned
    
    if won:
        profile["wins"] += 1
        profile["wins_by_mode"][match_type] += 1
        profile["win_streak"] += 1
        if profile["win_streak"] > profile["best_streak"]:
            profile["best_streak"] = profile["win_streak"]
    else:
        profile["losses"] += 1
        profile["win_streak"] = 0
    
    check_achievements(user_id)
    save_data()

def check_achievements(user_id: str):
    """Check and award achievements"""
    profile = user_data[user_id]
    achievements = profile["achievements"]
    
    # Achievement definitions
    achievement_list = [
        {"id": "first_win", "name": "First Blood", "desc": "Win your first match", "check": lambda p: p["wins"] >= 1},
        {"id": "win_10", "name": "Rising Star", "desc": "Win 10 matches", "check": lambda p: p["wins"] >= 10},
        {"id": "win_50", "name": "Superstar", "desc": "Win 50 matches", "check": lambda p: p["wins"] >= 50},
        {"id": "win_100", "name": "WWE Champion", "desc": "Win 100 matches", "check": lambda p: p["wins"] >= 100},
        {"id": "streak_5", "name": "On Fire", "desc": "Win 5 matches in a row", "check": lambda p: p["win_streak"] >= 5},
        {"id": "streak_10", "name": "Unstoppable", "desc": "Win 10 matches in a row", "check": lambda p: p["win_streak"] >= 10},
        {"id": "millionaire", "name": "Millionaire", "desc": "Earn 1,000,000 coins", "check": lambda p: p["coins"] >= 1000000},
        {"id": "gauntlet_winner", "name": "Gauntlet Master", "desc": "Win a gauntlet match", "check": lambda p: p["wins_by_mode"]["gauntlet"] >= 1},
        {"id": "rumble_winner", "name": "Royal Rumble Champion", "desc": "Win a Royal Rumble", "check": lambda p: p["wins_by_mode"]["royal_rumble"] >= 1},
        {"id": "veteran", "name": "Veteran", "desc": "Play 100 matches", "check": lambda p: p["total_matches"] >= 100}
    ]
    
    for achievement in achievement_list:
        if achievement["id"] not in achievements and achievement["check"](profile):
            achievements.append(achievement["id"])
            profile["coins"] += 500  # Bonus coins for achievement
            save_data()

# ============================================================================
# MATCH CLASS DEFINITIONS
# ============================================================================

class Match:
    """Base class for all match types"""
    def __init__(self, match_id: str, channel_id: int, match_type: str):
        self.match_id = match_id
        self.channel_id = channel_id
        self.match_type = match_type
        self.status = "pending"
        self.created_at = datetime.now()
        self.current_turn = 0
        self.last_gif_url = None
        self.last_move_description = None
        self.last_attacker = None
        self.turn_start_time = None
        self.timer_task = None
        self.warning_count = 0
        
    async def start_turn_timer(self, channel, defender_id):
        """Start countdown timer for current turn"""
        self.turn_start_time = datetime.now()
        remaining = MATCH_TIMEOUT
        
        while remaining > 0:
            await asyncio.sleep(1)
            remaining -= 1
            
            # Check if match still exists and is active
            if self.match_id not in active_matches or active_matches[self.match_id].status != "active":
                return
            
            # Send warnings at specific intervals (with rate limit protection)
            if remaining in WARNING_INTERVALS and self.warning_count < 3:
                try:
                    await safe_send(channel, f"⏰ **{remaining} seconds remaining** for <@{defender_id}> to counter!")
                    self.warning_count += 1
                    await asyncio.sleep(0.5)  # Small delay to avoid rate limits
                except:
                    pass
        
        # Time's up - defender loses
        await self.handle_timeout(channel, defender_id)
    
    async def handle_timeout(self, channel, defender_id):
        """Handle timeout - defender loses"""
        pass  # Overridden in subclasses

class OneVsOneMatch(Match):
    """1v1 Match"""
    def __init__(self, match_id: str, channel_id: int, player1_id: int, player2_id: int):
        super().__init__(match_id, channel_id, "1v1")
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.current_defender = player2_id
        self.scores = {player1_id: 0, player2_id: 0}
        
    async def handle_timeout(self, channel, defender_id):
        """Player who didn't respond in time loses"""
        self.status = "finished"
        
        # Determine winner
        attacker_id = self.player1_id if defender_id == self.player2_id else self.player2_id
        
        # Award coins
        winner_coins = MATCH_REWARDS["1v1"]["winner"]
        loser_coins = MATCH_REWARDS["1v1"]["loser"]
        
        update_user_stats(str(attacker_id), True, "1v1", winner_coins)
        update_user_stats(str(defender_id), False, "1v1", loser_coins)
        
        embed = discord.Embed(
            title="⏰ TIME'S UP!",
            description=f"<@{defender_id}> failed to respond in time!\n<@{attacker_id}> wins by timeout!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Winner", value=f"<@{attacker_id}>", inline=True)
        embed.add_field(name="Coins Earned", value=f"💰 {winner_coins}", inline=True)
        
        await safe_send(channel, embed=embed)
        
        # Remove from active matches
        if self.match_id in active_matches:
            del active_matches[self.match_id]

class TwoVsTwoMatch(Match):
    """2v2 Tag Team Match"""
    def __init__(self, match_id: str, channel_id: int, team1: List[int], team2: List[int]):
        super().__init__(match_id, channel_id, "2v2")
        self.team1 = team1
        self.team2 = team2
        self.current_attacker_team = 1
        self.current_attacker_index = 0
        self.current_defender_team = 2
        self.current_defender_index = 0
        self.eliminated = []
        
    def get_current_attacker(self):
        """Get current attacker"""
        if self.current_attacker_team == 1:
            return self.team1[self.current_attacker_index]
        return self.team2[self.current_attacker_index]
    
    def get_current_defender(self):
        """Get current defender"""
        if self.current_defender_team == 1:
            return self.team1[self.current_defender_index]
        return self.team2[self.current_defender_index]
    
    async def handle_timeout(self, channel, defender_id):
        """Handle timeout in 2v2"""
        self.status = "finished"
        
        # Losing team
        losing_team = self.team1 if defender_id in self.team1 else self.team2
        winning_team = self.team2 if defender_id in self.team1 else self.team1
        
        # Award coins
        winner_coins = MATCH_REWARDS["2v2"]["winner"]
        loser_coins = MATCH_REWARDS["2v2"]["loser"]
        
        for player_id in winning_team:
            update_user_stats(str(player_id), True, "2v2", winner_coins)
        
        for player_id in losing_team:
            update_user_stats(str(player_id), False, "2v2", loser_coins)
        
        embed = discord.Embed(
            title="⏰ 2v2 MATCH - TIME'S UP!",
            description=f"<@{defender_id}> failed to respond!\nTeam {1 if defender_id in losing_team else 2} wins!",
            color=discord.Color.gold()
        )
        
        winners_mention = ", ".join([f"<@{p}>" for p in winning_team])
        embed.add_field(name="Winners", value=winners_mention, inline=False)
        embed.add_field(name="Coins Earned", value=f"💰 {winner_coins} each", inline=True)
        
        await safe_send(channel, embed=embed)
        
        if self.match_id in active_matches:
            del active_matches[self.match_id]

class FourVsFourMatch(Match):
    """4v4 Tag Team Match"""
    def __init__(self, match_id: str, channel_id: int, team1: List[int], team2: List[int]):
        super().__init__(match_id, channel_id, "4v4")
        self.team1 = team1
        self.team2 = team2
        self.current_attacker_team = 1
        self.current_attacker_index = 0
        self.current_defender_team = 2
        self.current_defender_index = 0
        self.eliminated = []
        
    def get_current_attacker(self):
        """Get current attacker"""
        if self.current_attacker_team == 1:
            return self.team1[self.current_attacker_index]
        return self.team2[self.current_attacker_index]
    
    def get_current_defender(self):
        """Get current defender"""
        if self.current_defender_team == 1:
            return self.team1[self.current_defender_index]
        return self.team2[self.current_defender_index]
    
    async def handle_timeout(self, channel, defender_id):
        """Handle timeout in 4v4"""
        self.status = "finished"
        
        losing_team = self.team1 if defender_id in self.team1 else self.team2
        winning_team = self.team2 if defender_id in self.team1 else self.team1
        
        winner_coins = MATCH_REWARDS["4v4"]["winner"]
        loser_coins = MATCH_REWARDS["4v4"]["loser"]
        
        for player_id in winning_team:
            update_user_stats(str(player_id), True, "4v4", winner_coins)
        
        for player_id in losing_team:
            update_user_stats(str(player_id), False, "4v4", loser_coins)
        
        embed = discord.Embed(
            title="⏰ 4v4 MATCH - TIME'S UP!",
            description=f"<@{defender_id}> failed to respond!\nTeam {1 if defender_id in losing_team else 2} wins!",
            color=discord.Color.gold()
        )
        
        winners_mention = ", ".join([f"<@{p}>" for p in winning_team])
        embed.add_field(name="Winners", value=winners_mention, inline=False)
        embed.add_field(name="Coins Earned", value=f"💰 {winner_coins} each", inline=True)
        
        await safe_send(channel, embed=embed)
        
        if self.match_id in active_matches:
            del active_matches[self.match_id]

class GauntletMatch(Match):
    """10-Man Gauntlet Match"""
    def __init__(self, match_id: str, channel_id: int, participants: List[int]):
        super().__init__(match_id, channel_id, "gauntlet")
        self.participants = participants.copy()
        self.eliminated = []
        self.current_fighter_index = 0
        self.challenger_index = 1
        self.is_attacker_turn = True  # Fighter starts attacking
        
    def get_current_fighter(self):
        """Get current fighter in ring"""
        if self.current_fighter_index < len(self.participants):
            return self.participants[self.current_fighter_index]
        return None
    
    def get_challenger(self):
        """Get current challenger"""
        if self.challenger_index < len(self.participants):
            return self.participants[self.challenger_index]
        return None
    
    async def handle_timeout(self, channel, defender_id):
        """Handle timeout in gauntlet"""
        # Defender is eliminated
        self.eliminated.append(defender_id)
        
        # Check if it was the fighter or challenger
        if defender_id == self.get_current_fighter():
            # Fighter lost, challenger becomes new fighter
            self.current_fighter_index = self.challenger_index
            self.challenger_index += 1
            
            if self.challenger_index >= len(self.participants):
                # No more challengers - current fighter wins!
                await self.end_gauntlet(channel, self.get_current_fighter())
                return
            
            await safe_send(channel, f"💥 <@{defender_id}> has been eliminated! <@{self.get_current_fighter()}> is the new fighter!\n<@{self.get_challenger()}> enters the match!")
        else:
            # Challenger lost, next challenger comes in
            self.challenger_index += 1
            
            if self.challenger_index >= len(self.participants):
                # No more challengers - fighter wins!
                await self.end_gauntlet(channel, self.get_current_fighter())
                return
            
            await safe_send(channel, f"💥 <@{defender_id}> has been eliminated!\n<@{self.get_challenger()}> enters the match!")
        
        # Reset turn
        self.is_attacker_turn = True
        self.last_gif_url = None
    
    async def end_gauntlet(self, channel, winner_id):
        """End gauntlet match"""
        self.status = "finished"
        
        winner_coins = MATCH_REWARDS["gauntlet"]["winner"]
        participant_coins = MATCH_REWARDS["gauntlet"]["participant"]
        
        update_user_stats(str(winner_id), True, "gauntlet", winner_coins)
        
        for participant in self.participants:
            if participant != winner_id:
                update_user_stats(str(participant), False, "gauntlet", participant_coins)
        
        embed = discord.Embed(
            title="🏆 GAUNTLET MATCH COMPLETE!",
            description=f"<@{winner_id}> has survived the gauntlet!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Champion", value=f"<@{winner_id}>", inline=True)
        embed.add_field(name="Coins Earned", value=f"💰 {winner_coins}", inline=True)
        embed.add_field(name="Eliminations", value=str(len(self.eliminated)), inline=True)
        
        await safe_send(channel, embed=embed)
        
        if self.match_id in active_matches:
            del active_matches[self.match_id]

class RoyalRumbleMatch(Match):
    """30-Man Royal Rumble"""
    def __init__(self, match_id: str, channel_id: int, participants: List[int]):
        super().__init__(match_id, channel_id, "royal_rumble")
        self.all_participants = participants.copy()
        self.in_ring = []
        self.eliminated = []
        self.entry_order = participants.copy()
        random.shuffle(self.entry_order)
        self.next_entry_index = 0
        self.current_attacker = None
        self.entry_interval = 90  # seconds between entries
        
    async def start_rumble(self, channel):
        """Start the Royal Rumble"""
        # First two entrants
        self.in_ring.append(self.entry_order[0])
        self.in_ring.append(self.entry_order[1])
        self.next_entry_index = 2
        self.current_attacker = self.in_ring[0]
        
        embed = discord.Embed(
            title="🔥 ROYAL RUMBLE STARTING!",
            description="The first two competitors are entering!",
            color=discord.Color.red()
        )
        embed.add_field(name="Entrant #1", value=f"<@{self.in_ring[0]}>", inline=True)
        embed.add_field(name="Entrant #2", value=f"<@{self.in_ring[1]}>", inline=True)
        
        await safe_send(channel, embed=embed)
        
        # Start entry timer
        asyncio.create_task(self.entry_timer(channel))
    
    async def entry_timer(self, channel):
        """Timer for new entries"""
        while self.next_entry_index < len(self.entry_order):
            await asyncio.sleep(self.entry_interval)
            
            if self.status != "active":
                return
            
            # New entrant
            new_entrant = self.entry_order[self.next_entry_index]
            self.in_ring.append(new_entrant)
            self.next_entry_index += 1
            
            await safe_send(channel, f"🎺 **Entrant #{self.next_entry_index}** <@{new_entrant}> enters the Royal Rumble!\n**{len(self.in_ring)} superstars in the ring!**")
    
    def eliminate_participant(self, participant_id):
        """Eliminate a participant"""
        if participant_id in self.in_ring:
            self.in_ring.remove(participant_id)
            self.eliminated.append(participant_id)
            
            # Check for winner
            if len(self.in_ring) == 1:
                return self.in_ring[0]
        return None
    
    async def handle_timeout(self, channel, defender_id):
        """Handle timeout in Royal Rumble"""
        # Eliminate the defender
        winner = self.eliminate_participant(defender_id)
        
        await safe_send(channel, f"💥 <@{defender_id}> has been eliminated from the Royal Rumble!\n**{len(self.in_ring)} remaining!**")
        
        if winner:
            await self.end_rumble(channel, winner)
    
    async def end_rumble(self, channel, winner_id):
        """End Royal Rumble"""
        self.status = "finished"
        
        winner_coins = MATCH_REWARDS["royal_rumble"]["winner"]
        top3_coins = MATCH_REWARDS["royal_rumble"]["top3"]
        participant_coins = MATCH_REWARDS["royal_rumble"]["participant"]
        
        # Top 3 finishers
        top3 = [winner_id] + self.eliminated[-2:]
        
        update_user_stats(str(winner_id), True, "royal_rumble", winner_coins)
        
        for participant in self.all_participants:
            if participant in top3[1:]:
                update_user_stats(str(participant), False, "royal_rumble", top3_coins)
            elif participant != winner_id:
                update_user_stats(str(participant), False, "royal_rumble", participant_coins)
        
        embed = discord.Embed(
            title="👑 ROYAL RUMBLE WINNER!",
            description=f"<@{winner_id}> wins the Royal Rumble!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Winner", value=f"<@{winner_id}>", inline=False)
        embed.add_field(name="Coins Earned", value=f"💰 {winner_coins}", inline=True)
        
        if len(top3) > 1:
            top3_mentions = "\n".join([f"{i+2}. <@{p}>" for i, p in enumerate(top3[1:])])
            embed.add_field(name="Final Standings", value=top3_mentions, inline=False)
        
        await safe_send(channel, embed=embed)
        
        if self.match_id in active_matches:
            del active_matches[self.match_id]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_gif(url: str) -> bool:
    """Check if URL is a GIF"""
    return url.lower().endswith('.gif') or 'tenor.com' in url.lower() or 'giphy.com' in url.lower()

def extract_gif_from_message(message: discord.Message) -> Optional[str]:
    """Extract GIF URL from message"""
    # Check attachments
    for attachment in message.attachments:
        if is_gif(attachment.url):
            return attachment.url
    
    # Check embeds
    for embed in message.embeds:
        if embed.image and is_gif(embed.image.url):
            return embed.image.url
        if embed.thumbnail and is_gif(embed.thumbnail.url):
            return embed.thumbnail.url
    
    # Check message content for URLs
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
    for url in urls:
        if is_gif(url):
            return url
    
    return None

def generate_match_id() -> str:
    """Generate unique match ID"""
    return f"match_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"

# ============================================================================
# BOT EVENTS
# ============================================================================

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'✅ {bot.user.name} is online!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Prefix: {PREFIX}')
    print('=' * 50)
    
    load_data()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{PREFIX}help | WWE Sage Bot"
        )
    )
    
    print(f'Loaded {len(user_data)} user profiles')
    print(f'Loaded {len(match_history)} match records')
    print('Bot is ready for action!')
    
    # Start background tasks
    save_data_task.start()
    cleanup_expired_challenges.start()

@bot.event
async def on_message(message):
    """Handle messages - check for GIF responses in active matches"""
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check if message is in a channel with an active match
    match = None
    for match_id, m in active_matches.items():
        if m.channel_id == message.channel.id and m.status == "active":
            match = m
            break
    
    if not match:
        return
    
    # Check if message contains a GIF
    gif_url = extract_gif_from_message(message)
    if not gif_url:
        return
    
    # Handle different match types
    if isinstance(match, OneVsOneMatch):
        await handle_1v1_gif(message, match, gif_url)
    elif isinstance(match, TwoVsTwoMatch):
        await handle_2v2_gif(message, match, gif_url)
    elif isinstance(match, FourVsFourMatch):
        await handle_4v4_gif(message, match, gif_url)
    elif isinstance(match, GauntletMatch):
        await handle_gauntlet_gif(message, match, gif_url)
    elif isinstance(match, RoyalRumbleMatch):
        await handle_rumble_gif(message, match, gif_url)

async def handle_1v1_gif(message, match, gif_url):
    """Handle GIF submission in 1v1 match"""
    user_id = message.author.id
    
    # First move - attacker (player1) must send first
    if match.current_turn == 0:
        if user_id != match.player1_id:
            await safe_send(message.channel, f"❌ <@{match.player1_id}> must send the first move!")
            return
        
        match.last_gif_url = gif_url
        match.last_attacker = user_id
        match.current_defender = match.player2_id
        match.current_turn += 1
        match.warning_count = 0
        
        await safe_add_reaction(message, "✅")
        await safe_send(message.channel, f"🔥 <@{match.player1_id}> attacks! <@{match.player2_id}>, you have **50 seconds** to counter with a GIF!")
        
        # Start timer
        asyncio.create_task(match.start_turn_timer(message.channel, match.player2_id))
    
    # Counter move
    elif user_id == match.current_defender:
        # Valid counter
        match.last_gif_url = gif_url
        attacker = match.last_attacker
        match.last_attacker = user_id
        match.current_defender = attacker
        match.current_turn += 1
        match.warning_count = 0
        
        await safe_add_reaction(message, "💥")
        
        # Random chance to end match after 5 moves
        if match.current_turn >= 5 and random.random() < 0.3:
            # Match ends - defender wins with this counter
            match.status = "finished"
            
            winner_coins = MATCH_REWARDS["1v1"]["winner"]
            loser_coins = MATCH_REWARDS["1v1"]["loser"]
            
            update_user_stats(str(user_id), True, "1v1", winner_coins)
            update_user_stats(str(attacker), False, "1v1", loser_coins)
            
            embed = discord.Embed(
                title="🏆 1v1 MATCH COMPLETE!",
                description=f"<@{user_id}> hits the final blow and wins!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Winner", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="Coins Earned", value=f"💰 {winner_coins}", inline=True)
            embed.add_field(name="Total Moves", value=str(match.current_turn), inline=True)
            embed.set_thumbnail(url=gif_url)
            
            await safe_send(message.channel, embed=embed)
            
            del active_matches[match.match_id]
        else:
            await safe_send(message.channel, f"💥 <@{user_id}> counters! <@{attacker}>, send your counter! (**50 seconds**)")
            asyncio.create_task(match.start_turn_timer(message.channel, attacker))
    
    elif user_id == match.last_attacker:
        await safe_send(message.channel, f"❌ Wait for <@{match.current_defender}> to counter first!")

async def handle_2v2_gif(message, match, gif_url):
    """Handle GIF submission in 2v2 match"""
    user_id = message.author.id
    
    # Check if user is part of the match
    if user_id not in match.team1 and user_id not in match.team2:
        return
    
    # First move
    if match.current_turn == 0:
        if user_id not in match.team1:
            await safe_send(message.channel, f"❌ Team 1 must attack first!")
            return
        
        match.last_gif_url = gif_url
        match.last_attacker = user_id
        match.current_turn += 1
        match.warning_count = 0
        
        defender = match.get_current_defender()
        
        await safe_add_reaction(message, "✅")
        await safe_send(message.channel, f"🔥 <@{user_id}> from Team 1 attacks! <@{defender}> from Team 2, counter! (**50 seconds**)")
        
        asyncio.create_task(match.start_turn_timer(message.channel, defender))
    
    # Counter moves
    else:
        current_defender = match.get_current_defender()
        
        if user_id != current_defender:
            await safe_send(message.channel, f"❌ It's <@{current_defender}>'s turn to counter!")
            return
        
        match.last_gif_url = gif_url
        match.last_attacker = user_id
        match.current_turn += 1
        match.warning_count = 0
        
        # Switch teams
        if match.current_attacker_team == 1:
            match.current_attacker_team = 2
            match.current_defender_team = 1
        else:
            match.current_attacker_team = 1
            match.current_defender_team = 2
        
        # Rotate team members
        if match.current_turn % 2 == 0:
            match.current_attacker_index = (match.current_attacker_index + 1) % 2
            match.current_defender_index = (match.current_defender_index + 1) % 2
        
        next_defender = match.get_current_defender()
        
        await safe_add_reaction(message, "💥")
        
        # Random chance to end match after 10 moves
        if match.current_turn >= 10 and random.random() < 0.25:
            match.status = "finished"
            
            winning_team = match.team1 if user_id in match.team1 else match.team2
            losing_team = match.team2 if user_id in match.team1 else match.team1
            
            winner_coins = MATCH_REWARDS["2v2"]["winner"]
            loser_coins = MATCH_REWARDS["2v2"]["loser"]
            
            for player_id in winning_team:
                update_user_stats(str(player_id), True, "2v2", winner_coins)
            
            for player_id in losing_team:
                update_user_stats(str(player_id), False, "2v2", loser_coins)
            
            team_num = 1 if user_id in match.team1 else 2
            winners_mention = ", ".join([f"<@{p}>" for p in winning_team])
            
            embed = discord.Embed(
                title="🏆 2v2 TAG TEAM MATCH COMPLETE!",
                description=f"Team {team_num} wins with a devastating finisher!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Winners", value=winners_mention, inline=False)
            embed.add_field(name="Coins Earned", value=f"💰 {winner_coins} each", inline=True)
            embed.set_thumbnail(url=gif_url)
            
            await safe_send(message.channel, embed=embed)
            
            del active_matches[match.match_id]
        else:
            await safe_send(message.channel, f"💥 <@{user_id}> counters! <@{next_defender}>, your turn! (**50 seconds**)")
            asyncio.create_task(match.start_turn_timer(message.channel, next_defender))

async def handle_4v4_gif(message, match, gif_url):
    """Handle GIF submission in 4v4 match"""
    user_id = message.author.id
    
    if user_id not in match.team1 and user_id not in match.team2:
        return
    
    # First move
    if match.current_turn == 0:
        if user_id not in match.team1:
            await safe_send(message.channel, f"❌ Team 1 must attack first!")
            return
        
        match.last_gif_url = gif_url
        match.last_attacker = user_id
        match.current_turn += 1
        match.warning_count = 0
        
        defender = match.get_current_defender()
        
        await safe_add_reaction(message, "✅")
        await safe_send(message.channel, f"🔥 <@{user_id}> from Team 1 attacks! <@{defender}> from Team 2, counter! (**50 seconds**)")
        
        asyncio.create_task(match.start_turn_timer(message.channel, defender))
    
    else:
        current_defender = match.get_current_defender()
        
        if user_id != current_defender:
            await safe_send(message.channel, f"❌ It's <@{current_defender}>'s turn to counter!")
            return
        
        match.last_gif_url = gif_url
        match.last_attacker = user_id
        match.current_turn += 1
        match.warning_count = 0
        
        # Switch teams
        if match.current_attacker_team == 1:
            match.current_attacker_team = 2
            match.current_defender_team = 1
        else:
            match.current_attacker_team = 1
            match.current_defender_team = 2
        
        # Rotate through all 4 team members
        if match.current_turn % 2 == 0:
            match.current_attacker_index = (match.current_attacker_index + 1) % 4
            match.current_defender_index = (match.current_defender_index + 1) % 4
        
        next_defender = match.get_current_defender()
        
        await safe_add_reaction(message, "💥")
        
        # Random chance to end match after 15 moves
        if match.current_turn >= 15 and random.random() < 0.2:
            match.status = "finished"
            
            winning_team = match.team1 if user_id in match.team1 else match.team2
            losing_team = match.team2 if user_id in match.team1 else match.team1
            
            winner_coins = MATCH_REWARDS["4v4"]["winner"]
            loser_coins = MATCH_REWARDS["4v4"]["loser"]
            
            for player_id in winning_team:
                update_user_stats(str(player_id), True, "4v4", winner_coins)
            
            for player_id in losing_team:
                update_user_stats(str(player_id), False, "4v4", loser_coins)
            
            team_num = 1 if user_id in match.team1 else 2
            winners_mention = ", ".join([f"<@{p}>" for p in winning_team])
            
            embed = discord.Embed(
                title="🏆 4v4 WAR GAMES COMPLETE!",
                description=f"Team {team_num} dominates the competition!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Winners", value=winners_mention, inline=False)
            embed.add_field(name="Coins Earned", value=f"💰 {winner_coins} each", inline=True)
            embed.set_thumbnail(url=gif_url)
            
            await safe_send(message.channel, embed=embed)
            
            del active_matches[match.match_id]
        else:
            await safe_send(message.channel, f"💥 <@{user_id}> counters! <@{next_defender}>, your turn! (**50 seconds**)")
            asyncio.create_task(match.start_turn_timer(message.channel, next_defender))

async def handle_gauntlet_gif(message, match, gif_url):
    """Handle GIF submission in gauntlet match"""
    user_id = message.author.id
    
    current_fighter = match.get_current_fighter()
    challenger = match.get_challenger()
    
    if user_id not in [current_fighter, challenger]:
        return
    
    # First move - fighter attacks
    if match.last_gif_url is None:
        if user_id != current_fighter:
            await safe_send(message.channel, f"❌ <@{current_fighter}> must attack first!")
            return
        
        match.last_gif_url = gif_url
        match.last_attacker = user_id
        match.is_attacker_turn = False
        match.warning_count = 0
        
        await safe_add_reaction(message, "✅")
        await safe_send(message.channel, f"🔥 <@{current_fighter}> attacks! <@{challenger}>, counter! (**50 seconds**)")
        
        asyncio.create_task(match.start_turn_timer(message.channel, challenger))
    
    # Counter move
    elif not match.is_attacker_turn and user_id == challenger:
        match.last_gif_url = gif_url
        match.is_attacker_turn = True
        match.warning_count = 0
        
        await safe_add_reaction(message, "💥")
        
        # 40% chance challenger wins and becomes new fighter
        if random.random() < 0.4:
            # Fighter is eliminated
            match.eliminated.append(current_fighter)
            match.current_fighter_index = match.challenger_index
            match.challenger_index += 1
            
            if match.challenger_index >= len(match.participants):
                # No more challengers - current challenger wins!
                await match.end_gauntlet(message.channel, user_id)
                return
            
            new_challenger = match.get_challenger()
            
            await safe_send(message.channel, f"💥 <@{user_id}> eliminates <@{current_fighter}>!\n<@{user_id}> is the new fighter!\n<@{new_challenger}> enters as the next challenger!")
            
            match.last_gif_url = None
        else:
            await safe_send(message.channel, f"💥 Great counter! <@{current_fighter}>, attack back! (**50 seconds**)")
            asyncio.create_task(match.start_turn_timer(message.channel, current_fighter))
    
    # Fighter attacks back
    elif match.is_attacker_turn and user_id == current_fighter:
        match.last_gif_url = gif_url
        match.is_attacker_turn = False
        match.warning_count = 0
        
        await safe_add_reaction(message, "🔥")
        
        # 30% chance fighter eliminates challenger
        if random.random() < 0.3:
            # Challenger eliminated
            match.eliminated.append(challenger)
            match.challenger_index += 1
            
            if match.challenger_index >= len(match.participants):
                # No more challengers - fighter wins!
                await match.end_gauntlet(message.channel, current_fighter)
                return
            
            new_challenger = match.get_challenger()
            
            await safe_send(message.channel, f"💥 <@{current_fighter}> eliminates <@{challenger}>!\n<@{new_challenger}> enters as the next challenger!")
            
            match.last_gif_url = None
        else:
            await safe_send(message.channel, f"💥 <@{current_fighter}> strikes back! <@{challenger}>, counter! (**50 seconds**)")
            asyncio.create_task(match.start_turn_timer(message.channel, challenger))

async def handle_rumble_gif(message, match, gif_url):
    """Handle GIF submission in Royal Rumble"""
    user_id = message.author.id
    
    if user_id not in match.in_ring:
        return
    
    # Anyone in the ring can attack anyone else
    # Extract mentioned users
    mentioned_users = [u.id for u in message.mentions if u.id in match.in_ring and u.id != user_id]
    
    if not mentioned_users:
        # Random target
        possible_targets = [p for p in match.in_ring if p != user_id]
        if not possible_targets:
            return
        target = random.choice(possible_targets)
    else:
        target = mentioned_users[0]
    
    await safe_add_reaction(message, "💥")
    
    # 20% chance of elimination
    if random.random() < 0.2:
        winner = match.eliminate_participant(target)
        
        await safe_send(message.channel, f"🚨 <@{user_id}> ELIMINATES <@{target}> over the top rope!\n**{len(match.in_ring)} remaining!**")
        
        if winner:
            await match.end_rumble(message.channel, winner)
    else:
        await safe_send(message.channel, f"💥 <@{user_id}> attacks <@{target}>! The battle continues!\n**{len(match.in_ring)} superstars fighting!**")

# ============================================================================
# MATCH SETUP COMMANDS
# ============================================================================

@bot.command(name='chall')
async def challenge_1v1(ctx, opponent: discord.Member = None):
    """Challenge someone to a 1v1 match: +chall @user"""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "chall")
    if not can_use:
        await safe_send(ctx, f"⏰ Please wait **{int(remaining)}** seconds before challenging again!")
        return
    
    if opponent is None:
        await safe_send(ctx, "❌ Usage: `+chall @user`")
        return
    
    if opponent.bot:
        await safe_send(ctx, "❌ You can't challenge a bot!")
        return
    
    if opponent.id == ctx.author.id:
        await safe_send(ctx, "❌ You can't challenge yourself!")
        return
    
    # Check if either user is already in a match
    for match in active_matches.values():
        if isinstance(match, OneVsOneMatch):
            if ctx.author.id in [match.player1_id, match.player2_id]:
                await safe_send(ctx, "❌ You're already in a match!")
                return
            if opponent.id in [match.player1_id, match.player2_id]:
                await safe_send(ctx, f"❌ {opponent.mention} is already in a match!")
                return
    
    # Set cooldown
    set_cooldown(ctx.author.id, "chall")
    
    # Create pending challenge
    challenge_id = f"{ctx.author.id}_{opponent.id}_{int(datetime.now().timestamp())}"
    pending_challenges[challenge_id] = {
        "challenger": ctx.author.id,
        "opponent": opponent.id,
        "channel": ctx.channel.id,
        "type": "1v1",
        "expires": datetime.now() + timedelta(minutes=5)
    }
    
    embed = discord.Embed(
        title="🥊 1v1 CHALLENGE!",
        description=f"{ctx.author.mention} challenges {opponent.mention} to a 1v1 match!",
        color=discord.Color.red()
    )
    embed.add_field(name="Accept", value=f"`+accept @{ctx.author.name}`", inline=True)
    embed.add_field(name="Decline", value=f"`+decline @{ctx.author.name}`", inline=True)
    embed.set_footer(text="Challenge expires in 5 minutes")
    
    await safe_send(ctx, embed=embed)

@bot.command(name='accept')
async def accept_challenge(ctx, challenger: discord.Member = None):
    """Accept a challenge: +accept @user"""
    if challenger is None:
        await safe_send(ctx, "❌ Usage: `+accept @user`")
        return
    
    # Find pending challenge
    challenge = None
    challenge_id = None
    
    for cid, c in pending_challenges.items():
        if c["opponent"] == ctx.author.id and c["challenger"] == challenger.id:
            if datetime.now() < c["expires"]:
                challenge = c
                challenge_id = cid
                break
    
    if not challenge:
        await safe_send(ctx, "❌ No active challenge found from this user!")
        return
    
    # Start the match based on type
    if challenge["type"] == "1v1":
        await start_1v1_match(ctx, challenger.id, ctx.author.id)
    
    # Remove challenge
    del pending_challenges[challenge_id]

@bot.command(name='decline')
async def decline_challenge(ctx, challenger: discord.Member = None):
    """Decline a challenge: +decline @user"""
    if challenger is None:
        await safe_send(ctx, "❌ Usage: `+decline @user`")
        return
    
    # Find and remove challenge
    for cid, c in list(pending_challenges.items()):
        if c["opponent"] == ctx.author.id and c["challenger"] == challenger.id:
            del pending_challenges[cid]
            await safe_send(ctx, f"❌ {ctx.author.mention} declined the challenge from {challenger.mention}")
            return
    
    await safe_send(ctx, "❌ No active challenge found from this user!")

async def start_1v1_match(ctx, player1_id: int, player2_id: int):
    """Start a 1v1 match"""
    match_id = generate_match_id()
    match = OneVsOneMatch(match_id, ctx.channel.id, player1_id, player2_id)
    match.status = "active"
    active_matches[match_id] = match
    
    embed = discord.Embed(
        title="🔥 1v1 MATCH STARTING!",
        description="Send GIFs of WWE moves to attack and counter!",
        color=discord.Color.green()
    )
    embed.add_field(name="Player 1", value=f"<@{player1_id}>", inline=True)
    embed.add_field(name="VS", value="⚔️", inline=True)
    embed.add_field(name="Player 2", value=f"<@{player2_id}>", inline=True)
    embed.add_field(
        name="Rules",
        value="• Send GIFs of WWE moves\n• Respond within 50 seconds\n• Counter your opponent's moves\n• First to fail loses!",
        inline=False
    )
    embed.add_field(name="First Move", value=f"<@{player1_id}>, send your attack GIF!", inline=False)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='2v2')
async def setup_2v2(ctx, mode: str = "quick"):
    """Setup a 2v2 match: +2v2 quick OR +2v2 @teammate @opponent1 @opponent2"""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "2v2")
    if not can_use:
        await safe_send(ctx, f"⏰ Please wait **{int(remaining)}** seconds before starting another 2v2!")
        return
    
    # Quick mode - people join with reactions
    if mode.lower() == "quick":
        team_id = f"2v2_{ctx.channel.id}_{int(datetime.now().timestamp())}"
        
        pending_2v2_teams[team_id] = {
            "creator": ctx.author.id,
            "channel_id": ctx.channel.id,
            "team1": [ctx.author.id],
            "team2": [],
            "message_id": None,
            "expires": datetime.now() + timedelta(minutes=5)
        }
        
        embed = discord.Embed(
            title="🔥 2v2 TAG TEAM - RECRUITING!",
            description=f"{ctx.author.mention} is starting a 2v2 match!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="How to Join",
            value="React with 1️⃣ to join Team 1\nReact with 2️⃣ to join Team 2",
            inline=False
        )
        embed.add_field(name="Team 1 (1/2)", value=f"1. {ctx.author.mention}", inline=True)
        embed.add_field(name="Team 2 (0/2)", value="Empty", inline=True)
        embed.set_footer(text="Match starts when both teams are full! • Expires in 5 minutes")
        
        msg = await safe_send(ctx, embed=embed)
        await safe_add_reaction(msg, "1️⃣")
        await safe_add_reaction(msg, "2️⃣")
        await safe_add_reaction(msg, "❌")
        
        pending_2v2_teams[team_id]["message_id"] = msg.id
        
        # Set cooldown
        set_cooldown(ctx.author.id, "2v2")
        
        # Start monitoring reactions
        asyncio.create_task(monitor_2v2_reactions(ctx, team_id, msg))
    
    # Manual mode - mention all players
    else:
        members = ctx.message.mentions
        
        if len(members) != 3:
            await safe_send(ctx, "❌ Usage: `+2v2 quick` OR `+2v2 @teammate @opponent1 @opponent2`")
            return
        
        team1 = [ctx.author.id, members[0].id]
        team2 = [members[1].id, members[2].id]
        
        # Validation
        all_players = team1 + team2
        if len(set(all_players)) != 4:
            await safe_send(ctx, "❌ All players must be different!")
            return
        
        for player in members:
            if player.bot:
                await safe_send(ctx, "❌ Bots cannot participate!")
                return
        
        # Set cooldown
        set_cooldown(ctx.author.id, "2v2")
        
        # Start match immediately
        await start_2v2_match(ctx, team1, team2)

async def monitor_2v2_reactions(ctx, team_id, message):
    """Monitor reactions for 2v2 team formation"""
    
    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            not user.bot and
            str(reaction.emoji) in ["1️⃣", "2️⃣", "❌"]
        )
    
    while team_id in pending_2v2_teams:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
            
            team_data = pending_2v2_teams.get(team_id)
            if not team_data:
                break
            
            # Cancel match
            if str(reaction.emoji) == "❌" and user.id == team_data["creator"]:
                await safe_send(ctx, f"❌ 2v2 match cancelled by {user.mention}")
                del pending_2v2_teams[team_id]
                break
            
            # Join Team 1
            if str(reaction.emoji) == "1️⃣":
                if user.id not in team_data["team1"] and user.id not in team_data["team2"]:
                    if len(team_data["team1"]) < 2:
                        team_data["team1"].append(user.id)
                    else:
                        await safe_send(ctx, f"❌ {user.mention} Team 1 is full!")
                        continue
            
            # Join Team 2
            elif str(reaction.emoji) == "2️⃣":
                if user.id not in team_data["team1"] and user.id not in team_data["team2"]:
                    if len(team_data["team2"]) < 2:
                        team_data["team2"].append(user.id)
                    else:
                        await safe_send(ctx, f"❌ {user.mention} Team 2 is full!")
                        continue
            
            # Update embed
            team1_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(team_data["team1"])])
            team2_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(team_data["team2"])]) if team_data["team2"] else "Empty"
            
            embed = discord.Embed(
                title="🔥 2v2 TAG TEAM - RECRUITING!",
                description=f"{ctx.author.mention} is starting a 2v2 match!",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="How to Join",
                value="React with 1️⃣ to join Team 1\nReact with 2️⃣ to join Team 2",
                inline=False
            )
            embed.add_field(name=f"Team 1 ({len(team_data['team1'])}/2)", value=team1_list, inline=True)
            embed.add_field(name=f"Team 2 ({len(team_data['team2'])}/2)", value=team2_list, inline=True)
            embed.set_footer(text="Match starts when both teams are full!")
            
            await safe_edit(message, embed=embed)
            
            # Check if teams are full
            if len(team_data["team1"]) == 2 and len(team_data["team2"]) == 2:
                del pending_2v2_teams[team_id]
                await safe_send(ctx, "✅ Both teams are full! Starting match...")
                await start_2v2_match(ctx, team_data["team1"], team_data["team2"])
                break
        
        except asyncio.TimeoutError:
            if team_id in pending_2v2_teams:
                del pending_2v2_teams[team_id]
                await safe_send(ctx, "⏰ 2v2 match recruitment timed out!")
            break

async def start_2v2_match(ctx, team1, team2):
    """Start a 2v2 match"""
    match_id = generate_match_id()
    match = TwoVsTwoMatch(match_id, ctx.channel.id, team1, team2)
    match.status = "active"
    active_matches[match_id] = match
    
    embed = discord.Embed(
        title="🔥 2v2 TAG TEAM MATCH!",
        description="Tag team action! Send GIFs to dominate!",
        color=discord.Color.purple()
    )
    embed.add_field(name="Team 1", value=f"<@{team1[0]}> & <@{team1[1]}>", inline=True)
    embed.add_field(name="VS", value="⚔️", inline=True)
    embed.add_field(name="Team 2", value=f"<@{team2[0]}> & <@{team2[1]}>", inline=True)
    embed.add_field(
        name="Rules",
        value="• Teams alternate attacking\n• Tag team members rotate\n• 50 seconds per turn\n• Teamwork wins!",
        inline=False
    )
    embed.add_field(name="First Move", value=f"Team 1, <@{team1[0]}>, attack!", inline=False)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='4v4')
async def setup_4v4(ctx, mode: str = "quick"):
    """Setup a 4v4 match: +4v4 quick OR +4v4 @p1 @p2 @p3 @p4 @p5 @p6 @p7"""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "4v4")
    if not can_use:
        await safe_send(ctx, f"⏰ Please wait **{int(remaining)}** seconds before starting another 4v4!")
        return
    
    # Quick mode - people join with reactions
    if mode.lower() == "quick":
        team_id = f"4v4_{ctx.channel.id}_{int(datetime.now().timestamp())}"
        
        pending_4v4_teams[team_id] = {
            "creator": ctx.author.id,
            "channel_id": ctx.channel.id,
            "team1": [ctx.author.id],
            "team2": [],
            "message_id": None,
            "expires": datetime.now() + timedelta(minutes=5)
        }
        
        embed = discord.Embed(
            title="🔥 4v4 WAR GAMES - RECRUITING!",
            description=f"{ctx.author.mention} is starting a 4v4 match!",
            color=discord.Color.dark_red()
        )
        embed.add_field(
            name="How to Join",
            value="React with 1️⃣ to join Team 1\nReact with 2️⃣ to join Team 2",
            inline=False
        )
        embed.add_field(name="Team 1 (1/4)", value=f"1. {ctx.author.mention}", inline=True)
        embed.add_field(name="Team 2 (0/4)", value="Empty", inline=True)
        embed.set_footer(text="Match starts when both teams are full! • Expires in 5 minutes")
        
        msg = await safe_send(ctx, embed=embed)
        await safe_add_reaction(msg, "1️⃣")
        await safe_add_reaction(msg, "2️⃣")
        await safe_add_reaction(msg, "❌")
        
        pending_4v4_teams[team_id]["message_id"] = msg.id
        
        # Set cooldown
        set_cooldown(ctx.author.id, "4v4")
        
        # Start monitoring reactions
        asyncio.create_task(monitor_4v4_reactions(ctx, team_id, msg))
    
    # Manual mode - mention all players
    else:
        members = ctx.message.mentions
        
        if len(members) != 7:
            await safe_send(ctx, "❌ Usage: `+4v4 quick` OR `+4v4 @teammate1 @teammate2 @teammate3 @opponent1 @opponent2 @opponent3 @opponent4`")
            return
        
        team1 = [ctx.author.id] + [m.id for m in members[:3]]
        team2 = [m.id for m in members[3:]]
        
        # Validation
        all_players = team1 + team2
        if len(set(all_players)) != 8:
            await safe_send(ctx, "❌ All players must be different!")
            return
        
        for player in members:
            if player.bot:
                await safe_send(ctx, "❌ Bots cannot participate!")
                return
        
        # Set cooldown
        set_cooldown(ctx.author.id, "4v4")
        
        # Start match immediately
        await start_4v4_match(ctx, team1, team2)

async def monitor_4v4_reactions(ctx, team_id, message):
    """Monitor reactions for 4v4 team formation"""
    
    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            not user.bot and
            str(reaction.emoji) in ["1️⃣", "2️⃣", "❌"]
        )
    
    while team_id in pending_4v4_teams:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
            
            team_data = pending_4v4_teams.get(team_id)
            if not team_data:
                break
            
            # Cancel match
            if str(reaction.emoji) == "❌" and user.id == team_data["creator"]:
                await safe_send(ctx, f"❌ 4v4 match cancelled by {user.mention}")
                del pending_4v4_teams[team_id]
                break
            
            # Join Team 1
            if str(reaction.emoji) == "1️⃣":
                if user.id not in team_data["team1"] and user.id not in team_data["team2"]:
                    if len(team_data["team1"]) < 4:
                        team_data["team1"].append(user.id)
                    else:
                        await safe_send(ctx, f"❌ {user.mention} Team 1 is full!")
                        continue
            
            # Join Team 2
            elif str(reaction.emoji) == "2️⃣":
                if user.id not in team_data["team1"] and user.id not in team_data["team2"]:
                    if len(team_data["team2"]) < 4:
                        team_data["team2"].append(user.id)
                    else:
                        await safe_send(ctx, f"❌ {user.mention} Team 2 is full!")
                        continue
            
            # Update embed
            team1_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(team_data["team1"])])
            team2_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(team_data["team2"])]) if team_data["team2"] else "Empty"
            
            embed = discord.Embed(
                title="🔥 4v4 WAR GAMES - RECRUITING!",
                description=f"{ctx.author.mention} is starting a 4v4 match!",
                color=discord.Color.dark_red()
            )
            embed.add_field(
                name="How to Join",
                value="React with 1️⃣ to join Team 1\nReact with 2️⃣ to join Team 2",
                inline=False
            )
            embed.add_field(name=f"Team 1 ({len(team_data['team1'])}/4)", value=team1_list, inline=True)
            embed.add_field(name=f"Team 2 ({len(team_data['team2'])}/4)", value=team2_list, inline=True)
            embed.set_footer(text="Match starts when both teams are full!")
            
            await safe_edit(message, embed=embed)
            
            # Check if teams are full
            if len(team_data["team1"]) == 4 and len(team_data["team2"]) == 4:
                del pending_4v4_teams[team_id]
                await safe_send(ctx, "✅ Both teams are full! Starting match...")
                await start_4v4_match(ctx, team_data["team1"], team_data["team2"])
                break
        
        except asyncio.TimeoutError:
            if team_id in pending_4v4_teams:
                del pending_4v4_teams[team_id]
                await safe_send(ctx, "⏰ 4v4 match recruitment timed out!")
            break

async def start_4v4_match(ctx, team1, team2):
    """Start a 4v4 match"""
    match_id = generate_match_id()
    match = FourVsFourMatch(match_id, ctx.channel.id, team1, team2)
    match.status = "active"
    active_matches[match_id] = match
    
    team1_mentions = ", ".join([f"<@{p}>" for p in team1])
    team2_mentions = ", ".join([f"<@{p}>" for p in team2])
    
    embed = discord.Embed(
        title="🔥 4v4 WAR GAMES!",
        description="All-out war! May the best team win!",
        color=discord.Color.dark_red()
    )
    embed.add_field(name="Team 1", value=team1_mentions, inline=False)
    embed.add_field(name="Team 2", value=team2_mentions, inline=False)
    embed.add_field(
        name="Rules",
        value="• 4v4 warfare\n• Teams rotate members\n• 50 seconds per turn\n• Chaos reigns!",
        inline=False
    )
    embed.add_field(name="First Move", value=f"<@{team1[0]}> from Team 1, attack!", inline=False)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='gauntlet')
async def setup_gauntlet(ctx, mode: str = "quick"):
    """Setup a gauntlet match: +gauntlet quick OR +gauntlet @p1 @p2 @p3..."""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "gauntlet")
    if not can_use:
        await safe_send(ctx, f"⏰ Please wait **{int(remaining)}** seconds before starting another gauntlet!")
        return
    
    if mode.lower() == "quick":
        gauntlet_id = f"gauntlet_{ctx.channel.id}_{int(datetime.now().timestamp())}"
        
        pending_gauntlet[gauntlet_id] = {
            "creator": ctx.author.id,
            "channel_id": ctx.channel.id,
            "participants": [ctx.author.id],
            "message_id": None,
            "expires": datetime.now() + timedelta(minutes=5)
        }
        
        embed = discord.Embed(
            title="🔥 GAUNTLET MATCH - RECRUITING!",
            description=f"{ctx.author.mention} is starting a gauntlet!\nNeed 3-10 participants total.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="How to Join",
            value="React with ✅ to join the gauntlet!",
            inline=False
        )
        embed.add_field(name="Participants (1/10)", value=f"1. {ctx.author.mention}", inline=False)
        embed.set_footer(text="React ✅ to join • ❌ to cancel • Expires in 5 minutes")
        
        msg = await safe_send(ctx, embed=embed)
        await safe_add_reaction(msg, "✅")
        await safe_add_reaction(msg, "▶️")  # Start button
        await safe_add_reaction(msg, "❌")  # Cancel button
        
        pending_gauntlet[gauntlet_id]["message_id"] = msg.id
        
        # Set cooldown
        set_cooldown(ctx.author.id, "gauntlet")
        
        asyncio.create_task(monitor_gauntlet_reactions(ctx, gauntlet_id, msg))
    
    else:
        participants = ctx.message.mentions
        
        if len(participants) < 2:
            await safe_send(ctx, "❌ Gauntlet needs at least 3 participants total!")
            return
        
        if len(participants) > 9:
            await safe_send(ctx, "❌ Maximum 10 participants!")
            return
        
        all_participants = [ctx.author.id] + [m.id for m in participants]
        
        if len(set(all_participants)) != len(all_participants):
            await safe_send(ctx, "❌ All participants must be different!")
            return
        
        for player in participants:
            if player.bot:
                await safe_send(ctx, "❌ Bots cannot participate!")
                return
        
        # Set cooldown
        set_cooldown(ctx.author.id, "gauntlet")
        
        await start_gauntlet_match(ctx, all_participants)

async def monitor_gauntlet_reactions(ctx, gauntlet_id, message):
    """Monitor reactions for gauntlet formation"""
    
    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            not user.bot and
            str(reaction.emoji) in ["✅", "▶️", "❌"]
        )
    
    while gauntlet_id in pending_gauntlet:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
            
            gauntlet_data = pending_gauntlet.get(gauntlet_id)
            if not gauntlet_data:
                break
            
            # Cancel
            if str(reaction.emoji) == "❌" and user.id == gauntlet_data["creator"]:
                await safe_send(ctx, f"❌ Gauntlet cancelled by {user.mention}")
                del pending_gauntlet[gauntlet_id]
                break
            
            # Start match
            if str(reaction.emoji) == "▶️" and user.id == gauntlet_data["creator"]:
                if len(gauntlet_data["participants"]) >= 3:
                    del pending_gauntlet[gauntlet_id]
                    await safe_send(ctx, "✅ Starting gauntlet match!")
                    await start_gauntlet_match(ctx, gauntlet_data["participants"])
                    break
                else:
                    await safe_send(ctx, "❌ Need at least 3 participants!")
                    continue
            
            # Join
            if str(reaction.emoji) == "✅":
                if user.id not in gauntlet_data["participants"]:
                    if len(gauntlet_data["participants"]) < 10:
                        gauntlet_data["participants"].append(user.id)
                    else:
                        await safe_send(ctx, f"❌ {user.mention} Gauntlet is full!")
                        continue
                else:
                    continue
            
            # Update embed
            participants_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(gauntlet_data["participants"])])
            
            embed = discord.Embed(
                title="🔥 GAUNTLET MATCH - RECRUITING!",
                description=f"{ctx.author.mention} is starting a gauntlet!\nNeed 3-10 participants total.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="How to Join",
                value="React with ✅ to join!\nCreator: React ▶️ to start (min 3 players)",
                inline=False
            )
            embed.add_field(name=f"Participants ({len(gauntlet_data['participants'])}/10)", value=participants_list, inline=False)
            embed.set_footer(text="React ✅ to join • ▶️ to start • ❌ to cancel")
            
            await safe_edit(message, embed=embed)
        
        except asyncio.TimeoutError:
            if gauntlet_id in pending_gauntlet:
                del pending_gauntlet[gauntlet_id]
                await safe_send(ctx, "⏰ Gauntlet recruitment timed out!")
            break

async def start_gauntlet_match(ctx, participants):
    """Start a gauntlet match"""
    random.shuffle(participants)
    
    match_id = generate_match_id()
    match = GauntletMatch(match_id, ctx.channel.id, participants)
    match.status = "active"
    active_matches[match_id] = match
    
    participant_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(participants)])
    
    embed = discord.Embed(
        title="🔥 GAUNTLET MATCH!",
        description="One by one, they will fall!",
        color=discord.Color.orange()
    )
    embed.add_field(name="Entry Order", value=participant_list, inline=False)
    embed.add_field(
        name="Rules",
        value="• Fighter faces challengers one by one\n• Eliminate fighter to become new fighter\n• Last one standing wins\n• 50 seconds per turn",
        inline=False
    )
    embed.add_field(
        name="Starting",
        value=f"🥊 <@{participants[0]}> vs <@{participants[1]}>",
        inline=False
    )
    
    await safe_send(ctx, embed=embed)

@bot.command(name='royalrumble', aliases=['rumble', 'rr'])
async def setup_royal_rumble(ctx, mode: str = "quick"):
    """Setup a Royal Rumble: +royalrumble quick OR +royalrumble @p1 @p2..."""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "royalrumble")
    if not can_use:
        await safe_send(ctx, f"⏰ Please wait **{int(remaining)}** seconds before starting another Royal Rumble!")
        return
    
    if mode.lower() == "quick":
        rumble_id = f"rumble_{ctx.channel.id}_{int(datetime.now().timestamp())}"
        
        pending_rumble[rumble_id] = {
            "creator": ctx.author.id,
            "channel_id": ctx.channel.id,
            "participants": [ctx.author.id],
            "message_id": None,
            "expires": datetime.now() + timedelta(minutes=5)
        }
        
        embed = discord.Embed(
            title="👑 ROYAL RUMBLE - RECRUITING!",
            description=f"{ctx.author.mention} is starting a Royal Rumble!\nNeed 10-30 participants.",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="How to Join",
            value="React with ✅ to enter the Royal Rumble!",
            inline=False
        )
        embed.add_field(name="Participants (1/30)", value=f"1. {ctx.author.mention}", inline=False)
        embed.set_footer(text="React ✅ to join • ▶️ to start • ❌ to cancel • Expires in 5 minutes")
        
        msg = await safe_send(ctx, embed=embed)
        await safe_add_reaction(msg, "✅")
        await safe_add_reaction(msg, "▶️")
        await safe_add_reaction(msg, "❌")
        
        pending_rumble[rumble_id]["message_id"] = msg.id
        
        # Set cooldown
        set_cooldown(ctx.author.id, "royalrumble")
        
        asyncio.create_task(monitor_rumble_reactions(ctx, rumble_id, msg))
    
    else:
        participants = ctx.message.mentions
        
        if len(participants) < 9:
            await safe_send(ctx, "❌ Royal Rumble needs at least 10 participants!")
            return
        
        if len(participants) > 29:
            await safe_send(ctx, "❌ Maximum 30 participants!")
            return
        
        all_participants = [ctx.author.id] + [m.id for m in participants]
        
        if len(set(all_participants)) != len(all_participants):
            await safe_send(ctx, "❌ All participants must be different!")
            return
        
        for player in participants:
            if player.bot:
                await safe_send(ctx, "❌ Bots cannot participate!")
                return
        
        # Set cooldown
        set_cooldown(ctx.author.id, "royalrumble")
        
        await start_rumble_match(ctx, all_participants)

async def monitor_rumble_reactions(ctx, rumble_id, message):
    """Monitor reactions for Royal Rumble formation"""
    
    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            not user.bot and
            str(reaction.emoji) in ["✅", "▶️", "❌"]
        )
    
    while rumble_id in pending_rumble:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
            
            rumble_data = pending_rumble.get(rumble_id)
            if not rumble_data:
                break
            
            # Cancel
            if str(reaction.emoji) == "❌" and user.id == rumble_data["creator"]:
                await safe_send(ctx, f"❌ Royal Rumble cancelled by {user.mention}")
                del pending_rumble[rumble_id]
                break
            
            # Start match
            if str(reaction.emoji) == "▶️" and user.id == rumble_data["creator"]:
                if len(rumble_data["participants"]) >= 10:
                    del pending_rumble[rumble_id]
                    await safe_send(ctx, "✅ Starting Royal Rumble!")
                    await start_rumble_match(ctx, rumble_data["participants"])
                    break
                else:
                    await safe_send(ctx, "❌ Need at least 10 participants!")
                    continue
            
            # Join
            if str(reaction.emoji) == "✅":
                if user.id not in rumble_data["participants"]:
                    if len(rumble_data["participants"]) < 30:
                        rumble_data["participants"].append(user.id)
                    else:
                        await safe_send(ctx, f"❌ {user.mention} Royal Rumble is full!")
                        continue
                else:
                    continue
            
            # Update embed
            participants_list = "\n".join([f"{i+1}. <@{p}>" for i, p in enumerate(rumble_data["participants"][:10])])
            if len(rumble_data["participants"]) > 10:
                participants_list += f"\n... and {len(rumble_data['participants']) - 10} more"
            
            embed = discord.Embed(
                title="👑 ROYAL RUMBLE - RECRUITING!",
                description=f"{ctx.author.mention} is starting a Royal Rumble!\nNeed 10-30 participants.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="How to Join",
                value="React with ✅ to join!\nCreator: React ▶️ to start (min 10 players)",
                inline=False
            )
            embed.add_field(name=f"Participants ({len(rumble_data['participants'])}/30)", value=participants_list, inline=False)
            embed.set_footer(text="React ✅ to join • ▶️ to start • ❌ to cancel")
            
            await safe_edit(message, embed=embed)
        
        except asyncio.TimeoutError:
            if rumble_id in pending_rumble:
                del pending_rumble[rumble_id]
                await safe_send(ctx, "⏰ Royal Rumble recruitment timed out!")
            break

async def start_rumble_match(ctx, participants):
    """Start Royal Rumble"""
    match_id = generate_match_id()
    match = RoyalRumbleMatch(match_id, ctx.channel.id, participants)
    match.status = "active"
    active_matches[match_id] = match
    
    embed = discord.Embed(
        title="👑 ROYAL RUMBLE!",
        description=f"Every {match.entry_interval} seconds, a new superstar enters!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Total Participants", value=str(len(participants)), inline=True)
    embed.add_field(name="Prize", value=f"💰 {MATCH_REWARDS['royal_rumble']['winner']} coins", inline=True)
    embed.add_field(
        name="Rules",
        value="• Over-the-top-rope eliminations\n• Send GIFs attacking anyone in the ring\n• Mention your target\n• Last one standing wins!",
        inline=False
    )
    
    await safe_send(ctx, embed=embed)
    
    # Start the rumble
    await match.start_rumble(ctx.channel)

@bot.command(name='endmatch')
async def end_match(ctx):
    """End the current match in this channel (admin only)"""
    if not ctx.author.guild_permissions.administrator:
        await safe_send(ctx, "❌ Only administrators can end matches!")
        return
    
    # Find match in this channel
    match_to_end = None
    for match_id, match in active_matches.items():
        if match.channel_id == ctx.channel.id:
            match_to_end = match_id
            break
    
    if not match_to_end:
        await safe_send(ctx, "❌ No active match in this channel!")
        return
    
    del active_matches[match_to_end]
    await safe_send(ctx, "✅ Match ended by administrator!")

# ============================================================================
# PROFILE & ECONOMY COMMANDS
# ============================================================================

@bot.command(name='profile', aliases=['p', 'stats'])
async def profile(ctx, user: discord.Member = None):
    """View your profile or someone else's: +profile [@user]"""
    if user is None:
        user = ctx.author
    
    if user.bot:
        await safe_send(ctx, "❌ Bots don't have profiles!")
        return
    
    profile_data = get_user_profile(str(user.id))
    
    # Calculate win rate
    total = profile_data["total_matches"]
    wins = profile_data["wins"]
    win_rate = (wins / total * 100) if total > 0 else 0
    
    embed = discord.Embed(
        title=f"🏆 {user.display_name}'s Profile",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    
    embed.add_field(name="💰 Coins", value=f"{profile_data['coins']:,}", inline=True)
    embed.add_field(name="📊 Win Rate", value=f"{win_rate:.1f}%", inline=True)
    embed.add_field(name="🔥 Win Streak", value=str(profile_data['win_streak']), inline=True)
    
    embed.add_field(name="✅ Wins", value=str(wins), inline=True)
    embed.add_field(name="❌ Losses", value=str(profile_data['losses']), inline=True)
    embed.add_field(name="📈 Total Matches", value=str(total), inline=True)
    
# Match stats by mode
    modes_played = "\n".join([
        f"1v1: {profile_data['matches_played']['1v1']} ({profile_data['wins_by_mode']['1v1']}W)",
        f"2v2: {profile_data['matches_played']['2v2']} ({profile_data['wins_by_mode']['2v2']}W)",
        f"4v4: {profile_data['matches_played']['4v4']} ({profile_data['wins_by_mode']['4v4']}W)",
        f"Gauntlet: {profile_data['matches_played']['gauntlet']} ({profile_data['wins_by_mode']['gauntlet']}W)",
        f"Royal Rumble: {profile_data['matches_played']['royal_rumble']} ({profile_data['wins_by_mode']['royal_rumble']}W)"
    ])
    
    embed.add_field(name="🎮 Matches by Mode", value=modes_played, inline=False)
    embed.add_field(name="🏅 Best Streak", value=str(profile_data['best_streak']), inline=True)
    embed.add_field(name="🎖️ Achievements", value=str(len(profile_data['achievements'])), inline=True)
    
    embed.set_footer(text=f"Playing since {profile_data['created_at'][:10]}")
    
    await safe_send(ctx, embed=embed)

@bot.command(name='balance', aliases=['bal', 'coins'])
async def balance(ctx, user: discord.Member = None):
    """Check your coin balance: +balance [@user]"""
    if user is None:
        user = ctx.author
    
    if user.bot:
        await safe_send(ctx, "❌ Bots don't have coins!")
        return
    
    profile_data = get_user_profile(str(user.id))
    
    embed = discord.Embed(
        title=f"💰 {user.display_name}'s Balance",
        description=f"**{profile_data['coins']:,}** coins",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='daily')
async def daily_reward(ctx):
    """Claim your daily reward: +daily"""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "daily")
    if not can_use:
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await safe_send(ctx, f"⏰ Daily reward available in **{hours}h {minutes}m**!")
        return
    
    profile_data = get_user_profile(str(ctx.author.id))
    
    # Daily reward calculation
    base_reward = 100
    streak_bonus = profile_data['win_streak'] * 10
    total_reward = base_reward + streak_bonus
    
    profile_data['coins'] += total_reward
    set_cooldown(ctx.author.id, "daily")
    save_data()
    
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"You received **{total_reward}** coins!",
        color=discord.Color.green()
    )
    embed.add_field(name="Base Reward", value=f"{base_reward} coins", inline=True)
    embed.add_field(name="Streak Bonus", value=f"{streak_bonus} coins", inline=True)
    embed.add_field(name="New Balance", value=f"{profile_data['coins']:,} coins", inline=False)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='give', aliases=['transfer'])
async def give_coins(ctx, user: discord.Member = None, amount: int = None):
    """Give coins to another user: +give @user amount"""
    # Check cooldown
    can_use, remaining = check_cooldown(ctx.author.id, "give")
    if not can_use:
        await safe_send(ctx, f"⏰ Please wait **{int(remaining)}** seconds before giving coins again!")
        return
    
    if user is None or amount is None:
        await safe_send(ctx, "❌ Usage: `+give @user amount`")
        return
    
    if user.bot:
        await safe_send(ctx, "❌ You can't give coins to bots!")
        return
    
    if user.id == ctx.author.id:
        await safe_send(ctx, "❌ You can't give coins to yourself!")
        return
    
    if amount <= 0:
        await safe_send(ctx, "❌ Amount must be positive!")
        return
    
    sender_profile = get_user_profile(str(ctx.author.id))
    
    if sender_profile['coins'] < amount:
        await safe_send(ctx, f"❌ You don't have enough coins! You have {sender_profile['coins']:,}")
        return
    
    receiver_profile = get_user_profile(str(user.id))
    
    # Transfer coins
    sender_profile['coins'] -= amount
    receiver_profile['coins'] += amount
    set_cooldown(ctx.author.id, "give")
    save_data()
    
    embed = discord.Embed(
        title="💸 Coin Transfer",
        description=f"{ctx.author.mention} gave {user.mention} **{amount:,}** coins!",
        color=discord.Color.green()
    )
    embed.add_field(name="From", value=ctx.author.mention, inline=True)
    embed.add_field(name="To", value=user.mention, inline=True)
    embed.add_field(name="Amount", value=f"{amount:,} coins", inline=True)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='leaderboard', aliases=['lb', 'top'])
async def leaderboard(ctx, category: str = "coins"):
    """View leaderboards: +leaderboard [coins/wins/streak]"""
    if category.lower() not in ["coins", "wins", "streak", "matches"]:
        await safe_send(ctx, "❌ Categories: `coins`, `wins`, `streak`, `matches`")
        return
    
    # Sort users
    if category.lower() == "coins":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['coins'], reverse=True)[:10]
        title = "💰 Top 10 Richest Players"
        value_key = "coins"
        value_format = lambda x: f"{x:,} coins"
    elif category.lower() == "wins":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['wins'], reverse=True)[:10]
        title = "🏆 Top 10 Winners"
        value_key = "wins"
        value_format = lambda x: f"{x} wins"
    elif category.lower() == "streak":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['best_streak'], reverse=True)[:10]
        title = "🔥 Top 10 Win Streaks"
        value_key = "best_streak"
        value_format = lambda x: f"{x} streak"
    else:
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['total_matches'], reverse=True)[:10]
        title = "📊 Most Active Players"
        value_key = "total_matches"
        value_format = lambda x: f"{x} matches"
    
    embed = discord.Embed(
        title=title,
        color=discord.Color.gold()
    )
    
    leaderboard_text = ""
    for i, (user_id, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} {user.name} - {value_format(data[value_key])}\n"
        except:
            pass
    
    if leaderboard_text:
        embed.description = leaderboard_text
    else:
        embed.description = "No data yet!"
    
    await safe_send(ctx, embed=embed)

@bot.command(name='achievements', aliases=['ach'])
async def achievements(ctx, user: discord.Member = None):
    """View achievements: +achievements [@user]"""
    if user is None:
        user = ctx.author
    
    if user.bot:
        await safe_send(ctx, "❌ Bots don't have achievements!")
        return
    
    profile_data = get_user_profile(str(user.id))
    
    achievement_list = [
        {"id": "first_win", "name": "First Blood", "desc": "Win your first match", "emoji": "🩸"},
        {"id": "win_10", "name": "Rising Star", "desc": "Win 10 matches", "emoji": "⭐"},
        {"id": "win_50", "name": "Superstar", "desc": "Win 50 matches", "emoji": "🌟"},
        {"id": "win_100", "name": "WWE Champion", "desc": "Win 100 matches", "emoji": "🏆"},
        {"id": "streak_5", "name": "On Fire", "desc": "Win 5 in a row", "emoji": "🔥"},
        {"id": "streak_10", "name": "Unstoppable", "desc": "Win 10 in a row", "emoji": "💪"},
        {"id": "millionaire", "name": "Millionaire", "desc": "Earn 1M coins", "emoji": "💰"},
        {"id": "gauntlet_winner", "name": "Gauntlet Master", "desc": "Win a gauntlet", "emoji": "🥊"},
        {"id": "rumble_winner", "name": "Royal Rumble Champion", "desc": "Win a Royal Rumble", "emoji": "👑"},
        {"id": "veteran", "name": "Veteran", "desc": "Play 100 matches", "emoji": "🎖️"}
    ]
    
    embed = discord.Embed(
        title=f"🏅 {user.display_name}'s Achievements",
        description=f"**{len(profile_data['achievements'])}/{len(achievement_list)}** unlocked",
        color=discord.Color.purple()
    )
    
    unlocked = ""
    locked = ""
    
    for ach in achievement_list:
        if ach['id'] in profile_data['achievements']:
            unlocked += f"{ach['emoji']} **{ach['name']}** - {ach['desc']}\n"
        else:
            locked += f"🔒 {ach['name']} - {ach['desc']}\n"
    
    if unlocked:
        embed.add_field(name="Unlocked", value=unlocked, inline=False)
    if locked:
        embed.add_field(name="Locked", value=locked[:1024], inline=False)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='matches', aliases=['history'])
async def match_history_cmd(ctx, user: discord.Member = None):
    """View recent match history: +matches [@user]"""
    if user is None:
        user = ctx.author
    
    if user.bot:
        await safe_send(ctx, "❌ Bots don't have match history!")
        return
    
    embed = discord.Embed(
        title=f"📜 {user.display_name}'s Recent Matches",
        description="Last 10 matches",
        color=discord.Color.blue()
    )
    
    # This would show actual match history if we stored it
    # For now, show stats
    profile_data = get_user_profile(str(user.id))
    
    stats_text = f"**Total Matches:** {profile_data['total_matches']}\n"
    stats_text += f"**Win Rate:** {(profile_data['wins']/profile_data['total_matches']*100 if profile_data['total_matches'] > 0 else 0):.1f}%\n"
    stats_text += f"**Current Streak:** {profile_data['win_streak']}\n"
    
    embed.description = stats_text
    
    await safe_send(ctx, embed=embed)

# ============================================================================
# INFO COMMANDS
# ============================================================================

@bot.command(name='help', aliases=['h', 'commands'])
async def help_command(ctx, category: str = None):
    """Show help menu: +help [category]"""
    if category is None:
        embed = discord.Embed(
            title="🤖 WWE Sage Bot - Help Menu",
            description="The ultimate WWE GIF battle bot!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 Match Commands",
            value="`+chall @user` - Challenge to 1v1\n`+accept @user` - Accept challenge\n`+decline @user` - Decline challenge\n`+2v2 quick` - Start 2v2\n`+4v4 quick` - Start 4v4\n`+gauntlet quick` - Start gauntlet\n`+royalrumble quick` - Start Royal Rumble\n`+endmatch` - End match (admin)",
            inline=False
        )
        
        embed.add_field(
            name="💰 Economy Commands",
            value="`+profile [@user]` - View profile\n`+balance [@user]` - Check coins\n`+daily` - Daily reward\n`+give @user amount` - Give coins\n`+leaderboard [type]` - View rankings",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Stats Commands",
            value="`+achievements [@user]` - View achievements\n`+matches [@user]` - Match history\n`+info` - Bot information",
            inline=False
        )
        
        embed.add_field(
            name="🎮 How to Play",
            value="When a match starts, send WWE move GIFs to attack!\nCounter your opponent's moves with your own GIFs.\nYou have **50 seconds** per turn or you lose!\nFor detailed rules: `+help rules`",
            inline=False
        )
        
        embed.set_footer(text=f"Prefix: {PREFIX} | Use +help [category] for more info")
        
        await safe_send(ctx, embed=embed)
    
    elif category.lower() == "rules":
        embed = discord.Embed(
            title="📖 WWE Sage Bot - Game Rules",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🥊 1v1 Matches",
            value="• Player 1 sends first GIF attack\n• Player 2 counters with a GIF\n• Players alternate attacking\n• 50 seconds per turn\n• Match ends randomly after 5+ moves\n• Winner: 100 coins | Loser: 25 coins",
            inline=False
        )
        
        embed.add_field(
            name="👥 2v2 Matches",
            value="• Two teams of 2 players\n• Teams alternate turns\n• Team members rotate\n• 50 seconds per turn\n• Match ends randomly after 10+ moves\n• Winners: 150 coins each | Losers: 40 coins each",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ 4v4 Matches",
            value="• Two teams of 4 players\n• War Games style chaos\n• All team members rotate\n• 50 seconds per turn\n• Match ends randomly after 15+ moves\n• Winners: 200 coins each | Losers: 50 coins each",
            inline=False
        )
        
        embed.add_field(
            name="🔥 Gauntlet Match",
            value="• 3-10 participants\n• One fighter faces challengers\n• Defeat fighter to become new fighter\n• 50 seconds per turn\n• Last one standing wins\n• Winner: 500 coins | Participants: 100 coins",
            inline=False
        )
        
        embed.add_field(
            name="👑 Royal Rumble",
            value="• 10-30 participants\n• New entrant every 90 seconds\n• Attack anyone in the ring\n• Over-the-top eliminations\n• Last one standing wins\n• Winner: 1000 coins | Top 3: 500 coins | Others: 150 coins",
            inline=False
        )
        
        await safe_send(ctx, embed=embed)
    
    elif category.lower() == "economy":
        embed = discord.Embed(
            title="💰 WWE Sage Bot - Economy System",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Earning Coins",
            value="• Win 1v1: 100 coins\n• Win 2v2: 150 coins\n• Win 4v4: 200 coins\n• Win Gauntlet: 500 coins\n• Win Royal Rumble: 1000 coins\n• Daily Reward: 100+ coins\n• Achievements: 500 coins each",
            inline=False
        )
        
        embed.add_field(
            name="Starting Balance",
            value=f"{DEFAULT_STARTING_COINS:,} coins",
            inline=True
        )
        
        embed.add_field(
            name="Daily Reward",
            value="Base: 100 coins\n+10 per win streak",
            inline=True
        )
        
        await safe_send(ctx, embed=embed)

@bot.command(name='info', aliases=['about', 'botinfo'])
async def bot_info(ctx):
    """Bot information"""
    embed = discord.Embed(
        title="🤖 WWE Sage Bot",
        description="The ultimate WWE GIF battle Discord bot!",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="👥 Users", value=str(len(user_data)), inline=True)
    embed.add_field(name="🎮 Active Matches", value=str(len(active_matches)), inline=True)
    embed.add_field(name="📊 Servers", value=str(len(bot.guilds)), inline=True)
    
    embed.add_field(
        name="Features",
        value="• 1v1 GIF Battles\n• 2v2 Tag Teams\n• 4v4 War Games\n• 10-Man Gauntlets\n• 30-Man Royal Rumbles\n• Economy System\n• Achievements\n• Leaderboards",
        inline=False
    )
    
    embed.add_field(name="Prefix", value=f"`{PREFIX}`", inline=True)
    embed.add_field(name="Version", value="1.0.0", inline=True)
    
    embed.set_footer(text="Created for WWE GIF battle enthusiasts!")
    
    await safe_send(ctx, embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: **{latency}ms**",
        color=discord.Color.green()
    )
    
    await safe_send(ctx, embed=embed)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

@tasks.loop(minutes=5)
async def save_data_task():
    """Periodically save data"""
    save_data()

@tasks.loop(minutes=1)
async def cleanup_expired_challenges():
    """Clean up expired challenges and pending matches"""
    current_time = datetime.now()
    
    # Cleanup pending challenges
    expired_challenges = [
        cid for cid, challenge in pending_challenges.items()
        if current_time > challenge['expires']
    ]
    for cid in expired_challenges:
        del pending_challenges[cid]
    
    # Cleanup pending 2v2 teams
    expired_2v2 = [
        tid for tid, team in pending_2v2_teams.items()
        if current_time > team['expires']
    ]
    for tid in expired_2v2:
        del pending_2v2_teams[tid]
    
    # Cleanup pending 4v4 teams
    expired_4v4 = [
        tid for tid, team in pending_4v4_teams.items()
        if current_time > team['expires']
    ]
    for tid in expired_4v4:
        del pending_4v4_teams[tid]
    
    # Cleanup pending gauntlet
    expired_gauntlet = [
        gid for gid, gauntlet in pending_gauntlet.items()
        if current_time > gauntlet['expires']
    ]
    for gid in expired_gauntlet:
        del pending_gauntlet[gid]
    
    # Cleanup pending rumble
    expired_rumble = [
        rid for rid, rumble in pending_rumble.items()
        if current_time > rumble['expires']
    ]
    for rid in expired_rumble:
        del pending_rumble[rid]

# ============================================================================
# ERROR HANDLING
# ============================================================================

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await safe_send(ctx, f"❌ Missing argument: `{error.param.name}`")
    
    elif isinstance(error, commands.BadArgument):
        await safe_send(ctx, "❌ Invalid argument provided!")
    
    elif isinstance(error, commands.CommandOnCooldown):
        await safe_send(ctx, f"⏰ Command on cooldown! Try again in {error.retry_after:.1f}s")
    
    elif isinstance(error, commands.MissingPermissions):
        await safe_send(ctx, "❌ You don't have permission to use this command!")
    
    elif isinstance(error, commands.BotMissingPermissions):
        await safe_send(ctx, "❌ I don't have the required permissions!")
    
    else:
        print(f"Error in command {ctx.command}: {error}")
        await safe_send(ctx, "❌ An error occurred while processing the command!")

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

@bot.command(name='addcoins')
@commands.has_permissions(administrator=True)
async def add_coins(ctx, user: discord.Member, amount: int):
    """Add coins to a user (admin only): +addcoins @user amount"""
    if user.bot:
        await safe_send(ctx, "❌ Cannot add coins to bots!")
        return
    
    profile_data = get_user_profile(str(user.id))
    profile_data['coins'] += amount
    save_data()
    
    await safe_send(ctx, f"✅ Added **{amount:,}** coins to {user.mention}! New balance: **{profile_data['coins']:,}**")

@bot.command(name='removecoins')
@commands.has_permissions(administrator=True)
async def remove_coins(ctx, user: discord.Member, amount: int):
    """Remove coins from a user (admin only): +removecoins @user amount"""
    if user.bot:
        await safe_send(ctx, "❌ Cannot remove coins from bots!")
        return
    
    profile_data = get_user_profile(str(user.id))
    profile_data['coins'] = max(0, profile_data['coins'] - amount)
    save_data()
    
    await safe_send(ctx, f"✅ Removed **{amount:,}** coins from {user.mention}! New balance: **{profile_data['coins']:,}**")

@bot.command(name='resetuser')
@commands.has_permissions(administrator=True)
async def reset_user(ctx, user: discord.Member):
    """Reset a user's profile (admin only): +resetuser @user"""
    if user.bot:
        await safe_send(ctx, "❌ Cannot reset bot profiles!")
        return
    
    if str(user.id) in user_data:
        del user_data[str(user.id)]
        save_data()
        await safe_send(ctx, f"✅ Reset {user.mention}'s profile!")
    else:
        await safe_send(ctx, f"❌ {user.mention} has no profile!")

@bot.command(name='serverstats')
@commands.has_permissions(administrator=True)
async def server_stats(ctx):
    """View server statistics (admin only)"""
    # Count users from this server
    server_users = [uid for uid in user_data.keys() if ctx.guild.get_member(int(uid))]
    
    embed = discord.Embed(
        title=f"📊 {ctx.guild.name} Statistics",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Registered Users", value=str(len(server_users)), inline=True)
    embed.add_field(name="Active Matches", value=str(len([m for m in active_matches.values() if m.channel_id in [c.id for c in ctx.guild.channels]])), inline=True)
    embed.add_field(name="Bot Members", value=str(len([m for m in ctx.guild.members if m.bot])), inline=True)
    
    await safe_send(ctx, embed=embed)

# ============================================================================
# FUN COMMANDS
# ============================================================================

@bot.command(name='random', aliases=['randomwrestler'])
async def random_wrestler(ctx):
    """Get a random WWE wrestler"""
    wrestler = random.choice(WWE_WRESTLERS)
    
    embed = discord.Embed(
        title="🎲 Random Wrestler",
        description=f"**{wrestler}**",
        color=discord.Color.random()
    )
    
    await safe_send(ctx, embed=embed)

@bot.command(name='compare')
async def compare_users(ctx, user1: discord.Member = None, user2: discord.Member = None):
    """Compare two users' stats: +compare @user1 @user2"""
    if user1 is None:
        user1 = ctx.author
    
    if user2 is None:
        await safe_send(ctx, "❌ Please mention a second user to compare!")
        return
    
    if user1.bot or user2.bot:
        await safe_send(ctx, "❌ Cannot compare bots!")
        return
    
    profile1 = get_user_profile(str(user1.id))
    profile2 = get_user_profile(str(user2.id))
    
    embed = discord.Embed(
        title="⚔️ User Comparison",
        color=discord.Color.blue()
    )
    
    # Coins
    embed.add_field(
        name="💰 Coins",
        value=f"{user1.name}: {profile1['coins']:,}\n{user2.name}: {profile2['coins']:,}",
        inline=False
    )
    
    # Wins
    embed.add_field(
        name="🏆 Wins",
        value=f"{user1.name}: {profile1['wins']}\n{user2.name}: {profile2['wins']}",
        inline=True
    )
    
    # Win Rate
    wr1 = (profile1['wins'] / profile1['total_matches'] * 100) if profile1['total_matches'] > 0 else 0
    wr2 = (profile2['wins'] / profile2['total_matches'] * 100) if profile2['total_matches'] > 0 else 0
    
    embed.add_field(
        name="📊 Win Rate",
        value=f"{user1.name}: {wr1:.1f}%\n{user2.name}: {wr2:.1f}%",
        inline=True
    )
    
    # Best Streak
    embed.add_field(
        name="🔥 Best Streak",
        value=f"{user1.name}: {profile1['best_streak']}\n{user2.name}: {profile2['best_streak']}",
        inline=True
    )
    
    await safe_send(ctx, embed=embed)

@bot.command(name='flip', aliases=['coinflip'])
async def coin_flip(ctx):
    """Flip a coin"""
    result = random.choice(["Heads", "Tails"])
    
    embed = discord.Embed(
        title="🪙 Coin Flip",
        description=f"**{result}!**",
        color=discord.Color.gold()
    )
    
    await safe_send(ctx, embed=embed)

@bot.command(name='roll')
async def roll_dice(ctx, sides: int = 6):
    """Roll a dice: +roll [sides]"""
    if sides < 2 or sides > 100:
        await safe_send(ctx, "❌ Sides must be between 2 and 100!")
        return
    
    result = random.randint(1, sides)
    
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"You rolled a **{result}** (d{sides})",
        color=discord.Color.blue()
    )
    
    await safe_send(ctx, embed=embed)

# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@bot.command(name='serverinfo')
async def server_info(ctx):
    """Display server information"""
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f"📋 {guild.name}",
        color=discord.Color.blue()
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="📅 Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    
    embed.add_field(name="💬 Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)
    embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
    
    await safe_send(ctx, embed=embed)

@bot.command(name='userinfo')
async def user_info(ctx, user: discord.Member = None):
    """Display user information: +userinfo [@user]"""
    if user is None:
        user = ctx.author
    
    embed = discord.Embed(
        title=f"👤 {user.name}",
        color=user.color
    )
    
    embed.set_thumbnail(url=user.display_avatar.url)
    
    embed.add_field(name="ID", value=str(user.id), inline=True)
    embed.add_field(name="Nickname", value=user.nick or "None", inline=True)
    embed.add_field(name="Bot", value="Yes" if user.bot else "No", inline=True)
    
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d") if user.joined_at else "Unknown", inline=True)
    embed.add_field(name="Roles", value=str(len(user.roles) - 1), inline=True)
    
    await safe_send(ctx, embed=embed)

# # ============================================================================
# RUN BOT
# # ============================================================================

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')  # or 'BOT_TOKEN' — be consistent!
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable not set!")
    bot.run(token)
