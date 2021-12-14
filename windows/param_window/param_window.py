from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import numpy as np

from windows.param_window.hover_button import HoverButton
from windows.param_window.main_param_widget import MainParamWidget
from windows.param_window.motion_correction_widget import MotionCorrectionWidget
from windows.param_window.regressor_analysis_widget import RegressorAnalysisWidget
from windows.param_window.roi_filtering_widget import ROIFilteringWidget
from windows.param_window.roi_finding_widget import ROIFindingWidget
from windows.param_window.video_loading_widget import VideoLoadingWidget

try:
    import suite2p

    suite2p_available = True
except:
    suite2p_available = False

showing_video_color = QColor(151, 66, 252, 20)

SHOW_VIDEO_BUTTON_DISABLED_STYLESHEET = "QPushButton{border: none; background-size: contain; background-image:url(icons/play_icon_disabled.png);} QPushButton:hover{background-image:url(icons/play_icon.png);}"
SHOW_VIDEO_BUTTON_ENABLED_STYLESHEET = "QPushButton{border: none; background-size: contain; background-image:url(icons/play_icon_enabled.png);} QPushButton:hover{background-image:url(icons/play_icon_enabled.png);}"




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

        self.group_font = QFont()
        self.group_font.setBold(True)

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
                       self.videos_list.item(i).font() != self.group_font]

        print(video_paths)

        if len(video_paths) != len(video_items):
            raise ValueError(
                "Attempted to change the paths in the video list, but {} paths were provided, while {} videos are loaded.".format(
                    len(video_paths), len(video_items)))

        video_num = 0

        for i in range(self.videos_list.count()):
            item = self.videos_list.item(i)

            if item.font() != self.group_font:

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
        if item.font() != self.group_font:
            self.update_video_list_items()
        else:
            groups = []
            old_indices = []

            group_num = -1

            for i in range(self.videos_list.count()):
                item = self.videos_list.item(i)

                if item.font() == self.group_font:
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
        item.setFont(self.group_font)
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

            if item.font() != self.group_font:
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
            if selected_items[0].font() == self.group_font:
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
            if selected_items[0].font() != self.group_font:
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


def HLine():
    frame = QFrame()
    frame.setFrameShape(QFrame.HLine)
    frame.setFrameShadow(QFrame.Plain)

    return frame
