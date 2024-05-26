import pygame


class Crosshair:
    def __init__(self):
        self.pos = pygame.Vector2(0, 0)

    def move(self, pos):
        self.pos = pygame.Vector2(pos)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), self.pos, 5)
