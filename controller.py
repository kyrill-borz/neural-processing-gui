class AppController:
    def __init__(self):
        self.data = None
        self.filt_config = None
        self.channel_names = {}

    def load_data(self, path, start_min=0, dur_min=10):
        from functionality import apploadfilepolars, filt_config
        self.filt_config = filt_config
        self.filt_config['W'] = [300, 500] 
        self.filt_config['Butterworth']['Wn'] = filt_config['W']
        self.data = apploadfilepolars(start_min, dur_min, path, map_path=r"C:\Users\kyril\Documents\Cambridge\NeuralGui\neural-processing-gui\data\map_linear.csv")
        self.data.filter_ch = ["ch_24","ch_25","ch_26","ch_27", "ch_28", "ch_29", "ch_30", "ch_31"]
        self.make_channel_names()
        return self.data

    def apply_filter(self, filter_type='Butterworth'):
        
        self.data.apply_filter = filter_type
        self.data.filter(
            self.data.original,
            self.data.apply_filter,
            self.data.filter_ch,
            **self.filt_config[self.data.apply_filter]
        )

    def apply_referencing(self, method):
        self.data.apply_referencing(method)

    def export(self):
        # Implement export functionality here
        pass

    def make_channel_names(self):
        for i, channel in enumerate(self.data.filter_ch):
            self.channel_names[channel] = channel.replace("ch_", "Channel ") + (f" ({self.data.Z_magnitude})" if self.data.Z_magnitude is not None else "")
        print("Z magnitude:", self.data.Z_magnitude)
    
    def get_channel_name(self, channel):
        return self.channel_names[channel]