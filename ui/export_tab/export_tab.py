import pyqtgraph as pg
from PyQt5.QtWidgets import QFileDialog, QWidget, QGridLayout, QComboBox, QDialogButtonBox, QCheckBox, QPushButton

class ExportTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        """Create the Network page UI."""
        layout = QGridLayout(self)
        exportButton = QPushButton("Export Neurogram")
        exportButton.clicked.connect(self.export_neurogram)
        importButton = QPushButton("Import Neurogram")
        importButton.clicked.connect(self.import_neurogram)
        layout.addWidget(exportButton, 0,0)
        layout.addWidget(importButton, 0,1)


    def export_neurogram(self):

        folder_path = QFileDialog.getExistingDirectory(
            caption="Select Export Folder"
        )

        if not folder_path:
            return

        try:
            self.controller.export(folder_path)

        except Exception as e:
            print(f"Export failed: {e}")
    def import_neurogram(self, parent_widget=None):
        pass
        # file_path, _ = QFileDialog.getOpenFileName(
        #     parent_widget,
        #     "Select Neurogram File",
        #     filter="Neurogram Files (*.neurogram);;All Files (*)"
        # )

        # if not file_path:
        #     return

        # try:
        #     self.controller.load_data(file_path)

        # except Exception as e:
        #     print(f"Import failed: {e}")
