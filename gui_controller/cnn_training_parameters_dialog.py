from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class CNNTrainingParametersDialog(QDialog):
    def __init__(self, parent, learning_rate, batch_size):
        super(CNNTrainingParametersDialog, self).__init__(parent)

        param_layout = QVBoxLayout(self)
        param_layout.setContentsMargins(0, 0, 0, 0)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        param_layout.addWidget(widget)

        label = QLabel("Learning rate:")
        label.setToolTip("Learning rate for training the network.")
        layout.addWidget(label)

        self.learning_rate_textbox = QLineEdit()
        self.learning_rate_textbox.setAlignment(Qt.AlignHCenter)
        self.learning_rate_textbox.setFixedWidth(60)
        self.learning_rate_textbox.setFixedHeight(20)
        self.learning_rate_textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.learning_rate_textbox.setText("{}".format(learning_rate))
        layout.addWidget(self.learning_rate_textbox)

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        param_layout.addWidget(widget)

        label = QLabel("Batch size:")
        label.setToolTip("Batch size to use when training the network.")
        layout.addWidget(label)

        self.batch_size_textbox = QLineEdit()
        self.batch_size_textbox.setAlignment(Qt.AlignHCenter)
        self.batch_size_textbox.setFixedWidth(60)
        self.batch_size_textbox.setFixedHeight(20)
        self.batch_size_textbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.batch_size_textbox.setText("{}".format(batch_size))
        layout.addWidget(self.batch_size_textbox)

        param_layout.addStretch()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        param_layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def learning_rate(self):
        return float(self.learning_rate_textbox.text())

    def batch_size(self):
        return float(self.batch_size_textbox.text())

    @staticmethod
    def getParameters(parent, learning_rate, batch_size):
        dialog        = CNNTrainingParametersDialog(parent, learning_rate, batch_size)
        result        = dialog.exec_()
        learning_rate = dialog.learning_rate()
        batch_size    = dialog.batch_size()

        return (learning_rate, batch_size, result == QDialog.Accepted)