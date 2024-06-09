import pygame

import config
from AI import AI
from Game import game
from Player import Player


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    pygame.display.set_caption("Unnamed Topdown Gun Game")
    clock = pygame.time.Clock()
    game.running = True

    player1 = Player(game, 0)
    game.add_player(player1)
    game.client_player = player1

    player3 = Player(game, 1, ai=AI(), color=(0, 255, 0))
    game.add_player(player3)

    player4 = Player(game, 2, ai=AI(), color=(255, 0, 0))
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

    pygame.quit()


if __name__ == "__main__":
    main()
