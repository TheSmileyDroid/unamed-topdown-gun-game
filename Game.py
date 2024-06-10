from dataclasses import dataclass
from typing import Any

import pygame
from pygame.time import Clock

import config
from Player import Bullet, Player


@dataclass
class Game:
    clock = Clock()
    fast_forward = False
    players = []
    bullets = []
    delta = 0.0
    last_id = 1
    last_bullet = 1
    running = True
    client_player: Any | None = None

    def __post_init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Unnamed Topdown Gun Game")
        self.clock = pygame.time.Clock()
        self.running = True

    def add_player(self, player: Player) -> None:
        print(f"Player {len(self.players) + 1} joined")
        player.uuid = self.last_id
        self.last_id += 1
        self.players.append(player)

    def update(self) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_F5]:
            self.fast_forward = True
        if keys[pygame.K_F6]:
            self.fast_forward = False

        for player in self.players:
            player.move(self.delta)

            if player.is_shooting() and player.cooldown <= 0:
                self.add_bullet(Bullet(player.x, player.y, player.rotation, player))
                player.cooldown = 1

        for bullet in self.bullets:
            bullet.move(self.delta)

        for bullet in self.bullets:
            for player in self.players:
                if bullet.player == player:
                    continue
                if player.rect.colliderect(bullet.rect):
                    self.bullets.remove(bullet)
                    player.hp -= 10
                    player.score -= 10
                    bullet.player.score += 10
                    if player.hp <= 0:
                        bullet.player.score += 100
                        self.players.remove(player)
                    break
            if (
                bullet.rect.x < 0
                or bullet.rect.x > config.WIDTH
                or bullet.rect.y < 0
                or bullet.rect.y > config.HEIGHT
            ):
                self.bullets.remove(bullet)

    def draw(self) -> None:
        for player in self.players:
            player.draw(self.screen)

        for bullet in self.bullets:
            bullet.draw(self.screen)

        for i, player in enumerate(self.players):
            # HP bar player.hp / player.max_hp
            pygame.draw.rect(
                self.screen,
                (255, 0, 0),
                (
                    player.rect.x,
                    player.rect.y - 10,
                    player.hp / player.max_hp * player.rect.width,
                    5,
                ),
            )

            # Score
            font = pygame.font.Font(None, 24)
            text = font.render(
                f"{'AI' if player.ai else 'Player'} {i + 1} Score: {player.score}",
                True,
                player.color,
            )
            self.screen.blit(
                text, (config.WIDTH - max(text.get_width(), 270) - 10, 10 + i * 30)
            )

        # FPS
        font = pygame.font.Font(None, 24)
        text = font.render(
            f"FPS: {round(self.clock.get_fps())}",
            True,
            (255, 255, 255),
        )
        self.screen.blit(text, (10, 10))

    def add_bullet(self, bullet):
        bullet.uuid = self.last_bullet
        self.bullets.append(bullet)


game: Game = Game()
