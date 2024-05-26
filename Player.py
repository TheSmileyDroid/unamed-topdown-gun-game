import math

import pygame

import config
from Crosshair import Crosshair


class Bullet:
    def __init__(self, x, y, rotation, player):
        self.speed = 500
        self.rect = pygame.Rect(x, y, 5, 5)
        self.rotation = rotation
        self.player = player

    def move(self, delta):
        motion = pygame.Vector2(
            math.cos(math.radians(self.rotation)),
            math.sin(math.radians(self.rotation)),
        )

        motion = motion.normalize() * self.speed * delta

        self.rect.x += motion.x
        self.rect.y += motion.y

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), self.rect.center, 2)


class Player:
    def __init__(
        self,
        game,
        ai=None,
        controls={
            "up": pygame.K_w,
            "down": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "shoot": pygame.K_SPACE,
        },
        color=(255, 255, 255),
    ):
        self.speed = 300
        self.rect = pygame.Rect(200, 200, 32, 32)
        self.ai = ai
        self.controls = ai.get_controller() if ai else controls
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
