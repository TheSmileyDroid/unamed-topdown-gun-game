import asyncio
import sys

import pygame

import config
from AI import AI
from Game import game
from Network import PlayerOverNetwork
from Player import Player
from Server import sock

if len(sys.argv) > 1 and sys.argv[1] == "server":
    from Server import start_server

    start_server()


async def receive_new_players():
    while game.running:
        connection, client_address = sock.accept()

        game.semaphore.acquire()
        print(f"Connection from {client_address}")
        player = PlayerOverNetwork(
            game,
            connection,
            client_address,
            color=(255, 0, 0),
        )
        game.add_player(player)
        game.semaphore.release()


async def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Unamed Topdown Gun Game")
    clock = pygame.time.Clock()
    game.running = True

    player1 = Player(game)
    game.add_player(player1)

    new_players = None

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        new_players = asyncio.create_task(receive_new_players())

    player3 = Player(game, ai=AI(3), color=(0, 255, 0))
    game.add_player(player3)

    player4 = Player(game, ai=AI(2), color=(255, 0, 0))
    game.add_player(player4)

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

    if len(sys.argv) > 1 and sys.argv[1] == "server" and new_players is not None:
        await new_players
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
