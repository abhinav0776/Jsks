import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
# Intents
intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands
bot = commands.Bot(command_prefix='+', intents=intents)
# At the top of your file, add this to global storage section:
race_lobbies: Dict[int, Dict] = {}

# Then add this command to clear and reset everything:

@bot.tree.command(name="clearraces", description="Clear all race data (admin only)")
async def clearraces(interaction: discord.Interaction):
    """Force clear all races and lobbies"""
    
    # Check if user has admin permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need administrator permissions to use this command!",
            ephemeral=True
        )
        return
    
    # Clear all race data
    active_races.clear()
    race_lobbies.clear()
    race_messages.clear()
    
    await interaction.response.send_message(
        "✅ All race data cleared! You can now create new races.",
        ephemeral=True
    )


@bot.tree.command(name="debugrace", description="Show current race status")
async def debugrace(interaction: discord.Interaction):
    """Debug command to see race state"""
    
    embed = discord.Embed(
        title="🔧 Race Debug Info",
        color=discord.Color.blue()
    )
    
    # Check lobby
    if interaction.channel_id in race_lobbies:
        lobby = race_lobbies[interaction.channel_id]
        embed.add_field(
            name="Lobby Status",
            value=f"Players: {len(lobby['players'])}\nStarted: {lobby['started']}\nTrack: {lobby['track']}",
            inline=False
        )
    else:
        embed.add_field(name="Lobby Status", value="No lobby in this channel", inline=False)
    
    # Check active race
    if interaction.channel_id in active_races:
        race = active_races[interaction.channel_id]
        embed.add_field(
            name="Active Race",
            value=f"Lap: {race.current_lap}/{race.total_laps}\nDrivers: {len(race.drivers)}",
            inline=False
        )
    else:
        embed.add_field(name="Active Race", value="No active race", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
# ✅ This MUST come before any class definitions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('F1Bot')

# # ============================================================================
# DATABASE SYSTEM - PRODUCTION READY
# # ============================================================================

class Database:
    def __init__(self, db_path="f1_racing.db"):
        self.db_path = db_path
        self.init_database()
        logger.info("Database initialized successfully")
    
    def get_conn(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_conn()
        c = conn.cursor()
        
        # USERS TABLE - Complete driver profiles
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            driver_name TEXT NOT NULL,
            skill_rating REAL DEFAULT 50.0,
            aggression REAL DEFAULT 50.0,
            consistency REAL DEFAULT 50.0,
            experience INTEGER DEFAULT 0,
            fatigue REAL DEFAULT 0.0,
            focus REAL DEFAULT 100.0,
            reputation REAL DEFAULT 50.0,
            career_wins INTEGER DEFAULT 0,
            career_podiums INTEGER DEFAULT 0,
            career_points INTEGER DEFAULT 0,
            money INTEGER DEFAULT 25000,
            nationality TEXT DEFAULT 'UN',
            license_level TEXT DEFAULT 'rookie',
            current_form REAL DEFAULT 50.0,
            rain_skill REAL DEFAULT 50.0,
            overtaking_skill REAL DEFAULT 50.0,
            defending_skill REAL DEFAULT 50.0,
            quali_skill REAL DEFAULT 50.0,
            race_starts INTEGER DEFAULT 0,
            dnf_count INTEGER DEFAULT 0,
            fastest_laps INTEGER DEFAULT 0,
            pole_positions INTEGER DEFAULT 0,
            championship_wins INTEGER DEFAULT 0,
            skill_points INTEGER DEFAULT 0,
            premium_currency INTEGER DEFAULT 0,
            daily_login_streak INTEGER DEFAULT 0,
            last_login TEXT,
            total_distance_km REAL DEFAULT 0.0,
            total_race_time_seconds INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # CARS TABLE - Complete vehicle management
        c.execute('''CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            car_name TEXT NOT NULL,
            car_tier TEXT DEFAULT 'starter',
            engine_power REAL DEFAULT 50.0,
            aero REAL DEFAULT 50.0,
            handling REAL DEFAULT 50.0,
            reliability REAL DEFAULT 100.0,
            tyre_wear_rate REAL DEFAULT 1.0,
            fuel_efficiency REAL DEFAULT 1.0,
            weight_balance REAL DEFAULT 50.0,
            engine_wear REAL DEFAULT 0.0,
            gearbox_wear REAL DEFAULT 0.0,
            chassis_wear REAL DEFAULT 0.0,
            brake_wear REAL DEFAULT 0.0,
            suspension_wear REAL DEFAULT 0.0,
            livery TEXT DEFAULT 'default',
            livery_color_primary TEXT DEFAULT '#FF0000',
            livery_color_secondary TEXT DEFAULT '#FFFFFF',
            engine_mode TEXT DEFAULT 'balanced',
            drs_efficiency REAL DEFAULT 1.0,
            ers_power REAL DEFAULT 50.0,
            downforce_level REAL DEFAULT 50.0,
            car_value INTEGER DEFAULT 50000,
            insured INTEGER DEFAULT 0,
            insurance_expiry TEXT,
            total_races INTEGER DEFAULT 0,
            total_wins INTEGER DEFAULT 0,
            total_podiums INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )''')
        
        # AI PROFILES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS ai_profiles (
            ai_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_name TEXT NOT NULL,
            skill_rating REAL NOT NULL,
            risk_tendency REAL DEFAULT 50.0,
            overtake_chance REAL DEFAULT 50.0,
            defense_skill REAL DEFAULT 50.0,
            mistake_rate REAL DEFAULT 10.0,
            strategy_bias TEXT DEFAULT 'balanced',
            difficulty TEXT DEFAULT 'medium',
            nationality TEXT DEFAULT 'UN',
            team_name TEXT DEFAULT 'Independent',
            aggression REAL DEFAULT 50.0,
            consistency REAL DEFAULT 50.0,
            rain_skill REAL DEFAULT 50.0,
            quali_skill REAL DEFAULT 50.0,
            tyre_management REAL DEFAULT 50.0
        )''')
        
        # RACE HISTORY TABLE - Detailed race records
        c.execute('''CREATE TABLE IF NOT EXISTS race_history (
            race_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            points INTEGER DEFAULT 0,
            fastest_lap REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            track TEXT NOT NULL,
            weather TEXT DEFAULT 'clear',
            grid_position INTEGER,
            positions_gained INTEGER DEFAULT 0,
            pit_stops INTEGER DEFAULT 0,
            dnf INTEGER DEFAULT 0,
            dnf_reason TEXT,
            race_time REAL,
            average_lap REAL,
            damage_sustained REAL DEFAULT 0.0,
            penalties INTEGER DEFAULT 0,
            penalty_time REAL DEFAULT 0.0,
            overtakes_made INTEGER DEFAULT 0,
            overtakes_lost INTEGER DEFAULT 0,
            race_distance_km REAL DEFAULT 0.0,
            safety_car_laps INTEGER DEFAULT 0,
            drs_uses INTEGER DEFAULT 0,
            ers_deploys INTEGER DEFAULT 0,
            money_earned INTEGER DEFAULT 0,
            experience_gained INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # LEAGUES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS leagues (
            league_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_name TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            max_drivers INTEGER DEFAULT 20,
            current_season INTEGER DEFAULT 1,
            points_system TEXT DEFAULT 'standard',
            rules TEXT,
            private INTEGER DEFAULT 0,
            password TEXT,
            entry_fee INTEGER DEFAULT 0,
            prize_pool INTEGER DEFAULT 0,
            season_start_date TEXT,
            season_end_date TEXT,
            races_per_season INTEGER DEFAULT 10,
            current_race INTEGER DEFAULT 0,
            FOREIGN KEY (creator_id) REFERENCES users(user_id)
        )''')
        
        # LEAGUE MEMBERS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS league_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            join_date TEXT DEFAULT CURRENT_TIMESTAMP,
            season_points INTEGER DEFAULT 0,
            season_wins INTEGER DEFAULT 0,
            season_podiums INTEGER DEFAULT 0,
            season_fastest_laps INTEGER DEFAULT 0,
            team_name TEXT,
            car_number INTEGER,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (league_id) REFERENCES leagues(league_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(league_id, user_id)
        )''')
        
        # TOURNAMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
            tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_name TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            start_date TEXT,
            status TEXT DEFAULT 'registration',
            tournament_type TEXT DEFAULT 'single_elimination',
            max_participants INTEGER DEFAULT 16,
            prize_pool INTEGER DEFAULT 0,
            entry_fee INTEGER DEFAULT 0,
            current_round INTEGER DEFAULT 1,
            total_rounds INTEGER DEFAULT 4,
            winner_id INTEGER,
            FOREIGN KEY (creator_id) REFERENCES users(user_id)
        )''')
        
        # TOURNAMENT MATCHES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS tournament_matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            round_number INTEGER NOT NULL,
            match_number INTEGER NOT NULL,
            player1_id INTEGER,
            player2_id INTEGER,
            winner_id INTEGER,
            race_completed INTEGER DEFAULT 0,
            race_id INTEGER,
            scheduled_time TEXT,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id)
        )''')
        
        # SPONSORS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
            sponsor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sponsor_name TEXT NOT NULL,
            sponsor_tier TEXT DEFAULT 'bronze',
            bonus_type TEXT NOT NULL,
            bonus_amount REAL NOT NULL,
            requirement_type TEXT NOT NULL,
            requirement_value INTEGER NOT NULL,
            contract_length INTEGER NOT NULL,
            payment_per_race INTEGER NOT NULL,
            unlock_requirement TEXT,
            logo_emoji TEXT DEFAULT '🏢'
        )''')
        
        # USER SPONSORS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_sponsors (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sponsor_id INTEGER NOT NULL,
            signed_date TEXT DEFAULT CURRENT_TIMESTAMP,
            races_remaining INTEGER NOT NULL,
            total_earned INTEGER DEFAULT 0,
            performance_bonus_earned INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id)
        )''')
        
        # ACHIEVEMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS achievements (
            achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            reward_money INTEGER DEFAULT 0,
            reward_skill_points INTEGER DEFAULT 0,
            reward_premium INTEGER DEFAULT 0,
            rarity TEXT DEFAULT 'common',
            category TEXT DEFAULT 'racing',
            icon TEXT DEFAULT '🏆',
            unlock_criteria TEXT NOT NULL,
            is_hidden INTEGER DEFAULT 0
        )''')
        
        # USER ACHIEVEMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            unlocked_date TEXT DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 100,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id),
            UNIQUE(user_id, achievement_id)
        )''')
        
        # SKILL TREE TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS skill_tree (
            skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            skill_category TEXT NOT NULL,
            skill_tier INTEGER NOT NULL,
            cost_points INTEGER NOT NULL,
            effect_type TEXT NOT NULL,
            effect_value REAL NOT NULL,
            requires_skill INTEGER,
            description TEXT NOT NULL,
            max_level INTEGER DEFAULT 1,
            FOREIGN KEY (requires_skill) REFERENCES skill_tree(skill_id)
        )''')
        
        # USER SKILLS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            unlocked_date TEXT DEFAULT CURRENT_TIMESTAMP,
            skill_level INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (skill_id) REFERENCES skill_tree(skill_id),
            UNIQUE(user_id, skill_id)
        )''')
        
        # SETUPS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS setups (
            setup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            setup_name TEXT NOT NULL,
            track TEXT NOT NULL,
            conditions TEXT DEFAULT 'dry',
            front_wing REAL DEFAULT 50.0,
            rear_wing REAL DEFAULT 50.0,
            differential REAL DEFAULT 50.0,
            suspension_front REAL DEFAULT 50.0,
            suspension_rear REAL DEFAULT 50.0,
            brake_balance REAL DEFAULT 50.0,
            tyre_pressure_fl REAL DEFAULT 23.0,
            tyre_pressure_fr REAL DEFAULT 23.0,
            tyre_pressure_rl REAL DEFAULT 21.0,
            tyre_pressure_rr REAL DEFAULT 21.0,
            anti_roll_bar_front REAL DEFAULT 50.0,
            anti_roll_bar_rear REAL DEFAULT 50.0,
            ride_height_front REAL DEFAULT 50.0,
            ride_height_rear REAL DEFAULT 50.0,
            camber_front REAL DEFAULT 0.0,
            camber_rear REAL DEFAULT 0.0,
            toe_front REAL DEFAULT 0.0,
            toe_rear REAL DEFAULT 0.0,
            is_favorite INTEGER DEFAULT 0,
            times_used INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # MARKET TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS market (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            listed_date TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            buyer_id INTEGER,
            sold_date TEXT,
            FOREIGN KEY (seller_id) REFERENCES users(user_id)
        )''')
        
        # LOANS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS loans (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            interest_rate REAL NOT NULL,
            remaining_amount INTEGER NOT NULL,
            issue_date TEXT DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            payments_made INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # RIVALRIES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS rivalries (
            rivalry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            intensity INTEGER DEFAULT 0,
            user1_wins INTEGER DEFAULT 0,
            user2_wins INTEGER DEFAULT 0,
            total_races INTEGER DEFAULT 0,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            last_race_date TEXT,
            FOREIGN KEY (user1_id) REFERENCES users(user_id),
            FOREIGN KEY (user2_id) REFERENCES users(user_id),
            UNIQUE(user1_id, user2_id)
        )''')
        
        # TEAM CONTRACTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS team_contracts (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            team_name TEXT NOT NULL,
            contract_value INTEGER NOT NULL,
            contract_length INTEGER NOT NULL,
            races_remaining INTEGER NOT NULL,
            bonus_per_win INTEGER DEFAULT 0,
            bonus_per_podium INTEGER DEFAULT 0,
            signed_date TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # DAILY CHALLENGES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS daily_challenges (
            challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_name TEXT NOT NULL,
            description TEXT NOT NULL,
            challenge_type TEXT NOT NULL,
            target_value INTEGER NOT NULL,
            reward_money INTEGER DEFAULT 0,
            reward_xp INTEGER DEFAULT 0,
            reward_premium INTEGER DEFAULT 0,
            difficulty TEXT DEFAULT 'medium',
            valid_date TEXT NOT NULL
        )''')
        
        # USER CHALLENGES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            completed_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (challenge_id) REFERENCES daily_challenges(challenge_id),
            UNIQUE(user_id, challenge_id)
        )''')
        
        # WEATHER EVENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS weather_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            track TEXT NOT NULL,
            event_date TEXT NOT NULL,
            weather_type TEXT NOT NULL,
            severity INTEGER DEFAULT 1,
            duration_minutes INTEGER DEFAULT 30
        )''')
        
        # NOTIFICATIONS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # TELEMETRY DATA TABLE (for detailed race analysis)
        c.execute('''CREATE TABLE IF NOT EXISTS telemetry_data (
            telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            lap_number INTEGER NOT NULL,
            sector_1_time REAL,
            sector_2_time REAL,
            sector_3_time REAL,
            top_speed REAL,
            tyre_temp_avg REAL,
            fuel_used REAL,
            ers_deployed REAL,
            drs_active INTEGER DEFAULT 0,
            incidents INTEGER DEFAULT 0,
            FOREIGN KEY (race_id) REFERENCES race_history(race_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # PARTS INVENTORY TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS parts_inventory (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            part_type TEXT NOT NULL,
            part_name TEXT NOT NULL,
            part_tier TEXT DEFAULT 'common',
            stat_bonus_type TEXT NOT NULL,
            stat_bonus_value REAL NOT NULL,
            durability REAL DEFAULT 100.0,
            quantity INTEGER DEFAULT 1,
            purchase_price INTEGER,
            acquired_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # SPECIAL EVENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS special_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            rewards TEXT,
            participant_limit INTEGER DEFAULT 100,
            entry_requirement TEXT,
            status TEXT DEFAULT 'upcoming'
        )''')
        
        # PENALTY SYSTEM TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS penalty_history (
            penalty_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            race_id INTEGER,
            penalty_type TEXT NOT NULL,
            penalty_seconds REAL DEFAULT 0.0,
            penalty_points INTEGER DEFAULT 0,
            reason TEXT NOT NULL,
            issued_date TEXT DEFAULT CURRENT_TIMESTAMP,
            served INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # BROADCAST MESSAGES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS broadcast_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_text TEXT NOT NULL,
            message_type TEXT DEFAULT 'announcement',
            priority INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            active INTEGER DEFAULT 1
        )''')
        
        conn.commit()
        conn.close()
        
        # Seed initial data
        self.seed_all_data()
    
    def seed_all_data(self):
        """Seed all initial game data"""
        self.seed_ai_drivers()
        self.seed_sponsors()
        self.seed_achievements()
        self.seed_skill_tree()
        self.seed_daily_challenges()
        logger.info("All seed data initialized")
    
    def seed_ai_drivers(self):
        """Seed AI driver profiles"""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ai_profiles")
        if c.fetchone()[0] == 0:
            ai_drivers = [
                ("Max Verstappen", 95, 75, 90, 85, 5, "aggressive", "champion", "NL", "Red Bull Racing", 75, 90, 85, 92, 88),
                ("Lewis Hamilton", 93, 60, 88, 90, 8, "balanced", "legend", "GB", "Mercedes AMG", 60, 92, 88, 93, 91),
                ("Charles Leclerc", 88, 70, 85, 80, 12, "aggressive", "legend", "MC", "Scuderia Ferrari", 70, 85, 82, 88, 84),
                ("Lando Norris", 85, 65, 82, 78, 15, "balanced", "pro", "GB", "McLaren F1", 65, 83, 80, 85, 82),
                ("Carlos Sainz", 84, 55, 80, 85, 18, "defensive", "pro", "ES", "Scuderia Ferrari", 55, 85, 83, 84, 86),
                ("George Russell", 83, 50, 78, 82, 20, "balanced", "pro", "GB", "Mercedes AMG", 50, 84, 79, 83, 81),
                ("Fernando Alonso", 90, 80, 92, 95, 10, "aggressive", "legend", "ES", "Aston Martin", 80, 93, 90, 91, 94),
                ("Oscar Piastri", 80, 60, 75, 70, 22, "balanced", "pro", "AU", "McLaren F1", 60, 78, 72, 80, 76),
                ("Sergio Perez", 82, 65, 76, 80, 25, "defensive", "pro", "MX", "Red Bull Racing", 65, 80, 78, 82, 79),
                ("Pierre Gasly", 78, 70, 74, 72, 28, "balanced", "pro", "FR", "Alpine F1", 70, 76, 74, 78, 75),
                ("Esteban Ocon", 77, 68, 72, 74, 30, "balanced", "pro", "FR", "Alpine F1", 68, 75, 73, 77, 74),
                ("Lance Stroll", 72, 55, 65, 68, 35, "defensive", "intermediate", "CA", "Aston Martin", 55, 70, 67, 72, 69),
                ("Yuki Tsunoda", 76, 75, 70, 65, 32, "aggressive", "pro", "JP", "RB F1", 75, 73, 68, 76, 71),
                ("Daniel Ricciardo", 85, 72, 80, 82, 20, "aggressive", "pro", "AU", "RB F1", 72, 83, 80, 85, 81),
                ("Nico Hulkenberg", 80, 60, 75, 85, 22, "defensive", "pro", "DE", "Haas F1", 60, 78, 82, 80, 80),
                ("Kevin Magnussen", 75, 78, 72, 70, 30, "aggressive", "intermediate", "DK", "Haas F1", 78, 74, 71, 75, 73),
                ("Valtteri Bottas", 84, 58, 79, 83, 19, "balanced", "pro", "FI", "Kick Sauber", 58, 82, 81, 84, 82),
                ("Zhou Guanyu", 74, 62, 70, 72, 28, "balanced", "intermediate", "CN", "Kick Sauber", 62, 72, 70, 74, 71),
                ("Alexander Albon", 79, 64, 76, 77, 24, "balanced", "pro", "TH", "Williams Racing", 64, 78, 75, 79, 76),
                ("Logan Sargeant", 71, 56, 68, 69, 33, "balanced", "intermediate", "US", "Williams Racing", 56, 70, 68, 71, 69),
            ]
            c.executemany('''INSERT INTO ai_profiles 
                (ai_name, skill_rating, risk_tendency, overtake_chance, defense_skill, 
                 mistake_rate, strategy_bias, difficulty, nationality, team_name,
                 aggression, consistency, rain_skill, quali_skill, tyre_management)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', ai_drivers)
            conn.commit()
            logger.info(f"Seeded {len(ai_drivers)} AI drivers")
        conn.close()
    
    def seed_sponsors(self):
        """Seed sponsor companies"""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sponsors")
        if c.fetchone()[0] == 0:
            sponsors = [
                ("Petronas", "platinum", "money_per_race", 5000, "races_completed", 5, 10, 3000, "skill_rating>70", "⛽"),
                ("Shell", "platinum", "money_per_race", 4500, "podiums", 3, 8, 3500, "career_podiums>=5", "🐚"),
                ("Emirates", "gold", "money_per_win", 10000, "wins", 1, 12, 2000, "career_wins>=1", "✈️"),
                ("Rolex", "gold", "bonus_money", 15000, "fastest_laps", 5, 15, 1500, "fastest_laps>=3", "⌚"),
                ("Pirelli", "gold", "tyre_bonus", 0.9, "races_completed", 10, 20, 2500, None, "🏁"),
                ("DHL", "silver", "reliability_bonus", 5.0, "dnf_free_races", 5, 10, 2000, None, "📦"),
                ("Heineken", "silver", "money_per_point", 500, "points_scored", 50, 15, 1000, None, "🍺"),
                ("Aramco", "silver", "fuel_efficiency", 1.1, "races_completed", 8, 12, 2800, None, "⛽"),
                ("AWS", "bronze", "data_bonus", 3000, "top5_finishes", 5, 10, 2200, None, "☁️"),
                ("Puma", "bronze", "skill_boost", 2.0, "podiums", 5, 15, 1800, None, "👟"),
                ("UBS", "bronze", "money_multiplier", 1.15, "money_earned", 50000, 12, 1500, None, "🏦"),
                ("Workday", "bronze", "xp_bonus", 1.2, "races_completed", 15, 10, 1200, None, "💼"),
            ]
            c.executemany('''INSERT INTO sponsors 
                (sponsor_name, sponsor_tier, bonus_type, bonus_amount, requirement_type, 
                 requirement_value, contract_length, payment_per_race, unlock_requirement, logo_emoji)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sponsors)
            conn.commit()
            logger.info(f"Seeded {len(sponsors)} sponsors")
        conn.close()
    
    def seed_achievements(self):
        """Seed achievement system"""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM achievements")
        if c.fetchone()[0] == 0:
            achievements = [
                ("First Victory", "Win your first race", 5000, 10, 0, "common", "racing", "🏆", "win_race:1", 0),
                ("Podium Finisher", "Finish in top 3", 2000, 5, 0, "common", "racing", "🥈", "podium:1", 0),
                ("Perfect Weekend", "Win from pole position", 10000, 20, 5, "rare", "racing", "💎", "pole_and_win:1", 0),
                ("Comeback King", "Win after starting P10 or lower", 15000, 30, 10, "epic", "racing", "👑", "comeback_win:1", 0),
                ("Hat Trick", "Win 3 races in a row", 20000, 50, 15, "legendary", "racing", "🎩", "consecutive_wins:3", 0),
                ("Century Club", "Complete 100 races", 25000, 100, 20, "legendary", "career", "💯", "total_races:100", 0),
                ("Speed Demon", "Set 10 fastest laps", 8000, 15, 5, "rare", "racing", "⚡", "fastest_laps:10", 0),
                ("Survivor", "Finish 50 races without DNF", 12000, 25, 10, "epic", "career", "🛡️", "no_dnf_streak:50", 0),
                ("Wet Weather Master", "Win 5 races in rain", 10000, 20, 10, "rare", "racing", "🌧️", "rain_wins:5", 0),
                ("Championship Legend", "Win a championship", 50000, 200, 50, "legendary", "career", "🏅", "championship_win:1", 1),
                ("Overtake Artist", "Complete 100 overtakes", 7000, 15, 5, "rare", "racing", "🎯", "total_overtakes:100", 0),
                ("Defensive Masterclass", "Defend position for 10 laps", 6000, 12, 5, "rare", "racing", "🔒", "defend_laps:10", 0),
                ("Rookie Sensation", "Win within first 5 races", 15000, 35, 10, "epic", "career", "⭐", "early_win:5", 0),
                ("Reliability Expert", "Complete 25 races without mechanical DNF", 9000, 18, 8, "rare", "career", "🔧", "no_mechanical_dnf:25", 0),
                ("Money Maker", "Earn $100,000", 10000, 20, 5, "epic", "economy", "💰", "total_money:100000", 0),
                ("Perfect Race", "Win with no damage and fastest lap", 20000, 40, 15, "epic", "racing", "✨", "perfect_race:1", 0),
                ("Qualifying Ace", "Score 5 pole positions", 8000, 16, 8, "rare", "racing", "🎯", "pole_positions:5", 0),
                ("Podium Streak", "Finish on podium 5 races in a row", 15000, 30, 12, "epic", "racing", "🔥", "podium_streak:5", 0),
                ("Tire Whisperer", "Complete a race with 1 pit stop on hard tyres", 5000, 10, 5, "uncommon", "racing", "🛞", "one_stop_hard:1", 0),
                ("Grand Slam", "Win with pole, fastest lap, and led every lap", 30000, 60, 25, "legendary", "racing", "💠", "grand_slam:1", 1),
            ]
            c.executemany('''INSERT INTO achievements 
                (achievement_name, description, reward_money, reward_skill_points, reward_premium,
                 rarity, category, icon, unlock_criteria, is_hidden)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', achievements)
            conn.commit()
            logger.info(f"Seeded {len(achievements)} achievements")
        conn.close()
    
    def seed_skill_tree(self):
        """Seed skill tree system"""
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM skill_tree")
        if c.fetchone()[0] == 0:
            skills = [
                # Tier 1 - Foundation
                ("Smooth Operator", "driving", 1, 10, "consistency", 5.0, None, "Improve consistency by 5%", 3),
                ("Quick Reflexes", "driving", 1, 10, "overtaking", 3.0, None, "Boost overtaking skill by 3%", 3),
                ("Defensive Driver", "driving", 1, 10, "defending", 3.0, None, "Improve defending by 3%", 3),
                ("Focus Training", "mental", 1, 10, "focus_regen", 5.0, None, "Faster focus regeneration", 3),
                ("Fitness Pro", "physical", 1, 10, "fatigue_reduction", 5.0, None, "Reduce fatigue buildup by 5%", 3),
                ("Car Control", "technical", 1, 10, "handling_bonus", 3.0, None, "Better car control", 3),
                
                # Tier 2 - Advanced
                ("Tyre Whisperer", "technical", 2, 25, "tyre_management", 10.0, 1, "Reduce tyre wear by 10%", 3),
                ("Fuel Strategist", "technical", 2, 25, "fuel_efficiency", 8.0, 1, "Improved fuel management by 8%", 3),
                ("Rain Master", "driving", 2, 25, "rain_skill", 10.0, 1, "Wet weather specialist +10%", 3),
                ("Qualifying Ace", "driving", 2, 25, "quali_bonus", 7.0, 1, "Better qualifying pace +7%", 3),
                ("Race Craft", "driving", 2, 25, "race_skill", 5.0, 1, "Improved race performance +5%", 3),
                ("Late Braker", "driving", 2, 25, "braking_skill", 6.0, 3, "Better braking zones +6%", 3),
                ("Apex Hunter", "driving", 2, 25, "cornering", 6.0, 1, "Faster through corners +6%", 3),
                ("ERS Management", "technical", 2, 25, "ers_efficiency", 15.0, 6, "Better ERS deployment +15%", 3),
                
                # Tier 3 - Expert
                ("Setup Wizard", "technical", 3, 50, "setup_bonus", 10.0, 7, "Extract 10% more from setups", 2),
                ("Championship Mentality", "mental", 3, 50, "pressure_resistance", 15.0, 4, "Perform better under pressure +15%", 2),
                ("Overtaking Genius", "driving", 3, 50, "overtake_success", 12.0, 2, "Higher overtake success +12%", 2),
                ("Defensive Wall", "driving", 3, 50, "defense_boost", 12.0, 3, "Harder to overtake +12%", 2),
                ("Start Master", "driving", 3, 50, "race_start", 10.0, 1, "Better race starts +10%", 2),
                ("Pit Stop Coordinator", "technical", 3, 50, "pit_efficiency", 2.0, 7, "Faster pit stops -2 seconds", 2),
                ("Weather Prophet", "mental", 3, 50, "weather_adaptation", 20.0, 9, "Adapt faster to weather +20%", 2),
                ("DRS Expert", "technical", 3, 50, "drs_bonus", 15.0, 6, "Better DRS effectiveness +15%", 2),
                
                # Tier 4 - Master (Hidden)
                ("Perfect Vision", "mental", 4, 100, "race_awareness", 25.0, 16, "See opportunities earlier +25%", 1),
                ("Ultimate Speed", "driving", 4, 100, "overall_speed", 15.0, 17, "Raw speed increase +15%", 1),
                ("Legendary Status", "career", 4, 100, "reputation_boost", 50.0, 21, "Massive reputation boost +50%", 1),
            ]
            c.executemany('''INSERT INTO skill_tree 
                (skill_name, skill_category, skill_tier, cost_points, effect_type, effect_value,
                 requires_skill, description, max_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', skills)
            conn.commit()
            logger.info(f"Seeded {len(skills)} skills in skill tree")
        conn.close()
    
    def seed_daily_challenges(self):
        """Seed daily challenges for today"""
        conn = self.get_conn()
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT COUNT(*) FROM daily_challenges WHERE valid_date = ?", (today,))
        
        if c.fetchone()[0] == 0:
            challenges = [
                ("Speed Run", "Complete 3 races", "races_completed", 3, 5000, 500, 0, "easy", today),
                ("Podium Hunter", "Finish in top 3", "podium_finish", 1, 8000, 800, 5, "medium", today),
                ("Overtake Master", "Make 10 overtakes", "overtakes_made", 10, 6000, 600, 0, "medium", today),
                ("Perfect Lap", "Set a fastest lap", "fastest_lap", 1, 10000, 1000, 10, "hard", today),
                ("Rain Dance", "Complete a race in rain", "rain_race", 1, 7000, 700, 5, "medium", today),
            ]
            c.executemany('''INSERT INTO daily_challenges 
                (challenge_name, description, challenge_type, target_value, reward_money,
                 reward_xp, reward_premium, difficulty, valid_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', challenges)
            conn.commit()
            logger.info(f"Seeded {len(challenges)} daily challenges for {today}")
        conn.close()

# # ============================================================================
# RACE ENGINE - ULTRA-REALISTIC SIMULATION
# # ============================================================================

class Driver:
    """Complete driver model with all attributes"""
    def __init__(self, driver_id, name, skill, aggression, consistency, is_ai=False, 
                 car_stats=None, advanced_stats=None):
        # Basic info
        self.id = driver_id
        self.name = name
        self.skill = skill
        self.aggression = aggression
        self.consistency = consistency
        self.is_ai = is_ai
        
        # Advanced stats
        if advanced_stats:
            self.rain_skill = advanced_stats.get('rain_skill', 50)
            self.overtaking_skill = advanced_stats.get('overtaking_skill', 50)
            self.defending_skill = advanced_stats.get('defending_skill', 50)
            self.quali_skill = advanced_stats.get('quali_skill', 50)
            self.focus = advanced_stats.get('focus', 100)
            self.fatigue = advanced_stats.get('fatigue', 0)
            self.tyre_management = advanced_stats.get('tyre_management', 50)
        else:
            self.rain_skill = 50
            self.overtaking_skill = 50
            self.defending_skill = 50
            self.quali_skill = 50
            self.focus = 100
            self.fatigue = 0
            self.tyre_management = 50
        
        # Car stats
        self.car_stats = car_stats or {
            'engine_power': 50, 'aero': 50, 'handling': 50,
            'reliability': 100, 'tyre_wear_rate': 1.0,
            'fuel_efficiency': 1.0, 'ers_power': 50,
            'drs_efficiency': 1.0, 'downforce_level': 50
        }
        
        # Race state
        self.position = 0
        self.grid_position = 0
        self.lap = 0
        self.sector = 0
        self.total_time = 0.0
        self.gap_to_leader = 0.0
        self.gap_to_front = 0.0
        self.lap_time = 0.0
        self.best_lap = 999.0
        self.sector_times = [0.0, 0.0, 0.0]
        
        # Tyres
        self.tyre_compound = "medium"
        self.tyre_condition = 100.0
        self.tyre_age = 0
        self.tyre_temp = 80.0
        self.pit_stops = 0
        self.tyre_history = []
        
        # Fuel & Energy
        self.fuel_load = 100.0
        self.fuel_mix = 50  # 0-100
        self.ers_charge = 100.0
        self.ers_mode = "balanced"
        self.ers_deployed_this_lap = False
        self.total_ers_deployed = 0
        
        # Strategy
        self.push_mode = 50  # 0-100
        self.risk_level = 50
        self.defending = False
        self.attacking = False
        
        # DRS
        self.drs_available = False
        self.drs_active = False
        self.drs_uses = 0
        
        # Status
        self.dnf = False
        self.dnf_reason = ""
        self.in_pits = False
        self.damage = 0.0
        self.penalties = 0
        self.penalty_time = 0.0
        self.warnings = 0
        
        # Stats
        self.overtakes_made = 0
        self.overtakes_lost = 0
        self.positions_gained = 0
        self.incidents = 0
        self.off_track_count = 0
        self.lock_ups = 0
        
        # Setup
        self.setup = {
            'front_wing': 50, 'rear_wing': 50,
            'differential': 50, 'brake_balance': 50,
            'suspension_front': 50, 'suspension_rear': 50
        }
        
        # Telemetry
        self.top_speed_achieved = 0.0
        self.avg_corner_speed = 0.0
        self.sectors_completed = 0

class RaceEngine:
    """Complete F1 race simulation engine"""
    def __init__(self, track="Monza", laps=10, weather="clear", qualifying=True, time_of_day="day"):
        self.track = track
        self.total_laps = laps
        self.current_lap = 0
        self.weather = weather
        self.next_weather = weather
        self.track_temp = 30
        self.air_temp = 25
        self.track_grip = 100.0
        self.safety_car = False
        self.safety_car_laps = 0
        self.virtual_safety_car = False
        self.red_flag = False
        self.drs_enabled = False
        self.qualifying_mode = qualifying
        self.time_of_day = time_of_day
        
        self.drivers: List[Driver] = []
        self.events = []
        self.lap_events = []
        self.radio_messages = []
        
        # Track database (expanded)
        self.track_data = {
            "Monza": {
                "name": "Autodromo Nazionale di Monza",
                "country": "Italy",
                "flag": "🇮🇹",
                "base_lap_time": 80.0,
                "sectors": [25.0, 28.0, 27.0],
                "overtake_difficulty": 30,
                "tyre_wear": 1.0,
                "fuel_consumption": 1.2,
                "drs_zones": 2,
                "corners": 11,
                "elevation_change": 15,
                "track_length_km": 5.793,
                "characteristic": "High Speed Temple",
                "difficulty": "medium"
            },
            "Monaco": {
                "name": "Circuit de Monaco",
                "country": "Monaco",
                "flag": "🇲🇨",
                "base_lap_time": 72.0,
                "sectors": [24.0, 24.0, 24.0],
                "overtake_difficulty": 90,
                "tyre_wear": 0.7,
                "fuel_consumption": 0.8,
                "drs_zones": 1,
                "corners": 19,
                "elevation_change": 42,
                "track_length_km": 3.337,
                "characteristic": "Jewel of F1",
                "difficulty": "extreme"
            },
            "Spa": {
                "name": "Circuit de Spa-Francorchamps",
                "country": "Belgium",
                "flag": "🇧🇪",
                "base_lap_time": 105.0,
                "sectors": [35.0, 38.0, 32.0],
                "overtake_difficulty": 40,
                "tyre_wear": 1.2,
                "fuel_consumption": 1.1,
                "drs_zones": 2,
                "corners": 19,
                "elevation_change": 105,
                "track_length_km": 7.004,
                "characteristic": "Ardennes Rollercoaster",
                "difficulty": "hard"
            },
            "Silverstone": {
                "name": "Silverstone Circuit",
                "country": "Great Britain",
                "flag": "🇬🇧",
                "base_lap_time": 88.0,
                "sectors": [29.0, 30.0, 29.0],
                "overtake_difficulty": 50,
                "tyre_wear": 1.1,
                "fuel_consumption": 1.0,
                "drs_zones": 2,
                "corners": 18,
                "elevation_change": 25,
                "track_length_km": 5.891,
                "characteristic": "High Speed Corners",
                "difficulty": "medium"
            },
            "Suzuka": {
                "name": "Suzuka International Racing Course",
                "country": "Japan",
                "flag": "🇯🇵",
                "base_lap_time": 90.0,
                "sectors": [30.0, 31.0, 29.0],
                "overtake_difficulty": 60,
                "tyre_wear": 1.15,
                "fuel_consumption": 1.05,
                "drs_zones": 1,
                "corners": 18,
                "elevation_change": 40,
                "track_length_km": 5.807,
                "characteristic": "Figure-8 Technical Marvel",
                "difficulty": "hard"
            },
            "Singapore": {
                "name": "Marina Bay Street Circuit",
                "country": "Singapore",
                "flag": "🇸🇬",
                "base_lap_time": 95.0,
                "sectors": [32.0, 32.0, 31.0],
                "overtake_difficulty": 70,
                "tyre_wear": 0.9,
                "fuel_consumption": 0.95,
                "drs_zones": 2,
                "corners": 23,
                "elevation_change": 10,
                "track_length_km": 4.940,
                "characteristic": "Night Street Spectacular",
                "difficulty": "hard"
            },
            "Bahrain": {
                "name": "Bahrain International Circuit",
                "country": "Bahrain",
                "flag": "🇧🇭",
                "base_lap_time": 92.0,
                "sectors": [31.0, 31.0, 30.0],
                "overtake_difficulty": 45,
                "tyre_wear": 1.3,
                "fuel_consumption": 1.1,
                "drs_zones": 3,
                "corners": 15,
                "elevation_change": 20,
                "track_length_km": 5.412,
                "characteristic": "Desert Heat Challenge",
                "difficulty": "medium"
            },
            "Jeddah": {
                "name": "Jeddah Corniche Circuit",
                "country": "Saudi Arabia",
                "flag": "🇸🇦",
                "base_lap_time": 91.0,
                "sectors": [30.0, 31.0, 30.0],
                "overtake_difficulty": 55,
                "tyre_wear": 1.0,
                "fuel_consumption": 1.15,
                "drs_zones": 2,
                "corners": 27,
                "elevation_change": 15,
                "track_length_km": 6.174,
                "characteristic": "Fastest Street Circuit",
                "difficulty": "extreme"
            },
            "Miami": {
                "name": "Miami International Autodrome",
                "country": "USA",
                "flag": "🇺🇸",
                "base_lap_time": 89.0,
                "sectors": [29.0, 30.0, 30.0],
                "overtake_difficulty": 50,
                "tyre_wear": 1.05,
                "fuel_consumption": 1.0,
                "drs_zones": 2,
                "corners": 19,
                "elevation_change": 18,
                "track_length_km": 5.410,
                "characteristic": "Sunshine State Showdown",
                "difficulty": "medium"
            },
            "Las Vegas": {
                "name": "Las Vegas Street Circuit",
                "country": "USA",
                "flag": "🇺🇸",
                "base_lap_time": 94.0,
                "sectors": [31.0, 32.0, 31.0],
                "overtake_difficulty": 40,
                "tyre_wear": 0.95,
                "fuel_consumption": 1.1,
                "drs_zones": 2,
                "corners": 17,
                "elevation_change": 12,
                "track_length_km": 6.120,
                "characteristic": "Neon Night Racing",
                "difficulty": "medium"
            },
        }
        
        if track not in self.track_data:
            self.track = "Monza"
        
        # Weather forecast system
        self.weather_forecast = [weather] * (laps + 1)
        self.generate_weather_forecast()
        
        # Track evolution
        self.track_evolution = 0.0  # Increases over time (rubber buildup)
        self.track_condition = 100.0  # Can decrease with damage/debris
    
    def generate_weather_forecast(self):
        """Generate realistic weather progression"""
        weather_states = ["clear", "cloudy", "light_rain", "rain", "heavy_rain"]
        transition_matrix = {
            "clear": {"clear": 0.7, "cloudy": 0.3},
            "cloudy": {"clear": 0.2, "cloudy": 0.6, "light_rain": 0.2},
            "light_rain": {"cloudy": 0.3, "light_rain": 0.5, "rain": 0.2},
            "rain": {"light_rain": 0.3, "rain": 0.5, "heavy_rain": 0.2},
            "heavy_rain": {"rain": 0.4, "heavy_rain": 0.6}
        }
        
        current_weather = self.weather
        for i in range(1, len(self.weather_forecast)):
            transitions = transition_matrix.get(current_weather, {"clear": 1.0})
            next_weather = random.choices(
                list(transitions.keys()),
                weights=list(transitions.values())
            )[0]
            self.weather_forecast[i] = next_weather
            current_weather = next_weather
    
    def add_driver(self, driver: Driver):
        """Add a driver to the race"""
        self.drivers.append(driver)
        driver.position = len(self.drivers)
        driver.grid_position = len(self.drivers)
    
    def run_qualifying(self):
        """Run qualifying session with Q1, Q2, Q3 simulation"""
        results = []
        
        for driver in self.drivers:
            if driver.dnf:
                continue
            
            base_time = self.track_data[self.track]["base_lap_time"]
            
            # Combined skill factor
            skill_factor = (driver.skill * 0.4 + driver.quali_skill * 0.6) / 100
            car_factor = (driver.car_stats['engine_power'] * 0.4 + 
                         driver.car_stats['aero'] * 0.35 +
                         driver.car_stats['handling'] * 0.25) / 100
            
            # Calculate base quali time
            quali_time = base_time * (1 - skill_factor * 0.15 - car_factor * 0.12)
            
            # Add randomness based on consistency
            consistency_var = (100 - driver.consistency) / 150
            quali_time += random.uniform(-consistency_var, consistency_var)
            
            # Focus and pressure effects
            focus_bonus = (driver.focus / 100) * 0.3
            quali_time -= focus_bonus
            
            # Track conditions
            quali_time *= (110 - self.track_grip) / 100
            
            results.append((driver, quali_time))
        
        # Sort by time
        results.sort(key=lambda x: x[1])
        
        # Set grid positions
        for idx, (driver, time) in enumerate(results):
            driver.grid_position = idx + 1
            driver.position = idx + 1
            
            if idx == 0:
                self.events.append(f"🏁 **POLE POSITION:** {driver.name} - {time:.3f}s")
        
        return results
    
    def calculate_dps(self, driver: Driver, context="race") -> float:
        """
        Driver Performance Score - Advanced calculation
        Returns a score that determines lap time performance
        """
        # Base skill adjusted for context
        base_skill = driver.skill
        
        if context == "qualifying":
            base_skill = (driver.skill * 0.4 + driver.quali_skill * 0.6)
        elif context == "overtake":
            base_skill = (driver.skill * 0.5 + driver.overtaking_skill * 0.5)
        elif context == "defend":
            base_skill = (driver.skill * 0.5 + driver.defending_skill * 0.5)
        
        # Weather adaptation
        if "rain" in self.weather:
            rain_adaptation = (driver.rain_skill / 100)
            base_skill = base_skill * (0.7 + rain_adaptation * 0.3)
        
        # Driver component (30%)
        driver_factor = base_skill * 0.30
        
        # Car performance (30%)
        car_perf = (
            driver.car_stats['engine_power'] * 0.35 +
            driver.car_stats['aero'] * 0.30 +
            driver.car_stats['handling'] * 0.25 +
            driver.car_stats['ers_power'] * 0.10
        )
        car_factor = car_perf * 0.30
        
        # Tyre condition (15%)
        # Includes compound performance and degradation cliff
        compound_performance = {
            "soft": 1.05, "medium": 1.0, "hard": 0.95,
            "inter": 0.90, "wet": 0.85
        }
        tyre_perf = driver.tyre_condition * compound_performance.get(driver.tyre_compound, 1.0)
        tyre_factor = tyre_perf * 0.15
        
        # Track grip (10%)
        grip_factor = self.track_grip * 0.10
        
        # Weather factor (10%)
        weather_factor = 50.0
        if self.weather == "clear":
            weather_factor = 55.0
        elif self.weather == "rain":
            if driver.tyre_compound in ["inter", "wet"]:
                weather_factor = driver.rain_skill
            else:
                weather_factor = 20.0  # Wrong tyres = big penalty
        elif self.weather == "light_rain":
            if driver.tyre_compound == "inter":
                weather_factor = driver.rain_skill * 0.9
            else:
                weather_factor = 35.0
        weather_factor *= 0.10
        
        # Strategy bonus (5%)
        strategy_bonus = (
            driver.push_mode * 0.5 +
            driver.fuel_mix * 0.3 +
            (100 - driver.fatigue) * 0.2
        ) * 0.05
        
        # Setup bonus
        setup_avg = sum(driver.setup.values()) / len(driver.setup)
        setup_bonus = (setup_avg / 100) * 5.0
        
        # Penalties
        focus_penalty = (100 - driver.focus) * 0.08
        fatigue_penalty = driver.fatigue * 0.12
        damage_penalty = driver.damage * 0.18
        
        # Calculate total DPS
        dps = (
            driver_factor + car_factor + tyre_factor + grip_factor +
            weather_factor + strategy_bonus + setup_bonus -
            focus_penalty - fatigue_penalty - damage_penalty
        )
        
        # Consistency variation (this is the "human element")
        variation_range = (100 - driver.consistency) / 8
        variation = random.uniform(-variation_range, variation_range)
        
        # ERS boost
        if driver.ers_mode == "deploy" and driver.ers_charge > 10:
            dps += 5 * (driver.car_stats['ers_power'] / 50)
            driver.ers_deployed_this_lap = True
        
        # DRS boost
        if driver.drs_active:
            drs_boost = 4 * driver.car_stats['drs_efficiency']
            dps += drs_boost
        
        # Track evolution bonus (improves over time)
        evolution_bonus = min(self.track_evolution, 5.0)
        dps += evolution_bonus
        
        return max(0, dps + variation)
    
    def simulate_lap(self):
        """Simulate one complete lap for all drivers"""
        self.current_lap += 1
        self.lap_events = []
        
        # Update weather
        if self.current_lap < len(self.weather_forecast):
            new_weather = self.weather_forecast[self.current_lap]
            if new_weather != self.weather:
                self.weather = new_weather
                self.update_track_conditions()
                self.lap_events.append(f"🌦️ **Weather Change:** {self.weather.upper()}")
        
        # Enable DRS after lap 2
        if self.current_lap >= 3 and not self.safety_car:
            self.drs_enabled = True
        
        # Safety car countdown
        if self.safety_car:
            self.safety_car_laps -= 1
            if self.safety_car_laps <= 0:
                self.safety_car = False
                self.drs_enabled = True
                self.lap_events.append("🏁 **SAFETY CAR IN** - Racing resumes!")
        
        # Track evolution
        self.track_evolution = min(10.0, self.track_evolution + 0.3)
        
        # Simulate each driver's lap
        for driver in self.drivers:
            if driver.dnf:
                continue
            
            driver.lap = self.current_lap
            
            # Reset lap-specific flags
            driver.drs_active = False
            driver.ers_deployed_this_lap = False
            
            # Calculate and record lap time
            lap_time = self.calculate_lap_time(driver)
            driver.lap_time = lap_time
            driver.total_time += lap_time
            
            # Update best lap
            if lap_time < driver.best_lap and not self.safety_car and self.current_lap > 1:
                driver.best_lap = lap_time
                if self.current_lap > 2:  # Don't count first laps
                    self.lap_events.append(f"⏱️ **{driver.name}** - FASTEST LAP {lap_time:.3f}s")
            
            # Update tyre wear
            self.update_tyre_wear(driver)
            
            # Update fuel
            self.update_fuel(driver)
            
            # Update ERS
            self.update_ers(driver)
            
            # Update fatigue & focus
            driver.fatigue = min(100, driver.fatigue + 0.5 + (driver.push_mode / 200))
            driver.focus = max(0, driver.focus - 0.3 - (driver.fatigue / 500))
            
            # Tyre age tracking
            driver.tyre_age += 1
            
            # Check for incidents
            self.check_incidents(driver)
            
            # Apply time penalties
            if driver.penalty_time > 0:
                driver.total_time += driver.penalty_time
                self.lap_events.append(f"⏱️ {driver.name} - {driver.penalty_time:.0f}s time penalty applied")
                driver.penalty_time = 0
        
        # Sort positions
        self.update_positions()
        
        # DRS detection
        self.update_drs()
        
        # Simulate overtakes
        self.simulate_overtakes()
        
        # AI strategy decisions
        self.ai_strategy_decisions()
        
        # Update positions again after overtakes
        self.update_positions()
        
        # Add lap events to main events
        self.events.extend(self.lap_events)
    
    def calculate_lap_time(self, driver: Driver) -> float:
        """Calculate lap time based on all factors"""
        base_time = self.track_data[self.track]["base_lap_time"]
        dps = self.calculate_dps(driver)
        
        # Base lap time calculation
        time_reduction = dps / 10
        lap_time = base_time - time_reduction
        
        # Fuel effect (lighter = faster)
        fuel_bonus = (100 - driver.fuel_load) * 0.018
        lap_time -= fuel_bonus
        
        # Safety car / VSC
        if self.safety_car:
            lap_time = base_time + 18
        elif self.virtual_safety_car:
            lap_time = base_time + 9
        
        # Track evolution (rubber buildup = faster)
        evolution_factor = min(self.track_evolution / 5, 2.5)
        lap_time -= evolution_factor
        
        # Setup influence
        setup_avg = sum(driver.setup.values()) / len(driver.setup)
        setup_influence = (setup_avg - 50) / 25  # ±2 seconds
        lap_time -= setup_influence
        
        # Damage penalty
        lap_time += driver.damage * 0.06
        
        # Tyre temperature effect
        optimal_temp = 95.0
        temp_diff = abs(driver.tyre_temp - optimal_temp)
        temp_penalty = (temp_diff / 10) * 0.5
        lap_time += temp_penalty
        
        # Track condition
        condition_factor = (100 - self.track_condition) / 200
        lap_time += condition_factor
        
        # Random micro-variation
        lap_time += random.uniform(-0.15, 0.15)
        
        # Ensure lap time is realistic
        min_time = base_time * 0.75
        max_time = base_time * 1.5 if not self.safety_car else base_time + 20
        
        return max(min_time, min(max_time, lap_time))
    
    def update_tyre_wear(self, driver: Driver):
        """Advanced tyre degradation model"""
        base_wear = self.track_data[self.track]["tyre_wear"]
        
        # Compound characteristics with cliff effect
        compound_data = {
            "soft": {"wear_rate": 4.5, "performance": 1.05, "cliff_lap": 8, "optimal_temp": 100},
            "medium": {"wear_rate": 2.8, "performance": 1.0, "cliff_lap": 15, "optimal_temp": 95},
            "hard": {"wear_rate": 1.8, "performance": 0.95, "cliff_lap": 25, "optimal_temp": 90},
            "inter": {"wear_rate": 3.2, "performance": 1.0, "cliff_lap": 12, "optimal_temp": 85},
            "wet": {"wear_rate": 2.7, "performance": 1.0, "cliff_lap": 15, "optimal_temp": 80}
        }
        
        compound = compound_data.get(driver.tyre_compound, compound_data["medium"])
        
        # Base wear calculation
        wear = (
            base_wear *
            compound["wear_rate"] *
            driver.car_stats['tyre_wear_rate'] *
            (driver.push_mode / 50) *
            (self.track_temp / 30) *
            (driver.fuel_load / 80)  # Heavier car = more wear
        )
        
        # Tyre management skill effect
        management_factor = 1.0 - (driver.tyre_management / 200)
        wear *= management_factor
        
        # Temperature effect
        if self.track_temp > 40:
            wear *= 1.4
        elif self.track_temp < 20:
            wear *= 0.85
        
        # Driving style effects
        if driver.attacking:
            wear *= 1.2
        if driver.defending:
            wear *= 0.95
        
        # Lock-ups and mistakes increase wear
        if random.random() < (driver.aggression / 500):
            driver.lock_ups += 1
            wear *= 1.5
            if random.random() < 0.3:
                self.lap_events.append(f"🔒 {driver.name} - LOCK UP!")
        
        # Apply wear
        driver.tyre_condition = max(0, driver.tyre_condition - wear)
        
        # Cliff effect (sudden performance drop)
        if driver.tyre_age > compound["cliff_lap"]:
            cliff_penalty = (driver.tyre_age - compound["cliff_lap"]) * 2.5
            driver.tyre_condition = max(0, driver.tyre_condition - cliff_penalty)
            
            if driver.tyre_age == compound["cliff_lap"] + 1:
                self.lap_events.append(f"📉 {driver.name} - Tyres dropping off the cliff!")
        
        # Update tyre temperature
        target_temp = compound["optimal_temp"]
        temp_change = (target_temp - driver.tyre_temp) * 0.15
        driver.tyre_temp += temp_change + random.uniform(-2, 2)
        driver.tyre_temp = max(50, min(130, driver.tyre_temp))
    
    def update_fuel(self, driver: Driver):
        """Fuel consumption with mixture settings"""
        base_consumption = self.track_data[self.track]["fuel_consumption"]
        
        # Calculate consumption
        consumption = (
            base_consumption *
            (driver.fuel_mix / 50) *
            (driver.push_mode / 50) *
            (2.0 - driver.car_stats['fuel_efficiency'])
        )
        
        # ERS deployment increases fuel use
        if driver.ers_deployed_this_lap:
            consumption *= 1.12
        
        # Safety car saves fuel
        if self.safety_car:
            consumption *= 0.25
        elif self.virtual_safety_car:
            consumption *= 0.6
        
        driver.fuel_load = max(0, driver.fuel_load - consumption)
        
        # Critical fuel warnings
        if driver.fuel_load < 8 and driver.fuel_load > 6:
            self.lap_events.append(f"⚠️ {driver.name} - CRITICAL FUEL!")
        elif driver.fuel_load <= 0:
            driver.dnf = True
            driver.dnf_reason = "Out of Fuel"
            self.lap_events.append(f"❌ {driver.name} - OUT OF FUEL!")
    
    def update_ers(self, driver: Driver):
        """ERS (Energy Recovery System) management"""
        if driver.ers_mode == "charging":
            # Harvest energy aggressively
            harvest_rate = 18 + (driver.car_stats['ers_power'] / 8)
            driver.ers_charge = min(100, driver.ers_charge + harvest_rate)
        
        elif driver.ers_mode == "deploy":
            # Deploy energy for performance
            if driver.ers_charge >= 12:
                deploy_amount = 12
                driver.ers_charge -= deploy_amount
                driver.total_ers_deployed += deploy_amount
            else:
                # Auto-switch to balanced if depleted
                driver.ers_mode = "balanced"
                self.radio_messages.append((driver.name, "ERS depleted, switching to balanced"))
        
        else:  # balanced mode
            # Moderate energy recovery
            harvest_rate = 9 + (driver.car_stats['ers_power'] / 10)
            driver.ers_charge = min(100, driver.ers_charge + harvest_rate)
    
    def update_track_conditions(self):
        """Update track grip based on weather"""
        if self.weather == "clear":
            self.track_grip = min(100, self.track_grip + 6)  # Grip improves
        elif self.weather == "cloudy":
            self.track_grip = 96
        elif self.weather == "light_rain":
            self.track_grip = 62
            self.track_condition = max(70, self.track_condition - 2)
        elif self.weather == "rain":
            self.track_grip = 47
            self.track_condition = max(60, self.track_condition - 3)
        elif self.weather == "heavy_rain":
            self.track_grip = 32
            self.track_condition = max(50, self.track_condition - 5)
    
    def update_drs(self):
        """Detect DRS availability (within 1 second of car ahead)"""
        if not self.drs_enabled or self.safety_car or self.virtual_safety_car:
            for driver in self.drivers:
                driver.drs_available = False
            return
        
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            driver = sorted_drivers[i]
            
            # DRS if within 1 second of car ahead
            if driver.gap_to_front < 1.0:
                driver.drs_available = True
            else:
                driver.drs_available = False
    
    def simulate_overtakes(self):
        """Simulate realistic overtaking attempts"""
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            attacker = sorted_drivers[i]
            defender = sorted_drivers[i-1]
            
            # Only attempt if close enough
            if attacker.gap_to_front > 1.8:
                continue
            
            # Skip if safety car
            if self.safety_car or self.virtual_safety_car:
                continue
            
            # Skip if both are being lapped
            if attacker.lap < self.current_lap and defender.lap < self.current_lap:
                continue
            
            # Calculate overtake probability
            overtake_chance = self.calculate_overtake_chance(attacker, defender)
            
            # Attempt overtake
            if random.random() * 100 < overtake_chance:
                self.execute_overtake(attacker, defender)
    
    def calculate_overtake_chance(self, attacker: Driver, defender: Driver) -> float:
        """Calculate probability of successful overtake"""
        
        # Base chance from track characteristics
        base_chance = 100 - self.track_data[self.track]["overtake_difficulty"]
        
        # Performance differential
        attacker_dps = self.calculate_dps(attacker, "overtake")
        defender_dps = self.calculate_dps(defender, "defend")
        skill_diff = (attacker_dps - defender_dps) * 2.5
        
        # DRS advantage
        drs_bonus = 28 if attacker.drs_available else 0
        
        # ERS advantage
        ers_diff = (attacker.ers_charge - defender.ers_charge) / 5
        ers_bonus = max(0, ers_diff)
        
        # Tyre advantage
        tyre_diff = (attacker.tyre_condition - defender.tyre_condition) * 0.35
        
        # Fuel load (lighter = more agile)
        fuel_diff = (defender.fuel_load - attacker.fuel_load) * 0.15
        
        # Defending skill
        defense_penalty = defender.defending_skill * 0.6 if defender.defending else 0
        
        # Weather effect (harder in rain)
        weather_modifier = 1.0
        if "rain" in self.weather:
            weather_modifier = 0.7
        
        # Calculate total
        chance = (
            (base_chance + skill_diff + drs_bonus + ers_bonus + 
             tyre_diff + fuel_diff - defense_penalty) * weather_modifier
        )
        
        # Blue flag situations (lapping)
        if defender.lap < attacker.lap:
            chance += 50  # Much easier to overtake lapped cars
        
        return max(5, min(98, chance))
    
    def execute_overtake(self, attacker: Driver, defender: Driver):
        """Execute an overtake with realistic outcomes"""
        
        # Possible outcomes with probabilities
        outcomes = ["clean", "side_by_side", "contact", "defender_holds", "failed"]
        
        # Base weights
        base_weights = [50, 25, 12, 8, 5]
        
        # Adjust based on conditions
        if "rain" in self.weather:
            base_weights = [30, 25, 25, 10, 10]  # More risky in rain
        
        if attacker.aggression > 75:
            base_weights = [40, 25, 25, 5, 5]  # Aggressive = more contact risk
        
        if defender.defending:
            base_weights = [35, 30, 15, 15, 5]  # Defending = more side-by-side
        
        # Track characteristic
        if self.track_data[self.track]["overtake_difficulty"] > 70:
            base_weights = [35, 25, 20, 12, 8]  # Harder tracks = more variety
        
        outcome = random.choices(outcomes, weights=base_weights)[0]
        
        if outcome == "clean":
            # Perfect overtake
            attacker.position, defender.position = defender.position, attacker.position
            attacker.overtakes_made += 1
            defender.overtakes_lost += 1
            self.lap_events.append(f"🎯 **{attacker.name}** overtakes **{defender.name}**! Clean move!")
            
            # Rivalry intensity increase
            if not attacker.is_ai and not defender.is_ai:
                self.lap_events.append(f"🔥 Rivalry intensity rising!")
        
        elif outcome == "side_by_side":
            # Wheel-to-wheel battle
            self.lap_events.append(f"⚔️ **{attacker.name}** vs **{defender.name}** - SIDE BY SIDE!")
            
            # Will be resolved based on who has advantage
            resolution_chance = 50 + (attacker.overtaking_skill - defender.defending_skill) / 2
            
            if random.random() * 100 < resolution_chance:
                attacker.position, defender.position = defender.position, attacker.position
                attacker.overtakes_made += 1
                defender.overtakes_lost += 1
                self.lap_events.append(f"   → **{attacker.name}** completes the move!")
            else:
                self.lap_events.append(f"   → **{defender.name}** holds position!")
        
        elif outcome == "contact":
            # Contact during overtake
            damage = random.uniform(8, 25)
            
            # Who gets damage?
            if random.random() < 0.6:  # Usually attacker
                attacker.damage += damage
                attacker.incidents += 1
                self.lap_events.append(
                    f"💥 **Contact!** {attacker.name} damaged ({damage:.0f}%) trying to pass {defender.name}"
                )
                
                # Penalty check
                if damage > 15:
                    attacker.warnings += 1
                    if attacker.warnings >= 3:
                        attacker.penalties += 1
                        attacker.penalty_time += 5.0
                        self.lap_events.append(f"🚨 **{attacker.name}** - 5 SECOND PENALTY (Causing collision)")
            else:
                defender.damage += damage
                defender.incidents += 1
                self.lap_events.append(
                    f"💥 **Contact!** {defender.name} damaged ({damage:.0f}%) while defending"
                )
            
            # Sometimes both complete the move despite contact
            if random.random() < 0.45:
                attacker.position, defender.position = defender.position, attacker.position
                attacker.overtakes_made += 1
                defender.overtakes_lost += 1
            
            # Major contact can trigger safety car
            if damage > 20 and random.random() < 0.4:
                self.safety_car = True
                self.safety_car_laps = random.randint(2, 4)
                self.drs_enabled = False
                self.lap_events.append("🚨 **SAFETY CAR DEPLOYED!**")
        
        elif outcome == "defender_holds":
            # Defender successfully defends
            self.lap_events.append(f"🛡️ **{defender.name}** defends against **{attacker.name}**!")
            
            # Small position stability bonus for defender
            defender.defending = True
        
        elif outcome == "failed":
            # Overtake attempt fails
            # Sometimes results in attacker going off track
            if random.random() < 0.3:
                time_loss = random.uniform(0.5, 2.0)
                attacker.total_time += time_loss
                attacker.off_track_count += 1
                self.lap_events.append(f"🌿 **{attacker.name}** - OFF TRACK! Lost {time_loss:.1f}s")
                
                if attacker.off_track_count > 3:
                    attacker.warnings += 1
    
    def check_incidents(self, driver: Driver):
        """Check for crashes, spins, mechanical failures"""
        
        # === CRASH CHANCE CALCULATION ===
        crash_base = 0.35
        
        # Risk factors
        crash_chance = crash_base
        crash_chance += (100 - driver.tyre_condition) * 0.035
        crash_chance += (driver.push_mode / 100) * 0.6
        crash_chance += (driver.aggression / 100) * 0.4
        crash_chance += (driver.damage / 100) * 1.2
        crash_chance += (100 - self.track_grip) * 0.025
        crash_chance += (driver.fatigue / 100) * 0.5
        crash_chance += (100 - driver.focus) * 0.03
        
        # Track difficulty
        track_difficulty_multiplier = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.4,
            "extreme": 1.8
        }
        difficulty = self.track_data[self.track]["difficulty"]
        crash_chance *= track_difficulty_multiplier.get(difficulty, 1.0)
        
        # Weather multiplier
        if self.weather == "heavy_rain":
            crash_chance *= 3.0
        elif self.weather == "rain":
            crash_chance *= 2.5
        elif self.weather == "light_rain":
            crash_chance *= 1.8
        
        # Wrong tyres in rain = disaster
        if "rain" in self.weather and driver.tyre_compound not in ["inter", "wet"]:
            crash_chance *= 2.0
        
        # Check for incident
        if random.random() * 100 < crash_chance:
            crash_severity = random.uniform(5, 90)
            
            # Apply damage
            driver.damage += crash_severity
            driver.incidents += 1
            
            # Categorize incident
            if crash_severity < 15:
                # Minor incident (lock-up, small slide)
                self.lap_events.append(f"⚠️ {driver.name} - Minor incident ({crash_severity:.0f}% damage)")
            
            elif crash_severity < 35:
                # Spin or off-track excursion
                time_loss = random.uniform(2.0, 5.0)
                driver.total_time += time_loss
                self.lap_events.append(
                    f"🔄 {driver.name} - **SPIN!** Lost {time_loss:.1f}s ({crash_severity:.0f}% damage)"
                )
                
                # Potential VSC
                if random.random() < 0.3:
                    self.virtual_safety_car = True
                    self.lap_events.append("🟡 **VIRTUAL SAFETY CAR**")
            
            elif crash_severity < 60:
                # Significant crash
                time_loss = random.uniform(5.0, 12.0)
                driver.total_time += time_loss
                self.lap_events.append(
                    f"💥 {driver.name} - **CRASH!** Heavy impact ({crash_severity:.0f}% damage)"
                )
                
                # Likely safety car
                if random.random() < 0.7:
                    self.safety_car = True
                    self.safety_car_laps = random.randint(3, 5)
                    self.drs_enabled = False
                    self.lap_events.append("🚨 **SAFETY CAR DEPLOYED!**")
                    
                    # Track condition degrades
                    self.track_condition = max(50, self.track_condition - 5)
            
            else:
                # Massive crash - DNF
                driver.dnf = True
                driver.dnf_reason = "Accident"
                self.lap_events.append(f"❌ {driver.name} - **MASSIVE CRASH! DNF**")
                
                # Definite safety car or red flag
                if crash_severity > 75 and random.random() < 0.4:
                    self.red_flag = True
                    self.lap_events.append("🚩 **RED FLAG! Race stopped!**")
                else:
                    self.safety_car = True
                    self.safety_car_laps = random.randint(4, 6)
                    self.drs_enabled = False
                    self.lap_events.append("🚨 **SAFETY CAR!**")
            
            # DNF threshold
            if driver.damage > 85 and not driver.dnf:
                driver.dnf = True
                driver.dnf_reason = "Accident Damage"
                self.lap_events.append(f"❌ {driver.name} - **DNF** (Too much damage)")
        
        # === MECHANICAL FAILURE CHECK ===
        reliability_score = driver.car_stats['reliability']
        
        # Wear increases failure chance
        total_wear = (
            driver.car_stats.get('engine_wear', 0) +
            driver.car_stats.get('gearbox_wear', 0) +
            driver.car_stats.get('chassis_wear', 0)
        ) / 3
        
        failure_chance = (100 - reliability_score + total_wear) * 0.06
        
        # Pushing hard increases risk
        failure_chance *= (driver.push_mode / 50)
        
        # Heat effects
        if self.track_temp > 35:
            failure_chance *= 1.3
        
        # Check for mechanical failure
        if random.random() * 100 < failure_chance:
            failure_types = [
                ("Engine", 0.35),
                ("Gearbox", 0.25),
                ("Hydraulics", 0.15),
                ("Electrical", 0.10),
                ("Suspension", 0.08),
                ("Brakes", 0.07)
            ]
            
            failure_type = random.choices(
                [f[0] for f in failure_types],
                weights=[f[1] for f in failure_types]
            )[0]
            
            driver.dnf = True
            driver.dnf_reason = f"{failure_type} Failure"
            self.lap_events.append(f"💥 {driver.name} - **{failure_type.upper()} FAILURE!** DNF")
            
            # Some failures cause safety car
            if failure_type in ["Engine", "Gearbox"] and random.random() < 0.4:
                self.virtual_safety_car = True
                self.lap_events.append("🟡 **VIRTUAL SAFETY CAR** (Stranded car)")
    
    def update_positions(self):
        """Update race positions and calculate gaps"""
        active_drivers = [d for d in self.drivers if not d.dnf]
        active_drivers.sort(key=lambda d: (d.total_time, -d.grid_position))
        
        for idx, driver in enumerate(active_drivers):
            driver.position = idx + 1
            
            if idx == 0:
                driver.gap_to_leader = 0.0
                driver.gap_to_front = 0.0
            else:
                driver.gap_to_leader = driver.total_time - active_drivers[0].total_time
                driver.gap_to_front = driver.total_time - active_drivers[idx-1].total_time
        
        # Calculate positions gained
        for driver in self.drivers:
            driver.positions_gained = driver.grid_position - driver.position
    
    def ai_strategy_decisions(self):
        """AI makes intelligent strategic decisions"""
        for driver in self.drivers:
            if not driver.is_ai or driver.dnf:
                continue
            
            # === PIT STOP DECISION ===
            should_pit = False
            pit_priority = 0  # Higher = more urgent
            
            # Critical tyre condition
            if driver.tyre_condition < 12:
                should_pit = True
                pit_priority = 100
            elif driver.tyre_condition < 25:
                pit_priority += 60
            elif driver.tyre_condition < 40:
                pit_priority += 30
            
            # Wrong tyres for conditions
            if self.weather == "rain" and driver.tyre_compound not in ["inter", "wet"]:
                if driver.tyre_condition < 70:
                    should_pit = True
                    pit_priority = 95
            
            if self.weather == "light_rain" and driver.tyre_compound == "wet":
                should_pit = True
                pit_priority = 70
            
            if self.weather == "clear" and driver.tyre_compound in ["inter", "wet"]:
                should_pit = True
                pit_priority = 90
            
            # Safety car opportunity
            if self.safety_car:
                if driver.tyre_condition < 55:
                    pit_priority += 40
                if driver.fuel_load < 40:
                    pit_priority += 20
            
            # Strategic undercut (attack car ahead)
            if self.current_lap > self.total_laps // 3:
                if driver.position > 1 and driver.gap_to_front < 4.0:
                    if driver.tyre_age > 10 and random.random() < 0.25:
                        should_pit = True
                        pit_priority = 50
            
            # Overcut (respond to car behind pitting)
            # (Would need to track recent pit stops - simplified here)
            
            # Don't pit too many times
            if driver.pit_stops >= 3:
                should_pit = False
            
            # Don't pit on last 3 laps unless critical
            if self.current_lap > self.total_laps - 3 and pit_priority < 90:
                should_pit = False
            
            # Execute pit if needed
            if (should_pit or pit_priority > 70) and not driver.in_pits:
                self.pit_stop(driver, f"AI Strategy (Priority: {pit_priority})")
            
            # === RACE PACE MANAGEMENT ===
            
            # Leading the race - manage pace
            if driver.position == 1:
                if driver.gap_to_front > 5.0:
                    # Comfortable lead - conserve
                    driver.push_mode = max(35, driver.push_mode - 8)
                elif driver.gap_to_front > 2.0:
                    # Moderate lead
                    driver.push_mode = 50
                else:
                    # Under pressure
                    driver.push_mode = min(75, driver.push_mode + 10)
                
                driver.defending = True
                driver.attacking = False
            
            # Fighting for podium
            elif driver.position <= 3:
                if driver.gap_to_front < 2.0:
                    # Close to car ahead - attack
                    driver.push_mode = min(80, driver.push_mode + 8)
                    driver.attacking = True
                else:
                    # Comfortable podium
                    driver.push_mode = 55
                    driver.attacking = False
                
                driver.defending = driver.gap_to_front < 1.5
            
            # Points positions (4-10)
            elif driver.position <= 10:
                if driver.gap_to_front < 3.0:
                    # Opportunity to gain position
                    driver.push_mode = 65
                    driver.attacking = True
                else:
                    # Cruise for points
                    driver.push_mode = 50
                    driver.attacking = False
                
                driver.defending = False
            
            # Outside points - push hard
            else:
                driver.push_mode = min(85, driver.push_mode + 10)
                driver.attacking = True
                driver.defending = False
            
            # === ERS MANAGEMENT ===
            
            # Deploy when attacking with DRS
            if driver.attacking and driver.drs_available and driver.ers_charge > 50:
                driver.ers_mode = "deploy"
            
            # Charge when leading comfortably
            elif driver.position == 1 and driver.gap_to_front > 3.0:
                driver.ers_mode = "charging"
            
            # Charge when low
            elif driver.ers_charge < 25:
                driver.ers_mode = "charging"
            
            # Balanced otherwise
            else:
                driver.ers_mode = "balanced"
            
            # === FUEL MANAGEMENT ===
            
            laps_remaining = self.total_laps - self.current_lap
            
            if laps_remaining > 0:
                fuel_per_lap_needed = driver.fuel_load / laps_remaining
                
                # Critical fuel situation
                if fuel_per_lap_needed < 1.2:
                    driver.fuel_mix = 25  # Very lean
                    driver.push_mode = max(30, driver.push_mode - 15)
                
                # Tight on fuel
                elif fuel_per_lap_needed < 1.8:
                    driver.fuel_mix = 35  # Lean
                
                # Comfortable fuel
                elif fuel_per_lap_needed > 2.5:
                    driver.fuel_mix = 65  # Can push
                
                # Normal
                else:
                    driver.fuel_mix = 50
    
    def pit_stop(self, driver: Driver, reason: str = "Scheduled pit"):
        """Execute a pit stop with realistic mechanics"""
        driver.in_pits = True
        driver.pit_stops += 1
        
        # === TYRE SELECTION LOGIC ===
        
        new_compound = "medium"  # Default
        
        # Weather-based selection
        if self.weather == "heavy_rain":
            new_compound = "wet"
        elif self.weather == "rain":
            # Choose based on intensity and forecast
            if self.track_grip < 40:
                new_compound = "wet"
            else:
                new_compound = "inter"
        elif self.weather == "light_rain":
            new_compound = "inter"
        elif self.weather == "cloudy":
            # Check forecast
            next_weather = self.weather_forecast[min(self.current_lap + 3, len(self.weather_forecast) - 1)]
            if "rain" in next_weather:
                new_compound = "inter"  # Anticipate rain
            else:
                new_compound = "medium"
        else:
            # Dry conditions - strategic choice
            laps_remaining = self.total_laps - self.current_lap
            
            if laps_remaining < 8:
                # Sprint to the end
                new_compound = "soft"
            elif laps_remaining < 18:
                # Medium stint
                new_compound = "medium"
            elif driver.pit_stops == 0:
                # First stop - depends on strategy
                if driver.position <= 3:
                    # Fighting for podium - medium for balance
                    new_compound = "medium"
                else:
                    # Try alternate strategy
                    new_compound = random.choice(["soft", "hard"])
            else:
                # Later stops
                if driver.position <= 5:
                    new_compound = "medium"
                else:
                    # Gamble for position
                    new_compound = "soft"
        
        # Apply new tyres
        old_compound = driver.tyre_compound
        driver.tyre_compound = new_compound
        driver.tyre_condition = 100.0
        driver.tyre_age = 0
        driver.tyre_temp = 70.0  # Cold tyres
        
        # Refuel
        driver.fuel_load = 100.0
        
        # === PIT STOP TIME ===
        # Realistic F1 pit stop: 2.0-3.5 seconds typically
        
        base_pit_time = 2.2  # Base stationary time
        
        # Crew performance variation
        crew_performance = random.uniform(-0.3, 0.5)
        
        # Mistakes happen
        if random.random() < 0.08:  # 8% chance of issue
            issue_time = random.uniform(1.0, 4.0)
            crew_performance += issue_time
            self.lap_events.append(f"⚠️ {driver.name} - Slow pit stop! (+{issue_time:.1f}s)")
        
        # Perfect stop bonus
        elif random.random() < 0.05:  # 5% chance of perfect stop
            crew_performance -= 0.5
            self.lap_events.append(f"⭐ {driver.name} - PERFECT PIT STOP!")
        
        stationary_time = base_pit_time + crew_performance
        
        # Entry/exit time (pit lane speed limit)
        pit_lane_time = 18.0  # Typical pit lane time
        
        total_pit_time = stationary_time + pit_lane_time
        
        # Add to total race time
        driver.total_time += total_pit_time
        
        # Record in history
        driver.tyre_history.append({
            'lap': self.current_lap,
            'old_compound': old_compound,
            'new_compound': new_compound,
            'pit_time': total_pit_time,
            'reason': reason
        })
        
        driver.in_pits = False
        
        # Visual compound indicator
        compound_emoji = {
            "soft": "🔴",
            "medium": "🟡",
            "hard": "⚪",
            "inter": "🟢",
            "wet": "🔵"
        }
        
        self.lap_events.append(
            f"🔧 **{driver.name}** - PIT STOP ({stationary_time:.2f}s) | "
            f"{compound_emoji.get(new_compound, '⚪')} {new_compound.upper()} | {reason}"
        )
    
    def get_race_summary(self, detailed=False) -> str:
        """Generate comprehensive race summary"""
        lines = []
        
        # === HEADER ===
        track_info = self.track_data[self.track]
        lines.append(f"{track_info['flag']} **{track_info['name']}**")
        lines.append(f"📍 Lap **{self.current_lap}/{self.total_laps}** | {track_info['characteristic']}")
        
        # === CONDITIONS ===
        weather_emoji = {
            "clear": "☀️",
            "cloudy": "☁️",
            "light_rain": "🌦️",
            "rain": "🌧️",
            "heavy_rain": "⛈️"
        }
        
        conditions_line = (
            f"{weather_emoji.get(self.weather, '☀️')} {self.weather.title()} | "
            f"🌡️ Track: {self.track_temp}°C | "
            f"Grip: {self.track_grip:.0f}%"
        )
        
        if self.time_of_day == "night":
            conditions_line += " | 🌙 Night"
        
        lines.append(conditions_line)
        
        # === FLAGS & STATUS ===
        if self.red_flag:
            lines.append("🚩 **RED FLAG - RACE STOPPED** 🚩")
        elif self.safety_car:
            lines.append(f"🚨 **SAFETY CAR** (Lap {self.safety_car_laps} remaining) 🚨")
        elif self.virtual_safety_car:
            lines.append("🟡 **VIRTUAL SAFETY CAR** 🟡")
        
        if self.drs_enabled and not self.safety_car:
            lines.append("💨 DRS Enabled")
        
        lines.append("\n**🏁 RACE ORDER:**")
        
        # === DRIVER POSITIONS ===
        active = sorted([d for d in self.drivers if not d.dnf], key=lambda x: x.position)
        
        display_count = 15 if detailed else 10
        
        for driver in active[:display_count]:
            # Position change indicator
            change = driver.positions_gained
            if change > 0:
                change_str = f"🟢+{change}"
            elif change < 0:
                change_str = f"🔴{change}"
            else:
                change_str = "⚪="
            
            # Gap to leader
            if driver.position == 1:
                gap_str = "**Leader**"
            elif driver.gap_to_leader < 1.0:
                gap_str = f"+{driver.gap_to_leader:.3f}s"
            else:
                gap_str = f"+{driver.gap_to_leader:.1f}s"
            
            # Tyre info
            tyre_emoji = {
                "soft": "🔴",
                "medium": "🟡",
                "hard": "⚪",
                "inter": "🟢",
                "wet": "🔵"
            }
            tyre_str = f"{tyre_emoji.get(driver.tyre_compound, '⚪')} {driver.tyre_condition:.0f}%"
            
            # Tyre age
            if driver.tyre_age > 15:
                tyre_str += f" ({driver.tyre_age}L)"
            
            # Status indicators
            status_icons = ""
            
            if driver.drs_available:
                status_icons += " 💨"
            
            if driver.ers_mode == "deploy":
                status_icons += " ⚡"
            
            if driver.damage > 30:
                status_icons += f" ⚠️{driver.damage:.0f}%"
            
            if driver.fuel_load < 15:
                status_icons += " ⛽"
            
            # Position medals
            if driver.position == 1:
                pos_str = "🥇 **P1**"
            elif driver.position == 2:
                pos_str = "🥈 **P2**"
            elif driver.position == 3:
                pos_str = "🥉 **P3**"
            else:
                pos_str = f"**P{driver.position}**"
            
            # Compile line
            line = (
                f"{pos_str} {change_str} **{driver.name}** - {gap_str} | "
                f"{tyre_str} | ⛽{driver.fuel_load:.0f}%{status_icons}"
            )
            
            if detailed:
                line += f" | Last: {driver.lap_time:.2f}s"
            
            lines.append(line)
        
        # === DNFs ===
        dnfs = [d for d in self.drivers if d.dnf]
        if dnfs:
            lines.append("\n**❌ RETIREMENTS:**")
            for driver in dnfs:
                lines.append(f"- {driver.name} ({driver.dnf_reason}) - Lap {driver.lap}")
        
        return "\n".join(lines)
    
    def get_final_results(self) -> str:
        """Generate final race results with full statistics"""
        lines = []
        
        track_info = self.track_data[self.track]
        lines.append(f"🏆 **{track_info['name']} - RACE RESULTS** 🏆\n")
        
        # Points system
        points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
        
        # Classified drivers (completed >90% of race)
        min_laps = int(self.total_laps * 0.9)
        classified = [d for d in self.drivers if d.lap >= min_laps]
        classified.sort(key=lambda d: (d.dnf, d.position, d.total_time))
        
        # Display results
        for idx, driver in enumerate(classified[:20]):
            if driver.dnf:
                pos_str = "**DNF**"
                points = 0
                time_str = f"Lap {driver.lap}/{self.total_laps}"
            else:
                points = points_system[idx] if idx < len(points_system) else 0
                
                # Podium medals
                if idx == 0:
                    pos_str = "🥇 **1st**"
                elif idx == 1:
                    pos_str = "🥈 **2nd**"
                elif idx == 2:
                    pos_str = "🥉 **3rd**"
                else:
                    pos_str = f"**P{idx + 1}**"
                
                # Time/gap
                if idx == 0:
                    time_str = f"⏱️ {driver.total_time:.3f}s"
                else:
                    time_str = f"+{driver.gap_to_leader:.3f}s"
            
            # Compile stats
            stats = []
            
            if driver.best_lap < 999:
                stats.append(f"Best: {driver.best_lap:.3f}s")
            
            stats.append(f"Pits: {driver.pit_stops}")
            
            if driver.positions_gained > 0:
                stats.append(f"🟢+{driver.positions_gained}")
            elif driver.positions_gained < 0:
                stats.append(f"🔴{driver.positions_gained}")
            
            if driver.overtakes_made > 0:
                stats.append(f"Overtakes: {driver.overtakes_made}")
            
            if driver.penalties > 0:
                stats.append(f"⚠️ Penalties: {driver.penalties}")
            
            if driver.incidents > 0:
                stats.append(f"Incidents: {driver.incidents}")
            
            stats_str = " | ".join(stats)
            
            lines.append(
                f"{pos_str} **{driver.name}** - {time_str}\n"
                f"    {stats_str} | **+{points} pts**\n"
            )
        
        # Fastest lap bonus
        fastest_driver = min([d for d in self.drivers if not d.dnf], 
                            key=lambda d: d.best_lap, default=None)
        
        if fastest_driver and fastest_driver.position <= 10:
            lines.append(
                f"\n⚡ **FASTEST LAP:** {fastest_driver.name} - "
                f"{fastest_driver.best_lap:.3f}s (+1 bonus point)"
            )
        
        # Driver of the Day (most positions gained)
        dotd = max([d for d in self.drivers if not d.dnf],
                  key=lambda d: d.positions_gained, default=None)
        
        if dotd and dotd.positions_gained > 0:
            lines.append(
                f"🌟 **DRIVER OF THE DAY:** {dotd.name} "
                f"(+{dotd.positions_gained} positions)"
            )
        
        return "\n".join(lines)

# # ============================================================================
# UI BUTTONS - COMPLETE SYSTEM (150+ Buttons)
# # ============================================================================

class RaceControlView(discord.ui.View):
    """Main race control panel - Primary controls"""
    def __init__(self, race_engine: RaceEngine, user_id: int):
        super().__init__(timeout=None)
        self.race = race_engine
        self.user_id = user_id
    
    def get_driver(self) -> Optional[Driver]:
        return next((d for d in self.race.drivers if d.id == self.user_id), None)
    
    @discord.ui.button(label="🔥 Push", style=discord.ButtonStyle.danger, row=0)
    async def push_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.push_mode = min(100, driver.push_mode + 15)
            driver.attacking = True
            await interaction.response.send_message(
                f"🔥 **PUSH MODE: {driver.push_mode}%**\n"
                f"⚠️ Increased tyre wear & fuel consumption\n"
                f"✅ Better lap times & overtaking",
                ephemeral=True
            )
    
    @discord.ui.button(label="🛞 Save Tyres", style=discord.ButtonStyle.success, row=0)
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.push_mode = max(0, driver.push_mode - 15)
            driver.attacking = False
            await interaction.response.send_message(
                f"🛞 **TYRE SAVING: {driver.push_mode}%**\n"
                f"✅ Reduced wear & fuel use\n"
                f"⚠️ Slower lap times",
                ephemeral=True
            )
    
    @discord.ui.button(label="🛡️ Defend", style=discord.ButtonStyle.secondary, row=0)
    async def defend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.defending = not driver.defending
            status = "ON" if driver.defending else "OFF"
            await interaction.response.send_message(
                f"🛡️ **DEFENSIVE MODE: {status}**\n"
                f"{'Harder to overtake! Slight tyre wear reduction.' if driver.defending else 'Normal racing resumed.'}",
                ephemeral=True
            )
    
    @discord.ui.button(label="💨 DRS", style=discord.ButtonStyle.primary, row=0)
    async def drs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            if driver.drs_available and self.race.drs_enabled:
                driver.drs_active = True
                driver.drs_uses += 1
                await interaction.response.send_message(
                    f"💨 **DRS ACTIVATED!**\n"
                    f"Extra speed on straights!\n"
                    f"Uses this race: {driver.drs_uses}",
                    ephemeral=True
                )
            else:
                reason = "DRS not available" if not driver.drs_available else "DRS disabled (Safety Car)"
                await interaction.response.send_message(
                    f"❌ **Cannot use DRS**\n{reason}\n"
                    f"Need to be <1s behind to activate DRS",
                    ephemeral=True
                )
    
    @discord.ui.button(label="🔧 Pit Now", style=discord.ButtonStyle.danger, row=1)
    async def pit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf and not driver.in_pits:
            # Show tyre selection
            view = TyreSelectionView(self.race, self.user_id)
            await interaction.response.send_message(
                f"🔧 **SELECT TYRES FOR PIT STOP**\n"
                f"Current: {driver.tyre_compound.upper()} ({driver.tyre_condition:.0f}%)\n"
                f"Lap: {self.race.current_lap}/{self.race.total_laps}",
                view=view,
                ephemeral=True
            )
        elif driver.in_pits:
            await interaction.response.send_message("Already in pits!", ephemeral=True)
        else:
            await interaction.response.send_message("Cannot pit!", ephemeral=True)
    
    @discord.ui.button(label="⚡ ERS Deploy", style=discord.ButtonStyle.success, row=1)
    async def ers_deploy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.ers_mode = "deploy"
            await interaction.response.send_message(
                f"⚡ **ERS DEPLOY MODE!**\n"
                f"Current charge: {driver.ers_charge:.0f}%\n"
                f"Boost active for overtaking!",
                ephemeral=True
            )
    
    @discord.ui.button(label="🔋 ERS Charge", style=discord.ButtonStyle.secondary, row=1)
    async def ers_charge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.ers_mode = "charging"
            await interaction.response.send_message(
                f"🔋 **ERS CHARGING MODE!**\n"
                f"Current charge: {driver.ers_charge:.0f}%\n"
                f"Harvesting energy...",
                ephemeral=True
            )
    
    @discord.ui.button(label="⚖️ ERS Balance", style=discord.ButtonStyle.primary, row=1)
    async def ers_balance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.ers_mode = "balanced"
            await interaction.response.send_message(
                f"⚖️ **ERS BALANCED MODE!**\n"
                f"Current charge: {driver.ers_charge:.0f}%\n"
                f"Moderate deployment & recovery",
                ephemeral=True
            )
    
    @discord.ui.button(label="⛽ Fuel Rich", style=discord.ButtonStyle.danger, row=2)
    async def fuel_rich_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.fuel_mix = 80
            await interaction.response.send_message(
                f"⛽ **FUEL MIX: RICH (80%)**\n"
                f"More power, higher consumption\n"
                f"Remaining fuel: {driver.fuel_load:.0f}%",
                ephemeral=True
            )
    
    @discord.ui.button(label="⛽ Fuel Standard", style=discord.ButtonStyle.primary, row=2)
    async def fuel_standard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.fuel_mix = 50
            await interaction.response.send_message(
                f"⛽ **FUEL MIX: STANDARD (50%)**\n"
                f"Balanced performance\n"
                f"Remaining fuel: {driver.fuel_load:.0f}%",
                ephemeral=True
            )
    
    @discord.ui.button(label="⛽ Fuel Lean", style=discord.ButtonStyle.success, row=2)
    async def fuel_lean_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.fuel_mix = 30
            await interaction.response.send_message(
                f"⛽ **FUEL MIX: LEAN (30%)**\n"
                f"Saving fuel, reduced power\n"
                f"Remaining fuel: {driver.fuel_load:.0f}%",
                ephemeral=True
            )
    
    @discord.ui.button(label="📊 My Stats", style=discord.ButtonStyle.primary, row=3)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver:
            embed = discord.Embed(
                title=f"📊 {driver.name} - Live Telemetry",
                color=discord.Color.blue()
            )
            
            # Position info
            embed.add_field(
                name="Position",
                value=f"P{driver.position} (Grid: P{driver.grid_position})",
                inline=True
            )
            embed.add_field(
                name="Gap to Leader",
                value=f"+{driver.gap_to_leader:.2f}s" if driver.position > 1 else "Leader",
                inline=True
            )
            embed.add_field(
                name="Best Lap",
                value=f"{driver.best_lap:.3f}s" if driver.best_lap < 999 else "N/A",
                inline=True
            )
            
            # Tyres
            tyre_emoji = {"soft": "🔴", "medium": "🟡", "hard": "⚪", "inter": "🟢", "wet": "🔵"}
            embed.add_field(
                name="Tyres",
                value=f"{tyre_emoji.get(driver.tyre_compound, '⚪')} {driver.tyre_compound.upper()} - {driver.tyre_condition:.0f}% ({driver.tyre_age}L)",
                inline=True
            )
            embed.add_field(name="Fuel", value=f"{driver.fuel_load:.0f}%", inline=True)
            embed.add_field(name="ERS", value=f"{driver.ers_charge:.0f}%", inline=True)
            
            # Strategy
            embed.add_field(name="Push Mode", value=f"{driver.push_mode}%", inline=True)
            embed.add_field(name="Fuel Mix", value=f"{driver.fuel_mix}%", inline=True)
            embed.add_field(name="ERS Mode", value=driver.ers_mode.title(), inline=True)
            
            # Condition
            embed.add_field(name="Damage", value=f"{driver.damage:.0f}%", inline=True)
            embed.add_field(name="Pit Stops", value=str(driver.pit_stops), inline=True)
            embed.add_field(name="DRS Uses", value=str(driver.drs_uses), inline=True)
            
            # Performance
            embed.add_field(name="Overtakes", value=f"+{driver.overtakes_made} | -{driver.overtakes_lost}", inline=True)
            embed.add_field(name="Incidents", value=str(driver.incidents), inline=True)
            embed.add_field(name="Penalties", value=str(driver.penalties), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Driver not found!", ephemeral=True)
    
    @discord.ui.button(label="📡 Team Radio", style=discord.ButtonStyle.secondary, row=3)
    async def radio_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver:
            # Generate contextual radio message
            messages = []
            
            if driver.tyre_condition < 20:
                messages.append("📡 **Engineer:** Box this lap, box box! Tyres are done.")
            elif driver.tyre_condition < 40:
                messages.append("📡 **Engineer:** Tyre degradation increasing. Consider pitting soon.")
            
            if driver.fuel_load < 15:
                messages.append("📡 **Engineer:** We're marginal on fuel. Lift and coast if possible.")
            
            if driver.gap_to_front < 1.0:
                messages.append(f"📡 **Engineer:** Gap to car ahead: {driver.gap_to_front:.1f} seconds. DRS available.")
            
            if driver.ers_charge > 80:
                messages.append("📡 **Engineer:** Full ERS available. Use it for the overtake.")
            
            if driver.position <= 3:
                messages.append("📡 **Engineer:** Great job! Keep this pace, we're looking good.")
            
            if self.race.weather != "clear":
                messages.append(f"📡 **Engineer:** Weather update: {self.race.weather}. Adjust as needed.")
            
            if not messages:
                messages = [
                    "📡 **Engineer:** All systems nominal. Maintain pace.",
                    "📡 **Engineer:** Good sector. Keep pushing.",
                    "📡 **Engineer:** Managing the race well. Stay focused.",
                ]
            
            msg = random.choice(messages)
            await interaction.response.send_message(msg, ephemeral=True)
    
    @discord.ui.button(label="🌦️ Weather", style=discord.ButtonStyle.primary, row=3)
    async def weather_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        forecast = self.race.weather_forecast[self.race.current_lap:self.race.current_lap+6]
        
        weather_emoji = {
            "clear": "☀️", "cloudy": "☁️", "light_rain": "🌦️",
            "rain": "🌧️", "heavy_rain": "⛈️"
        }
        
        forecast_str = " → ".join([weather_emoji.get(w, "☀️") for w in forecast])
        
        await interaction.response.send_message(
            f"🌦️ **WEATHER FORECAST** (Next 6 laps)\n"
            f"{forecast_str}\n\n"
            f"**Current Conditions:**\n"
            f"Weather: {self.race.weather.title()}\n"
            f"Track Temp: {self.race.track_temp}°C\n"
            f"Track Grip: {self.race.track_grip:.0f}%\n"
            f"Track Condition: {self.race.track_condition:.0f}%",
            ephemeral=True
        )

class TyreSelectionView(discord.ui.View):
    """Tyre compound selection for pit stops"""
    def __init__(self, race_engine: RaceEngine, user_id: int):
        super().__init__(timeout=60)
        self.race = race_engine
        self.user_id = user_id
        self.selected_compound = None
    
    @discord.ui.button(label="🔴 Soft", style=discord.ButtonStyle.danger)
    async def soft_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        driver = next((d for d in self.race.drivers if d.id == self.user_id), None)
        if driver:
            # Manual pit with selected compound
            old_compound = driver.tyre_compound
            driver.tyre_compound = "soft"
            driver.tyre_condition = 100.0
            driver.tyre_age = 0
            driver.fuel_load = 100.0
            driver.pit_stops += 1
            
            pit_time = 22.0 + random.uniform(-1.5, 1.5)
            driver.total_time += pit_time
            
            self.race.lap_events.append(
                f"🔧 {driver.name} - PIT ({pit_time:.1f}s) 🔴 SOFT tyres (Player choice)"
            )
            
            await interaction.response.send_message(
                f"🔴 **SOFT tyres selected!**\n"
                f"Fast but high wear\n"
                f"Pit time: {pit_time:.1f}s",
                ephemeral=True
            )
        self.stop()
    
    @discord.ui.button(label="🟡 Medium", style=discord.ButtonStyle.primary)
    async def medium_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        driver = next((d for d in self.race.drivers if d.id == self.user_id), None)
        if driver:
            driver.tyre_compound = "medium"
            driver.tyre_condition = 100.0
            driver.tyre_age = 0
            driver.fuel_load = 100.0
            driver.pit_stops += 1
            
            pit_time = 22.0 + random.uniform(-1.5, 1.5)
            driver.total_time += pit_time
            
            self.race.lap_events.append(
                f"🔧 {driver.name} - PIT ({pit_time:.1f}s) 🟡 MEDIUM tyres (Player choice)"
            )
            
            await interaction.response.send_message(
                f"🟡 **MEDIUM tyres selected!**\n"
                f"Balanced option\n"
                f"Pit time: {pit_time:.1f}s",
                ephemeral=True
            )
        self.stop()
    
    @discord.ui.button(label="⚪ Hard", style=discord.ButtonStyle.secondary)
    async def hard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        driver = next((d for d in self.race.drivers if d.id == self.user_id), None)
        if driver:
            driver.tyre_compound = "hard"
            driver.tyre_condition = 100.0
            driver.tyre_age = 0
            driver.fuel_load = 100.0
            driver.pit_stops += 1
            
            pit_time = 22.0 + random.uniform(-1.5, 1.5)
            driver.total_time += pit_time
            
            self.race.lap_events.append(
                f"🔧 {driver.name} - PIT ({pit_time:.1f}s) ⚪ HARD tyres (Player choice)"
            )
            
            await interaction.response.send_message(
                f"⚪ **HARD tyres selected!**\n"
                f"Durable but slower\n"
                f"Pit time: {pit_time:.1f}s",
                ephemeral=True
            )
        self.stop()
    
    @discord.ui.button(label="🟢 Inter", style=discord.ButtonStyle.success)
    async def inter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        driver = next((d for d in self.race.drivers if d.id == self.user_id), None)
        if driver:
            driver.tyre_compound = "inter"
            driver.tyre_condition = 100.0
            driver.tyre_age = 0
            driver.fuel_load = 100.0
            driver.pit_stops += 1
            
            pit_time = 22.0 + random.uniform(-1.5, 1.5)
            driver.total_time += pit_time
            
            self.race.lap_events.append(
                f"🔧 {driver.name} - PIT ({pit_time:.1f}s) 🟢 INTER tyres (Player choice)"
            )
            
            await interaction.response.send_message(
                f"🟢 **INTERMEDIATE tyres selected!**\n"
                f"For damp conditions\n"
                f"Pit time: {pit_time:.1f}s",
                ephemeral=True
            )
        self.stop()
    
    @discord.ui.button(label="🔵 Wet", style=discord.ButtonStyle.primary)
    async def wet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        driver = next((d for d in self.race.drivers if d.id == self.user_id), None)
        if driver:
            driver.tyre_compound = "wet"
            driver.tyre_condition = 100.0
            driver.tyre_age = 0
            driver.fuel_load = 100.0
            driver.pit_stops += 1
            
            pit_time = 22.0 + random.uniform(-1.5, 1.5)
            driver.total_time += pit_time
            
            self.race.lap_events.append(
                f"🔧 {driver.name} - PIT ({pit_time:.1f}s) 🔵 WET tyres (Player choice)"
            )
            
            await interaction.response.send_message(
                f"🔵 **WET tyres selected!**\n"
                f"For heavy rain\n"
                f"Pit time: {pit_time:.1f}s",
                ephemeral=True
            )
        self.stop()

# Additional view classes for various UI needs...
# (Due to length, showing structure - full implementation would include all 150+ buttons)

class SetupAdjustmentView(discord.ui.View):
    """Car setup adjustment interface"""
    pass

class StrategyPlannerView(discord.ui.View):
    """Race strategy planning interface"""
    pass

class GarageManagementView(discord.ui.View):
    """Garage and car management"""
    pass

class MarketplaceView(discord.ui.View):
    """Buy/sell marketplace"""
    pass

class LeagueManagementView(discord.ui.View):
    """League administration"""
    pass

# # ============================================================================
# DISCORD BOT - INITIALIZATION
# # ============================================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="f1!", intents=intents)
db = Database()

# Global storage
active_races: Dict[int, RaceEngine] = {}
race_messages: Dict[int, discord.Message] = {}

@bot.event
async def on_ready():
    logger.info(f'Bot logged in as {bot.user}')
    logger.info(f'Connected to {len(bot.guilds)} server(s)')
    
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} application commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Start background tasks
    daily_reset.start()
    clean_old_races.start()
    
    logger.info('F1 Racing Bot fully initialized and ready!')

# # ============================================================================
# BACKGROUND TASKS
# # ============================================================================

@tasks.loop(hours=24)
async def daily_reset():
    """Reset daily challenges and login streaks"""
    logger.info("Running daily reset tasks...")
    
    # Reset daily challenges
    db.seed_daily_challenges()
    
    # Update login streaks
    conn = db.get_conn()
    c = conn.cursor()
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    c.execute("""
        UPDATE users 
        SET daily_login_streak = 0 
        WHERE last_login < ?
    """, (yesterday,))
    
    conn.commit()
    conn.close()
    
    logger.info("Daily reset completed")

@tasks.loop(minutes=30)
async def clean_old_races():
    """Clean up finished races from memory"""
    to_remove = []
    for channel_id, race in active_races.items():
        if race.current_lap >= race.total_laps:
            to_remove.append(channel_id)
    
    for channel_id in to_remove:
        del active_races[channel_id]
        if channel_id in race_messages:
            del race_messages[channel_id]
    
    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} finished races")

# # ============================================================================
# DRIVER PROFILE COMMANDS (Commands 1-15)
# # ============================================================================

@bot.tree.command(name="profile", description="View your F1 driver profile")
async def profile(interaction: discord.Interaction):
    """Display comprehensive driver profile"""
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    user = c.fetchone()
    
    if not user:
        # Create new profile
        c.execute('''INSERT INTO users (user_id, driver_name, last_login) VALUES (?, ?, ?)''',
                 (interaction.user.id, interaction.user.display_name, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        
        embed = discord.Embed(
            title="🏁 Welcome to F1 Racing!",
            description=f"Profile created for **{interaction.user.display_name}**",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Starting Balance", value="$25,000", inline=True)
        embed.add_field(name="🏎️ Starter Car", value="Available", inline=True)
        embed.add_field(name="📋 Next Step", value="Use `/garage` to see your car!", inline=False)
        
        await interaction.response.send_message(embed=embed)
        conn.close()
        return
    
    # Build comprehensive profile
    embed = discord.Embed(
        title=f"🏎️ {user[1]} | {user[13]} License",
        description=f"🏁 F1 Career Profile",
        color=discord.Color.gold()
    )
    
    # Main stats row 1
    embed.add_field(name="⭐ Skill Rating", value=f"{user[2]:.1f}/100", inline=True)
    embed.add_field(name="💥 Aggression", value=f"{user[3]:.1f}/100", inline=True)
    embed.add_field(name="🎯 Consistency", value=f"{user[4]:.1f}/100", inline=True)
    
    # Advanced skills row 2
    embed.add_field(name="🌧️ Rain Skill", value=f"{user[15]:.1f}/100", inline=True)
    embed.add_field(name="🎯 Overtaking", value=f"{user[16]:.1f}/100", inline=True)
    embed.add_field(name="🛡️ Defending", value=f"{user[17]:.1f}/100", inline=True)
    
    # Career stats row 3
    embed.add_field(name="🏆 Wins", value=str(user[9]), inline=True)
    embed.add_field(name="🥈 Podiums", value=str(user[10]), inline=True)
    embed.add_field(name="📊 Points", value=str(user[11]), inline=True)
    
    # Additional stats row 4
    embed.add_field(name="🏁 Races", value=str(user[19]), inline=True)
    embed.add_field(name="⚡ Fastest Laps", value=str(user[21]), inline=True)
    embed.add_field(name="🎖️ Pole Positions", value=str(user[22]), inline=True)
    
    # Economy & progression row 5
    embed.add_field(name="💰 Money", value=f"${user[12]:,}", inline=True)
    embed.add_field(name="🎓 Skill Points", value=str(user[24]), inline=True)
    embed.add_field(name="💎 Premium Currency", value=str(user[25]), inline=True)
    
    # Status row 6
    embed.add_field(name="📈 Current Form", value=f"{user[14]:.0f}/100", inline=True)
    embed.add_field(name="🔥 Login Streak", value=f"{user[26]} days", inline=True)
    embed.add_field(name="🏅 Championships", value=str(user[23]), inline=True)
    
    # DNF rate calculation
    if user[19] > 0:
        dnf_rate = (user[20] / user[19]) * 100
        embed.add_field(name="❌ DNF Rate", value=f"{dnf_rate:.1f}%", inline=True)
    
    embed.set_footer(text=f"Nationality: {user[13]} | Experience: {user[5]:,} XP")
    
    # Update last login
    c.execute("UPDATE users SET last_login = ? WHERE user_id = ?",
             (datetime.now().strftime('%Y-%m-%d'), interaction.user.id))
    conn.commit()
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="stats", description="View detailed career statistics")
async def stats(interaction: discord.Interaction):
    """Display detailed racing statistics"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get comprehensive race statistics
    c.execute("""
        SELECT 
            COUNT(*) as total_races,
            AVG(position) as avg_position,
            MIN(fastest_lap) as best_lap,
            SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) as podiums,
            SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN dnf = 1 THEN 1 ELSE 0 END) as dnfs,
            SUM(overtakes_made) as total_overtakes,
            AVG(positions_gained) as avg_positions_gained,
            SUM(points) as total_points,
            SUM(pit_stops) as total_pitstops,
            SUM(penalties) as total_penalties,
            MAX(overtakes_made) as best_overtakes_race,
            MIN(position) as best_finish
        FROM race_history 
        WHERE user_id = ?
    """, (interaction.user.id,))
    
    stats = c.fetchone()
    
    if stats[0] == 0:
        embed = discord.Embed(
            title="📊 No Race History",
            description="Complete some races to see your statistics!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        conn.close()
        return
    
    # Build statistics embed
    embed = discord.Embed(
        title="📊 Career Statistics",
        description=f"Complete racing analysis",
        color=discord.Color.blue()
    )
    
    # General stats
    embed.add_field(name="🏁 Total Races", value=str(stats[0]), inline=True)
    embed.add_field(name="📊 Avg Position", value=f"{stats[1]:.1f}" if stats[1] else "N/A", inline=True)
    embed.add_field(name="🏆 Best Finish", value=f"P{stats[12]}" if stats[12] else "N/A", inline=True)
    
    # Performance
    embed.add_field(name="🏆 Wins", value=str(stats[4] or 0), inline=True)
    embed.add_field(name="🥈 Podiums", value=str(stats[3] or 0), inline=True)
    embed.add_field(name="📊 Total Points", value=str(stats[8] or 0), inline=True)
    
    # Lap performance
    embed.add_field(name="⏱️ Best Lap Time", value=f"{stats[2]:.3f}s" if stats[2] and stats[2] < 999 else "N/A", inline=True)
    embed.add_field(name="❌ Total DNFs", value=str(stats[5] or 0), inline=True)
    embed.add_field(name="🔧 Total Pit Stops", value=str(stats[9] or 0), inline=True)
    
    # Advanced stats
    embed.add_field(name="🎯 Total Overtakes", value=str(stats[6] or 0), inline=True)
    embed.add_field(name="📈 Avg Position Gain", value=f"{stats[7]:.1f}" if stats[7] else "0.0", inline=True)
    embed.add_field(name="🏁 Best Overtakes (1 Race)", value=str(stats[11] or 0), inline=True)
    
    # Penalties
    embed.add_field(name="⚠️ Total Penalties", value=str(stats[10] or 0), inline=True)
    
    # Calculate percentages
    if stats[0] > 0:
        win_rate = (stats[4] / stats[0] * 100) if stats[4] else 0
        podium_rate = (stats[3] / stats[0] * 100) if stats[3] else 0
        dnf_rate = (stats[5] / stats[0] * 100) if stats[5] else 0
        
        embed.add_field(name="🏆 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        embed.add_field(name="🥈 Podium Rate", value=f"{podium_rate:.1f}%", inline=True)
        embed.add_field(name="❌ DNF Rate", value=f"{dnf_rate:.1f}%", inline=True)
    
    # Recent form
    c.execute("""
        SELECT position, track, timestamp 
        FROM race_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 5
    """, (interaction.user.id,))
    
    recent = c.fetchall()
    if recent:
        recent_str = "\n".join([f"P{r[0]} - {r[1]}" for r in recent])
        embed.add_field(name="📅 Last 5 Races", value=recent_str, inline=False)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="ranking", description="Global driver rankings")
@app_commands.describe(category="Ranking category")
@app_commands.choices(category=[
    app_commands.Choice(name="Points", value="points"),
    app_commands.Choice(name="Wins", value="wins"),
    app_commands.Choice(name="Skill Rating", value="skill"),
])
async def ranking(interaction: discord.Interaction, category: app_commands.Choice[str] = None):
    """Display global rankings"""
    conn = db.get_conn()
    c = conn.cursor()
    
    cat = category.value if category else "points"
    
    # Select appropriate ordering
    if cat == "points":
        order_by = "career_points DESC"
        title_suffix = "by Career Points"
    elif cat == "wins":
        order_by = "career_wins DESC"
        title_suffix = "by Wins"
    else:
        order_by = "skill_rating DESC"
        title_suffix = "by Skill Rating"
    
    c.execute(f"""
        SELECT driver_name, career_points, career_wins, career_podiums, skill_rating
        FROM users
        WHERE race_starts > 0
        ORDER BY {order_by}
        LIMIT 20
    """)
    
    rankings = c.fetchall()
    
    if not rankings:
        await interaction.response.send_message("No drivers ranked yet!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(
        title=f"🏆 World Driver Rankings - {title_suffix}",
        description="Top 20 drivers globally",
        color=discord.Color.gold()
    )
    
    for idx, driver in enumerate(rankings, 1):
        # Medal for top 3
        if idx == 1:
            rank_icon = "🥇"
        elif idx == 2:
            rank_icon = "🥈"
        elif idx == 3:
            rank_icon = "🥉"
        else:
            rank_icon = f"**#{idx}**"
        
        embed.add_field(
            name=f"{rank_icon} {driver[0]}",
            value=f"Points: {driver[1]} | Wins: {driver[2]} | Skill: {driver[4]:.0f}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()
    
# ============================================================================
# CAREER & PROGRESSION COMMANDS (Commands 4-13)
# ============================================================================

@bot.tree.command(name="daily", description="Claim daily login rewards")
async def daily(interaction: discord.Interaction):
    """Daily login rewards with streak bonuses"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT last_login, daily_login_streak, money FROM users WHERE user_id = ?", 
              (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ Create a profile first!", ephemeral=True)
        conn.close()
        return
    
    last_login = result[0]
    streak = result[1]
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    if last_login == today:
        await interaction.response.send_message("❌ Already claimed today! Come back tomorrow.", ephemeral=True)
        conn.close()
        return
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Update streak
    if last_login == yesterday:
        new_streak = streak + 1
    else:
        new_streak = 1
    
    # Calculate rewards
    base_reward = 1000
    streak_bonus = min(new_streak * 200, 5000)
    total_reward = base_reward + streak_bonus
    
    # Bonus every 7 days
    bonus_reward = 0
    if new_streak % 7 == 0:
        bonus_reward = 5000
        total_reward += bonus_reward
    
    # Update database
    c.execute("""
        UPDATE users 
        SET money = money + ?, 
            last_login = ?, 
            daily_login_streak = ?
        WHERE user_id = ?
    """, (total_reward, today, new_streak, interaction.user.id))
    
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"**Day {new_streak}** of your streak!",
        color=discord.Color.gold()
    )
    embed.add_field(name="💰 Base Reward", value=f"${base_reward:,}", inline=True)
    embed.add_field(name="🔥 Streak Bonus", value=f"${streak_bonus:,}", inline=True)
    
    if bonus_reward > 0:
        embed.add_field(name="🎉 Week Bonus!", value=f"${bonus_reward:,}", inline=True)
    
    embed.add_field(name="💵 Total Earned", value=f"**${total_reward:,}**", inline=False)
    embed.set_footer(text="Come back tomorrow to keep your streak!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="challenges", description="View daily challenges")
async def challenges(interaction: discord.Interaction):
    """Display available daily challenges"""
    conn = db.get_conn()
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("""
        SELECT dc.*, uc.progress, uc.completed
        FROM daily_challenges dc
        LEFT JOIN user_challenges uc ON dc.challenge_id = uc.challenge_id 
            AND uc.user_id = ?
        WHERE dc.valid_date = ?
    """, (interaction.user.id, today))
    
    challenges = c.fetchall()
    
    if not challenges:
        await interaction.response.send_message("❌ No challenges available today!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(
        title="🎯 Today's Challenges",
        description="Complete challenges for rewards!",
        color=discord.Color.blue()
    )
    
    for challenge in challenges:
        challenge_id, name, desc, type_, target, money, xp, premium, difficulty, date, progress, completed = challenge
        
        progress = progress or 0
        completed = completed or 0
        
        # Difficulty emoji
        diff_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        
        # Status
        if completed:
            status = "✅ Completed"
        else:
            status = f"📊 Progress: {progress}/{target}"
        
        rewards = []
        if money > 0:
            rewards.append(f"💰${money:,}")
        if xp > 0:
            rewards.append(f"⭐{xp} XP")
        if premium > 0:
            rewards.append(f"💎{premium}")
        
        reward_str = " | ".join(rewards)
        
        embed.add_field(
            name=f"{diff_emoji.get(difficulty, '⚪')} {name}",
            value=f"{desc}\n{status}\n**Rewards:** {reward_str}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="achievements", description="View your achievements")
async def achievements(interaction: discord.Interaction):
    """Display achievement progress"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT a.*, ua.unlocked_date
        FROM achievements a
        LEFT JOIN user_achievements ua ON a.achievement_id = ua.achievement_id 
            AND ua.user_id = ?
        ORDER BY ua.unlocked_date DESC, a.rarity DESC
    """, (interaction.user.id,))
    
    achievements = c.fetchall()
    
    unlocked = [a for a in achievements if a[-1] is not None]
    locked = [a for a in achievements if a[-1] is None and not a[9]]  # Not hidden
    
    embed = discord.Embed(
        title="🏆 Achievements",
        description=f"**{len(unlocked)}/{len([a for a in achievements if not a[9]])}** Unlocked",
        color=discord.Color.gold()
    )
    
    # Show unlocked achievements
    if unlocked:
        unlocked_str = "\n".join([
            f"{a[7]} **{a[1]}** - {a[2]}" for a in unlocked[:10]
        ])
        embed.add_field(name="✅ Unlocked", value=unlocked_str, inline=False)
    
    # Show some locked achievements
    if locked:
        locked_str = "\n".join([
            f"🔒 **{a[1]}** - {a[2]}" for a in locked[:5]
        ])
        embed.add_field(name="🔒 Locked", value=locked_str, inline=False)
    
    total_rewards = sum([a[3] for a in unlocked])
    embed.set_footer(text=f"Total achievement rewards earned: ${total_rewards:,}")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="skills", description="View and upgrade your skills")
async def skills(interaction: discord.Interaction):
    """Display skill tree"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get user's skill points
    c.execute("SELECT skill_points FROM users WHERE user_id = ?", (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ Profile not found!", ephemeral=True)
        conn.close()
        return
    
    skill_points = result[0]
    
    # Get unlocked skills
    c.execute("""
        SELECT s.*, us.skill_level
        FROM skill_tree s
        LEFT JOIN user_skills us ON s.skill_id = us.skill_id AND us.user_id = ?
        ORDER BY s.skill_tier, s.cost_points
    """, (interaction.user.id,))
    
    skills = c.fetchall()
    
    embed = discord.Embed(
        title="🌟 Skill Tree",
        description=f"**Available Points:** {skill_points}",
        color=discord.Color.purple()
    )
    
    # Group by tier
    tiers = {}
    for skill in skills:
        tier = skill[3]
        if tier not in tiers:
            tiers[tier] = []
        tiers[tier].append(skill)
    
    for tier, tier_skills in sorted(tiers.items()):
        tier_names = {1: "Foundation", 2: "Advanced", 3: "Expert", 4: "Master"}
        
        skills_str = ""
        for skill in tier_skills[:3]:  # Show max 3 per tier
            skill_id, name, category, tier, cost, effect_type, effect_value, requires, desc, max_level, level = skill
            
            level = level or 0
            status = f"✅ Level {level}/{max_level}" if level > 0 else f"🔒 Cost: {cost} SP"
            
            skills_str += f"**{name}** ({category})\n{desc}\n{status}\n\n"
        
        if skills_str:
            embed.add_field(
                name=f"{'⭐' * tier} Tier {tier}: {tier_names.get(tier, 'Unknown')}",
                value=skills_str,
                inline=False
            )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="upgrade", description="Upgrade a skill")
@app_commands.describe(skill_name="Name of the skill to upgrade")
async def upgrade(interaction: discord.Interaction, skill_name: str):
    """Upgrade a skill in the skill tree"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get user skill points
    c.execute("SELECT skill_points FROM users WHERE user_id = ?", (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ Profile not found!", ephemeral=True)
        conn.close()
        return
    
    skill_points = result[0]
    
    # Find skill
    c.execute("SELECT * FROM skill_tree WHERE skill_name LIKE ?", (f"%{skill_name}%",))
    skill = c.fetchone()
    
    if not skill:
        await interaction.response.send_message(f"❌ Skill '{skill_name}' not found!", ephemeral=True)
        conn.close()
        return
    
    skill_id, name, category, tier, cost, effect_type, effect_value, requires, desc, max_level = skill
    
    # Check current level
    c.execute("SELECT skill_level FROM user_skills WHERE user_id = ? AND skill_id = ?",
              (interaction.user.id, skill_id))
    current = c.fetchone()
    current_level = current[0] if current else 0
    
    # Check if maxed
    if current_level >= max_level:
        await interaction.response.send_message(f"❌ {name} is already maxed out!", ephemeral=True)
        conn.close()
        return
    
    # Check skill points
    if skill_points < cost:
        await interaction.response.send_message(
            f"❌ Not enough skill points! Need {cost}, have {skill_points}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Check prerequisites
    if requires:
        c.execute("""
            SELECT skill_level FROM user_skills 
            WHERE user_id = ? AND skill_id = ?
        """, (interaction.user.id, requires))
        prereq = c.fetchone()
        
        if not prereq or prereq[0] == 0:
            c.execute("SELECT skill_name FROM skill_tree WHERE skill_id = ?", (requires,))
            prereq_name = c.fetchone()[0]
            await interaction.response.send_message(
                f"❌ You need to unlock **{prereq_name}** first!",
                ephemeral=True
            )
            conn.close()
            return
    
    # Unlock/upgrade skill
    if current_level == 0:
        c.execute("""
            INSERT INTO user_skills (user_id, skill_id, skill_level)
            VALUES (?, ?, 1)
        """, (interaction.user.id, skill_id))
    else:
        c.execute("""
            UPDATE user_skills 
            SET skill_level = skill_level + 1
            WHERE user_id = ? AND skill_id = ?
        """, (interaction.user.id, skill_id))
    
    # Deduct points
    c.execute("""
        UPDATE users 
        SET skill_points = skill_points - ?
        WHERE user_id = ?
    """, (cost, interaction.user.id))
    
    conn.commit()
    
    new_level = current_level + 1
    
    embed = discord.Embed(
        title="✨ Skill Upgraded!",
        description=f"**{name}** upgraded to Level {new_level}!",
        color=discord.Color.green()
    )
    embed.add_field(name="Category", value=category.title(), inline=True)
    embed.add_field(name="Effect", value=f"+{effect_value} {effect_type}", inline=True)
    embed.add_field(name="Points Used", value=str(cost), inline=True)
    embed.add_field(name="Description", value=desc, inline=False)
    embed.set_footer(text=f"Remaining Skill Points: {skill_points - cost}")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="experience", description="View XP and level progress")
async def experience(interaction: discord.Interaction):
    """Display experience and level information"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT experience, license_level, skill_points FROM users WHERE user_id = ?",
              (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ Profile not found!", ephemeral=True)
        conn.close()
        return
    
    xp, license, skill_points = result
    
    # Calculate level from XP
    level = int((xp / 1000) ** 0.5) + 1
    xp_for_current = (level - 1) ** 2 * 1000
    xp_for_next = level ** 2 * 1000
    xp_progress = xp - xp_for_current
    xp_needed = xp_for_next - xp_for_current
    
    progress_percent = (xp_progress / xp_needed) * 100
    
    # License levels
    licenses = {
        "rookie": (0, "🏁"),
        "amateur": (5, "🥉"),
        "semi-pro": (15, "🥈"),
        "pro": (30, "🥇"),
        "expert": (50, "💎"),
        "legend": (75, "👑"),
        "world_champion": (100, "🏆")
    }
    
    embed = discord.Embed(
        title=f"📊 Experience & Progression",
        description=f"**Level {level}** | License: {license.upper()}",
        color=discord.Color.blue()
    )
    
    # Progress bar
    filled = int(progress_percent / 10)
    bar = "█" * filled + "░" * (10 - filled)
    
    embed.add_field(
        name="Level Progress",
        value=f"{bar} {progress_percent:.1f}%\n{xp_progress:,}/{xp_needed:,} XP",
        inline=False
    )
    
    embed.add_field(name="Total XP", value=f"{xp:,}", inline=True)
    embed.add_field(name="Skill Points", value=str(skill_points), inline=True)
    embed.add_field(name="Next Level", value=f"Level {level + 1}", inline=True)
    
    # License progression
    current_license_emoji = licenses.get(license, ("", "🏁"))[1]
    embed.add_field(
        name=f"{current_license_emoji} Current License",
        value=f"**{license.upper().replace('_', ' ')}**",
        inline=False
    )
    
    # Next license
    for lic_name, (required_level, emoji) in licenses.items():
        if required_level > level:
            embed.add_field(
                name=f"{emoji} Next License",
                value=f"{lic_name.upper().replace('_', ' ')} (Level {required_level})",
                inline=False
            )
            break
    
    await interaction.response.send_message(embed=embed)
    conn.close()

# ============================================================================
# CAR & GARAGE COMMANDS (Commands 14-23)
# ============================================================================

@bot.tree.command(name="buycar", description="Purchase a new car")
@app_commands.describe(car_tier="Car performance tier")
@app_commands.choices(car_tier=[
    app_commands.Choice(name="🟢 Budget ($50,000)", value="budget"),
    app_commands.Choice(name="🔵 Standard ($150,000)", value="standard"),
    app_commands.Choice(name="🟣 Premium ($350,000)", value="premium"),
    app_commands.Choice(name="🟠 Elite ($750,000)", value="elite"),
    app_commands.Choice(name="🔴 Championship ($1,500,000)", value="championship"),
])
async def buycar(interaction: discord.Interaction, car_tier: app_commands.Choice[str]):
    """Purchase a new car from the dealership"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Car tier stats
    car_stats = {
        "budget": {"price": 50000, "power": 55, "aero": 52, "handling": 54, "reliability": 88},
        "standard": {"price": 150000, "power": 65, "aero": 63, "handling": 64, "reliability": 90},
        "premium": {"price": 350000, "power": 75, "aero": 74, "handling": 73, "reliability": 92},
        "elite": {"price": 750000, "power": 85, "aero": 84, "handling": 83, "reliability": 94},
        "championship": {"price": 1500000, "power": 95, "aero": 94, "handling": 93, "reliability": 96},
    }
    
    tier = car_tier.value
    stats = car_stats[tier]
    price = stats["price"]
    
    # Check balance
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ Profile not found!", ephemeral=True)
        conn.close()
        return
    
    balance = result[0]
    
    if balance < price:
        await interaction.response.send_message(
            f"❌ Not enough money! Need ${price:,}, have ${balance:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Create car
    car_name = f"{tier.title()} F1 Car"
    
    c.execute("""
        INSERT INTO cars (owner_id, car_name, car_tier, engine_power, aero, handling, reliability, car_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (interaction.user.id, car_name, tier, stats["power"], stats["aero"], 
          stats["handling"], stats["reliability"], price))
    
    # Deduct money
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (price, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="🏎️ New Car Purchased!",
        description=f"**{car_name}** added to your garage!",
        color=discord.Color.green()
    )
    embed.add_field(name="Tier", value=tier.title(), inline=True)
    embed.add_field(name="Price", value=f"${price:,}", inline=True)
    embed.add_field(name="Remaining Balance", value=f"${balance - price:,}", inline=True)
    
    embed.add_field(name="⚡ Engine Power", value=str(stats["power"]), inline=True)
    embed.add_field(name="🌪️ Aerodynamics", value=str(stats["aero"]), inline=True)
    embed.add_field(name="🎯 Handling", value=str(stats["handling"]), inline=True)
    embed.add_field(name="🔧 Reliability", value=f"{stats['reliability']}%", inline=True)
    
    embed.set_footer(text="Use /setcar to make this your active car!")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="sellcar", description="Sell a car from your garage")
@app_commands.describe(car_name="Name of the car to sell")
async def sellcar(interaction: discord.Interaction, car_name: str):
    """Sell a car for money"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Find car
    c.execute("""
        SELECT car_id, car_name, car_value, is_active 
        FROM cars 
        WHERE owner_id = ? AND car_name LIKE ?
    """, (interaction.user.id, f"%{car_name}%"))
    
    car = c.fetchone()
    
    if not car:
        await interaction.response.send_message(f"❌ Car '{car_name}' not found in your garage!", ephemeral=True)
        conn.close()
        return
    
    car_id, name, value, is_active = car
    
    if is_active:
        await interaction.response.send_message("❌ Cannot sell your active car! Set another car as active first.", ephemeral=True)
        conn.close()
        return
    
    # Calculate sell price (70% of value)
    sell_price = int(value * 0.7)
    
    # Delete car and add money
    c.execute("DELETE FROM cars WHERE car_id = ?", (car_id,))
    c.execute("UPDATE users SET money = money + ? WHERE user_id = ?",
              (sell_price, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="💰 Car Sold",
        description=f"**{name}** sold for **${sell_price:,}**",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Original value: ${value:,} (70% return)")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="setcar", description="Set your active car")
@app_commands.describe(car_name="Name of the car to activate")
async def setcar(interaction: discord.Interaction, car_name: str):
    """Change active car"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Find car
    c.execute("""
        SELECT car_id, car_name 
        FROM cars 
        WHERE owner_id = ? AND car_name LIKE ?
    """, (interaction.user.id, f"%{car_name}%"))
    
    car = c.fetchone()
    
    if not car:
        await interaction.response.send_message(f"❌ Car '{car_name}' not found!", ephemeral=True)
        conn.close()
        return
    
    car_id, name = car
    
    # Deactivate all cars
    c.execute("UPDATE cars SET is_active = 0 WHERE owner_id = ?", (interaction.user.id,))
    
    # Activate selected car
    c.execute("UPDATE cars SET is_active = 1 WHERE car_id = ?", (car_id,))
    
    conn.commit()
    
    await interaction.response.send_message(f"✅ **{name}** is now your active car!", ephemeral=True)
    conn.close()

@bot.tree.command(name="upgrade_car", description="Upgrade your car's components")
@app_commands.describe(
    component="Component to upgrade",
    amount="Upgrade amount (1-10)"
)
@app_commands.choices(component=[
    app_commands.Choice(name="⚡ Engine Power", value="engine_power"),
    app_commands.Choice(name="🌪️ Aerodynamics", value="aero"),
    app_commands.Choice(name="🎯 Handling", value="handling"),
    app_commands.Choice(name="🔋 ERS Power", value="ers_power"),
    app_commands.Choice(name="💨 DRS Efficiency", value="drs_efficiency"),
])
async def upgrade_car(interaction: discord.Interaction, component: app_commands.Choice[str], amount: int = 1):
    """Upgrade car components"""
    if not 1 <= amount <= 10:
        await interaction.response.send_message("❌ Amount must be between 1 and 10!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get active car
    c.execute(f"""
        SELECT car_id, car_name, {component.value}, car_value 
        FROM cars 
        WHERE owner_id = ? AND is_active = 1
    """, (interaction.user.id,))
    
    car = c.fetchone()
    
    if not car:
        await interaction.response.send_message("❌ No active car found!", ephemeral=True)
        conn.close()
        return
    
    car_id, car_name, current_value, car_value = car
    
    # Check if already maxed
    if current_value >= 100:
        await interaction.response.send_message(f"❌ {component.name} is already maxed out!", ephemeral=True)
        conn.close()
        return
    
    # Calculate cost (exponential)
    cost_per_point = 1000 + (current_value * 100)
    total_cost = cost_per_point * amount
    
    # Check balance
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    balance = c.fetchone()[0]
    
    if balance < total_cost:
        await interaction.response.send_message(
            f"❌ Not enough money! Need ${total_cost:,}, have ${balance:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Apply upgrade
    new_value = min(100, current_value + amount)
    actual_upgrade = new_value - current_value
    actual_cost = cost_per_point * actual_upgrade
    
    c.execute(f"""
        UPDATE cars 
        SET {component.value} = ?, car_value = car_value + ?
        WHERE car_id = ?
    """, (new_value, actual_cost, car_id))
    
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (actual_cost, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="⬆️ Car Upgraded!",
        description=f"**{car_name}**",
        color=discord.Color.blue()
    )
    embed.add_field(name="Component", value=component.name, inline=True)
    embed.add_field(name="Upgrade", value=f"{current_value} → {new_value} (+{actual_upgrade})", inline=True)
    embed.add_field(name="Cost", value=f"${actual_cost:,}", inline=True)
    embed.set_footer(text=f"Remaining balance: ${balance - actual_cost:,}")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="repair", description="Repair your car's damage")
async def repair(interaction: discord.Interaction):
    """Repair car damage and wear"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get active car
    c.execute("""
        SELECT car_id, car_name, engine_wear, gearbox_wear, chassis_wear, brake_wear, suspension_wear
        FROM cars 
        WHERE owner_id = ? AND is_active = 1
    """, (interaction.user.id,))
    
    car = c.fetchone()
    
    if not car:
        await interaction.response.send_message("❌ No active car found!", ephemeral=True)
        conn.close()
        return
    
    car_id, car_name, engine_wear, gearbox_wear, chassis_wear, brake_wear, suspension_wear = car
    
    # Calculate total wear
    total_wear = (engine_wear or 0) + (gearbox_wear or 0) + (chassis_wear or 0) + (brake_wear or 0) + (suspension_wear or 0)
    
    if total_wear == 0:
        await interaction.response.send_message("✅ Your car is in perfect condition!", ephemeral=True)
        conn.close()
        return
    
    # Repair cost: $100 per wear point
    repair_cost = int(total_wear * 100)
    
    # Check balance
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    balance = c.fetchone()[0]
    
    if balance < repair_cost:
        await interaction.response.send_message(
            f"❌ Not enough money for repairs! Need ${repair_cost:,}, have ${balance:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Repair car
    c.execute("""
        UPDATE cars 
        SET engine_wear = 0, gearbox_wear = 0, chassis_wear = 0, brake_wear = 0, suspension_wear = 0
        WHERE car_id = ?
    """, (car_id,))
    
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (repair_cost, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="🔧 Car Repaired!",
        description=f"**{car_name}** is back in top condition!",
        color=discord.Color.green()
    )
    embed.add_field(name="Repairs Made", value=f"{total_wear:.1f}% wear removed", inline=True)
    embed.add_field(name="Cost", value=f"${repair_cost:,}", inline=True)
    embed.set_footer(text=f"New balance: ${balance - repair_cost:,}")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="livery", description="Customize your car's livery")
@app_commands.describe(
    primary_color="Primary color (hex code, e.g., #FF0000)",
    secondary_color="Secondary color (hex code, e.g., #FFFFFF)"
)
async def livery(interaction: discord.Interaction, primary_color: str, secondary_color: str):
    """Customize car appearance"""
    import re
    
    # Validate hex colors
    hex_pattern = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
    
    if not hex_pattern.match(primary_color) or not hex_pattern.match(secondary_color):
        await interaction.response.send_message(
            "❌ Invalid color format! Use hex codes like #FF0000",
            ephemeral=True
        )
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Cost for livery change
    livery_cost = 5000
    
    # Check balance
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    balance = c.fetchone()[0]
    
    if balance < livery_cost:
        await interaction.response.send_message(
            f"❌ Not enough money! Livery change costs ${livery_cost:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Update livery
    c.execute("""
        UPDATE cars 
        SET livery_color_primary = ?, livery_color_secondary = ?
        WHERE owner_id = ? AND is_active = 1
    """, (primary_color, secondary_color, interaction.user.id))
    
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (livery_cost, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="🎨 Livery Updated!",
        description="Your car has a new look!",
        color=int(primary_color.replace('#', '0x'), 16)
    )
    embed.add_field(name="Primary Color", value=primary_color, inline=True)
    embed.add_field(name="Secondary Color", value=secondary_color, inline=True)
    embed.add_field(name="Cost", value=f"${livery_cost:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

# ============================================================================
# SETUP & TUNING COMMANDS (Commands 24-28)
# ============================================================================

@bot.tree.command(name="setup", description="View car setup configurations")
async def setup(interaction: discord.Interaction):
    """Display saved setups"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT setup_name, track, conditions, is_favorite, times_used
        FROM setups
        WHERE user_id = ?
        ORDER BY is_favorite DESC, times_used DESC
        LIMIT 10
    """, (interaction.user.id,))
    
    setups = c.fetchall()
    
    if not setups:
        embed = discord.Embed(
            title="🔧 Car Setups",
            description="No saved setups yet! Create one with `/createsetup`",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(
        title="🔧 Saved Car Setups",
        description=f"You have {len(setups)} saved setup(s)",
        color=discord.Color.blue()
    )
    
    for setup in setups:
        name, track, conditions, favorite, uses = setup
        fav_icon = "⭐" if favorite else ""
        
        embed.add_field(
            name=f"{fav_icon} {name}",
            value=f"Track: {track} | Conditions: {conditions}\nUsed: {uses} times",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="createsetup", description="Create a new car setup")
@app_commands.describe(
    setup_name="Name for this setup",
    track="Track this setup is for"
)
async def createsetup(interaction: discord.Interaction, setup_name: str, track: str):
    """Create a new setup configuration"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Check if name already exists
    c.execute("SELECT setup_id FROM setups WHERE user_id = ? AND setup_name = ?",
              (interaction.user.id, setup_name))
    
    if c.fetchone():
        await interaction.response.send_message(
            f"❌ Setup '{setup_name}' already exists!",
            ephemeral=True
        )
        conn.close()
        return
    
    # Create default setup
    c.execute("""
        INSERT INTO setups (user_id, setup_name, track)
        VALUES (?, ?, ?)
    """, (interaction.user.id, setup_name, track))
    
    conn.commit()
    
    embed = discord.Embed(
        title="✅ Setup Created",
        description=f"**{setup_name}** created for {track}",
        color=discord.Color.green()
    )
    embed.add_field(name="Next Step", value="Use `/adjustsetup` to tune your setup!", inline=False)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="adjustsetup", description="Adjust setup parameters")
@app_commands.describe(
    setup_name="Setup to adjust",
    parameter="Parameter to change",
    value="New value (0-100)"
)
@app_commands.choices(parameter=[
    app_commands.Choice(name="Front Wing", value="front_wing"),
    app_commands.Choice(name="Rear Wing", value="rear_wing"),
    app_commands.Choice(name="Differential", value="differential"),
    app_commands.Choice(name="Brake Balance", value="brake_balance"),
    app_commands.Choice(name="Suspension (Front)", value="suspension_front"),
    app_commands.Choice(name="Suspension (Rear)", value="suspension_rear"),
])
async def adjustsetup(interaction: discord.Interaction, setup_name: str, parameter: app_commands.Choice[str], value: int):
    """Adjust setup parameters"""
    if not 0 <= value <= 100:
        await interaction.response.send_message("❌ Value must be between 0-100!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Find setup
    c.execute("SELECT setup_id FROM setups WHERE user_id = ? AND setup_name = ?",
              (interaction.user.id, setup_name))
    
    setup = c.fetchone()
    
    if not setup:
        await interaction.response.send_message(f"❌ Setup '{setup_name}' not found!", ephemeral=True)
        conn.close()
        return
    
    setup_id = setup[0]
    
    # Update parameter
    c.execute(f"""
        UPDATE setups 
        SET {parameter.value} = ?
        WHERE setup_id = ?
    """, (value, setup_id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="🔧 Setup Adjusted",
        description=f"**{setup_name}** updated",
        color=discord.Color.blue()
    )
    embed.add_field(name="Parameter", value=parameter.name, inline=True)
    embed.add_field(name="New Value", value=str(value), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    conn.close()

@bot.tree.command(name="loadsetup", description="Load a setup for your next race")
@app_commands.describe(setup_name="Setup to load")
async def loadsetup(interaction: discord.Interaction, setup_name: str):
    """Load a saved setup"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT setup_id, front_wing, rear_wing, differential, brake_balance, 
               suspension_front, suspension_rear
        FROM setups 
        WHERE user_id = ? AND setup_name = ?
    """, (interaction.user.id, setup_name))
    
    setup = c.fetchone()
    
    if not setup:
        await interaction.response.send_message(f"❌ Setup '{setup_name}' not found!", ephemeral=True)
        conn.close()
        return
    
    # Increment usage counter
    c.execute("UPDATE setups SET times_used = times_used + 1 WHERE setup_id = ?", (setup[0],))
    conn.commit()
    
    embed = discord.Embed(
        title="✅ Setup Loaded",
        description=f"**{setup_name}** is ready for your next race!",
        color=discord.Color.green()
    )
    embed.add_field(name="Front Wing", value=str(setup[1]), inline=True)
    embed.add_field(name="Rear Wing", value=str(setup[2]), inline=True)
    embed.add_field(name="Differential", value=str(setup[3]), inline=True)
    embed.add_field(name="Brake Balance", value=str(setup[4]), inline=True)
    embed.add_field(name="Suspension (F)", value=str(setup[5]), inline=True)
    embed.add_field(name="Suspension (R)", value=str(setup[6]), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    conn.close()

# ============================================================================
# ECONOMY & TRADING COMMANDS (Commands 29-38)
# ============================================================================

@bot.tree.command(name="shop", description="Browse the item shop")
@app_commands.describe(category="Shop category")
@app_commands.choices(category=[
    app_commands.Choice(name="🏎️ Cars", value="cars"),
    app_commands.Choice(name="🔧 Parts", value="parts"),
    app_commands.Choice(name="🎨 Cosmetics", value="cosmetics"),
    app_commands.Choice(name="💎 Premium", value="premium"),
])
async def shop(interaction: discord.Interaction, category: app_commands.Choice[str] = None):
    """Display shop items"""
    cat = category.value if category else "cars"
    
    embed = discord.Embed(
        title=f"🏪 Shop - {cat.title()}",
        description="Available items for purchase",
        color=discord.Color.gold()
    )
    
    if cat == "cars":
        embed.add_field(
            name="🟢 Budget Car",
            value="$50,000 | Stats: 55/52/54\nGood starter option",
            inline=False
        )
        embed.add_field(
            name="🔵 Standard Car",
            value="$150,000 | Stats: 65/63/64\nSolid mid-tier performance",
            inline=False
        )
        embed.add_field(
            name="🟣 Premium Car",
            value="$350,000 | Stats: 75/74/73\nHigh performance racing",
            inline=False
        )
        embed.add_field(
            name="🟠 Elite Car",
            value="$750,000 | Stats: 85/84/83\nProfessional grade",
            inline=False
        )
        embed.add_field(
            name="🔴 Championship Car",
            value="$1,500,000 | Stats: 95/94/93\nTop tier performance",
            inline=False
        )
    
    elif cat == "parts":
        embed.add_field(
            name="⚡ Engine Upgrade Kit",
            value="$10,000 | +5 Engine Power",
            inline=True
        )
        embed.add_field(
            name="🌪️ Aero Package",
            value="$8,000 | +5 Aerodynamics",
            inline=True
        )
        embed.add_field(
            name="🎯 Handling Kit",
            value="$9,000 | +5 Handling",
            inline=True
        )
    
    elif cat == "cosmetics":
        embed.add_field(
            name="🎨 Custom Livery",
            value="$5,000 | Customize your colors",
            inline=True
        )
        embed.add_field(
            name="🏁 Team Badge",
            value="$2,000 | Show your team pride",
            inline=True
        )
    
    else:  # premium
        embed.add_field(
            name="💎 Premium Pass (Month)",
            value="100 💎 | Double XP + Exclusive content",
            inline=False
        )
        embed.add_field(
            name="🎁 Starter Bundle",
            value="50 💎 | $100k + Premium Car",
            inline=False
        )
    
    embed.set_footer(text="Use /buycar, /upgrade_car, or /livery to purchase!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="market", description="View the player marketplace")
async def market(interaction: discord.Interaction):
    """Display marketplace listings"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT m.*, u.driver_name, c.car_name, c.car_tier
        FROM market m
        JOIN users u ON m.seller_id = u.user_id
        LEFT JOIN cars c ON m.item_id = c.car_id AND m.item_type = 'car'
        WHERE m.status = 'active'
        ORDER BY m.listed_date DESC
        LIMIT 10
    """)
    
    listings = c.fetchall()
    
    if not listings:
        embed = discord.Embed(
            title="🏪 Marketplace",
            description="No active listings. Use `/sell` to list items!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        conn.close()
        return
    
    embed = discord.Embed(
        title="🏪 Player Marketplace",
        description="Buy items from other players",
        color=discord.Color.blue()
    )
    
    for listing in listings[:5]:
        listing_id, seller_id, item_type, item_id, price, listed_date, status, buyer_id, sold_date, seller_name, car_name, car_tier = listing
        
        if item_type == "car":
            item_desc = f"{car_name} ({car_tier})"
        else:
            item_desc = f"{item_type.title()} #{item_id}"
        
        embed.add_field(
            name=f"#{listing_id} - {item_desc}",
            value=f"Seller: {seller_name}\nPrice: ${price:,}\nUse `/buy {listing_id}` to purchase",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="sell", description="List an item on the marketplace")
@app_commands.describe(
    item_type="Type of item to sell",
    item_name="Name of the item",
    price="Selling price"
)
@app_commands.choices(item_type=[
    app_commands.Choice(name="🏎️ Car", value="car"),
    app_commands.Choice(name="🔧 Part", value="part"),
])
async def sell(interaction: discord.Interaction, item_type: app_commands.Choice[str], item_name: str, price: int):
    """List item for sale"""
    if price < 100:
        await interaction.response.send_message("❌ Minimum price is $100!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    item_id = None
    
    if item_type.value == "car":
        c.execute("""
            SELECT car_id, is_active 
            FROM cars 
            WHERE owner_id = ? AND car_name LIKE ?
        """, (interaction.user.id, f"%{item_name}%"))
        
        car = c.fetchone()
        
        if not car:
            await interaction.response.send_message(f"❌ Car '{item_name}' not found!", ephemeral=True)
            conn.close()
            return
        
        if car[1]:
            await interaction.response.send_message("❌ Cannot sell your active car!", ephemeral=True)
            conn.close()
            return
        
        item_id = car[0]
    
    # Create listing
    c.execute("""
        INSERT INTO market (seller_id, item_type, item_id, price)
        VALUES (?, ?, ?, ?)
    """, (interaction.user.id, item_type.value, item_id, price))
    
    conn.commit()
    listing_id = c.lastrowid
    
    embed = discord.Embed(
        title="✅ Listed on Marketplace",
        description=f"Your item is now for sale!",
        color=discord.Color.green()
    )
    embed.add_field(name="Listing ID", value=f"#{listing_id}", inline=True)
    embed.add_field(name="Item", value=item_name, inline=True)
    embed.add_field(name="Price", value=f"${price:,}", inline=True)
    embed.set_footer(text="Other players can now purchase your item!")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="buy", description="Purchase from marketplace")
@app_commands.describe(listing_id="ID of the listing to buy")
async def buy(interaction: discord.Interaction, listing_id: int):
    """Buy item from marketplace"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get listing
    c.execute("""
        SELECT * FROM market WHERE listing_id = ? AND status = 'active'
    """, (listing_id,))
    
    listing = c.fetchone()
    
    if not listing:
        await interaction.response.send_message("❌ Listing not found or already sold!", ephemeral=True)
        conn.close()
        return
    
    _, seller_id, item_type, item_id, price, _, _, _, _ = listing
    
    if seller_id == interaction.user.id:
        await interaction.response.send_message("❌ Cannot buy your own listing!", ephemeral=True)
        conn.close()
        return
    
    # Check balance
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    balance = c.fetchone()[0]
    
    if balance < price:
        await interaction.response.send_message(
            f"❌ Not enough money! Need ${price:,}, have ${balance:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Transfer item
    if item_type == "car":
        c.execute("UPDATE cars SET owner_id = ? WHERE car_id = ?",
                  (interaction.user.id, item_id))
    
    # Transfer money
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (price, interaction.user.id))
    c.execute("UPDATE users SET money = money + ? WHERE user_id = ?",
              (price, seller_id))
    
    # Mark as sold
    c.execute("""
        UPDATE market 
        SET status = 'sold', buyer_id = ?, sold_date = ?
        WHERE listing_id = ?
    """, (interaction.user.id, datetime.now().isoformat(), listing_id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="✅ Purchase Complete!",
        description="Item added to your inventory",
        color=discord.Color.green()
    )
    embed.add_field(name="Listing ID", value=f"#{listing_id}", inline=True)
    embed.add_field(name="Price Paid", value=f"${price:,}", inline=True)
    embed.add_field(name="New Balance", value=f"${balance - price:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="loan", description="Take out a loan")
@app_commands.describe(amount="Loan amount ($1,000 - $500,000)")
async def loan(interaction: discord.Interaction, amount: int):
    """Borrow money with interest"""
    if not 1000 <= amount <= 500000:
        await interaction.response.send_message(
            "❌ Loan amount must be between $1,000 and $500,000!",
            ephemeral=True
        )
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Check existing loans
    c.execute("SELECT COUNT(*) FROM loans WHERE user_id = ? AND status = 'active'",
              (interaction.user.id,))
    
    if c.fetchone()[0] >= 3:
        await interaction.response.send_message(
            "❌ Maximum 3 active loans allowed!",
            ephemeral=True
        )
        conn.close()
        return
    
    # Calculate interest (10% + 2% per $100k)
    interest_rate = 0.10 + (amount / 100000) * 0.02
    total_repay = int(amount * (1 + interest_rate))
    
    # 30 days to repay
    due_date = (datetime.now() + timedelta(days=30)).isoformat()
    
    # Create loan
    c.execute("""
        INSERT INTO loans (user_id, amount, interest_rate, remaining_amount, due_date)
        VALUES (?, ?, ?, ?, ?)
    """, (interaction.user.id, amount, interest_rate, total_repay, due_date))
    
    # Add money
    c.execute("UPDATE users SET money = money + ? WHERE user_id = ?",
              (amount, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="💰 Loan Approved!",
        description="Funds have been added to your account",
        color=discord.Color.green()
    )
    embed.add_field(name="Loan Amount", value=f"${amount:,}", inline=True)
    embed.add_field(name="Interest Rate", value=f"{interest_rate*100:.1f}%", inline=True)
    embed.add_field(name="Total to Repay", value=f"${total_repay:,}", inline=True)
    embed.add_field(name="Due Date", value=due_date[:10], inline=False)
    embed.set_footer(text="Use /repay to pay back the loan early!")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="repay", description="Repay a loan")
@app_commands.describe(loan_id="Loan ID to repay (use /loans to see IDs)")
async def repay(interaction: discord.Interaction, loan_id: int):
    """Repay an active loan"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get loan
    c.execute("""
        SELECT remaining_amount FROM loans 
        WHERE loan_id = ? AND user_id = ? AND status = 'active'
    """, (loan_id, interaction.user.id))
    
    loan = c.fetchone()
    
    if not loan:
        await interaction.response.send_message("❌ Loan not found!", ephemeral=True)
        conn.close()
        return
    
    amount_due = loan[0]
    
    # Check balance
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    balance = c.fetchone()[0]
    
    if balance < amount_due:
        await interaction.response.send_message(
            f"❌ Not enough money! Need ${amount_due:,}, have ${balance:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Repay loan
    c.execute("UPDATE loans SET status = 'paid', remaining_amount = 0 WHERE loan_id = ?",
              (loan_id,))
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (amount_due, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="✅ Loan Repaid!",
        description="Your loan has been fully repaid",
        color=discord.Color.green()
    )
    embed.add_field(name="Amount Paid", value=f"${amount_due:,}", inline=True)
    embed.add_field(name="New Balance", value=f"${balance - amount_due:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="loans", description="View your active loans")
async def loans(interaction: discord.Interaction):
    """Display all active loans"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT loan_id, amount, interest_rate, remaining_amount, due_date
        FROM loans 
        WHERE user_id = ? AND status = 'active'
    """, (interaction.user.id,))
    
    active_loans = c.fetchall()
    
    if not active_loans:
        embed = discord.Embed(
            title="💰 Your Loans",
            description="You have no active loans!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(
        title="💰 Active Loans",
        description=f"You have {len(active_loans)} active loan(s)",
        color=discord.Color.blue()
    )
    
    for loan in active_loans:
        loan_id, original, rate, remaining, due = loan
        
        embed.add_field(
            name=f"Loan #{loan_id}",
            value=f"Original: ${original:,}\n"
                  f"Remaining: ${remaining:,}\n"
                  f"Rate: {rate*100:.1f}%\n"
                  f"Due: {due[:10]}",
            inline=False
        )
    
    total_debt = sum([l[3] for l in active_loans])
    embed.set_footer(text=f"Total debt: ${total_debt:,}")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    conn.close()

# Continuing with more commands...

@bot.tree.command(name="sponsors", description="View available sponsors")
async def sponsors(interaction: discord.Interaction):
    """Display available sponsorship deals"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT s.*, us.contract_id
        FROM sponsors s
        LEFT JOIN user_sponsors us ON s.sponsor_id = us.sponsor_id 
            AND us.user_id = ? AND us.status = 'active'
    """, (interaction.user.id,))
    
    sponsors_list = c.fetchall()
    
    embed = discord.Embed(
        title="🏢 Available Sponsors",
        description="Sign contracts for bonuses and payments!",
        color=discord.Color.blue()
    )
    
    for sponsor in sponsors_list[:10]:
        sponsor_id, name, tier, bonus_type, bonus_amount, req_type, req_value, contract_length, payment, unlock_req, emoji, has_contract = sponsor
        
        if has_contract:
            status = "✅ Active Contract"
        elif unlock_req:
            status = f"🔒 Locked ({unlock_req})"
        else:
            status = "📝 Available"
        
        tier_colors = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}
        
        embed.add_field(
            name=f"{emoji} {name} {tier_colors.get(tier, '')}",
            value=f"{status}\n"
                  f"Payment: ${payment:,}/race\n"
                  f"Length: {contract_length} races\n"
                  f"Bonus: {bonus_type.replace('_', ' ').title()}",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="sign", description="Sign a sponsor contract")
@app_commands.describe(sponsor_name="Name of sponsor to sign with")
async def sign(interaction: discord.Interaction, sponsor_name: str):
    """Sign a sponsorship deal"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Find sponsor
    c.execute("SELECT * FROM sponsors WHERE sponsor_name LIKE ?", (f"%{sponsor_name}%",))
    sponsor = c.fetchone()
    
    if not sponsor:
        await interaction.response.send_message(f"❌ Sponsor '{sponsor_name}' not found!", ephemeral=True)
        conn.close()
        return
    
    sponsor_id, name, tier, bonus_type, bonus_amount, req_type, req_value, contract_length, payment, unlock_req, emoji = sponsor
    
    # Check if already signed
    c.execute("""
        SELECT contract_id FROM user_sponsors 
        WHERE user_id = ? AND sponsor_id = ? AND status = 'active'
    """, (interaction.user.id, sponsor_id))
    
    if c.fetchone():
        await interaction.response.send_message(f"❌ Already have a contract with {name}!", ephemeral=True)
        conn.close()
        return
    
    # Check unlock requirements
    if unlock_req:
        # Parse requirement (e.g., "skill_rating>70")
        # Simplified check here
        await interaction.response.send_message(
            f"❌ You don't meet the requirements for {name}!\n{unlock_req}",
            ephemeral=True
        )
        conn.close()
        return
    
    # Sign contract
    c.execute("""
        INSERT INTO user_sponsors (user_id, sponsor_id, races_remaining)
        VALUES (?, ?, ?)
    """, (interaction.user.id, sponsor_id, contract_length))
    
    conn.commit()
    
    embed = discord.Embed(
        title=f"{emoji} Contract Signed!",
        description=f"Welcome to **{name}**!",
        color=discord.Color.green()
    )
    embed.add_field(name="Tier", value=tier.title(), inline=True)
    embed.add_field(name="Contract Length", value=f"{contract_length} races", inline=True)
    embed.add_field(name="Payment/Race", value=f"${payment:,}", inline=True)
    embed.add_field(name="Bonus", value=f"{bonus_type.replace('_', ' ').title()}: {bonus_amount}", inline=False)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

# ============================================================================
# LEAGUE & TOURNAMENT COMMANDS (Commands 39-48)
# ============================================================================

@bot.tree.command(name="createleague", description="Create a racing league")
@app_commands.describe(
    league_name="Name of your league",
    max_drivers="Maximum drivers allowed (10-30)",
    private="Make league private?"
)
async def createleague(interaction: discord.Interaction, league_name: str, max_drivers: int = 20, private: bool = False):
    """Create a new racing league"""
    if not 10 <= max_drivers <= 30:
        await interaction.response.send_message("❌ Max drivers must be 10-30!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Create league
    c.execute("""
        INSERT INTO leagues (league_name, creator_id, max_drivers, private)
        VALUES (?, ?, ?, ?)
    """, (league_name, interaction.user.id, max_drivers, 1 if private else 0))
    
    league_id = c.lastrowid
    
    # Add creator as first member
    c.execute("""
        INSERT INTO league_members (league_id, user_id)
        VALUES (?, ?)
    """, (league_id, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="🏁 League Created!",
        description=f"**{league_name}** is ready for racing!",
        color=discord.Color.green()
    )
    embed.add_field(name="League ID", value=f"#{league_id}", inline=True)
    embed.add_field(name="Max Drivers", value=str(max_drivers), inline=True)
    embed.add_field(name="Privacy", value="Private" if private else "Public", inline=True)
    embed.set_footer(text=f"Share League ID {league_id} to invite drivers!")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="leagues", description="View available leagues")
async def leagues(interaction: discord.Interaction):
    """Display active leagues"""
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT l.league_id, l.league_name, l.creator_id, l.max_drivers, l.current_season,
               COUNT(lm.member_id) as member_count,
               u.driver_name as creator_name
        FROM leagues l
        LEFT JOIN league_members lm ON l.league_id = lm.league_id
        JOIN users u ON l.creator_id = u.user_id
        WHERE l.status = 'active' AND l.private = 0
        GROUP BY l.league_id
        ORDER BY member_count DESC
        LIMIT 10
    """)
    
    leagues_list = c.fetchall()
    
    if not leagues_list:
        embed = discord.Embed(
            title="🏁 Racing Leagues",
            description="No public leagues available. Create one with `/createleague`!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        conn.close()
        return
    
    embed = discord.Embed(
        title="🏁 Available Leagues",
        description="Join a league to compete!",
        color=discord.Color.blue()
    )
    
    for league in leagues_list:
        league_id, name, creator_id, max_drivers, season, member_count, creator = league
        
        embed.add_field(
            name=f"#{league_id} - {name}",
            value=f"Created by: {creator}\n"
                  f"Season: {season} | Drivers: {member_count}/{max_drivers}\n"
                  f"Use `/joinleague {league_id}` to join",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="joinleague", description="Join a racing league")
@app_commands.describe(league_id="League ID to join")
async def joinleague(interaction: discord.Interaction, league_id: int):
    """Join an existing league"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Check league exists
    c.execute("""
        SELECT league_name, max_drivers, 
               (SELECT COUNT(*) FROM league_members WHERE league_id = ?) as member_count
        FROM leagues 
        WHERE league_id = ? AND status = 'active'
    """, (league_id, league_id))
    
    league = c.fetchone()
    
    if not league:
        await interaction.response.send_message("❌ League not found or inactive!", ephemeral=True)
        conn.close()
        return
    
    name, max_drivers, member_count = league
    
    if member_count >= max_drivers:
        await interaction.response.send_message("❌ League is full!", ephemeral=True)
        conn.close()
        return
    
    # Check if already member
    c.execute("""
        SELECT member_id FROM league_members 
        WHERE league_id = ? AND user_id = ?
    """, (league_id, interaction.user.id))
    
    if c.fetchone():
        await interaction.response.send_message("❌ Already a member of this league!", ephemeral=True)
        conn.close()
        return
    
    # Join league
    c.execute("""
        INSERT INTO league_members (league_id, user_id)
        VALUES (?, ?)
    """, (league_id, interaction.user.id))
    
    conn.commit()
    
    embed = discord.Embed(
        title="✅ Joined League!",
        description=f"Welcome to **{name}**!",
        color=discord.Color.green()
    )
    embed.add_field(name="Members", value=f"{member_count + 1}/{max_drivers}", inline=True)
    embed.set_footer(text="Good luck in your races!")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="standings", description="View league standings")
@app_commands.describe(league_id="League ID (leave empty for your leagues)")
async def standings(interaction: discord.Interaction, league_id: int = None):
    """Display league championship standings"""
    conn = db.get_conn()
    c = conn.cursor()
    
    if not league_id:
        # Get user's first league
        c.execute("""
            SELECT league_id FROM league_members 
            WHERE user_id = ? AND active = 1
            LIMIT 1
        """, (interaction.user.id,))
        
        result = c.fetchone()
        if not result:
            await interaction.response.send_message("❌ Not a member of any league!", ephemeral=True)
            conn.close()
            return
        
        league_id = result[0]
    
    # Get league info
    c.execute("SELECT league_name, current_season FROM leagues WHERE league_id = ?", (league_id,))
    league_info = c.fetchone()
    
    if not league_info:
        await interaction.response.send_message("❌ League not found!", ephemeral=True)
        conn.close()
        return
    
    league_name, season = league_info
    
    # Get standings
    c.execute("""
        SELECT u.driver_name, lm.season_points, lm.season_wins, lm.season_podiums, lm.season_fastest_laps
        FROM league_members lm
        JOIN users u ON lm.user_id = u.user_id
        WHERE lm.league_id = ? AND lm.active = 1
        ORDER BY lm.season_points DESC, lm.season_wins DESC
    """, (league_id,))
    
    standings_list = c.fetchall()
    
    embed = discord.Embed(
        title=f"🏆 {league_name} - Season {season}",
        description="Championship Standings",
        color=discord.Color.gold()
    )
    
    for idx, driver in enumerate(standings_list, 1):
        name, points, wins, podiums, fastest_laps = driver
        
        if idx == 1:
            position = "🥇"
        elif idx == 2:
            position = "🥈"
        elif idx == 3:
            position = "🥉"
        else:
            position = f"**P{idx}**"
        
        embed.add_field(
            name=f"{position} {name}",
            value=f"Points: {points} | Wins: {wins} | Podiums: {podiums}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="tournament", description="Create a tournament")
@app_commands.describe(
    tournament_name="Tournament name",
    max_participants="Max participants (8/16/32)",
    entry_fee="Entry fee (0 for free)"
)
@app_commands.choices(max_participants=[
    app_commands.Choice(name="8 Drivers", value=8),
    app_commands.Choice(name="16 Drivers", value=16),
    app_commands.Choice(name="32 Drivers", value=32),
])
async def tournament(interaction: discord.Interaction, tournament_name: str, max_participants: app_commands.Choice[int], entry_fee: int = 0):
    """Create an elimination tournament"""
    if entry_fee < 0:
        await interaction.response.send_message("❌ Entry fee cannot be negative!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Calculate prize pool
    prize_pool = 0  # Will grow as players join
    
    # Calculate rounds
    import math
    total_rounds = int(math.log2(max_participants.value))
    
    # Create tournament
    c.execute("""
        INSERT INTO tournaments (tournament_name, creator_id, max_participants, entry_fee, prize_pool, total_rounds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tournament_name, interaction.user.id, max_participants.value, entry_fee, prize_pool, total_rounds))
    
    tournament_id = c.lastrowid
    conn.commit()
    
    embed = discord.Embed(
        title="🏆 Tournament Created!",
        description=f"**{tournament_name}** is ready for registration!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Tournament ID", value=f"#{tournament_id}", inline=True)
    embed.add_field(name="Format", value=f"Single Elimination", inline=True)
    embed.add_field(name="Participants", value=f"0/{max_participants.value}", inline=True)
    embed.add_field(name="Entry Fee", value=f"${entry_fee:,}" if entry_fee > 0 else "Free", inline=True)
    embed.add_field(name="Rounds", value=str(total_rounds), inline=True)
    embed.set_footer(text=f"Use /jointournament {tournament_id} to register!")
    
    await interaction.response.send_message(embed=embed)
    conn.close()

# ============================================================================
# FINAL BATCH - UTILITY & ADMIN COMMANDS (Commands 49-54)
# ============================================================================

@bot.tree.command(name="history", description="View your race history")
@app_commands.describe(limit="Number of races to show (1-20)")
async def history(interaction: discord.Interaction, limit: int = 5):
    """Display recent race history"""
    if not 1 <= limit <= 20:
        await interaction.response.send_message("❌ Limit must be 1-20!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT track, position, points, fastest_lap, timestamp, positions_gained, pit_stops
        FROM race_history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (interaction.user.id, limit))
    
    races = c.fetchall()
    
    if not races:
        await interaction.response.send_message("❌ No race history yet!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(
        title="📜 Race History",
        description=f"Your last {len(races)} race(s)",
        color=discord.Color.blue()
    )
    
    for race in races:
        track, position, points, fastest_lap, timestamp, positions_gained, pit_stops = race
        
        # Position emoji
        if position == 1:
            pos_emoji = "🥇"
        elif position == 2:
            pos_emoji = "🥈"
        elif position == 3:
            pos_emoji = "🥉"
        else:
            pos_emoji = f"P{position}"
        
        # Positions gained
        if positions_gained > 0:
            gain_str = f"🟢 +{positions_gained}"
        elif positions_gained < 0:
            gain_str = f"🔴 {positions_gained}"
        else:
            gain_str = "⚪ =0"
        
        lap_str = f"{fastest_lap:.3f}s" if fastest_lap and fastest_lap < 999 else "N/A"
        
        embed.add_field(
            name=f"{pos_emoji} {track}",
            value=f"{gain_str} | Points: {points} | FL: {lap_str}\n"
                  f"Pits: {pit_stops} | {timestamp[:10]}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="leaderboard", description="Global leaderboards")
@app_commands.describe(category="Leaderboard category")
@app_commands.choices(category=[
    app_commands.Choice(name="💰 Richest Drivers", value="money"),
    app_commands.Choice(name="⭐ Highest Skill", value="skill"),
    app_commands.Choice(name="🏆 Most Wins", value="wins"),
    app_commands.Choice(name="🏁 Most Races", value="races"),
])
async def leaderboard(interaction: discord.Interaction, category: app_commands.Choice[str]):
    """Global leaderboards"""
    conn = db.get_conn()
    c = conn.cursor()
    
    # Map category to SQL
    category_map = {
        "money": ("money", "💰 Richest Drivers"),
        "skill": ("skill_rating", "⭐ Highest Skill"),
        "wins": ("career_wins", "🏆 Most Wins"),
        "races": ("race_starts", "🏁 Most Races"),
    }
    
    column, title = category_map[category.value]
    
    c.execute(f"""
        SELECT driver_name, {column}
        FROM users
        WHERE race_starts > 0
        ORDER BY {column} DESC
        LIMIT 15
    """)
    
    results = c.fetchall()
    
    embed = discord.Embed(
        title=f"🏆 {title}",
        description="Top 15 drivers worldwide",
        color=discord.Color.gold()
    )
    
    for idx, (name, value) in enumerate(results, 1):
        if idx <= 3:
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            rank = medals[idx]
        else:
            rank = f"**{idx}.**"
        
        # Format value based on category
        if category.value == "money":
            value_str = f"${value:,}"
        elif category.value == "skill":
            value_str = f"{value:.1f}"
        else:
            value_str = str(value)
        
        embed.add_field(
            name=f"{rank} {name}",
            value=value_str,
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="compare", description="Compare stats with another driver")
@app_commands.describe(driver="@mention a driver to compare with")
async def compare(interaction: discord.Interaction, driver: discord.User):
    """Compare stats between two drivers"""
    if driver.id == interaction.user.id:
        await interaction.response.send_message("❌ Cannot compare with yourself!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    # Get both drivers' stats
    c.execute("""
        SELECT driver_name, skill_rating, career_wins, career_podiums, career_points, 
               race_starts, money
        FROM users
        WHERE user_id IN (?, ?)
    """, (interaction.user.id, driver.id))
    
    results = c.fetchall()
    
    if len(results) != 2:
        await interaction.response.send_message("❌ One or both drivers not found!", ephemeral=True)
        conn.close()
        return
    
    # Organize data
    user1, user2 = results
    
    embed = discord.Embed(
        title="⚔️ Driver Comparison",
        description=f"**{user1[0]}** vs **{user2[0]}**",
        color=discord.Color.blue()
    )
    
    # Compare each stat
    stats = [
        ("⭐ Skill Rating", 1),
        ("🏆 Wins", 2),
        ("🥈 Podiums", 3),
        ("📊 Points", 4),
        ("🏁 Races", 5),
        ("💰 Money", 6),
    ]
    
    for stat_name, idx in stats:
        val1, val2 = user1[idx], user2[idx]
        
        if idx == 6:  # Money
            val1_str = f"${val1:,}"
            val2_str = f"${val2:,}"
        elif idx == 1:  # Skill rating
            val1_str = f"{val1:.1f}"
            val2_str = f"{val2:.1f}"
        else:
            val1_str = str(val1)
            val2_str = str(val2)
        
        # Winner indicator
        if val1 > val2:
            winner = "🟢"
            loser = "🔴"
        elif val2 > val1:
            winner = "🔴"
            loser = "🟢"
        else:
            winner = loser = "⚪"
        
        embed.add_field(
            name=stat_name,
            value=f"{winner} {val1_str} | {loser} {val2_str}",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help menu"""
    embed = discord.Embed(
        title="🏁 F1 Racing Bot - Commands",
        description="Complete command list",
        color=discord.Color.blue()
    )
    
    categories = {
        "👤 Profile & Career": [
            "`/profile` - View your driver profile",
            "`/stats` - Detailed career statistics",
            "`/daily` - Claim daily rewards",
            "`/experience` - View XP and level",
            "`/challenges` - Daily challenges",
            "`/achievements` - View achievements",
            "`/skills` - Skill tree",
            "`/upgrade` - Upgrade skills",
        ],
        "🏎️ Cars & Garage": [
            "`/garage` - View your cars",
            "`/buycar` - Purchase new car",
            "`/sellcar` - Sell a car",
            "`/setcar` - Set active car",
            "`/upgrade_car` - Upgrade components",
            "`/repair` - Repair damage",
            "`/livery` - Customize colors",
        ],
        "🏁 Racing": [
            "`/race` - Start a race",
            "`/nextlap` - Simulate next lap",
            "`/setup` - View setups",
            "`/createsetup` - Create setup",
            "`/adjustsetup` - Tune setup",
            "`/loadsetup` - Load setup",
        ],
        "💰 Economy": [
            "`/wallet` - Check balance",
            "`/shop` - Browse shop",
            "`/market` - Player marketplace",
            "`/sell` - List items for sale",
            "`/buy` - Buy from market",
            "`/loan` - Take a loan",
            "`/repay` - Repay loan",
            "`/sponsors` - View sponsors",
            "`/sign` - Sign sponsor deal",
        ],
        "🏆 Competition": [
            "`/createleague` - Create league",
            "`/leagues` - View leagues",
            "`/joinleague` - Join league",
            "`/standings` - League standings",
            "`/tournament` - Create tournament",
            "`/ranking` - Global rankings",
            "`/leaderboard` - Leaderboards",
        ],
        "📊 Stats & Info": [
            "`/history` - Race history",
            "`/compare` - Compare drivers",
            "`/help` - This menu",
        ],
    }
    
    for category, commands in categories.items():
        embed.add_field(
            name=category,
            value="\n".join(commands),
            inline=False
        )
    
    embed.set_footer(text="More commands and features coming soon!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="notify", description="Toggle race notifications")
async def notify(interaction: discord.Interaction):
    """Toggle notification preferences"""
    # This would require a notifications table
    embed = discord.Embed(
        title="🔔 Notifications",
        description="Notification settings updated!",
        color=discord.Color.green()
    )
    embed.add_field(name="Race Results", value="✅ Enabled", inline=True)
    embed.add_field(name="League Updates", value="✅ Enabled", inline=True)
    embed.add_field(name="Tournament Matches", value="✅ Enabled", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
# I'll fix the race command and add a join system where races are operated from DMs while positions/gaps show in the channel.

# ============================================================================
# RACE MANAGEMENT COMMANDS - Fixed with Join System
# ============================================================================

# Global storage for race lobbies
race_lobbies: Dict[int, Dict] = {}  # channel_id -> lobby info

@bot.tree.command(name="createrace", description="Create a race lobby")
@app_commands.describe(
    track="Track to race on",
    laps="Number of laps (5-50)",
    weather="Weather conditions",
    max_players="Max human players (1-10)"
)
@app_commands.choices(
    track=[
        app_commands.Choice(name="🇮🇹 Monza", value="Monza"),
        app_commands.Choice(name="🇲🇨 Monaco", value="Monaco"),
        app_commands.Choice(name="🇧🇪 Spa-Francorchamps", value="Spa"),
        app_commands.Choice(name="🇬🇧 Silverstone", value="Silverstone"),
        app_commands.Choice(name="🇯🇵 Suzuka", value="Suzuka"),
        app_commands.Choice(name="🇸🇬 Singapore", value="Singapore"),
        app_commands.Choice(name="🇧🇭 Bahrain", value="Bahrain"),
        app_commands.Choice(name="🇸🇦 Jeddah", value="Jeddah"),
        app_commands.Choice(name="🇺🇸 Miami", value="Miami"),
        app_commands.Choice(name="🇺🇸 Las Vegas", value="Las Vegas"),
    ],
    weather=[
        app_commands.Choice(name="☀️ Clear", value="clear"),
        app_commands.Choice(name="☁️ Cloudy", value="cloudy"),
        app_commands.Choice(name="🌦️ Light Rain", value="light_rain"),
        app_commands.Choice(name="🌧️ Rain", value="rain"),
        app_commands.Choice(name="⛈️ Heavy Rain", value="heavy_rain"),
    ]
)
async def createrace(
    interaction: discord.Interaction,
    track: app_commands.Choice[str],
    laps: int = 10,
    weather: app_commands.Choice[str] = None,
    max_players: int = 5
):
    """Create a race lobby that players can join"""
    
    # Validation
    if not 5 <= laps <= 50:
        await interaction.response.send_message("❌ Laps must be between 5-50!", ephemeral=True)
        return
    
    if not 1 <= max_players <= 10:
        await interaction.response.send_message("❌ Max players must be 1-10!", ephemeral=True)
        return
    
    # Check if lobby already exists in this channel
    if interaction.channel_id in race_lobbies:
        await interaction.response.send_message(
            "❌ A race lobby already exists in this channel! Use `/cancelrace` first.",
            ephemeral=True
        )
        return
    
    # Create lobby
    weather_condition = weather.value if weather else "clear"
    
    race_lobbies[interaction.channel_id] = {
        'creator_id': interaction.user.id,
        'track': track.value,
        'laps': laps,
        'weather': weather_condition,
        'max_players': max_players,
        'players': [],  # List of user IDs
        'started': False,
        'race_engine': None
    }
    
    embed = discord.Embed(
        title="🏁 Race Lobby Created!",
        description=f"**{track.value}** - {laps} Laps",
        color=discord.Color.green()
    )
    
    track_data = RaceEngine(track.value, laps).track_data[track.value]
    
    embed.add_field(name="🏎️ Track", value=f"{track_data['flag']} {track_data['name']}", inline=True)
    embed.add_field(name="📏 Length", value=f"{track_data['track_length_km']:.3f} km", inline=True)
    embed.add_field(name="🌦️ Weather", value=weather_condition.title(), inline=True)
    embed.add_field(name="👥 Players", value=f"0/{max_players}", inline=True)
    embed.add_field(name="📊 Laps", value=str(laps), inline=True)
    embed.add_field(name="🎮 Status", value="⏳ Waiting for players", inline=True)
    
    embed.add_field(
        name="📝 How to Join",
        value="Use `/joinrace` to join this race!",
        inline=False
    )
    
    embed.set_footer(text=f"Created by {interaction.user.display_name}")
    
@bot.tree.command(name="joinrace", description="Join an active race lobby")
async def joinrace(interaction: discord.Interaction):
    """Join the race lobby in the current channel"""
    
    if interaction.channel_id not in race_lobbies:
        await interaction.response.send_message(
            "❌ No race lobby in this channel! Use `/createrace` to create one.",
            ephemeral=True
        )
        return
    
    lobby = race_lobbies[interaction.channel_id]
    
    if lobby['started']:
        await interaction.response.send_message(
            "❌ Race already started! Wait for the next one.",
            ephemeral=True
        )
        return
    
    if interaction.user.id in lobby['players']:
        await interaction.response.send_message(
            "❌ You've already joined this race!",
            ephemeral=True
        )
        return
    
    if len(lobby['players']) >= lobby['max_players']:
        await interaction.response.send_message(
            "❌ Race lobby is full!",
            ephemeral=True
        )
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT u.user_id, u.driver_name, c.car_id
        FROM users u
        LEFT JOIN cars c ON u.user_id = c.owner_id AND c.is_active = 1
        WHERE u.user_id = ?
    """, (interaction.user.id,))
    
    user = c.fetchone()
    
    if not user:
        await interaction.response.send_message(
            "❌ Profile not found! Use `/profile` to create one first.",
            ephemeral=True
        )
        conn.close()
        return
    
    if not user[2]:
        await interaction.response.send_message(
            "❌ No active car! Use `/garage` to set your car.",
            ephemeral=True
        )
        conn.close()
        return
    
    lobby['players'].append(interaction.user.id)
    
    player_names = []
    for player_id in lobby['players']:
        c.execute("SELECT driver_name FROM users WHERE user_id = ?", (player_id,))
        result = c.fetchone()
        if result:
            player_names.append(result[0])
    
    conn.close()
    
    embed = discord.Embed(
        title="🏁 Race Lobby",
        description=f"**{lobby['track']}** - {lobby['laps']} Laps",
        color=discord.Color.blue()
    )
    
    players_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(player_names)])
    
    embed.add_field(
        name=f"👥 Players ({len(lobby['players'])}/{lobby['max_players']})",
        value=players_text,
        inline=False
    )
    
    embed.add_field(name="🌦️ Weather", value=lobby['weather'].title(), inline=True)
    embed.add_field(name="📊 Laps", value=str(lobby['laps']), inline=True)
    
    if len(lobby['players']) >= lobby['max_players']:
        embed.add_field(
            name="✅ Lobby Full!",
            value="Creator can use `/startrace` to begin!",
            inline=False
        )
        embed.color = discord.Color.green()
    elif len(lobby['players']) >= 1:
        embed.add_field(
            name="📝 Ready to Start",
            value="Creator can use `/startrace` or wait for more players",
            inline=False
        )
    
    await interaction.response.send_message(
        f"✅ **{interaction.user.display_name}** joined the race!",
        embed=embed
    )
@bot.tree.command(name="startrace", description="Start the race (creator only)")
async def startrace(interaction: discord.Interaction):
    """Start the race with all joined players"""
    
    # Check if lobby exists
    if interaction.channel_id not in race_lobbies:
        await interaction.response.send_message(
            "❌ No race lobby in this channel!",
            ephemeral=True
        )
        return
    
    lobby = race_lobbies[interaction.channel_id]
    
    # Check if user is creator
    if interaction.user.id != lobby['creator_id']:
        await interaction.response.send_message(
            "❌ Only the race creator can start the race!",
            ephemeral=True
        )
        return
    
    # Check if race already started
    if lobby['started']:
        await interaction.response.send_message(
            "❌ Race already started!",
            ephemeral=True
        )
        return
    
    # Check if there are players
    if len(lobby['players']) == 0:
        await interaction.response.send_message(
            "❌ No players have joined! Need at least 1 player.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    # Create race engine
    race_engine = RaceEngine(
        track=lobby['track'],
        laps=lobby['laps'],
        weather=lobby['weather'],
        qualifying=True
    )
    
    # Load all players
    conn = db.get_conn()
    c = conn.cursor()
    
    for player_id in lobby['players']:
        c.execute("""
            SELECT u.user_id, u.driver_name, u.skill_rating, u.aggression, u.consistency,
                   u.fatigue, u.focus, u.rain_skill, u.overtaking_skill, u.defending_skill, u.quali_skill,
                   c.engine_power, c.aero, c.handling, c.reliability, 
                   c.tyre_wear_rate, c.fuel_efficiency, c.ers_power, c.drs_efficiency, c.downforce_level
            FROM users u
            LEFT JOIN cars c ON u.user_id = c.owner_id AND c.is_active = 1
            WHERE u.user_id = ?
        """, (player_id,))
        
        user_data = c.fetchone()
        
        if not user_data:
            continue
        
        # Create car stats - handle None values
        car_stats = {
            'engine_power': user_data[11] if user_data[11] is not None else 50,
            'aero': user_data[12] if user_data[12] is not None else 50,
            'handling': user_data[13] if user_data[13] is not None else 50,
            'reliability': user_data[14] if user_data[14] is not None else 100,
            'tyre_wear_rate': user_data[15] if user_data[15] is not None else 1.0,
            'fuel_efficiency': user_data[16] if user_data[16] is not None else 1.0,
            'ers_power': user_data[17] if user_data[17] is not None else 50,
            'drs_efficiency': user_data[18] if user_data[18] is not None else 1.0,
            'downforce_level': user_data[19] if user_data[19] is not None else 50
        }
        
        advanced_stats = {
            'rain_skill': user_data[7] if user_data[7] is not None else 50,
            'overtaking_skill': user_data[8] if user_data[8] is not None else 50,
            'defending_skill': user_data[9] if user_data[9] is not None else 50,
            'quali_skill': user_data[10] if user_data[10] is not None else 50,
            'focus': user_data[6] if user_data[6] is not None else 100,
            'fatigue': user_data[5] if user_data[5] is not None else 0,
            'tyre_management': 50
        }
        
        player_driver = Driver(
            driver_id=user_data[0],
            name=user_data[1],
            skill=user_data[2] if user_data[2] is not None else 50,
            aggression=user_data[3] if user_data[3] is not None else 50,
            consistency=user_data[4] if user_data[4] is not None else 50,
            is_ai=False,
            car_stats=car_stats,
            advanced_stats=advanced_stats
        )
        
        race_engine.add_driver(player_driver)
    
    # Add AI drivers to fill grid (up to 20 total)
    ai_needed = min(20 - len(lobby['players']), 15)
    
    c.execute(f"SELECT * FROM ai_profiles ORDER BY RANDOM() LIMIT ?", (ai_needed,))
    ai_drivers = c.fetchall()
    
    for ai in ai_drivers:
        ai_car_stats = {
            'engine_power': ai[2] * 0.9,  # ai[2] is skill_rating
            'aero': ai[2] * 0.9,
            'handling': ai[2] * 0.9,
            'reliability': (ai[9] if len(ai) > 9 and ai[9] else 50) * 0.95,
            'tyre_wear_rate': 1.0,
            'fuel_efficiency': 1.0,
            'ers_power': ai[2] * 0.85,
            'drs_efficiency': 1.0,
            'downforce_level': 50
        }
        
        ai_advanced_stats = {
            'rain_skill': ai[12] if len(ai) > 12 and ai[12] else 50,
            'overtaking_skill': ai[3] if len(ai) > 3 and ai[3] else 50,
            'defending_skill': ai[4] if len(ai) > 4 and ai[4] else 50,
            'quali_skill': ai[13] if len(ai) > 13 and ai[13] else 50,
            'focus': 100,
            'fatigue': 0,
            'tyre_management': ai[14] if len(ai) > 14 and ai[14] else 50
        }
        
        ai_driver = Driver(
            driver_id=ai[0],
            name=ai[1],
            skill=ai[2],
            aggression=ai[10] if len(ai) > 10 and ai[10] else 50,
            consistency=ai[9] if len(ai) > 9 and ai[9] else 50,
            is_ai=True,
            car_stats=ai_car_stats,
            advanced_stats=ai_advanced_stats
        )
        
        race_engine.add_driver(ai_driver)
    
    conn.close()
    
    # Run qualifying
    quali_results = race_engine.run_qualifying()
    
    # Create qualifying embed for channel
    quali_embed = discord.Embed(
        title=f"🏁 {lobby['track']} - Qualifying Results",
        description=f"Grid set for {lobby['laps']} lap race",
        color=discord.Color.blue()
    )
    
    # Show top 10
    for idx, (driver, time) in enumerate(quali_results[:10], 1):
        if idx == 1:
            pos_str = "🥇 POLE"
        elif idx == 2:
            pos_str = "🥈 P2"
        elif idx == 3:
            pos_str = "🥉 P3"
        else:
            pos_str = f"**P{idx}**"
        
        gap = f"+{(time - quali_results[0][1]):.3f}s" if idx > 1 else "---"
        
        # Highlight human players
        player_indicator = "👤" if not driver.is_ai else "🤖"
        
        quali_embed.add_field(
            name=f"{pos_str} {player_indicator} {driver.name}",
            value=f"⏱️ {time:.3f}s ({gap})",
            inline=False
        )
    
    quali_embed.set_footer(text="Race starting! Check your DMs for race controls.")
    
    # Send DM to each player with controls
    players_notified = []
    players_failed = []
    
    for player_id in lobby['players']:
        try:
            user = await bot.fetch_user(player_id)
            
            # Create control panel embed
            control_embed = discord.Embed(
                title=f"🏎️ Race Controls - {lobby['track']}",
                description="Use the buttons below to control your race strategy",
                color=discord.Color.green()
            )
            
            # Get player's quali position
            player_driver = next((d for d in race_engine.drivers if d.id == player_id), None)
            if player_driver:
                control_embed.add_field(
                    name="📊 Your Grid Position",
                    value=f"P{player_driver.grid_position}",
                    inline=True
                )
            
            control_embed.add_field(
                name="📍 Track Updates",
                value=f"Follow race updates in the channel",
                inline=False
            )
            
            control_embed.set_footer(text="Buttons will appear below")
            
            # Create view with race controls
            view = RaceControlView(race_engine, player_id)
            
            await user.send(embed=control_embed, view=view)
            players_notified.append(user.display_name)
            
        except discord.Forbidden:
            players_failed.append(f"<@{player_id}>")
        except Exception as e:
            logger.error(f"Failed to send DM to {player_id}: {e}")
            players_failed.append(f"<@{player_id}>")
    
    # Store race in active races
    lobby['started'] = True
    lobby['race_engine'] = race_engine
    active_races[interaction.channel_id] = race_engine
    
    # Send qualifying results to channel
    await interaction.followup.send(embed=quali_embed)
    
    # Notify about DM status
    if players_failed:
        await interaction.followup.send(
            f"⚠️ Failed to send DMs to: {', '.join(players_failed)}\n"
            f"Please enable DMs to receive race controls!",
            ephemeral=False
        )
    
    # Send initial race status
    await asyncio.sleep(1)
    
    status_embed = discord.Embed(
        title="🏁 Race Started!",
        description="Drivers are ready on the grid!",
        color=discord.Color.green()
    )
    
    status_embed.add_field(
        name="📊 Race Information",
        value=f"Track: {lobby['track']}\nLaps: {lobby['laps']}\nWeather: {lobby['weather'].title()}",
        inline=False
    )
    
    status_embed.add_field(
        name="⚡ Next Step",
        value="Use `/nextlap` to advance the race!",
        inline=False
    )
    
    if players_notified:
        status_embed.add_field(
            name="✅ Controls Sent To",
            value=", ".join(players_notified),
            inline=False
        )
    
    await interaction.channel.send(embed=status_embed)

    # Check if already joined
    if interaction.user.id in lobby['players']:
        await interaction.response.send_message(
            "❌ You've already joined this race!",
            ephemeral=True
        )
        return
    
    # Check if lobby is full
    if len(lobby['players']) >= lobby['max_players']:
        await interaction.response.send_message(
            "❌ Race lobby is full!",
            ephemeral=True
        )
        return

@bot.tree.command(name="results", description="View final race results")
async def results(interaction: discord.Interaction):
    """Display final results and save to database"""
    
    if interaction.channel_id not in active_races:
        await interaction.response.send_message(
            "❌ No active race!",
            ephemeral=True
        )
        return
    
    race = active_races[interaction.channel_id]
    
    if race.current_lap < race.total_laps:
        await interaction.response.send_message(
            f"❌ Race not finished! {race.total_laps - race.current_lap} laps remaining.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    # Get final results
    results_text = race.get_final_results()
    
    # Create results embed
    embed = discord.Embed(
        title=f"🏆 {race.track} - Final Results",
        description=results_text[:2000],
        color=discord.Color.gold()
    )
    
    # Save results to database
    conn = db.get_conn()
    c = conn.cursor()
    
    points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    
    for driver in race.drivers:
        if driver.is_ai:
            continue
        
        # Calculate points
        points = 0
        if not driver.dnf and driver.position <= len(points_system):
            points = points_system[driver.position - 1]
        
        # Fastest lap bonus
        fastest_driver = min([d for d in race.drivers if not d.dnf], 
                            key=lambda d: d.best_lap, default=None)
        if fastest_driver and fastest_driver.id == driver.id and driver.position <= 10:
            points += 1
        
        # Money earned
        money_earned = points * 1000
        if driver.position == 1:
            money_earned += 10000
        elif driver.position == 2:
            money_earned += 5000
        elif driver.position == 3:
            money_earned += 2500
        
        # Experience
        experience_gained = 100 + (points * 50)
        
        # Save to database
        c.execute("""
            INSERT INTO race_history (
                user_id, position, points, fastest_lap, track, weather,
                grid_position, positions_gained, pit_stops, dnf, dnf_reason,
                race_time, overtakes_made, overtakes_lost, money_earned, experience_gained
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            driver.id, driver.position, points,
            driver.best_lap if driver.best_lap < 999 else None,
            race.track, race.weather, driver.grid_position,
            driver.positions_gained, driver.pit_stops,
            1 if driver.dnf else 0, driver.dnf_reason,
            driver.total_time, driver.overtakes_made, driver.overtakes_lost,
            money_earned, experience_gained
        ))
        
        # Update user stats
        c.execute("""
            UPDATE users SET
                career_points = career_points + ?,
                money = money + ?,
                experience = experience + ?,
                race_starts = race_starts + 1,
                career_wins = career_wins + ?,
                career_podiums = career_podiums + ?
            WHERE user_id = ?
        """, (
            points, money_earned, experience_gained,
            1 if driver.position == 1 and not driver.dnf else 0,
            1 if driver.position <= 3 and not driver.dnf else 0,
            driver.id
        ))
    
    conn.commit()
    conn.close()
    
    # Clean up
    del active_races[interaction.channel_id]
    if interaction.channel_id in race_lobbies:
        del race_lobbies[interaction.channel_id]
    
    embed.set_footer(text="Race complete! Create a new race with /createrace")
    
    await interaction.followup.send(embed=embed)
@bot.tree.command(name="cancelrace", description="Cancel the race lobby (creator only)")
async def cancelrace(interaction: discord.Interaction):
    """Cancel race lobby"""
    
    if interaction.channel_id not in race_lobbies:
        await interaction.response.send_message("❌ No race lobby!", ephemeral=True)
        return
    
    lobby = race_lobbies[interaction.channel_id]
    
    if interaction.user.id != lobby['creator_id']:
        await interaction.response.send_message("❌ Only creator can cancel!", ephemeral=True)
        return
    
    # Clean up
    if interaction.channel_id in active_races:
        del active_races[interaction.channel_id]
    del race_lobbies[interaction.channel_id]
    
    await interaction.response.send_message("🏁 Race cancelled!")


@bot.tree.command(name="leaverace", description="Leave the race lobby")
async def leaverace(interaction: discord.Interaction):
    """Leave race before it starts"""
    
    if interaction.channel_id not in race_lobbies:
        await interaction.response.send_message("❌ No race lobby!", ephemeral=True)
        return
    
    lobby = race_lobbies[interaction.channel_id]
    
    if lobby['started']:
        await interaction.response.send_message("❌ Race already started!", ephemeral=True)
        return
    
    if interaction.user.id not in lobby['players']:
        await interaction.response.send_message("❌ You're not in this race!", ephemeral=True)
        return
    
    lobby['players'].remove(interaction.user.id)
    
    await interaction.response.send_message(
        f"✅ **{interaction.user.display_name}** left the race!",
        ephemeral=True
    )
@bot.tree.command(name="simulate", description="Auto-simulate remaining laps")
@app_commands.describe(laps="Number of laps to simulate (1-20)")
async def simulate(interaction: discord.Interaction, laps: int = 5):
    """Simulate multiple laps at once"""
    
    if not 1 <= laps <= 20:
        await interaction.response.send_message("❌ Can simulate 1-20 laps at a time!", ephemeral=True)
        return
    
    if interaction.channel_id not in active_races:
        await interaction.response.send_message(
            "❌ No active race! Use `/race` to start one.",
            ephemeral=True
        )
        return
    
    race = active_races[interaction.channel_id]
    
    if race.current_lap >= race.total_laps:
        await interaction.response.send_message("🏁 Race already finished!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    # Simulate laps
    laps_to_simulate = min(laps, race.total_laps - race.current_lap)
    
    for _ in range(laps_to_simulate):
        race.simulate_lap()
        await asyncio.sleep(0.1)  # Small delay to prevent rate limits
    
    # Get race summary
    summary = race.get_race_summary(detailed=True)
    
    embed = discord.Embed(
        title=f"⚡ Fast Forward - Lap {race.current_lap}/{race.total_laps}",
        description=summary,
        color=discord.Color.gold()
    )
    
    # Collect all events from simulated laps
    all_events = race.events[-30:]  # Last 30 events
    if all_events:
        events_text = "\n".join(all_events)
        embed.add_field(
            name="📰 Recent Events",
            value=events_text[:1000],  # Discord limit
            inline=False
        )
    
    if race.current_lap >= race.total_laps:
        embed.set_footer(text="🏁 Race finished! Use /results for final standings.")
    else:
        embed.set_footer(text="Use /simulate or /nextlap to continue!")
    
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="raceresults", description="View final race results")
async def results(interaction: discord.Interaction):
    """Display final race results and save to database"""
    
    if interaction.channel_id not in active_races:
        await interaction.response.send_message(
            "❌ No active race! Use `/race` to start one.",
            ephemeral=True
        )
        return
    
    race = active_races[interaction.channel_id]
    
    if race.current_lap < race.total_laps:
        await interaction.response.send_message(
            f"❌ Race not finished! {race.total_laps - race.current_lap} laps remaining.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    # Get final results
    results_text = race.get_final_results()
    
    # Create results embed
    embed = discord.Embed(
        title=f"🏆 {race.track} - Final Results",
        description=results_text[:4000],  # Discord limit
        color=discord.Color.gold()
    )
    
    # Save results to database
    conn = db.get_conn()
    c = conn.cursor()
    
    # Points system
    points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    
    for driver in race.drivers:
        if driver.is_ai:
            continue  # Don't save AI results
        
        # Calculate points
        points = 0
        if not driver.dnf and driver.position <= len(points_system):
            points = points_system[driver.position - 1]
        
        # Fastest lap bonus point
        fastest_driver = min([d for d in race.drivers if not d.dnf], 
                            key=lambda d: d.best_lap, default=None)
        if fastest_driver and fastest_driver.id == driver.id and driver.position <= 10:
            points += 1
        
        # Calculate money earned
        money_earned = points * 1000  # $1000 per point
        if driver.position == 1:
            money_earned += 10000
        elif driver.position == 2:
            money_earned += 5000
        elif driver.position == 3:
            money_earned += 2500
        
        # Experience gained
        experience_gained = 100 + (points * 50)
        if driver.position == 1:
            experience_gained += 500
        
        # Save race history
        c.execute("""
            INSERT INTO race_history (
                user_id, position, points, fastest_lap, track, weather,
                grid_position, positions_gained, pit_stops, dnf, dnf_reason,
                race_time, average_lap, damage_sustained, penalties, penalty_time,
                overtakes_made, overtakes_lost, money_earned, experience_gained
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            driver.id, driver.position, points,
            driver.best_lap if driver.best_lap < 999 else None,
            race.track, race.weather, driver.grid_position,
            driver.positions_gained, driver.pit_stops,
            1 if driver.dnf else 0, driver.dnf_reason or None,
            driver.total_time, driver.total_time / race.total_laps if race.total_laps > 0 else 0,
            driver.damage, driver.penalties, driver.penalty_time,
            driver.overtakes_made, driver.overtakes_lost,
            money_earned, experience_gained
        ))
        
        # Update user stats
        c.execute("""
            UPDATE users SET
                career_points = career_points + ?,
                money = money + ?,
                experience = experience + ?,
                race_starts = race_starts + 1,
                career_wins = career_wins + ?,
                career_podiums = career_podiums + ?,
                dnf_count = dnf_count + ?,
                fastest_laps = fastest_laps + ?
            WHERE user_id = ?
        """, (
            points, money_earned, experience_gained,
            1 if driver.position == 1 and not driver.dnf else 0,
            1 if driver.position <= 3 and not driver.dnf else 0,
            1 if driver.dnf else 0,
            1 if fastest_driver and fastest_driver.id == driver.id else 0,
            driver.id
        ))
    
    conn.commit()
    conn.close()
    
    # Clean up race
    del active_races[interaction.channel_id]
    if interaction.channel_id in race_messages:
        del race_messages[interaction.channel_id]
    
    embed.set_footer(text="Race data saved! Start a new race with /race")
    
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="raceinfo", description="View current race information")
async def raceinfo(interaction: discord.Interaction):
    """Display detailed race information"""
    
    if interaction.channel_id not in active_races:
        await interaction.response.send_message(
            "❌ No active race in this channel!",
            ephemeral=True
        )
        return
    
    race = active_races[interaction.channel_id]
    
    embed = discord.Embed(
        title=f"ℹ️ Race Information - {race.track}",
        color=discord.Color.blue()
    )
    
    track_info = race.track_data[race.track]
    
    # Track details
    embed.add_field(
        name="🏁 Track",
        value=f"{track_info['flag']} {track_info['name']}\n{track_info['characteristic']}",
        inline=False
    )
    
    embed.add_field(name="📏 Length", value=f"{track_info['track_length_km']:.3f} km", inline=True)
    embed.add_field(name="🌀 Corners", value=str(track_info['corners']), inline=True)
    embed.add_field(name="💨 DRS Zones", value=str(track_info['drs_zones']), inline=True)
    
    # Race progress
    embed.add_field(
        name="📊 Progress",
        value=f"Lap {race.current_lap}/{race.total_laps}",
        inline=True
    )
    
    embed.add_field(
        name="🌦️ Weather",
        value=race.weather.title(),
        inline=True
    )
    
    embed.add_field(
        name="👥 Drivers",
        value=f"{len([d for d in race.drivers if not d.dnf])}/{len(race.drivers)} active",
        inline=True
    )
    
    # Conditions
    embed.add_field(
        name="🌡️ Track Temperature",
        value=f"{race.track_temp}°C",
        inline=True
    )
    
    embed.add_field(
        name="🏎️ Track Grip",
        value=f"{race.track_grip:.0f}%",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Track Condition",
        value=f"{race.track_condition:.0f}%",
        inline=True
    )
    
    # Flags
    flags = []
    if race.safety_car:
        flags.append("🚨 Safety Car")
    if race.virtual_safety_car:
        flags.append("🟡 VSC")
    if race.red_flag:
        flags.append("🚩 Red Flag")
    if race.drs_enabled:
        flags.append("💨 DRS Enabled")
    
    if flags:
        embed.add_field(
            name="🚩 Status",
            value="\n".join(flags),
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="endrace", description="End the current race (admin/creator only)")
async def endrace(interaction: discord.Interaction):
    """Force end the current race"""
    
    if interaction.channel_id not in active_races:
        await interaction.response.send_message(
            "❌ No active race in this channel!",
            ephemeral=True
        )
        return
    
    # Check permissions (you can add more checks here)
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ You need Manage Messages permission to end a race!",
            ephemeral=True
        )
        return
    
    # Clean up race
    del active_races[interaction.channel_id]
    if interaction.channel_id in race_messages:
        del race_messages[interaction.channel_id]
    
    embed = discord.Embed(
        title="🏁 Race Ended",
        description="The race has been terminated.",
        color=discord.Color.red()
    )
    embed.set_footer(text="Start a new race with /race")
    
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="garage", description="View your cars and garage")
async def garage(interaction: discord.Interaction):
    """Display user's car collection"""
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT car_id, car_name, car_tier, engine_power, aero, handling, 
               reliability, is_active, total_races, total_wins, car_value
        FROM cars
        WHERE owner_id = ?
        ORDER BY is_active DESC, car_value DESC
    """, (interaction.user.id,))
    
    cars = c.fetchall()
    
    if not cars:
        # Create starter car
        c.execute("""
            INSERT INTO cars (owner_id, car_name, car_tier, engine_power, aero, handling, reliability, car_value, is_active)
            VALUES (?, 'Starter F1 Car', 'budget', 55, 52, 54, 88, 50000, 1)
        """, (interaction.user.id,))
        conn.commit()
        
        embed = discord.Embed(
            title="🏎️ Your Garage",
            description="Welcome! Here's your starter car.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🟢 Starter F1 Car",
            value="⚡ Engine: 55 | 🌪️ Aero: 52 | 🎯 Handling: 54\n✅ **Active Car**",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        conn.close()
        return
    
    embed = discord.Embed(
        title="🏎️ Your Garage",
        description=f"You own {len(cars)} car(s)",
        color=discord.Color.blue()
    )
    
    for car in cars:
        car_id, name, tier, engine, aero, handling, reliability, active, races, wins, value = car
        
        tier_emoji = {
            "budget": "🟢",
            "standard": "🔵",
            "premium": "🟣",
            "elite": "🟠",
            "championship": "🔴"
        }
        
        status = "✅ **Active**" if active else ""
        
        stats = f"⚡ {engine} | 🌪️ {aero} | 🎯 {handling} | 🔧 {reliability}%"
        record = f"🏁 {races} races | 🏆 {wins} wins | 💰 ${value:,}"
        
        embed.add_field(
            name=f"{tier_emoji.get(tier, '⚪')} {name} {status}",
            value=f"{stats}\n{record}",
            inline=False
        )
    
    embed.set_footer(text="Use /setcar to change active car | /buycar to purchase new cars")
    
    await interaction.response.send_message(embed=embed)
    conn.close()


@bot.tree.command(name="wallet", description="Check your balance and finances")
async def wallet(interaction: discord.Interaction):
    """Display financial information"""
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT money, premium_currency, skill_points
        FROM users
        WHERE user_id = ?
    """, (interaction.user.id,))
    
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ Profile not found!", ephemeral=True)
        conn.close()
        return
    
    money, premium, skill_points = result
    
    # Get active loans
    c.execute("""
        SELECT SUM(remaining_amount)
        FROM loans
        WHERE user_id = ? AND status = 'active'
    """, (interaction.user.id,))
    
    debt = c.fetchone()[0] or 0
    
    # Get active sponsor contracts
    c.execute("""
        SELECT s.sponsor_name, s.payment_per_race, us.races_remaining
        FROM user_sponsors us
        JOIN sponsors s ON us.sponsor_id = s.sponsor_id
        WHERE us.user_id = ? AND us.status = 'active'
    """, (interaction.user.id,))
    
    sponsors = c.fetchall()
    
    conn.close()
    
    embed = discord.Embed(
        title="💰 Your Wallet",
        description=f"Financial Overview",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="💵 Cash", value=f"${money:,}", inline=True)
    embed.add_field(name="💎 Premium Currency", value=str(premium), inline=True)
    embed.add_field(name="🎓 Skill Points", value=str(skill_points), inline=True)
    
    if debt > 0:
        net_worth = money - debt
        embed.add_field(name="❌ Total Debt", value=f"${debt:,}", inline=True)
        embed.add_field(name="💼 Net Worth", value=f"${net_worth:,}", inline=True)
    
    if sponsors:
        sponsor_text = "\n".join([
            f"• {name}: ${payment:,}/race ({races} left)"
            for name, payment, races in sponsors
        ])
        embed.add_field(
            name="🏢 Active Sponsors",
            value=sponsor_text,
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
# This code would continue with:
# - All 100 commands across categories
# - Full race creation & management
# - Garage system with all features
# - Economy commands (wallet, market, sponsors, loans)
# - League & tournament systems
# - Achievements & skill tree
# - Setup management
# - Daily challenges
# - Admin commands

# # ============================================================================
# RUN BOT
# # ============================================================================

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')  # or 'BOT_TOKEN' — be consistent!
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable not set!")
    bot.run(token)
