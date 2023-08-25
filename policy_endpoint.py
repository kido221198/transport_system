from policy_repository import SceneSetup, Pallet, Workstation
from astar import astar
import numpy as np
import random
import matplotlib as plt


class Controller:
    """
    Represent the Control layer of the MVC pattern.
    Have public interfaces for Simulator or Visualization.
    Import the repository classes for the simulating purpose,
    or import the TCP client for interacting with actual models.
    """

    def __init__(self):
        """

        """
        self.__workspace = SceneSetup.workspace
        for wall in SceneSetup.wall:
            x, y, w, h = wall
            self.__workspace[x:x + w, y:y + h] = SceneSetup.WALL
        for ws in SceneSetup.workstation:
            x, y, w, h = ws
            self.__workspace[x:x + w, y:y + h] = SceneSetup.WORKSTATION
        if SceneSetup.TRAFFIC_POLICY:
            for ps in SceneSetup.parking_slot:
                x, y = ps
                self.__workspace[x, y] = SceneSetup.PARK
            for ws in SceneSetup.queueing_slot:
                for qs in ws:
                    x, y = qs
                    self.__workspace[x, y] = SceneSetup.QUEUEING
            for rw in SceneSetup.roadway:
                x, y, w, h = rw
                self.__workspace[x:x + w, y:y + h] = SceneSetup.ROADWAY
        self.__pallets = dict()
        self.__workstations = dict()
        self.__add_workstations()
        self.__predict_window = dict()

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

        # Create a new pallet instance
        pos = np.array([pos_x, pos_y])
        new_pallet = Pallet(pallet_id, pos)

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
        self.__predict_window[pallet_id] = list()

        return pallet_id

    def __find_workstation(self, pos_x, pos_y):
        """

        :param pos_x:
        :param pos_y:
        :return:
        """
        for name, ws in self.__workstations.items():
            if ws.check_inside(pos_x, pos_y):
                return name, ws
        return None, None

    def remove_pallet(self, pallet_id):
        """
        Take the pallet out of line.
        Remove the pallet instance from the list and the prediction window.
        :param pallet_id: string, the ID of the pallet
        """
        del self.__pallets[pallet_id]
        del self.__predict_window[pallet_id]

    def predict_motion(self, prev_x, prev_y, x, y):
        """

        :param prev_x:
        :param prev_y:
        :param x:
        :param y:
        :return:
        """
        for pallet in self.__pallets.values():
            # Find all pallets
            px, py = pallet.get_position()
            if px == prev_x and py == prev_y:
                path = pallet.get_path()
                # Check if pallet is about to move and move into the (x, y)
                if path is not None and len(path) > 0 and np.array_equal(path[0], np.array([x, y])):
                    return True
        return False

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
        if new_x != prev_x or new_y != prev_y:
            # Leave workstation
            if self.__is(prev_x, prev_y, 'WORKSTATION') and not self.__is(new_x, new_y, 'WORKSTATION'):
                pallet.set_ws(None)
                name, ws = self.__find_workstation(prev_x, prev_y)
                ws.set_state(Workstation.STARVE)
                print(f"Pallet {pallet_id} leaves Workstation {name}")

            # Enter workstation
            elif self.__is(new_x, new_y, 'WORKSTATION') and self.__is(prev_x, prev_y, 'QUEUEING'):
                name, ws = self.__find_workstation(new_x, new_y)
                pallet.set_target(None)
                pallet.set_ws(name)
                ws.set_state(Workstation.BUSY)
                print(f"Pallet {pallet_id} enters Workstation {name}")

        if len(pallet.get_path()) == 0 and random.random() < 0.08:
            self.move_to_ws(pallet_id, random.choice(list(SceneSetup.workstation_index.keys())))

    def __is_empty(self, x, y):
        """
        Check if the designated slot is empty, simply by checking the last digit.

        :param x: integer, x-axis value
        :param y: integer, y-axis value
        :return: boolean, True if the condition is match, False otherwise
        """
        return self.__workspace[x, y] % 10 == SceneSetup.EMPTY

    def __is(self, x, y, name):
        """
        Check what kind of slot is the designated position, simply by checking the 2nd-to-last digit.

        :param x: integer, x-axis value
        :param y: integer, y-axis value
        :param name: string, name of the block class
        :return: boolean, True if the condition is match, False otherwise
        """
        return self.__workspace[x, y] // 10 * 10 == eval(f"SceneSetup.{name}")

    def __check_queue_available(self, ws_name, idx):
        """
        Check if the specific slot in the queue is going to be empty,
        whether the Workstation is STARVE or any slot the former slots is empty.

        :param ws_name: string, Workstation alias
        :param idx: integer, the index in the slot
        :return: boolean, True if any condition is match, False otherwise
        """
        if self.__workstations[ws_name].get_state() == Workstation.STARVE:
            return True

        # TODO: check if the index is out of range
        for x, y in self.__workstations[ws_name].get_queue_path()[:idx + 1]:
            if self.__is_empty(x, y):
                return True

        return False

    def __observe(self, pallet_id):
        """
        Check the environment around the pallet and alternate the path if necessary.
        Final decision (w/ or w/o modifications) will be saved into the prediction window

        :param pallet_id: string, ID of the pallet
        """
        pallet = self.__pallets[pallet_id]
        cur_x, cur_y = pallet.get_position()
        path = pallet.get_path()

        # Only consider when moving
        if path is not None and len(path) > 0:
            new_x, new_y = path[0]

            # Crossing the roadway
            # TODO: check the condition of crossing the roadway
            if self.__is(cur_x, cur_y, 'ROADWAY') and self.__is(new_x, new_y, 'ROADWAY') and cur_y != new_y:
                # From 3rd row to 4th row
                if cur_y == SceneSetup.roadway[0][1]:
                    # Check if there is incoming pallet and the opposite slot is empty
                    if self.predict_motion(new_x - 1, new_y, new_x, new_y) or not self.__is_empty(new_x, new_y):

                        # If in middle roadway, continue moving
                        if cur_x > SceneSetup.roadway[0][0]:
                            path = list([np.array([cur_x - 1, cur_y]),
                                         np.array([cur_x - 1, new_y])]) + path
                        # If at the end of the road, stay still
                        else:
                            path = list([np.array([cur_x, cur_y])]) + path

                        # Update the prediction window
                        self.__predict_window[pallet_id] = path

                # From 4th row to 3rd row
                elif cur_y == SceneSetup.roadway[1][1]:
                    # Check if there is incoming pallet
                    if self.predict_motion(new_x + 1, new_y, new_x, new_y) or not self.__is_empty(new_x, new_y):

                        # If in middle roadway, continue moving
                        if cur_x < SceneSetup.roadway[1][0] + SceneSetup.roadway[1][2]:
                            path = list([np.array([cur_x + 1, cur_y]),
                                         np.array([cur_x + 1, new_y])]) + path
                        # If at the end of the road, stay still
                        else:
                            path = list([np.array([cur_x, cur_y])]) + path

                        # Update the prediction window
                        self.__predict_window[pallet_id] = path

                # There should not be any errors here
                else:
                    print(f"Controller.__observer({pallet_id}): Unexpected error!")

            # Moving within queue slots
            elif self.__is(new_x, new_y, 'QUEUEING'):
                ws_name = pallet.get_target()
                queue_index = self.__workstations[ws_name].get_queue(new_x, new_y)

                # Wait if the queue is not about moving and front slot is occupied
                if not self.__is_empty(new_x, new_y) or not self.__check_queue_available(ws_name, queue_index):
                    path = list([np.array([cur_x, cur_y])]) + path
                    # Update the prediction window
                    self.__predict_window[pallet_id] = path

            # Moving from queueing slot into workstation
            elif self.__is(cur_x, cur_y, 'QUEUEING') and self.__is(new_x, new_y, 'WORKSTATION'):
                ws_name = pallet.get_target()

                # Wait if the Workstation is not demanding for a new pallet
                if self.__workstations[ws_name].get_state() != Workstation.STARVE:
                    path = list([np.array([cur_x, cur_y])]) + path
                    # Update the prediction window
                    self.__predict_window[pallet_id] = path

            # Entering the roadway
            elif not self.__is(cur_x, cur_y, 'ROADWAY') and self.__is(new_x, new_y, 'ROADWAY'):
                # Checking a set of conditions where
                # 1: No upcoming pallets from the left
                # 2: No upcoming pallets from the right
                # 3: No upcoming pallets from the top
                # 4: No upcoming pallets from the bottom

                # Find if any movements in each direction
                cond_1 = self.predict_motion(new_x - 1, new_y, new_x, new_y)
                cond_2 = self.predict_motion(new_x + 1, new_y, new_x, new_y)
                cond_3 = self.predict_motion(new_x, new_y - 1, new_x, new_y)
                cond_4 = self.predict_motion(new_x, new_y + 1, new_x, new_y)

                # Exclude the self pallet from checking movements
                counter_1 = (cur_x == new_x - 1) and (cur_y == new_y)
                counter_2 = (cur_x == new_x + 1) and (cur_y == new_y)
                counter_3 = (cur_x == new_x) and (cur_y == new_y - 1)
                counter_4 = (cur_x == new_x) and (cur_y == new_y + 1)

                # Movement priority, only consider if it is on ROADWAY
                sub_1 = self.__is(new_x - 1, new_y, 'ROADWAY')
                sub_2 = self.__is(new_x + 1, new_y, 'ROADWAY')
                sub_3 = self.__is(new_x, new_y - 1, 'ROADWAY')
                sub_4 = self.__is(new_x, new_y + 1, 'ROADWAY')

                # Combined: there are upcoming on-ROADWAY movements from other three directions
                if (cond_1 and sub_1 and not counter_1) or \
                        (cond_2 and sub_2 and not counter_2) or \
                        (cond_3 and sub_3 and not counter_3) or \
                        (cond_4 and sub_4 and not counter_4):
                    path = list([np.array([cur_x, cur_y])]) + path
                    # Update the prediction window
                    self.__predict_window[pallet_id] = path
                    print(f"Pallet {pallet_id} waits to enter the roadway")

            elif self.__is(cur_x, cur_y, 'WORKSTATION') and not self.__is(new_x, new_y, 'WORKSTATION'):
                if not self.__is_empty(new_x, new_y):
                    path = list([np.array([cur_x, cur_y])]) + path
                    # Update the prediction window
                    self.__predict_window[pallet_id] = path

            # # Generic case
            # # TODO: check if there are other cases
            # else:
            #     if not self.__is_empty(new_x, new_y):
            #         path = list([np.array([cur_x, cur_y])]) + path
            #         # Update the prediction window
            #         self.__predict_window[pallet_id] = path

    def move_to_ws(self, pallet_id, ws_name):
        """
        Generate a route to a workstation for a pallet.

        :param pallet_id: string, ID of the pallet
        :param ws_name: string, alias of the Workstation
        """
        pallet = self.__pallets[pallet_id]
        queue = self.__workstations[ws_name].get_queue_path()

        self.generate_path(pallet_id, queue[-1][0], queue[-1][1])
        path = pallet.get_path()

        for slot in reversed(queue[:-1]):
            path = path + list([np.array(slot)])
        path = path + list([np.array(self.__workstations[ws_name].get_entry())])
        # TODO: check if the path should be put in the prediction window instead
        # Update new path and new target for the pallet
        pallet.set_path(path)
        pallet.set_target(ws_name)

    def generate_path(self, pallet_id, pos_x, pos_y):
        """
        Generate path consisting of slots from the current pallet's position to the desired one.
        Different algorithms/approaches can be defined within.

        :param pallet_id: string, ID of the pallet
        :param pos_x: integer, desired x-axis value
        :param pos_y: integer, desired y-axis value
        """
        pallet = self.__pallets[pallet_id]
        cur_x, cur_y = pallet.get_position()

        if SceneSetup.TRAFFIC_POLICY:
            path = list()
            if self.__workspace[cur_x, cur_y] // 10 * 10 == SceneSetup.WORKSTATION:
                path.append((cur_pos := self.__workstations[pallet.get_ws()].get_exit()))
                cur_x, cur_y = cur_pos[0], cur_pos[1]
                next_x, next_y = self.find_address(cur_x, cur_y)
                path_to_roadway = astar(self.__workspace.copy(), (cur_x, cur_y), (next_x, next_y),
                                        wall=SceneSetup.WALL)
                path = path + path_to_roadway[1:]
                cur_x, cur_y = path[-1]

            elif self.__workspace[cur_x, cur_y] // 10 * 10 in [SceneSetup.PARK,
                                                               SceneSetup.QUEUEING] and 2 <= cur_y <= 5:
                next_x, next_y = self.find_address(cur_x, cur_y)
                path_to_roadway = astar(self.__workspace.copy(), (cur_x, cur_y), (next_x, next_y),
                                        wall=SceneSetup.WALL)
                path = path + path_to_roadway[1:]
                cur_x, cur_y = path[-1]

            elif self.__is(cur_x, cur_y, 'QUEUEING') and (cur_y < 2 or cur_y > 5):
                next_x = cur_x - 1 if cur_y < 2 else cur_x + 1
                path.append(np.array([next_x, cur_y]))
                addr_x, addr_y = self.find_address(next_x, cur_y)
                path_to_roadway = astar(self.__workspace.copy(), (next_x, cur_y), (addr_x, addr_y),
                                        wall=SceneSetup.WALL)
                path = path + path_to_roadway[1:]
                cur_x, cur_y = path[-1]

            else:
                addr_x, addr_y = self.find_address(cur_x, cur_y)
                path_to_roadway = astar(self.__workspace.copy(), (cur_x, cur_y), (addr_x, addr_y),
                                        wall=SceneSetup.WALL)
                path = path + path_to_roadway[1:]
                cur_x, cur_y = path[-1]

            desired_x, desired_y = self.find_address(pos_x, pos_y)
            if cur_x == desired_x:
                # crossing only
                path.append(np.array([desired_x, desired_y]))

            elif (cur_x > desired_x and cur_y == desired_y == SceneSetup.roadway[1][1]) or \
                    (cur_x < desired_x and cur_y == desired_y == SceneSetup.roadway[0][1]):
                # Making a U turn
                opposite_y = SceneSetup.roadway[0][1] if cur_x > desired_x else SceneSetup.roadway[1][1]
                # 1st turn
                path.append(np.array([cur_x, opposite_y]))
                # straight path
                path_to_desired_address = astar(self.__workspace.copy(), (cur_x, opposite_y), (desired_x, opposite_y),
                                                wall=SceneSetup.WALL)
                path = path + path_to_desired_address[1:]
                # 2nd turn
                path.append(np.array([desired_x, desired_y]))

            elif (cur_x < desired_x and cur_y == desired_y == SceneSetup.roadway[1][1]) or \
                    (cur_x > desired_x and cur_y == desired_y == SceneSetup.roadway[0][1]):
                # straight path
                path_to_desired_address = astar(self.__workspace.copy(), (cur_x, cur_y), (desired_x, desired_y),
                                                wall=SceneSetup.WALL)
                path = path + path_to_desired_address[1:]

            elif (cur_x > desired_x and cur_y > desired_y) or (cur_x < desired_x and cur_y < desired_y):
                # reversed L turn
                # crossing
                path.append(np.array([cur_x, desired_y]))
                # straight path
                path_to_desired_address = astar(self.__workspace.copy(), (cur_x, desired_y), (desired_x, desired_y),
                                                wall=SceneSetup.WALL)
                path = path + path_to_desired_address[1:]

            elif (cur_x > desired_x and cur_y < desired_y) or (cur_x < desired_x and cur_y > desired_y):
                # L turn
                # straight path
                path_to_desired_address = astar(self.__workspace.copy(), (cur_x, cur_y), (desired_x, cur_y),
                                                wall=SceneSetup.WALL)
                path = path + path_to_desired_address[1:]
                # crossing
                path.append(np.array([desired_x, desired_y]))

            cur_x, cur_y = path[-1]
            path_to_goal = astar(self.__workspace.copy(), (cur_x, cur_y), (pos_x, pos_y),
                                 wall=SceneSetup.WALL)
            path = path + path_to_goal[1:]
            self.__pallets[pallet_id].set_path(path)

        # Casual go-to-goal algorithm
        else:
            path = astar(self.__workspace.copy(), (cur_x, cur_y), (pos_x, pos_y), wall=SceneSetup.WALL)
            # TODO: check if prediction window is needed
            self.__pallets[pallet_id].set_path(path[1:])

    def update(self):
        """

        """
        for pallet_id, pallet in self.__pallets.items():
            self.__predict_window[pallet_id] = pallet.get_path()
            self.__observe(pallet_id)
        for pallet_id, pallet in self.__pallets.items():
            pallet.set_path(self.__predict_window[pallet_id])
            self.__move_pallet(pallet_id)
        self.__sim_verify()

    def __sim_verify(self):
        """

        """
        occupied = dict()
        for pallet_id, pallet in self.__pallets.items():
            pos = pallet.get_position()
            for other_id, other in occupied.items():
                if not (pos - other).any():
                    import os
                    print(f"Collision at {pos.tolist()} between "
                          f"{pallet_id} moving from {self.__predict_window[pallet_id][0]} "
                          f"and {other_id} moving from {self.__predict_window[other_id][0]}")
                    os.system("pause")

            occupied[pallet_id] = pos

    def get_path(self, pallet_id):
        """

        :param pallet_id:
        :return:
        """
        return self.__pallets[pallet_id].get_path()

    def get_ws_size(self):
        """

        :return:
        """
        return self.__workspace.shape[0], self.__workspace.shape[1]

    def get_workspace(self):
        """

        :return:
        """
        return self.__workspace.tolist()

    def get_all_pallets(self):
        """

        :return:
        """
        res = dict()
        for pallet_id, pallet in self.__pallets.items():
            position = pallet.get_position()
            res[pallet_id] = dict({'x': int(position[0]), 'y': int(position[1])})
        return res

    def get_pallet(self, pallet_id):
        """

        :param pallet_id:
        :return:
        """
        position = self.__pallets[pallet_id].get_position()
        return dict({'x': int(position[0]), 'y': int(position[1])})

    def get_motion(self, pallet_id):
        """

        :param pallet_id:
        :return:
        """
        return self.__pallets[pallet_id].get_motion()

    @staticmethod
    def find_address(x, y):
        """

        :param x:
        :param y:
        :return:
        """
        if abs(SceneSetup.roadway[0][1] - y) > abs(SceneSetup.roadway[1][1] - y):
            pos_y = SceneSetup.roadway[1][1]
            if x < SceneSetup.roadway[1][0]:
                pos_x = SceneSetup.roadway[1][0]
            elif x > (max_x := SceneSetup.roadway[1][2] + SceneSetup.roadway[1][0]):
                pos_x = max_x
            else:
                pos_x = x
        else:
            pos_y = SceneSetup.roadway[0][1]
            if x < SceneSetup.roadway[0][0]:
                pos_x = SceneSetup.roadway[0][0]
            elif x > (max_x := SceneSetup.roadway[0][2] + SceneSetup.roadway[0][0]):
                pos_x = max_x
            else:
                pos_x = x
        return pos_x, pos_y

    @staticmethod
    def find_exit(x, y):
        """

        :param x:
        :param y:
        :return:
        """
        cur = np.array([x, y])
        for robot in SceneSetup.robot.values():
            if np.linalg.norm(cur - (exit_gate := robot['exit'])) < 3:
                return exit_gate

        return None

    def __add_workstations(self):
        for ws_name in SceneSetup.workstation_index.keys():
            self.__workstations[ws_name] = Workstation(ws_name)


if __name__ == '__main__':
    cont = Controller()
    cont.add_pallet("001", 0, 7)
    cont.generate_path("001", 12, 7)
    for _ in range(20):
        cont.update()
        print(cont.get_path("001"))
