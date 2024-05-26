import math
import pickle
from socket import socket

import pygame

import config
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
        return self.ai is not None or pygame.mouse.get_pressed()[0]

    def move(self, delta: float) -> None:
        if self.ai is None:
            keys = pygame.key.get_pressed()
        else:
            keys = self.ai.get_keys()
        if self.ai is None:
            mouse = pygame.mouse.get_pos()
        else:
            mouse = self.ai.get_mouse(delta)

        motion = pygame.Vector2(0, 0)

        if keys[self.controls["up"]]:
            motion.y -= 1
        if keys[self.controls["down"]]:
            motion.y += 1
        if keys[self.controls["left"]]:
            motion.x -= 1
        if keys[self.controls["right"]]:
            motion.x += 1

        if motion.length() > 0:
            motion = motion.normalize() * self.speed * delta

        if self.x + motion.x < 0:
            self.x = 0
        if self.x + motion.x > config.WIDTH:
            self.x = config.WIDTH
        if self.y + motion.y < 0:
            self.y = 0
        if self.y + motion.y > config.HEIGHT:
            self.y = config.HEIGHT

        self.x += motion.x
        self.y += motion.y

        mouse_x, mouse_y = mouse

        self.rotation = math.degrees(math.atan2(mouse_y - self.y, mouse_x - self.x))

        self.crosshair.move(mouse)

        if self.is_shooting() and self.cooldown <= 0:
            self.game.add_bullet(Bullet(self.x, self.y, self.rotation, self))
            self.cooldown = 1

        if self.cooldown >= 0.0:
            self.cooldown -= 1 * delta

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

        self.crosshair.draw(screen)

    def receive_update(self):
        try:
            data = self.connection.recv(1024)
            if data:
                state = pickle.loads(data)
                self.deserialize_state(state)
        except Exception as e:
            print(f"Failed to receive update: {e}")

    def serialize_state(self):
        """Serialize the player's state."""
        return {
            "position": (self.x, self.y),
            "rotation": self.rotation,
            "hp": self.hp,
            "score": self.score,
            "is_shooting": self.is_shooting(),
        }

    @classmethod
    def deserialize_state(cls, state):
        """Deserialize the player's state."""
        player = cls.__new__(cls)
        player.x, player.y = state["position"]
        player.rotation = state["rotation"]
        player.hp = state["hp"]
        player.score = state["score"]
        player.cooldown = 0  # Reset cooldown on deserialization
        return player
