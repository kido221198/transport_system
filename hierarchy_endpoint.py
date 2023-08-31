from hierarchy_repository import SceneSetup, Pallet, Workstation
from copy import deepcopy
import random
import logging
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


class Controller:
    """
    Represent the Control layer of the MVC pattern.
    Have public interfaces for Simulator or Visualization.
    Import the repository classes for the simulating purpose,
    or import the TCP client for interacting with actual models.
    """

    def __init__(self, topology='hex_topology4.json', roadmap='hex_roadmap4.json', H=1, K=10., origin=True):
        """
        Initialize the Controller.
        Load up the Workspace Configuration.
        Load up the Topological and Roadmap Graph.
        """
        logging.basicConfig(filename='last_log.txt', filemode='w', level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S')

        # Load the Workspace configuration
        self.__workspace = SceneSetup.workspace
        for wall in SceneSetup.wall:
            x, y, w, h = wall
            self.__workspace[x:x + w, y:y + h] = SceneSetup.WALL
        for ws in SceneSetup.workstation:
            x, y, w, h = ws
            self.__workspace[x:x + w, y:y + h] = SceneSetup.WORKSTATION

        # Update information of parking slot and queueing slot
        for ps in SceneSetup.parking_slot:
            x, y = ps
            self.__workspace[x, y] = SceneSetup.PARK
        for ws in SceneSetup.queueing_slot:
            for qs in ws:
                x, y = qs
                self.__workspace[x, y] = SceneSetup.QUEUEING

        # Initiate the graph and properties
        self.topology__ = topology
        self.roadmap__ = roadmap
        self.__init_graph()
        self.__H = H
        self.__K = K
        self.__hist_V = []
        self.__unexpected_event = False
        self.__idle_step = 0
        self.__origin = origin

        # Common memory allocation
        self.__pallets = dict()
        self.__workstations = dict()
        self.__add_workstations()
        self.__logger = []

    def __init_graph(self):
        """
        Import topology and roadmap configuration.
        """
        self.__G = nx.DiGraph(dim=(59, 7))
        self.__V = nx.DiGraph(dim=(59, 7))
        import json

        # Create topology graph
        with open(f"graphs/{self.topology__}", 'r') as f:
            g = json.load(f)
            self.__V.add_nodes_from([node["node"] for node in g], )
            self.__V.add_weighted_edges_from([(node['node'], node['neighbor'][i], node['distance'][i])
                                              for node in g for i in range(len(node['neighbor']))])
            for e in self.__V.edges:
                self.__V.edges[e[0], e[1]]['distance'] = self.__V.edges[e[0], e[1]]['weight']
            for n in g:
                self.__V.nodes[n['node']]['sub'] = []
                self.__V.nodes[n['node']]['capacity'] = n['capacity']
                self.__V.nodes[n['node']]['occupied'] = 0
                self.__V.nodes[n['node']]['weight'] = 0

            self.__V_laplacian = nx.to_numpy_array(self.__V)
            for i, row in enumerate(self.__V_laplacian):
                row[i] = -sum(row)
                row *= -1
            # print(self.__V_laplacian)

        # Create roadmap graph
        with open(f"graphs/{self.roadmap__}", 'r') as f:
            g = json.load(f)
            self.__G.add_nodes_from([node["node"] for node in g])
            self.__G.add_weighted_edges_from([(node['node'], node['neighbor'][i], node['distance'][i])
                                              for node in g for i in range(len(node['neighbor']))])
            for n in g:
                node_id = n['node']
                self.__V.nodes[node_id // 100]['sub'].append(node_id)
                self.__G.nodes[node_id]['node'] = node_id
                self.__G.nodes[node_id]['occupied'] = 0
                self.__G.nodes[node_id]['position'] = n['position']
                self.__G.nodes[node_id]['host'] = node_id // 100

            self.__G_weighted_edges = [edge for edge in self.__G.edges if edge[0] // 100 != edge[1] // 100]

        # Extended Graph declaration
        self.__ext_G = []
        self.__ext_V = []

    def __log(self, s):
        if len(self.__logger) > 15:
            self.__logger.pop(0)
        self.__logger.append(s)

    def __add_workstations(self):
        """
        Add workstations into database.
        """
        for ws_name in SceneSetup.workstation_index.keys():
            self.__workstations[ws_name] = Workstation(ws_name)

    def __find_workstation(self, pos_x, pos_y):
        """
        Check which workstation contains the input coordinate.

        :param pos_x: integer, x-axis coordinate.
        :param pos_y: integer, y-axis coordinate.
        :return: string, alias of the Workstation, None if not fond.
        :return: Workstation, None if not found.
        """
        for name, ws in self.__workstations.items():
            if ws.check_inside(pos_x, pos_y):
                return name, ws
        return None, None

    def __move_pallet(self, pallet_id):
        """
        Move pallet according to its desired path.
        :param pallet_id: string, ID of the pallet.
        """
        pallet = self.__pallets[pallet_id]

        # Find the current position and clear the table cell
        prev_x, prev_y = pallet.get_position()
        self.__workspace[prev_x, prev_y] = (self.__workspace[prev_x, prev_y] // 10) * 10 + SceneSetup.EMPTY
        pallet.move()

        # Get new position and update the table
        new_x, new_y = pallet.get_position()
        self.__workspace[new_x, new_y] = (self.__workspace[new_x, new_y] // 10) * 10 + SceneSetup.OCCUPIED

        if len(pallet.get_path()) == 0 and random.random() < 0.08:
            self.move_to_ws(pallet_id, random.choice(list(SceneSetup.workstation_index.keys())))

    def __is_empty(self, x, y):
        """
        Check if the designated slot is empty, simply by checking the last digit.

        :param x: integer, x-axis value.
        :param y: integer, y-axis value.
        :return: boolean, True if the condition is match, False otherwise.
        """
        return self.__workspace[x, y] % 10 == SceneSetup.EMPTY

    def __is(self, x, y, name):
        """
        Check what kind of slot is the designated position, simply by checking the 2nd-to-last digit.

        :param x: integer, x-axis value.
        :param y: integer, y-axis value.
        :param name: string, name of the block class.
        :return: boolean, True if the condition is match, False otherwise.
        """
        return self.__workspace[x, y] // 10 * 10 == eval(f"SceneSetup.{name}")

    def __negotiate(self, conflicts, excluded=[]):
        """
        Pick up a winner in a group of conflicting pallets based on policies.

        :param conflicts: list, each element as ID of conflicting pallet.
        :param excluded: list, each element as ID of prioritized pallet.
        :return: string, ID of the winning pallet.
        """
        s1 = f"Negotiating... {[c for c in conflicts]}"
        logging.info(s1)

        if len(conflicts) > 1:
            # Some pallets have higher privilege
            if len(excluded) > 0:
                winner = excluded[0]
            # None is prioritized
            else:
                # Longest Waiting
                delays = [self.__pallets[p].get_waited() for p in conflicts]
                winner = conflicts[[i for i, d in enumerate(delays) if d == max(delays)][0]]

                ## Random selection
                # winner = random.choice(conflicts)
            s2 = f"Negotiating ended: {winner} won."
        else:
            winner = None
            s2 = f"Negotiating ended: None."

        logging.info(s2)
        self.__log(f'{s1} {s2}')

        return winner

    def __set_path(self, pallet_id, path):
        """
        Call path setter of Pallet instance
        :param pallet_id: string, ID of demanding pallet.
        :param path: list, each element as ID of node in G.
        """
        self.__pallets[pallet_id].set_path(path)

    def __update_traffic(self):
        """
        Take the 2nd window in Extended Graph as the current.
        """
        self.__V = self.__ext_V[1]
        self.__G = self.__ext_G[1]

    def __calculate_timewindow(self):
        """
        Create predict H-long windows as Extended Graph.
        Update the traffic cost in each window with according predefined paths.
        """
        # Reduced copy costing time
        self.__ext_G = [deepcopy(self.__G) for _ in range(2)] + [None for _ in range(self.__H - 1)]
        self.__ext_V = [deepcopy(self.__V) for _ in range(2)] + [None for _ in range(self.__H - 1)]

        # Gather all paths
        paths = []
        for pallet_id, pallet in self.__pallets.items():
            path = pallet.get_path()
            paths.append(path)

        self.update_paths(paths)

    def __coordination(self):
        """
        Check for collisions and resolve if any.
        Looking toward H-long windows in the future.
        """
        t = 1
        # check windows 1, 2, ... H as 0 is current state
        while t < self.__H + 1:
            node = self.__check_collision(t)
            p1, p2 = self.__check_transition(t)

            # No conflict, move to next window
            if node is None and p1 is None and p2 is None:
                t += 1

            # Lot-typed conflict(s) found, continuous resolve
            elif p1 is None:
                conflicts = self.__trace_collision(node, t)
                logging.warning(f"Lot Conflicts: {[p for p in conflicts]}.")
                [logging.warning(f"Pallet {p}: {self.__pallets[p].get_path()}") for p in conflicts]
                excluded = [p for p in conflicts if self.__pallets[p].get_path()[t - 1] == node]

                # Negotiation strategy
                winner = self.__negotiate(conflicts, excluded)

                for pallet_id in conflicts:
                    if winner != pallet_id:
                        pallet = self.__pallets[pallet_id]
                        path = pallet.get_path()

                        # Solution: wait for one iteration at t
                        path = path[:t] + [path[t - 1]] + path[t - 1:]

                        # # Solution: find an alternative route, wait if cannot
                        # sub_path = self.generate_path(pallet_id, self.__pallets[pallet_id].get_goal(),
                        #                               source=path[t - 1],
                        #                               excluded=[self.__pallets[winner].get_path()[t]])
                        # path = path[:t - 1] + sub_path

                        # Update the path
                        self.__set_path(pallet_id, path)

                # Recalculate for recheck
                self.__calculate_timewindow()

            # Transition conflict(s) found
            else:
                logging.warning(f"Transition Conflicts: {p1, p2}.")
                logging.warning(f"Pallet {p1}: {self.__pallets[p1].get_path()}")
                logging.warning(f"Pallet {p2}: {self.__pallets[p2].get_path()}")

                # Negotiation strategy
                winner = self.__negotiate([p1, p2])

                for pallet_id in [p1, p2]:
                    if pallet_id != winner:
                        pallet = self.__pallets[pallet_id]

                        # Replace the part of path starting from the collision
                        path = pallet.get_path()
                        sub_path = self.generate_path(pallet_id, self.__pallets[pallet_id].get_goal(),
                                                      source=path[t - 1],
                                                      excluded=[self.__pallets[winner].get_path()[t - 1]])
                        path = path[:t - 1] + sub_path

                        self.__set_path(pallet_id, path)
                self.__calculate_timewindow()

    def __trace_collision(self, node, t):
        """
        Find pallets caused the lot-typed collision at a node at future t.

        :param node: int, index of the node where the collision occurs.
        :param t: the next t iterations when collision occurs.
        :return: list, array of pallet_id.
        """
        conflicting_pallets = []

        for pallet_id, pallet in self.__pallets.items():
            path = pallet.get_path()

            # Check if the pallet is moving at time t and at node
            if len(path) > t and node == path[t]:
                conflicting_pallets.append(pallet_id)

        return conflicting_pallets

    def __check_collision(self, t):
        """
        Check if any node G at future t is occupied more than 1.
        :param t: integer, belongs to [1, H].
        :return: string, ID of the crammed node, None if not found any.
        """
        # Moving into the same area
        for node in self.__ext_G[t]:
            if self.__ext_G[t].nodes[node]['occupied'] > 1:
                logging.warning(f"Collision at NodeG {node} time T+{t}")
                return node

        return None

    def __check_transition(self, t):
        """
        Check if any there is exchange collision at future t.
        :param t: integer, belongs to [1, H].
        :return: string x2, IDs of two neighboring nodes, None x2 if not found any.
        """
        paths = {}
        for pallet_id, pallet in self.__pallets.items():
            path = pallet.get_path()
            prev_position = path[t - 1] if t < len(path) + 1 else path[-2] if len(path) > 1 else path[0]

            next_position = path[t] if t < len(path) else path[-1]
            paths[pallet_id] = [prev_position, next_position]

        for p1, t1 in paths.items():
            for p2, t2 in paths.items():
                if p1 != p2 and t1[0] == t2[1] and t1[1] == t2[0]:
                    return p1, p2

        return None, None

    # TODO: add transition checking
    def __sim_verify(self):
        """
        Verification after each simulation iteration.
        :return: node, ID of node which is crammed, None if not found any.
        """
        for node in self.__G:
            if self.__G.nodes[node]['occupied'] > 1:
                logging.critical(f"Collision at NodeG {node}")
                return node

    def add_pallet(self, pos_x=SceneSetup.DEFAULT_FEED_X, pos_y=SceneSetup.DEFAULT_FEED_Y):
        """
        Add a new pallet to the system with auto incremental ID indexing.
        Default position would be used if no specific initial position provided.
        Update the workstation state if the pallet was put in any.

        :param pos_x: integer, initial x-axis value
        :param pos_y: integer, initial y-axis value
        :return pallet_id: string, ID of the pallet
        """
        # Check indexing and create a new one
        if len(self.__pallets.keys()) == 0:
            pallet_id = "001"
        else:
            pallet_id = str(max([int(idx) for idx in self.__pallets.keys()]) + 1).zfill(3)

        new_pallet = None

        # Create a new pallet instance
        for node_id in self.__G.nodes:
            if (node := self.__G.nodes[node_id])['position'] == [pos_x, pos_y]:
                new_pallet = Pallet(pallet_id, node['node'])
                node['occupied'] += 1
                (host := self.__V.nodes[node['host']])['occupied'] += 1
                if self.__origin:
                    host['weight'] = self.__K * (host['occupied'] / (host['capacity'] - host['occupied'])
                                                 if host['occupied'] < host['capacity'] else host['capacity'])
                else:
                    host['weight'] = self.__K * host['occupied'] / host['capacity']
                break

        # Check if the pallet was put inside any workstation
        name, ws = self.__find_workstation(pos_x, pos_y)
        if name is not None:
            # Update the current workstation alias
            new_pallet.set_ws(name)
            # Update the state of the workstation
            # TODO: additional property telling which pallet is inside the Workstation
            ws.set_state(Workstation.BUSY)

        # Update the pallet list and the prediction window
        self.__pallets[pallet_id] = new_pallet

        return pallet_id

    def remove_pallet(self, pallet_id):
        """
        Take the pallet out of line.
        Remove the pallet instance from the list and the prediction window.
        :param pallet_id: string, the ID of the pallet
        """
        del self.__pallets[pallet_id]
        del self.__predict_window[pallet_id]

    def move_to_ws(self, pallet_id, ws_name):
        """
        Generate a route to a workstation for a pallet.

        :param pallet_id: string, ID of the pallet
        :param ws_name: string, alias of the Workstation
        """
        pallet = self.__pallets[pallet_id]
        # queue = self.__workstations[ws_name].get_queue_path()
        logging.info(f"Received new order for pallet {pallet_id} going to workstation {ws_name}.")

        dest = self.__workstations[ws_name].get_entry().tolist()
        for node in self.__G.nodes:
            if self.__G.nodes[node]['position'] == dest:
                # self.generate_path(pallet_id, node)
                pallet.set_goal(node)
                pallet.set_target(ws_name)
                return

    def update_paths(self, paths):
        """
        Update occupied property of nodes in Extended Graph according to input paths.
        After that calculate the weight on each edge in V.
        :param paths: list, each element as a list of IDs of node in G
        """
        # TODO: concern about shallow copy
        paths = [path + [path[-1] for _ in range(max(0, self.__H - len(path) + 1))] for path in paths]

        # Update windows 1, 2, ... H as 0 is current state
        for i in range(1, self.__H + 1):
            for p in paths:
                # Change occupation
                # logging.debug(f"Window {i} {p[i - 1]} {p[i]}")
                new_node_g = self.__ext_G[i].nodes[(new_id_g := p[i])]
                prev_node_g = self.__ext_G[i].nodes[(prev_id_g := p[i - 1])]
                if prev_id_g != new_id_g:
                    new_node_g['occupied'] += 1
                    prev_node_g['occupied'] -= 1

                    # Find host
                    new_node_v = self.__ext_V[i].nodes[(new_id_v := new_node_g['host'])]
                    prev_node_v = self.__ext_V[i].nodes[(prev_id_v := prev_node_g['host'])]

                    # If crossing sectors
                    if new_id_v != prev_id_v:
                        # Change occupation
                        new_node_v['occupied'] += 1
                        prev_node_v['occupied'] -= 1

                        # # Update weight
                        # new_node_v['weight'] = self.__K * (
                        #     new_node_v['occupied'] / (new_node_v['capacity'] - new_node_v['occupied'])
                        #     if new_node_v['occupied'] < new_node_v['capacity'] else new_node_v['capacity'])
                        #
                        # prev_node_v['weight'] = self.__K * (
                        #     prev_node_v['occupied'] / (prev_node_v['capacity'] - prev_node_v['occupied'])
                        #     if prev_node_v['occupied'] < prev_node_v['capacity'] else prev_node_v['capacity'])
                        #
                        # # Update weight
                        # if (prev_id_v, new_id_v) in self.__ext_V[i].edges:
                        #     prev_edge_v = self.__ext_V[i].edges[prev_id_v, new_id_v]
                        #     prev_edge_v['weight'] = prev_edge_v['distance'] + new_node_v['weight']
                        # if (new_id_v, prev_id_v) in self.__ext_V[i].edges:
                        #     new_edge_v = self.__ext_V[i].edges[new_id_v, prev_id_v]
                        #     new_edge_v['weight'] = new_edge_v['distance'] + prev_node_v['weight']

            # Update weight on each node
            # Formulation
            arr = []
            for node in self.__ext_V[i].nodes:
                node_v = self.__ext_V[i].nodes[node]
                if self.__origin:
                    node_v['weight'] = self.__K * (node_v['occupied'] / (node_v['capacity'] - node_v['occupied'])
                                                   if node_v['occupied'] < node_v['capacity'] else node_v['capacity'])
                else:
                    node_v['weight'] = self.__K * node_v['occupied'] / node_v['capacity']
                    arr.append([node_v['weight']])

            if not self.__origin:
                # Consensus
                weights = np.array(arr)
                new_weights = (1 + self.__K * self.__V_laplacian) @ weights
                for node in self.__ext_V[i].nodes:
                    node_v = self.__ext_V[i].nodes[node]
                    # node_v['weight'] = max(new_weights[node - 1, 0], 0)
                    node_v['weight'] = new_weights[node - 1, 0]

            # Update weight on each edge V
            for node in self.__ext_V[i].nodes:
                node_v = self.__ext_V[i].nodes[node]
                for edge in self.__ext_V[i].in_edges(node_v):
                    # edge['weight'] = edge['distance'] + node_v['weight']
                    edge['weight'] = max(edge['distance'] + node_v['weight'], 0)

            # Reset and Update weight on each edge G
            for e in self.__G_weighted_edges:
                self.__ext_G[i].edges[e]['weight'] = 1.

            for e in self.__G_weighted_edges:
                edge = self.__ext_G[i].edges[e]
                new_v = self.__ext_V[i].nodes[e[1] // 100]
                edge['weight'] = max(new_v['weight'] + edge['weight'], 0)


            # Copy ith window to (i+1)th for continuous update
            if i != self.__H:
                self.__ext_G[i + 1] = deepcopy(self.__ext_G[i])
                self.__ext_V[i + 1] = deepcopy(self.__ext_V[i])

    def generate_path(self, pallet_id, target, source=None, excluded=[]):
        """
        Generate path consisting of slots from the current pallet's position to the desired one.
        Different algorithms/approaches can be defined within.

        :param pallet_id: string, ID of the pallet
        :param target: integer, ID of end node in G
        :param source: integer, ID of starting node in G
        :param excluded: list, each element as ID of occupied node in G
        """
        pallet = self.__pallets[pallet_id]
        if source is None:
            source = pallet.get_position()

        excluded_v = [self.__G.nodes[g]['host'] for g in excluded]
        available_v = [v for v in self.__V.nodes if v not in excluded_v or v in [target // 100, source // 100]]

        try:
            seq_v = nx.dijkstra_path(nx.subgraph(self.__V, available_v), source // 100, target // 100, weight='weight')
            # seq_v = nx.bellman_ford_path(nx.subgraph(self.__V, available_v), source // 100, target // 100, weight='weight')
        except nx.NetworkXNoPath as e:
            logging.warning(f"Pallet {pallet_id} has to go through {excluded_v} due to no sufficient path to {target}.")
            seq_v = nx.dijkstra_path(self.__V, source // 100, target // 100, weight='weight')
            # seq_v = nx.bellman_ford_path(self.__V, source // 100, target // 100, weight='weight')

        sub_v = [sub for v in seq_v for sub in self.__V.nodes[v]['sub']]
        available_g = [v for v in sub_v if v not in excluded]
        # available_g = [sub for v in seq_v for sub in self.__V.nodes[v]['sub']]
        # TODO: check if weight in W is updated
        # Also include the current position
        try:
            path = nx.dijkstra_path(nx.subgraph(self.__G, available_g), source, target, weight='weight')
            # path = nx.bellman_ford_path(nx.subgraph(self.__G, available_g), source, target, weight='weight')
        except nx.NetworkXNoPath as e:
            logging.warning(f"Pallet {pallet_id} staying in {source} due to no sufficient path to {target}.")
            path = [source, source]

        logging.info(
            f"Generated path for pallet {pallet_id} going from node {source}: {path} excluding node {excluded}.")
        return path

    def update(self):
        """
        Make the system moving forward one step
        1. Save the current state to history
        2. Assign new job and generate route for idle pallets
        3. Generate Predict Window
        4. Coordination
        5. Execute the next step of every pallet
        6. Verify conflicts
        """
        logging.info("###### Started new update round ######")

        for node in self.__V.nodes:
            logging.info(f"NodeV {node}: {self.__V.nodes[node]['occupied']} occupied, {self.__V.nodes[node]['weight']}")
        self.__hist_V.append(self.__V)

        self.__unexpected_event = False

        # Generate path (optional)
        # Automatic move to new WS
        for pallet_id, pallet in self.__pallets.items():
            if pallet.get_goal() == pallet.get_position() or pallet.get_goal() is None:
                self.__unexpected_event = True
                available_ws = list(SceneSetup.workstation_index.keys())
                available_ws.remove(pallet.get_ws()) if pallet.get_ws() is not None else None
                self.move_to_ws(pallet_id, random.choice(available_ws))

            if self.__unexpected_event or self.__idle_step % (self.__H) == 0:
                path = self.generate_path(pallet_id, pallet.get_goal())  # Also include the current position
                self.__set_path(pallet_id, path)

        # Update the timewindow
        self.__calculate_timewindow()

        # Coordination
        if self.__unexpected_event or self.__idle_step % self.__H == 0:
            self.__coordination()
            self.__idle_step = 0

        # Execute movement
        for pallet in self.__pallets.values():
            pallet.move()
        self.__update_traffic()
        self.__sim_verify()
        self.__idle_step += 1

    def get_path(self, pallet_id):
        """
        Return predefined path of demanding pallet

        :param pallet_id: string, ID of demanding pallet
        :return: list, each element as ID of node in G
        """
        return self.__pallets[pallet_id].get_path()

    def get_ws_size(self):
        """
        Return size width, height
        :return: integer x2, as the width and height of the workspace
        """
        return self.__workspace.shape[0], self.__workspace.shape[1]

    def get_workspace(self):
        """
        Get current state of the workspace
        :return: list of
        """
        return self.__workspace.tolist()

    def get_pallet(self, pallet_id):
        """
        Return position of input pallet in graph G
        :param pallet_id: string, ID of demanding pallet
        :return: dict, with integer value of x and y as values
        """
        node = self.__pallets[pallet_id].get_position()
        return dict({'x': self.__G.nodes[node]['position'][0], 'y': self.__G.nodes[node]['position'][1]})

    def get_all_pallets(self):
        """
        Return all pallets position in graph G
        :return: dict, each key as ID of pallet and value as coordinate of pallet
        """
        return {pallet_id: self.get_pallet(pallet_id) for pallet_id in self.__pallets}

    def get_log(self):
        return self.__logger[:]

    def get_occupied(self):
        return self.__V.nodes.data('occupied')

    def get_capacity(self):
        return self.__V.nodes.data('capacity')

    def get_history(self):
        """
        Get historical tracks of all pallets
        :return: list, each element as a list of G-nodes
        """
        return [pallet.get_history() for pallet in self.__pallets.values()]

    def get_G(self):
        return self.__G

    def get_V(self):
        return self.__V

    def history_plot(self):
        """
        Plot the Extended Graph based on historical tracks of all pallets
        """
        ax = plt.figure().add_subplot(projection='3d')
        ax.invert_yaxis()

        # Plot a base map using the x and y axes.
        x = [self.__G.nodes[node]['position'][0] for node in self.__G.nodes]
        y = [self.__G.nodes[node]['position'][1] for node in self.__G.nodes]
        ax.scatter(x, y, zs=0, zdir='z', label='roadmap', marker='.')

        # Plot the tracks
        for i, pallet in enumerate(self.__pallets.values()):
            hist = pallet.get_history()
            x = [self.__G.nodes[node]['position'][0] for node in hist]
            y = [self.__G.nodes[node]['position'][1] for node in hist]
            z = [i for i in range(len(hist))]
            ax.plot(x, y, z)

        # Make legend, set axes limits and labels
        ax.legend()
        ax.set_xlim(0, 57)
        ax.set_ylim(0, 7)
        ax.set_zlim(0, len(self.__hist_V))
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Iteration')
        ax.set_box_aspect((58, 24, 30))

        # Customize the view angle so it's easier to see that the scatter points lie
        # on the plane y=0
        ax.view_init(elev=10., azim=-30, roll=0)

        plt.show()


if __name__ == '__main__':
    cont = Controller()
    cont.add_pallet("001", 0, 7)
    cont.generate_path("001", 12, 7)
    for _ in range(20):
        cont.update()
        print(cont.get_path("001"))
