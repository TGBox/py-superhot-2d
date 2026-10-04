# SUPERHOT 2D

Ein minimalistisches, taktisches 2D-Top-Down-Actionspiel in Python (`pygame-ce`), inspiriert vom legendären Klassiker **SUPERHOT**.

> **„DIE ZEIT BEWEGT SICH NUR, WENN DU DICH BEWEGST.“**

Im Stillstand verharrt die Spielwelt in extremer Zeitlupe (ca. 4% Geschwindigkeit). Jede Bewegung mit WASD, schnelles Zielen mit dem Mauszeiger oder Angriffsaktionen beschleunigen den Zeitfluss dynamisch auf Normalzeit (100%).

---

## Features

- **High-Contrast SUPERHOT-Ästhetik**:
  - Steril-weiße Architektur mit subtilen Rasterlinien und Schatten.
  - Tiefschwarze Waffen, Munition und Wurfgegenstände.
  - Kristallrote Feinde, die bei Treffern in dynamische, physikalische Polygon-Glasscherben zerspringen.
- **Taktisches Waffenarsenal**:
  - **Fäuste**: Ein gezielter Faustschlag betäubt Gegner und schleudert deren Waffe in hohem Bogen durch die Luft.
  - **Waffen werfen & fangen**: Leere oder volle Waffen können mit Rechtsklick geschleudert werden, um Feinde auszuschalten. Fliegende Waffen lassen sich mit Rechtsklick direkt aus der Luft greifen!
  - **Pistole, Schrotflinte & Sturmgewehr**: Begrenzte Magazine, taktische Projektilflugbahnen mit glühenden Schweifen.
  - **Katana**: Zerschneidet heranstürmende Feinde und **zerteilt anfliegende Projektile im Flug**!
- **HOTSWITCH (Körpertausch)**:
  - Visiere einen Gegner an und drücke `E` oder `Leertaste`, um blitzartig in dessen Körper zu teleportieren. Dein alter Körper zerfällt in Kristallstaub, der Feind wird vernichtet und du übernimmst seine Position und Waffe.
- **Echtzeit-Replay & 'SUPER. HOT.'-Chant**:
  - Nach jedem bezwungenen Level wird der gesamte Ablauf in ununterbrochener Normalgeschwindigkeit als Replay wiedergegeben – untermalt vom legendären, pulsierenden **SUPER. HOT.**-Banner.
- **Spielmodi**:
  - **Kampagne**: 5 handgefertigte Szenario-Levels (*Das Büro*, *Die Bar*, *U-Bahn Station*, *Die Lagerhalle*, *Das Penthouse*).
  - **Endlos-Modus**: Eine sich dynamisch füllende Arena mit ansteigenden Gegnerwellen und Highscore-Zähler.
- **Prozedurales Audio**:
  - Komplett integrierte Synthese für Schüsse, Glasscherben, Hotswitch-Drops und Beats via NumPy & Pygame Mixer – keine externen Mediendateien erforderlich.
- **Vollbild- & Fenstermodus**:
  - Nahtloser Wechsel jederzeit mit `F11` oder im Einstellungsmenü. Automatische 16:9-Letterbox-Skalierung für gestochen scharfe Darstellung auf allen Bildschirmgrößen.

---

## Steuerung

| Taste / Eingabe | Aktion |
| :--- | :--- |
| **W, A, S, D** / Pfeiltasten | Spieler bewegen (beschleunigt die Zeit) |
| **Mauszeiger** | Zielen & Blickrichtung (schnelle Bewegung beschleunigt die Zeit) |
| **Linke Maustaste (LMB)** | Schlagen (unbewaffnet) / Schießen / Katana-Hieb |
| **Rechte Maustaste (RMB)** | Waffe werfen / Waffe im Flug oder am Boden fangen |
| **E / Leertaste** | **HOTSWITCH** (Körpertausch mit anvisiertem Feind) |
| **F11** | Umschalten zwischen **Vollbild** und **Fenstermodus** |
| **R** | Schneller Level-Neustart |
| **ESC** | Pause / Zurück zum Menü |

---

## Installation & Spielstart

Das Projekt nutzt den modernen Paket- und Projektmanager [uv](https://github.com/astral-sh/uv).

### Spiel starten

```bash
uv run py-superhot-2d
```

### Automatisierte Tests ausführen

```bash
uv run pytest
```

---

## Projektstruktur

```text
py-superhot-2d/
├── src/
│   └── py_superhot_2d/
│       ├── __init__.py      # Einstiegspunkt & CLI
│       ├── config.py        # Konstanten, Farben, deutsche UI-Texte, Zeitdilatation
│       ├── math_utils.py    # Vektoren, Raycasting, Kollisionen, Sichtlinien
│       ├── audio.py         # Prozedurale Sound-Synthese (NumPy + Pygame Mixer)
│       ├── particles.py     # Crystalline Polygon-Scherben, Funken & Slice-Trails
│       ├── weapons.py       # Projektile, Waffenlogik, Wurf- und Fangmechanik
│       ├── entities.py      # Spieler, Gegner-KI (Line-of-Sight, Telegrafieren), Hotswitch
│       ├── levels.py        # 5 Kampagnenlevels & Endlos-Arena
│       ├── replay.py        # Frame-Recorder, Realtime-Playback & SUPER. HOT. Banner
│       ├── ui.py            # Menüs, Buttons, HUD, Crosshair & Vollbildverwaltung
│       └── game.py          # Hauptspielschleife, Zustandsautomat, Zeitdilatation
├── tests/
│   ├── test_superhot.py        # Unit-Tests für Physik, Kampf & Replay
│   └── test_engine_headless.py # Integrationstest für Engine-Lebenszyklus
├── pyproject.toml
└── README.md
```
