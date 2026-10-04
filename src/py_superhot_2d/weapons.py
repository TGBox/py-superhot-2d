"""Weapon classes, projectile bullet physics, and throwable item mechanics."""

from __future__ import annotations
import math
import random
from enum import Enum
from typing import List, Tuple, Optional
import pygame

from py_superhot_2d.config import (
    COLOR_WEAPON,
    COLOR_WEAPON_PICKUP,
    COLOR_KATANA_BLADE,
    COLOR_BULLET_PLAYER,
    COLOR_BULLET_ENEMY,
    COLOR_BULLET_CORE,
    COLOR_TRAIL_PLAYER,
    COLOR_TRAIL_ENEMY,
    BULLET_SPEED,
    BULLET_RADIUS,
    THROW_SPEED,
)
from py_superhot_2d.math_utils import (
    Vec2,
    line_segment_intersection,
    ray_cast_rect,
    circle_rect_collision,
)
from py_superhot_2d.audio import get_audio
from py_superhot_2d.particles import ParticleSystem


class WeaponType(Enum):
    FISTS = "fists"
    PISTOL = "pistol"
    SHOTGUN = "shotgun"
    RIFLE = "rifle"
    KATANA = "katana"
    BOTTLE = "bottle"


class Bullet:
    """A high-speed tactical projectile with glowing trail."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        owner: str,  # "player" or "enemy"
        speed: float = BULLET_SPEED,
    ):
        self.pos = Vec2(pos)
        self.vel = vel.normalize() * speed if vel.length_squared() > 0 else Vec2(speed, 0)
        self.owner = owner
        self.alive = True
        self.trail: List[Vec2] = [Vec2(pos)]
        self.max_trail_len = 10
        self.radius = BULLET_RADIUS

    def update(
        self,
        dt: float,
        walls: List[pygame.Rect],
        particles: ParticleSystem,
    ) -> bool:
        """Update position and check wall collisions. Returns True if still alive."""
        if not self.alive:
            return False

        old_pos = Vec2(self.pos)
        step = self.vel * dt
        new_pos = old_pos + step

        # Raycast against all walls to detect tunneling at high speed
        closest_hit = None
        min_t = 1.0

        for wall in walls:
            hit = ray_cast_rect(old_pos, new_pos, wall)
            if hit is not None:
                hit_pt, t, normal = hit
                if t < min_t:
                    min_t = t
                    closest_hit = (hit_pt, normal)

        if closest_hit is not None:
            hit_pt, normal = closest_hit
            self.pos = hit_pt
            self.alive = False
            # Spawn ricochet sparks and play ping sound
            spark_col = (255, 200, 60) if self.owner == "enemy" else (180, 180, 200)
            particles.spawn_sparks(hit_pt, normal, count=7, color=spark_col)
            get_audio().play("ricochet", volume=0.45)
            return False

        self.pos = new_pos
        self.trail.append(Vec2(new_pos))
        if len(self.trail) > self.max_trail_len:
            self.trail.pop(0)

        return True

    def draw(self, surface: pygame.Surface) -> None:
        """Draw bullet with incandescent core and fading trail."""
        if len(self.trail) > 1:
            trail_col = COLOR_TRAIL_ENEMY if self.owner == "enemy" else COLOR_TRAIL_PLAYER
            for i in range(len(self.trail) - 1):
                prog = (i + 1) / len(self.trail)
                width = max(1, int(self.radius * prog * 1.5))
                pygame.draw.line(
                    surface,
                    trail_col,
                    (self.trail[i].x, self.trail[i].y),
                    (self.trail[i + 1].x, self.trail[i + 1].y),
                    width,
                )

        # Bullet Head
        col = COLOR_BULLET_ENEMY if self.owner == "enemy" else COLOR_BULLET_PLAYER
        pygame.draw.circle(surface, col, (int(self.pos.x), int(self.pos.y)), int(self.radius))
        pygame.draw.circle(surface, COLOR_BULLET_CORE, (int(self.pos.x), int(self.pos.y)), max(1, int(self.radius * 0.5)))


class WeaponItem:
    """A physical weapon that can be carried, dropped, thrown, or caught."""

    def __init__(
        self,
        weapon_type: WeaponType,
        pos: Vec2,
        ammo: Optional[int] = None,
    ):
        self.weapon_type = weapon_type
        self.pos = Vec2(pos)
        self.vel = Vec2(0, 0)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = 0.0
        self.thrown = False
        self.throw_owner: Optional[str] = None  # "player" or "enemy"
        self.picked_up = False
        self.pickup_radius = 28.0

        # Max ammo and fire stats configuration
        if weapon_type == WeaponType.PISTOL:
            self.max_ammo = 6
            self.fire_rate = 0.35  # seconds
            self.name = "Pistole"
        elif weapon_type == WeaponType.SHOTGUN:
            self.max_ammo = 2
            self.fire_rate = 0.75
            self.name = "Schrotflinte"
        elif weapon_type == WeaponType.RIFLE:
            self.max_ammo = 24
            self.fire_rate = 0.12
            self.name = "Sturmgewehr"
        elif weapon_type == WeaponType.KATANA:
            self.max_ammo = 999  # Melee
            self.fire_rate = 0.3
            self.name = "Katana"
        elif weapon_type == WeaponType.BOTTLE:
            self.max_ammo = 0
            self.fire_rate = 0.4
            self.name = "Flasche"
        else:
            self.max_ammo = 0
            self.fire_rate = 0.3
            self.name = "Fäuste"

        self.ammo = self.max_ammo if ammo is None else ammo
        self.cooldown = 0.0
        self.burst_count = 0  # For burst fire weapons (Rifle)
        self.burst_timer = 0.0

    def throw(self, direction: Vec2, owner: str) -> None:
        """Launch weapon as a lethal spinning projectile."""
        self.thrown = True
        self.throw_owner = owner
        self.picked_up = False
        dir_norm = direction.normalize() if direction.length_squared() > 0 else Vec2(1, 0)
        self.vel = dir_norm * THROW_SPEED
        self.rot_speed = random.choice([-1, 1]) * random.uniform(720, 1080)
        get_audio().play("throw", volume=0.7)

    def update(
        self,
        dt: float,
        walls: List[pygame.Rect],
        particles: ParticleSystem,
    ) -> None:
        """Update physics when thrown or dropped."""
        if self.cooldown > 0:
            self.cooldown = max(0.0, self.cooldown - dt)

        if not self.thrown and self.vel.length_squared() < 4:
            return

        friction = max(0.0, 1.0 - 2.8 * dt)
        self.vel *= friction
        self.rot_speed *= friction

        if self.vel.length_squared() < 25:
            self.thrown = False
            self.vel = Vec2(0, 0)
            self.rot_speed = 0.0

        new_pos = self.pos + self.vel * dt
        self.rotation = (self.rotation + self.rot_speed * dt) % 360

        # Wall collisions for thrown items
        for wall in walls:
            push = circle_rect_collision(new_pos, 12.0, wall)
            if push is not None:
                new_pos += push
                # Bounce
                if abs(push.x) > abs(push.y):
                    self.vel.x = -self.vel.x * 0.45
                else:
                    self.vel.y = -self.vel.y * 0.45
                particles.spawn_sparks(new_pos, push.normalize(), count=3)
                get_audio().play("ricochet", volume=0.3)
                break

        self.pos = new_pos

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the weapon silhouette on the ground or spinning in air."""
        if self.picked_up:
            return

        rad = math.radians(self.rotation)
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        def rot_pt(x: float, y: float) -> Tuple[float, float]:
            return (
                self.pos.x + x * cos_a - y * sin_a,
                self.pos.y + x * sin_a + y * cos_a,
            )

        # Draw weapon drop shadow
        shadow_off = 3.0 if self.thrown else 1.5
        shadow_pts = []

        if self.weapon_type == WeaponType.PISTOL:
            # Gun shape: Barrel + grip
            pts = [rot_pt(-6, -3), rot_pt(8, -3), rot_pt(8, 2), rot_pt(2, 2), rot_pt(-1, 8), rot_pt(-6, 8)]
            pygame.draw.polygon(surface, COLOR_WEAPON, pts)

        elif self.weapon_type == WeaponType.SHOTGUN:
            # Longer bulky shotgun
            pts = [rot_pt(-12, -4), rot_pt(15, -4), rot_pt(15, 2), rot_pt(2, 2), rot_pt(-4, 7), rot_pt(-12, 7)]
            pygame.draw.polygon(surface, COLOR_WEAPON, pts)

        elif self.weapon_type == WeaponType.RIFLE:
            # Sleek automatic rifle with magazine
            pts = [
                rot_pt(-14, -3), rot_pt(16, -3), rot_pt(16, 2), rot_pt(6, 2),
                rot_pt(4, 9), rot_pt(0, 9), rot_pt(0, 2), rot_pt(-6, 7), rot_pt(-14, 7)
            ]
            pygame.draw.polygon(surface, COLOR_WEAPON, pts)

        elif self.weapon_type == WeaponType.KATANA:
            # Long slender curved blade with guard
            p_tip = rot_pt(22, 0)
            p_base = rot_pt(-14, 0)
            p_hilt = rot_pt(-20, 0)
            # Guard
            g1 = rot_pt(-14, -5)
            g2 = rot_pt(-14, 5)
            pygame.draw.line(surface, COLOR_WEAPON, g1, g2, 3)
            pygame.draw.line(surface, COLOR_WEAPON, p_base, p_hilt, 3)
            pygame.draw.line(surface, COLOR_KATANA_BLADE, p_base, p_tip, 2)
            pygame.draw.circle(surface, COLOR_KATANA_BLADE, (int(p_tip[0]), int(p_tip[1])), 1)

        elif self.weapon_type == WeaponType.BOTTLE:
            # Bottle silhouette
            pts = [
                rot_pt(-8, -4), rot_pt(3, -4), rot_pt(6, -2), rot_pt(10, -2),
                rot_pt(10, 2), rot_pt(6, 2), rot_pt(3, 4), rot_pt(-8, 4)
            ]
            pygame.draw.polygon(surface, COLOR_WEAPON, pts)

        # Highlight ring if near and pickable
        if not self.thrown and self.ammo > 0:
            pygame.draw.circle(surface, COLOR_WEAPON_PICKUP, (int(self.pos.x), int(self.pos.y)), 14, 1)
