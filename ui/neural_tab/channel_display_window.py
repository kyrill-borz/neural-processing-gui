from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QCheckBox,
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class ChannelDisplayWindow(QWidget):
    def __init__(self, controller):
        super().__init__(None)
        self.setWindowFlag(Qt.Window)
        self.controller = controller
        self.setWindowTitle("Channel Selection")
        self.resize(900, 800)

        self.main_layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)

        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        self.populate_channels()

    # ---------------------------------------------------------
    # Populate Channel Rows
    # ---------------------------------------------------------

    def populate_channels(self):

        df = self.controller.data.filtered
        
        # Handle LazyFrame vs DataFrame
        if hasattr(df, 'collect'):
            # LazyFrame - need to collect for operations
            df_collected = df.collect()
            channels = [col for col in df_collected.columns if col.startswith('ch')]
        else:
            # DataFrame
            df_collected = df
            channels = [col for col in df.columns if col.startswith('ch')]
            
        print(channels)
        fs = self.controller.data.fs
        max_points = 10000  # Safe visual size

        for ch in channels:

            row_layout = QHBoxLayout()

            # ---- Downsample safely ----
            if hasattr(df, 'collect'):
                # LazyFrame - collect the specific column
                series = df.select(ch).collect().to_series()
            else:
                # DataFrame
                series = df[ch]
                
            length = len(series)

            if length > max_points:
                step = length // max_points
                series_ds = series.gather_every(step)
            else:
                step = 1
                series_ds = series

            y = series_ds.to_numpy()

            # ---- Plot ----
            plot = pg.PlotWidget()
            plot.setFixedHeight(120)
            plot.plot(y, pen="b")
            plot.getAxis('left').setLabel('Amplitude (uV)', color='#2a2a2a')

            plot.setMouseEnabled(x=False, y=False)
            plot.hideAxis("left")
            plot.hideAxis("bottom")

            # Scale X axis
            plot.getAxis("bottom").setScale(step / fs)

            # ---- Checkbox ----
            checkbox = QCheckBox(ch)

            # Default checked if already in selected channels
            if ch in getattr(self.controller.data, "channels", []):
                checkbox.setChecked(True)

            checkbox.stateChanged.connect(
                lambda state, channel=ch: self.update_channel_selection(channel, state)
            )

            # ---- Assemble row ----
            row_layout.addWidget(plot)
            row_layout.addWidget(checkbox)

            self.container_layout.addLayout(row_layout)

        self.container_layout.addStretch()

    def update_channel_selection(self, channel, state):

        # Ensure channels attribute exists and is a list
        if not isinstance(getattr(self.controller.data, "channels", None), list):
            self.controller.data.channels = []

        if state:  # Checked
            if channel not in self.controller.data.channels:
                self.controller.data.channels.append(channel)
        else:  # Unchecked
            if channel in self.controller.data.channels:
                self.controller.data.channels.remove(channel)