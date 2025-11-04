import sys
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QGridLayout,
    QLineEdit,
    QDialogButtonBox
)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Processing GUI")
        self.resize(800, 400)
        # Create a top-level layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Create the tab widget with two tabs
        tabs = QTabWidget()
        tabs.addTab(self.ImportTabUI(), "Import")
        tabs.addTab(self.FilteringTabUI(), "Filtering")
        tabs.setTabPosition(QTabWidget.West)
        tabs.tabBar().setStyleSheet("QTabBar::tab{ height: 100 px; width: 150px; }")
        layout.addWidget(tabs)

    def ImportTabUI(self):
        """Create the General page UI."""
        importTab = QWidget()
        layout = QVBoxLayout()
        formlayout = QFormLayout()
        formlayout.addRow("Data Path:", QLineEdit())
        formlayout.addRow("See Data:", QCheckBox())
        btnBox = QDialogButtonBox()
        btnBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addLayout(formlayout)
        layout.addWidget(btnBox)
        importTab.setLayout(layout)
        return importTab

    def FilteringTabUI(self):
        """Create the Network page UI."""
        filteringTab = QWidget()
        layout = QGridLayout()
        layout.addWidget(QCheckBox("Filter 1"), 0,0)
        layout.addWidget(QCheckBox("Filter 2"),1,0)
        plot_graph = pg.PlotWidget()
        layout.addWidget(plot_graph,2,1)
        filteringTab.setLayout(layout)
        return filteringTab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())