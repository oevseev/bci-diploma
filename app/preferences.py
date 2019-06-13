from PySide2.QtCore import QSettings
from PySide2.QtWidgets import QDialog, QGridLayout, QLabel, QLayout, QLineEdit, QPushButton

import app


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        settings = QSettings()

        layout = QGridLayout(self)
        layout.setSizeConstraint(QLayout.SetFixedSize)

        layout.addWidget(QLabel("CyKit address:"), 0, 0)
        self.cykit_address_field = QLineEdit()
        self.cykit_address_field.setText(settings.value('CyKitAddress'))
        self.cykit_address_field.setPlaceholderText(app.DEFAULT_CYKIT_ADDRESS)
        layout.addWidget(self.cykit_address_field, 0, 1, 1, 2)

        layout.addWidget(QLabel("CyKit port:"), 1, 0)
        self.cykit_port_field = QLineEdit()
        self.cykit_port_field.setText(settings.value('CyKitPort'))
        self.cykit_port_field.setPlaceholderText(str(app.DEFAULT_CYKIT_PORT))
        layout.addWidget(self.cykit_port_field, 1, 1, 1, 2)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button, 2, 1)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, 2, 2)

        self.setLayout(layout)
        self.setWindowTitle("Preferences")

    def accept(self):
        super().accept()

        settings = QSettings()

        cykit_address = self.cykit_address_field.text()
        if cykit_address:
            settings.setValue('CyKitAddress', cykit_address)
        else:
            settings.remove('CyKitAddress')

        cykit_port = self.cykit_port_field.text()
        if cykit_port:
            settings.setValue('CyKitPort', cykit_port)
        else:
            settings.remove('CyKitPort')
