from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from controller.regressor_analysis import save_data

import os
import numpy as np

try:
    import suite2p

    suite2p_available = True
except:
    suite2p_available = False

showing_video_color = QColor(151, 66, 252, 20)

SHOW_VIDEO_BUTTON_DISABLED_STYLESHEET = "QPushButton{border: none; background-size: contain; background-image:url(icons/play_icon_disabled.png);} QPushButton:hover{background-image:url(icons/play_icon.png);}"
SHOW_VIDEO_BUTTON_ENABLED_STYLESHEET = "QPushButton{border: none; background-size: contain; background-image:url(icons/play_icon_enabled.png);} QPushButton:hover{background-image:url(icons/play_icon_enabled.png);}"

group_font = QFont()
group_font.setBold(True)

heading_font = QFont()
heading_font.setBold(True)
heading_font.setPointSize(16)

subheading_font = QFont()
subheading_font.setBold(True)
subheading_font.setPointSize(13)


class ParamWindow(QMainWindow):
    def __init__(self, controller):
        global rounded_stylesheet, statusbar_stylesheet, showing_video_color, show_video_button_disabled_stylesheet, show_video_button_enabled_stylesheet, video_label_selected_color, video_label_unselected_color
        QMainWindow.__init__(self)

        # set controller
        self.controller = controller

        # set window title
        self.setWindowTitle("Automatic ROI Segmentation")

        # set initial position
        self.setGeometry(0, 32, 10, 10)

        # create main widget & layout
        self.main_widget = QWidget(self)
        self.main_layout = QGridLayout(self.main_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 10)
        self.main_layout.setSpacing(5)

        # set main widget to be the central widget
        self.setCentralWidget(self.main_widget)

        self.set_default_statusbar_message(
            "To begin, open one or more video files. Only TIFF files are currently supported.")

        self.main_param_widget = MainParamWidget(self, self.controller)
        self.main_layout.addWidget(self.main_param_widget, 0, 0)

        # create loading widget
        self.loading_widget = VideoLoadingWidget(self, self.controller)

        # create motion correction widget
        self.motion_correction_widget = MotionCorrectionWidget(self, self.controller)

        # create ROI finding widget
        self.roi_finding_widget = ROIFindingWidget(self, self.controller)

        # create ROI filtering widget
        self.roi_filtering_widget = ROIFilteringWidget(self, self.controller)

        self.regression_analysis_widget = RegressorAnalysisWidget(self, self.controller)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setContentsMargins(5, 5, 5, 5)
        self.main_layout.addWidget(self.tab_widget, 3, 0)
        self.tab_widget.addTab(self.loading_widget, "1. Video Selection")
        self.tab_widget.addTab(self.motion_correction_widget, "2. Motion Correction")
        self.tab_widget.addTab(self.roi_finding_widget, "3. ROI Finding")
        self.tab_widget.addTab(self.roi_filtering_widget, "4. Refinement && Saving")
        self.tab_widget.addTab(self.regression_analysis_widget, "5. Regression Analysis")
        self.tab_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        for i in range(self.tab_widget.count()):
            if i == 0:
                self.tab_widget.widget(i).setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
            else:
                self.tab_widget.widget(i).setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Ignored)

        self.tab_widget.currentChanged.connect(self.tab_selected)

        self.videos_list_widget = QWidget(self)
        self.videos_list_layout = QHBoxLayout(self.videos_list_widget)
        self.videos_list_layout.setContentsMargins(5, 0, 5, 0)
        self.main_layout.addWidget(self.videos_list_widget, 4, 0)
        self.videos_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        self.videos_list = QListWidget(self)
        self.videos_list.itemSelectionChanged.connect(self.item_selected)
        self.videos_list_layout.addWidget(self.videos_list)
        self.videos_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.videos_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.videos_list.installEventFilter(self)

        self.delete_shortcut = QShortcut(QKeySequence('Delete'), self.videos_list)
        self.delete_shortcut.activated.connect(self.remove_selected_items)

        self.group_nums = []

        # create menus
        self.create_menus()

        # set initial state of widgets, buttons & menu items
        self.set_initial_state()

        # set window title bar buttons
        self.setWindowFlags(
            Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowFullscreenButtonHint)

        self.show()

    def update_ignored_frames_textbox(self, string):
        self.roi_finding_widget.ignored_frames_textbox.setText(string)

    def set_default_statusbar_message(self, message):
        self.default_statusbar_message = message
        self.statusBar().showMessage(self.default_statusbar_message)

    def set_initial_state(self):
        # disable buttons, widgets & menu items
        self.main_param_widget.setDisabled(True)
        self.tab_widget.setCurrentIndex(0)
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(2, False)
        self.tab_widget.setTabEnabled(3, False)
        self.show_rois_action.setEnabled(False)
        self.save_rois_action.setEnabled(False)
        self.load_rois_action.setEnabled(False)

        self.set_default_statusbar_message(
            "To begin, open one or more video files. Only TIFF files are currently supported.")

    def first_video_imported(self):
        self.play_video_action.setEnabled(True)

    def set_imaging_fps(self, imaging_fps):
        self.roi_filtering_widget.update_param_slider_and_textbox('imaging_fps', imaging_fps, multiplier=1,
                                                                  int_values=True)

    def set_video_paths(self, video_paths):
        video_items = [self.videos_list.item(i) for i in range(self.videos_list.count()) if
                       self.videos_list.item(i).font() != group_font]

        print(video_paths)

        if len(video_paths) != len(video_items):
            raise ValueError(
                "Attempted to change the paths in the video list, but {} paths were provided, while {} videos are loaded.".format(
                    len(video_paths), len(video_items)))

        video_num = 0

        for i in range(self.videos_list.count()):
            item = self.videos_list.item(i)

            if item.font() != group_font:

                item.setData(100, video_paths[video_num])

                widget = self.videos_list.itemWidget(item)
                if widget is not None:
                    label = widget.findChild(QLabel)

                    label.setText(video_paths[video_num])

                    button = widget.findChild(HoverButton)
                    button.clicked.disconnect()
                    button.clicked.connect(self.make_show_video(video_paths[video_num], button))

                    item.setSizeHint(widget.sizeHint())

                video_num += 1

    def set_show_zscore(self, show_zscore):
        self.controller.set_show_zscore(show_zscore)

        self.roi_finding_widget.show_zscore_checkbox.setChecked(show_zscore)
        self.roi_filtering_widget.show_zscore_checkbox.setChecked(show_zscore)

    def tab_selected(self):
        index = self.tab_widget.currentIndex()

        for i in range(self.tab_widget.count()):
            if i == index:
                self.tab_widget.widget(i).setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            else:
                self.tab_widget.widget(i).setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Ignored)

        if index == 0:
            self.controller.show_video_loading_params()
        elif index == 1:
            self.controller.show_motion_correction_params()
        elif index == 2:
            self.controller.show_roi_finding_params()
        elif index == 3:
            self.controller.show_roi_filtering_params()

    def single_roi_selected(self, discarded=False):
        if not discarded:
            self.roi_filtering_widget.discard_selected_roi_button.setEnabled(True)
            self.discard_rois_action.setEnabled(True)
            self.roi_filtering_widget.keep_selected_roi_button.setEnabled(False)
            self.keep_rois_action.setEnabled(False)
        else:
            self.roi_filtering_widget.discard_selected_roi_button.setEnabled(False)
            self.discard_rois_action.setEnabled(False)
            self.roi_filtering_widget.keep_selected_roi_button.setEnabled(True)
            self.keep_rois_action.setEnabled(True)
        self.roi_filtering_widget.merge_rois_button.setEnabled(False)
        self.merge_rois_action.setEnabled(False)

    def multiple_rois_selected(self, discarded=False, merge_enabled=True):
        if not discarded:
            self.roi_filtering_widget.discard_selected_roi_button.setEnabled(True)
            self.discard_rois_action.setEnabled(True)
            self.roi_filtering_widget.keep_selected_roi_button.setEnabled(False)
            self.keep_rois_action.setEnabled(False)
            self.roi_filtering_widget.merge_rois_button.setEnabled(merge_enabled)
            self.merge_rois_action.setEnabled(merge_enabled)
        else:
            self.roi_filtering_widget.discard_selected_roi_button.setEnabled(False)
            self.discard_rois_action.setEnabled(False)
            self.roi_filtering_widget.keep_selected_roi_button.setEnabled(True)
            self.keep_rois_action.setEnabled(True)
            self.roi_filtering_widget.merge_rois_button.setEnabled(False)
            self.merge_rois_action.setEnabled(False)

    def no_rois_selected(self):
        self.roi_filtering_widget.discard_selected_roi_button.setEnabled(False)
        self.discard_rois_action.setEnabled(False)
        self.roi_filtering_widget.keep_selected_roi_button.setEnabled(False)
        self.keep_rois_action.setEnabled(False)
        self.roi_filtering_widget.merge_rois_button.setEnabled(False)
        self.merge_rois_action.setEnabled(False)

    def eventFilter(self, sender, event):
        if (event.type() == QEvent.ChildRemoved):
            self.on_order_changed()
        return False

    def on_order_changed(self):
        print("Order changed.")

        item = self.videos_list.item(0)
        if item.font() != group_font:
            self.update_video_list_items()
        else:
            groups = []
            old_indices = []

            group_num = -1

            for i in range(self.videos_list.count()):
                item = self.videos_list.item(i)

                if item.font() == group_font:
                    group_num = int(item.text().split(" ")[-1]) - 1
                else:
                    groups.append(group_num)

                    old_index = self.controller.video_paths().index(item.data(100))
                    old_indices.append(old_index)

            self.controller.videos_rearranged(old_indices, groups)

    def update_video_list_items(self):
        self.videos_list.clear()

        video_paths = self.controller.video_paths()
        video_groups = self.controller.video_groups()

        groups = np.unique(video_groups)

        for group in groups:
            self.add_group(group)

            paths = [video_paths[i] for i in range(len(video_paths)) if video_groups[i] == group]

            for path in paths:
                index = video_paths.index(path)
                self.add_video_item(path, playing=(self.controller.video_num == index))

    def add_group(self, group_num):
        item = QListWidgetItem("Group {}".format(group_num + 1))
        item.setFont(group_font)
        color = QColor(36, 87, 201, 60)
        item.setBackground(QBrush(color, Qt.SolidPattern))
        item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
        self.videos_list.addItem(item)
        self.group_nums.append(group_num)

        self.controller.add_group(group_num)

    def add_new_group(self):
        if len(self.group_nums) > 0:
            group_num = np.amax(self.group_nums) + 1
        else:
            group_num = 0

        self.add_group(group_num)

    def remove_selected_items(self):
        selected_items = self.videos_list.selectedItems()

        self.controller.remove_videos_at_indices(
            [self.controller.video_paths().index(item.data(100)) for item in selected_items])

        for i in range(len(selected_items) - 1, -1, -1):
            self.videos_list.takeItem(self.videos_list.row(selected_items[i]))

    def remove_items(self, items):
        self.controller.remove_videos_at_indices(
            [self.controller.video_paths().index(item.data(100)) for item in items])

        for i in range(len(items) - 1, -1, -1):
            self.videos_list.takeItem(self.videos_list.row(items[i]))

    def remove_selected_group(self):
        selected_items = self.videos_list.selectedItems()

        self.videos_list.takeItem(self.videos_list.row(selected_items[0]))

        group_num = int(selected_items[0].text().split(" ")[-1]) - 1

        print("Removing group {}.".format(group_num + 1))

        if group_num in self.group_nums:
            index = self.group_nums.index(group_num)
            del self.group_nums[index]

        items_to_remove = []

        for i in range(self.videos_list.count()):
            item = self.videos_list.item(i)

            if item.font() != group_font:
                index = self.controller.video_paths().index(item.data(100))
                if self.controller.video_groups()[index] == group_num:
                    items_to_remove.append(item)

        if len(items_to_remove) > 0:
            self.remove_items(items_to_remove)

        self.controller.remove_group(group_num)

    def item_selected(self):
        tab_index = self.tab_widget.currentIndex()

        selected_items = self.videos_list.selectedItems()

        if len(selected_items) > 0:
            if selected_items[0].font() == group_font:
                group_num = int(selected_items[0].text().split(" ")[-1]) - 1

                print("Group {} clicked.".format(group_num + 1))

                self.loading_widget.remove_videos_button.setDisabled(True)
                self.show_video_action.setDisabled(True)
                self.loading_widget.remove_group_button.setDisabled(False)
                if tab_index == 0:
                    self.remove_videos_action.setEnabled(False)
                    self.remove_group_action.setEnabled(True)
            else:
                if len(selected_items) == 1:
                    self.show_video_action.setDisabled(False)
                else:
                    self.show_video_action.setDisabled(True)
                self.loading_widget.remove_videos_button.setDisabled(False)
                self.loading_widget.remove_group_button.setDisabled(True)
                if tab_index == 0:
                    self.remove_videos_action.setEnabled(True)
                    self.remove_group_action.setEnabled(False)
        else:
            self.show_video_action.setDisabled(True)
            self.loading_widget.remove_videos_button.setDisabled(True)
            self.loading_widget.remove_group_button.setDisabled(True)
            if tab_index == 0:
                self.remove_videos_action.setEnabled(False)
                self.remove_group_action.setEnabled(False)

        for i in range(self.videos_list.count()):
            item = self.videos_list.item(i)

            widget = self.videos_list.itemWidget(item)
            if widget is not None:
                label = widget.findChild(QLabel)

            index = None

    def show_selected_video(self):
        selected_items = self.videos_list.selectedItems()

        if len(selected_items) == 1:
            if selected_items[0].font() != group_font:
                video_path = selected_items[0].data(100)

                self.show_video(video_path)

    def video_loaded(self, video_path):
        for i in range(self.videos_list.count()):
            item = self.videos_list.item(i)

            widget = self.videos_list.itemWidget(item)

            if widget is not None:
                button = widget.findChild(HoverButton, "play_button")

                if item.data(100) == video_path:
                    item.setBackground(QBrush(showing_video_color, Qt.SolidPattern))

                    button.setStyleSheet(SHOW_VIDEO_BUTTON_ENABLED_STYLESHEET)
                else:
                    color = QColor(255, 255, 255, 0)
                    item.setBackground(QBrush(color, Qt.SolidPattern))

                    button.setStyleSheet(SHOW_VIDEO_BUTTON_DISABLED_STYLESHEET)

        self.statusBar().showMessage("")
        self.main_param_widget.param_sliders["z"].setMaximum(self.controller.video.shape[1] - 1)
        self.main_param_widget.param_sliders["z"].setValue(self.controller.z)
        self.main_param_widget.param_textboxes["z"].setText(str(self.controller.z))

    def make_show_video(self, video_path, preview_selected_video_button):
        def show_video():
            index = self.controller.video_paths().index(video_path)
            self.controller.load_video(index)

            for i in range(self.videos_list.count()):
                item = self.videos_list.item(i)

                widget = self.videos_list.itemWidget(item)
                if widget is not None:
                    button = widget.findChild(HoverButton, "play_button")

                    if button == preview_selected_video_button:
                        item.setBackground(QBrush(showing_video_color, Qt.SolidPattern))

                        button.setStyleSheet(SHOW_VIDEO_BUTTON_ENABLED_STYLESHEET)
                    else:
                        color = QColor(255, 255, 255, 0)
                        item.setBackground(QBrush(color, Qt.SolidPattern))

                        button.setStyleSheet(SHOW_VIDEO_BUTTON_DISABLED_STYLESHEET)

        return show_video

    def create_menus(self):
        def create_action(menu, label, shortcut="", shortcut_context=None, status_tip="", trigger=None, enabled=True,
                          checkable=False, checked=False):
            action = QAction(label, self)
            if shortcut:
                action.setShortcut(shortcut)
            if shortcut_context:
                action.setShortcutContext(shortcut_context)
            if status_tip:
                action.setStatusTip(status_tip)
            if trigger:
                action.triggered.connect(trigger)
            action.setEnabled(enabled)
            if checkable:
                action.setCheckable(True)
                action.setChecked(checked)
            menu.addAction(action)
            return action

        # Define Menu Bar
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('&File')
        create_action(file_menu, 'Add Videos...', shortcut='Ctrl+O', status_tip='Add video files for processing.',
                      trigger=self.controller.import_videos)

        create_action(file_menu, 'Add Secondary Image...', trigger=self.controller.add_secondary_image)

        self.load_tail_angles_action = create_action(file_menu, 'Load Tail Angle Trace...', shortcut='Ctrl+T',
                                                     status_tip='Load a tail angle CSV.',
                                                     trigger=self.controller.load_tail_angles, enabled=False,
                                                     shortcut_context=Qt.ApplicationShortcut)

        self.save_rois_action = create_action(file_menu, 'Save ROIs...', shortcut='Alt+S',
                                              status_tip='Save the current ROIs.',
                                              trigger=self.controller.save_all_rois, enabled=False,
                                              shortcut_context=Qt.ApplicationShortcut)

        # Video Menu
        video_menu = menubar.addMenu('&Videos')
        self.remove_videos_action = create_action(video_menu, 'Remove Video', shortcut='Ctrl+D',
                                                  status_tip='Remove the selected video.',
                                                  enabled=False, trigger=self.remove_selected_items)

        self.show_video_action = create_action(video_menu, 'Show Selected Video', shortcut='S',
                                               status_tip='Show the selected video.',
                                               enabled=False, trigger=self.show_selected_video)

        self.remove_group_action = create_action(video_menu, 'Remove Group', shortcut='Ctrl+D',
                                                 status_tip='Remove the selected group.',
                                                 enabled=False, trigger=self.remove_selected_group)

        # View Menu
        view_menu = menubar.addMenu('&View')
        self.show_rois_action = create_action(view_menu, 'Show ROIs', checkable=True, shortcut='R',
                                              status_tip='Toggle showing the ROIs.',
                                              trigger=lambda: self.controller.preview_window.set_show_rois(
                                                  self.show_rois_action.isChecked()),
                                              enabled=False, shortcut_context=Qt.ApplicationShortcut)

        self.play_video_action = create_action(view_menu, 'Play Video', checkable=True, shortcut='Space',
                                               status_tip='Toggle playing the video.',
                                               trigger=lambda: self.controller.preview_window.set_play_video(
                                                   self.play_video_action.isChecked()),
                                               checked=True, enabled=False, shortcut_context=Qt.ApplicationShortcut)
        # ROI Menu
        rois_menu = menubar.addMenu('&ROIs')
        self.load_rois_action = create_action(rois_menu, 'Load ROIs...', shortcut='Alt+O',
                                              status_tip='Load ROIs from a file.',
                                              trigger=self.controller.load_rois,
                                              shortcut_context=Qt.ApplicationShortcut, enabled=False)
        self.discard_rois_action = create_action(rois_menu, 'Discard Selected ROIs', shortcut='Delete',
                                                 status_tip='Discard the selected ROIs.',
                                                 trigger=self.controller.discard_selected_rois, enabled=False,
                                                 shortcut_context=Qt.ApplicationShortcut)

        self.keep_rois_action = create_action(rois_menu, 'Keep Selected ROIs', shortcut_context=Qt.ApplicationShortcut,
                                              shortcut='K',
                                              status_tip='Keep Selected ROIs',
                                              trigger=self.controller.keep_selected_rois, enabled=False)

        create_action(rois_menu, 'Save Traces of Selected ROIs...', shortcut='T',
                      status_tip='Save traces of the selected ROIs to a CSV file.',
                      trigger=self.controller.save_selected_roi_traces, shortcut_context=Qt.ApplicationShortcut)

        create_action(rois_menu, 'Save Images of ROIs...', shortcut='Q',
                      status_tip='Save images of current ROIs to a folder.', trigger=self.controller.save_roi_images,
                      shortcut_context=Qt.ApplicationShortcut)

        self.merge_rois_action = create_action(rois_menu, 'Merge Selected ROIs', shortcut='M',
                                               status_tip='Merge the selected ROIs.',
                                               trigger=self.controller.merge_selected_rois, enabled=False,
                                               shortcut_context=Qt.ApplicationShortcut)

        self.mc_and_find_rois_action = create_action(rois_menu, 'Motion Correct && Find ROIs', shortcut='Shift+M',
                                                     status_tip='Perform motion correction followed by ROI finding for all videos.',
                                                     trigger=self.controller.motion_correct_and_find_rois,
                                                     enabled=False,
                                                     shortcut_context=Qt.ApplicationShortcut)

    def add_video_item(self, video_path, playing=False):
        self.videos_list.addItem(video_path)

        item = self.videos_list.findItems(video_path, Qt.MatchFlag.MatchExactly)[0]
        widget = QWidget()
        label = QLabel(video_path)

        button_name = "play_button"

        preview_selected_video_button = HoverButton('', self, self.statusBar())
        preview_selected_video_button.setHoverMessage("View the selected video.")
        preview_selected_video_button.setFixedSize(QSize(13, 16))
        preview_selected_video_button.clicked.connect(self.make_show_video(video_path, preview_selected_video_button))
        preview_selected_video_button.setStyleSheet(SHOW_VIDEO_BUTTON_DISABLED_STYLESHEET)
        preview_selected_video_button.setObjectName(button_name)
        widgetButton = QPushButton()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(preview_selected_video_button)
        layout.addWidget(label)

        layout.setSizeConstraint(QLayout.SetFixedSize)
        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())
        item.setText("")
        item.setData(100, video_path)
        color = QColor(255, 255, 255, 0)
        item.setBackground(QBrush(color, Qt.SolidPattern))

        if playing:
            item.setBackground(QBrush(showing_video_color, Qt.SolidPattern))

            preview_selected_video_button.setStyleSheet(SHOW_VIDEO_BUTTON_ENABLED_STYLESHEET)

        self.videos_list.setItemWidget(item, widget)

    def videos_imported(self, video_paths):
        self.add_new_group()

        for video_path in video_paths:
            self.add_video_item(video_path)

        self.main_param_widget.setDisabled(False)
        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setTabEnabled(2, True)
        self.tab_widget.setTabEnabled(3, False)
        self.tab_widget.setCurrentIndex(0)
        self.load_rois_action.setEnabled(True)
        self.load_tail_angles_action.setEnabled(True)
        self.loading_widget.mc_and_find_rois_button.setEnabled(True)
        self.mc_and_find_rois_action.setEnabled(True)

        self.set_default_statusbar_message("")

    def video_opened(self, max_z, z):
        self.statusBar().showMessage("")
        self.main_param_widget.param_sliders["z"].setMaximum(max_z)
        self.main_param_widget.param_sliders["z"].setValue(z)
        self.main_param_widget.param_textboxes["z"].setText(str(z))

    def motion_correction_started(self):
        self.motion_correction_widget.motion_correction_started()

    def motion_correction_ended(self):
        self.motion_correction_widget.motion_correction_ended()

    def roi_finding_started(self):
        self.roi_finding_widget.roi_finding_started()

        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(3, False)

    def roi_finding_ended(self):
        self.roi_finding_widget.roi_finding_ended()

        self.tab_widget.setTabEnabled(0, True)
        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setTabEnabled(3, True)

    def mask_drawing_started(self):
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(3, False)
        self.roi_finding_widget.param_widget.setEnabled(False)
        self.roi_finding_widget.find_rois_button.setEnabled(False)
        self.roi_finding_widget.show_zscore_checkbox.setEnabled(False)
        self.roi_finding_widget.use_multiprocessing_checkbox.setEnabled(False)
        self.videos_list_widget.setEnabled(False)
        self.roi_finding_widget.draw_mask_button.setText("Done")

    def mask_drawing_ended(self):
        self.tab_widget.setTabEnabled(0, True)
        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setTabEnabled(3, True)
        self.roi_finding_widget.param_widget.setEnabled(True)
        self.roi_finding_widget.find_rois_button.setEnabled(True)
        self.roi_finding_widget.show_zscore_checkbox.setEnabled(True)
        self.roi_finding_widget.use_multiprocessing_checkbox.setEnabled(True)
        self.videos_list_widget.setEnabled(True)
        self.roi_finding_widget.draw_mask_button.setText("Edit Masks...")

    def update_motion_correction_progress(self, group_num):
        self.motion_correction_widget.update_motion_correction_progress(group_num)

    def update_roi_finding_progress(self, group_num):
        self.roi_finding_widget.update_roi_finding_progress(group_num)

    def closeEvent(self, event):
        self.controller.close_all()


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


class ParamWidget(QWidget):
    def __init__(self, parent_widget, controller, title):
        QWidget.__init__(self)

        self.parent_widget = parent_widget

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        if len(title) > 0:
            self.title_widget = QWidget(self)
            self.title_layout = QHBoxLayout(self.title_widget)
            self.title_layout.setContentsMargins(5, 5, 0, 0)
            self.main_layout.addWidget(self.title_widget)

            self.title_label = QLabel(title)
            self.title_label.setFont(heading_font)
            self.title_layout.addWidget(self.title_label)
            self.main_layout.setAlignment(self.title_widget, Qt.AlignTop)

        self.param_widget = QWidget(self)
        self.param_layout = QGridLayout(self.param_widget)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        self.param_layout.setSpacing(0)
        self.main_layout.addWidget(self.param_widget)

        self.param_sliders = {}
        self.param_slider_multipliers = {}
        self.param_textboxes = {}
        self.param_checkboxes = {}
        self.param_choosers = {}
        self.param_widgets = {}

    def add_param_slider(self, label_name, name, minimum, maximum, value, moved, num, multiplier=1, pressed=None,
                         released=None, description=None, int_values=False):
        row = np.floor(num / 2)
        col = num % 2

        if released == self.update_param:
            released = lambda: self.update_param(name, int_values=int_values)
        if moved == self.update_param:
            moved = lambda: self.update_param(name, int_values=int_values)
        if pressed == self.update_param:
            pressed = lambda: self.update_param(name, int_values=int_values)

        widget = QWidget(self.param_widget)
        layout = QHBoxLayout(widget)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.param_layout.addWidget(widget, row, col)
        label = HoverLabel("{}:".format(label_name), self.parent_widget, self.parent_widget.statusBar())
        label.setHoverMessage(description)
        layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setObjectName(name)
        slider.setFocusPolicy(Qt.StrongFocus)
        slider.setTickPosition(QSlider.NoTicks)
        slider.setTickInterval(1)
        slider.setSingleStep(1)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)
        slider.sliderMoved.connect(moved)
        if pressed:
            slider.sliderPressed.connect(pressed)
        if released:
            slider.sliderReleased.connect(released)
        layout.addWidget(slider)

        slider.sliderMoved.connect(lambda: self.update_textbox_from_slider(slider, textbox, multiplier, int_values))
        slider.sliderReleased.connect(lambda: self.update_textbox_from_slider(slider, textbox, multiplier, int_values))

        # make textbox & add to layout
        textbox = QLineEdit()
        textbox.setAlignment(Qt.AlignHCenter)
        textbox.setObjectName(name)
        textbox.setFixedWidth(60)
        textbox.setFixedHeight(20)
        textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        textbox.editingFinished.connect(
            lambda: self.update_slider_from_textbox(slider, textbox, multiplier, int_values))
        textbox.editingFinished.connect(released)
        self.update_textbox_from_slider(slider, textbox, multiplier, int_values)
        layout.addWidget(textbox)

        self.param_sliders[name] = slider
        self.param_slider_multipliers[name] = multiplier
        self.param_textboxes[name] = textbox
        self.param_widgets[name] = widget

    def add_param_checkbox(self, label_name, name, clicked, num, description=None, related_params=[]):
        row = np.floor(num / 2)
        col = num % 2

        widget = QWidget(self.param_widget)
        layout = QHBoxLayout(widget)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.param_layout.addWidget(widget, row, col)
        label = HoverLabel("{}:".format(label_name), self.parent_widget, self.parent_widget.statusBar())
        label.setHoverMessage(description)
        layout.addWidget(label)

        layout.addStretch()

        checkbox = HoverCheckBox("", self.parent_widget, self.parent_widget.statusBar())
        checkbox.setHoverMessage(description)
        checkbox.setChecked(self.controller.params()[name])
        widget.setContentsMargins(0, 0, 5, 0)
        checkbox.clicked.connect(
            lambda: clicked(checkbox.isChecked(), checkbox=checkbox, related_params=related_params))
        layout.addWidget(checkbox)

        self.param_widgets[name] = widget
        self.param_checkboxes[name] = checkbox

    def add_param_chooser(self, label_name, name, options, callback, num, description=None):
        row = np.floor(num / 2)
        col = num % 2

        widget = QWidget(self.param_widget)
        layout = QHBoxLayout(widget)
        self.param_layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        self.param_layout.addWidget(widget, row, col)
        label = HoverLabel("{}:".format(label_name), self.parent_widget, self.parent_widget.statusBar())
        label.setHoverMessage(description)
        layout.addWidget(label)

        layout.addStretch()

        combobox = QComboBox()
        combobox.addItems(options)
        combobox.currentIndexChanged.connect(callback)
        layout.addWidget(combobox)

        self.param_widgets[name] = widget
        self.param_choosers[name] = combobox

    def update_textbox_from_slider(self, slider, textbox, multiplier=1, int_values=False):
        if int_values:
            textbox.setText(str(int(slider.sliderPosition() / multiplier)))
        else:
            textbox.setText(str(slider.sliderPosition() / multiplier))

    def update_slider_from_textbox(self, slider, textbox, multiplier=1, int_values=False):
        try:
            if int_values:
                value = int(float(textbox.text()))
            else:
                value = float(textbox.text())

            slider.setValue(value * multiplier)
            textbox.setText(str(value))
        except:
            pass

    def update_param_slider_and_textbox(self, param, value, multiplier=1, int_values=False):
        try:
            slider = self.param_sliders[param]
            textbox = self.param_textboxes[param]

            if int_values:
                value = int(value)

            slider.setValue(value * multiplier)
            textbox.setText(str(value))
        except:
            pass

    def update_param(self, param, int_values=False):
        value = self.param_sliders[param].sliderPosition() / float(self.param_slider_multipliers[param])

        if int_values:
            value = int(value)

        self.controller.update_param(param, value)


class MainParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Preview Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Gamma", name="gamma", minimum=1, maximum=500,
                              value=self.controller.gui_params['gamma'] * 100, moved=self.preview_gamma, num=0,
                              multiplier=100, released=self.update_param, description="Gamma of the video preview.")
        self.add_param_slider(label_name="Contrast", name="contrast", minimum=1, maximum=500,
                              value=self.controller.gui_params['contrast'] * 100, moved=self.preview_contrast, num=1,
                              multiplier=100, released=self.update_param, description="Contrast of the video preview.")
        self.add_param_slider(label_name="FPS", name="fps", minimum=1, maximum=60,
                              value=self.controller.gui_params['fps'], moved=self.update_param, num=2,
                              released=self.update_param, description="Frames per second of the video preview.",
                              int_values=True)
        self.add_param_slider(label_name="Z", name="z", minimum=0, maximum=0, value=self.controller.z,
                              moved=self.update_param, num=3, released=self.update_param,
                              description="Z plane of the video preview.", int_values=True)

        self.setFixedHeight(120)

    def preview_contrast(self):
        contrast = self.param_sliders["contrast"].sliderPosition() / float(self.param_slider_multipliers["contrast"])

        self.controller.preview_contrast(contrast)

    def preview_gamma(self):
        gamma = self.param_sliders["gamma"].sliderPosition() / float(self.param_slider_multipliers["gamma"])

        self.controller.preview_gamma(gamma)


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


class CNMFROIFindingWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "CNMF Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Autoregressive Model Order", name="autoregressive_order", minimum=0,
                              maximum=2, value=self.controller.params()['autoregressive_order'],
                              moved=self.update_param, num=0, multiplier=1, pressed=self.update_param,
                              released=self.update_param, description="Order of the autoregressive model (0, 1 or 2).",
                              int_values=True)
        self.add_param_slider(label_name="Background Components", name="num_bg_components", minimum=1, maximum=100,
                              value=self.controller.params()['num_bg_components'], moved=self.update_param, num=1,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Number of background components.", int_values=True)
        self.add_param_slider(label_name="Merge Threshold", name="merge_threshold", minimum=1, maximum=200,
                              value=self.controller.params()['merge_threshold'] * 200, moved=self.update_param, num=2,
                              multiplier=200, pressed=self.update_param, released=self.update_param,
                              description="Merging threshold (maximum correlation allowed before merging two components).",
                              int_values=False)
        self.add_param_slider(label_name="Components", name="num_components", minimum=1, maximum=5000,
                              value=self.controller.params()['num_components'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Number of components expected (if using patches, in each patch; otherwise, in the entire FOV).",
                              int_values=True)
        self.add_param_slider(label_name="HALS Iterations", name="hals_iter", minimum=1, maximum=100,
                              value=self.controller.params()['hals_iter'], moved=self.update_param, num=4, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Number of HALS iterations following initialization (default: 5).",
                              int_values=True)
        self.add_param_checkbox(label_name="Use Patches", name="use_patches", clicked=self.toggle_use_patches,
                                description="Whether to use patches when performing CNMF.", num=5,
                                related_params=['cnmf_patch_size', 'cnmf_patch_stride'])
        self.add_param_slider(label_name="Patch Size", name="cnmf_patch_size", minimum=1, maximum=100,
                              value=self.controller.params()['cnmf_patch_size'], moved=self.update_param, num=6,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Size of each patch (pixels).", int_values=True)
        self.add_param_slider(label_name="Patch Stride", name="cnmf_patch_stride", minimum=1, maximum=100,
                              value=self.controller.params()['cnmf_patch_stride'], moved=self.update_param, num=7,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Stride for each patch (pixels).", int_values=True)
        self.add_param_slider(label_name="Max Merge Area", name="max_merge_area", minimum=1, maximum=500,
                              value=self.controller.params()['max_merge_area'], moved=self.update_param, num=8,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum area of merged ROI above which ROIs will not be merged (pixels).",
                              int_values=True)
        self.add_param_chooser(label_name="Initialization Method", name="init_method",
                               options=["Greedy ROI", "Sparse NMF", "PCA/ICA", "Graph NMF"],
                               callback=self.set_init_method, num=9,
                               description="Method to use to initialize ROI locations.")

        self.greedy_roi_param_widget = GreedyROIParamWidget(self.parent_widget, self.controller)
        self.sparse_nmf_param_widget = SparseNMFParamWidget(self.parent_widget, self.controller)
        self.pca_ica_param_widget = PCAICAParamWidget(self.parent_widget, self.controller)
        self.graph_nmf_param_widget = GraphNMFParamWidget(self.parent_widget, self.controller)
        self.main_layout.addWidget(self.greedy_roi_param_widget)
        self.main_layout.addWidget(self.sparse_nmf_param_widget)
        self.main_layout.addWidget(self.pca_ica_param_widget)
        self.main_layout.addWidget(self.graph_nmf_param_widget)

        self.init_param_widgets = [self.greedy_roi_param_widget, self.sparse_nmf_param_widget,
                                   self.pca_ica_param_widget, self.graph_nmf_param_widget]

        self.show_selected_init_method_params()

        self.main_layout.addStretch()

    def tab_selected(self):
        index = self.tab_widget.currentIndex()
        if index == 0:
            self.set_init_method("greedy_roi")

    def toggle_use_patches(self, boolean, checkbox, related_params=[]):
        self.controller.params()['use_patches'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())

    def toggle_use_hals(self, boolean, checkbox, related_params=[]):
        self.controller.params()['use_hals'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())

    def set_init_method(self, i):
        methods = ['greedy_roi', 'sparse_nmf', 'pca_ica', 'graph_nmf']

        self.controller.params()['init_method'] = methods[i]

        self.show_selected_init_method_params()

    def show_selected_init_method_params(self):
        i = self.param_choosers['init_method'].currentIndex()
        print(i)
        for j in range(len(self.init_param_widgets)):
            if i == j:
                self.init_param_widgets[j].show()
            else:
                self.init_param_widgets[j].hide()


class GreedyROIParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Greedy ROI Initialization Parameters")

        self.controller = controller

        self.add_param_checkbox(label_name="Rolling Max", name="rolling_max", clicked=self.toggle_rolling_max,
                                description="Detect new components based on a rolling sum of pixel activity (default: True).",
                                num=0, related_params=['rolling_length'])
        self.add_param_slider(label_name="Rolling Length", name="rolling_length", minimum=1, maximum=200,
                              value=self.controller.params()['rolling_length'], moved=self.update_param, num=1,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Length of rolling window (default: 100).", int_values=True)
        self.add_param_slider(label_name="Num Iterations", name="n_iter", minimum=1, maximum=100,
                              value=self.controller.params()['n_iter'], moved=self.update_param, num=2, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Number of iterations when refining estimates (default: 5).", int_values=True)
        self.add_param_slider(label_name="Neuron Half-Size", name="half_size", minimum=1, maximum=50,
                              value=self.controller.params()['half_size'], moved=self.update_param, num=3, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Expected half-size of neurons (pixels).", int_values=True)

        self.main_layout.addStretch()

    def toggle_rolling_max(self, boolean, checkbox, related_params=[]):
        self.controller.params()['rolling_max'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())


class SparseNMFParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Sparse NMF Initialization Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Alpha", name="alpha_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['alpha_snmf'], moved=self.update_param, num=0,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Weight of the sparsity regularization (default: 100).", int_values=True)
        self.add_param_slider(label_name="Sigma Smooth", name="sigma_smooth_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['sigma_smooth_snmf'] * 100, moved=self.update_param, num=1,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Smoothing along z,x, and y (default: 0.5).", int_values=False)
        self.add_param_slider(label_name="Max Iterations", name="max_iter_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['max_iter_snmf'], moved=self.update_param, num=2,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum SNMF iterations (default: 500).", int_values=True)
        self.add_param_slider(label_name="Percent Baseline", name="perc_baseline_snmf", minimum=1, maximum=100,
                              value=self.controller.params()['perc_baseline_snmf'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Percentile to remove from movie before NMF (default: 20).", int_values=True)

        self.main_layout.addStretch()


class PCAICAParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "PCA/ICA Initialization Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Sigma Smooth", name="sigma_smooth_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['sigma_smooth_snmf'] * 100, moved=self.update_param, num=1,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Smoothing along z,x, and y (default: 0.5).", int_values=False)
        self.add_param_slider(label_name="Max Iterations", name="max_iter_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['max_iter_snmf'], moved=self.update_param, num=2,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum SNMF iterations (default: 500).", int_values=True)
        self.add_param_slider(label_name="Percent Baseline", name="perc_baseline_snmf", minimum=1, maximum=100,
                              value=self.controller.params()['perc_baseline_snmf'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Percentile to remove from movie before NMF (default: 20).", int_values=True)

        self.main_layout.addStretch()


class GraphNMFParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Graph NMF Initialization Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Lambda", name="lambda_gnmf", minimum=1, maximum=100,
                              value=self.controller.params()['alpha_snmf'] * 10, moved=self.update_param, num=0,
                              multiplier=10, pressed=self.update_param, released=self.update_param,
                              description="Regularization weight for graph NMF (default: 1).", int_values=False)
        self.add_param_slider(label_name="Sigma Smooth", name="sigma_smooth_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['sigma_smooth_snmf'] * 100, moved=self.update_param, num=1,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Smoothing along z,x, and y (default: 0.5).", int_values=False)
        self.add_param_slider(label_name="Max Iterations", name="max_iter_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['max_iter_snmf'], moved=self.update_param, num=2,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum SNMF iterations (default: 500).", int_values=True)
        self.add_param_slider(label_name="Percent Baseline", name="perc_baseline_snmf", minimum=1, maximum=100,
                              value=self.controller.params()['perc_baseline_snmf'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Percentile to remove from movie before NMF (default: 20).", int_values=True)
        self.add_param_checkbox(label_name="SC Normalize", name="sc_normalize", clicked=self.toggle_sc_normalize,
                                description="Standardize entries prior to computing affinity matrix (default: True).",
                                num=4, related_params=[])
        self.add_param_checkbox(label_name="SC Use NN", name="sc_use_nn", clicked=self.toggle_sc_use_nn,
                                description="Sparsify affinity matrix by using only nearest neighbors (default: True).",
                                num=5, related_params=[])
        self.add_param_slider(label_name="SC Threshold", name="sc_threshold", minimum=0, maximum=1000,
                              value=self.controller.params()['sc_threshold'] * 100, moved=self.update_param, num=6,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Threshold for affinity matrix (default: 0).", int_values=False)
        self.add_param_slider(label_name="SC Sigma", name="sc_sigma", minimum=1, maximum=1000,
                              value=self.controller.params()['sc_sigma'] * 100, moved=self.update_param, num=7,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Standard deviation for SC kernel (default: 1).", int_values=False)

        self.main_layout.addStretch()

    def toggle_sc_normalize(self, boolean, checkbox, related_params=[]):
        self.controller.params()['sc_normalize'] = boolean

    def toggle_sc_use_nn(self, boolean, checkbox, related_params=[]):
        self.controller.params()['sc_use_nn'] = boolean


class Suite2pROIFindingWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Suite2p Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Diameter", name="diameter", minimum=1, maximum=100,
                              value=self.controller.params()['diameter'], moved=self.update_param, num=0, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Sampling Rate", name="sampling_rate", minimum=1, maximum=60,
                              value=self.controller.params()['sampling_rate'], moved=self.update_param, num=1,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_checkbox(label_name="Connected", name="connected", clicked=self.toggle_connected,
                                description="Whether to use a convolutional neural network for determining which ROIs are neurons.",
                                num=2)
        self.add_param_slider(label_name="Neuropil Basis Ratio", name="neuropil_basis_ratio", minimum=1, maximum=20,
                              value=self.controller.params()['neuropil_basis_ratio'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Neuropil Radius Ratio", name="neuropil_radius_ratio", minimum=1, maximum=50,
                              value=self.controller.params()['neuropil_radius_ratio'], moved=self.update_param, num=4,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Inner Neropil Radius", name="inner_neuropil_radius", minimum=1, maximum=50,
                              value=self.controller.params()['inner_neuropil_radius'], moved=self.update_param, num=5,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Min. Neuropil Pixels", name="min_neuropil_pixels", minimum=1, maximum=500,
                              value=self.controller.params()['min_neuropil_pixels'], moved=self.update_param, num=6,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)

        self.main_layout.addStretch()

    def toggle_connected(self, boolean):
        self.controller.params()['connected'] = boolean


class ROIFilteringWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "ROI Filtering Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Imaging FPS", name="imaging_fps", minimum=1, maximum=100,
                              value=self.controller.params()['imaging_fps'], moved=self.update_param, num=0,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Imaging frame rate (frames per second).", int_values=True)
        self.add_param_slider(label_name="Decay Time", name="decay_time", minimum=1, maximum=100,
                              value=self.controller.params()['decay_time'] * 100, moved=self.update_param, num=1,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Length of a typical calcium transient (seconds).", int_values=False)
        self.add_param_slider(label_name="Minimum SNR", name="min_snr", minimum=1, maximum=500,
                              value=self.controller.params()['min_snr'] * 100, moved=self.update_param, num=2,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Minimum signal to noise ratio.", int_values=False)
        self.add_param_slider(label_name="Minimum Spatial Correlation", name="min_spatial_corr", minimum=1, maximum=100,
                              value=self.controller.params()['min_spatial_corr'] * 100, moved=self.update_param, num=3,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Minimum spatial correlation.", int_values=False)
        self.add_param_checkbox(label_name="Use CNN", name="use_cnn", clicked=self.toggle_use_cnn,
                                description="Whether to use a convolutional neural network for determining which ROIs are neurons.",
                                num=4, related_params=['cnn_accept_threshold', 'cnn_reject_threshold'])
        self.add_param_slider(label_name="CNN Accept Threshold", name="cnn_accept_threshold", minimum=1, maximum=100,
                              value=self.controller.params()['cnn_accept_threshold'] * 100, moved=self.update_param,
                              num=5, multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Minimum CNN confidence above which an ROI will automatically be accepted.",
                              int_values=False)
        self.add_param_slider(label_name="CNN Reject Threshold", name="cnn_reject_threshold", minimum=1, maximum=100,
                              value=self.controller.params()['cnn_reject_threshold'] * 100, moved=self.update_param,
                              num=6, multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Minimum CNN confidence below which an ROI will automatically be rejected.",
                              int_values=False)
        self.add_param_slider(label_name="Minimum Area", name="min_area", minimum=1, maximum=1000,
                              value=self.controller.params()['min_area'], moved=self.update_param, num=7, multiplier=1,
                              pressed=self.update_param, released=self.update_param, description="Minimum area.",
                              int_values=True)
        self.add_param_slider(label_name="Maximum Area", name="max_area", minimum=1, maximum=1000,
                              value=self.controller.params()['max_area'], moved=self.update_param, num=8, multiplier=1,
                              pressed=self.update_param, released=self.update_param, description="Maximum area.",
                              int_values=True)
        self.add_param_slider(label_name="Motion Artifact Max Decay Speed", name="artifact_decay_speed", minimum=0,
                              maximum=10, value=self.controller.params()['imaging_fps'], moved=self.update_param, num=9,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum decay speed of z-scored traces above which ROIs will be determined to be motion artifacts.",
                              int_values=False)
        self.add_param_slider(label_name="Minimum DF/F", name="min_df_f", minimum=0, maximum=100,
                              value=self.controller.params()['min_df_f'], moved=self.update_param, num=10, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Minimum DF/F below which ROIs will be discarded.", int_values=False)

        self.main_layout.addStretch()

        self.roi_button_widget = QWidget(self)
        self.roi_button_layout = QHBoxLayout(self.roi_button_widget)
        self.roi_button_layout.setContentsMargins(5, 0, 0, 0)
        self.roi_button_layout.setSpacing(5)
        self.main_layout.addWidget(self.roi_button_widget)

        label = QLabel("Selected ROIs")
        label.setFont(subheading_font)
        self.roi_button_layout.addWidget(label)

        self.roi_button_layout.addStretch()

        self.discard_selected_roi_button = HoverButton('Discard', self.parent_widget, self.parent_widget.statusBar())
        self.discard_selected_roi_button.setHoverMessage("Discard the selected ROIs.")
        self.discard_selected_roi_button.setIcon(QIcon("../icons/discard_icon.png"))
        self.discard_selected_roi_button.setIconSize(QSize(16, 16))
        self.discard_selected_roi_button.clicked.connect(self.controller.discard_selected_rois)
        self.discard_selected_roi_button.setEnabled(False)
        self.roi_button_layout.addWidget(self.discard_selected_roi_button)

        self.keep_selected_roi_button = HoverButton('Keep', self.parent_widget, self.parent_widget.statusBar())
        self.keep_selected_roi_button.setHoverMessage("Keep the selected ROIs.")
        self.keep_selected_roi_button.setIcon(QIcon("../icons/keep_icon.png"))
        self.keep_selected_roi_button.setIconSize(QSize(16, 16))
        self.keep_selected_roi_button.clicked.connect(self.controller.keep_selected_rois)
        self.keep_selected_roi_button.setEnabled(False)
        self.roi_button_layout.addWidget(self.keep_selected_roi_button)

        self.merge_rois_button = HoverButton('Merge', self.parent_widget, self.parent_widget.statusBar())
        self.merge_rois_button.setHoverMessage("Merge the selected ROIs.")
        self.merge_rois_button.setIcon(QIcon("../icons/merge_icon.png"))
        self.merge_rois_button.setIconSize(QSize(20, 16))
        self.merge_rois_button.clicked.connect(self.controller.merge_selected_rois)
        self.roi_button_layout.addWidget(self.merge_rois_button)
        self.merge_rois_button.setEnabled(False)

        self.roi_button_widget_2 = QWidget(self)
        self.roi_button_layout_2 = QHBoxLayout(self.roi_button_widget_2)
        self.roi_button_layout_2.setContentsMargins(5, 0, 0, 0)
        self.roi_button_layout_2.setSpacing(5)
        self.main_layout.addWidget(self.roi_button_widget_2)

        self.train_cnn_button = HoverButton('CNN Training...', self.parent_widget, self.parent_widget.statusBar())
        self.train_cnn_button.setHoverMessage("Label ROIs to add to the CNN dataset, and edit the existing dataset.")
        self.train_cnn_button.setIcon(QIcon("../icons/cnn_icon.png"))
        self.train_cnn_button.setIconSize(QSize(16, 16))
        self.train_cnn_button.clicked.connect(self.controller.pick_data_to_train_cnn)
        self.roi_button_layout_2.addWidget(self.train_cnn_button)

        self.roi_button_layout_2.addStretch()

        self.discard_all_rois_button = HoverButton('Discard All', self.parent_widget, self.parent_widget.statusBar())
        self.discard_all_rois_button.setHoverMessage("Discard all ROIs.")
        self.discard_all_rois_button.setIcon(QIcon("../icons/discard_icon.png"))
        self.discard_all_rois_button.setIconSize(QSize(16, 16))
        self.discard_all_rois_button.clicked.connect(self.controller.discard_all_rois)
        self.roi_button_layout_2.addWidget(self.discard_all_rois_button)

        self.keep_all_rois_button = HoverButton('Keep All', self.parent_widget, self.parent_widget.statusBar())
        self.keep_all_rois_button.setHoverMessage("Keep all ROIs.")
        self.keep_all_rois_button.setIcon(QIcon("../icons/keep_icon.png"))
        self.keep_all_rois_button.setIconSize(QSize(16, 16))
        self.keep_all_rois_button.clicked.connect(self.controller.keep_all_rois)
        self.roi_button_layout_2.addWidget(self.keep_all_rois_button)

        self.button_widget = QWidget(self)
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setSpacing(15)
        self.main_layout.addWidget(self.button_widget)

        self.show_zscore_checkbox = QCheckBox("Show Z-Score")
        self.show_zscore_checkbox.setObjectName("Show Z-Score")
        self.show_zscore_checkbox.setChecked(True)
        self.show_zscore_checkbox.clicked.connect(self.toggle_show_zscore)
        self.button_layout.addWidget(self.show_zscore_checkbox)

        self.button_layout.addStretch()

        self.filter_rois_button = HoverButton('Filter ROIs', self.parent_widget, self.parent_widget.statusBar())
        self.filter_rois_button.setHoverMessage("Automatically filter ROIs with the current parameters.")
        self.filter_rois_button.setIcon(QIcon("../icons/action_icon.png"))
        self.filter_rois_button.setIconSize(QSize(13, 16))
        self.filter_rois_button.setStyleSheet('font-weight: bold;')
        self.filter_rois_button.clicked.connect(self.controller.filter_rois)
        self.button_layout.addWidget(self.filter_rois_button)

        self.save_rois_button = HoverButton('Save...', self.parent_widget, self.parent_widget.statusBar())
        self.save_rois_button.setHoverMessage("Save traces, ROI centroids and other ROI data.")
        self.save_rois_button.setIcon(QIcon("../icons/save_icon.png"))
        self.save_rois_button.setIconSize(QSize(16, 16))
        self.save_rois_button.setStyleSheet('font-weight: bold;')
        self.save_rois_button.clicked.connect(self.controller.save_all_rois)
        self.button_layout.addWidget(self.save_rois_button)

        self.toggle_use_cnn(self.controller.params()['use_cnn'], self.param_checkboxes['use_cnn'],
                            related_params=['cnn_accept_threshold', 'cnn_reject_threshold'])

    def toggle_show_zscore(self):
        show_zscore = self.show_zscore_checkbox.isChecked()

        self.parent_widget.set_show_zscore(show_zscore)

    def toggle_use_cnn(self, boolean, checkbox, related_params=[]):
        self.controller.params()['use_cnn'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())


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


class HoverCheckBox(QCheckBox):
    def __init__(self, text, parent=None, status_bar=None):
        QCheckBox.__init__(self, text, parent)
        self.setMouseTracking(True)

        self.parent = parent
        self.status_bar = status_bar
        self.hover_message = ""

    def setHoverMessage(self, message):
        self.hover_message = message

    def enterEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.hover_message)

    def leaveEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.parent.default_statusbar_message)


class HoverButton(QPushButton):
    def __init__(self, text, parent=None, status_bar=None):
        QPushButton.__init__(self, text, parent)
        self.setMouseTracking(True)

        self.parent = parent
        self.status_bar = status_bar
        self.hover_message = ""

    def setHoverMessage(self, message):
        self.hover_message = message

    def enterEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.hover_message)

    def leaveEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.parent.default_statusbar_message)


class HoverLabel(QLabel):
    def __init__(self, text, parent=None, status_bar=None):
        QLabel.__init__(self, text, parent)
        self.setMouseTracking(True)

        self.parent = parent
        self.status_bar = status_bar
        self.hover_message = ""

    def setHoverMessage(self, message):
        self.hover_message = message

    def enterEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.hover_message)

    def leaveEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.parent.default_statusbar_message)


def HLine():
    frame = QFrame()
    frame.setFrameShape(QFrame.HLine)
    frame.setFrameShadow(QFrame.Plain)

    return frame
