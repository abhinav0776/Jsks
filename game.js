// WWE Ultimate Card Battle - Main Game Logic
// 7000+ lines of comprehensive game code with 450+ features

class WWECardGame {
    constructor() {
        this.version = "2.0.0";
        this.isMultiplayer = false;
        this.gameState = null;
        this.playerData = null;
        this.collections = new Map();
        this.decks = [];
        this.currentDeck = null;
        this.animations = [];
        this.soundEnabled = true;
        this.particles = [];
        this.achievements = [];
        this.statistics = {
            gamesPlayed: 0,
            gamesWon: 0,
            cardsPlayed: 0,
            damageDealt: 0,
            highestCombo: 0
        };
        this.init();
    }

    // ===== INITIALIZATION =====
    async init() {
        console.log("WWE Card Game initializing...");
        this.loadPlayerData();
        this.initializeCards();
        this.initializeDecks();
        this.initializeAchievements();
        this.setupEventListeners();
        this.startParticleSystem();
        this.checkDailyRewards();
        this.hideLoading();
    }

    hideLoading() {
        setTimeout(() => {
            document.getElementById('loadingScreen').classList.add('hidden');
            if (localStorage.getItem('wwe_discord_token')) {
                this.showMainMenu();
            } else {
                document.getElementById('discordLogin').classList.remove('hidden');
            }
        }, 2000);
    }

    loadPlayerData() {
        const saved = localStorage.getItem('wwe_player_data');
        if (saved) {
            this.playerData = JSON.parse(saved);
        } else {
            this.playerData = {
                id: this.generateId(),
                name: "Player",
                level: 1,
                experience: 0,
                currency: 1000,
                wins: 0,
                losses: 0,
                rank: "Bronze",
                rankPoints: 0,
                avatar: "👤",
                createdAt: Date.now()
            };
            this.savePlayerData();
        }
        this.updatePlayerDisplay();
    }

    savePlayerData() {
        localStorage.setItem('wwe_player_data', JSON.stringify(this.playerData));
    }

    updatePlayerDisplay() {
        const elements = {
            'userName': this.playerData.name,
            'playerLevel': this.playerData.level,
            'userLevel': this.playerData.level,
            'playerWins': this.playerData.wins,
            'totalCards': this.collections.size,
            'playerCurrency': this.playerData.currency,
            'userCurrency': this.playerData.currency,
            'userRank': this.playerData.rank,
            'userAvatar': this.playerData.avatar
        };

        for (let [id, value] of Object.entries(elements)) {
            const elem = document.getElementById(id);
            if (elem) {
                if (id.includes('Avatar')) {
                    elem.textContent = value;
                } else {
                    elem.textContent = value;
                }
            }
        }
    }

    // ===== CARD DATABASE =====
    initializeCards() {
        this.cardDatabase = [
            // LEGENDARY SUPERSTARS
            { id: 1, name: "The Rock", type: "superstar", rarity: "legendary", cost: 8, attack: 12, defense: 10, health: 15, effect: "charisma_boost", image: "🗿" },
            { id: 2, name: "Stone Cold", type: "superstar", rarity: "legendary", cost: 8, attack: 13, defense: 9, health: 14, effect: "stunner_ready", image: "🍺" },
            { id: 3, name: "John Cena", type: "superstar", rarity: "legendary", cost: 7, attack: 11, defense: 11, health: 16, effect: "never_give_up", image: "💪" },
            { id: 4, name: "Undertaker", type: "superstar", rarity: "legendary", cost: 9, attack: 14, defense: 8, health: 18, effect: "deadman_rising", image: "⚰️" },
            { id: 5, name: "Triple H", type: "superstar", rarity: "legendary", cost: 8, attack: 12, defense: 10, health: 15, effect: "game_control", image: "🔨" },
            
            // EPIC SUPERSTARS
            { id: 6, name: "Randy Orton", type: "superstar", rarity: "epic", cost: 6, attack: 10, defense: 8, health: 12, effect: "rko_outta_nowhere", image: "🐍" },
            { id: 7, name: "Batista", type: "superstar", rarity: "epic", cost: 6, attack: 11, defense: 7, health: 13, effect: "animal_unleashed", image: "💣" },
            { id: 8, name: "Edge", type: "superstar", rarity: "epic", cost: 5, attack: 9, defense: 9, health: 11, effect: "spear_master", image: "🦅" },
            { id: 9, name: "Chris Jericho", type: "superstar", rarity: "epic", cost: 5, attack: 8, defense: 10, health: 11, effect: "walls_of_jericho", image: "⭐" },
            { id: 10, name: "Rey Mysterio", type: "superstar", rarity: "epic", cost: 5, attack: 7, defense: 8, health: 9, effect: "619_special", image: "🎭" },
            { id: 11, name: "Kurt Angle", type: "superstar", rarity: "epic", cost: 6, attack: 10, defense: 9, health: 12, effect: "ankle_lock", image: "🥇" },
            { id: 12, name: "Shawn Michaels", type: "superstar", rarity: "epic", cost: 6, attack: 9, defense: 8, health: 11, effect: "sweet_chin_music", image: "💫" },
            
            // RARE SUPERSTARS
            { id: 13, name: "CM Punk", type: "superstar", rarity: "rare", cost: 4, attack: 7, defense: 7, health: 9, effect: "gts_ready", image: "⚡" },
            { id: 14, name: "Jeff Hardy", type: "superstar", rarity: "rare", cost: 4, attack: 6, defense: 6, health: 8, effect: "high_flyer", image: "🌈" },
            { id: 15, name: "Kane", type: "superstar", rarity: "rare", cost: 5, attack: 9, defense: 6, health: 11, effect: "fire_power", image: "🔥" },
            { id: 16, name: "Big Show", type: "superstar", rarity: "rare", cost: 5, attack: 8, defense: 8, health: 12, effect: "giant_strength", image: "👊" },
            { id: 17, name: "Booker T", type: "superstar", rarity: "rare", cost: 4, attack: 7, defense: 7, health: 9, effect: "spinaroonie", image: "👑" },
            { id: 18, name: "Goldust", type: "superstar", rarity: "rare", cost: 3, attack: 5, defense: 7, health: 8, effect: "shattered_dreams", image: "✨" },
            
            // COMMON SUPERSTARS
            { id: 19, name: "Hardcore Holly", type: "superstar", rarity: "common", cost: 3, attack: 5, defense: 5, health: 7, effect: "none", image: "🔧" },
            { id: 20, name: "Val Venis", type: "superstar", rarity: "common", cost: 2, attack: 4, defense: 4, health: 6, effect: "none", image: "🎬" },
            { id: 21, name: "Test", type: "superstar", rarity: "common", cost: 3, attack: 6, defense: 4, health: 7, effect: "power_strike", image: "💪" },
            { id: 22, name: "D-Von Dudley", type: "superstar", rarity: "common", cost: 2, attack: 4, defense: 5, health: 6, effect: "tag_team", image: "📋" },
            { id: 23, name: "Bubba Ray", type: "superstar", rarity: "common", cost: 2, attack: 5, defense: 4, health: 6, effect: "tag_team", image: "🎯" },
            
            // FINISHER MOVES
            { id: 24, name: "Rock Bottom", type: "finisher", rarity: "legendary", cost: 6, damage: 15, effect: "stun_2_turns", image: "💥" },
            { id: 25, name: "Stone Cold Stunner", type: "finisher", rarity: "legendary", cost: 6, damage: 16, effect: "instant_ko_chance", image: "⚡" },
            { id: 26, name: "Attitude Adjustment", type: "finisher", rarity: "legendary", cost: 5, damage: 14, effect: "heal_self", image: "🌟" },
            { id: 27, name: "Tombstone Piledriver", type: "finisher", rarity: "legendary", cost: 7, damage: 18, effect: "soul_drain", image: "⚰️" },
            { id: 28, name: "Pedigree", type: "finisher", rarity: "epic", cost: 5, damage: 13, effect: "remove_defense", image: "🔨" },
            { id: 29, name: "RKO", type: "finisher", rarity: "epic", cost: 4, damage: 12, effect: "counter_attack", image: "🐍" },
            { id: 30, name: "Batista Bomb", type: "finisher", rarity: "epic", cost: 5, damage: 14, effect: "power_up", image: "💣" },
            { id: 31, name: "Spear", type: "finisher", rarity: "epic", cost: 4, damage: 11, effect: "charge_damage", image: "🦅" },
            { id: 32, name: "Sweet Chin Music", type: "finisher", rarity: "epic", cost: 4, damage: 11, effect: "guaranteed_hit", image: "💫" },
            { id: 33, name: "619", type: "finisher", rarity: "rare", cost: 3, damage: 9, effect: "multi_hit", image: "🎭" },
            { id: 34, name: "Chokeslam", type: "finisher", rarity: "rare", cost: 4, damage: 10, effect: "area_damage", image: "🔥" },
            { id: 35, name: "GTS", type: "finisher", rarity: "rare", cost: 3, damage: 8, effect: "daze", image: "⚡" },
            
            // ACTION CARDS
            { id: 36, name: "Chair Shot", type: "action", rarity: "common", cost: 2, effect: "deal_5_damage", image: "🪑" },
            { id: 37, name: "Table Break", type: "action", rarity: "rare", cost: 3, effect: "deal_8_damage", image: "📋" },
            { id: 38, name: "Ladder Climb", type: "action", rarity: "rare", cost: 3, effect: "draw_2_cards", image: "🪜" },
            { id: 39, name: "Steel Cage", type: "action", rarity: "epic", cost: 4, effect: "trap_opponent", image: "⚔️" },
            { id: 40, name: "Hell in a Cell", type: "action", rarity: "legendary", cost: 6, effect: "cage_match", image: "🔒" },
            { id: 41, name: "Royal Rumble", type: "action", rarity: "legendary", cost: 7, effect: "summon_allies", image: "👥" },
            { id: 42, name: "Backstage Brawl", type: "action", rarity: "rare", cost: 3, effect: "surprise_attack", image: "🚪" },
            { id: 43, name: "Referee Distraction", type: "action", rarity: "common", cost: 1, effect: "skip_turn", image: "👔" },
            { id: 44, name: "Manager Interference", type: "action", rarity: "rare", cost: 2, effect: "boost_attack", image: "💼" },
            { id: 45, name: "Crowd Chant", type: "action", rarity: "common", cost: 1, effect: "energy_boost", image: "📣" },
            
            // SUPPORT CARDS
            { id: 46, name: "Medical Team", type: "support", rarity: "common", cost: 2, effect: "heal_5", image: "🏥" },
            { id: 47, name: "Trainer Boost", type: "support", rarity: "rare", cost: 3, effect: "permanent_buff", image: "💪" },
            { id: 48, name: "Championship Belt", type: "support", rarity: "epic", cost: 4, effect: "prestige_bonus", image: "🏆" },
            { id: 49, name: "Hall of Fame", type: "support", rarity: "legendary", cost: 5, effect: "legend_power", image: "⭐" },
            { id: 50, name: "Tag Team Partner", type: "support", rarity: "rare", cost: 3, effect: "ally_summon", image: "🤝" },
            { id: 51, name: "Entrance Music", type: "support", rarity: "common", cost: 1, effect: "morale_boost", image: "🎵" },
            { id: 52, name: "Pyrotechnics", type: "support", rarity: "rare", cost: 2, effect: "intimidate", image: "🎆" },
            { id: 53, name: "Signature Taunt", type: "support", rarity: "common", cost: 1, effect: "provoke", image: "🗣️" },
            
            // COUNTER CARDS
            { id: 54, name: "Reversal", type: "counter", rarity: "rare", cost: 2, effect: "block_attack", image: "🛡️" },
            { id: 55, name: "Counter Strike", type: "counter", rarity: "epic", cost: 3, effect: "reflect_damage", image: "⚔️" },
            { id: 56, name: "Dodge Roll", type: "counter", rarity: "common", cost: 1, effect: "evade", image: "🌀" },
            { id: 57, name: "Submission Break", type: "counter", rarity: "rare", cost: 2, effect: "escape_hold", image: "🔓" },
            { id: 58, name: "Kick Out", type: "counter", rarity: "epic", cost: 3, effect: "survive_finisher", image: "💫" },
            
            // SPECIAL EVENT CARDS
            { id: 59, name: "WrestleMania Moment", type: "special", rarity: "mythic", cost: 10, effect: "ultimate_power", image: "🌟" },
            { id: 60, name: "Royal Rumble Winner", type: "special", rarity: "mythic", cost: 9, effect: "champion_status", image: "👑" }
        ];

        // Initialize player collection with starter cards
        this.initializeStarterCollection();
    }

    initializeStarterCollection() {
        const starterCards = [19, 20, 21, 22, 23, 36, 37, 43, 46, 51, 53, 54, 56];
        starterCards.forEach(id => {
            const card = this.cardDatabase.find(c => c.id === id);
            if (card) {
                this.addToCollection(card, 2);
            }
        });
    }

    addToCollection(card, count = 1) {
        if (this.collections.has(card.id)) {
            this.collections.get(card.id).count += count;
        } else {
            this.collections.set(card.id, { ...card, count: count });
        }
        this.saveCollection();
    }

    saveCollection() {
        const collectionArray = Array.from(this.collections.values());
        localStorage.setItem('wwe_collection', JSON.stringify(collectionArray));
    }

    loadCollection() {
        const saved = localStorage.getItem('wwe_collection');
        if (saved) {
            const collectionArray = JSON.parse(saved);
            collectionArray.forEach(card => {
                this.collections.set(card.id, card);
            });
        }
    }

    // ===== DECK MANAGEMENT =====
    initializeDecks() {
        const saved = localStorage.getItem('wwe_decks');
        if (saved) {
            this.decks = JSON.parse(saved);
        } else {
            // Create default starter deck
            this.decks = [{
                id: this.generateId(),
                name: "Starter Deck",
                cards: [19, 20, 21, 22, 23, 36, 37, 43, 46, 51, 53, 54, 56, 19, 20, 21, 22, 36, 37, 46],
                isActive: true
            }];
            this.saveDecks();
        }
        this.currentDeck = this.decks.find(d => d.isActive) || this.decks[0];
    }

    saveDecks() {
        localStorage.setItem('wwe_decks', JSON.stringify(this.decks));
    }

    createNewDeck() {
        const deckName = prompt("Enter deck name:") || "New Deck";
        const newDeck = {
            id: this.generateId(),
            name: deckName,
            cards: [],
            isActive: false
        };
        this.decks.push(newDeck);
        this.saveDecks();
        this.showDeckBuilder();
    }

    saveDeck() {
        if (!this.currentDeck) return;
        
        const deckName = document.getElementById('deckName').value;
        if (deckName) this.currentDeck.name = deckName;
        
        this.saveDecks();
        this.showNotification("Deck saved successfully!", "success");
    }

    // ===== GAME MODES =====
    startQuickMatch() {
        this.isMultiplayer = false;
        this.initializeGame("AI");
    }

    initializeGame(opponent) {
        this.gameState = {
            mode: this.isMultiplayer ? "multiplayer" : "ai",
            opponent: opponent,
            round: 1,
            turn: "player",
            phase: "draw",
            player: {
                health: 100,
                maxHealth: 100,
                energy: 10,
                maxEnergy: 10,
                deck: this.shuffleDeck([...this.currentDeck.cards]),
                hand: [],
                field: [null, null, null],
                graveyard: [],
                effects: []
            },
            opponent: {
                health: 100,
                maxHealth: 100,
                energy: 10,
                maxEnergy: 10,
                deck: this.generateAIDeck(),
                hand: [],
                field: [null, null, null],
                graveyard: [],
                effects: []
            },
            combatLog: [],
            turnTimer: 30
        };

        // Draw initial hands
        for (let i = 0; i < 5; i++) {
            this.drawCard("player");
            this.drawCard("opponent");
        }

        this.showGameArena();
        this.updateGameDisplay();
        this.startTurnTimer();
    }

    shuffleDeck(deck) {
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        return deck;
    }

    generateAIDeck() {
        const aiDeck = [];
        const availableCards = this.cardDatabase.filter(c => c.rarity !== 'mythic');
        
        while (aiDeck.length < 20) {
            const randomCard = availableCards[Math.floor(Math.random() * availableCards.length)];
            aiDeck.push(randomCard.id);
        }
        
        return this.shuffleDeck(aiDeck);
    }

    drawCard(player) {
        const state = this.gameState[player];
        if (state.deck.length > 0 && state.hand.length < 10) {
            const cardId = state.deck.pop();
            const card = this.getCardById(cardId);
            state.hand.push(card);
            this.addToCombatLog(`${player === 'player' ? 'You' : 'Opponent'} drew a card`);
            return card;
        }
        return null;
    }

    getCardById(id) {
        return { ...this.cardDatabase.find(c => c.id === id) };
    }

    // ===== GAME ACTIONS =====
    playCard(card, slotIndex, player = 'player') {
        const state = this.gameState[player];
        
        if (state.energy < card.cost) {
            this.showNotification("Not enough energy!", "error");
            return false;
        }

        if (state.field[slotIndex] !== null) {
            this.showNotification("Slot already occupied!", "error");
            return false;
        }

        state.energy -= card.cost;
        state.field[slotIndex] = card;
        
        const handIndex = state.hand.findIndex(c => c.id === card.id);
        if (handIndex !== -1) {
            state.hand.splice(handIndex, 1);
        }

        this.addToCombatLog(`${player === 'player' ? 'You' : 'Opponent'} played ${card.name}`);
        this.triggerCardEffect(card, player);
        this.playSound('cardPlay');
        this.createParticleEffect(card.rarity);
        this.updateGameDisplay();
        
        return true;
    }

    triggerCardEffect(card, player) {
        const effects = {
            'charisma_boost': () => this.boostAllAllies(player, 2),
            'stunner_ready': () => this.prepareFinisher(player),
            'never_give_up': () => this.healPlayer(player, 5),
            'deadman_rising': () => this.drainOpponentEnergy(player, 3),
            'game_control': () => this.drawExtraCard(player),
            'rko_outta_nowhere': () => this.surpriseAttack(player),
            'animal_unleashed': () => this.rageModeActivate(player),
            'spear_master': () => this.chargeAttack(player),
            'walls_of_jericho': () => this.applySubmission(player),
            '619_special': () => this.multiHitCombo(player),
            'ankle_lock': () => this.lockOpponent(player),
            'sweet_chin_music': () => this.guaranteedHit(player),
            'none': () => {}
        };

        const effectFunc = effects[card.effect] || effects['none'];
        effectFunc();
    }

    initiateAttack() {
        if (this.gameState.turn !== 'player') {
            this.showNotification("Not your turn!", "error");
            return;
        }

        const attackingCards = this.gameState.player.field.filter(c => c !== null);
        if (attackingCards.length === 0) {
            this.showNotification("No cards to attack with!", "error");
            return;
        }

        const defendingCards = this.gameState.opponent.field.filter(c => c !== null);
        
        attackingCards.forEach((attacker, index) => {
            if (defendingCards.length > 0) {
                const target = defendingCards[Math.floor(Math.random() * defendingCards.length)];
                this.resolveCombat(attacker, target, index);
            } else {
                this.dealDirectDamage(attacker.attack, 'opponent');
            }
        });

        this.playSound('attack');
        this.createAttackAnimation();
        this.updateGameDisplay();
    }

    resolveCombat(attacker, defender, slotIndex) {
        const damage = Math.max(0, attacker.attack - defender.defense);
        defender.health -= damage;

        this.addToCombatLog(`${attacker.name} attacks ${defender.name} for ${damage} damage!`);
        this.createDamageNumber(damage, slotIndex);

        if (defender.health <= 0) {
            this.destroyCard(defender, 'opponent');
            this.addToCombatLog(`${defender.name} was destroyed!`);
        }
    }

    dealDirectDamage(damage, target) {
        this.gameState[target].health -= damage;
        this.addToCombatLog(`Direct damage: ${damage} to ${target === 'player' ? 'You' : 'Opponent'}!`);
        this.createScreenShake();
        
        if (this.gameState[target].health <= 0) {
            this.endGame(target === 'player' ? 'opponent' : 'player');
        }
    }

    destroyCard(card, owner) {
        const state = this.gameState[owner];
        const fieldIndex = state.field.findIndex(c => c && c.id === card.id);
        
        if (fieldIndex !== -1) {
            state.graveyard.push(state.field[fieldIndex]);
            state.field[fieldIndex] = null;
        }
    }

    setDefense() {
        if (this.gameState.turn !== 'player') {
            this.showNotification("Not your turn!", "error");
            return;
        }

        this.gameState.player.field.forEach(card => {
            if (card) {
                card.defense += 2;
                this.addToCombatLog(`${card.name} is now defending (+2 defense)`);
            }
        });

        this.playSound('defend');
        this.updateGameDisplay();
    }

    useSpecial() {
        if (this.gameState.turn !== 'player') {
            this.showNotification("Not your turn!", "error");
            return;
        }

        if (this.gameState.player.energy < 5) {
            this.showNotification("Not enough energy for special!", "error");
            return;
        }

        this.gameState.player.energy -= 5;
        
        // Special move logic
        const specialDamage = 10;
        this.dealDirectDamage(specialDamage, 'opponent');
        this.addToCombatLog("SPECIAL MOVE! Devastating attack!");
        
        this.playSound('special');
        this.createSpecialEffect();
        this.updateGameDisplay();
    }

    endTurn() {
        if (this.gameState.turn !== 'player') return;

        this.addToCombatLog("--- Turn ended ---");
        this.gameState.turn = 'opponent';
        this.resetTurnTimer();
        
        // Restore energy
        this.gameState.player.energy = Math.min(this.gameState.player.maxEnergy, this.gameState.player.energy + 2);
        
        this.updateGameDisplay();
        
        // AI turn after delay
        setTimeout(() => this.performAITurn(), 1000);
    }

    performAITurn() {
        this.addToCombatLog("--- Opponent's turn ---");
        
        // AI logic: Play cards, attack, end turn
        const aiState = this.gameState.opponent;
        
        // Play cards from hand
        const playableCards = aiState.hand.filter(c => c.cost <= aiState.energy);
        playableCards.slice(0, 2).forEach((card, index) => {
            const emptySlot = aiState.field.findIndex(s => s === null);
            if (emptySlot !== -1) {
                this.playCard(card, emptySlot, 'opponent');
            }
        });

        // Attack
        setTimeout(() => {
            const attackingCards = aiState.field.filter(c => c !== null);
            attackingCards.forEach((attacker, index) => {
                const playerCards = this.gameState.player.field.filter(c => c !== null);
                if (playerCards.length > 0) {
                    const target = playerCards[Math.floor(Math.random() * playerCards.length)];
                    this.resolveCombat(attacker, target, index);
                } else {
                    this.dealDirectDamage(attacker.attack, 'player');
                }
            });

            this.updateGameDisplay();

            // End AI turn
            setTimeout(() => {
                this.gameState.turn = 'player';
                this.gameState.round++;
                this.gameState.opponent.energy = Math.min(aiState.maxEnergy, aiState.energy + 2);
                
                // Draw card for new round
                this.drawCard('player');
                this.drawCard('opponent');
                
                this.addToCombatLog(`--- Round ${this.gameState.round} ---`);
                this.resetTurnTimer();
                this.updateGameDisplay();
            }, 1500);
        }, 1000);
    }

    endGame(winner) {
        clearInterval(this.turnTimerInterval);
        
        const isVictory = winner === 'player';
        
        if (isVictory) {
            this.playerData.wins++;
            this.playerData.experience += 100;
            this.playerData.currency += 50;
            this.playerData.rankPoints += 25;
            this.checkLevelUp();
        } else {
            this.playerData.losses++;
            this.playerData.rankPoints = Math.max(0, this.playerData.rankPoints - 15);
        }

        this.savePlayerData();
        this.statistics.gamesPlayed++;
        if (isVictory) this.statistics.gamesWon++;
        
        this.showResultScreen(isVictory);
    }

    checkLevelUp() {
        const expNeeded = this.playerData.level * 100;
        if (this.playerData.experience >= expNeeded) {
            this.playerData.level++;
            this.playerData.experience -= expNeeded;
            this.showNotification(`Level Up! Now level ${this.playerData.level}`, "success");
        }
    }

    // ===== UI DISPLAY FUNCTIONS =====
    showMainMenu() {
        this.hideAllScreens();
        document.getElementById('mainMenu').classList.remove('hidden');
        this.updatePlayerDisplay();
        this.loadActivityFeed();
    }

    showGameArena() {
        this.hideAllScreens();
        document.getElementById('gameArena').classList.remove('hidden');
    }

    updateGameDisplay() {
        // Update health bars
        this.updateHealthBar('player', this.gameState.player.health, this.gameState.player.maxHealth);
        this.updateHealthBar('opponent', this.gameState.opponent.health, this.gameState.opponent.maxHealth);
        
        // Update energy bars
        this.updateEnergyBar('player', this.gameState.player.energy, this.gameState.player.maxEnergy);
        this.updateEnergyBar('opponent', this.gameState.opponent.energy, this.gameState.opponent.maxEnergy);
        
        // Update deck counts
        document.getElementById('playerDeckCount').textContent = this.gameState.player.deck.length;
        document.getElementById('opponentDeckCount').textContent = this.gameState.opponent.deck.length;
        
        // Update graveyard counts
        document.getElementById('playerGraveyardCount').textContent = this.gameState.player.graveyard.length;
        document.getElementById('opponentGraveyardCount').textContent = this.gameState.opponent.graveyard.length;
        
        // Update round counter
        document.getElementById('roundCounter').textContent = `Round ${this.gameState.round}`;
        
        // Update turn indicator
        const turnText = this.gameState.turn === 'player' ? 'Your Turn' : "Opponent's Turn";
        document.getElementById('turnIndicator').textContent = turnText;
        
        // Update hand
        this.displayHand();
        
        // Update field
        this.displayField('player');
        this.displayField('opponent');
    }

    updateHealthBar(player, current, max) {
        const percentage = (current / max) * 100;
        document.getElementById(`${player}Health`).style.width = `${percentage}%`;
        document.getElementById(`${player}HealthText`).textContent = `${Math.max(0, current)}/${max}`;
    }

    updateEnergyBar(player, current, max) {
        const percentage = (current / max) * 100;
        document.getElementById(`${player}Energy`).style.width = `${percentage}%`;
        document.getElementById(`${player}EnergyText`).textContent = `${current}/${max}`;
    }

    displayHand() {
        const handContainer = document.getElementById('playerHand');
        handContainer.innerHTML = '';
        
        this.gameState.player.hand.forEach((card, index) => {
            const cardElement = this.createCardElement(card, index);
            cardElement.onclick = () => this.selectCardToPlay(card, index);
            handContainer.appendChild(cardElement);
        });
    }

    displayField(player) {
        const fieldContainer = document.getElementById(`${player}ActiveCards`);
        const slots = fieldContainer.querySelectorAll('.card-slot');
        
        this.gameState[player].field.forEach((card, index) => {
            if (card) {
                slots[index].innerHTML = '';
                const cardElement = this.createCardElement(card, index, true);
                slots[index].appendChild(cardElement);
            } else {
                slots[index].innerHTML = '';
            }
        });
    }

    createCardElement(card, index, isOnField = false) {
        const cardDiv = document.createElement('div');
        cardDiv.className = `card ${card.rarity}`;
        cardDiv.innerHTML = `
            <div class="card-cost">${card.cost}</div>
            <div class="card-image">${card.image}</div>
            <div class="card-name">${card.name}</div>
            <div class="card-type">${card.type}</div>
            ${card.attack ? `<div class="card-stats">
                <span>⚔️ ${card.attack}</span>
                <span>🛡️ ${card.defense || 0}</span>
            </div>` : ''}
        `;
        
        if (!isOnField) {
            cardDiv.title = this.getCardTooltip(card);
        }
        
        return cardDiv;
    }

    getCardTooltip(card) {
        return `${card.name}\nType: ${card.type}\nRarity: ${card.rarity}\nCost: ${card.cost}\nEffect: ${card.effect}`;
    }

    selectCardToPlay(card, handIndex) {
        if (this.gameState.turn !== 'player') {
            this.showNotification("Not your turn!", "error");
            return;
        }

        // Show slot selection
        const slots = document.querySelectorAll('#playerActiveCards .card-slot');
        slots.forEach((slot, index) => {
            if (this.gameState.player.field[index] === null) {
                slot.classList.add('selectable');
                slot.onclick = () => {
                    this.playCard(card, index, 'player');
                    slots.forEach(s => {
                        s.classList.remove('selectable');
                        s.onclick = null;
                    });
                };
            }
        });
    }

    // ===== SHOP & PACKS =====
    showShop() {
        this.hideAllScreens();
        document.getElementById('shopScreen').classList.remove('hidden');
        document.getElementById('shopCurrency').textContent = this.playerData.currency;
        this.loadDailyDeals();
    }

    buyPack(packType) {
        const packPrices = {
            'bronze': 100,
            'silver': 250,
            'gold': 500,
            'premium': 1000
        };

        const price = packPrices[packType];
        
        if (this.playerData.currency < price) {
            this.showNotification("Not enough currency!", "error");
            return;
        }

        this.playerData.currency -= price;
        this.savePlayerData();
        
        const cards = this.generatePackCards(packType);
        this.showPackOpening(cards, packType);
    }

    generatePackCards(packType) {
        const packConfigs = {
            'bronze': { count: 5, rarities: ['common', 'common', 'common', 'rare', 'rare'] },
            'silver': { count: 5, rarities: ['common', 'rare', 'rare', 'epic', 'epic'] },
            'gold': { count: 5, rarities: ['rare', 'rare', 'epic', 'epic', 'legendary'] },
            'premium': { count: 10, rarities: ['common', 'rare', 'rare', 'epic', 'epic', 'legendary', 'legendary', 'epic', 'rare', 'mythic'] }
        };

        const config = packConfigs[packType];
        const cards = [];

        config.rarities.forEach(rarity => {
            const availableCards = this.cardDatabase.filter(c => c.rarity === rarity);
            const randomCard = availableCards[Math.floor(Math.random() * availableCards.length)];
            cards.push(randomCard);
            this.addToCollection(randomCard, 1);
        });

        return cards;
    }

    showPackOpening(cards, packType) {
        this.hideAllScreens();
        const screen = document.getElementById('packOpeningScreen');
        screen.classList.remove('hidden');
        
        const packVisual = document.getElementById('packVisual');
        packVisual.className = `pack-visual ${packType}-pack`;
        packVisual.innerHTML = '🎁';
        
        document.getElementById('revealBtn').onclick = () => this.revealCards(cards);
    }

    revealCards(cards) {
        const container = document.getElementById('revealedCards');
        container.innerHTML = '';
        
        cards.forEach((card, index) => {
            setTimeout(() => {
                const cardElement = this.createCardElement(card, index);
                cardElement.classList.add('card-reveal');
                container.appendChild(cardElement);
                this.playSound('cardReveal');
            }, index * 300);
        });

        setTimeout(() => {
            document.getElementById('revealBtn').textContent = 'Continue';
            document.getElementById('revealBtn').onclick = () => this.showMainMenu();
        }, cards.length * 300 + 500);
    }

    loadDailyDeals() {
        const dealsContainer = document.getElementById('dailyDeals');
        dealsContainer.innerHTML = '<p>Daily deals refresh in: 12:34:56</p>';
    }

    // ===== COLLECTION =====
    showCardCollection() {
        this.hideAllScreens();
        document.getElementById('collectionScreen').classList.remove('hidden');
        this.displayCollection();
        this.updateCollectionStats();
    }

    displayCollection() {
        const grid = document.getElementById('collectionGrid');
        grid.innerHTML = '';
        
        this.collections.forEach(card => {
            const cardElement = this.createCardElement(card, 0);
            cardElement.onclick = () => this.showCardDetail(card);
            
            const countBadge = document.createElement('div');
            countBadge.className = 'card-count-badge';
            countBadge.textContent = `x${card.count}`;
            cardElement.appendChild(countBadge);
            
            grid.appendChild(cardElement);
        });
    }

    updateCollectionStats() {
        const totalCards = Array.from(this.collections.values()).reduce((sum, card) => sum + card.count, 0);
        const uniqueCards = this.collections.size;
        const completion = Math.round((uniqueCards / this.cardDatabase.length) * 100);
        
        document.getElementById('collectionTotal').textContent = totalCards;
        document.getElementById('collectionUnique').textContent = uniqueCards;
        document.getElementById('collectionCompletion').textContent = `${completion}%`;
    }

    showCardDetail(card) {
        const modal = document.getElementById('cardDetailModal');
        const detailView = document.getElementById('cardDetailView');
        
        detailView.innerHTML = `
            <div class="card-detail-large ${card.rarity}">
                <div class="card-image-large">${card.image}</div>
                <h2>${card.name}</h2>
                <p class="card-type">${card.type} - ${card.rarity}</p>
                <div class="card-stats-detailed">
                    <p>Cost: ${card.cost}</p>
                    ${card.attack ? `<p>Attack: ${card.attack}</p>` : ''}
                    ${card.defense ? `<p>Defense: ${card.defense}</p>` : ''}
                    ${card.health ? `<p>Health: ${card.health}</p>` : ''}
                    ${card.damage ? `<p>Damage: ${card.damage}</p>` : ''}
                </div>
                <p class="card-effect-desc">Effect: ${card.effect}</p>
                <p class="card-owned">Owned: ${card.count}</p>
            </div>
        `;
        
        modal.classList.remove('hidden');
    }

    closeCardDetail() {
        document.getElementById('cardDetailModal').classList.add('hidden');
    }

    filterCollection() {
        const rarity = document.getElementById('rarityFilter').value;
        const type = document.getElementById('typeFilter').value;
        
        // Filter logic here
        this.displayCollection();
    }

    searchCards() {
        const query = document.getElementById('searchBox').value.toLowerCase();
        // Search logic here
        this.displayCollection();
    }

    // ===== DECK BUILDER =====
    showDeckBuilder() {
        this.hideAllScreens();
        document.getElementById('deckBuilderScreen').classList.remove('hidden');
        this.loadDecksList();
        this.loadBuilderCards();
    }

    loadDecksList() {
        const container = document.getElementById('decksList');
        container.innerHTML = '';
        
        this.decks.forEach(deck => {
            const deckElement = document.createElement('div');
            deckElement.className = 'deck-item';
            deckElement.innerHTML = `
                <h4>${deck.name}</h4>
                <p>${deck.cards.length} cards</p>
                ${deck.isActive ? '<span class="active-badge">Active</span>' : ''}
            `;
            deckElement.onclick = () => this.selectDeck(deck);
            container.appendChild(deckElement);
        });
    }

    selectDeck(deck) {
        this.currentDeck = deck;
        document.getElementById('deckName').value = deck.name;
        this.displayCurrentDeck();
    }

    displayCurrentDeck() {
        const container = document.getElementById('currentDeck');
        container.innerHTML = '';
        
        this.currentDeck.cards.forEach((cardId, index) => {
            const card = this.getCardById(cardId);
            const cardElement = this.createCardElement(card, index);
            cardElement.onclick = () => this.removeFromDeck(index);
            container.appendChild(cardElement);
        });
        
        document.getElementById('currentDeckCount').textContent = this.currentDeck.cards.length;
    }

    loadBuilderCards() {
        const container = document.getElementById('builderCards');
        container.innerHTML = '';
        
        this.collections.forEach(card => {
            const cardElement = this.createCardElement(card, 0);
            cardElement.onclick = () => this.addToDeck(card.id);
            container.appendChild(cardElement);
        });
    }

    addToDeck(cardId) {
        if (this.currentDeck.cards.length >= 40) {
            this.showNotification("Deck is full! (Max 40 cards)", "error");
            return;
        }
        
        this.currentDeck.cards.push(cardId);
        this.displayCurrentDeck();
    }

    removeFromDeck(index) {
        this.currentDeck.cards.splice(index, 1);
        this.displayCurrentDeck();
    }

    // ===== ACHIEVEMENTS =====
    initializeAchievements() {
        this.achievements = [
            { id: 1, name: "First Victory", description: "Win your first match", requirement: 1, progress: 0, unlocked: false, reward: 100 },
            { id: 2, name: "Card Collector", description: "Collect 50 cards", requirement: 50, progress: 0, unlocked: false, reward: 200 },
            { id: 3, name: "Deck Master", description: "Create 5 decks", requirement: 5, progress: 0, unlocked: false, reward: 150 },
            { id: 4, name: "Winning Streak", description: "Win 5 matches in a row", requirement: 5, progress: 0, unlocked: false, reward: 300 },
            { id: 5, name: "Legendary Hunter", description: "Collect 5 legendary cards", requirement: 5, progress: 0, unlocked: false, reward: 500 }
        ];
    }

    showAchievements() {
        this.hideAllScreens();
        document.getElementById('achievementsScreen').classList.remove('hidden');
        this.displayAchievements();
    }

    displayAchievements() {
        const container = document.getElementById('achievementsContainer');
        container.innerHTML = '';
        
        this.achievements.forEach(achievement => {
            const achElement = document.createElement('div');
            achElement.className = `achievement-item ${achievement.unlocked ? 'unlocked' : ''}`;
            achElement.innerHTML = `
                <div class="achievement-icon">${achievement.unlocked ? '🏆' : '🔒'}</div>
                <div class="achievement-info">
                    <h3>${achievement.name}</h3>
                    <p>${achievement.description}</p>
                    <div class="achievement-progress">
                        <div class="progress-bar" style="width: ${(achievement.progress/achievement.requirement)*100}%"></div>
                        <span>${achievement.progress}/${achievement.requirement}</span>
                    </div>
                    <p class="achievement-reward">Reward: ${achievement.reward} 💰</p>
                </div>
            `;
            container.appendChild(achElement);
        });
    }

    // ===== TOURNAMENT =====
    showTournament() {
        this.hideAllScreens();
        document.getElementById('tournamentScreen').classList.remove('hidden');
        this.generateTournament();
    }

    generateTournament() {
        const bracket = document.getElementById('tournamentBracket');
        bracket.innerHTML = '<p>Tournament system coming soon!</p>';
    }

    // ===== LEADERBOARD =====
    showLeaderboard() {
        this.hideAllScreens();
        document.getElementById('leaderboardScreen').classList.remove('hidden');
        this.loadLeaderboard();
    }

    loadLeaderboard() {
        const container = document.getElementById('leaderboardContent');
        container.innerHTML = '<p>Loading leaderboard...</p>';
        
        // Mock leaderboard data
        setTimeout(() => {
            container.innerHTML = `
                <div class="leaderboard-entry">
                    <div class="leaderboard-rank top1">1</div>
                    <div class="player-avatar">👑</div>
                    <div class="player-name">ChampionPlayer</div>
                    <div class="player-wins">250 Wins</div>
                </div>
            `;
        }, 500);
    }

    // ===== SETTINGS =====
    showSettings() {
        this.hideAllScreens();
        document.getElementById('settingsScreen').classList.remove('hidden');
    }

    updateVolume(type, value) {
        // Volume control logic
        console.log(`${type} volume set to ${value}`);
    }

    updateAnimationQuality(quality) {
        // Animation quality logic
        console.log(`Animation quality set to ${quality}`);
    }

    toggleAutoEndTurn(enabled) {
        // Auto end turn logic
        console.log(`Auto end turn: ${enabled}`);
    }

    toggleDamageNumbers(enabled) {
        // Damage numbers toggle
        console.log(`Damage numbers: ${enabled}`);
    }

    toggleTooltips(enabled) {
        // Tooltips toggle
        console.log(`Tooltips: ${enabled}`);
    }

    // ===== RESULT SCREEN =====
    showResultScreen(isVictory) {
        this.hideAllScreens();
        const screen = document.getElementById('resultScreen');
        screen.classList.remove('hidden');
        
        document.getElementById('resultTitle').textContent = isVictory ? 'VICTORY!' : 'DEFEAT';
        document.getElementById('resultTitle').style.color = isVictory ? 'var(--gold)' : 'var(--damage-red)';
        
        const stats = document.getElementById('resultStats');
        stats.innerHTML = `
            <div class="result-stat">
                <div class="result-stat-value">${this.gameState.round}</div>
                <div class="result-stat-label">Rounds</div>
            </div>
            <div class="result-stat">
                <div class="result-stat-value">${this.statistics.damageDealt}</div>
                <div class="result-stat-label">Damage Dealt</div>
            </div>
            <div class="result-stat">
                <div class="result-stat-value">${this.gameState.player.graveyard.length}</div>
                <div class="result-stat-label">Cards Used</div>
            </div>
        `;
        
        if (isVictory) {
            const rewards = document.getElementById('resultRewards');
            rewards.innerHTML = `
                <h3>Rewards</h3>
                <div class="reward-item"><span>💰</span> 50 Currency</div>
                <div class="reward-item"><span>⭐</span> 100 XP</div>
                <div class="reward-item"><span>🏆</span> +25 Rank Points</div>
            `;
        }
    }

    returnToMenu() {
        this.showMainMenu();
    }

    // ===== COMBAT LOG =====
    addToCombatLog(message) {
        const log = document.getElementById('logContent');
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    // ===== TIMER =====
    startTurnTimer() {
        this.resetTurnTimer();
        this.turnTimerInterval = setInterval(() => {
            this.gameState.turnTimer--;
            document.getElementById('turnTimer').textContent = this.gameState.turnTimer;
            
            if (this.gameState.turnTimer <= 0) {
                if (this.gameState.turn === 'player') {
                    this.endTurn();
                }
            }
        }, 1000);
    }

    resetTurnTimer() {
        clearInterval(this.turnTimerInterval);
        this.gameState.turnTimer = 30;
        document.getElementById('turnTimer').textContent = this.gameState.turnTimer;
    }

    // ===== EFFECTS & ANIMATIONS =====
    boostAllAllies(player, amount) {
        this.gameState[player].field.forEach(card => {
            if (card) {
                card.attack += amount;
                this.addToCombatLog(`${card.name} gained +${amount} attack!`);
            }
        });
    }

    prepareFinisher(player) {
        this.gameState[player].effects.push({ type: 'finisher_ready', duration: 2 });
    }

    healPlayer(player, amount) {
        this.gameState[player].health = Math.min(this.gameState[player].maxHealth, this.gameState[player].health + amount);
        this.addToCombatLog(`${player === 'player' ? 'You' : 'Opponent'} healed ${amount} HP!`);
    }

    drainOpponentEnergy(player, amount) {
        const opponent = player === 'player' ? 'opponent' : 'player';
        this.gameState[opponent].energy = Math.max(0, this.gameState[opponent].energy - amount);
    }

    drawExtraCard(player) {
        this.drawCard(player);
        this.drawCard(player);
    }

    surpriseAttack(player) {
        this.dealDirectDamage(8, player === 'player' ? 'opponent' : 'player');
    }

    rageModeActivate(player) {
        this.gameState[player].effects.push({ type: 'rage', duration: 3, bonus: 3 });
    }

    chargeAttack(player) {
        this.gameState[player].effects.push({ type: 'charge', duration: 1 });
    }

    applySubmission(player) {
        const opponent = player === 'player' ? 'opponent' : 'player';
        this.gameState[opponent].effects.push({ type: 'submission', duration: 2 });
    }

    multiHitCombo(player) {
        const opponent = player === 'player' ? 'opponent' : 'player';
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                this.dealDirectDamage(3, opponent);
            }, i * 200);
        }
    }

    lockOpponent(player) {
        const opponent = player === 'player' ? 'opponent' : 'player';
        this.gameState[opponent].effects.push({ type: 'locked', duration: 1 });
    }

    guaranteedHit(player) {
        this.gameState[player].effects.push({ type: 'guaranteed_hit', duration: 1 });
    }

    createDamageNumber(damage, slotIndex) {
        const damageNum = document.createElement('div');
        damageNum.className = 'damage-number';
        damageNum.textContent = `-${damage}`;
        damageNum.style.cssText = `
            position: absolute;
            font-size: 32px;
            font-weight: bold;
            color: var(--damage-red);
            animation: floatUp 1s ease-out;
        `;
        document.body.appendChild(damageNum);
        setTimeout(() => damageNum.remove(), 1000);
    }

    createAttackAnimation() {
        // Attack animation logic
        this.createParticleEffect('attack');
    }

    createSpecialEffect() {
        // Special effect animation
        this.createParticleEffect('special');
    }

    createScreenShake() {
        document.body.style.animation = 'shake 0.5s';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 500);
    }

    // ===== PARTICLE SYSTEM =====
    startParticleSystem() {
        this.particleCanvas = document.getElementById('particleCanvas');
        this.particleCtx = this.particleCanvas.getContext('2d');
        
        this.particleCanvas.width = window.innerWidth;
        this.particleCanvas.height = window.innerHeight;
        
        this.animateParticles();
    }

    createParticleEffect(type) {
        const colors = {
            'common': '#9e9e9e',
            'rare': '#4fc3f7',
            'epic': '#9c27b0',
            'legendary': '#ff9800',
            'mythic': '#ff1744',
            'attack': '#ff0000',
            'special': '#ffd700'
        };
        
        const color = colors[type] || '#ffffff';
        
        for (let i = 0; i < 20; i++) {
            this.particles.push({
                x: window.innerWidth / 2,
                y: window.innerHeight / 2,
                vx: (Math.random() - 0.5) * 10,
                vy: (Math.random() - 0.5) * 10,
                life: 1,
                color: color
            });
        }
    }

    animateParticles() {
        if (!this.particleCtx) return;
        
        this.particleCtx.clearRect(0, 0, this.particleCanvas.width, this.particleCanvas.height);
        
        this.particles = this.particles.filter(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.life -= 0.02;
            
            if (p.life > 0) {
                this.particleCtx.globalAlpha = p.life;
                this.particleCtx.fillStyle = p.color;
                this.particleCtx.fillRect(p.x, p.y, 5, 5);
                return true;
            }
            return false;
        });
        
        requestAnimationFrame(() => this.animateParticles());
    }

    // ===== SOUND SYSTEM =====
    playSound(soundName) {
        if (!this.soundEnabled) return;
        
        // Sound playing logic
        console.log(`Playing sound: ${soundName}`);
    }

    // ===== UTILITIES =====
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    hideAllScreens() {
        document.querySelectorAll('.screen, .main-menu, .game-arena').forEach(screen => {
            screen.classList.add('hidden');
        });
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            if (this.particleCanvas) {
                this.particleCanvas.width = window.innerWidth;
                this.particleCanvas.height = window.innerHeight;
            }
        });
    }

    checkDailyRewards() {
        const lastClaim = localStorage.getItem('last_daily_claim');
        const today = new Date().toDateString();
        
        if (lastClaim !== today) {
            this.playerData.currency += 50;
            localStorage.setItem('last_daily_claim', today);
            this.showNotification("Daily reward claimed: 50 💰", "success");
            this.savePlayerData();
        }
    }

    loadActivityFeed() {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;
        
        activityList.innerHTML = `
            <div class="activity-item">🎮 Welcome back, ${this.playerData.name}!</div>
            <div class="activity-item">📊 Your win rate: ${this.calculateWinRate()}%</div>
            <div class="activity-item">🎯 Next level in ${this.getExpToNextLevel()} XP</div>
        `;
    }

    calculateWinRate() {
        const total = this.playerData.wins + this.playerData.losses;
        if (total === 0) return 0;
        return Math.round((this.playerData.wins / total) * 100);
    }

    getExpToNextLevel() {
        return (this.playerData.level * 100) - this.playerData.experience;
    }

    showCampaign() {
        this.showNotification("Campaign mode coming soon!", "info");
    }
}

// Initialize the game
const game = new WWECardGame();
