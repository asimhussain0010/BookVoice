/**
 * WebSocket Client for Real-Time Updates
 */

class WebSocketClient {
    constructor(userId) {
        this.userId = userId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = {};
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.userId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.emit('connected');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.emit('error', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.emit('disconnected');
            this.attemptReconnect();
        };
    }
    
    handleMessage(data) {
        const { type, ...payload } = data;
        
        // Emit event for this message type
        this.emit(type, payload);
        
        // Emit general message event
        this.emit('message', data);
    }
    
    send(type, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...data }));
        } else {
            console.error('WebSocket is not connected');
        }
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }
    
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.emit('max_reconnect_attempts');
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    getProgress(audioId) {
        this.send('get_progress', { audio_id: audioId });
    }
    
    ping() {
        this.send('ping');
    }
}

// Example usage:
/*
const user = JSON.parse(localStorage.getItem('user'));
const wsClient = new WebSocketClient(user.id);

wsClient.on('connected', () => {
    console.log('Connected to WebSocket');
});

wsClient.on('progress_update', (data) => {
    console.log('Progress update:', data);
    // Update UI with progress
    updateProgressBar(`progress-${data.audio_id}`, data.progress);
});

wsClient.on('disconnected', () => {
    console.log('Disconnected from WebSocket');
});

wsClient.connect();

// Request progress for specific audio file
wsClient.getProgress(123);
*/

window.WebSocketClient = WebSocketClient;