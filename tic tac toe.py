import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random, time, json, math, copy, os
from datetime import datetime

# ---------------- Developers ----------------
DEVELOPERS = ["AJMAL BIN AJMAL", "VINCENT MAKA"]

# ---------------- Config ----------------
GAME_FILE = "game_history.json"
ACTIVITY_FILE = "game_activity_log.json"
FPS = 60

THEME = {
    "bg": "#0a0b0f",
    "panel": "#0d1117",
    "glass": "#0f1622",
    "accent": "#00f6ff",
    "neon_x": "#ffd84d",
    "neon_o": "#c7cbd0",
    "muted": "#1f2329",
    "text": "#e6fbff",
    "win_glow": "#8cffb6",
    "particle_start": ["#00f6ff", "#8cffb6", "#ff7ad9", "#f6ff5c"]
}

EMOJIS = {
    "move": ["😎","🔥","🤖","✨","😂","💥"],
    "win": ["🏆","🎉","✨","🥳"],
    "draw": ["🤝","😐"]
}

# ---------------- Persistence / Activity Logging ----------------
def _safe_read_json(path):
    try:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _safe_write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_history():
    return _safe_read_json(GAME_FILE)

def append_history(record):
    hist = _safe_read_json(GAME_FILE)
    hist.append(record)
    _safe_write_json(GAME_FILE, hist)

def log_activity(entry):
    """
    Append an activity entry to ACTIVITY_FILE. Entry should be serializable.
    We keep this robust (no exceptions escaping).
    """
    try:
        data = _safe_read_json(ACTIVITY_FILE)
        data.append(entry)
        _safe_write_json(ACTIVITY_FILE, data)
    except Exception:
        # swallow errors to avoid breaking gameplay
        pass

# ---------------- Game Logic ----------------
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.current = "X"
        self.started_at = None
        self.ended_at = None
        self.winner = None
        self.win_line = None
        self.over = False

    def make_move(self, r, c):
        if self.over or self.board[r][c] != "":
            return False
        if self.started_at is None:
            self.started_at = datetime.utcnow().isoformat()
        self.board[r][c] = self.current
        self._update_state()
        if not self.over:
            self.current = "O" if self.current == "X" else "X"
        else:
            self.ended_at = datetime.utcnow().isoformat()
        return True

    def _update_state(self):
        b = self.board
        lines = []
        coords = []
        for i in range(3):
            lines.append(b[i][:]); coords.append([(i,0),(i,1),(i,2)])
            lines.append([b[r][i] for r in range(3)]); coords.append([(0,i),(1,i),(2,i)])
        lines.append([b[i][i] for i in range(3)]); coords.append([(0,0),(1,1),(2,2)])
        lines.append([b[i][2-i] for i in range(3)]); coords.append([(0,2),(1,1),(2,0)])
        for line,cd in zip(lines, coords):
            if line[0] != "" and line.count(line[0]) == 3:
                self.over = True
                self.winner = line[0]
                self.win_line = cd
                return
        filled = all(b[r][c] != "" for r in range(3) for c in range(3))
        if filled:
            self.over = True
            self.winner = None
            self.win_line = None

# ---------------- AI ----------------
def ai_easy(state):
    opts = [(r,c) for r in range(3) for c in range(3) if state.board[r][c] == ""]
    return random.choice(opts) if opts else None

def ai_medium(state, player="O"):
    opponent = "X" if player == "O" else "O"
    def can_win_by(r,c,p):
        ng = copy.deepcopy(state)
        ng.board[r][c] = p
        ng._update_state()
        return ng.winner == p
    for r in range(3):
        for c in range(3):
            if state.board[r][c] == "" and can_win_by(r,c,player):
                return (r,c)
    for r in range(3):
        for c in range(3):
            if state.board[r][c] == "" and can_win_by(r,c,opponent):
                return (r,c)
    if random.random() < 0.4:
        return ai_easy(state)
    return ai_easy(state)

def ai_hard(state, player="O"):
    opponent = "X" if player == "O" else "O"
    def score(g):
        if g.winner == player: return 1
        if g.winner == opponent: return -1
        return 0
    def minimax(g, maximizing):
        if g.over:
            return score(g), None
        best_move = None
        if maximizing:
            val = -2
            for r in range(3):
                for c in range(3):
                    if g.board[r][c] == "":
                        ng = copy.deepcopy(g)
                        ng.board[r][c] = player
                        ng._update_state()
                        s,_ = minimax(ng, False)
                        if s > val:
                            val = s; best_move = (r,c)
                        if val == 1: return val, best_move
            return val, best_move
        else:
            val = 2
            for r in range(3):
                for c in range(3):
                    if g.board[r][c] == "":
                        ng = copy.deepcopy(g)
                        ng.board[r][c] = opponent
                        ng._update_state()
                        s,_ = minimax(ng, True)
                        if s < val:
                            val = s; best_move = (r,c)
                        if val == -1: return val, best_move
            return val, best_move
    val, mv = minimax(copy.deepcopy(state), True)
    if mv is None: return ai_easy(state)
    return mv

# ---------------- Particles (Enhanced) ----------------
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(2.0, 9.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(0,2)
        self.size = random.uniform(2,7)
        self.life = random.uniform(0.6, 1.6)
        self.age = 0.0
        self.color = color
        self.history = [(x,y)]
        self.max_hist = 6

    def step(self, dt):
        self.age += dt
        self.vx *= (1 - 0.03*dt*60)
        self.vy *= (1 - 0.02*dt*60)
        self.vy += 0.15 * dt * 60
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.history.append((self.x, self.y))
        if len(self.history) > self.max_hist:
            self.history.pop(0)

    def alive(self):
        return self.age < self.life

# ---------------- Leaderboard ----------------
def compute_leaderboard(history):
    stats = {}
    for h in history:
        players = h.get("players", [])
        if not players or len(players) < 2: continue
        p1,p2 = players[0],players[1]
        for p in (p1,p2): stats.setdefault(p,{"wins":0,"losses":0,"draws":0,"games":0})
        w = h.get("winner")
        if w == "X": stats[p1]["wins"] +=1; stats[p2]["losses"] +=1
        elif w == "O": stats[p2]["wins"] +=1; stats[p1]["losses"] +=1
        else: stats[p1]["draws"] +=1; stats[p2]["draws"] +=1
        stats[p1]["games"] +=1; stats[p2]["games"] +=1
    board = sorted([(p,v) for p,v in stats.items()], key=lambda x:(-x[1]["wins"],-x[1]["games"],x[0]))
    return board

# ---------------- Main App ----------------
class NeonTicTacToeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Neon Tic-Tac-Toe — Premium")
        self.configure(bg=THEME["bg"])
        self.geometry("820x920")
        self.minsize(560,700)

        self.state = GameState()
        self.mode = "AI"
        self.difficulty = "Hard"
        self.p1 = "Player 1"
        self.p2 = "Computer"
        self.moves_log = []
        self.match_started = False
        self.last_saved = None

        self.particles = []
        self.hover = None
        self.cell_rects = [[(0,0,0,0) for _ in range(3)] for __ in range(3)]
        self._last_time = time.time()

        self._build_ui()
        # log app start
        log_activity({"type":"app_start","time":datetime.utcnow().isoformat(),"developers":DEVELOPERS})
        self.after(120, self._open_start_dialog)
        self._tick()

    def _build_ui(self):
        # Top control bar
        top = tk.Frame(self, bg=THEME["panel"], bd=0)
        top.pack(fill="x", padx=12, pady=10)
        self.banner = tk.Label(top, text="", bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI", 18, "bold"))
        self.banner.pack(side="left", padx=8)
        self.banner_emoji = tk.Label(top, text="", bg=THEME["panel"], fg=THEME["accent"], font=("Segoe UI Emoji", 20))
        self.banner_emoji.pack(side="left", padx=6)

        ctrl = tk.Frame(top, bg=THEME["panel"]) ; ctrl.pack(side="right")
        ttk.Button(ctrl, text="Change", command=self._open_start_dialog).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Next", command=self.next_round).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Reset", command=self.reset_match).pack(side="left", padx=6)
        ttk.Button(ctrl, text="Leaderboard", command=self.show_leaderboard).pack(side="left", padx=6)

        # Canvas
        self.canvas = tk.Canvas(self, bg=THEME["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=8)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))

        # Status and footer (developers)
        self.status = tk.Label(self, text="", bg=THEME["bg"], fg=THEME["text"], font=("Segoe UI", 12))
        self.status.pack(pady=(6,6))
        footer_text = "Developed by: " + " & ".join(DEVELOPERS)
        self.footer = tk.Label(self, text=footer_text, bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 10))
        self.footer.pack(pady=(0,10))
        self._update_banner()

    def _open_start_dialog(self):
        dlg = StartDialog(self, default_mode=self.mode, default_diff=self.difficulty, default_names={"X":self.p1,"O":self.p2})
        self.wait_window(dlg)
        if dlg.result is None: return
        r = dlg.result
        self.mode = r["mode"]
        self.difficulty = r["difficulty"]
        if self.mode == "PVP":
            self.p1 = r["names"]["p1"] or "Player 1"
            self.p2 = r["names"]["p2"] or "Player 2"
        else:
            self.p1 = r["names"]["p1"] or "You"
            self.p2 = "Computer"
        # reset logs & state
        self.moves_log = []
        self.match_started = False
        self.state.reset()
        self.last_saved = None
        self._update_banner()
        self._redraw()
        self.status.config(text=f"{self.p1} (X) to move — {self.difficulty}")
        log_activity({"type":"match_start","mode":self.mode,"difficulty":self.difficulty,"players":[self.p1,self.p2],"time":datetime.utcnow().isoformat()})

    def _update_banner(self):
        self.banner.config(text=f"{self.p1} (X)   ✦   {self.p2} (O)")
        self.banner_emoji.config(text=random.choice(EMOJIS["move"]))

    def _on_resize(self, event):
        w = self.canvas.winfo_width(); h = self.canvas.winfo_height()
        size = min(w, h) * 0.8
        left = (w - size) / 2; top = (h - size) / 2
        cell = size / 3
        for r in range(3):
            for c in range(3):
                x1 = left + c*cell; y1 = top + r*cell; x2 = x1 + cell; y2 = y1 + cell
                self.cell_rects[r][c] = (x1,y1,x2,y2)
        self._redraw()

    def _coords_to_cell(self, x, y):
        for r in range(3):
            for c in range(3):
                x1,y1,x2,y2 = self.cell_rects[r][c]
                if x1 <= x <= x2 and y1 <= y <= y2: return (r,c)
        return None

    def _on_mouse_move(self, event):
        cell = self._coords_to_cell(event.x, event.y)
        self._set_hover(cell)

    def _set_hover(self, cell):
        if cell != self.hover:
            self.hover = cell
            # no immediate redraw here; main loop will redraw

    def _on_click(self, event):
        if self.state.over: return
        pos = self._coords_to_cell(event.x, event.y)
        if not pos: return
        r,c = pos
        if self.state.board[r][c] != "": return
        if not self.match_started:
            self.match_started = True
            self.state.started_at = datetime.utcnow().isoformat()
            log_activity({"type":"match_started_by_first_move","time":datetime.utcnow().isoformat(),"players":[self.p1,self.p2]})
        mark = self.state.current
        ok = self.state.make_move(r,c)
        if not ok: return
        move_entry = {"index": len(self.moves_log)+1, "mark": mark, "player": (self.p1 if mark=="X" else self.p2), "r":r, "c":c, "ts": datetime.utcnow().isoformat()}
        self.moves_log.append(move_entry)
        log_activity({"type":"move","detail":move_entry})
        self._spawn_move_emoji(r,c)
        if self.state.over:
            self._on_game_end()
            return
        if self.mode == "AI" and self.state.current == "O" and self.p2 == "Computer":
            # schedule AI move slightly delayed for UX
            self.after(260, self._ai_move)

    def _ai_move(self):
        if self.state.over: return
        if self.difficulty == "Easy": mv = ai_easy(self.state)
        elif self.difficulty == "Medium": mv = ai_medium(self.state, player="O")
        else: mv = ai_hard(self.state, player="O")
        if not mv: mv = ai_easy(self.state)
        r,c = mv
        ok = self.state.make_move(r,c)
        if not ok:
            return
        move_entry = {"index": len(self.moves_log)+1, "mark": "O", "player": self.p2, "r":r, "c":c, "ts": datetime.utcnow().isoformat()}
        self.moves_log.append(move_entry)
        log_activity({"type":"ai_move","detail":move_entry})
        self._spawn_move_emoji(r,c)
        if self.state.over:
            self._on_game_end()
        else:
            self.status.config(text=f"{self.p1 if self.state.current=='X' else self.p2} to move")

    def _on_game_end(self):
        if self.state.winner is None:
            emoji = random.choice(EMOJIS["draw"]); comment = "It's a draw!"; result = "Draw"
        else:
            winner_name = self.p1 if self.state.winner == "X" else self.p2
            emoji = random.choice(EMOJIS["win"]); comment = f"{winner_name} wins! {emoji}"; result = "Win"
        # spawn particles along win line or center
        if self.state.win_line:
            for (r,c) in self.state.win_line:
                self._spawn_particles_at_cell(r,c, count=8)
        else:
            self._spawn_center_particles(48)
        self._spawn_center_emoji(emoji)
        self.status.config(text=comment)
        self.state.ended_at = datetime.utcnow().isoformat()
        rec = {"timestamp": datetime.utcnow().isoformat(), "players": [self.p1, self.p2], "winner": (self.state.winner if self.state.winner else "Draw"), "moves": self.moves_log, "mode": self.mode, "difficulty": self.difficulty, "started_at": self.state.started_at, "ended_at": self.state.ended_at}
        append_history(rec)
        self.last_saved = rec
        log_activity({"type":"game_end","result":rec})
        # overlay show
        self.after(60, lambda: setattr(self, '_show_result_overlay', True))
        self.after(2200, lambda: setattr(self, '_show_result_overlay', False))

    # ----------- Drawing primitives (neon glow) -----------
    def _draw_glow_text(self, x,y, text, font, base_color, glow_color, layers=5):
        for i in range(layers,0,-1):
            self.canvas.create_text(x+i*0.6,y+i*0.6, text=text, font=font, fill=glow_color)
        self.canvas.create_text(x,y, text=text, font=font, fill=base_color)

    def _draw_X(self,x1,y1,x2,y2):
        cx,cy = (x1+x2)/2,(y1+y2)/2
        hw = (x2-x1)/2 - (min(x2-x1,y2-y1)/7)
        neon = THEME["neon_x"]
        for w in (20,12,6,3):
            self.canvas.create_line(cx-hw, cy-hw, cx+hw, cy+hw, fill=neon, width=w, capstyle="round")
            self.canvas.create_line(cx-hw, cy+hw, cx+hw, cy-hw, fill=neon, width=w, capstyle="round")
        self.canvas.create_line(cx-hw, cy-hw, cx+hw, cy+hw, fill="#fff6d1", width=1.5, capstyle="round")

    def _draw_O(self,x1,y1,x2,y2):
        cx,cy = (x1+x2)/2,(y1+y2)/2
        rad = min((x2-x1),(y2-y1))/2 - (min(x2-x1,y2-y1)/7)
        neon = THEME["neon_o"]
        for i in range(4):
            r = rad + (i*3)
            w = max(2, 10 - i*2)
            col = neon if i>1 else THEME["accent"]
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=col, width=w)
        self.canvas.create_oval(cx-r+6, cy-r+6, cx+r-6, cy+r-6, outline="#ffffff", width=1)

    # ----------- Particles spawning -----------
    def _spawn_center_particles(self, count=18):
        w = self.canvas.winfo_width(); h = self.canvas.winfo_height(); cx=w/2; cy=h/2
        for _ in range(count):
            color = random.choice(THEME["particle_start"])
            p = Particle(cx + random.uniform(-10,10), cy + random.uniform(-10,10), color)
            self.particles.append(p)

    def _spawn_particles_at_cell(self, r, c, count=10):
        x1,y1,x2,y2 = self.cell_rects[r][c]
        cx,cy = (x1+x2)/2, (y1+y2)/2
        for _ in range(count):
            color = random.choice(THEME["particle_start"])
            p = Particle(cx + random.uniform(-6,6), cy + random.uniform(-6,6), color)
            self.particles.append(p)

    def _spawn_move_emoji(self, r, c):
        x1,y1,x2,y2 = self.cell_rects[r][c]
        cx,cy = (x1+x2)/2, (y1+y2)/2
        txt = random.choice(EMOJIS["move"]) ; tag = f"emoji_{time.time()}"
        self.canvas.create_text(cx, cy - 12, text=txt, font=("Segoe UI Emoji", 28), tags=tag)
        self.after(700, lambda t=tag: self.canvas.delete(t))
        self._spawn_particles_at_cell(r,c, count=6)

    def _spawn_center_emoji(self, emoji):
        w = self.canvas.winfo_width(); h = self.canvas.winfo_height(); cx,cy = w/2, h/2
        tag = f"cent_{time.time()}"
        self.canvas.create_text(cx, cy - 28, text=emoji, font=("Segoe UI Emoji", 64), tags=tag)
        self.after(1400, lambda t=tag: self.canvas.delete(t))

    # ----------- Particle rendering -----------
    def _draw_particles(self):
        if not self.particles: return
        dt = 1.0 / FPS
        to_remove = []
        for p in self.particles:
            p.step(dt)
            if not p.alive():
                to_remove.append(p); continue
            pts = p.history
            for i in range(len(pts)-1):
                x1,y1 = pts[i]; x2,y2 = pts[i+1]
                w = max(1, int((i+1)/2))
                self.canvas.create_line(x1,y1,x2,y2, fill=p.color, width=w, capstyle="round")
            s = max(1, int(p.size * (1.0 - p.age/p.life) + 0.5))
            self.canvas.create_oval(p.x-s, p.y-s, p.x+s, p.y+s, fill=p.color, outline="")
        for r in to_remove:
            if r in self.particles: self.particles.remove(r)

    # ----------- High level redraw ----------
    def _redraw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width(); h = self.canvas.winfo_height()
        # subtle background
        self.canvas.create_rectangle(0,0,w,h, fill=THEME["bg"], outline="")
        # draw board tiles
        for r in range(3):
            for c in range(3):
                x1,y1,x2,y2 = self.cell_rects[r][c]
                self.canvas.create_rectangle(x1+6,y1+6,x2-6,y2-6, fill=THEME["glass"], outline=THEME["muted"], width=2)
                self.canvas.create_line(x1+8, y1+8, x2-8, y1+8, fill="#0f2533", width=2)
                self.canvas.create_line(x1+8, y2-8, x2-8, y2-8, fill="#071017", width=2)
                if self.hover == (r,c) and not self.state.over and self.state.board[r][c] == "":
                    self.canvas.create_rectangle(x1+12,y1+12,x2-12,y2-12, outline=THEME["accent"], width=3)
                mark = self.state.board[r][c]
                if mark == "X": self._draw_X(x1,y1,x2,y2)
                elif mark == "O": self._draw_O(x1,y1,x2,y2)
        # draw particles
        self._draw_particles()
        # result overlay
        if getattr(self, '_show_result_overlay', False):
            self._draw_result_overlay()
        if random.random() < 0.12:
            self.banner_emoji.config(text=random.choice(EMOJIS["move"]))

    def _draw_result_overlay(self):
        w = self.canvas.winfo_width(); h = self.canvas.winfo_height()
        self.canvas.create_rectangle(0,0,w,h, fill="#07121a", outline="", stipple="gray25")
        self.canvas.create_oval(-w*0.25, -h*0.4, w*1.25, h*0.6, fill="#000000", outline="", stipple="gray12")
        cx,cy = w/2, h/2
        if self.state.winner is None:
            txt = "DRAW"; sub = "Nobody wins"
        else:
            name = self.p1 if self.state.winner == "X" else self.p2
            txt = f"{name} WINS"; sub = f"{self.state.winner} — Victory"
        self._draw_glow_text(cx, cy-20, txt, ("Segoe UI", 36, "bold"), THEME["text"], THEME["win_glow"], layers=6)
        self.canvas.create_text(cx, cy+32, text=sub, font=("Segoe UI", 14), fill=THEME["accent"])

    # ---------- Controls ----------
    def next_round(self):
        self.state.reset(); self.moves_log = []; self.match_started = False; self.particles.clear(); self._redraw(); self.status.config(text=f"{self.p1} (X) to move")
        log_activity({"type":"next_round","time":datetime.utcnow().isoformat(),"players":[self.p1,self.p2]})

    def reset_match(self):
        self.state.reset(); self.moves_log = []; self.match_started = False; self.particles.clear(); self.last_saved = None; self._redraw(); self.status.config(text="Match reset — new scoreboard")
        log_activity({"type":"reset_match","time":datetime.utcnow().isoformat()})

    def export_last(self):
        if not self.last_saved:
            messagebox.showinfo("No match","No recently saved match to export. Play and finish one match first.") ; return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f: json.dump(self.last_saved, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Exported last match to:\n{path}")
            log_activity({"type":"export","path":path,"time":datetime.utcnow().isoformat()})
        except Exception:
            messagebox.showerror("Error","Failed to export match.")
            log_activity({"type":"export_failed","time":datetime.utcnow().isoformat()})

    def show_leaderboard(self):
        hist = load_history(); board = compute_leaderboard(hist)
        wnd = tk.Toplevel(self); wnd.title("Leaderboard"); wnd.geometry("520x420"); wnd.configure(bg=THEME["panel"])
        lbl = tk.Label(wnd, text="Leaderboard — Top Players", bg=THEME["panel"], fg=THEME["text"], font=("Segoe UI",14,"bold")) ; lbl.pack(pady=8)
        frame = tk.Frame(wnd, bg=THEME["panel"]) ; frame.pack(fill="both", expand=True, padx=12, pady=8)
        cols = ("Player","Wins","Draws","Losses","Games")
        header = tk.Frame(frame, bg=THEME["panel"]) ; header.pack(fill="x")
        for i,c in enumerate(cols): tk.Label(header, text=c, bg=THEME["panel"], fg=THEME["accent"], font=("Segoe UI",11,"bold")).grid(row=0,column=i,padx=8,sticky="w")
        for idx,(name,stat) in enumerate(board[:30], start=1):
            tk.Label(frame, text=name, bg=THEME["panel"], fg=THEME["text"]).grid(row=idx, column=0, sticky="w", padx=8)
            tk.Label(frame, text=str(stat["wins"]), bg=THEME["panel"], fg=THEME["text"]).grid(row=idx, column=1, sticky="w", padx=8)
            tk.Label(frame, text=str(stat["draws"]), bg=THEME["panel"], fg=THEME["text"]).grid(row=idx, column=2, sticky="w", padx=8)
            tk.Label(frame, text=str(stat["losses"]), bg=THEME["panel"], fg=THEME["text"]).grid(row=idx, column=3, sticky="w", padx=8)
            tk.Label(frame, text=str(stat["games"]), bg=THEME["panel"], fg=THEME["text"]).grid(row=idx, column=4, sticky="w", padx=8)
        log_activity({"type":"leaderboard_open","time":datetime.utcnow().isoformat(),"players":[self.p1,self.p2]})

    # ---------- Main tick ----------
    def _tick(self):
        now = time.time(); dt = now - self._last_time; self._last_time = now
        self._redraw()
        self.after(int(1000/FPS), self._tick)

# ---------------- Start Dialog ----------------
class StartDialog(tk.Toplevel):
    def __init__(self, parent, default_mode="AI", default_diff="Hard", default_names=None):
        super().__init__(parent)
        self.transient(parent); self.grab_set(); self.title("Start Match"); self.configure(bg=THEME["bg"])
        self.resizable(False, False); self.result = None
        if default_names is None: default_names = {"X":"Player 1","O":"Computer"}
        tk.Label(self, text="Select Mode & Difficulty", bg=THEME["bg"], fg=THEME["text"], font=("Segoe UI",14,"bold")).pack(padx=12,pady=10)
        mf = tk.Frame(self, bg=THEME["bg"]) ; mf.pack(padx=12,pady=6)
        tk.Label(mf, text="Mode:", bg=THEME["bg"], fg=THEME["text"]).grid(row=0,column=0, sticky="w")
        self.mode_var = tk.StringVar(value=default_mode)
        ttk.Radiobutton(mf, text="Play vs Computer", variable=self.mode_var, value="AI").grid(row=0,column=1, padx=6)
        ttk.Radiobutton(mf, text="Play with Friend", variable=self.mode_var, value="PVP").grid(row=0,column=2, padx=6)
        tk.Label(mf, text="AI Difficulty:", bg=THEME["bg"], fg=THEME["text"]).grid(row=1,column=0, sticky="w", pady=6)
        self.diff_var = tk.StringVar(value=default_diff)
        ttk.Radiobutton(mf, text="Easy", variable=self.diff_var, value="Easy").grid(row=1,column=1)
        ttk.Radiobutton(mf, text="Medium", variable=self.diff_var, value="Medium").grid(row=1,column=2)
        ttk.Radiobutton(mf, text="Hard", variable=self.diff_var, value="Hard").grid(row=1,column=3)
        nf = tk.Frame(self, bg=THEME["bg"]) ; nf.pack(padx=12,pady=8)
        tk.Label(nf, text="Player 1 (X):", bg=THEME["bg"], fg=THEME["text"]).grid(row=0,column=0, sticky="w", pady=6)
        self.e1 = tk.Entry(nf) ; self.e1.grid(row=0,column=1, padx=6)
        tk.Label(nf, text="Player 2 / Computer (O):", bg=THEME["bg"], fg=THEME["text"]).grid(row=1,column=0, sticky="w", pady=6)
        self.e2 = tk.Entry(nf) ; self.e2.grid(row=1,column=1, padx=6)
        self.e1.insert(0, default_names.get("X","Player 1")) ; self.e2.insert(0, default_names.get("O","Computer"))
        bf = tk.Frame(self, bg=THEME["bg"]) ; bf.pack(pady=8)
        tk.Button(bf, text="Start", command=self._on_ok).pack(side="right", padx=8)
        tk.Button(bf, text="Cancel", command=self._on_cancel).pack(side="right")
        self.mode_var.trace_add("write", lambda *a: self._update_entries())
        self._update_entries()

    def _update_entries(self):
        if self.mode_var.get() == "AI":
            self.e2.delete(0, "end"); self.e2.insert(0, "Computer"); self.e2.config(state="disabled")
        else:
            self.e2.config(state="normal")

    def _on_ok(self):
        mode = self.mode_var.get(); diff = self.diff_var.get()
        names = {"p1": self.e1.get().strip() or "Player 1", "p2": self.e2.get().strip() or ("Computer" if mode=="AI" else "Player 2")}
        self.result = {"mode":mode, "difficulty":diff, "names":names}
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

# ---------------- Run ----------------
if __name__ == "__main__":
    app = NeonTicTacToeApp()
    app.mainloop()
