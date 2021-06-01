import pickle
import select
import socket
import sys
from threading import Thread
from typing import Dict, Tuple

import pygame
from pygame.locals import *

import c
from models import *


class Game:
    location: list[int, int] = [c.WIDTH / 2, c.HEIGHT / 2]
    velocity: list[int, int] = [0, 0]
    current_player: Player = None
    other_players: Dict[str, Tuple[Player, Tuple[int, int]]] = {}
    connection: socket.socket
    font: pygame.font.Font

    def __init__(self):
        pygame.init()
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.screen = pygame.display.set_mode((c.WIDTH, c.HEIGHT))
        pygame.display.set_caption('Socket Game')
        self.clock = pygame.time.Clock()
        self.screen.fill('white')
        self.font = pygame.font.SysFont(None, c.FONT_SIZE)

    def start(self):
        self.connect_to_server()
        while True:
            self.game_loop()

    def connect_to_server(self):
        self.connection.connect((c.HOST, c.PORT))

    def listen_to_server(self):
        ins, outs, ex = select.select([self.connection], [], [], 0)
        for inm in ins:
            received_data = inm.recv(c.BUFFSIZE)
            event: Event = pickle.loads(received_data)
            print("<<<", event)
            if isinstance(event, CurrentPlayerEvent):
                pygame.display.set_caption(f'Socket Game - {event.player.nickname}')
                self.current_player = event.player
            elif isinstance(event, PlayerDidMoveEvent):
                self.update_player(event.player, event.location)
            elif isinstance(event, PlayerJoinedEvent):
                self.update_player(event.player)

    def update_player(self, player: Player, location=(c.WIDTH / 2, c.HEIGHT / 2)):
        self.other_players[player.nickname] = (player, location)

    def update_server(self):
        if self.current_player is not None:
            self.connection.send(pickle.dumps(PlayerDidMoveEvent(self.current_player, (
                self.location[0], self.location[1],
            ))))

    def game_loop(self):
        self.listen_to_server()
        self.event_handling()
        self.update_location()
        self.render()
        self.update_server()
        self.clock.tick(60)

    def update_location(self):
        oldx, oldy = self.location
        vx, vy = self.velocity
        newx, newy = oldx + vx, oldy + vy
        if newx > c.WIDTH - c.PLAYER_SIZE:
            newx = c.WIDTH - c.PLAYER_SIZE
        if newx < 0:
            newx = 0

        if newy > c.HEIGHT - c.PLAYER_SIZE:
            newy = c.HEIGHT - c.PLAYER_SIZE
        if newy < 0:
            newy = 0

        self.location = [newx, newy]

    def render_player(self, player: Player, location: Tuple[int, int]):
        x, y = location
        img = self.font.render(player.nickname, True, player.color)
        pygame.draw.rect(self.screen, player.color, (x, y, c.PLAYER_SIZE, c.PLAYER_SIZE))
        self.screen.blit(img, (x, y - img.get_height()))

    def render(self):
        self.screen.fill((255, 255, 255))
        if self.current_player is not None:
            self.render_player(self.current_player, (self.location[0], self.location[1]))
        for nickname, (player, location) in self.other_players.items():
            self.render_player(player, location)

        pygame.display.flip()

    def event_handling(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_LEFT: self.velocity[0] = -c.MOVEMENT_SPEED
                if event.key == K_RIGHT: self.velocity[0] = c.MOVEMENT_SPEED
                if event.key == K_UP: self.velocity[1] = -c.MOVEMENT_SPEED
                if event.key == K_DOWN:  self.velocity[1] = c.MOVEMENT_SPEED
            if event.type == KEYUP:
                if event.key == K_LEFT: self.velocity[0] = 0
                if event.key == K_RIGHT: self.velocity[0] = 0
                if event.key == K_UP: self.velocity[1] = 0
                if event.key == K_DOWN:  self.velocity[1] = 0


if __name__ == "__main__":
    s = Game()
    s.start()
