from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot
from controller.regressor_analysis import *

import os
import numpy as np

try:
    import suite2p

    suite2p_available = True
except:
    suite2p_available = False

class RegressionPlotWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        self.title = "Regression Analysis"


        self.top = 32
        self.width = 400
        self.left = self.controller.preview_window.x() + self.controller.preview_window.width() + 32
        self.height = 600

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # create main widget & layout
        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(0)

        # set main widget to be the central widget
        self.setCentralWidget(self.main_widget)

        self.show()

        self.top_widget = QWidget()
        self.top_layout = QHBoxLayout(self.top_widget)
        self.main_layout.addWidget(self.top_widget)

        left_plot_groupbox = QGroupBox("Regressor Correlations")
        self.top_layout.addWidget(left_plot_groupbox)
        left_plot_layout = QVBoxLayout(left_plot_groupbox)

        self.left_plot_canvas = PlotCanvas(self)
        self.left_plot_canvas.setFixedHeight(600)
        self.left_plot_canvas.setFixedWidth(300)
        self.controller.dataset_editing_window.close() ## FIGURE OUT WHY I NEED THIS ###########
        left_plot_layout.addWidget(self.left_plot_canvas)
        left_plot_layout.setAlignment(self.left_plot_canvas, Qt.AlignCenter)

        widget = QWidget()
        left_plot_layout.addWidget(widget)
        layout = QHBoxLayout(widget)

        right_plot_groupbox = QGroupBox("Multi-Regressor Analysis")
        self.top_layout.addWidget(right_plot_groupbox)
        right_plot_layout = QVBoxLayout(right_plot_groupbox)

        self.right_plot_canvas = PlotCanvas(self)
        self.right_plot_canvas.setFixedHeight(600)
        self.right_plot_canvas.setFixedWidth(300)
        right_plot_layout.addWidget(self.right_plot_canvas)
        right_plot_layout.setAlignment(self.right_plot_canvas, Qt.AlignCenter)

        widget = QWidget()
        right_plot_layout.addWidget(widget)
        layout = QHBoxLayout(widget)

    def closeEvent(self, ce):
        if not self.controller.closing:
            ce.ignore()
        else:
            ce.accept()

    def update_plots(self, selected_regressors=None):
        if self.controller.correlation_results is not None:
            if selected_regressors is None:
                selected_regressors = self.controller.regressors

            self.left_plot_canvas.plot_correlation(self.controller.correlation_results, self.controller.regressors, self.controller.spatial_footprints, self.controller.temporal_footprints, self.controller.calcium_video, self.controller.regressor_mean_images, self.controller.n_frames, self.controller.roi_centers, self.controller.regression_z, self.controller.max_p, self.controller.regressor_index)
            self.right_plot_canvas.plot_multilinear_regression(self.controller.regression_coefficients, self.controller.regression_intercepts, self.controller.regression_scores, selected_regressors, self.controller.spatial_footprints, self.controller.temporal_footprints, self.controller.calcium_video, self.controller.regressor_mean_images, self.controller.n_frames, self.controller.roi_centers, self.controller.regression_z)
        else:
            self.left_plot_canvas.clear_plot()
            self.right_plot_canvas.clear_plot()


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, dpi=30):
        self.fig = matplotlib.pyplot.figure(0, dpi=dpi)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        self.setStyleSheet("background-color:rgba(0, 0, 0, 0);")

        self.fig.patch.set_alpha(0)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def clear_plot(self):
        self.fig.clear()
        self.draw()

    def plot_correlation(self, correlation_results, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, z, max_p, regressor_index):
        self.fig.clear()

        plot_correlation(correlation_results, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, z, max_p, regressor_index, fig=self.fig)

        self.draw()

    def plot_multilinear_regression(self, regression_coefficients, regression_intercepts, regression_scores, selected_regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, z):
        self.fig.clear()

        plot_multilinear_regression(regression_coefficients, regression_intercepts, regression_scores, selected_regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, z, fig=self.fig)

        self.draw()