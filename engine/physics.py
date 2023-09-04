import pygame

from engine.gui import CoordinateArrayType
from engine.tools import Vector


class CollisionRect(pygame.Rect):

    def __init__(self, owner, dim: CoordinateArrayType, pos=None):
        super().__init__(0, 0, *dim)
        self.owner = owner
        if pos is not None:
            self.center = pos
            self.ground_counter = 0

    def collide_x(self, collision_list: tuple = None):
        self.centerx = self.owner.pos.x
        collided = [False, False]

        if collision_list is None:
            return collided

        for body in collision_list:
            if self.colliderect(body.body):
                if self.owner.vel.x > 0:
                    collided[1] = True
                    self.right = body.body.left
                elif self.owner.vel.x < 0:
                    collided[0] = True
                    body.left = body.body.right
                self.owner.vel.x = 0
                self.owner.pos.x = body.centerx
        return collided

    def collide_y(self, collision_list: tuple = None):
        self.centery = self.owner.pos.y
        collided = [False, False]

        if collision_list is None:
            return collided

        for body in collision_list:
            if self.colliderect(body.body):
                if self.owner.vel.y > 0:
                    collided[1] = True
                    self.ground_counter = 5
                    self.bottom = body.body.top
                elif self.owner.vel.y < 0:
                    collided[0] = True
                    self.top = body.body.bottom
                self.owner.vel.y = 0
                self.owner.pos.y = self.centery
        return collided


class StaticBody:

    def __init__(self, dim, pos):
        self.pos = Vector(pos)
        self.body = CollisionRect(self, dim, pos)

    def resize(self, dim):
        self.body = CollisionRect(self, dim)
        self.body.center = self.pos


class KinematicBody(StaticBody):

    def __init__(self, dim, pos, vel=(0, 0)):
        super().__init__(dim, pos)
        self.vel = Vector(vel)
        self.acc = Vector(0, 0)
        self.ground_counter = 0
        self.collided = [False, False, False, False]

    def move(self, dt: float, collision_list: tuple = None):

        self.pos.x += self.vel.x * dt                            # x = ∫vx dt
        self.collided[:2] = self.body.collide_x(collision_list)  # solving collisions in the x direction

        self.pos.y += self.vel.y * dt                            # y = ∫vy dt
        self.collided[2:] = self.body.collide_y(collision_list)  # solving collisions in the y direction


class DynamicBody(KinematicBody):

    def __init__(
            self,
            dim: CoordinateArrayType,
            pos: CoordinateArrayType,
            vel: CoordinateArrayType = Vector(0, 0),
            mass: float = 1.0,
            gravity: float = 0.0,
            friction: float = 0.0,
    ):
        super().__init__(dim, pos, vel)
        self.mass = mass
        self.g = gravity
        self.friction = friction
        self.test = Vector(0, 0)

    def gravity(self) -> Vector:
        return Vector(0, self.g) * self.mass

    def damping(self) -> Vector:
        return -self.vel * self.friction

    def net_force(self):
        return self.gravity() + self.damping() + self.test

    def move(self, dt: float, collision_list: tuple = None):

        self.acc = self.net_force() / self.mass                  # a = F / m
        self.collided = [False, False, False, False]

        self.vel.x += self.acc.x * dt                            # vx = ∫ax dt
        self.pos.x = self.pos.x + self.vel.x * dt                # x = ∫vx dt
        self.collided[:2] = self.body.collide_x(collision_list)  # solving collisions in the x direction

        self.vel.y += self.acc.y * dt                            # vy = ∫ay dt
        self.pos.y = self.pos.y + self.vel.y * dt                # y = ∫vy dt
        self.collided[2:] = self.body.collide_y(collision_list)  # solving collisions in the y direction
