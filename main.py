import asyncio
import sys
import threading

import pygame

import config
import Network
import Server
from AI import AI
from Game import game
from Player import Player
from PlayerOverNetwork import PlayerOverNetwork

if Server.is_server:
    from Server import start_server

    start_server(Server.address, Server.port)


def receive_new_players():
    while game.running:
        print("Waiting for a connection...")
        connection, client_address = Server.sock.accept()
        print("connection from", client_address)

        game.semaphore.acquire()
        print(f"New Player {client_address}")
        player = PlayerOverNetwork(
            game,
            connection,
            client_address,
            color=(255, 0, 0),
        )
        game.add_player(player)

        print("Sending initial info")
        Network.send_initial_info(connection, player.uuid)

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

    if Server.is_server:
        new_players = threading.Thread(target=receive_new_players)
        new_players.daemon = True

        new_players.start()

        player3 = Player(game, ai=AI(3), color=(0, 255, 0))
        game.add_player(player3)

        player4 = Player(game, ai=AI(2), color=(255, 0, 0))
        game.add_player(player4)

    if len(sys.argv) > 1 and sys.argv[1] == "client":
        print("Connecting...")
        try:
            Server.sock.connect((Server.address, Server.port))
        except ConnectionRefusedError:
            print("Connection refused")
            sys.exit(1)
        print("Connected")

        print("Waiting for initial info")
        state = Network.receive_initial_info(Server.sock)
        if state:
            player1.uuid = state["uuid"]
            print("Conectado como player", player1.uuid)

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

    pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        print("Usage: python main.py [server|client] [address] [port]")
        sys.exit(0)

    asyncio.run(main())
