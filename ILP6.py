import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, Radiobutton, IntVar
import threading
import cplex
from itertools import permutations
import networkx as nx
from tqdm import tqdm
import matplotlib.pyplot as plt

def generate_ilp_constraints(vertices, forbidden_graphs_info, i):
    # forbidden_graphs_info is expected to be a tuple (forbidden_edges, lone_vertices)
    forbidden_edges, lone_vertices = forbidden_graphs_info
    edge_vertices = set(sum([list(edge) for edge in forbidden_edges], []))
    unique_vertices = edge_vertices.union(lone_vertices)  # include lone vertices
    k = len(unique_vertices)
    constraints = []
    
    for perm in tqdm(list(permutations(vertices, k)), desc=f'Constraint #{i}'):
        mapping = dict(zip(sorted(unique_vertices), perm))
        include_edges_vars = [f"y{min(mapping[u], mapping[v])}{max(mapping[u], mapping[v])}" for u, v in forbidden_edges]
        all_possible_edges = {(min(i, j), max(i, j)) for i in perm for j in perm if i != j}
        defined_edges = {(min(mapping[u], mapping[v]), max(mapping[u], mapping[v])) for u, v in forbidden_edges}
        exclude_edges_vars = [f"y{u}{v}" for u, v in all_possible_edges if (u, v) not in defined_edges]
        coeffs = [1] * len(include_edges_vars) + [-1] * len(exclude_edges_vars)
        constraints.append((include_edges_vars + exclude_edges_vars, coeffs, len(include_edges_vars) - 1))
    return constraints


def solve_ilp_for_graph(graph, constraints, filename, operation_mode):
    problem = cplex.Cplex()
    problem.set_problem_type(cplex.Cplex.problem_type.MILP)

    # Define nodes and edges
    nodes = list(graph.nodes())
    edges = [(u, v) for u in nodes for v in nodes if u < v]

    # Create decision variables for each possible edge
    y_vars = [f"y{min(u, v)}{max(u, v)}" for u, v in edges]
    initial_states = {f"y{min(u, v)}{max(u, v)}": graph.has_edge(u, v) for u, v in edges}

    # Add variables
    problem.variables.add(names=y_vars, lb=[0] * len(y_vars), ub=[1] * len(y_vars), types=['B'] * len(y_vars))

    if operation_mode == 1:
        # Minimize the sum of y_vars to limit addition of edges
        problem.objective.set_sense(problem.objective.sense.minimize)
        problem.objective.set_linear([(y_var, 1) for y_var in y_vars if not initial_states[y_var]])
    elif operation_mode == 2:
        # Maximize the sum of y_vars to limit deletion of edges
        problem.objective.set_sense(problem.objective.sense.maximize)
        problem.objective.set_linear([(y_var, 1) for y_var in y_vars if initial_states[y_var]])
    elif operation_mode == 3:
        # Minimize the symmetric difference between original and new graph
        problem.objective.set_sense(problem.objective.sense.minimize)
        for y_var, initial_state in initial_states.items():
            # Calculate the net effect for each y_var based on initial_state
            net_coefficient = (1 - initial_state) + (-1) * initial_state
            # Set the objective function coefficient for y_var
            problem.objective.set_linear(y_var, net_coefficient)


    # Mode-specific constraints to ensure no deletions or additions where not allowed
    for y_var, initial in initial_states.items():
        if (operation_mode == 1 and initial) or (operation_mode == 2 and not initial):
            # Ensure existing edges are not deleted in mode 1 and no new edges are added in mode 2
            constraint_value = 1 if initial else 0
            problem.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=[problem.variables.get_indices(y_var)], val=[1])],
                senses="E",
                rhs=[constraint_value])

    # Add custom constraints
    for ind, val, rhs in constraints:
        problem.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=ind, val=val)], senses="L", rhs=[rhs])

    problem.solve()

    # Update graph based on solution values
    solution_values = problem.solution.get_values()
    updated_graph = graph.copy()
    for (y_var, value), (u, v) in zip(zip(y_vars, solution_values), edges):
        if value > 0.5:
            updated_graph.add_edge(u, v)
        else:
            if updated_graph.has_edge(u, v):
                updated_graph.remove_edge(u, v)
    changed_edges = [(u, v) for (u, v) in edges if graph.has_edge(u, v) != updated_graph.has_edge(u, v)]
    changed_edges_formatted = ", ".join(f"({u},{v})" for u, v in changed_edges if u < v)  # List only one of each pair

    # Write updated graph and changes to file
    with open(filename, 'a') as f:
        f.write("Original Graph:\n")
        original_adj_list = nx.generate_adjlist(graph)
        for line in original_adj_list:
            f.write(line + '\n')
        f.write("\nUpdated Graph:\n")
        updated_adj_list = nx.generate_adjlist(updated_graph)
        for line in updated_adj_list:
            f.write(line + '\n')
        f.write("Changed Edges:\n")
        f.write(changed_edges_formatted + '\n\n')

    return updated_graph

def run_ilp(graphs, forbidden, filename, operation_mode):
    diffs = []
    vertices = list(graphs[0].nodes())
    constraints = []
    for i, forbidden_graph in enumerate(forbidden):
        constraints += generate_ilp_constraints(vertices, forbidden_graph, i)
    for i, graph in enumerate(graphs):
        edges_to_delete = solve_ilp_for_graph(graph, constraints, filename, operation_mode)
        diffs.append(len(edges_to_delete))

def setup_ui():
    global root, input_field, output_filename_entry, file_path_label, file_button
    root = tk.Tk()
    root.title("Graph Solver")

    input_field_label = tk.Label(root, text="Enter Forbidden Graphs (One per line):"+
                                 "\n Example: ([(0,1),(1,2)],[3,4])")
    input_field_label.pack(fill='x', padx=10, pady=5)
    input_field = scrolledtext.ScrolledText(root, height=10)
    input_field.pack(fill='both', expand=True, padx=10, pady=5)

    filename_label = tk.Label(root, text="Enter output filename:")
    filename_label.pack(fill='x', padx=10, pady=5)
    output_filename_entry = tk.Entry(root)
    output_filename_entry.pack(fill='x', padx=10, pady=5)

    file_button = tk.Button(root, text="Select Input File", command=open_file)
    file_button.pack(fill='x', padx=10, pady=5)

    file_path_label = tk.Label(root, text="No file selected")
    file_path_label.pack(fill='x', padx=10, pady=5)

    solve_button = tk.Button(root, text="Solve Graphs", command=lambda: solve_graphs(output_filename_entry.get(), operation_mode.get()))
    solve_button.pack(fill='x', padx=10, pady=5)

    operation_mode = IntVar()
    Radiobutton(root, text="Add Edges", variable=operation_mode, value=1).pack(anchor=tk.W)
    Radiobutton(root, text="Delete Edges", variable=operation_mode, value=2).pack(anchor=tk.W)
    Radiobutton(root, text="Edit Graph", variable=operation_mode, value=3).pack(anchor=tk.W)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

def open_file():
    global file_path
    file_path = filedialog.askopenfilename()
    if file_path:
        file_path_label.config(text=file_path)

def read_graphs_from_file(filepath):
    graphs = []
    with open(filepath, 'r') as file:
        adjacency_list = []
        for line in file:
            if line.strip():  # Check if the line is not empty
                adjacency_list.append(line.strip())
            else:  # When an empty line is encountered, process the current adjacency list
                if adjacency_list:
                    # Create a graph from the adjacency list
                    graph = nx.parse_adjlist(adjacency_list, nodetype=int)
                    graphs.append(graph)
                    adjacency_list = []  # Reset for the next graph
        # Check if the last graph needs to be added
        if adjacency_list:
            graph = nx.parse_adjlist(adjacency_list, nodetype=int)
            graphs.append(graph)
    return graphs

def solve_graphs(output_filename, operation_mode):
    print(operation_mode)
    if not file_path:
        messagebox.showerror("Error", "Please select a file first.")
        return
    if not output_filename:
        messagebox.showerror("Error", "Please specify an output filename.")
        return

    try:
        graphs = read_graphs_from_file(file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file: {e}")
        return

    forbidden_input = input_field.get("1.0", tk.END).strip()
    forbidden = []
    for line in forbidden_input.split('\n'):
        # Check if the line is not empty
        if line.strip():
            # Evaluate the line as Python code to convert it to a tuple
            try:
                forbidden_tuple = eval(line.strip())
                # Check if the evaluated result is a tuple
                if isinstance(forbidden_tuple, tuple):
                    # If it's a tuple, check if it has two elements
                    if len(forbidden_tuple) == 2:
                        edges, vertices = forbidden_tuple
                        # Append the edges and vertices to the forbidden list
                        forbidden.append((edges, vertices))
                    else:
                        raise ValueError("Invalid input: Tuple must contain two elements")
                else:
                    raise ValueError("Invalid input: Not a tuple")
            except Exception as e:
                # Handle any errors that occur during evaluation
                messagebox.showerror("Error", f"Invalid input in Forbidden Graphs field: {e}")
                return

    threading.Thread(target=run_ilp, args=(graphs, forbidden, output_filename, operation_mode), daemon=True).start()


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

setup_ui()
