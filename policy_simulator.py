import sys
from hierarchy_endpoint import Controller
# from policy_endpoint import Controller
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def adjust_scene(sim):
    # [init_x, init_y, des_x, des_y, des_ws]
    pallets = {'001': [0, 0, 27, 0, "pen1"],
               '002': [12, 0, 27, 1, "OMRON1"],
               '003': [24, 0, 39, 1, "ABB2"],
               '004': [36, 0, 39, 0, "UR"],
               '005': [44, 2, 42, 5, "OMRON1"],
               '006': [8, 2, 41, 5, "KUKA"],
               '007': [9, 2, 36, 7, "ABB2"],
               '008': [10, 2, 36, 6, "OMRON1"],
               '009': [11, 2, 15, 0, "pen2"],
               '010': [20, 2, 15, 1, "pen2"],
               '011': [21, 2, 3, 1, "OMRON1"],
               '012': [22, 2, 3, 0, "ABB1"],
               '013': [23, 2, 0, 6, "KUKA"],
               '014': [32, 2, 0, 7, "ABB2"],
               '015': [33, 2, 12, 7, "pen3"],
               '016': [34, 2, 12, 6, "OMRON2"],
               '017': [35, 2, 24, 7, "UR"],
               '018': [4, 5, 24, 6, "ABB2"],
               '019': [5, 5, 27, 0, "UR"],
               '020': [6, 5, 27, 1, "KUKA"],
               '021': [7, 5, 39, 1, "pen4"],
               '022': [16, 5, 39, 0, "ABB2"],
               '023': [17, 5, 42, 5, "KUKA"],
               '024': [18, 5, 41, 5, "UR"],
               '025': [19, 5, 36, 7, "ABB1"],
               '026': [28, 5, 36, 6, "UR"],
               '027': [29, 5, 15, 0, "UR"],
               '028': [30, 5, 15, 1, "ABB2"],
               '029': [31, 5, 3, 1, "KUKA"],
               '030': [2, 7, 3, 0, "ABB2"],
               '031': [14, 7, 0, 6, "OMRON2"],
               '032': [26, 7, 0, 7, "pen2"],
               '033': [38, 7, 12, 7, "OMRON2"],
               '034': [3, 0, 12, 6, "pen1"],
               '035': [0, 7, 24, 7, "pen2"]
               }

    for pallet_id, pallet in pallets.items():
        sim._Simulator__add_pallet(pallet[0], pallet[1], update_visualization=False)
        # sim._Simulator__move_pallet(pallet_id, pallet[2], pallet[3])
        # sim._Simulator__move_to_ws(pallet_id, pallet[4])


class Simulator(QWidget):
    def __init__(self, parent=None):
        """

        """
        super().__init__()
        self.controller = Controller()
        self.__center()
        self.__initial_plot()
        self.__pallets = dict()

        # Timer
        self.__interval = 200
        self.__timer = QTimer()
        self.__time = 0
        self.__timer.timeout.connect(self.__timer_handler)
        self.__animate_step = 10
        self.__animate_interval = int(self.__interval / self.__animate_step)
        self.__buffer_pallets = None

        # Initialize Scenario
        adjust_scene(self)

    def __center(self):
        """
        Maximize and fix window.
        """
        frameGm = self.frameGeometry()
        # screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        screen = app.primaryScreen()
        # centerPoint = QApplication.desktop().screenGeometry(screen).center()
        centerPoint = screen.geometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
        rect = screen.availableGeometry()
        # rect =QApplication.desktop().screenGeometry(screen)
        self.window_width = rect.width()
        self.window_height = rect.height()
        self.setWindowState(Qt.WindowMaximized)

        self.setFixedWidth(self.window_width)
        self.setFixedHeight(self.window_height)
        print("Window size:", self.window_width, self.window_height)

    def __initial_plot(self):
        """
        Initialize widgets.
        """
        self.__button_font_sz = 18

        # Margins
        self.margins = [0.025, 0.025, 0.025, 0.025]  # top, bottom, left, right
        self.top_margin = round(self.margins[0] * self.window_height)
        self.bottom_margin = round(self.margins[1] * self.window_height)
        self.left_margin = round(self.margins[2] * self.window_width)
        self.right_margin = round(self.margins[3] * self.window_width)
        self.inner_height = self.window_height - self.top_margin - self.bottom_margin
        self.inner_width = self.window_width - self.left_margin - self.right_margin

        # Grid
        self.rows = [0., 0.2, 0.3, 0.4, 0.5, 0.6]
        self.cols = [0., 0.8, 0.9]
        self.minor_row_space = self.minor_col_space = 0.01
        self.major_row_space = self.major_col_space = 0.02

        # Logo Geometry
        self.logo_height = round(self.inner_width * 0.15)
        self.logo_width = round(self.inner_height * 0.4)
        self.logo_pose = round((self.window_width - self.logo_width) / 2)
        self.logo = QLabel("FAST-Lab.", self)
        self.logo.setFont(QFont('Arial', 62))
        self.logo.setStyleSheet("QLabel { color : #441587; }")
        self.logo.setGeometry(self.logo_pose, round(self.rows[0] * self.inner_height),
                              self.logo_width, self.logo_height)

        # Add Pallet button
        self.add_button = QPushButton("Add Pallet", self)
        self.add_button.setFont(QFont('Arial', self.__button_font_sz))
        self.add_button.setGeometry(round(self.cols[1] * self.inner_width) + self.left_margin,
                                    round(self.rows[1] * self.inner_height) + self.top_margin,
                                    round((1 - self.cols[1] - self.minor_col_space) * self.inner_width),
                                    round((self.rows[2] - self.rows[1] - self.minor_row_space) * self.inner_height))
        self.add_button.pressed.connect(self.__add_pallet)

        # Textbox for X
        self.pos_x = QLineEdit(self)
        self.pos_x.setAlignment(Qt.AlignCenter)
        self.pos_x.setPlaceholderText("X")
        self.pos_x.setFont(QFont('Arial', self.__button_font_sz))
        self.pos_x.setGeometry(round(self.cols[1] * self.inner_width) + self.left_margin,
                               round(self.rows[2] * self.inner_height) + self.top_margin,
                               round((self.cols[2] - self.cols[1] - self.minor_col_space) * self.inner_width),
                               round((self.rows[3] - self.rows[2] - self.minor_row_space) * self.inner_height))

        # Textbox for Y
        self.pos_y = QLineEdit(self)
        self.pos_y.setAlignment(Qt.AlignCenter)
        self.pos_y.setPlaceholderText("Y")
        self.pos_y.setFont(QFont('Arial', self.__button_font_sz))
        self.pos_y.setGeometry(round(self.cols[2] * self.inner_width) + self.left_margin,
                               round(self.rows[2] * self.inner_height) + self.top_margin,
                               round((1 - self.cols[2] - self.minor_col_space) * self.inner_width),
                               round((self.rows[3] - self.rows[2] - self.minor_row_space) * self.inner_height))

        # Textbox for Pallet ID
        self.type_box = QLineEdit(self)
        self.type_box.setAlignment(Qt.AlignCenter)
        self.type_box.setPlaceholderText("Pallet ID")
        self.type_box.setFont(QFont('Arial', self.__button_font_sz))
        self.type_box.setGeometry(round(self.cols[1] * self.inner_width) + self.left_margin,
                                  round(self.rows[3] * self.inner_height) + self.top_margin,
                                  round((self.cols[2] - self.cols[1] - self.minor_col_space) * self.inner_width),
                                  round((self.rows[4] - self.rows[3] - self.minor_row_space) * self.inner_height))

        # Generate new path
        self.move_button = QPushButton(self)
        self.move_button.setText("Move")
        self.move_button.setFont(QFont('Arial', self.__button_font_sz))
        self.move_button.setGeometry(round(self.cols[2] * self.inner_width) + self.left_margin,
                                     round(self.rows[3] * self.inner_height) + self.top_margin,
                                     round((1 - self.cols[2] - self.minor_col_space) * self.inner_width),
                                     round((self.rows[4] - self.rows[3] - self.minor_row_space) * self.inner_height))
        self.move_button.pressed.connect(self.__move_pallet)

        # Reset button
        self.reset_button = QPushButton(self)
        self.reset_button.setText("Reset")
        self.reset_button.setFont(QFont('Arial', self.__button_font_sz))
        self.reset_button.setGeometry(round(self.cols[1] * self.inner_width) + self.left_margin,
                                      round(self.rows[4] * self.inner_height) + self.top_margin,
                                      round((self.cols[2] - self.cols[1] - self.minor_col_space) * self.inner_width),
                                      round((self.rows[5] - self.rows[4] - self.minor_row_space) * self.inner_height))
        self.reset_button.pressed.connect(self.__reset)

        # Pause button
        self.pause_button = QPushButton(self)
        self.pause_button.setText("Start")
        self.pause_button.setFont(QFont('Arial', self.__button_font_sz))
        self.pause_button.setGeometry(round(self.cols[2] * self.inner_width) + self.left_margin,
                                      round(self.rows[4] * self.inner_height) + self.top_margin,
                                      round((1 - self.cols[2] - self.minor_col_space) * self.inner_width),
                                      round((self.rows[5] - self.rows[4] - self.minor_row_space) * self.inner_height))
        self.pause_button.pressed.connect(self.__pause)

        # Clock display
        self.clock = QLabel(self)
        self.clock.setText(f"Time: {0:>6.2f}s")
        self.clock.setFont(QFont('Arial', 12))
        self.clock.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.clock.setGeometry(round(self.cols[1] * self.inner_width) + self.left_margin,
                               round(self.rows[5] * self.inner_height) + self.top_margin,
                               round((1 - self.cols[1] - self.minor_col_space) * self.inner_width),
                               round((1 - self.rows[5]) * self.inner_height))

        # Status display
        self.status = QLabel(self)
        self.status.setText("Initializing..")
        self.status.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.status.setFont(QFont('Arial', 12))
        self.status.setGeometry(round(self.cols[0] * self.inner_width) + self.left_margin,
                                round(self.rows[5] * self.inner_height) + self.top_margin,
                                round((self.cols[1] - self.major_col_space) * self.inner_width),
                                round((1 - self.rows[5]) * self.inner_height))

        # Visualization area
        self.visualization = QGraphicsView(self)
        self.visualization.setGeometry(round(self.cols[0] * self.inner_width) + self.left_margin,
                                       round(self.rows[1] * self.inner_height) + self.top_margin,
                                       round((self.cols[1] - self.major_col_space) * self.inner_width),
                                       round((self.rows[5] - self.rows[1] - self.minor_row_space) * self.inner_height))
        self.white_board = QGraphicsScene(self.visualization)
        self.visualization.setStyleSheet("background: white")
        self.visualization.setScene(self.white_board)
        self.__initialize_visualization()
        self.show()

    def __initialize_visualization(self):
        """
        Initialize local visualization
        """
        self.__coordinate_font_sz = 6

        self.__pallet_ratio = 0.6
        self.__padding = (1 - self.__pallet_ratio) / 2
        width, height = self.controller.get_ws_size()
        # width2, height2 = width // 2, height // 2
        self.step = (step := int(min((self.visualization.width() - 1) // width,
                                     (self.visualization.height() - 1) // height)))
        wb_w, wb_h = step * width, step * height
        self.white_board.setSceneRect(0, 0, wb_w, wb_h)
        workspace = self.controller.get_workspace()
        pen = QPen(Qt.lightGray)
        pen.setWidth(1)

        for y in range(height):
            for x in range(width):
                if workspace[x][y] // 10 == 2:
                    self.white_board.addRect(step * x, step * y, step, step,
                                             QPen(QColor(151, 117, 198)), QBrush(QColor(151, 117, 198)))
                    if x % 2 == y % 2 == 0:
                        text = self.white_board.addText(f"{x * 2}, {y * 2}", QFont('Arial', self.__coordinate_font_sz))
                        text.setPos(step * x, step * y)

                elif workspace[x][y] // 10 == 0:
                    self.white_board.addRect(step * x, step * y, step, step,
                                             pen, QBrush(Qt.transparent))
                elif workspace[x][y] // 10 == 3:
                    self.white_board.addRect(step * x, step * y, step, step,
                                             pen, QBrush(QColor(244, 176, 132)))
                elif workspace[x][y] // 10 == 4:
                    self.white_board.addRect(step * x, step * y, step, step,
                                             pen, QBrush(QColor(226, 239, 218)))
                elif workspace[x][y] // 10 == 5:
                    self.white_board.addRect(step * x, step * y, step, step,
                                             pen, QBrush(QColor(242, 242, 242)))

                if workspace[x][y] // 10 in [0, 3, 4, 5] and x % 4 == y % 2 == 0:
                    text = self.white_board.addText(f"{x}, {y}", QFont('Arial', self.__coordinate_font_sz))
                    text.setPos(step * x, step * y)

    def __update_visualization(self):
        """
        Update visualization
        """
        prev_pallets = self.__buffer_pallets
        pallets = self.controller.get_all_pallets()
        step = self.__time % self.__interval / self.__animate_interval
        step = self.__animate_step + 0 if step == 0 else step
        for pallet_id, pallet in pallets.items():
            sz = int(self.step * self.__pallet_ratio)
            self.__pallets[pallet_id].setRect(self.step * (prev_pallets[pallet_id]['x'] * (1 - step / self.__animate_step) + pallet['x'] * step / self.__animate_step + self.__padding),
                                              self.step * (prev_pallets[pallet_id]['y'] * (1 - step / self.__animate_step) + pallet['y'] * step / self.__animate_step + self.__padding),
                                              sz, sz)

    def __add_pallet(self, x=None, y=None, update_visualization=True):
        """
        Add new pallet with automatic ID indexing
        """
        if x is not None and y is not None:
            pallet_id = self.controller.add_pallet(x, y)
        else:
            pallet_id = self.controller.add_pallet()
        pos = self.controller.get_pallet(pallet_id)
        pallet = self.white_board.addRect(self.step * pos['x'] + int(self.step * self.__padding),
                                          self.step * pos['y'] + int(self.step * self.__padding),
                                          int(self.step * self.__pallet_ratio), int(self.step * self.__pallet_ratio),
                                          QPen(Qt.black), QBrush(QColor(68, 21, 135)))
        self.__pallets[pallet_id] = pallet
        if update_visualization:
            # print("Visualization of adding new pallet..")
            self.__update_visualization()
        print(f"Added new pallet {pallet_id}.")

    def __move_pallet(self, pallet_id=None, x=None, y=None):
        """
        Make new order on moving specific pallet
        """
        if x is None or y is None or pallet_id is None:
            x = int(self.pos_x.text())
            y = int(self.pos_y.text())
            pallet_id = self.type_box.text().zfill(3)

        self.controller.generate_path(pallet_id, x, y)
        print(f"Generated path for pallet {pallet_id} moving to slot ({x}, {y}).")

    def __move_to_ws(self, pallet_id, ws_name):
        """

        :param pallet_id:
        :param ws_name:
        """
        self.controller.move_to_ws(pallet_id, ws_name)
        print(f"Generate path for pallet {pallet_id} moving to Workstation {ws_name}.")

    def __show_time(self):
        self.clock.setText(f"Time: {self.__time / 1000:>6.2f}s")

    def __pause(self):
        """

        """
        if self.pause_button.text() == "Pause":
            self.__end_timer()
        else:
            self.__start_timer()

    def __reset(self):
        """

        :return:
        """
        self.__time = 0.
        self.__end_timer()
        self.__show_time()
        self.pause_button.setText("Start")
        del self.controller
        self.controller = Controller()
        for pallet in self.__pallets.values():
            self.white_board.removeItem(pallet)
        self.__pallets = dict()
        self.__update_visualization()

    def __start_timer(self):
        """

        """
        self.__timer.start(self.__animate_interval)
        self.pause_button.setText("Pause")
        print("Simulation resumed.")

    def __end_timer(self):
        """

        """
        self.__timer.stop()
        self.pause_button.setText("Resume")
        print("Simulation paused.")

    def __timer_handler(self):
        """

        """
        if self.__time == 0:
            self.__buffer_pallets = self.controller.get_all_pallets()
        if self.__time % self.__interval == 0:
            self.__buffer_pallets = self.controller.get_all_pallets()
            self.controller.update()

        prev_second = self.__time // 1000
        self.__time += self.__animate_interval
        self.__show_time()
        print(f'Simulating t = {self.__time // 1000:>4}s ..') if self.__time // 1000 > prev_second else None

        self.__update_visualization()
        self.__timer.start(self.__animate_interval)

    def closeEvent(self, event):
        """

        """
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    print('Screen: %s' % screen.name())
    size = screen.size()
    print('Size: %d x %d' % (size.width(), size.height()))
    rect = screen.availableGeometry()
    print('Available: %d x %d' % (rect.width(), rect.height()))
    mainform = Simulator()
    app.exec_()
