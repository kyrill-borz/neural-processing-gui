class AppController:
    def __init__(self):
        self.data = None
        self.filt_config = None
        self.channel_names = {}
        self.reverse_channel_names = {}

    def load_data(self, path, start_min=0, dur_min=10, port="Port A"):
        from functionality import apploadfilepolars, filt_config
        self.filt_config = filt_config
        self.filt_config['W'] = [300, 500] 
        self.filt_config['Butterworth']['Wn'] = filt_config['W']
        self.data = apploadfilepolars(start_min, dur_min, path, port=port)
        columns = None
        if hasattr(self.data, "columns"):
            columns = self.data.columns
        elif hasattr(self.data, "original") and hasattr(self.data.original, "columns"):
            columns = self.data.original.columns
        elif hasattr(self.data, "recording") and hasattr(self.data.recording, "columns"):
            columns = self.data.recording.columns

        self.data.filter_ch = [col for col in columns if col.startswith("ch")] if columns else []
        print(self.data.filter_ch)
        self.make_channel_names()
        return self.data

    def apply_filter(self, filter_type='Butterworth', filter_params=100):
        
        self.data.apply_filter = filter_type
        self.filt_config[filter_type]['Wn'] = filter_params
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
            try:
                self.channel_names[channel] = channel.replace("ch_", "Channel ") + (f" ({round(self.data.information['Z_magnitude_KOhms'].iloc[i],3)} KOhms)" if self.data.information is not [] else " kOhms")
            except:
                self.channel_names[channel] = channel.replace("ch_", "Channel ")

        self.reverse_channel_names = {v: k for k, v in self.channel_names.items()}
                
    def get_channel_name(self, channel):
        return self.channel_names[channel]