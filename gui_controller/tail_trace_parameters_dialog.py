from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class TailTraceParametersDialog(QDialog):
    def __init__(self, parent, tail_fps, imaging_fps):
        super(TailTraceParametersDialog, self).__init__(parent)

        param_layout = QVBoxLayout(self)
        param_layout.setContentsMargins(0, 0, 0, 0)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        param_layout.addWidget(widget)

        label = QLabel("Tail trace FPS:")
        label.setToolTip("Tail trace frame rate (frames per second).")
        layout.addWidget(label)

        self.tail_fps_textbox = QLineEdit()
        self.tail_fps_textbox.setAlignment(Qt.AlignHCenter)
        self.tail_fps_textbox.setObjectName("Tail Trace FPS")
        self.tail_fps_textbox.setFixedWidth(60)
        self.tail_fps_textbox.setFixedHeight(20)
        self.tail_fps_textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tail_fps_textbox.setText("{}".format(tail_fps))
        layout.addWidget(self.tail_fps_textbox)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        param_layout.addWidget(widget)

        label = QLabel("Imaging FPS (per plane):")
        label.setToolTip("Imaging frame rate (frames per second).")
        layout.addWidget(label)

        self.imaging_fps_textbox = QLineEdit()
        self.imaging_fps_textbox.setAlignment(Qt.AlignHCenter)
        self.imaging_fps_textbox.setObjectName("Imaging FPS")
        self.imaging_fps_textbox.setFixedWidth(60)
        self.imaging_fps_textbox.setFixedHeight(20)
        self.imaging_fps_textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.imaging_fps_textbox.setText("{}".format(imaging_fps))
        layout.addWidget(self.imaging_fps_textbox)

        param_layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        param_layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def tail_fps(self):
        return float(self.tail_fps_textbox.text())

    def imaging_fps(self):
        return float(self.imaging_fps_textbox.text())

    @staticmethod
    def getParameters(parent, tail_fps, imaging_fps):
        dialog      = TailTraceParametersDialog(parent, tail_fps, imaging_fps)
        result      = dialog.exec_()
        tail_fps    = dialog.tail_fps()
        imaging_fps = dialog.imaging_fps()

        return (tail_fps, imaging_fps, result == QDialog.Accepted)
