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
            self.apply_single_channel_analysis(self.controller.data.filter_ch[4])

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
