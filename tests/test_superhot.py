"""Comprehensive unit tests for Superhot 2D core systems."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import math
import pytest
import pygame
from py_superhot_2d.math_utils import (
    Vec2,
    distance,
    clamp,
    lerp,
    line_segment_intersection,
    ray_cast_rect,
    has_line_of_sight,
    circle_rect_collision,
    resolve_circle_walls,
    cast_vision_cone_polygon,
)
from py_superhot_2d.weapons import Bullet, WeaponItem, WeaponType
from py_superhot_2d.particles import ParticleSystem
from py_superhot_2d.entities import Player, Enemy
from py_superhot_2d.replay import ReplaySystem


@pytest.fixture(scope="session", autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


class TestMathUtils:
    def test_distance(self):
        p1 = Vec2(0, 0)
        p2 = Vec2(3, 4)
        assert distance(p1, p2) == pytest.approx(5.0)

    def test_clamp_and_lerp(self):
        assert clamp(15.0, 0.0, 10.0) == 10.0
        assert clamp(-5.0, 0.0, 10.0) == 0.0
        assert clamp(5.0, 0.0, 10.0) == 5.0
        assert lerp(10.0, 20.0, 0.5) == 15.0

    def test_line_intersection(self):
        p1 = Vec2(0, 0)
        p2 = Vec2(10, 10)
        p3 = Vec2(0, 10)
        p4 = Vec2(10, 0)
        res = line_segment_intersection(p1, p2, p3, p4)
        assert res is not None
        pt, t = res
        assert pt.x == pytest.approx(5.0)
        assert pt.y == pytest.approx(5.0)
        assert t == pytest.approx(0.5)

    def test_ray_cast_rect(self):
        start = Vec2(0, 50)
        end = Vec2(100, 50)
        rect = pygame.Rect(40, 20, 20, 60)
        hit = ray_cast_rect(start, end, rect)
        assert hit is not None
        hit_pt, t, normal = hit
        assert hit_pt.x == pytest.approx(40.0)
        assert hit_pt.y == pytest.approx(50.0)
        assert t == pytest.approx(0.4)
        assert normal.x == -1.0

    def test_line_of_sight(self):
        p1 = Vec2(10, 50)
        p2 = Vec2(100, 50)
        wall = pygame.Rect(40, 20, 20, 60)
        assert not has_line_of_sight(p1, p2, [wall])

        # Clear line of sight when wall is elsewhere
        wall_clear = pygame.Rect(40, 120, 20, 60)
        assert has_line_of_sight(p1, p2, [wall_clear])

    def test_circle_rect_collision(self):
        circle_pos = Vec2(45, 50)
        radius = 10.0
        rect = pygame.Rect(50, 20, 50, 60)  # Circle penetrates left edge by 5px
        push = circle_rect_collision(circle_pos, radius, rect)
        assert push is not None
        assert push.x < 0  # Should push to the left away from rect

    def test_vision_cone_polygon(self):
        origin = Vec2(100, 100)
        facing = 0.0  # Facing right (+x)
        wall = pygame.Rect(200, 50, 40, 100)  # Wall directly in front
        pts = cast_vision_cone_polygon(origin, facing, fov_deg=60.0, max_range=300.0, walls=[wall], num_rays=12)
        assert len(pts) == 14  # origin + 12 rays + 1
        # The center ray hits wall at x=200
        center_pt = pts[7]
        assert center_pt[0] == pytest.approx(200.0)


class TestWeaponsAndCombat:
    def test_punch_animation_and_cooldown(self):
        player = Player(Vec2(100, 100))
        assert player.get_punch_cooldown_progress() == 1.0
        assert player.punch_anim_timer == 0.0

        # Punch empty air
        player.punch([], [], ParticleSystem())
        assert player.punch_anim_timer > 0.0
        assert player.get_punch_cooldown_progress() < 1.0

        # Update 0.1s real time
        player.update(0.01, 0.1, [], Vec2(200, 100))
        assert player.punch_anim_timer < 0.16

    def test_bullet_wall_collision(self):
        particles = ParticleSystem()
        wall = pygame.Rect(100, 0, 50, 200)
        b = Bullet(Vec2(50, 50), Vec2(1, 0), owner="player", speed=500)

        # Step 0.2s -> moves 100px, hitting wall
        alive = b.update(0.2, [wall], particles)
        assert not alive
        assert not b.alive
        assert len(particles.sparks) > 0

    def test_weapon_throw_and_catch(self):
        particles = ParticleSystem()
        w = WeaponItem(WeaponType.PISTOL, Vec2(50, 50), ammo=6)
        w.throw(Vec2(1, 0), owner="player")
        assert w.thrown
        assert w.vel.x > 0

        # Update physics
        w.update(0.1, [], particles)
        assert w.pos.x > 50

        # Player catches weapon
        player = Player(Vec2(w.pos.x, w.pos.y))
        assert player.equipped_weapon is None
        caught = player.try_catch([w])
        assert caught
        assert player.equipped_weapon is w
        assert not w.thrown

    def test_player_punch_disarm(self):
        player = Player(Vec2(100, 100))
        player.angle = 0.0  # Facing right (+x)
        enemy = Enemy(Vec2(130, 100), weapon_type=WeaponType.PISTOL)
        weapons_world = []
        particles = ParticleSystem()

        hit = player.punch([enemy], weapons_world, particles)
        assert hit
        assert enemy.state == "stunned"
        assert enemy.equipped_weapon is None
        assert len(weapons_world) == 1
        assert weapons_world[0].thrown  # Weapon knocked flying

    def test_katana_bullet_slice(self):
        player = Player(Vec2(100, 100))
        player.angle = 0.0  # Facing right
        player.equipped_weapon = WeaponItem(WeaponType.KATANA, Vec2(100, 100))

        # Enemy bullet heading towards player
        incoming_bullet = Bullet(Vec2(140, 100), Vec2(-1, 0), owner="enemy")
        bullets = [incoming_bullet]
        particles = ParticleSystem()

        player.fire_weapon(bullets, [], [], particles)
        assert not incoming_bullet.alive  # Bullet sliced in half!
        assert len(particles.slashes) == 1


class TestEntitiesAndHotswitch:
    def test_hotswitch_swap(self):
        player = Player(Vec2(100, 100))
        player.equipped_weapon = WeaponItem(WeaponType.PISTOL, Vec2(100, 100), ammo=2)
        enemy = Enemy(Vec2(300, 100), weapon_type=WeaponType.SHOTGUN)
        particles = ParticleSystem()
        weapons_world = []

        # Find hotswitch target
        target = player.find_hotswitch_target([enemy], [], Vec2(300, 100))
        assert target is enemy

        player.target_enemy = enemy
        success = player.trigger_hotswitch([enemy], weapons_world, particles, [])
        assert success
        assert player.pos.x == pytest.approx(300.0)
        assert player.pos.y == pytest.approx(100.0)
        assert player.equipped_weapon.weapon_type == WeaponType.SHOTGUN
        assert not enemy.is_alive
        assert not player.can_hotswitch()  # On cooldown


class TestReplaySystem:
    def test_replay_record_and_playback(self):
        replay = ReplaySystem()
        replay.start_recording()

        player = Player(Vec2(100, 100))
        enemies = [Enemy(Vec2(200, 200), weapon_type=WeaponType.PISTOL)]
        bullets = []
        weapons = []
        particles = ParticleSystem()

        replay.record_frame(player, enemies, bullets, weapons, particles)
        assert len(replay.frames) == 1

        replay.start_playback()
        assert not replay.recording
        assert replay.playback_index == 0

        # Step playback
        replay.update_playback(0.02)
        assert replay.playback_index == 0
