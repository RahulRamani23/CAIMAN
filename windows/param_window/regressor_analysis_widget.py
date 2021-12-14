from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QComboBox, QSlider, QLineEdit, \
    QScrollArea, QFileDialog, QCheckBox

from controller.regressor_analysis import save_data
from windows.param_window.param_widget import ParamWidget
from windows.param_window.param_window import *

subheading_font = QFont()
subheading_font.setBold(True)
subheading_font.setPointSize(13)

class RegressorAnalysisWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Regresor Analysis Parameters")
        self.controller = controller

        self.button_layout = self.initalize_horizontal_layout()

        self.load_calcium_video_button = QPushButton("Load Calcium Video(s)...")
        self.load_calcium_video_button.setFixedWidth(180)
        self.load_calcium_video_button.clicked.connect(self.load_calcium_video)
        self.button_layout.addWidget(self.load_calcium_video_button)

        self.load_roi_data_button = QPushButton("Load ROI Data File(s)...")
        self.load_roi_data_button.setFixedWidth(180)
        self.load_roi_data_button.clicked.connect(self.load_roi_data)
        self.load_roi_data_button.setEnabled(False)
        self.button_layout.addWidget(self.load_roi_data_button)

        self.load_bouts_button = QPushButton("Load Bout File(s)...")
        self.load_bouts_button.setFixedWidth(150)
        self.load_bouts_button.clicked.connect(self.load_bouts)
        self.load_bouts_button.setEnabled(False)
        self.button_layout.addWidget(self.load_bouts_button)

        self.load_frame_timestamps_button = QPushButton("Load Timestamp File(s)...")
        self.load_frame_timestamps_button.setFixedWidth(190)
        self.load_frame_timestamps_button.clicked.connect(self.load_frame_timestamps)
        self.load_frame_timestamps_button.setEnabled(False)
        self.button_layout.addWidget(self.load_frame_timestamps_button)
        self.button_layout.addStretch()

        self.video_param_widget = QWidget()
        self.video_param_layout = QVBoxLayout(self.video_param_widget)
        self.main_layout.addWidget(self.video_param_widget)

        self.video_param_layout.addWidget(QLabel("Video Parameters").setFont(subheading_font))

        widget = QWidget()
        self.video_param_layout.addWidget(widget)
        layout = QHBoxLayout(widget)
        layout.setSpacing(15)

        self.video_combobox = QComboBox()
        self.video_combobox.currentIndexChanged.connect(self.set_video)
        layout.addWidget(self.video_combobox)

        label = QLabel("Z: ")
        layout.addWidget(label)

        self.z_slider = QSlider(Qt.Horizontal)
        self.z_slider.setRange(0, 0)
        self.z_slider.setValue(self.controller.regression_z)
        self.z_slider.setMaximumWidth(50)
        self.z_slider.valueChanged.connect(self.set_z)
        layout.addWidget(self.z_slider)

        self.z_label = QLabel(str(self.controller.regression_z))
        self.z_label.setMaximumWidth(10)
        layout.addWidget(self.z_label)

        self.remove_video_button = QPushButton("Remove Video")
        self.remove_video_button.clicked.connect(self.remove_selected_video)
        self.remove_video_button.setFixedWidth(120)
        self.remove_video_button.setEnabled(False)
        layout.addWidget(self.remove_video_button)

        widget = QWidget()
        self.video_param_layout.addWidget(widget)
        layout = QHBoxLayout(widget)

        label = QLabel("Frame Offset: ")
        layout.addWidget(label)

        self.tail_calcium_offset_slider = QSlider(Qt.Horizontal)
        self.tail_calcium_offset_slider.setRange(0, 10)
        self.tail_calcium_offset_slider.setValue(self.controller.tail_calcium_offset)
        self.tail_calcium_offset_slider.valueChanged.connect(self.set_tail_calcium_offset)
        layout.addWidget(self.tail_calcium_offset_slider)

        self.tail_calcium_offset_label = QLabel(str(self.controller.tail_calcium_offset))
        layout.addWidget(self.tail_calcium_offset_label)

        label = QLabel("Calcium FPS: ")
        layout.addWidget(label)

        self.calcium_fps_textbox = QLineEdit()
        self.calcium_fps_textbox.setText(str(self.controller.calcium_fps))
        self.calcium_fps_textbox.setFixedWidth(50)
        self.calcium_fps_textbox.editingFinished.connect(self.set_calcium_fps)
        layout.addWidget(self.calcium_fps_textbox)

        label = QLabel("Tail Data FPS: ")
        layout.addWidget(label)

        self.tail_fps_textbox = QLineEdit()
        self.tail_fps_textbox.setText(str(self.controller.tail_fps))
        self.tail_fps_textbox.setFixedWidth(50)
        self.tail_fps_textbox.editingFinished.connect(self.set_tail_fps)
        layout.addWidget(self.tail_fps_textbox)

        self.export_data_button = QPushButton("Export Data...")
        self.export_data_button.setFixedWidth(120)
        self.export_data_button.clicked.connect(self.export_data)
        self.export_data_button.setEnabled(True)
        layout.addWidget(self.export_data_button)

        widget = QWidget()
        self.regressor_correlation_params = QVBoxLayout(widget)
        label = QLabel("Regressor Correlation Params")
        label.setFont(subheading_font)
        self.regressor_correlation_params.addWidget(label)
        self.main_layout.addWidget(widget)

        self.regressor_slider_layout = self.initalize_horizontal_layout()

        self.regressor_slider_layout.addWidget(QLabel("Regressor: "))
        self.regressor_index_slider = QSlider(Qt.Horizontal)
        self.regressor_index_slider.setRange(0, self.controller.n_regressors)
        self.regressor_index_slider.setValue(self.controller.regressor_index)
        self.regressor_index_slider.valueChanged.connect(self.set_regressor_index)
        self.regressor_slider_layout.addWidget(self.regressor_index_slider)

        self.regressor_index_label = QLabel(str(0))
        self.regressor_slider_layout.addWidget(self.regressor_index_label)

        self.p_slider_layout = self.initalize_horizontal_layout()
        label = QLabel("Max p-value: ")
        self.p_slider_layout.addWidget(label)

        self.max_p_slider = QSlider(Qt.Horizontal)
        self.max_p_slider.setRange(1, 50)
        self.max_p_slider.setValue(int(100 * self.controller.max_p))
        self.max_p_slider.valueChanged.connect(self.set_max_p)
        self.p_slider_layout.addWidget(self.max_p_slider)

        self.max_p_label = QLabel(str(0.05))
        self.p_slider_layout.addWidget(self.max_p_label)

        widget = QWidget()
        self.regressor_correlation_params = QVBoxLayout(widget)
        label = QLabel("Multi-Regressor Params")
        label.setFont(subheading_font)
        self.regressor_correlation_params.addWidget(label)
        self.main_layout.addWidget(widget)

        widget = QWidget()
        self.regressor_correlation_params.addWidget(widget)
        layout = QHBoxLayout(widget)

        label = QLabel("Regressors to use for multilinear regression:")
        layout.addWidget(label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.regressor_correlation_params.addWidget(scroll_area)

        widget = QWidget()
        scroll_area.setWidget(widget)
        self.checkbox_layout = QVBoxLayout(widget)

    def export_data(self):
        save_data(self.controller.correlation_results, self.controller.regressors)
        # print('replication of clever test')

    def initalize_horizontal_layout(self):
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        self.main_layout.addWidget(widget)

        return layout

    def update_gui(self):
        if len(self.controller.calcium_video_fnames) > 0:
            self.load_calcium_video_button.setText("✓ Load Calcium Video(s)...")
            self.remove_video_button.setEnabled(True)
        else:
            self.load_calcium_video_button.setText("Load Calcium Video(s)...")
            self.remove_video_button.setEnabled(False)

            self.regressor_index_slider.setRange(0, 0)
            self.regressor_index_label.setText("0")
            self.export_data_button.setEnabled(False)
            self.z_slider.setRange(0, 0)
            self.z_label.setText("0")

            for i in range(self.video_combobox.count() - 1, -1, -1):
                self.video_combobox.removeItem(i)

            self.controller.regression_plot_window.update_plots()

        self.update_regressor_checkboxes()

        if len(self.controller.roi_data_fnames) > 0:
            self.load_roi_data_button.setText("✓ Load ROI Data File(s)...")
        else:
            self.load_roi_data_button.setText("Load ROI Data File(s)...")

        if len(self.controller.bout_fnames) > 0:
            self.load_bouts_button.setText("✓ Load Bout File(s)...")
        else:
            self.load_bouts_button.setText("Load Bout File(s)...")

        if len(self.controller.frame_timestamp_fnames) > 0:
            self.load_frame_timestamps_button.setText("✓ Load Timestamp File(s)...")
        else:
            self.load_frame_timestamps_button.setText("Load Timestamp File(s)...")

    def load_calcium_video(self):
        calcium_video_fnames = \
            QFileDialog.getOpenFileNames(self, 'Select calcium imaging video(s).', '', 'Videos (*.tiff *.tif)')[0]

        if calcium_video_fnames:
            self.set_fnames(calcium_video_fnames=calcium_video_fnames)

            self.load_roi_data_button.setEnabled(True)
            self.load_bouts_button.setEnabled(True)
            self.load_frame_timestamps_button.setEnabled(True)

            self.controller.roi_data_fnames = []
            self.controller.bout_fnames = []
            self.controller.frame_timestamp_fnames = []

        self.update_gui()

    def load_roi_data(self):
        roi_data_fnames = QFileDialog.getOpenFileNames(self, 'Select ROI data file(s).', '', 'Numpy files (*.npy)')[0]

        if roi_data_fnames is not None and len(roi_data_fnames) == len(self.controller.calcium_video_fnames):
            self.set_fnames(roi_data_fnames=roi_data_fnames)

        self.update_gui()

    def load_bouts(self):
        bout_fnames = QFileDialog.getOpenFileNames(self, 'Select labeled bouts file(s).', '', 'CSV files (*.csv)')[0]

        if bout_fnames is not None and len(bout_fnames) == len(self.controller.calcium_video_fnames):
            self.set_fnames(bout_fnames=bout_fnames)

        self.update_gui()

    def load_frame_timestamps(self):
        frame_timestamp_fnames = \
            QFileDialog.getOpenFileNames(self, 'Select frame timestamp file.', '', 'Text files (*.txt)')[0]

        if frame_timestamp_fnames is not None and len(frame_timestamp_fnames) == len(
                self.controller.calcium_video_fnames):
            self.set_fnames(frame_timestamp_fnames=frame_timestamp_fnames)

        self.update_gui()

    def remove_selected_video(self):
        if len(self.controller.calcium_video_fnames) > 0:
            del self.controller.calcium_video_fnames[self.controller.selected_video]
            del self.controller.roi_data_fnames[self.controller.selected_video]
            if len(self.controller.bout_fnames) > self.controller.selected_video:
                del self.controller.bout_fnames[self.controller.selected_video]
            if len(self.controller.frame_timestamp_fnames) > self.controller.selected_video:
                del self.controller.frame_timestamp_fnames[self.controller.selected_video]

            self.controller.selected_video = max(0, self.controller.selected_video - 1)

            if len(self.controller.calcium_video_fnames) > 0:
                self.set_video(self.controller.selected_video)
            else:
                self.controller.reset_regression_variables()

        self.update_gui()

    def set_fnames(self, calcium_video_fnames=None, roi_data_fnames=None, bout_fnames=None,
                   frame_timestamp_fnames=None):
        self.controller.calcium_video_fnames = calcium_video_fnames if calcium_video_fnames is not None else self.controller.calcium_video_fnames
        self.controller.roi_data_fnames = roi_data_fnames if roi_data_fnames is not None else self.controller.roi_data_fnames
        self.controller.bout_fnames = bout_fnames if bout_fnames is not None else self.controller.bout_fnames
        self.controller.frame_timestamp_fnames = frame_timestamp_fnames if frame_timestamp_fnames is not None else self.controller.frame_timestamp_fnames

        for i in range(self.video_combobox.count(), -1, -1):
            self.video_combobox.removeItem(i)

        self.video_combobox.addItems(self.controller.calcium_video_fnames)

    def set_video(self, i):
        self.controller.selected_video = int(i)

        if len(self.controller.calcium_video_fnames) > 0 and len(self.controller.roi_data_fnames) == len(
                self.controller.calcium_video_fnames) and (
                len(self.controller.bout_fnames) == len(self.controller.calcium_video_fnames) or len(
            self.controller.frame_timestamp_fnames) == len(self.controller.calcium_video_fnames)):
            self.do_regressor_analysis()

    def set_tail_calcium_offset(self, i):
        self.controller.tail_calcium_offset = int(i)

        self.tail_calcium_offset_label.setText(str(self.controller.tail_calcium_offset))

        if 0 < len(self.controller.calcium_video_fnames) == len(
                self.controller.bout_fnames) and len(self.controller.roi_data_fnames) == len(
            self.controller.calcium_video_fnames):
            self.do_regressor_analysis()

    def set_calcium_fps(self):
        self.controller.calcium_fps = float(self.calcium_fps_textbox.text())

        if 0 < len(self.controller.calcium_video_fnames) == len(
                self.controller.bout_fnames) and len(self.controller.roi_data_fnames) == len(
            self.controller.calcium_video_fnames):
            self.do_regressor_analysis()

    def set_tail_fps(self):
        self.controller.tail_fps = float(self.tail_fps_textbox.text())

        if 0 < len(self.controller.calcium_video_fnames) == len(
                self.controller.bout_fnames) and len(self.controller.roi_data_fnames) == len(
            self.controller.calcium_video_fnames):
            self.do_regressor_analysis()

    def set_regressor_index(self, i):
        self.controller.regressor_index = int(i)

        self.regressor_index_label.setText(str(self.controller.regressor_index))

        self.controller.regression_plot_window.update_plots()

    def set_max_p(self, i):
        self.controller.max_p = i / 100.0

        self.max_p_label.setText(str(self.controller.max_p))

        self.controller.regression_plot_window.update_plots()

    def set_z(self, i):
        self.controller.regression_z = int(i)

        self.z_label.setText(str(self.controller.regression_z))

        self.controller.regression_plot_window.update_plots()

    def do_regressor_analysis(self):
        self.controller.do_regressor_analysis()
        self.regressor_index_slider.setRange(0, len(self.controller.regressors.keys()) - 1)
        self.z_slider.setRange(0, self.controller.calcium_video.shape[1] - 1)
        self.update_regressor_checkboxes()

    def checkbox_state_changed(self, state):
        self.controller.update_multilinear_regression()

    def update_regressor_checkboxes(self):
        for i in reversed(range(self.checkbox_layout.count())):
            self.checkbox_layout.itemAt(i).widget().setParent(None)

        self.controller.checkboxes = []

        if self.controller.regressors is not None:
            keys = list(self.controller.regressors.keys())

            for i in range(len(keys)):
                checkbox = QCheckBox(keys[i])
                checkbox.setChecked(True)
                self.checkbox_layout.addWidget(checkbox)
                checkbox.stateChanged.connect(self.checkbox_state_changed)
                self.controller.checkboxes.append(checkbox)