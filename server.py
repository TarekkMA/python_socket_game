import pickle
import socket
import queue
from random import randint
from threading import Thread
from typing import Dict, Tuple

import c
from models import *


def random_color() -> (int, int, int):
    return randint(0, 255), randint(0, 255), randint(0, 255)


class Server:
    event_queue: queue.Queue[Event] = queue.Queue(100)
    player_counter: int = 0
    connection: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    players_sockets: Dict[str, Tuple[socket.socket, Player]] = {}

    def __init__(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def serve(self, host: str, port: int):
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection.bind((host, port))
        self.connection.listen(100)
        Thread(target=self.accept_connections).start()
        self.event_loop()

    def accept_connections(self):
        while True:
            player_socket, address = self.connection.accept()
            self.player_counter += 1
            nickname = f"Player {self.player_counter}"
            print(f"[{nickname} is now connected]")
            player = Player(nickname, random_color())
            self.players_sockets[nickname] = (player_socket, player)
            player_socket.send(pickle.dumps(CurrentPlayerEvent(player)))
            self.event_queue.put(PlayerJoinedEvent(player))
            Thread(target=self.player_handler, args=(player_socket, nickname,)).start()

    def player_handler(self, player_conn: socket.socket, nickname: str):
        while True:
            try:
                received_data = player_conn.recv(c.BUFFSIZE)
                event: Event = pickle.loads(received_data)
                self.event_queue.put(PlayerSentDataEvent(nickname, event))
            except:
                pass

    def broadcast(self, event: Event, exception: list[Player] = None):
        if exception is None:
            exception = []
        else:
            exception = [self.players_sockets[p.nickname][0] for p in exception]
        for nickname, (conn, player) in self.players_sockets.items():
            if conn not in exception:
                try:
                    conn.send(pickle.dumps(event))
                except:
                    pass

    def event_loop(self):
        while True:
            event = self.event_queue.get()
            print(">>>", event)
            if isinstance(event, PlayerSentDataEvent):
                sent_event = event.event
                player = self.players_sockets[event.nickname][1]
                if isinstance(sent_event, PlayerDidMoveEvent):
                    self.broadcast(sent_event, [player])
            if isinstance(event, PlayerJoinedEvent):
                self.broadcast(event, exception=[event.player])


if __name__ == "__main__":
    s = Server()
    s.serve(c.HOST, c.PORT)
