from gymnasium.envs.registration import register

register(
    id="topdown_shooter/TopdownShooter-v0",
    entry_point="topdown_shooter.envs:TopDownShooterEnv",
    max_episode_steps=9000,
)
