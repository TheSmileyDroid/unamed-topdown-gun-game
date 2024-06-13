import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.vec_env import SubprocVecEnv

import topdown_shooter  # noqa


def make_env(env_id: str, rank: int, seed: int = 0):
    """
    Utility function for multiprocessed env.

    :param env_id: the environment ID
    :param num_env: the number of environments you wish to have in subprocesses
    :param seed: the initial seed for RNG
    :param rank: index of the subprocess
    """

    def _init():
        env = gym.make(env_id, render_mode="rgb_array")
        env.reset(seed=seed + rank)
        return env

    set_random_seed(seed)
    return _init


def main():
    env_id = "topdown_shooter/TopdownShooter-v0"
    num_cpu = 4

    vec_env = SubprocVecEnv([make_env(env_id, i) for i in range(num_cpu)])

    model = PPO("MlpPolicy", vec_env, verbose=1)
    model.learn(total_timesteps=40000)
    model.save("topdown_shooter_model")

    # model.load("topdown_shooter_model")

    obs = vec_env.reset()
    for i in range(1000):
        action, _states = model.predict(obs)
        obs, rewards, dones, info = vec_env.step(action)
        vec_env.render(mode="human")
        # VecEnv resets automatically
        # if done:
        #   obs = vec_env.reset()
    pass


if __name__ == "__main__":
    main()
