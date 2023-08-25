import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

G = nx.DiGraph(dim=(57, 7))
pos = None
size = None
temp = None

# with open("graphs/hex_topology.json", 'r') as f:
#     import json
#     temp = json.load(f)
#     for node in temp:
#         node['distance'] = [round(np.linalg.norm(np.array(node['position']) - np.array(m['position'])), 2)
#                             for n in node['neighbor'] for m in temp if n == m['node']]
#
#     print(temp)


# with open("graphs/hex_topology.json", 'w') as f:
#     import json
#     json.dump(temp, f)

with open("graphs/hex_topology3.json", 'r') as f:
    import json
    g = json.load(f)
    G.add_nodes_from([node["node"] for node in g])
    # [print(f"{node['node']}: {len(node['neighbor']) - len(node['distance'])}") for node in g]
    G.add_weighted_edges_from([(node['node'], node['neighbor'][i], node['distance'][i])
                               for node in g for i in range(len(node['neighbor']))])
    pos = {node["node"]: np.array([node["position"][0], 6 - node["position"][1]]) for node in g}

    try:
        size = [node['capacity'] for node in g]
    except KeyError:
        size = [1] * len(g)


#     print(pos)

# with open("graphs/roadmap.txt", 'r') as f:
#     lines = f.readlines()
#     branches = [line.replace("\n", "").split() for line in lines]
#     j = [{"node": int(l[0]), "position": [int(l[1]), int(l[2])], "neighbor": [int(k) for k in l[3:]], "distance": [1] * len(l[3:])}
#          for l in branches]
#     import json
#     with open("graphs/roadmap.json", "w") as js:
#         json.dump(j, js)

    # tuples = list(map(lambda x: [(x[0], x[i], 1.0) for i in range(3, len(x))], branches))
    # elist = [x for y in tuples for x in y]
    # G.add_weighted_edges_from(elist)
    # pos = {x[0]: np.array([int(x[1]) * 4, 6 - int(x[2])]) for x in branches}
    # print(len(G.edges))


# plt.subplot(111)
nx.draw(G, pos, with_labels=True, **{"node_color": "white", "edgecolors": "black",
                                     "font_size": 10, "node_size": [n * 250 for n in size]})
plt.show()