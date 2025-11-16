# backend/utils/ws_manager.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    """Gerencia as conexões ativas de WebSocket, mapeando o user_id para as conexões."""
    
    def __init__(self):
        # Mapeamento de user_id (int) para o conjunto de conexões ativas (WebSocket)
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Aceita uma nova conexão e a registra no dicionário."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"📣 [WS] Usuário {user_id} conectado. Total de conexões: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a conexão do gerenciador."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"📣 [WS] Usuário {user_id} desconectado.")

    async def send_personal_message(self, message: Dict, user_id: int) -> bool:
        """Envia uma mensagem JSON para todas as conexões ativas de um usuário."""
        if user_id in self.active_connections:
            data = json.dumps(message)
            tasks = [conn.send_text(data) for conn in self.active_connections[user_id]]
            await asyncio.gather(*tasks)
            print(f"📣 [WS] Notificação enviada para o usuário {user_id}: {message.get('type')}")
            return True
        return False

    def get_active_connections_count(self) -> int:
        """
        Retorna o número total de conexões WebSocket ativas (não usuários únicos).
        """
        return sum(len(connections) for connections in self.active_connections.values())

manager = ConnectionManager()