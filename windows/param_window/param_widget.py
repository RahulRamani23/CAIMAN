from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QSlider, QLineEdit, QSizePolicy, \
    QComboBox

import numpy as np

from windows.param_window.hover_check_box import HoverCheckBox
from windows.param_window.hover_label import HoverLabel

heading_font = QFont()
heading_font.setBold(True)
heading_font.setPointSize(16)


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