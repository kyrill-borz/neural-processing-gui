class AppController:
    def __init__(self):
        self.data = None
        self.filt_config = None

    def load_data(self, path):
        from functionality import apploadfilepolars, filt_config
        self.filt_config = filt_config
        self.filt_config['butter']['Wn'] = filt_config['W']
        self.data = apploadfilepolars(path)
        return self.data

    def apply_filter(self):
        self.data.filter_ch = ["ch_27"]
        self.data.apply_filter = 'butter_lowpass'
        print(self.data.apply_filter)
        self.data.filter(
            self.data.original,
            self.data.apply_filter,
            **self.filt_config[self.data.apply_filter]
        )

    def apply_referencing(self, method):
        self.data.apply_referencing(method)