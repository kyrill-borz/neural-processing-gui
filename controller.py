class AppController:
    def __init__(self):
        self.data = None
        self.filt_config = None
        self.channel_names = {}

    def load_data(self, path, start_min=0, dur_min=10, port="Port A"):
        from functionality import apploadfilepolars, filt_config
        self.filt_config = filt_config
        self.filt_config['W'] = [300, 500] 
        self.filt_config['Butterworth']['Wn'] = filt_config['W']
        self.data = apploadfilepolars(start_min, dur_min, path, port=port)
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

    def export(self, folder_path):
        # Implement export functionality here
        self.data.export(folder_path)
    
    def import_data_from_folder(self, folder_path):
        from utils.Neurogram import Recording
        self.data = Recording.load_from_folder(folder_path)
        self.make_channel_names()

    def make_channel_names(self):
        for i, channel in enumerate(self.data.filter_ch):
            self.channel_names[channel] = channel.replace("ch_", "Channel ") + (f" ({round(self.data.information['Z_magnitude_KOhms'].iloc[i],3)})" if self.data.information is not [] else " kOhms")
    
    def get_channel_name(self, channel):
        return self.channel_names[channel]