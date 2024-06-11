import random
from collections import deque

import numpy as np
import torch
from numpy import ndarray

import config
import ppo
from Game import Game
from Player import Player
from model import QTrainer

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LEARNING_RATE = 0.01

MAX_PLAYERS = 8
STATES_PER_PLAYER = 8
MAX_BULLETS = 8
STATES_PER_BULLET = 2


class AI:
    def __init__(self, is_train=False, model_path=None):
        self.player = None
        self.old_reward = None
        self.old_action = None
        self.mouse = (0, 0)
        self.keys = [random.choice([False, True]) for _ in range(5)]
        self.number_of_games = 0
        self.epsilon = 0  # aleatorização
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)
        self.device = torch.device("cpu")
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        self.model = ppo.ActorPPO(64, 8, self.device)
        self.trainer = QTrainer(self.model, lr=LEARNING_RATE, gamma=self.gamma)
        self.is_train = is_train
        self.old_state = None
        self.model_path = model_path

    def set_player(self, player):
        self.player = player

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

        state = np.zeros(MAX_PLAYERS * STATES_PER_PLAYER)

        state[0] = ai_player.y
        state[1] = ai_player.x
        state[2] = ai_player.rotation
        state[3] = ai_player.hp
        state[4] = ai_player.max_hp
        state[5] = ai_player.score
        state[6] = ai_player.uuid
        state[7] = ai_player.cooldown
        i = 8
        i = self.save_state_from(enemies, i, state)
        self.save_state_from(allies, i, state)

        return state

    @staticmethod
    def save_state_from(enemies, i, state):
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
        return i

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            minibatch = random.sample(self.memory, BATCH_SIZE)
        else:
            minibatch = self.memory

        states, actions, rewards, next_states, dones = zip(*minibatch)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state):
        self.trainer.train_step(
            self.old_state, self.old_action, self.old_reward, state, False
        )

    def get_action(self, state: np.ndarray) -> ndarray:
        self.epsilon = 0.3 if self.is_train else 0.1
        prediction: np.ndarray = self.model.act(state, self.epsilon)
        final_move = prediction
        final_move[0] = 1 if final_move[0] > 0.5 else 0
        final_move[1] = 1 if final_move[1] > 0.5 else 0
        final_move[2] = 1 if final_move[2] > 0.5 else 0
        final_move[3] = 1 if final_move[3] > 0.5 else 0
        final_move[4] = 1 if final_move[4] > 0.5 else 0
        final_move[5] = final_move[5] * config.WIDTH
        final_move[6] = final_move[6] * config.HEIGHT
        self.old_action = prediction
        self.old_state = state
        self.old_reward = self.player.score

        if self.is_train and self.old_state is not None and self.player is not None:
            self.train_short_memory(state)

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

        reward, done, score = (
            agent.get_player(game).score,
            not game.running,
            agent.get_player(game).score,
        )

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
            print("GAME", agent.number_of_games, "Score", score, "Record", record)

            # TODO: plot


if __name__ == "__main__":
    train()
