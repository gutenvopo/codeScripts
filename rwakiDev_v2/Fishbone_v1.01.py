import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import math
import pathlib

# ─── Asset paths ──────────────────────────────────────────────────────────────
_HERE = pathlib.Path(__file__).parent
ICON_ICO = _HERE / "assets" / "icon.ico"
ICON_PNG = _HERE / "assets" / "icon_256.png"

# ─── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0F1117"
PANEL_BG  = "#1A1D2E"
CANVAS_BG = "#13162B"
ACCENT    = "#4F8EF7"
ACCENT3   = "#4FF7A0"
TEXT      = "#E8EAF6"
MUTED     = "#6B7280"
BORDER    = "#2D3250"
HEAD_CLR  = "#F7874F"
SPINE_CLR = "#4F8EF7"
BRANCH_COLORS = [
    "#4F8EF7","#F7874F","#4FF7A0","#F74F8E",
    "#F7E44F","#AF4FF7","#4FF7E4","#F7A44F",
]

FONT_TITLE = ("Courier New", 18, "bold")
FONT_LABEL = ("Courier New", 11, "bold")
FONT_SMALL = ("Courier New", 9)
FONT_BTN   = ("Courier New", 10, "bold")
FONT_INPUT = ("Courier New", 10)

BRANCH_ANGLE  = 45   # degrees – branch rises from spine
SUB_RIB_ANGLE = 60   # degrees – sub-rib departs from branch
CAUSE_FONT_SZ  = 10
BRANCH_FONT_SZ = 12
CAUSE_LABEL_W  = 140  # text wrap width (unscaled px) — fits ~13 chars per line


# ─── Model ────────────────────────────────────────────────────────────────────
class FishboneDiagram:
    def __init__(self):
        self.problem = "Problem / Effect"
        self.branches: list[dict] = []
        self._init_defaults()

    def _init_defaults(self):
        defaults = [
            ("People",      ["Training", "Experience", "Motivation"]),
            ("Process",     ["Workflow", "Procedure", "Control"]),
            ("Materials",   ["Quality", "Availability", "Storage"]),
            ("Machine",     ["Maintenance", "Calibration", "Age"]),
            ("Method",      ["Standard", "Documentation"]),
            ("Environment", ["Temperature", "Humidity"]),
        ]
        for name, causes in defaults:
            self.branches.append({"name": name, "causes": list(causes)})

    def add_branch(self, name):      self.branches.append({"name": name, "causes": []})
    def remove_branch(self, idx):
        if 0 <= idx < len(self.branches): self.branches.pop(idx)
    def add_cause(self, bi, cause):  self.branches[bi]["causes"].append(cause)
    def remove_cause(self, bi, ci):
        b = self.branches[bi]
        if 0 <= ci < len(b["causes"]): b["causes"].pop(ci)
    def rename_branch(self, idx, name):        self.branches[idx]["name"] = name
    def rename_cause(self, bi, ci, name):      self.branches[bi]["causes"][ci] = name


# ─── App ──────────────────────────────────────────────────────────────────────
class FishboneApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fishbone (Ishikawa) Diagram Analyser")
        self.configure(bg=BG)
        self.geometry("1380x800")
        self.minsize(900, 580)
        # ── Set window icon ───────────────────────────────────────────────────
        try:
            if ICON_ICO.exists():
                self.iconbitmap(str(ICON_ICO))          # Windows / some Linux WMs
            elif ICON_PNG.exists():
                _img = tk.PhotoImage(file=str(ICON_PNG))
                self.iconphoto(True, _img)
                self._icon_ref = _img                   # keep reference alive
        except Exception:
            pass                                        # silently skip if unsupported
        self.model = FishboneDiagram()
        self._zoom = 1.0
        self._build_ui()
        self._draw()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(top, text="◆ FISHBONE ANALYSIS", font=FONT_TITLE, bg=BG, fg=ACCENT).pack(side="left")

        pf = tk.Frame(top, bg=BG); pf.pack(side="left", padx=24)
        tk.Label(pf, text="PROBLEM:", font=FONT_SMALL, bg=BG, fg=MUTED).pack(side="left", padx=(0,4))
        self.prob_var = tk.StringVar(value=self.model.problem)
        pe = tk.Entry(pf, textvariable=self.prob_var, font=FONT_INPUT,
                      bg=PANEL_BG, fg=HEAD_CLR, insertbackground=HEAD_CLR,
                      relief="flat", width=32, bd=4)
        pe.pack(side="left")
        pe.bind("<Return>",   lambda _: self._set_problem())
        pe.bind("<FocusOut>", lambda _: self._set_problem())

        bc = dict(font=FONT_BTN, relief="flat", cursor="hand2", padx=10, pady=5)
        tk.Button(top, text="+ Branch",   bg=ACCENT,   fg=BG,        command=self._add_branch,  **bc).pack(side="right", padx=4)
        tk.Button(top, text="Export Diagram", bg=PANEL_BG, fg=ACCENT,    command=self._export_png,  **bc).pack(side="right", padx=4)
        tk.Button(top, text="Reset Diagram", bg="#0A2D0A", fg="#4FF7A0", command=self._reset_diagram, **bc).pack(side="right", padx=4)
        tk.Button(top, text="Clear All",  bg="#2D0A0A", fg="#F74F4F", command=self._clear_all,   **bc).pack(side="right", padx=4)

        body = tk.Frame(self, bg=BG); body.pack(fill="both", expand=True, padx=10, pady=(10,0))

        # ── Bottom bar: Root Cause / Solution ────────────────────────────────
        bottom = tk.Frame(self, bg=PANEL_BG, pady=8)
        bottom.pack(fill="x", padx=10, pady=(4, 10))
        tk.Label(bottom, text="Root Cause / Solution:", font=FONT_LABEL,
                 bg=PANEL_BG, fg=ACCENT).pack(side="left", padx=(12, 8))
        self.root_cause_var = tk.StringVar()
        tk.Entry(bottom, textvariable=self.root_cause_var, font=FONT_INPUT,
                 bg=BG, fg=TEXT, insertbackground=TEXT, relief="flat",
                 bd=4, width=80).pack(side="left", fill="x", expand=True, padx=(0, 12))

        cw = tk.Frame(body, bg=BORDER, bd=1); cw.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(cw, bg=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self._draw())
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-4>",   self._on_scroll)
        self.canvas.bind("<Button-5>",   self._on_scroll)

        self.sidebar = tk.Frame(body, bg=PANEL_BG, width=245)
        self.sidebar.pack(side="right", fill="y", padx=(8, 0))
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

    def _build_sidebar(self):
        for w in self.sidebar.winfo_children(): w.destroy()
        tk.Label(self.sidebar, text="BRANCHES & CAUSES", font=FONT_LABEL, bg=PANEL_BG, fg=ACCENT).pack(pady=(12,6))

        sbc = tk.Canvas(self.sidebar, bg=PANEL_BG, highlightthickness=0)
        sbs = ttk.Scrollbar(self.sidebar, orient="vertical", command=sbc.yview)
        sbc.configure(yscrollcommand=sbs.set)
        sbs.pack(side="right", fill="y"); sbc.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(sbc, bg=PANEL_BG)
        sbc.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: sbc.configure(scrollregion=sbc.bbox("all")))
        sbc.bind("<MouseWheel>", lambda e: sbc.yview_scroll(-1*(e.delta//120), "units"))

        for bi, branch in enumerate(self.model.branches):
            self._sidebar_branch(inner, bi, branch, BRANCH_COLORS[bi % len(BRANCH_COLORS)])

    def _sidebar_branch(self, parent, bi, branch, clr):
        frame = tk.Frame(parent, bg=PANEL_BG); frame.pack(fill="x", padx=6, pady=(4,0))
        hdr = tk.Frame(frame, bg=BORDER); hdr.pack(fill="x")
        tk.Label(hdr, text="●", bg=BORDER, fg=clr, font=FONT_LABEL).pack(side="left", padx=4)
        tk.Label(hdr, text=branch["name"], bg=BORDER, fg=TEXT, font=FONT_LABEL).pack(side="left")

        def rename(b=bi):
            n = simpledialog.askstring("Rename Branch", "New name:",
                                       initialvalue=self.model.branches[b]["name"], parent=self)
            if n: self.model.rename_branch(b, n); self._refresh()
        def delete(b=bi):
            if messagebox.askyesno("Delete", f"Delete '{self.model.branches[b]['name']}'?", parent=self):
                self.model.remove_branch(b); self._refresh()
        def add_cause(b=bi):
            cc = simpledialog.askstring("Add Cause", f"Cause for '{self.model.branches[b]['name']}':", parent=self)
            if cc: self.model.add_cause(b, cc); self._refresh()

        bc = dict(relief="flat", cursor="hand2", font=FONT_SMALL, padx=4)
        tk.Button(hdr, text="✏", bg=BORDER, fg=ACCENT,    command=rename,    **bc).pack(side="right")
        tk.Button(hdr, text="✕", bg=BORDER, fg="#F74F4F", command=delete,    **bc).pack(side="right")
        tk.Button(hdr, text="+", bg=BORDER, fg=ACCENT3,   command=add_cause, **bc).pack(side="right")

        for ci, cause in enumerate(branch["causes"]):
            row = tk.Frame(frame, bg=PANEL_BG); row.pack(fill="x", padx=(16,0))
            tk.Label(row, text="—", bg=PANEL_BG, fg=clr, font=FONT_SMALL).pack(side="left")
            tk.Label(row, text=cause, bg=PANEL_BG, fg=TEXT, font=FONT_SMALL,
                     wraplength=140, justify="left").pack(side="left", padx=2)
            def rc(b=bi, c=ci):
                n = simpledialog.askstring("Rename Cause", "New name:",
                                           initialvalue=self.model.branches[b]["causes"][c], parent=self)
                if n: self.model.rename_cause(b, c, n); self._refresh()
            def dc(b=bi, c=ci): self.model.remove_cause(b, c); self._refresh()
            tk.Button(row, text="✏", bg=PANEL_BG, fg=MUTED,    command=rc, relief="flat", cursor="hand2", font=FONT_SMALL).pack(side="right")
            tk.Button(row, text="✕", bg=PANEL_BG, fg="#F74F4F", command=dc, relief="flat", cursor="hand2", font=FONT_SMALL).pack(side="right")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=6, pady=2)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _set_problem(self):
        self.model.problem = self.prob_var.get() or "Problem / Effect"; self._draw()
    def _add_branch(self):
        n = simpledialog.askstring("Add Branch", "Branch / Category name:", parent=self)
        if n: self.model.add_branch(n); self._refresh()
    def _clear_all(self):
        if messagebox.askyesno("Clear All", "Remove all branches and causes?", parent=self):
            self.model.branches.clear(); self._refresh()
    def _reset_diagram(self):
        if messagebox.askyesno("Reset Diagram", "Reset to the default example diagram?", parent=self):
            self.model.branches.clear()
            self.model.problem = "Problem / Effect"
            self.prob_var.set(self.model.problem)
            self.model._init_defaults()
            self._refresh()
    def _refresh(self): self._build_sidebar(); self._draw()
    def _on_scroll(self, event):
        self._zoom = min(self._zoom*1.1, 3.0) if (event.num==4 or event.delta>0) \
                     else max(self._zoom/1.1, 0.3)
        self._draw()
    def _export_png(self):
        try:
            from PIL import ImageGrab
        except ImportError:
            messagebox.showinfo("Export", "Install Pillow for PNG export.", parent=self)
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Diagram As",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            initialfile="fishbone_diagram.png",
        )
        if not path:
            return   # user cancelled
        # Capture the entire application window (not just the canvas)
        self.update_idletasks()   # ensure geometry is current
        x  = self.winfo_rootx()
        y  = self.winfo_rooty()
        w  = self.winfo_width()
        h  = self.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)
        messagebox.showinfo("Exported", f"Diagram saved to:\n{path}", parent=self)

    # ── Core draw ─────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.canvas
        c.delete("all")
        W, H = c.winfo_width(), c.winfo_height()
        if W < 20 or H < 20:
            return

        z  = self._zoom
        branches = self.model.branches
        n  = len(branches)

        # Split into top (even indices) and bottom (odd indices)
        top_idx = list(range(0, n, 2))
        bot_idx = list(range(1, n, 2))
        top_br  = [branches[i] for i in top_idx]
        bot_br  = [branches[i] for i in bot_idx]
        top_n   = len(top_br)
        bot_n   = len(bot_br)
        side_n  = max(top_n, bot_n, 1)

        ang_rad = math.radians(BRANCH_ANGLE)

        # ── Compute branch length from available vertical space ───────────────
        # Available height per half = from spine to canvas edge minus padding
        margin_v   = 40
        avail_h    = (H / 2 - margin_v) / z          # unscaled

        # Branch vertical rise = branch_len * sin(45°)
        # Sub-rib adds extra vertical: sub_len * sin(SUB_RIB_ANGLE) + text_h
        # We solve for branch_len such that all content fits:
        text_h_est = 22                               # estimated label height unscaled
        sub_ang_rad = math.radians(SUB_RIB_ANGLE)

        max_causes = max((len(b["causes"]) for b in branches), default=0)
        # Sub-rib length: at most 55% of branch length (keeps ribs inside the branch zone)
        # and at least enough so causes don't crowd the branch itself
        # We pick sub_len as a fraction and compute iteratively
        # branch rise + sub_rib rise + text must fit in avail_h
        # rise_branch = branch_len * sin(45)
        # rise_sub    = sub_len * sin(60)
        # text clearance = text_h_est
        # constraint: rise_branch + rise_sub + text_h_est <= avail_h
        # sub_len = 0.5 * branch_len  (fixed ratio)
        # => branch_len*(sin45 + 0.5*sin60) + text_h_est <= avail_h
        combined_sin = math.sin(ang_rad) + 0.5 * math.sin(sub_ang_rad)
        branch_len_u = max(80, min(
            (avail_h - text_h_est) / combined_sin,
            300                                       # hard cap
        ))
        branch_len   = branch_len_u * z               # scaled
        sub_len      = min(branch_len * 0.52, 120 * z)

        # ── Spine geometry ────────────────────────────────────────────────────
        # Tail and head sizes are FIXED in screen pixels (not zoom-scaled) so
        # they never clip regardless of zoom level.  Only the diagram content
        # (branches, ribs, labels) scales with z.
        TAIL_HW     = 56   # fixed screen px – half-width of tail block
        TAIL_HH     = 40   # fixed screen px – half-height of tail block
        TAIL_FIN_EX = int(TAIL_HW * 0.38)  # fin points this many px LEFT of tail anchor
        HEAD_W      = 145  # fixed screen px – rectangle width
        HEAD_H      = 52   # fixed screen px – rectangle half-height
        EDGE_PAD    = 8    # min gap from canvas edge

        # tail anchor = far enough right that fins don't clip left edge
        tail_x      = EDGE_PAD + TAIL_FIN_EX
        head_x      = W - EDGE_PAD - HEAD_W   # left edge of head rectangle

        spine_left  = tail_x
        spine_right = head_x
        spine_len   = max(60, spine_right - spine_left)
        spine_y     = H / 2

        # ── Attachment x-positions ────────────────────────────────────────────
        # Each branch group is spread over 15%–88% of spine, so the root end
        # (near the head) leaves room for the arrow and the tip end has padding.
        def attach_xs(total):
            if total == 0:
                return []
            lo = spine_left + spine_len * 0.35
            hi = spine_right - spine_len * 0.10
            if total == 1:
                return [(lo + hi) / 2]
            return [lo + (hi - lo) * i / (total - 1) for i in range(total)]

        top_xs = attach_xs(top_n)
        bot_xs = attach_xs(bot_n)

        # ── Draw tail (fixed size, fins anchored away from left edge) ─────────
        self._draw_fish_tail(c, tail_x, spine_y, TAIL_HW, TAIL_HH)

        # ── Draw spine (on top so it connects cleanly) ────────────────────────
        c.create_line(spine_left, spine_y, spine_right, spine_y,
                      fill=SPINE_CLR, width=max(2, 3*z),
                      arrow="last", arrowshape=(16*z, 20*z, 6*z))

        # ── Draw head rectangle + problem label ───────────────────────────────
        self._draw_fish_head(c, head_x, spine_y, HEAD_W, HEAD_H,
                             self.model.problem)

        if n == 0:
            c.create_text(W/2, H/2 - 30, text="No branches yet — click  + Branch",
                          font=FONT_LABEL, fill=MUTED)
        else:
            for slot, (branch, bi) in enumerate(zip(top_br, top_idx)):
                clr = BRANCH_COLORS[bi % len(BRANCH_COLORS)]
                self._draw_branch(c, top_xs[slot], spine_y, branch_len, sub_len,
                                  branch, clr, z, top=True)
            for slot, (branch, bi) in enumerate(zip(bot_br, bot_idx)):
                clr = BRANCH_COLORS[bi % len(BRANCH_COLORS)]
                self._draw_branch(c, bot_xs[slot], spine_y, branch_len, sub_len,
                                  branch, clr, z, top=False)

        c.create_text(8, H-8, text="Scroll to zoom  •  Use sidebar to edit",
                      font=FONT_SMALL, fill=MUTED, anchor="sw")
        c.create_text(W-8, H-8, text="By Lillian Boit, 2026",
                      font=FONT_SMALL, fill=MUTED, anchor="se")

    # ── Fish head: rectangle (right side) ────────────────────────────────────
    def _draw_fish_head(self, c, x, y, w, h, problem_text=""):
        """Draw a rounded rectangle head. x is the LEFT edge of the rectangle."""
        r = 10  # corner radius
        x1, y1, x2, y2 = x, y - h, x + w, y + h
        # Rounded rectangle via polygon with arc corners
        c.create_polygon(
            x1+r, y1,  x2-r, y1,
            x2,   y1+r, x2,  y2-r,
            x2-r, y2,   x1+r, y2,
            x1,   y2-r, x1,  y1+r,
            fill=HEAD_CLR, outline="#FFAA55", width=2, smooth=True)
        # Spine connector triangle pointing left
        c.create_polygon(
            x1, y - 10, x1 - 14, y, x1, y + 10,
            fill=HEAD_CLR, outline="#FFAA55", width=1)
        # Divider line (decorative)
        c.create_line(x1+8, y1+6, x1+8, y2-6, fill="#FFAA55", width=1, dash=(3,3))
        # Problem label centred in rectangle
        fs = max(9, min(13, int(w // 10)))
        c.create_text((x1+x2)/2 + 4, y,
                      text=problem_text,
                      font=(FONT_INPUT[0], fs, "bold"),
                      fill=BG, width=w - 20, justify="center")

    # ── Fish tail (left side, fixed screen size) ───────────────────────────────
    def _draw_fish_tail(self, c, x, y, w, h):
        """Forked tail anchored at (x, y) — fins grow to the LEFT.
        x should already have enough left-padding so fins never leave canvas.
        w, h are in raw screen pixels (not zoom-scaled) so size is stable.
        """
        # Spine stub – small filled rect connecting tail to spine
        stub = int(w * 0.20)
        c.create_rectangle(x - stub, y - int(h*0.30),
                            x + stub, y + int(h*0.30),
                            fill=HEAD_CLR, outline="#FFAA55", width=1)
        fin_tip = int(w * 0.38)   # how far left the fin points go
        # Upper fin
        c.create_polygon(
            x,          y - int(h*0.18),
            x - fin_tip, y - h,
            x - int(w*0.10), y,
            fill="#E0763A", outline="#FFAA55", width=1, smooth=True)
        # Lower fin
        c.create_polygon(
            x,          y + int(h*0.18),
            x - fin_tip, y + h,
            x - int(w*0.10), y,
            fill="#E0763A", outline="#FFAA55", width=1, smooth=True)

    # ── Branch ────────────────────────────────────────────────────────────────
    def _draw_branch(self, c, ax, ay, branch_len, sub_len, branch, clr, z, top):
        """
        Draw one main branch + sub-rib causes with no-overlap layout.

        Key decisions
        -------------
        * Branch tip is placed at angle BRANCH_ANGLE above/below spine.
        * Causes are spaced evenly along 15 %–85 % of the branch segment
          so the tip and root ends stay clear.
        * Sub-ribs fan in a fixed direction (further from spine than the
          branch itself) so they never collide with each other.
        * Branch name is placed at the outer tip, offset perpendicular to
          the branch so it clears the last sub-rib.
        * All coordinates are fully determined by (ax, ay, branch_len,
          sub_len, top) — no random offsets — so re-draws are stable.
        """
        sign    = -1 if top else 1      # -1 = upward on screen
        ang     = math.radians(BRANCH_ANGLE)
        sub_ang = math.radians(SUB_RIB_ANGLE)

        # Branch endpoints
        tip_x = ax - branch_len * math.cos(ang)
        tip_y = ay + sign * branch_len * math.sin(ang)

        # ── Main branch arrow (tip → spine attachment) ────────────────────────
        c.create_line(tip_x, tip_y, ax, ay,
                      fill=clr, width=max(2, 2.5*z),
                      arrow="last", arrowshape=(10*z, 13*z, 4*z))

        # ── Branch name label ─────────────────────────────────────────────────
        # Place beyond the tip, shifted outward (away from spine)
        fs_b = max(9, int(BRANCH_FONT_SZ * z))
        # Estimate label height: font size * 1.4
        label_h_est = fs_b * 1.4
        # Offset: move a bit further along the branch direction + perpendicular outward
        extend   = 6 * z
        perp_off = label_h_est * 0.7 + sub_len * 0.15   # enough clearance from last rib
        lx = tip_x - extend * math.cos(ang)
        ly = tip_y + sign * (extend * math.sin(ang) + perp_off)
        c.create_text(lx, ly,
                      text=branch["name"],
                      font=(FONT_LABEL[0], fs_b, "bold"),
                      fill=clr, anchor="center")

        # ── Cause sub-ribs ────────────────────────────────────────────────────
        causes = branch["causes"]
        nc     = len(causes)
        if nc == 0:
            return

        # Sub-rib unit vector: parallel to the spine (horizontal), pointing
        # left (away from the fish head) — same direction as the main spine.
        rib_dx = -1.0
        rib_dy =  0.0

        # Spread attachment points from 15% to 85% along branch
        for ci, cause in enumerate(causes):
            t  = 0.15 + 0.70 * (ci / max(nc-1, 1)) if nc > 1 else 0.50
            bx = tip_x + (ax - tip_x) * t
            by = tip_y + (ay - tip_y) * t

            # Sub-rib end point
            rx = bx + sub_len * rib_dx
            ry = by + sub_len * rib_dy

            c.create_line(rx, ry, bx, by,
                          fill=clr, width=max(1, 1.5*z), dash=(4, 3),
                          arrow="last", arrowshape=(6*z, 8*z, 3*z))

            # Cause label: at the end of rib, offset a little further outward
            fs_c    = max(9, int(CAUSE_FONT_SZ * z))
            # Label sits above (top branches) or below (bottom branches) the
            # rib tip so it never overlaps the rib line itself.
            label_x = rx
            label_y = ry + sign * (fs_c * 0.9)
            c.create_text(label_x, label_y,
                          text=cause,
                          font=(FONT_SMALL[0], fs_c),
                          fill=TEXT,
                          anchor="center",
                          width=int(CAUSE_LABEL_W * z))


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = FishboneApp()
    app.mainloop()