"""Level designs, geometry, obstacle layouts, and spawn configurations."""

from __future__ import annotations
from typing import List, Tuple, Optional
import pygame
from py_superhot_2d.math_utils import Vec2
from py_superhot_2d.weapons import WeaponItem, WeaponType
from py_superhot_2d.entities import Enemy


class LevelData:
    """Encapsulates all static geometry and initial entity spawns for a level."""

    def __init__(
        self,
        name: str,
        subtitle: str,
        walls: List[pygame.Rect],
        player_start: Vec2,
        player_weapon: Optional[WeaponType],
        enemies: List[Enemy],
        weapons: List[WeaponItem],
    ):
        self.name = name
        self.subtitle = subtitle
        self.walls = walls
        self.player_start = player_start
        self.player_weapon = player_weapon
        self.enemies = enemies
        self.weapons = weapons


def build_boundary_walls(width: int = 1280, height: int = 720, thickness: int = 24) -> List[pygame.Rect]:
    """Create the outer border walls of the arena."""
    return [
        pygame.Rect(0, 0, width, thickness),                           # Top
        pygame.Rect(0, height - thickness, width, thickness),          # Bottom
        pygame.Rect(0, 0, thickness, height),                          # Left
        pygame.Rect(width - thickness, 0, thickness, height),          # Right
    ]


def get_level_1() -> LevelData:
    """Level 1: Das Büro (The Office) - Unarmed start, learn punch, disarm and pistol combat."""
    walls = build_boundary_walls()
    # Office desks and dividers
    walls.extend([
        pygame.Rect(320, 180, 160, 28),   # Desk 1
        pygame.Rect(320, 340, 160, 28),   # Desk 2
        pygame.Rect(320, 500, 160, 28),   # Desk 3
        pygame.Rect(640, 140, 28, 220),   # Office partition top
        pygame.Rect(640, 420, 28, 200),   # Office partition bottom
        pygame.Rect(820, 260, 180, 32),   # Breakroom table
    ])

    player_start = Vec2(160, 360)
    player_weapon = None  # Start unarmed

    enemies = [
        # Guard 1: Right in front of desk, facing away
        Enemy(Vec2(480, 360), weapon_type=WeaponType.PISTOL),
        # Guard 2: Near top partition
        Enemy(Vec2(760, 220), weapon_type=WeaponType.PISTOL),
        # Guard 3: Bottom corner
        Enemy(Vec2(880, 480), weapon_type=WeaponType.PISTOL),
    ]

    weapons = [
        WeaponItem(WeaponType.BOTTLE, Vec2(340, 240)),  # Mug / Bottle on desk
        WeaponItem(WeaponType.BOTTLE, Vec2(840, 280)),
    ]

    return LevelData(
        name="LEVEL 1: DAS BÜRO",
        subtitle="Entwaffne den ersten Wachmann mit einem Schlag [LMB].",
        walls=walls,
        player_start=player_start,
        player_weapon=player_weapon,
        enemies=enemies,
        weapons=weapons,
    )


def get_level_2() -> LevelData:
    """Level 2: Die Bar (The Bar) - Close quarters, shotguns and throwable bottles."""
    walls = build_boundary_walls()
    # Central Bar counter and tables
    walls.extend([
        pygame.Rect(440, 240, 400, 36),   # Main Bar counter
        pygame.Rect(440, 276, 36, 140),   # Bar corner left
        pygame.Rect(804, 276, 36, 140),   # Bar corner right
        pygame.Rect(200, 160, 80, 80),    # Stool / table
        pygame.Rect(200, 480, 80, 80),    # Stool / table
        pygame.Rect(1000, 200, 110, 160), # Pool billiard table
        pygame.Rect(1000, 440, 80, 80),   # Lounge table
    ])

    player_start = Vec2(140, 340)
    player_weapon = WeaponType.PISTOL

    enemies = [
        Enemy(Vec2(520, 340), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(680, 340), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(960, 260), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(1040, 520), weapon_type=WeaponType.SHOTGUN),
    ]

    weapons = [
        WeaponItem(WeaponType.BOTTLE, Vec2(580, 220)),
        WeaponItem(WeaponType.BOTTLE, Vec2(720, 220)),
        WeaponItem(WeaponType.BOTTLE, Vec2(220, 180)),
    ]

    return LevelData(
        name="LEVEL 2: DIE BAR",
        subtitle="Vorsicht vor Schrotflinten. Wirf leere Waffen mit [RMB].",
        walls=walls,
        player_start=player_start,
        player_weapon=player_weapon,
        enemies=enemies,
        weapons=weapons,
    )


def get_level_3() -> LevelData:
    """Level 3: U-Bahn Station (Subway) - Long pillar corridors, rifle burst enemies."""
    walls = build_boundary_walls()
    # Subway train tracks partition and support columns
    walls.extend([
        pygame.Rect(160, 180, 40, 40),    # Pillar 1
        pygame.Rect(380, 180, 40, 40),    # Pillar 2
        pygame.Rect(600, 180, 40, 40),    # Pillar 3
        pygame.Rect(820, 180, 40, 40),    # Pillar 4
        pygame.Rect(1040, 180, 40, 40),   # Pillar 5
        pygame.Rect(160, 480, 40, 40),    # Pillar 6
        pygame.Rect(380, 480, 40, 40),    # Pillar 7
        pygame.Rect(600, 480, 40, 40),    # Pillar 8
        pygame.Rect(820, 480, 40, 40),    # Pillar 9
        pygame.Rect(1040, 480, 40, 40),   # Pillar 10
        pygame.Rect(480, 330, 320, 24),   # Ticket counter / bench
    ])

    player_start = Vec2(100, 340)
    player_weapon = WeaponType.PISTOL

    enemies = [
        Enemy(Vec2(440, 160), weapon_type=WeaponType.RIFLE),
        Enemy(Vec2(520, 500), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(740, 340), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(960, 160), weapon_type=WeaponType.RIFLE),
        Enemy(Vec2(1080, 500), weapon_type=WeaponType.PISTOL),
    ]

    weapons = [
        WeaponItem(WeaponType.RIFLE, Vec2(380, 340), ammo=18),
    ]

    return LevelData(
        name="LEVEL 3: U-BAHN STATION",
        subtitle="Nutze die Säulen als Deckung vor Dauerfeuer.",
        walls=walls,
        player_start=player_start,
        player_weapon=player_weapon,
        enemies=enemies,
        weapons=weapons,
    )


def get_level_4() -> LevelData:
    """Level 4: Die Lagerhalle (Warehouse) - Katana bullet slicing!"""
    walls = build_boundary_walls()
    # Cargo container crates maze
    walls.extend([
        pygame.Rect(260, 120, 140, 70),
        pygame.Rect(260, 280, 140, 140),
        pygame.Rect(260, 500, 140, 90),
        pygame.Rect(540, 180, 160, 110),
        pygame.Rect(540, 420, 160, 130),
        pygame.Rect(840, 120, 130, 140),
        pygame.Rect(840, 380, 130, 180),
    ])

    player_start = Vec2(120, 360)
    player_weapon = WeaponType.KATANA

    enemies = [
        Enemy(Vec2(460, 160), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(460, 540), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(740, 330), weapon_type=WeaponType.RIFLE),
        Enemy(Vec2(800, 160), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(1080, 260), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(1080, 480), weapon_type=WeaponType.KATANA),
    ]

    weapons = [
        WeaponItem(WeaponType.KATANA, Vec2(540, 340)),
    ]

    return LevelData(
        name="LEVEL 4: DIE LAGERHALLE",
        subtitle="Zerschneide anfliegende Projektile im Flug mit dem Katana!",
        walls=walls,
        player_start=player_start,
        player_weapon=player_weapon,
        enemies=enemies,
        weapons=weapons,
    )


def get_level_5() -> LevelData:
    """Level 5: Das Penthouse (Penthouse Ambush) - Master Hotswitch to survive crossfire."""
    walls = build_boundary_walls()
    # Central elevator column and luxury barriers
    walls.extend([
        pygame.Rect(540, 280, 200, 160),  # Central elevator core
        pygame.Rect(240, 180, 160, 24),   # Balcony partition
        pygame.Rect(240, 520, 160, 24),
        pygame.Rect(880, 180, 160, 24),
        pygame.Rect(880, 520, 160, 24),
    ])

    player_start = Vec2(640, 160)
    player_weapon = WeaponType.PISTOL

    enemies = [
        Enemy(Vec2(280, 140), weapon_type=WeaponType.RIFLE),
        Enemy(Vec2(280, 560), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(1000, 140), weapon_type=WeaponType.RIFLE),
        Enemy(Vec2(1000, 560), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(420, 360), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(860, 360), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(640, 540), weapon_type=WeaponType.KATANA),
    ]

    weapons = [
        WeaponItem(WeaponType.SHOTGUN, Vec2(320, 360)),
        WeaponItem(WeaponType.RIFLE, Vec2(960, 360)),
    ]

    return LevelData(
        name="LEVEL 5: DAS PENTHOUSE",
        subtitle="Kreuzfeuer! Nutze HOTSWITCH [E / LEERTASTE] zum Überleben.",
        walls=walls,
        player_start=player_start,
        player_weapon=player_weapon,
        enemies=enemies,
        weapons=weapons,
    )


def get_endless_arena() -> LevelData:
    """Base arena layout for Endless Survival Mode."""
    walls = build_boundary_walls()
    # Dynamic arena obstacles
    walls.extend([
        pygame.Rect(320, 200, 60, 60),
        pygame.Rect(320, 460, 60, 60),
        pygame.Rect(900, 200, 60, 60),
        pygame.Rect(900, 460, 60, 60),
        pygame.Rect(590, 310, 100, 100),  # Central block
    ])

    player_start = Vec2(640, 520)
    player_weapon = WeaponType.PISTOL

    # Initial wave of 3 enemies
    enemies = [
        Enemy(Vec2(340, 140), weapon_type=WeaponType.PISTOL),
        Enemy(Vec2(640, 140), weapon_type=WeaponType.SHOTGUN),
        Enemy(Vec2(940, 140), weapon_type=WeaponType.PISTOL),
    ]

    weapons = [
        WeaponItem(WeaponType.SHOTGUN, Vec2(350, 490)),
        WeaponItem(WeaponType.KATANA, Vec2(930, 490)),
    ]

    return LevelData(
        name="ENDLOS-ARENA",
        subtitle="Überlebe so viele Feindwellen wie möglich.",
        walls=walls,
        player_start=player_start,
        player_weapon=player_weapon,
        enemies=enemies,
        weapons=weapons,
    )


CAMPAIGN_LEVELS = [
    get_level_1,
    get_level_2,
    get_level_3,
    get_level_4,
    get_level_5,
]
