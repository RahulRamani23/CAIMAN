from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox

from windows.param_window.param_widget import ParamWidget
from windows.param_window.param_window import *
from windows.param_window.hover_button import HoverButton

subheading_font = QFont()
subheading_font.setBold(True)
subheading_font.setPointSize(13)

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