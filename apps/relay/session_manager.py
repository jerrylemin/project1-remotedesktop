from __future__ import annotations

from apps.relay.registry import registry


def has_control(machine_id: str) -> bool:
    return machine_id in registry.controllers

