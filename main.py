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

"""
# Local search neighborhoods
from rec_problem.neighborhoods.geometry_based_neighbor import *
from rec_problem.neighborhoods.partial_overlap_neighbor import *
from rec_problem.neighborhoods.rule_based_neighbor import *
"""


class PackingGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rectangle Packing — OptAlgos")
        self.root.geometry("1200x700")

        # fonts
        self.font_h1 = ("Segoe UI", 16, "bold")
        self.font_h2 = ("Segoe UI", 12, "bold")
        self.font = ("Segoe UI", 10)

        # state
        self.rectangles = []
        self.algorithm = None
        self.primary_choice = tk.StringVar(value="")      # "greedy" or "local"
        self.secondary_choice = tk.StringVar(value="")
        self.selected_strategy_obj = None
        self.problem = None
        self.strategy_height_ratio = 0.40
        self._solutions = None       # list of solutions from solve()
        self.current_solution = None # last rendered solution
        self.solution_window = None
        self.solution_canvas = None
        self.solution_header_var = tk.StringVar(value="Boxes: —")  # header text for solution popup
        self._zoom = 1.4            # start slightly zoomed-in
        self.MIN_CELL = 200         # minimum pixel size per box cell

        # layout: two main columns
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=3, minsize=700)
        self.root.columnconfigure(1, weight=2, minsize=380)

        # LEFT SIDE: Controls + Table
        self._build_left_side()

        # RIGHT SIDE: Strategy chooser
        self._build_strategy_frame()

        self.root.bind("<Configure>", self._on_resize)


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

        # rectangle min / max size
        ttk.Label(controls, text="Rect size min/max:", font=self.font).grid(row=0, column=4, sticky="w")
        self.in_rect_min = ttk.Spinbox(controls, from_=1, to=10000, width=6)
        self.in_rect_min.set(1)
        self.in_rect_min.grid(row=0, column=5, padx=4, sticky="w")
        self.in_rect_max = ttk.Spinbox(controls, from_=1, to=10000, width=6)
        self.in_rect_max.set(5)
        self.in_rect_max.grid(row=0, column=6, padx=(4, 12), sticky="w")

        ttk.Button(controls, text="Generate", command=self._on_generate).grid(row=0, column=9, sticky="e")

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
            rect_min = int(self.in_rect_min.get())
            rect_max = int(self.in_rect_max.get())

            if rect_min > rect_max:
                raise ValueError("Rect size min must be ≤ max.")

            self.problem = RectanglePackingProblem(
                box_length=box_length,
                rect_number=rect_count,
                rect_min_size=rect_min,
                rect_max_size=rect_max,
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
        title = ttk.Label(self.strategy_frame, text="Select Algorithm", font=self.font_h2)
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        rb_greedy = ttk.Radiobutton(
            self.strategy_frame, text="Greedy", value="greedy",
            variable=self.primary_choice, command=self._on_primary_changed
        )
        rb_local = ttk.Radiobutton(
            self.strategy_frame, text="Local Search", value="local",
            variable=self.primary_choice, command=self._on_primary_changed
        )
        rb_greedy.grid(row=1, column=0, sticky="w", pady=2)
        rb_local.grid(row=2, column=0, sticky="w", pady=2)

        choose_btn = ttk.Button(self.strategy_frame, text="Choose", command=self._on_primary_choose)
        choose_btn.grid(row=99, column=2, sticky="e", pady=(16, 0))

        # If rectangles not generated yet and no problem exists => disable controls
        if self.problem is None:
            hint = ttk.Label(self.strategy_frame, text="Generate a problem first.", foreground="#888")
            hint.grid(row=3, column=0, sticky="w", pady=(8, 0))
            rb_greedy.state(["disabled"])
            rb_local.state(["disabled"])
            choose_btn.state(["disabled"])

    def _on_primary_changed(self):
        """If you select greedy or local without pressing 'Choose' yet. """
        pass

    def _on_primary_choose(self):
        if self.problem is None:
            messagebox.showwarning("No Problem", "Please generate a problem first.")
            return

        choice = self.primary_choice.get()
        if choice == "greedy":
            self._render_greedy_options()
        elif choice == "local":
            self._render_local_search_options()
        else:
            messagebox.showwarning("Selection Required", "Please select Greedy or Local Search.")

    def _render_greedy_options(self):
        self._clear_strategy_frame()
        title = ttk.Label(self.strategy_frame, text="Greedy — Select Strategy", font=self.font_h2)
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.secondary_choice.set("")
        ttk.Radiobutton(
            self.strategy_frame, text="Largest-Area-First", value="largest_area",
            variable=self.secondary_choice
        ).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            self.strategy_frame, text="Longest-Side-First", value="longest_side",
            variable=self.secondary_choice
        ).grid(row=2, column=0, sticky="w", pady=2)

        # Add buttons Return (bottom-left) and Choose (bottom-right)
        ttk.Button(self.strategy_frame, text="Return", command=self._render_primary_options).grid(
            row=99, column=0, sticky="w", pady=(16, 0)
        )
        ttk.Button(self.strategy_frame, text="Choose", command=self._on_greedy_choose).grid(
            row=99, column=2, sticky="e", pady=(16, 0)
        )

    def _render_local_search_options(self):
        self._clear_strategy_frame()
        title = ttk.Label(self.strategy_frame, text="Local Search — Select Neighborhood", font=self.font_h2)
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.secondary_choice.set("")
        ttk.Radiobutton(
            self.strategy_frame, text="Geometry-Based", value="geometry",
            variable=self.secondary_choice
        ).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            self.strategy_frame, text="Partial Overlap", value="partial_overlap",
            variable=self.secondary_choice
        ).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Radiobutton(
            self.strategy_frame, text="Rule-Based", value="rule_based",
            variable=self.secondary_choice
        ).grid(row=3, column=0, sticky="w", pady=2)

        ttk.Button(self.strategy_frame, text="Return", command=self._render_primary_options).grid(
            row=99, column=0, sticky="w", pady=(16, 0)
        )
        ttk.Button(self.strategy_frame, text="Choose", command=self._on_local_choose).grid(
            row=99, column=2, sticky="e", pady=(16, 0)
        )

    def _on_greedy_choose(self):
        token = self.secondary_choice.get()
        if not token:
            messagebox.showwarning("Selection Required", "Please choose one Greedy strategy.")
            return

        if self.problem is None:
            messagebox.showwarning("No Problem", "Please generate a problem first.")
            return

        # Map user choice to strategy object
        if token == "largest_area":
            self.selected_strategy_obj = LargestAreaFirstStrategy()
        elif token == "longest_side":
            self.selected_strategy_obj = LongestSideFirstStrategy()
        else:
            messagebox.showerror("Unknown Strategy", f"Unknown strategy token: {token}")
            return

        try:
            # 1) Create algo
            self.algorithm = GreedyAlgo(self.selected_strategy_obj)

            # 2) get list of solution steps
            self._solutions = self.algorithm.solve(self.problem)

            if not self._solutions or len(self._solutions) == 0:
                messagebox.showwarning("Empty result", "The algorithm returned no solutions.")
                return

            # Show the final state
            self._show_final_solution()

        except Exception as e:
            messagebox.showerror("Error running Greedy", str(e))

    def _on_local_choose(self):
        token = self.secondary_choice.get()
        if not token:
            messagebox.showwarning("Selection Required", "Please choose one Local Search neighborhood.")
            return

        # TODO: instantiate real neighborhoods once implemented
        self.selected_strategy_obj = {
            "geometry": "GeometryBasedNeighborhood",
            "partial_overlap": "PartialOverlapNeighborhood",
            "rule_based": "RuleBasedNeighborhood",
        }.get(token, token)

        messagebox.showinfo("Neighborhood Selected", f"Local Search with {self.selected_strategy_obj}")


    # ---------------- Solution rendering ----------------
    def _render_solution(self, solution):
        """Draw the solution on the (vertically scrollable) canvas with a fixed min cell size."""
        if not getattr(self, "solution_canvas", None):
            return
        c: tk.Canvas = self.solution_canvas
        c.delete("all")

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

        n = len(boxes)
        self.solution_header_var.set(f"Boxes: {n}")

        w = max(c.winfo_width(), 1)
        h = max(c.winfo_height(), 1)

        gap = 24
        title_h = 22

        # Column number depends on MIN_CELL
        max_cols_by_min = (w - gap) // (self.MIN_CELL + gap)
        cols = int(max(1, min(n, max_cols_by_min)))
        rows = (n + cols - 1) // cols

        # Per-cell width
        cell_w_avail = (w - (cols + 1) * gap) / cols

        # Desired cell size
        desired = max(self.MIN_CELL, int(cell_w_avail * self._zoom))
        cell_size = int(min(cell_w_avail, desired))
        scale = cell_size / float(box_len)

        # Draw
        content_bottom = 0
        for idx, box in enumerate(boxes):
            r = idx // cols
            ccol = idx % cols

            cell_x = int(gap + ccol * (cell_size + gap))
            cell_y = int(gap + r * (cell_size + title_h + gap))

            # Title for box
            c.create_text(
                cell_x + cell_size // 2,
                cell_y + title_h // 2,
                anchor="center",
                text=f"Box {idx+1} (L={box_len}, number of rects={len(getattr(box, 'my_rects', {}) )})",
                font=("Segoe UI", 10, "bold")
            )

            x0 = cell_x
            y0 = cell_y + title_h
            x1 = x0 + cell_size
            y1 = y0 + cell_size

            c.create_rectangle(x0, y0, x1, y1, outline="#333", width=2)

            my_rects = getattr(box, "my_rects", {})
            for rect, (rx, ry) in my_rects.items():
                px0 = x0 + int(rx * scale)
                py0 = y0 + int(ry * scale)
                px1 = px0 + int(getattr(rect, "width", 0) * scale)
                py1 = py0 + int(getattr(rect, "length", 0) * scale)

                c.create_rectangle(px0, py0, px1, py1, fill="lightgreen", outline="#1a73e8", width=2)
                c.create_text(px0 + 6, py0 + 6, anchor="nw",
                            text=f"{getattr(rect,'length','?')}×{getattr(rect,'width','?')}",
                            font=("Segoe UI", 9))

            content_bottom = max(content_bottom, y1)

        # Vertical-only scrolling
        c.configure(scrollregion=(0, 0, w, content_bottom + gap))

    def _show_final_solution(self):
        if not self._solutions:
            messagebox.showwarning("No solution", "No solution available to display.")
            return
        final = self._solutions[-1]
        self.current_solution = final

        self._ensure_solution_window()
        self._render_solution(final)

    def _ensure_solution_window(self):
        """Create (or reuse) a dedicated pop-up window for rendering solutions."""
        if self.solution_window and self.solution_window.winfo_exists():
            self.solution_window.deiconify()
            self.solution_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Solution Viewer")
        win.geometry("1200x900")
        win.minsize(800, 600)

        outer = ttk.Frame(win, padding=0)
        outer.pack(fill="both", expand=True)
        outer.rowconfigure(1, weight=1)   # row 1 holds canvas
        outer.columnconfigure(0, weight=1)

        # Header with total box count
        header = ttk.Label(
            outer, textvariable=self.solution_header_var,
            anchor="w", padding=(8, 6), font=("Segoe UI", 10, "bold")
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Canvas + vertical scrollbar
        can = tk.Canvas(outer, bg="white", highlightthickness=1, highlightbackground="#ddd")
        vbar = ttk.Scrollbar(outer, orient="vertical", command=can.yview)
        can.configure(yscrollcommand=vbar.set)

        can.grid(row=1, column=0, sticky="nsew")
        vbar.grid(row=1, column=1, sticky="ns")

        # Vertical mouse wheel
        def _on_wheel(e):
            can.yview_scroll(int(-1*(e.delta/120)), "units")
        can.bind("<MouseWheel>", _on_wheel)          # Windows/macOS
        can.bind("<Button-4>", lambda e: can.yview_scroll(-3, "units"))  # Linux
        can.bind("<Button-5>", lambda e: can.yview_scroll( 3, "units"))

        def _on_close():
            try:
                self.solution_canvas = None
            finally:
                win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_close)

        # Re-render on resize
        can.bind("<Configure>",
                lambda e: self._render_solution(self.current_solution) if getattr(self, "current_solution", None) else None)

        # Zoom keys
        win.bind_all("<Control-plus>", lambda e: self._zoom_change(1.15))
        win.bind_all("<Control-minus>", lambda e: self._zoom_change(1/1.15))
        win.bind_all("<Control-Key-0>", lambda e: self._zoom_reset())

        self.solution_window = win
        self.solution_canvas = can

    def _zoom_change(self, factor: float):
        self._zoom = max(0.4, min(3.0, self._zoom * factor))
        if self.current_solution:
            self._render_solution(self.current_solution)

    def _zoom_reset(self):
        self._zoom = 1.4
        if self.current_solution:
            self._render_solution(self.current_solution)


def main():
    root = tk.Tk()
    app = PackingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
