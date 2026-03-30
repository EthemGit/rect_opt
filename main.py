import tkinter as tk
from tkinter import ttk, messagebox


# Problem generator
from rec_problem.rectangle_packing_problem import RectanglePackingProblem

# Algorithms
from greedy.greedy_algo import GreedyAlgo
from local_search.local_search_algo import LocalSearchAlgo

# Greedy strategies
from rec_problem.strategies.strat_largest_area_first import LargestAreaFirstStrategy
from rec_problem.strategies.strat_longest_side_first import LongestSideFirstStrategy

# Local search neighborhoods
from rec_problem.neighborhoods.geometry_based_neighbor import GeometryBasedNeighborhood
from rec_problem.neighborhoods.partial_overlap_neighbor import PartialOverlapNeighborhood
from rec_problem.neighborhoods.rule_based_neighbor import RuleBasedNeighborhood

START_ALGO_BUTTON_DESCRIPTION = "Run Algorithm"

class PackingGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rectangle Packing — OptAlgos")
        self.root.state('zoomed')

        # fonts
        self.font_h2 = ("Segoe UI", 12, "bold")
        self.font = ("Segoe UI", 10)

        # colors
        self.color_new = "#07631c"           # dark green - changed box
        self.color_moved = "#5aa86a"         # middle green - position changed only
        self.color_old = "#b8e6b8"           # light green - unchanged
        self.color_outline = "#1a73e8"

        # per-step metadata
        self._step_new_keys = None           # list[set], same length as self._solutions
        self._step_change_types = None       # list[dict], maps rect_id -> 'box_changed' or 'position_only'

        # state
        self.rectangles = []
        self.algorithm = None
        self.algorithm_choice = tk.StringVar(value="")  # combined algorithm+strategy choice
        self.problem = None
        self.strategy_height_ratio = 0.40
        self._solutions = None       # list of solutions from solve()
        self._sol_index = 0          # index of currently shown solution
        self.current_solution = None # last rendered solution
        self.stepbar = None                # ttk.Scale for stepping through solutions
        self.step_var = tk.IntVar(value=0)
        self._stepbar_updating = False     # guard to avoid feedback loops

        self.solution_window = None
        self.solution_canvas = None
        self.solution_header_var = tk.StringVar(value="Boxes: —")  # header text for solution popup
        self.solution_problem_var = tk.StringVar(value=": —")
        self._zoom = 1.4            # start slightly zoomed-in
        self.BASE_CELL = 200        # box size at zoom=1.0
        self.MIN_CELL = 80          # minimum pixel size per box cell
        self.MAX_COLS = 6           # do not exceed 6 columns in the viewer

        # layout: two main columns
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=3, minsize=700)
        self.root.columnconfigure(1, weight=2, minsize=380)

        # layout lock (final-solution-based)
        self._locked_cols = None
        self._locked_cell_size = None
        self._locked_scale = None

        # draw constants (so we reuse the same numbers everywhere)
        self._gap = 24
        self._title_h = 22

        # LEFT SIDE: Controls + Table
        self._build_left_side()

        # RIGHT SIDE: Strategy chooser
        self._build_strategy_frame()

        self.root.bind("<Configure>", self._on_resize)

    def _ensure_final_layout_lock(self):
        """Compute layout from final step + current zoom.

        As zoom increases, the number of columns is reduced dynamically.
        """
        if not self._solutions or not self.solution_canvas:
            return
        final_sol = self._solutions[-1]
        boxes_final = getattr(final_sol, "boxes", None) or []
        box_len_final = getattr(final_sol, "box_length", None)
        if not boxes_final or not box_len_final:
            return

        c = self.solution_canvas
        w = max(c.winfo_width(), 1)
        cols, cell_size, scale = self._compute_layout_from_count_and_box_len(
            len(boxes_final), box_len_final, w
        )

        self._locked_cols = cols
        self._locked_cell_size = cell_size
        self._locked_scale = scale

    def _compute_layout_from_count_and_box_len(self, box_count: int, box_len: int, canvas_width: int):
        """Return (cols, cell_size, scale) from box count, box length, and canvas width."""
        gap = self._gap
        desired_cell = int(self.BASE_CELL * self._zoom)
        desired_cell = max(self.MIN_CELL, min(1200, desired_cell))
        max_cols_by_zoom = int((canvas_width - gap) // (desired_cell + gap))
        max_cols_by_zoom = max(1, max_cols_by_zoom)
        cols = int(max(1, min(box_count, self.MAX_COLS, max_cols_by_zoom)))
        cell_w_avail = (canvas_width - (cols + 1) * gap) / cols
        cell_size = int(min(cell_w_avail, desired_cell))
        cell_size = max(1, cell_size)
        scale = cell_size / float(box_len)
        return cols, cell_size, scale


    # ---------------- Left side: Problem Generation ----------------
    def _build_left_side(self):
        left = ttk.Frame(self.root, padding=(12, 12, 12, 12))
        left.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        # Controls row
        controls = ttk.LabelFrame(left, text="Generate Rectangles", padding=10)
        controls.grid(row=0, column=0, sticky="ew")
        for i in range(10):
            controls.columnconfigure(i, weight=1)

        # USER INPUTS FOR PROBLEM GENERATION
        # box_length
        ttk.Label(controls, text="Box length:", font=self.font).grid(row=0, column=0, sticky="w")
        self.in_box_length = ttk.Spinbox(controls, from_=1, to=10000, width=8)
        self.in_box_length.set(10)
        self.in_box_length.grid(row=0, column=1, padx=(4, 12), sticky="w")

        # rectangle_count
        ttk.Label(controls, text="Rectangle count:", font=self.font).grid(row=0, column=2, sticky="w")
        self.in_rect_count = ttk.Spinbox(controls, from_=1, to=10000, width=8)
        self.in_rect_count.set(10)
        self.in_rect_count.grid(row=0, column=3, padx=(4, 12), sticky="w")

        # rectangle width min / max
        ttk.Label(controls, text="Width min/max:", font=self.font).grid(row=0, column=4, sticky="w")
        self.in_min_width = ttk.Spinbox(controls, from_=1, to=10000, width=6)
        self.in_min_width.set(1)
        self.in_min_width.grid(row=0, column=5, padx=4, sticky="w")
        self.in_max_width = ttk.Spinbox(controls, from_=1, to=10000, width=6)
        self.in_max_width.set(5)
        self.in_max_width.grid(row=0, column=6, padx=(4, 12), sticky="w")

        # rectangle height min / max
        ttk.Label(controls, text="Height min/max:", font=self.font).grid(row=1, column=4, sticky="w")
        self.in_min_height = ttk.Spinbox(controls, from_=1, to=10000, width=6)
        self.in_min_height.set(1)
        self.in_min_height.grid(row=1, column=5, padx=4, sticky="w")
        self.in_max_height = ttk.Spinbox(controls, from_=1, to=10000, width=6)
        self.in_max_height.set(5)
        self.in_max_height.grid(row=1, column=6, padx=(4, 12), sticky="w")

        ttk.Button(controls, text="Generate", command=self._on_generate).grid(
            row=0, column=9, rowspan=2, sticky="e"
        )

        # Table of Rects
        table_frame = ttk.Frame(left)
        table_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        columns = ("ID", "Length", "Width")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=22)

        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("Length", width=120, anchor="center")
        self.tree.column("Width", width=120, anchor="center")

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

    def _on_generate(self):
        try:
            box_length = int(self.in_box_length.get())
            rect_count = int(self.in_rect_count.get())
            min_width = int(self.in_min_width.get())
            max_width = int(self.in_max_width.get())
            min_height = int(self.in_min_height.get())
            max_height = int(self.in_max_height.get())

            if min_width > max_width:
                raise ValueError("Width min must be ≤ max.")
            if min_height > max_height:
                raise ValueError("Height min must be ≤ max.")
            if max_width > box_length or max_height > box_length:
                raise ValueError("Rect sizes must be ≤ box length.")

            self.problem = RectanglePackingProblem(
                box_length=box_length,
                rect_number=rect_count,
                min_width=min_width,
                max_width=max_width,
                min_height=min_height,
                max_height=max_height,
            )

            self._refresh_table()

            # Enable strategy selection now that a problem exists
            self._render_primary_options()

        except Exception as e:
            messagebox.showerror("Generation Error", str(e))

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        if not self.problem:
            return
        for idx, rect in enumerate(self.problem.rectangles, start=1):
            self.tree.insert("", "end", values=(idx, rect.length, rect.width))


    # ---------------- Right side: Strategy selection ----------------
    def _build_strategy_frame(self):
        self.strategy_wrapper = ttk.Frame(self.root, padding=(12, 12, 12, 12))
        self.strategy_wrapper.grid(row=0, column=1, sticky="nsew")
        self.strategy_wrapper.rowconfigure(0, weight=0)
        self.strategy_wrapper.columnconfigure(0, weight=1)

        self.strategy_frame = ttk.LabelFrame(self.strategy_wrapper, text="Choose Strategy", padding=(16, 12))
        self.strategy_frame.grid(row=0, column=0, sticky="new")
        self.strategy_frame.grid_propagate(False)

        self._render_primary_options()

    def _on_resize(self, event):
        """Keep the strategy frame ~40% of the current window height and full width of right column."""
        try:
            target_h = max(200, int(self.root.winfo_height() * self.strategy_height_ratio))
            self.strategy_frame.configure(height=target_h)
            self.strategy_frame.configure(width=self.strategy_wrapper.winfo_width())
        except Exception:
            pass

    def _clear_strategy_frame(self):
        for w in self.strategy_frame.winfo_children():
            w.destroy()

    def _render_primary_options(self):
        self._clear_strategy_frame()
        title = ttk.Label(self.strategy_frame, text="Select an Algorithm", font=self.font_h2)
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        options = [
            ("Greedy - Largest-Area First", "Greedy - Largest-Area First"),
            ("Greedy - Longest-Side First", "Greedy - Longest-Side First"),
            ("Local Search - Geometry-Based", "Local Search - Geometry-Based"),
            ("Local Search - Partial Overlap", "Local Search - Partial Overlap"),
            ("Local Search - Rule-Based", "Local Search - Rule-Based"),
        ]
        
        self.algorithm_choice.set("")
        
        disabled = self.problem is None
        
        for idx, (label, value) in enumerate(options, start=1):
            rb = ttk.Radiobutton(
                self.strategy_frame,
                text=label,
                value=value,
                variable=self.algorithm_choice
            )
            rb.grid(row=idx, column=0, sticky="w", pady=2)
            if disabled:
                rb.state(["disabled"])

        run_btn = ttk.Button(self.strategy_frame, text=START_ALGO_BUTTON_DESCRIPTION, command=self._on_algorithm_chosen)
        run_btn.grid(row=99, column=0, sticky="e", pady=(12, 0))

        # If rectangles not generated yet and no problem exists => disable controls
        if self.problem is None:
            hint = ttk.Label(self.strategy_frame, text="Generate a problem first.", foreground="#888")
            hint.grid(row=7, column=0, sticky="w", pady=(8, 0))
            run_btn.state(["disabled"])

    def _on_algorithm_chosen(self):
        if self.problem is None:
            messagebox.showwarning("No Problem", "Please generate a problem first.")
            return

        choice = self.algorithm_choice.get()
        if not choice:
            messagebox.showwarning("Selection Required", "Please select an algorithm.")
            return
        
        try:
            local_search_common = {
                "max_iters": 20000,
                "stride": 5,
                "first_improvement": True,
                "max_neighbors_per_step": 2000,
                "time_limit_seconds": 15.0,
            }

            if choice == "Greedy - Largest-Area First":
                self.algorithm = GreedyAlgo(LargestAreaFirstStrategy())
            elif choice == "Greedy - Longest-Side First":
                self.algorithm = GreedyAlgo(LongestSideFirstStrategy())
            elif choice == "Local Search - Geometry-Based":
                neighborhood = GeometryBasedNeighborhood(max_neighbors=500)
                self.algorithm = LocalSearchAlgo(
                    neighborhood,
                    **local_search_common,
                    no_improve_limit=10
                )
            elif choice == "Local Search - Partial Overlap":
                neighborhood = PartialOverlapNeighborhood(max_neighbors=500)
                self.algorithm = LocalSearchAlgo(
                    neighborhood,
                    **local_search_common,
                    no_improve_limit=1
                )
            elif choice == "Local Search - Rule-Based":
                neighborhood = RuleBasedNeighborhood(max_neighbors=2000)
                rect_count = len(getattr(self.problem, "rectangles", []) or [])
                proportional_limit = max(1, rect_count // 10)
                max_allowed = max(10, rect_count // 3)
                non_box_improve_accept_limit = max(10, min(proportional_limit, max_allowed))
                self.algorithm = LocalSearchAlgo(
                    neighborhood,
                    **local_search_common,
                    no_improve_limit=15,
                    non_box_improve_accept_limit=non_box_improve_accept_limit
                )
            else:
                messagebox.showerror("Unknown Algorithm", f"Unknown algorithm choice: {choice}")
                return

            self._solutions = self.algorithm.solve(self.problem)
            self._solutions = self._deduplicate_solutions(self._solutions)
            self._compute_step_new_sets()
            
            if not self._solutions:
                messagebox.showwarning("Empty result", "The algorithm returned no solutions.")
                return

            self._show_solution_at(0)
            
        except Exception as e:
            messagebox.showerror("Error running algorithm", str(e))


    # ---------------- Solution rendering ---------------------------------------------------------
    def _render_solution(self, solution):
        """Draw the solution on the canvas.
        New rects in the current step are dark green; older ones are light green.
        """
        if not getattr(self, "solution_canvas", None):
            return

        c: tk.Canvas = self.solution_canvas
        c.delete("all")

        # guards / empty states
        if not solution:
            self.solution_header_var.set("Boxes: —")
            c.configure(scrollregion=(0, 0, c.winfo_width(), c.winfo_height()))
            return

        boxes = getattr(solution, "boxes", None)
        box_len = getattr(solution, "box_length", None)
        if not boxes or not isinstance(boxes, list) or not box_len:
            self.solution_header_var.set("Boxes: —")
            c.configure(scrollregion=(0, 0, c.winfo_width(), c.winfo_height()))
            return

        # use final layout throughout
        if hasattr(self, "_ensure_final_layout_lock"):
            try:
                self._ensure_final_layout_lock()
            except Exception:
                pass

        need_lock = (
            getattr(self, "_locked_cols", None) is None or
            getattr(self, "_locked_cell_size", None) is None or
            getattr(self, "_locked_scale", None) is None
        )

        w = max(c.winfo_width(), 1)
        gap = getattr(self, "_gap", 24)
        title_h = getattr(self, "_title_h", 22)

        if need_lock:
            final = None
            try:
                final = self._solutions[-1] if self._solutions else None
            except Exception:
                final = None

            if final and getattr(final, "boxes", None) and getattr(final, "box_length", None):
                cols, cell_size, scale = self._compute_layout_from_count_and_box_len(
                    len(final.boxes), final.box_length, w
                )
            else:
                # As a last resort, compute from the CURRENT step
                cols, cell_size, scale = self._compute_layout_from_count_and_box_len(
                    len(boxes), box_len, w
                )

            self._locked_cols = cols
            self._locked_cell_size = cell_size
            self._locked_scale = scale

        # Use the locked layout for every step:
        cols = self._locked_cols or 1
        cell_size = self._locked_cell_size or self.MIN_CELL
        scale = self._locked_scale or (cell_size / float(box_len))

        # draw all boxes and rects
        content_bottom = 0

        new_set = None
        if getattr(self, "_step_new_keys", None) and 0 <= self._sol_index < len(self._step_new_keys):
            new_set = self._step_new_keys[self._sol_index]

        # colors (with safe defaults if you didn't add them in __init__)
        color_new = getattr(self, "color_new", "#0a7d24")
        color_old = getattr(self, "color_old", "#b8e6b8")
        color_outline = getattr(self, "color_outline", "#1a73e8")

        for idx, box in enumerate(boxes):
            r = idx // cols
            ccol = idx % cols

            cell_x = int(gap + ccol * (cell_size + gap))
            cell_y = int(gap + r * (cell_size + title_h + gap))

            # Box title
            try:
                rect_count = len((getattr(box, "my_rects", {}) or {}))
            except Exception:
                rect_count = "?"
            c.create_text(
                cell_x + cell_size // 2,
                cell_y + title_h // 2,
                anchor="center",
                text=f"Box {idx+1} ({rect_count} rects)",
                font=("Segoe UI", 10, "bold")
            )

            # Box boundary
            x0 = cell_x
            y0 = cell_y + title_h
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            c.create_rectangle(x0, y0, x1, y1, outline="#333", width=2)

            # Rectangles inside the box
            my_rects = getattr(box, "my_rects", {}) or {}
            items_iter = my_rects.items() if isinstance(my_rects, dict) else []

            for rect, (rx, ry) in items_iter:
                px0 = x0 + int(rx * scale)
                py0 = y0 + int(ry * scale)
                px1 = px0 + int(getattr(rect, "width", 0) * scale)
                py1 = py0 + int(getattr(rect, "length", 0) * scale)

                # Coloring: changed box (dark green) vs position-only (middle green) vs unchanged (light green)
                key = getattr(rect, "id", None)
                if key is None:
                    key = id(rect)  # fallback, shouldn't be needed with your dataclass
                
                fill_color = color_old  # default: unchanged
                if new_set is not None and key in new_set:
                    # Rect changed - check what type of change
                    change_types = None
                    if getattr(self, "_step_change_types", None) and 0 <= self._sol_index < len(self._step_change_types):
                        change_types = self._step_change_types[self._sol_index]
                    
                    if change_types and key in change_types:
                        change_type = change_types[key]
                        if change_type == 'box_changed':
                            fill_color = color_new  # dark green
                        elif change_type == 'position_only':
                            fill_color = getattr(self, "color_moved", "#61b16e")  # middle green
                    else:
                        # Fallback for highlighted_ids (assume box change)
                        fill_color = color_new

                c.create_rectangle(px0, py0, px1, py1, fill=fill_color, outline=color_outline, width=2)
                c.create_text(
                    px0 + 6, py0 + 6, anchor="nw",
                    text=f"{getattr(rect,'length','?')}×{getattr(rect,'width','?')}",
                    font=("Segoe UI", 9)
                )

            content_bottom = max(content_bottom, y1)

        # Vertical-only scrolling
        c.configure(scrollregion=(0, 0, w, content_bottom + gap))

    def _ensure_solution_window(self):
        """Create (or reuse) a dedicated pop-up window for rendering solutions."""
        if self.solution_window and self.solution_window.winfo_exists():
            self.solution_window.deiconify()
            self.solution_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Solution Viewer")
        win.state('zoomed')

        outer = ttk.Frame(win, padding=0)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(3, weight=1)   # row 3 holds canvas
        outer.columnconfigure(0, weight=1)

        # Header with total box count
        header = ttk.Label(
            outer, textvariable=self.solution_header_var,
            anchor="w", padding=(8, 6), font=("Segoe UI", 10, "bold")
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Problem specifics row (above legend)
        problem_info = ttk.Frame(outer, padding=(8, 2))
        problem_info.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Label(problem_info, text="Problem:", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(problem_info, textvariable=self.solution_problem_var, font=("Segoe UI", 9)).grid(
            row=0, column=1, sticky="w", padx=(4, 0)
        )

        # Color legend
        legend = ttk.Frame(outer, padding=(8, 2, 8, 6))
        legend.grid(row=2, column=0, columnspan=2, sticky="ew")

        ttk.Label(legend, text="Legend:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(0, 10), sticky="w")

        tk.Label(legend, bg=self.color_new, width=2, relief="solid", borderwidth=1).grid(row=0, column=1, padx=(0, 4), sticky="w")
        ttk.Label(legend, text="Changed box").grid(row=0, column=2, padx=(0, 12), sticky="w")

        tk.Label(legend, bg=self.color_moved, width=2, relief="solid", borderwidth=1).grid(row=0, column=3, padx=(0, 4), sticky="w")
        ttk.Label(legend, text="Moved in same box").grid(row=0, column=4, padx=(0, 12), sticky="w")

        tk.Label(legend, bg=self.color_old, width=2, relief="solid", borderwidth=1).grid(row=0, column=5, padx=(0, 4), sticky="w")
        ttk.Label(legend, text="Unchanged").grid(row=0, column=6, sticky="w")

        # Canvas + vertical scrollbar
        can = tk.Canvas(outer, bg="white", highlightthickness=1, highlightbackground="#ddd")
        vbar = ttk.Scrollbar(outer, orient="vertical", command=can.yview)
        can.configure(yscrollcommand=vbar.set)

        can.grid(row=3, column=0, sticky="nsew")
        vbar.grid(row=3, column=1, sticky="ns")

        # --- Navigation toolbar (Prev / Next + Zoom) ---
        toolbar = ttk.Frame(outer, padding=(8, 6))
        toolbar.grid(row=4, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(0, weight=0)
        toolbar.columnconfigure(1, weight=0)
        toolbar.columnconfigure(2, weight=1)  # spacer
        toolbar.columnconfigure(3, weight=0)
        toolbar.columnconfigure(4, weight=0)

        self.btn_prev = ttk.Button(toolbar, text="◀ Prev",
                                command=lambda: self._show_solution_at(self._sol_index - 1))
        self.btn_prev.grid(row=0, column=0, padx=(0, 6))

        self.btn_next = ttk.Button(toolbar, text="Next ▶",
                                command=lambda: self._show_solution_at(self._sol_index + 1))
        self.btn_next.grid(row=0, column=1, padx=(0, 12))

        # Zoom buttons
        ttk.Button(toolbar, text="Zoom -", command=lambda: self._zoom_change(1/1.15)).grid(row=0, column=3, padx=6)
        ttk.Button(toolbar, text="Zoom +", command=lambda: self._zoom_change(1.15)).grid(row=0, column=4, padx=6)

        # Make sure button states reflect current position
        self._update_nav_buttons()

        # Vertical mouse wheel
        def _on_wheel(e):
            can.yview_scroll(int(-1*(e.delta/120)), "units")
        can.bind("<MouseWheel>", _on_wheel)          # Windows/macOS
        can.bind("<Button-4>", lambda e: can.yview_scroll(-3, "units"))  # Linux
        can.bind("<Button-5>", lambda e: can.yview_scroll( 3, "units"))

        def _on_close():
            try:
                win.unbind_all("<Right>")
                win.unbind_all("<Left>")
                win.unbind_all("<Control-plus>")
                win.unbind_all("<Control-minus>")
                win.unbind_all("<Control-Key-0>")
                self.solution_window = None
                self.solution_canvas = None
                self.stepbar = None
                self.btn_prev = None
                self.btn_next = None
            finally:
                win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_close)

        can.bind("<Configure>", lambda e: (
            self._ensure_final_layout_lock(),
            self._render_solution(self.current_solution) if getattr(self, "current_solution", None) else None
        ))
        # Zoom keys
        win.bind_all("<Control-plus>", lambda e: self._zoom_change(1.15))
        win.bind_all("<Control-minus>", lambda e: self._zoom_change(1/1.15))
        win.bind_all("<Control-Key-0>", lambda e: self._zoom_reset())

        win.bind_all("<Right>", lambda e: self._show_solution_at(self._sol_index + 1))
        win.bind_all("<Left>",  lambda e: self._show_solution_at(self._sol_index - 1))

        self.solution_window = win
        self.solution_canvas = can

        # --- Step bar ---
        if not self.stepbar:
            self.stepbar = tk.Scale(
                toolbar,
                from_=0,
                to=0,                 
                orient="horizontal",
                showvalue=False,
                resolution=1,         
                variable=self.step_var,
                command=self._on_stepbar_drag,
            )
            self.stepbar.grid(row=0, column=2, sticky="ew", padx=(6, 6))
            self.stepbar.bind("<ButtonRelease-1>", self._on_stepbar_release)

        toolbar.columnconfigure(2, weight=1)

        win.update_idletasks()

        if self.current_solution:
            self._render_solution(self.current_solution)

    def _zoom_change(self, factor: float):
        self._zoom = max(0.4, min(3.0, self._zoom * factor))
        if self.current_solution:
            self._ensure_final_layout_lock()
            self._render_solution(self.current_solution)

    def _zoom_reset(self):
        self._zoom = 1.4
        if self.current_solution:
            self._ensure_final_layout_lock()
            self._render_solution(self.current_solution)

    def _format_overlap_percentage(self, sol):
        """Return clamped overlap percentage string (e.g. '42.0%') or None."""
        allowed_overlap = getattr(sol, "allowed_overlap", None)
        if allowed_overlap is None:
            return None
        try:
            overlap_pct = max(0.0, min(1.0, float(allowed_overlap))) * 100.0
            return f"{overlap_pct:.1f}%"
        except (TypeError, ValueError):
            return None

    def _show_solution_at(self, idx: int):
        if not self._solutions:
            messagebox.showwarning("No solution", "No solution available to display.")
            return

        idx = max(0, min(idx, len(self._solutions) - 1))
        self._sol_index = idx
        sol = self._solutions[idx]
        self.current_solution = sol

        self._ensure_solution_window()
        self._ensure_final_layout_lock()
        self._render_solution(sol)

        # Update header
        step_txt = f"Step {idx+1}/{len(self._solutions)}"
        try:
            n_boxes = len(getattr(sol, "boxes", []) or [])
        except Exception:
            n_boxes = "—"

        # Update problem specifics row
        if self.problem is not None:
            try:
                prob_box_len = getattr(self.problem, "box_length", "—")
                prob_rect_count = len(getattr(self.problem, "rectangles", []) or [])
                self.solution_problem_var.set(
                    f"Box length = {prob_box_len}   Total rectangles = {prob_rect_count}"
                )
            except Exception:
                self.solution_problem_var.set(": —")
        else:
            self.solution_problem_var.set(": —")

        # display chosen Algorithm
        algo_specification = self.algorithm_choice.get() or "Unknown"

        extra = ""
        if algo_specification == "Local Search - Partial Overlap":
            is_compacting = getattr(sol, "is_compacting", False)
            is_reheating = getattr(sol, "is_reheating", False)
            
            if is_compacting:
                extra = f"  —  Compacting the boxes"
            elif is_reheating:
                overlap_pct = self._format_overlap_percentage(sol)
                if overlap_pct is not None:
                    extra = f"  —  {overlap_pct} - Reheating after compaction"
            else:
                overlap_pct = self._format_overlap_percentage(sol)
                if overlap_pct is not None:
                    extra = f"  —  Allowed overlap: {overlap_pct}"

        self.solution_header_var.set(
            f"{step_txt}  —  Boxes: {n_boxes}  —  Algorithm: {algo_specification}{extra}"
        )

        self._update_nav_buttons()
        self._sync_stepbar() # step bar in sync

    def _update_nav_buttons(self):
        """Enable/disable Prev/Next depending on current index."""
        if not getattr(self, "btn_prev", None) or not getattr(self, "btn_next", None):
            return
        if not self._solutions:
            self.btn_prev.state(["disabled"])
            self.btn_next.state(["disabled"])
            return
        if self._sol_index <= 0:
            self.btn_prev.state(["disabled"])
        else:
            self.btn_prev.state(["!disabled"])
        if self._sol_index >= len(self._solutions) - 1:
            self.btn_next.state(["disabled"])
        else:
            self.btn_next.state(["!disabled"])

    def _sync_stepbar(self):
        if not getattr(self, "stepbar", None):
            return
        self._stepbar_updating = True
        try:
            max_idx = max(0, len(self._solutions) - 1) if self._solutions else 0
            self.stepbar.configure(to=max_idx)
            self.step_var.set(self._sol_index)
            # tk.Scale uses configure(state=...)
            self.stepbar.configure(state="disabled" if max_idx == 0 else "normal")
        finally:
            self._stepbar_updating = False

    def _rect_key(self, rect) -> int:
        """Stable key for a rectangle across steps (uses Rectangle.id)."""
        rid = getattr(rect, "id", None)
        if rid is None:
            # fallback
            return id(rect)
        return int(rid)

    def _extract_positions_from_solution(self, sol) -> dict:
        """Returns {rect_id: (box_idx, x, y)} for every placed rect."""
        positions = {}
        for box_idx, box in enumerate(getattr(sol, "boxes", None) or []):
            my_rects = getattr(box, "my_rects", {}) or {}
            if isinstance(my_rects, dict):
                for rect, (x, y) in my_rects.items():
                    positions[self._rect_key(rect)] = (box_idx, x, y)
        return positions

    def _deduplicate_solutions(self, solutions):
        """Remove consecutive solutions that are visually identical (same positions for all rects)."""
        if not solutions:
            return solutions
        deduped = [solutions[0]]
        prev_pos = self._extract_positions_from_solution(solutions[0])
        pending_compacting = bool(getattr(solutions[0], "is_compacting", False))
        pending_reheating = bool(getattr(solutions[0], "is_reheating", False))
        for sol in solutions[1:]:
            cur_pos = self._extract_positions_from_solution(sol)

            # Accumulate important states from skipped frames and show them on next displayed frame.
            pending_compacting = pending_compacting or bool(getattr(sol, "is_compacting", False))
            pending_reheating = pending_reheating or bool(getattr(sol, "is_reheating", False))

            if cur_pos != prev_pos:
                if pending_compacting:
                    sol.is_compacting = True
                if pending_reheating:
                    sol.is_reheating = True
                deduped.append(sol)
                prev_pos = cur_pos
                pending_compacting = False
                pending_reheating = False

        # If the stream ended with repeated frames that only carried state changes,
        # attach the pending state to the final displayed frame.
        if deduped:
            if pending_compacting:
                deduped[-1].is_compacting = True
            if pending_reheating:
                deduped[-1].is_reheating = True
        return deduped

    def _compute_step_new_sets(self):
        """For each step: which rects changed and what type of change.
        If the solution carries .highlighted_ids (set by the neighborhood for precise
        per-move highlighting), use that directly. Otherwise fall back to comparing
        (box_idx, x, y) positions between consecutive steps.
        
        Also tracks whether each rect changed box or just position."""
        self._step_new_keys = []
        self._step_change_types = []
        prev_positions = {}
        for sol in (self._solutions or []):
            change_type_dict = {}  # maps rect_id -> 'box_changed' or 'position_only'
            cur_positions = self._extract_positions_from_solution(sol)
            is_compacting = bool(getattr(sol, "is_compacting", False))
            
            highlighted = getattr(sol, 'highlighted_ids', None)
            # During compaction we must compare displayed-step deltas, not neighborhood highlights.
            if highlighted is not None and not is_compacting:
                # When highlighted_ids is provided, assume all are box changes
                # (typical for single-move neighborhood operations)
                self._step_new_keys.append(set(highlighted))
                for rid in highlighted:
                    change_type_dict[rid] = 'box_changed'
                # keep prev_positions in sync for any subsequent fallback steps
                prev_positions = cur_positions
            else:
                changed = set()
                for rid, pos in cur_positions.items():
                    if prev_positions.get(rid) != pos:
                        changed.add(rid)
                        # Determine if this is a box change or position-only change
                        prev_pos = prev_positions.get(rid)
                        if prev_pos is None:
                            # Rect didn't exist before (shouldn't happen normally)
                            change_type_dict[rid] = 'box_changed'
                        else:
                            prev_box_idx = prev_pos[0]
                            cur_box_idx = pos[0]
                            if prev_box_idx != cur_box_idx:
                                # Box changed
                                change_type_dict[rid] = 'box_changed'
                            else:
                                # Same box, only position changed
                                change_type_dict[rid] = 'position_only'
                
                self._step_new_keys.append(changed)
                prev_positions = cur_positions
            
            self._step_change_types.append(change_type_dict)

    def _on_stepbar_drag(self, value_str):
        if self._stepbar_updating or not self._solutions:
            return
        try:
            idx = int(round(float(value_str)))
        except ValueError:
            return
        self.solution_header_var.set(
            f"Step {idx+1}/{len(self._solutions)} — release to jump"
        )

    def _on_stepbar_release(self, _event):
        if not self._solutions:
            return
        idx = int(round(float(self.stepbar.get())))
        self._show_solution_at(idx)


def main():
    root = tk.Tk()
    app = PackingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
