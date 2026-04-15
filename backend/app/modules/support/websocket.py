"""WebSocket handler for real-time support ticket updates.

Provides real-time notifications for:
- New ticket messages
- Ticket status changes
- New ticket assignments (for admins)
"""

import json
import uuid
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class SupportWebSocketMessage(BaseModel):
    """WebSocket message structure for support events."""
    type: str  # 'new_message', 'status_change', 'new_ticket', 'ticket_assigned'
    ticket_id: str
    payload: dict
    timestamp: str


class ConnectionManager:
    """Manages WebSocket connections for support system."""
    
    def __init__(self):
        # User connections: user_id -> set of WebSocket connections
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Admin connections: admin_id -> set of WebSocket connections
        self.admin_connections: Dict[str, Set[WebSocket]] = {}
        # Ticket subscriptions: ticket_id -> set of (user_id, is_admin)
        self.ticket_subscriptions: Dict[str, Set[tuple]] = {}
    
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """Connect a user to the support WebSocket."""
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        print(f"[SupportWS] User {user_id} connected. Total user connections: {len(self.user_connections)}")
    
    async def connect_admin(self, websocket: WebSocket, admin_id: str):
        """Connect an admin to the support WebSocket."""
        await websocket.accept()
        if admin_id not in self.admin_connections:
            self.admin_connections[admin_id] = set()
        self.admin_connections[admin_id].add(websocket)
        print(f"[SupportWS] Admin {admin_id} connected. Total admin connections: {len(self.admin_connections)}")
    
    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Disconnect a user from the support WebSocket."""
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    def disconnect_admin(self, websocket: WebSocket, admin_id: str):
        """Disconnect an admin from the support WebSocket."""
        if admin_id in self.admin_connections:
            self.admin_connections[admin_id].discard(websocket)
            if not self.admin_connections[admin_id]:
                del self.admin_connections[admin_id]
    
    def subscribe_to_ticket(self, ticket_id: str, user_id: str, is_admin: bool = False):
        """Subscribe a user/admin to ticket updates."""
        if ticket_id not in self.ticket_subscriptions:
            self.ticket_subscriptions[ticket_id] = set()
        self.ticket_subscriptions[ticket_id].add((user_id, is_admin))
        print(f"[SupportWS] {'Admin' if is_admin else 'User'} {user_id} subscribed to ticket {ticket_id}")
    
    def unsubscribe_from_ticket(self, ticket_id: str, user_id: str, is_admin: bool = False):
        """Unsubscribe from ticket updates."""
        if ticket_id in self.ticket_subscriptions:
            self.ticket_subscriptions[ticket_id].discard((user_id, is_admin))
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to a specific user."""
        print(f"[SupportWS] Attempting to send to user {user_id}")
        if user_id in self.user_connections:
            print(f"[SupportWS] Found {len(self.user_connections[user_id])} connection(s) for user {user_id}")
            disconnected = set()
            for ws in self.user_connections[user_id]:
                try:
                    await ws.send_json(message)
                    print(f"[SupportWS] Message sent to user {user_id}")
                except Exception as e:
                    print(f"[SupportWS] Failed to send to user {user_id}: {e}")
                    disconnected.add(ws)
            # Clean up disconnected sockets
            for ws in disconnected:
                self.user_connections[user_id].discard(ws)
        else:
            print(f"[SupportWS] No connections found for user {user_id}")
    
    async def send_to_admin(self, admin_id: str, message: dict):
        """Send a message to a specific admin."""
        print(f"[SupportWS] Attempting to send to admin {admin_id}")
        if admin_id in self.admin_connections:
            print(f"[SupportWS] Found {len(self.admin_connections[admin_id])} connection(s) for admin {admin_id}")
            disconnected = set()
            for ws in self.admin_connections[admin_id]:
                try:
                    await ws.send_json(message)
                    print(f"[SupportWS] Message sent to admin {admin_id}")
                except Exception as e:
                    print(f"[SupportWS] Failed to send to admin {admin_id}: {e}")
                    disconnected.add(ws)
            # Clean up disconnected sockets
            for ws in disconnected:
                self.admin_connections[admin_id].discard(ws)
        else:
            print(f"[SupportWS] No connections found for admin {admin_id}")
    
    async def broadcast_to_all_admins(self, message: dict):
        """Broadcast a message to all connected admins."""
        for admin_id in list(self.admin_connections.keys()):
            await self.send_to_admin(admin_id, message)
    
    async def notify_ticket_update(
        self,
        ticket_id: str,
        event_type: str,
        payload: dict,
        exclude_sender: Optional[str] = None,
    ):
        """Notify all subscribers of a ticket update."""
        message = {
            "type": event_type,
            "ticket_id": ticket_id,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if ticket_id in self.ticket_subscriptions:
            for user_id, is_admin in self.ticket_subscriptions[ticket_id]:
                if user_id == exclude_sender:
                    continue
                if is_admin:
                    await self.send_to_admin(user_id, message)
                else:
                    await self.send_to_user(user_id, message)


# Global connection manager instance
support_ws_manager = ConnectionManager()


# Helper functions for broadcasting events
async def broadcast_new_message(
    ticket_id: str,
    user_id: str,
    message_data: dict,
    sender_id: str,
):
    """Broadcast a new message to ticket subscribers."""
    print(f"[SupportWS] Broadcasting new message for ticket {ticket_id}")
    print(f"[SupportWS] Sender: {sender_id}, Ticket owner: {user_id}")
    print(f"[SupportWS] Current subscriptions: {support_ws_manager.ticket_subscriptions}")
    print(f"[SupportWS] User connections: {list(support_ws_manager.user_connections.keys())}")
    print(f"[SupportWS] Admin connections: {list(support_ws_manager.admin_connections.keys())}")
    
    message = {
        "type": "new_message",
        "ticket_id": ticket_id,
        "payload": message_data,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Send to all subscribers of this ticket (except sender)
    if ticket_id in support_ws_manager.ticket_subscriptions:
        for sub_user_id, is_admin in support_ws_manager.ticket_subscriptions[ticket_id]:
            if sub_user_id == sender_id:
                print(f"[SupportWS] Skipping sender {sender_id}")
                continue
            
            print(f"[SupportWS] Sending to {'admin' if is_admin else 'user'} {sub_user_id}")
            if is_admin:
                await support_ws_manager.send_to_admin(sub_user_id, message)
            else:
                await support_ws_manager.send_to_user(sub_user_id, message)
    else:
        print(f"[SupportWS] No subscriptions found for ticket {ticket_id}")
    
    # Also send to ticket owner if they're not the sender and not already subscribed
    if user_id != sender_id:
        # Check if user is already subscribed
        is_subscribed = ticket_id in support_ws_manager.ticket_subscriptions and \
                       (user_id, False) in support_ws_manager.ticket_subscriptions[ticket_id]
        
        if not is_subscribed:
            print(f"[SupportWS] Sending to ticket owner {user_id} (not subscribed)")
            await support_ws_manager.send_to_user(user_id, message)
        else:
            print(f"[SupportWS] Ticket owner {user_id} already subscribed, skipping duplicate")
    
    print(f"[SupportWS] Message broadcast complete")


async def broadcast_status_change(
    ticket_id: str,
    user_id: str,
    old_status: str,
    new_status: str,
):
    """Broadcast a status change to ticket subscribers."""
    print(f"[SupportWS] Broadcasting status change for ticket {ticket_id}: {old_status} → {new_status}")
    print(f"[SupportWS] Ticket owner: {user_id}")
    print(f"[SupportWS] Current subscriptions: {support_ws_manager.ticket_subscriptions}")
    
    message = {
        "type": "status_change",
        "ticket_id": ticket_id,
        "payload": {
            "old_status": old_status,
            "new_status": new_status,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Send to all subscribers of this ticket
    if ticket_id in support_ws_manager.ticket_subscriptions:
        for sub_user_id, is_admin in support_ws_manager.ticket_subscriptions[ticket_id]:
            print(f"[SupportWS] Sending status change to {'admin' if is_admin else 'user'} {sub_user_id}")
            if is_admin:
                await support_ws_manager.send_to_admin(sub_user_id, message)
            else:
                await support_ws_manager.send_to_user(sub_user_id, message)
    else:
        print(f"[SupportWS] No subscriptions found for ticket {ticket_id}")
    
    # Also send to ticket owner if not already subscribed
    is_subscribed = ticket_id in support_ws_manager.ticket_subscriptions and \
                   (user_id, False) in support_ws_manager.ticket_subscriptions[ticket_id]
    
    if not is_subscribed:
        print(f"[SupportWS] Sending to ticket owner {user_id} (not subscribed)")
        await support_ws_manager.send_to_user(user_id, message)
    
    print(f"[SupportWS] Status change broadcast complete")


async def broadcast_new_ticket_to_admins(ticket_data: dict):
    """Broadcast new ticket notification to all admins."""
    await support_ws_manager.broadcast_to_all_admins({
        "type": "new_ticket",
        "ticket_id": ticket_data.get("id"),
        "payload": ticket_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


def get_debug_state():
    """Get current WebSocket state for debugging."""
    return {
        "user_connections": list(support_ws_manager.user_connections.keys()),
        "admin_connections": list(support_ws_manager.admin_connections.keys()),
        "ticket_subscriptions": {
            k: [(uid, is_admin) for uid, is_admin in v] 
            for k, v in support_ws_manager.ticket_subscriptions.items()
        },
    }
