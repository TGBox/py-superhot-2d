"""Player and Enemy entities, AI state machine, melee combat, and HOTSWITCH mechanic."""

from __future__ import annotations
import math
import random
from typing import List, Optional, Tuple
import pygame

from py_superhot_2d.config import (
    COLOR_PLAYER,
    COLOR_PLAYER_HANDS,
    COLOR_ENEMY,
    COLOR_ENEMY_ACCENT,
    COLOR_ENEMY_STUN,
    COLOR_HOTSWITCH_TARGET,
    COLOR_WEAPON,
    COLOR_KATANA_BLADE,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    ENEMY_RADIUS,
    ENEMY_SPEED,
    PUNCH_RANGE,
    PUNCH_COOLDOWN,
    HOTSWITCH_COOLDOWN,
    HOTSWITCH_RANGE,
)
from py_superhot_2d.math_utils import (
    Vec2,
    resolve_circle_walls,
    has_line_of_sight,
    ray_cast_rect,
)
from py_superhot_2d.audio import get_audio
from py_superhot_2d.particles import ParticleSystem
from py_superhot_2d.weapons import WeaponItem, WeaponType, Bullet


class Player:
    """The player character with time dilation influence and Hotswitch capability."""

    def __init__(self, pos: Vec2):
        self.pos = Vec2(pos)
        self.angle = 0.0  # Angle in radians
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED
        self.is_alive = True
        self.equipped_weapon: Optional[WeaponItem] = None
        self.punch_cooldown = 0.0
        self.hotswitch_cooldown = 0.0
        self.burst_bullets_left = 0
        self.burst_timer = 0.0
        self.burst_dir = Vec2(1, 0)
        self.target_enemy: Optional[Enemy] = None

    def update(
        self,
        dt_effective: float,
        dt_real: float,
        walls: List[pygame.Rect],
        mouse_world_pos: Vec2,
    ) -> None:
        """Update cooldowns, aiming angle, and wall collisions."""
        if not self.is_alive:
            return

        # Aim towards mouse
        aim_diff = mouse_world_pos - self.pos
        if aim_diff.length_squared() > 1:
            self.angle = math.atan2(aim_diff.y, aim_diff.x)

        # Cooldowns update with real time or effective time
        if self.punch_cooldown > 0:
            self.punch_cooldown = max(0.0, self.punch_cooldown - dt_effective)
        if self.hotswitch_cooldown > 0:
            self.hotswitch_cooldown = max(0.0, self.hotswitch_cooldown - dt_real)

        if self.equipped_weapon is not None:
            self.equipped_weapon.update(dt_effective, walls, ParticleSystem())

        # Resolve wall collision
        self.pos = resolve_circle_walls(self.pos, self.radius, walls)

    def move(self, move_dir: Vec2, dt_effective: float, walls: List[pygame.Rect]) -> None:
        """Move player based on directional input."""
        if not self.is_alive or move_dir.length_squared() == 0:
            return
        step = move_dir.normalize() * self.speed * dt_effective
        self.pos += step
        self.pos = resolve_circle_walls(self.pos, self.radius, walls)

    def punch(
        self,
        enemies: List[Enemy],
        weapons_world: List[WeaponItem],
        particles: ParticleSystem,
    ) -> bool:
        """Perform a close-quarters punch. Returns True if hit."""
        if self.punch_cooldown > 0:
            return False

        self.punch_cooldown = PUNCH_COOLDOWN
        hit_any = False
        forward = Vec2(math.cos(self.angle), math.sin(self.angle))

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            to_enemy = enemy.pos - self.pos
            dist = to_enemy.length()
            if dist <= PUNCH_RANGE:
                dot = forward.dot(to_enemy.normalize()) if dist > 0 else 1.0
                if dot > 0.4:  # Facing enemy
                    hit_any = True
                    enemy.take_punch(forward * 200, weapons_world, particles)
                    break

        if hit_any:
            get_audio().play("punch", volume=0.85)
        return hit_any

    def fire_weapon(
        self,
        bullets: List[Bullet],
        enemies: List[Enemy],
        weapons_world: List[WeaponItem],
        particles: ParticleSystem,
    ) -> bool:
        """Fire or swing the currently equipped weapon."""
        if self.equipped_weapon is None:
            # Unarmed punch
            return self.punch(enemies, weapons_world, particles)

        w = self.equipped_weapon
        if w.cooldown > 0:
            return False

        forward = Vec2(math.cos(self.angle), math.sin(self.angle))

        if w.weapon_type == WeaponType.KATANA:
            # Katana slice! Destroys enemy bullets in arc and slices enemies in reach
            w.cooldown = w.fire_rate
            particles.spawn_slash(self.pos + forward * 20, self.angle)
            get_audio().play("katana", volume=0.9)

            # 1. Slice / deflect enemy bullets within 70px in front arc
            for b in bullets:
                if b.owner == "enemy" and b.alive:
                    diff = b.pos - self.pos
                    if diff.length() < 78.0 and forward.dot(diff.normalize()) > 0.3:
                        b.alive = False
                        particles.spawn_sparks(b.pos, -diff.normalize(), count=9, color=(255, 255, 255))
                        get_audio().play("ricochet", volume=0.7)

            # 2. Slice enemies in reach
            for enemy in enemies:
                if enemy.is_alive:
                    diff = enemy.pos - self.pos
                    if diff.length() < 68.0 and forward.dot(diff.normalize()) > 0.4:
                        enemy.kill(forward * 250, particles, weapons_world)

            return True

        if w.ammo <= 0:
            # Empty weapon click
            get_audio().play("catch", volume=0.3)
            return False

        # Fire ranged weapon
        w.cooldown = w.fire_rate
        w.ammo -= 1

        spawn_pos = self.pos + forward * (self.radius + 10)

        if w.weapon_type == WeaponType.PISTOL:
            bullets.append(Bullet(spawn_pos, forward, owner="player"))
            get_audio().play("pistol", volume=0.85)
            particles.spawn_sparks(spawn_pos, forward, count=4, color=(255, 220, 100))

        elif w.weapon_type == WeaponType.SHOTGUN:
            # Spread 7 pellets in cone
            for _ in range(7):
                spread_ang = self.angle + random.uniform(-0.24, 0.24)
                pellet_dir = Vec2(math.cos(spread_ang), math.sin(spread_ang))
                pellet_spd = random.uniform(500, 620)
                bullets.append(Bullet(spawn_pos, pellet_dir, owner="player", speed=pellet_spd))
            get_audio().play("shotgun", volume=1.0)
            particles.spawn_sparks(spawn_pos, forward, count=10, color=(255, 200, 80))

        elif w.weapon_type == WeaponType.RIFLE:
            # Queue 3 round burst
            bullets.append(Bullet(spawn_pos, forward, owner="player"))
            self.burst_bullets_left = 2
            self.burst_timer = 0.06
            self.burst_dir = forward
            get_audio().play("rifle", volume=0.8)
            particles.spawn_sparks(spawn_pos, forward, count=5, color=(255, 210, 90))

        return True

    def update_burst(self, dt_effective: float, bullets: List[Bullet]) -> None:
        """Handle remaining burst bullets for rifle."""
        if self.burst_bullets_left > 0:
            self.burst_timer -= dt_effective
            if self.burst_timer <= 0:
                self.burst_timer = 0.06
                self.burst_bullets_left -= 1
                spread = random.uniform(-0.06, 0.06)
                ang = math.atan2(self.burst_dir.y, self.burst_dir.x) + spread
                d = Vec2(math.cos(ang), math.sin(ang))
                spawn_pos = self.pos + d * (self.radius + 10)
                bullets.append(Bullet(spawn_pos, d, owner="player"))
                get_audio().play("rifle", volume=0.75)

    def throw_weapon(self, weapons_world: List[WeaponItem]) -> bool:
        """Throw the equipped weapon or catch one in the air/floor."""
        # First priority: If a weapon is near in air or on ground and player is unarmed, try catch
        if self.equipped_weapon is None:
            return self.try_catch(weapons_world)

        # Throw currently held weapon
        w = self.equipped_weapon
        w.pos = Vec2(self.pos)
        forward = Vec2(math.cos(self.angle), math.sin(self.angle))
        w.throw(forward, owner="player")
        weapons_world.append(w)
        self.equipped_weapon = None
        return True

    def try_catch(self, weapons_world: List[WeaponItem]) -> bool:
        """Attempt to catch an incoming or nearby weapon."""
        if self.equipped_weapon is not None:
            return False

        best_w = None
        best_dist = 60.0  # Catch radius

        for w in weapons_world:
            if w.picked_up:
                continue
            d = (w.pos - self.pos).length()
            if d < best_dist:
                best_dist = d
                best_w = w

        if best_w is not None:
            best_w.picked_up = True
            best_w.thrown = False
            best_w.vel = Vec2(0, 0)
            self.equipped_weapon = best_w
            get_audio().play("catch", volume=0.8)
            return True
        return False

    def can_hotswitch(self) -> bool:
        """Whether Hotswitch cooldown has completed."""
        return self.hotswitch_cooldown <= 0

    def trigger_hotswitch(
        self,
        enemies: List[Enemy],
        weapons_world: List[WeaponItem],
        particles: ParticleSystem,
        walls: List[pygame.Rect],
    ) -> bool:
        """Perform body-swap into the focused enemy."""
        if not self.can_hotswitch() or self.target_enemy is None:
            return False

        target = self.target_enemy
        if not target.is_alive:
            return False

        # Disintegrate old player body into black/gray crystal shards
        particles.spawn_shatter(self.pos, Vec2(0, 0), count=16, is_red=False)

        # Transfer into enemy position
        self.pos = Vec2(target.pos)
        self.equipped_weapon = target.equipped_weapon
        if self.equipped_weapon is not None:
            self.equipped_weapon.picked_up = True

        # Kill and obliterate enemy target
        target.is_alive = False
        target.equipped_weapon = None
        particles.spawn_shatter(self.pos, Vec2(0, 0), count=22, is_red=True)

        self.hotswitch_cooldown = HOTSWITCH_COOLDOWN
        self.target_enemy = None
        get_audio().play("hotswitch", volume=1.0)
        return True

    def find_hotswitch_target(
        self, enemies: List[Enemy], walls: List[pygame.Rect], mouse_pos: Vec2
    ) -> Optional[Enemy]:
        """Find the enemy closest to cursor with clear line of sight."""
        if not self.can_hotswitch():
            return None

        best_enemy = None
        min_mouse_dist = 140.0  # Must be aiming somewhat near the enemy

        for enemy in enemies:
            if not enemy.is_alive:
                continue
            dist_to_player = (enemy.pos - self.pos).length()
            if dist_to_player > HOTSWITCH_RANGE:
                continue
            if not has_line_of_sight(self.pos, enemy.pos, walls):
                continue

            dist_cursor = (enemy.pos - mouse_pos).length()
            if dist_cursor < min_mouse_dist:
                min_mouse_dist = dist_cursor
                best_enemy = enemy

        return best_enemy

    def draw(self, surface: pygame.Surface) -> None:
        """Render player body, hands, and held weapon."""
        if not self.is_alive:
            return

        rad = self.angle
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        # Hands / Fists
        hand_dist = 14.0
        hand_r = 5.0
        h1 = (
            self.pos.x + 10 * cos_a - hand_dist * sin_a,
            self.pos.y + 10 * sin_a + hand_dist * cos_a,
        )
        h2 = (
            self.pos.x + 10 * cos_a + hand_dist * sin_a,
            self.pos.y + 10 * sin_a - hand_dist * cos_a,
        )
        pygame.draw.circle(surface, COLOR_PLAYER_HANDS, (int(h1[0]), int(h1[1])), int(hand_r))
        pygame.draw.circle(surface, COLOR_PLAYER_HANDS, (int(h2[0]), int(h2[1])), int(hand_r))

        # Main Body Circle
        pygame.draw.circle(surface, COLOR_PLAYER, (int(self.pos.x), int(self.pos.y)), int(self.radius))

        # Visor / Direction notch
        notch = (self.pos.x + self.radius * cos_a, self.pos.y + self.radius * sin_a)
        pygame.draw.circle(surface, (80, 85, 95), (int(notch[0]), int(notch[1])), 4)

        # Held weapon visual
        if self.equipped_weapon is not None:
            w_type = self.equipped_weapon.weapon_type
            w_pos = (self.pos.x + 16 * cos_a, self.pos.y + 16 * sin_a)
            if w_type == WeaponType.KATANA:
                tip = (self.pos.x + 46 * cos_a, self.pos.y + 46 * sin_a)
                pygame.draw.line(surface, COLOR_KATANA_BLADE, w_pos, tip, 3)
            else:
                pygame.draw.circle(surface, COLOR_WEAPON, (int(w_pos[0]), int(w_pos[1])), 5)


class Enemy:
    """A faceted red crystalline enemy with AI sight, aiming telegraph, and weapon handling."""

    def __init__(
        self,
        pos: Vec2,
        weapon_type: Optional[WeaponType] = WeaponType.PISTOL,
        patrol_points: Optional[List[Vec2]] = None,
    ):
        self.pos = Vec2(pos)
        self.angle = random.uniform(0, math.tau)
        self.radius = ENEMY_RADIUS
        self.speed = ENEMY_SPEED
        self.is_alive = True
        self.patrol_points = patrol_points or [Vec2(pos)]
        self.patrol_index = 0
        self.equipped_weapon = WeaponItem(weapon_type, pos) if weapon_type else None
        if self.equipped_weapon:
            self.equipped_weapon.picked_up = True

        # AI States: "patrol", "engage", "stunned"
        self.state = "patrol"
        self.stun_timer = 0.0
        self.aim_timer = 0.0
        self.aim_duration = 0.65  # Telegraph duration before firing
        self.reaction_delay = 0.15
        self.alert_timer = 0.0

    def update(
        self,
        dt_effective: float,
        player: Player,
        walls: List[pygame.Rect],
        bullets: List[Bullet],
        weapons_world: List[WeaponItem],
        particles: ParticleSystem,
    ) -> None:
        """Update AI decisions, navigation, aiming, and shooting."""
        if not self.is_alive:
            return

        if self.equipped_weapon is not None:
            self.equipped_weapon.update(dt_effective, walls, particles)

        # Stun state
        if self.stun_timer > 0:
            self.stun_timer -= dt_effective
            if self.stun_timer <= 0:
                self.state = "patrol"
            return

        if not player.is_alive:
            return

        to_player = player.pos - self.pos
        dist_to_player = to_player.length()
        can_see_player = dist_to_player < 700.0 and has_line_of_sight(self.pos, player.pos, walls)

        # State transition
        if can_see_player:
            self.state = "engage"
        elif self.state == "engage" and not can_see_player:
            self.alert_timer += dt_effective
            if self.alert_timer > 2.0:
                self.state = "patrol"
                self.alert_timer = 0.0

        # State execution
        if self.state == "engage":
            # Rotate smoothly towards player
            target_angle = math.atan2(to_player.y, to_player.x)
            # Angle difference
            diff = (target_angle - self.angle + math.pi) % math.tau - math.pi
            self.angle += diff * min(1.0, 7.0 * dt_effective)

            # Move towards or maintain distance
            preferred_dist = 220.0 if (self.equipped_weapon and self.equipped_weapon.weapon_type != WeaponType.KATANA) else 20.0
            if dist_to_player > preferred_dist + 20:
                move_dir = to_player.normalize()
                self.pos += move_dir * self.speed * dt_effective
            elif dist_to_player < preferred_dist - 30:
                move_dir = -to_player.normalize()
                self.pos += move_dir * self.speed * 0.6 * dt_effective

            # Aiming telegraph and firing
            if can_see_player:
                self.aim_timer += dt_effective
                if self.aim_timer >= self.aim_duration:
                    self.fire(bullets, player, particles, weapons_world)
                    self.aim_timer = random.uniform(-0.3, 0.0)  # Reset with slight delay
            else:
                self.aim_timer = max(0.0, self.aim_timer - dt_effective * 0.5)

        elif self.state == "patrol":
            self.aim_timer = 0.0
            if len(self.patrol_points) > 1:
                target_pt = self.patrol_points[self.patrol_index]
                diff = target_pt - self.pos
                if diff.length() < 16.0:
                    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                else:
                    self.angle = math.atan2(diff.y, diff.x)
                    self.pos += diff.normalize() * (self.speed * 0.5) * dt_effective

        # Wall collisions
        self.pos = resolve_circle_walls(self.pos, self.radius, walls)

        # Check if hit by thrown weapons
        for w in weapons_world:
            if w.thrown and (w.pos - self.pos).length() < (self.radius + 14.0):
                # Lethal thrown weapon impact!
                w.thrown = False
                w.vel = Vec2(0, 0)
                self.kill(w.vel, particles, weapons_world)
                get_audio().play("punch", volume=1.0)
                break

    def fire(
        self,
        bullets: List[Bullet],
        player: Player,
        particles: ParticleSystem,
        weapons_world: List[WeaponItem],
    ) -> None:
        """Enemy fires their weapon at the player."""
        if not self.is_alive or not player.is_alive:
            return

        forward = Vec2(math.cos(self.angle), math.sin(self.angle))

        if self.equipped_weapon is None:
            # Unarmed enemy charges to punch
            if (player.pos - self.pos).length() <= PUNCH_RANGE + 10:
                player.is_alive = False
                particles.spawn_shatter(player.pos, forward * 200, count=18, is_red=False)
                get_audio().play("punch", volume=1.0)
            return

        w = self.equipped_weapon
        spawn_pos = self.pos + forward * (self.radius + 10)

        # Slight enemy aim inaccuracy
        aim_err = random.uniform(-0.08, 0.08)
        ang = self.angle + aim_err
        bullet_dir = Vec2(math.cos(ang), math.sin(ang))

        if w.weapon_type == WeaponType.PISTOL:
            bullets.append(Bullet(spawn_pos, bullet_dir, owner="enemy"))
            get_audio().play("pistol", volume=0.8)
            particles.spawn_sparks(spawn_pos, bullet_dir, count=4, color=(255, 120, 60))

        elif w.weapon_type == WeaponType.SHOTGUN:
            for _ in range(5):
                pellet_ang = ang + random.uniform(-0.25, 0.25)
                p_dir = Vec2(math.cos(pellet_ang), math.sin(pellet_ang))
                bullets.append(Bullet(spawn_pos, p_dir, owner="enemy", speed=random.uniform(460, 560)))
            get_audio().play("shotgun", volume=0.9)
            particles.spawn_sparks(spawn_pos, bullet_dir, count=8, color=(255, 120, 60))

        elif w.weapon_type == WeaponType.RIFLE:
            bullets.append(Bullet(spawn_pos, bullet_dir, owner="enemy"))
            get_audio().play("rifle", volume=0.75)
            particles.spawn_sparks(spawn_pos, bullet_dir, count=4, color=(255, 120, 60))

        elif w.weapon_type == WeaponType.KATANA:
            if (player.pos - self.pos).length() <= 55.0:
                player.is_alive = False
                particles.spawn_slash(self.pos + forward * 20, self.angle)
                particles.spawn_shatter(player.pos, forward * 220, count=18, is_red=False)
                get_audio().play("katana", volume=1.0)

    def take_punch(
        self,
        impact_dir: Vec2,
        weapons_world: List[WeaponItem],
        particles: ParticleSystem,
    ) -> None:
        """Handle being punched: drops weapon flying out and enters stunned state."""
        self.stun_timer = 2.4
        self.state = "stunned"
        self.aim_timer = 0.0

        if self.equipped_weapon is not None:
            w = self.equipped_weapon
            w.picked_up = False
            w.pos = Vec2(self.pos)
            w.throw(impact_dir + Vec2(random.uniform(-50, 50), random.uniform(-50, 50)), owner="player")
            weapons_world.append(w)
            self.equipped_weapon = None

        particles.spawn_sparks(self.pos, impact_dir.normalize(), count=6, color=(255, 100, 100))

    def kill(
        self,
        impact_vel: Vec2,
        particles: ParticleSystem,
        weapons_world: List[WeaponItem],
    ) -> None:
        """Enemy shatters into crystal shards upon death."""
        if not self.is_alive:
            return

        self.is_alive = False
        get_audio().play("shatter", volume=0.85)

        # Drop weapon
        if self.equipped_weapon is not None:
            w = self.equipped_weapon
            w.picked_up = False
            w.pos = Vec2(self.pos)
            w.vel = impact_vel * 0.4 + Vec2(random.uniform(-40, 40), random.uniform(-40, 40))
            weapons_world.append(w)
            self.equipped_weapon = None

        # Burst of crystal polygon shards
        particles.spawn_shatter(self.pos, impact_vel, count=20, is_red=True)

    def draw(self, surface: pygame.Surface, is_hotswitch_target: bool = False) -> None:
        """Render faceted red crystal enemy."""
        if not self.is_alive:
            return

        rad = self.angle
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        color_body = COLOR_ENEMY_STUN if self.state == "stunned" else COLOR_ENEMY

        # Draw red laser pointer line when aiming at player
        if self.state == "engage" and self.aim_timer > 0.15:
            laser_len = 500.0
            p_end = (
                self.pos.x + laser_len * cos_a,
                self.pos.y + laser_len * sin_a,
            )
            laser_alpha = min(220, int(255 * (self.aim_timer / self.aim_duration)))
            laser_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.line(laser_surf, (255, 30, 40, laser_alpha), (self.pos.x, self.pos.y), p_end, 1)
            surface.blit(laser_surf, (0, 0))

        # Faceted crystalline shoulders (polygonal points)
        pts = [
            (self.pos.x + 16 * cos_a, self.pos.y + 16 * sin_a),
            (self.pos.x + 4 * cos_a - 14 * sin_a, self.pos.y + 4 * sin_a + 14 * cos_a),
            (self.pos.x - 14 * cos_a - 10 * sin_a, self.pos.y - 14 * sin_a + 10 * cos_a),
            (self.pos.x - 14 * cos_a + 10 * sin_a, self.pos.y - 14 * sin_a - 10 * cos_a),
            (self.pos.x + 4 * cos_a + 14 * sin_a, self.pos.y + 4 * sin_a - 14 * cos_a),
        ]
        pygame.draw.polygon(surface, color_body, pts)
        pygame.draw.polygon(surface, COLOR_ENEMY_ACCENT, pts, 2)

        # Facet center head
        head_pos = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surface, (255, 80, 90), head_pos, int(self.radius * 0.55))

        # Held weapon
        if self.equipped_weapon is not None:
            w_pos = (self.pos.x + 16 * cos_a, self.pos.y + 16 * sin_a)
            pygame.draw.circle(surface, COLOR_WEAPON, (int(w_pos[0]), int(w_pos[1])), 4)

        # Stun stars if stunned
        if self.state == "stunned":
            pygame.draw.circle(surface, (255, 230, 100), (int(self.pos.x), int(self.pos.y - 20)), 3)

        # Hotswitch focus reticle
        if is_hotswitch_target:
            pygame.draw.circle(surface, COLOR_HOTSWITCH_TARGET, (int(self.pos.x), int(self.pos.y)), int(self.radius + 14), 2)
            pygame.draw.circle(surface, COLOR_HOTSWITCH_TARGET, (int(self.pos.x), int(self.pos.y)), 4)
