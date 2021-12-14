from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from windows.param_window.hover_button import HoverButton
from windows.param_window.hover_check_box import HoverCheckBox

heading_font = QFont()
heading_font.setBold(True)
heading_font.setPointSize(16)


class VideoLoadingWidget(QWidget):
    def __init__(self, parent_widget, controller):
        QWidget.__init__(self)

        self.parent_widget = parent_widget

        self.controller = controller

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.title_widget = QWidget(self)
        self.title_layout = QHBoxLayout(self.title_widget)
        self.title_layout.setContentsMargins(5, 5, 0, 0)
        self.main_layout.addWidget(self.title_widget)

        self.title_label = QLabel("Videos to Process")
        self.title_label.setFont(heading_font)
        self.title_layout.addWidget(self.title_label)
        self.main_layout.setAlignment(self.title_widget, Qt.AlignTop)

        # create main buttons
        self.button_widget = QWidget(self)
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setSpacing(5)
        self.main_layout.addWidget(self.button_widget)

        self.open_file_button = HoverButton('Add Videos...', self.parent_widget, self.parent_widget.statusBar())
        self.open_file_button.setHoverMessage("Add video files for processing. TIFF files are currently supported.")
        self.open_file_button.setStyleSheet('font-weight: bold;')
        self.open_file_button.setIcon(QIcon("../icons/add_video_icon.png"))
        self.open_file_button.setIconSize(QSize(21, 16))
        self.open_file_button.clicked.connect(self.controller.import_videos)
        self.button_layout.addWidget(self.open_file_button)

        self.add_secondary_image_button = HoverButton('Add Secondary Image...', self.parent_widget,
                                                      self.parent_widget.statusBar())
        self.add_secondary_image_button.setHoverMessage("Add secondary image. TIFF files are currently supported.")
        self.add_secondary_image_button.setStyleSheet('font-weight: bold;')
        self.add_secondary_image_button.setIcon(QIcon("../icons/add_video_icon.png"))
        self.add_secondary_image_button.setIconSize(QSize(21, 16))
        self.add_secondary_image_button.clicked.connect(self.controller.add_secondary_image)
        self.button_layout.addWidget(self.add_secondary_image_button)

        self.remove_videos_button = HoverButton('Remove Video', self.parent_widget, self.parent_widget.statusBar())
        self.remove_videos_button.setHoverMessage("Remove the selected video.")
        self.remove_videos_button.setIcon(QIcon("../icons/remove_video_icon.png"))
        self.remove_videos_button.setIconSize(QSize(21, 16))
        self.remove_videos_button.setDisabled(True)
        self.remove_videos_button.clicked.connect(self.parent_widget.remove_selected_items)
        self.button_layout.addWidget(self.remove_videos_button)

        self.button_layout.addStretch()

        self.add_group_button = HoverButton('Add Group', self.parent_widget, self.parent_widget.statusBar())
        self.add_group_button.setHoverMessage("Add a new group. Videos in a group are combined before being processed.")
        self.add_group_button.setIcon(QIcon("../icons/add_group_icon.png"))
        self.add_group_button.setIconSize(QSize(16, 16))
        self.add_group_button.clicked.connect(self.parent_widget.add_new_group)
        self.button_layout.addWidget(self.add_group_button)

        self.remove_group_button = HoverButton('Remove Group', self.parent_widget, self.parent_widget.statusBar())
        self.remove_group_button.setHoverMessage("Remove the selected group.")
        self.remove_group_button.setIcon(QIcon("../icons/remove_group_icon.png"))
        self.remove_group_button.setIconSize(QSize(16, 16))
        self.remove_group_button.setDisabled(True)
        self.remove_group_button.clicked.connect(self.parent_widget.remove_selected_group)
        self.button_layout.addWidget(self.remove_group_button)

        # create secondary buttons
        self.button_widget_2 = QWidget(self)
        self.button_layout_2 = QHBoxLayout(self.button_widget_2)
        self.button_layout_2.setContentsMargins(10, 0, 0, 0)
        self.button_layout_2.setSpacing(15)
        self.main_layout.addWidget(self.button_widget_2)

        self.button_layout_2.addStretch()

        self.use_multiprocessing_checkbox = HoverCheckBox("Use multiprocessing", self.parent_widget,
                                                          self.parent_widget.statusBar())
        self.use_multiprocessing_checkbox.setHoverMessage("Use all available CPU cores to speed up computations.")
        self.use_multiprocessing_checkbox.setChecked(True)
        self.use_multiprocessing_checkbox.clicked.connect(
            lambda: self.controller.set_use_multiprocessing(self.use_multiprocessing_checkbox.isChecked()))
        self.button_layout_2.addWidget(self.use_multiprocessing_checkbox)

        self.mc_and_find_rois_button = HoverButton('Motion Correct && Find ROIs...', self.parent_widget,
                                                   self.parent_widget.statusBar())
        self.mc_and_find_rois_button.setHoverMessage(
            "Motion correct and find ROIs for all videos using the current parameters.")
        self.mc_and_find_rois_button.setStyleSheet('font-weight: bold;')
        self.mc_and_find_rois_button.setIcon(QIcon("../icons/fast_forward_icon.png"))
        self.mc_and_find_rois_button.setIconSize(QSize(18, 16))
        self.mc_and_find_rois_button.setEnabled(False)
        self.mc_and_find_rois_button.clicked.connect(self.controller.motion_correct_and_find_rois)
        self.button_layout_2.addWidget(self.mc_and_find_rois_button)