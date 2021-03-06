import numpy as np
import cv2
import pyqtgraph as pg
from matplotlib import cm

from controller import utilities

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

n_colors = 20
cmap = utilities.get_cmap(n_colors)

colormaps  = ["inferno", "plasma", "viridis", "magma", "Reds", "Greens", "Blues", "Greys", "gray", "hot"]

ROUNDED_STYLESHEET   = "QLineEdit { background-color: rgba(255, 255, 255, 0.3); border-radius: 2px; border: 1px solid rgba(0, 0, 0, 0.5); padding: 2px; color: white; };"
STATUSBAR_STYLESHEET = "background-color: rgba(50, 50, 50, 1); border-top: 1px solid rgba(0, 0, 0, 1); font-size: 12px; font-style: italic; color: white;"
TOP_LABEL_STYLESHEET = "QLabel{color: white; font-weight: bold; font-size: 14px;}"

class PreviewWindow(QMainWindow):
    def __init__(self, controller):
        QMainWindow.__init__(self)

        # set controller
        self.controller = controller

        # get parameter window position & size
        param_window_x      = self.controller.param_window.x()
        param_window_y      = self.controller.param_window.y()
        param_window_width  = self.controller.param_window.width()

        # set position & size
        self.setGeometry(param_window_x + param_window_width + 32, param_window_y + 32, 10, 10)

        # create main widget
        self.main_widget = QWidget(self)
        self.main_widget.setMinimumSize(QSize(800, 700))
        self.resize(800, 1000)

        # create main layout
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # set background and foreground colors
        bg_color = (20, 20, 20)
        fg_color = (150, 150, 150)
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(bg_color[0], bg_color[1], bg_color[2], 255))
        self.main_widget.setAutoFillBackground(True)
        self.main_widget.setPalette(palette)
        pg.setConfigOption('background', bg_color)
        pg.setConfigOption('foreground', fg_color)

        # create top widget
        self.top_widget = QWidget()
        self.top_widget.setFixedHeight(35)
        self.top_layout = QHBoxLayout(self.top_widget)
        self.top_layout.setContentsMargins(20, 10, 20, 0)
        self.main_layout.addWidget(self.top_widget)

        # create left label
        self.left_label = QLabel("Kept ROIs ???")
        self.left_label.setStyleSheet(TOP_LABEL_STYLESHEET)
        self.top_layout.addWidget(self.left_label)

        self.top_layout.addStretch()

        # create right label
        self.right_label = QLabel("??? Discarded ROIs")
        self.right_label.setStyleSheet(TOP_LABEL_STYLESHEET)
        self.top_layout.addWidget(self.right_label)

        # create PyQTGraph widget
        self.pg_widget = pg.GraphicsLayoutWidget()
        self.pg_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.pg_widget.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.main_layout.addWidget(self.pg_widget)

        # create left and right image viewboxes
        self.left_image_viewbox  = self.pg_widget.addViewBox(lockAspect=True, name='left_image', border=None, row=0,col=0, invertY=True)
        self.right_image_viewbox = self.pg_widget.addViewBox(lockAspect=True, name='right_image', border=None, row=0,col=1, invertY=True)
        self.left_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.right_image_viewbox.setLimits(minXRange=10, minYRange=10, maxXRange=2000, maxYRange=2000)
        self.left_image_viewbox.setBackgroundColor(bg_color)
        self.right_image_viewbox.setBackgroundColor(bg_color)
        self.right_image_viewbox.setXLink('left_image')
        self.right_image_viewbox.setYLink('left_image')
        self.left_image_viewbox.setMenuEnabled(False)
        self.right_image_viewbox.setMenuEnabled(False)

        # create left and right image and overlay items
        self.left_image          = pg.ImageItem()
        self.left_image_overlay  = pg.ImageItem()
        self.right_image         = pg.ImageItem()
        self.right_image_overlay = pg.ImageItem()
        self.left_image_viewbox.addItem(self.left_image)
        self.left_image_viewbox.addItem(self.left_image_overlay)
        self.right_image_viewbox.addItem(self.right_image)
        self.right_image_viewbox.addItem(self.right_image_overlay)

        self.left_image.scene().sigMouseMoved.connect(self.update_secondary)

        # create selected ROI trace viewbox
        self.roi_trace_viewbox = self.pg_widget.addPlot(name='roi_trace', row=1, col=0, colspan=2)
        self.roi_trace_viewbox.setLabel('bottom', "Frame #")
        self.roi_trace_viewbox.showButtons()
        self.roi_trace_viewbox.setMouseEnabled(x=True,y=False)
        if self.controller.show_zscore:
            self.roi_trace_viewbox.setYRange(-2, 3)
            self.roi_trace_viewbox.setLabel('left', "Z-Score")
        else:
            self.roi_trace_viewbox.setYRange(0, 1)
            self.roi_trace_viewbox.setLabel('left', "Fluorescence")

        # create kept ROI traces viewbox
        self.kept_traces_viewbox = self.pg_widget.addPlot(name='heatmap_plot', row=2, col=0, colspan=2)
        self.kept_traces_viewbox.setLabel('bottom', "Frame #")
        self.kept_traces_viewbox.setLabel('left', "ROI #")
        self.kept_traces_viewbox.setMouseEnabled(x=True,y=False)
        self.kept_traces_viewbox.setXLink('roi_trace')

        # create kept ROI traces item
        self.kept_traces_image = pg.ImageItem()
        self.kept_traces_viewbox.addItem(self.kept_traces_image)

        # set kept ROI traces colormap
        colormap = cm.get_cmap("inferno")
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)
        self.kept_traces_image.setLookupTable(lut)

        # create tail angle viewbox
        self.tail_angle_viewbox = self.pg_widget.addPlot(name='tail_angle_plot', row=3, col=0, colspan=2)
        self.tail_angle_viewbox.setLabel('bottom', "Frame #")
        self.tail_angle_viewbox.setLabel('left', "Tail Angle (??)")
        self.tail_angle_viewbox.setMouseEnabled(x=True,y=False)
        self.tail_angle_viewbox.setXLink('roi_trace')

        # register a callback function for when the PyQTGraph widget is clicked
        self.pg_widget.scene().sigMouseClicked.connect(self.plot_clicked)

        # set stretch factors for each row
        self.pg_widget.ci.layout.setRowStretchFactor(0, 32)
        self.pg_widget.ci.layout.setRowStretchFactor(1, 8)
        self.pg_widget.ci.layout.setRowStretchFactor(2, 8)
        self.pg_widget.ci.layout.setRowStretchFactor(3, 8)

        # create current frame line items
        self.current_frame_line_1 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(color=(255, 255, 0, 100), width=5))
        self.current_frame_line_2 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(color=(255, 255, 0, 100), width=5))
        self.current_frame_line_3 = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(color=(255, 255, 0, 100), width=5))
        self.roi_trace_viewbox.addItem(self.current_frame_line_1)
        self.kept_traces_viewbox.addItem(self.current_frame_line_2)
        self.tail_angle_viewbox.addItem(self.current_frame_line_3)

        # create bottom widget
        self.bottom_widget = QWidget()
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.main_layout.addWidget(self.bottom_widget)

        # create checkbox to show/hide ROIs
        self.show_rois_checkbox = HoverCheckBox("Show ROIs", self, self.statusBar())
        self.show_rois_checkbox.setHoverMessage("Toggle showing ROIs.")
        self.show_rois_checkbox.setObjectName("Show ROIs")
        self.show_rois_checkbox.setStyleSheet("color: rgba(150, 150, 150, 1);")
        self.show_rois_checkbox.setChecked(False)
        self.show_rois_checkbox.setEnabled(False)
        self.show_rois_checkbox.clicked.connect(self.toggle_show_rois)
        self.bottom_layout.addWidget(self.show_rois_checkbox)

        # create checkbox to toggle video playback
        self.play_video_checkbox = HoverCheckBox("Play Video", self, self.statusBar())
        self.play_video_checkbox.setHoverMessage("Play the video (if unchecked, the mean image will be shown).")
        self.play_video_checkbox.setObjectName("Play Video")
        self.play_video_checkbox.setStyleSheet("color: rgba(150, 150, 150, 1);")
        self.play_video_checkbox.setChecked(True)
        self.show_rois_checkbox.setEnabled(False)
        self.play_video_checkbox.clicked.connect(self.toggle_play_video)
        self.bottom_layout.addWidget(self.play_video_checkbox)

        self.bottom_layout.addStretch()

        # create textbox to add a frame offset to calcium imaging data
        label = HoverLabel("Frame Offset:")
        label.setHoverMessage("Set number of frames to offset the calcium imaging data from tail angle data (for previewing only).")
        label.setStyleSheet("color: rgba(150, 150, 150, 1);")
        self.bottom_layout.addWidget(label)

        self.frame_offset_textbox = QLineEdit("Frame Offset")
        self.frame_offset_textbox.setObjectName("Frame Offset")
        self.frame_offset_textbox.setText("0")
        self.frame_offset_textbox.editingFinished.connect(lambda:self.update_frame_offset())
        self.frame_offset_textbox.setStyleSheet(ROUNDED_STYLESHEET)
        self.bottom_layout.addWidget(self.frame_offset_textbox)

        self.bottom_layout.addStretch()

        # create combobox to change the colormap used to plot kept ROI traces
        label = QLabel("Colormap:")
        label.setStyleSheet("color: rgba(150, 150, 150, 1);")
        self.bottom_layout.addWidget(label)

        combobox = QComboBox()
        combobox.addItems([ colormap.title() for colormap in colormaps ])
        combobox.currentIndexChanged.connect(self.change_colormap)
        self.bottom_layout.addWidget(combobox)

        # set main widget
        self.setCentralWidget(self.main_widget)

        # set window buttons
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowFullscreenButtonHint)

        # create a timer for updating the frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        self.set_initial_state()

        self.item_hovered = False
        self.play_right   = False

        # set up the status bar
        self.statusBar().setStyleSheet(STATUSBAR_STYLESHEET)

        self.show()

    def set_default_statusbar_message(self, message):
        self.default_statusbar_message = message
        self.statusBar().showMessage(self.default_statusbar_message)

    def reset_default_statusbar_message(self):
        self.set_default_statusbar_message("To view a video, click the arrow next to its name.")

    def set_initial_state(self):
        self.kept_rois_image         = None
        self.removed_rois_image      = None
        self.text_items              = []
        self.outline_items           = []
        self.mask_items              = []
        self.temp_mask_item          = None
        self.frame_num               = 0    # current frame #
        self.n_frames                = 1    # total number of frames
        self.video_name              = ""   # name of the currently showing video
        self.mask_points             = []
        self.mask                    = None
        self.selected_rois           = []
        self.roi_temporal_footprints = None

        self.left_image.clear()
        self.left_image_overlay.clear()
        self.right_image.clear()
        self.right_image_overlay.clear()
        self.kept_traces_image.clear()

        self.show_rois_checkbox.setEnabled(False)
        self.pg_widget.hide()
        self.top_widget.hide()
        self.bottom_widget.hide()
        self.timer.stop()
        self.setWindowTitle("Preview")
        self.reset_default_statusbar_message()

    def update_frame_offset(self):
        try:
            self.controller.frame_offset = int(float(self.frame_offset_textbox.text()))

            if self.controller.heatmap is not None:
                self.kept_traces_image.setRect(QRectF(self.controller.frame_offset + self.controller.z/self.controller.video.shape[1], 0, self.controller.heatmap.shape[0], self.controller.heatmap.shape[1]))

            if self.roi_temporal_footprints is not None:
                self.plot_traces(self.roi_temporal_footprints, self.selected_rois)

            self.set_play_video(play_video_bool=self.play_video_checkbox.isChecked())
        except:
            pass

    def toggle_show_rois(self):
        show_rois = self.show_rois_checkbox.isChecked()

        self.set_show_rois(show_rois)

    def toggle_play_video(self):
        play_video_bool = self.play_video_checkbox.isChecked()

        self.set_play_video(play_video_bool)

    def uncheck_play_video(self):
        self.play_video_checkbox.setChecked(False)

        self.set_play_video(False)

    def check_play_video(self):
        self.play_video_checkbox.setChecked(True)

        self.set_play_video(True)

    def set_show_rois(self, show_rois):
        print("Setting show ROIs to {}.".format(show_rois))
        self.controller.set_show_rois(show_rois)

        self.create_text_items()

    def show_plot(self):
        self.pg_widget.show()
        self.bottom_widget.show()
        self.top_widget.show()

    def hide_plot(self):
        self.pg_widget.hide()
        self.bottom_widget.hide()
        self.top_widget.hide()

    def change_colormap(self, i):
        colormap_name = colormaps[i]

        colormap = cm.get_cmap(colormap_name)
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)
        self.kept_traces_image.setLookupTable(lut)

    def plot_tail_angles(self, tail_angles, tail_data_fps, imaging_fps):
        self.tail_angle_viewbox.clear()

        imaging_fps_one_plane = imaging_fps

        if tail_angles is not None:
            one_frame    = (1.0/imaging_fps_one_plane)*tail_data_fps
            total_frames = int(np.floor(one_frame*self.controller.video.shape[0] + self.controller.frame_offset + 1))

            if total_frames < tail_angles.shape[0]:
                x = np.linspace(0, self.controller.video.shape[0]+self.controller.frame_offset+1, total_frames)

                self.tail_angle_viewbox.plot(x, tail_angles[:total_frames], pen=pg.mkPen((255, 255, 0), width=2))

                self.tail_angle_viewbox.addItem(self.current_frame_line_3)

                return True
            else:
                self.tail_angle_viewbox.addItem(self.current_frame_line_3)
                return False
        else:
            self.tail_angle_viewbox.addItem(self.current_frame_line_3)
            return False

    def plot_traces(self, roi_temporal_footprints, selected_rois=[]):
        self.roi_trace_viewbox.clear()
        self.selected_rois = selected_rois
        self.roi_temporal_footprints = roi_temporal_footprints
        if roi_temporal_footprints is not None and len(selected_rois) > 0:
            if self.controller.show_zscore:
                max_value = 1
            else:
                max_value = np.amax(roi_temporal_footprints)

            x = np.arange(roi_temporal_footprints.shape[1]) + self.controller.z/self.controller.video.shape[1] + self.controller.frame_offset
            for i in range(len(selected_rois)):
                roi = selected_rois[i]

                color = cmap(roi % n_colors)[:3]
                color = [255*color[0], 255*color[1], 255*color[2]]

                self.roi_trace_viewbox.plot(x, roi_temporal_footprints[roi]/max_value, pen=pg.mkPen(color, width=2))

        self.roi_trace_viewbox.addItem(self.current_frame_line_1)

    def clear_text_and_outline_items(self):
        # remove all text and outline items from left and right plots
        self.clear_outline_items()
        self.clear_text_items()

    def clear_outline_items(self):
        # remove all outline items from left and right plots
        for i in range(len(self.outline_items)-1, -1, -1):
            outline_item = self.outline_items[i]
            if outline_item in self.left_image_viewbox.addedItems:
                self.left_image_viewbox.removeItem(outline_item)
                del outline_item
            elif outline_item in self.right_image_viewbox.addedItems:
                self.right_image_viewbox.removeItem(outline_item)
                del outline_item

    def clear_text_items(self):
        # remove all text items from left and right plots
        for i in range(len(self.text_items)-1, -1, -1):
            text_item = self.text_items[i]
            if text_item in self.left_image_viewbox.addedItems:
                self.left_image_viewbox.removeItem(text_item)
                del text_item
            elif text_item in self.right_image_viewbox.addedItems:
                self.right_image_viewbox.removeItem(text_item)
                del text_item

    def clear_mask_items(self):
        for i in range(len(self.mask_items)-1, -1, -1):
            mask_item = self.mask_items[i]
            if mask_item in self.left_image_viewbox.addedItems:
                self.left_image_viewbox.removeItem(mask_item)
                del mask_item

        if self.temp_mask_item is not None:
            if self.temp_mask_item in self.left_image_viewbox.addedItems:
                self.left_image_viewbox.removeItem(self.temp_mask_item)
                self.temp_mask_item = None
                self.mask_points = []

    def no_rois_selected(self):
        self.clear_outline_items()

    def single_roi_selected(self, roi):
        self.clear_outline_items()

        if roi not in self.controller.removed_rois():
            image = self.kept_rois_image.copy()
            contours = []
            for i in [roi]:
                contours += self.controller.roi_contours[i]
                x = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 0]) for j in range(len(self.controller.roi_contours[i])) ])
                y = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 1]) for j in range(len(self.controller.roi_contours[i])) ])
                
                color = cmap(i % n_colors)[:3]
                color = [255*color[0], 255*color[1], 255*color[2]]

                # text_item = pg.TextItem("{}".format(i), color=color)
                # text_item.setPos(QPoint(int(y), int(x)))
                # self.text_items.append(text_item)
                # self.left_image_viewbox.addItem(text_item)
                for j in range(len(self.controller.roi_contours[i])):
                    outline_item = pg.PlotDataItem(np.concatenate([self.controller.roi_contours[i][j][:, 0, 1], np.array([self.controller.roi_contours[i][j][0, 0, 1]])]), np.concatenate([self.controller.roi_contours[i][j][:, 0, 0], np.array([self.controller.roi_contours[i][j][0, 0, 0]])]), pen=pg.mkPen(color, width=3))
                    self.outline_items.append(outline_item)
                    self.left_image_viewbox.addItem(outline_item)
        else:
            image = self.removed_rois_image.copy()
            contours = []
            for i in [roi]:
                contours += self.controller.roi_contours[i]
                
                x = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 0]) for j in range(len(self.controller.roi_contours[i])) ])
                y = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 1]) for j in range(len(self.controller.roi_contours[i])) ])
                
                color = cmap(i % n_colors)[:3]
                color = [255*color[0], 255*color[1], 255*color[2]]

                # text_item = pg.TextItem("{}".format(i), color=color)
                # text_item.setPos(QPoint(int(y), int(x)))
                # self.text_items.append(text_item)
                # self.right_image_viewbox.addItem(text_item)
                for j in range(len(self.controller.roi_contours[i])):
                    outline_item = pg.PlotDataItem(np.concatenate([self.controller.roi_contours[i][j][:, 0, 1], np.array([self.controller.roi_contours[i][j][0, 0, 1]])]), np.concatenate([self.controller.roi_contours[i][j][:, 0, 0], np.array([self.controller.roi_contours[i][j][0, 0, 0]])]), pen=pg.mkPen(color, width=3))
                    self.outline_items.append(outline_item)
                    self.right_image_viewbox.addItem(outline_item)

    def update_secondary(self, pos):
        if len(self.controller.secondary_image) > 0:
            pos = self.left_image_viewbox.mapSceneToView(pos)
            if not self.controller.drawing_mask:
                # Plot cursor on secondary image
                self.controller.plot_cursor(pos.x(), pos.y(), self.left_image.height(), self.left_image.width())

    def plot_clicked(self, event):
        # get x-y coordinates of where the user clicked
        items = self.pg_widget.scene().items(event.scenePos())
        if self.left_image in items:
            pos = self.left_image_viewbox.mapSceneToView(event.scenePos())
        elif self.right_image in items:
            pos = self.right_image_viewbox.mapSceneToView(event.scenePos())
        else:
            return
        x = pos.x()
        y = pos.y()

        # check whether the user is holding Ctrl
        ctrl_held = event.modifiers() == Qt.ControlModifier

        # remove all outline items from left and right plots
        self.clear_outline_items()

        if event.button() == 1:
            # left click means selecting/deselecting ROIs or masks
            if not self.controller.drawing_mask:
                self.controller.select_roi((int(y), int(x)), ctrl_held=ctrl_held)

                # don't allow selecting removed & kept ROIs at the same time
                removed_count = 0
                for i in self.controller.selected_rois:
                    if i in self.controller.removed_rois():
                        removed_count += 1
                if removed_count !=0 and removed_count != len(self.controller.selected_rois):
                    self.controller.selected_rois = [self.controller.selected_rois[-1]]

                if len(self.controller.selected_rois) > 0:
                    if self.controller.selected_rois[-1] in self.controller.removed_rois() and self.left_image in items:
                        self.controller.selected_rois = []
                    elif self.controller.selected_rois[-1] not in self.controller.removed_rois() and self.right_image in items:
                        self.controller.selected_rois = []

                if len(self.controller.selected_rois) > 0:
                    roi_to_select = self.controller.selected_rois[0]

                    if self.left_image in items:
                        image = self.kept_rois_image.copy()
                        contours = []
                        for i in self.controller.selected_rois:
                            contours += self.controller.roi_contours[i]
                            x = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 0]) for j in range(len(self.controller.roi_contours[i])) ])
                            y = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 1]) for j in range(len(self.controller.roi_contours[i])) ])
                            
                            color = cmap(i % n_colors)[:3]
                            color = [255*color[0], 255*color[1], 255*color[2]]

                            # text_item = pg.TextItem("{}".format(i), color=color)
                            # text_item.setPos(QPoint(int(y), int(x)))
                            # self.text_items.append(text_item)
                            # self.left_image_viewbox.addItem(text_item)
                            for j in range(len(self.controller.roi_contours[i])):
                                outline_item = pg.PlotDataItem(np.concatenate([self.controller.roi_contours[i][j][:, 0, 1], np.array([self.controller.roi_contours[i][j][0, 0, 1]])]), np.concatenate([self.controller.roi_contours[i][j][:, 0, 0], np.array([self.controller.roi_contours[i][j][0, 0, 0]])]), pen=pg.mkPen(color, width=3))
                                self.outline_items.append(outline_item)
                                self.left_image_viewbox.addItem(outline_item)
                    else:
                        image = self.removed_rois_image.copy()
                        contours = []
                        for i in self.controller.selected_rois:
                            contours += self.controller.roi_contours[i]
                            # print([ self.controller.roi_contours[i][j].shape for j in range(len(self.controller.roi_contours[i])) ])
                            x = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 0]) for j in range(len(self.controller.roi_contours[i])) ])
                            y = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 1]) for j in range(len(self.controller.roi_contours[i])) ])
                            
                            color = cmap(i % n_colors)[:3]
                            color = [255*color[0], 255*color[1], 255*color[2]]

                            # text_item = pg.TextItem("{}".format(i), color=color)
                            # text_item.setPos(QPoint(int(y), int(x)))
                            # self.text_items.append(text_item)
                            # self.right_image_viewbox.addItem(text_item)
                            for j in range(len(self.controller.roi_contours[i])):
                                outline_item = pg.PlotDataItem(np.concatenate([self.controller.roi_contours[i][j][:, 0, 1], np.array([self.controller.roi_contours[i][j][0, 0, 1]])]), np.concatenate([self.controller.roi_contours[i][j][:, 0, 0], np.array([self.controller.roi_contours[i][j][0, 0, 0]])]), pen=pg.mkPen(color, width=3))
                                self.outline_items.append(outline_item)
                                self.right_image_viewbox.addItem(outline_item)
            elif self.left_image in items:
                if ctrl_held:
                    # add mask point
                    self.mask_points.append([x, y])

                    if self.temp_mask_item is not None:
                        self.left_image_viewbox.removeItem(self.temp_mask_item)

                    self.temp_mask_item = self.create_mask_item(self.mask_points, temporary=True)
                    self.left_image_viewbox.addItem(self.temp_mask_item)
                else:
                    # determine which mask was clicked, if any
                    mask_num = -1

                    if self.controller.mask_images is not None:
                        for i in range(len(self.controller.mask_images[self.controller.z])):
                            mask = self.controller.mask_images[self.controller.z][i]

                            if mask[int(y), int(x)] > 0:
                                mask_num = i

                    if mask_num == -1 and len(self.mask_points) >= 3:
                        self.controller.create_mask(self.mask_points)

                        self.mask_points = []

                    self.update_mask_items(selected_mask=mask_num)

        elif event.button() == 2:
            if not self.controller.drawing_mask:
                if self.left_image in items:
                    selected_roi = utilities.get_roi_containing_point(self.controller.roi_spatial_footprints(), (int(y), int(x)), self.controller.adjusted_mean_image.shape)

                    if selected_roi is not None:
                        # self.controller.selected_rois = []
                        if selected_roi not in self.controller.selected_rois:
                            self.controller.selected_rois.append(selected_roi)

                        print("ROIs selected: {}.".format(self.controller.selected_rois))

                        self.controller.discard_selected_rois()
                else:
                    selected_roi = utilities.get_roi_containing_point(self.controller.roi_spatial_footprints(), (int(y), int(x)), self.controller.adjusted_mean_image.shape)

                    if selected_roi is not None:
                        # self.controller.selected_rois = []
                        if selected_roi not in self.controller.selected_rois:
                            self.controller.selected_rois.append(selected_roi)

                        print("ROIs selected: {}.".format(self.controller.selected_rois))

                        self.controller.keep_selected_rois()
            else:
                if not ctrl_held:
                    # determine which mask was clicked, if any
                    mask_num = -1

                    if self.controller.mask_images is not None:
                        for i in range(len(self.controller.mask_images[self.controller.z])):
                            mask = self.controller.mask_images[self.controller.z][i]

                            if mask[int(y), int(x)] > 0:
                                mask_num = i

                        if mask_num >= 0:
                            # delete this maximumsk
                            self.controller.delete_mask(mask_num)

                            self.update_mask_items()

        self.controller.update_selected_rois_plot()

    def create_mask_item(self, mask_points, temporary=False, selected=False):
        if temporary:
            return pg.PlotDataItem([ p[0] for p in mask_points ] + [mask_points[0][0]], [ p[1] for p in mask_points ] + [mask_points[0][1]], symbolSize=5, pen=pg.mkPen((255, 255, 255)), symbolPen=pg.mkPen((255, 255, 255)))
        elif selected:
            return pg.PlotDataItem([ p[0] for p in mask_points ] + [mask_points[0][0]], [ p[1] for p in mask_points ] + [mask_points[0][1]], symbolSize=5, pen=pg.mkPen((0, 255, 0)), symbolPen=pg.mkPen((0, 255, 0)))
        return pg.PlotDataItem([ p[0] for p in mask_points ] + [mask_points[0][0]], [ p[1] for p in mask_points ] + [mask_points[0][1]], symbolSize=5, pen=pg.mkPen((255, 255, 0)), symbolPen=pg.mkPen((255, 255, 0)))

    def set_play_video(self, play_video_bool=True):
        self.timer.stop()

        if play_video_bool:
            self.controller.play_video()
        else:
            self.controller.show_mean_image()

            self.current_frame_line_1.setValue(self.controller.frame_offset)
            self.current_frame_line_2.setValue(self.controller.frame_offset)
            self.current_frame_line_3.setValue(self.controller.frame_offset)

        self.controller.set_play_video(play_video_bool)

    def create_text_items(self):
        self.clear_text_items()

        if self.controller.show_rois:
            if self.controller.roi_spatial_footprints() is not None:
                for i in range(self.controller.roi_spatial_footprints().shape[-1]):
                    x = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 0])-5 for j in range(len(self.controller.roi_contours[i])) ])
                    y = np.amax([ np.amax(self.controller.roi_contours[i][j][:, 0, 1])-5 for j in range(len(self.controller.roi_contours[i])) ])
                    
                    color = cmap(i % n_colors)[:3]
                    color = [255*color[0], 255*color[1], 255*color[2]]

                    text_item = pg.TextItem("{}".format(i), color=color)
                    text_item.setPos(QPoint(int(y), int(x)))
                    self.text_items.append(text_item)

                    if i not in self.controller.removed_rois():
                        self.left_image_viewbox.addItem(text_item)
                    else:
                        self.right_image_viewbox.addItem(text_item)

    def play_video(self):
        self.timer.stop()
        
        self.show_plot()

        # set frame number to 0
        self.frame_num = 0

        # get the number of frames
        self.n_frames = self.controller.adjusted_video.shape[0]

        # start the timer to update the frames
        self.timer.start(int(1000.0/self.controller.gui_params['fps']))

        self.kept_traces_viewbox.setXRange(0, self.controller.adjusted_video.shape[0])

        self.create_text_items()

    def show_mean_image(self):
        self.timer.stop()

        self.show_plot()

        self.update_left_image_plot(self.controller.adjusted_mean_image, roi_spatial_footprints=self.controller.roi_spatial_footprints(), video_dimensions=self.controller.video.shape, removed_rois=self.controller.removed_rois(), selected_rois=self.controller.selected_rois, show_rois=self.controller.show_rois)
        self.update_right_image_plot(self.controller.adjusted_mean_image, roi_spatial_footprints=self.controller.roi_spatial_footprints(), video_dimensions=self.controller.video.shape, removed_rois=self.controller.removed_rois(), selected_rois=self.controller.selected_rois, show_rois=self.controller.show_rois)

        self.create_text_items()

    def set_fps(self, fps):
        # restart the timer with the new fps
        self.timer.stop()
        self.timer.start(int(1000.0/fps))

    def show_frame(self, frame):
        self.update_left_image_plot(frame, roi_spatial_footprints=self.controller.roi_spatial_footprints(), video_dimensions=self.controller.video.shape, removed_rois=self.controller.removed_rois(), selected_rois=self.controller.selected_rois, show_rois=self.controller.show_rois)
        self.update_right_image_plot(frame, roi_spatial_footprints=self.controller.roi_spatial_footprints(), video_dimensions=self.controller.video.shape, removed_rois=self.controller.removed_rois(), selected_rois=self.controller.selected_rois, show_rois=self.controller.show_rois)

    def update_frame(self):
        if self.controller.adjusted_video is not None:
            frame = self.controller.adjusted_video[self.frame_num]

            self.update_left_image_plot(frame, roi_spatial_footprints=self.controller.roi_spatial_footprints(), video_dimensions=self.controller.video.shape, removed_rois=self.controller.removed_rois(), selected_rois=self.controller.selected_rois, show_rois=self.controller.show_rois)
            self.update_right_image_plot(frame, roi_spatial_footprints=self.controller.roi_spatial_footprints(), video_dimensions=self.controller.video.shape, removed_rois=self.controller.removed_rois(), selected_rois=self.controller.selected_rois, show_rois=self.controller.show_rois)

            # increment frame number (keeping it between 0 and n_frames)
            self.frame_num += 1
            self.frame_num = self.frame_num % self.n_frames

            self.current_frame_line_1.setValue(self.frame_num + self.controller.frame_offset)
            self.current_frame_line_2.setValue(self.frame_num + self.controller.frame_offset)
            self.current_frame_line_3.setValue(self.frame_num + self.controller.frame_offset)

            if not self.item_hovered:
                # update status bar
                self.set_default_statusbar_message("Viewing {}. Z={}. Frame {}/{}.".format(self.video_name, self.controller.z, self.frame_num + 1, self.n_frames))

    def update_left_image_plot(self, image, roi_spatial_footprints=None, video_dimensions=None, removed_rois=None, selected_rois=None, show_rois=False):
        image = 255.0*image/self.controller.video_max
        image[image > 255] = 255

        if len(image.shape) < 3:
            image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        else:
            image = image.astype(np.uint8)

        self.kept_rois_image = image

        self.left_image.setImage(image, autoLevels=False)

        if show_rois:
            if self.controller.kept_rois_overlay is not None:
                self.left_image_overlay.setImage(self.controller.kept_rois_overlay, levels=(0, 255))
            else:
                self.left_image_overlay.clear()
        else:
            if self.controller.kept_rois_overlay is not None:
                self.left_image_overlay.setImage(0*self.controller.kept_rois_overlay, levels=(0, 255))

        self.update_mask_items()

        if not self.item_hovered:
            self.set_default_statusbar_message("Viewing {}. Z={}.".format(self.video_name, self.controller.z))

    def update_mask_items(self, selected_mask=-1):
        self.clear_mask_items()
        mask_points = self.controller.mask_points()

        for i in range(len(mask_points)):
            mask_item = self.create_mask_item(mask_points[i], selected=selected_mask==i)
            self.left_image_viewbox.addItem(mask_item)
            self.mask_items.append(mask_item)

    def create_kept_rois_image(self, image, video_max, roi_spatial_footprints=None, video_dimensions=None, removed_rois=None, selected_rois=None, show_rois=False):
        image = 255.0*image/video_max
        image[image > 255] = 255

        if len(image.shape) < 3:
            image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        else:
            image = image.astype(np.uint8)

        if self.controller.kept_rois_overlay is not None and roi_spatial_footprints is not None:
            if show_rois:
                image = utilities.blend_transparent(image, self.controller.kept_rois_overlay)

        return image

    def first_video_imported(self):
        self.play_video_checkbox.setEnabled(True)

    def update_heatmap_plot(self, heatmap):
        if heatmap is not None:
            if self.controller.show_zscore:
                self.kept_traces_image.setImage(heatmap, levels=(-2.01, 3.01))
            else:
                self.kept_traces_image.setImage(heatmap, levels=(0, 1.01))

            self.kept_traces_image.setRect(QRectF(self.controller.frame_offset + self.controller.z/self.controller.video.shape[1], 0, heatmap.shape[0], heatmap.shape[1]))
        else:
            self.kept_traces_image.setImage(None)

    def create_removed_rois_image(self, image, video_max, roi_spatial_footprints=None, video_dimensions=None, removed_rois=None, selected_rois=None, show_rois=False):
        image = 255.0*image/video_max
        image[image > 255] = 255

        if len(image.shape) < 3:
            image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        else:
            image = image.astype(np.uint8)

        if show_rois and self.controller.removed_rois_overlay is not None and roi_spatial_footprints is not None:
            image = utilities.blend_transparent(image, self.controller.removed_rois_overlay)

        return image

    def plot_mean_image(self, image, video_max):
        image = 255.0*image/video_max
        image[image > 255] = 255
        if len(image.shape) < 3:
            image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        else:
            image = image.astype(np.uint8)

        self.right_image.setImage(image, autoLevels=False)

    def update_right_image_plot(self, image, roi_spatial_footprints=None, video_dimensions=None, removed_rois=None, selected_rois=None, show_rois=False):
        image = 255.0*image/self.controller.video_max
        image[image > 255] = 255

        if len(image.shape) < 3:
            image = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_GRAY2RGB)
        else:
            image = image.astype(np.uint8)

        self.removed_rois_image = image

        self.right_image.setImage(image, autoLevels=False)

        if show_rois:
            if self.controller.removed_rois_overlay is not None:
                self.right_image_overlay.setImage(self.controller.removed_rois_overlay, levels=(0, 255))
            else:
                self.right_image_overlay.clear()
        else:
            if self.controller.removed_rois_overlay is not None:
                self.right_image_overlay.setImage(0*self.controller.removed_rois_overlay, levels=(0, 255))

    def reset_zoom(self):
        print("Resetting zoom.")
        self.left_image_viewbox.setRange(QRectF(0, 0, self.controller.video.shape[2], self.controller.video.shape[3]))
        self.right_image_viewbox.setRange(QRectF(0, 0, self.controller.video.shape[2], self.controller.video.shape[3]))

    def item_hover_entered(self):
        self.item_hovered = True

    def item_hover_exited(self):
        self.item_hovered = False

    def closeEvent(self, ce):
        if not self.controller.closing:
            ce.ignore()
        else:
            ce.accept()

class HoverCheckBox(QCheckBox):
    def __init__(self, text, parent=None, status_bar=None):
        QCheckBox.__init__(self, text, parent)
        self.setMouseTracking(True)

        self.parent        = parent
        self.status_bar    = status_bar
        self.hover_message = ""

    def setHoverMessage(self, message):
        self.hover_message = message

    def enterEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.hover_message)
            self.parent.item_hover_entered()

    def leaveEvent(self, event):
        if self.status_bar is not None:
            self.status_bar.showMessage(self.parent.default_statusbar_message)
            self.parent.item_hover_exited()

class HoverLabel(QLabel):
    def __init__(self, text, parent=None, status_bar=None):
        QLabel.__init__(self, text, parent)
        self.setMouseTracking(True)

        self.parent        = parent
        self.status_bar    = status_bar
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

    frame.setStyleSheet("color: rgba(0, 0, 0, 0.2);")

    return frame
