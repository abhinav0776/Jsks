# F1 DISCORD RACING BOT - ULTRA COMPLETE SYSTEM
# 300+ Features, DM Race Controls, Advanced Simulation
# Compatible with Pydroid 3

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# ============================================================================
# DATABASE SYSTEM - COMPLETE
# ============================================================================

class Database:
    def __init__(self, db_name="f1_racing.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_conn(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_conn()
        c = conn.cursor()
        
        # USERS TABLE - Complete driver profiles
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            driver_name TEXT,
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
            money INTEGER DEFAULT 10000,
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
            skill_points INTEGER DEFAULT 0,
            fitness REAL DEFAULT 100.0,
            mental_strength REAL DEFAULT 50.0,
            race_craft REAL DEFAULT 50.0,
            adaptability REAL DEFAULT 50.0,
            wet_weather_master INTEGER DEFAULT 0,
            street_circuit_specialist INTEGER DEFAULT 0,
            high_speed_expert INTEGER DEFAULT 0,
            total_distance REAL DEFAULT 0.0,
            total_race_time REAL DEFAULT 0.0,
            avg_finish REAL DEFAULT 15.0,
            best_finish INTEGER DEFAULT 20,
            worst_finish INTEGER DEFAULT 20,
            team_name TEXT DEFAULT 'Independent',
            team_color TEXT DEFAULT '#FFFFFF',
            helmet_design TEXT DEFAULT 'classic',
            racing_number INTEGER DEFAULT 0,
            favorite_track TEXT DEFAULT 'Monza',
            preferred_strategy TEXT DEFAULT 'balanced',
            risk_tolerance REAL DEFAULT 50.0,
            tire_management REAL DEFAULT 50.0,
            fuel_management REAL DEFAULT 50.0,
            race_iq REAL DEFAULT 50.0,
            technical_knowledge REAL DEFAULT 50.0,
            media_presence REAL DEFAULT 50.0,
            fan_favorite_rating REAL DEFAULT 50.0,
            sponsor_appeal REAL DEFAULT 50.0,
            crash_avoidance REAL DEFAULT 50.0,
            battle_hardened INTEGER DEFAULT 0,
            championship_wins INTEGER DEFAULT 0,
            grand_slams INTEGER DEFAULT 0,
            hat_tricks INTEGER DEFAULT 0,
            royal_flush INTEGER DEFAULT 0,
            created_date TEXT,
            last_race_date TEXT,
            total_earnings INTEGER DEFAULT 10000,
            season_points INTEGER DEFAULT 0,
            season_wins INTEGER DEFAULT 0,
            season_podiums INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            loyalty_bonus REAL DEFAULT 1.0,
            vip_status INTEGER DEFAULT 0,
            premium_tier INTEGER DEFAULT 0
        )''')
        
        # CARS TABLE - Complete car system
        c.execute('''CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            car_name TEXT,
            engine_power REAL DEFAULT 50.0,
            aero REAL DEFAULT 50.0,
            handling REAL DEFAULT 50.0,
            reliability REAL DEFAULT 100.0,
            tyre_wear_rate REAL DEFAULT 1.0,
            fuel_efficiency REAL DEFAULT 1.0,
            weight_balance REAL DEFAULT 50.0,
            engine_wear REAL DEFAULT 0.0,
            gearbox_wear REAL DEFAULT 0.0,
            ers_power REAL DEFAULT 50.0,
            drs_efficiency REAL DEFAULT 1.0,
            is_active INTEGER DEFAULT 1,
            total_races INTEGER DEFAULT 0,
            total_wins INTEGER DEFAULT 0,
            downforce REAL DEFAULT 50.0,
            drag_coefficient REAL DEFAULT 1.0,
            brake_power REAL DEFAULT 50.0,
            cooling_efficiency REAL DEFAULT 50.0,
            suspension_stiffness REAL DEFAULT 50.0,
            differential_setting REAL DEFAULT 50.0,
            battery_capacity REAL DEFAULT 50.0,
            mgu_k_power REAL DEFAULT 50.0,
            mgu_h_power REAL DEFAULT 50.0,
            turbo_efficiency REAL DEFAULT 50.0,
            gearbox_ratios TEXT DEFAULT '{}',
            wing_levels TEXT DEFAULT '{}',
            car_livery TEXT DEFAULT 'default',
            car_manufacturer TEXT DEFAULT 'Custom',
            chassis_age INTEGER DEFAULT 0,
            engine_age INTEGER DEFAULT 0,
            engine_mode TEXT DEFAULT 'balanced',
            last_service_date TEXT,
            service_history TEXT DEFAULT '[]',
            upgrades_installed TEXT DEFAULT '[]',
            custom_parts TEXT DEFAULT '[]',
            telemetry_data TEXT DEFAULT '{}',
            performance_rating REAL DEFAULT 50.0,
            value INTEGER DEFAULT 50000,
            insurance_cost INTEGER DEFAULT 1000,
            maintenance_cost INTEGER DEFAULT 500,
            total_damage_history REAL DEFAULT 0.0,
            best_lap_time REAL DEFAULT 999.0,
            development_potential REAL DEFAULT 50.0,
            aero_efficiency REAL DEFAULT 50.0,
            mechanical_grip REAL DEFAULT 50.0,
            straight_line_speed REAL DEFAULT 50.0,
            corner_speed REAL DEFAULT 50.0,
            stability REAL DEFAULT 50.0,
            responsiveness REAL DEFAULT 50.0,
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )''')
        
        # AI PROFILES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS ai_profiles (
            ai_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_name TEXT,
            skill_rating REAL,
            aggression REAL,
            consistency REAL,
            overtake_skill REAL,
            defend_skill REAL,
            rain_skill REAL DEFAULT 50.0,
            quali_skill REAL DEFAULT 50.0,
            race_craft REAL DEFAULT 50.0,
            tire_management REAL DEFAULT 50.0,
            fuel_management REAL DEFAULT 50.0,
            personality TEXT DEFAULT 'balanced',
            nationality TEXT DEFAULT 'UN',
            team TEXT DEFAULT 'Independent',
            racing_number INTEGER,
            career_wins INTEGER DEFAULT 0,
            career_podiums INTEGER DEFAULT 0,
            reputation REAL DEFAULT 50.0
        )''')
        
        # RACE HISTORY TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS race_history (
            race_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            position INTEGER,
            points INTEGER,
            fastest_lap REAL,
            timestamp TEXT,
            track TEXT,
            weather TEXT,
            grid_position INTEGER,
            positions_gained INTEGER,
            pit_stops INTEGER,
            dnf INTEGER DEFAULT 0,
            dnf_reason TEXT,
            overtakes_made INTEGER DEFAULT 0,
            overtakes_lost INTEGER DEFAULT 0,
            battles_won INTEGER DEFAULT 0,
            battles_lost INTEGER DEFAULT 0,
            corners_perfect INTEGER DEFAULT 0,
            corners_mistake INTEGER DEFAULT 0,
            top_speed REAL DEFAULT 0.0,
            avg_lap_time REAL DEFAULT 0.0,
            race_time REAL DEFAULT 0.0,
            gap_to_winner REAL DEFAULT 0.0,
            gap_to_leader REAL DEFAULT 0.0,
            laps_led INTEGER DEFAULT 0,
            time_in_drs REAL DEFAULT 0.0,
            ers_deployed REAL DEFAULT 0.0,
            fuel_saved REAL DEFAULT 0.0,
            tire_strategy TEXT,
            final_tire_condition REAL DEFAULT 0.0,
            penalties_received INTEGER DEFAULT 0,
            penalty_seconds INTEGER DEFAULT 0,
            warnings_received INTEGER DEFAULT 0,
            safety_car_laps INTEGER DEFAULT 0,
            virtual_safety_car_laps INTEGER DEFAULT 0,
            race_rating REAL DEFAULT 0.0,
            consistency_rating REAL DEFAULT 0.0,
            aggression_rating REAL DEFAULT 0.0,
            defense_rating REAL DEFAULT 0.0,
            money_earned INTEGER DEFAULT 0,
            skill_xp_earned INTEGER DEFAULT 0,
            achievements_unlocked TEXT DEFAULT '[]',
            race_mode TEXT DEFAULT 'normal',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # LEAGUES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS leagues (
            league_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_name TEXT,
            creator_id INTEGER,
            created_date TEXT,
            max_drivers INTEGER DEFAULT 20,
            current_season INTEGER DEFAULT 1,
            season_races INTEGER DEFAULT 20,
            points_system TEXT DEFAULT 'standard',
            entry_fee INTEGER DEFAULT 0,
            prize_pool INTEGER DEFAULT 0,
            league_type TEXT DEFAULT 'open',
            skill_requirement REAL DEFAULT 0.0,
            min_races_required INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            description TEXT,
            rules TEXT,
            banned_users TEXT DEFAULT '[]',
            moderators TEXT DEFAULT '[]',
            sponsors TEXT DEFAULT '[]',
            league_livery TEXT DEFAULT 'default'
        )''')
        
        # LEAGUE MEMBERS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS league_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER,
            user_id INTEGER,
            join_date TEXT,
            season_points INTEGER DEFAULT 0,
            season_wins INTEGER DEFAULT 0,
            season_podiums INTEGER DEFAULT 0,
            season_poles INTEGER DEFAULT 0,
            season_fastest_laps INTEGER DEFAULT 0,
            races_completed INTEGER DEFAULT 0,
            dnf_count INTEGER DEFAULT 0,
            avg_finish REAL DEFAULT 15.0,
            best_finish INTEGER DEFAULT 20,
            points_per_race REAL DEFAULT 0.0,
            current_position INTEGER DEFAULT 0,
            peak_position INTEGER DEFAULT 20,
            constructor_points INTEGER DEFAULT 0,
            team_name TEXT,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (league_id) REFERENCES leagues(league_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # SPONSORS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
            sponsor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sponsor_name TEXT,
            payment_per_race INTEGER,
            contract_length INTEGER,
            bonus_amount INTEGER,
            sponsor_type TEXT DEFAULT 'general',
            reputation_requirement REAL DEFAULT 0.0,
            wins_requirement INTEGER DEFAULT 0,
            podiums_requirement INTEGER DEFAULT 0,
            points_requirement INTEGER DEFAULT 0,
            bonus_conditions TEXT DEFAULT '{}',
            sponsor_logo TEXT DEFAULT 'default',
            sponsor_color TEXT DEFAULT '#FFFFFF'
        )''')
        
        # USER SPONSORS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_sponsors (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sponsor_id INTEGER,
            signed_date TEXT,
            races_remaining INTEGER,
            total_earned INTEGER DEFAULT 0,
            bonuses_earned INTEGER DEFAULT 0,
            performance_multiplier REAL DEFAULT 1.0,
            contract_status TEXT DEFAULT 'active',
            auto_renew INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id)
        )''')
        
        # ACHIEVEMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS achievements (
            achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_name TEXT,
            description TEXT,
            reward_money INTEGER DEFAULT 0,
            reward_skill_points INTEGER DEFAULT 0,
            category TEXT DEFAULT 'general',
            rarity TEXT DEFAULT 'common',
            icon TEXT DEFAULT '🏆',
            unlock_condition TEXT DEFAULT '{}',
            hidden INTEGER DEFAULT 0,
            repeatable INTEGER DEFAULT 0
        )''')
        
        # USER ACHIEVEMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_id INTEGER,
            unlocked_date TEXT,
            progress REAL DEFAULT 0.0,
            times_unlocked INTEGER DEFAULT 1,
            showcase INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
        )''')
        
        # SETUPS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS setups (
            setup_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            setup_name TEXT,
            track TEXT,
            front_wing REAL DEFAULT 50.0,
            rear_wing REAL DEFAULT 50.0,
            suspension REAL DEFAULT 50.0,
            brake_balance REAL DEFAULT 50.0,
            differential REAL DEFAULT 50.0,
            anti_roll_bar_front REAL DEFAULT 50.0,
            anti_roll_bar_rear REAL DEFAULT 50.0,
            ride_height_front REAL DEFAULT 50.0,
            ride_height_rear REAL DEFAULT 50.0,
            brake_pressure REAL DEFAULT 50.0,
            tyre_pressure_fl REAL DEFAULT 50.0,
            tyre_pressure_fr REAL DEFAULT 50.0,
            tyre_pressure_rl REAL DEFAULT 50.0,
            tyre_pressure_rr REAL DEFAULT 50.0,
            camber_front REAL DEFAULT 50.0,
            camber_rear REAL DEFAULT 50.0,
            toe_front REAL DEFAULT 50.0,
            toe_rear REAL DEFAULT 50.0,
            ballast REAL DEFAULT 50.0,
            fuel_load REAL DEFAULT 100.0,
            ers_deployment TEXT DEFAULT 'balanced',
            weather_condition TEXT DEFAULT 'dry',
            notes TEXT,
            created_date TEXT,
            last_used TEXT,
            times_used INTEGER DEFAULT 0,
            avg_lap_time REAL DEFAULT 0.0,
            best_lap_time REAL DEFAULT 999.0,
            rating REAL DEFAULT 50.0,
            public INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # LOANS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS loans (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            interest_rate REAL,
            remaining_amount INTEGER,
            issue_date TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'active',
            missed_payments INTEGER DEFAULT 0,
            total_paid INTEGER DEFAULT 0,
            payment_plan TEXT DEFAULT 'standard',
            collateral TEXT DEFAULT 'none',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # TEAM CONTRACTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS team_contracts (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            team_name TEXT,
            salary_per_race INTEGER,
            bonus_per_win INTEGER,
            bonus_per_podium INTEGER,
            bonus_per_point INTEGER,
            contract_length INTEGER,
            races_remaining INTEGER,
            performance_clauses TEXT DEFAULT '{}',
            signed_date TEXT,
            status TEXT DEFAULT 'active',
            total_earned INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # PRACTICE SESSIONS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS practice_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            track TEXT,
            session_type TEXT,
            laps_completed INTEGER,
            best_lap REAL,
            avg_lap REAL,
            setup_used INTEGER,
            session_date TEXT,
            weather TEXT,
            fuel_used REAL,
            tire_wear REAL,
            ers_data TEXT DEFAULT '{}',
            telemetry TEXT DEFAULT '{}',
            skill_xp_earned INTEGER DEFAULT 0,
            money_spent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # PENALTIES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS penalties (
            penalty_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            race_id INTEGER,
            penalty_type TEXT,
            penalty_reason TEXT,
            time_penalty INTEGER DEFAULT 0,
            grid_penalty INTEGER DEFAULT 0,
            points_deduction INTEGER DEFAULT 0,
            license_points INTEGER DEFAULT 0,
            fine_amount INTEGER DEFAULT 0,
            issued_date TEXT,
            served INTEGER DEFAULT 0,
            appealed INTEGER DEFAULT 0,
            appeal_result TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # INCIDENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS incidents (
            incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_id INTEGER,
            lap_number INTEGER,
            incident_type TEXT,
            drivers_involved TEXT,
            description TEXT,
            severity TEXT,
            under_investigation INTEGER DEFAULT 0,
            penalty_issued INTEGER DEFAULT 0,
            timestamp TEXT
        )''')
        
        # WEATHER FORECASTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS weather_forecasts (
            forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
            track TEXT,
            forecast_date TEXT,
            hourly_forecast TEXT,
            temperature REAL,
            humidity REAL,
            wind_speed REAL,
            wind_direction REAL,
            precipitation_chance REAL,
            track_temp_forecast TEXT,
            grip_forecast TEXT
        )''')
        
        # TRACK RECORDS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS track_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            track TEXT,
            record_type TEXT,
            user_id INTEGER,
            record_value REAL,
            race_id INTEGER,
            set_date TEXT,
            car_used INTEGER,
            weather TEXT,
            verified INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # DAILY CHALLENGES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS daily_challenges (
            challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_name TEXT,
            description TEXT,
            challenge_type TEXT,
            target_value REAL,
            reward_money INTEGER,
            reward_xp INTEGER,
            valid_date TEXT,
            difficulty TEXT,
            completions INTEGER DEFAULT 0
        )''')
        
        # USER DAILY PROGRESS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_daily_progress (
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id INTEGER,
            current_progress REAL DEFAULT 0.0,
            completed INTEGER DEFAULT 0,
            completion_date TEXT,
            reward_claimed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (challenge_id) REFERENCES daily_challenges(challenge_id)
        )''')
        
        # MARKETPLACE TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS marketplace (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            item_type TEXT,
            item_id INTEGER,
            price INTEGER,
            listed_date TEXT,
            status TEXT DEFAULT 'active',
            views INTEGER DEFAULT 0,
            featured INTEGER DEFAULT 0,
            FOREIGN KEY (seller_id) REFERENCES users(user_id)
        )''')
        
        # TRADE HISTORY TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS trade_history (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            buyer_id INTEGER,
            item_type TEXT,
            item_id INTEGER,
            price INTEGER,
            trade_date TEXT,
            FOREIGN KEY (seller_id) REFERENCES users(user_id),
            FOREIGN KEY (buyer_id) REFERENCES users(user_id)
        )''')
        
        # NOTIFICATIONS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            notification_type TEXT,
            message TEXT,
            data TEXT DEFAULT '{}',
            read INTEGER DEFAULT 0,
            created_date TEXT,
            priority TEXT DEFAULT 'normal',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        conn.commit()
        conn.close()
        
        self.seed_ai_drivers()
        self.seed_sponsors()
        self.seed_achievements()
        self.seed_daily_challenges()
    
    def seed_ai_drivers(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ai_profiles")
        if c.fetchone()[0] == 0:
            ai_drivers = [
                ("Max Verstappen", 95, 75, 85, 90, 85, 80, 92, 90, 85, 88, "aggressive", "NL", "Red Bull Racing", 1),
                ("Lewis Hamilton", 93, 60, 90, 88, 90, 88, 94, 95, 90, 92, "smooth", "GB", "Mercedes", 44),
                ("Charles Leclerc", 88, 70, 80, 85, 80, 75, 90, 85, 80, 82, "attacking", "MC", "Ferrari", 16),
                ("Lando Norris", 85, 65, 78, 82, 78, 70, 85, 82, 78, 80, "consistent", "GB", "McLaren", 4),
                ("Carlos Sainz", 84, 55, 85, 80, 85, 72, 86, 88, 85, 84, "tactical", "ES", "Ferrari", 55),
                ("George Russell", 83, 50, 82, 78, 82, 68, 88, 83, 82, 81, "calculating", "GB", "Mercedes", 63),
                ("Fernando Alonso", 90, 80, 95, 92, 95, 92, 85, 98, 95, 94, "defensive", "ES", "Aston Martin", 14),
                ("Oscar Piastri", 80, 60, 70, 75, 70, 65, 82, 78, 72, 75, "learning", "AU", "McLaren", 81),
                ("Sergio Perez", 82, 65, 80, 76, 80, 74, 80, 80, 78, 79, "support", "MX", "Red Bull Racing", 11),
                ("Pierre Gasly", 78, 70, 72, 74, 72, 68, 79, 75, 74, 73, "hopeful", "FR", "Alpine", 10),
                ("Esteban Ocon", 77, 68, 74, 72, 74, 67, 78, 76, 75, 74, "steady", "FR", "Alpine", 31),
                ("Yuki Tsunoda", 76, 75, 65, 70, 65, 60, 77, 70, 68, 70, "wild", "JP", "AlphaTauri", 22),
                ("Lance Stroll", 72, 55, 68, 65, 70, 62, 74, 72, 70, 69, "funded", "CA", "Aston Martin", 18),
                ("Valtteri Bottas", 80, 50, 88, 75, 85, 78, 83, 85, 84, 82, "follower", "FI", "Alfa Romeo", 77),
                ("Zhou Guanyu", 70, 58, 65, 62, 68, 58, 72, 68, 66, 67, "rookie", "CN", "Alfa Romeo", 24),
                ("Kevin Magnussen", 75, 78, 70, 70, 75, 65, 76, 74, 72, 73, "aggressive", "DK", "Haas", 20),
                ("Nico Hulkenberg", 78, 62, 80, 75, 78, 72, 80, 82, 80, 79, "experienced", "DE", "Haas", 27),
                ("Alex Albon", 77, 60, 75, 72, 75, 68, 78, 76, 74, 75, "resilient", "TH", "Williams", 23),
                ("Logan Sargeant", 68, 52, 60, 58, 62, 55, 70, 65, 64, 66, "developing", "US", "Williams", 2),
                ("Daniel Ricciardo", 84, 72, 82, 85, 80, 76, 82, 86, 82, 83, "veteran", "AU", "AlphaTauri", 3),
            ]
            c.executemany('''INSERT INTO ai_profiles 
                (ai_name, skill_rating, aggression, consistency, overtake_skill, defend_skill, 
                rain_skill, quali_skill, race_craft, tire_management, fuel_management, 
                personality, nationality, team, racing_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', ai_drivers)
            conn.commit()
        conn.close()
    
    def seed_sponsors(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sponsors")
        if c.fetchone()[0] == 0:
            sponsors = [
                ("Petronas", 3000, 10, 5000, "title", 60.0, 5, 10, 100, '{"podium": 2000, "win": 5000}', "petronas", "#00D2BE"),
                ("Shell", 3500, 8, 4500, "title", 65.0, 8, 15, 150, '{"podium": 2500, "win": 6000}', "shell", "#DD1D21"),
                ("Emirates", 2000, 12, 10000, "major", 50.0, 3, 5, 50, '{"top5": 1000, "podium": 3000}', "emirates", "#FF0000"),
                ("Rolex", 1500, 15, 15000, "luxury", 70.0, 10, 20, 200, '{"pole": 2000, "fastest_lap": 1500}', "rolex", "#006039"),
                ("Pirelli", 2500, 20, 2500, "technical", 40.0, 2, 3, 30, '{"finish": 500}', "pirelli", "#FFF200"),
                ("DHL", 2000, 10, 2000, "logistics", 35.0, 0, 2, 20, '{"finish": 300}', "dhl", "#FFCC00"),
                ("Heineken", 1000, 15, 3000, "beverage", 45.0, 1, 5, 40, '{"points": 200}', "heineken", "#008200"),
                ("AWS", 2200, 10, 3000, "technology", 55.0, 5, 8, 80, '{"top10": 800}', "aws", "#FF9900"),
                ("Aramco", 4000, 6, 8000, "energy", 75.0, 12, 25, 250, '{"win": 10000, "championship": 50000}', "aramco", "#005EB8"),
                ("Monster Energy", 1800, 12, 2500, "beverage", 48.0, 2, 4, 35, '{"podium": 1500}', "monster", "#7CFC00"),
                ("Red Bull", 3200, 10, 6000, "title", 68.0, 10, 18, 180, '{"win": 7000, "podium": 3500}', "redbull", "#1E1E1E"),
                ("Tag Heuer", 1600, 14, 4000, "luxury", 52.0, 4, 7, 60, '{"pole": 1000, "fastest_lap": 1000}', "tagheuer", "#000000"),
                ("Puma", 1400, 16, 2800, "apparel", 42.0, 1, 3, 25, '{"finish": 400}', "puma", "#000000"),
                ("UBS", 1900, 11, 3500, "finance", 58.0, 6, 10, 90, '{"points": 300, "podium": 2000}', "ubs", "#E60000"),
                ("Santander", 1700, 13, 3200, "finance", 54.0, 4, 8, 70, '{"top5": 1200}', "santander", "#EC0000"),
            ]
            c.executemany('''INSERT INTO sponsors 
                (sponsor_name, payment_per_race, contract_length, bonus_amount, sponsor_type, 
                reputation_requirement, wins_requirement, podiums_requirement, points_requirement,
                bonus_conditions, sponsor_logo, sponsor_color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sponsors)
            conn.commit()
        conn.close()
    
    def seed_achievements(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM achievements")
        if c.fetchone()[0] == 0:
            achievements = [
                ("First Steps", "Complete your first race", 5000, 10, "career", "common", "🏁", '{"races": 1}', 0, 0),
                ("First Victory", "Win your first race", 10000, 25, "career", "rare", "🏆", '{"wins": 1}', 0, 0),
                ("Podium Finisher", "Finish in top 3", 5000, 15, "career", "common", "🥈", '{"podiums": 1}', 0, 0),
                ("Perfect Weekend", "Win from pole position with fastest lap", 25000, 50, "performance", "epic", "💎", '{"grand_slam": 1}', 0, 0),
                ("Comeback King", "Win after starting P10 or lower", 20000, 40, "performance", "rare", "👑", '{"comeback_win": 1}', 0, 0),
                ("Hat Trick", "Win 3 races in a row", 30000, 75, "streak", "epic", "🎩", '{"win_streak": 3}', 0, 0),
                ("Century Club", "Complete 100 races", 50000, 100, "career", "legendary", "💯", '{"races": 100}', 0, 0),
                ("Speed Demon", "Set 10 fastest laps", 15000, 30, "performance", "rare", "⚡", '{"fastest_laps": 10}', 0, 0),
                ("Wet Master", "Win 5 races in rain", 18000, 35, "specialist", "rare", "🌧️", '{"rain_wins": 5}', 0, 0),
                ("Millionaire", "Earn $1,000,000 total", 50000, 50, "wealth", "epic", "💰", '{"money": 1000000}', 0, 0),
                ("Untouchable", "Win with 30+ second gap", 20000, 40, "domination", "epic", "🚀", '{"dominant_win": 1}', 0, 0),
                ("Surgeon", "Complete a race with 0 damage", 8000, 20, "precision", "uncommon", "🏥", '{"clean_race": 1}', 0, 1),
                ("Iron Man", "Complete 10 races without DNF", 12000, 25, "reliability", "rare", "🛡️", '{"reliability_streak": 10}', 0, 0),
                ("Overtake Master", "Make 20+ overtakes in career", 10000, 20, "combat", "uncommon", "🎯", '{"overtakes": 20}', 0, 0),
                ("Defender", "Defend position for 10+ laps", 8000, 18, "combat", "uncommon", "🛡️", '{"defense": 1}', 0, 1),
                ("Pole Position", "Qualify P1", 7000, 15, "qualifying", "uncommon", "🥇", '{"poles": 1}', 0, 1),
                ("Perfect Start", "Gain 5+ positions on lap 1", 9000, 20, "starts", "uncommon", "🚦", '{"start_gain": 5}', 0, 1),
                ("Tire Whisperer", "Finish with 15%+ tire condition", 7000, 15, "management", "uncommon", "🛞", '{"tire_save": 1}', 0, 1),
                ("Fuel Saver", "Finish race with 10%+ fuel", 6000, 12, "management", "common", "⛽", '{"fuel_save": 1}', 0, 1),
                ("Strategic Genius", "Win with opposite strategy to leader", 15000, 30, "strategy", "rare", "🧠", '{"strategy_win": 1}', 0, 0),
            ]
            c.executemany('''INSERT INTO achievements 
                (achievement_name, description, reward_money, reward_skill_points, category, rarity, 
                icon, unlock_condition, hidden, repeatable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', achievements)
            conn.commit()
        conn.close()
    
    def seed_daily_challenges(self):
        conn = self.get_conn()
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        
        c.execute("SELECT COUNT(*) FROM daily_challenges WHERE valid_date = ?", (today,))
        if c.fetchone()[0] == 0:
            challenges = [
                (f"Win a Race - {today}", "Win any race today", "win", 1, 10000, 50, today, "hard"),
                (f"Top 3 Finish - {today}", "Finish in the top 3", "podium", 1, 5000, 25, today, "medium"),
                (f"Complete 3 Races - {today}", "Finish 3 races today", "races", 3, 3000, 15, today, "easy"),
                (f"Set Fastest Lap - {today}", "Set the fastest lap in any race", "fastest_lap", 1, 4000, 20, today, "medium"),
                (f"Make 10 Overtakes - {today}", "Successfully overtake 10 drivers", "overtakes", 10, 2500, 12, today, "easy"),
            ]
            c.executemany('''INSERT INTO daily_challenges 
                (challenge_name, description, challenge_type, target_value, reward_money, reward_xp, valid_date, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', challenges)
            conn.commit()
        conn.close()

# ============================================================================
# RACE ENGINE - ULTRA REALISTIC
# ============================================================================

class Driver:
    def __init__(self, driver_id, name, skill, aggression, consistency, is_ai=False, car_stats=None, advanced_stats=None):
        self.id = driver_id
        self.name = name
        self.skill = skill
        self.aggression = aggression
        self.consistency = consistency
        self.is_ai = is_ai
        
        if advanced_stats:
            self.rain_skill = advanced_stats.get('rain_skill', 50)
            self.overtaking_skill = advanced_stats.get('overtaking_skill', 50)
            self.defending_skill = advanced_stats.get('defending_skill', 50)
            self.quali_skill = advanced_stats.get('quali_skill', 50)
            self.tire_management = advanced_stats.get('tire_management', 50)
            self.fuel_management = advanced_stats.get('fuel_management', 50)
            self.race_craft = advanced_stats.get('race_craft', 50)
        else:
            self.rain_skill = 50
            self.overtaking_skill = 50
            self.defending_skill = 50
            self.quali_skill = 50
            self.tire_management = 50
            self.fuel_management = 50
            self.race_craft = 50
        
        self.car_stats = car_stats or {
            'engine_power': 50, 'aero': 50, 'handling': 50,
            'reliability': 100, 'tyre_wear_rate': 1.0,
            'fuel_efficiency': 1.0, 'ers_power': 50, 'drs_efficiency': 1.0,
            'brake_power': 50, 'cooling_efficiency': 50
        }
        
        self.position = 0
        self.grid_position = 0
        self.lap = 0
        self.total_time = 0.0
        self.gap_to_leader = 0.0
        self.gap_to_front = 0.0
        self.lap_time = 0.0
        self.best_lap = 999.0
        self.theoretical_best = 999.0
        
        self.tyre_compound = "medium"
        self.tyre_condition = 100.0
        self.tyre_age = 0
        self.tyre_temp = 80.0
        self.pit_stops = 0
        self.pit_window_open = False
        self.pit_strategy = []
        
        self.fuel_load = 100.0
        self.fuel_mix = 50
        self.fuel_per_lap = 2.0
        
        self.ers_charge = 100.0
        self.ers_mode = "balanced"
        self.ers_deployed_lap = 0.0
        self.battery_temp = 40.0
        
        self.engine_mode = "balanced"
        self.engine_temp = 90.0
        self.engine_wear_lap = 0.0
        
        self.brake_temp = [80.0, 80.0, 80.0, 80.0]
        self.brake_wear = 100.0
        
        self.drs_available = False
        self.drs_uses = 0
        self.slipstream_active = False
        
        self.push_mode = 50
        self.defending = False
        self.attacking = False
        self.in_battle = False
        self.battle_partner = None
        
        self.dnf = False
        self.dnf_reason = ""
        self.damage = 0.0
        self.damage_locations = {"front_wing": 0, "rear_wing": 0, "floor": 0, "suspension": 0}
        self.penalties = 0
        self.penalty_time = 0
        self.warnings = 0
        
        self.overtakes_made = 0
        self.overtakes_lost = 0
        self.positions_gained = 0
        self.laps_led = 0
        self.battles_won = 0
        self.battles_lost = 0
        
        self.mistakes_count = 0
        self.perfect_corners = 0
        self.lock_ups = 0
        self.spins = 0
        
        self.sector_times = [0.0, 0.0, 0.0]
        self.sector_bests = [999.0, 999.0, 999.0]
        
        self.focus = 100.0
        self.fatigue = 0.0
        self.confidence = 50.0
        
        self.radio_messages = []
        self.team_orders = None
        
        self.dm_channel_id = None
        self.last_dm_update = 0

class RaceEngine:
    def __init__(self, track="Monza", laps=15, weather="clear", qualifying=True, race_mode="normal"):
        self.track = track
        self.total_laps = laps
        self.current_lap = 0
        self.weather = weather
        self.track_temp = 30
        self.air_temp = 25
        self.humidity = 50
        self.wind_speed = 5
        self.track_grip = 100.0
        self.track_evolution = 0.0
        self.rubbered_in = False
        
        self.safety_car = False
        self.virtual_safety_car = False
        self.safety_car_laps = 0
        self.vsc_laps = 0
        self.red_flag = False
        
        self.drs_enabled = False
        self.drs_zones = 2
        
        self.qualifying_mode = qualifying
        self.race_mode = race_mode
        self.race_started = False
        self.race_finished = False
        
        self.drivers: List[Driver] = []
        self.events = []
        self.lap_events = []
        self.sector_events = []
        self.incidents = []
        
        self.marshals_active = False
        self.debris_on_track = False
        
        self.pit_lane_open = True
        self.pit_lane_speed_limit = 80
        
        self.track_data = {
            "Monza": {
                "name": "Autodromo Nazionale di Monza",
                "country": "🇮🇹 Italy",
                "length": 5.793,
                "corners": 11,
                "base_lap_time": 80.0,
                "overtake_difficulty": 30,
                "tyre_wear": 1.0,
                "fuel_usage": 1.1,
                "characteristic": "High Speed Temple",
                "drs_zones": 2,
                "elevation_change": 15,
                "avg_speed": 264,
                "sector_lengths": [0.30, 0.35, 0.35],
                "key_corners": ["Variante del Rettifilo", "Curva di Lesmo", "Parabolica"]
            },
            "Monaco": {
                "name": "Circuit de Monaco",
                "country": "🇲🇨 Monaco",
                "length": 3.337,
                "corners": 19,
                "base_lap_time": 72.0,
                "overtake_difficulty": 90,
                "tyre_wear": 0.7,
                "fuel_usage": 0.85,
                "characteristic": "Street Circuit Jewel",
                "drs_zones": 1,
                "elevation_change": 42,
                "avg_speed": 160,
                "sector_lengths": [0.33, 0.33, 0.34],
                "key_corners": ["Sainte Devote", "Swimming Pool", "Rascasse"]
            },
            "Spa": {
                "name": "Circuit de Spa-Francorchamps",
                "country": "🇧🇪 Belgium",
                "length": 7.004,
                "corners": 19,
                "base_lap_time": 105.0,
                "overtake_difficulty": 40,
                "tyre_wear": 1.2,
                "fuel_usage": 1.15,
                "characteristic": "Ardennes Roller Coaster",
                "drs_zones": 2,
                "elevation_change": 104,
                "avg_speed": 237,
                "sector_lengths": [0.35, 0.30, 0.35],
                "key_corners": ["Eau Rouge", "Pouhon", "Blanchimont"]
            },
            "Silverstone": {
                "name": "Silverstone Circuit",
                "country": "🇬🇧 Great Britain",
                "length": 5.891,
                "corners": 18,
                "base_lap_time": 88.0,
                "overtake_difficulty": 50,
                "tyre_wear": 1.1,
                "fuel_usage": 1.05,
                "characteristic": "High Speed Challenge",
                "drs_zones": 2,
                "elevation_change": 18,
                "avg_speed": 241,
                "sector_lengths": [0.32, 0.36, 0.32],
                "key_corners": ["Maggotts-Becketts", "Copse", "Stowe"]
            },
            "Suzuka": {
                "name": "Suzuka International Racing Course",
                "country": "🇯🇵 Japan",
                "length": 5.807,
                "corners": 18,
                "base_lap_time": 90.0,
                "overtake_difficulty": 60,
                "tyre_wear": 1.15,
                "fuel_usage": 1.08,
                "characteristic": "Technical Figure-8",
                "drs_zones": 1,
                "elevation_change": 45,
                "avg_speed": 232,
                "sector_lengths": [0.34, 0.33, 0.33],
                "key_corners": ["130R", "Spoon Curve", "Degner"]
            },
            "Singapore": {
                "name": "Marina Bay Street Circuit",
                "country": "🇸🇬 Singapore",
                "length": 4.940,
                "corners": 23,
                "base_lap_time": 95.0,
                "overtake_difficulty": 70,
                "tyre_wear": 0.9,
                "fuel_usage": 0.95,
                "characteristic": "Night Street Challenge",
                "drs_zones": 3,
                "elevation_change": 23,
                "avg_speed": 187,
                "sector_lengths": [0.33, 0.34, 0.33],
                "key_corners": ["Turn 1", "Singapore Sling", "Anderson Bridge"]
            },
            "Interlagos": {
                "name": "Autódromo José Carlos Pace",
                "country": "🇧🇷 Brazil",
                "length": 4.309,
                "corners": 15,
                "base_lap_time": 70.0,
                "overtake_difficulty": 45,
                "tyre_wear": 1.05,
                "fuel_usage": 1.0,
                "characteristic": "Anti-Clockwise Classic",
                "drs_zones": 2,
                "elevation_change": 45,
                "avg_speed": 222,
                "sector_lengths": [0.30, 0.40, 0.30],
                "key_corners": ["Senna S", "Descida do Lago", "Juncao"]
            },
            "Austin": {
                "name": "Circuit of the Americas",
                "country": "🇺🇸 USA",
                "length": 5.513,
                "corners": 20,
                "base_lap_time": 92.0,
                "overtake_difficulty": 48,
                "tyre_wear": 1.08,
                "fuel_usage": 1.06,
                "characteristic": "Modern American Classic",
                "drs_zones": 2,
                "elevation_change": 41,
                "avg_speed": 215,
                "sector_lengths": [0.35, 0.32, 0.33],
                "key_corners": ["Turn 1", "Esses", "Turn 19"]
            },
        }
        
        if track not in self.track_data:
            self.track = "Monza"
        
        self.weather_forecast = [weather] * (laps + 1)
        self.generate_weather_forecast()
        
        self.race_control_channel = None
        self.dm_messages = {}
    
    def generate_weather_forecast(self):
        weather_states = ["clear", "partly_cloudy", "cloudy", "light_rain", "rain", "heavy_rain"]
        weather_transitions = {
            "clear": {"clear": 0.7, "partly_cloudy": 0.25, "cloudy": 0.05},
            "partly_cloudy": {"clear": 0.2, "partly_cloudy": 0.5, "cloudy": 0.25, "light_rain": 0.05},
            "cloudy": {"partly_cloudy": 0.15, "cloudy": 0.5, "light_rain": 0.3, "rain": 0.05},
            "light_rain": {"cloudy": 0.2, "light_rain": 0.4, "rain": 0.35, "heavy_rain": 0.05},
            "rain": {"light_rain": 0.25, "rain": 0.5, "heavy_rain": 0.2, "cloudy": 0.05},
            "heavy_rain": {"rain": 0.6, "heavy_rain": 0.35, "light_rain": 0.05}
        }
        
        for i in range(1, len(self.weather_forecast)):
            current = self.weather_forecast[i-1]
            if current in weather_transitions:
                choices = list(weather_transitions[current].keys())
                weights = list(weather_transitions[current].values())
                self.weather_forecast[i] = random.choices(choices, weights=weights)[0]
        
        self.update_weather_conditions()
    
    def update_weather_conditions(self):
        weather_temps = {
            "clear": (28, 35),
            "partly_cloudy": (24, 30),
            "cloudy": (20, 26),
            "light_rain": (18, 24),
            "rain": (16, 22),
            "heavy_rain": (14, 20)
        }
        
        weather_grip = {
            "clear": 100,
            "partly_cloudy": 98,
            "cloudy": 95,
            "light_rain": 65,
            "rain": 50,
            "heavy_rain": 35
        }
        
        if self.weather in weather_temps:
            self.track_temp = random.uniform(*weather_temps[self.weather])
            self.track_grip = weather_grip[self.weather] + self.track_evolution
    
    def add_driver(self, driver: Driver):
        self.drivers.append(driver)
        driver.position = len(self.drivers)
        driver.grid_position = len(self.drivers)
    
    def run_qualifying(self):
        results = []
        
        for driver in self.drivers:
            if driver.dnf:
                continue
            
            base_time = self.track_data[self.track]["base_lap_time"]
            
            skill_factor = (driver.skill * 0.4 + driver.quali_skill * 0.6) / 100
            car_factor = (
                driver.car_stats['engine_power'] * 0.35 +
                driver.car_stats['aero'] * 0.30 +
                driver.car_stats['handling'] * 0.25 +
                driver.car_stats['ers_power'] * 0.10
            ) / 100
            
            quali_time = base_time * (1 - skill_factor * 0.18 - car_factor * 0.12)
            
            consistency_var = (100 - driver.consistency) / 150
            quali_time += random.uniform(-consistency_var, consistency_var)
            
            tire_factor = random.uniform(-0.15, 0.05)
            quali_time += tire_factor
            
            track_evolution = len(results) * 0.002
            quali_time -= track_evolution
            
            quali_time += random.uniform(-0.3, 0.3)
            
            results.append((driver, quali_time))
        
        results.sort(key=lambda x: x[1])
        
        for idx, (driver, time) in enumerate(results):
            driver.grid_position = idx + 1
            driver.position = idx + 1
            
            if idx == 0:
                self.events.append(f"🏁 **POLE POSITION:** {driver.name} - {time:.3f}s")
            elif idx == 1:
                gap = time - results[0][1]
                self.events.append(f"🥈 **P2:** {driver.name} - +{gap:.3f}s")
            elif idx == 2:
                gap = time - results[0][1]
                self.events.append(f"🥉 **P3:** {driver.name} - +{gap:.3f}s")
        
        return results
    
    def calculate_dps(self, driver: Driver) -> float:
        base_skill = driver.skill
        
        if "rain" in self.weather:
            weather_skill = driver.rain_skill
            base_skill = (base_skill * 0.4 + weather_skill * 0.6)
        
        tire_skill = driver.tire_management
        fuel_skill = driver.fuel_management
        
        driver_factor = (
            base_skill * 0.35 +
            driver.race_craft * 0.15 +
            tire_skill * 0.10 +
            fuel_skill * 0.05
        ) * 0.30
        
        car_perf = (
            driver.car_stats['engine_power'] * 0.30 +
            driver.car_stats['aero'] * 0.25 +
            driver.car_stats['handling'] * 0.20 +
            driver.car_stats['ers_power'] * 0.15 +
            driver.car_stats['brake_power'] * 0.10
        )
        car_factor = car_perf * 0.35
        
        tire_temp_optimal = abs(driver.tyre_temp - 90) < 10
        tire_factor = (
            driver.tyre_condition * 0.7 +
            (100 if tire_temp_optimal else 70) * 0.3
        ) * 0.15
        
        grip_factor = self.track_grip * 0.08
        
        weather_factor = 50.0
        if "rain" in self.weather:
            if driver.tyre_compound in ["inter", "wet"]:
                weather_factor = driver.rain_skill * 1.2
            else:
                weather_factor = 15.0
        elif driver.tyre_compound in ["inter", "wet"] and self.weather == "clear":
            weather_factor = 20.0
        weather_factor *= 0.07
        
        strategy_bonus = (
            driver.push_mode * 0.5 +
            driver.fuel_mix * 0.3 +
            (driver.engine_mode == "overtake" and 20 or 0) * 0.2
        ) * 0.03
        
        damage_penalty = sum(driver.damage_locations.values()) * 0.02
        total_damage = driver.damage * 0.10
        
        fatigue_penalty = driver.fatigue * 0.05
        focus_bonus = (driver.focus / 100) * 5
        confidence_bonus = (driver.confidence / 100) * 3
        
        dps = (
            driver_factor + car_factor + tire_factor + grip_factor +
            weather_factor + strategy_bonus + focus_bonus + confidence_bonus -
            damage_penalty - total_damage - fatigue_penalty
        )
        
        variation_range = driver.consistency / 8
        variation = random.uniform(-variation_range, variation_range)
        
        if driver.ers_mode == "deploy" and driver.ers_charge > 10:
            dps += random.uniform(4, 7)
            driver.battery_temp += 2
        
        if driver.drs_available and not "rain" in self.weather:
            dps += random.uniform(2.5, 4.5) * driver.car_stats['drs_efficiency']
        
        if driver.slipstream_active:
            dps += random.uniform(1.5, 3.0)
        
        if driver.in_battle:
            battle_skill = (driver.overtaking_skill if driver.attacking else driver.defending_skill) / 100
            dps += battle_skill * random.uniform(-2, 3)
        
        if driver.engine_temp > 105:
            dps -= random.uniform(2, 5)
        
        return max(0, dps + variation)
    
    async def simulate_lap(self, bot):
        self.current_lap += 1
        self.lap_events = []
        self.sector_events = []
        
        if self.current_lap < len(self.weather_forecast):
            new_weather = self.weather_forecast[self.current_lap]
            if new_weather != self.weather:
                old_weather = self.weather
                self.weather = new_weather
                self.update_weather_conditions()
                
                weather_emoji = {
                    "clear": "☀️", "partly_cloudy": "⛅", "cloudy": "☁️",
                    "light_rain": "🌦️", "rain": "🌧️", "heavy_rain": "⛈️"
                }
                
                self.lap_events.append(
                    f"🌦️ **WEATHER CHANGE:** {weather_emoji.get(old_weather, '')} → "
                    f"{weather_emoji.get(new_weather, '')} {new_weather.replace('_', ' ').title()}"
                )
                
                if "rain" in new_weather and "rain" not in old_weather:
                    self.lap_events.append("⚠️ **TRACK IS GETTING WET** - Drivers may pit for inters/wets")
        
        if self.current_lap >= 3 and not self.safety_car:
            if not self.drs_enabled:
                self.drs_enabled = True
                self.lap_events.append("💨 **DRS ENABLED**")
        
        self.track_evolution = min(15, self.current_lap * 0.5)
        if self.current_lap > 10 and not self.rubbered_in:
            self.rubbered_in = True
            self.lap_events.append("🏁 Track is now fully rubbered in - Grip improved")
        
        for driver in self.drivers:
            if driver.dnf:
                continue
            
            driver.lap = self.current_lap
            
            lap_time = self.calculate_lap_time(driver)
            driver.lap_time = lap_time
            driver.total_time += lap_time
            
            if lap_time < driver.best_lap and not self.safety_car:
                driver.best_lap = lap_time
                if self.current_lap > 3:
                    self.lap_events.append(
                        f"⏱️ **FASTEST LAP:** {driver.name} - {lap_time:.3f}s "
                        f"(Avg: {lap_time/3:.3f}s/sector)"
                    )
            
            if driver.position == 1:
                driver.laps_led += 1
            
            self.update_tyre_wear(driver)
            self.update_tyre_temperature(driver)
            self.update_fuel(driver)
            self.update_ers(driver)
            self.update_engine(driver)
            self.update_brakes(driver)
            self.update_driver_condition(driver)
            
            driver.tyre_age += 1
            
            await self.check_incidents(driver)
            
            self.check_pit_window(driver)
        
        self.update_positions()
        self.update_drs()
        self.update_slipstream()
        await self.simulate_overtakes()
        self.ai_strategy_decisions()
        self.check_safety_car()
        self.update_positions()
        
        self.events.extend(self.lap_events)
        
        await self.send_dm_updates(bot)
    
    def calculate_lap_time(self, driver: Driver) -> float:
        base_time = self.track_data[self.track]["base_lap_time"]
        dps = self.calculate_dps(driver)
        
        lap_time = base_time - (dps / 10)
        
        fuel_bonus = (100 - driver.fuel_load) * 0.018
        lap_time -= fuel_bonus
        
        if self.safety_car:
            lap_time = base_time + random.uniform(18, 25)
        elif self.virtual_safety_car:
            lap_time = base_time + random.uniform(8, 12)
        
        lap_time += driver.damage * 0.06
        
        if driver.penalty_time > 0:
            lap_time += 5
            driver.penalty_time = 0
            self.lap_events.append(f"⏱️ {driver.name} serves 5s time penalty")
        
        lap_time += random.uniform(-0.4, 0.4)
        
        sector_split = self.track_data[self.track]["sector_lengths"]
        for idx, split in enumerate(sector_split):
            sector_time = lap_time * split
            driver.sector_times[idx] = sector_time
            if sector_time < driver.sector_bests[idx]:
                driver.sector_bests[idx] = sector_time
        
        return max(base_time * 0.75, lap_time)
    
    def update_tyre_wear(self, driver: Driver):
        base_wear = self.track_data[self.track]["tyre_wear"]
        
        compound_wear = {
            "soft": 4.5, "medium": 2.8, "hard": 1.6,
            "inter": 3.2, "wet": 2.8
        }
        
        compound = compound_wear.get(driver.tyre_compound, 2.8)
        
        temp_factor = 1.0
        if driver.tyre_temp > 110:
            temp_factor = 1.5
        elif driver.tyre_temp < 70:
            temp_factor = 1.3
        
        management_factor = (100 - driver.tire_management) / 100
        
        wear = (
            base_wear * compound * driver.car_stats['tyre_wear_rate'] *
            (driver.push_mode / 50) * temp_factor *
            (self.track_temp / 30) * (1 + management_factor * 0.3)
        )
        
        if driver.attacking or driver.defending:
            wear *= 1.25
        
        if driver.lock_ups > 0:
            wear *= 1.1
        
        if "rain" in self.weather and driver.tyre_compound in ["soft", "medium", "hard"]:
            wear *= 2.5
        
        driver.tyre_condition = max(0, driver.tyre_condition - wear)
    
    def update_tyre_temperature(self, driver: Driver):
        target_temp = 90
        
        if driver.push_mode > 70:
            target_temp = 100
        elif driver.push_mode < 30:
            target_temp = 80
        
        if self.safety_car or self.virtual_safety_car:
            target_temp = 70
        
        temp_change = (target_temp - driver.tyre_temp) * 0.3
        driver.tyre_temp = max(60, min(120, driver.tyre_temp + temp_change + random.uniform(-2, 2)))
    
    def update_fuel(self, driver: Driver):
        base_consumption = self.track_data[self.track]["fuel_usage"]
        
        consumption = (
            base_consumption * (driver.fuel_mix / 50) * 
            (driver.push_mode / 50) * driver.car_stats['fuel_efficiency']
        )
        
        if driver.engine_mode == "overtake":
            consumption *= 1.3
        elif driver.engine_mode == "eco":
            consumption *= 0.7
        
        if self.safety_car:
            consumption *= 0.25
        elif self.virtual_safety_car:
            consumption *= 0.5
        
        management_bonus = driver.fuel_management / 200
        consumption *= (1 - management_bonus)
        
        driver.fuel_load = max(0, driver.fuel_load - consumption)
        driver.fuel_per_lap = consumption
        
        if driver.fuel_load < 5 and not driver.dnf:
            driver.dnf = True
            driver.dnf_reason = "Out of Fuel"
            self.lap_events.append(f"⛽ **{driver.name} - OUT OF FUEL!**")
    
    def update_ers(self, driver: Driver):
        if driver.ers_mode == "charging":
            charge_rate = 18 + (driver.car_stats['battery_capacity'] / 10)
            driver.ers_charge = min(100, driver.ers_charge + charge_rate)
            driver.battery_temp = max(35, driver.battery_temp - 1.5)
        elif driver.ers_mode == "deploy":
            if driver.ers_charge >= 12:
                deploy_amount = 12 + random.uniform(-2, 2)
                driver.ers_charge -= deploy_amount
                driver.ers_deployed_lap += deploy_amount
                driver.battery_temp += 2.5
            else:
                driver.ers_mode = "balanced"
        else:
            charge_rate = 10
            driver.ers_charge = min(100, driver.ers_charge + charge_rate)
            driver.battery_temp = max(40, driver.battery_temp - 0.5)
        
        if driver.battery_temp > 80:
            driver.ers_charge -= 5
            if not driver.is_ai:
                driver.radio_messages.append("⚠️ Battery overheating! ERS limited")
    
    def update_engine(self, driver: Driver):
        if driver.engine_mode == "overtake":
            driver.engine_temp += random.uniform(1.5, 3.0)
            driver.engine_wear_lap += 0.15
        elif driver.engine_mode == "eco":
            driver.engine_temp = max(85, driver.engine_temp - 1.0)
            driver.engine_wear_lap += 0.03
        else:
            temp_change = random.uniform(-0.5, 1.0)
            driver.engine_temp += temp_change
            driver.engine_wear_lap += 0.08
        
        cooling = driver.car_stats['cooling_efficiency'] / 100
        driver.engine_temp = max(85, driver.engine_temp - (cooling * 2))
        
        if driver.engine_temp > 115:
            if random.random() < 0.05:
                driver.dnf = True
                driver.dnf_reason = "Engine Overheating"
                self.lap_events.append(f"🔥 **{driver.name} - ENGINE FAILURE!** (Overheating)")
    
    def update_brakes(self, driver: Driver):
        for i in range(4):
            if driver.push_mode > 70:
                driver.brake_temp[i] += random.uniform(2, 5)
            else:
                driver.brake_temp[i] = max(80, driver.brake_temp[i] - random.uniform(1, 3))
            
            driver.brake_temp[i] = max(60, min(800, driver.brake_temp[i]))
        
        if any(temp > 700 for temp in driver.brake_temp):
            driver.brake_wear -= random.uniform(3, 6)
            if driver.brake_wear < 20 and random.random() < 0.08:
                driver.damage_locations["suspension"] += random.uniform(10, 25)
                if not driver.is_ai:
                    driver.radio_messages.append("🚨 Brake failure! Box box!")
    
    def update_driver_condition(self, driver: Driver):
        base_fatigue = 0.3
        
        if "rain" in self.weather:
            base_fatigue *= 1.5
        
        if driver.in_battle:
            base_fatigue *= 1.3
        
        if self.track == "Singapore" or self.track == "Monaco":
            base_fatigue *= 1.2
        
        driver.fatigue = min(100, driver.fatigue + base_fatigue)
        
        driver.focus = max(60, 100 - (driver.fatigue * 0.4))
        
        if driver.position <= 3:
            driver.confidence = min(100, driver.confidence + 0.5)
        elif driver.position > driver.grid_position + 3:
            driver.confidence = max(20, driver.confidence - 0.3)
        
        if driver.mistakes_count > 3:
            driver.focus -= 5
    
    def check_pit_window(self, driver: Driver):
        laps_remaining = self.total_laps - self.current_lap
        
        if driver.tyre_age > 8:
            driver.pit_window_open = True
        
        if driver.tyre_condition < 25:
            driver.pit_window_open = True
        
        if laps_remaining < 5:
            driver.pit_window_open = False
    
    def update_track_conditions(self):
        if self.weather == "clear":
            self.track_grip = min(100, self.track_grip + 0.5 + self.track_evolution)
        elif self.weather == "partly_cloudy":
            self.track_grip = 98 + self.track_evolution
        elif self.weather == "cloudy":
            self.track_grip = 95 + self.track_evolution
        elif self.weather == "light_rain":
            self.track_grip = max(40, 65 - (self.current_lap * 0.5))
        elif self.weather == "rain":
            self.track_grip = max(35, 50 - (self.current_lap * 0.3))
        elif self.weather == "heavy_rain":
            self.track_grip = max(25, 35 - (self.current_lap * 0.2))
    
    def update_drs(self):
        if not self.drs_enabled or self.safety_car or self.virtual_safety_car:
            for driver in self.drivers:
                driver.drs_available = False
            return
        
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            driver = sorted_drivers[i]
            
            gap_threshold = 1.0
            if self.track in ["Monza", "Spa"]:
                gap_threshold = 1.2
            
            if driver.gap_to_front < gap_threshold:
                driver.drs_available = True
                driver.drs_uses += 1
            else:
                driver.drs_available = False
    
    def update_slipstream(self):
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            driver = sorted_drivers[i]
            
            if driver.gap_to_front < 0.5:
                driver.slipstream_active = True
            else:
                driver.slipstream_active = False
    
    async def simulate_overtakes(self):
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            attacker = sorted_drivers[i]
            defender = sorted_drivers[i-1]
            
            if attacker.gap_to_front > 2.0 or self.safety_car or self.virtual_safety_car:
                attacker.in_battle = False
                defender.in_battle = False
                continue
            
            if attacker.gap_to_front < 0.8:
                attacker.in_battle = True
                defender.in_battle = True
                attacker.battle_partner = defender.name
                defender.battle_partner = attacker.name
                attacker.attacking = True
                defender.defending = True
            
            if attacker.gap_to_front < 0.3:
                overtake_chance = self.calculate_overtake_chance(attacker, defender)
                
                if random.random() * 100 < overtake_chance:
                    await self.execute_overtake(attacker, defender)
    
    def calculate_overtake_chance(self, attacker: Driver, defender: Driver) -> float:
        base_chance = 100 - self.track_data[self.track]["overtake_difficulty"]
        
        attacker_dps = self.calculate_dps(attacker)
        defender_dps = self.calculate_dps(defender)
        skill_diff = (attacker_dps - defender_dps) * 2.5
        
        drs_bonus = 28 if attacker.drs_available else 0
        ers_bonus = 18 if attacker.ers_charge > 60 else 8 if attacker.ers_charge > 30 else 0
        
        tire_diff = (attacker.tyre_condition - defender.tyre_condition) * 0.35
        
        slipstream_bonus = 12 if attacker.slipstream_active else 0
        
        attacker_skill = attacker.overtaking_skill / 100
        defender_skill = defender.defending_skill / 100
        skill_bonus = (attacker_skill - defender_skill) * 15
        
        aggression_factor = (attacker.aggression / 100) * 8
        
        chance = (
            base_chance + skill_diff + drs_bonus + ers_bonus + 
            tire_diff + slipstream_bonus + skill_bonus + aggression_factor
        )
        
        if "rain" in self.weather:
            rain_skill_diff = (attacker.rain_skill - defender.rain_skill) * 0.3
            chance += rain_skill_diff
        
        return max(3, min(97, chance))
    
    async def execute_overtake(self, attacker: Driver, defender: Driver):
        outcomes = ["clean", "side_by_side", "dive_bomb", "contact", "failed"]
        
        if "rain" in self.weather:
            weights = [35, 25, 15, 18, 7]
        else:
            weights = [55, 25, 10, 8, 2]
        
        if attacker.aggression > 70:
            weights[2] += 10
            weights[0] -= 5
        
        outcome = random.choices(outcomes, weights=weights)[0]
        
        if outcome == "clean":
            old_pos = attacker.position
            attacker.position, defender.position = defender.position, attacker.position
            attacker.overtakes_made += 1
            defender.overtakes_lost += 1
            attacker.battles_won += 1
            defender.battles_lost += 1
            attacker.confidence = min(100, attacker.confidence + 2)
            defender.confidence = max(30, defender.confidence - 1)
            
            self.lap_events.append(
                f"🎯 **OVERTAKE!** {attacker.name} passes {defender.name} for P{old_pos-1} (Clean move)"
            )
            attacker.attacking = False
            defender.defending = False
            attacker.in_battle = False
            defender.in_battle = False
        
        elif outcome == "side_by_side":
            if random.random() < 0.6:
                old_pos = attacker.position
                attacker.position, defender.position = defender.position, attacker.position
                attacker.overtakes_made += 1
                defender.overtakes_lost += 1
                self.lap_events.append(
                    f"⚔️ **BATTLE!** {attacker.name} edges past {defender.name} for P{old_pos-1}"
                )
            else:
                self.lap_events.append(
                    f"⚔️ **WHEEL TO WHEEL!** {attacker.name} vs {defender.name} - {defender.name} holds position"
                )
        
        elif outcome == "dive_bomb":
            if random.random() < 0.5:
                old_pos = attacker.position
                attacker.position, defender.position = defender.position, attacker.position
                attacker.overtakes_made += 1
                defender.overtakes_lost += 1
                self.lap_events.append(
                    f"💥 **AGGRESSIVE!** {attacker.name} dive-bombs {defender.name} for P{old_pos-1}"
                )
                
                if random.random() < 0.3:
                    attacker.warnings += 1
                    self.lap_events.append(f"⚠️ {attacker.name} - Warning for aggressive driving")
            else:
                minor_damage = random.uniform(3, 8)
                attacker.damage += minor_damage
                self.lap_events.append(
                    f"💥 **DIVE FAILED!** {attacker.name} locks up - Minor damage"
                )
        
        elif outcome == "contact":
            damage = random.uniform(8, 25)
            attacker.damage += damage
            defender.damage += damage * 0.6
            
            damage_location = random.choice(["front_wing", "rear_wing", "floor", "suspension"])
            attacker.damage_locations[damage_location] += damage
            
            self.lap_events.append(
                f"💥 **CONTACT!** {attacker.name} and {defender.name} collide! "
                f"Damage: {attacker.name} ({damage:.0f}%) {defender.name} ({damage*0.6:.0f}%)"
            )
            
            self.incidents.append({
                "lap": self.current_lap,
                "type": "collision",
                "drivers": [attacker.name, defender.name],
                "severity": "medium" if damage < 15 else "high"
            })
            
            if random.random() < 0.6:
                penalty_type = random.choice(["5s", "10s"])
                if penalty_type == "5s":
                    attacker.penalty_time += 5
                else:
                    attacker.penalty_time += 10
                self.lap_events.append(f"⚠️ {attacker.name} - {penalty_type} time penalty for causing collision")
        
        elif outcome == "failed":
            self.lap_events.append(
                f"🔄 {attacker.name} attempts a move on {defender.name} but can't make it stick"
            )
    
    async def check_incidents(self, driver: Driver):
        crash_chance = 0.25
        
        crash_chance += (100 - driver.tyre_condition) * 0.025
        crash_chance += (driver.push_mode / 100) * 0.4
        crash_chance += (driver.damage / 100) * 0.8
        crash_chance += (driver.fatigue / 100) * 0.5
        crash_chance += (1 - driver.focus / 100) * 0.6
        
        if "rain" in self.weather:
            rain_multiplier = {"light_rain": 2.0, "rain": 3.0, "heavy_rain": 4.5}
            crash_chance *= rain_multiplier.get(self.weather, 1.0)
            
            if driver.tyre_compound in ["soft", "medium", "hard"]:
                crash_chance *= 2.5
        
        if self.track in ["Monaco", "Singapore"]:
            crash_chance *= 1.4
        
        if random.random() * 100 < crash_chance:
            crash_severity = random.uniform(5, 100)
            
            if crash_severity < 20:
                driver.damage += crash_severity
                driver.lock_ups += 1
                driver.mistakes_count += 1
                self.lap_events.append(f"⚠️ {driver.name} - Lock-up! Minor damage ({crash_severity:.0f}%)")
            elif crash_severity < 40:
                driver.damage += crash_severity
                driver.spins += 1
                driver.mistakes_count += 1
                positions_lost = random.randint(1, 3)
                self.lap_events.append(
                    f"🌪️ {driver.name} - SPIN! Lost ~{positions_lost} positions ({crash_severity:.0f}% damage)"
                )
            elif crash_severity < 70:
                driver.damage += crash_severity
                self.lap_events.append(f"🚨 {driver.name} - BIG MOMENT! Heavy damage ({crash_severity:.0f}%)")
                self.virtual_safety_car = True
                self.lap_events.append("🟡 **VIRTUAL SAFETY CAR**")
            else:
                driver.damage += crash_severity
                self.lap_events.append(f"💥 {driver.name} - **HUGE CRASH!**")
                self.safety_car = True
                self.lap_events.append("🚨 **SAFETY CAR DEPLOYED**")
            
            if crash_severity > 75 or driver.damage > 80:
                driver.dnf = True
                driver.dnf_reason = "Accident"
                self.lap_events.append(f"❌ {driver.name} - **DNF** (Accident)")
        
        failure_chance = (100 - driver.car_stats['reliability']) * 0.04
        failure_chance += driver.engine_wear_lap * 0.5
        
        if driver.engine_temp > 110:
            failure_chance *= 2.0
        
        if random.random() * 100 < failure_chance:
            failure_type = random.choice([
                "Engine", "Gearbox", "Hydraulics", "Electrical", 
                "Suspension", "Brake", "Power Unit"
            ])
            
            driver.dnf = True
            driver.dnf_reason = f"{failure_type} Failure"
            self.lap_events.append(f"💥 {driver.name} - **{failure_type.upper()} FAILURE!**")
            
            if random.random() < 0.4:
                self.virtual_safety_car = True
                self.lap_events.append("🟡 **VIRTUAL SAFETY CAR**")
    
    def check_safety_car(self):
        if self.safety_car:
            self.safety_car_laps += 1
            if self.safety_car_laps >= random.randint(2, 4):
                self.safety_car = False
                self.safety_car_laps = 0
                self.lap_events.append("🏁 **SAFETY CAR IN THIS LAP**")
                self.lap_events.append("🟢 **RACING RESUMES!**")
        
        if self.virtual_safety_car:
            self.vsc_laps += 1
            if self.vsc_laps >= random.randint(1, 3):
                self.virtual_safety_car = False
                self.vsc_laps = 0
                self.lap_events.append("🟢 **VSC ENDING - Green flag!**")
    
    def update_positions(self):
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
        
        for driver in self.drivers:
            driver.positions_gained = driver.grid_position - driver.position
    
    def ai_strategy_decisions(self):
        for driver in self.drivers:
            if not driver.is_ai or driver.dnf:
                continue
            
            should_pit = False
            pit_reason = ""
            
            if driver.tyre_condition < 12:
                should_pit = True
                pit_reason = "Tyres critical"
            
            if driver.tyre_condition < 20 and self.safety_car:
                should_pit = True
                pit_reason = "Safety car opportunity"
            
            if "rain" in self.weather and driver.tyre_compound not in ["inter", "wet"]:
                if self.weather == "heavy_rain" or driver.tyre_condition < 70:
                    should_pit = True
                    pit_reason = "Weather change"
            
            if self.weather == "clear" and driver.tyre_compound in ["inter", "wet"]:
                should_pit = True
                pit_reason = "Track drying"
            
            if self.virtual_safety_car and driver.tyre_condition < 50:
                if random.random() < 0.65:
                    should_pit = True
                    pit_reason = "VSC window"
            
            laps_remaining = self.total_laps - self.current_lap
            if driver.tyre_age > 15 and laps_remaining > 5:
                should_pit = True
                pit_reason = "High tyre age"
            
            if should_pit and driver.pit_stops < 4 and laps_remaining > 2:
                self.pit_stop(driver, pit_reason)
            
            if driver.position <= 3:
                driver.push_mode = max(25, driver.push_mode - 3)
                driver.fuel_mix = max(30, driver.fuel_mix - 2)
            elif driver.position > 10:
                driver.push_mode = min(85, driver.push_mode + 3)
                driver.fuel_mix = min(75, driver.fuel_mix + 2)
            
            if driver.in_battle:
                if driver.attacking:
                    driver.push_mode = min(95, driver.push_mode + 10)
                    driver.engine_mode = "overtake" if driver.ers_charge > 40 else "balanced"
                else:
                    driver.push_mode = min(80, driver.push_mode + 5)
                    driver.engine_mode = "balanced"
            
            if driver.ers_charge > 70 and driver.drs_available:
                driver.ers_mode = "deploy"
            elif driver.ers_charge < 25:
                driver.ers_mode = "charging"
            else:
                driver.ers_mode = "balanced"
            
            if driver.fuel_load < 15:
                driver.fuel_mix = max(20, driver.fuel_mix - 15)
                driver.engine_mode = "eco"
    
    def pit_stop(self, driver: Driver, reason: str = "Strategy"):
        driver.pit_stops += 1
        
        if "rain" in self.weather:
            if self.weather == "heavy_rain":
                new_compound = "wet"
            elif self.weather in ["rain", "light_rain"]:
                new_compound = "inter"
            else:
                new_compound = "soft"
        elif self.weather == "clear" and driver.tyre_compound in ["inter", "wet"]:
            new_compound = "soft"
        else:
            laps_remaining = self.total_laps - self.current_lap
            if laps_remaining < 8:
                new_compound = "soft"
            elif laps_remaining < 18:
                new_compound = "medium"
            else:
                new_compound = "hard"
        
        base_pit_time = 22.0
        
        crew_skill = random.uniform(-1.8, 1.2)
        
        if self.safety_car or self.virtual_safety_car:
            traffic_penalty = random.uniform(0, 2)
        else:
            traffic_penalty = random.uniform(0, 5)
        
        pit_time = base_pit_time + crew_skill + traffic_penalty
        
        driver.tyre_compound = new_compound
        driver.tyre_condition = 100.0
        driver.tyre_age = 0
        driver.tyre_temp = 70.0
        driver.fuel_load = min(100.0, driver.fuel_load + 50)
        
        minor_repairs = min(20, driver.damage)
        driver.damage = max(0, driver.damage - minor_repairs)
        
        driver.total_time += pit_time
        
        compound_emoji = {
            "soft": "🔴", "medium": "🟡", "hard": "⚪",
            "inter": "🟢", "wet": "🔵"
        }
        
        pit_quality = "Perfect" if pit_time < 21 else "Good" if pit_time < 23 else "Slow"
        
        self.lap_events.append(
            f"🔧 **PIT:** {driver.name} - {pit_time:.2f}s ({pit_quality}) | "
            f"{compound_emoji.get(new_compound, '⚪')} {new_compound.upper()} | {reason}"
        )
        
        if minor_repairs > 0:
            self.lap_events.append(f"   🔨 Repairs: {minor_repairs:.0f}% damage fixed")
    
    async def send_dm_updates(self, bot):
        """Send race updates to drivers' DMs"""
        for driver in self.drivers:
            if driver.is_ai or not driver.dm_channel_id:
                continue
            
            if self.current_lap - driver.last_dm_update < 2:
                continue
            
            try:
                channel = await bot.fetch_channel(driver.dm_channel_id)
                
                embed = discord.Embed(
                    title=f"🏎️ Lap {self.current_lap}/{self.total_laps}",
                    color=discord.Color.blue()
                )
                
                embed.add_field(name="Position", value=f"**P{driver.position}**", inline=True)
                embed.add_field(
                    name="Gap",
                    value=f"+{driver.gap_to_leader:.2f}s" if driver.position > 1 else "Leader",
                    inline=True
                )
                embed.add_field(name="Last Lap", value=f"{driver.lap_time:.3f}s", inline=True)
                
                tyre_emoji = {"soft": "🔴", "medium": "🟡", "hard": "⚪", "inter": "🟢", "wet": "🔵"}
                embed.add_field(
                    name="Tyres",
                    value=f"{tyre_emoji.get(driver.tyre_compound, '⚪')} {driver.tyre_compound.upper()} ({driver.tyre_condition:.0f}%)",
                    inline=True
                )
                embed.add_field(name="Fuel", value=f"{driver.fuel_load:.0f}%", inline=True)
                embed.add_field(name="ERS", value=f"{driver.ers_charge:.0f}%", inline=True)
                
                if driver.drs_available:
                    embed.add_field(name="DRS", value="✅ Available", inline=True)
                
                if driver.radio_messages:
                    recent_messages = driver.radio_messages[-3:]
                    embed.add_field(
                        name="📻 Team Radio",
                        value="\n".join(recent_messages),
                        inline=False
                    )
                    driver.radio_messages = driver.radio_messages[-5:]
                
                view = RaceControlView(embed.add_field(
                        name="📻 Team Radio",
                        value="\n".join(recent_messages),
                        inline=False
                    )
                    driver.radio_messages = driver.radio_messages[-5:]
                
                view = RaceControlView(driver, self)
                await channel.send(embed=embed, view=view)
                
                driver.last_dm_update = self.current_lap
                
            except Exception as e:
                print(f"Error sending DM to {driver.name}: {e}")

# ============================================================================
# DM RACE CONTROL VIEWS
# ============================================================================

class RaceControlView(discord.ui.View):
    def __init__(self, driver: Driver, race: 'RaceEngine'):
        super().__init__(timeout=180)
        self.driver = driver
        self.race = race
    
    @discord.ui.button(label="🔴 Soft Tyres", style=discord.ButtonStyle.danger, row=0)
    async def pit_soft(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.race.race_finished:
            await interaction.response.send_message("Race is finished!", ephemeral=True)
            return
        
        self.race.pit_stop(self.driver, "Player Request - Soft")
        self.driver.tyre_compound = "soft"
        await interaction.response.send_message("✅ Pitting for SOFT tyres!", ephemeral=True)
    
    @discord.ui.button(label="🟡 Medium Tyres", style=discord.ButtonStyle.secondary, row=0)
    async def pit_medium(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.race.race_finished:
            await interaction.response.send_message("Race is finished!", ephemeral=True)
            return
        
        self.race.pit_stop(self.driver, "Player Request - Medium")
        self.driver.tyre_compound = "medium"
        await interaction.response.send_message("✅ Pitting for MEDIUM tyres!", ephemeral=True)
    
    @discord.ui.button(label="⚪ Hard Tyres", style=discord.ButtonStyle.secondary, row=0)
    async def pit_hard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.race.race_finished:
            await interaction.response.send_message("Race is finished!", ephemeral=True)
            return
        
        self.race.pit_stop(self.driver, "Player Request - Hard")
        self.driver.tyre_compound = "hard"
        await interaction.response.send_message("✅ Pitting for HARD tyres!", ephemeral=True)
    
    @discord.ui.button(label="🟢 Inters", style=discord.ButtonStyle.success, row=0)
    async def pit_inter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.race.race_finished:
            await interaction.response.send_message("Race is finished!", ephemeral=True)
            return
        
        self.race.pit_stop(self.driver, "Player Request - Inters")
        self.driver.tyre_compound = "inter"
        await interaction.response.send_message("✅ Pitting for INTERMEDIATE tyres!", ephemeral=True)
    
    @discord.ui.button(label="🔵 Wets", style=discord.ButtonStyle.primary, row=0)
    async def pit_wet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.race.race_finished:
            await interaction.response.send_message("Race is finished!", ephemeral=True)
            return
        
        self.race.pit_stop(self.driver, "Player Request - Wets")
        self.driver.tyre_compound = "wet"
        await interaction.response.send_message("✅ Pitting for WET tyres!", ephemeral=True)
    
    @discord.ui.button(label="⚡ Push Mode", style=discord.ButtonStyle.danger, row=1)
    async def push_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.driver.push_mode = min(100, self.driver.push_mode + 20)
        self.driver.fuel_mix = min(100, self.driver.fuel_mix + 15)
        await interaction.response.send_message(
            f"✅ PUSH MODE! Push: {self.driver.push_mode}% | Fuel: {self.driver.fuel_mix}%",
            ephemeral=True
        )
    
    @discord.ui.button(label="🔋 Conserve", style=discord.ButtonStyle.success, row=1)
    async def conserve_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.driver.push_mode = max(30, self.driver.push_mode - 20)
        self.driver.fuel_mix = max(30, self.driver.fuel_mix - 15)
        await interaction.response.send_message(
            f"✅ CONSERVE MODE! Push: {self.driver.push_mode}% | Fuel: {self.driver.fuel_mix}%",
            ephemeral=True
        )
    
    @discord.ui.button(label="💨 ERS Deploy", style=discord.ButtonStyle.primary, row=1)
    async def ers_deploy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.driver.ers_charge < 20:
            await interaction.response.send_message("❌ Not enough ERS charge!", ephemeral=True)
            return
        
        self.driver.ers_mode = "deploy"
        await interaction.response.send_message(
            f"✅ ERS DEPLOY MODE! Charge: {self.driver.ers_charge:.0f}%",
            ephemeral=True
        )
    
    @discord.ui.button(label="🔌 ERS Charge", style=discord.ButtonStyle.secondary, row=1)
    async def ers_charge(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.driver.ers_mode = "charging"
        await interaction.response.send_message("✅ ERS CHARGING MODE!", ephemeral=True)
    
    @discord.ui.button(label="🏎️ Overtake Mode", style=discord.ButtonStyle.danger, row=2)
    async def overtake_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.driver.engine_mode = "overtake"
        self.driver.push_mode = 95
        await interaction.response.send_message(
            "✅ OVERTAKE MODE ACTIVATED! Maximum attack!",
            ephemeral=True
        )
    
    @discord.ui.button(label="📊 Telemetry", style=discord.ButtonStyle.primary, row=2)
    async def telemetry(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=f"🔧 Telemetry - {self.driver.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Position", value=f"P{self.driver.position}", inline=True)
        embed.add_field(name="Gap to Leader", value=f"+{self.driver.gap_to_leader:.2f}s", inline=True)
        embed.add_field(name="Gap to Front", value=f"+{self.driver.gap_to_front:.2f}s", inline=True)
        
        embed.add_field(name="Tyre Condition", value=f"{self.driver.tyre_condition:.1f}%", inline=True)
        embed.add_field(name="Tyre Age", value=f"{self.driver.tyre_age} laps", inline=True)
        embed.add_field(name="Tyre Temp", value=f"{self.driver.tyre_temp:.0f}°C", inline=True)
        
        embed.add_field(name="Fuel Load", value=f"{self.driver.fuel_load:.1f}%", inline=True)
        embed.add_field(name="Fuel Mix", value=f"{self.driver.fuel_mix}%", inline=True)
        embed.add_field(name="Fuel/Lap", value=f"{self.driver.fuel_per_lap:.2f}%", inline=True)
        
        embed.add_field(name="ERS Charge", value=f"{self.driver.ers_charge:.1f}%", inline=True)
        embed.add_field(name="Battery Temp", value=f"{self.driver.battery_temp:.0f}°C", inline=True)
        embed.add_field(name="ERS Mode", value=f"{self.driver.ers_mode.upper()}", inline=True)
        
        embed.add_field(name="Engine Temp", value=f"{self.driver.engine_temp:.0f}°C", inline=True)
        embed.add_field(name="Engine Mode", value=f"{self.driver.engine_mode.upper()}", inline=True)
        embed.add_field(name="Push Mode", value=f"{self.driver.push_mode}%", inline=True)
        
        embed.add_field(name="Damage", value=f"{self.driver.damage:.1f}%", inline=True)
        embed.add_field(name="Brake Wear", value=f"{self.driver.brake_wear:.1f}%", inline=True)
        embed.add_field(name="DRS", value="✅" if self.driver.drs_available else "❌", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================================================================
# RACE MANAGER - HANDLES LIVE RACE DISPLAY
# ============================================================================

class RaceManager:
    def __init__(self, race: RaceEngine, channel: discord.TextChannel):
        self.race = race
        self.channel = channel
        self.leaderboard_message = None
        self.events_message = None
        
    async def send_race_start(self):
        """Send race start information"""
        embed = discord.Embed(
            title=f"🏁 RACE START - {self.race.track_data[self.race.track]['name']}",
            description=f"{self.race.track_data[self.race.track]['country']}",
            color=discord.Color.red()
        )
        
        track_info = self.race.track_data[self.race.track]
        embed.add_field(name="Distance", value=f"{track_info['length']:.3f} km", inline=True)
        embed.add_field(name="Laps", value=f"{self.race.total_laps}", inline=True)
        embed.add_field(name="Total Distance", value=f"{track_info['length'] * self.race.total_laps:.1f} km", inline=True)
        
        embed.add_field(name="Weather", value=f"{self.race.weather.replace('_', ' ').title()}", inline=True)
        embed.add_field(name="Track Temp", value=f"{self.race.track_temp:.0f}°C", inline=True)
        embed.add_field(name="Air Temp", value=f"{self.race.air_temp:.0f}°C", inline=True)
        
        embed.add_field(
            name="Track Characteristics",
            value=f"🏎️ {track_info['characteristic']}\n"
                  f"🏎️ Avg Speed: {track_info['avg_speed']} km/h\n"
                  f"🔄 Corners: {track_info['corners']}\n"
                  f"📏 Elevation: {track_info['elevation_change']}m",
            inline=False
        )
        
        grid = "**STARTING GRID:**\n"
        for i, driver in enumerate(sorted([d for d in self.race.drivers if not d.dnf], key=lambda x: x.grid_position)):
            grid += f"`P{driver.grid_position:2d}` {driver.name}\n"
            if i >= 19:
                break
        
        embed.add_field(name="Grid", value=grid, inline=False)
        
        await self.channel.send(embed=embed)
        
    async def update_leaderboard(self):
        """Update race leaderboard"""
        active_drivers = sorted([d for d in self.race.drivers if not d.dnf], key=lambda x: x.position)
        
        embed = discord.Embed(
            title=f"🏁 LAP {self.race.current_lap}/{self.race.total_laps} - {self.race.track}",
            color=discord.Color.gold() if not self.race.safety_car else discord.Color.orange()
        )
        
        weather_emoji = {
            "clear": "☀️", "partly_cloudy": "⛅", "cloudy": "☁️",
            "light_rain": "🌦️", "rain": "🌧️", "heavy_rain": "⛈️"
        }
        
        status = ""
        if self.race.safety_car:
            status = "🚨 SAFETY CAR"
        elif self.race.virtual_safety_car:
            status = "🟡 VIRTUAL SAFETY CAR"
        elif self.race.drs_enabled:
            status = "💨 DRS ENABLED"
        else:
            status = "🟢 GREEN FLAG"
        
        embed.description = f"{weather_emoji.get(self.race.weather, '☀️')} {self.race.weather.replace('_', ' ').title()} | {status}"
        
        # Leaderboard
        leaderboard = ""
        for i, driver in enumerate(active_drivers[:20]):
            pos_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(driver.position, f"`P{driver.position:2d}`")
            
            tire_emoji = {"soft": "🔴", "medium": "🟡", "hard": "⚪", "inter": "🟢", "wet": "🔵"}
            tire_icon = tire_emoji.get(driver.tyre_compound, "⚪")
            
            gap = f"+{driver.gap_to_leader:.2f}s" if driver.position > 1 else "Leader"
            
            drs = "💨" if driver.drs_available else ""
            battle = "⚔️" if driver.in_battle else ""
            
            name_display = f"**{driver.name}**" if not driver.is_ai else driver.name
            
            leaderboard += f"{pos_emoji} {name_display} {tire_icon} {gap} {drs}{battle}\n"
        
        embed.add_field(name="Positions", value=leaderboard or "No active drivers", inline=False)
        
        # DNFs
        dnf_drivers = [d for d in self.race.drivers if d.dnf]
        if dnf_drivers:
            dnf_text = ""
            for driver in dnf_drivers:
                dnf_text += f"❌ {driver.name} - {driver.dnf_reason}\n"
            embed.add_field(name="DNF", value=dnf_text, inline=False)
        
        # Race Stats
        if active_drivers:
            fastest = min(active_drivers, key=lambda x: x.best_lap)
            embed.add_field(
                name="⏱️ Fastest Lap",
                value=f"{fastest.name} - {fastest.best_lap:.3f}s",
                inline=True
            )
        
        if self.leaderboard_message:
            try:
                await self.leaderboard_message.edit(embed=embed)
            except:
                self.leaderboard_message = await self.channel.send(embed=embed)
        else:
            self.leaderboard_message = await self.channel.send(embed=embed)
    
    async def send_lap_events(self):
        """Send lap events"""
        if not self.race.lap_events:
            return
        
        events_text = "\n".join(self.race.lap_events[:15])
        
        embed = discord.Embed(
            title=f"📻 Lap {self.race.current_lap} Events",
            description=events_text,
            color=discord.Color.blue()
        )
        
        await self.channel.send(embed=embed)
    
    async def send_race_results(self, db: Database):
        """Send final race results"""
        all_drivers = sorted(self.race.drivers, key=lambda x: (x.dnf, x.position))
        
        embed = discord.Embed(
            title=f"🏁 RACE RESULTS - {self.race.track}",
            color=discord.Color.gold()
        )
        
        # Points system
        points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
        
        results = ""
        for driver in all_drivers:
            if driver.dnf:
                results += f"❌ `DNF ` {driver.name} - {driver.dnf_reason}\n"
            else:
                pos_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(driver.position, f"`P{driver.position:2d}`")
                points = points_system[driver.position - 1] if driver.position <= 10 else 0
                
                # Fastest lap bonus
                fastest = min([d for d in all_drivers if not d.dnf], key=lambda x: x.best_lap)
                if driver.id == fastest.id and driver.position <= 10:
                    points += 1
                    results += f"{pos_emoji} {driver.name} - {points}pts ⚡\n"
                else:
                    results += f"{pos_emoji} {driver.name} - {points}pts\n"
        
        embed.add_field(name="Final Classification", value=results, inline=False)
        
        # Race Stats
        fastest = min([d for d in all_drivers if not d.dnf], key=lambda x: x.best_lap)
        most_overtakes = max(all_drivers, key=lambda x: x.overtakes_made)
        
        stats = f"⏱️ **Fastest Lap:** {fastest.name} - {fastest.best_lap:.3f}s\n"
        stats += f"🎯 **Most Overtakes:** {most_overtakes.name} - {most_overtakes.overtakes_made}\n"
        stats += f"🏁 **Laps Completed:** {self.race.current_lap}/{self.race.total_laps}\n"
        
        if self.race.safety_car_laps > 0:
            stats += f"🚨 **Safety Car Laps:** {self.race.safety_car_laps}\n"
        if self.race.vsc_laps > 0:
            stats += f"🟡 **VSC Laps:** {self.race.vsc_laps}\n"
        
        embed.add_field(name="Race Statistics", value=stats, inline=False)
        
        await self.channel.send(embed=embed)
        
        # Save to database
        for driver in all_drivers:
            if not driver.is_ai:
                points = points_system[driver.position - 1] if not driver.dnf and driver.position <= 10 else 0
                if driver.id == fastest.id and driver.position <= 10:
                    points += 1
                
                money_earned = self.calculate_race_earnings(driver, points)
                
                conn = db.get_conn()
                c = conn.cursor()
                
                # Update user stats
                c.execute('''UPDATE users SET 
                    career_points = career_points + ?,
                    money = money + ?,
                    race_starts = race_starts + 1,
                    career_wins = career_wins + ?,
                    career_podiums = career_podiums + ?,
                    fastest_laps = fastest_laps + ?,
                    dnf_count = dnf_count + ?,
                    total_distance = total_distance + ?,
                    total_race_time = total_race_time + ?,
                    last_race_date = ?
                    WHERE user_id = ?''',
                    (points, money_earned, 1 if driver.position == 1 else 0,
                     1 if driver.position <= 3 and not driver.dnf else 0,
                     1 if driver.id == fastest.id else 0,
                     1 if driver.dnf else 0,
                     self.race.track_data[self.race.track]['length'] * self.race.current_lap,
                     driver.total_time,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     driver.id))
                
                # Save race history
                c.execute('''INSERT INTO race_history (
                    user_id, position, points, fastest_lap, timestamp, track, weather,
                    grid_position, positions_gained, pit_stops, dnf, dnf_reason,
                    overtakes_made, overtakes_lost, battles_won, battles_lost,
                    top_speed, avg_lap_time, race_time, gap_to_winner,
                    tire_strategy, money_earned, race_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (driver.id, driver.position, points, driver.best_lap,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     self.race.track, self.race.weather, driver.grid_position,
                     driver.positions_gained, driver.pit_stops, 1 if driver.dnf else 0,
                     driver.dnf_reason, driver.overtakes_made, driver.overtakes_lost,
                     driver.battles_won, driver.battles_lost, 0,
                     driver.total_time / max(1, driver.lap), driver.total_time,
                     driver.gap_to_leader, f"{driver.tyre_compound}",
                     money_earned, self.race.race_mode))
                
                conn.commit()
                conn.close()
    
    def calculate_race_earnings(self, driver: Driver, points: int) -> int:
        """Calculate race earnings"""
        base_pay = 5000
        position_bonus = max(0, (20 - driver.position) * 1000) if not driver.dnf else 0
        points_bonus = points * 500
        overtake_bonus = driver.overtakes_made * 200
        fastest_lap_bonus = 2500 if driver.best_lap == min(d.best_lap for d in self.race.drivers if not d.dnf) else 0
        
        return base_pay + position_bonus + points_bonus + overtake_bonus + fastest_lap_bonus

# ============================================================================
# BOT SETUP
# ============================================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = Database()

active_races = {}

# ============================================================================
# BOT COMMANDS
# ============================================================================

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} commands')
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')

@bot.tree.command(name="register", description="Register as an F1 driver")
@app_commands.describe(driver_name="Your driver name", nationality="Your nationality (2-letter code)")
async def register(interaction: discord.Interaction, driver_name: str, nationality: str = "UN"):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    if c.fetchone():
        await interaction.response.send_message("❌ You're already registered!", ephemeral=True)
        conn.close()
        return
    
    c.execute('''INSERT INTO users (user_id, driver_name, nationality, created_date, racing_number)
                 VALUES (?, ?, ?, ?, ?)''',
              (interaction.user.id, driver_name, nationality.upper(),
               datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               random.randint(1, 99)))
    
    # Create default car
    c.execute('''INSERT INTO cars (owner_id, car_name, is_active)
                 VALUES (?, ?, 1)''',
              (interaction.user.id, f"{driver_name}'s Car"))
    
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="🏁 Registration Complete!",
        description=f"Welcome to F1 Racing, {driver_name}!",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Driver Name", value=driver_name, inline=True)
    embed.add_field(name="Nationality", value=nationality.upper(), inline=True)
    embed.add_field(name="Starting Money", value="$10,000", inline=True)
    
    embed.add_field(
        name="📚 Getting Started",
        value="• Use `/profile` to view your stats\n"
              "• Use `/race` to start racing\n"
              "• Use `/garage` to manage your car\n"
              "• Use `/shop` to buy upgrades",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="profile", description="View your driver profile")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    target = user or interaction.user
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (target.id,))
    user_data = c.fetchone()
    
    if not user_data:
        await interaction.response.send_message("❌ Driver not registered! Use `/register` first.", ephemeral=True)
        conn.close()
        return
    
    # Get column names
    columns = [description[0] for description in c.description]
    user_dict = dict(zip(columns, user_data))
    
    embed = discord.Embed(
        title=f"🏎️ {user_dict['driver_name']}",
        description=f"🏴 {user_dict['nationality']} | #{user_dict['racing_number']}",
        color=discord.Color.blue()
    )
    
    embed.set_thumbnail(url=target.display_avatar.url)
    
    # Career Stats
    win_rate = (user_dict['career_wins'] / max(1, user_dict['race_starts'])) * 100
    podium_rate = (user_dict['career_podiums'] / max(1, user_dict['race_starts'])) * 100
    
    embed.add_field(
        name="🏆 Career Statistics",
        value=f"**Races:** {user_dict['race_starts']}\n"
              f"**Wins:** {user_dict['career_wins']} ({win_rate:.1f}%)\n"
              f"**Podiums:** {user_dict['career_podiums']} ({podium_rate:.1f}%)\n"
              f"**Points:** {user_dict['career_points']}\n"
              f"**Fastest Laps:** {user_dict['fastest_laps']}",
        inline=True
    )
    
    # Skills
    embed.add_field(
        name="⚡ Skills",
        value=f"**Rating:** {user_dict['skill_rating']:.1f}\n"
              f"**Aggression:** {user_dict['aggression']:.1f}\n"
              f"**Consistency:** {user_dict['consistency']:.1f}\n"
              f"**Overtaking:** {user_dict['overtaking_skill']:.1f}\n"
              f"**Defending:** {user_dict['defending_skill']:.1f}",
        inline=True
    )
    
    # Financial
    embed.add_field(
        name="💰 Financial",
        value=f"**Money:** ${user_dict['money']:,}\n"
              f"**Total Earnings:** ${user_dict['total_earnings']:,}\n"
              f"**License:** {user_dict['license_level'].title()}",
        inline=True
    )
    
    # Advanced Stats
    embed.add_field(
        name="📊 Advanced Stats",
        value=f"**Rain Skill:** {user_dict['rain_skill']:.1f}\n"
              f"**Quali Skill:** {user_dict['quali_skill']:.1f}\n"
              f"**Race Craft:** {user_dict['race_craft']:.1f}\n"
              f"**Tire Mgmt:** {user_dict['tire_management']:.1f}\n"
              f"**Fuel Mgmt:** {user_dict['fuel_management']:.1f}",
        inline=True
    )
    
    # Form & Condition
    embed.add_field(
        name="🎯 Current Form",
        value=f"**Form:** {user_dict['current_form']:.1f}\n"
              f"**Fitness:** {user_dict['fitness']:.1f}\n"
              f"**Reputation:** {user_dict['reputation']:.1f}\n"
              f"**Confidence:** {user_dict['mental_strength']:.1f}",
        inline=True
    )
    
    # Best Results
    c.execute('''SELECT position, track, timestamp FROM race_history 
                 WHERE user_id = ? AND dnf = 0 
                 ORDER BY position ASC LIMIT 3''', (target.id,))
    best_results = c.fetchall()
    
    if best_results:
        results_text = ""
        for pos, track, timestamp in best_results:
            results_text += f"P{pos} - {track}\n"
        embed.add_field(name="🌟 Best Results", value=results_text, inline=True)
    
    conn.close()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="race", description="Start a race")
@app_commands.describe(
    track="Choose a track",
    laps="Number of laps (5-50)",
    weather="Weather conditions",
    qualifying="Run qualifying session",
    ai_count="Number of AI drivers (1-19)"
)
@app_commands.choices(track=[
    app_commands.Choice(name="🇮🇹 Monza", value="Monza"),
    app_commands.Choice(name="🇲🇨 Monaco", value="Monaco"),
    app_commands.Choice(name="🇧🇪 Spa", value="Spa"),
    app_commands.Choice(name="🇬🇧 Silverstone", value="Silverstone"),
    app_commands.Choice(name="🇯🇵 Suzuka", value="Suzuka"),
    app_commands.Choice(name="🇸🇬 Singapore", value="Singapore"),
    app_commands.Choice(name="🇧🇷 Interlagos", value="Interlagos"),
    app_commands.Choice(name="🇺🇸 Austin", value="Austin"),
])
@app_commands.choices(weather=[
    app_commands.Choice(name="☀️ Clear", value="clear"),
    app_commands.Choice(name="⛅ Partly Cloudy", value="partly_cloudy"),
    app_commands.Choice(name="☁️ Cloudy", value="cloudy"),
    app_commands.Choice(name="🌦️ Light Rain", value="light_rain"),
    app_commands.Choice(name="🌧️ Rain", value="rain"),
    app_commands.Choice(name="⛈️ Heavy Rain", value="heavy_rain"),
])
async def race(
    interaction: discord.Interaction,
    track: str = "Monza",
    laps: int = 15,
    weather: str = "clear",
    qualifying: bool = True,
    ai_count: int = 19
):
    # Check registration
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    user_data = c.fetchone()
    
    if not user_data:
        await interaction.response.send_message("❌ You need to register first! Use `/register`", ephemeral=True)
        conn.close()
        return
    
    # Check if already in a race
    if interaction.channel.id in active_races:
        await interaction.response.send_message("❌ A race is already active in this channel!", ephemeral=True)
        conn.close()
        return
    
    # Validate inputs
    laps = max(5, min(50, laps))
    ai_count = max(1, min(19, ai_count))
    
    await interaction.response.defer()
    
    # Get user data
    columns = [description[0] for description in c.description]
    user_dict = dict(zip(columns, user_data))
    
    # Get user's car
    c.execute("SELECT * FROM cars WHERE owner_id = ? AND is_active = 1 LIMIT 1", (interaction.user.id,))
    car_data = c.fetchone()
    
    if car_data:
        car_columns = [description[0] for description in c.description]
        car_dict = dict(zip(car_columns, car_data))
    else:
        car_dict = {
            'engine_power': 50, 'aero': 50, 'handling': 50,
            'reliability': 100, 'tyre_wear_rate': 1.0,
            'fuel_efficiency': 1.0, 'ers_power': 50, 'drs_efficiency': 1.0,
            'brake_power': 50, 'cooling_efficiency': 50
        }
    
    # Create race engine
    race = RaceEngine(track=track, laps=laps, weather=weather, qualifying=qualifying)
    
    # Create player driver
    player_driver = Driver(
        driver_id=interaction.user.id,
        name=user_dict['driver_name'],
        skill=user_dict['skill_rating'],
        aggression=user_dict['aggression'],
        consistency=user_dict['consistency'],
        is_ai=False,
        car_stats=car_dict,
        advanced_stats={
            'rain_skill': user_dict['rain_skill'],
            'overtaking_skill': user_dict['overtaking_skill'],
            'defending_skill': user_dict['defending_skill'],
            'quali_skill': user_dict['quali_skill'],
            'tire_management': user_dict['tire_management'],
            'fuel_management': user_dict['fuel_management'],
            'race_craft': user_dict['race_craft']
        }
    )
    
    # Setup DM channel
    try:
        dm_channel = await interaction.user.create_dm()
        player_driver.dm_channel_id = dm_channel.id
        
        welcome_embed = discord.Embed(
            title="🏎️ Race Control Connected!",
            description=f"You can control your race strategy from here!\n\n**Track:** {track}\n**Laps:** {laps}",
            color=discord.Color.green()
        )
        await dm_channel.send(embed=welcome_embed)
    except:
        pass
    
    race.add_driver(player_driver)
    
    # Add AI drivers
    c.execute(f"SELECT * FROM ai_profiles ORDER BY RANDOM() LIMIT {ai_count}")
    ai_drivers_data = c.fetchall()
    
    ai_columns = [description[0] for description in c.description]
    
    for ai_data in ai_drivers_data:
        ai_dict = dict(zip(ai_columns, ai_data))
        
        ai_car = {
            'engine_power': random.uniform(45, 95),
            'aero': random.uniform(45, 95),
            'handling': random.uniform(45, 95),
            'reliability': random.uniform(85, 100),
            'tyre_wear_rate': random.uniform(0.8, 1.2),
            'fuel_efficiency': random.uniform(0.9, 1.1),
            'ers_power': random.uniform(45, 95),
            'drs_efficiency': random.uniform(0.9, 1.1),
            'brake_power': random.uniform(45, 95),
            'cooling_efficiency': random.uniform(45, 95)
        }
        
        ai_driver = Driver(
            driver_id=ai_dict['ai_id'] + 100000,
            name=ai_dict['ai_name'],
            skill=ai_dict['skill_rating'],
            aggression=ai_dict['aggression'],
            consistency=ai_dict['consistency'],
            is_ai=True,
            car_stats=ai_car,
            advanced_stats={
                'rain_skill': ai_dict['rain_skill'],
                'overtaking_skill': ai_dict['overtake_skill'],
                'defending_skill': ai_dict['defend_skill'],
                'quali_skill': ai_dict['quali_skill'],
                'tire_management': ai_dict['tire_management'],
                'fuel_management': ai_dict['fuel_management'],
                'race_craft': ai_dict['race_craft']
            }
        )
        
        race.add_driver(ai_driver)
    
    conn.close()
    
    # Create race manager
    race_manager = RaceManager(race, interaction.channel)
    active_races[interaction.channel.id] = race
    
    # Run qualifying
    if qualifying:
        quali_embed = discord.Embed(
            title=f"🏁 QUALIFYING - {track}",
            description="Running qualifying session...",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=quali_embed)
        
        await asyncio.sleep(2)
        
        quali_results = race.run_qualifying()
        
        results_text = ""
        for idx, (driver, time) in enumerate(quali_results[:10]):
            pos_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}.get(idx, f"`P{idx+1:2d}`")
            gap = f"+{time - quali_results[0][1]:.3f}s" if idx > 0 else "POLE"
            results_text += f"{pos_emoji} {driver.name} - {time:.3f}s ({gap})\n"
        
        quali_result_embed = discord.Embed(
            title="🏁 QUALIFYING RESULTS",
            description=results_text,
            color=discord.Color.gold()
        )
        
        await interaction.channel.send(embed=quali_result_embed)
        await asyncio.sleep(3)
    
    # Start race
    await race_manager.send_race_start()
    await asyncio.sleep(2)
    
    # Race simulation loop
    while race.current_lap < race.total_laps:
        await race.simulate_lap(bot)
        
        await race_manager.update_leaderboard()
        await race_manager.send_lap_events()
        
        # Check if all non-AI drivers DNFed
        active_players = [d for d in race.drivers if not d.is_ai and not d.dnf]
        if not active_players:
            break
        
        await asyncio.sleep(3)
    
    race.race_finished = True
    
    # Send final results
    await race_manager.send_race_results(db)
    
    # Clean up
    if interaction.channel.id in active_races:
        del active_races[interaction.channel.id]

@bot.tree.command(name="quickrace", description="Quick 5-lap sprint race")
async def quickrace(interaction: discord.Interaction):
    await race(interaction, laps=5, qualifying=False, ai_count=10)

@bot.tree.command(name="garage", description="Manage your car")
async def garage(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    if not c.fetchone():
        await interaction.response.send_message("❌ You need to register first!", ephemeral=True)
        conn.close()
        return
    
    c.execute("SELECT * FROM cars WHERE owner_id = ? AND is_active = 1", (interaction.user.id,))
    car_data = c.fetchone()
    
    if not car_data:
        await interaction.response.send_message("❌ No active car found!", ephemeral=True)
        conn.close()
        return
    
    columns = [description[0] for description in c.description]
    car = dict(zip(columns, car_data))
    
    embed = discord.Embed(
        title=f"🏎️ {car['car_name']}",
        description=f"**Performance Rating:** {car['performance_rating']:.1f}/100",
        color=discord.Color.blue()
    )
    
    # Performance stats
    embed.add_field(
        name="⚡ Power & Speed",
        value=f"**Engine Power:** {car['engine_power']:.1f}/100\n"
              f"**ERS Power:** {car['ers_power']:.1f}/100\n"
              f"**Turbo Efficiency:** {car['turbo_efficiency']:.1f}/100",
        inline=True
    )
    
    embed.add_field(
        name="🌀 Aerodynamics",
        value=f"**Downforce:** {car['downforce']:.1f}/100\n"
              f"**Aero Efficiency:** {car['aero_efficiency']:.1f}/100\n"
              f"**Drag Coefficient:** {car['drag_coefficient']:.2f}",
        inline=True
    )
    
    embed.add_field(
        name="🎯 Handling",
        value=f"**Handling:** {car['handling']:.1f}/100\n"
              f"**Brake Power:** {car['brake_power']:.1f}/100\n"
              f"**Stability:** {car['stability']:.1f}/100",
        inline=True
    )
    
    # Reliability
    reliability_emoji = "🟢" if car['reliability'] > 80 else "🟡" if car['reliability'] > 60 else "🔴"
    embed.add_field(
        name=f"{reliability_emoji} Reliability",
        value=f"**Condition:** {car['reliability']:.1f}%\n"
              f"**Engine Wear:** {car['engine_wear']:.1f}%\n"
              f"**Gearbox Wear:** {car['gearbox_wear']:.1f}%",
        inline=True
    )
    
    # Efficiency
    embed.add_field(
        name="♻️ Efficiency",
        value=f"**Fuel Efficiency:** {car['fuel_efficiency']:.2f}x\n"
              f"**Tyre Wear Rate:** {car['tyre_wear_rate']:.2f}x\n"
              f"**Cooling:** {car['cooling_efficiency']:.1f}/100",
        inline=True
    )
    
    # Racing Stats
    embed.add_field(
        name="🏁 Racing Record",
        value=f"**Races:** {car['total_races']}\n"
              f"**Wins:** {car['total_wins']}\n"
              f"**Best Lap:** {car['best_lap_time']:.3f}s" if car['best_lap_time'] < 999 else "N/A",
        inline=True
    )
    
    conn.close()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="upgrade", description="Upgrade your car")
@app_commands.describe(component="Component to upgrade")
@app_commands.choices(component=[
    app_commands.Choice(name="⚡ Engine Power", value="engine_power"),
    app_commands.Choice(name="🌀 Aerodynamics", value="aero"),
    app_commands.Choice(name="🎯 Handling", value="handling"),
    app_commands.Choice(name="🔋 ERS Power", value="ers_power"),
    app_commands.Choice(name="🛑 Brake Power", value="brake_power"),
    app_commands.Choice(name="❄️ Cooling", value="cooling_efficiency"),
    app_commands.Choice(name="⚙️ Reliability", value="reliability"),
])
async def upgrade(interaction: discord.Interaction, component: str):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    user_data = c.fetchone()
    
    if not user_data:
        await interaction.response.send_message("❌ You need to register first!", ephemeral=True)
        conn.close()
        return
    
    money = user_data[0]
    
    c.execute(f"SELECT {component} FROM cars WHERE owner_id = ? AND is_active = 1", (interaction.user.id,))
    car_data = c.fetchone()
    
    if not car_data:
        await interaction.response.send_message("❌ No active car found!", ephemeral=True)
        conn.close()
        return
    
    current_value = car_data[0]
    
    # Calculate upgrade cost
    base_cost = 5000
    level_multiplier = (current_value / 10) ** 2
    upgrade_cost = int(base_cost * (1 + level_multiplier))
    
    if money < upgrade_cost:
        await interaction.response.send_message(
            f"❌ Not enough money! Need ${upgrade_cost:,} but you have ${money:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    if current_value >= 100:
        await interaction.response.send_message("❌ Component already at maximum level!", ephemeral=True)
        conn.close()
        return
    
    # Perform upgrade
    upgrade_amount = random.uniform(1.5, 3.5)
    new_value = min(100, current_value + upgrade_amount)
    
    c.execute(f"UPDATE cars SET {component} = ? WHERE owner_id = ? AND is_active = 1",
              (new_value, interaction.user.id))
    
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?",
              (upgrade_cost, interaction.user.id))
    
    conn.commit()
    conn.close()
    
    component_names = {
        "engine_power": "⚡ Engine Power",
        "aero": "🌀 Aerodynamics",
        "handling": "🎯 Handling",
        "ers_power": "🔋 ERS Power",
        "brake_power": "🛑 Brake Power",
        "cooling_efficiency": "❄️ Cooling Efficiency",
        "reliability": "⚙️ Reliability"
    }
    
    embed = discord.Embed(
        title="✅ Upgrade Complete!",
        description=f"**{component_names.get(component, component)}**",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Before", value=f"{current_value:.1f}", inline=True)
    embed.add_field(name="→", value="📈", inline=True)
    embed.add_field(name="After", value=f"{new_value:.1f}", inline=True)
    
    embed.add_field(name="Cost", value=f"${upgrade_cost:,}", inline=True)
    embed.add_field(name="Remaining", value=f"${money - upgrade_cost:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stats", description="View your racing statistics")
async def stats(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    user_data = c.fetchone()
    
    if not user_data:
        await interaction.response.send_message("❌ You need to register first!", ephemeral=True)
        conn.close()
        return
    
    columns = [description[0] for description in c.description]
    user = dict(zip(columns, user_data))
    
    # Get race history
    c.execute('''SELECT COUNT(*), AVG(position), MIN(position), MAX(fastest_lap)
                 FROM race_history WHERE user_id = ? AND dnf = 0''', (interaction.user.id,))
    races, avg_pos, best_pos, best_lap = c.fetchone()
    
    c.execute('''SELECT track, COUNT(*) as wins FROM race_history 
                 WHERE user_id = ? AND position = 1 
                 GROUP BY track ORDER BY wins DESC LIMIT 3''', (interaction.user.id,))
    best_tracks = c.fetchall()
    
    embed = discord.Embed(
        title=f"📊 Statistics - {user['driver_name']}",
        color=discord.Color.blue()
    )
    
    # Career overview
    win_rate = (user['career_wins'] / max(1, user['race_starts'])) * 100
    podium_rate = (user['career_podiums'] / max(1, user['race_starts'])) * 100
    dnf_rate = (user['dnf_count'] / max(1, user['race_starts'])) * 100
    
    embed.add_field(
        name="🏆 Career Overview",
        value=f"**Races:** {user['race_starts']}\n"
              f"**Wins:** {user['career_wins']} ({win_rate:.1f}%)\n"
              f"**Podiums:** {user['career_podiums']} ({podium_rate:.1f}%)\n"
              f"**DNFs:** {user['dnf_count']} ({dnf_rate:.1f}%)\n"
              f"**Points:** {user['career_points']}",
        inline=True
    )
    
    # Performance
    embed.add_field(
        name="⚡ Performance",
        value=f"**Avg Finish:** P{avg_pos:.1f}\n"
              f"**Best Finish:** P{best_pos}\n"
              f"**Best Lap:** {best_lap:.3f}s\n"
              f"**Fastest Laps:** {user['fastest_laps']}\n"
              f"**Poles:** {user['pole_positions']}",
        inline=True
    )
    
    # Race craft
    c.execute('''SELECT SUM(overtakes_made), SUM(battles_won), SUM(pit_stops)
                 FROM race_history WHERE user_id = ?''', (interaction.user.id,))
    overtakes, battles, pit_stops = c.fetchone()
    
    embed.add_field(
        name="🎯 Race Craft",
        value=f"**Overtakes:** {overtakes or 0}\n"
              f"**Battles Won:** {battles or 0}\n"
              f"**Pit Stops:** {pit_stops or 0}\n"
              f"**Distance:** {user['total_distance']:.0f} km",
        inline=True
    )
    
    # Best tracks
    if best_tracks:
        tracks_text = ""
        for track, wins in best_tracks:
            tracks_text += f"**{track}:** {wins} wins\n"
        embed.add_field(name="🌟 Best Tracks", value=tracks_text, inline=True)
    
    # Recent form
    c.execute('''SELECT position, track FROM race_history 
                 WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5''', (interaction.user.id,))
    recent = c.fetchall()
    
    if recent:
        recent_text = ""
        for pos, track in recent:
            recent_text += f"P{pos} - {track}\n"
        embed.add_field(name="📈 Recent Form", value=recent_text, inline=True)
    
    conn.close()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="View global leaderboard")
@app_commands.describe(category="Leaderboard category")
@app_commands.choices(category=[
    app_commands.Choice(name="🏆 Championship Points", value="points"),
    app_commands.Choice(name="💰 Money", value="money"),
    app_commands.Choice(name="🥇 Wins", value="wins"),
    app_commands.Choice(name="⚡ Skill Rating", value="skill"),
])
async def leaderboard(interaction: discord.Interaction, category: str = "points"):
    conn = db.get_conn()
    c = conn.cursor()
    
    category_map = {
        "points": ("career_points", "Points"),
        "money": ("money", "Money"),
        "wins": ("career_wins", "Wins"),
        "skill": ("skill_rating", "Rating")
    }
    
    column, name = category_map.get(category, ("career_points", "Points"))
    
    c.execute(f'''SELECT driver_name, {column}, nationality, racing_number 
                  FROM users ORDER BY {column} DESC LIMIT 10''')
    top_drivers = c.fetchall()
    
    embed = discord.Embed(
        title=f"🏆 Global Leaderboard - {name}",
        color=discord.Color.gold()
    )
    
    leaderboard_text = ""
    for idx, (name_driver, value, nationality, number) in enumerate(top_drivers, 1):
        emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"`#{idx:2d}`")
        
        if category == "money":
            value_str = f"${value:,}"
        elif category == "skill":
            value_str = f"{value:.1f}"
        else:
            value_str = f"{value}"
        
        leaderboard_text += f"{emoji} **{name_driver}** 🏴 {nationality} #{number} - {value_str}\n"
    
    embed.description = leaderboard_text
    
    # User's position
    c.execute(f'''SELECT COUNT(*) + 1 FROM users u1, users u2 
                  WHERE u1.user_id = ? AND u2.{column} > u1.{column}''',
              (interaction.user.id,))
    user_rank = c.fetchone()[0]
    
    c.execute(f"SELECT {column} FROM users WHERE user_id = ?", (interaction.user.id,))
    user_value = c.fetchone()
    
    if user_value:
        if category == "money":
            val_str = f"${user_value[0]:,}"
        elif category == "skill":
            val_str = f"{user_value[0]:.1f}"
        else:
            val_str = f"{user_value[0]}"
        
        embed.set_footer(text=f"Your rank: #{user_rank} - {val_str}")
    
    conn.close()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="history", description="View your race history")
async def history(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute('''SELECT position, track, weather, points, fastest_lap, timestamp, dnf, dnf_reason
                 FROM race_history WHERE user_id = ? 
                 ORDER BY timestamp DESC LIMIT 10''', (interaction.user.id,))
    
    races = c.fetchall()
    
    if not races:
        await interaction.response.send_message("❌ No race history found!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(
        title="📜 Race History",
        color=discord.Color.blue()
    )
    
    for pos, track, weather, points, fastest_lap, timestamp, dnf, dnf_reason in races:
        if dnf:
            result = f"❌ DNF - {dnf_reason}"
        else:
            pos_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"P{pos}")
            result = f"{pos_emoji} - {points} pts - {fastest_lap:.3f}s"
        
        date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        
        embed.add_field(
            name=f"{track} - {date}",
            value=f"{result}\n{weather.replace('_', ' ').title()}",
            inline=False
        )
    
    conn.close()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="View bot commands and features")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏎️ F1 Racing Bot - Help",
        description="Ultra-realistic F1 racing simulation with 300+ features!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🏁 Getting Started",
        value="`/register` - Register as a driver\n"
              "`/profile` - View your profile\n"
              "`/garage` - Manage your car\n"
              "`/help` - Show this help",
        inline=False
    )
    
    embed.add_field(
        name="🏎️ Racing",
        value="`/race` - Start a full race\n"
              "`/quickrace` - Quick 5-lap race\n"
              "`/history` - View race history\n"
              "`/stats` - View statistics",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Car Management",
        value="`/upgrade` - Upgrade car components\n"
              "`/garage` - View car details\n"
              "`/shop` - Visit the shop",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Competition",
        value="`/leaderboard` - Global rankings\n"
              "`/championship` - Championship standings",
        inline=False
    )
    
    embed.add_field(
        name="📊 Features",
        value="✅ Realistic physics & tire degradation\n"
              "✅ Dynamic weather system\n"
              "✅ DM race controls\n"
              "✅ Live position updates\n"
              "✅ Pit stop strategy\n"
              "✅ ERS & DRS management\n"
              "✅ Overtaking battles\n"
              "✅ Safety car periods\n"
              "✅ Car damage system\n"
              "✅ Advanced AI drivers",
        inline=False
    )
    
    embed.set_footer(text="Control your race from DMs during races!")
    
    await interaction.response.send_message(embed=embed)

# ============================================================================
# RUN BOT
# ============================================================================

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
if token is None:
    raise ValueError("Discord token not found!")
bot.run(token)
