from threading import Semaphore

import pygame

import config
from Player import Player


class Game:
    def __init__(self) -> None:
        self.players = []
        self.bullets = []
        self.delta = 0.0
        self.last_id = 0
        self.semaphore = Semaphore(1)
        self.running = True

    def add_player(self, player: Player) -> None:
        print(f"Player {len(self.players) + 1} joined")
        player.uuid = self.last_id
        self.last_id += 1
        self.players.append(player)

    def update(self) -> None:
        self.semaphore.acquire()
        for player in self.players:
            player.move(self.delta)

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

        self.semaphore.release()

    def draw(self, screen: pygame.Surface) -> None:
        for player in self.players:
            player.draw(screen)

        for bullet in self.bullets:
            bullet.draw(screen)

        for i, player in enumerate(self.players):
            # HP bar player.hp / player.max_hp
            pygame.draw.rect(
                screen,
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
            screen.blit(
                text, (config.WIDTH - max(text.get_width(), 270) - 10, 10 + i * 30)
            )

    def add_bullet(self, bullet):
        self.bullets.append(bullet)


game = Game()
