"""Procedural sound synthesis using NumPy and Pygame mixer.

Generates all sound effects dynamically at runtime without external audio assets.
Gracefully handles headless environments or systems without audio devices.
"""

from __future__ import annotations
import math
import numpy as np
import pygame

SAMPLE_RATE = 44100


class SoundManager:
    """Manages generation and playback of synthesized procedural sound effects."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.initialized = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self.initialized = True
            self._generate_catalog()
        except Exception as e:
            # Fallback for systems without audio hardware
            print(f"[SoundManager] Audio device unavailable: {e}. Running in silent mode.")
            self.initialized = False

    def _make_sound(self, mono_samples: np.ndarray) -> pygame.mixer.Sound:
        """Convert a float [-1, 1] 1D numpy array into a 16-bit stereo Pygame Sound."""
        # Clamp samples to prevent clipping distortion
        clamped = np.clip(mono_samples, -1.0, 1.0)
        # Convert to int16
        int16_samples = (clamped * 32767).astype(np.int16)
        # Duplicate to stereo (N, 2)
        stereo_samples = np.column_stack((int16_samples, int16_samples))
        return pygame.sndarray.make_sound(np.ascontiguousarray(stereo_samples))

    def _generate_catalog(self) -> None:
        """Synthesize all game sound effects."""
        # 1. Pistol Shot (snappy transient + punch)
        dur = 0.18
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 45)
        body = np.sin(2 * np.pi * (160 * np.exp(-t * 25)) * t) * np.exp(-t * 22)
        pistol = 0.7 * noise + 0.5 * body
        self.sounds["pistol"] = self._make_sound(pistol)

        # 2. Shotgun Blast (deep heavy sub-bass + wide explosive noise)
        dur = 0.35
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 18)
        sub = np.sin(2 * np.pi * (110 * np.exp(-t * 12)) * t) * np.exp(-t * 10)
        shotgun = 0.8 * noise + 0.6 * sub
        self.sounds["shotgun"] = self._make_sound(shotgun)

        # 3. Rifle Shot (crisp metallic snap)
        dur = 0.14
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 60)
        snap = np.sin(2 * np.pi * (320 * np.exp(-t * 40)) * t) * np.exp(-t * 35)
        rifle = 0.6 * noise + 0.5 * snap
        self.sounds["rifle"] = self._make_sound(rifle)

        # 4. Punch (heavy thud impact)
        dur = 0.16
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        thud = np.sin(2 * np.pi * (95 * np.exp(-t * 30)) * t) * np.exp(-t * 25)
        pop = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-t * 65)
        self.sounds["punch"] = self._make_sound(0.8 * thud + 0.4 * pop)

        # 5. Crystal Shatter (layered high-frequency ringing glass/crystal)
        dur = 0.45
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        shatter_noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-t * 16)
        ring1 = np.sin(2 * np.pi * 2150 * t) * np.exp(-t * 10)
        ring2 = np.sin(2 * np.pi * 3420 * t) * np.exp(-t * 14)
        ring3 = np.sin(2 * np.pi * 4800 * t) * np.exp(-t * 20)
        crystal = 0.4 * shatter_noise + 0.25 * ring1 + 0.2 * ring2 + 0.15 * ring3
        self.sounds["shatter"] = self._make_sound(crystal)

        # 6. Katana Slice (fast metallic ring & woosh)
        dur = 0.28
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        ring = np.sin(2 * np.pi * (1800 + 400 * t) * t) * np.exp(-t * 12)
        whoosh = np.random.uniform(-0.4, 0.4, len(t)) * np.sin(np.pi * t / dur)
        self.sounds["katana"] = self._make_sound(0.6 * ring + 0.5 * whoosh)

        # 7. Throw / Whoosh
        dur = 0.22
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        whoosh = np.random.uniform(-0.6, 0.6, len(t)) * np.sin(np.pi * t / dur) ** 2
        self.sounds["throw"] = self._make_sound(whoosh)

        # 8. Catch (clean snappy wooden/metallic click)
        dur = 0.08
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        click = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 90)
        self.sounds["catch"] = self._make_sound(0.7 * click)

        # 9. Hotswitch (deep cosmic warp / bass sweep)
        dur = 0.6
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        freq_sweep = 220 * np.exp(-t * 4) + 40
        sweep = np.sin(2 * np.pi * freq_sweep * t) * np.exp(-t * 3.5)
        warp = np.sin(2 * np.pi * (freq_sweep * 1.5) * t) * np.exp(-t * 4.5) * 0.4
        self.sounds["hotswitch"] = self._make_sound(0.7 * sweep + warp)

        # 10. Ricochet / Bullet Deflect
        dur = 0.25
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        freq = 3200 + 1500 * np.sin(2 * np.pi * 18 * t)
        ping = np.sin(2 * np.pi * freq * t) * np.exp(-t * 16)
        self.sounds["ricochet"] = self._make_sound(0.6 * ping)

        # 11. UI Blip
        dur = 0.05
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        blip = np.sin(2 * np.pi * 920 * t) * np.exp(-t * 50)
        self.sounds["ui_blip"] = self._make_sound(0.3 * blip)

        # 12. Superhot Replay Chant Beat
        dur = 0.35
        t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
        beat = np.sin(2 * np.pi * (80 * np.exp(-t * 10)) * t) * np.exp(-t * 8)
        self.sounds["beat"] = self._make_sound(0.8 * beat)

    def play(self, sound_name: str, volume: float = 1.0) -> None:
        """Play a named sound effect if audio is initialized and enabled."""
        if not self.initialized or not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd is not None:
            snd.set_volume(max(0.0, min(1.0, volume)))
            snd.play()

    def toggle(self) -> bool:
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        return self.enabled


# Global singleton instance
_AUDIO_INSTANCE: SoundManager | None = None


def get_audio() -> SoundManager:
    global _AUDIO_INSTANCE
    if _AUDIO_INSTANCE is None:
        _AUDIO_INSTANCE = SoundManager(enabled=True)
    return _AUDIO_INSTANCE
