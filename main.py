import tkinter as tk
from tkinter import ttk, messagebox

try:
    # Problem generator
    from rec_problem.rectangle_packing_problem import RectanglePackingProblem

    # Greedy strategies
    from rec_problem.strategies.strat_largest_area_first import LargestAreaFirstStrategy
    from rec_problem.strategies.strat_longest_side_first import LongestSideFirstStrategy

    # Local search neighborhoods
    from rec_problem.neighborhoods.geometry_based_neighbor import *
    from rec_problem.neighborhoods.partial_overlap_neighbor import *
    from rec_problem.neighborhoods.rule_based_neighbor import *
except Exception as e:
    print("Warning: backend imports not available yet:", e)


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
        self.primary_choice = tk.StringVar(value="")      # "greedy" or "local"
        self.secondary_choice = tk.StringVar(value="")
        self.selected_strategy_obj = None
        self.problem = None
        self.strategy_height_ratio = 0.40

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

        # If no problem yet, disable controls and show hint
        if self.problem is None:
            hint = ttk.Label(self.strategy_frame, text="Generate a problem first.", foreground="#888")
            hint.grid(row=3, column=0, sticky="w", pady=(8, 0))
            rb_greedy.state(["disabled"])
            rb_local.state(["disabled"])
            choose_btn.state(["disabled"])

    def _on_primary_changed(self):
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

        # Return (bottom-left) and Choose (bottom-right)
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

        # Instantiate the chosen greedy strategy
        if token == "largest_area":
            try:
                self.selected_strategy_obj = LargestAreaFirstStrategy()
            except Exception:
                self.selected_strategy_obj = "LargestAreaFirstStrategy"
        elif token == "longest_side":
            try:
                self.selected_strategy_obj = LongestSideFirstStrategy()
            except Exception:
                self.selected_strategy_obj = "LongestSideFirstStrategy"

        messagebox.showinfo("Strategy Selected", f"Greedy with {self.selected_strategy_obj}")

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

def main():
    root = tk.Tk()
    app = PackingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
