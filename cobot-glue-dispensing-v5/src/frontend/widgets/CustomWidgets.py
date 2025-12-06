import os

from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QTabWidget, QWidget, QSizePolicy


class BackgroundTabPage(QWidget):
    def __init__(self):
        super().__init__()


class CustomTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("QTabBar::tab { height: 40px; width: 120px; }")

