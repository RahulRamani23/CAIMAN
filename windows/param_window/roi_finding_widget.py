import numpy as np
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QCheckBox, QLineEdit, QSizePolicy

from windows.param_window.param_widget import ParamWidget
from windows.param_window.param_window import *
from windows.param_window.hover_label import HoverLabel
from windows.param_window.hover_button import HoverButton
from windows.param_window.hover_check_box import HoverCheckBox
from windows.param_window.suite2p_roi_finding_widget import Suite2pROIFindingWidget
from windows.param_window.cnmf_roi_finding_widget import CNMFROIFindingWidget

try:
    import suite2p

    suite2p_available = True
except:
    suite2p_available = False


class ROIFindingWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "")

        self.controller = controller

        self.cnmf_roi_finding_widget = CNMFROIFindingWidget(self.parent_widget, self.controller)
        self.suite2p_roi_finding_widget = Suite2pROIFindingWidget(self.parent_widget, self.controller)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.tab_widget)
        self.tab_widget.addTab(self.cnmf_roi_finding_widget, "CNMF")
        self.tab_widget.addTab(self.suite2p_roi_finding_widget, "Suite2p")
        self.tab_widget.currentChanged.connect(self.tab_selected)

        # disable suite2p if the module hasn't been installed
        if not suite2p_available:
            self.tab_widget.setTabEnabled(1, False)

        self.main_layout.addStretch()

        self.button_widget = QWidget(self)
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(10, 10, 10, 10)
        self.button_layout.setSpacing(15)
        self.main_layout.addWidget(self.button_widget)

        self.show_zscore_checkbox = QCheckBox("Show Z-Score")
        self.show_zscore_checkbox.setObjectName("Show Z-Score")
        self.show_zscore_checkbox.setChecked(True)
        self.show_zscore_checkbox.clicked.connect(self.toggle_show_zscore)
        self.button_layout.addWidget(self.show_zscore_checkbox)

        self.ignored_frames_label = HoverLabel("Ignored frames: ", self.parent_widget, self.parent_widget.statusBar())
        self.ignored_frames_label.setHoverMessage("Input comma-separated frames to ignore when finding ROIs.")
        self.button_layout.addWidget(self.ignored_frames_label)

        self.ignored_frames_textbox = QLineEdit()
        self.ignored_frames_textbox.setFixedWidth(60)
        self.ignored_frames_textbox.setFixedHeight(20)
        self.ignored_frames_textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ignored_frames_textbox.editingFinished.connect(self.controller.update_ignored_frames)
        self.button_layout.addWidget(self.ignored_frames_textbox)

        self.button_layout.addStretch()

        self.use_multiprocessing_checkbox = HoverCheckBox("Use multiprocessing", self.parent_widget,
                                                          self.parent_widget.statusBar())
        self.use_multiprocessing_checkbox.setHoverMessage("Use multiple cores to speed up computations.")
        self.use_multiprocessing_checkbox.setChecked(True)
        self.use_multiprocessing_checkbox.clicked.connect(
            lambda: self.controller.set_use_multiprocessing(self.use_multiprocessing_checkbox.isChecked()))
        self.button_layout.addWidget(self.use_multiprocessing_checkbox)

        self.draw_mask_button = HoverButton('Edit Masks...', self.parent_widget, self.parent_widget.statusBar())
        self.draw_mask_button.setHoverMessage(
            "Draw masks to constrain where ROIs are found (or remove existing masks).")
        self.draw_mask_button.setIcon(QIcon("../icons/action_icon.png"))
        self.draw_mask_button.setIconSize(QSize(13, 16))
        self.draw_mask_button.clicked.connect(self.controller.toggle_mask_mode)
        self.button_layout.addWidget(self.draw_mask_button)

        self.find_rois_button = HoverButton('Find ROIs', self.parent_widget, self.parent_widget.statusBar())
        self.find_rois_button.setHoverMessage("Find ROIs for all videos.")
        self.find_rois_button.setIcon(QIcon("../icons/action_icon.png"))
        self.find_rois_button.setIconSize(QSize(13, 16))
        self.find_rois_button.clicked.connect(self.controller.find_rois)
        self.button_layout.addWidget(self.find_rois_button)

    def toggle_show_zscore(self):
        show_zscore = self.show_zscore_checkbox.isChecked()

        self.parent_widget.set_show_zscore(show_zscore)

    def roi_finding_started(self):
        n_groups = len(np.unique(self.controller.video_groups()))

        self.find_rois_button.setEnabled(False)
        self.draw_mask_button.setEnabled(False)

        self.parent_widget.set_default_statusbar_message("Finding ROIs for group {}/{}...".format(1, n_groups))

    def update_roi_finding_progress(self, group_num):
        n_groups = len(np.unique(self.controller.video_groups()))

        if group_num != n_groups - 1:
            self.parent_widget.set_default_statusbar_message(
                "Finding ROIs for group {}/{}...".format(group_num + 2, n_groups))

    def roi_finding_ended(self):
        self.find_rois_button.setEnabled(True)
        self.draw_mask_button.setEnabled(True)

        self.parent_widget.set_default_statusbar_message("")

    def tab_selected(self):
        index = self.tab_widget.currentIndex()
        if index == 0:
            self.controller.set_roi_finding_mode("cnmf")
        elif index == 1:
            self.controller.set_roi_finding_mode("suite2p")