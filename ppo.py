import os
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
            nn.Sigmoid(),
        )
        self.critic = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.net.parameters(), lr=0.001)

    def forward(self, state):
        return self.net(state)

    def act(self, state, eps=0.1) -> np.ndarray:
        state = torch.from_numpy(state).float().to(self.device)
        action = self.net(state)
        if rd.random() < eps:
            action = torch.rand(self.action_dim).to(self.device)
        return action.cpu().detach().numpy()

    def update(self, state, action, reward, next_state, done):
        state = torch.from_numpy(state).float().to(self.device)
        action = torch.from_numpy(action).float().to(self.device)
        reward = torch.from_numpy(reward).float().to(self.device)
        next_state = torch.from_numpy(next_state).float().to(self.device)
        done = torch.from_numpy(done).float().to(self.device)

        # Calculate the target Q value
        target_q = reward + (1 - done) * self.critic.gamma * self.critic.target_Q(
            next_state
        )

        # Calculate the Q value of the current state
        current_q = self.critic.Q(state, action)

        # Calculate the loss
        loss = self.critic.loss(current_q, target_q)

        # Update the parameters
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def save(self, path):
        if not os.path.exists("models"):
            os.makedirs("models")
        with open(path, "wb") as f:
            torch.save(self.state_dict(), f)

    def load(self, path):
        if not os.path.exists(path):
            return
        with open(path, "rb") as f:
            self.load_state_dict(torch.load(f))
