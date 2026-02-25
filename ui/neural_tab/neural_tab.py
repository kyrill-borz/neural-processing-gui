import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QCheckBox, QGridLayout, QComboBox, QDialogButtonBox, QPushButton, QScrollArea
from ui.analysis.analysis_window import AnalysisWindow
from ui.neural_tab.channel_display_window import ChannelDisplayWindow
class NeuralTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()
        self._last_ref_method = None

    def _build_ui(self):
        layout = QGridLayout(self)

        self.dropBadChCheck = QPushButton("Select Channels")
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

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)

        self.scroll.setWidget(self.plot_container)

        layout.addWidget(self.scroll, 2, 0, 2, 3)

        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout.addWidget(self.refCombo, 0, 0)
        layout.addWidget(self.btns, 4, 2)

        self.btns.accepted.connect(self.apply)
        self.dropBadChCheck.clicked.connect(self.handleChannelDisplayButton)

    def apply(self):
        print(self.controller.data.channels)
        method = self.refCombo.currentText()

        if method == "Select Referencing Method":
            return

        if method != self._last_ref_method:
            print("starting referencing")
            self.controller.apply_referencing(method)
            self._last_ref_method = method

        ref_df = self.controller.data.referenced

        self.display_referenced_channels(ref_df)

        if self.singleChCheck.isChecked():
            self.apply_single_channel_analysis(self.controller.data.filter_ch[4])

        # if self.multiChCheck.isChecked():
        #     self.apply_multi_channel_analysis()
    
    def display_referenced_channels(self, ref_df):
        fs = 20000
        max_points = 200000

        # Clear old plots
        while self.plot_layout.count():
            item = self.plot_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        selected_channels = getattr(self.controller.data, "channels", [])

        for ch in selected_channels:

            if ch not in ref_df.columns:
                continue

            series = ref_df[ch]
            length = len(series)

            if length > max_points:
                step = length // max_points
                series = series.gather_every(step)
            else:
                step = 1

            y = series.to_numpy()

            plot = pg.PlotWidget(title=ch)
            plot.setFixedHeight(150)

            curve = plot.plot(y)
            curve.setDownsampling(auto=True, method="peak")
            curve.setClipToView(True)

            plot.getAxis("bottom").setScale(step / fs)
            plot.getAxis("bottom").setLabel("Time (s)")
            plot.getAxis("left").setLabel("Amplitude (uV)")

            self.plot_layout.addWidget(plot)

        self.plot_layout.addStretch()
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

    def get_spike_data(self, channel: str):
        """
        Returns spike analysis result for a channel.
        Computes it if not already cached.
        """

        if not hasattr(self, "_spike_cache"):
            self._spike_cache = {}

        if channel in self._spike_cache:
            return self._spike_cache[channel]

        # Compute and cache
        spike_result = self.controller.data.single_channel_spike_analysis_polars(
            channel=channel,
            extract_waveforms=True,
        )

        self._spike_cache[channel] = spike_result

        return spike_result

    def apply_single_channel_analysis(self, channel: str):
        analysis = self.singleAnalysisCombo.currentText()

        if analysis == "Single Channel Spike Detection":
            channel = self.controller.data.filter_ch[0]
            print("getting spike data")
            spike_data = self.get_spike_data(channel)
              # Assuming first filtered channel    
            # No spikes case
            if spike_data["indices"] is None or len(spike_data["indices"]) == 0:
                payload = {
                    "title": f"Spike Analysis – {channel}",
                    "plots": [
                        {
                            "kind": "text",
                            "content": "No spikes detected for this channel."
                        }
                    ]
                }
            else:
                payload = {
                    "title": f"Spike Analysis – {channel}",
                    "plots": [
                        {
                            "title": "Detected Spikes",
                            "x": spike_data["times"],
                            "y": spike_data["peaks"],
                            "kind": "scatter",
                        }
                    ]
                }

                # Add waveform if available
                if spike_data["mean_waveform"] is not None:
                    payload["plots"].append({
                        "title": "Average Spike Waveform",
                        "x": np.arange(len(spike_data["mean_waveform"])),
                        "y": spike_data["mean_waveform"],
                        "kind": "line",
                    })

                # Add ISI if available
                if spike_data["isi_ms"] is not None:
                    payload["plots"].append({
                        "title": "ISI Histogram",
                        "y": spike_data["isi_ms"],
                        "kind": "hist",
                    })

            self.analysis_window = AnalysisWindow(payload, self)
            self.analysis_window.show()
        if analysis == "ISI Distribution":
                channel = self.controller.data.filter_ch[4]
                spike_data = self.get_spike_data(channel)
                spike_times = spike_data["times"].to_numpy()
                isi_result = self.controller.data.compute_isi_distribution_over_time(
                    spike_times_ms=spike_times
                )

                analysis_payload = {
                    "title": "ISI Distribution Over Time",
                    "plots": [
                        {
                            "kind": "image",
                            "title": "ISI Heatmap",
                            "z": isi_result["isi_matrix"].T,
                            "x": isi_result["window_centers_sec"],
                            "y": isi_result["isi_bins_ms"],
                            "xlabel": "Time (s)",
                            "ylabel": "ISI (ms)",
                        },
                        {
                            "kind": "text",
                            "content": (
                                f"KS Statistic: {isi_result['ks_stat']:.4f}\n"
                                f"p-value: {isi_result['ks_p']:.4f}"
                            )
                        }
                    ]
                }

                self.analysis_window = AnalysisWindow(analysis_payload, self)
                self.analysis_window.show()
            
        if analysis == "Clustering of Spikes":
            spike_data = self.get_spike_data(self.controller.data.filter_ch[4])
            spike_times = spike_data["times"].to_numpy()
            spike_waveforms = spike_data["waveforms"]

            clustering_result = self.controller.data.cluster_spike_waveforms(
                waveforms=spike_waveforms,
                spike_times_sec=spike_times
            )
            plots = []

            for i, mean_wf in enumerate(clustering_result["cluster_means"]):
                if mean_wf is None:
                    continue

                plots.append({
                    "kind": "line",
                    "title": f"Cluster {i} Mean Waveform",
                    "x": np.arange(len(mean_wf)),
                    "y": mean_wf,
                })
            for i, isi in enumerate(clustering_result["cluster_isi"]):
                if len(isi) == 0:
                    continue

                plots.append({
                    "kind": "hist",
                    "title": f"Cluster {i} ISI",
                    "y": isi,
                    "bins": 50
                })

            features = clustering_result["features"]
            labels = clustering_result["labels"]

            plots.append({
                "kind": "scatter",
                "title": "Feature Space (Peak-to-Peak vs Energy)",
                "x": features[:, 0],
                "y": features[:, 1],
            })

            analysis_payload = {
                "title": "Spike Clustering Results",
                "plots": plots
            }

            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()
    
    def handleChannelDisplayButton(self):
        self.channel_window = ChannelDisplayWindow(self.controller)
        self.channel_window.show()