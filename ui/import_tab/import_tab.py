import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QCheckBox, QDialogButtonBox,
    QFileDialog, QMessageBox
)

class ImportTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()
        

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.pathEdit = QLineEdit(readOnly=True)
        self.filterCheck = QCheckBox()
        self.seeDataCheck = QCheckBox()
        self.autofilterCheck = QCheckBox()
        self.plot_raw = pg.PlotWidget(title="Raw Signal")
        self.plot_filt = pg.PlotWidget(title="Filtered Signal")

        form.addRow("Data Path:", self.pathEdit)
        form.addRow("Filter:", self.filterCheck)
        form.addRow("Autofilter:", self.autofilterCheck)
        form.addRow("See Data:", self.seeDataCheck)

        form.addRow("Raw Signal:", self.plot_raw)
        form.addRow("Filtered Signal:", self.plot_filt)

        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout.addLayout(form)
        layout.addWidget(self.btns)

        self.btns.accepted.connect(self.load_data)
        self.btns.rejected.connect(self.clear)

    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Data File")
        if not path:
            return

        try:
            data = self.controller.load_data(path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))
            return

        self.pathEdit.setText(path)
        y = data.original["ch_27"].to_numpy()
        self.plot_raw.plot(y)

        if self.filterCheck.isChecked():
            self.controller.apply_filter()
            y_f = data.filtered["ch_27"].to_numpy()
            self.plot_filt.plot(y_f)

    def clear(self):
        self.plot_raw.clear()
        self.plot_filt.clear()
        self.pathEdit.clear()