# backend/api/notifications.py

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from typing import Optional

from ..utils.ws_manager import manager
from ..utils.security import get_user_id_from_websocket_token

router = APIRouter()

# Rota WebSocket para Notificações. 
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    # O user_id é injetado AQUI pela função de segurança.
    # Se o token for inválido, o FastAPI já trata a exceção e fecha a conexão com 401.
    user_id: int = Depends(get_user_id_from_websocket_token) 
):
    """
    Endpoint WebSocket para conectar clientes e enviar notificações.
    A autenticação é feita via Depends(get_user_id_from_websocket_token).
    """
    
    # Inicia a Conexão (Se chegou aqui, user_id é válido)
    try:
        await manager.connect(websocket, user_id)
        print(f"✅ [WS] Conexão estabelecida para user_id: {user_id}")
        
        # Loop de escuta: Mantém a conexão aberta. 
        # É necessário escutar para detectar desconexões (código 1000).
        while True:
            # Não faz nada com o texto, apenas espera o cliente fechar a conexão
            await websocket.receive_text() 
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"🛑 [WS] Conexão encerrada para user_id: {user_id}")
    except Exception as e:
        print(f"❌ [WS ERROR] Erro inesperado na conexão do user_id {user_id}: {e}")
        # Garante que a conexão será fechada em caso de erro interno
        await websocket.close()