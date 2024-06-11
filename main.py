import pygame

from AI import AI
from Game import game
from Player import Player


def main(is_train=False):
    player1 = Player(
        game, 0, ai=AI(is_train, model_path="models/model1.pth"), color=(0, 255, 0)
    )
    game.add_player(player1)

    player2 = Player(
        game, 1, ai=AI(is_train, model_path="models/model2.pth"), color=(255, 0, 0)
    )
    game.add_player(player2)

    player1.ai.model.load("models/model1.pth")
    player2.ai.model.load("models/model2.pth")

    if is_train:
        player1.ai.model.net.train()
        player2.ai.model.net.train()

    player1.hp = 100
    player2.hp = 100
    player1.x = 100
    player2.x = 300
    player1.y = 100
    player2.y = 300

    delta = 0.0

    time = 0

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if is_train:
                    player1.ai.model.save("models/model1.pth")
                    player2.ai.model.save("models/model2.pth")
                game.running = False
        game.screen.fill((0, 0, 0))

        game.delta = delta

        game.update()

        game.draw()

        if is_train:
            if player1.hp <= 0 or player2.hp <= 0:
                player1.hp = 100
                player2.hp = 100
                player1.x = 100
                player2.x = 100
                player1.y = 300
                player2.y = 300

        if is_train and time > 1000:
            player1.ai.model.save("models/model1.pth")
            player2.ai.model.save("models/model2.pth")
            time = 0

        pygame.display.flip()
        if not (game.fast_forward or not is_train):
            time += game.clock.tick()
            delta = 0.016
        else:
            delta = game.clock.tick(60) / 1000.0
            time += delta

    pygame.quit()


if __name__ == "__main__":
    main()
