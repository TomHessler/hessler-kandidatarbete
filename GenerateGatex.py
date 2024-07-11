import networkx as nx
import random
import string
from tralda.datastructures import Tree

def generate_galled_tree(n):
    tree = Tree.random_tree(n)
    nx_tree = Tree.to_nx(tree)
    tree = nx_tree[0]
    root = nx_tree[1]
    gall_vertices = [vertex for vertex in list(tree.nodes()) if len(list(tree.successors(vertex))) > 2]
    for vertex in gall_vertices:
        tree = add_gall(tree, vertex)
    labels = label_graph(tree)
    return tree, labels

def add_gall(G, vertex):
    children = list(G.successors(vertex))
    gall_size = len(children)
    
    gall_nodes = [f"{vertex}_gall_{i}" for i in range(gall_size)]
    G.add_nodes_from(gall_nodes)
    
    hybrid_vertex_index = random.randint(0, gall_size - 1)
    
    G.add_edge(vertex, gall_nodes[0])
    G.add_edge(vertex, gall_nodes[-1])
    for i in range(hybrid_vertex_index):
        G.add_edge(gall_nodes[i], gall_nodes[i + 1])

    for i in range(gall_size - 1, hybrid_vertex_index, -1):
        G.add_edge(gall_nodes[i], gall_nodes[i - 1])

    for i, child in enumerate(children):
        G.add_edge(gall_nodes[i], child)
        G.remove_edge(vertex, child)
    
    return G

def label_graph(G):
    labels = {}
    if not G.nodes:
        print("Graph is empty. Cannot label.")
        return labels
    for node in G.nodes():
        if node not in labels and len(list(G.successors(node))) > 0:
            labels[node] = 0 if random.random() < 50 / 100 else 1
    letter_label = iter(string.ascii_lowercase)
    next_letter = lambda: next(letter_label, 'a')
    for node in G.nodes():
        if len(list(G.successors(node))) == 0 and node not in labels:
            labels[node] = next_letter()
    return labels

def add_noise(G, noiselevel):
    G_comp = nx.complement(G)
    edges_to_add = int(len(G_comp.edges) * (noiselevel/100))
    edges_to_add_list = random.sample(G_comp.edges(), edges_to_add)
    G.add_edges_from(edges_to_add_list)
    return G

def from_galled_tree_to_gatex(G, labels):
    """
    Convert a galled tree graph G to a GaTEx graph based on the given labels.
    """
    GATEX = nx.Graph()
    # find leaves in G
    leaves = [node for node in G.nodes() if G.out_degree(node) == 0]
    
    # add leaves as nodes in GATEX
    GATEX.add_nodes_from(leaves)
    
    # iterate over pairs of leaves to determine connections in GATEX
    for i in range(len(leaves)):
        for j in range(i + 1, len(leaves)):
            lca = nx.lowest_common_ancestor(G, leaves[i], leaves[j])
            if labels[lca] == 1 or labels[lca] == '1/root':
                # connect the nodes in GATEX if their last common ancestor in G is labeled 1
                GATEX.add_edge(leaves[i], leaves[j])
                
    
    # create GATEXlabels by filtering labels for the leaves
    GATEXlabels = {leaf: labels[leaf] for leaf in leaves}
    
    return GATEX, GATEXlabels

def getGraph(n, noise_level=50):
    G, labels = generate_galled_tree(n)
    GATEX, GATEXlabels = from_galled_tree_to_gatex(G, labels)
    G = add_noise(GATEX, noise_level)
    G = nx.convert_node_labels_to_integers(G)
    return G
    