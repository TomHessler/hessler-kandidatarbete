import networkx as nx
import itertools

def FindForbidden(H, G):
	"""Checks (brute-force) if G contains H as an induced subgraph
    
    Parameters
    ----------
    H, G  : nexworkx.Graph
         	Two graph.
         
    Returns
    -------
	True if H is an induced subgraph of H and, otherwise, False
    """

	N=H.number_of_nodes()
	V_set = set(G.nodes)
	for l in range(5,N+1):
		AllSubsets=list(itertools.combinations(V_set, l))
		for W in AllSubsets:
			subG =  G.subgraph(W)
			if(nx.is_isomorphic(H, subG)): 
				return True
	return False

def isGatex(G):
    with open('FinalForbiddenGatex-G6format.txt', 'r') as file:
        F = [nx.from_graph6_bytes(line.strip().encode('utf-8')) for line in file]
    for forbidden in F:
        if FindForbidden(forbidden,G):
            return False
    return True