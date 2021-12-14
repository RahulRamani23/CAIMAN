from windows.param_window.param_widget import ParamWidget


class GraphNMFParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Graph NMF Initialization Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Lambda", name="lambda_gnmf", minimum=1, maximum=100,
                              value=self.controller.params()['alpha_snmf'] * 10, moved=self.update_param, num=0,
                              multiplier=10, pressed=self.update_param, released=self.update_param,
                              description="Regularization weight for graph NMF (default: 1).", int_values=False)
        self.add_param_slider(label_name="Sigma Smooth", name="sigma_smooth_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['sigma_smooth_snmf'] * 100, moved=self.update_param, num=1,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Smoothing along z,x, and y (default: 0.5).", int_values=False)
        self.add_param_slider(label_name="Max Iterations", name="max_iter_snmf", minimum=1, maximum=1000,
                              value=self.controller.params()['max_iter_snmf'], moved=self.update_param, num=2,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum SNMF iterations (default: 500).", int_values=True)
        self.add_param_slider(label_name="Percent Baseline", name="perc_baseline_snmf", minimum=1, maximum=100,
                              value=self.controller.params()['perc_baseline_snmf'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Percentile to remove from movie before NMF (default: 20).", int_values=True)
        self.add_param_checkbox(label_name="SC Normalize", name="sc_normalize", clicked=self.toggle_sc_normalize,
                                description="Standardize entries prior to computing affinity matrix (default: True).",
                                num=4, related_params=[])
        self.add_param_checkbox(label_name="SC Use NN", name="sc_use_nn", clicked=self.toggle_sc_use_nn,
                                description="Sparsify affinity matrix by using only nearest neighbors (default: True).",
                                num=5, related_params=[])
        self.add_param_slider(label_name="SC Threshold", name="sc_threshold", minimum=0, maximum=1000,
                              value=self.controller.params()['sc_threshold'] * 100, moved=self.update_param, num=6,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Threshold for affinity matrix (default: 0).", int_values=False)
        self.add_param_slider(label_name="SC Sigma", name="sc_sigma", minimum=1, maximum=1000,
                              value=self.controller.params()['sc_sigma'] * 100, moved=self.update_param, num=7,
                              multiplier=100, pressed=self.update_param, released=self.update_param,
                              description="Standard deviation for SC kernel (default: 1).", int_values=False)

        self.main_layout.addStretch()

    def toggle_sc_normalize(self, boolean, checkbox, related_params=[]):
        self.controller.params()['sc_normalize'] = boolean

    def toggle_sc_use_nn(self, boolean, checkbox, related_params=[]):
        self.controller.params()['sc_use_nn'] = boolean