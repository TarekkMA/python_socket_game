from abc import ABC
from dataclasses import dataclass


@dataclass
class Player:
    nickname: str
    color: (int, int, int)
    health: float = 100
    max_health: float = 100


class Event(ABC):
    pass


@dataclass
class CurrentPlayerEvent(Event):
    player: Player


@dataclass
class PlayerJoinedEvent(Event):
    player: Player


@dataclass
class PlayerSentDataEvent(Event):
    nickname: str
    event: Event


@dataclass
class PlayerDidMoveEvent(Event):
    player: Player
    location: (int, int)
