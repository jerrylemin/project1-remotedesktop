from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket


@dataclass
class AdminConnection:
    websocket: WebSocket
    user_id: str
    controlled: set[str] = field(default_factory=set)
    observed: set[str] = field(default_factory=set)


class RelayRegistry:
    def __init__(self) -> None:
        self.agents: dict[str, WebSocket] = {}
        self.admins: dict[WebSocket, AdminConnection] = {}
        self.subscribers: dict[str, set[WebSocket]] = {}
        self.controllers: dict[str, WebSocket] = {}

    async def register_agent(self, machine_id: str, websocket: WebSocket) -> None:
        self.agents[machine_id] = websocket

    def unregister_agent(self, websocket: WebSocket) -> list[str]:
        removed = [machine_id for machine_id, ws in self.agents.items() if ws is websocket]
        for machine_id in removed:
            self.agents.pop(machine_id, None)
            self.controllers.pop(machine_id, None)
        return removed

    async def register_admin(self, websocket: WebSocket, user_id: str) -> None:
        self.admins[websocket] = AdminConnection(websocket=websocket, user_id=user_id)

    def unregister_admin(self, websocket: WebSocket) -> None:
        conn = self.admins.pop(websocket, None)
        for subscribers in self.subscribers.values():
            subscribers.discard(websocket)
        for machine_id, controller in list(self.controllers.items()):
            if controller is websocket:
                self.controllers.pop(machine_id, None)
        if conn:
            conn.controlled.clear()
            conn.observed.clear()

    def subscribe(self, websocket: WebSocket, machine_id: str, want_control: bool) -> tuple[bool, str]:
        if websocket not in self.admins:
            return False, "admin not registered"
        self.subscribers.setdefault(machine_id, set()).add(websocket)
        self.admins[websocket].observed.add(machine_id)
        if not want_control:
            return True, "observer"
        existing = self.controllers.get(machine_id)
        if existing is not None and existing is not websocket:
            return False, "machine already controlled"
        self.controllers[machine_id] = websocket
        self.admins[websocket].controlled.add(machine_id)
        return True, "controller"

    def is_controller(self, websocket: WebSocket, machine_id: str) -> bool:
        return self.controllers.get(machine_id) is websocket

    def agent_for(self, machine_id: str) -> WebSocket | None:
        return self.agents.get(machine_id)

    def subscribers_for(self, machine_id: str) -> set[WebSocket]:
        return set(self.subscribers.get(machine_id, set()))

    async def send_json_safe(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        try:
            await websocket.send_json(message)
        except RuntimeError:
            self.unregister_admin(websocket)


registry = RelayRegistry()

