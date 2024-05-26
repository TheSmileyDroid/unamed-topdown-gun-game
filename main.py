import asyncio
import socket
from threading import Semaphore

import pygame

import config
from AI import AI
from Network import PlayerOverNetwork
from Player import Player

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind(("localhost", 8080))

sock.listen(1)


class Game:
    def __init__(self) -> None:
        self.players = []
        self.bullets = []
        self.delta = 0.0
        self.semaphore = Semaphore(1)
        self.running = True

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


async def receive_new_players():
    while game.running:
        connection, client_address = sock.accept()

        game.semaphore.acquire()
        player2 = PlayerOverNetwork(
            game,
            connection,
            client_address,
            color=(255, 0, 0),
        )
        game.players.append(player2)
        game.semaphore.release()


async def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Unamed Topdown Gun Game")
    clock = pygame.time.Clock()
    game.running = True

    player1 = Player(game)
    game.players.append(player1)

    new_players = asyncio.create_task(receive_new_players())

    player3 = Player(game, ai=AI(3), color=(0, 255, 0))
    game.players.append(player3)

    delta = 0.0

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
        screen.fill((0, 0, 0))

        game.delta = delta

        game.update()

        game.draw(screen)

        pygame.display.flip()
        delta = clock.tick(60) / 1000

    await new_players
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
