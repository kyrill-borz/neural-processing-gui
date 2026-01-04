import sys
import pyqtgraph as pg
from scipy import signal as sg
import polars as pl
from functionality import apploadfilepolars, apply_butterworth_filter, filt_config
from utils.utils import convertDfType
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QGridLayout,
    QLineEdit,
    QDialogButtonBox,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox
)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        pg.setConfigOption('background', '#f2f2f2')
        pg.setConfigOption('foreground', '#2a2a2a')
        self.filt_config = filt_config
        self.filt_config['butter']['Wn'] = filt_config['W']

        self.setWindowTitle("Processing GUI")
        self.resize(1200, 600)
        # Create a top-level layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Create the tab widget with two tabs
        tabs = QTabWidget()
        tabs.addTab(self.ImportTabUI(), "Import")
        tabs.addTab(self.NeuralTabUI(), "Neural Check")
        tabs.addTab(self.ProcessingTabUI(), "Analysis")
        tabs.setTabPosition(QTabWidget.West)
        tabs.tabBar().setStyleSheet("QTabBar::tab{ height: 124 px; width: 150px; }")
        layout.addWidget(tabs)

        with open("style.css","r") as fh:
            self.setStyleSheet(fh.read())

    def update_pg1_raw_plot(self):
        self.plot_pg1_raw.clear()

        y = self.data.original["ch_27"].to_numpy()[20000000:22000000]
        x = range(len(y))
        print(y)
        print("plotting raw data")
        self.plot_pg1_raw.plot(x, y, pen="b")

    def update_pg1_filtered_plot(self):
        self.plot_pg1_filtered.clear()
        self.data.filter_ch = ["ch_27"]
        signal2filter = self.data.original ###record.original #record.recording
        self.data.apply_filter = 'butter_lowpass'
        #config_text.append('signal2filter: %s' %signal2filter.name)
        self.data.filter(signal2filter, self.data.apply_filter, **filt_config[self.data.apply_filter])
        # Change from float64 to float 16
        # self.data.filtered = convertDfType(self.data.filtered, typeFloat=pl.Float32)
        y = self.data.filtered["ch_27"].to_numpy()[20000000:22000000]
        x = range(len(y))
        print(y)
        self.plot_pg1_filtered.plot(x, y, pen="b")

    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data File",
            "",
            "Data Files (*.csv *.parquet *.txt);;All Files (*)"
        )

        if not path:
            return

        try:
            self.data = apploadfilepolars(path)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))
            return

        self.pathEdit.setText(path)

        self.update_pg1_raw_plot()

        if self.filterCheck.isChecked():
            self.update_pg1_filtered_plot()

    def clear_import_tab(self):
        self.pathEdit.clear()
        self.plot_pg1_raw.clear()
        self.plot_pg1_filtered.clear()
        self.data = None
                
    def ImportTabUI(self):
        """Create the Import tab UI."""
        self.importTab = QWidget()
        layout = QVBoxLayout()
        formLayout = QFormLayout()

        # Data path
        self.pathEdit = QLineEdit()
        self.pathEdit.setReadOnly(True)
        formLayout.addRow("Data Path:", self.pathEdit)

        # Controls
        self.filterCheck = QCheckBox()
        self.seeDataCheck = QCheckBox()
        self.autofilterCheck = QCheckBox()
        formLayout.addRow("Filter:", self.filterCheck)
        formLayout.addRow("Autofilter:", self.autofilterCheck)
        formLayout.addRow("See Data:", self.seeDataCheck)

        # Plots
        self.plot_pg1_raw = pg.PlotWidget(title="Raw Signal")
        self.plot_pg1_filtered = pg.PlotWidget(title="Filtered Signal")
        formLayout.addRow("Raw Signal:", self.plot_pg1_raw)
        formLayout.addRow("Filtered Signal:", self.plot_pg1_filtered)

        # Buttons
        self.btnBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout.addLayout(formLayout)
        layout.addWidget(self.btnBox)
        self.importTab.setLayout(layout)

        # Signal wiring
        self.btnBox.accepted.connect(self.load_data)
        self.btnBox.rejected.connect(self.clear_import_tab)

        return self.importTab

    def update_referencing_view(self):
        self.plot_pg2_before.clear()
        self.plot_pg2_after.clear()

        # BEFORE
        y_before = self.data.filtered[self.data.filter_ch[0]].to_numpy()
        self.plot_pg2_before.plot(y_before)

        # AFTER
        y_after = self.data.referenced[self.data.filter_ch[0]].to_numpy()
        self.plot_pg2_after.plot(y_after)

    def apply_referencing(self):
        method = self.refCombo.currentText()

        if method in ("Select Referencing Method", "No Referencing"):
            return

        self.data.apply_referencing(method)
        self.update_referencing_view()

    def NeuralTabUI(self):
        """Create the Neural Analysis tab UI."""
        self.neuralTab = QWidget()
        layout = QGridLayout()

        # Checkboxes
        self.dropBadChCheck = QCheckBox("Drop Bad Channels")
        self.singleChCheck = QCheckBox("Single Channel Analysis")
        self.multiChCheck = QCheckBox("Multiple Channel Analysis")

        layout.addWidget(self.dropBadChCheck, 1, 0)
        layout.addWidget(self.singleChCheck, 0, 1)
        layout.addWidget(self.multiChCheck, 0, 2)

        # Referencing selection
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
        layout.addWidget(self.refCombo, 0, 0)

        # Analysis selectors
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

        # Plots (THIS is what you care about)
        self.plot_pg2_before = pg.PlotWidget(title="Before Referencing")
        self.plot_pg2_after = pg.PlotWidget(title="After Referencing")

        layout.addWidget(self.plot_pg2_before, 2, 0, 1, 3)
        layout.addWidget(self.plot_pg2_after, 3, 0, 1, 3)

        # Buttons
        self.neuralBtnBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addWidget(self.neuralBtnBox, 4, 2)

        self.neuralTab.setLayout(layout)

        # Signal wiring
        self.refCombo.currentTextChanged.connect(self.update_referencing_view)
        self.neuralBtnBox.accepted.connect(self.apply_referencing)

        return self.neuralTab
    
    def ProcessingTabUI(self):
        """Create the Network page UI."""
        processingTab = QWidget()
        layout = QGridLayout()
        layout.addWidget(QCheckBox("Using Multiple Traces"), 0,0)

        layout.addWidget(QPushButton("Temporal Heatmap Correlogram"),0,1)
        layout.addWidget(QPushButton("Overlap Analysed Traces"),0,2)
        plot_graph_raw = pg.PlotWidget()
        plot_graph_filtered = pg.PlotWidget()
        layout.addWidget(plot_graph_raw,2,0,1,3)
        layout.addWidget(plot_graph_filtered,3,0,1,3)
        processingTab.setLayout(layout)
        return processingTab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    

    window = Window()
    window.show()
    sys.exit(app.exec_())