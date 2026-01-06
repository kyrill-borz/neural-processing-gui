class AppController:
    def __init__(self):
        self.data = None
        self.filt_config = None

    def load_data(self, path):
        from functionality import apploadfilepolars, filt_config
        self.filt_config = filt_config
        self.filt_config['W'] = [300, 500] 
        self.filt_config['Butterworth']['Wn'] = filt_config['W']
        self.data = apploadfilepolars(path, map_path=r"C:\Users\kyril\Documents\Cambridge\NeuralGui\neural-processing-gui\data\map_linear.csv")
        return self.data

    def apply_filter(self, filter_type='Butterworth'):
        self.data.filter_ch = ["ch_24","ch_25","ch_26","ch_27", "ch_28", "ch_29", "ch_30", "ch_31"]
        self.data.apply_filter = filter_type
        print(self.data.filter_ch)
        self.data.filter(
            self.data.original,
            self.data.apply_filter,
            self.data.filter_ch,
            **self.filt_config[self.data.apply_filter]
        )

    def apply_referencing(self, method):
        self.data.apply_referencing(method)