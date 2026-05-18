import pyqtgraph as pg
from PyQt5.QtWidgets import (QWidget, QGridLayout, QComboBox, QDialogButtonBox,
                             QCheckBox, QPushButton, QMessageBox, QDialog)
from PyQt5.QtCore import Qt
import numpy as np
import pandas as pd
from ui.widgets.FunctionPopup import ParameterDialog
from ui.analysis.analysis_window import AnalysisWindow

class ProcessingTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        """Create the Network page UI."""
        layout = QGridLayout(self)
        layout.addWidget(QPushButton("Glucose Comparison"),0,0)

        # Connect the Glucose Comparison button
        glucose_btn = layout.itemAtPosition(0, 0).widget()
        glucose_btn.clicked.connect(self.on_glucose_comparison)


        self.btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

    def on_glucose_comparison(self):
        """Handle Glucose Comparison button click."""
        if self.controller.data is None:
            QMessageBox.warning(self, "No Data", "Please load data first.")
            return

        # Build parameter spec for channel selection and file import
        channel_names = list(self.controller.channel_names.values())

        param_spec = {
            "channels": {
                "label": "Select Channels",
                "type": "multichoice",
                "options": sorted(channel_names),
                "default": []
            },
            "glucose_file": {
                "label": "Glucose CSV File",
                "type": "file",
                "file_type": "Glucose CSV",
                "file_filter": "CSV Files (*.csv);;All Files (*)"
            }
        }

        # Show dialog
        dialog = ParameterDialog(param_spec, title="Glucose Comparison", parent=self)

        if dialog.exec_() != QDialog.Accepted:
            return  # User cancelled

        # Get values
        values = dialog.get_values()

        selected_channel_names = values.get("channels", [])
        csv_path = values.get("glucose_file")

        # Validate selections
        if not selected_channel_names:
            QMessageBox.warning(self, "No Selection", "Please select at least one channel.")
            return

        if not csv_path:
            QMessageBox.warning(self, "No File", "No CSV file selected.")
            return

        # Map channel names back to channel IDs
        reverse_mapping = {v: k for k, v in self.controller.channel_names.items()}
        selected_channels = [reverse_mapping[name] for name in selected_channel_names]

        # Load and process data
        try:
            glucose_df = pd.read_csv(csv_path, delimiter=";", decimal=",")

            if 'glucose' not in glucose_df.columns:
                raise ValueError("CSV must contain 'glucose' column")

            glucose_df['glucose'] = pd.to_numeric(glucose_df['glucose'], errors='coerce')

            if 't_session_min' not in glucose_df.columns:
                raise ValueError("CSV must contain a time column like 't_session_min', 'time', or 'clock_time'")

            time_series = glucose_df['t_session_min']
            time_values = None

            if pd.api.types.is_numeric_dtype(time_series):
                time_values = pd.to_numeric(time_series, errors='coerce')
            else:
                time_values = pd.to_datetime(time_series, format="%H:%M:%S", errors='coerce')
                if time_values.isna().all():
                    time_values = pd.to_datetime(time_series, errors='coerce')

            if time_values.isna().all():
                for candidate in ['time', 'clock_time']:
                    if candidate in glucose_df.columns:
                        time_series = glucose_df[candidate]
                        time_values = pd.to_datetime(time_series, format="%H:%M:%S", errors='coerce')
                        if time_values.isna().all():
                            time_values = pd.to_datetime(time_series, errors='coerce')
                        if not time_values.isna().all():
                            break

            if time_values.isna().all() or glucose_df['glucose'].isna().all():
                raise ValueError("CSV time column must contain valid times and 'glucose' must be numeric")

            if pd.api.types.is_datetime64_any_dtype(time_values):
                start_time = time_values.iloc[0]
                glucose_df['t_session_min'] = (time_values - start_time).dt.total_seconds().astype(float)
            else:
                glucose_df['t_session_min'] = pd.to_numeric(time_values, errors='coerce').astype(float)

            glucose_df = glucose_df.dropna(subset=['t_session_min', 'glucose'])

            # Get spike data for selected channels
            series = []
            # Prefer referenced data if present, otherwise filtered or original
            if getattr(self.controller.data, 'referenced', None) is not None:
                signal_source = self.controller.data.referenced
            elif getattr(self.controller.data, 'filtered', None) is not None:
                signal_source = self.controller.data.filtered
            else:
                signal_source = self.controller.data.original

            def downsample(x, y, max_points=5000):
                if len(x) <= max_points:
                    return x, y
                indices = np.linspace(0, len(x) - 1, num=max_points, dtype=int)
                return x[indices], y[indices]

            if hasattr(signal_source, 'select'):
                # LazyFrame or DataFrame
                data = signal_source
                time_data = data.select("time").collect().to_series().to_numpy()
                time_data = np.asarray(time_data, dtype=float)
                channel_data = {}
                for channel_name in selected_channel_names:
                    ch = self.controller.reverse_channel_names[channel_name]
                    if ch in data.columns:
                        channel_data[ch] = np.asarray(
                            data.select(ch).collect().to_series().to_numpy(),
                            dtype=float
                        )
            else:
                # Fallback for other formats
                data = signal_source
                raw_time = data["time"]
                time_data = raw_time.to_numpy() if hasattr(raw_time, 'to_numpy') else raw_time
                time_data = np.asarray(time_data, dtype=float)
                channel_data = {}
                for channel_name in selected_channel_names:
                    ch = self.controller.reverse_channel_names[channel_name]
                    if ch in data.columns:
                        value = data[ch]
                        channel_data[ch] = np.asarray(
                            value.to_numpy() if hasattr(value, 'to_numpy') else value,
                            dtype=float
                        )

            for i, channel in enumerate(selected_channel_names):
                internal_ch = self.controller.reverse_channel_names[channel]
                x_ds, y_ds = downsample(time_data, channel_data[internal_ch])
                series.append({
                    "type": "line",
                    "name": channel,
                    "x": x_ds,
                    "y": y_ds,
                })

            glucose_x, glucose_y = downsample(
                glucose_df["t_session_min"].to_numpy(dtype=float),
                glucose_df["glucose"].to_numpy(dtype=float)
            )

            analysis_payload = {
                "title": "Signals vs Glucose Comparison",
                "plots": [
                    {
                        "kind": "plot",
                        "title": "Signals",
                        "series": series,
                        "xlabel": "Time (s)",
                        "ylabel": "uV"
                    },
                    {"kind": "plot",
                     "title": "Glucose Levels",
                     "series": [
                         {
                             "type": "line",
                             "name": "Glucose",
                             "x": glucose_x,
                             "y": glucose_y,
                         }
                     ],
                     "xlabel": "Time (s)",
                     "ylabel": "Glucose (mg/dL)"
                    }
                ]
            }
            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()


        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process data: {str(e)}")