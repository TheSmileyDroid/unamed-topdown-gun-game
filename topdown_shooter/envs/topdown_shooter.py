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
    score: float = 0
    direction: tuple[int, int] = (0, 0)
    time_to_next_action: float = 0

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
    real: bool = True
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
        self._players: list[Player] = [
            Player(x=0, y=0, angle=0, health=100) for _ in range(7)
        ]
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
                "players": spaces.Tuple(
                    [
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
                    ]
                    * 7,
                ),
                "near_bullets": spaces.Tuple(
                    [
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
                        )
                    ]
                    * 10,
                ),
                "cooldown": spaces.Box(low=0, high=100, shape=(1,)),
            }
        )
        self.observation_space = spaces.flatten_space(self._observation_space)

        self.action_space = spaces.MultiDiscrete(
            [2, 2, 2, 2, 2, 2, 2]
        )  # up, down, left, right, shoot, rotate_left, rotate_right
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        self.window = None
        self.clock = None

    def _get_near_bullets(self):
        bullets = sorted(
            self._bullets,
            key=lambda b: b.distance(self._agent),
            reverse=True,
        )[:10]

        for i in range(10 - len(bullets)):
            bullets.append(Bullet(x=0, y=0, angle=0, real=False))

        return bullets

    def _get_obs(self):
        return spaces.flatten(
            self._observation_space,
            {
                "you": self._agent.to_dict(),
                "players": tuple(map(lambda p: p.to_dict(), self._players)),
                "near_bullets": tuple(
                    map(lambda b: b.to_dict(), self._get_near_bullets())
                ),
                "cooldown": self._agent.cooldown,
            },
        )

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
        for player in self._players:
            player.x = np.random.randint(0, self.window_size[0])
            player.y = np.random.randint(0, self.window_size[1])
            player.angle = 0
            player.health = 100
            player.cooldown = 0

        obs = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return obs, info

    @staticmethod
    def _transform_actions(action):
        return {
            "up": action[0],
            "down": action[1],
            "left": action[2],
            "right": action[3],
            "shoot": action[4],
            "rotate_left": action[5],
            "rotate_right": action[6],
        }

    def _shoot(self, player: Player):
        if player.cooldown > 0:
            return
        player.cooldown = 0.5
        self._bullets.append(
            Bullet(
                x=player.x,
                y=player.y,
                angle=player.angle,
                player=player,
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

    def _update_players(self):
        for player in self._players:
            if player.health <= 0:
                continue
            player.time_to_next_action -= 0.5
            if player.time_to_next_action <= 0:
                player.direction = (
                    np.random.randint(0, 3) - 1,
                    np.random.randint(0, 3) - 1,
                )
                player.angle = np.random.rand() * 2 * np.pi
                player.time_to_next_action = np.random.randint(0, 10)

            player.x += player.direction[0]
            player.y += player.direction[1]
            player.x = np.clip(player.x, 0, self.window_size[0])
            player.y = np.clip(player.y, 0, self.window_size[1])

            if np.random.rand() < 0.1:
                self._shoot(player)

    def _update_bullets(self):
        for bullet in self._bullets:
            bullet.x += np.cos(bullet.angle) * bullet.speed
            bullet.y += np.sin(bullet.angle) * bullet.speed
            if bullet.x < 0 or bullet.x > self.window_size[0]:
                self._bullets.remove(bullet)
            if bullet.y < 0 or bullet.y > self.window_size[1]:
                try:
                    self._bullets.remove(bullet)
                except ValueError:
                    pass

            for player in self._players:
                if player.health <= 0:
                    continue
                if bullet.collides_with(player):
                    if bullet.player is not player:
                        player.health -= bullet.damage
                        player.score -= bullet.damage
                        bullet.player.score += bullet.damage
                        try:
                            self._bullets.remove(bullet)
                        except ValueError:
                            pass
                        break

            if bullet.collides_with(self._agent):
                if self._agent is not bullet.player:
                    try:
                        self._bullets.remove(bullet)
                    except ValueError:
                        pass
                    self._agent.health -= bullet.damage
                    self._agent.score -= bullet.damage
                    bullet.player.score += bullet.damage

    def step(
        self, action: ActType
    ) -> tuple[ObsType, SupportsFloat, bool, bool, dict[str, Any]]:
        action: dict = self._transform_actions(action)

        self._agent.cooldown -= 0.01
        self._agent.score = 0
        for player in self._players:
            player.cooldown -= 0.01
            player.score = 0

        self._move(action)

        if action["shoot"]:
            self._shoot(self._agent)

        self._rotate(action)

        self._update_bullets()

        self._update_players()

        terminated = not self._any_players_alive()
        reward = 1000 if terminated else 0

        reward += self._agent.score

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
            if player.health <= 0:
                continue
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
