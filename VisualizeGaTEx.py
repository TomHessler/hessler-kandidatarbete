from GenerateGatex import generate_galled_tree, from_galled_tree_to_gatex
import matplotlib.pyplot as plt
import networkx as nx

def visualizeGaTEx(n):
    G, labels = generate_galled_tree(n)
    GATEX, GATEXlabels = from_galled_tree_to_gatex(G, labels)
    print(len(GATEX.nodes()))
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    nx.draw(G, pos, with_labels=True, labels=labels, node_color='lightgreen', font_weight='bold')
    plt.title(r'Galled-tree, $(N, t)$:', fontsize=14)  # LaTeX formatted title for the Galled Tree
    
    plt.subplot(1, 2, 2)
    pos2 = nx.nx_agraph.graphviz_layout(GATEX, prog="neato")
    nx.draw(GATEX, pos2, with_labels=True, labels=GATEXlabels, node_color='lightblue', font_weight='bold')
    plt.title(r'GaTEx Graph, $G$:', fontsize=14)  # LaTeX formatted title for the GaTEx Graph
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    visualizeGaTEx(7)
