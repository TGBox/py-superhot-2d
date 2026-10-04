"""Replay recording, playback engine, and the iconic 'SUPER. HOT.' victory chant."""

from __future__ import annotations
import math
from typing import List, Tuple, Dict, Any, Optional
import pygame

from py_superhot_2d.config import (
    COLOR_BG,
    COLOR_BG_GRID,
    COLOR_WALL,
    COLOR_WALL_BORDER,
    COLOR_PLAYER,
    COLOR_PLAYER_HANDS,
    COLOR_ENEMY,
    COLOR_ENEMY_ACCENT,
    COLOR_ENEMY_STUN,
    COLOR_WEAPON,
    COLOR_KATANA_BLADE,
    COLOR_BULLET_PLAYER,
    COLOR_BULLET_ENEMY,
    COLOR_BULLET_CORE,
    COLOR_TRAIL_PLAYER,
    COLOR_TRAIL_ENEMY,
    COLOR_UI_TEXT_RED,
    COLOR_UI_TEXT_DARK,
    TEXT_TITLE_SUPER,
    TEXT_TITLE_HOT,
    TEXT_REPLAY_HINT,
)
from py_superhot_2d.math_utils import Vec2
from py_superhot_2d.audio import get_audio


class FrameSnapshot:
    """A lightweight serialized representation of a single simulation frame."""

    __slots__ = (
        "player_pos",
        "player_ang",
        "player_alive",
        "player_weapon",
        "enemies",
        "bullets",
        "weapons",
        "shards",
    )

    def __init__(
        self,
        player_pos: Tuple[float, float],
        player_ang: float,
        player_alive: bool,
        player_weapon: Optional[str],
        enemies: List[Tuple[float, float, float, bool, Optional[str], bool]],
        bullets: List[Tuple[float, float, str, List[Tuple[float, float]]]],
        weapons: List[Tuple[float, float, float, str, bool]],
        shards: List[Tuple[float, float, float, Tuple[int, int, int], List[Tuple[float, float]]]],
    ):
        self.player_pos = player_pos
        self.player_ang = player_ang
        self.player_alive = player_alive
        self.player_weapon = player_weapon
        self.enemies = enemies
        self.bullets = bullets
        self.weapons = weapons
        self.shards = shards


class ReplaySystem:
    """Records gameplay snapshots and plays them back in real time with the SUPERHOT chant."""

    def __init__(self):
        self.frames: List[FrameSnapshot] = []
        self.recording = False
        self.playback_index = 0
        self.playback_timer = 0.0
        self.beat_timer = 0.0
        self.beat_phase = 0  # 0 = "SUPER", 1 = "HOT"
        self.font_huge: Optional[pygame.font.Font] = None
        self.font_hint: Optional[pygame.font.Font] = None

    def start_recording(self) -> None:
        """Clear buffer and begin recording."""
        self.frames.clear()
        self.recording = True

    def record_frame(
        self,
        player,
        enemies,
        bullets,
        weapons_world,
        particles,
    ) -> None:
        """Capture active scene state into replay buffer."""
        if not self.recording:
            return

        p_pos = (player.pos.x, player.pos.y)
        p_ang = player.angle
        p_alive = player.is_alive
        p_weap = player.equipped_weapon.weapon_type.value if player.equipped_weapon else None

        # Enemies: (x, y, ang, is_alive, weapon_type_str, is_stunned)
        e_list = []
        for e in enemies:
            e_w = e.equipped_weapon.weapon_type.value if e.equipped_weapon else None
            e_list.append((e.pos.x, e.pos.y, e.angle, e.is_alive, e_w, e.state == "stunned"))

        # Bullets: (x, y, owner, [(tx, ty), ...])
        b_list = []
        for b in bullets:
            if b.alive:
                trails = [(t.x, t.y) for t in b.trail]
                b_list.append((b.pos.x, b.pos.y, b.owner, trails))

        # Weapons on ground/air: (x, y, rotation, weapon_type_str, thrown)
        w_list = []
        for w in weapons_world:
            if not w.picked_up:
                w_list.append((w.pos.x, w.pos.y, w.rotation, w.weapon_type.value, w.thrown))

        # Shards
        s_list = []
        for s in particles.shards:
            pts = [(p.x, p.y) for p in s.base_points]
            s_list.append((s.pos.x, s.pos.y, s.rotation, s.color, pts))

        self.frames.append(
            FrameSnapshot(
                player_pos=p_pos,
                player_ang=p_ang,
                player_alive=p_alive,
                player_weapon=p_weap,
                enemies=e_list,
                bullets=b_list,
                weapons=w_list,
                shards=s_list,
            )
        )

    def start_playback(self) -> None:
        """Switch from recording to playback loop."""
        self.recording = False
        self.playback_index = 0
        self.playback_timer = 0.0
        self.beat_timer = 0.0
        self.beat_phase = 0

        # Lazy init fonts
        if self.font_huge is None:
            self.font_huge = pygame.font.Font(None, 110)
            self.font_hint = pygame.font.Font(None, 28)

    def update_playback(self, dt: float) -> None:
        """Step playback frame at fast, thrilling real-time speed."""
        if not self.frames:
            return

        playback_speed = 1.15  # Fast-paced action movie speed
        self.playback_timer += dt * playback_speed
        frame_duration = 1.0 / 60.0

        while self.playback_timer >= frame_duration:
            self.playback_timer -= frame_duration
            self.playback_index = (self.playback_index + 1) % len(self.frames)

        # Rhythmic SUPER... HOT... chant pulse (every 0.45s)
        self.beat_timer += dt * playback_speed
        if self.beat_timer >= 0.45:
            self.beat_timer = 0.0
            self.beat_phase = 1 - self.beat_phase
            get_audio().play("beat", volume=0.9)

    def draw_playback(self, surface: pygame.Surface, walls: List[pygame.Rect]) -> None:
        """Render the recorded frame snapshot along with the pulsing victory overlay."""
        if not self.frames or self.playback_index >= len(self.frames):
            return

        frame = self.frames[self.playback_index]

        # 1. Floor
        surface.fill(COLOR_BG)
        for x in range(0, surface.get_width(), 48):
            pygame.draw.line(surface, COLOR_BG_GRID, (x, 0), (x, surface.get_height()), 1)
        for y in range(0, surface.get_height(), 48):
            pygame.draw.line(surface, COLOR_BG_GRID, (0, y), (surface.get_width(), y), 1)

        # 2. Walls
        for wall in walls:
            pygame.draw.rect(surface, COLOR_WALL, wall)
            pygame.draw.rect(surface, COLOR_WALL_BORDER, wall, 2)

        # 3. Weapons
        for wx, wy, wrot, wtype, wthrown in frame.weapons:
            rad = math.radians(wrot)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            pts = [
                (wx - 8 * cos_a + 3 * sin_a, wy - 8 * sin_a - 3 * cos_a),
                (wx + 10 * cos_a + 3 * sin_a, wy + 10 * sin_a - 3 * cos_a),
                (wx + 10 * cos_a - 3 * sin_a, wy + 10 * sin_a + 3 * cos_a),
                (wx - 8 * cos_a - 3 * sin_a, wy - 8 * sin_a + 3 * cos_a),
            ]
            pygame.draw.polygon(surface, COLOR_WEAPON, pts)

        # 4. Shards
        for sx, sy, srot, scol, base_pts in frame.shards:
            rad = math.radians(srot)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            pts = []
            for bx, by in base_pts:
                rx = bx * cos_a - by * sin_a + sx
                ry = bx * sin_a + by * cos_a + sy
                pts.append((rx, ry))
            if len(pts) >= 3:
                pygame.draw.polygon(surface, scol, pts)

        # 5. Bullets
        for bx, by, bowner, trails in frame.bullets:
            col = COLOR_BULLET_ENEMY if bowner == "enemy" else COLOR_BULLET_PLAYER
            if len(trails) > 1:
                t_col = COLOR_TRAIL_ENEMY if bowner == "enemy" else COLOR_TRAIL_PLAYER
                for i in range(len(trails) - 1):
                    pygame.draw.line(surface, t_col, trails[i], trails[i + 1], 3)
            pygame.draw.circle(surface, col, (int(bx), int(by)), 4)
            pygame.draw.circle(surface, COLOR_BULLET_CORE, (int(bx), int(by)), 2)

        # 6. Enemies
        for ex, ey, eang, ealive, eweap, estun in frame.enemies:
            if not ealive:
                continue
            cos_a, sin_a = math.cos(eang), math.sin(eang)
            pts = [
                (ex + 16 * cos_a, ey + 16 * sin_a),
                (ex + 4 * cos_a - 14 * sin_a, ey + 4 * sin_a + 14 * cos_a),
                (ex - 14 * cos_a - 10 * sin_a, ey - 14 * sin_a + 10 * cos_a),
                (ex - 14 * cos_a + 10 * sin_a, ey - 14 * sin_a - 10 * cos_a),
                (ex + 4 * cos_a + 14 * sin_a, ey + 4 * sin_a - 14 * cos_a),
            ]
            c = COLOR_ENEMY_STUN if estun else COLOR_ENEMY
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.polygon(surface, COLOR_ENEMY_ACCENT, pts, 2)
            pygame.draw.circle(surface, (255, 80, 90), (int(ex), int(ey)), 9)

        # 7. Player
        if frame.player_alive:
            px, py = frame.player_pos
            pang = frame.player_ang
            cos_a, sin_a = math.cos(pang), math.sin(pang)
            pygame.draw.circle(surface, COLOR_PLAYER_HANDS, (int(px + 10 * cos_a - 14 * sin_a), int(py + 10 * sin_a + 14 * cos_a)), 5)
            pygame.draw.circle(surface, COLOR_PLAYER_HANDS, (int(px + 10 * cos_a + 14 * sin_a), int(py + 10 * sin_a - 14 * cos_a)), 5)
            pygame.draw.circle(surface, COLOR_PLAYER, (int(px), int(py)), 16)
            pygame.draw.circle(surface, (80, 85, 95), (int(px + 16 * cos_a), int(py + 16 * sin_a)), 4)

        # 8. SUPER. HOT. Pulsing Typography Banner
        if self.font_huge:
            word = TEXT_TITLE_SUPER if self.beat_phase == 0 else TEXT_TITLE_HOT
            word_color = COLOR_UI_TEXT_RED if self.beat_phase == 0 else COLOR_UI_TEXT_DARK

            # Pulse scale
            scale_factor = 1.0 + 0.12 * math.sin(self.beat_timer * math.pi / 0.55)
            txt_surf = self.font_huge.render(word, True, word_color)

            # Center on screen
            cx, cy = surface.get_width() // 2, surface.get_height() // 2
            sw = int(txt_surf.get_width() * scale_factor)
            sh = int(txt_surf.get_height() * scale_factor)
            scaled = pygame.transform.smoothscale(txt_surf, (sw, sh))
            rect = scaled.get_rect(center=(cx, cy - 30))
            surface.blit(scaled, rect)

        # 9. Control Hints
        if self.font_hint:
            hint_surf = self.font_hint.render(TEXT_REPLAY_HINT, True, (60, 64, 75))
            rect = hint_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() - 48))
            surface.blit(hint_surf, rect)
