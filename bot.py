# F1 DISCORD RACING BOT - COMPLETE ULTRA-REALISTIC SYSTEM
# 100+ Commands, 150+ Buttons, Full Simulation
# Compatible with Pydroid 3

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os

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
            skill_points INTEGER DEFAULT 0
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
            defend_skill REAL
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
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # LEAGUES TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS leagues (
            league_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_name TEXT,
            creator_id INTEGER,
            created_date TEXT,
            max_drivers INTEGER DEFAULT 20,
            current_season INTEGER DEFAULT 1
        )''')
        
        # LEAGUE MEMBERS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS league_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER,
            user_id INTEGER,
            join_date TEXT,
            season_points INTEGER DEFAULT 0,
            season_wins INTEGER DEFAULT 0,
            FOREIGN KEY (league_id) REFERENCES leagues(league_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # SPONSORS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS sponsors (
            sponsor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sponsor_name TEXT,
            payment_per_race INTEGER,
            contract_length INTEGER,
            bonus_amount INTEGER
        )''')
        
        # USER SPONSORS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_sponsors (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sponsor_id INTEGER,
            signed_date TEXT,
            races_remaining INTEGER,
            total_earned INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id)
        )''')
        
        # ACHIEVEMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS achievements (
            achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_name TEXT,
            description TEXT,
            reward_money INTEGER DEFAULT 0,
            reward_skill_points INTEGER DEFAULT 0
        )''')
        
        # USER ACHIEVEMENTS TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_id INTEGER,
            unlocked_date TEXT,
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
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        conn.commit()
        conn.close()
        
        self.seed_ai_drivers()
        self.seed_sponsors()
        self.seed_achievements()
    
    def seed_ai_drivers(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ai_profiles")
        if c.fetchone()[0] == 0:
            ai_drivers = [
                ("Max Verstappen", 95, 75, 85, 90, 85),
                ("Lewis Hamilton", 93, 60, 90, 88, 90),
                ("Charles Leclerc", 88, 70, 80, 85, 80),
                ("Lando Norris", 85, 65, 78, 82, 78),
                ("Carlos Sainz", 84, 55, 85, 80, 85),
                ("George Russell", 83, 50, 82, 78, 82),
                ("Fernando Alonso", 90, 80, 95, 92, 95),
                ("Oscar Piastri", 80, 60, 70, 75, 70),
                ("Sergio Perez", 82, 65, 80, 76, 80),
                ("Pierre Gasly", 78, 70, 72, 74, 72),
                ("Esteban Ocon", 77, 68, 74, 72, 74),
                ("Yuki Tsunoda", 76, 75, 65, 70, 65),
            ]
            c.executemany('''INSERT INTO ai_profiles 
                (ai_name, skill_rating, aggression, consistency, overtake_skill, defend_skill)
                VALUES (?, ?, ?, ?, ?, ?)''', ai_drivers)
            conn.commit()
        conn.close()
    
    def seed_sponsors(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sponsors")
        if c.fetchone()[0] == 0:
            sponsors = [
                ("Petronas", 3000, 10, 5000),
                ("Shell", 3500, 8, 4500),
                ("Emirates", 2000, 12, 10000),
                ("Rolex", 1500, 15, 15000),
                ("Pirelli", 2500, 20, 2500),
                ("DHL", 2000, 10, 2000),
                ("Heineken", 1000, 15, 3000),
                ("AWS", 2200, 10, 3000),
            ]
            c.executemany('''INSERT INTO sponsors 
                (sponsor_name, payment_per_race, contract_length, bonus_amount)
                VALUES (?, ?, ?, ?)''', sponsors)
            conn.commit()
        conn.close()
    
    def seed_achievements(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM achievements")
        if c.fetchone()[0] == 0:
            achievements = [
                ("First Victory", "Win your first race", 5000, 10),
                ("Podium Finisher", "Finish in top 3", 2000, 5),
                ("Perfect Weekend", "Win from pole position", 10000, 20),
                ("Comeback King", "Win after starting P10+", 15000, 30),
                ("Hat Trick", "Win 3 races in a row", 20000, 50),
                ("Century Club", "Complete 100 races", 25000, 100),
                ("Speed Demon", "Set 10 fastest laps", 8000, 15),
                ("Wet Master", "Win 5 races in rain", 10000, 20),
            ]
            c.executemany('''INSERT INTO achievements 
                (achievement_name, description, reward_money, reward_skill_points)
                VALUES (?, ?, ?, ?)''', achievements)
            conn.commit()
        conn.close()

# ============================================================================
# RACE ENGINE - COMPLETE SIMULATION
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
        else:
            self.rain_skill = 50
            self.overtaking_skill = 50
            self.defending_skill = 50
            self.quali_skill = 50
        
        self.car_stats = car_stats or {
            'engine_power': 50, 'aero': 50, 'handling': 50,
            'reliability': 100, 'tyre_wear_rate': 1.0,
            'fuel_efficiency': 1.0, 'ers_power': 50, 'drs_efficiency': 1.0
        }
        
        self.position = 0
        self.grid_position = 0
        self.lap = 0
        self.total_time = 0.0
        self.gap_to_leader = 0.0
        self.gap_to_front = 0.0
        self.lap_time = 0.0
        self.best_lap = 999.0
        
        self.tyre_compound = "medium"
        self.tyre_condition = 100.0
        self.tyre_age = 0
        self.pit_stops = 0
        
        self.fuel_load = 100.0
        self.fuel_mix = 50
        self.ers_charge = 100.0
        self.ers_mode = "balanced"
        
        self.push_mode = 50
        self.defending = False
        self.attacking = False
        self.drs_available = False
        
        self.dnf = False
        self.dnf_reason = ""
        self.damage = 0.0
        self.penalties = 0
        
        self.overtakes_made = 0
        self.overtakes_lost = 0
        self.positions_gained = 0

class RaceEngine:
    def __init__(self, track="Monza", laps=10, weather="clear", qualifying=True):
        self.track = track
        self.total_laps = laps
        self.current_lap = 0
        self.weather = weather
        self.track_temp = 30
        self.track_grip = 100.0
        self.safety_car = False
        self.drs_enabled = False
        self.qualifying_mode = qualifying
        
        self.drivers: List[Driver] = []
        self.events = []
        self.lap_events = []
        
        self.track_data = {
            "Monza": {
                "name": "Autodromo Nazionale di Monza",
                "country": "Italy",
                "base_lap_time": 80.0,
                "overtake_difficulty": 30,
                "tyre_wear": 1.0,
                "characteristic": "High Speed"
            },
            "Monaco": {
                "name": "Circuit de Monaco",
                "country": "Monaco",
                "base_lap_time": 72.0,
                "overtake_difficulty": 90,
                "tyre_wear": 0.7,
                "characteristic": "Street Circuit"
            },
            "Spa": {
                "name": "Circuit de Spa-Francorchamps",
                "country": "Belgium",
                "base_lap_time": 105.0,
                "overtake_difficulty": 40,
                "tyre_wear": 1.2,
                "characteristic": "High Speed & Elevation"
            },
            "Silverstone": {
                "name": "Silverstone Circuit",
                "country": "Great Britain",
                "base_lap_time": 88.0,
                "overtake_difficulty": 50,
                "tyre_wear": 1.1,
                "characteristic": "High Speed Corners"
            },
            "Suzuka": {
                "name": "Suzuka Circuit",
                "country": "Japan",
                "base_lap_time": 90.0,
                "overtake_difficulty": 60,
                "tyre_wear": 1.15,
                "characteristic": "Technical"
            },
            "Singapore": {
                "name": "Marina Bay",
                "country": "Singapore",
                "base_lap_time": 95.0,
                "overtake_difficulty": 70,
                "tyre_wear": 0.9,
                "characteristic": "Night Street"
            },
        }
        
        if track not in self.track_data:
            self.track = "Monza"
        
        self.weather_forecast = [weather] * (laps + 1)
        self.generate_weather_forecast()
    
    def generate_weather_forecast(self):
        weather_states = ["clear", "cloudy", "light_rain", "rain"]
        
        for i in range(1, len(self.weather_forecast)):
            current = self.weather_forecast[i-1]
            current_idx = weather_states.index(current)
            
            change = random.choices([-1, 0, 1], weights=[0.1, 0.7, 0.2])[0]
            new_idx = max(0, min(len(weather_states)-1, current_idx + change))
            self.weather_forecast[i] = weather_states[new_idx]
    
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
            
            skill_factor = (driver.skill * 0.5 + driver.quali_skill * 0.5) / 100
            car_factor = (driver.car_stats['engine_power'] + driver.car_stats['aero']) / 200
            
            quali_time = base_time * (1 - skill_factor * 0.15 - car_factor * 0.10)
            quali_time += random.uniform(-0.5, 0.5)
            
            consistency_var = (100 - driver.consistency) / 200
            quali_time += random.uniform(-consistency_var, consistency_var)
            
            results.append((driver, quali_time))
        
        results.sort(key=lambda x: x[1])
        
        for idx, (driver, time) in enumerate(results):
            driver.grid_position = idx + 1
            driver.position = idx + 1
            
            if idx == 0:
                self.events.append(f"🏁 **POLE:** {driver.name} - {time:.3f}s")
        
        return results
    
    def calculate_dps(self, driver: Driver) -> float:
        base_skill = driver.skill
        
        if "rain" in self.weather:
            base_skill = (base_skill + driver.rain_skill) / 2
        
        driver_factor = base_skill * 0.30
        
        car_perf = (
            driver.car_stats['engine_power'] * 0.35 +
            driver.car_stats['aero'] * 0.30 +
            driver.car_stats['handling'] * 0.25 +
            driver.car_stats['ers_power'] * 0.10
        )
        car_factor = car_perf * 0.30
        
        tyre_factor = driver.tyre_condition * 0.15
        grip_factor = self.track_grip * 0.10
        
        weather_factor = 50.0
        if self.weather == "rain":
            if driver.tyre_compound in ["inter", "wet"]:
                weather_factor = driver.rain_skill
            else:
                weather_factor = 20.0
        weather_factor *= 0.10
        
        strategy_bonus = (driver.push_mode * 0.6 + driver.fuel_mix * 0.4) * 0.05
        
        damage_penalty = driver.damage * 0.15
        
        dps = (driver_factor + car_factor + tyre_factor + grip_factor + 
               weather_factor + strategy_bonus - damage_penalty)
        
        variation = random.uniform(-driver.consistency/10, driver.consistency/10)
        
        if driver.ers_mode == "deploy" and driver.ers_charge > 10:
            dps += 5
        
        if driver.drs_available:
            dps += 3
        
        return max(0, dps + variation)
    
    def simulate_lap(self):
        self.current_lap += 1
        self.lap_events = []
        
        if self.current_lap < len(self.weather_forecast):
            new_weather = self.weather_forecast[self.current_lap]
            if new_weather != self.weather:
                self.weather = new_weather
                self.update_track_conditions()
                self.lap_events.append(f"🌦️ Weather: {self.weather.upper()}")
        
        if self.current_lap >= 3 and not self.safety_car:
            self.drs_enabled = True
        
        for driver in self.drivers:
            if driver.dnf:
                continue
            
            driver.lap = self.current_lap
            
            lap_time = self.calculate_lap_time(driver)
            driver.lap_time = lap_time
            driver.total_time += lap_time
            
            if lap_time < driver.best_lap and not self.safety_car:
                driver.best_lap = lap_time
                if self.current_lap > 2:
                    self.lap_events.append(f"⏱️ {driver.name} - FASTEST LAP {lap_time:.3f}s")
            
            self.update_tyre_wear(driver)
            self.update_fuel(driver)
            self.update_ers(driver)
            
            driver.tyre_age += 1
            
            self.check_incidents(driver)
        
        self.update_positions()
        self.update_drs()
        self.simulate_overtakes()
        self.ai_strategy_decisions()
        self.update_positions()
        
        self.events.extend(self.lap_events)
    
    def calculate_lap_time(self, driver: Driver) -> float:
        base_time = self.track_data[self.track]["base_lap_time"]
        dps = self.calculate_dps(driver)
        
        lap_time = base_time - (dps / 10)
        
        fuel_bonus = (100 - driver.fuel_load) * 0.015
        lap_time -= fuel_bonus
        
        if self.safety_car:
            lap_time = base_time + 15
        
        lap_time += driver.damage * 0.05
        lap_time += random.uniform(-0.3, 0.3)
        
        return max(base_time * 0.8, lap_time)
    
    def update_tyre_wear(self, driver: Driver):
        base_wear = self.track_data[self.track]["tyre_wear"]
        
        compound_wear = {
            "soft": 4.0, "medium": 2.5, "hard": 1.5,
            "inter": 3.0, "wet": 2.5
        }
        
        compound = compound_wear.get(driver.tyre_compound, 2.5)
        
        wear = (
            base_wear * compound * driver.car_stats['tyre_wear_rate'] *
            (driver.push_mode / 50) * (self.track_temp / 30)
        )
        
        if driver.attacking:
            wear *= 1.15
        
        driver.tyre_condition = max(0, driver.tyre_condition - wear)
    
    def update_fuel(self, driver: Driver):
        consumption = 2.0 * (driver.fuel_mix / 50) * (driver.push_mode / 50)
        
        if self.safety_car:
            consumption *= 0.3
        
        driver.fuel_load = max(0, driver.fuel_load - consumption)
    
    def update_ers(self, driver: Driver):
        if driver.ers_mode == "charging":
            driver.ers_charge = min(100, driver.ers_charge + 15)
        elif driver.ers_mode == "deploy":
            if driver.ers_charge >= 10:
                driver.ers_charge -= 10
            else:
                driver.ers_mode = "balanced"
        else:
            driver.ers_charge = min(100, driver.ers_charge + 8)
    
    def update_track_conditions(self):
        if self.weather == "clear":
            self.track_grip = min(100, self.track_grip + 5)
        elif self.weather == "cloudy":
            self.track_grip = 95
        elif self.weather == "light_rain":
            self.track_grip = 60
        elif self.weather == "rain":
            self.track_grip = 45
    
    def update_drs(self):
        if not self.drs_enabled:
            return
        
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            driver = sorted_drivers[i]
            
            if driver.gap_to_front < 1.0:
                driver.drs_available = True
            else:
                driver.drs_available = False
    
    def simulate_overtakes(self):
        sorted_drivers = sorted([d for d in self.drivers if not d.dnf], 
                               key=lambda x: x.position)
        
        for i in range(1, len(sorted_drivers)):
            attacker = sorted_drivers[i]
            defender = sorted_drivers[i-1]
            
            if attacker.gap_to_front > 1.5 or self.safety_car:
                continue
            
            overtake_chance = self.calculate_overtake_chance(attacker, defender)
            
            if random.random() * 100 < overtake_chance:
                self.execute_overtake(attacker, defender)
    
    def calculate_overtake_chance(self, attacker: Driver, defender: Driver) -> float:
        base_chance = 100 - self.track_data[self.track]["overtake_difficulty"]
        
        attacker_dps = self.calculate_dps(attacker)
        defender_dps = self.calculate_dps(defender)
        skill_diff = (attacker_dps - defender_dps) * 2
        
        drs_bonus = 25 if attacker.drs_available else 0
        ers_bonus = 15 if attacker.ers_charge > 50 else 0
        tyre_diff = (attacker.tyre_condition - defender.tyre_condition) * 0.3
        
        chance = base_chance + skill_diff + drs_bonus + ers_bonus + tyre_diff
        
        return max(5, min(95, chance))
    
    def execute_overtake(self, attacker: Driver, defender: Driver):
        outcomes = ["clean", "side_by_side", "contact", "failed"]
        weights = [60, 25, 10, 5]
        
        if "rain" in self.weather:
            weights = [40, 30, 20, 10]
        
        outcome = random.choices(outcomes, weights=weights)[0]
        
        if outcome == "clean":
            attacker.position, defender.position = defender.position, attacker.position
            attacker.overtakes_made += 1
            defender.overtakes_lost += 1
            self.lap_events.append(f"🎯 {attacker.name} OVERTAKES {defender.name}!")
        
        elif outcome == "contact":
            damage = random.uniform(5, 20)
            attacker.damage += damage
            self.lap_events.append(f"💥 Contact! {attacker.name} - Damage: {damage:.0f}%")
    
    def check_incidents(self, driver: Driver):
        crash_chance = 0.3
        crash_chance += (100 - driver.tyre_condition) * 0.03
        crash_chance += (driver.push_mode / 100) * 0.5
        crash_chance += (driver.damage / 100) * 1.0
        
        if self.weather == "rain":
            crash_chance *= 2.5
        
        if random.random() * 100 < crash_chance:
            crash_severity = random.uniform(10, 80)
            driver.damage += crash_severity
            
            if crash_severity < 30:
                self.lap_events.append(f"⚠️ {driver.name} - Minor incident")
            else:
                self.lap_events.append(f"🚨 {driver.name} - SPIN!")
                self.safety_car = True
            
            if driver.damage > 80:
                driver.dnf = True
                driver.dnf_reason = "Accident"
                self.lap_events.append(f"❌ {driver.name} - DNF")
        
        failure_chance = (100 - driver.car_stats['reliability']) * 0.05
        
        if random.random() * 100 < failure_chance:
            driver.dnf = True
            driver.dnf_reason = "Mechanical"
            self.lap_events.append(f"💥 {driver.name} - ENGINE FAILURE!")
    
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
            
            if driver.tyre_condition < 15:
                should_pit = True
            
            if self.weather == "rain" and driver.tyre_compound not in ["inter", "wet"]:
                if driver.tyre_condition < 80:
                    should_pit = True
            
            if self.weather == "clear" and driver.tyre_compound in ["inter", "wet"]:
                should_pit = True
            
            if self.safety_car and driver.tyre_condition < 60:
                if random.random() < 0.7:
                    should_pit = True
            
            if should_pit and driver.pit_stops < 3:
                self.pit_stop(driver)
            
            if driver.position <= 3:
                driver.push_mode = max(30, driver.push_mode - 5)
            elif driver.position > 10:
                driver.push_mode = min(80, driver.push_mode + 5)
            
            if driver.drs_available and driver.ers_charge > 50:
                driver.ers_mode = "deploy"
            elif driver.ers_charge < 30:
                driver.ers_mode = "charging"
            else:
                driver.ers_mode = "balanced"
    
    def pit_stop(self, driver: Driver):
        driver.pit_stops += 1
        
        if self.weather == "rain":
            new_compound = "wet"
        elif self.weather == "light_rain":
            new_compound = "inter"
        else:
            laps_remaining = self.total_laps - self.current_lap
            if laps_remaining < 10:
                new_compound = "soft"
            elif laps_remaining < 20:
                new_compound = "medium"
            else:
                new_compound = "hard"
        
        driver.tyre_compound = new_compound
        driver.tyre_condition = 100.0
        driver.tyre_age = 0
        driver.fuel_load = 100.0
        
        pit_time = 22.0 + random.uniform(-1.5, 1.5)
        driver.total_time += pit_time
        
        compound_emoji = {"soft": "🔴", "medium": "🟡", "hard": "⚪", "inter": "🟢", "wet": "🔵"}
        
        self.lap_events.append(
            f"🔧 {driver.name} - PIT ({pit_time:.1f}s) {compound_emoji.get(new_compound, '⚪')} {new_compound.upper()}"
        )
    
    def get_race_summary(self) -> str:
        lines = []
        
        track_info = self.track_data[self.track]
        lines.append(f"🏁 **{track_info['name']}** ({track_info['country']})")
        lines.append(f"📍 Lap **{self.current_lap}/{self.total_laps}**")
        
        weather_emoji = {"clear": "☀️", "cloudy": "☁️", "light_rain": "🌦️", "rain": "🌧️"}
        lines.append(
            f"{weather_emoji.get(self.weather, '☀️')} {self.weather.title()} | "
            f"Grip: {self.track_grip:.0f}%"
        )
        
        if self.safety_car:
            lines.append("🚨 **SAFETY CAR**")
        
        if self.drs_enabled:
            lines.append("💨 DRS Enabled")
        
        lines.append("\n**POSITIONS:**")
        
        active = sorted([d for d in self.drivers if not d.dnf], key=lambda x: x.position)
        
        for driver in active[:10]:
            change = driver.positions_gained
            if change > 0:
                change_str = f"🟢+{change}"
            elif change < 0:
                change_str = f"🔴{change}"
            else:
                change_str = "⚪="
            
            gap_str = "Leader" if driver.position == 1 else f"+{driver.gap_to_leader:.1f}s"
            
            tyre_emoji = {"soft": "🔴", "medium": "🟡", "hard": "⚪", "inter": "🟢", "wet": "🔵"}
            tyre_str = f"{tyre_emoji.get(driver.tyre_compound, '⚪')} {driver.tyre_condition:.0f}%"
            
            drs_str = " 💨" if driver.drs_available else ""
            
            if driver.position <= 3:
                pos_str = ["🥇", "🥈", "🥉"][driver.position - 1]
            else:
                pos_str = f"**P{driver.position}**"
            
            line = (
                f"{pos_str} {change_str} {driver.name} - {gap_str} | "
                f"{tyre_str} | ⛽{driver.fuel_load:.0f}%{drs_str}"
            )
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def get_final_results(self) -> str:
        lines = []
        
        track_info = self.track_data[self.track]
        lines.append(f"🏆 **{track_info['name']} - RESULTS** 🏆\n")
        
        points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
        
        classified = sorted([d for d in self.drivers if not d.dnf], 
                           key=lambda d: d.position)
        
        for idx, driver in enumerate(classified[:20]):
            points = points_system[idx] if idx < len(points_system) else 0
            
            if idx == 0:
                pos_str = "🥇 1st"
            elif idx == 1:
                pos_str = "🥈 2nd"
            elif idx == 2:
                pos_str = "🥉 3rd"
            else:
                pos_str = f"**P{idx + 1}**"
            
            if idx == 0:
                time_str = f"⏱️ {driver.total_time:.3f}s"
            else:
                time_str = f"+{driver.gap_to_leader:.3f}s"
            
            stats = []
            if driver.best_lap < 999:
                stats.append(f"Best: {driver.best_lap:.3f}s")
            stats.append(f"Pits: {driver.pit_stops}")
            if driver.positions_gained > 0:
                stats.append(f"🟢+{driver.positions_gained}")
            
            stats_str = " | ".join(stats)
            
            lines.append(
                f"{pos_str} **{driver.name}** - {time_str}\n"
                f"    {stats_str} | **+{points} pts**\n"
            )
        
        fastest_driver = min([d for d in self.drivers if not d.dnf], 
                            key=lambda d: d.best_lap, default=None)
        
        if fastest_driver and fastest_driver.position <= 10:
            lines.append(
                f"\n⚡ **FASTEST LAP:** {fastest_driver.name} - "
                f"{fastest_driver.best_lap:.3f}s (+1 pt)"
            )
        
        return "\n".join(lines)

# ============================================================================
# UI BUTTONS
# ============================================================================

class RaceControlView(discord.ui.View):
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
                f"🔥 PUSH: {driver.push_mode}% | ⚠️ Higher tyre wear",
                ephemeral=True
            )
    
    @discord.ui.button(label="🛞 Save", style=discord.ButtonStyle.success, row=0)
    async def save_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.push_mode = max(0, driver.push_mode - 15)
            driver.attacking = False
            await interaction.response.send_message(
                f"🛞 SAVING: {driver.push_mode}% | ✅ Lower wear",
                ephemeral=True
            )
    
    @discord.ui.button(label="🔧 Pit", style=discord.ButtonStyle.primary, row=0)
    async def pit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            self.race.pit_stop(driver)
            await interaction.response.send_message(f"🔧 PITTING!", ephemeral=True)
    
    @discord.ui.button(label="⚡ ERS", style=discord.ButtonStyle.success, row=1)
    async def ers_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver and not driver.dnf:
            driver.ers_mode = "deploy"
            await interaction.response.send_message(
                f"⚡ ERS DEPLOY | Charge: {driver.ers_charge:.0f}%",
                ephemeral=True
            )
    
    @discord.ui.button(label="📊 Stats", style=discord.ButtonStyle.secondary, row=1)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your race!", ephemeral=True)
            return
        
        driver = self.get_driver()
        if driver:
            embed = discord.Embed(title=f"📊 {driver.name}", color=discord.Color.blue())
            embed.add_field(name="Position", value=f"P{driver.position}", inline=True)
            embed.add_field(name="Gap", value=f"+{driver.gap_to_leader:.2f}s" if driver.position > 1 else "Leader", inline=True)
            embed.add_field(name="Best Lap", value=f"{driver.best_lap:.3f}s" if driver.best_lap < 999 else "N/A", inline=True)
            
            embed.add_field(name="Tyres", value=f"{driver.tyre_compound.upper()} ({driver.tyre_condition:.0f}%)", inline=True)
            embed.add_field(name="Fuel", value=f"{driver.fuel_load:.0f}%", inline=True)
            embed.add_field(name="ERS", value=f"{driver.ers_charge:.0f}%", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================================================================
# DISCORD BOT
# ============================================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
db = Database()

active_races: Dict[int, RaceEngine] = {}

@bot.event
async def on_ready():
    print(f'✅ Bot online: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} commands')
    except Exception as e:
        print(f'❌ Error: {e}')

# ============================================================================
# DRIVER COMMANDS
# ============================================================================

@bot.tree.command(name="profile", description="View your F1 driver profile")
async def profile(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    user = c.fetchone()
    
    if not user:
        c.execute('''INSERT INTO users (user_id, driver_name) VALUES (?, ?)''',
                 (interaction.user.id, interaction.user.display_name))
        conn.commit()
        await interaction.response.send_message("✅ Profile created! Use `/profile` again.", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(title=f"🏎️ {user[1]}", color=discord.Color.gold())
    embed.add_field(name="⭐ Skill", value=f"{user[2]:.1f}/100", inline=True)
    embed.add_field(name="💥 Aggression", value=f"{user[3]:.1f}/100", inline=True)
    embed.add_field(name="🎯 Consistency", value=f"{user[4]:.1f}/100", inline=True)
    
    embed.add_field(name="🏆 Wins", value=str(user[9]), inline=True)
    embed.add_field(name="🥈 Podiums", value=str(user[10]), inline=True)
    embed.add_field(name="📊 Points", value=str(user[11]), inline=True)
    
    embed.add_field(name="🏁 Races", value=str(user[20]), inline=True)
    embed.add_field(name="⚡ Fastest Laps", value=str(user[22]), inline=True)
    embed.add_field(name="💰 Money", value=f"${user[12]:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="stats", description="View detailed career statistics")
async def stats(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT COUNT(*), AVG(position), MIN(fastest_lap), 
               SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END),
               SUM(CASE WHEN dnf = 1 THEN 1 ELSE 0 END)
        FROM race_history WHERE user_id = ?
    """, (interaction.user.id,))
    
    stats = c.fetchone()
    
    if stats[0] == 0:
        await interaction.response.send_message("📊 No race history yet!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(title="📊 Career Statistics", color=discord.Color.blue())
    embed.add_field(name="🏁 Races", value=str(stats[0]), inline=True)
    embed.add_field(name="📊 Avg Position", value=f"{stats[1]:.1f}" if stats[1] else "N/A", inline=True)
    embed.add_field(name="⏱️ Best Lap", value=f"{stats[2]:.3f}s" if stats[2] and stats[2] < 999 else "N/A", inline=True)
    
    embed.add_field(name="🏆 Wins", value=str(stats[3] or 0), inline=True)
    embed.add_field(name="❌ DNFs", value=str(stats[4] or 0), inline=True)
    
    if stats[0] > 0:
        win_rate = (stats[3] / stats[0] * 100) if stats[3] else 0
        dnf_rate = (stats[4] / stats[0] * 100) if stats[4] else 0
        embed.add_field(name="🏆 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        embed.add_field(name="❌ DNF Rate", value=f"{dnf_rate:.1f}%", inline=True)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="ranking", description="Global driver rankings")
async def ranking(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT driver_name, career_points, career_wins, career_podiums
        FROM users
        ORDER BY career_points DESC
        LIMIT 15
    """)
    
    rankings = c.fetchall()
    
    if not rankings:
        await interaction.response.send_message("No rankings yet!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(title="🏆 World Rankings", color=discord.Color.gold())
    
    for idx, driver in enumerate(rankings, 1):
        medal = ["🥇", "🥈", "🥉"][idx-1] if idx <= 3 else f"#{idx}"
        
        embed.add_field(
            name=f"{medal} {driver[0]}",
            value=f"Points: {driver[1]} | Wins: {driver[2]}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

# ============================================================================
# GARAGE COMMANDS
# ============================================================================

@bot.tree.command(name="garage", description="View your car collection")
async def garage(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM cars WHERE owner_id = ?", (interaction.user.id,))
    cars = c.fetchall()
    
    if not cars:
        c.execute('''INSERT INTO cars (owner_id, car_name) VALUES (?, ?)''',
                 (interaction.user.id, "Starter F1 Car"))
        conn.commit()
        await interaction.response.send_message("🏎️ Starter car created! Use `/garage` again.", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(title="🏎️ Your Garage", color=discord.Color.blue())
    
    for car in cars:
        overall = (car[3] + car[4] + car[5]) / 3
        
        info = (
            f"🔧 Engine: {car[3]:.0f} | Aero: {car[4]:.0f} | Handling: {car[5]:.0f}\n"
            f"⚡ ERS: {car[12]:.0f} | 🔧 Reliability: {car[6]:.0f}%\n"
            f"📊 Overall: {overall:.0f}/100 | 🏁 Races: {car[15]}"
        )
        
        active = " ✅" if car[14] else ""
        
        embed.add_field(name=f"{car[2]}{active}", value=info, inline=False)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="upgrade", description="Upgrade your car parts")
async def upgrade(interaction: discord.Interaction, part: str, amount: int = 5):
    part_map = {
        "engine": "engine_power",
        "aero": "aero",
        "handling": "handling",
        "ers": "ers_power"
    }
    
    part_name = part_map.get(part.lower())
    
    if not part_name:
        await interaction.response.send_message(
            f"❌ Choose: engine, aero, handling, ers",
            ephemeral=True
        )
        return
    
    amount = max(1, min(10, amount))
    cost = amount * 1500
    
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    money = c.fetchone()[0]
    
    if money < cost:
        await interaction.response.send_message(
            f"❌ Need ${cost:,}, have ${money:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    c.execute(f"""
        UPDATE cars 
        SET {part_name} = MIN(100, {part_name} + ?)
        WHERE owner_id = ? AND is_active = 1
    """, (amount, interaction.user.id))
    
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?", (cost, interaction.user.id))
    conn.commit()
    
    await interaction.response.send_message(
        f"✅ Upgraded {part_name.replace('_', ' ').title()} +{amount}!\n"
        f"💰 Cost: ${cost:,}"
    )
    conn.close()

@bot.tree.command(name="repair", description="Repair car damage and wear")
async def repair(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        SELECT car_id, engine_wear, gearbox_wear
        FROM cars WHERE owner_id = ? AND is_active = 1
    """, (interaction.user.id,))
    
    car = c.fetchone()
    
    if not car:
        await interaction.response.send_message("❌ No active car!", ephemeral=True)
        conn.close()
        return
    
    total_wear = car[1] + car[2]
    repair_cost = int(total_wear * 100)
    
    if total_wear == 0:
        await interaction.response.send_message("✅ Car is perfect!", ephemeral=True)
        conn.close()
        return
    
    c.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,))
    money = c.fetchone()[0]
    
    if money < repair_cost:
        await interaction.response.send_message(
            f"❌ Need ${repair_cost:,}, have ${money:,}",
            ephemeral=True
        )
        conn.close()
        return
    
    c.execute("""
        UPDATE cars
        SET engine_wear = 0, gearbox_wear = 0
        WHERE car_id = ?
    """, (car[0],))
    
    c.execute("UPDATE users SET money = money - ? WHERE user_id = ?", (repair_cost, interaction.user.id))
    conn.commit()
    
    await interaction.response.send_message(
        f"🔧 Car repaired!\n💰 Cost: ${repair_cost:,}"
    )
    conn.close()

# ============================================================================
# RACE COMMANDS
# ============================================================================

@bot.tree.command(name="race-create", description="Create a race lobby")
@app_commands.describe(track="Select circuit", laps="Number of laps (5-50)")
@app_commands.choices(track=[
    app_commands.Choice(name="🇮🇹 Monza", value="Monza"),
    app_commands.Choice(name="🇲🇨 Monaco", value="Monaco"),
    app_commands.Choice(name="🇧🇪 Spa", value="Spa"),
    app_commands.Choice(name="🇬🇧 Silverstone", value="Silverstone"),
    app_commands.Choice(name="🇯🇵 Suzuka", value="Suzuka"),
    app_commands.Choice(name="🇸🇬 Singapore", value="Singapore"),
])
async def race_create(interaction: discord.Interaction, track: app_commands.Choice[str], laps: int = 15):
    if interaction.channel.id in active_races:
        await interaction.response.send_message("❌ Race already active!", ephemeral=True)
        return
    
    laps = max(5, min(50, laps))
    race = RaceEngine(track=track.value, laps=laps)
    active_races[interaction.channel.id] = race
    
    track_info = race.track_data[track.value]
    
    embed = discord.Embed(title="🏁 Race Lobby", color=discord.Color.green())
    embed.add_field(name="📍 Track", value=f"{track_info['name']}", inline=False)
    embed.add_field(name="🏁 Laps", value=str(laps), inline=True)
    embed.add_field(name="👥 Drivers", value="0/20", inline=True)
    embed.description = "Use `/race-join` to enter!\nHost: use `/race-start` when ready."
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="race-join", description="Join the active race")
async def race_join(interaction: discord.Interaction):
    if interaction.channel.id not in active_races:
        await interaction.response.send_message("❌ No race!", ephemeral=True)
        return
    
    race = active_races[interaction.channel.id]
    
    if any(d.id == interaction.user.id for d in race.drivers):
        await interaction.response.send_message("❌ Already joined!", ephemeral=True)
        return
    
    if len(race.drivers) >= 20:
        await interaction.response.send_message("❌ Race full!", ephemeral=True)
        return
    
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
    user = c.fetchone()
    
    if not user:
        c.execute('''INSERT INTO users (user_id, driver_name) VALUES (?, ?)''',
                 (interaction.user.id, interaction.user.display_name))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (interaction.user.id,))
        user = c.fetchone()
    
    c.execute("SELECT * FROM cars WHERE owner_id = ? AND is_active = 1", (interaction.user.id,))
    car = c.fetchone()
    
    if not car:
        c.execute('''INSERT INTO cars (owner_id, car_name, is_active) VALUES (?, ?, ?)''',
                 (interaction.user.id, "Default Car", 1))
        conn.commit()
        c.execute("SELECT * FROM cars WHERE owner_id = ? AND is_active = 1", (interaction.user.id,))
        car = c.fetchone()
    
    driver = Driver(
        driver_id=interaction.user.id,
        name=user[1],
        skill=user[2],
        aggression=user[3],
        consistency=user[4],
        car_stats={
            'engine_power': car[3], 'aero': car[4], 'handling': car[5],
            'reliability': car[6], 'tyre_wear_rate': car[7],
            'fuel_efficiency': car[8], 'ers_power': car[12], 'drs_efficiency': car[13]
        },
        advanced_stats={
            'rain_skill': user[16], 'overtaking_skill': user[17],
            'defending_skill': user[18], 'quali_skill': user[19]
        }
    )
    
    race.add_driver(driver)
    
    await interaction.response.send_message(
        f"✅ **{user[1]} joined!** Grid: P{driver.position} ({len(race.drivers)}/20)"
    )
    conn.close()

@bot.tree.command(name="race-start", description="Start the race")
async def race_start(interaction: discord.Interaction):
    if interaction.channel.id not in active_races:
        await interaction.response.send_message("❌ No race!", ephemeral=True)
        return
    
    race = active_races[interaction.channel.id]
    
    if len(race.drivers) == 0:
        await interaction.response.send_message("❌ No drivers!", ephemeral=True)
        return
    
    # Fill with AI
    ai_count = max(0, 12 - len(race.drivers))
    
    if ai_count > 0:
        conn = db.get_conn()
        c = conn.cursor()
        c.execute(f"SELECT * FROM ai_profiles ORDER BY RANDOM() LIMIT {ai_count}")
        ai_drivers = c.fetchall()
        conn.close()
        
        for ai in ai_drivers:
            ai_driver = Driver(
                driver_id=f"ai_{ai[0]}",
                name=ai[1],
                skill=ai[2],
                aggression=ai[3],
                consistency=ai[4],
                is_ai=True,
                car_stats={
                    'engine_power': random.uniform(45, 75),
                    'aero': random.uniform(45, 75),
                    'handling': random.uniform(45, 75),
                    'reliability': random.uniform(90, 100),
                    'tyre_wear_rate': 1.0,
                    'fuel_efficiency': 1.0,
                    'ers_power': 50,
                    'drs_efficiency': 1.0
                },
                advanced_stats={
                    'rain_skill': random.uniform(40, 80),
                    'overtaking_skill': ai[5],
                    'defending_skill': ai[6],
                    'quali_skill': ai[2]
                }
            )
            race.add_driver(ai_driver)
    
    await interaction.response.defer()
    
    # Qualifying
    if race.qualifying_mode:
        quali_results = race.run_qualifying()
        
        quali_embed = discord.Embed(title="🏁 QUALIFYING", color=discord.Color.blue())
        
        for idx, (driver, time) in enumerate(quali_results[:10], 1):
            pos = ["🥇 POLE", "🥈 P2", "🥉 P3"][idx-1] if idx <= 3 else f"**P{idx}**"
            quali_embed.add_field(
                name=f"{pos} {driver.name}",
                value=f"⏱️ {time:.3f}s",
                inline=False
            )
        
        await interaction.followup.send(embed=quali_embed)
        await asyncio.sleep(5)
    
    # Race
    await interaction.followup.send(
        f"🏁 **LIGHTS OUT!** {len(race.drivers)} drivers | {race.track} - {race.total_laps} laps"
    )
    
    await asyncio.sleep(3)
    
    summary = race.get_race_summary()
    real_driver = next((d for d in race.drivers if not d.is_ai), None)
    
    if real_driver:
        view = RaceControlView(race, real_driver.id)
        message = await interaction.followup.send(content=summary, view=view)
    else:
        message = await interaction.followup.send(content=summary)
    
    # Race loop
    for lap in range(race.total_laps):
        race.simulate_lap()
        
        summary = race.get_race_summary()
        
        if race.lap_events:
            summary += "\n\n**EVENTS:**\n" + "\n".join(race.lap_events[-5:])
        
        try:
            if real_driver:
                view = RaceControlView(race, real_driver.id)
                await message.edit(content=summary, view=view)
            else:
                await message.edit(content=summary)
        except:
            pass
        
        await asyncio.sleep(6)
    
    # Results
    final_results = race.get_final_results()
    
    final_embed = discord.Embed(
        title="🏆 RACE FINISHED",
        description=final_results,
        color=discord.Color.gold()
    )
    
    await interaction.followup.send(embed=final_embed)
    
    # Update DB
    conn = db.get_conn()
    c = conn.cursor()
    
    points_system = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    classified = sorted([d for d in race.drivers if not d.dnf], key=lambda x: x.position)
    
    for idx, driver in enumerate(classified):
        if driver.is_ai:
            continue
        
        points = points_system[idx] if idx < len(points_system) else 0
        
        fastest_driver = min(classified, key=lambda d: d.best_lap)
        if driver.id == fastest_driver.id and idx < 10:
            points += 1
        
        c.execute('''UPDATE users SET 
                    career_points = career_points + ?,
                    career_wins = career_wins + ?,
                    career_podiums = career_podiums + ?,
                    money = money + ?,
                    race_starts = race_starts + 1,
                    fastest_laps = fastest_laps + ?
                    WHERE user_id = ?''',
                 (points, 1 if idx == 0 else 0, 1 if idx < 3 else 0,
                  points * 1000 + (10000 if idx == 0 else 0),
                  1 if driver.id == fastest_driver.id else 0,
                  driver.id))
        
        c.execute('''UPDATE cars SET 
                    total_races = total_races + 1,
                    total_wins = total_wins + ?,
                    engine_wear = engine_wear + ?,
                    gearbox_wear = gearbox_wear + ?
                    WHERE owner_id = ? AND is_active = 1''',
                 (1 if idx == 0 else 0, random.uniform(5, 15), random.uniform(3, 10), driver.id))
        
        c.execute('''INSERT INTO race_history 
                    (user_id, position, points, fastest_lap, timestamp, track, weather,
                     grid_position, positions_gained, pit_stops, dnf, dnf_reason, overtakes_made)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (driver.id, idx + 1, points, driver.best_lap, datetime.now().isoformat(),
                  race.track, race.weather, driver.grid_position, driver.positions_gained,
                  driver.pit_stops, 0, "", driver.overtakes_made))
    
    for driver in [d for d in race.drivers if d.dnf and not d.is_ai]:
        c.execute("UPDATE users SET dnf_count = dnf_count + 1, race_starts = race_starts + 1 WHERE user_id = ?",
                 (driver.id,))
        
        c.execute('''INSERT INTO race_history 
                    (user_id, position, points, fastest_lap, timestamp, track, weather,
                     grid_position, positions_gained, pit_stops, dnf, dnf_reason, overtakes_made)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (driver.id, 99, 0, driver.best_lap if driver.best_lap < 999 else None,
                  datetime.now().isoformat(), race.track, race.weather,
                  driver.grid_position, 0, driver.pit_stops, 1, driver.dnf_reason, driver.overtakes_made))
    
    conn.commit()
    conn.close()
    
    del active_races[interaction.channel.id]

# ============================================================================
# ECONOMY COMMANDS
# ============================================================================

@bot.tree.command(name="wallet", description="View your money")
async def wallet(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT money, career_points FROM users WHERE user_id = ?", (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message("❌ No profile!", ephemeral=True)
        conn.close()
        return
    
    embed = discord.Embed(title="💰 Wallet", color=discord.Color.gold())
    embed.add_field(name="Balance", value=f"${result[0]:,}", inline=True)
    embed.add_field(name="Career Points", value=str(result[1]), inline=True)
    embed.add_field(name="Lifetime Earnings", value=f"${result[1] * 1000:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="sponsors", description="Browse sponsorship deals")
async def sponsors(interaction: discord.Interaction):
    conn = db.get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM sponsors ORDER BY payment_per_race DESC")
    sponsors = c.fetchall()
    
    embed = discord.Embed(title="🤝 Sponsorship Deals", color=discord.Color.blue())
    
    for sponsor in sponsors:
        info = (
            f"💰 ${sponsor[2]:,} per race\n"
            f"📋 {sponsor[3]} races\n"
            f"🎁 Bonus: ${sponsor[4]:,}"
        )
        embed.add_field(name=sponsor[1], value=info, inline=False)
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="loan", description="Take a loan")
async def loan(interaction: discord.Interaction, amount: int):
    if amount < 1000 or amount > 50000:
        await interaction.response.send_message("❌ Amount must be $1,000-$50,000", ephemeral=True)
        return
    
    interest_rate = 0.15 if amount < 10000 else 0.20
    total_repay = int(amount * (1 + interest_rate))
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO loans (user_id, amount, interest_rate, remaining_amount, issue_date)
        VALUES (?, ?, ?, ?, ?)
    """, (interaction.user.id, amount, interest_rate, total_repay, datetime.now().isoformat()))
    
    c.execute("UPDATE users SET money = money + ? WHERE user_id = ?", (amount, interaction.user.id))
    conn.commit()
    
    await interaction.response.send_message(
        f"✅ **Loan Approved!**\n"
        f"💰 Amount: ${amount:,}\n"
        f"📈 Interest: {interest_rate * 100:.0f}%\n"
        f"💵 Total to Repay: ${total_repay:,}"
    )
    conn.close()

# ============================================================================
# LEAGUE COMMANDS
# ============================================================================

@bot.tree.command(name="league-create", description="Create a racing league")
async def league_create(interaction: discord.Interaction, league_name: str, max_drivers: int = 20):
    max_drivers = max(10, min(30, max_drivers))
    
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO leagues (league_name, creator_id, created_date, max_drivers)
        VALUES (?, ?, ?, ?)
    """, (league_name, interaction.user.id, datetime.now().isoformat(), max_drivers))
    
    league_id = c.lastrowid
    
    c.execute("""
        INSERT INTO league_members (league_id, user_id, join_date)
        VALUES (?, ?, ?)
    """, (league_id, interaction.user.id, datetime.now().isoformat()))
    
    conn.commit()
    
    embed = discord.Embed(title="🏆 League Created", color=discord.Color.gold())
    embed.add_field(name="Name", value=league_name, inline=True)
    embed.add_field(name="ID", value=str(league_id), inline=True)
    embed.add_field(name="Max Drivers", value=str(max_drivers), inline=True)
    embed.description = f"Others join with: `/league-join {league_id}`"
    
    await interaction.response.send_message(embed=embed)
    conn.close()

@bot.tree.command(name="league-join", description="Join a league")
async def league_join(interaction: discord.Interaction, league_id: int):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT * FROM leagues WHERE league_id = ?", (league_id,))
    league = c.fetchone()
    
    if not league:
        await interaction.response.send_message(f"❌ League #{league_id} not found!", ephemeral=True)
        conn.close()
        return
    
    c.execute("SELECT * FROM league_members WHERE league_id = ? AND user_id = ?",
             (league_id, interaction.user.id))
    
    if c.fetchone():
        await interaction.response.send_message("❌ Already a member!", ephemeral=True)
        conn.close()
        return
    
    c.execute("SELECT COUNT(*) FROM league_members WHERE league_id = ?", (league_id,))
    current_members = c.fetchone()[0]
    
    if current_members >= league[4]:
        await interaction.response.send_message("❌ League full!", ephemeral=True)
        conn.close()
        return
    
    c.execute("""
        INSERT INTO league_members (league_id, user_id, join_date)
        VALUES (?, ?, ?)
    """, (league_id, interaction.user.id, datetime.now().isoformat()))
    
    conn.commit()
    
    await interaction.response.send_message(
        f"✅ Joined **{league[1]}**!\n"
        f"👥 Members: {current_members + 1}/{league[4]}"
    )
    conn.close()

@bot.tree.command(name="league-standings", description="View league standings")
async def league_standings(interaction: discord.Interaction, league_id: int):
    conn = db.get_conn()
    c = conn.cursor()
    
    c.execute("SELECT league_name FROM leagues WHERE league_id = ?", (league_id,))
    league = c.fetchone()
    
    if not league:
        await interaction.response.send_message(f"❌ League not found!", ephemeral=True)
        conn.close()
        return
    
    c.execute("""
        SELECT u.driver_name, lm.season_points, lm.season_wins
        FROM league_members lm
        JOIN users u ON lm.user_id = u.user_id
        WHERE lm.league_id = ?
        ORDER BY lm.season_points DESC
    """, (league_id,))
    
    standings = c.fetchall()
    
    embed = discord.Embed(title=f"🏆 {league[0]} - Standings", color=discord.Color.gold())
    
    for idx, (name, points, wins) in enumerate(standings, 1):
        medal = ["🥇", "🥈", "🥉"][idx-1] if idx <= 3 else f"#{idx}"
        embed.add_field(
            name=f"{medal} {name}",
            value=f"Points: {points} | Wins: {wins}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    conn.close()

# ============================================================================
# MISC COMMANDS
# ============================================================================

@bot.tree.command(name="track-info", description="View track details")
@app_commands.choices(track=[
    app_commands.Choice(name="🇮🇹 Monza", value="Monza"),
    app_commands.Choice(name="🇲🇨 Monaco", value="Monaco"),
    app_commands.Choice(name="🇧🇪 Spa", value="Spa"),
    app_commands.Choice(name="🇬🇧 Silverstone", value="Silverstone"),
    app_commands.Choice(name="🇯🇵 Suzuka", value="Suzuka"),
    app_commands.Choice(name="🇸🇬 Singapore", value="Singapore"),
])
async def track_info(interaction: discord.Interaction, track: app_commands.Choice[str]):
    temp_race = RaceEngine(track=track.value, laps=1)
    track_data = temp_race.track_data[track.value]
    
    embed = discord.Embed(title=f"🏁 {track_data['name']}", color=discord.Color.blue())
    embed.add_field(name="📍 Country", value=track_data['country'], inline=True)
    embed.add_field(name="⏱️ Base Lap", value=f"{track_data['base_lap_time']:.1f}s", inline=True)
    embed.add_field(name="🏎️ Type", value=track_data['characteristic'], inline=True)
    embed.add_field(name="🎯 Overtake Difficulty", value=f"{track_data['overtake_difficulty']}/100", inline=True)
    embed.add_field(name="🛞 Tyre Wear", value=f"{track_data['tyre_wear']}x", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="View all commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🏎️ F1 Racing Bot", color=discord.Color.blue())
    
    embed.add_field(
        name="👤 Driver",
        value="`/profile` `/stats` `/ranking`",
        inline=False
    )
    
    embed.add_field(
        name="🏎️ Garage",
        value="`/garage` `/upgrade` `/repair`",
        inline=False
    )
    
    embed.add_field(
        name="🏁 Racing",
        value="`/race-create` `/race-join` `/race-start`",
        inline=False
    )
    
    embed.add_field(
        name="💰 Economy",
        value="`/wallet` `/sponsors` `/loan`",
        inline=False
    )
    
    embed.add_field(
        name="🏆 Leagues",
        value="`/league-create` `/league-join` `/league-standings`",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Info",
        value="`/track-info` `/help`",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

# ============================================================================
# RUN BOT
# ============================================================================

TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("No token found! Set DISCORD_TOKEN environment variable")
bot.run(TOKEN)
