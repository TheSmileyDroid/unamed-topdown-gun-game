import pygame

from AI import AI
from Game import game
from Player import Player


def main(is_train=False):
    player1 = Player(game, 0, ai=AI(is_train), color=(0, 255, 0))
    game.add_player(player1)

    player2 = Player(game, 1, ai=AI(is_train), color=(255, 0, 0))
    game.add_player(player2)

    delta = 0.0

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
        game.screen.fill((0, 0, 0))

        game.delta = delta

        game.update()

        game.draw()

        pygame.display.flip()
        if game.fast_forward:
            game.clock.tick()
            delta = 0.016
        else:
            delta = game.clock.tick(60) / 1000.0

    pygame.quit()


if __name__ == "__main__":
    main()
