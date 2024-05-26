import threading
import time
from threading import Semaphore
from typing import Any

import pygame

import config
import Network
import Server
from Player import Bullet, Player
from PlayerOverNetwork import PlayerOverNetwork


def receive(game):
    while True:
        time.sleep(0.05)
        state = Network.receive_broadcast(Server.sock)
        game.semaphore.acquire()
        if state:
            for player in game.players:
                if player.uuid in state["players"]:
                    if player.uuid != game.client_player.uuid:
                        Network.deserialize_state(state["players"][player.uuid], player)
                    del state["players"][player.uuid]
                else:
                    game.players.remove(player)
                    print("Player Left", player.uuid)

            for uuid in state["players"]:
                player = PlayerOverNetwork(game, Server.sock, Server.address)
                player.uuid = uuid
                print("New Player", player.uuid)
                Network.deserialize_state(state["players"][uuid], player)
                game.players.append(player)

            for bullet in game.bullets:
                if bullet.uuid in state["bullets"]:
                    Network.deserialize_state_bullet(
                        state["bullets"][bullet.uuid], bullet
                    )
                    del state["bullets"][bullet.uuid]
                else:
                    game.bullets.remove(bullet)

            for uuid in state["bullets"]:
                bullet = Bullet(0, 0, 0, None)
                bullet.uuid = uuid
                Network.deserialize_state_bullet(state["bullets"][uuid], bullet)
                game.bullets.append(bullet)

        game.semaphore.release()


def send(game):
    while True:
        time.sleep(0.05)
        Network.broadcast_state(game.players, game.bullets, Server.sock)


class Game:
    def __init__(self) -> None:
        self.players = []
        self.bullets = []
        self.delta = 0.0
        self.last_id = 1
        self.last_bullet = 1
        self.semaphore = Semaphore(1)
        self.running = True
        self.client_player: Any | None = None

        if Server.is_server:
            self.send_thread = threading.Thread(target=send, args=(self,))
            self.send_thread.daemon = True
            self.send_thread.start()

        if Server.is_client:
            self.receive_thread = threading.Thread(target=receive, args=(self,))
            self.receive_thread.daemon = True
            self.receive_thread.start()

    def add_player(self, player: Player) -> None:
        print(f"Player {len(self.players) + 1} joined")
        player.uuid = self.last_id
        self.last_id += 1
        self.players.append(player)

    def update(self) -> None:
        self.semaphore.acquire()

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
        bullet.uuid = self.last_bullet
        self.bullets.append(bullet)


game = Game()
