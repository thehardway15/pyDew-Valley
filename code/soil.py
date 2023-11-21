import pygame
import random
from settings import *
from support import *
from pytmx.util_pygame import load_pygame


class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']


class WaterTile(pygame.sprite.Sprite):

    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']


class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)
        self.plant_type = plant_type
        self.frames = import_folder(f'../graphics/fruit/{plant_type}')
        self.soil = soil
        self.check_watered = check_watered

        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.soil):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))


class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):

        # sprites groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        # graphics
        self.soil_surfs = import_folder_dict('../graphics/soil')
        self.soil_water_sprites = import_folder('../graphics/soil_water')

        self.create_soil_grid()
        self.create_hit_rects()

    def create_soil_grid(self):
        ground = pygame.image.load('../graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]

        for x, y, _ in load_pygame('../data/map.tmx').get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE

                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:

                    # tile neighbors
                    t = 'X' in self.grid[index_row - 1][index_col]
                    b = 'X' in self.grid[index_row + 1][index_col]
                    r = 'X' in row[index_col + 1]
                    l = 'X' in row[index_col - 1]

                    # diagonal
                    tl = 'X' in self.grid[index_row - 1][index_col - 1]
                    tr = 'X' in self.grid[index_row - 1][index_col + 1]
                    bl = 'X' in self.grid[index_row + 1][index_col - 1]
                    br = 'X' in self.grid[index_row + 1][index_col + 1]

                    tile_type = 'o'

                    # all sides
                    if all([t, b, r, l]): tile_type = 'x'

                    # horizontal tiles only
                    if l and not any([t, b, r]): tile_type = 'r'
                    if r and not any([t, b, l]): tile_type = 'l'
                    if r and l and not any([t, b]): tile_type = 'lr'

                    # vertical tiles only
                    if t and not any([r, l, b]): tile_type = 'b'
                    if b and not any([r, l, t]): tile_type = 't'
                    if b and t and not any([r, l]): tile_type = 'tb'

                    # corners
                    if r and b and not any([l, t]): tile_type = 'tl'
                    if l and b and not any([r, t]): tile_type = 'tr'
                    if r and t and not any([l, b]): tile_type = 'bl'
                    if l and t and not any([r, b]): tile_type = 'br'

                    # T shapes
                    if all([t, b, r]) and not l: tile_type = 'tbr'
                    if all([t, b, l]) and not r: tile_type = 'tbl'
                    if all([r, l, b]) and not t: tile_type = 'lrt'
                    if all([r, l, t]) and not b: tile_type = 'lrb'

                    # middle
                    if all([l, r, b, bl, br]) and not t: tile_type = 'tm'
                    if all([l, r, t, tl, tr]) and not b: tile_type = 'bm'
                    if all([t, b, l, tl, bl]) and not r: tile_type = 'rm'
                    if all([t, b, r, tr, br]) and not l: tile_type = 'lm'

                    if all([l, r, b, bl]) and not t: tile_type = 'tm'
                    if all([l, r, t, tl]) and not b: tile_type = 'bm'
                    if all([t, b, l, tl]) and not r: tile_type = 'rm'
                    if all([t, b, r, tr]) and not l: tile_type = 'lm'

                    if all([l, r, b, br]) and not t: tile_type = 'tm'
                    if all([l, r, t, tr]) and not b: tile_type = 'bm'
                    if all([t, b, l, bl]) and not r: tile_type = 'rm'
                    if all([t, b, r, br]) and not l: tile_type = 'lm'

                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites]
                    )

    def water(self, point):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(point):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')

                WaterTile(
                    pos=(soil_sprite.rect.x, soil_sprite.rect.y),
                    surf=random.choice(self.soil_water_sprites),
                    groups=[self.all_sprites, self.water_sprites]
                )

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    WaterTile(
                        pos=(x, y),
                        surf=random.choice(self.soil_water_sprites),
                        groups=[self.all_sprites, self.water_sprites]
                    )

    def remove_water(self):
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def plant_seed(self, point, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(point):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)

    def check_watered(self, soil):
        x = soil.rect.x // TILE_SIZE
        y = soil.rect.y // TILE_SIZE
        cell = self.grid[y][x]
        is_watered = 'W' in cell
        return is_watered

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()