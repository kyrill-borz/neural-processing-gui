import pyqtgraph as pg
from PyQt5.QtWidgets import (QWidget, QGridLayout, QComboBox, QDialogButtonBox,
                             QCheckBox, QPushButton, QMessageBox, QDialog)
from PyQt5.QtCore import Qt
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
            glucose_df = pd.read_csv(csv_path)

            # Validate required columns
            if 'time' not in glucose_df.columns or 'glucose' not in glucose_df.columns:
                raise ValueError("CSV must contain 'time' and 'glucose' columns")

            # Get spike data for selected channels
            series = []
            data = self.controller.data.referenced[channel]
            for i, channel in enumerate(selected_channel_names):
                series.append({
                    "type": "line",
                    "name": channel,
                    "x": data["time"],
                    "y": data[channel],
                })

            analysis_payload = {
                "title": "Signals vs Glucose Comparison",
                "plots": [
                    {
                        "kind": "plot",
                        "title": "Signals",
                        "series": series,
                        "xlabel": "Time (min)",
                        "ylabel": "uV"
                    },
                    {"kind": "plot",
                     "title": "Glucose Levels",
                     "series": [
                         {
                             "type": "line",
                             "name": "Glucose",
                             "x": glucose_df["time"],
                             "y": glucose_df["glucose"],
                         }
                     ],
                     "xlabel": "Time (min)",
                     "ylabel": "Glucose (mg/dL)"
                    }
                ]
            }
            self.analysis_window = AnalysisWindow(analysis_payload, self)
            self.analysis_window.show()


        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process data: {str(e)}")