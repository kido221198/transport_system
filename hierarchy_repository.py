import numpy as np


class SceneSetup:
    """

    """
    HIERARCHY_POLICY = True
    num_pallet = 2
    ws_width, ws_height = 60, 8
    workspace = np.zeros((ws_width, ws_height))

    workstation_index = {"Workstation 01": 0,
                         "Workstation 02": 1,
                         "Workstation 03": 2,
                         "Workstation 04": 3,
                         "Workstation 05": 4,
                         "Workstation 06": 5,
                         "Workstation 07": 6,
                         "Workstation 08": 7,
                         "Workstation 09": 8,
                         "Workstation 10": 9,
                         "Workstation 11": 10
                         }
    wall = [[6, 0, 6, 2],
            [18, 0, 6, 2],
            [30, 0, 6, 2],
            [42, 0, 6, 2],
            [54, 0, 6, 2],
            [6, 6, 6, 2],
            [18, 6, 6, 2],
            [30, 6, 6, 2],
            [42, 6, 6, 2],
            [54, 6, 6, 2]]

    workstation = [[0, 0, 2, 2],  # pen1
                   [12, 0, 2, 2],  # pen2
                   [24, 0, 2, 2],  # KUKA
                   [36, 0, 2, 2],  # ABB1
                   [48, 0, 2, 2],  # OMRON1
                   [4, 6, 2, 2],  # pen3
                   [16, 6, 2, 2],  # pen4
                   [28, 6, 2, 2],  # UR
                   [40, 6, 2, 2],  # ABB2
                   [52, 6, 2, 2],  # OMRON2
                   [58, 2, 2, 4]]  # YASKAWA

    parking_slot = []

    queueing_slot = [[[2, 0], [3, 0], [4, 0], [5, 0], [5, 1], [4, 1], [3, 1], [2, 1]],  # pen1
                     [[14, 0], [15, 0], [16, 0], [17, 0], [17, 1], [16, 1], [15, 1], [14, 1]],  # pen2
                     [[26, 0], [27, 0], [28, 0], [29, 0], [29, 1], [28, 1], [27, 1], [26, 1]],  # KUKA
                     [[38, 0], [39, 0], [40, 0], [41, 0], [41, 1], [40, 1], [39, 1], [38, 1]],  # ABB1
                     [[50, 0], [51, 0], [52, 0], [53, 0], [53, 1], [52, 1], [51, 1], [50, 1]],  # OMRON1
                     [[3, 7], [2, 7], [1, 7], [0, 7], [0, 6], [1, 6], [2, 6], [3, 6]],  # pen3
                     [[15, 7], [14, 7], [13, 7], [12, 7], [12, 6], [13, 6], [14, 6], [15, 6]],  # pen4
                     [[27, 7], [26, 7], [25, 7], [24, 7], [24, 6], [25, 6], [26, 6], [27, 6]],  # UR
                     [[39, 7], [38, 7], [37, 7], [36, 7], [36, 6], [37, 6], [38, 6], [39, 6]],  # ABB2
                     [[51, 7], [50, 7], [49, 7], [48, 7], [48, 6], [49, 6], [50, 6], [51, 6]],  # OMRON2
                     []]

    roadway = [[2, 3, 41, 1], [2, 4, 41, 1]]

    robot = {
        'Workstation 01': {'entry': np.array([1, 0]), 'exit': np.array([0, 1])},
        'Workstation 02': {'entry': np.array([13, 0]), 'exit': np.array([12, 1])},
        'Workstation 03': {'entry': np.array([25, 0]), 'exit': np.array([24, 1])},
        'Workstation 04': {'entry': np.array([37, 0]), 'exit': np.array([36, 1])},
        'Workstation 05': {'entry': np.array([49, 0]), 'exit': np.array([48, 1])},
        'Workstation 06': {'entry': np.array([4, 7]), 'exit': np.array([5, 6])},
        'Workstation 07': {'entry': np.array([16, 7]), 'exit': np.array([17, 6])},
        'Workstation 08': {'entry': np.array([28, 7]), 'exit': np.array([29, 6])},
        'Workstation 09': {'entry': np.array([40, 7]), 'exit': np.array([41, 6])},
        'Workstation 10': {'entry': np.array([52, 7]), 'exit': np.array([53, 6])},
        'Workstation 11': {'entry': np.array([58, 5]), 'exit': np.array([58, 2])}
    }

    EMPTY = 0
    OCCUPIED = 1

    WALL = 10
    WORKSTATION = 20
    QUEUEING = 30
    PARK = 40
    ROADWAY = 50

    DEFAULT_FEED_X = 0
    DEFAULT_FEED_Y = 3


class Workstation:
    """

    """
    OFFLINE = 0
    STARVE = 1
    BUSY = 2

    def __init__(self, name):
        """

        :param name:
        """
        self.__name = name
        self.__index = SceneSetup.workstation_index[name]
        self.__state = self.STARVE
        self.__queue_position = SceneSetup.queueing_slot[self.__index]
        self.__queue = [None] * len(self.__queue_position)
        self.__entry = SceneSetup.robot[name]['entry']
        self.__exit = SceneSetup.robot[name]['exit']
        self.__area = SceneSetup.workstation[self.__index]

    def set_state(self, state):
        """

        :param state:
        """
        self.__state = state

    def get_state(self):
        """

        :return:
        """
        return self.__state * 1

    def get_queue(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """
        for index, slot in enumerate(self.__queue_position):
            if slot[0] == x and slot[1] == y:
                return index
        return -1

    def get_queue_path(self):
        """

        :return:
        """
        return self.__queue_position[:]

    def get_exit(self):
        """

        :return:
        """
        return self.__exit.copy()

    def get_entry(self):
        """

        :return:
        """
        return self.__entry.copy()

    def check_inside(self, pos_x, pos_y):
        """

        :param pos_x:
        :param pos_y:
        :return:
        """
        x, y, w, h = self.__area
        # print(x, pos_x, x + w, y, pos_y, y + h)
        if x <= pos_x < x + w and y <= pos_y < y + h:
            return True
        else:
            return False


class Pallet:
    def __init__(self, pallet_id, position):
        """

        :param pallet_id:
        :param position:
        """
        self.__pallet_id = pallet_id
        self.__carry = list()
        self.__position = position
        self.__path = list()
        self.__target = None
        self.__goal = None
        self.__workstation = None
        self.__history = [position]
        self.__waited = 0

    def move(self):
        """

        :return:
        """
        if len(self.__path) > 1:
            if self.__position == self.__path[1]:
                self.__waited += 1
            else:
                self.__waited = 0
            self.__path.pop(0)
            self.__position = self.__path[0]
        self.__history.append(self.__position)

    def get_history(self):
        return self.__history[:]

    def get_position(self):
        """

        :return:
        """
        return self.__position + 0

    def get_path(self):
        """

        :return:
        """
        return self.__path[:]

    def set_path(self, path):
        """

        :param path:
        :return:
        """
        self.__path = path[:]

    def set_target(self, ws_name):
        """

        :param ws_name:
        :return:
        """
        self.__target = ws_name

    def set_goal(self, node):
        """

        :param node:
        :return:
        """
        self.__goal = node + 0

    def get_goal(self):
        """

        :param node:
        :return:
        """
        return self.__goal + 0 if self.__goal is not None else None

    def get_target(self):
        """

        :return:
        """
        return self.__target[:] if self.__target is not None else None

    def set_ws(self, ws_name):
        """

        :param ws_name:
        :return:
        """
        self.__workstation = ws_name

    def get_ws(self):
        """

        :return:
        """
        return self.__workstation[:] if self.__workstation is not None else None

    def get_waited(self):
        return self.__waited + 0
