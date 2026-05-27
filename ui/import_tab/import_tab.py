import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QProgressDialog, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QCheckBox, QDialogButtonBox,
    QFileDialog, QMessageBox, QGridLayout, QComboBox, QLabel, QDialog
)
from PyQt5.QtCore import Qt
from ..widgets.CollapsibleBox import CollapsibleBox
from ..widgets.FunctionPopup import ParameterDialog
import numpy as np
from pyqtgraph import AxisItem


class LogAxisItem(AxisItem):
    """AxisItem that formats ticks as powers-of-ten (0.1, 1, 10, 100...).

    Works with a log-x view (PlotWidget.setLogMode(x=True)).
    """
    def tickStrings(self, values, scale, spacing):
        strs = []
        for v in values:
        # Only label ticks that fall on integer log10 positions (powers of 10)
            if abs(v - round(v)) < 1e-6:
                val = 10 ** round(v)
                if val >= 1:
                    s = str(int(val))
                else:
                    s = ('%g' % val)
            else:
                s = ""
            strs.append(s)
        return strs


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
        self.pathEdit = QLineEdit()
        self.pathEdit.setReadOnly(True)
        self.pathEdit.setPlaceholderText("Click to select data file")
        self.pathEdit.mousePressEvent = self._choose_file
        self.filterCheck = QCheckBox("Filter",)
        self.seeDataCheck = QCheckBox("See Data")
        self.portSelect = QComboBox()
        self.portSelect.addItems(["Port A", "Port B"])

        self.startTimeLabel = QLabel("Start Time (mins)")
        self.startTime = QLineEdit("0")
        self.duration = QLineEdit("10")
        self.durationLabel = QLabel("Duration (mins)")
        self.filterType = QComboBox()
        self.filterType.addItems([
            "No Filter",
            "Butterworth",
            "Lowpass",
            "Highpass",
            "Automatic"
        ])
        self.text = QLabel("Filter Type:")
        self.plot_raw_signal = pg.PlotWidget(title="Raw Signal")
        self.plot_raw_signal.getAxis('bottom').setLabel('Time (s)', color='#2a2a2a')
        self.plot_raw_signal.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')
        self.plot_raw_spectrum = pg.PlotWidget(title="Raw Signal Spectrum", axisItems={'bottom': LogAxisItem(orientation='bottom')})
        self.plot_raw_spectrum.getAxis('bottom').setLabel('Frequency (Hz)', color='#2a2a2a')
        self.plot_raw_spectrum.getAxis('left').setLabel('PSD (dB/Hz)', color='#2a2a2a')

        self.plot_filt_signal = pg.PlotWidget(title="Filtered Signal")
        self.plot_filt_signal.getAxis('bottom').setLabel('Time (s)', color='#2a2a2a')
        self.plot_filt_signal.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')
        self.plot_filt_spectrum = pg.PlotWidget(title="Filtered Signal Spectrum", axisItems={'bottom': LogAxisItem(orientation='bottom')})
        self.plot_filt_spectrum.getAxis('bottom').setLabel('Frequency (Hz)', color='#2a2a2a')
        self.plot_filt_spectrum.getAxis('left').setLabel('PSD (dB/Hz)', color='#2a2a2a')

        form.addRow("Data Path:", self.pathEdit)
        options_layout.addWidget(self.text, 0, 0)
        options_layout.addWidget(self.filterType, 0, 1)
        options_layout.addWidget(self.portSelect, 0, 2)
        options_layout.addWidget(self.startTimeLabel, 1, 0)
        options_layout.addWidget(self.startTime, 1, 1)
        options_layout.addWidget(self.durationLabel, 1, 2)
        options_layout.addWidget(self.duration, 1, 3)
        options_box.setContentLayout(options_layout)
        form.addRow(options_box)
        graph_layout = QGridLayout()
        graph_layout.addWidget(self.plot_raw_signal, 0, 0)
        graph_layout.addWidget(self.plot_raw_spectrum, 1, 0)
        graph_layout.addWidget(self.plot_filt_signal, 0, 1)
        graph_layout.addWidget(self.plot_filt_spectrum, 1, 1)
        form.addRow(graph_layout)

        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout.addLayout(form)
        layout.addWidget(self.btns)

        self.btns.accepted.connect(self.load_data)
        self.btns.rejected.connect(self.clear)

    def _choose_file(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Select Data File")
        if path:
            self.pathEdit.setText(path)
        QLineEdit.mousePressEvent(self.pathEdit, event)

    def load_data(self):
        path = self.pathEdit.text()
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Select Data File")
            if not path:
                return
            self.pathEdit.setText(path)

        # Create and show progress dialog
        progress = QProgressDialog("Loading data...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Loading")
        progress.setMinimumDuration(0)  # Show immediately
        progress.setValue(0)  # Indeterminate progress
        progress.show()

        try:
            data = self.controller.load_data(path, float(self.startTime.text()), float(self.duration.text()), port=self.portSelect.currentText())
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Load Error", str(e))
            return


        progress.close()
        self.pathEdit.setText(path)
        
        # Handle LazyFrame or DataFrame
        if hasattr(data.original, 'collect'):
            # LazyFrame - need to collect first
            y = data.original.select(self.controller.data.filter_ch[0]).collect().to_series().to_numpy().ravel()
        elif hasattr(data.original, 'select'):
            # DataFrame
            y = data.original.select(self.controller.data.filter_ch[0]).to_series().to_numpy().ravel()
        else:
            # Fallback for other formats
            y = data.original[self.controller.data.filter_ch[0]].to_numpy()
        self.plot_raw_signal.clear()
        self.plot_raw_spectrum.clear()
        raw_curve = self.plot_raw_signal.plot(y, pen=pg.mkPen(color=(50, 50, 200), width=1))
        raw_curve.setDownsampling(auto=True, method="peak")
        raw_curve.setClipToView(True)
        self.plot_raw_signal.getAxis('bottom').setScale(1 / self.controller.data.fs)
        freq_data = self.controller.data.compute_frequency_content(
                signal_1d=y,
                fs=self.controller.data.fs,
                nperseg=min(100000, len(y)) if len(y) > 0 else 512,
            )
        self.plot_psd(self.plot_raw_spectrum, freq_data)


        if self.filterType.currentText() != "No filter": 
            if self.filterType.currentText() == "Automatic" or self.filterType.currentText() == "No Filter":
                pass
            elif self.filterType.currentText() == "Butterworth":
                 param_spec = {
                "lowcut": {
                    "type": "float",
                    "label": "Low Cutoff (Hz)",
                    "default": 300.0,
                },   
                "highcut": {
                    "type": "float",
                    "label": "High Cutoff (Hz)",
                    "default": 500.0,
                }
                 }
            else:
                param_spec = {
                    "cutoff": {
                        "type": "float",
                        "label": "Cutoff Frequency (Hz)",
                        "default": 300.0,
                    }
                    }
            
            if self.filterType.currentText() != "Automatic" and self.filterType.currentText() != "No Filter":
                dialog = ParameterDialog(param_spec, parent=self)

                if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

                params = dialog.get_values()
                self.controller.apply_filter(self.filterType.currentText(), filter_params = (lambda v: v[0] if len(v) == 1 else v)(list(params.values())))
            else:
                self.controller.apply_filter(self.filterType.currentText())

            # Handle LazyFrame or DataFrame
            if hasattr(data.filtered, 'collect'):
                # LazyFrame - need to collect first
                y_f = data.filtered.select(self.controller.data.filter_ch[0]).collect().to_series().to_numpy().ravel()
            elif hasattr(data.filtered, 'select'):
                # DataFrame
                y_f = data.filtered.select(self.controller.data.filter_ch[0]).to_series().to_numpy().ravel()
            else:
                # Fallback for other formats
                y_f = data.filtered[self.controller.data.filter_ch[0]].to_numpy()
            
            self.plot_filt_signal.clear()
            self.plot_filt_spectrum.clear()
            filt_curve = self.plot_filt_signal.plot(y_f, pen=pg.mkPen(color=(200, 50, 50), width=1))
            filt_curve.setDownsampling(auto=True, method="peak")
            filt_curve.setClipToView(True)
            self.plot_filt_signal.getAxis('bottom').setScale(1 / self.controller.data.fs)
            freq_data = self.controller.data.compute_frequency_content(
                signal_1d=y_f,
                fs=self.controller.data.fs,
                nperseg=min(100000, len(y_f)) if len(y_f) > 0 else 512
                )
            self.plot_psd(self.plot_filt_spectrum, freq_data)
    def clear(self):
        self.plot_raw_signal.clear()
        self.plot_raw_spectrum.clear()
        self.plot_filt_signal.clear()
        self.plot_filt_spectrum.clear()
        self.pathEdit.clear()
    
    def plot_psd(self, plot, freq_data: dict):
        """
        Plot Welch PSD in self.plot_raw_spectrum (PlotWidget).
        """
        # --- Clear previous content ---
        plot.clear()

        freqs = freq_data["psd_freqs"]
        psd = freq_data["psd"]

        # Convert PSD to dB for consistency with matplotlib
        psd_db = 10 * np.log10(psd + np.finfo(float).eps)

        # Remove non-positive frequencies (log axis requires positive x)
        mask = freqs > 0
        freqs = freqs[mask]
        psd_db = psd_db[mask]

        # --- Plot ---
        plot.plot(
            freqs,
            psd_db,
            pen=pg.mkPen(color=(50, 150, 255), width=2),
        )

        # --- Axes & labels ---
        plot.setLabel("left", "PSD (dB/Hz)")
        plot.setLabel("bottom", "Frequency (Hz)")
        plot.setTitle("Power Spectral Density (Welch)")

        # --- Log frequency axis (recommended for neural data) ---
        plot.setLogMode(x=True, y=False)
        # --- Grid ---
        plot.showGrid(x=True, y=True, alpha=0.3)

        # --- Set x-axis to start from 0.1 Hz ---
        max_freq = freqs[-1] if len(freqs) > 0 else 1000
        plot.setXRange(np.log10(0.1), np.log10(max_freq), padding=0)
        # --- Auto-range y-axis ---
        plot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)