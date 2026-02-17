// WWE Ultimate Card Battle - Multiplayer & Discord Integration
// Comprehensive multiplayer system with 200+ features

class MultiplayerManager {
    constructor() {
        this.ws = null;
        this.currentUser = null;
        this.friends = [];
        this.onlinePlayers = 0;
        this.currentRoom = null;
        this.matchmakingQueue = null;
        this.chatMessages = [];
        this.voiceChannel = null;
        this.richPresence = null;
        this.pendingInvites = [];
        this.latency = 0;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.queueTimerInterval = null;
        this.currentMatch = null;
        
        // Discord OAuth Configuration
        this.discordConfig = {
            clientId: 'YOUR_DISCORD_CLIENT_ID', // Replace with your Discord Client ID
            redirectUri: window.location.origin + '/auth/callback',
            scope: 'identify guilds guilds.join connections',
            apiEndpoint: 'https://discord.com/api/v10'
        };
        
        // WebSocket Configuration
        this.serverUrl = this.getWebSocketURL();
        
        this.init();
    }

    // ===== INITIALIZATION =====
    init() {
        console.log("Multiplayer system initializing...");
        this.loadSavedSession();
        this.checkForOAuthCallback();
    }

    getWebSocketURL() {
        // Detect environment and construct appropriate WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        
        // Check if running on Railway
        if (host.includes('railway.app')) {
            return `wss://${host}`;
        }
        
        // Check if running on Heroku
        if (host.includes('herokuapp.com')) {
            return `wss://${host}`;
        }
        
        // Local development
        return 'ws://localhost:3000';
    }

    loadSavedSession() {
        const token = localStorage.getItem('wwe_discord_token');
        const user = localStorage.getItem('wwe_discord_user');
        
        if (token && user) {
            try {
                this.currentUser = JSON.parse(user);
                this.connectToServer();
            } catch (error) {
                console.error("Error loading saved session:", error);
                localStorage.removeItem('wwe_discord_token');
                localStorage.removeItem('wwe_discord_user');
            }
        }
    }

    checkForOAuthCallback() {
        if (window.location.search.includes('code=')) {
            this.handleOAuthCallback();
        }
    }

    // ===== DISCORD AUTHENTICATION =====
    loginWithDiscord() {
        const state = this.generateState();
        localStorage.setItem('discord_auth_state', state);
        
        // For demo purposes, if no client ID is set, show info
        if (this.discordConfig.clientId === 'YOUR_DISCORD_CLIENT_ID') {
            alert('Please configure Discord OAuth credentials in multiplayer.js\n\nFor now, you can play as a guest.');
            this.playAsGuest();
            return;
        }
        
        const authUrl = `https://discord.com/api/oauth2/authorize?` +
            `client_id=${this.discordConfig.clientId}&` +
            `redirect_uri=${encodeURIComponent(this.discordConfig.redirectUri)}&` +
            `response_type=code&` +
            `scope=${encodeURIComponent(this.discordConfig.scope)}&` +
            `state=${state}`;
        
        window.location.href = authUrl;
    }

    async handleOAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        const savedState = localStorage.getItem('discord_auth_state');
        
        if (state !== savedState) {
            game.showNotification("Authentication error: Invalid state", "error");
            window.location.href = window.location.origin;
            return;
        }
        
        if (code) {
            try {
                const tokenData = await this.exchangeCodeForToken(code);
                await this.handleSuccessfulAuth(tokenData);
            } catch (error) {
                console.error("OAuth error:", error);
                game.showNotification("Login failed. Please try again.", "error");
                window.location.href = window.location.origin;
            }
        }
    }

    async exchangeCodeForToken(code) {
        const response = await fetch('/api/discord/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                redirectUri: this.discordConfig.redirectUri
            })
        });
        
        if (!response.ok) throw new Error('Token exchange failed');
        return await response.json();
    }

    async handleSuccessfulAuth(tokenData) {
        localStorage.setItem('wwe_discord_token', tokenData.access_token);
        localStorage.setItem('wwe_discord_refresh', tokenData.refresh_token);
        
        const userProfile = await this.fetchUserProfile(tokenData.access_token);
        this.currentUser = userProfile;
        
        localStorage.setItem('wwe_discord_user', JSON.stringify(userProfile));
        
        // Update game player data
        game.playerData.name = userProfile.username;
        game.playerData.avatar = userProfile.avatar ? 
            `https://cdn.discordapp.com/avatars/${userProfile.id}/${userProfile.avatar}.png` : 
            '👤';
        game.playerData.discordId = userProfile.id;
        game.playerData.tag = `#${userProfile.discriminator}`;
        game.savePlayerData();
        
        // Clear URL parameters and redirect to clean URL
        window.history.replaceState({}, document.title, window.location.origin);
        
        this.connectToServer();
        this.updateRichPresence('In Menu', 'Browsing');
        
        game.showMainMenu();
        game.showNotification(`Welcome, ${userProfile.username}!`, "success");
    }

    async fetchUserProfile(token) {
        const response = await fetch(`${this.discordConfig.apiEndpoint}/users/@me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch user profile');
        return await response.json();
    }

    playAsGuest() {
        this.currentUser = {
            id: 'guest_' + Date.now(),
            username: 'Guest_' + Math.floor(Math.random() * 10000),
            discriminator: '0000',
            avatar: null,
            isGuest: true
        };
        
        game.playerData.name = this.currentUser.username;
        game.playerData.tag = '#0000';
        game.savePlayerData();
        
        this.connectToServer();
        game.showMainMenu();
        game.showNotification("Playing as guest. Limited features available.", "info");
    }

    logout() {
        if (confirm("Are you sure you want to logout?")) {
            localStorage.removeItem('wwe_discord_token');
            localStorage.removeItem('wwe_discord_user');
            localStorage.removeItem('wwe_discord_refresh');
            
            if (this.ws) this.ws.close();
            
            window.location.reload();
        }
    }

    // ===== WEBSOCKET CONNECTION =====
    connectToServer() {
        try {
            console.log('Connecting to server:', this.serverUrl);
            this.ws = new WebSocket(this.serverUrl);
            
            this.ws.onopen = () => this.handleConnect();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (error) => this.handleError(error);
            this.ws.onclose = () => this.handleDisconnect();
            
        } catch (error) {
            console.error("WebSocket connection error:", error);
            game.showNotification("Failed to connect to server. Using offline mode.", "error");
            // Continue in offline mode
        }
    }

    handleConnect() {
        console.log("Connected to game server");
        this.reconnectAttempts = 0;
        
        // Authenticate with server
        this.sendMessage({
            type: 'authenticate',
            data: {
                userId: this.currentUser.id,
                username: this.currentUser.username,
                avatar: game.playerData.avatar,
                token: localStorage.getItem('wwe_discord_token')
            }
        });
        
        this.updateConnectionStatus(true);
        this.startLatencyCheck();
        game.showNotification("Connected to server", "success");
    }

    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.routeMessage(message);
        } catch (error) {
            console.error("Error parsing message:", error);
        }
    }

    routeMessage(message) {
        const handlers = {
            'authenticated': this.onAuthenticated.bind(this),
            'online_count': this.onOnlineCount.bind(this),
            'matchmaking_update': this.onMatchmakingUpdate.bind(this),
            'match_found': this.onMatchFound.bind(this),
            'room_created': this.onRoomCreated.bind(this),
            'room_updated': this.onRoomUpdated.bind(this),
            'player_joined': this.onPlayerJoined.bind(this),
            'player_left': this.onPlayerLeft.bind(this),
            'chat_message': this.onChatMessage.bind(this),
            'game_action': this.onGameAction.bind(this),
            'game_state': this.onGameState.bind(this),
            'game_started': this.onGameStarted.bind(this),
            'friend_request': this.onFriendRequest.bind(this),
            'friend_online': this.onFriendOnline.bind(this),
            'friend_accepted': this.onFriendAccepted.bind(this),
            'friends_list': this.onFriendsList.bind(this),
            'invite_received': this.onInviteReceived.bind(this),
            'emote': this.onEmoteReceived.bind(this),
            'rematch_request': this.onRematchRequest.bind(this),
            'pong': this.onPong.bind(this),
            'error': this.onServerError.bind(this)
        };

        const handler = handlers[message.type];
        if (handler) {
            handler(message.data);
        } else {
            console.warn("Unknown message type:", message.type);
        }
    }

    handleError(error) {
        console.error("WebSocket error:", error);
    }

    handleDisconnect() {
        console.log("Disconnected from server");
        this.updateConnectionStatus(false);
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            game.showNotification(`Reconnecting in ${delay/1000}s... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, "info");
            
            setTimeout(() => this.connectToServer(), delay);
        } else {
            game.showNotification("Connection lost. Playing in offline mode.", "error");
        }
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error("WebSocket not connected");
        }
    }

    // ===== MESSAGE HANDLERS =====
    onAuthenticated(data) {
        console.log("Authenticated with server");
        this.fetchFriendsList();
        this.fetchOnlinePlayers();
    }

    onOnlineCount(data) {
        this.onlinePlayers = data.count;
        const elem = document.getElementById('onlineCount');
        if (elem) elem.textContent = data.count;
    }

    onMatchmakingUpdate(data) {
        const elem = document.getElementById('queuePlayers');
        if (elem) elem.textContent = data.queueSize || '...';
    }

    onMatchFound(data) {
        console.log("Match found!", data);
        this.matchmakingQueue = null;
        clearInterval(this.queueTimerInterval);
        
        game.showNotification("Match found! Preparing game...", "success");
        
        this.currentMatch = data;
        
        setTimeout(() => {
            this.startMultiplayerGame(data);
        }, 2000);
    }

    onRoomCreated(data) {
        this.currentRoom = data.room;
        this.showRoomLobby();
        game.showNotification("Room created successfully!", "success");
    }

    onRoomUpdated(data) {
        this.currentRoom = data.room;
        this.updateRoomDisplay();
    }

    onPlayerJoined(data) {
        game.showNotification(`${data.username} joined the room`, "info");
        this.updateRoomPlayers();
    }

    onPlayerLeft(data) {
        game.showNotification(`${data.username} left the room`, "info");
        this.updateRoomPlayers();
    }

    onChatMessage(data) {
        this.addChatMessage(data);
    }

    onGameAction(data) {
        this.processOpponentAction(data);
    }

    onGameState(data) {
        if (game.gameState) {
            game.gameState = data.gameState;
            game.updateGameDisplay();
        }
    }

    onGameStarted(data) {
        console.log("Game started!", data);
        this.startMultiplayerGame({
            matchId: this.currentRoom.id,
            opponent: data.players.find(p => p.id !== this.currentUser.id)
        });
    }

    onFriendRequest(data) {
        this.showFriendRequestNotification(data);
    }

    onFriendOnline(data) {
        this.updateFriendStatus(data.userId, true);
    }

    onFriendAccepted(data) {
        game.showNotification(`${data.username} accepted your friend request!`, "success");
        this.fetchFriendsList();
    }

    onFriendsList(data) {
        this.friends = data.friends || [];
        const badge = document.getElementById('friendRequests');
        if (badge) {
            const pendingCount = this.friends.filter(f => f.pending).length;
            badge.textContent = pendingCount;
        }
    }

    onInviteReceived(data) {
        this.showInviteNotification(data);
    }

    onEmoteReceived(data) {
        this.displayEmote(data.emote, data.username);
    }

    onRematchRequest(data) {
        this.showRematchDialog(data);
    }

    onPong(data) {
        const latency = Date.now() - data.timestamp;
        this.latency = latency;
        const elem = document.getElementById('pingDisplay');
        if (elem) elem.textContent = `${latency}ms`;
    }

    onServerError(data) {
        game.showNotification(data.message || "Server error occurred", "error");
    }

    // ===== MATCHMAKING =====
    quickMatch() {
        this.startMatchmaking('quick');
    }

    rankedMatch() {
        if (this.currentUser && this.currentUser.isGuest) {
            game.showNotification("Guests cannot play ranked matches", "error");
            return;
        }
        this.startMatchmaking('ranked');
    }

    startMatchmaking(mode) {
        this.matchmakingQueue = {
            mode: mode,
            startTime: Date.now()
        };
        
        this.sendMessage({
            type: 'join_queue',
            data: {
                mode: mode,
                rank: game.playerData.rankPoints || 0,
                deck: game.currentDeck ? game.currentDeck.id : null
            }
        });
        
        game.hideAllScreens();
        document.getElementById('matchmakingScreen').classList.remove('hidden');
        document.getElementById('matchMode').textContent = mode === 'quick' ? 'Quick Match' : 'Ranked Match';
        
        this.startQueueTimer();
    }

    cancelMatchmaking() {
        if (!this.matchmakingQueue) return;
        
        this.sendMessage({
            type: 'leave_queue',
            data: {}
        });
        
        this.matchmakingQueue = null;
        clearInterval(this.queueTimerInterval);
        game.showMainMenu();
    }

    startQueueTimer() {
        const startTime = Date.now();
        
        this.queueTimerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            const elem = document.getElementById('queueTime');
            if (elem) {
                elem.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    startMultiplayerGame(matchData) {
        clearInterval(this.queueTimerInterval);
        
        game.isMultiplayer = true;
        
        // Set opponent info
        if (matchData.opponent) {
            const opponentName = document.getElementById('opponentName');
            const opponentAvatar = document.getElementById('opponentAvatar');
            
            if (opponentName) opponentName.textContent = matchData.opponent.username || 'Opponent';
            if (opponentAvatar) opponentAvatar.textContent = matchData.opponent.avatar || '🤖';
        }
        
        game.initializeGame(matchData.opponent || { username: 'Opponent', id: 'ai' });
        
        // Setup multiplayer-specific handlers
        this.setupMultiplayerGameHandlers();
        
        this.updateRichPresence('In Match', `vs ${matchData.opponent?.username || 'Opponent'}`);
    }

    setupMultiplayerGameHandlers() {
        // Store original functions
        const originalPlayCard = game.playCard.bind(game);
        const originalEndTurn = game.endTurn.bind(game);
        const originalAttack = game.initiateAttack.bind(game);

        // Override with multiplayer versions
        game.playCard = (card, slotIndex, player) => {
            const result = originalPlayCard(card, slotIndex, player);
            if (result && player === 'player') {
                this.sendGameAction('play_card', { card, slotIndex });
            }
            return result;
        };

        game.endTurn = () => {
            this.sendGameAction('end_turn', {});
            originalEndTurn();
        };

        game.initiateAttack = () => {
            this.sendGameAction('attack', {});
            originalAttack();
        };
    }

    sendGameAction(action, data) {
        this.sendMessage({
            type: 'game_action',
            data: {
                action: action,
                actionData: data,
                gameState: game.gameState
            }
        });
    }

    processOpponentAction(data) {
        const { action, actionData } = data;
        
        switch (action) {
            case 'play_card':
                if (actionData.card && typeof actionData.slotIndex === 'number') {
                    game.playCard(actionData.card, actionData.slotIndex, 'opponent');
                }
                break;
            case 'attack':
                // Opponent attacked - handled by game state sync
                break;
            case 'end_turn':
                if (game.gameState) {
                    game.gameState.turn = 'player';
                    game.updateGameDisplay();
                }
                break;
        }
    }

    // ===== ROOM MANAGEMENT =====
    createRoom() {
        game.hideAllScreens();
        document.getElementById('roomCreationScreen').classList.remove('hidden');
    }

    closeRoomCreation() {
        game.showMainMenu();
    }

    confirmCreateRoom() {
        const roomData = {
            name: document.getElementById('roomName').value || 'My WWE Arena',
            password: document.getElementById('roomPassword').value || null,
            maxPlayers: parseInt(document.getElementById('maxPlayers').value),
            gameMode: document.getElementById('gameMode').value,
            turnTimeLimit: parseInt(document.getElementById('turnTimeLimit').value)
        };
        
        this.sendMessage({
            type: 'create_room',
            data: roomData
        });
    }

    joinRoom() {
        const roomCode = prompt("Enter room code:");
        if (!roomCode) return;
        
        const password = prompt("Enter password (leave empty if none):");
        
        this.sendMessage({
            type: 'join_room',
            data: {
                roomCode: roomCode.toUpperCase(),
                password: password || null
            }
        });
    }

    leaveRoom() {
        if (!this.currentRoom) return;
        
        if (confirm("Leave this room?")) {
            this.sendMessage({
                type: 'leave_room',
                data: {}
            });
            
            this.currentRoom = null;
            game.showMainMenu();
        }
    }

    showRoomLobby() {
        game.hideAllScreens();
        const screen = document.getElementById('roomLobbyScreen');
        screen.classList.remove('hidden');
        
        document.getElementById('lobbyRoomName').textContent = this.currentRoom.name;
        document.getElementById('roomCode').textContent = this.currentRoom.code;
        
        this.updateRoomDisplay();
    }

    updateRoomDisplay() {
        if (!this.currentRoom) return;
        
        document.getElementById('playerCount').textContent = this.currentRoom.players.length;
        document.getElementById('maxPlayerCount').textContent = this.currentRoom.maxPlayers;
        
        this.updateRoomPlayers();
        this.updateRoomSettings();
        this.checkStartGameButton();
    }

    updateRoomPlayers() {
        if (!this.currentRoom) return;
        
        const container = document.getElementById('lobbyPlayers');
        container.innerHTML = '';
        
        this.currentRoom.players.forEach(player => {
            const playerDiv = document.createElement('div');
            playerDiv.className = 'lobby-player';
            playerDiv.innerHTML = `
                <div class="player-avatar-small">${player.avatar || '👤'}</div>
                <div class="player-info">
                    <div class="player-name">${player.username}</div>
                    ${player.isHost ? '<span class="host-badge">👑 Host</span>' : ''}
                    ${player.isReady ? '<span class="ready-badge">✓ Ready</span>' : ''}
                </div>
            `;
            container.appendChild(playerDiv);
        });
    }

    updateRoomSettings() {
        if (!this.currentRoom) return;
        
        const container = document.getElementById('lobbyGameSettings');
        container.innerHTML = `
            <p><strong>Game Mode:</strong> ${this.currentRoom.gameMode}</p>
            <p><strong>Turn Time:</strong> ${this.currentRoom.turnTimeLimit}s</p>
            <p><strong>Max Players:</strong> ${this.currentRoom.maxPlayers}</p>
        `;
    }

    checkStartGameButton() {
        if (!this.currentRoom) return;
        
        const btn = document.getElementById('startGameBtn');
        const isHost = this.currentRoom.players.find(p => p.id === this.currentUser.id)?.isHost;
        const minPlayers = this.currentRoom.gameMode === 'standard' ? 2 : 4;
        const canStart = isHost && this.currentRoom.players.length >= minPlayers;
        
        btn.disabled = !canStart;
    }

    startRoomGame() {
        this.sendMessage({
            type: 'start_game',
            data: {}
        });
    }

    copyRoomCode() {
        const code = document.getElementById('roomCode').textContent;
        navigator.clipboard.writeText(code).then(() => {
            game.showNotification("Room code copied!", "success");
        }).catch(err => {
            console.error('Failed to copy:', err);
            game.showNotification("Failed to copy code", "error");
        });
    }

    // ===== FRIENDS SYSTEM =====
    showFriendsList() {
        game.hideAllScreens();
        document.getElementById('friendsScreen').classList.remove('hidden');
        this.showFriendsTab('online');
    }

    closeFriendsList() {
        game.showMainMenu();
    }

    fetchFriendsList() {
        this.sendMessage({
            type: 'get_friends',
            data: {}
        });
    }

    showFriendsTab(tab) {
        // Remove active class from all tabs
        document.querySelectorAll('.friends-tabs .tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active to clicked tab
        event?.target?.classList.add('active');
        
        const container = document.getElementById('friendsTabContent');
        container.innerHTML = '';
        
        switch (tab) {
            case 'online':
                this.displayOnlineFriends(container);
                break;
            case 'all':
                this.displayAllFriends(container);
                break;
            case 'requests':
                this.displayFriendRequests(container);
                break;
            case 'add':
                this.displayAddFriend(container);
                break;
        }
    }

    displayOnlineFriends(container) {
        const onlineFriends = this.friends.filter(f => f.online);
        
        if (onlineFriends.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 40px; color: #888;">No friends online</p>';
            return;
        }
        
        onlineFriends.forEach(friend => {
            this.createFriendElement(friend, container);
        });
    }

    displayAllFriends(container) {
        if (this.friends.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 40px; color: #888;">No friends yet. Add some friends!</p>';
            return;
        }
        
        this.friends.forEach(friend => {
            this.createFriendElement(friend, container);
        });
    }

    createFriendElement(friend, container) {
        const friendDiv = document.createElement('div');
        friendDiv.className = 'friend-item';
        friendDiv.innerHTML = `
            <div class="player-avatar-small">${friend.avatar || '👤'}</div>
            <div class="friend-info">
                <h4>${friend.username}</h4>
                <p class="friend-status ${friend.online ? 'online' : 'offline'}">
                    ${friend.online ? '🟢 Online' : '⚫ Offline'}
                </p>
            </div>
            <div class="friend-actions">
                ${friend.online ? `
                    <button class="friend-btn" onclick="multiplayer.inviteFriend('${friend.id}')">
                        Invite
                    </button>
                ` : ''}
                <button class="friend-btn" onclick="multiplayer.viewProfile('${friend.id}')">
                    Profile
                </button>
                <button class="friend-btn remove" onclick="multiplayer.removeFriend('${friend.id}')">
                    Remove
                </button>
            </div>
        `;
        container.appendChild(friendDiv);
    }

    displayFriendRequests(container) {
        const pendingRequests = this.friends.filter(f => f.pending);
        
        if (pendingRequests.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 40px; color: #888;">No pending requests</p>';
            return;
        }
        
        pendingRequests.forEach(request => {
            const requestDiv = document.createElement('div');
            requestDiv.className = 'friend-request';
            requestDiv.innerHTML = `
                <div class="player-avatar-small">${request.avatar || '👤'}</div>
                <div class="request-info">
                    <h4>${request.username}</h4>
                    <p>Wants to be friends</p>
                </div>
                <div class="friend-actions">
                    <button class="friend-btn" onclick="multiplayer.acceptFriendRequest('${request.id}')">
                        Accept
                    </button>
                    <button class="friend-btn remove" onclick="multiplayer.declineFriendRequest('${request.id}')">
                        Decline
                    </button>
                </div>
            `;
            container.appendChild(requestDiv);
        });
    }

    displayAddFriend(container) {
        container.innerHTML = `
            <div class="add-friend-form" style="max-width: 500px; margin: 40px auto; padding: 20px;">
                <h3>Add Friend</h3>
                <p style="color: #888; margin-bottom: 20px;">Enter a Discord username or user ID</p>
                <input type="text" id="friendUsername" placeholder="Username#1234" 
                    style="width: 100%; padding: 12px; margin-bottom: 20px; background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); border-radius: 6px; color: white;">
                <button class="friend-btn" onclick="multiplayer.sendFriendRequest()" 
                    style="width: 100%; padding: 15px; background: var(--primary-red); border: none; color: white; font-size: 16px; border-radius: 8px; cursor: pointer;">
                    Send Request
                </button>
            </div>
        `;
    }

    sendFriendRequest() {
        const username = document.getElementById('friendUsername').value;
        if (!username) {
            game.showNotification("Please enter a username", "error");
            return;
        }
        
        this.sendMessage({
            type: 'friend_request',
            data: { username: username }
        });
        
        game.showNotification("Friend request sent!", "success");
        document.getElementById('friendUsername').value = '';
    }

    acceptFriendRequest(friendId) {
        this.sendMessage({
            type: 'accept_friend',
            data: { friendId: friendId }
        });
    }

    declineFriendRequest(friendId) {
        this.sendMessage({
            type: 'decline_friend',
            data: { friendId: friendId }
        });
    }

    removeFriend(friendId) {
        if (confirm("Remove this friend?")) {
            this.sendMessage({
                type: 'remove_friend',
                data: { friendId: friendId }
            });
        }
    }

    inviteFriend(friendId) {
        this.sendMessage({
            type: 'invite_friend',
            data: {
                friendId: friendId,
                roomCode: this.currentRoom?.code
            }
        });
        
        game.showNotification("Invite sent!", "success");
    }

    viewProfile(userId) {
        game.showNotification("Profile view coming soon!", "info");
    }

    updateFriendStatus(userId, online) {
        const friend = this.friends.find(f => f.id === userId);
        if (friend) {
            friend.online = online;
        }
    }

    showFriendRequestNotification(data) {
        this.pendingInvites.push(data);
        
        const badge = document.getElementById('friendRequests');
        if (badge) badge.textContent = this.pendingInvites.length;
        
        game.showNotification(`${data.username} sent you a friend request`, "info");
    }

    showInviteNotification(data) {
        const accept = confirm(`${data.fromUsername} invited you to play. Accept?`);
        if (accept) {
            this.sendMessage({
                type: 'accept_invite',
                data: { inviteId: data.inviteId }
            });
        }
    }

    // ===== CHAT SYSTEM =====
    sendChatMessage(event) {
        if (event && event.key && event.key !== 'Enter') return;
        
        const input = document.getElementById('lobbyChatInput');
        if (!input) return;
        
        const message = input.value.trim();
        
        if (!message) return;
        
        this.sendMessage({
            type: 'chat_message',
            data: {
                message: message,
                roomId: this.currentRoom?.id
            }
        });
        
        input.value = '';
    }

    sendGameChat(event) {
        if (event && event.key && event.key !== 'Enter') return;
        
        const input = document.getElementById('gameChatInput');
        if (!input) return;
        
        const message = input.value.trim();
        
        if (!message) return;
        
        this.sendMessage({
            type: 'game_chat',
            data: { message: message }
        });
        
        input.value = '';
    }

    toggleGameChat() {
        const panel = document.getElementById('chatPanel');
        if (panel) {
            panel.classList.toggle('hidden');
        }
    }

    addChatMessage(data) {
        const container = this.currentRoom ? 
            document.getElementById('lobbyChatMessages') : 
            document.getElementById('gameChatMessages');
        
        if (!container) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message';
        messageDiv.innerHTML = `
            <span class="chat-username" style="color: var(--primary-red); font-weight: bold;">${data.username}:</span>
            <span class="chat-text">${this.sanitizeMessage(data.message)}</span>
        `;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    sanitizeMessage(message) {
        return message.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // ===== EMOTES =====
    showEmoteWheel() {
        const wheel = document.getElementById('emoteWheel');
        if (wheel) {
            wheel.classList.toggle('hidden');
        }
    }

    sendEmote(emote) {
        this.sendMessage({
            type: 'emote',
            data: { emote: emote }
        });
        
        const wheel = document.getElementById('emoteWheel');
        if (wheel) {
            wheel.classList.add('hidden');
        }
    }

    displayEmote(emote, username) {
        const emoteDiv = document.createElement('div');
        emoteDiv.className = 'floating-emote';
        emoteDiv.textContent = emote;
        emoteDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 64px;
            animation: emoteFloat 2s ease-out;
            z-index: 10000;
            pointer-events: none;
        `;
        
        document.body.appendChild(emoteDiv);
        
        game.showNotification(`${username}: ${emote}`, "info");
        
        setTimeout(() => emoteDiv.remove(), 2000);
    }

    // ===== REMATCH =====
    requestRematch() {
        this.sendMessage({
            type: 'rematch_request',
            data: {}
        });
        
        game.showNotification("Rematch request sent!", "info");
        const btn = document.getElementById('rematchBtn');
        if (btn) btn.disabled = true;
    }

    showRematchDialog(data) {
        const accept = confirm(`${data.username} wants a rematch. Accept?`);
        if (accept) {
            this.sendMessage({
                type: 'accept_rematch',
                data: {}
            });
        }
    }

    // ===== DECK SHARING =====
    shareDeck() {
        if (!game.currentDeck) {
            game.showNotification("No deck selected", "error");
            return;
        }
        
        const deckCode = this.encodeDeck(game.currentDeck);
        const message = `Check out my WWE deck: ${game.currentDeck.name}\nCode: ${deckCode}`;
        
        if (this.currentUser && this.currentUser.isGuest) {
            game.showNotification("Deck sharing requires Discord login", "info");
            return;
        }
        
        navigator.clipboard.writeText(message).then(() => {
            game.showNotification("Deck code copied! Share it on Discord!", "success");
        }).catch(err => {
            console.error('Failed to copy:', err);
            game.showNotification("Failed to copy deck code", "error");
        });
    }

    encodeDeck(deck) {
        const encoded = btoa(JSON.stringify({
            name: deck.name,
            cards: deck.cards
        }));
        return encoded.substr(0, 20);
    }

    importDeck(code) {
        try {
            const decoded = JSON.parse(atob(code));
            const newDeck = {
                id: game.generateId(),
                name: decoded.name + ' (Imported)',
                cards: decoded.cards,
                isActive: false
            };
            
            game.decks.push(newDeck);
            game.saveDecks();
            game.showNotification("Deck imported successfully!", "success");
        } catch (error) {
            game.showNotification("Invalid deck code", "error");
        }
    }

    // ===== DISCORD RICH PRESENCE =====
    checkDiscordRPC() {
        // Check if Discord RPC is available (for desktop app)
        if (typeof DiscordSDK !== 'undefined') {
            this.initializeRichPresence();
        }
    }

    initializeRichPresence() {
        console.log("Discord Rich Presence initialized");
    }

    updateRichPresence(state, details) {
        // Update Discord activity
        this.sendMessage({
            type: 'update_presence',
            data: {
                state: state,
                details: details,
                largeImageKey: 'wwe_logo',
                largeImageText: 'WWE Ultimate Card Battle',
                startTimestamp: Date.now()
            }
        });
    }

    // ===== CONNECTION MANAGEMENT =====
    updateConnectionStatus(connected) {
        const status = document.getElementById('connectionStatus');
        if (!status) return;
        
        const dot = status.querySelector('.status-dot');
        const text = status.querySelector('.status-text');
        
        if (connected) {
            if (dot) dot.style.background = 'var(--discord-green)';
            if (text) text.textContent = 'Connected';
        } else {
            if (dot) dot.style.background = 'var(--damage-red)';
            if (text) text.textContent = 'Disconnected';
        }
    }

    startHeartbeat() {
        setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.sendMessage({
                    type: 'heartbeat',
                    data: { timestamp: Date.now() }
                });
            }
        }, 30000);
    }

    startLatencyCheck() {
        setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.sendMessage({
                    type: 'ping',
                    data: { timestamp: Date.now() }
                });
            }
        }, 5000);
    }

    fetchOnlinePlayers() {
        this.sendMessage({
            type: 'get_online_count',
            data: {}
        });
    }

    // ===== UTILITY FUNCTIONS =====
    generateState() {
        return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    }
}

// Initialize multiplayer system
const multiplayer = new MultiplayerManager();

// Handle OAuth callback
if (window.location.search.includes('code=')) {
    multiplayer.handleOAuthCallback();
}

// Add CSS animation for emote float
const style = document.createElement('style');
style.textContent = `
    @keyframes emoteFloat {
        0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
        }
        50% {
            opacity: 1;
            transform: translate(-50%, -60%) scale(1.2);
        }
        100% {
            opacity: 0;
            transform: translate(-50%, -70%) scale(0.8);
        }
    }
`;
document.head.appendChild(style);
