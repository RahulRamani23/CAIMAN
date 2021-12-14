from windows.param_window.param_widget import ParamWidget


class GreedyROIParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Greedy ROI Initialization Parameters")

        self.controller = controller

        self.add_param_checkbox(label_name="Rolling Max", name="rolling_max", clicked=self.toggle_rolling_max,
                                description="Detect new components based on a rolling sum of pixel activity (default: True).",
                                num=0, related_params=['rolling_length'])
        self.add_param_slider(label_name="Rolling Length", name="rolling_length", minimum=1, maximum=200,
                              value=self.controller.params()['rolling_length'], moved=self.update_param, num=1,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Length of rolling window (default: 100).", int_values=True)
        self.add_param_slider(label_name="Num Iterations", name="n_iter", minimum=1, maximum=100,
                              value=self.controller.params()['n_iter'], moved=self.update_param, num=2, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Number of iterations when refining estimates (default: 5).", int_values=True)
        self.add_param_slider(label_name="Neuron Half-Size", name="half_size", minimum=1, maximum=50,
                              value=self.controller.params()['half_size'], moved=self.update_param, num=3, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Expected half-size of neurons (pixels).", int_values=True)

        self.main_layout.addStretch()

    def toggle_rolling_max(self, boolean, checkbox, related_params=[]):
        self.controller.params()['rolling_max'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())