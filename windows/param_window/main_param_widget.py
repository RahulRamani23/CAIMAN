from windows.param_window.param_widget import ParamWidget


class MainParamWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "Preview Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Gamma", name="gamma", minimum=1, maximum=500,
                              value=self.controller.gui_params['gamma'] * 100, moved=self.preview_gamma, num=0,
                              multiplier=100, released=self.update_param, description="Gamma of the video preview.")
        self.add_param_slider(label_name="Contrast", name="contrast", minimum=1, maximum=500,
                              value=self.controller.gui_params['contrast'] * 100, moved=self.preview_contrast, num=1,
                              multiplier=100, released=self.update_param, description="Contrast of the video preview.")
        self.add_param_slider(label_name="FPS", name="fps", minimum=1, maximum=60,
                              value=self.controller.gui_params['fps'], moved=self.update_param, num=2,
                              released=self.update_param, description="Frames per second of the video preview.",
                              int_values=True)
        self.add_param_slider(label_name="Z", name="z", minimum=0, maximum=0, value=self.controller.z,
                              moved=self.update_param, num=3, released=self.update_param,
                              description="Z plane of the video preview.", int_values=True)

        self.setFixedHeight(120)

    def preview_contrast(self):
        contrast = self.param_sliders["contrast"].sliderPosition() / float(self.param_slider_multipliers["contrast"])

        self.controller.preview_contrast(contrast)

    def preview_gamma(self):
        gamma = self.param_sliders["gamma"].sliderPosition() / float(self.param_slider_multipliers["gamma"])

        self.controller.preview_gamma(gamma)