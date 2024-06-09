import random
from collections import deque
from typing import Tuple

import numpy as np
import torch
from torch import Tensor

import config
from Game import Game
from Player import Player
from model import LinearNet, QTrainer

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LEARNING_RATE = 0.01

MAX_PLAYERS = 8
STATES_PER_PLAYER = 8
MAX_BULLETS = 8
STATES_PER_BULLET = 2


class AI:
    def __init__(self):
        self.mouse = (0, 0)
        self.keys = [random.choice([False, True]) for _ in range(5)]
        self.number_of_games = 0
        self.epsilon = 0  # aleatorização
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = LinearNet(MAX_PLAYERS*STATES_PER_PLAYER, 255, 8)
        self.trainer = QTrainer(self.model, lr=LEARNING_RATE, gamma=self.gamma)

    def get_enemies(self, game):
        ai_player: Player = self.get_player(game)
        enemies: list[Player] = []
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

    def get_state(self, game) -> np.ndarray:
        ai_player = self.get_player(game)
        enemies = self.get_enemies(game)
        allies = self.get_allies(game)
        bullets = game.bullets

        state = np.zeros(MAX_PLAYERS*STATES_PER_PLAYER)

        state[0] = ai_player.y
        state[1] = ai_player.x
        state[2] = ai_player.rotation
        state[3] = ai_player.hp
        state[4] = ai_player.max_hp
        state[5] = ai_player.score
        state[6] = ai_player.uuid
        state[7] = ai_player.cooldown
        i = 8
        for enemy in enemies:
            state[i] = enemy.y
            state[i + 1] = enemy.x
            state[i + 2] = enemy.rotation
            state[i + 3] = enemy.hp
            state[i + 4] = enemy.max_hp
            state[i + 5] = enemy.score
            state[i + 6] = enemy.uuid
            state[i + 7] = enemy.cooldown
            i += 8
        i = 8
        for ally in allies:
            state[i] = ally.y
            state[i + 1] = ally.x
            state[i + 2] = ally.rotation
            state[i + 3] = ally.hp
            state[i + 4] = ally.max_hp
            state[i + 5] = ally.score
            state[i + 6] = ally.uuid
            state[i + 7] = ally.cooldown
            i += 8

        return state

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

    def get_action(self, state: np.ndarray) -> list[float]:
        self.epsilon = 80 - self.number_of_games
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
            prediction: Tensor = self.model(state0.to(torch.float32))
            final_move = prediction.detach().cpu().numpy()

        return final_move

    def get_player(self, game):
        for player in game.players:
            if self == player.ai:
                return player

    @staticmethod
    def get_controller():
        return {
            "up": 0,
            "down": 1,
            "left": 2,
            "right": 3,
            "shoot": 4,
        }

    def update(self, game):
        output = self.get_action(self.get_state(game))
        self.keys = output[:5]
        self.mouse = output[5:7]

    def get_keys(self):
        return self.keys

    def is_shooting(self):
        return self.keys[4]

    def get_mouse(self, delta) -> tuple:
        if self.mouse[0] < 0:
            self.mouse = (0, self.mouse[1])
        if self.mouse[0] > config.WIDTH:
            self.mouse = (config.WIDTH, self.mouse[1])
        if self.mouse[1] < 0:
            self.mouse = (self.mouse[0], 0)
        if self.mouse[1] > config.HEIGHT:
            self.mouse = (self.mouse[0], config.HEIGHT)

        return tuple(self.mouse)


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
