from windows.param_window.param_widget import ParamWidget


class PCAICAParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "PCA/ICA Initialization Parameters")

        self.controller = controller

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

        self.main_layout.addStretch()