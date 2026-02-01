import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QWidget, QCheckBox, QGridLayout, QComboBox, QDialogButtonBox
from ui.analysis.analysis_window import AnalysisWindow

class NeuralTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)

        self.dropBadChCheck = QCheckBox("Drop Bad Channels")
        self.singleChCheck = QCheckBox("Single Channel Analysis")
        self.multiChCheck = QCheckBox("Multiple Channel Analysis")

        layout.addWidget(self.dropBadChCheck, 1, 0)
        layout.addWidget(self.singleChCheck, 0, 1)
        layout.addWidget(self.multiChCheck, 0, 2)

        self.refCombo = QComboBox()
        self.refCombo.addItems([
            "Select Referencing Method",
            "No Referencing",
            "Median",
            "Mean",
            "Laplacian",
            "Bipolar",
            "Tripolar",
        ])

        self.singleAnalysisCombo = QComboBox()
        self.singleAnalysisCombo.addItems([
            "Type of Single Channel Analysis",
            "Referencing Only",
            "Single Channel Spike Detection",
            "ISI Distribution",
            "Clustering of Spikes",
        ])
        layout.addWidget(self.singleAnalysisCombo, 1, 1)

        self.multiAnalysisCombo = QComboBox()
        self.multiAnalysisCombo.addItems([
            "Type of Multi-Channel Analysis",
            "Multiple Channel Spike Detection",
            "Cross Correlation of Spike Trains",
            "Directionality Analysis",
            "Propagation Coefficient",
        ])
        layout.addWidget(self.multiAnalysisCombo, 1, 2)

        # self.plot_pg2_waveform = pg.PlotWidget(title="Average Spike Waveform")
        # layout.addWidget(self.plot_pg2_waveform, 4, 0, 1, 3)

        self.plot_before = pg.PlotWidget(title="Before")
        self.plot_after = pg.PlotWidget(title="After")
        self.plot_before.getAxis('bottom').setLabel('Time (s)', color='#2a2a2a')
        self.plot_before.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')
        self.plot_after.getAxis('bottom').setLabel('Time (s)', color='#2a2a2a')
        self.plot_after.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')

        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout.addWidget(self.refCombo, 0, 0)
        layout.addWidget(self.plot_before, 2, 0, 1, 3)
        layout.addWidget(self.plot_after, 3, 0, 1, 3)
        layout.addWidget(self.btns, 4, 2)

        self.refCombo.currentTextChanged.connect(self.preview)
        self.btns.accepted.connect(self.apply)

    def preview(self):
        data = self.controller.data
        if not data:
            return
        y = data.filtered[data.filter_ch[0]].to_numpy()
        x = [ x/20000 for x in list(range(len(y))) ]
        self.plot_before.plot(x,y)

    def apply(self):
        method = self.refCombo.currentText()
        self.controller.apply_referencing(method)
        ref_df = self.controller.data.referenced
        first_col = ref_df.columns[0]
        y = ref_df[first_col].to_numpy()
        x = [ x/20000 for x in list(range(len(y))) ]
        self.plot_after.plot(x,y)
        if self.singleChCheck.isChecked():
            self.apply_single_channel_analysis()

        # if self.multiChCheck.isChecked():
        #     self.apply_multi_channel_analysis()
    def update_single_channel_waveform(self):
        self.plot_pg2_waveform.clear()

        mean = self.single_channel_result["mean_waveform"]
        std = self.single_channel_result["std_waveform"]

        x = np.arange(len(mean))

        self.plot_pg2_waveform.plot(x, mean, pen="b")
        self.plot_pg2_waveform.plot(x, mean + 3 * std, pen="r")
        self.plot_pg2_waveform.plot(x, mean - 3 * std, pen="r")

    def update_single_channel_plots(self):
        result = self.single_channel_result

        self.plot_pg2_waveform.clear()

        signal = (
            self.controller.data.referenced
            .select(result["channel"])
            .to_numpy()
            .ravel()
        )

        self.plot_pg2_waveform.plot(signal, pen="k")

        # Overlay spikes
        y = signal[result["indices"]]
        self.plot_pg2_waveform.plot(
            result["indices"],
            y,
            pen=None,
            symbol="o",
            symbolSize=4,
        )

    def apply_single_channel_analysis(self):
        analysis = self.singleAnalysisCombo.currentText()

        if analysis == "Single Channel Spike Detection":
            result = self.controller.data.single_channel_spike_analysis_polars(
                self.controller.data.filter_ch[0]
            )

            self.analysis_window = AnalysisWindow(result, self)
            self.analysis_window.show()
