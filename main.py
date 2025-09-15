"""
    # main
    problem_params = get_problem_params_from_GUI()
    problem = RectProblem(problem_params)

    # User sets Strategy in GUI
    strategy = Strategy()
    if strategy==largest_area or strategy==largest_side:
        algo = greedy(strategy)
    if strategy==geometric or strategy==overlap or strategy==rule_based:
        algo = local_search(strategy)
    final_solution = algo.solve(initial_solution)


"""


import tkinter as tk
import tkinter.ttk as ttk
from rec_problem.rectangle_packing_problem import RectanglePackingProblem


class PackingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rectangle Packing Problem")

        self.root.state("zoomed")

        self.font = ("Arial", 14)

        # Container frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(expand=True, fill="both")

        self.build_input_form()

    def build_input_form(self):
        """Creates the centered input form for problem parameters"""

        wrapper = tk.Frame(self.main_frame)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")  # stays centered on resize

        tk.Label(wrapper, text="Box length:", font=self.font).grid(row=0, column=0, sticky="e", padx=10, pady=5)
        tk.Label(wrapper, text="Number of rectangles:", font=self.font).grid(row=1, column=0, sticky="e", padx=10, pady=5)
        tk.Label(wrapper, text="Min rectangle size:", font=self.font).grid(row=2, column=0, sticky="e", padx=10, pady=5)
        tk.Label(wrapper, text="Max rectangle size:", font=self.font).grid(row=3, column=0, sticky="e", padx=10, pady=5)

        self.box_length_entry = tk.Entry(wrapper, font=self.font)
        self.rect_number_entry = tk.Entry(wrapper, font=self.font)
        self.rect_min_size_entry = tk.Entry(wrapper, font=self.font)
        self.rect_max_size_entry = tk.Entry(wrapper, font=self.font)

        self.box_length_entry.grid(row=0, column=1, padx=10, pady=5)
        self.rect_number_entry.grid(row=1, column=1, padx=10, pady=5)
        self.rect_min_size_entry.grid(row=2, column=1, padx=10, pady=5)
        self.rect_max_size_entry.grid(row=3, column=1, padx=10, pady=5)

        self.run_button = tk.Button(
            wrapper,
            text="Generate Problem",
            command=self.generate_problem,
            font=self.font
        )
        self.run_button.grid(row=4, column=0, columnspan=2, pady=20)

    def clear_main_frame(self):
        """Remove all widgets from main_frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def generate_problem(self):
        try:
            box_length = int(self.box_length_entry.get())
            rect_number = int(self.rect_number_entry.get())
            rect_min_size = int(self.rect_min_size_entry.get())
            rect_max_size = int(self.rect_max_size_entry.get())

            problem = RectanglePackingProblem(
                box_length=box_length,
                rect_number=rect_number,
                rect_min_size=rect_min_size,
                rect_max_size=rect_max_size,
            )

            # Replace input form with success display
            self.clear_main_frame()

            success_label = tk.Label(
                self.main_frame,
                text=f"Successfully generated {len(problem.rectangles)} rectangles!",
                font=("Arial", 16, "bold"),
                fg="green"
            )
            success_label.pack(pady=10)

            # ---------- Scrollable Table ----------
            table_container = tk.Frame(self.main_frame)
            table_container.pack(expand=True, fill="y", padx=10, pady=10)

            columns = ("ID", "Width", "Length")
            tree = ttk.Treeview(table_container, columns=columns, show="headings", height=20)

            # Define headings
            tree.heading("ID", text="ID")
            tree.heading("Width", text="Width")
            tree.heading("Length", text="Length")

            # Define column widths
            tree.column("ID", width=60, anchor="center")
            tree.column("Width", width=60, anchor="center")
            tree.column("Length", width=60, anchor="center")

            # Vertical scrollbar
            vsb = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            tree.pack(side="left", fill="y", expand=True)

            # Insert rectangles
            rows = [(i, rect.width, rect.length) for i, rect in enumerate(problem.rectangles, start=1)]
            for row in rows:
                tree.insert("", "end", values=row)

            # ---------- Bottom Section (fixed) ----------
            bottom_frame = tk.Frame(self.main_frame, bd=1, relief="raised")
            bottom_frame.pack(fill="x", side="bottom")

            separator = tk.Frame(bottom_frame, height=2, bd=1, relief="sunken")
            separator.pack(fill="x", padx=5, pady=5)

            params_label = tk.Label(
                bottom_frame,
                text=f"Given Parameters: Box Length = {box_length}, Rectangles = {rect_number}, Min Rectangle Size = {rect_min_size}, Max Rectangle Size = {rect_max_size}",
                font=("Arial", 14),
                fg="black"
            )
            params_label.pack(pady=5)

        except Exception as e:
            error_label = tk.Label(self.main_frame, text=f"Error: {str(e)}", font=self.font, fg="red")
            error_label.pack(pady=10)



if __name__ == "__main__":
    root = tk.Tk()
    app = PackingGUI(root)
    root.mainloop()

