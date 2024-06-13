import gymnasium as gym

import topdown_shooter  # noqa


def main():
    env = gym.make("topdown_shooter/TopdownShooter-v0", render_mode="human")

    obs = env.reset()
    for i in range(1000):
        action = env.action_space.sample()
        obs, reward, done, _, info = env.step(action)
        env.render()
        # VecEnv resets automatically
        # if done:
        #   obs = vec_env.reset()
    pass


if __name__ == "__main__":
    main()
