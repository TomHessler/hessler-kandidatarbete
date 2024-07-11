import networkx as nx
from itertools import combinations, chain

def apply_heuristic(graph):
    forbidden_graph_set = load_graphs_from_file('FinalForbiddenGatex-G6format.txt')
    edges_to_be_removed = []

    while True:
        optimal_edge = find_optimal_edge(graph, forbidden_graph_set)
        if optimal_edge:
            graph.remove_edge(*optimal_edge)
            edges_to_be_removed.append(optimal_edge)
        else: break
    return edges_to_be_removed

def find_forbidden_induced_subgraph(graph, forbidden_graph_set):
    forbidden_induced_subgraphs = []
    for subgraph in all_induced_subgraphs_of_size_5_to_8(graph):
        for forbidden in forbidden_graph_set:
            if nx.is_isomorphic(subgraph, forbidden):
                forbidden_induced_subgraphs.append(subgraph)
    return forbidden_induced_subgraphs

def load_graphs_from_file(file_path):
    with open(file_path, 'r') as file:
        return [nx.from_graph6_bytes(line.strip().encode('utf-8')) for line in file]

def find_optimal_edge(graph, forbidden_graph_set):
    forbidden_induced_subgraphs = find_forbidden_induced_subgraph(graph, forbidden_graph_set)
    edges = []
    if forbidden_induced_subgraphs:
        for forbidden_induced_subgraph in forbidden_induced_subgraphs:
            edges.append(list(forbidden_induced_subgraph.edges()))
    edges = [edge for sublist in edges for edge in sublist]
    if edges:
        return max(edges, key=edges.count)
    else: return None

def all_induced_subgraphs_of_size_5_to_8(graph):
    powerset_of_nodes = list(chain.from_iterable(combinations(graph.nodes(), r) for r in range(5, 9)))

    induced_subgraphs = [nx.induced_subgraph(graph, node_set) for node_set in powerset_of_nodes]

    return induced_subgraphs