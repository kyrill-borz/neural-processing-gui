import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from ui.import_tab.import_tab import ImportTab
from ui.neural_tab.neural_tab import NeuralTab
from ui.processing_tab.processing_tab import ProcessingTab
from ui.export_tab.export_tab import ExportTab
import pyqtgraph as pg


def resource_path(relative_path: str) -> str:
    """Return the absolute path to a resource, whether running as script or bundled."""
    base_path = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
    return str(Path(base_path) / relative_path)


class Window(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        with open(resource_path('style.css'), 'r') as fh:
            self.setStyleSheet(fh.read())

        pg.setConfigOption('background', '#f2f2f2')
        pg.setConfigOption('foreground', '#2a2a2a')
        tabs.addTab(ImportTab(controller), "Import")
        tabs.addTab(NeuralTab(controller), "Neural Check")
        tabs.addTab(ProcessingTab(controller), "Analysis")
        tabs.addTab(ExportTab(controller), "Export")
        
        layout.addWidget(tabs)