"""Game configuration, constants, color palette, and localized text."""

import pygame

# Window & Display Settings
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
TARGET_FPS = 60
TITLE = "SUPERHOT 2D"

# Time Dilation Constants
TIME_SCALE_BASE = 0.04  # Crawling speed when motionless
TIME_SCALE_MAX = 1.0   # Full speed during movement/action
TIME_RAMP_UP_SPEED = 14.0    # Speed of transition when moving
TIME_RAMP_DOWN_SPEED = 9.0   # Speed of transition when stopping
MOUSE_TIME_WEIGHT = 0.003    # Time scale influence from fast cursor motion
ACTION_BURST_DURATION = 0.22 # Duration of full speed after shooting/punching/throwing

# Colors (Superhot high-contrast aesthetic)
COLOR_BG = (246, 246, 248)               # Stark white/gray room floor
COLOR_BG_GRID = (234, 234, 238)          # Subtle architectural grid lines
COLOR_WALL = (205, 208, 214)             # Light concrete/plaster walls
COLOR_WALL_BORDER = (155, 158, 168)      # Wall edge contour
COLOR_WALL_SHADOW = (185, 188, 196)      # Subtle ambient occlusion edge

COLOR_PLAYER = (28, 30, 36)              # Charcoal black player
COLOR_PLAYER_HANDS = (45, 48, 56)        # Slightly lighter hands/fists
COLOR_ENEMY = (235, 30, 40)              # Intense crystal red
COLOR_ENEMY_ACCENT = (255, 90, 100)      # Facet highlight on enemies
COLOR_ENEMY_STUN = (245, 140, 140)       # Stunned lighter tint

COLOR_WEAPON = (18, 18, 20)              # Pitch black weapons & interactables
COLOR_WEAPON_PICKUP = (30, 30, 35)       # Dropped weapon highlight
COLOR_KATANA_BLADE = (230, 235, 245)     # Gleaming steel blade

COLOR_BULLET_PLAYER = (30, 30, 30)       # Black player bullet
COLOR_BULLET_ENEMY = (245, 30, 30)       # Red glowing enemy bullet
COLOR_BULLET_CORE = (255, 245, 210)      # Incandescent center of bullets
COLOR_TRAIL_ENEMY = (245, 40, 40)        # Red laser trail
COLOR_TRAIL_PLAYER = (70, 70, 75)        # Smoke gray trail

COLOR_HOTSWITCH_TARGET = (255, 0, 80)    # Laser target ring
COLOR_UI_TEXT_DARK = (20, 22, 28)        # Charcoal text
COLOR_UI_TEXT_RED = (235, 30, 40)        # Punchy red text
COLOR_UI_ACCENT = (245, 45, 55)

# Gameplay Constants
PLAYER_RADIUS = 16.0
PLAYER_SPEED = 240.0           # Pixels per second at 1.0 time scale
ENEMY_RADIUS = 16.0
ENEMY_SPEED = 145.0            # Pixels per second at 1.0 time scale
BULLET_SPEED = 560.0           # Fast tactical bullet speed
BULLET_RADIUS = 4.0
PUNCH_RANGE = 46.0             # Melee reach in pixels
PUNCH_COOLDOWN = 0.35          # Seconds between punches
THROW_SPEED = 500.0            # Initial velocity of thrown weapon
HOTSWITCH_COOLDOWN = 6.0       # Seconds between Hotswitches
HOTSWITCH_RANGE = 750.0        # Max range for body swap

# Localized UI Strings (German)
TEXT_TITLE_SUPER = "SUPER"
TEXT_TITLE_HOT = "HOT"
TEXT_SUBTITLE = "DIE ZEIT BEWEGT SICH NUR, WENN DU DICH BEWEGST"

TEXT_BTN_CAMPAIGN = "KAMPAGNE"
TEXT_BTN_ENDLESS = "ENDLOS-MODUS"
TEXT_BTN_CONTROLS = "STEUERUNG"
TEXT_BTN_SETTINGS = "EINSTELLUNGEN"
TEXT_BTN_QUIT = "BEENDEN"
TEXT_BTN_CONTINUE = "WEITER"
TEXT_BTN_RESTART = "LEVEL NEU STARTEN"
TEXT_BTN_MENU = "HAUPTMENÜ"

TEXT_CONTROLS_TITLE = "STEUERUNG"
TEXT_CONTROLS_WASD = "W, A, S, D  -  BEWEGUNG"
TEXT_CONTROLS_MOUSE = "MAUSZEIGER  -  ZIELEN"
TEXT_CONTROLS_LMB = "LINKE MAUSTASTE  -  SCHLAGEN / SCHIESSEN"
TEXT_CONTROLS_RMB = "RECHTE MAUSTASTE  -  WAFFE WERFEN / FANGEN"
TEXT_CONTROLS_HOTSWITCH = "E / LEERTASTE  -  HOTSWITCH (KÖRPERTAUSCH)"
TEXT_CONTROLS_FULLSCREEN = "F11  -  VOLLBILD / FENSTERMODUS"
TEXT_CONTROLS_RESTART = "R  -  SCHNELLER NEUSTART"
TEXT_CONTROLS_PAUSE = "ESC  -  PAUSE"

TEXT_SETTINGS_TITLE = "EINSTELLUNGEN"
TEXT_SETTINGS_FULLSCREEN = "VOLLBILDMODUS"
TEXT_SETTINGS_ON = "AN"
TEXT_SETTINGS_OFF = "AUS"
TEXT_SETTINGS_SOUND = "TONEFFEKTE"
TEXT_SETTINGS_BACK = "ZURÜCK"

TEXT_HUD_AMMO = "MUNITION"
TEXT_HUD_EMPTY = "LEER"
TEXT_HUD_PUNCH = "FÄUSTE"
TEXT_HUD_HOTSWITCH = "HOTSWITCH"
TEXT_HUD_READY = "BEREIT"
TEXT_HUD_STANDSTILL = "ZEIT: STILLSTAND"
TEXT_HUD_MOVING = "ZEIT: BEWEGUNG"
TEXT_HUD_WAVE = "WELLE"
TEXT_HUD_SCORE = "KILLS"

TEXT_LEVEL_COMPLETE = "LEVEL GESCHAFFT"
TEXT_GAME_OVER = "ZERSTÖRT"
TEXT_REPLAY_HINT = "[LEERTASTE] NÄCHSTES LEVEL   |   [R] WIEDERHOLEN"
TEXT_GAMEOVER_HINT = "[R] NEUSTART   |   [ESC] MENÜ"
TEXT_CAMPAIGN_WIN = "KAMPAGNE VOLLENDET"
