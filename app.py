import sys

from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFormLayout,
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
        tabs.addTab(self.FilteringTabUI(), "Network")
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
        layout = QVBoxLayout()
        layout.addWidget(QCheckBox("Network Option 1"))
        layout.addWidget(QCheckBox("Network Option 2"))
        
        filteringTab.setLayout(layout)
        return filteringTab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())