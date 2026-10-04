"""Main game engine, loop coordinator, time dilation controller, and state machine."""

from __future__ import annotations
import math
import random
import sys
from typing import List, Optional, Tuple
import pygame

from py_superhot_2d.config import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    TARGET_FPS,
    TITLE,
    TIME_SCALE_BASE,
    TIME_SCALE_MAX,
    TIME_RAMP_UP_SPEED,
    TIME_RAMP_DOWN_SPEED,
    MOUSE_TIME_WEIGHT,
    ACTION_BURST_DURATION,
    COLOR_BG,
    COLOR_BG_GRID,
    COLOR_WALL,
    COLOR_WALL_BORDER,
    COLOR_WALL_SHADOW,
    COLOR_UI_TEXT_DARK,
    COLOR_UI_TEXT_RED,
    TEXT_TITLE_SUPER,
    TEXT_TITLE_HOT,
    TEXT_SUBTITLE,
    TEXT_BTN_CAMPAIGN,
    TEXT_BTN_ENDLESS,
    TEXT_BTN_CONTROLS,
    TEXT_BTN_SETTINGS,
    TEXT_BTN_QUIT,
    TEXT_BTN_CONTINUE,
    TEXT_BTN_RESTART,
    TEXT_BTN_MENU,
    TEXT_CONTROLS_TITLE,
    TEXT_CONTROLS_WASD,
    TEXT_CONTROLS_MOUSE,
    TEXT_CONTROLS_LMB,
    TEXT_CONTROLS_RMB,
    TEXT_CONTROLS_HOTSWITCH,
    TEXT_CONTROLS_FULLSCREEN,
    TEXT_CONTROLS_RESTART,
    TEXT_CONTROLS_PAUSE,
    TEXT_SETTINGS_TITLE,
    TEXT_SETTINGS_FULLSCREEN,
    TEXT_SETTINGS_ON,
    TEXT_SETTINGS_OFF,
    TEXT_SETTINGS_SOUND,
    TEXT_SETTINGS_BACK,
)
from py_superhot_2d.math_utils import Vec2
from py_superhot_2d.audio import get_audio
from py_superhot_2d.particles import ParticleSystem
from py_superhot_2d.weapons import WeaponItem, WeaponType, Bullet
from py_superhot_2d.entities import Player, Enemy
from py_superhot_2d.levels import CAMPAIGN_LEVELS, get_endless_arena, LevelData
from py_superhot_2d.replay import ReplaySystem
from py_superhot_2d.ui import UIManager, Button


class GameEngine:
    """Core Game Manager coordinating state transitions, physics, time dilation, and render loops."""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption(TITLE)

        # Base Virtual Surface (fixed 1280x720 canvas)
        self.vw = DEFAULT_WINDOW_WIDTH
        self.vh = DEFAULT_WINDOW_HEIGHT
        self.virtual_surface = pygame.Surface((self.vw, self.vh))

        # Real Window Screen
        self.screen = pygame.display.set_mode((self.vw, self.vh), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Systems
        self.audio = get_audio()
        self.particles = ParticleSystem()
        self.replay = ReplaySystem()
        self.ui = UIManager(self.screen)

        # Time Dilation
        self.current_time_scale = TIME_SCALE_BASE
        self.target_time_scale = TIME_SCALE_BASE
        self.action_burst_timer = 0.0

        # State: "menu", "controls", "settings", "playing", "game_over", "replay", "campaign_win", "pause"
        self.state = "menu"
        self.is_endless = False
        self.current_level_idx = 0

        # Gameplay Entities
        self.player: Player = Player(Vec2(self.vw // 2, self.vh // 2))
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.weapons_world: List[WeaponItem] = []
        self.walls: List[pygame.Rect] = []

        # Endless Mode Metrics
        self.endless_wave = 1
        self.endless_kills = 0
        self.wave_spawn_timer = 0.0

        # Mouse tracking
        self.prev_mouse_pos = Vec2(pygame.mouse.get_pos())
        self.mouse_world = Vec2(self.prev_mouse_pos)

        # Setup Menus
        self._init_menus()

    def _init_menus(self) -> None:
        """Create buttons for main menu, settings, controls, and pause screens."""
        btn_w, btn_h = 280, 50
        cx = self.vw // 2 - btn_w // 2

        # Main Menu Buttons
        self.main_menu_buttons = [
            Button(pygame.Rect(cx, 270, btn_w, btn_h), TEXT_BTN_CAMPAIGN, self.start_campaign, self.ui.font_btn),
            Button(pygame.Rect(cx, 335, btn_w, btn_h), TEXT_BTN_ENDLESS, self.start_endless, self.ui.font_btn),
            Button(pygame.Rect(cx, 400, btn_w, btn_h), TEXT_BTN_CONTROLS, lambda: self.set_state("controls"), self.ui.font_btn),
            Button(pygame.Rect(cx, 465, btn_w, btn_h), TEXT_BTN_SETTINGS, lambda: self.set_state("settings"), self.ui.font_btn),
            Button(pygame.Rect(cx, 530, btn_w, btn_h), TEXT_BTN_QUIT, self.quit_game, self.ui.font_btn),
        ]

        # Settings Buttons
        self.settings_buttons = [
            Button(
                pygame.Rect(cx, 280, btn_w, btn_h),
                f"{TEXT_SETTINGS_FULLSCREEN}: {'AN' if self.ui.is_fullscreen else 'AUS'}",
                self._toggle_fullscreen_menu,
                self.ui.font_btn,
            ),
            Button(
                pygame.Rect(cx, 350, btn_w, btn_h),
                f"{TEXT_SETTINGS_SOUND}: {'AN' if self.audio.enabled else 'AUS'}",
                self._toggle_sound_menu,
                self.ui.font_btn,
            ),
            Button(pygame.Rect(cx, 460, btn_w, btn_h), TEXT_SETTINGS_BACK, lambda: self.set_state("menu"), self.ui.font_btn),
        ]

        # Controls Screen Back Button
        self.controls_back_button = Button(
            pygame.Rect(cx, 550, btn_w, btn_h), TEXT_SETTINGS_BACK, lambda: self.set_state("menu"), self.ui.font_btn
        )

        # Pause Screen Buttons
        self.pause_buttons = [
            Button(pygame.Rect(cx, 280, btn_w, btn_h), TEXT_BTN_CONTINUE, lambda: self.set_state("playing"), self.ui.font_btn),
            Button(pygame.Rect(cx, 350, btn_w, btn_h), TEXT_BTN_RESTART, self.restart_level, self.ui.font_btn),
            Button(pygame.Rect(cx, 420, btn_w, btn_h), TEXT_BTN_MENU, lambda: self.set_state("menu"), self.ui.font_btn),
        ]

    def _toggle_fullscreen_menu(self) -> None:
        self.ui.toggle_fullscreen()
        self.screen = self.ui.display_surface
        self.settings_buttons[0].text = f"{TEXT_SETTINGS_FULLSCREEN}: {'AN' if self.ui.is_fullscreen else 'AUS'}"

    def _toggle_sound_menu(self) -> None:
        enabled = self.audio.toggle()
        self.settings_buttons[1].text = f"{TEXT_SETTINGS_SOUND}: {'AN' if enabled else 'AUS'}"

    def set_state(self, new_state: str) -> None:
        """Switch game state."""
        self.state = new_state
        if new_state == "settings":
            self.settings_buttons[0].text = f"{TEXT_SETTINGS_FULLSCREEN}: {'AN' if self.ui.is_fullscreen else 'AUS'}"
            self.settings_buttons[1].text = f"{TEXT_SETTINGS_SOUND}: {'AN' if self.audio.enabled else 'AUS'}"

    def quit_game(self) -> None:
        self.running = False

    def start_campaign(self) -> None:
        """Start campaign from Level 1."""
        self.is_endless = False
        self.current_level_idx = 0
        self.load_level(CAMPAIGN_LEVELS[self.current_level_idx]())

    def start_endless(self) -> None:
        """Start Endless Survival mode."""
        self.is_endless = True
        self.endless_wave = 1
        self.endless_kills = 0
        self.wave_spawn_timer = 0.0
        self.load_level(get_endless_arena())

    def load_level(self, level: LevelData) -> None:
        """Initialize all level components, spawns, and begin replay recording."""
        self.walls = level.walls
        self.player = Player(level.player_start)
        if level.player_weapon is not None:
            w = WeaponItem(level.player_weapon, level.player_start)
            w.picked_up = True
            self.player.equipped_weapon = w

        self.enemies = level.enemies
        self.weapons_world = level.weapons
        self.bullets = []
        self.particles.clear()
        self.replay.start_recording()

        self.current_time_scale = TIME_SCALE_BASE
        self.target_time_scale = TIME_SCALE_BASE
        self.action_burst_timer = 0.0

        self.ui.show_card(level.name, level.subtitle)
        self.state = "playing"

    def restart_level(self) -> None:
        """Restart the current level."""
        if self.is_endless:
            self.start_endless()
        else:
            self.load_level(CAMPAIGN_LEVELS[self.current_level_idx]())

    def advance_level(self) -> None:
        """Advance to next campaign level or display victory screen."""
        if self.is_endless:
            self.restart_level()
            return

        self.current_level_idx += 1
        if self.current_level_idx < len(CAMPAIGN_LEVELS):
            self.load_level(CAMPAIGN_LEVELS[self.current_level_idx]())
        else:
            self.state = "campaign_win"

    def _screen_to_virtual_mouse(self, screen_mouse_pos: Tuple[int, int]) -> Vec2:
        """Convert real window mouse coordinates to 1280x720 virtual canvas coordinates."""
        sw, sh = self.screen.get_width(), self.screen.get_height()
        scale_x = sw / self.vw
        scale_y = sh / self.vh
        scale = min(scale_x, scale_y)

        # Offsets due to letterboxing
        render_w = self.vw * scale
        render_h = self.vh * scale
        offset_x = (sw - render_w) / 2
        offset_y = (sh - render_h) / 2

        vx = (screen_mouse_pos[0] - offset_x) / scale
        vy = (screen_mouse_pos[1] - offset_y) / scale
        return Vec2(max(0, min(self.vw, vx)), max(0, min(self.vh, vy)))

    def handle_events(self) -> None:
        """Handle keyboard, mouse, and system events."""
        raw_mouse = pygame.mouse.get_pos()
        self.mouse_world = self._screen_to_virtual_mouse(raw_mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # F11: Global Fullscreen Toggle at any time
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self._toggle_fullscreen_menu()

            # State-specific event handling
            if self.state == "menu":
                for btn in self.main_menu_buttons:
                    btn.handle_event(event)

            elif self.state == "settings":
                for btn in self.settings_buttons:
                    btn.handle_event(event)

            elif self.state == "controls":
                self.controls_back_button.handle_event(event)

            elif self.state == "pause":
                for btn in self.pause_buttons:
                    btn.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.set_state("playing")

            elif self.state == "game_over":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.restart_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.set_state("menu")

            elif self.state == "replay":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.advance_level()
                    elif event.key == pygame.K_r:
                        self.restart_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.set_state("menu")

            elif self.state == "campaign_win":
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    self.set_state("menu")

            elif self.state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.set_state("pause")
                    elif event.key == pygame.K_r:
                        self.restart_level()
                    elif event.key in (pygame.K_e, pygame.K_SPACE):
                        # HOTSWITCH body swap
                        if self.player.trigger_hotswitch(self.enemies, self.weapons_world, self.particles, self.walls):
                            self.action_burst_timer = ACTION_BURST_DURATION * 1.5

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Left Click: Fire or Punch
                        if self.player.fire_weapon(self.bullets, self.enemies, self.weapons_world, self.particles):
                            self.action_burst_timer = ACTION_BURST_DURATION
                    elif event.button == 3:
                        # Right Click: Throw held weapon or Catch nearby weapon
                        if self.player.throw_weapon(self.weapons_world):
                            self.action_burst_timer = ACTION_BURST_DURATION

    def update_time_dilation(self, dt_real: float) -> float:
        """
        Calculate current time scale factor based on:
        - Movement keys (WASD)
        - Mouse aim velocity
        - Action bursts (firing, punching, throwing)
        Returns effective delta time.
        """
        keys = pygame.key.get_pressed()
        move_input = any([
            keys[pygame.K_w], keys[pygame.K_s], keys[pygame.K_a], keys[pygame.K_d],
            keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_LEFT], keys[pygame.K_RIGHT],
        ])

        # Mouse aim movement
        mouse_delta = (self.mouse_world - self.prev_mouse_pos).length()
        self.prev_mouse_pos = Vec2(self.mouse_world)

        mouse_time = min(0.7, mouse_delta * MOUSE_TIME_WEIGHT)

        if self.action_burst_timer > 0:
            self.action_burst_timer = max(0.0, self.action_burst_timer - dt_real)
            self.target_time_scale = TIME_SCALE_MAX
        elif move_input:
            self.target_time_scale = TIME_SCALE_MAX
        else:
            self.target_time_scale = max(TIME_SCALE_BASE, mouse_time)

        # Smooth interpolation
        ramp_speed = TIME_RAMP_UP_SPEED if self.target_time_scale > self.current_time_scale else TIME_RAMP_DOWN_SPEED
        self.current_time_scale += (self.target_time_scale - self.current_time_scale) * min(1.0, ramp_speed * dt_real)

        return dt_real * self.current_time_scale

    def update_playing(self, dt_real: float) -> None:
        """Update simulation when in PLAYING state."""
        dt_effective = self.update_time_dilation(dt_real)

        # 1. Player input movement
        keys = pygame.key.get_pressed()
        move_dir = Vec2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_dir.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_dir.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_dir.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_dir.x += 1

        self.player.move(move_dir, dt_effective, self.walls)
        self.player.update(dt_effective, dt_real, self.walls, self.mouse_world)
        self.player.update_burst(dt_effective, self.bullets)

        # Hotswitch focus target check
        self.player.target_enemy = self.player.find_hotswitch_target(self.enemies, self.walls, self.mouse_world)

        # 2. Update Bullets
        active_bullets = []
        for b in self.bullets:
            if b.update(dt_effective, self.walls, self.particles):
                # Check collision with player
                if b.owner == "enemy" and self.player.is_alive:
                    if (b.pos - self.player.pos).length() < (self.player.radius + b.radius):
                        self.player.is_alive = False
                        b.alive = False
                        self.particles.spawn_shatter(self.player.pos, b.vel, count=22, is_red=False)
                        self.audio.play("punch", volume=1.0)
                        self.audio.play("shatter", volume=0.9)

                # Check collision with enemies
                if b.owner == "player" and b.alive:
                    for enemy in self.enemies:
                        if enemy.is_alive:
                            if (b.pos - enemy.pos).length() < (enemy.radius + b.radius):
                                enemy.kill(b.vel, self.particles, self.weapons_world)
                                b.alive = False
                                if self.is_endless:
                                    self.endless_kills += 1
                                break

            if b.alive:
                active_bullets.append(b)
        self.bullets = active_bullets

        # 3. Update Weapons in World
        for w in self.weapons_world:
            w.update(dt_effective, self.walls, self.particles)

        # 4. Update Enemies
        for enemy in self.enemies:
            enemy.update(
                dt_effective,
                self.player,
                self.walls,
                self.bullets,
                self.weapons_world,
                self.particles,
            )

        # 5. Update Particles
        self.particles.update(dt_effective, self.walls)
        self.ui.update_card(dt_real)

        # 6. Record Replay Frame
        if dt_effective > 0.0001:
            self.replay.record_frame(
                self.player,
                self.enemies,
                self.bullets,
                self.weapons_world,
                self.particles,
            )

        # 7. Check Game Over (Player Death)
        if not self.player.is_alive:
            self.state = "game_over"
            return

        # 8. Check Endless Mode Waves
        if self.is_endless:
            alive_enemies = [e for e in self.enemies if e.is_alive]
            if len(alive_enemies) == 0:
                self.endless_wave += 1
                self._spawn_endless_wave()

        # 9. Check Level Clear (All enemies killed in campaign)
        elif all(not e.is_alive for e in self.enemies):
            self.replay.start_playback()
            self.state = "replay"

    def _spawn_endless_wave(self) -> None:
        """Spawn the next escalating wave in endless mode."""
        spawn_count = 2 + self.endless_wave
        types = [WeaponType.PISTOL, WeaponType.SHOTGUN, WeaponType.RIFLE, WeaponType.KATANA]

        for _ in range(spawn_count):
            # Choose spawn away from player
            for _ in range(10):
                sx = random.uniform(80, self.vw - 80)
                sy = random.uniform(80, self.vh - 80)
                pos = Vec2(sx, sy)
                if (pos - self.player.pos).length() > 280:
                    break

            w_choice = random.choice(types)
            self.enemies.append(Enemy(pos, weapon_type=w_choice))

        # Drop extra weapons
        if random.random() < 0.6:
            wx = random.uniform(100, self.vw - 100)
            wy = random.uniform(100, self.vh - 100)
            self.weapons_world.append(WeaponItem(random.choice(types), Vec2(wx, wy)))

    def draw_world(self, surface: pygame.Surface) -> None:
        """Render playing world on 1280x720 surface."""
        # 1. Floor & Grid
        surface.fill(COLOR_BG)
        for x in range(0, self.vw, 48):
            pygame.draw.line(surface, COLOR_BG_GRID, (x, 0), (x, self.vh), 1)
        for y in range(0, self.vh, 48):
            pygame.draw.line(surface, COLOR_BG_GRID, (0, y), (self.vw, y), 1)

        # 2. Walls with ambient shadow
        for wall in self.walls:
            shadow = wall.inflate(4, 4)
            pygame.draw.rect(surface, COLOR_WALL_SHADOW, shadow)
            pygame.draw.rect(surface, COLOR_WALL, wall)
            pygame.draw.rect(surface, COLOR_WALL_BORDER, wall, 2)

        # 3. Weapons in world
        for w in self.weapons_world:
            w.draw(surface)

        # 4. Particles (Shards, sparks, slashes)
        self.particles.draw(surface)

        # 5. Enemies
        for enemy in self.enemies:
            is_target = (enemy == self.player.target_enemy)
            enemy.draw(surface, is_hotswitch_target=is_target)

        # 6. Bullets
        for b in self.bullets:
            b.draw(surface)

        # 7. Player
        self.player.draw(surface)

        # 8. HUD & Crosshair
        w_val = self.endless_wave if self.is_endless else None
        s_val = self.endless_kills if self.is_endless else None
        self.ui.draw_hud(surface, self.player, self.current_time_scale, w_val, s_val)
        self.ui.draw_crosshair(surface, (int(self.mouse_world.x), int(self.mouse_world.y)), self.player.target_enemy is not None)

    def draw_screen(self) -> None:
        """Render virtual surface scaled with aspect ratio preservation (letterboxed) to screen."""
        self.virtual_surface.fill(COLOR_BG)

        # Render active state
        if self.state == "menu":
            self._draw_main_menu(self.virtual_surface)
        elif self.state == "controls":
            self._draw_controls(self.virtual_surface)
        elif self.state == "settings":
            self._draw_settings(self.virtual_surface)
        elif self.state == "playing":
            self.draw_world(self.virtual_surface)
        elif self.state == "pause":
            self.draw_world(self.virtual_surface)
            self._draw_pause(self.virtual_surface)
        elif self.state == "game_over":
            self.draw_world(self.virtual_surface)
            self.ui.draw_game_over(self.virtual_surface)
        elif self.state == "replay":
            self.replay.draw_playback(self.virtual_surface, self.walls)
        elif self.state == "campaign_win":
            self.ui.draw_campaign_win(self.virtual_surface)

        # Scale virtual surface to screen maintaining 16:9
        sw, sh = self.screen.get_width(), self.screen.get_height()
        scale = min(sw / self.vw, sh / self.vh)
        rw = int(self.vw * scale)
        rh = int(self.vh * scale)
        scaled_surf = pygame.transform.smoothscale(self.virtual_surface, (rw, rh))

        self.screen.fill((10, 12, 16))  # Outer letterbox background
        ox = (sw - rw) // 2
        oy = (sh - rh) // 2
        self.screen.blit(scaled_surf, (ox, oy))

        pygame.display.flip()

    def _draw_main_menu(self, surface: pygame.Surface) -> None:
        """Render high-contrast Title screen."""
        # Background Grid
        for x in range(0, self.vw, 48):
            pygame.draw.line(surface, COLOR_BG_GRID, (x, 0), (x, self.vh), 1)
        for y in range(0, self.vh, 48):
            pygame.draw.line(surface, COLOR_BG_GRID, (0, y), (self.vw, y), 1)

        # Title: SUPER (red) HOT (black) 2D
        t_super = self.ui.font_title.render(f"{TEXT_TITLE_SUPER} ", True, COLOR_UI_TEXT_RED)
        t_hot = self.ui.font_title.render(f"{TEXT_TITLE_HOT} 2D", True, COLOR_UI_TEXT_DARK)
        total_w = t_super.get_width() + t_hot.get_width()
        start_x = (self.vw - total_w) // 2
        surface.blit(t_super, (start_x, 120))
        surface.blit(t_hot, (start_x + t_super.get_width(), 120))

        sub_surf = self.ui.font_subtitle.render(TEXT_SUBTITLE, True, (90, 95, 105))
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.vw // 2, 205)))

        # Update and draw buttons
        m_pos = (int(self.mouse_world.x), int(self.mouse_world.y))
        dt = self.clock.get_time() / 1000.0
        for btn in self.main_menu_buttons:
            btn.update(m_pos, dt)
            btn.draw(surface)

        self.ui.draw_crosshair(surface, m_pos, False)

    def _draw_settings(self, surface: pygame.Surface) -> None:
        """Render settings menu."""
        t_surf = self.ui.font_card.render(TEXT_SETTINGS_TITLE, True, COLOR_UI_TEXT_DARK)
        surface.blit(t_surf, t_surf.get_rect(center=(self.vw // 2, 160)))

        m_pos = (int(self.mouse_world.x), int(self.mouse_world.y))
        dt = self.clock.get_time() / 1000.0
        for btn in self.settings_buttons:
            btn.update(m_pos, dt)
            btn.draw(surface)

        self.ui.draw_crosshair(surface, m_pos, False)

    def _draw_controls(self, surface: pygame.Surface) -> None:
        """Render controls overview screen."""
        t_surf = self.ui.font_card.render(TEXT_CONTROLS_TITLE, True, COLOR_UI_TEXT_DARK)
        surface.blit(t_surf, t_surf.get_rect(center=(self.vw // 2, 130)))

        controls_list = [
            TEXT_CONTROLS_WASD,
            TEXT_CONTROLS_MOUSE,
            TEXT_CONTROLS_LMB,
            TEXT_CONTROLS_RMB,
            TEXT_CONTROLS_HOTSWITCH,
            TEXT_CONTROLS_FULLSCREEN,
            TEXT_CONTROLS_RESTART,
            TEXT_CONTROLS_PAUSE,
        ]

        start_y = 190
        for idx, text in enumerate(controls_list):
            txt_surf = self.ui.font_hud.render(text, True, (40, 42, 50))
            surface.blit(txt_surf, txt_surf.get_rect(center=(self.vw // 2, start_y + idx * 42)))

        m_pos = (int(self.mouse_world.x), int(self.mouse_world.y))
        dt = self.clock.get_time() / 1000.0
        self.controls_back_button.update(m_pos, dt)
        self.controls_back_button.draw(surface)

        self.ui.draw_crosshair(surface, m_pos, False)

    def _draw_pause(self, surface: pygame.Surface) -> None:
        """Render pause overlay and buttons."""
        overlay = pygame.Surface((self.vw, self.vh), pygame.SRCALPHA)
        overlay.fill((246, 246, 248, 200))
        surface.blit(overlay, (0, 0))

        t_surf = self.ui.font_card.render("PAUSE", True, COLOR_UI_TEXT_DARK)
        surface.blit(t_surf, t_surf.get_rect(center=(self.vw // 2, 180)))

        m_pos = (int(self.mouse_world.x), int(self.mouse_world.y))
        dt = self.clock.get_time() / 1000.0
        for btn in self.pause_buttons:
            btn.update(m_pos, dt)
            btn.draw(surface)

        self.ui.draw_crosshair(surface, m_pos, False)

    def run(self) -> None:
        """Master application loop."""
        pygame.mouse.set_visible(False)  # Custom crosshair rendered instead

        while self.running:
            dt_real = self.clock.tick(TARGET_FPS) / 1000.0
            dt_real = min(dt_real, 0.1)  # Cap large delta spikes

            self.handle_events()

            if self.state == "playing":
                self.update_playing(dt_real)
            elif self.state == "replay":
                self.replay.update_playback(dt_real)

            self.draw_screen()

        pygame.quit()
        sys.exit(0)
