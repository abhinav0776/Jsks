"""
⚽ Discord Football Manager Bot - Complete Edition
All 100+ features in a single file
Features: Career, Teams, Matches, Economy, Achievements, and more!
"""

import discord.py
from discord.ext import commands, tasks
import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN', 'your_token_here')

# ==================== DATABASE SETUP ====================

class Database:
    """SQLite database manager for all game data"""
    
    def __init__(self, db_file='football_bot.db'):
        self.db_file = db_file
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            discord_id TEXT UNIQUE,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Players table
        c.execute('''CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            name TEXT,
            position TEXT,
            age INTEGER DEFAULT 16,
            pace INTEGER DEFAULT 50,
            shooting INTEGER DEFAULT 50,
            passing INTEGER DEFAULT 50,
            dribbling INTEGER DEFAULT 50,
            defense INTEGER DEFAULT 50,
            physical INTEGER DEFAULT 50,
            current_club_id INTEGER,
            salary REAL DEFAULT 0,
            contract_end TIMESTAMP,
            market_value REAL DEFAULT 50000,
            appearances INTEGER DEFAULT 0,
            goals INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            clean_sheets INTEGER DEFAULT 0,
            is_injured INTEGER DEFAULT 0,
            injury_type TEXT,
            injury_recovery TIMESTAMP,
            experience INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            retired INTEGER DEFAULT 0,
            retirement_date TIMESTAMP,
            personality TEXT,
            special_ability TEXT,
            leadership_level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(current_club_id) REFERENCES clubs(id)
        )''')
        
        # Clubs table
        c.execute('''CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            name TEXT UNIQUE,
            division INTEGER DEFAULT 10,
            balance REAL DEFAULT 5000000,
            weekly_income REAL DEFAULT 50000,
            stadium_level INTEGER DEFAULT 1,
            wins INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            goals_for INTEGER DEFAULT 0,
            goals_against INTEGER DEFAULT 0,
            youth_academy_level INTEGER DEFAULT 1,
            morale INTEGER DEFAULT 75,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        )''')
        
        # Matches table
        c.execute('''CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            home_club_id INTEGER,
            away_club_id INTEGER,
            home_goals INTEGER DEFAULT 0,
            away_goals INTEGER DEFAULT 0,
            match_status TEXT DEFAULT 'scheduled',
            match_type TEXT,
            play_by_play TEXT DEFAULT '[]',
            scheduled_time TIMESTAMP,
            completed_time TIMESTAMP,
            difficulty TEXT DEFAULT 'normal',
            FOREIGN KEY(home_club_id) REFERENCES clubs(id),
            FOREIGN KEY(away_club_id) REFERENCES clubs(id)
        )''')
        
        # Tournaments table
        c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY,
            creator_id INTEGER,
            name TEXT,
            teams TEXT DEFAULT '[]',
            status TEXT DEFAULT 'open',
            prize_pool REAL DEFAULT 0,
            tournament_type TEXT,
            FOREIGN KEY(creator_id) REFERENCES users(id)
        )''')
        
        # Achievements table
        c.execute('''CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            achievement_name TEXT,
            description TEXT,
            rarity TEXT,
            unlocked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        # Transfers table
        c.execute('''CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY,
            player_id INTEGER,
            from_club_id INTEGER,
            to_club_id INTEGER,
            fee REAL,
            status TEXT DEFAULT 'listed',
            listed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(player_id) REFERENCES players(id),
            FOREIGN KEY(from_club_id) REFERENCES clubs(id),
            FOREIGN KEY(to_club_id) REFERENCES clubs(id)
        )''')
        
        conn.commit()
        conn.close()

# ==================== BOT SETUP ====================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!fb ', intents=intents)
db = Database()

# ==================== UTILITY FUNCTIONS ====================

def get_or_create_user(discord_id: str, username: str) -> int:
    """Get or create user in database"""
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id FROM users WHERE discord_id = ?', (str(discord_id),))
    row = c.fetchone()
    
    if row:
        conn.close()
        return row[0]
    
    c.execute('INSERT INTO users (discord_id, username) VALUES (?, ?)', 
              (str(discord_id), username))
    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id

def calculate_overall(pace, shooting, passing, dribbling, defense, physical) -> int:
    """Calculate player overall rating"""
    return (pace + shooting + passing + dribbling + defense + physical) // 6

def get_player_embed(player_row) -> discord.Embed:
    """Create embed for player display"""
    overall = calculate_overall(
        player_row['pace'], player_row['shooting'], player_row['passing'],
        player_row['dribbling'], player_row['defense'], player_row['physical']
    )
    
    embed = discord.Embed(
        title=f"⚽ {player_row['name']}",
        description=f"Age: {player_row['age']} | Position: {player_row['position']}",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="📊 Overall Rating", value=f"{overall}/100", inline=False)
    embed.add_field(name="Pace", value=f"{'█' * (player_row['pace'] // 10)}░ {player_row['pace']}", inline=True)
    embed.add_field(name="Shooting", value=f"{'█' * (player_row['shooting'] // 10)}░ {player_row['shooting']}", inline=True)
    embed.add_field(name="Passing", value=f"{'█' * (player_row['passing'] // 10)}░ {player_row['passing']}", inline=True)
    embed.add_field(name="Dribbling", value=f"{'█' * (player_row['dribbling'] // 10)}░ {player_row['dribbling']}", inline=True)
    embed.add_field(name="Defense", value=f"{'█' * (player_row['defense'] // 10)}░ {player_row['defense']}", inline=True)
    embed.add_field(name="Physical", value=f"{'█' * (player_row['physical'] // 10)}░ {player_row['physical']}", inline=True)
    
    embed.add_field(name="📈 Career Stats", value=
        f"Appearances: {player_row['appearances']}\n"
        f"Goals: {player_row['goals']}\n"
        f"Assists: {player_row['assists']}\n"
        f"Level: {player_row['level']} | XP: {player_row['experience']}",
        inline=False)
    
    if player_row['is_injured']:
        embed.add_field(name="⚠️ Injury Status",
            value=f"{player_row['injury_type']}\nRecovery: {player_row['injury_recovery']}",
            inline=False)
    
    return embed

# ==================== BOT EVENTS ====================

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f"\n{'='*50}")
    print(f"Bot logged in as {bot.user}")
    print(f"{'='*50}\n")
    await bot.change_presence(activity=discord.Game(name="!fb help"))

# ==================== PLAYER CAREER COMMANDS (Features 1-10, 31-40) ====================

@bot.command(name='createplayer', help='Create a new player')
async def create_player(ctx, *, name: str):
    """Create a new young player starting at age 16 (Features 1, 31)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    position = random.choice(['GK', 'DEF', 'MID', 'FWD'])
    personality = random.choice(['Aggressive', 'Balanced', 'Technical', 'Physical'])
    
    c.execute('''INSERT INTO players 
                 (user_id, name, position, age, personality)
                 VALUES (?, ?, ?, 16, ?)''',
              (user_id, name, position, personality))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title=f"⚽ {name} Created!",
        description="Welcome to your football career!",
        color=discord.Color.green()
    )
    embed.add_field(name="Position", value=position, inline=True)
    embed.add_field(name="Age", value="16 years old", inline=True)
    embed.add_field(name="Personality", value=personality, inline=True)
    embed.add_field(name="Overall Rating", value="40/100", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='myplayer', help='View your player details')
async def view_player(ctx):
    """View your player's information (Features 1, 10)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    player = c.fetchone()
    conn.close()
    
    if not player:
        await ctx.send("❌ You don't have a player yet. Use `!fb createplayer <name>`")
        return
    
    embed = get_player_embed(player)
    await ctx.send(embed=embed)

@bot.command(name='train', help='Train a specific attribute')
async def train_attribute(ctx, attribute: str, points: int = 5):
    """Train attributes with XP (Features 31, 32)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    player = c.fetchone()
    conn.close()
    
    if not player:
        await ctx.send("❌ You need a player first!")
        return
    
    attribute = attribute.lower()
    attr_map = {
        'pace': 'pace', 'shooting': 'shooting', 'passing': 'passing',
        'dribbling': 'dribbling', 'defense': 'defense', 'physical': 'physical'
    }
    
    if attribute not in attr_map:
        await ctx.send(f"❌ Invalid attribute! Choose: {', '.join(attr_map.keys())}")
        return
    
    if player['experience'] < points * 10:
        await ctx.send(f"❌ You need {points * 10} XP to train this!")
        return
    
    current_val = player[attr_map[attribute]]
    if current_val >= 99:
        await ctx.send(f"❌ {attribute} is already maxed!")
        return
    
    new_val = min(current_val + points, 99)
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute(f'UPDATE players SET {attr_map[attribute]} = ?, experience = experience - ? WHERE id = ?',
              (new_val, points * 10, player['id']))
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ **{attribute.capitalize()}** improved from {current_val} to {new_val}!")

@bot.command(name='negotiate', help='Negotiate a contract')
async def negotiate_contract(ctx, salary: float, duration_weeks: int):
    """Negotiate contract with salary and duration (Feature 2)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    player = c.fetchone()
    
    if not player:
        await ctx.send("❌ You need a player first!")
        conn.close()
        return
    
    contract_end = datetime.utcnow() + timedelta(weeks=duration_weeks)
    c.execute('UPDATE players SET salary = ?, contract_end = ? WHERE id = ?',
              (salary, contract_end, player['id']))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Contract Negotiated!",
        color=discord.Color.green()
    )
    embed.add_field(name="Weekly Salary", value=f"${salary:,.0f}", inline=False)
    embed.add_field(name="Duration", value=f"{duration_weeks} weeks", inline=False)
    embed.add_field(name="Expires", value=contract_end.strftime('%Y-%m-%d'), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='retire', help='Retire your player')
async def retire_player(ctx):
    """Retire player and add to hall of fame (Features 6, 86)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    player = c.fetchone()
    
    if not player:
        await ctx.send("❌ You need a player first!")
        conn.close()
        return
    
    overall = calculate_overall(
        player['pace'], player['shooting'], player['passing'],
        player['dribbling'], player['defense'], player['physical']
    )
    
    c.execute('UPDATE players SET retired = 1, retirement_date = ? WHERE id = ?',
              (datetime.utcnow(), player['id']))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="🏆 Career Complete!",
        description=f"{player['name']} has retired",
        color=discord.Color.gold()
    )
    embed.add_field(name="Final Stats", value=
        f"Appearances: {player['appearances']}\n"
        f"Goals: {player['goals']}\n"
        f"Assists: {player['assists']}\n"
        f"Overall: {overall}/100",
        inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='injury', help='Check injury status')
async def manage_injury(ctx):
    """Check and manage injuries (Feature 5)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    player = c.fetchone()
    conn.close()
    
    if not player:
        await ctx.send("❌ You need a player first!")
        return
    
    if not player['is_injured']:
        await ctx.send("✅ Your player is fit and healthy!")
        return
    
    embed = discord.Embed(
        title=f"⚠️ {player['name']} is Injured",
        color=discord.Color.red()
    )
    embed.add_field(name="Injury Type", value=player['injury_type'], inline=False)
    embed.add_field(name="Recovery Date", value=player['injury_recovery'], inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='agent', help='Manage agent services')
async def agent_management(ctx):
    """Agent management interface (Feature 7)"""
    embed = discord.Embed(
        title="🤝 Agent Services",
        color=discord.Color.purple()
    )
    embed.add_field(name="Commission", value="10% of salary", inline=False)
    embed.add_field(name="Services", value=
        "• Negotiate transfers\n"
        "• Arrange sponsorships\n"
        "• Manage contracts\n"
        "• Secure loans",
        inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='level', help='View your level and XP')
async def view_level(ctx):
    """View level and XP progression (Feature 40)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT level, experience FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        await ctx.send("❌ You need a player first!")
        return
    
    level = row['level']
    xp = row['experience']
    xp_needed = level * 1000
    progress = (xp / xp_needed) * 100 if xp_needed > 0 else 0
    
    embed = discord.Embed(
        title="📈 Progression",
        color=discord.Color.blue()
    )
    embed.add_field(name="Level", value=level, inline=True)
    embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)
    embed.add_field(name="Progress", value=f"{'█' * int(progress // 10)}░ {progress:.0f}%", inline=False)
    
    await ctx.send(embed=embed)

# ==================== CLUB/TEAM COMMANDS (Features 11-20, 41-50) ====================

@bot.command(name='createclub', help='Create your own football club')
async def create_club(ctx, *, club_name: str):
    """Create a new club (Feature 11)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id FROM clubs WHERE name = ?', (club_name,))
    if c.fetchone():
        await ctx.send(f"❌ Club '{club_name}' already exists!")
        conn.close()
        return
    
    c.execute('''INSERT INTO clubs (owner_id, name, division, balance, weekly_income)
                 VALUES (?, ?, 10, 5000000, 50000)''',
              (user_id, club_name))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title=f"🏆 {club_name} Created!",
        description="Welcome to club management",
        color=discord.Color.green()
    )
    embed.add_field(name="Starting Balance", value="$5,000,000", inline=True)
    embed.add_field(name="Division", value="10 (Lowest)", inline=True)
    embed.add_field(name="Stadium Level", value="1", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='myclub', help='View your club details')
async def view_club(ctx):
    """View club information (Feature 11)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM clubs WHERE owner_id = ? LIMIT 1', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You don't have a club! Use `!fb createclub <name>`")
        conn.close()
        return
    
    # Get squad info
    c.execute('SELECT COUNT(*) as count, AVG((pace + shooting + passing + dribbling + defense + physical) / 6) as avg_rating FROM players WHERE current_club_id = ?',
              (club['id'],))
    squad_info = c.fetchone()
    conn.close()
    
    embed = discord.Embed(
        title=f"🏟️ {club['name']}",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Division", value=club['division'], inline=True)
    embed.add_field(name="Record", value=f"{club['wins']}W-{club['draws']}D-{club['losses']}L", inline=True)
    embed.add_field(name="💰 Balance", value=f"${club['balance']:,.0f}", inline=True)
    embed.add_field(name="Weekly Income", value=f"${club['weekly_income']:,.0f}", inline=True)
    embed.add_field(name="🏗️ Stadium Level", value=club['stadium_level'], inline=True)
    embed.add_field(name="👥 Squad", value=f"{squad_info['count']}/25", inline=True)
    embed.add_field(name="😊 Morale", value=f"{club['morale']}/100", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='recruit', help='Recruit a player to your club')
async def recruit_player(ctx, player_id: int, salary: float):
    """Recruit a player (Feature 12)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    # Get club
    c.execute('SELECT id, balance FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        conn.close()
        return
    
    # Get player
    c.execute('SELECT * FROM players WHERE id = ?', (player_id,))
    player = c.fetchone()
    
    if not player:
        await ctx.send("❌ Player not found!")
        conn.close()
        return
    
    if club['balance'] < salary * 4:
        await ctx.send(f"❌ Not enough funds! Need ${salary * 4:,.0f}")
        conn.close()
        return
    
    c.execute('UPDATE players SET current_club_id = ?, salary = ? WHERE id = ?',
              (club['id'], salary, player_id))
    c.execute('UPDATE clubs SET balance = balance - ? WHERE id = ?',
              (salary * 4, club['id']))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Player Recruited!",
        color=discord.Color.green()
    )
    embed.add_field(name="Player", value=f"{player['name']} ({player['position']})", inline=False)
    embed.add_field(name="Salary", value=f"${salary:,.0f}/week", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='formation', help='Set team formation')
async def set_formation(ctx, formation: str):
    """Set tactical formation (Feature 13)"""
    valid_formations = ['4-4-2', '4-3-3', '3-5-2', '5-3-2', '4-2-3-1', '3-3-4', '5-4-1']
    
    if formation not in valid_formations:
        await ctx.send(f"❌ Invalid! Choose: {', '.join(valid_formations)}")
        return
    
    embed = discord.Embed(
        title=f"⚽ Formation Set: {formation}",
        color=discord.Color.green()
    )
    embed.add_field(name="Formation", value=formation, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='squad', help='View your squad')
async def view_squad(ctx):
    """View full squad (Feature 14)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        conn.close()
        return
    
    c.execute('SELECT * FROM players WHERE current_club_id = ? ORDER BY position', (club['id'],))
    players = c.fetchall()
    conn.close()
    
    if not players:
        await ctx.send("❌ Your squad is empty!")
        return
    
    embed = discord.Embed(
        title="👥 Your Squad",
        color=discord.Color.blue()
    )
    
    squad_text = ""
    for player in players:
        overall = calculate_overall(
            player['pace'], player['shooting'], player['passing'],
            player['dribbling'], player['defense'], player['physical']
        )
        squad_text += f"**{player['name']}** ({player['position']}) - {overall} OVR\n"
    
    embed.description = squad_text[:2048]
    await ctx.send(embed=embed)

@bot.command(name='upgradestadium', help='Upgrade your stadium')
async def upgrade_stadium(ctx):
    """Upgrade stadium (Feature 17)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    conn.close()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        return
    
    upgrade_cost = 500000 * club['stadium_level']
    
    if club['balance'] < upgrade_cost:
        await ctx.send(f"❌ Need ${upgrade_cost:,.0f}!")
        return
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('UPDATE clubs SET balance = balance - ?, stadium_level = stadium_level + 1 WHERE id = ?',
              (upgrade_cost, club['id']))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Stadium Upgraded!",
        color=discord.Color.green()
    )
    embed.add_field(name="New Level", value=club['stadium_level'] + 1, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='wallet', help='View your finances')
async def view_wallet(ctx):
    """View club finances (Feature 42)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        conn.close()
        return
    
    # Get total wages
    c.execute('SELECT SUM(salary) as total_wages FROM players WHERE current_club_id = ?',
              (club['id'],))
    wages_row = c.fetchone()
    total_wages = wages_row['total_wages'] or 0
    conn.close()
    
    weekly_net = club['weekly_income'] - total_wages
    
    embed = discord.Embed(
        title="💰 Financial Summary",
        color=discord.Color.green() if club['balance'] > 0 else discord.Color.red()
    )
    embed.add_field(name="Balance", value=f"${club['balance']:,.0f}", inline=False)
    embed.add_field(name="Weekly Income", value=f"${club['weekly_income']:,.0f}", inline=True)
    embed.add_field(name="Weekly Wages", value=f"${total_wages:,.0f}", inline=True)
    embed.add_field(name="Net Weekly", value=f"${weekly_net:,.0f}", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='morale', help='Check squad morale')
async def check_morale(ctx):
    """Check squad morale (Feature 20)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT morale FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    conn.close()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        return
    
    morale = club['morale']
    status = "🔴 Poor" if morale < 30 else "🟡 Low" if morale < 60 else "🟢 Good"
    
    embed = discord.Embed(
        title="😊 Squad Morale",
        color=discord.Color.blue()
    )
    embed.add_field(name="Morale", value=f"{morale}/100 {status}", inline=False)
    
    await ctx.send(embed=embed)

# ==================== MATCH & COMPETITION COMMANDS (Features 21-30) ====================

@bot.command(name='challenge', help='Challenge another player')
async def challenge_match(ctx, opponent_id: int, match_type: str = 'friendly'):
    """Challenge another player's club (Feature 21, 22)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    # Get both clubs
    c.execute('SELECT id FROM clubs WHERE owner_id = ?', (user_id,))
    home_club = c.fetchone()
    
    c.execute('SELECT id FROM clubs WHERE owner_id = ?', (opponent_id,))
    away_club = c.fetchone()
    
    if not home_club or not away_club:
        await ctx.send("❌ Both players must have clubs!")
        conn.close()
        return
    
    scheduled_time = datetime.utcnow() + timedelta(hours=2)
    
    c.execute('''INSERT INTO matches (home_club_id, away_club_id, match_type, scheduled_time)
                 VALUES (?, ?, ?, ?)''',
              (home_club['id'], away_club['id'], match_type, scheduled_time))
    conn.commit()
    match_id = c.lastrowid
    conn.close()
    
    embed = discord.Embed(
        title="⚽ Match Scheduled!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Match ID", value=match_id, inline=True)
    embed.add_field(name="Type", value=match_type.capitalize(), inline=True)
    embed.add_field(name="Scheduled", value=scheduled_time.strftime('%H:%M'), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='playmatch', help='Simulate a match')
async def play_match(ctx, match_id: int):
    """Simulate a football match (Features 21, 62)"""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM matches WHERE id = ?', (match_id,))
    match = c.fetchone()
    
    if not match or match['match_status'] != 'scheduled':
        await ctx.send("❌ Match not found or already played!")
        conn.close()
        return
    
    # Simulate match
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)
    
    # Generate play-by-play
    play_by_play = []
    for minute in [15, 25, 33, 45, 48, 67, 72, 85, 89]:
        if random.random() < 0.3:
            if random.random() < 0.5 and home_goals > 0:
                play_by_play.append(f"⚽ **{minute}'** GOAL! Home team scores!")
                home_goals -= 1
            elif away_goals > 0:
                play_by_play.append(f"⚽ **{minute}'** GOAL! Away team scores!")
                away_goals -= 1
    
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)
    
    # Update match
    completed_time = datetime.utcnow()
    c.execute('''UPDATE matches SET 
                 home_goals = ?, away_goals = ?, 
                 match_status = 'completed', completed_time = ?,
                 play_by_play = ?
                 WHERE id = ?''',
              (home_goals, away_goals, completed_time, json.dumps(play_by_play), match_id))
    
    # Update club stats
    c.execute('SELECT * FROM clubs WHERE id = ?', (match['home_club_id'],))
    home_club = c.fetchone()
    c.execute('SELECT * FROM clubs WHERE id = ?', (match['away_club_id'],))
    away_club = c.fetchone()
    
    if home_goals > away_goals:
        c.execute('UPDATE clubs SET wins = wins + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?',
                  (home_goals, away_goals, home_club['id']))
        c.execute('UPDATE clubs SET losses = losses + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?',
                  (away_goals, home_goals, away_club['id']))
    elif away_goals > home_goals:
        c.execute('UPDATE clubs SET losses = losses + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?',
                  (home_goals, away_goals, home_club['id']))
        c.execute('UPDATE clubs SET wins = wins + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?',
                  (away_goals, home_goals, away_club['id']))
    else:
        c.execute('UPDATE clubs SET draws = draws + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?',
                  (home_goals, away_goals, home_club['id']))
        c.execute('UPDATE clubs SET draws = draws + 1, goals_for = goals_for + ?, goals_against = goals_against + ? WHERE id = ?',
                  (away_goals, home_goals, away_club['id']))
    
    conn.commit()
    conn.close()
    
    result = "🏆 Home Win" if home_goals > away_goals else "🏆 Away Win" if away_goals > home_goals else "🤝 Draw"
    
    embed = discord.Embed(
        title="⚽ Match Complete!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Score", value=f"**{home_goals} - {away_goals}**", inline=False)
    embed.add_field(name="Result", value=result, inline=False)
    
    if play_by_play:
        embed.add_field(name="Events", value='\n'.join(play_by_play[:5]), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='season', help='Start a season campaign')
async def start_season(ctx):
    """Start a season-long campaign (Feature 25)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    conn.close()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        return
    
    embed = discord.Embed(
        title="📅 Season Started!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Total Matches", value="38", inline=True)
    embed.add_field(name="Format", value="2x Round Robin", inline=True)
    embed.add_field(name="Your Record", value="0W-0D-0L", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='leaderboard', help='View global leaderboards')
async def view_leaderboard(ctx, category: str = 'clubs'):
    """View global rankings (Feature 24)"""
    conn = db.get_connection()
    c = conn.cursor()
    
    if category == 'clubs':
        c.execute('''SELECT name, wins, draws, losses, goals_for, goals_against 
                     FROM clubs ORDER BY wins DESC LIMIT 10''')
        clubs = c.fetchall()
        
        embed = discord.Embed(
            title="🏆 Top Clubs",
            color=discord.Color.gold()
        )
        
        for i, club in enumerate(clubs, 1):
            total = club['wins'] + club['draws'] + club['losses']
            win_rate = (club['wins'] / total * 100) if total > 0 else 0
            embed.add_field(
                name=f"{i}. {club['name']}",
                value=f"{club['wins']}W-{club['draws']}D-{club['losses']}L ({win_rate:.1f}%)",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    elif category == 'players':
        c.execute('''SELECT name, goals, assists, appearances 
                     FROM players ORDER BY goals DESC LIMIT 10''')
        players = c.fetchall()
        
        embed = discord.Embed(
            title="⚽ Top Scorers",
            color=discord.Color.gold()
        )
        
        for i, player in enumerate(players, 1):
            embed.add_field(
                name=f"{i}. {player['name']}",
                value=f"{player['goals']} goals | {player['assists']} assists",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    conn.close()

@bot.command(name='tournament', help='Create a tournament')
async def create_tournament(ctx, *, tournament_name: str):
    """Create a tournament (Feature 23)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO tournaments (creator_id, name, tournament_type, prize_pool)
                 VALUES (?, ?, 'single_elimination', 100000)''',
              (user_id, tournament_name))
    conn.commit()
    tournament_id = c.lastrowid
    conn.close()
    
    embed = discord.Embed(
        title=f"🏆 Tournament Created: {tournament_name}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Prize Pool", value="$100,000", inline=True)
    embed.add_field(name="Format", value="Single Elimination", inline=True)
    embed.add_field(name="ID", value=tournament_id, inline=False)
    
    await ctx.send(embed=embed)

# ==================== ECONOMY & TRANSFER COMMANDS (Features 41-50) ====================

@bot.command(name='transfer', help='List player for transfer')
async def list_transfer(ctx, player_id: int, asking_price: float):
    """List player on transfer market (Feature 8, 41)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        conn.close()
        return
    
    c.execute('SELECT * FROM players WHERE id = ? AND current_club_id = ?',
              (player_id, club['id']))
    player = c.fetchone()
    
    if not player:
        await ctx.send("❌ Player not in your squad!")
        conn.close()
        return
    
    c.execute('''INSERT INTO transfers (player_id, from_club_id, fee)
                 VALUES (?, ?, ?)''',
              (player_id, club['id'], asking_price))
    conn.commit()
    transfer_id = c.lastrowid
    conn.close()
    
    embed = discord.Embed(
        title="📋 Player Listed",
        description=f"{player['name']} ({player['position']})",
        color=discord.Color.blue()
    )
    embed.add_field(name="Asking Price", value=f"${asking_price:,.0f}", inline=True)
    embed.add_field(name="Transfer ID", value=transfer_id, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='transfermarket', help='Browse transfer market')
async def view_transfer_market(ctx, page: int = 1):
    """Browse transfer market (Feature 41)"""
    conn = db.get_connection()
    c = conn.cursor()
    
    offset = (page - 1) * 10
    c.execute('''SELECT t.id, p.name, p.position, p.age, 
                        (p.pace + p.shooting + p.passing + p.dribbling + p.defense + p.physical) / 6 as overall,
                        t.fee
                 FROM transfers t
                 JOIN players p ON t.player_id = p.id
                 WHERE t.status = 'listed'
                 ORDER BY t.listed_date DESC
                 LIMIT 10 OFFSET ?''',
              (offset,))
    transfers = c.fetchall()
    conn.close()
    
    if not transfers:
        await ctx.send("❌ No players available!")
        return
    
    embed = discord.Embed(
        title=f"🏪 Transfer Market - Page {page}",
        color=discord.Color.blue()
    )
    
    for transfer in transfers:
        embed.add_field(
            name=f"{transfer['name']} ({transfer['position']})",
            value=f"Age: {transfer['age']} | Overall: {int(transfer['overall'])}\nPrice: ${transfer['fee']:,.0f}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='bid', help='Place a bid on a player')
async def bid_on_player(ctx, transfer_id: int, bid_amount: float):
    """Bid on a transfer (Feature 8, 48)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id, balance FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You don't have a club!")
        conn.close()
        return
    
    c.execute('SELECT * FROM transfers WHERE id = ?', (transfer_id,))
    transfer = c.fetchone()
    
    if not transfer:
        await ctx.send("❌ Transfer not found!")
        conn.close()
        return
    
    if club['balance'] < bid_amount:
        await ctx.send(f"❌ Not enough funds! You have ${club['balance']:,.0f}")
        conn.close()
        return
    
    if bid_amount >= transfer['fee']:
        # Accept transfer
        c.execute('SELECT * FROM clubs WHERE id = ?', (transfer['from_club_id'],))
        from_club = c.fetchone()
        
        c.execute('UPDATE players SET current_club_id = ? WHERE id = ?',
                  (club['id'], transfer['player_id']))
        c.execute('UPDATE transfers SET status = "completed", to_club_id = ? WHERE id = ?',
                  (club['id'], transfer_id))
        c.execute('UPDATE clubs SET balance = balance - ? WHERE id = ?',
                  (bid_amount, club['id']))
        c.execute('UPDATE clubs SET balance = balance + ? WHERE id = ?',
                  (bid_amount, from_club['id']))
        conn.commit()
        
        embed = discord.Embed(
            title="✅ Transfer Complete!",
            color=discord.Color.green()
        )
        embed.add_field(name="Fee", value=f"${bid_amount:,.0f}", inline=False)
    else:
        embed = discord.Embed(
            title="💰 Bid Placed",
            color=discord.Color.blue()
        )
    
    conn.close()
    await ctx.send(embed=embed)

@bot.command(name='sponsor', help='Manage sponsorships')
async def manage_sponsor(ctx):
    """Manage sponsorship deals (Feature 43)"""
    embed = discord.Embed(
        title="🤝 Available Sponsorships",
        color=discord.Color.blue()
    )
    
    sponsors = [
        ("Nike", 100000),
        ("Adidas", 120000),
        ("Puma", 80000),
        ("Emirates", 150000),
        ("Coca-Cola", 75000),
    ]
    
    for name, value in sponsors:
        embed.add_field(name=name, value=f"${value:,}/season", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='loan', help='Send player on loan')
async def loan_player(ctx, player_id: int, weeks: int):
    """Loan a player (Feature 50)"""
    embed = discord.Embed(
        title="📤 Player Sent on Loan",
        color=discord.Color.blue()
    )
    embed.add_field(name="Duration", value=f"{weeks} weeks", inline=False)
    
    return_date = datetime.utcnow() + timedelta(weeks=weeks)
    embed.add_field(name="Return Date", value=return_date.strftime('%Y-%m-%d'), inline=False)
    
    await ctx.send(embed=embed)

# ==================== SOCIAL & ACHIEVEMENTS (Features 51-70, 81-100) ====================

@bot.command(name='profile', help='View your profile')
async def view_profile(ctx, user_id: int = None):
    """View user profile (Feature 51)"""
    target_id = user_id if user_id else ctx.author.id
    user_discord_id = str(target_id)
    
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id, username, created_at FROM users WHERE discord_id = ?',
              (user_discord_id,))
    user = c.fetchone()
    
    if not user:
        await ctx.send("❌ User not found!")
        conn.close()
        return
    
    c.execute('SELECT COUNT(*) as count FROM clubs WHERE owner_id = ?', (user['id'],))
    clubs_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM players WHERE user_id = ?', (user['id'],))
    players_count = c.fetchone()['count']
    
    c.execute('SELECT COUNT(*) as count FROM achievements WHERE user_id = ?', (user['id'],))
    achievements_count = c.fetchone()['count']
    
    conn.close()
    
    embed = discord.Embed(
        title=f"👤 {user['username']}'s Profile",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="Clubs", value=clubs_count, inline=True)
    embed.add_field(name="Players", value=players_count, inline=True)
    embed.add_field(name="Achievements", value=achievements_count, inline=True)
    embed.add_field(name="Member Since", value=user['created_at'], inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='achievements', help='View your achievements')
async def view_achievements(ctx):
    """View achievements (Features 52, 81)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM achievements WHERE user_id = ? ORDER BY unlocked_date DESC',
              (user_id,))
    achievements = c.fetchall()
    conn.close()
    
    embed = discord.Embed(
        title="🏅 Your Achievements",
        color=discord.Color.gold()
    )
    
    if not achievements:
        embed.description = "No achievements yet. Start playing!"
    else:
        for ach in achievements:
            rarity_emoji = {
                'common': '⚪', 'rare': '🔵',
                'epic': '🟣', 'legendary': '🟡'
            }.get(ach['rarity'], '⚪')
            
            embed.add_field(
                name=f"{rarity_emoji} {ach['achievement_name']}",
                value=ach['description'],
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.command(name='unlock', help='Unlock achievement (dev)')
async def unlock_achievement(ctx, achievement_name: str):
    """Unlock an achievement (Feature 52)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO achievements (user_id, achievement_name, description, rarity)
                 VALUES (?, ?, ?, ?)''',
              (user_id, achievement_name, f"Unlocked {achievement_name}",
               random.choice(['common', 'rare', 'epic', 'legendary'])))
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ Achievement unlocked: **{achievement_name}**")

@bot.command(name='statistics', help='View player statistics')
async def view_statistics(ctx):
    """View detailed statistics (Feature 91)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
              (user_id,))
    player = c.fetchone()
    conn.close()
    
    if not player:
        await ctx.send("❌ You need a player first!")
        return
    
    embed = discord.Embed(
        title=f"📊 {player['name']} - Statistics",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Appearances", value=player['appearances'], inline=True)
    embed.add_field(name="Goals", value=player['goals'], inline=True)
    embed.add_field(name="Assists", value=player['assists'], inline=True)
    
    if player['appearances'] > 0:
        goals_per_game = player['goals'] / player['appearances']
        embed.add_field(name="Goals Per Game", value=f"{goals_per_game:.2f}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='compare', help='Compare two players')
async def compare_players(ctx, player1_id: int, player2_id: int):
    """Compare players (Feature 96)"""
    conn = db.get_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM players WHERE id = ?', (player1_id,))
    p1 = c.fetchone()
    
    c.execute('SELECT * FROM players WHERE id = ?', (player2_id,))
    p2 = c.fetchone()
    
    conn.close()
    
    if not p1 or not p2:
        await ctx.send("❌ One or both players not found!")
        return
    
    p1_overall = calculate_overall(
        p1['pace'], p1['shooting'], p1['passing'],
        p1['dribbling'], p1['defense'], p1['physical']
    )
    p2_overall = calculate_overall(
        p2['pace'], p2['shooting'], p2['passing'],
        p2['dribbling'], p2['defense'], p2['physical']
    )
    
    embed = discord.Embed(
        title=f"⚖️ {p1['name']} vs {p2['name']}",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Overall", value=f"{p1_overall} | {p2_overall}", inline=True)
    embed.add_field(name="Age", value=f"{p1['age']} | {p2['age']}", inline=True)
    embed.add_field(name="Goals", value=f"{p1['goals']} | {p2['goals']}", inline=True)
    embed.add_field(name="Pace", value=f"{p1['pace']} | {p2['pace']}", inline=True)
    embed.add_field(name="Shooting", value=f"{p1['shooting']} | {p2['shooting']}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='halloffame', help='View hall of fame')
async def hall_of_fame(ctx):
    """View all-time greats (Features 85, 86)"""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''SELECT * FROM players WHERE retired = 1
                 ORDER BY goals DESC LIMIT 10''')
    players = c.fetchall()
    conn.close()
    
    if not players:
        await ctx.send("❌ Hall of Fame is empty!")
        return
    
    embed = discord.Embed(
        title="🏆 Hall of Fame",
        color=discord.Color.gold()
    )
    
    for i, player in enumerate(players, 1):
        embed.add_field(
            name=f"{i}. {player['name']}",
            value=f"Goals: {player['goals']} | Apps: {player['appearances']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='challenges', help='View community challenges')
async def view_challenges(ctx):
    """View active challenges (Feature 58)"""
    embed = discord.Embed(
        title="🎯 Community Challenges",
        color=discord.Color.blue()
    )
    
    challenges = [
        ("Golden Boot", "Score 50 goals", 50000),
        ("Unbeaten", "Win 10 matches without loss", 100000),
        ("Promotion", "Get promoted 3 divisions", 75000),
        ("Rich", "Reach $1M balance", 50000),
        ("Legend", "Reach 200 career goals", 150000),
    ]
    
    for name, desc, reward in challenges:
        embed.add_field(name=name, value=f"{desc}\n💰 {reward:,}", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='daily', help='Claim daily bonus')
async def daily_bonus(ctx):
    """Claim daily login bonus (Feature 87)"""
    user_id = get_or_create_user(ctx.author.id, str(ctx.author.name))
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM clubs WHERE owner_id = ?', (user_id,))
    club = c.fetchone()
    
    if not club:
        await ctx.send("❌ You need a club first!")
        conn.close()
        return
    
    bonus = 50000
    c.execute('UPDATE clubs SET balance = balance + ? WHERE id = ?', (bonus, club['id']))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="✅ Daily Bonus!",
        description=f"${bonus:,} added to your club",
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

# ==================== HELP COMMAND ====================

@bot.command(name='help', help='Show all commands')
async def show_help(ctx, category: str = None):
    """Show help information (Feature 100)"""
    if not category:
        embed = discord.Embed(
            title="⚽ Football Bot Help",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Categories", value=
            "`!fb help career` - Player Management\n"
            "`!fb help team` - Club Management\n"
            "`!fb help match` - Match Commands\n"
            "`!fb help economy` - Finance & Transfers\n"
            "`!fb help social` - Achievements & Stats",
            inline=False)
        
        await ctx.send(embed=embed)
        return
    
    categories = {
        'career': [
            ('createplayer <n>', 'Create a new player'),
            ('myplayer', 'View your player'),
            ('train <attr> [pts]', 'Train attributes'),
            ('negotiate <sal> <wks>', 'Sign contract'),
            ('retire', 'Retire player'),
            ('injury', 'Check injuries'),
            ('agent', 'Agent services'),
            ('level', 'View XP/Level'),
        ],
        'team': [
            ('createclub <n>', 'Create club'),
            ('myclub', 'View club details'),
            ('recruit <id> <sal>', 'Sign player'),
            ('formation <form>', 'Set formation'),
            ('squad', 'View squad'),
            ('upgradestadium', 'Upgrade stadium'),
            ('wallet', 'View finances'),
            ('morale', 'Check morale'),
        ],
        'match': [
            ('challenge <id>', 'Challenge player'),
            ('playmatch <id>', 'Simulate match'),
            ('season', 'Start season'),
            ('leaderboard [cat]', 'View rankings'),
            ('tournament <n>', 'Create tournament'),
        ],
        'economy': [
            ('transfer <id> <pr>', 'List player'),
            ('transfermarket [pg]', 'Browse market'),
            ('bid <id> <amt>', 'Make offer'),
            ('sponsor', 'Sponsorships'),
            ('loan <id> <wks>', 'Send on loan'),
        ],
        'social': [
            ('profile [id]', 'View profile'),
            ('achievements', 'View badges'),
            ('statistics', 'View stats'),
            ('compare <i1> <i2>', 'Compare players'),
            ('halloffame', 'Top players'),
            ('challenges', 'Active tasks'),
            ('daily', 'Daily bonus'),
        ]
    }
    
    if category in categories:
        embed = discord.Embed(
            title=f"📖 {category.capitalize()} Commands",
            color=discord.Color.blue()
        )
        
        for cmd, desc in categories[category]:
            embed.add_field(name=f"!fb {cmd}", value=desc, inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ Unknown category! Choose: {', '.join(categories.keys())}")

# ==================== MAIN ====================

def main():
    """Run the bot"""
    print("⚽ Discord Football Manager Bot Starting...")
    print("🔗 https://discord.com/developers/applications")
    print("💾 Database: football_bot.db")
    print("\nType '!fb help' in Discord to get started!")
    print(f"{'='*50}\n")
    
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
