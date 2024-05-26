import math
import threading
from socket import socket
from time import sleep

import pygame

import config
import Network
import Server
from Crosshair import Crosshair
from Player import Bullet, Player


def receive_data_from_player(connection, player, game):
    while True:
        try:
            Network.receive_state(connection, player)
            sleep(0.05)
        except BrokenPipeError:
            game.semaphore.acquire()
            del player.connection
            game.players.remove(player)
            game.semaphore.release()
        except Exception as e:
            print(f"Failed to receive update: {e}")


class PlayerOverNetwork(Player):
    def __init__(
        self,
        game,
        connection: socket,
        client_address,
        color=(255, 255, 255),
    ):
        self.uuid = 0
        self.speed = 300
        self.rect = pygame.Rect(200, 200, 32, 32)
        self.connection = connection
        self.client_address = client_address
        self.color = color
        self.rotation = 0
        self.cooldown = 0
        self.crosshair = Crosshair()
        self.game = game
        self.hp = 100
        self.max_hp = 100
        self.score = 0
        self.motion = pygame.Vector2(0, 0)
        self.mouse = (0, 0)
        self.ai = None
        self._is_shooting = False
        if self.connection and Server.is_server:
            self.connection.setblocking(False)
            self.connection.settimeout(0.05)
            self.receive_thread = threading.Thread(
                target=receive_data_from_player,
                args=(
                    self.connection,
                    self,
                    game,
                ),
            )
            self.receive_thread.daemon = True
            self.receive_thread.start()

    def is_shooting(self) -> bool:
        return self._is_shooting

    def move(self, delta: float) -> None:
        if self.motion.length() > 0:
            self.motion = self.motion.normalize() * self.speed * delta

        if self.x + self.motion.x < 0:
            self.x = 0
        if self.x + self.motion.x > config.WIDTH:
            self.x = config.WIDTH
        if self.y + self.motion.y < 0:
            self.y = 0
        if self.y + self.motion.y > config.HEIGHT:
            self.y = config.HEIGHT

        self.x += self.motion.x
        self.y += self.motion.y

        mouse_x = self.crosshair.pos.x
        mouse_y = self.crosshair.pos.y

        self.rotation = math.degrees(math.atan2(mouse_y - self.y, mouse_x - self.x))

        if self.is_shooting() and self.cooldown <= 0:
            self.game.add_bullet(Bullet(self.x, self.y, self.rotation, self))
            self.cooldown = 1

        if self.cooldown >= 0.0:
            self.cooldown -= 1 * delta
