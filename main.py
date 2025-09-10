"""
    # main pseudo code
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

    TODO
        -- strategy kriegt neues algo attribut + getter

"""