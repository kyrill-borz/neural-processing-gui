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
    def update_raw_plot(self):
        self.plot_raw.clear()

        y = self.data.original["ch_27"].to_numpy()[20000000:22000000]
        x = range(len(y))
        print(y)
        print("plotting raw data")
        self.plot_raw.plot(x, y, pen="b")
    def update_filtered_plot(self):
        self.plot_filtered.clear()
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
        self.plot_filtered.plot(x, y, pen="b")

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

        self.update_raw_plot()

        if self.filterCheck.isChecked():
            self.update_filtered_plot()
    def clear_import_tab(self):
        self.pathEdit.clear()
        self.plot_raw.clear()
        self.plot_filtered.clear()
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
        formLayout.addRow("Filter:", self.filterCheck)
        formLayout.addRow("See Data:", self.seeDataCheck)

        # Plots
        self.plot_raw = pg.PlotWidget(title="Raw Signal")
        self.plot_filtered = pg.PlotWidget(title="Filtered Signal")
        formLayout.addRow("Raw Signal:", self.plot_raw)
        formLayout.addRow("Filtered Signal:", self.plot_filtered)

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

    def NeuralTabUI(self):
        """Create the Network page UI."""
        NeuralTab = QWidget()
        layout = QGridLayout()
        layout.addWidget(QCheckBox("Drop Bad Channels"), 1,0)
        layout.addWidget(QCheckBox("Single Channel Analysis"),0,1)
        layout.addWidget(QCheckBox("Multiple Channel Analysis"),0,2)

        combobox = QComboBox(self)
        combobox.addItem("Select Referencing Method")
        combobox.addItem("No Referencing")
        combobox.addItem("Median")
        combobox.addItem("Laplacian")
        combobox.addItem("Bipolar")
        combobox.addItem("Tripolar")
        layout.addWidget(combobox,0,0)

        combobox2 = QComboBox(self)
        combobox2.addItem("Type of Single Channel Analysis")
        combobox2.addItem("Referencing Only")
        combobox2.addItem("Single Channel Spike Detection")
        combobox2.addItem("ISI Distribution")
        combobox2.addItem("Clustering of Spikes")
        layout.addWidget(combobox2,1,1)

        combobox3 = QComboBox(self)
        combobox3.addItem("Type of Multi-Channel Analysis")
        combobox3.addItem("Multiple Channel Spike Detection")
        combobox3.addItem("Cross Correlation of Spike Trains")
        combobox3.addItem("Directionality Analysis")
        combobox3.addItem("Propogation Coefficient")
        layout.addWidget(combobox3,1,2)

        plot_graph_raw = pg.PlotWidget()
        plot_graph_filtered = pg.PlotWidget()
        layout.addWidget(plot_graph_raw,2,0,1,3)
        layout.addWidget(plot_graph_filtered,3,0,1,3)
        btnBox = QDialogButtonBox()
        btnBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        layout.addWidget(btnBox,4,2)
        NeuralTab.setLayout(layout)
        return NeuralTab
    
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