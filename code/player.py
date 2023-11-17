import pygame
from settings import *
from support import *
from timer import Timer


class Player(pygame.sprite.Sprite):

    def __init__(self, pos, group):
        super().__init__(group)

        self.import_assets()
        self.status = 'down_idle'
        self.frame_index = 0

        # general setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center=pos)

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200

        # timers
        self.timers = {
            'tool use': Timer(350, self.use_tool),
            'tool switch': Timer(200),
            'seed use': Timer(350, self.plant_seed),
            'seed switch': Timer(200)
        }

        # tools
        self.selected_tool = 'axe'

    def import_assets(self):
        self.animations = {
            'left': [], 'right': [], 'up': [], 'down': [],
            'left_idle': [], 'right_idle': [], 'up_idle': [], 'down_idle': [],
            'left_hoe': [], 'right_hoe': [], 'up_hoe': [], 'down_hoe': [],
            'left_axe': [], 'right_axe': [], 'up_axe': [], 'down_axe': [],
            'left_water': [], 'right_water': [], 'up_water': [], 'down_water': [],
        }

        for animation in self.animations.keys():
            full_path = f'../graphics/character/{animation}'
            self.animations[animation] = import_folder(full_path)

    def animation(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        self.image = self.animations[self.status][int(self.frame_index)]

    def use_tool(self):
        pass

    def plant_seed(self):
        pass

    def input(self):
        keys = pygame.key.get_pressed()

        if not self.timers['tool use'].active:
            # movement
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            elif keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            else:
                self.direction.x = 0

            # tools
            if keys[pygame.K_SPACE]:
                self.timers['tool use'].activate()
                self.direction = pygame.math.Vector2()
                self.frame_index = 0

    def get_status(self):
        # idle
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'

        # tool use
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool

    def move(self, dt):
        # normalazing a vector (diagonal move speed)
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        # horizonal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.centerx = self.pos.x

        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.rect.centery = self.pos.y

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def update(self, dt):
        self.update_timers()
        self.input()
        self.get_status()
        self.move(dt)
        self.animation(dt)