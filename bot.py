
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
FANTASY_SQUADS_FILE = f'{DATA_DIR}/fantasy_squads.json'

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
        LOANS_FILE: {},
        FANTASY_SQUADS_FILE: {}
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
            'created_at': datetime.now().isoformat(),
            'stats': {
                'goals': 0,
                'assists': 0,
                'interceptions': 0,
                'tackles': 0,
                'saves': 0
            }
        }
        save_json(PLAYERS_FILE, players)
    return players[key]

def update_player_data(user_id, guild_id, data):
    players = load_json(PLAYERS_FILE)
    key = f"{guild_id}_{user_id}"
    players[key] = data
    save_json(PLAYERS_FILE, players)

def calculate_stock_price_from_stats(user_id, guild_id):
    """Calculate stock price based on player stats"""
    player_data = get_player_data(user_id, guild_id)
    stats = player_data.get('stats', {})
    
    base_price = 1000
    
    # Calculate price based on stats
    goals = stats.get('goals', 0)
    assists = stats.get('assists', 0)
    interceptions = stats.get('interceptions', 0)
    tackles = stats.get('tackles', 0)
    saves = stats.get('saves', 0)
    
    # Pricing formula
    price = base_price + (goals * 200) + (assists * 150) + (interceptions * 50) + (tackles * 50) + (saves * 100)
    
    return max(price, base_price)

def get_stock_price(user_id, guild_id):
    """Get the current stock price for a user"""
    return calculate_stock_price_from_stats(user_id, guild_id)

def update_stock_price(user_id, guild_id, new_price=None):
    """Update stock price - if new_price is None, calculate from stats"""
    stocks = load_json(STOCKS_FILE)
    key = f"{guild_id}_{user_id}"
    
    if new_price is None:
        new_price = calculate_stock_price_from_stats(user_id, guild_id)
    
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

def generate_fantasy_squad_id():
    """Generate a unique 1-word ID for fantasy squads"""
    import string
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

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

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Check for raw stats message reply
    if message.reference and not isinstance(message.channel, discord.DMChannel):
        # Check if user is admin
        if message.author.guild_permissions.administrator:
            try:
                referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                
                # Check if referenced message contains raw statistics
                if "raw statistics" in referenced_msg.content.lower() or "```" in referenced_msg.content:
                    
                    content = referenced_msg.content
                    
                    # Find the code block
                    if "```python" in content or "```" in content:
                        start = content.find("```python")
                        if start == -1:
                            start = content.find("```")
                        
                        if start != -1:
                            start = content.find("\n", start) + 1
                            end = content.find("```", start)
                            
                            if end != -1:
                                stats_block = content[start:end].strip()
                                
                                # Process each line
                                lines = stats_block.split("\n")
                                added_count = 0
                                failed_count = 0
                                results = []
                                
                                for line in lines:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    
                                    # Parse: userid, goals, assists, interceptions, tackles, saves
                                    parts = [p.strip() for p in line.split(",")]
                                    
                                    if len(parts) >= 6:
                                        try:
                                            user_id = int(parts[0])
                                            goals = int(parts[1])
                                            assists = int(parts[2])
                                            interceptions = int(parts[3])
                                            tackles = int(parts[4])
                                            saves = int(parts[5])
                                            
                                            member = message.guild.get_member(user_id)
                                            
                                            if member and not member.bot:
                                                player_data = get_player_data(user_id, message.guild.id)
                                                
                                                if 'stats' not in player_data:
                                                    player_data['stats'] = {
                                                        'goals': 0,
                                                        'assists': 0,
                                                        'interceptions': 0,
                                                        'tackles': 0,
                                                        'saves': 0
                                                    }
                                                
                                                player_data['stats']['goals'] += goals
                                                player_data['stats']['assists'] += assists
                                                player_data['stats']['interceptions'] += interceptions
                                                player_data['stats']['tackles'] += tackles
                                                player_data['stats']['saves'] += saves
                                                
                                                update_player_data(user_id, message.guild.id, player_data)
                                                
                                                # Update stock price based on new stats
                                                update_stock_price(user_id, message.guild.id)
                                                
                                                results.append(f"✅ {member.mention}: G{goals} A{assists} I{interceptions} T{tackles} S{saves}")
                                                added_count += 1
                                            else:
                                                results.append(f"❌ User ID {user_id}: Not found or is a bot")
                                                failed_count += 1
                                        
                                        except ValueError:
                                            failed_count += 1
                                            continue
                                
                                # Send results
                                embed = discord.Embed(
                                    title="📊 Match Stats Added!",
                                    description=f"**Successfully added:** {added_count}\n**Failed:** {failed_count}",
                                    color=discord.Color.green()
                                )
                                
                                result_text = "\n".join(results[:25])
                                if result_text:
                                    embed.add_field(name="Results", value=result_text, inline=False)
                                
                                if len(results) > 25:
                                    embed.set_footer(text=f"Showing 25/{len(results)} results")
                                
                                await message.reply(embed=embed)
                                return
                
            except Exception as e:
                print(f"Error processing stats: {e}")
    
    # Check if message is in DMs
    if isinstance(message.channel, discord.DMChannel):
        transfers = load_json(TRANSFERS_FILE)
        loans = load_json(LOANS_FILE)
        
        # Check for transfer responses
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
                
                elif response == 'accept' or response.isdigit():
                    # Process transfer
                    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
                    from_key = f"{transfer_data['guild_id']}_{transfer_data['from_user']}"
                    to_key = f"{transfer_data['guild_id']}_{transfer_data['to_user']}"
                    
                    if to_key not in fantasy_teams:
                        await message.author.send("❌ You need to create a fantasy squad first! Use `+createfantasy`")
                        return
                    
                    # Find and remove player from sender
                    player_found = None
                    for i, p in enumerate(fantasy_teams[from_key]['players']):
                        if p['user_id'] == transfer_data['player_id']:
                            player_found = fantasy_teams[from_key]['players'].pop(i)
                            break
                    
                    if player_found:
                        # Add to receiver
                        fantasy_teams[to_key]['players'].append(player_found)
                        save_json(FANTASY_TEAMS_FILE, fantasy_teams)
                        
                        transfer_data['status'] = 'completed'
                        save_json(TRANSFERS_FILE, transfers)
                        
                        await message.author.send(f"✅ Transfer completed! {transfer_data['player_name']} added to your squad.")
                        
                        from_user = bot.get_user(transfer_data['from_user'])
                        if from_user:
                            await from_user.send(f"✅ Transfer completed! {transfer_data['player_name']} transferred.")
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
                        {'name': '+card @user', 'value': 'Generate player card for a user', 'inline': False},
                        {'name': '+profile @user', 'value': 'View player profile with stats', 'inline': False}
                    ]
                },
                {
                    'title': '🏆 Team Commands',
                    'description': 'Create and manage your team',
                    'fields': [
                        {'name': '+createteam <name>', 'value': 'Create a new team', 'inline': False},
                        {'name': '+jointeam <teamname>', 'value': 'Join an existing team', 'inline': False},
                        {'name': '+deleteteam <teamname>', 'value': 'Delete a team (owner only)', 'inline': False},
                        {'name': '+teamlist', 'value': 'View all teams in the server', 'inline': False},
                        {'name': '+vc @user', 'value': 'Set vice-captain (team owner only)', 'inline': False}
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
            embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)}")
            return embed
        
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
    embed.add_field(name="Card Value", value=f"${get_stock_price(target.id, ctx.guild.id):,}", inline=True)
    
    if player_data.get('team_id'):
        teams = load_json(TEAMS_FILE)
        team_key = f"{ctx.guild.id}_{player_data['team_id']}"
        if team_key in teams:
            embed.add_field(name="Team", value=teams[team_key].get('name', 'Unnamed Team'), inline=True)
    
    embed.set_thumbnail(url=target.display_avatar.url)
    
    await ctx.send(embed=embed)

# Wallet Command
@bot.hybrid_command(name='wallet', aliases=['wal'], description='Check wallet balance')
async def wallet(ctx, member: discord.Member = None):
    """Check your or another user's wallet balance"""
    target = member or ctx.author
    player_data = get_player_data(target.id, ctx.guild.id)
    
    embed = discord.Embed(
        title=f"👛 {target.display_name}'s Wallet",
        color=discord.Color.green()
    )
    
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💵 Cash", value=f"${player_data['balance']:,}", inline=False)
    embed.add_field(name="💳 Card Value", value=f"${get_stock_price(target.id, ctx.guild.id):,}", inline=True)
    
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
    stats = player_data.get('stats', {})
    
    # Create card image
    img = Image.new('RGB', (400, 600), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    
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
    y_pos = 220
    stat_list = [
        f"Goals: {stats.get('goals', 0)}",
        f"Assists: {stats.get('assists', 0)}",
        f"Card Value: ${current_price:,}",
        f"Balance: ${player_data['balance']:,}"
    ]
    
    for stat in stat_list:
        draw.text((200, y_pos), stat, font=font_small, fill=(255, 255, 255), anchor="mm")
        y_pos += 40
    
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

# Add Stats Command
@bot.hybrid_command(name='addstats', description='Add stats to a player (Admin only)')
@commands.has_permissions(administrator=True)
async def addstats(ctx, member: discord.Member, goals: int = 0, assists: int = 0, interceptions: int = 0, tackles: int = 0, saves: int = 0):
    """Add stats to a player"""
    player_data = get_player_data(member.id, ctx.guild.id)
    
    if 'stats' not in player_data:
        player_data['stats'] = {
            'goals': 0,
            'assists': 0,
            'interceptions': 0,
            'tackles': 0,
            'saves': 0
        }
    
    player_data['stats']['goals'] += goals
    player_data['stats']['assists'] += assists
    player_data['stats']['interceptions'] += interceptions
    player_data['stats']['tackles'] += tackles
    player_data['stats']['saves'] += saves
    
    update_player_data(member.id, ctx.guild.id, player_data)
    
    # Update stock price based on new stats
    update_stock_price(member.id, ctx.guild.id)
    
    embed = discord.Embed(
        title="✅ Stats Added!",
        description=f"Stats updated for {member.mention}",
        color=discord.Color.green()
    )
    embed.add_field(name="Goals", value=f"+{goals}", inline=True)
    embed.add_field(name="Assists", value=f"+{assists}", inline=True)
    embed.add_field(name="Interceptions", value=f"+{interceptions}", inline=True)
    embed.add_field(name="Tackles", value=f"+{tackles}", inline=True)
    embed.add_field(name="Saves", value=f"+{saves}", inline=True)
    embed.add_field(name="New Card Value", value=f"${get_stock_price(member.id, ctx.guild.id):,}", inline=False)
    
    await ctx.send(embed=embed)

# Profile Command
@bot.hybrid_command(name='profile', description='View player profile')
async def profile(ctx, member: discord.Member = None):
    """View player profile with stats"""
    target = member or ctx.author
    
    if target.bot:
        await ctx.send("❌ Bots don't have profiles!")
        return
    
    player_data = get_player_data(target.id, ctx.guild.id)
    current_price = get_stock_price(target.id, ctx.guild.id)
    
    embed = discord.Embed(
        title=f"👤 {target.display_name}'s Profile",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="💰 Balance", value=f"${player_data['balance']:,}", inline=True)
    embed.add_field(name="💳 Card Value", value=f"${current_price:,}", inline=True)
    
    if player_data.get('team_id'):
        teams = load_json(TEAMS_FILE)
        team_key = f"{ctx.guild.id}_{player_data['team_id']}"
        if team_key in teams:
            embed.add_field(name="⚽ Team", value=teams[team_key]['name'], inline=True)
    
    if 'stats' in player_data:
        stats = player_data['stats']
        embed.add_field(name="⚽ Goals", value=stats.get('goals', 0), inline=True)
        embed.add_field(name="🎯 Assists", value=stats.get('assists', 0), inline=True)
        embed.add_field(name="🛡️ Interceptions", value=stats.get('interceptions', 0), inline=True)
        embed.add_field(name="💪 Tackles", value=stats.get('tackles', 0), inline=True)
        embed.add_field(name="🧤 Saves", value=stats.get('saves', 0), inline=True)
    
    await ctx.send(embed=embed)

# Portfolio Command
@bot.hybrid_command(name='portfolio', aliases=['port'], description='View portfolio')
async def portfolio(ctx, member: discord.Member = None):
    """View your or another user's portfolio"""
    target = member or ctx.author
    
    if target.bot:
        await ctx.send("❌ Bots don't have portfolios!")
        return
    
    player_data = get_player_data(target.id, ctx.guild.id)
    fantasy_teams = load_json(FANTASY_TEAMS_FILE)
    key = f"{ctx.guild.id}_{target.id}"
    
    embed = discord.Embed(
        title=f"💼 {target.display_name}'s Portfolio",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="💰 Cash Balance", value=f"${player_data['balance']:,}", inline=True)
    
    squad_value = 0
    if key in fantasy_teams:
        for player in fantasy_teams[key]['players']:
            squad_value += get_stock_price(player['user_id'], ctx.guild.id)
    
    embed.add_field(name="⭐ Squad Value", value=f"${squad_value:,}", inline=True)
    
    total_value = player_data['balance'] + squad_value
    embed.add_field(name="📊 Total Portfolio", value=f"${total_value:,}", inline=True)
    
    if key in fantasy_teams and fantasy_teams[key]['players']:
        squad_text = ""
        for i, player in enumerate(fantasy_teams[key]['players'][:10], 1):
            current_price = get_stock_price(player['user_id'], ctx.guild.id)
            squad_text += f"{i}. <@{player['user_id']}> - ${current_price:,}\n"
        
        embed.add_field(name="Squad Players", value=squad_text, inline=False)
    
    await ctx.send(embed=embed)

# Stats Leaderboards
@bot.hybrid_command(name='lbgoals', description='Top 10 goal scorers')
async def lbgoals(ctx):
    """Leaderboard for goals"""
    players = load_json(PLAYERS_FILE)
    guild_players = [(key, data) for key, data in players.items() if data['guild_id'] == ctx.guild.id and 'stats' in data]
    
    guild_players.sort(key=lambda x: x[1]['stats'].get('goals', 0), reverse=True)
    
    embed = discord.Embed(
        title="⚽ Top 10 Goal Scorers",
        color=discord.Color.gold()
    )
    
    for i, (key, data) in enumerate(guild_players[:10], 1):
        member = ctx.guild.get_member(data['user_id'])
        if member:
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {member.display_name}",
                value=f"{data['stats'].get('goals', 0)} goals",
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name='lbassists', description='Top 10 assist providers')
async def lbassists(ctx):
    """Leaderboard for assists"""
    players = load_json(PLAYERS_FILE)
    guild_players = [(key, data) for key, data in players.items() if data['guild_id'] == ctx.guild.id and 'stats' in data]
    
    guild_players.sort(key=lambda x: x[1]['stats'].get('assists', 0), reverse=True)
    
    embed = discord.Embed(
        title="🎯 Top 10 Assist Providers",
        color=discord.Color.gold()
    )
    
    for i, (key, data) in enumerate(guild_players[:10], 1):
        member = ctx.guild.get_member(data['user_id'])
        if member:
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {member.display_name}",
                value=f"{data['stats'].get('assists', 0)} assists",
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name='lbdefense', description='Top 10 defenders')
async def lbdefense(ctx):
    """Leaderboard for tackles + interceptions"""
    players = load_json(PLAYERS_FILE)
    guild_players = [(key, data) for key, data in players.items() if data['guild_id'] == ctx.guild.id and 'stats' in data]
    
    guild_players.sort(key=lambda x: x[1]['stats'].get('tackles', 0) + x[1]['stats'].get('interceptions', 0), reverse=True)
    
    embed = discord.Embed(
        title="🛡️ Top 10 Defenders",
        color=discord.Color.gold()
    )
    
    for i, (key, data) in enumerate(guild_players[:10], 1):
        member = ctx.guild.get_member(data['user_id'])
        if member:
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            total = data['stats'].get('tackles', 0) + data['stats'].get('interceptions', 0)
            embed.add_field(
                name=f"{medal} {member.display_name}",
                value=f"{total} defensive actions",
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name='lbsaves', description='Top 10 goalkeepers')
async def lbsaves(ctx):
    """Leaderboard for saves"""
    players = load_json(PLAYERS_FILE)
    guild_players = [(key, data) for key, data in players.items() if data['guild_id'] == ctx.guild.id and 'stats' in data]
    
    guild_players.sort(key=lambda x: x[1]['stats'].get('saves', 0), reverse=True)
    
    embed = discord.Embed(
        title="🧤 Top 10 Goalkeepers",
        color=discord.Color.gold()
    )
    
    for i, (key, data) in enumerate(guild_players[:10], 1):
        member = ctx.guild.get_member(data['user_id'])
        if member:
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {member.display_name}",
                value=f"{data['stats'].get('saves', 0)} saves",
                inline=False
            )
    
    await ctx.send(embed=embed)

# Create Team
@bot.hybrid_command(name='createteam', description='Create your football team')
async def createteam(ctx, *, team_name: str):
    """Create a new team"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if player_data.get('team_id'):
        await ctx.send("❌ You're already in a team! Leave your current team first.")
        return
    
    teams = load_json(TEAMS_FILE)
    
    # Check if team name already exists
    for key, team in teams.items():
        if team['guild_id'] == ctx.guild.id and team['name'].lower() == team_name.lower():
            await ctx.send(f"❌ Team **{team_name}** already exists!")
            return
    
    team_id = f"team_{ctx.guild.id}_{ctx.author.id}_{len(teams)}"
    key = f"{ctx.guild.id}_{team_id}"
    
    teams[key] = {
        'id': team_id,
        'name': team_name,
        'owner_id': ctx.author.id,
        'guild_id': ctx.guild.id,
        'logo': None,
        'created_at': datetime.now().isoformat(),
        'members': [ctx.author.id],
        'captain': ctx.author.id,
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
    
    await ctx.send(embed=embed)

# Join Team
@bot.hybrid_command(name='jointeam', description='Join an existing team')
async def jointeam(ctx, *, team_name: str):
    """Join an existing team"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if player_data.get('team_id'):
        await ctx.send("❌ You're already in a team!")
        return
    
    teams = load_json(TEAMS_FILE)
    team_found = None
    team_key = None
    
    for key, team in teams.items():
        if team['guild_id'] == ctx.guild.id and team['name'].lower() == team_name.lower():
            team_found = team
            team_key = key
            break
    
    if not team_found:
        await ctx.send(f"❌ Team **{team_name}** not found!")
        return
    
    # Add member to team
    if ctx.author.id not in team_found['members']:
        team_found['members'].append(ctx.author.id)
    
    teams[team_key] = team_found
    save_json(TEAMS_FILE, teams)
    
    player_data['team_id'] = team_found['id']
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    await ctx.send(f"✅ You joined **{team_found['name']}**!")

# Delete Team
@bot.hybrid_command(name='deleteteam', description='Delete a team (owner only)')
async def deleteteam(ctx, *, team_name: str):
    """Delete a team"""
    teams = load_json(TEAMS_FILE)
    team_found = None
    team_key = None
    
    for key, team in teams.items():
        if team['guild_id'] == ctx.guild.id and team['name'].lower() == team_name.lower():
            team_found = team
            team_key = key
            break
    
    if not team_found:
        await ctx.send(f"❌ Team **{team_name}** not found!")
        return
    
    if team_found['owner_id'] != ctx.author.id:
        await ctx.send("❌ Only the team owner can delete the team!")
        return
    
    # Remove team from all members
    players = load_json(PLAYERS_FILE)
    for member_id in team_found['members']:
        player_key = f"{ctx.guild.id}_{member_id}"
        if player_key in players:
            players[player_key]['team_id'] = None
    save_json(PLAYERS_FILE, players)
    
    del teams[team_key]
    save_json(TEAMS_FILE, teams)
    
    await ctx.send(f"✅ Team **{team_name}** has been deleted.")

# Set Vice Captain
@bot.hybrid_command(name='vc', description='Set vice-captain of your team')
async def vc(ctx, member: discord.Member):
    """Set vice captain"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if not player_data.get('team_id'):
        await ctx.send("❌ You don't have a team!")
        return
    
    teams = load_json(TEAMS_FILE)
    team_key = f"{ctx.guild.id}_{player_data['team_id']}"
    
    if team_key not in teams:
        await ctx.send("❌ Team not found!")
        return
    
    if teams[team_key]['owner_id'] != ctx.author.id:
        await ctx.send("❌ Only the team owner can set vice-captain!")
        return
    
    if member.id not in teams[team_key]['members']:
        await ctx.send("❌ This player is not in your team!")
        return
    
    teams[team_key]['vice_captain'] = member.id
    save_json(TEAMS_FILE, teams)
    
    await ctx.send(f"✅ {member.mention} is now the vice-captain of **{teams[team_key]['name']}**!")

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
        members_count = len(team.get('members', []))
        embed.add_field(
            name=f"{i}. {team['name']}",
            value=f"Owner: {owner_name} | Members: {members_count}",
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
    
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    for player in fantasy_teams[key]['players']:
        player_data['balance'] += int(player['price'] * 0.5)
    
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    del fantasy_teams[key]
    save_json(FANTASY_TEAMS_FILE, fantasy_teams)
    
    await ctx.send(f"✅ Fantasy squad deleted! You received a 50% refund. New balance: ${player_data['balance']:,}")

# Buy Fantasy Player
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
            players_text += f"{i}. <@{player['user_id']}> - ${current_price:,}\n"
        
        embed.add_field(name="Players", value=players_text or "No players", inline=False)
    else:
        embed.add_field(name="Players", value="No players in squad", inline=False)
    
    embed.set_thumbnail(url=target.display_avatar.url)
    
    await ctx.send(embed=embed)

# Fantasy Team Create (Dream XI style)
@bot.hybrid_command(name='fantasyteamcreate', aliases=['ftc'], description='Create a fantasy team like Dream XI')
async def fantasyteamcreate(ctx, *, team_name: str):
    """Create a fantasy team (Dream XI style)"""
    fantasy_squads = load_json(FANTASY_SQUADS_FILE)
    
    # Check if user already has a fantasy team
    for key, squad in fantasy_squads.items():
        if squad['owner_id'] == ctx.author.id and squad['guild_id'] == ctx.guild.id:
            await ctx.send("❌ You already have a fantasy team! Delete it first with `+deletefantasyteam`")
            return
    
    # Generate unique ID
    squad_id = generate_fantasy_squad_id()
    
    while squad_id in fantasy_squads:
        squad_id = generate_fantasy_squad_id()
    
    fantasy_squads[squad_id] = {
        'id': squad_id,
        'name': team_name,
        'owner_id': ctx.author.id,
        'guild_id': ctx.guild.id,
        'players': [],
        'created_at': datetime.now().isoformat(),
        'shares_total': 1000,
        'share_price': 100,
        'shareholders': {}
    }
    save_json(FANTASY_SQUADS_FILE, fantasy_squads)
    
    embed = discord.Embed(
        title="✅ Fantasy Team Created!",
        description=f"**{team_name}** is ready!",
        color=discord.Color.green()
    )
    embed.add_field(name="Team ID", value=f"`{squad_id}`", inline=True)
    embed.add_field(name="Share Price", value="$100", inline=True)
    embed.add_field(name="Total Shares", value="1000", inline=True)
    
    await ctx.send(embed=embed)

# Fantasy Buy Shares
@bot.hybrid_command(name='fantasybuy', aliases=['fb'], description='Buy shares of a fantasy team')
async def fantasybuy(ctx, squad_id: str, amount: int):
    """Buy shares of a fantasy team"""
    fantasy_squads = load_json(FANTASY_SQUADS_FILE)
    
    if squad_id not in fantasy_squads:
        await ctx.send(f"❌ Fantasy team `{squad_id}` not found!")
        return
    
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    squad = fantasy_squads[squad_id]
    total_cost = squad['share_price'] * amount
    
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    if player_data['balance'] < total_cost:
        await ctx.send(f"❌ Insufficient funds! You need ${total_cost:,} but have ${player_data['balance']:,}")
        return
    
    # Deduct balance
    player_data['balance'] -= total_cost
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    # Add shares to user
    user_key = str(ctx.author.id)
    if user_key in squad['shareholders']:
        squad['shareholders'][user_key] += amount
    else:
        squad['shareholders'][user_key] = amount
    
    # Give money to team owner
    owner_data = get_player_data(squad['owner_id'], ctx.guild.id)
    owner_data['balance'] += total_cost
    update_player_data(squad['owner_id'], ctx.guild.id, owner_data)
    
    fantasy_squads[squad_id] = squad
    save_json(FANTASY_SQUADS_FILE, fantasy_squads)
    
    embed = discord.Embed(
        title="✅ Shares Purchased!",
        description=f"You bought {amount} shares of **{squad['name']}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Total Cost", value=f"${total_cost:,}", inline=True)
    embed.add_field(name="Your Shares", value=squad['shareholders'][user_key], inline=True)
    embed.add_field(name="Remaining Balance", value=f"${player_data['balance']:,}", inline=True)
    
    await ctx.send(embed=embed)

# Fantasy Sell Shares
@bot.hybrid_command(name='fantasysell', aliases=['fs'], description='Sell shares of a fantasy team')
async def fantasysell(ctx, squad_id: str, amount: int):
    """Sell shares of a fantasy team"""
    fantasy_squads = load_json(FANTASY_SQUADS_FILE)
    
    if squad_id not in fantasy_squads:
        await ctx.send(f"❌ Fantasy team `{squad_id}` not found!")
        return
    
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    squad = fantasy_squads[squad_id]
    user_key = str(ctx.author.id)
    
    if user_key not in squad['shareholders']:
        await ctx.send("❌ You don't own any shares of this team!")
        return
    
    if squad['shareholders'][user_key] < amount:
        await ctx.send(f"❌ You only own {squad['shareholders'][user_key]} shares!")
        return
    
    # Calculate sale value (90% of share price)
    sale_value = int(squad['share_price'] * 0.9 * amount)
    
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    player_data['balance'] += sale_value
    update_player_data(ctx.author.id, ctx.guild.id, player_data)
    
    # Remove shares
    squad['shareholders'][user_key] -= amount
    if squad['shareholders'][user_key] == 0:
        del squad['shareholders'][user_key]
    
    fantasy_squads[squad_id] = squad
    save_json(FANTASY_SQUADS_FILE, fantasy_squads)
    
    embed = discord.Embed(
        title="💰 Shares Sold!",
        description=f"You sold {amount} shares of **{squad['name']}**",
        color=discord.Color.orange()
    )
    embed.add_field(name="Sale Value", value=f"${sale_value:,}", inline=True)
    embed.add_field(name="New Balance", value=f"${player_data['balance']:,}", inline=True)
    
    await ctx.send(embed=embed)

# Fantasy List
@bot.hybrid_command(name='fantasylist', aliases=['fl'], description='List all fantasy teams')
async def fantasylist(ctx):
    """List all fantasy teams"""
    fantasy_squads = load_json(FANTASY_SQUADS_FILE)
    guild_squads = [squad for key, squad in fantasy_squads.items() if squad['guild_id'] == ctx.guild.id]
    
    if not guild_squads:
        await ctx.send("❌ No fantasy teams found!")
        return
    
    embed = discord.Embed(
        title="📋 Fantasy Teams",
        description=f"Total Teams: {len(guild_squads)}",
        color=discord.Color.blue()
    )
    
    for squad in guild_squads[:25]:
        owner = ctx.guild.get_member(squad['owner_id'])
        owner_name = owner.display_name if owner else "Unknown"
        embed.add_field(
            name=f"{squad['name']} (ID: {squad['id']})",
            value=f"Owner: {owner_name} | Share Price: ${squad['share_price']}",
            inline=False
        )
    
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
    
    # Show stats
    player_data = get_player_data(member.id, ctx.guild.id)
    stats = player_data.get('stats', {})
    stats_text = f"⚽ {stats.get('goals', 0)} | 🎯 {stats.get('assists', 0)} | 🛡️ {stats.get('interceptions', 0)}"
    embed.add_field(name="Stats", value=stats_text, inline=False)
    
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

# Stock Market Command
@bot.hybrid_command(name='stockmarket', aliases=['sm'], description='View the stock market')
async def stockmarket(ctx):
    """View enhanced stock market"""
    stocks = load_json(STOCKS_FILE)
    guild_stocks = [(user_id.split('_')[1], data) for user_id, data in stocks.items() 
                    if user_id.startswith(f"{ctx.guild.id}_")]
    
    guild_stocks.sort(key=lambda x: x[1]['price'], reverse=True)
    
    embed = discord.Embed(
        title="📈 Stock Market",
        description="Player Card Values & Changes",
        color=discord.Color.gold()
    )
    
    # Top gainers
    gainers = sorted(guild_stocks, key=lambda x: x[1].get('change_percent', 0), reverse=True)[:5]
    gainers_text = ""
    for user_id, data in gainers:
        member = ctx.guild.get_member(int(user_id))
        if member and not member.bot and data.get('change_percent', 0) > 0:
            gainers_text += f"{member.display_name}: ${data['price']:,} (+{data['change_percent']}%)\n"
    
    if gainers_text:
        embed.add_field(name="📈 Top Gainers", value=gainers_text, inline=False)
    
    # Top losers
    losers = sorted(guild_stocks, key=lambda x: x[1].get('change_percent', 0))[:5]
    losers_text = ""
    for user_id, data in losers:
        member = ctx.guild.get_member(int(user_id))
        if member and not member.bot and data.get('change_percent', 0) < 0:
            losers_text += f"{member.display_name}: ${data['price']:,} ({data['change_percent']}%)\n"
    
    if losers_text:
        embed.add_field(name="📉 Top Losers", value=losers_text, inline=False)
    
    # Most valuable
    valuable_text = ""
    for i, (user_id, data) in enumerate(guild_stocks[:5], 1):
        member = ctx.guild.get_member(int(user_id))
        if member and not member.bot:
            change = data.get('change_percent', 0)
            change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➖"
            valuable_text += f"{i}. {member.display_name}: ${data['price']:,} {change_emoji}\n"
    
    if valuable_text:
        embed.add_field(name="💎 Most Valuable", value=valuable_text, inline=False)
    
    await ctx.send(embed=embed)

# My Options Command
@bot.hybrid_command(name='myoptions', aliases=['myops'], description='View your active options contracts')
async def myoptions(ctx):
    """View all active options contracts"""
    player_data = get_player_data(ctx.author.id, ctx.guild.id)
    
    options = player_data.get('options', [])
    
    if not options:
        await ctx.send("❌ You don't have any active options contracts!")
        return
    
    embed = discord.Embed(
        title=f"📋 {ctx.author.display_name}'s Options Contracts",
        description=f"Total Contracts: {len(options)}",
        color=discord.Color.blue()
    )
    
    for i, option in enumerate(options[:10], 1):
        member = ctx.guild.get_member(option['player_id'])
        player_name = member.display_name if member else "Unknown"
        
        embed.add_field(
            name=f"{i}. {player_name}",
            value=f"Type: {option['type']}\nStrike: ${option['strike_price']:,}\nExpiry: {option['expiry']}\nPremium: ${option['premium']:,}",
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
    
    transfers = load_json(TRANSFERS_FILE)
    transfer_id = f"transfer_{ctx.guild.id}_{ctx.author.id}_{team_owner.id}_{int(datetime.now().timestamp())}"
    
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
        'guild_id': ctx.guild.id
    }
    save_json(TRANSFERS_FILE, transfers)
    
    embed_sender = discord.Embed(
        title="📤 Transfer Request Sent",
        description=f"You've initiated a transfer of **{player.display_name}** to {team_owner.mention}",
        color=discord.Color.blue()
    )
    embed_sender.add_field(name="Player", value=player.mention, inline=True)
    embed_sender.add_field(name="Current Price", value=f"${current_price:,}", inline=True)
    
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
        value="Type `accept` to accept\nType `reject` to decline",
        inline=False
    )
    
    try:
        await team_owner.send(embed=embed_receiver)
        await ctx.send(f"✅ Transfer request sent to {team_owner.mention}! Check your DMs.")
    except:
        await ctx.send(f"❌ Could not send DM to {team_owner.mention}. Make sure they have DMs enabled!")

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
    loan_id = f"loan_{ctx.guild.id}_{ctx.author.id}_{team_owner.id}_{int(datetime.now().timestamp())}"
    
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
    
    try:
        await team_owner.send(embed=embed_receiver)
        await ctx.send(f"✅ Loan request sent to {team_owner.mention}! Check your DMs.")
    except:
        await ctx.send(f"❌ Could not send DM to {team_owner.mention}. Make sure they have DMs enabled!")

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
    
    teams = load_json(TEAMS_FILE)
    guild_teams = {team['name'].lower(): team for key, team in teams.items() if team['guild_id'] == ctx.guild.id}
    
    if team1.lower() not in guild_teams:
        await ctx.send(f"❌ Team '{team1}' not found! Use `+teamlist` to see all teams.")
        return
    
    if team2.lower() not in guild_teams:
        await ctx.send(f"❌ Team '{team2}' not found! Use `+teamlist` to see all teams.")
        return
    
    matches = load_json(MATCHES_FILE)
    match_id = f"match_{ctx.guild.id}_{len(matches)}_{int(datetime.now().timestamp())}"
    
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
    fantasy_squads = load_json(FANTASY_SQUADS_FILE)
    
    guild_teams = sum(1 for t in teams.values() if t['guild_id'] == ctx.guild.id)
    guild_fantasy = sum(1 for f in fantasy_teams.values() if f['guild_id'] == ctx.guild.id)
    guild_players = sum(1 for p in players.values() if p['guild_id'] == ctx.guild.id)
    guild_transactions = sum(1 for t in transactions if t['guild_id'] == ctx.guild.id)
    guild_matches = sum(1 for m in matches.values() if m['guild_id'] == ctx.guild.id)
    guild_fantasy_squads = sum(1 for s in fantasy_squads.values() if s['guild_id'] == ctx.guild.id)
    
    embed = discord.Embed(
        title="📊 Hand Football Statistics",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Total Teams", value=guild_teams, inline=True)
    embed.add_field(name="Fantasy Squads", value=guild_fantasy, inline=True)
    embed.add_field(name="Fantasy Teams", value=guild_fantasy_squads, inline=True)
    embed.add_field(name="Registered Players", value=guild_players, inline=True)
    embed.add_field(name="Total Transactions", value=guild_transactions, inline=True)
    embed.add_field(name="Active Matches", value=guild_matches, inline=True)
    
    await ctx.send(embed=embed)

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
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    print("Starting Hand Football Support Bot...")
    print("Make sure to set your bot token!")
    
    TOKEN = os.getenv('DISCORD_BOT_TOKEN') or 'YOUR_BOT_TOKEN_HERE'
    
    if TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("⚠️ WARNING: Please set your Discord bot token!")
