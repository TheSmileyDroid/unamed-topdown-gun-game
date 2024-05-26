import math
from socket import socket

import pygame

import config
import Network
import Server
from Crosshair import Crosshair
from Player import Bullet, Player


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

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, value):
        self.rect.y = value

    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, value):
        self.rect.x = value

    def is_shooting(self) -> bool:
        return self._is_shooting

    def move(self, delta: float) -> None:
        if Server.is_server:
            Network.receive_state(self.connection, self)

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

        mouse_x, mouse_y = self.mouse

        self.rotation = math.degrees(math.atan2(mouse_y - self.y, mouse_x - self.x))

        self.crosshair.move(self.mouse)

        if self.is_shooting() and self.cooldown <= 0:
            self.game.add_bullet(Bullet(self.x, self.y, self.rotation, self))
            self.cooldown = 1

        if self.cooldown >= 0.0:
            self.cooldown -= 1 * delta

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

        self.crosshair.draw(screen)
