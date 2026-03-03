#!/usr/bin/env python3
# Maia2 UCI wrapper with optional helper engine + stronger stability (CPU-only).
# Author: Dirk D. Sommerfeld
#
# v6.2 changes (conversion mode + mate guard):
# - Removed GPU option completely (CPU-only). No "Device" UCI option.
# - HelperEnginePath remains a string option so you can point directly to the helper .exe.
#
# Default behavior:
# - StrengthMode = lookahead1 (more stable than pure sampling)
# - AvoidRepetition = true (reduces back-and-forth)
# - TotalMoveTimeMs = 1000ms wall-clock

import sys, os, time, math, random, subprocess, threading, queue, argparse
import chess

_ALLOWED_PREFIXES = (
    "id ", "option ", "uciok", "readyok",
    "bestmove ", "copyprotection ", "registration "
)

class UCIStdoutFilter:
    def __init__(self, real_stdout, real_stderr):
        self._out = real_stdout
        self._err = real_stderr
        self._buf = ""

    def write(self, s: str):
        if not s:
            return 0
        self._buf += s
        while True:
            nl = self._buf.find("\n")
            if nl == -1:
                break
            line = self._buf[:nl+1]
            self._buf = self._buf[nl+1:]
            self._route_line(line)
        return len(s)

    def flush(self):
        if self._buf:
            self._route_line(self._buf)
            self._buf = ""
        try: self._out.flush()
        except Exception: pass
        try: self._err.flush()
        except Exception: pass

    def _route_line(self, line: str):
        stripped = line.strip("\r\n")
        if not stripped:
            return
        if any(stripped.startswith(p) for p in _ALLOWED_PREFIXES):
            self._out.write(line)
            try: self._out.flush()
            except Exception: pass
        else:
            self._err.write(line)
            try: self._err.flush()
            except Exception: pass

    def isatty(self): return False
    def fileno(self): return self._out.fileno()
    @property
    def encoding(self): return getattr(self._out, "encoding", "utf-8")

sys.stdout = UCIStdoutFilter(sys.__stdout__, sys.__stderr__)
try:
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

def eprint(*a):
    print(*a, file=sys.__stderr__, flush=True)

def normalize_engine_path(p: str) -> str:
    """Normalize an engine path entered in a GUI (strip quotes/whitespace, expand env vars)."""
    if not p:
        return ""
    p = p.strip()
    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
        p = p[1:-1].strip()
    return os.path.expandvars(p)

class UCIProcess:
    def __init__(self, path: str):
        self.path = path
        self.proc = None
        self._q = queue.Queue()

    def start(self) -> bool:
        if not self.path:
            return False
        if self.proc is not None:
            return True
        try:
            self.proc = subprocess.Popen(
                [self.path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            eprint(f"[maia2-uci] Helper start failed: {e}")
            self.proc = None
            return False

        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()

        self.send("uci")
        if not self.wait_for("uciok", timeout=2.5):
            eprint("[maia2-uci] Helper did not answer uciok (not UCI engine?)")
            self.stop()
            return False
        self.send("isready")
        if not self.wait_for("readyok", timeout=2.5):
            eprint("[maia2-uci] Helper did not answer readyok")
            self.stop()
            return False
        return True

    def stop(self):
        if self.proc is None:
            return
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.kill()
        except Exception:
            pass
        self.proc = None

    def _read_stdout(self):
        try:
            for line in self.proc.stdout:
                if not line:
                    break
                self._q.put(line.strip())
        except Exception:
            pass

    def _drain_stderr(self):
        try:
            for line in self.proc.stderr:
                if not line:
                    break
                eprint(f"[helper] {line.strip()}")
        except Exception:
            pass

    def send(self, cmd: str):
        if self.proc is None or self.proc.stdin is None:
            return
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def wait_for(self, token: str, timeout: float) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self._q.get(timeout=0.05)
            except queue.Empty:
                continue
            if line == token:
                return True
        return False

    def read_until_bestmove(self, timeout: float):
        end = time.time() + timeout
        best = None
        last_cp = None
        while time.time() < end:
            try:
                line = self._q.get(timeout=0.05)
            except queue.Empty:
                continue

            if line.startswith("info "):
                parts = line.split()
                if "score" in parts:
                    i = parts.index("score")
                    if i + 2 < len(parts):
                        kind, val = parts[i+1], parts[i+2]
                        if kind == "cp":
                            try: last_cp = int(val)
                            except: pass
                        elif kind == "mate":
                            try:
                                m = int(val)
                                last_cp = 100000 if m > 0 else -100000
                            except:
                                pass

            if line.startswith("bestmove "):
                sp = line.split()
                best = sp[1] if len(sp) >= 2 else None
                return best, last_cp
        return None, last_cp

def _inverse_uci(move_uci: str) -> str:
    if not move_uci or len(move_uci) < 4:
        return ""
    return move_uci[2:4] + move_uci[0:2] + move_uci[4:]

class Maia2Lazy:
    """Lazy loader around maia2 (imports only when needed). CPU-only."""
    def __init__(self):
        self._loaded = False
        self.model = None
        self.prepared = None
        self.model_type = None
        self._infer_lib = None

    def ensure(self, model_type: str):
        if self._loaded and self.model_type == model_type:
            return
        from maia2 import model as maia2_model_lib
        from maia2 import inference as maia2_inference
        self._infer_lib = maia2_inference

        self.model = maia2_model_lib.from_pretrained(type=model_type, device="cpu")
        self.prepared = maia2_inference.prepare()
        self._loaded = True
        self.model_type = model_type

    def inference_each(self, fen: str, elo_self: int, elo_oppo: int):
        return self._infer_lib.inference_each(self.model, self.prepared, fen, elo_self, elo_oppo)

class Maia2UCIEngine:
    def __init__(self, model_type="blitz"):
        self.board = chess.Board()
        self.model_type = model_type

        self.elo_self = 1500
        self.elo_oppo = 1500

        self.total_movetime_ms = 1000

        self.strength_mode = "lookahead1"  # fast | lookahead1
        self.topk = 8
        self.temperature = 0.20
        self.avoid_backtrack = True
        self.avoid_repetition = True
        self.random_seed = 1
        self._rng = random.Random(1)
        self.last_engine_move = None

        self.helper_path = ""
        self.helper_mode = "off"          # off | blundercheck
        self.helper_movetime_ms = 350
        self.blunder_threshold_cp = 200
        self.helper = None

        self.maia = Maia2Lazy()

    def _ensure_maia(self):
        self.maia.ensure(self.model_type)

    def _ensure_helper(self) -> bool:
        if not self.helper_path or self.helper_mode == "off":
            return False
        if self.helper is None:
            self.helper = UCIProcess(self.helper_path)
        ok = self.helper.start()
        if not ok:
            self.helper = None
        return ok

    def uci(self):
        print("id name Maia2-UCI+Helper", flush=True)
        print("id author Dirk D. Sommerfeld", flush=True)
        print('option name MaiaSelfElo type spin default 1500 min 800 max 2800', flush=True)
        print('option name MaiaOppoElo type spin default 1500 min 800 max 2800', flush=True)
        print('option name ModelType type combo default blitz var rapid var blitz', flush=True)
        print('option name TotalMoveTimeMs type spin default 1000 min 50 max 10000', flush=True)
        print('option name StrengthMode type combo default lookahead1 var fast var lookahead1', flush=True)
        print('option name TopK type spin default 8 min 1 max 30', flush=True)
        print('option name Temperature type spin default 20 min 10 max 300', flush=True)
        print('option name AvoidBacktrack type check default true', flush=True)
        print('option name AvoidRepetition type check default true', flush=True)
        print('option name RandomSeed type spin default 1 min 0 max 2147483647', flush=True)
        print('option name HelperEnginePath type string default', flush=True)
        print('option name HelperMode type combo default off var off var blundercheck', flush=True)
        print('option name HelperMoveTimeMs type spin default 350 min 50 max 10000', flush=True)
        print('option name BlunderThresholdCp type spin default 200 min 50 max 2000', flush=True)
        print("uciok", flush=True)

    def isready(self):
        try:
            self._ensure_maia()
        except Exception as e:
            eprint("[maia2-uci] Maia load failed:", e)
        if self.helper_path and self.helper_mode != "off":
            self._ensure_helper()
        print("readyok", flush=True)

    def ucinewgame(self):
        self.board.reset()
        self.last_engine_move = None

    def setoption(self, name, value):
        lname = name.strip().lower()
        value = (value or "").strip()

        if lname == "maiaselfelo":
            try: self.elo_self = int(value)
            except: pass
            return
        if lname == "maiaoppoelo":
            try: self.elo_oppo = int(value)
            except: pass
            return
        if lname == "modeltype":
            v = value.lower()
            if v in ("rapid", "blitz"):
                self.model_type = v
                self.maia._loaded = False
            return
        if lname == "totalmovetimems":
            try: self.total_movetime_ms = max(50, min(10000, int(value)))
            except: pass
            return
        if lname == "strengthmode":
            v = value.lower()
            if v in ("fast","lookahead1"):
                self.strength_mode = v
            return
        if lname == "topk":
            try: self.topk = max(1, min(30, int(value)))
            except: pass
            return
        if lname == "temperature":
            try:
                t = max(10, min(300, int(value)))
                self.temperature = t / 100.0
            except: pass
            return
        if lname == "avoidbacktrack":
            self.avoid_backtrack = value.lower() in ("true","1","yes","on")
            return
        if lname == "avoidrepetition":
            self.avoid_repetition = value.lower() in ("true","1","yes","on")
            return
        if lname == "randomseed":
            try:
                s = int(value)
                self.random_seed = s
                self._rng.seed(os.getpid() ^ int(time.time()*1000) if s == 0 else s)
            except: pass
            return

        if lname == "helperenginepath":
            newp = normalize_engine_path(value)
            if newp != self.helper_path:
                self.helper_path = newp
                if self.helper is not None:
                    self.helper.stop()
                    self.helper = None
            return
        if lname == "helpermode":
            v = value.lower()
            if v in ("off","blundercheck"):
                self.helper_mode = v
                if v == "off" and self.helper is not None:
                    self.helper.stop()
                    self.helper = None
            return
        if lname == "helpermovetimems":
            try: self.helper_movetime_ms = max(50, min(10000, int(value)))
            except: pass
            return
        if lname == "blunderthresholdcp":
            try: self.blunder_threshold_cp = max(50, min(2000, int(value)))
            except: pass
            return

    def position(self, tokens):
        if not tokens:
            return
        idx = 0
        if tokens[0] == "startpos":
            self.board = chess.Board()
            idx = 1
        elif tokens[0] == "fen":
            if len(tokens) < 7:
                return
            fen = " ".join(tokens[1:7])
            try:
                self.board = chess.Board(fen=fen)
            except Exception:
                return
            idx = 7
        else:
            return

        if idx < len(tokens) and tokens[idx] == "moves":
            for mv in tokens[idx+1:]:
                try: self.board.push_uci(mv)
                except Exception: break

    def _maia_infer(self, board: chess.Board):
        fen = board.fen()
        out = self.maia.inference_each(fen, self.elo_self, self.elo_oppo)
        if isinstance(out, tuple) and len(out) >= 2:
            return out[0], out[1]
        if isinstance(out, tuple) and len(out) >= 1:
            return out[0], None
        return out, None

    def _legal_items(self, move_probs):
        legal = [m.uci() for m in self.board.legal_moves]
        inv = _inverse_uci(self.last_engine_move) if self.avoid_backtrack else ""
        items = []
        for u in legal:
            if inv and u == inv:
                continue
            items.append((u, float(move_probs.get(u, 0.0))))
        items.sort(key=lambda x: x[1], reverse=True)
        return items

    def _creates_repetition(self, uci_move: str) -> bool:
        if not self.avoid_repetition:
            return False
        try:
            mv = chess.Move.from_uci(uci_move)
            if mv not in self.board.legal_moves:
                return False
            b2 = self.board.copy(stack=True)
            b2.push(mv)
            return b2.is_repetition(2)
        except Exception:
            return False

    def _sample_from(self, items):
        items_pos = [(u, p) for u, p in items if p > 0.0 and not self._creates_repetition(u)]
        if not items_pos:
            items_pos = [(u, p) for u, p in items if p > 0.0]
        if not items_pos:
            return items[0][0] if items else None

        eps = 1e-12
        T = max(0.10, float(self.temperature))
        logits = []
        max_log = None
        for u, p in items_pos[:60]:
            lp = math.log(p + eps) / T
            logits.append((u, lp))
            max_log = lp if max_log is None else max(max_log, lp)

        total = 0.0
        moves = []
        weights = []
        for u, lp in logits:
            w = math.exp(lp - max_log)
            moves.append(u)
            weights.append(w)
            total += w

        r = self._rng.random() * total
        acc = 0.0
        for u, w in zip(moves, weights):
            acc += w
            if acc >= r:
                return u
        return moves[-1]

    def _score_reply_position(self, board_after: chess.Board) -> float:
        _, winprob2 = self._maia_infer(board_after)
        if isinstance(winprob2, (float, int)):
            return -float(winprob2)
        return 0.0

    def choose_move(self, deadline: float) -> str:
        move_probs, _ = self._maia_infer(self.board)
        items = self._legal_items(move_probs)
        if not items:
            return None

        if self.strength_mode == "fast":
            return self._sample_from(items)

        k = min(self.topk, len(items))
        candidates = items[:k]

        best_move = candidates[0][0]
        best_score = -1e18

        for uci_move, p1 in candidates:
            if time.perf_counter() > (deadline - 0.02):
                break
            rep_pen = -0.25 if (self.avoid_repetition and self._creates_repetition(uci_move)) else 0.0
            try:
                mv = chess.Move.from_uci(uci_move)
                if mv not in self.board.legal_moves:
                    continue
                b2 = self.board.copy(stack=False)
                b2.push(mv)
                s2 = self._score_reply_position(b2)
                tie = 0.05 * math.log(max(p1, 1e-12))
                score = s2 + tie + rep_pen
                if score > best_score:
                    best_score = score
                    best_move = uci_move
            except Exception:
                continue

        return best_move

    def _helper_score_move(self, maia_move: str, movetime_ms: int):
        if not self._ensure_helper():
            return None, None, None
        fen = self.board.fen()

        self.helper.send(f"position fen {fen}")
        self.helper.send(f"go movetime {movetime_ms}")
        best, best_cp = self.helper.read_until_bestmove(timeout=max(0.2, movetime_ms/1000.0 + 0.6))

        maia_cp = None
        if maia_move:
            self.helper.send(f"position fen {fen}")
            self.helper.send(f"go movetime {movetime_ms} searchmoves {maia_move}")
            _bm2, maia_cp = self.helper.read_until_bestmove(timeout=max(0.2, movetime_ms/1000.0 + 0.6))

        return best, best_cp, maia_cp

    def _material_diff_pawns(self) -> int:
        """Material advantage (pawns=1, N/B=3, R=5, Q=9) for side to move."""
        if self.board is None:
            return 0
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        stm = self.board.turn
        my_pts = 0
        op_pts = 0
        for ptype, val in values.items():
            my_pts += val * len(self.board.pieces(ptype, stm))
            op_pts += val * len(self.board.pieces(ptype, not stm))
        return my_pts - op_pts

    def _find_mate_in_1(self):
        """Return a legal move that mates immediately, if any."""
        try:
            for mv in self.board.legal_moves:
                b2 = self.board.copy(stack=False)
                b2.push(mv)
                if b2.is_checkmate():
                    return mv.uci()
        except Exception:
            return None
        return None

    def _helper_bestmove_and_cp(self, movetime_ms: int):
        """Ask helper for best move in current position. Returns (uci, cp_or_mate)."""
        if not self._ensure_helper():
            return None, None
        fen = self.board.fen()
        self.helper.send(f"position fen {fen}")
        self.helper.send(f"go movetime {movetime_ms}")
        best, best_cp = self.helper.read_until_bestmove(timeout=max(0.2, movetime_ms/1000.0 + 0.6))
        return best, best_cp

    def _helper_eval_move_cp(self, uci_move: str, movetime_ms: int):
        """Evaluate a specific move using helper 'searchmoves'. Returns cp_or_mate (higher is better for side to move)."""
        if not uci_move or not self._ensure_helper():
            return None
        fen = self.board.fen()
        self.helper.send(f"position fen {fen}")
        self.helper.send(f"go movetime {movetime_ms} searchmoves {uci_move}")
        _bm, cp = self.helper.read_until_bestmove(timeout=max(0.2, movetime_ms/1000.0 + 0.6))
        return cp

    def go(self, tokens):
        start = time.perf_counter()
        deadline = start + (self.total_movetime_ms / 1000.0)

        # Ensure Maia is loaded
        try:
            self._ensure_maia()
        except Exception as e:
            eprint("[maia2-uci] Maia load failed on go:", e)
            remaining = deadline - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
            print("bestmove 0000", flush=True)
            return

        # 1) Instant mate-in-1 (cheap, fixes many embarrassing misses)
        mate1 = self._find_mate_in_1()
        if mate1:
            remaining = deadline - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
            self.last_engine_move = mate1
            print(f"bestmove {mate1}", flush=True)
            return

        # Conversion mode if up >= +8 pawns in material
        diff = self._material_diff_pawns()
        conversion_mode = (diff >= 8)

        chosen = None

        # 2) Conversion mode: prioritize objective conversion / mating.
        #    Still tries to keep Maia flavor by preferring Maia if close to helper eval.
        if conversion_mode and self.helper_mode == "blundercheck" and self.helper_path:
            remaining_ms = int(max(0, (deadline - time.perf_counter()) * 1000))
            helper_ms = min(max(self.helper_movetime_ms, int(self.total_movetime_ms * 0.75)), remaining_ms)

            hb, hb_cp = (None, None)
            if helper_ms >= 80:
                hb, hb_cp = self._helper_bestmove_and_cp(helper_ms)

            # if helper sees a forced mate for us, take it immediately
            if hb and hb_cp is not None and hb_cp >= 90000:
                chosen = hb
            else:
                try:
                    chosen_maia = self.choose_move(deadline)
                except Exception:
                    chosen_maia = None

                maia_cp = None
                if chosen_maia and helper_ms >= 120:
                    eval_ms = max(80, min(200, helper_ms // 3))
                    maia_cp = self._helper_eval_move_cp(chosen_maia, eval_ms)

                # If Maia is within 80cp of helper, keep Maia (style). Otherwise take helper.
                if hb and hb_cp is not None and maia_cp is not None:
                    chosen = chosen_maia if (hb_cp - maia_cp) <= 80 else hb
                else:
                    chosen = chosen_maia or hb

        # 3) Normal mode: Maia move + blundercheck helper
        if chosen is None:
            try:
                chosen = self.choose_move(deadline)
            except Exception as e:
                eprint("[maia2-uci] choose_move error:", e)

            if chosen and self.helper_mode == "blundercheck" and self.helper_path:
                remaining_ms = int(max(0, (deadline - time.perf_counter()) * 1000))
                helper_ms = min(self.helper_movetime_ms, remaining_ms)
                if helper_ms >= 80:
                    try:
                        best, best_cp, maia_cp = self._helper_score_move(chosen, helper_ms)
                        if best and best_cp is not None and best_cp >= 90000:
                            chosen = best
                        elif best and maia_cp is not None and best_cp is not None:
                            if (best_cp - maia_cp) >= self.blunder_threshold_cp:
                                chosen = best
                    except Exception as e:
                        eprint("[maia2-uci] Helper error:", e)

        remaining = deadline - time.perf_counter()
        if remaining > 0:
            time.sleep(remaining)

        self.last_engine_move = chosen
        print(f"bestmove {chosen if chosen else '0000'}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="blitz", choices=["rapid", "blitz"])
    args = ap.parse_args()

    eng = Maia2UCIEngine(model_type=args.model)

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        cmd, rest = parts[0], parts[1:]

        if cmd == "uci":
            eng.uci()
        elif cmd == "isready":
            eng.isready()
        elif cmd == "ucinewgame":
            eng.ucinewgame()
        elif cmd == "setoption":
            try:
                name_idx = rest.index("name")
                value_idx = rest.index("value") if "value" in rest else None
                if value_idx is None:
                    name = " ".join(rest[name_idx+1:])
                    value = ""
                else:
                    name = " ".join(rest[name_idx+1:value_idx])
                    value = " ".join(rest[value_idx+1:])
                eng.setoption(name, value)
            except Exception:
                pass
        elif cmd == "position":
            eng.position(rest)
        elif cmd == "go":
            eng.go(rest)
        elif cmd == "quit":
            if eng.helper is not None:
                eng.helper.stop()
            break

if __name__ == "__main__":
    main()
