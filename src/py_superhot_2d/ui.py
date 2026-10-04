"""UI components, HUD, menus, button controls, and fullscreen/windowed management."""

from __future__ import annotations
import math
from typing import List, Tuple, Callable, Optional
import pygame

from py_superhot_2d.config import (
    COLOR_BG,
    COLOR_BG_GRID,
    COLOR_UI_TEXT_DARK,
    COLOR_UI_TEXT_RED,
    COLOR_UI_ACCENT,
    COLOR_WEAPON,
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
    TEXT_HUD_AMMO,
    TEXT_HUD_EMPTY,
    TEXT_HUD_PUNCH,
    TEXT_HUD_HOTSWITCH,
    TEXT_HUD_READY,
    TEXT_HUD_STANDSTILL,
    TEXT_HUD_MOVING,
    TEXT_HUD_WAVE,
    TEXT_HUD_SCORE,
    TEXT_GAME_OVER,
    TEXT_GAMEOVER_HINT,
    TEXT_CAMPAIGN_WIN,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
)
from py_superhot_2d.math_utils import Vec2
from py_superhot_2d.audio import get_audio
from py_superhot_2d.weapons import WeaponType


class Button:
    """A clean, reactive UI button with hover animation and sound feedback."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Callable[[], None],
        font: pygame.font.Font,
    ):
        self.rect = rect
        self.text = text
        self.on_click = on_click
        self.font = font
        self.is_hovered = False
        self.hover_progress = 0.0

    def update(self, mouse_pos: Tuple[int, int], dt: float) -> None:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.is_hovered else 0.0
        self.hover_progress += (target - self.hover_progress) * min(1.0, 16.0 * dt)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                get_audio().play("ui_blip", volume=0.5)
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        # Hover expansion & fill
        bg_col = (
            int(246 - 215 * self.hover_progress),
            int(246 - 215 * self.hover_progress),
            int(248 - 218 * self.hover_progress),
        )
        text_col = (
            int(20 + 225 * self.hover_progress),
            int(22 + 225 * self.hover_progress),
            int(28 + 220 * self.hover_progress),
        )
        border_col = (
            int(40 + 195 * self.hover_progress),
            int(40 - 10 * self.hover_progress),
            int(45 - 5 * self.hover_progress),
        )

        draw_rect = self.rect.inflate(int(self.hover_progress * 12), int(self.hover_progress * 6))
        pygame.draw.rect(surface, bg_col, draw_rect)
        pygame.draw.rect(surface, border_col, draw_rect, 2)

        txt_surf = self.font.render(self.text, True, text_col)
        t_rect = txt_surf.get_rect(center=draw_rect.center)
        surface.blit(txt_surf, t_rect)


class UIManager:
    """Manages HUD, start menu, controls screen, settings, and display mode toggling."""

    def __init__(self, display_surface: pygame.Surface):
        self.display_surface = display_surface
        self.is_fullscreen = False

        # Fonts
        self.font_title = pygame.font.Font(None, 84)
        self.font_subtitle = pygame.font.Font(None, 24)
        self.font_btn = pygame.font.Font(None, 34)
        self.font_hud = pygame.font.Font(None, 30)
        self.font_card = pygame.font.Font(None, 52)
        self.font_small = pygame.font.Font(None, 22)

        # Crosshair image/vectors
        self.card_timer = 0.0
        self.card_title = ""
        self.card_sub = ""

    def toggle_fullscreen(self) -> None:
        """Toggle between windowed and fullscreen display mode."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.display_surface = pygame.display.set_mode(
                (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT), pygame.RESIZABLE
            )

    def show_card(self, title: str, subtitle: str) -> None:
        """Display a fading scenario title card."""
        self.card_title = title
        self.card_sub = subtitle
        self.card_timer = 3.2

    def update_card(self, dt: float) -> None:
        if self.card_timer > 0:
            self.card_timer -= dt

    def draw_hud(
        self,
        surface: pygame.Surface,
        player,
        time_scale: float,
        endless_wave: Optional[int] = None,
        endless_score: Optional[int] = None,
    ) -> None:
        """Render minimalist tactical HUD in German."""
        sw, sh = surface.get_width(), surface.get_height()

        # 1. Ammo / Weapon Indicator (Bottom-Left)
        if player.equipped_weapon is not None:
            w = player.equipped_weapon
            w_name = w.name.upper()
            if w.weapon_type == WeaponType.KATANA:
                ammo_str = "UNBEGRENZT"
            elif w.weapon_type == WeaponType.BOTTLE:
                ammo_str = "WURFBEREIT"
            elif w.ammo <= 0:
                ammo_str = TEXT_HUD_EMPTY
            else:
                ammo_str = f"{w.ammo} / {w.max_ammo}"
        else:
            w_name = TEXT_HUD_PUNCH
            ammo_str = "-"

        # Panel Box Bottom-Left
        box_rect = pygame.Rect(28, sh - 74, 210, 48)
        pygame.draw.rect(surface, (255, 255, 255, 180), box_rect)
        pygame.draw.rect(surface, (20, 20, 20), box_rect, 2)

        name_surf = self.font_small.render(w_name, True, (90, 95, 105))
        surface.blit(name_surf, (box_rect.left + 14, box_rect.top + 6))
        ammo_col = COLOR_UI_TEXT_RED if ammo_str == TEXT_HUD_EMPTY else COLOR_UI_TEXT_DARK
        ammo_surf = self.font_hud.render(ammo_str, True, ammo_col)
        surface.blit(ammo_surf, (box_rect.left + 14, box_rect.top + 22))

        # 2. HOTSWITCH Cooldown Meter (Bottom-Center)
        hs_ready = player.can_hotswitch()
        hs_box = pygame.Rect(sw // 2 - 120, sh - 58, 240, 34)
        pygame.draw.rect(surface, (255, 255, 255), hs_box)
        pygame.draw.rect(surface, (20, 20, 20), hs_box, 2)

        if hs_ready:
            pygame.draw.rect(surface, (245, 30, 40), hs_box.inflate(-6, -6))
            hs_txt = self.font_small.render(f"{TEXT_HUD_HOTSWITCH}: {TEXT_HUD_READY} [E]", True, (255, 255, 255))
        else:
            prog = 1.0 - (player.hotswitch_cooldown / 6.0)
            fill_w = int((hs_box.width - 6) * max(0.0, prog))
            fill_rect = pygame.Rect(hs_box.left + 3, hs_box.top + 3, fill_w, hs_box.height - 6)
            pygame.draw.rect(surface, (180, 185, 195), fill_rect)
            hs_txt = self.font_small.render(f"{TEXT_HUD_HOTSWITCH}: {int(player.hotswitch_cooldown) + 1}s", True, COLOR_UI_TEXT_DARK)

        surface.blit(hs_txt, hs_txt.get_rect(center=hs_box.center))

        # 3. Time status (Top-Right)
        is_moving = time_scale > 0.15
        time_text = TEXT_HUD_MOVING if is_moving else TEXT_HUD_STANDSTILL
        time_col = COLOR_UI_TEXT_RED if is_moving else (120, 125, 135)
        time_surf = self.font_small.render(time_text, True, time_col)
        surface.blit(time_surf, (sw - time_surf.get_width() - 32, 28))

        # 4. Endless score / wave (Top-Left)
        if endless_wave is not None and endless_score is not None:
            stats_str = f"{TEXT_HUD_WAVE}: {endless_wave}   |   {TEXT_HUD_SCORE}: {endless_score}"
            stats_surf = self.font_hud.render(stats_str, True, COLOR_UI_TEXT_DARK)
            surface.blit(stats_surf, (32, 28))

        # 5. Title Card Overlay (fade out)
        if self.card_timer > 0:
            alpha = min(255, int(255 * (self.card_timer / 1.0))) if self.card_timer < 1.0 else 255
            card_surf = pygame.Surface((sw, 120), pygame.SRCALPHA)
            t_surf = self.font_card.render(self.card_title, True, (*COLOR_UI_TEXT_DARK, alpha))
            s_surf = self.font_subtitle.render(self.card_sub, True, (*COLOR_UI_ACCENT, alpha))
            card_surf.blit(t_surf, t_surf.get_rect(center=(sw // 2, 40)))
            card_surf.blit(s_surf, s_surf.get_rect(center=(sw // 2, 85)))
            surface.blit(card_surf, (0, sh // 4))

    def draw_crosshair(self, surface: pygame.Surface, mouse_pos: Tuple[int, int], has_target: bool) -> None:
        """Render high-contrast tactical crosshair at cursor position."""
        mx, my = mouse_pos
        col = COLOR_UI_ACCENT if has_target else (20, 22, 28)
        size = 10
        gap = 4

        # Crosshair lines
        pygame.draw.line(surface, col, (mx - size - gap, my), (mx - gap, my), 2)
        pygame.draw.line(surface, col, (mx + gap, my), (mx + size + gap, my), 2)
        pygame.draw.line(surface, col, (mx, my - size - gap), (mx, my - gap), 2)
        pygame.draw.line(surface, col, (mx, my + gap), (mx, my + size + gap), 2)
        pygame.draw.circle(surface, col, (mx, my), 1)

    def draw_game_over(self, surface: pygame.Surface) -> None:
        """Render stark Red/Black Game Over screen."""
        sw, sh = surface.get_width(), surface.get_height()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((246, 246, 248, 220))
        surface.blit(overlay, (0, 0))

        go_surf = self.font_title.render(TEXT_GAME_OVER, True, COLOR_UI_TEXT_RED)
        hint_surf = self.font_hud.render(TEXT_GAMEOVER_HINT, True, COLOR_UI_TEXT_DARK)

        surface.blit(go_surf, go_surf.get_rect(center=(sw // 2, sh // 2 - 40)))
        surface.blit(hint_surf, hint_surf.get_rect(center=(sw // 2, sh // 2 + 40)))

    def draw_campaign_win(self, surface: pygame.Surface) -> None:
        """Render Campaign Completion Victory screen."""
        sw, sh = surface.get_width(), surface.get_height()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((246, 246, 248, 230))
        surface.blit(overlay, (0, 0))

        win_surf = self.font_title.render(TEXT_CAMPAIGN_WIN, True, COLOR_UI_TEXT_RED)
        hint_surf = self.font_hud.render("[LEERTASTE] ZUM HAUPTMENÜ", True, COLOR_UI_TEXT_DARK)

        surface.blit(win_surf, win_surf.get_rect(center=(sw // 2, sh // 2 - 40)))
        surface.blit(hint_surf, hint_surf.get_rect(center=(sw // 2, sh // 2 + 40)))
