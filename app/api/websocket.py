"""
WebSocket API
Real-time updates for audio generation progress
"""

from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audio import AudioFile
import json

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, user_id: int, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/ws/123');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(data);
        };
    """
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get('type') == 'ping':
                await manager.send_personal_message(
                    {'type': 'pong'},
                    user_id
                )
            
            elif message.get('type') == 'get_progress':
                audio_id = message.get('audio_id')
                if audio_id:
                    audio = db.query(AudioFile).filter(
                        AudioFile.id == audio_id,
                        AudioFile.user_id == user_id
                    ).first()
                    
                    if audio:
                        await manager.send_personal_message({
                            'type': 'progress_update',
                            'audio_id': audio.id,
                            'status': audio.status.value,
                            'progress': audio.progress
                        }, user_id)
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)


async def send_progress_update(user_id: int, audio_id: int, progress: int, status: str):
    """
    Send progress update to user
    Can be called from Celery tasks
    """
    await manager.send_personal_message({
        'type': 'progress_update',
        'audio_id': audio_id,
        'progress': progress,
        'status': status
    }, user_id)