// WWE Ultimate Card Battle - Multiplayer Server
// Node.js WebSocket Server with matchmaking, rooms, and game logic
// Deploy to Railway, Heroku, or any Node.js hosting platform

require('dotenv').config();

const WebSocket = require('ws');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const crypto = require('crypto');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// Middleware
app.use(cors({
    origin: process.env.CORS_ORIGIN || '*',
    credentials: true
}));
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// Server State
const server = {
    clients: new Map(),
    rooms: new Map(),
    matchmakingQueue: {
        quick: [],
        ranked: []
    },
    friends: new Map(),
    invites: new Map(),
    matches: new Map()
};

// Discord OAuth Configuration
const DISCORD_CONFIG = {
    clientId: process.env.DISCORD_CLIENT_ID || '',
    clientSecret: process.env.DISCORD_CLIENT_SECRET || '',
    redirectUri: process.env.DISCORD_REDIRECT_URI || `http://localhost:${PORT}/auth/callback`,
    apiEndpoint: 'https://discord.com/api/v10'
};

// ===== EXPRESS ROUTES =====
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        uptime: process.uptime(),
        clients: server.clients.size,
        rooms: server.rooms.size,
        timestamp: new Date().toISOString()
    });
});

app.post('/api/discord/token', async (req, res) => {
    try {
        const { code, redirectUri } = req.body;
        
        if (!DISCORD_CONFIG.clientId || !DISCORD_CONFIG.clientSecret) {
            return res.status(500).json({ 
                error: 'Discord OAuth not configured. Please set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET environment variables.' 
            });
        }
        
        const params = new URLSearchParams({
            client_id: DISCORD_CONFIG.clientId,
            client_secret: DISCORD_CONFIG.clientSecret,
            grant_type: 'authorization_code',
            code: code,
            redirect_uri: redirectUri
        });
        
        const response = await axios.post(
            'https://discord.com/api/oauth2/token',
            params.toString(),
            {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            }
        );
        
        res.json(response.data);
    } catch (error) {
        console.error('Token exchange error:', error.response?.data || error.message);
        res.status(500).json({ 
            error: 'Token exchange failed',
            details: error.response?.data?.error_description || error.message
        });
    }
});

app.get('/api/stats', (req, res) => {
    res.json({
        onlinePlayers: server.clients.size,
        activeRooms: server.rooms.size,
        queueSizes: {
            quick: server.matchmakingQueue.quick.length,
            ranked: server.matchmakingQueue.ranked.length
        },
        activeMatches: server.matches.size
    });
});

// Catch-all route for SPA
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// ===== WEBSOCKET SERVER =====
const httpServer = app.listen(PORT, () => {
    console.log('════════════════════════════════════════════════');
    console.log('🎮 WWE Ultimate Card Battle Server');
    console.log('════════════════════════════════════════════════');
    console.log(`🌐 Server running on port: ${PORT}`);
    console.log(`📊 Environment: ${NODE_ENV}`);
    console.log(`🔌 WebSocket: ws://localhost:${PORT}`);
    console.log(`⚙️  Discord OAuth: ${DISCORD_CONFIG.clientId ? 'Configured ✓' : 'Not configured ✗'}`);
    console.log('════════════════════════════════════════════════');
});

const wss = new WebSocket.Server({ 
    server: httpServer,
    path: '/'
});

wss.on('connection', (ws, req) => {
    const clientIp = req.socket.remoteAddress;
    console.log(`📥 New client connected from ${clientIp}`);
    
    const clientId = generateId();
    const client = {
        id: clientId,
        ws: ws,
        user: null,
        room: null,
        lastPing: Date.now(),
        ip: clientIp
    };
    
    server.clients.set(clientId, client);
    broadcastOnlineCount();
    
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            handleMessage(client, data);
        } catch (error) {
            console.error('Message parse error:', error);
            sendToClient(client, {
                type: 'error',
                data: { message: 'Invalid message format' }
            });
        }
    });
    
    ws.on('close', () => {
        handleDisconnect(client);
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
    
    // Send initial data
    setTimeout(() => {
        broadcastOnlineCount();
    }, 1000);
});

// ===== MESSAGE HANDLERS =====
function handleMessage(client, message) {
    const handlers = {
        'authenticate': handleAuthenticate,
        'join_queue': handleJoinQueue,
        'leave_queue': handleLeaveQueue,
        'create_room': handleCreateRoom,
        'join_room': handleJoinRoom,
        'leave_room': handleLeaveRoom,
        'start_game': handleStartGame,
        'game_action': handleGameAction,
        'chat_message': handleChatMessage,
        'game_chat': handleGameChat,
        'emote': handleEmote,
        'friend_request': handleFriendRequest,
        'accept_friend': handleAcceptFriend,
        'decline_friend': handleDeclineFriend,
        'remove_friend': handleRemoveFriend,
        'get_friends': handleGetFriends,
        'invite_friend': handleInviteFriend,
        'accept_invite': handleAcceptInvite,
        'rematch_request': handleRematchRequest,
        'accept_rematch': handleAcceptRematch,
        'update_presence': handleUpdatePresence,
        'get_online_count': handleGetOnlineCount,
        'ping': handlePing,
        'heartbeat': handleHeartbeat
    };
    
    const handler = handlers[message.type];
    if (handler) {
        try {
            handler(client, message.data);
        } catch (error) {
            console.error(`Error handling ${message.type}:`, error);
            sendToClient(client, {
                type: 'error',
                data: { message: 'Error processing request' }
            });
        }
    } else {
        console.warn('Unknown message type:', message.type);
    }
}

function handleAuthenticate(client, data) {
    client.user = {
        id: data.userId,
        username: data.username,
        avatar: data.avatar || '👤',
        token: data.token
    };
    
    console.log(`✅ User authenticated: ${data.username} (${data.userId})`);
    
    sendToClient(client, {
        type: 'authenticated',
        data: { success: true }
    });
    
    // Notify about online status
    broadcastOnlineCount();
}

function handleJoinQueue(client, data) {
    if (!client.user) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Not authenticated' }
        });
        return;
    }
    
    const { mode, rank, deck } = data;
    
    // Check if already in queue
    const existingEntry = server.matchmakingQueue[mode].find(e => e.client === client);
    if (existingEntry) {
        return;
    }
    
    const queueEntry = {
        client: client,
        mode: mode,
        rank: rank || 0,
        deck: deck,
        joinTime: Date.now()
    };
    
    server.matchmakingQueue[mode].push(queueEntry);
    
    console.log(`🎮 ${client.user.username} joined ${mode} queue (${server.matchmakingQueue[mode].length} in queue)`);
    
    // Try to find match immediately
    setTimeout(() => findMatch(mode), 500);
    
    // Send queue update
    broadcastQueueUpdate(mode);
}

function findMatch(mode) {
    const queue = server.matchmakingQueue[mode];
    
    if (queue.length < 2) return;
    
    // Simple matchmaking: pair first two players
    // In production, you'd want rank-based matching
    const player1 = queue.shift();
    const player2 = queue.shift();
    
    if (!player1 || !player2) return;
    
    const matchId = generateId();
    
    // Create match
    server.matches.set(matchId, {
        id: matchId,
        mode: mode,
        players: [player1.client, player2.client],
        startTime: Date.now()
    });
    
    // Notify both players
    sendToClient(player1.client, {
        type: 'match_found',
        data: {
            matchId: matchId,
            opponent: {
                id: player2.client.user.id,
                username: player2.client.user.username,
                avatar: player2.client.user.avatar
            }
        }
    });
    
    sendToClient(player2.client, {
        type: 'match_found',
        data: {
            matchId: matchId,
            opponent: {
                id: player1.client.user.id,
                username: player1.client.user.username,
                avatar: player1.client.user.avatar
            }
        }
    });
    
    console.log(`⚔️  Match found: ${player1.client.user.username} vs ${player2.client.user.username}`);
    
    broadcastQueueUpdate(mode);
}

function handleLeaveQueue(client, data) {
    // Remove from all queues
    Object.keys(server.matchmakingQueue).forEach(mode => {
        const initialLength = server.matchmakingQueue[mode].length;
        server.matchmakingQueue[mode] = server.matchmakingQueue[mode].filter(
            entry => entry.client !== client
        );
        
        if (server.matchmakingQueue[mode].length !== initialLength) {
            console.log(`🚪 ${client.user?.username || 'Unknown'} left ${mode} queue`);
            broadcastQueueUpdate(mode);
        }
    });
}

function handleCreateRoom(client, data) {
    if (!client.user) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Not authenticated' }
        });
        return;
    }
    
    const roomCode = generateRoomCode();
    const room = {
        id: generateId(),
        code: roomCode,
        name: data.name || 'WWE Arena',
        password: data.password || null,
        maxPlayers: data.maxPlayers || 2,
        gameMode: data.gameMode || 'standard',
        turnTimeLimit: data.turnTimeLimit || 30,
        host: client.user.id,
        players: [{
            id: client.user.id,
            username: client.user.username,
            avatar: client.user.avatar,
            isHost: true,
            isReady: true
        }],
        createdAt: Date.now()
    };
    
    server.rooms.set(roomCode, room);
    client.room = roomCode;
    
    sendToClient(client, {
        type: 'room_created',
        data: { room: room }
    });
    
    console.log(`🎪 Room created: ${roomCode} by ${client.user.username}`);
}

function handleJoinRoom(client, data) {
    if (!client.user) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Not authenticated' }
        });
        return;
    }
    
    const room = server.rooms.get(data.roomCode);
    
    if (!room) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Room not found' }
        });
        return;
    }
    
    if (room.players.length >= room.maxPlayers) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Room is full' }
        });
        return;
    }
    
    if (room.password && data.password !== room.password) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Incorrect password' }
        });
        return;
    }
    
    // Check if already in room
    const alreadyInRoom = room.players.find(p => p.id === client.user.id);
    if (alreadyInRoom) {
        sendToClient(client, {
            type: 'room_updated',
            data: { room: room }
        });
        return;
    }
    
    room.players.push({
        id: client.user.id,
        username: client.user.username,
        avatar: client.user.avatar,
        isHost: false,
        isReady: false
    });
    
    client.room = data.roomCode;
    
    console.log(`👥 ${client.user.username} joined room ${data.roomCode}`);
    
    // Notify all players in room
    broadcastToRoom(room, {
        type: 'player_joined',
        data: {
            userId: client.user.id,
            username: client.user.username,
            avatar: client.user.avatar
        }
    });
    
    // Send updated room state
    broadcastToRoom(room, {
        type: 'room_updated',
        data: { room: room }
    });
}

function handleLeaveRoom(client, data) {
    if (!client.room) return;
    
    const room = server.rooms.get(client.room);
    if (!room) return;
    
    room.players = room.players.filter(p => p.id !== client.user?.id);
    
    console.log(`🚪 ${client.user?.username || 'Unknown'} left room ${client.room}`);
    
    // If host left, assign new host
    if (room.host === client.user?.id && room.players.length > 0) {
        room.host = room.players[0].id;
        room.players[0].isHost = true;
        console.log(`👑 New host: ${room.players[0].username}`);
    }
    
    // If room is empty, delete it
    if (room.players.length === 0) {
        server.rooms.delete(client.room);
        console.log(`🗑️  Room ${client.room} deleted (empty)`);
    } else {
        broadcastToRoom(room, {
            type: 'player_left',
            data: {
                userId: client.user?.id,
                username: client.user?.username
            }
        });
        
        broadcastToRoom(room, {
            type: 'room_updated',
            data: { room: room }
        });
    }
    
    client.room = null;
}

function handleStartGame(client, data) {
    if (!client.room || !client.user) return;
    
    const room = server.rooms.get(client.room);
    if (!room || room.host !== client.user.id) {
        sendToClient(client, {
            type: 'error',
            data: { message: 'Only the host can start the game' }
        });
        return;
    }
    
    const minPlayers = room.gameMode === 'standard' ? 2 : 4;
    if (room.players.length < minPlayers) {
        sendToClient(client, {
            type: 'error',
            data: { message: `Need at least ${minPlayers} players to start` }
        });
        return;
    }
    
    console.log(`🎮 Game starting in room ${client.room}`);
    
    // Start game for all players in room
    broadcastToRoom(room, {
        type: 'game_started',
        data: {
            gameMode: room.gameMode,
            players: room.players
        }
    });
}

function handleGameAction(client, data) {
    // Relay game action to opponent(s)
    if (client.room) {
        const room = server.rooms.get(client.room);
        if (room) {
            broadcastToRoom(room, {
                type: 'game_action',
                data: data
            }, client);
        }
    } else {
        // In matchmaking game, find opponent through match
        const match = Array.from(server.matches.values()).find(m => 
            m.players.includes(client)
        );
        
        if (match) {
            const opponent = match.players.find(p => p !== client);
            if (opponent) {
                sendToClient(opponent, {
                    type: 'game_action',
                    data: data
                });
            }
        }
    }
}

function handleChatMessage(client, data) {
    if (!client.room || !client.user) return;
    
    const room = server.rooms.get(client.room);
    if (!room) return;
    
    const message = {
        userId: client.user.id,
        username: client.user.username,
        avatar: client.user.avatar,
        message: data.message,
        timestamp: Date.now()
    };
    
    console.log(`💬 [${room.code}] ${client.user.username}: ${data.message}`);
    
    broadcastToRoom(room, {
        type: 'chat_message',
        data: message
    });
}

function handleGameChat(client, data) {
    // Send chat to opponent in active match
    const match = Array.from(server.matches.values()).find(m => 
        m.players.includes(client)
    );
    
    if (match && client.user) {
        const opponent = match.players.find(p => p !== client);
        if (opponent) {
            sendToClient(opponent, {
                type: 'chat_message',
                data: {
                    userId: client.user.id,
                    username: client.user.username,
                    message: data.message,
                    timestamp: Date.now()
                }
            });
        }
    }
}

function handleEmote(client, data) {
    if (!client.user) return;
    
    // Broadcast to opponent or room
    if (client.room) {
        const room = server.rooms.get(client.room);
        if (room) {
            broadcastToRoom(room, {
                type: 'emote',
                data: {
                    userId: client.user.id,
                    username: client.user.username,
                    emote: data.emote
                }
            }, client);
        }
    } else {
        const match = Array.from(server.matches.values()).find(m => 
            m.players.includes(client)
        );
        
        if (match) {
            const opponent = match.players.find(p => p !== client);
            if (opponent) {
                sendToClient(opponent, {
                    type: 'emote',
                    data: {
                        userId: client.user.id,
                        username: client.user.username,
                        emote: data.emote
                    }
                });
            }
        }
    }
}

function handleFriendRequest(client, data) {
    if (!client.user) return;
    
    const requestId = generateId();
    server.invites.set(requestId, {
        from: client.user.id,
        fromUsername: client.user.username,
        to: data.username,
        type: 'friend_request',
        timestamp: Date.now()
    });
    
    console.log(`👥 Friend request: ${client.user.username} -> ${data.username}`);
    
    // Try to find target user and notify if online
    const targetClient = findClientByUsername(data.username);
    if (targetClient) {
        sendToClient(targetClient, {
            type: 'friend_request',
            data: {
                requestId: requestId,
                id: client.user.id,
                username: client.user.username,
                avatar: client.user.avatar
            }
        });
    }
    
    sendToClient(client, {
        type: 'info',
        data: { message: 'Friend request sent' }
    });
}

function handleAcceptFriend(client, data) {
    if (!client.user) return;
    
    // Initialize friends list if doesn't exist
    if (!server.friends.has(client.user.id)) {
        server.friends.set(client.user.id, []);
    }
    if (!server.friends.has(data.friendId)) {
        server.friends.set(data.friendId, []);
    }
    
    // Add to both friends lists
    server.friends.get(client.user.id).push(data.friendId);
    server.friends.get(data.friendId).push(client.user.id);
    
    console.log(`✅ Friend connection: ${client.user.username} <-> ${data.friendId}`);
    
    // Notify both users
    const friendClient = findClientById(data.friendId);
    if (friendClient) {
        sendToClient(friendClient, {
            type: 'friend_accepted',
            data: {
                id: client.user.id,
                username: client.user.username,
                avatar: client.user.avatar
            }
        });
    }
    
    sendToClient(client, {
        type: 'friend_accepted',
        data: {
            id: data.friendId,
            username: friendClient?.user?.username || 'Friend'
        }
    });
}

function handleDeclineFriend(client, data) {
    console.log(`❌ Friend request declined by ${client.user?.username}`);
}

function handleRemoveFriend(client, data) {
    if (!client.user) return;
    
    if (server.friends.has(client.user.id)) {
        const friends = server.friends.get(client.user.id);
        server.friends.set(client.user.id, friends.filter(id => id !== data.friendId));
    }
    
    if (server.friends.has(data.friendId)) {
        const friends = server.friends.get(data.friendId);
        server.friends.set(data.friendId, friends.filter(id => id !== client.user.id));
    }
    
    console.log(`💔 Friend removed: ${client.user.username} - ${data.friendId}`);
}

function handleGetFriends(client, data) {
    if (!client.user) return;
    
    const friendsList = server.friends.get(client.user.id) || [];
    
    // Get detailed info for each friend
    const friendsData = friendsList.map(friendId => {
        const friendClient = findClientById(friendId);
        return {
            id: friendId,
            online: !!friendClient,
            username: friendClient?.user?.username || 'Unknown',
            avatar: friendClient?.user?.avatar || '👤'
        };
    });
    
    sendToClient(client, {
        type: 'friends_list',
        data: { friends: friendsData }
    });
}

function handleInviteFriend(client, data) {
    if (!client.user) return;
    
    const inviteId = generateId();
    server.invites.set(inviteId, {
        from: client.user.id,
        to: data.friendId,
        roomCode: data.roomCode,
        timestamp: Date.now()
    });
    
    const friendClient = findClientById(data.friendId);
    if (friendClient) {
        sendToClient(friendClient, {
            type: 'invite_received',
            data: {
                inviteId: inviteId,
                fromUserId: client.user.id,
                fromUsername: client.user.username,
                roomCode: data.roomCode
            }
        });
    }
    
    console.log(`📧 Invite sent: ${client.user.username} -> ${data.friendId}`);
}

function handleAcceptInvite(client, data) {
    const invite = server.invites.get(data.inviteId);
    if (!invite) return;
    
    // Join the room
    handleJoinRoom(client, { roomCode: invite.roomCode });
    
    server.invites.delete(data.inviteId);
}

function handleRematchRequest(client, data) {
    if (!client.user) return;
    
    const match = Array.from(server.matches.values()).find(m => 
        m.players.includes(client)
    );
    
    if (match) {
        const opponent = match.players.find(p => p !== client);
        if (opponent) {
            sendToClient(opponent, {
                type: 'rematch_request',
                data: {
                    userId: client.user.id,
                    username: client.user.username
                }
            });
        }
    }
}

function handleAcceptRematch(client, data) {
    console.log(`🔄 Rematch accepted by ${client.user?.username}`);
    // Start new game with same opponent
}

function handleUpdatePresence(client, data) {
    if (client.user) {
        client.presence = data;
        console.log(`👤 Presence updated: ${client.user.username} - ${data.state}`);
    }
}

function handleGetOnlineCount(client, data) {
    sendToClient(client, {
        type: 'online_count',
        data: { count: server.clients.size }
    });
}

function handlePing(client, data) {
    sendToClient(client, {
        type: 'pong',
        data: { timestamp: data.timestamp }
    });
}

function handleHeartbeat(client, data) {
    client.lastPing = Date.now();
}

// ===== DISCONNECT HANDLER =====
function handleDisconnect(client) {
    console.log(`📤 Client disconnected: ${client.user?.username || client.id}`);
    
    // Remove from matchmaking queues
    Object.keys(server.matchmakingQueue).forEach(mode => {
        const initialLength = server.matchmakingQueue[mode].length;
        server.matchmakingQueue[mode] = server.matchmakingQueue[mode].filter(
            entry => entry.client !== client
        );
        
        if (server.matchmakingQueue[mode].length !== initialLength) {
            broadcastQueueUpdate(mode);
        }
    });
    
    // Leave room if in one
    if (client.room) {
        handleLeaveRoom(client, {});
    }
    
    // Remove from matches
    server.matches.forEach((match, matchId) => {
        if (match.players.includes(client)) {
            // Notify opponent
            const opponent = match.players.find(p => p !== client);
            if (opponent) {
                sendToClient(opponent, {
                    type: 'opponent_disconnected',
                    data: { reason: 'Opponent disconnected' }
                });
            }
            server.matches.delete(matchId);
        }
    });
    
    server.clients.delete(client.id);
    broadcastOnlineCount();
}

// ===== UTILITY FUNCTIONS =====
function sendToClient(client, message) {
    if (client.ws && client.ws.readyState === WebSocket.OPEN) {
        try {
            client.ws.send(JSON.stringify(message));
        } catch (error) {
            console.error('Error sending to client:', error);
        }
    }
}

function broadcastToRoom(room, message, exclude = null) {
    room.players.forEach(player => {
        const client = findClientById(player.id);
        if (client && client !== exclude) {
            sendToClient(client, message);
        }
    });
}

function broadcastToAll(message, exclude = null) {
    server.clients.forEach(client => {
        if (client !== exclude) {
            sendToClient(client, message);
        }
    });
}

function broadcastOnlineCount() {
    const message = {
        type: 'online_count',
        data: { count: server.clients.size }
    };
    
    server.clients.forEach(client => {
        sendToClient(client, message);
    });
}

function broadcastQueueUpdate(mode) {
    const queueSize = server.matchmakingQueue[mode].length;
    broadcastToAll({
        type: 'matchmaking_update',
        data: {
            mode: mode,
            queueSize: queueSize
        }
    });
}

function findClientById(userId) {
    for (let client of server.clients.values()) {
        if (client.user && client.user.id === userId) {
            return client;
        }
    }
    return null;
}

function findClientByUsername(username) {
    for (let client of server.clients.values()) {
        if (client.user && client.user.username === username) {
            return client;
        }
    }
    return null;
}

function generateId() {
    return crypto.randomBytes(16).toString('hex');
}

function generateRoomCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    // Ensure uniqueness
    if (server.rooms.has(code)) {
        return generateRoomCode();
    }
    
    return code;
}

// ===== CLEANUP & MAINTENANCE =====
// Clean up stale rooms every 5 minutes
setInterval(() => {
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    let cleaned = 0;
    
    for (let [code, room] of server.rooms) {
        if (room.createdAt < oneHourAgo) {
            server.rooms.delete(code);
            cleaned++;
        }
    }
    
    if (cleaned > 0) {
        console.log(`🧹 Cleaned ${cleaned} stale room(s)`);
    }
}, 5 * 60 * 1000);

// Clean up old invites every 5 minutes
setInterval(() => {
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    let cleaned = 0;
    
    for (let [id, invite] of server.invites) {
        if (invite.timestamp < oneHourAgo) {
            server.invites.delete(id);
            cleaned++;
        }
    }
    
    if (cleaned > 0) {
        console.log(`🧹 Cleaned ${cleaned} old invite(s)`);
    }
}, 5 * 60 * 1000);

// Check for inactive clients every 30 seconds
setInterval(() => {
    const timeout = 120000; // 2 minutes
    const now = Date.now();
    let disconnected = 0;
    
    server.clients.forEach((client, id) => {
        if (now - client.lastPing > timeout) {
            console.log(`⏰ Timeout: ${client.user?.username || id}`);
            client.ws.close();
            server.clients.delete(id);
            disconnected++;
        }
    });
    
    if (disconnected > 0) {
        broadcastOnlineCount();
    }
}, 30000);

// Log server stats every 5 minutes
setInterval(() => {
    console.log('════════════════════════════════════════════════');
    console.log('📊 Server Statistics');
    console.log('════════════════════════════════════════════════');
    console.log(`👥 Online Players: ${server.clients.size}`);
    console.log(`🎪 Active Rooms: ${server.rooms.size}`);
    console.log(`⚔️  Active Matches: ${server.matches.size}`);
    console.log(`🎮 Quick Queue: ${server.matchmakingQueue.quick.length}`);
    console.log(`🏆 Ranked Queue: ${server.matchmakingQueue.ranked.length}`);
    console.log(`⏱️  Uptime: ${Math.floor(process.uptime() / 60)} minutes`);
    console.log('════════════════════════════════════════════════');
}, 5 * 60 * 1000);

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 SIGTERM received. Shutting down gracefully...');
    
    // Notify all clients
    broadcastToAll({
        type: 'server_shutdown',
        data: { message: 'Server is shutting down for maintenance' }
    });
    
    // Close all connections
    server.clients.forEach(client => {
        client.ws.close();
    });
    
    // Close server
    httpServer.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
    
    // Force close after 10 seconds
    setTimeout(() => {
        console.log('⚠️  Forcing shutdown');
        process.exit(1);
    }, 10000);
});

process.on('SIGINT', () => {
    console.log('\n🛑 SIGINT received. Shutting down...');
    process.exit(0);
});

// Error handling
process.on('uncaughtException', (error) => {
    console.error('❌ Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason);
});

console.log('✅ Server initialization complete');
console.log('🎮 Ready to accept connections!');
