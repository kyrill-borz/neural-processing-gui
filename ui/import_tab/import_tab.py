import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QCheckBox, QDialogButtonBox,
    QFileDialog, QMessageBox, QGridLayout, QComboBox, QLabel
)
from ui.widgets.CollapsibleBox import CollapsibleBox

class ImportTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()
        

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        options_box = CollapsibleBox("Import Options")
        options_layout = QGridLayout()
        self.pathEdit = QLineEdit(readOnly=True)
        self.filterCheck = QCheckBox("Filter",)
        self.seeDataCheck = QCheckBox("See Data")
        self.startTimeLabel = QLabel("Start Time (mins)")
        self.startTime = QLineEdit("0")
        self.duration = QLineEdit("10")
        self.durationLabel = QLabel("Duration (mins)")
        self.filterType = QComboBox()
        self.filterType.addItems([
            "No Filter",
            "Butterworth",
            "Lowpass",
            "Automatic"
        ])
        self.text = QLabel("Filter Type:")
        self.plot_raw = pg.PlotWidget(title="Raw Signal")
        self.plot_raw.getAxis('bottom').setLabel('Time (s)', color='#2a2a2a')
        self.plot_raw.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')
        self.plot_filt = pg.PlotWidget(title="Filtered Signal")
        self.plot_filt.getAxis('bottom').setLabel('Time (s)', color='#2a2a2a')
        self.plot_filt.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')

        form.addRow("Data Path:", self.pathEdit)
        options_layout.addWidget(self.text, 0, 0)
        options_layout.addWidget(self.filterType, 0, 1)
        options_layout.addWidget(self.seeDataCheck, 0, 2)
        options_layout.addWidget(self.startTimeLabel, 1, 0)
        options_layout.addWidget(self.startTime, 1, 1)
        options_layout.addWidget(self.durationLabel, 1, 2)
        options_layout.addWidget(self.duration, 1, 3)
        options_box.setContentLayout(options_layout)
        form.addRow(options_box)
        
        form.addRow(self.plot_raw)
        form.addRow(self.plot_filt)

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
            data = self.controller.load_data(path, float(self.startTime.text()), float(self.duration.text()))
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))
            return

        self.pathEdit.setText(path)
        y = data.original["ch_27"].to_numpy()
        x = [ x/20000 for x in list(range(len(y))) ]
        self.plot_raw.plot(x,y)

        if self.filterType.currentText() != "No filter":
            self.controller.apply_filter(self.filterType.currentText())
            y_f = data.filtered["ch_27"].to_numpy()
            self.plot_filt.plot(x, y_f)

    def clear(self):
        self.plot_raw.clear()
        self.plot_filt.clear()
        self.pathEdit.clear()