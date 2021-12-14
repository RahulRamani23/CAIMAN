from windows.param_window.param_widget import ParamWidget


class Suite2pROIFindingWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Suite2p Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Diameter", name="diameter", minimum=1, maximum=100,
                              value=self.controller.params()['diameter'], moved=self.update_param, num=0, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Sampling Rate", name="sampling_rate", minimum=1, maximum=60,
                              value=self.controller.params()['sampling_rate'], moved=self.update_param, num=1,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_checkbox(label_name="Connected", name="connected", clicked=self.toggle_connected,
                                description="Whether to use a convolutional neural network for determining which ROIs are neurons.",
                                num=2)
        self.add_param_slider(label_name="Neuropil Basis Ratio", name="neuropil_basis_ratio", minimum=1, maximum=20,
                              value=self.controller.params()['neuropil_basis_ratio'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Neuropil Radius Ratio", name="neuropil_radius_ratio", minimum=1, maximum=50,
                              value=self.controller.params()['neuropil_radius_ratio'], moved=self.update_param, num=4,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Inner Neropil Radius", name="inner_neuropil_radius", minimum=1, maximum=50,
                              value=self.controller.params()['inner_neuropil_radius'], moved=self.update_param, num=5,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)
        self.add_param_slider(label_name="Min. Neuropil Pixels", name="min_neuropil_pixels", minimum=1, maximum=500,
                              value=self.controller.params()['min_neuropil_pixels'], moved=self.update_param, num=6,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Order of the autoregressive model (0, 1 or 2).", int_values=True)

        self.main_layout.addStretch()

    def toggle_connected(self, boolean):
        self.controller.params()['connected'] = boolean