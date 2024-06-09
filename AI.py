import random
import torch
import numpy as np
from collections import deque
import config
from Game import Game
from Player import Player, Bullet
from model import LinearNet, QTrainer

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LEARNING_RATE = 0.01


class AI:
    def __init__(self):
        self.number_of_games = 0
        self.epsilon = 0 # aleatorização
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = LinearNet(7, 255, 8) # Colocar o primeiro
        # valor com o número de estados que o modelo vai receber
        self.trainer = QTrainer(self.model, lr=LEARNING_RATE, gamma=self.gamma)

    def get_enemies(self, game):
        ai_player = self.get_player(game)
        enemies = []
        for player in game.players:
            if player.team != ai_player.team:
                enemies.append(player)
        return enemies

    def get_allies(self, game):
        ai_player = self.get_player(game)
        allies = []
        for player in game.players:
            if player.team == ai_player.team:
                allies.append(player)
        return allies

    def get_state(self, game):
        ai_player = self.get_player(game)
        enemies = self.get_enemies(game)
        allies = self.get_allies(game)
        bullets = game.bullets()

        # TODO: Formatar em um np.array a posição,
        #  cooldown, time e vida dos players e a posição,
        #  direção e time das balas
        # return np.array(state)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            minibatch = random.sample(self.memory, BATCH_SIZE)
        else:
            minibatch = self.memory


        states, actions, rewards, next_states, dones = zip(*minibatch)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        self.epsilon = 80 - self.number_of_games
        final_move = [0, 0, 0, 0, 0, 0, 0, 0]
        if random.randint(0, 200) < self.epsilon:
            move_up = random.choice([0, 1])
            move_left = random.choice([0, 1])
            move_right = random.choice([0, 1])
            move_down = random.choice([0, 1])
            shooting = random.choice([0, 1])
            mouse_x = random.randint(0, config.WIDTH)
            mouse_y = random.randint(0, config.HEIGHT)
            final_move = [move_up, move_left, move_right, move_down, shooting, mouse_x, mouse_y]
        else:
            state0 = torch.tensor(state)
            prediction = self.model(state0)
            # TODO: final_move = torch.argmax(prediction).?? Retornar um array de 8 inteiros, sendo os primeiros 5 booleanos (0, 1)

        return final_move

    def get_player(self, game):
        for player in game.players:
            if self == player.ai:
                return player

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = AI()
    game = Game()
    while True:
        state_old = agent.get_state(game)

        final_move = agent.get_action(state_old)

        reward, done, score = agent.get_player(game).score, not game.running, agent.get_player(game).score

        state_new = agent.get_state(game)

        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # TODO: Implementar game.reset()
            agent.number_of_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                # TODO: agent.model.save()
            print('GAME', agent.number_of_games, 'Score', score, 'Record', record)

            # TODO: plot


if __name__ == '__main__':
    train()


    def get_controller(self):
        return {
            "up": 0,
            "down": 1,
            "left": 2,
            "right": 3,
            "shoot": 4,
        }

    def is_shooting(self):
        return random.choice([True, False])
    def get_keys(self):
        return [random.choice([False, True]) for _ in range(5)]

    def get_mouse(self, delta):
        self.mouse = (
            self.mouse[0] + random.randint(-300, 300) * delta,
            self.mouse[1] + random.randint(-300, 300) * delta,
        )

        if self.mouse[0] < 0:
            self.mouse = (0, self.mouse[1])
        if self.mouse[0] > config.WIDTH:
            self.mouse = (config.WIDTH, self.mouse[1])
        if self.mouse[1] < 0:
            self.mouse = (self.mouse[0], 0)
        if self.mouse[1] > config.HEIGHT:
            self.mouse = (self.mouse[0], config.HEIGHT)

        return self.mouse
