"""Headless integration test for GameEngine lifecycle and transitions."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from py_superhot_2d.game import GameEngine
from py_superhot_2d.levels import CAMPAIGN_LEVELS


def test_game_engine_lifecycle():
    engine = GameEngine()
    assert engine.state == "menu"

    # Step menu frame
    engine.draw_screen()

    # Transition to controls
    engine.set_state("controls")
    engine.draw_screen()

    # Transition to settings
    engine.set_state("settings")
    engine.draw_screen()

    # Fullscreen toggle test
    engine._toggle_fullscreen_menu()
    assert engine.ui.is_fullscreen
    engine._toggle_fullscreen_menu()
    assert not engine.ui.is_fullscreen

    # Start campaign
    engine.start_campaign()
    assert engine.state == "playing"
    assert engine.player.is_alive
    assert len(engine.enemies) > 0

    # Simulate 30 frames of playing
    for _ in range(30):
        engine.update_playing(0.016)
        engine.draw_screen()

    # Simulate player killing all enemies to trigger replay
    for e in engine.enemies:
        e.is_alive = False

    engine.update_playing(0.016)
    assert engine.state == "replay"

    # Simulate replay playback
    for _ in range(15):
        engine.replay.update_playback(0.016)
        engine.draw_screen()

    # Advance to next level
    engine.advance_level()
    assert engine.state == "playing"
    assert engine.current_level_idx == 1

    # Start endless mode
    engine.start_endless()
    assert engine.state == "playing"
    assert engine.is_endless

    pygame.quit()
