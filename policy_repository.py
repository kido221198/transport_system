import numpy as np


class SceneSetup:
    """

    """
    TRAFFIC_POLICY = True
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
                         "YASKAWA": 10
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

    if TRAFFIC_POLICY:
        workstation = [[0, 0, 2, 2],  # pen1
                       [12, 0, 2, 2],  # pen2
                       [24, 0, 2, 2],  # KUKA
                       [36, 0, 2, 2],  # ABB1
                       [48, 0, 2, 2],  # OMRON1
                       [2, 6, 2, 2],  # pen3
                       [14, 6, 2, 2],  # pen4
                       [26, 6, 2, 2],  # UR
                       [38, 6, 2, 2],  # ABB2
                       [50, 6, 2, 2],  # OMRON2
                       [56, 2, 2, 4]]  # YASKAWA

        parking_slot = [[8, 2], [9, 2], [10, 2], [11, 2],
                        [20, 2], [21, 2], [22, 2], [23, 2],
                        [32, 2], [33, 2], [34, 2], [35, 2],
                        [44, 2], [45, 2], [46, 2], [47, 2],
                        [4, 5], [5, 5], [6, 5], [7, 5],
                        [16, 5], [17, 5], [18, 5], [19, 5],
                        [28, 5], [29, 5], [30, 5], [31, 5],
                        [40, 5], [41, 5], [42, 5], [43, 5]]

        queueing_slot = [[[3, 0], [3, 1], [3, 2], [4, 2], [5, 2], [6, 2], [7, 2]],  # pen1
                         [[15, 0], [15, 1], [15, 2], [16, 2], [17, 2], [18, 2], [19, 2]],  # pen2
                         [[27, 0], [27, 1], [27, 2], [28, 2], [29, 2], [30, 2], [31, 2]],  # KUKA
                         [[39, 0], [39, 1], [39, 2], [40, 2], [41, 2], [42, 2], [43, 2]],  # ABB1
                         [[51, 0], [51, 1], [51, 2], [52, 2], [53, 2], [54, 2]],  # OMRON1
                         [[0, 7], [0, 6], [0, 5], [0, 4]],  # pen3
                         [[12, 7], [12, 6], [12, 5], [11, 5], [10, 5], [9, 5], [8, 5]],  # pen4
                         [[24, 7], [24, 6], [24, 5], [23, 5], [22, 5], [21, 5], [20, 5]],  # UR
                         [[36, 7], [36, 6], [36, 5], [35, 5], [34, 5], [33, 5], [32, 5]],  # ABB2
                         [[48, 7], [48, 6], [48, 5], [47, 5], [46, 5], [45, 5], [44, 5]],  # OMRON2
                         [[54, 5], [53, 5], [52, 5]]]  # YASKAWA

        roadway = [[1, 3, 54, 1], [1, 4, 54, 1]]
        # roadway = [[2, 3, 41, 1], [2, 4, 41, 1]]

        robot = {
            'pen1': {'entry': np.array([1, 0]), 'exit': np.array([1, 1])},
            'pen2': {'entry': np.array([13, 0]), 'exit': np.array([12, 1])},
            'KUKA': {'entry': np.array([25, 0]), 'exit': np.array([24, 1])},
            'ABB1': {'entry': np.array([37, 0]), 'exit': np.array([36, 1])},
            'OMRON1': {'entry': np.array([49, 0]), 'exit': np.array([48, 1])},
            'pen3': {'entry': np.array([2, 7]), 'exit': np.array([3, 6])},
            'pen4': {'entry': np.array([14, 7]), 'exit': np.array([15, 6])},
            'UR': {'entry': np.array([26, 7]), 'exit': np.array([27, 6])},
            'ABB2': {'entry': np.array([38, 7]), 'exit': np.array([39, 6])},
            'OMRON2': {'entry': np.array([50, 7]), 'exit': np.array([51, 6])},
            'YASKAWA': {'entry': np.array([56, 5]), 'exit': np.array([56, 3])}
        }

    # Default configuration
    else:
        workstation = [[0, 0, 4, 2],  # pen1
                       [12, 0, 4, 2],  # pen2
                       [24, 0, 4, 2],  # KUKA
                       [36, 0, 4, 2],  # ABB1
                       [48, 0, 4, 2],  # OMRON1
                       [0, 6, 4, 2],  # pen3
                       [12, 6, 4, 2],  # pen4
                       [24, 6, 4, 2],  # UR
                       [36, 6, 4, 2],  # ABB2
                       [48, 6, 4, 2],  # OMRON2
                       [56, 2, 2, 4]]  # YASKAWA

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
        self.__workstation = None

    def move(self):
        """

        :return:
        """
        if len(self.__path) > 0:
            self.__position = self.__path.pop(0)

    def get_position(self):
        """

        :return:
        """
        return self.__position.copy()

    def get_path(self):
        """

        :return:
        """
        return self.__path.copy()

    def get_motion(self):
        """

        :return:
        """
        if len(self.__path) > 0:
            return self.__path[0][0] - self.__position[0], self.__path[0][1] - self.__position[1]
        else:
            return 0, 0

    def set_path(self, path):
        """

        :param path:
        :return:
        """
        self.__path = path

    def set_target(self, ws_name):
        """

        :param ws_name:
        :return:
        """
        self.__target = ws_name

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
