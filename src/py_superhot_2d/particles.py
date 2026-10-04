"""Particle physics system: Crystal shards, sparks, slice effects, and bullet trails."""

from __future__ import annotations
import math
import random
from typing import List, Tuple
import pygame
from py_superhot_2d.config import (
    COLOR_ENEMY,
    COLOR_ENEMY_ACCENT,
    COLOR_BULLET_CORE,
    COLOR_WALL,
)
from py_superhot_2d.math_utils import Vec2


class Shard:
    """A crystalline polygon shard created when an enemy shatters."""

    def __init__(self, pos: Vec2, base_vel: Vec2, is_red: bool = True):
        self.pos = Vec2(pos)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(80, 360)
        self.vel = Vec2(math.cos(angle), math.sin(angle)) * speed + base_vel * 0.4
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-400, 400)
        self.scale = random.uniform(3.0, 9.0)
        self.lifetime = random.uniform(3.5, 6.0)
        self.age = 0.0
        self.is_red = is_red

        # Generate a distinct faceted polygon (3 to 5 points)
        num_points = random.choice([3, 4, 4, 5])
        self.base_points: List[Vec2] = []
        for i in range(num_points):
            pt_ang = (i / num_points) * math.tau + random.uniform(-0.3, 0.3)
            pt_r = random.uniform(0.5, 1.2) * self.scale
            self.base_points.append(Vec2(math.cos(pt_ang) * pt_r, math.sin(pt_ang) * pt_r))

        # Color variation
        if self.is_red:
            r = random.randint(210, 255)
            g = random.randint(20, 60)
            b = random.randint(30, 70)
            self.color = (r, g, b)
            self.edge_color = (255, 120, 130)
        else:
            # Dark charcoal shard (player death)
            v = random.randint(25, 45)
            self.color = (v, v, v)
            self.edge_color = (70, 70, 80)

    def update(self, dt: float, walls: List[pygame.Rect]) -> bool:
        """Update physics. Returns False if expired."""
        self.age += dt
        if self.age >= self.lifetime:
            return False

        # Apply friction
        friction = max(0.0, 1.0 - 1.8 * dt)
        self.vel *= friction
        self.rot_speed *= friction

        new_pos = self.pos + self.vel * dt

        # Simple wall bouncing
        for wall in walls:
            if wall.collidepoint(new_pos.x, new_pos.y):
                # Reverse component closest to edge
                dx_left = abs(new_pos.x - wall.left)
                dx_right = abs(new_pos.x - wall.right)
                dy_top = abs(new_pos.y - wall.top)
                dy_bottom = abs(new_pos.y - wall.bottom)
                m = min(dx_left, dx_right, dy_top, dy_bottom)
                if m in (dx_left, dx_right):
                    self.vel.x = -self.vel.x * 0.5
                else:
                    self.vel.y = -self.vel.y * 0.5
                new_pos = self.pos
                break

        self.pos = new_pos
        self.rotation += self.rot_speed * dt
        return True

    def draw(self, surface: pygame.Surface) -> None:
        """Render rotated polygon facet."""
        # Calculate fade out during final 1.5 seconds
        fade_start = self.lifetime - 1.5
        alpha = 255
        if self.age > fade_start:
            alpha = int(255 * (1.0 - (self.age - fade_start) / 1.5))
            if alpha <= 0:
                return

        rad = math.radians(self.rotation)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        pts = []
        for pt in self.base_points:
            rx = pt.x * cos_a - pt.y * sin_a + self.pos.x
            ry = pt.x * sin_a + pt.y * cos_a + self.pos.y
            pts.append((rx, ry))

        if len(pts) >= 3:
            if alpha < 255:
                # Draw on transparent temp surface
                min_x = min(p[0] for p in pts) - 2
                max_x = max(p[0] for p in pts) + 2
                min_y = min(p[1] for p in pts) - 2
                max_y = max(p[1] for p in pts) + 2
                w = max(4, int(max_x - min_x))
                h = max(4, int(max_y - min_y))
                shard_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                local_pts = [(p[0] - min_x, p[1] - min_y) for p in pts]
                pygame.draw.polygon(shard_surf, (*self.color, alpha), local_pts)
                pygame.draw.polygon(shard_surf, (*self.edge_color, alpha), local_pts, 1)
                surface.blit(shard_surf, (min_x, min_y))
            else:
                pygame.draw.polygon(surface, self.color, pts)
                pygame.draw.polygon(surface, self.edge_color, pts, 1)


class Spark:
    """A bright spark emitted from bullet wall hits or blade collisions."""

    def __init__(self, pos: Vec2, dir_vec: Vec2, color: Tuple[int, int, int]):
        self.pos = Vec2(pos)
        spread = random.uniform(-0.7, 0.7)
        spd = random.uniform(150, 420)
        cos_s, sin_s = math.cos(spread), math.sin(spread)
        rot_dir = Vec2(
            dir_vec.x * cos_s - dir_vec.y * sin_s,
            dir_vec.x * sin_s + dir_vec.y * cos_s,
        )
        self.vel = rot_dir * spd
        self.color = color
        self.lifetime = random.uniform(0.12, 0.28)
        self.age = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False
        self.pos += self.vel * dt
        self.vel *= max(0.0, 1.0 - 4.0 * dt)
        return True

    def draw(self, surface: pygame.Surface) -> None:
        rem = 1.0 - (self.age / self.lifetime)
        line_len = max(2.0, self.vel.length() * 0.02)
        end_pos = self.pos - self.vel.normalize() * line_len if self.vel.length_squared() > 1 else self.pos
        pygame.draw.line(surface, self.color, (self.pos.x, self.pos.y), (end_pos.x, end_pos.y), max(1, int(rem * 2)))


class SliceSlash:
    """Visual arc trail for Katana blade swings."""

    def __init__(self, pos: Vec2, angle: float, arc_degrees: float = 120.0, radius: float = 52.0):
        self.pos = Vec2(pos)
        self.angle = angle
        self.arc_rad = math.radians(arc_degrees)
        self.radius = radius
        self.lifetime = 0.16
        self.age = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface) -> None:
        alpha = int(255 * (1.0 - self.age / self.lifetime))
        if alpha <= 0:
            return
        surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        start_ang = self.angle - self.arc_rad / 2
        end_ang = self.angle + self.arc_rad / 2
        steps = 10
        pts = []
        for i in range(steps + 1):
            a = start_ang + (end_ang - start_ang) * (i / steps)
            pts.append((
                self.pos.x + math.cos(a) * self.radius,
                self.pos.y + math.sin(a) * self.radius,
            ))
        if len(pts) > 1:
            pygame.draw.lines(surf, (255, 255, 255, alpha), False, pts, 3)
            pygame.draw.lines(surf, (220, 240, 255, int(alpha * 0.6)), False, pts, 6)
        surface.blit(surf, (0, 0))


class ParticleSystem:
    """Manages all active particles, shards, sparks, and visual effects."""

    def __init__(self):
        self.shards: List[Shard] = []
        self.sparks: List[Spark] = []
        self.slashes: List[SliceSlash] = []

    def spawn_shatter(self, pos: Vec2, impact_vel: Vec2, count: int = 18, is_red: bool = True) -> None:
        """Spawn exploding glass/crystal shards."""
        for _ in range(count):
            self.shards.append(Shard(pos, impact_vel, is_red=is_red))

    def spawn_sparks(self, pos: Vec2, normal: Vec2, count: int = 8, color: Tuple[int, int, int] = (255, 200, 60)) -> None:
        """Spawn bright wall ricochet / slice sparks."""
        for _ in range(count):
            self.sparks.append(Spark(pos, normal, color))

    def spawn_slash(self, pos: Vec2, angle: float) -> None:
        """Spawn katana slash arc visual."""
        self.slashes.append(SliceSlash(pos, angle))

    def update(self, dt: float, walls: List[pygame.Rect]) -> None:
        """Update all particles with given delta time."""
        self.shards = [s for s in self.shards if s.update(dt, walls)]
        self.sparks = [s for s in self.sparks if s.update(dt)]
        self.slashes = [s for s in self.slashes if s.update(dt)]

    def draw(self, surface: pygame.Surface) -> None:
        """Render all particles."""
        for shard in self.shards:
            shard.draw(surface)
        for spark in self.sparks:
            spark.draw(surface)
        for slash in self.slashes:
            slash.draw(surface)

    def clear(self) -> None:
        """Clear all particles."""
        self.shards.clear()
        self.sparks.clear()
        self.slashes.clear()
