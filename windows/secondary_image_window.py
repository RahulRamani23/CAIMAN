from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import cv2

class SecondaryImageWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        self.title = "Secondary Image Window"

        # get parameter window position & size
        param_window_x = self.controller.preview_window.x()
        param_window_y = self.controller.preview_window.y()
        param_window_width = self.controller.preview_window.width()

        # set position & size
        self.setGeometry(param_window_x + param_window_width + 32, param_window_y + 32, 10, 10)

        # create main widget
        self.main_widget = QWidget(self)
        self.main_widget.setMinimumSize(QSize(800, 800))
        self.resize(800, 800)

        # create main layout
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(20)

        bg_color = (20, 20, 20)
        fg_color = (150, 150, 150)
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(bg_color[0], bg_color[1], bg_color[2], 255))
        self.main_widget.setAutoFillBackground(True)
        self.main_widget.setPalette(palette)
        pg.setConfigOption('background', bg_color)
        pg.setConfigOption('foreground', fg_color)

        self.pg_widget = pg.GraphicsLayoutWidget()
        self.pg_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.pg_widget.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.main_layout.addWidget(self.pg_widget)

        self.image_viewbox = self.pg_widget.addViewBox(lockAspect=True, name='image', border=None, row=0, col=1,
                                                       invertY=True)
        self.image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.image_viewbox.setBackgroundColor((20, 20, 20))
        self.image = pg.ImageItem()
        self.cursor = None

        self.image_viewbox.addItem(self.image)

        self.slider_widget = QWidget()
        self.main_layout.addWidget(self.slider_widget)
        layout = QHBoxLayout(self.slider_widget)

        label = QLabel("Z: ")
        label.setStyleSheet("color: white;")
        layout.addWidget(label)

        self.z_slider = QSlider(Qt.Horizontal)
        self.z_slider.setRange(0, 0)
        self.z_slider.setValue(self.controller.secondary_z)
        self.z_slider.setMaximumWidth(50)
        self.z_slider.valueChanged.connect(self.set_z)
        layout.addWidget(self.z_slider)

        self.z_label = QLabel(str(self.controller.secondary_z))
        self.z_label.setStyleSheet("color: white;")
        layout.addWidget(self.z_label)
        layout.addStretch()

        self.pg_widget.hide()

    def update_image_plot(self, image):
        image = 255.0*image/self.controller.secondary_image_max
        image[image > 255] = 255

        if len(image.shape) < 3:
            image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        else:
            image = image.astype(np.uint8)

        self.image.setImage(image)

    def show_image(self):
        self.update_image_plot(self.controller.secondary_image[0, 0])
        self.pg_widget.show()
        self.z_slider.setRange(0, self.controller.secondary_image_frames - 1)

        self.show()

    def closeEvent(self, ce):
        self.controller.secondary_image = []
        self.controller.secondary_image_max = 1
        self.cursor = None

    def update_image(self):
        self.update_image_plot(self.controller.secondary_image[0, self.controller.secondary_z])

    def set_z(self, i):
        self.controller.secondary_z = int(i)
        self.z_label.setText(str(self.controller.secondary_z))
        self.update_image()

    def plot_cursor(self, x, y, height, width):
        y_scale = self.image.height() / height
        x_scale = self.image.width() / width

        # Scale the x and y position based of the height and width of image in preview window
        x = x * x_scale
        y = y * y_scale

        if not self.cursor:
            self.cursor = pg.PlotDataItem([1, 1], pen=pg.mkPen((200,50, 200), width=10))
            self.image_viewbox.addItem(self.cursor)

        self.cursor.setPos(x, y)

