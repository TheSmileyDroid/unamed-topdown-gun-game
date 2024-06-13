from typing import Any, SupportsFloat

import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces
from gymnasium.core import ObsType, ActType
from pydantic import dataclasses


@dataclasses.dataclass
class Player:
    x: float
    y: float
    angle: float
    health: float
    cooldown: float = 0

    def distance(self, other):
        return np.linalg.norm((self.x - other.x, self.y - other.y), 2)

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "health": self.health,
        }


@dataclasses.dataclass
class Bullet:
    x: float
    y: float
    angle: float
    radius: float = 5
    speed: float = 4
    damage: float = 10
    player: Player | None = None

    def distance(self, other):
        return np.linalg.norm((self.x - other.x, self.y - other.y), 2)

    def collides_with(self, other):
        return self.distance(other) < self.radius

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
        }


class TopDownShooterEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self, render_mode=None):
        self._agent: Player = Player(x=0, y=0, angle=0, health=100)
        self._players: list[Player] = [Player(x=0, y=0, angle=0, health=100)] * 7
        self._bullets: list[Bullet] = []
        self.window_size = (640, 480)
        self._observation_space = spaces.Dict(
            {
                "you": spaces.Dict(
                    {
                        "x": spaces.Box(low=0, high=self.window_size[0], shape=(1,)),
                        "y": spaces.Box(low=0, high=self.window_size[1], shape=(1,)),
                        "angle": spaces.Box(low=0, high=2 * np.pi, shape=(1,)),
                        "health": spaces.Box(low=0, high=100, shape=(1,)),
                    }
                ),
                "players": spaces.Sequence(
                    spaces.Dict(
                        {
                            "x": spaces.Box(
                                low=0, high=self.window_size[0], shape=(1,)
                            ),
                            "y": spaces.Box(
                                low=0, high=self.window_size[1], shape=(1,)
                            ),
                            "angle": spaces.Box(low=0, high=2 * np.pi, shape=(1,)),
                            "health": spaces.Box(low=0, high=100, shape=(1,)),
                        }
                    )
                ),
                "near_bullets": spaces.Sequence(
                    spaces.Dict(
                        {
                            "x": spaces.Box(
                                low=0, high=self.window_size[0], shape=(1,)
                            ),
                            "y": spaces.Box(
                                low=0, high=self.window_size[1], shape=(1,)
                            ),
                            "angle": spaces.Box(low=0, high=2 * np.pi, shape=(1,)),
                        }
                    ),
                ),
                "cooldown": spaces.Box(low=0, high=100, shape=(1,)),
            }
        )
        self.observation_space = self._observation_space
        self._action_space = spaces.Dict(
            {
                "up": spaces.Discrete(2),
                "down": spaces.Discrete(2),
                "left": spaces.Discrete(2),
                "right": spaces.Discrete(2),
                "shoot": spaces.Discrete(2),
                "rotate_left": spaces.Discrete(2),
                "rotate_right": spaces.Discrete(2),
            }
        )
        self.action_space = self._action_space
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        self.window = None
        self.clock = None

    def _get_near_bullets(self):
        return sorted(
            self._bullets,
            key=lambda b: b.distance(self._agent),
            reverse=True,
        )[:10]

    def _get_obs(self):
        return {
            "you": self._agent.to_dict(),
            "players": tuple(map(lambda p: p.to_dict(), self._players)),
            "near_bullets": tuple(map(lambda b: b.to_dict(), self._get_near_bullets())),
            "cooldown": self._agent.cooldown,
        }

    def _get_info(self):
        return {}

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[ObsType, dict[str, Any]]:
        super().reset(seed=seed)

        self._agent = Player(
            x=np.random.randint(0, self.window_size[0]),
            y=np.random.randint(0, self.window_size[1]),
            angle=0,
            health=100,
            cooldown=0,
        )
        self._players = [
            Player(
                x=np.random.randint(0, self.window_size[0]),
                y=np.random.randint(0, self.window_size[1]),
                angle=0,
                health=100,
                cooldown=0,
            )
        ] * 7

        obs = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return obs, info

    def _shoot(self):
        if self._agent.cooldown > 0:
            return
        self._agent.cooldown = 0.5
        self._bullets.append(
            Bullet(
                x=self._agent.x,
                y=self._agent.y,
                angle=self._agent.angle,
                player=self._agent,
            )
        )

    def _move(self, action):
        if action["up"]:
            self._agent.y -= 1
        if action["down"]:
            self._agent.y += 1
        if action["left"]:
            self._agent.x -= 1
        if action["right"]:
            self._agent.x += 1

        self._agent.x = np.clip(self._agent.x, 0, self.window_size[0])
        self._agent.y = np.clip(self._agent.y, 0, self.window_size[1])

    def _rotate(self, action):
        if action["rotate_left"]:
            self._agent.angle -= np.pi / 8
        if action["rotate_right"]:
            self._agent.angle += np.pi / 8

        self._agent.angle = np.mod(self._agent.angle, 2 * np.pi)

    def _any_players_alive(self):
        return any(p.health > 0 for p in self._players)

    def _update_bullets(self):
        self._agent.cooldown -= 0.01
        for player in self._players:
            player.cooldown -= 0.01
        for bullet in self._bullets:
            bullet.x += np.cos(bullet.angle) * bullet.speed
            bullet.y += np.sin(bullet.angle) * bullet.speed
            if bullet.x < 0 or bullet.x > self.window_size[0]:
                self._bullets.remove(bullet)
            if bullet.y < 0 or bullet.y > self.window_size[1]:
                self._bullets.remove(bullet)

            for player in self._players:
                if bullet.collides_with(player):
                    if bullet.player is not player:
                        player.health -= bullet.damage
                        self._bullets.remove(bullet)
                        break

            if bullet.collides_with(self._agent):
                if self._agent is not bullet.player:
                    self._bullets.remove(bullet)
                    self._agent.health -= bullet.damage

    def step(
        self, action: ActType
    ) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:

        self._move(action)

        if action["shoot"]:
            self._shoot()

        self._rotate(action)

        terminated = not self._any_players_alive()
        reward = 100 if terminated else 0

        self._update_bullets()

        obs = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return obs, reward, terminated, False, info

    def render(self):
        if self.render_mode == "rgb_array":
            return self._render_frame()

    def _render_frame(self):
        if self.window is None and self.render_mode == "human":
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode(self.window_size)
            pygame.display.set_caption("TopDownShooter")
        if self.clock is None and self.render_mode == "human":
            self.clock = pygame.time.Clock()

        canvas = pygame.Surface(self.window_size)
        canvas.fill((255, 255, 255))

        pygame.draw.circle(
            canvas,
            (0, 0, 100),
            (self._agent.x, self._agent.y),
            5,
            0,
        )

        for player in self._players:
            pygame.draw.circle(
                canvas,
                (100, 0, 0),
                (player.x, player.y),
                5,
                0,
            )

        for bullet in self._bullets:
            pygame.draw.circle(
                canvas,
                (0, 0, 0),
                (bullet.x, bullet.y),
                bullet.radius,
                0,
            )

        if self.render_mode == "human":
            self.window.blit(canvas, canvas.get_rect())
            pygame.event.pump()
            pygame.display.update()
            self.clock.tick(self.metadata["render_fps"])
        else:
            return np.transpose(np.array(pygame.surfarray.pixels3d(canvas)), (1, 0, 2))

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()


if __name__ == "__main__":
    env = TopDownShooterEnv()