import numpy as np


class SceneSetup:
    """

    """
    HIERARCHY_POLICY = True
    num_pallet = 2
    ws_width, ws_height = 58, 8
    workspace = np.zeros((ws_width, ws_height))

    workstation_index = {"pen1": 0,
                         "pen2": 1,
                         "KUKA": 2,
                         "ABB1": 3,
                         "OMRON1": 4,
                         "pen3": 5,
                         "pen4": 6,
                         "UR": 7,
                         "ABB2": 8,
                         "OMRON2": 9,
                         # "YASKAWA": 10
                         }
    wall = [[4, 0, 8, 2],
            [16, 0, 8, 2],
            [28, 0, 8, 2],
            [40, 0, 8, 2],
            [52, 0, 6, 2],
            [4, 6, 8, 2],
            [16, 6, 8, 2],
            [28, 6, 8, 2],
            [40, 6, 8, 2],
            [52, 6, 6, 2]]

    workstation = [[0, 0, 2, 2],  # pen1
                   [12, 0, 2, 2],  # pen2
                   [24, 0, 1, 2],  # KUKA
                   [36, 0, 1, 2],  # ABB1
                   [48, 0, 1, 2],  # OMRON1
                   [2, 6, 2, 2],  # pen3
                   [14, 6, 2, 2],  # pen4
                   [27, 6, 1, 2],  # UR
                   [39, 6, 1, 2],  # ABB2
                   [51, 6, 1, 2]]  # OMRON2

    parking_slot = []

    queueing_slot = [[[2, 0], [3, 0], [3, 1], [2, 1]],  # pen1
                     [[14, 0], [15, 0], [15, 1], [14, 1]],  # pen2
                     [[25, 0], [26, 0], [27, 0], [27, 1], [26, 1], [25, 1]],  # KUKA
                     [[37, 0], [38, 0], [39, 0], [39, 1], [38, 1], [37, 1]],  # ABB1
                     [[49, 0], [50, 0], [51, 0], [51, 1], [50, 1], [49, 1]],  # OMRON1
                     [[1, 7], [0, 7], [0, 6], [1, 6]],  # pen3
                     [[13, 7], [12, 7], [12, 6], [13, 6]],  # pen4
                     [[26, 7], [25, 7], [24, 7], [24, 6], [25, 6], [26, 6]],  # UR
                     [[38, 7], [37, 7], [36, 7], [36, 6], [37, 6], [38, 6]],  # ABB2
                     [[50, 7], [49, 7], [48, 7], [48, 6], [49, 6], [50, 6]]]   # OMRON2

    roadway = [[2, 3, 41, 1], [2, 4, 41, 1]]

    robot = {
        'pen1': {'entry': np.array([1, 0]), 'exit': np.array([0, 1])},
        'pen2': {'entry': np.array([13, 0]), 'exit': np.array([12, 1])},
        'KUKA': {'entry': np.array([24, 0]), 'exit': np.array([24, 1])},
        'ABB1': {'entry': np.array([36, 0]), 'exit': np.array([36, 1])},
        'OMRON1': {'entry': np.array([48, 0]), 'exit': np.array([48, 1])},
        'pen3': {'entry': np.array([2, 7]), 'exit': np.array([3, 6])},
        'pen4': {'entry': np.array([14, 7]), 'exit': np.array([15, 6])},
        'UR': {'entry': np.array([27, 7]), 'exit': np.array([27, 6])},
        'ABB2': {'entry': np.array([39, 7]), 'exit': np.array([39, 6])},
        'OMRON2': {'entry': np.array([51, 7]), 'exit': np.array([51, 6])}
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
