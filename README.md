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
A actual List of ELO strength and the configuration. thx to Eric from schachcomputer.info for making teste and provide this sheet.
ELO    Avg CPL   BlunderThresholdCP
 800   138.8            345
 900   121.9            305
1000   105.0            265
1100    88.1            220
1200    71.2            180
1300    53.2            135
1400    50.6            125
1500    48.0            120
1600    45.4            115
1700    42.8            105
1800    40.2            100
1900    37.6             95
2000    35.0             90
2100    32.4             80
2200    29.8             75
2300    27.2             70
2400    24.6             60
2500    22.0             55
2600    19.4             50
2700    16.8             40
2800    14.2             35
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

# maia2-uci

UCI wrapper for **Maia 2** chess models.

This project allows Maia neural network models to run as a **standard
UCI chess engine**, making them compatible with chess GUIs such as:

-   Arena
-   CuteChess
-   BanksiaGUI
-   ChessBase
-   Lucas Chess

Maia models simulate human-like play at different Elo levels rather than
optimal engine play.

------------------------------------------------------------------------

## Features

-   ✅ UCI-compatible Maia engine
-   ✅ Human-like move selection
-   ✅ Adjustable simulated Elo
-   ✅ Helper engine support (e.g. Stockfish)
-   ✅ CPU and CUDA support
-   ✅ Optional Windows executable build

------------------------------------------------------------------------

## Quick Start

``` bash
pip install maia2 python-chess pyyaml gdown pyzstd
python maia2_uci.py
```

Add the engine to your chess GUI as a normal UCI engine.

------------------------------------------------------------------------

## Installation

### 1. Install Python

Python **3.10 -- 3.13** recommended.

Download: https://www.python.org/downloads/

Verify installation:

``` bash
python --version
```

------------------------------------------------------------------------

### 2. Install Dependencies

``` bash
pip install maia2
pip install python-chess pyyaml gdown pyzstd
```

------------------------------------------------------------------------

### 3. Download the Engine Script

Clone the repository or download:

    maia2_uci.py

------------------------------------------------------------------------

### 4. Run the Engine

``` bash
python maia2_uci.py
```

Your GUI should now detect the engine via UCI.

------------------------------------------------------------------------

## Building a Windows Executable (Optional)

Ready to run windows binary's are in the bin folder (download link) 
Install PyInstaller:

``` powershell
python -m pip install pyinstaller
```

Build:

``` powershell
python -m PyInstaller --noconfirm --clean --onedir `
  --name maia2-uci `
  maia2_uci.py
```

Executable location:

``` text
dist/maia2-uci/
```

Add `maia2-uci.exe` to your chess GUI.

------------------------------------------------------------------------

## UCI Options

### Maia Settings

  Option            Description
  ----------------- ---------------------------------------
  MaiaSelfElo       Simulated engine Elo
  MaiaOppoElo       Expected opponent Elo
  ModelType         `blitz` or `rapid`
  TotalMoveTimeMs   Thinking time per move (milliseconds)

------------------------------------------------------------------------

### Helper Engine Settings

Optional external engine used for evaluation assistance.

  Option             Description
  ------------------ ----------------------------------
  HelperEnginePath   Path to helper engine executable
  HelperNodes        Nodes searched by helper engine

Example:

``` text
HelperEnginePath = C:\Engines\stockfish18.exe
HelperNodes = 100000
```

------------------------------------------------------------------------

### Policy Control

Controls randomness and human-like behavior.

  Option       Description
  ------------ --------------------------------------------
  PolicyTemp   Softmax temperature (higher = more random)
  PolicyTopK   Restrict moves to top-K candidates
  PolicyTopP   Nucleus sampling probability cutoff

------------------------------------------------------------------------

### Performance Settings

  Option      Description
  ----------- -------------------
  Device      `cpu` or `cuda`
  Precision   `fp32` or `fp16`
  Threads     CPU thread count
  Hash        Memory size in MB

------------------------------------------------------------------------

## Usage in Chess GUIs

1.  Open your chess GUI.
2.  Add new engine.
3.  Select:
    -   `python maia2_uci.py`
    -   or `maia2-uci.exe`
4.  Choose **UCI engine**.
5.  Configure options if desired.

------------------------------------------------------------------------

## Notes

-   First startup may download Maia model weights automatically.
-   CUDA requires a compatible NVIDIA GPU and installed CUDA runtime.
-   Lower temperature values produce stronger, less random play.
-   Higher helper nodes increase strength but reduce speed.

------------------------------------------------------------------------

## Troubleshooting

### Engine does not start

-   Ensure Python is in PATH.

-   Run manually in terminal to see errors:

    ``` bash
    python maia2_uci.py
    ```

### CUDA not detected

-   Verify CUDA installation.

-   Try:

        Device = cpu

### GUI cannot detect engine

-   Confirm UCI mode is selected.
-   Check file permissions.

------------------------------------------------------------------------

## License

Follow the maia2 license

------------------------------------------------------------------------

## Acknowledgements

-   Maia Chess Project
-   python-chess
-   UCI protocol community
