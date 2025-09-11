"""
    # main
    problem_params = get_problem_params_from_GUI()
    problem = RectProblem(problem_params)

    # User sets Strategy in GUI
    strategy = Strategy()
    algo = strategy.get_algo()
    initial_solution = RectSolution(algo)
    # Konstruktor unterscheidet:
        greedy -> kein rect platziert
        local -> rects reudig platziert

    # GUI: Boxen (leer oder reudig)

    final_solution = algo.solve(initial_solution)
"""


import tkinter as tk
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
            success_label.pack(pady=20)

            # Table frame with border
            rect_frame = tk.Frame(self.main_frame, bd=2, relief="groove", padx=10, pady=10)
            rect_frame.pack(pady=10)

            header = tk.Label(rect_frame, text="Generated Rectangles:", font=("Arial", 16, "underline"))
            header.grid(row=0, column=0, columnspan=3, pady=5)

            tk.Label(rect_frame, text="ID", font=self.font, borderwidth=1, relief="solid", width=10).grid(row=1, column=0, padx=1, pady=1, sticky="nsew")
            tk.Label(rect_frame, text="Width", font=self.font, borderwidth=1, relief="solid", width=10).grid(row=1, column=1, padx=1, pady=1, sticky="nsew")
            tk.Label(rect_frame, text="Length", font=self.font, borderwidth=1, relief="solid", width=10).grid(row=1, column=2, padx=1, pady=1, sticky="nsew")

            # Fill table with generated rectangles
            for i, rect in enumerate(problem.rectangles, start=1):
                tk.Label(rect_frame, text=str(i), font=self.font, borderwidth=1, relief="solid", width=10).grid(row=i+1, column=0, padx=1, pady=1, sticky="nsew")
                tk.Label(rect_frame, text=str(rect.width), font=self.font, borderwidth=1, relief="solid", width=10).grid(row=i+1, column=1, padx=1, pady=1, sticky="nsew")
                tk.Label(rect_frame, text=str(rect.length), font=self.font, borderwidth=1, relief="solid", width=10).grid(row=i+1, column=2, padx=1, pady=1, sticky="nsew")

            # Show given user inputs at the bottom of the window.
            params_label = tk.Label(
                self.main_frame,
                text=f"Given Parameters: \t Box Length = {box_length}, Rectangles = {rect_number}, Min Rectangle Size = {rect_min_size}, Max Rectangle Size = {rect_max_size}",
                font=("Arial", 14),
                fg="black"
            )
            params_label.pack(side="bottom", pady=15)

            # Separate parameters with horizontal line. Drawn last because of side="bottom".
            separator = tk.Frame(self.main_frame, height=2, bd=1, relief="sunken")
            separator.pack(side="bottom", fill="x", padx=5, pady=5)

        except Exception as e:
            # Show error directly in the main window
            error_label = tk.Label(self.main_frame, text=f"Error: {str(e)}", font=self.font, fg="red")
            error_label.pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = PackingGUI(root)
    root.mainloop()