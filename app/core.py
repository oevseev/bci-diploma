import logging
import sys

from PySide2.QtCore import Qt, QProcess, QSettings
from PySide2.QtGui import QIcon, QPixmap, QTextCursor
from PySide2.QtWidgets import (
    QAction, QActionGroup, QApplication, QLabel, QMenu, QSystemTrayIcon, QTextBrowser)

import app
from app.realtime_interaction import InteractionServer
from app.preferences import PreferencesDialog
from app.ui import KeyboardUI

logger = logging.getLogger(__name__)


class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self._create_tray_icon()
        self._create_ui()
        self._create_interaction_server()

        self._session = None

    def open_preferences(self):
        prefs_dialog = PreferencesDialog()
        prefs_dialog.exec()

    def _mode_changed(self):
        action = self._mode_group.checkedAction()
        if action == self._mode_off:
            self._stop_session()
        elif action == self._mode_enabled:
            self._interaction_server.train = False
            self._start_session()
        elif action == self._mode_training:
            self._interaction_server.train = True
            self._start_session()

    def _start_session(self):
        if self._session is not None:
            return

        self._session = QProcess(self)
        self._session.finished.connect(self._session_ended)
        self._session.readyReadStandardOutput.connect(self._log_append_stdout)
        self._session.readyReadStandardError.connect(self._log_append_stderr)

        settings = QSettings()
        self._session.start(sys.executable, [
            'run_session.py',
            settings.value('CyKitAddress', app.DEFAULT_CYKIT_ADDRESS),
            str(settings.value('CyKitPort', app.DEFAULT_CYKIT_PORT)),
            str(self._interaction_server.port)
        ])

    def _stop_session(self):
        if self._session is not None:
            self._session.close()

    # TODO: Handle non-null exit codes
    def _session_ended(self):
        self._session = None
        self._mode_off.setChecked(True)

    def _log_append_stdout(self):
        process = self.sender()
        self._log_window.moveCursor(QTextCursor.End)
        self._log_window.insertPlainText(process.readAllStandardOutput().data().decode('utf-8'))
        self._log_window.moveCursor(QTextCursor.End)

    def _log_append_stderr(self):
        process = self.sender()
        self._log_window.moveCursor(QTextCursor.End)
        self._log_window.insertPlainText(process.readAllStandardError().data().decode('utf-8'))
        self._log_window.moveCursor(QTextCursor.End)

    def _select_letter(self, letter):
        self._letter_ui.setText(letter)

    def _create_tray_icon(self):
        menu = QMenu()

        self._mode_group = QActionGroup(menu)
        self._mode_group.triggered.connect(self._mode_changed)

        self._mode_off = QAction("&Off", parent=menu)
        self._mode_off.setCheckable(True)
        self._mode_off.setChecked(True)
        self._mode_group.addAction(self._mode_off)
        menu.addAction(self._mode_off)

        self._mode_enabled = QAction("&Enabled", parent=menu)
        self._mode_enabled.setCheckable(True)
        self._mode_group.addAction(self._mode_enabled)
        menu.addAction(self._mode_enabled)

        self._mode_training = QAction("&Training mode", parent=menu)
        self._mode_training.setCheckable(True)
        self._mode_group.addAction(self._mode_training)
        menu.addAction(self._mode_training)

        menu.addSeparator()
        menu.addAction("&Preferences", self.open_preferences)
        menu.addSeparator()
        menu.addAction("E&xit", self.exit)

        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.white)
        icon = QIcon(pixmap)

        self._tray_icon = QSystemTrayIcon(parent=self)
        self._tray_icon.setContextMenu(menu)
        self._tray_icon.setIcon(icon)
        self._tray_icon.show()

    def _create_ui(self):
        self._keyboard_ui = KeyboardUI()
        self._keyboard_ui.show()

        # TODO: Get rid of this in favor of os_interaction
        self._letter_ui = QLabel("-")
        self._letter_ui.setWindowTitle("Selected letter")
        self._letter_ui.setStyleSheet('font-size: 72pt')
        self._letter_ui.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._letter_ui.setGeometry(600, 0, 100, 100)
        self._letter_ui.show()

        # TODO: Replace with more user-friendly log
        self._log_window = QTextBrowser()
        self._log_window.setWindowTitle("Session Log")
        self._log_window.setGeometry(700, 0, 500, 500)
        self._log_window.show()

    def _create_interaction_server(self):
        self._interaction_server = InteractionServer(self)
        self._interaction_server.keyboard_flash_row.connect(self._keyboard_ui.flash_row)
        self._interaction_server.keyboard_flash_col.connect(self._keyboard_ui.flash_col)
        self._interaction_server.keyboard_highlight_letter.connect(self._keyboard_ui.highlight_letter)
        self._interaction_server.keyboard_select_letter.connect(self._select_letter)
