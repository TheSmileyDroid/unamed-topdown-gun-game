import random as rd

import numpy as np
import torch
import torch.nn as nn


class ActorPPO(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, device: torch.device) -> None:
        super(ActorPPO, self).__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.device = device
        self.net = nn.Sequential(
            nn.Linear(self.state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, self.action_dim),
            nn.Tanh(),
        )

    def forward(self, state):
        return self.net(state)

    def act(self, state, eps=0.1) -> np.ndarray:
        state = torch.from_numpy(state).float().to(self.device)
        action = self.net(state)
        if rd.random() < eps:
            action = self.max_action * torch.rand(self.action_dim).to(self.device)
        return action.cpu().numpy()

    def update(self, state, action, reward, next_state, done):
        pass
        # TODO

    def save(self, path):
        pass

    def load(self, path):
        pass
