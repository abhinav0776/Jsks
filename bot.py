
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import aiohttp

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='+', intents=intents)

# Data storage paths
DATA_DIR = 'bot_data'
TEAMS_FILE = f'{DATA_DIR}/teams.json'
PLAYERS_FILE = f'{DATA_DIR}/players.json'
FANTASY_TEAMS_FILE = f'{DATA_DIR}/fantasy_teams.json'
STOCKS_FILE = f'{DATA_DIR}/stocks.json'
TRANSACTIONS_FILE = f'{DATA_DIR}/transactions.json'
CONFIG_FILE = f'{DATA_DIR}/config.json'
BANS_FILE = f'{DATA_DIR}/bans.json'
MATCHES_FILE = f'{DATA_DIR}/matches.json'
PREDICTIONS_FILE = f'{DATA_DIR}/predictions.json'
TRANSFERS_FILE = f'{DATA_DIR}/transfers.json'
LOANS_FILE = f'{DATA_DIR}/loans.json'

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize data files
def init_data_files():
    files = {
        TEAMS_FILE: {},
        PLAYERS_FILE: {},
        FANTASY_TEAMS_FILE: {},
        STOCKS_FILE: {},
        TRANSACTIONS_FILE: [],
        BANS_FILE: {},
        CONFIG_FILE: {'servers': {}},
        MATCHES_FILE: {},
        PREDICTIONS_FILE: {},
        TRANSFERS_FILE: {},
        LOANS_FILE: {}
    }
    for file_path, default_data in files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)

init_data_files()

# Helper functions
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_server_config(guild_id):
    config = load_json(CONFIG_FILE)
    guild_id_str = str(guild_id)
    if guild_id_str not in config['servers']:
        config['servers'][guild_id_str] = {
            'prefix': '+',
            'transaction_channel': None,
            'team_logs_channel': None,
            'starting_balance': 50000,
            'base_card_value': 1000,
            'max_fantasy_size': 11,
            'min_fantasy_size': 5
        }
        save_json(CONFIG_FILE, config)
    return config['servers'][guild_id_str]

def get_player_data(user_id, guild_id):
    players = load_json(PLAYERS_FILE)
    key = f"{guild_id}_{user_id}"
    if key not in players:
        config = get_server_config(guild_id)
        players[key] = {
            'user_id': user_id,
            'guild_id': guild_id,
            'balance': config['starting_balance'],
            'team_id': None,
            'card_value': config['base_card_value'],
            'created_at': datetime.now().isoformat()
        }
        save_json(PLAYERS_FILE, players)
    return players[key]

def update_player_data(user_id, guild_id, data):
    players = load_json(PLAYERS_FILE)
    key = f"{guild_id}_{user_id}"
    players[key] = data
    save_json(PLAYERS_FILE, players)

def get_stock_price(user_id, guild_id):
    """Get the current stock price for a user"""
    stocks = load_json(STOCKS_FILE)
    key = f"{guild_id}_{user_id}"
    if key not in stocks:
        config = get_server_config(guild_id)
        stocks[key] = {
            'user_id': user_id,
            'price': config['base_card_value'],
            'change_percent': 0
        }
        save_json(STOCKS_FILE, stocks)
    return stocks[key]['price']

def update_stock_price(user_id, guild_id, new_price):
    stocks = load_json(STOCKS_FILE)
    key = f"{guild_id}_{user_id}"
    old_price = stocks.get(key, {}).get('price', new_price)
    change = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
    stocks[key] = {
        'user_id': user_id,
        'price': new_price,
        'change_percent': round(change, 2)
    }
    save_json(STOCKS_FILE, stocks)

def log_transaction(guild_id, transaction_type, details):
    transactions = load_json(TRANSACTIONS_FILE)
    transactions.append({
        'guild_id': guild_id,
        'type': transaction_type,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    save_json(TRANSACTIONS_FILE, transactions)

# Bot Events
@bot.event
async def on_ready():
    print(f'⚽ Hand Football Support Bot is ready!')
    print(f'Logged in as {bot.user}')
    print(f'Bot is in {len(bot.guilds)} servers')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# Tutorial Command
@bot.hybrid_command(name='tutorial', description='View the interactive bot tutorial')
async def tutorial(ctx):
    """Display an interactive tutorial"""
    
    class TutorialView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
            self.current_page = 0
            self.pages = [
                {
                    'title': '⚽ Hand Football Support Bot - Tutorial',
                    'description': 'Welcome to Hand Football Support Bot! This bot helps you manage fantasy teams of real Discord users.',
                    'fields': [
                        {'name': '📚 What is this bot?', 'value': 'Create fantasy teams by buying and selling "cards" of real server members. Build your dream team!', 'inline': False},
                        {'name': '💡 Getting Started', 'value': 'Use the buttons below to navigate through this tutorial.', 'inline': False}
                    ]
                },
                {
                    'title': '👤 Player Management',
                    'description': 'Commands for managing your account',
                    'fields': [
                        {'name': '+register', 'value': 'Create your account and get starting balance', 'inline': False},
                        {'name': '+balance or +bal', 'value': 'Check your current balance', 'inline': False},
                        {'name': '+daily', 'value': 'Claim your daily reward', 'inline': False},
                        {'name': '+addbalance @user <amount>', 'value': 'Add balance to a user (Admin only)', 'inline': False},
                        {'name': '+removebalance @user <amount>', 'value': 'Remove balance from a user (Admin only)', 'inline': False},
                        {'name': '+card @user', 'value': 'Generate player card for a user', 'inline': False}
                    ]
                },
                {
                    'title': '🏆 Team Commands',
                    'description': 'Create and manage your team',
                    'fields': [
                        {'name': '+createteam <name>', 'value': 'Create a new team', 'inline': False},
                        {'name': '+setteamname <name>', 'value': 'Change your team name', 'inline': False},
                        {'name': '+setteamlogo <url>', 'value': 'Set your team logo (image URL)', 'inline': False},
                        {'name': '+deleteteam', 'value': 'Delete your team permanently', 'inline': False},
                        {'name': '+teamlist', 'value': 'View all teams in the server', 'inline': False},
                        {'name': '+vc @user', 'value': 'Set vice-captain of your team', 'inline': False}
                    ]
                },
                {
                    'title': '⭐ Fantasy Squad Commands',
                    'description': 'Build your fantasy team with real users',
                    'fields': [
                        {'name': '+createfantasy', 'value': 'Create your fantasy squad', 'inline': False},
                        {'name': '+buyfantasy @user', 'value': 'Buy a user card for your fantasy team', 'inline': False},
                        {'name': '+sellfantasy @user', 'value': 'Sell a user card from your fantasy team', 'inline': False},
                        {'name': '+viewsquad or +vsq', 'value': 'View your fantasy squad', 'inline': False},
                        {'name': '+deletefantasy', 'value': 'Delete your fantasy squad', 'inline': False}
                    ]
                },
                {
                    'title': '💰 Market & Trading',
                    'description': 'Trade and invest in user cards',
                    'fields': [
                        {'name': '+price @user', 'value': 'Check the current price of a user card', 'inline': False},
                        {'name': '+updatefantasyprices or +ufp', 'value': 'Update all fantasy player prices (Admin only)', 'inline': False},
                        {'name': '+setcardvalue @user <amount>', 'value': 'Set card value for a user (Admin only)', 'inline': False},
                        {'name': '+invest @user <amount>', 'value': 'Invest in a user\'s card', 'inline': False},
                        {'name': '+market', 'value': 'View the transfer market', 'inline': False},
                        {'name': '+transfer @user @team_owner', 'value': 'Initiate transfer to another team', 'inline': False},
                        {'name': '+loan @user @team_owner', 'value': 'Initiate loan to another team', 'inline': False}
                    ]
                },
                {
                    'title': '⚽ Match & Predictions',
                    'description': 'Predict match outcomes',
                    'fields': [
                        {'name': '+predictmatchadd <team1> vs <team2>', 'value': 'Add a match for predictions (Admin)', 'inline': False},
                        {'name': '+matchremove <match_id>', 'value': 'Remove a match (Admin)', 'inline': False},
                        {'name': '+predict <match_id> <team_name>', 'value': 'Predict match winner', 'inline': False},
                        {'name': '+predictions', 'value': 'View all active matches', 'inline': False}
                    ]
                },
                {
                    'title': '📊 Statistics & Info',
                    'description': 'View stats and leaderboards',
                    'fields': [
                        {'name': '+stats', 'value': 'View bot statistics', 'inline': False},
                        {'name': '+leaderboard or +lb', 'value': 'View richest players', 'inline': False},
                        {'name': '+ping', 'value': 'Check bot latency', 'inline': False},
                        {'name': '+whereami', 'value': 'Show current server info', 'inline': False}
                    ]
                },
                {
                    'title': '⚙️ Server Configuration',
                    'description': 'Admin commands for server setup',
                    'fields': [
                        {'name': '+setprefix <prefix>', 'value': 'Change bot prefix (Admin only)', 'inline': False},
                        {'name': '+teamlogs <channel>', 'value': 'Set team approval log channel (Admin only)', 'inline': False},
                        {'name': '+toggle <feature>', 'value': 'Toggle server features (Bot owner/admin only)', 'inline': False},
                        {'name': '+tier', 'value': 'List all servers in a tier (Admin only)', 'inline': False}
                    ]
                },
                {
                    'title': '🔨 Moderation',
                    'description': 'Moderation and ban commands',
                    'fields': [
                        {'name': '+ban @user', 'value': 'Ban a user from using the bot (Admin only)', 'inline': False},
                        {'name': '+unban @user', 'value': 'Unban a user (Admin only)', 'inline': False},
                        {'name': '+bantrader @user', 'value': 'Ban user from stock market (Admin only)', 'inline': False},
                        {'name': '+unbantrader @user', 'value': 'Unban user from stock market (Admin only)', 'inline': False}
                    ]
                },
                {
                    'title': '🎮 Other Commands',
                    'description': 'Additional features',
                    'fields': [
                        {'name': '+troll', 'value': 'Send a random funny message', 'inline': False},
                        {'name': '+trace', 'value': 'Get detailed bot trace info', 'inline': False},
                        {'name': '+help', 'value': 'Show all available commands', 'inline': False}
                    ]
                }
            ]
        
        def get_embed(self):
            page = self.pages[self.current_page]
            embed = discord.Embed(
                title=page['title'],
                description=page['description'],
                color=discord.Color.green()
            )
            for field in page['fields']:
                embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
            embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • Use buttons to navigate")
            return embed
        
        @discord.ui.button(label='⏮️ First', style=discord.ButtonStyle.gray)
        async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = 0
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        
        @discord.ui.button(label='◀️ Previous', style=discord.ButtonStyle.blurple)
        async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.current_page > 0:
                self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        
        @discord.ui.button(label='▶️ Next', style=discord.ButtonStyle.blurple)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.current_page < len(self.pages) - 1:
                self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        
        @discord.ui.button(label='⏭️ Last', style=discord.ButtonStyle.gray)
        async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page = len(self.pages) - 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        
        @discord.ui.button(label='🛑 Stop', style=discord.ButtonStyle.red)
        async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(view=None)
            self.stop()
    
    view = TutorialView()
    await ctx.send(embed=view.get_embed(), view=view)

# Player Registration
@bot.hybrid_command(name='register', description='Register to play Hand Football Fantasy')
async def register(ctx):
    """Register a new player"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    config = get_server_config(ctx.guild.id)
    
    embed = discord.Embed(
        title="✅ Registration Successful!",
        description=f"Welcome to Hand Football Fantasy, {ctx.author.mention}!",
        color=discord.Color.green()
    )
    
    embed.add_field(name="💰 Starting Balance", value=f"${player_data['balance']:,}", inline=True)
    embed.add_field(name="💳 Your Card Value", value=f"${player_data['card_value']:,}", inline=True)
    embed.add_field(
        name="🎯 Next Steps",
        value="• Use `+createteam <name>` to create your team\n• Use `+createfantasy` to create a fantasy squad\n• Use `+tutorial` for a full guide",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Balance Command
@bot.hybrid_command(name='balance', aliases=['bal', 'money'], description='Check your balance')
async def balance(ctx, member: discord.Member = None):
    """Check balance of yourself or another player"""
    target = member or ctx.author
    player_data = get_player_data(target.id, ctx.guild.id)
    
    embed = discord.Embed(
        title=f"💰 {target.display_name}'s Wallet",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="Current Balance", value=f"${player_data['balance']:,}", inline=False)
    embed.add_field(name="Card Value", value=f"${player_data['card_value']:,}", inline=True)
    
    if player_data.get('team_id'):
        teams = load_json(TEAMS_FILE)
        team_key = f"{ctx.guild.id}_{player_data['team_id']}"
        if team_key in teams:
            embed.add_field(name="Team", value=teams[team_key].get('name', 'Unnamed Team'), inline=True)
    
    embed.set_thumbnail(url=target.display_avatar.url)
    
    await ctx.send(embed=embed)

# Add Balance (Admin only)
@bot.hybrid_command(name='addbalance', description='Add balance to a user (Admin only)')
@commands.has_permissions(administrator=True)
async def addbalance(ctx, member: discord.Member, amount: int):
    """Add balance to a user"""
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    player_data = get_player_data(member.id, ctx.guild.id)
    player_data['balance'] += amount
    update_player_data(member.id, ctx.guild.id, player_data)
    
    await ctx.send(f"✅ Added ${amount:,} to {member.mention}. New balance: ${player_data['balance']:,}")

# Remove Balance (Admin only)
@bot.hybrid_command(name='removebalance', aliases=['rb'], description='Remove balance from a user (Admin only)')
@commands.has_permissions(administrator=True)
async def removebalance(ctx, member: discord.Member, amount: int):
    """Remove balance from a user"""
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    player_data = get_player_data(member.id, ctx.guild.id)
    player_data['balance'] -= amount
    if player_data['balance'] < 0:
        player_data['balance'] = 0
    update_player_data(member.id, ctx.guild.id, player_data)
    
    await ctx.send(f"✅ Removed ${amount:,} from {member.mention}. New balance: ${player_data['balance']:,}")

# Card Command
@bot.hybrid_command(name='card', description='Generate player card')
async def card(ctx, member: discord.Member = None):
    """Generate a player card image"""
    target = member or ctx.author
    
    if target.bot:
        await ctx.send("❌ Cannot generate cards for bots!")
        return
    
    player_data = get_player_data(target.id, ctx.guild.id)
    current_price = get_stock_price(target.id, ctx.guild.id)
    
    # Create card image
    img = Image.new('RGB', (400, 600), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    # Try to use default font
    try:
        font_large = ImageFont.truetype("arial.ttf", 40)
        font_medium = ImageFont.truetype("arial.ttf", 30)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw card border
    draw.rectangle([(10, 10), (390, 590)], outline=(255, 215, 0), width=5)
    
    # Draw header
    draw.rectangle([(10, 10), (390, 100)], fill=(255, 215, 0))
    draw.text((200, 55), "PLAYER CARD", font=font_medium, fill=(0, 0, 0), anchor="mm")
    
    # Draw player name
    draw.text((200, 150), target.display_name[:20], font=font_large, fill=(255, 255, 255), anchor="mm")
    
    # Draw stats
    stats = [
        f"Balance: ${player_data['balance']:,}",
        f"Card Value: ${current_price:,}",
        f"Rating: {random.randint(60, 99)}"
    ]
    
    y_pos = 250
    for stat in stats:
        draw.text((200, y_pos), stat, font=font_small, fill=(255, 255, 255), anchor="mm")
        y_pos += 50
    
    # Draw team info if exists
    if player_data.get('team_id'):
        teams = load_json(TEAMS_FILE)
        team_key = f"{ctx.guild.id}_{player_data['team_id']}"
        if team_key in teams:
            draw.text((200, 450), f"Team: {teams[team_key]['name'][:25]}", font=font_small, fill=(255, 255, 255), anchor="mm")
    
    # Draw footer
    draw.rectangle([(10, 500), (390, 590)], fill=(50, 50, 50))
    draw.text((200, 545), f"ID: {target.id}", font=font_small, fill=(200, 200, 200), anchor="mm")
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    file = discord.File(img_bytes, filename=f"{target.display_name}_card.png")
    await ctx.send(file=file)

# Create Team
@bot.hybrid_command(name='createteam', description='Create your football team')
async def createteam(ctx, *, team_name: str):
    """Create a new team"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if player_data.get('team_id'):
        await ctx.send("❌ You already have a team! Use `+deleteteam` first if you want to create a new one.")
        return
    
    teams = load_json(TEAMS_FILE)
    team_id = f"team_{ctx.guild.id}_{ctx.author.id}_{len(teams)}"
    key = f"{ctx.guild.id}_{team_id}"
    
    teams[key] = {
        'id': team_id,
        'name': team_name,
        'owner_id': ctx.author.id,
        'guild_id': ctx.guild.id,
        'logo': None,
        'created_at': datetime.now().isoformat(),
        'captain': None,
        'vice_captain': None
    }
    save_json(TEAMS_FILE, teams)
    
    player_data['team_id'] = team_id
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    embed = discord.Embed(
        title="⚽ Team Created!",
        description=f"**{team_name}** has been successfully created!",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Owner", value=ctx.author.mention, inline=True)
    embed.add_field(name="Team ID", value=f"`{team_id}`", inline=True)
    embed.add_field(
        name="Next Steps",
        value="• Use `+setteamlogo <url>` to add a logo\n• Use `+createfantasy` to build your squad\n• Use `+vc @user` to set a vice-captain",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Delete Team
@bot.hybrid_command(name='deleteteam', description='Delete your team')
async def deleteteam(ctx):
    """Delete user's team"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You don't have a team!")
        return
    
    teams = load_json(TEAMS_FILE)
    key = f"{ctx.guild.id}_{player_data['team_id']}"
    
    if key in teams:
        team_name = teams[key]['name']
        del teams[key]
        save_json(TEAMS_FILE, teams)
        
        player_data['team_id'] = None
        update_player_data(ctx.author.id, ctx.guild.id, player_data)
        
        await ctx.send(f"✅ Team **{team_name}** has been deleted.")
    else:
        await ctx.send("❌ Team not found!")

# Set Team Name
@bot.hybrid_command(name='setteamname', description='Set or update your team name')
async def setteamname(ctx, *, new_name: str):
    """Update team name"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You don't have a team! Use `+createteam` first.")
        return
    
    teams = load_json(TEAMS_FILE)
    key = f"{ctx.guild.id}_{player_data['team_id']}"
    
    if key not in teams:
        await ctx.send("❌ Team not found!")
        return
    
    old_name = teams[key]['name']
    teams[key]['name'] = new_name
    save_json(TEAMS_FILE, teams)
    
    await ctx.send(f"✅ Team name updated from **{old_name}** to **{new_name}**!")

# Set Team Logo
@bot.hybrid_command(name='setteamlogo', description='Set your team logo (image URL)')
async def setteamlogo(ctx, logo_url: str):
    """Set team logo"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You don't have a team! Use `+createteam` first.")
        return
    
    teams = load_json(TEAMS_FILE)
    key = f"{ctx.guild.id}_{player_data['team_id']}"
    
    if key not in teams:
        await ctx.send("❌ Team not found!")
        return
    
    teams[key]['logo'] = logo_url
    save_json(TEAMS_FILE, teams)
    
    embed = discord.Embed(
        title="✅ Logo Updated!",
        description=f"Team logo for **{teams[key]['name']}** has been updated!",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=logo_url)
    
    await ctx.send(embed=embed)

# Set Vice Captain
@bot.hybrid_command(name='vc', description='Set vice-captain of your team')
async def vc(ctx, member: discord.Member):
    """Set vice captain"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You don't have a team!")
        return
    
    teams = load_json(TEAMS_FILE)
    key = f"{ctx.guild.id}_{player_data['team_id']}"
    
    if key not in teams:
        await ctx.send("❌ Team not found!")
        return
    
    teams[key]['vice_captain'] = member.id
    save_json(TEAMS_FILE, teams)
    
    await ctx.send(f"✅ {member.mention} is now the vice-captain of **{teams[key]['name']}**!")

# Team List
@bot.hybrid_command(name='teamlist', description='View all teams in the server')
async def teamlist(ctx):
    """List all teams"""
    teams = load_json(TEAMS_FILE)
    guild_teams = [team for key, team in teams.items() if team['guild_id'] == ctx.guild.id]
    
    if not guild_teams:
        await ctx.send("❌ No teams found in this server!")
        return
    
    embed = discord.Embed(
        title=f"⚽ Teams in {ctx.guild.name}",
        description=f"Total Teams: {len(guild_teams)}",
        color=discord.Color.blue()
    )
    
    for i, team in enumerate(guild_teams[:25], 1):
        owner = ctx.guild.get_member(team['owner_id'])
        owner_name = owner.mention if owner else "Unknown"
        embed.add_field(
            name=f"{i}. {team['name']}",
            value=f"Owner: {owner_name}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Create Fantasy Squad
@bot.hybrid_command(name='createfantasy', description='Create your fantasy squad')
async def createfantasy(ctx):
    """Create a fantasy squad"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You need to create a team first! Use `+createteam <name>`")
        return
    
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    key = f"{ctx.guild.id}_{ctx.author.id}"
    
    if key in fantasy_teams:
        await ctx.send("❌ You already have a fantasy squad! Use `+deletefantasy` first if you want to recreate it.")
        return
    
    fantasy_teams[key] = {
        'owner_id': ctx.author.id,
        'guild_id': ctx.guild.id,
        'players': [],
        'created_at': datetime.now().isoformat(),
        'formation': '4-3-3'
    }
    save_json(FANTASY_TEAMS_FILE, fantasy_teams)
    
    embed = discord.Embed(
        title="⭐ Fantasy Squad Created!",
        description="Your fantasy squad is ready!",
        color=discord.Color.purple()
    )
    
    config = get_server_config(ctx.guild.id)
    embed.add_field(name="Squad Size", value=f"0/{config['max_fantasy_size']}", inline=True)
    embed.add_field(name="Formation", value="4-3-3 (Default)", inline=True)
    embed.add_field(
        name="Next Steps",
        value="• Use `+buyfantasy @user` to add players\n• Use `+viewsquad` to see your squad",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Delete Fantasy Squad
@bot.hybrid_command(name='deletefantasy', description='Delete your fantasy squad')
async def deletefantasy(ctx):
    """Delete fantasy squad"""
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    key = f"{ctx.guild.id}_{ctx.author.id}"
    
    if key not in fantasy_teams:
        await ctx.send("❌ You don't have a fantasy squad!")
        return
    
    # Refund all players
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    for player in fantasy_teams[key]['players']:
        player_data['balance'] += int(player['price'] * 0.5)
    
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    del fantasy_teams[key]
    save_json(FANTASY_TEAMS_FILE, fantasy_teams)
    
    await ctx.send(f"✅ Fantasy squad deleted! You received a 50% refund. New balance: ${player_data['balance']:,}")

# Buy Fantasy Player (REAL USER)
@bot.hybrid_command(name='buyfantasy', aliases=['buy'], description='Buy a user card for your fantasy squad')
async def buyfantasy(ctx, member: discord.Member):
    """Buy a fantasy player (real user)"""
    
    if member.id == ctx.author.id:
        await ctx.send("❌ You cannot buy yourself!")
        return
    
    if member.bot:
        await ctx.send("❌ You cannot buy bot cards!")
        return
    
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You need to create a team first! Use `+createteam <name>`")
        return
    
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    key = f"{ctx.guild.id}_{ctx.author.id}"
    
    if key not in fantasy_teams:
        await ctx.send("❌ You don't have a fantasy squad! Use `+createfantasy` first.")
        return
    
    config = get_server_config(ctx.guild.id)
    
    if len(fantasy_teams[key]['players']) >= config['max_fantasy_size']:
        await ctx.send(f"❌ Squad is full! Maximum size is {config['max_fantasy_size']} players.")
        return
    
    if any(p['user_id'] == member.id for p in fantasy_teams[key]['players']):
        await ctx.send(f"❌ You already own {member.display_name}'s card!")
        return
    
    price = get_stock_price(member.id, ctx.guild.id)
    
    if player_data['balance'] < price:
        await ctx.send(f"❌ Insufficient funds! You need ${price:,} but have ${player_data['balance']:,}")
        return
    
    player_data['balance'] -= price
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    fantasy_teams[key]['players'].append({
        'user_id': member.id,
        'username': str(member),
        'display_name': member.display_name,
        'price': price,
        'purchased_at': datetime.now().isoformat(),
        'position': 'Player'
    })
    save_json(FANTASY_TEAMS_FILE, fantasy_teams)
    
    new_price = int(price * 1.05)
    update_stock_price(member.id, ctx.guild.id, new_price)
    
    log_transaction(ctx.guild.id, 'fantasy_purchase', {
        'buyer': str(ctx.author),
        'player': str(member),
        'price': price
    })
    
    embed = discord.Embed(
        title="✅ Player Card Purchased!",
        description=f"**{member.display_name}** has been added to your fantasy squad!",
        color=discord.Color.green()
    )
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Price Paid", value=f"${price:,}", inline=True)
    embed.add_field(name="New Card Value", value=f"${new_price:,} (+5%)", inline=True)
    embed.add_field(name="Remaining Balance", value=f"${player_data['balance']:,}", inline=True)
    embed.add_field(name="Squad Size", value=f"{len(fantasy_teams[key]['players'])}/{config['max_fantasy_size']}", inline=True)
    
    await ctx.send(embed=embed)

# Sell Fantasy Player
@bot.hybrid_command(name='sellfantasy', aliases=['sellf'], description='Sell a player from your fantasy squad')
async def sellfantasy(ctx, member: discord.Member):
    """Sell a fantasy player"""
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    key = f"{ctx.guild.id}_{ctx.author.id}"
    
    if key not in fantasy_teams:
        await ctx.send("❌ You don't have a fantasy squad!")
        return
    
    player_found = None
    for i, player in enumerate(fantasy_teams[key]['players']):
        if player['user_id'] == member.id:
            player_found = fantasy_teams[key]['players'].pop(i)
            break
    
    if not player_found:
        await ctx.send(f"❌ {member.display_name}'s card is not in your squad!")
        return
    
    current_price = get_stock_price(member.id, ctx.guild.id)
    sell_price = int(current_price * 0.8)
    
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    player_data['balance'] += sell_price
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    save_json(FANTASY_TEAMS_FILE, fantasy_teams)
    
    new_price = int(current_price * 0.97)
    update_stock_price(member.id, ctx.guild.id, new_price)
    
    log_transaction(ctx.guild.id, 'fantasy_sale', {
        'seller': str(ctx.author),
        'player': str(member),
        'price': sell_price
    })
    
    embed = discord.Embed(
        title="💰 Player Card Sold!",
        description=f"**{member.display_name}**'s card has been sold!",
        color=discord.Color.orange()
    )
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Sale Price", value=f"${sell_price:,} (80% of market)", inline=True)
    embed.add_field(name="New Balance", value=f"${player_data['balance']:,}", inline=True)
    embed.add_field(name="New Card Value", value=f"${new_price:,} (-3%)", inline=True)
    
    await ctx.send(embed=embed)

# View Squad
@bot.hybrid_command(name='viewsquad', aliases=['vsq', 'squad'], description='View your fantasy squad')
async def viewsquad(ctx, member: discord.Member = None):
    """View fantasy squad"""
    target = member or ctx.author
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    key = f"{ctx.guild.id}_{target.id}"
    
    if key not in fantasy_teams:
        await ctx.send(f"❌ {target.display_name} doesn't have a fantasy squad!")
        return
    
    squad = fantasy_teams[key]
    config = get_server_config(ctx.guild.id)
    
    embed = discord.Embed(
        title=f"⭐ {target.display_name}'s Fantasy Squad",
        description=f"Formation: {squad.get('formation', '4-3-3')}",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="Squad Size", value=f"{len(squad['players'])}/{config['max_fantasy_size']}", inline=True)
    
    total_value = sum(get_stock_price(p['user_id'], ctx.guild.id) for p in squad['players'])
    embed.add_field(name="Total Squad Value", value=f"${total_value:,}", inline=True)
    
    if squad['players']:
        players_text = ""
        for i, player in enumerate(squad['players'], 1):
            current_price = get_stock_price(player['user_id'], ctx.guild.id)
            profit = current_price - player['price']
            profit_emoji = "📈" if profit > 0 else "📉" if profit < 0 else "➖"
            players_text += f"{i}. <@{player['user_id']}> - ${current_price:,} {profit_emoji}\n"
        
        embed.add_field(name="Players", value=players_text or "No players", inline=False)
    else:
        embed.add_field(name="Players", value="No players in squad", inline=False)
    
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text=f"Created {squad.get('created_at', 'Unknown')[:10]}")
    
    await ctx.send(embed=embed)

# Price Command
@bot.hybrid_command(name='price', aliases=['pr'], description='Check user card price')
async def price(ctx, member: discord.Member):
    """Check price of a user's card"""
    
    if member.bot:
        await ctx.send("❌ Bots don't have card values!")
        return
    
    current_price = get_stock_price(member.id, ctx.guild.id)
    stocks = load_json(STOCKS_FILE)
    stock_key = f"{ctx.guild.id}_{member.id}"
    change_percent = stocks.get(stock_key, {}).get('change_percent', 0)
    
    embed = discord.Embed(
        title=f"💳 {member.display_name}'s Card",
        color=discord.Color.blue()
    )
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Current Price", value=f"${current_price:,}", inline=True)
    
    if change_percent > 0:
        embed.add_field(name="Change", value=f"+{change_percent}% 📈", inline=True)
    elif change_percent < 0:
        embed.add_field(name="Change", value=f"{change_percent}% 📉", inline=True)
    else:
        embed.add_field(name="Change", value=f"0% ➖", inline=True)
    
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    owners = sum(1 for team in fantasy_teams.values() 
                 if team['guild_id'] == ctx.guild.id and 
                 any(p['user_id'] == member.id for p in team['players']))
    
    embed.add_field(name="Owned By", value=f"{owners} team(s)", inline=True)
    
    await ctx.send(embed=embed)

# Set Card Value (Admin)
@bot.hybrid_command(name='setcardvalue', aliases=['scv'], description='Set card value for a user (Admin only)')
@commands.has_permissions(administrator=True)
async def setcardvalue(ctx, member: discord.Member, amount: int):
    """Set card value for a user"""
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    if member.bot:
        await ctx.send("❌ Cannot set value for bots!")
        return
    
    update_stock_price(member.id, ctx.guild.id, amount)
    
    player_data = get_player_data(member.id, ctx.guild.id)
    player_data['card_value'] = amount
    update_player_data(member.id, ctx.guild.id, player_data)
    
    await ctx.send(f"✅ Set {member.mention}'s card value to ${amount:,}")

# Update Fantasy Prices (Admin)
@bot.hybrid_command(name='updatefantasyprices', aliases=['ufp'], description='Update fantasy prices (Admin only)')
@commands.has_permissions(administrator=True)
async def updatefantasyprices(ctx):
    """Recalculate all fantasy prices"""
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    updated = 0
    
    for team_key, team in fantasy_teams.items():
        if team['guild_id'] == ctx.guild.id:
            for player in team['players']:
                current_price = get_stock_price(player['user_id'], ctx.guild.id)
                player['price'] = current_price
                updated += 1
    
    save_json(FANTASY_TEAMS_FILE, fantasy_teams)
    await ctx.send(f"✅ Updated {updated} player prices!")

# Invest Command
@bot.hybrid_command(name='invest', description='Invest in a user card')
async def invest(ctx, member: discord.Member, amount: int):
    """Invest in a user's card to increase its value"""
    
    if member.bot:
        await ctx.send("❌ Cannot invest in bots!")
        return
    
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if player_data['balance'] < amount:
        await ctx.send(f"❌ Insufficient funds! You have ${player_data['balance']:,}")
        return
    
    player_data['balance'] -= amount
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    current_price = get_stock_price(member.id, ctx.guild.id)
    increase = int(amount * 0.1)
    new_price = current_price + increase
    update_stock_price(member.id, ctx.guild.id, new_price)
    
    log_transaction(ctx.guild.id, 'investment', {
        'investor': str(ctx.author),
        'target': str(member),
        'amount': amount,
        'increase': increase
    })
    
    embed = discord.Embed(
        title="📊 Investment Complete!",
        description=f"You invested ${amount:,} in {member.mention}'s card!",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Price Increase", value=f"+${increase:,}", inline=True)
    embed.add_field(name="New Card Value", value=f"${new_price:,}", inline=True)
    embed.add_field(name="Your Balance", value=f"${player_data['balance']:,}", inline=True)
    
    await ctx.send(embed=embed)

# Market Command
@bot.hybrid_command(name='market', description='View transfer market')
async def market(ctx):
    """View the transfer market"""
    stocks = load_json(STOCKS_FILE)
    guild_stocks = [(user_id.split('_')[1], data) for user_id, data in stocks.items() 
                    if user_id.startswith(f"{ctx.guild.id}_")]
    
    guild_stocks.sort(key=lambda x: x[1]['price'], reverse=True)
    
    embed = discord.Embed(
        title="📊 Transfer Market",
        description="Top 10 Most Valuable Cards",
        color=discord.Color.gold()
    )
    
    for i, (user_id, data) in enumerate(guild_stocks[:10], 1):
        member = ctx.guild.get_member(int(user_id))
        if member and not member.bot:
            change = data.get('change_percent', 0)
            change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➖"
            embed.add_field(
                name=f"{i}. {member.display_name}",
                value=f"${data['price']:,} {change_emoji} ({change:+.1f}%)",
                inline=False
            )
    
    await ctx.send(embed=embed)

# Transfer Command
@bot.hybrid_command(name='transfer', description='Transfer player to another team')
async def transfer(ctx, player: discord.Member, team_owner: discord.Member):
    """Initiate a player transfer"""
    
    if player.bot or team_owner.bot:
        await ctx.send("❌ Cannot transfer bots!")
        return
    
    if ctx.author.id == team_owner.id:
        await ctx.send("❌ Cannot transfer to yourself!")
        return
    
    # Check if sender owns the player
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    sender_key = f"{ctx.guild.id}_{ctx.author.id}"
    
    if sender_key not in fantasy_teams:
        await ctx.send("❌ You don't have a fantasy squad!")
        return
    
    player_in_squad = None
    for p in fantasy_teams[sender_key]['players']:
        if p['user_id'] == player.id:
            player_in_squad = p
            break
    
    if not player_in_squad:
        await ctx.send(f"❌ {player.display_name} is not in your squad!")
        return
    
    # Check if recipient has a team
    receiver_data = get_player_data(team_owner.id, ctx.guild.id)
    if not receiver_data.get('team_id'):
        await ctx.send(f"❌ {team_owner.display_name} doesn't have a team!")
        return
    
    # Create transfer request
    transfers = load_json(TRANSFERS_FILE)
    transfer_id = f"transfer_{ctx.guild.id}_{ctx.author.id}_{team_owner.id}_{datetime.now().timestamp()}"
    
    current_price = get_stock_price(player.id, ctx.guild.id)
    
    transfers[transfer_id] = {
        'id': transfer_id,
        'from_user': ctx.author.id,
        'to_user': team_owner.id,
        'player_id': player.id,
        'player_name': player.display_name,
        'initial_price': current_price,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'guild_id': ctx.guild.id,
        'type': 'transfer',
        'counter_offer_price': None,
        'counter_offer_player': None
    }
    save_json(TRANSFERS_FILE, transfers)
    
    # Send DM to both parties
    embed_sender = discord.Embed(
        title="📤 Transfer Request Sent",
        description=f"You've initiated a transfer of **{player.display_name}** to {team_owner.mention}",
        color=discord.Color.blue()
    )
    embed_sender.add_field(name="Player", value=player.mention, inline=True)
    embed_sender.add_field(name="Current Price", value=f"${current_price:,}", inline=True)
    embed_sender.add_field(name="Transfer ID", value=f"`{transfer_id}`", inline=False)
    
    try:
        await ctx.author.send(embed=embed_sender)
    except:
        pass
    
    embed_receiver = discord.Embed(
        title="📥 Transfer Offer Received",
        description=f"{ctx.author.mention} wants to transfer **{player.display_name}** to your team!",
        color=discord.Color.green()
    )
    embed_receiver.add_field(name="Player", value=player.mention, inline=True)
    embed_receiver.add_field(name="Asking Price", value=f"${current_price:,}", inline=True)
    embed_receiver.add_field(
        name="Options",
        value=f"• Type `{current_price}` to accept at current price\n• Type a different number to counter-offer\n• Type a player mention to exchange\n• Type `price,@player` to offer both\n• Type `reject` to decline",
        inline=False
    )
    embed_receiver.add_field(name="Transfer ID", value=f"`{transfer_id}`", inline=False)
    
    try:
        await team_owner.send(embed=embed_receiver)
        await ctx.send(f"✅ Transfer request sent to {team_owner.mention}! Check your DMs.")
    except:
        await ctx.send(f"❌ Could not send DM to {team_owner.mention}. Make sure they have DMs enabled!")
        
@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check if message is in DMs
    if isinstance(message.channel, discord.DMChannel):
        # Check for transfer responses
        transfers = load_json(TRANSFERS_FILE)
        loans = load_json(LOANS_FILE)
        
        # Check if user has pending transfer offers
        for transfer_id, transfer_data in transfers.items():
            if transfer_data['to_user'] == message.author.id and transfer_data['status'] == 'pending':
                response = message.content.lower().strip()
                
                if response == 'reject':
                    transfer_data['status'] = 'rejected'
                    save_json(TRANSFERS_FILE, transfers)
                    
                    from_user = bot.get_user(transfer_data['from_user'])
                    await message.author.send("❌ Transfer rejected!")
                    if from_user:
                        await from_user.send(f"❌ Your transfer of {transfer_data['player_name']} was rejected.")
                    return
                
                # Check if it's a price
                elif response.isdigit():
                    new_price = int(response)
                    
                    # Accept at current price
                    if new_price == transfer_data['initial_price']:
                        # Process transfer
                        fantasy_teams = load_json(FANTASY_TEAMS_FILE)
                        from_key = f"{transfer_data['guild_id']}_{transfer_data['from_user']}"
                        to_key = f"{transfer_data['guild_id']}_{transfer_data['to_user']}"
                        
                        # Remove from sender's team
                        for i, p in enumerate(fantasy_teams[from_key]['players']):
                            if p['user_id'] == transfer_data['player_id']:
                                player_data = fantasy_teams[from_key]['players'].pop(i)
                                break
                        
                        # Check if receiver has fantasy team
                        if to_key not in fantasy_teams:
                            await message.author.send("❌ You need to create a fantasy squad first! Use `+createfantasy`")
                            return
                        
                        # Add to receiver's team
                        fantasy_teams[to_key]['players'].append(player_data)
                        save_json(FANTASY_TEAMS, fantasy_teams)
                        
                        # Handle payment
                        receiver_player_data = get_player_data(transfer_data['to_user'], transfer_data['guild_id'])
                        if receiver_player_data['balance'] < new_price:
                            await message.author.send(f"❌ Insufficient funds! You need ${new_price:,}")
                            return
                        
                        receiver_player_data['balance'] -= new_price
                        update_player_data(transfer_data['to_user'], transfer_data['guild_id'], receiver_player_data)
                        
                        sender_player_data = get_player_data(transfer_data['from_user'], transfer_data['guild_id'])
                        sender_player_data['balance'] += new_price
                        update_player_data(transfer_data['from_user'], transfer_data['guild_id'], sender_player_data)
                        
                        transfer_data['status'] = 'completed'
                        save_json(TRANSFERS_FILE, transfers)
                        
                        await message.author.send(f"✅ Transfer completed! You paid ${new_price:,}")
                        
                        from_user = bot.get_user(transfer_data['from_user'])
                        if from_user:
                            await from_user.send(f"✅ Transfer completed! You received ${new_price:,}")
                        return
                    
                    # Counter offer
                    else:
                        transfer_data['counter_offer_price'] = new_price
                        save_json(TRANSFERS_FILE, transfers)
                        
                        await message.author.send(f"✅ Counter-offer sent: ${new_price:,}")
                        
                        from_user = bot.get_user(transfer_data['from_user'])
                        if from_user:
                            await from_user.send(f"📥 Counter-offer received: ${new_price:,}\nType `accept` to accept or `reject` to decline.")
                        return
                
                # Check for player exchange
                elif message.mentions:
                    exchange_player = message.mentions[0]
                    
                    # Check if offering player exists in their team
                    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
                    to_key = f"{transfer_data['guild_id']}_{transfer_data['to_user']}"
                    
                    has_player = any(p['user_id'] == exchange_player.id for p in fantasy_teams[to_key]['players'])
                    
                    if not has_player:
                        await message.author.send(f"❌ You don't have {exchange_player.display_name} in your squad!")
                        return
                    
                    transfer_data['counter_offer_player'] = exchange_player.id
                    save_json(TRANSFERS_FILE, transfers)
                    
                    await message.author.send(f"✅ Exchange offer sent: {exchange_player.display_name}")
                    
                    from_user = bot.get_user(transfer_data['from_user'])
                    if from_user:
                        await from_user.send(f"📥 Exchange offer: {exchange_player.mention}\nType `accept` to accept or `reject` to decline.")
                    return
                
                # Check for combined offer (price,@player)
                elif ',' in response and message.mentions:
                    parts = response.split(',')
                    if parts[0].isdigit():
                        new_price = int(parts[0])
                        exchange_player = message.mentions[0]
                        
                        fantasy_teams = load_json(FANTASY_TEAMS_FILE)
                        to_key = f"{transfer_data['guild_id']}_{transfer_data['to_user']}"
                        
                        has_player = any(p['user_id'] == exchange_player.id for p in fantasy_teams[to_key]['players'])
                        
                        if not has_player:
                            await message.author.send(f"❌ You don't have {exchange_player.display_name} in your squad!")
                            return
                        
                        transfer_data['counter_offer_price'] = new_price
                        transfer_data['counter_offer_player'] = exchange_player.id
                        save_json(TRANSFERS_FILE, transfers)
                        
                        await message.author.send(f"✅ Combined offer sent: ${new_price:,} + {exchange_player.display_name}")
                        
                        from_user = bot.get_user(transfer_data['from_user'])
                        if from_user:
                            await from_user.send(f"📥 Combined offer: ${new_price:,} + {exchange_player.mention}\nType `accept` to accept or `reject` to decline.")
                        return
        
        # Check for counter-offer responses from original sender
        for transfer_id, transfer_data in transfers.items():
            if transfer_data['from_user'] == message.author.id and transfer_data['status'] == 'pending':
                if transfer_data.get('counter_offer_price') or transfer_data.get('counter_offer_player'):
                    response = message.content.lower().strip()
                    
                    if response == 'accept':
                        # Process the counter-offer
                        fantasy_teams = load_json(FANTASY_TEAMS_FILE)
                        from_key = f"{transfer_data['guild_id']}_{transfer_data['from_user']}"
                        to_key = f"{transfer_data['guild_id']}_{transfer_data['to_user']}"
                        
                        # Handle player exchange
                        if transfer_data.get('counter_offer_player'):
                            # Swap players
                            player1 = None
                            for i, p in enumerate(fantasy_teams[from_key]['players']):
                                if p['user_id'] == transfer_data['player_id']:
                                    player1 = fantasy_teams[from_key]['players'].pop(i)
                                    break
                            
                            player2 = None
                            for i, p in enumerate(fantasy_teams[to_key]['players']):
                                if p['user_id'] == transfer_data['counter_offer_player']:
                                    player2 = fantasy_teams[to_key]['players'].pop(i)
                                    break
                            
                            if player1 and player2:
                                fantasy_teams[to_key]['players'].append(player1)
                                fantasy_teams[from_key]['players'].append(player2)
                        else:
                            # Just move player
                            for i, p in enumerate(fantasy_teams[from_key]['players']):
                                if p['user_id'] == transfer_data['player_id']:
                                    player_data = fantasy_teams[from_key]['players'].pop(i)
                                    fantasy_teams[to_key]['players'].append(player_data)
                                    break
                        
                        # Handle payment if counter-offer price exists
                        if transfer_data.get('counter_offer_price'):
                            price = transfer_data['counter_offer_price']
                            
                            receiver_player_data = get_player_data(transfer_data['to_user'], transfer_data['guild_id'])
                            receiver_player_data['balance'] -= price
                            update_player_data(transfer_data['to_user'], transfer_data['guild_id'], receiver_player_data)
                            
                            sender_player_data = get_player_data(transfer_data['from_user'], transfer_data['guild_id'])
                            sender_player_data['balance'] += price
                            update_player_data(transfer_data['from_user'], transfer_data['guild_id'], sender_player_data)
                        
                        save_json(FANTASY_TEAMS_FILE, fantasy_teams)
                        transfer_data['status'] = 'completed'
                        save_json(TRANSFERS_FILE, transfers)
                        
                        await message.author.send("✅ Counter-offer accepted! Transfer completed.")
                        
                        to_user = bot.get_user(transfer_data['to_user'])
                        if to_user:
                            await to_user.send("✅ Your counter-offer was accepted! Transfer completed.")
                        return
                    
                    elif response == 'reject':
                        transfer_data['status'] = 'rejected'
                        save_json(TRANSFERS_FILE, transfers)
                        
                        await message.author.send("❌ Counter-offer rejected!")
                        
                        to_user = bot.get_user(transfer_data['to_user'])
                        if to_user:
                            await to_user.send("❌ Your counter-offer was rejected.")
                        return
# Loan Command
@bot.hybrid_command(name='loan', description='Loan player to another team')
async def loan(ctx, player: discord.Member, team_owner: discord.Member):
    """Initiate a player loan"""
    
    if player.bot or team_owner.bot:
        await ctx.send("❌ Cannot loan bots!")
        return
    
    if ctx.author.id == team_owner.id:
        await ctx.send("❌ Cannot loan to yourself!")
        return
    
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    sender_key = f"{ctx.guild.id}_{ctx.author.id}"
    
    if sender_key not in fantasy_teams:
        await ctx.send("❌ You don't have a fantasy squad!")
        return
    
    player_in_squad = None
    for p in fantasy_teams[sender_key]['players']:
        if p['user_id'] == player.id:
            player_in_squad = p
            break
    
    if not player_in_squad:
        await ctx.send(f"❌ {player.display_name} is not in your squad!")
        return
    
    receiver_data = get_player_data(team_owner.id, ctx.guild.id)
    if not receiver_data.get('team_id'):
        await ctx.send(f"❌ {team_owner.display_name} doesn't have a team!")
        return
    
    loans = load_json(LOANS_FILE)
    loan_id = f"loan_{ctx.guild.id}_{ctx.author.id}_{team_owner.id}_{datetime.now().timestamp()}"
    
    current_price = get_stock_price(player.id, ctx.guild.id)
    
    loans[loan_id] = {
        'id': loan_id,
        'from_user': ctx.author.id,
        'to_user': team_owner.id,
        'player_id': player.id,
        'player_name': player.display_name,
        'price': current_price,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'guild_id': ctx.guild.id,
        'matches': None
    }
    save_json(LOANS_FILE, loans)
    
    embed_sender = discord.Embed(
        title="📤 Loan Request Sent",
        description=f"You've initiated a loan of **{player.display_name}** to {team_owner.mention}",
        color=discord.Color.blue()
    )
    embed_sender.add_field(name="Player", value=player.mention, inline=True)
    embed_sender.add_field(name="Loan ID", value=f"`{loan_id}`", inline=False)
    
    try:
        await ctx.author.send(embed=embed_sender)
    except:
        pass
    
    embed_receiver = discord.Embed(
        title="📥 Loan Offer Received",
        description=f"{ctx.author.mention} wants to loan **{player.display_name}** to your team!",
        color=discord.Color.orange()
    )
    embed_receiver.add_field(name="Player", value=player.mention, inline=True)
    embed_receiver.add_field(
        name="Response Required",
        value="Type the number of matches you want to loan them for (e.g., `5` for 5 matches)\nType `reject` to decline",
        inline=False
    )
    embed_receiver.add_field(name="Loan ID", value=f"`{loan_id}`", inline=False)
    
    try:
        await team_owner.send(embed=embed_receiver)
        await ctx.send(f"✅ Loan request sent to {team_owner.mention}! Check your DMs.")
    except:
        await ctx.send(f"❌ Could not send DM to {team_owner.mention}. Make sure they have DMs enabled!")
@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check if message is in DMs
    if isinstance(message.channel, discord.DMChannel):
        # Check for transfer responses
        transfers = load_json(TRANSFERS_FILE)
        loans = load_json(LOANS_FILE)
        
        # Check if user has pending transfer offers
        for transfer_id, transfer_data in transfers.items():
            if transfer_data['to_user'] == message.author.id and transfer_data['status'] == 'pending':
                response = message.content.lower().strip()
                
                if response == 'reject':
                    transfer_data['status'] = 'rejected'
                    save_json(TRANSFERS_FILE, transfers)
                    
                    from_user = bot.get_user(transfer_data['from_user'])
                    await message.author.send("❌ Transfer rejected!")
                    if from_user:
                        await from_user.send(f"❌ Your transfer of {transfer_data['player_name']} was rejected.")
                    return     
        # Check for loan responses
        for loan_id, loan_data in loans.items():
            if loan_data['to_user'] == message.author.id and loan_data['status'] == 'pending':
                response = message.content.lower().strip()
                
                if response == 'reject':
                    loan_data['status'] = 'rejected'
                    save_json(LOANS_FILE, loans)
                    
                    from_user = bot.get_user(loan_data['from_user'])
                    await message.author.send("❌ Loan rejected!")
                    if from_user:
                        await from_user.send(f"❌ Your loan offer for {loan_data['player_name']} was rejected.")
                    return
                
                elif response.isdigit():
                    matches = int(response)
                    
                    if matches <= 0:
                        await message.author.send("❌ Number of matches must be positive!")
                        return
                    
                    loan_data['matches'] = matches
                    loan_data['status'] = 'active'
                    save_json(LOANS_FILE, loans)
                    
                    await message.author.send(f"✅ Loan accepted for {matches} matches!")
                    
                    from_user = bot.get_user(loan_data['from_user'])
                    if from_user:
                        await from_user.send(f"✅ Loan accepted! {loan_data['player_name']} loaned for {matches} matches.")
                    return
# Predict Match Add (Admin)
@bot.hybrid_command(name='predictmatchadd', description='Add a match for predictions (Admin)')
@commands.has_permissions(administrator=True)
async def predictmatchadd(ctx, *, match_text: str):
    """Add a match for predictions"""
    
    if ' vs ' not in match_text.lower():
        await ctx.send("❌ Format: `+predictmatchadd Team1 vs Team2`")
        return
    
    parts = match_text.split(' vs ')
    if len(parts) != 2:
        await ctx.send("❌ Format: `+predictmatchadd Team1 vs Team2`")
        return
    
    team1 = parts[0].strip()
    team2 = parts[1].strip()
    
    # Verify teams exist
    teams = load_json(TEAMS_FILE)
    guild_teams = {team['name'].lower(): team for key, team in teams.items() if team['guild_id'] == ctx.guild.id}
    
    if team1.lower() not in guild_teams:
        await ctx.send(f"❌ Team '{team1}' not found! Use `+teamlist` to see all teams.")
        return
    
    if team2.lower() not in guild_teams:
        await ctx.send(f"❌ Team '{team2}' not found! Use `+teamlist` to see all teams.")
        return
    
    matches = load_json(MATCHES_FILE)
    match_id = f"match_{ctx.guild.id}_{len(matches)}_{datetime.now().timestamp()}"
    
    matches[match_id] = {
        'id': match_id,
        'team1': team1,
        'team2': team2,
        'guild_id': ctx.guild.id,
        'created_at': datetime.now().isoformat(),
        'status': 'active',
        'result': None
    }
    save_json(MATCHES_FILE, matches)
    
    embed = discord.Embed(
        title="⚽ Match Added!",
        description=f"**{team1}** vs **{team2}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Match ID", value=f"`{match_id}`", inline=False)
    embed.add_field(name="How to Predict", value=f"Use `+predict {match_id} <team_name>`", inline=False)
    
    await ctx.send(embed=embed)

# Match Remove (Admin)
@bot.hybrid_command(name='matchremove', description='Remove a match (Admin)')
@commands.has_permissions(administrator=True)
async def matchremove(ctx, match_id: str):
    """Remove a match"""
    matches = load_json(MATCHES_FILE)
    
    if match_id not in matches:
        await ctx.send("❌ Match not found!")
        return
    
    match_data = matches[match_id]
    del matches[match_id]
    save_json(MATCHES_FILE, matches)
    
    # Remove associated predictions
    predictions = load_json(PREDICTIONS_FILE)
    predictions = {k: v for k, v in predictions.items() if v.get('match_id') != match_id}
    save_json(PREDICTIONS_FILE, predictions)
    
    await ctx.send(f"✅ Match **{match_data['team1']} vs {match_data['team2']}** has been removed!")

# Predict Command
@bot.hybrid_command(name='predict', description='Predict match winner')
async def predict(ctx, match_id: str, *, team_name: str):
    """Make a prediction for a match"""
    matches = load_json(MATCHES_FILE)
    
    if match_id not in matches:
        await ctx.send("❌ Match not found! Use `+predictions` to see active matches.")
        return
    
    match_data = matches[match_id]
    
    if match_data['status'] != 'active':
        await ctx.send("❌ This match is no longer accepting predictions!")
        return
    
    # Verify team name
    if team_name.lower() != match_data['team1'].lower() and team_name.lower() != match_data['team2'].lower():
        await ctx.send(f"❌ Team must be either '{match_data['team1']}' or '{match_data['team2']}'")
        return
    
    predictions = load_json(PREDICTIONS_FILE)
    prediction_key = f"{ctx.guild.id}_{ctx.author.id}_{match_id}"
    
    if prediction_key in predictions:
        await ctx.send(f"❌ You've already predicted this match! Your prediction: **{predictions[prediction_key]['predicted_team']}**")
        return
    
    predictions[prediction_key] = {
        'user_id': ctx.author.id,
        'match_id': match_id,
        'predicted_team': team_name,
        'created_at': datetime.now().isoformat(),
        'guild_id': ctx.guild.id
    }
    save_json(PREDICTIONS_FILE, predictions)
    
    embed = discord.Embed(
        title="✅ Prediction Recorded!",
        description=f"You predicted **{team_name}** to win!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Match", value=f"{match_data['team1']} vs {match_data['team2']}", inline=False)
    
    await ctx.send(embed=embed)

# Predictions List
@bot.hybrid_command(name='predictions', description='View all active matches')
async def predictions(ctx):
    """View all active matches for predictions"""
    matches = load_json(MATCHES_FILE)
    active_matches = {k: v for k, v in matches.items() if v['guild_id'] == ctx.guild.id and v['status'] == 'active'}
    
    if not active_matches:
        await ctx.send("❌ No active matches for predictions!")
        return
    
    embed = discord.Embed(
        title="⚽ Active Matches",
        description="Use `+predict <match_id> <team_name>` to make your prediction!",
        color=discord.Color.blue()
    )
    
    for match_id, match_data in list(active_matches.items())[:25]:
        predictions_data = load_json(PREDICTIONS_FILE)
        match_predictions = sum(1 for p in predictions_data.values() if p['match_id'] == match_id)
        
        embed.add_field(
            name=f"{match_data['team1']} vs {match_data['team2']}",
            value=f"Match ID: `{match_id}`\nPredictions: {match_predictions}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Leaderboard
@bot.hybrid_command(name='leaderboard', aliases=['lb'], description='View richest players')
async def leaderboard(ctx):
    """Show richest players"""
    players = load_json(PLAYERS_FILE)
    guild_players = [(key, data) for key, data in players.items() if data['guild_id'] == ctx.guild.id]
    
    guild_players.sort(key=lambda x: x[1]['balance'], reverse=True)
    
    embed = discord.Embed(
        title="💰 Richest Players",
        description=f"Top 10 in {ctx.guild.name}",
        color=discord.Color.gold()
    )
    
    for i, (key, data) in enumerate(guild_players[:10], 1):
        member = ctx.guild.get_member(data['user_id'])
        if member:
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {member.display_name}",
                value=f"${data['balance']:,}",
                inline=False
            )
    
    await ctx.send(embed=embed)

# Stats
@bot.hybrid_command(name='stats', description='View bot statistics')
async def stats(ctx):
    """View bot statistics"""
    teams = load_json(TEAMS_FILE)
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    players = load_json(PLAYERS_FILE)
    transactions = load_json(TRANSACTIONS_FILE)
    matches = load_json(MATCHES_FILE)
    
    guild_teams = sum(1 for t in teams.values() if t['guild_id'] == ctx.guild.id)
    guild_fantasy = sum(1 for f in fantasy_teams.values() if f['guild_id'] == ctx.guild.id)
    guild_players = sum(1 for p in players.values() if p['guild_id'] == ctx.guild.id)
    guild_transactions = sum(1 for t in transactions if t['guild_id'] == ctx.guild.id)
    guild_matches = sum(1 for m in matches.values() if m['guild_id'] == ctx.guild.id)
    
    embed = discord.Embed(
        title="📊 Hand Football Statistics",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Total Teams", value=guild_teams, inline=True)
    embed.add_field(name="Fantasy Squads", value=guild_fantasy, inline=True)
    embed.add_field(name="Registered Players", value=guild_players, inline=True)
    embed.add_field(name="Total Transactions", value=guild_transactions, inline=True)
    embed.add_field(name="Active Matches", value=guild_matches, inline=True)
    embed.add_field(name="Server Members", value=ctx.guild.member_count, inline=True)
    
    await ctx.send(embed=embed)

# Ping
@bot.hybrid_command(name='ping', description='Check bot latency')
async def ping(ctx):
    """Check bot's ping"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot latency: **{latency}ms**",
        color=discord.Color.green() if latency < 100 else discord.Color.orange()
    )
    
    await ctx.send(embed=embed)

# Where Am I
@bot.hybrid_command(name='whereami', description='Show current server info')
async def whereami(ctx):
    """Show server information"""
    embed = discord.Embed(
        title=f"📍 {ctx.guild.name}",
        color=discord.Color.blue()
    )
    
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.add_field(name="Server ID", value=f"`{ctx.guild.id}`", inline=True)
    embed.add_field(name="Owner", value=ctx.guild.owner.mention if ctx.guild.owner else "Unknown", inline=True)
    embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
    embed.add_field(name="Created", value=ctx.guild.created_at.strftime("%Y-%m-%d"), inline=True)
    
    config = get_server_config(ctx.guild.id)
    embed.add_field(name="Bot Prefix", value=config['prefix'], inline=True)
    
    await ctx.send(embed=embed)

# Team Logs (Admin)
@bot.hybrid_command(name='teamlogs', aliases=['tl'], description='Set team logs channel (Admin only)')
@commands.has_permissions(administrator=True)
async def teamlogs(ctx, channel: discord.TextChannel):
    """Set team logs channel"""
    config = load_json(CONFIG_FILE)
    config['servers'][str(ctx.guild.id)]['team_logs_channel'] = channel.id
    save_json(CONFIG_FILE, config)
    
    await ctx.send(f"✅ Team logs channel set to {channel.mention}")

# Set Prefix (Admin)
@bot.hybrid_command(name='setprefix', description='Change bot prefix (Admin only)')
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix: str):
    """Change bot prefix"""
    config = load_json(CONFIG_FILE)
    config['servers'][str(ctx.guild.id)]['prefix'] = new_prefix
    save_json(CONFIG_FILE, config)
    
    await ctx.send(f"✅ Prefix changed to `{new_prefix}`")

# Ban from bot (Admin)
@bot.hybrid_command(name='ban', description='Ban a user from the bot (Admin only)')
@commands.has_permissions(administrator=True)
async def ban_user(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Ban a user from using the bot"""
    bans = load_json(BANS_FILE)
    key = f"{ctx.guild.id}_{member.id}"
    
    bans[key] = {
        'user_id': member.id,
        'guild_id': ctx.guild.id,
        'reason': reason,
        'banned_by': ctx.author.id,
        'banned_at': datetime.now().isoformat()
    }
    save_json(BANS_FILE, bans)
    
    await ctx.send(f"✅ {member.mention} has been banned from using the bot. Reason: {reason}")

# Unban from bot (Admin)
@bot.hybrid_command(name='unban', description='Unban a user (Admin only)')
@commands.has_permissions(administrator=True)
async def unban_user(ctx, member: discord.Member):
    """Unban a user"""
    bans = load_json(BANS_FILE)
    key = f"{ctx.guild.id}_{member.id}"
    
    if key in bans:
        del bans[key]
        save_json(BANS_FILE, bans)
        await ctx.send(f"✅ {member.mention} has been unbanned!")
    else:
        await ctx.send(f"❌ {member.mention} is not banned!")

# Ban Trader (Admin)
@bot.hybrid_command(name='bantrader', description='Ban user from trading (Admin only)')
@commands.has_permissions(administrator=True)
async def bantrader(ctx, member: discord.Member):
    """Ban from stock market"""
    bans = load_json(BANS_FILE)
    key = f"trader_{ctx.guild.id}_{member.id}"
    
    bans[key] = {
        'user_id': member.id,
        'guild_id': ctx.guild.id,
        'type': 'trader',
        'banned_at': datetime.now().isoformat()
    }
    save_json(BANS_FILE, bans)
    
    await ctx.send(f"✅ {member.mention} has been banned from trading!")

# Unban Trader (Admin)
@bot.hybrid_command(name='unbantrader', description='Unban user from trading (Admin only)')
@commands.has_permissions(administrator=True)
async def unbantrader(ctx, member: discord.Member):
    """Unban from stock market"""
    bans = load_json(BANS_FILE)
    key = f"trader_{ctx.guild.id}_{member.id}"
    
    if key in bans:
        del bans[key]
        save_json(BANS_FILE, bans)
        await ctx.send(f"✅ {member.mention} can now trade again!")
    else:
        await ctx.send(f"❌ {member.mention} is not banned from trading!")

# Troll command
@bot.hybrid_command(name='troll', description='Send a random troll message')
async def troll(ctx):
    """Send a funny troll message"""
    messages = [
        "You just got trolled! 😂",
        "Pranked! 🤪",
        "No u! 🔄",
        "Imagine getting trolled by a bot 💀",
        "Ez troll gg 😎",
        "You've been bamboozled! 🎭",
        "gottem 😈"
    ]
    await ctx.send(random.choice(messages))

# Trace
@bot.hybrid_command(name='trace', description='Get bot trace info')
async def trace(ctx):
    """Show trace information"""
    embed = discord.Embed(
        title="🔍 Bot Trace",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Python Version", value="3.11+", inline=True)
    embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
    
    await ctx.send(embed=embed)

# Tier (Admin)
@bot.hybrid_command(name='tier', description='List servers in a tier (Admin only)')
@commands.has_permissions(administrator=True)
async def tier(ctx):
    """List all servers (tiers)"""
    embed = discord.Embed(
        title="🏆 Server Tiers",
        description=f"Total Servers: {len(bot.guilds)}",
        color=discord.Color.gold()
    )
    
    for i, guild in enumerate(bot.guilds[:25], 1):
        embed.add_field(
            name=f"{i}. {guild.name}",
            value=f"Members: {guild.member_count}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Toggle (Admin/Owner)
@bot.hybrid_command(name='toggle', description='Toggle features (Admin only)')
@commands.has_permissions(administrator=True)
async def toggle(ctx, feature: str):
    """Toggle server features"""
    await ctx.send(f"✅ Toggled feature: {feature} (This is a placeholder - implement specific features as needed)")

# Daily Reward
@bot.hybrid_command(name='daily', description='Claim your daily reward')
async def daily(ctx):
    """Claim daily reward"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    last_claim = player_data.get('last_daily_claim')
    if last_claim:
        last_claim_date = datetime.fromisoformat(last_claim).date()
        if last_claim_date == datetime.now().date():
            await ctx.send("❌ You already claimed your daily reward today! Come back tomorrow.")
            return
    
    reward = 1000
    player_data['balance'] += reward
    player_data['last_daily_claim'] = datetime.now().isoformat()
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    embed = discord.Embed(
        title="🎁 Daily Reward Claimed!",
        description=f"You received ${reward:,}!",
        color=discord.Color.green()
    )
    embed.add_field(name="New Balance", value=f"${player_data['balance']:,}", inline=True)
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    print("Starting Hand Football Support Bot...")
    print("Make sure to set your bot token!")
    
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("⚠️ WARNING: Please set your Discord bot token!")
        print("Either set DISCORD_BOT_TOKEN environment variable or replace YOUR_BOT_TOKEN_HERE in the code")
    else:
        bot.run(TOKEN)
