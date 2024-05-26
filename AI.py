import random

import config


class AI:
    def __init__(self, seed=0):
        random.seed(seed)
        self.mouse = (0, 0)
        pass

    def get_keys(self):
        return [random.choice([False, True]) for _ in range(5)]

    def get_controller(self):
        return {
            "up": 0,
            "down": 1,
            "left": 2,
            "right": 3,
            "shoot": 4,
        }

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
