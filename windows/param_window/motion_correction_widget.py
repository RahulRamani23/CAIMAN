from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon

from windows.param_window.param_widget import *
from windows.param_window.hover_button import HoverButton

class MotionCorrectionWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Motion Correction Parameters")

        self.controller = controller

        self.main_layout.addStretch()

        self.add_param_slider(label_name="Maximum Shift", name="max_shift", minimum=1, maximum=100,
                              value=self.controller.params()['max_shift'], moved=self.update_param, num=0,
                              released=self.update_param,
                              description="Maximum shift (in pixels) allowed for motion correction.", int_values=True)
        self.add_param_slider(label_name="Patch Stride", name="patch_stride", minimum=1, maximum=100,
                              value=self.controller.params()['patch_stride'], moved=self.update_param, num=1,
                              released=self.update_param,
                              description="Stride length (in pixels) of each patch used in motion correction.",
                              int_values=True)
        self.add_param_slider(label_name="Patch Overlap", name="patch_overlap", minimum=1, maximum=100,
                              value=self.controller.params()['patch_overlap'], moved=self.update_param, num=2,
                              released=self.update_param,
                              description="Overlap (in pixels) of patches used in motion correction.", int_values=True)

        self.button_widget_2 = QWidget(self)
        self.button_layout_2 = QHBoxLayout(self.button_widget_2)
        self.button_layout_2.setContentsMargins(10, 10, 10, 10)
        self.button_layout_2.setSpacing(15)
        self.main_layout.addWidget(self.button_widget_2)

        self.use_mc_video_checkbox = HoverCheckBox("Use motion-corrected videos", self.parent_widget,
                                                   self.parent_widget.statusBar())
        self.use_mc_video_checkbox.setHoverMessage("Use the motion-corrected videos for finding ROIs.")
        self.use_mc_video_checkbox.setChecked(False)
        self.use_mc_video_checkbox.clicked.connect(
            lambda: self.controller.set_use_mc_video(self.use_mc_video_checkbox.isChecked()))
        self.use_mc_video_checkbox.setDisabled(True)
        self.button_layout_2.addWidget(self.use_mc_video_checkbox)

        self.button_layout_2.addStretch()

        self.use_multiprocessing_checkbox = HoverCheckBox("Use multiprocessing", self.parent_widget,
                                                          self.parent_widget.statusBar())
        self.use_multiprocessing_checkbox.setHoverMessage("Use multiple cores to speed up computations.")
        self.use_multiprocessing_checkbox.setChecked(True)
        self.use_multiprocessing_checkbox.clicked.connect(
            lambda: self.controller.set_use_multiprocessing(self.use_multiprocessing_checkbox.isChecked()))
        self.button_layout_2.addWidget(self.use_multiprocessing_checkbox)

        self.motion_correct_button = HoverButton('Motion Correct', self.parent_widget, self.parent_widget.statusBar())
        self.motion_correct_button.setHoverMessage("Perform motion correction on all videos.")
        self.motion_correct_button.setIcon(QIcon("../icons/action_icon.png"))
        self.motion_correct_button.setIconSize(QSize(13, 16))
        self.motion_correct_button.setStyleSheet('font-weight: bold;')
        self.motion_correct_button.clicked.connect(self.controller.motion_correct_video)
        self.button_layout_2.addWidget(self.motion_correct_button)

    def motion_correction_started(self):
        n_groups = len(np.unique(self.controller.video_groups()))

        self.parent_widget.set_default_statusbar_message("Motion correcting group {}/{}...".format(1, n_groups))
        self.motion_correct_button.setEnabled(False)
        self.parent_widget.tab_widget.setTabEnabled(0, False)
        self.parent_widget.tab_widget.setTabEnabled(2, False)
        self.parent_widget.tab_widget.setTabEnabled(3, False)

    def motion_correction_ended(self):
        self.motion_correct_button.setEnabled(True)
        self.parent_widget.tab_widget.setTabEnabled(0, True)
        self.parent_widget.tab_widget.setTabEnabled(2, True)
        self.use_mc_video_checkbox.setEnabled(True)
        self.use_mc_video_checkbox.setChecked(True)

        self.parent_widget.set_default_statusbar_message("")

    def update_motion_correction_progress(self, group_num):
        n_groups = len(np.unique(self.controller.video_groups()))

        if group_num != n_groups - 1:
            self.parent_widget.set_default_statusbar_message(
                "Motion correcting group {}/{}...".format(group_num + 2, n_groups))