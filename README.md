# maia2-uci
converts maia2 in a humanlike uci engine
# Maia2-UCI (Human-Style Chess Engine Wrapper)

**Author:** Dirk D. Sommerfeld

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
- Wasp (if UCI compatible)

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

🔧 UCI Options
Maia Settings
Option	Description
MaiaSelfElo	simulated engine Elo
MaiaOppoElo	expected opponent Elo
ModelType	blitz or rapid
TotalMoveTimeMs	thinking time per move

Strength Controls
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

Helper Engine
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

⏱ Time Management

Total thinking time is strictly limited:
TotalMoveTimeMs = Maia + Helper combined
Default = 1000 ms per move

📁 Networks

Maia automatically downloads networks:
blitz model
rapid model
Location:
~/.cache/maia2/
You may also load custom weights via Maia2 configuration.

🎯 Design Philosophy

This project does not try to beat Stockfish.

Instead it explores:
human-like AI play
explainable chess behavior
hybrid neural + classical evaluation
Maia chooses moves like humans.
The helper engine only prevents catastrophic mistakes.
⚠️ GPU Support

This build is CPU-only by design.
Reasons:
PyTorch CPU version installed
AMD GPU support under Windows is inconsistent
CPU execution is stable and portable

🙏 Credits
Maia2 research team (CSSLab)
Lichess game database
python-chess library

📜 License
Follow Maia2 upstream license.
Wrapper code © Dirk D. Sommerfeld.
