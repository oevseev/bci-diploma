from functools import partial

from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QGridLayout, QLabel, QWidget

LETTERS = ['ABCDEF', 'GHIJKL', 'MNOPQR', 'STUVWX', 'YZ0123', '456789']
NUM_ROWS = len(LETTERS)
NUM_COLS = len(LETTERS[0])


class KeyboardUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QGridLayout(self)
        for i in range(NUM_ROWS * NUM_COLS):
            row, col = i // NUM_COLS, i % NUM_COLS
            label = QLabel(LETTERS[row][col], parent=self)
            label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            layout.addWidget(label, row, col)
        self.setLayout(layout)

        self.setWindowTitle("Keyboard UI")
        self.setStyleSheet('background-color: black; color: white; font-size: 72pt')

        # TODO: Position at center
        self.setGeometry(0, 0, 600, 600)

    def flash_row(self, idx):
        indices = list(range(idx * NUM_COLS, (idx + 1) * NUM_COLS))
        self._flash_indices(indices)

    def flash_col(self, idx):
        indices = list(range(idx, NUM_ROWS * NUM_COLS, NUM_COLS))
        self._flash_indices(indices)

    def highlight_letter(self, letter, show_time=4000):
        row = [letter in x for x in LETTERS].index(True)
        col = LETTERS[row].index(letter)
        idx = row * NUM_COLS + col
        self._flash_indices([idx], 'red', show_time)

    def _flash_indices(self, indices, color='white', flash_time=100):
        for cur in indices:
            widget = self.layout().itemAt(cur).widget()
            widget.setStyleSheet('background-color: {}; color: black'.format(color))
        QTimer.singleShot(flash_time, partial(self._end_flash, indices))

    def _end_flash(self, indices):
        for idx in indices:
            self.layout().itemAt(idx).widget().setStyleSheet('')
