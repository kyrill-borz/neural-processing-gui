import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QWidget, QCheckBox, QGridLayout, QComboBox, QDialogButtonBox, QPushButton, QScrollArea
from PyQt5.QtCore import Qt
from ui.analysis.analysis_window import AnalysisWindow
from ui.neural_tab.channel_display_window import ChannelDisplayWindow
from ui.widgets.FunctionPopup import ParameterDialog
from ui.widgets.InfoHover import InfoHoverButton
class NeuralTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()
        self._last_ref_method = None
        self.min_threshold_std = 2.5
        self.maximum_height_std = 10.0

    def _build_ui(self):
        layout = QGridLayout(self)

        self.dropBadChCheck = QPushButton("Select Channels to Display")
        self.singleChCheck = QCheckBox("Single Channel Analysis")
        self.multiChCheck = QCheckBox("Multiple Channel Analysis")

        layout.addWidget(self.dropBadChCheck, 1, 0)
        layout.addWidget(self.singleChCheck, 0, 1)
        self.singleInfo = InfoHoverButton("""Information about the different Single Channel Analysis functions:\n\n
                                          - Referencing Only: Applies the selected referencing method without further analysis.\n\n
                                          - Single Channel Spike Detection: Detects spikes on the selected channel using a thresholding method. Parameters include spike threshold (in standard deviations), maximum spike threshold, and waveform extraction window.\n\n
                                          - ISI Distribution: Computes the distribution of inter-spike intervals for the detected spikes, displaying a histogram for each window.\n\n
                                          - Clustering of Spikes: Clusters detected spikes based on their waveforms to identify potential different neuron types or units. Provides average waveform and ISI distribution for each cluster.""")
        layout.addWidget(self.singleInfo, 0, 1, alignment=Qt.AlignRight)
        layout.addWidget(self.multiChCheck, 0, 2)
        self.multiInfo = InfoHoverButton("""Information about the different Multiple Channel Analysis functions: \n\n
                                         - Multiple Channel Spike Detection: Detects spikes across multiple channels simultaneously, which can help identify synchronous firing patterns. Parameters are similar to single channel spike detection but applied across all selected channels.\n\n
                                         - Cross Correlation of Spike Trains: Analyzes the temporal relationship between spike trains from different channels to identify potential functional connectivity or synchrony.\n\n
                                         - Propagation Coefficient: Measures the speed and direction of spike propagation across the electrode array, which can provide insights into network dynamics and connectivity.""")
        layout.addWidget(self.multiInfo, 0, 2, alignment=Qt.AlignRight)

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
        self.absoluteInfo = InfoHoverButton("""Referencing methods explained:\n\
                                        - No Referencing: Uses the raw or filtered signal without any referencing.\n
                                        - Median: Subtracts the median of the signal from each channel.\n
                                        - Mean: Subtracts the mean of the signal from each channel.\n
                                        - Laplacian: Applies a weighted average of the signal against its neighbors to emphasize edges and boundaries.\n
                                        - Bipolar: Subtracts the signal from one channel from another channel.\n
                                        - Tripolar: Combines bipolar referencing with additional channels for more complex referencing schemes. \n\n

                                            Overall Explanations for this page: \n
                                        - checking the Single/Multi Channel Analysis boxes will apply the selected analyses at particular thresholds.\n
                                        - The "Select Channels to Display" button allows you to choose which channels to visualize in the plots below. This is useful for focusing on specific channels of interest or excluding noisy channels from the visualization.\n
                                               
                                        """)
        
        layout.addWidget(self.absoluteInfo, 4, 0, alignment=Qt.AlignLeft)

        self.singleAnalysisCombo = QComboBox()
        self.singleAnalysisCombo.addItems([
            "Type of Single Channel Analysis",
            #"Referencing Only",
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
            #"Directionality Analysis",
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
            self.apply_single_channel_analysis()

        if self.multiChCheck.isChecked():
            self.apply_multi_channel_analysis()
    
    def display_referenced_channels(self, df):

        fs = 20000
        max_points = 200000

        # Clear old plots
        while self.plot_layout.count():
            item = self.plot_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        selected_channels = getattr(self.controller.data, "channels", [])

        master_plot = None  # first plot becomes x-axis master

        for idx, ch in enumerate(selected_channels):

            # Handle LazyFrame or DataFrame
            if hasattr(df, 'collect'):
                # LazyFrame - need to collect first
                if ch not in df.columns:
                    continue
                series = df.select(ch).collect().to_series()
            elif hasattr(df, 'select'):
                # DataFrame
                if ch not in df.columns:
                    continue
                series = df.select(ch).to_series()
            else:
                # Fallback for other formats
                if ch not in df.columns:
                    continue
                series = df[ch]
            
            length = len(series)

            if length > max_points:
                step = length // max_points
                series = series.gather_every(step)
            else:
                step = 1

            y = series.to_numpy()

            plot = pg.PlotWidget(title=self.controller.get_channel_name(ch))
            plot.setFixedHeight(140)

            curve = plot.plot(y)
            curve.setDownsampling(auto=True, method="peak")
            curve.setClipToView(True)

            plot.getAxis("bottom").setScale(step / fs)
            plot.getAxis("bottom").setLabel("Time (s)")
            plot.getAxis("left").setLabel("Amplitude (uV)")

            # Link x-axis
            if master_plot is None:
                master_plot = plot
            else:
                plot.setXLink(master_plot)

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

    def get_spike_data(self, channel: str, height_std=2.5, maximum_height_std=10.0, window_ms=2):
        """
        Returns spike analysis result for a channel.
        Computes it if not already cached.
        """

        if not hasattr(self, "_spike_cache"):
            self._spike_cache = {}

        if channel in self._spike_cache and self._spike_cache[channel]["height_std"] == height_std and self._spike_cache[channel]["window_ms"] == window_ms:
            return self._spike_cache[channel]["data"]

        # Compute and cache
        spike_result = self.controller.data.single_channel_spike_analysis_polars(
            channel=channel,
            extract_waveforms=True,
            height_std=height_std,
            maximum_height_std=maximum_height_std,
            waveform_width_ms=window_ms,
            min_distance_ms = 1 /500 * self.controller.data.fs
        )

        self._spike_cache[channel] = {
            "data": spike_result,
            "height_std": height_std,
            "window_ms": window_ms
        }

        return spike_result

    def apply_single_channel_analysis(self):
        analysis = self.singleAnalysisCombo.currentText()
        channel_names = self.controller.channel_names.values() if self.controller.channel_names else self.controller.data.filter_ch
        if analysis == "Single Channel Spike Detection":
            param_spec = {
                "channel": {
                    "type": "choice",
                    "options": channel_names,
                    "label": "Channel",
                    "default": list(channel_names)[0] if channel_names else None,
                },
                "threshold_std": {
                    "type": "float",
                    "label": "Spike Threshold (std)",
                    "default": self.min_threshold_std,
                    "min": 0,
                    "max": 20,
                    "step": 0.1,
                },
                "maximum_height_std": {
                    "type": "float",
                    "label": "Maximum Spike Threshold (std)",
                    "default": self.maximum_height_std,
                    "min": 0,
                    "max": 50,
                    "step": 0.1,
                },
                "window_ms": {
                    "type": "int",
                    "label": "Waveform Window (ms)",
                    "default": 2,
                    "min": 1,
                    "max": 10,
                },
                # "polarity": {
                #     "type": "choice",
                #     "label": "Polarity",
                #     "options": ["negative", "positive", "both"],
                #     "default": "negative",
                # },
            }

            dialog = ParameterDialog(param_spec, parent=self)

            if dialog.exec_() != QDialog.Accepted:
                return  # User cancelled

            params = dialog.get_values()
            params["channel"] = self.controller.reverse_channel_names[params["channel"]]
            self.min_threshold_std = params["threshold_std"]
            self.maximum_height_std = params["maximum_height_std"]
            print("getting spike data")
            spike_data = self.get_spike_data(
                channel=params["channel"],
                height_std=params["threshold_std"],
                maximum_height_std=params["maximum_height_std"],
                window_ms=params["window_ms"]
            )
            # No spikes case
            if spike_data["indices"] is None or len(spike_data["indices"]) == 0:
                payload = {
                    "title": f"Spike Analysis – {params['channel']}",
                    "plots": [
                        {
                            "kind": "text",
                            "content": "No spikes detected for this channel."
                        }
                    ]
                }
            else:
                # Handle LazyFrame or DataFrame
                if hasattr(self.controller.data.referenced, 'select'):
                    # LazyFrame or DataFrame
                    series = self.controller.data.referenced.select(params["channel"]).collect().to_series()
                else:
                    # Fallback for other formats
                    series = self.controller.data.referenced[params["channel"]]
                
                fs = self.controller.data.fs
                max_points = 100000  # Safe visual size
                # ---- Downsample safely ----
            
                length = len(series)

                if length > max_points:
                    step = length // max_points
                    series_ds = series.gather_every(step)
                else:
                    step = 1
                    series_ds = series
                    
                x_ds = np.arange(len(series_ds))* step / fs
                y_channel = series_ds.to_numpy()
                payload = {
                    "title": f"Spike Analysis – {self.controller.get_channel_name(params['channel'])}",
                    "plots": [
                        {
                            "title": "Detected Spikes",
                            "kind":"plot",
                            "series": [
                                {
                                    "x": spike_data["times"],
                                    "y": spike_data["peaks"],
                                    "type": "scatter"
                                }, {
                                    "x": x_ds,
                                    "y": y_channel,
                                    "type": "line"

                                }
                            ],
                            "xlabel": "Time (s)",
                            "ylabel": "Amplitude (uV)",
                        }
                    ]
                }

                # Add waveform if available
                if spike_data["mean_waveform"] is not None:
                    payload["plots"].append({
                        "title": "Average Spike Waveform",
                        "series":[{
                            "x": np.arange(len(spike_data["mean_waveform"]))/fs*1000,
                            "y": spike_data["mean_waveform"],
                            "type": "line"
                        }],
                        "xlabel": "Time (ms)",
                        "ylabel": "Amplitude (uV)",
                        "kind": "plot",
                    })

                # Add ISI if available
                if spike_data["isi_ms"] is not None:
                    payload["plots"].append({
                        "title": "ISI Histogram",
                        "series": [{
                            "y": spike_data["isi_ms"],
                            "type": "hist"
                        }],
                        "xlabel": "Inter-Spike Interval (ms)",
                        "ylabel": "Count",
                        "kind": "plot",
                    })

            self.analysis_window = AnalysisWindow(payload, self)
            self.analysis_window.show()
        if analysis == "ISI Distribution":
                param_spec = {
                    "channel": {
                        "type": "choice",
                        "options": channel_names,
                        "label": "Channel",
                        "default": list(channel_names)[0] if channel_names else None,
                    },
                    "threshold_std": {
                        "type": "float",
                        "label": "Spike Threshold (std)",
                        "default": self.min_threshold_std,
                        "min": 0,
                        "max": 20,
                        "step": 0.1,
                    },
                    "maximum_height_std": {
                        "type": "float",
                        "label": "Maximum Spike Threshold (std)",
                        "default": self.maximum_height_std,
                        "min": 0,
                        "max": 50,
                        "step": 0.1,
                    },
                    "window_ms": {
                        "type": "int",
                        "label": "Waveform Window (ms)",
                        "default": 2,
                        "min": 1,
                        "max": 10,
                    },
                    "isi_bins_ms": {
                        "type": "int",
                        "label": "ISI Bin Size (ms)",
                        "default": 10,
                        "min": 1,
                        "max": 200,
                    },
                    "isi_range_ms": {
                        "type": "int",
                        "label": "Max ISI (ms)",
                        "default": 200,
                        "min": 10,
                        "max": 1000,
                    },
                    "window_size_sec": {
                        "type": "int",
                        "label": "Time Window Size (s)",
                        "default": 10,
                        "min": 10,
                        "max": 600,
                    },
                }

                dialog = ParameterDialog(param_spec, parent=self)

                if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

                params = dialog.get_values()
                params["channel"] = self.controller.reverse_channel_names[params["channel"]]
                self.min_threshold_std = params["threshold_std"]
                self.maximum_height_std = params["maximum_height_std"]
                spike_data = self.get_spike_data(
                    channel=params["channel"],
                    height_std=params["threshold_std"],
                    maximum_height_std=params["maximum_height_std"],
                    window_ms=params["window_ms"]
                )
                spike_times = spike_data["times"].to_numpy()
                isi_result = self.controller.data.compute_isi_distribution_over_time(
                    spike_times=spike_times,
                    bin_size_ms=params["isi_bins_ms"],
                    window_seconds=params["window_size_sec"],
                    isi_range_ms=params["isi_range_ms"],
                )
                print(isi_result)
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
                            "ylabel": "Inter-Spike Interval (ms)",
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
            param_spec = {
                        "channel": {
                            "type": "choice",
                            "options": channel_names,
                            "label": "Channel",
                            "default": list(channel_names)[0] if channel_names else None,
                        },
                        "min_threshold_std": {
                            "type": "float",
                            "label": "Spike Threshold (std)",
                            "default": self.min_threshold_std,
                            "min": 0,
                            "max": 20,
                            "step": 0.1,
                        },
                        "maximum_height_std": {
                            "type": "float",
                            "label": "Maximum Spike Threshold (std)",
                            "default": self.maximum_height_std,
                            "min": 0,
                            "max": 50,
                            "step": 0.1,
                        },
                        "window_ms": {
                            "type": "int",
                            "label": "Waveform Window (ms)",
                            "default": 2,
                            "min": 1,
                            "max": 10,
                        },
            }

            dialog = ParameterDialog(param_spec, parent=self)

            if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

            params = dialog.get_values()
            params["channel"] = self.controller.reverse_channel_names[params["channel"]]
            self.min_threshold_std = params["threshold_std"]
            self.maximum_height_std = params["maximum_height_std"]
            spike_data = self.get_spike_data(params["channel"], 
                                             height_std=params["min_threshold_std"], 
                                             maximum_height_std=params["maximum_height_std"], 
                                             window_ms=params["window_ms"])
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
                    "kind": "plot",
                    "title": f"Cluster {i} Mean Waveform",
                    "series": [{
                        "x": np.arange(len(mean_wf)),
                        "y": mean_wf,
                        "type": "line"
                    }],
                    "xlabel": "Time (ms)",
                    "ylabel": "Amplitude (uV)",
                })
            for i, isi in enumerate(clustering_result["cluster_isi"]):
                if len(isi) == 0:
                    continue

                plots.append({
                    "kind": "plot",
                    "title": f"Cluster {i} ISI",
                    "series": [{
                        "y": isi,
                        "type": "hist",
                        "bins": 50
                    }],
                    "xlabel": "Inter-Spike Interval (ms)",
                    "ylabel": "Count",
                    
                })

            features = clustering_result["features"]
            labels = clustering_result["labels"]

            plots.append({
                "kind": "plot",
                "title": "Feature Space (Peak-to-Peak vs Energy)",
                "series": [{
                    "x": features[:, 0],
                    "y": features[:, 1],
                    "type": "scatter"
                }],
                "xlabel": "Peak-to-Peak (uV)",
                "ylabel": "Energy (uV^2)",
            })

            analysis_payload = {
                "title": "Spike Clustering Results",
                "plots": plots
            }

            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()
    import numpy as np


    def build_multi_channel_dashboard(self, results: dict, fs: float):
        """
        Convert multi-channel spike analysis results into a dashboard payload.

        Parameters
        ----------
        results : dict
            Output of multi_channel_spike_analysis_polars()

        fs : float
            Sampling rate

        Returns
        -------
        dict
            analysis_payload for AnalysisWindow
        """

        plots = []

        channels = []
        raster_x = []
        raster_y = []

        firing_rates = []
        channel_labels = []

        # ------------------------------------------------
        # Raster + firing rate preparation
        # ------------------------------------------------

        for idx, (ch, res) in enumerate(results.items()):

            if res["indices"] is None:
                continue

            spike_times = res["times"]

            if spike_times is None or len(spike_times) == 0:
                continue

            channels.append(ch)

            # Raster coordinates
            raster_x.extend(spike_times)
            raster_y.extend([idx] * len(spike_times))

            # Firing rate
            duration = spike_times[-1] if len(spike_times) > 0 else 1
            rate = len(spike_times) / duration

            firing_rates.append(rate)
            channel_labels.append(ch)

            # ------------------------------------------------
            # ISI histogram per channel
            # ------------------------------------------------

            isi = res.get("isi_ms")

            if isi is not None and len(isi) > 0:

                plots.append({
                    "kind": "plot",
                    "title": f"{ch} ISI Distribution",
                    "series": [{
                        "y": isi,
                        "type": "hist",
                        "bins": 50
                    }],
                    
                    "xlabel": "Inter-Spike Interval (ms)",
                    "ylabel": "Count"
                })

            # ------------------------------------------------
            # Mean spike waveform
            # ------------------------------------------------

            mean_wf = res.get("mean_waveform")

            if mean_wf is not None:

                x = np.arange(len(mean_wf)) / fs * 1000

                plots.append({
                    "kind": "plot",
                    "title": f"{ch} Mean Spike Waveform",
                    "series": [{
                        "x": x,
                        "y": mean_wf,
                        "type": "line"
                        
                    }],
                    "xlabel": "Time (ms)",
                    "ylabel": "Amplitude (uV)"
                })

        # ------------------------------------------------
        # Spike raster plot
        # ------------------------------------------------

        if len(raster_x) > 0:

            plots.insert(0, {
                "kind": "plot",
                "title": "Spike Raster",
                "series": [{
                    "x": np.array(raster_x),
                    "y": np.array(raster_y),
                    "type": "scatter",

                }],
                "xlabel": "Time (s)",
                "ylabel": "Channel Index",
                "time_axis": True
            })

        # ------------------------------------------------
        # Channel firing rate bar chart
        # ------------------------------------------------

        if len(firing_rates) > 0:

            plots.insert(1, {
                "kind": "plot",
                "title": "Channel Firing Rates",
                "series": [{
                    "x": np.arange(len(firing_rates)),
                    "y": firing_rates,
                    "type": "bar"
                }],
                "xlabel": "Channel",
                "ylabel": "Rate (Hz)",
                "labels": channel_labels
            })

        # ------------------------------------------------
        # Population firing rate
        # ------------------------------------------------

        all_spikes = []

        for res in results.values():

            if res["times"] is not None:
                all_spikes.extend(res["times"])

        if len(all_spikes) > 0:

            all_spikes = np.array(all_spikes)

            bins = np.linspace(0, all_spikes.max(), 200)
            hist, edges = np.histogram(all_spikes, bins=bins)

            plots.insert(2, {
                "kind": "plot",
                "title": "Population Firing Rate",
                "series": [{
                    "x": (edges[:-1] + edges[1:]) / 2,
                    "y": hist,
                    "type": "hist"
                }],
                "xlabel": "Time (s)",
                "ylabel": "Spike Count"
            })

        analysis_payload = {
            "title": "Multi-Channel Neural Analysis",
            "plots": plots
        }

        return analysis_payload
    def build_spatial_correlation_payload(self, result):

        distances = np.array(result["distances"])
        correlations = np.array(result["correlations"])
        channel_pairs = result["pairs"]

        slope = result["slope"]
        intercept = result["intercept"]

        # ---- Ensure sorted for clean line rendering ----
        # order = np.argsort(distances)
        # distances = distances[order]
        # correlations = correlations[order]

        fit = slope * distances + intercept

        plots = [
            {
                "kind": "plot",
                "title": "Spatial Spike Correlation vs Distance",
                "xlabel": "Distance (mm)",
                "ylabel": "Normalized Max Cross-Correlation",
                "grid": False,

                "series": [
                    {
                        "type": "scatter",
                        "x": distances,
                        "y": correlations,
                        "name": "Observed Correlation",
                        "labels": channel_pairs
                    },
                    {
                        "type": "line",
                        "x": distances,
                        "y": fit,
                        "name": (f"Linear Fit: y = {slope:.4f}x + {intercept:.4f}")
                    }
                ],

            }
        ]

        return {
            "title": "Spatial Neural Correlation",
            "plots": plots
        }

    def build_propagation_payload(self, result):

        plots = []

        distances = []
        pos = []
        neg = []

        for dist, counts in result["directionality_counts"].items():

            distances.append(dist)
            pos.append(counts["positive"])
            neg.append(counts["negative"])

        distances = np.array(distances)
        pos = np.array(pos)
        neg = np.array(neg)

        plots.append({
            "kind": "plot",
            "title": "Spike Propagation Directionality",
            "series": [{
                "type": "line",
                "x": distances,
                "y": pos,
                "name": "Forward Spikes"
            },{
                "type": "line",
                "x": distances,
                "y": neg,
                "name": "Reverse Spikes"
            }],
            "xlabel": "Distance (mm)",
            "ylabel": "Forward Spikes"
        })

        return {
            "title": "Neural Spike Propagation",
            "plots": plots
        }
    def apply_multi_channel_analysis(self):
        analysis = self.multiAnalysisCombo.currentText()
        channel_names = self.controller.channel_names.values() if self.controller.channel_names else self.controller.data.filter_ch
        if analysis == "Multiple Channel Spike Detection":
            param_spec = {
                        "channels": {
                            "type": "multichoice",
                            "options": channel_names,
                            "label": "Channels",
                            "default": list(channel_names)[0] if channel_names else None,
                        },
                        "threshold_std": {
                            "type": "float",
                            "label": "Spike Threshold (std)",
                            "default": 4.5,
                            "min": 0,
                            "max": 20,
                            "step": 0.1,
                        },
                        "maximum_height_std": {
                            "type": "float",
                            "label": "Maximum Spike Threshold (std)",
                            "default": 10.0,
                            "min": 0,
                            "max": 50,
                            "step": 0.1,
                        },

                        "window_ms": {
                            "type": "int",
                            "label": "Waveform Window (ms)",
                            "default": 2,
                            "min": 1,
                            "max": 10,
                        },
            }
            dialog = ParameterDialog(param_spec, parent=self)

            if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

            params = dialog.get_values()
            params["channels"] = [self.controller.reverse_channel_names[ch] for ch in params["channels"]]
            results = self.controller.data.multi_channel_spike_analysis_polars(
                channels=params["channels"],
                height_std=params["threshold_std"],
                maximum_height_std=params["maximum_height_std"],
                min_distance_ms=1/500 * self.controller.data.fs,
                window_ms=params["window_ms"]
            )
            analysis_payload = self.build_multi_channel_dashboard(results, fs=20000)

            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()
        if analysis == "Cross Correlation of Spike Trains":
            param_spec = {
                        "channels": {
                            "type": "multichoice",
                            "options": channel_names,
                            "label": "Channels",
                            "default": list(channel_names)[0] if channel_names else None,
                        },
                        "threshold_std": {
                            "type": "float",
                            "label": "Spike Threshold (std)",
                            "default": self.min_threshold_std,
                            "min": 0,
                            "max": 20,
                            "step": 0.1,
                        },
                        "maximum_height_std": {
                            "type": "float",
                            "label": "Maximum Spike Threshold (std)",
                            "default": self.maximum_height_std,
                            "min": 0,
                            "max": 50,
                            "step": 0.1,
                        },
                        "window_ms": {
                            "type": "int",
                            "label": "Waveform Window (ms)",
                            "default": 2,
                            "min": 1,
                            "max": 10,
                        },
            }
            dialog = ParameterDialog(param_spec, parent=self)

            if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

            params = dialog.get_values()
            params["channels"] = [self.controller.reverse_channel_names[ch] for ch in params["channels"]]
            self.min_threshold_std = params["threshold_std"]
            self.maximum_height_std = params["maximum_height_std"]
            spike_results = self.controller.data.multi_channel_spike_analysis_polars(
                channels=params["channels"],
                height_std=params["threshold_std"],
                maximum_height_std=params["maximum_height_std"],
                min_distance_ms=1/500 * self.controller.data.fs,
                window_ms=params["window_ms"]
            )
            spike_trains = {
                ch: spike_results[ch]["indices"]
                for ch in spike_results
            } if spike_results is not None else {}
            
            corr_result = self.controller.data.spatial_spike_correlation(
                spike_trains,
                correct_order=[16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]
            )                                                                   
            analysis_payload = self.build_spatial_correlation_payload(corr_result)
            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()

        if analysis == "Directionality Analysis":
            param_spec = {
                        "channels": {
                            "type": "multichoice",
                            "options": channel_names,
                            "label": "Channels",
                            "default": list(channel_names)[0] if channel_names else None,
                        },
                        "threshold_std": {
                            "type": "float",
                            "label": "Spike Threshold (std)",
                            "default": self.min_threshold_std,
                            "min": 0,
                            "max": 20,
                            "step": 0.1,
                        },
                        "window_ms": {
                            "type": "int",
                            "label": "Waveform Window (ms)",
                            "default": 2,
                            "min": 1,
                            "max": 10,
                        },
            }
            dialog = ParameterDialog(param_spec, parent=self)

            if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

            params = dialog.get_values()
            params["channels"] = [self.controller.reverse_channel_names[ch] for ch in params["channels"]]
            results = self.controller.data.multi_channel_spike_analysis_polars(
                channels=params["channels"],
                height_std=params["threshold_std"],
                min_distance_ms=1/500 * self.controller.data.fs,
                window_ms=params["window_ms"]
            )

            spike_times_ms = {
                ch: results[ch]["times"] * 1000
                for ch in results
                if results[ch]["times"] is not None
            }
            directionality_result = self.controller.data.spike_propagation_directionality(
                spike_times_ms=spike_times_ms,
                correct_order=[16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
                max_delay_ms=7
            )
            analysis_payload = self.build_propagation_payload(directionality_result)
            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()
            
        if analysis == "Propagation Coefficient":
            param_spec = {
                        "channels": {
                            "type": "multichoice",
                            "options": channel_names,
                            "label": "Channels",
                            "default": list(channel_names)[0] if channel_names else None,
                        },
                        "threshold_std": {
                            "type": "float",
                            "label": "Spike Threshold (std)",
                            "default": self.min_threshold_std,
                            "min": 0,
                            "max": 20,
                            "step": 0.1,
                        },
                        "maximum_height_std": {
                            "type": "float",
                            "label": "Maximum Spike Threshold (std)",
                            "default": self.maximum_height_std,
                            "min": 0,
                            "max": 50,
                            "step": 0.1,
                        },
                        "window_ms": {
                            "type": "int",
                            "label": "Waveform Window (ms)",
                            "default": 2,
                            "min": 1,
                            "max": 10,
                        },
                        "window_length_min": {
                            "type": "int",
                            "label": "Rolling Window Length (min)",
                            "default": 1,
                            "min": 1,
                            "max": 10,
                        },
            }
            dialog = ParameterDialog(param_spec, parent=self)

            if dialog.exec_() != QDialog.Accepted:
                    return  # User cancelled

            params = dialog.get_values()
            self.min_threshold_std = params["threshold_std"]
            self.maximum_height_std = params["maximum_height_std"]
            params["channels"] = [self.controller.reverse_channel_names[ch] for ch in params["channels"]]
            spike_results = self.controller.data.multi_channel_spike_analysis_polars(
                channels=params["channels"],
                height_std=params["threshold_std"],
                maximum_height_std=params["maximum_height_std"],
                min_distance_ms=1/500 * self.controller.data.fs,
                window_ms=params["window_ms"]
            )
            spike_trains = {
                ch: spike_results[ch]["times"] * 1000
                for ch in spike_results
            }
            result = self.controller.data.rolling_propagation_index(
                spike_trains,
                correct_order=[16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
                window_length_min = params["window_length_min"],
                step_size_min = 1,
                c2c_mm = 4.5,
                max_delay_ms = 2,
                bin_range=(-2, 2),
                bin_width=0.002
            )                                                                   

            series = []

            for i, pair in enumerate(result["pairs"]):
                dist = result.get("electrode_distances", {}).get(pair, None)
                name = f"PI {pair[0]}-{pair[1]}"
                if dist is not None:
                    name = f"{name} ({dist:.2f} mm)"
                series.append({
                    "type": "line",
                    "name": name,
                    "x": result["periods_min"],
                    "y": result["pi_storage"][pair],
                })

            analysis_payload = {
                "title": "Rolling Propagation Index",
                "plots": [
                    {
                        "kind": "plot",
                        "title": "Rolling Propagation Index",
                        "series": series,
                        "xlabel": "Time (min)",
                        "ylabel": "Propagation Index"
                    }
                ]
            }
            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()
            
    def handleChannelDisplayButton(self):
        self.channel_window = ChannelDisplayWindow(self.controller)
        self.channel_window.show()