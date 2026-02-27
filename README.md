# maia2-uci
converts maia2 in a humanlike uci engine https://github.com/CSSLab/maia2
A human-style neural chess engine based on Maia2 with optional
blunder filtering via a helper UCI engine.
# Maia2-UCI (Human-Style Chess Engine Wrapper)
**Author:** Dirk D. Sommerfeld

## Motivation

The main motivation of this project was to create a UCI chess engine that plays in a human-like style, similar to the SenseRobot AI.
While searching for approaches different from classical chess engines, I discovered the **Maia2** project.
My idea was to build a UCI engine that runs in GUIs like Arena or BearChess and allows experimenting with different playing styles.  
The Maia2 networks already produce very human-like moves, but since Maia2 is **not a classical search engine**, it sometimes makes very strong blunders.
To improve stability while preserving the human style, I added an optional **helper engine**.  
This can be any UCI engine (for example Stockfish or Wasp).
The helper engine does **not play moves**.  
Instead, it only evaluates Maia2’s chosen move for a short time window (for example 600 ms) and checks whether the move is a serious blunder.
This behaviour is controlled by the parameter:
BlunderThresholdCP
- `200` = roughly 2 pawns difference  
- `80`  = good setting for human-like play (0,8 pwan)
If Maia2’s move falls outside the allowed evaluation range, the helper engine rejects it and Maia2 searches for a better alternative.  
All final moves still come from Maia2 — the helper engine only acts as a safety check.
The result is a flexible AI engine that can:
- play extremely fast (e.g. 2 seconds per move),
- maintain a human-like style,
- and still avoid catastrophic tactical mistakes.
I am very happy with the outcome: a configurable hybrid AI engine combining neural human-style play with classical engine stability.

Maia2-UCI is a UCI chess engine wrapper that converts the
[Maia2](https://github.com/CSSLab/maia2) neural chess model into a
fully compatible **UCI engine** usable in chess GUIs such as:

- BearChess
- Arena
- CuteChess
- BanksiaGUI
- any UCI-compatible interface

The goal is **human-like chess**, not brute-force engine play.

Unlike classical engines, Maia2 predicts moves based on human games.
This wrapper adds:

- ✅ UCI compatibility
- ✅ Stable 1-second move timing
- ✅ Lookahead stabilization
- ✅ Repetition avoidance
- ✅ Optional helper engine (Stockfish/Wasp) for blunder filtering
- ✅ CPU-only stability (no GPU required)

---

## 🧠 What is Maia2?

Maia2 is a neural chess model trained on millions of Lichess games.
It predicts moves similarly to human players of different Elo levels.

Key differences vs classical engines:

| Classical Engine | Maia2 |
|---|---|
| Deep search | Neural prediction |
| Objective best move | Human-like move |
| Deterministic | Probabilistic |
| Maximizes evaluation | Mimics human decisions |

This wrapper adds lightweight reasoning to improve stability while
preserving Maia’s playing style.

---

## ⚙️ Features

### Core Engine
- UCI compliant
- Fixed move time (default: 1 second)
- Supports Maia **rapid** and **blitz** networks
- Adjustable Elo simulation

### Strength Improvements
- `lookahead1` mode (default)
- avoids immediate move backtracking
- repetition guard
- temperature-based sampling

### Helper Engine (Optional)
An external engine can verify moves:


Supported helpers:
- Stockfish (recommended)
- Wasp I like this engine 

This keeps Maia human-like while avoiding tactical blunders.

---

## 📦 Installation

### 1. Install Python
Python 3.10–3.13 recommended.

### 2. Install Maia2
```bash
pip install maia2
pip install python-chess pyyaml gdown pyzstd
download the engine maia2_uci.py

start per bash
python maia2_uci.py

build a windows binary
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onedir \
  --name maia2-uci \
  maia2_uci.py
Executable appears in:
dist/maia2-uci/
add the maia2-uci.exe to your GUI

## 🔧 UCI Options
Maia Settings
Option	Description
MaiaSelfElo	simulated engine Elo
MaiaOppoElo	expected opponent Elo
ModelType	blitz or rapid
TotalMoveTimeMs	thinking time per move

## Strength Controls
Option	Description
StrengthMode	fast or lookahead1
TopK	candidate moves evaluated
Temperature	randomness (lower = stronger)
AvoidBacktrack	avoid undoing previous move
AvoidRepetition	prevent repetition loops

Recommended:

StrengthMode = lookahead1
TopK = 8–10
Temperature = 15–20

## Helper Engine
Option	Description
HelperEnginePath	full path to helper EXE
HelperMode	off / blundercheck
HelperMoveTimeMs	helper analysis time
BlunderThresholdCp	replace move if worse

Example:
HelperEnginePath = C:\Engines\stockfish18.exe
HelperMode = blundercheck
HelperMoveTimeMs = 350
BlunderThresholdCp = 200

##⏱ Time Management

Total thinking time is strictly limited:
TotalMoveTimeMs = Maia + Helper combined
Default = 1000 ms per move

## 📁 Networks

Maia automatically downloads networks:
blitz model
rapid model
Location:
~/.cache/maia2/
You may also load custom weights via Maia2 configuration.

## 🎯 Design Philosophy

This project does not try to beat Stockfish.

Instead it explores:
human-like AI play
explainable chess behavior
hybrid neural + classical evaluation
Maia chooses moves like humans.
The helper engine only prevents catastrophic mistakes.

##⚠️ GPU Support

This build is CPU-only by design.
Reasons:
PyTorch CPU version installed
AMD GPU support under Windows is inconsistent
CPU execution is stable and portable

##🙏 Credits
Maia2 research team (CSSLab)
Lichess game database
python-chess library

##📜 License
Follow Maia2 upstream license.
Wrapper code © Dirk D. Sommerfeld.

Ready to run windows download: https://drive.google.com/file/d/1wGxPVT_eokVG4oyGSYWttyJUSBrmwP_B/view?usp=sharing
