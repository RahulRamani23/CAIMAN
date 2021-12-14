from windows.param_window.param_widget import ParamWidget
from windows.param_window.graph_nmf_param_widget import GraphNMFParamWidget
from windows.param_window.pca_ica_param_widget import PCAICAParamWidget
from windows.param_window.sparse_nmf_param_widget import SparseNMFParamWidget
from windows.param_window.greedy_roi_param_widget import GreedyROIParamWidget


class CNMFROIFindingWidget(ParamWidget):
    def __init__(self, parent_widget, controller):
        ParamWidget.__init__(self, parent_widget, controller, "CNMF Parameters")

        self.controller = controller

        self.add_param_slider(label_name="Autoregressive Model Order", name="autoregressive_order", minimum=0,
                              maximum=2, value=self.controller.params()['autoregressive_order'],
                              moved=self.update_param, num=0, multiplier=1, pressed=self.update_param,
                              released=self.update_param, description="Order of the autoregressive model (0, 1 or 2).",
                              int_values=True)
        self.add_param_slider(label_name="Background Components", name="num_bg_components", minimum=1, maximum=100,
                              value=self.controller.params()['num_bg_components'], moved=self.update_param, num=1,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Number of background components.", int_values=True)
        self.add_param_slider(label_name="Merge Threshold", name="merge_threshold", minimum=1, maximum=200,
                              value=self.controller.params()['merge_threshold'] * 200, moved=self.update_param, num=2,
                              multiplier=200, pressed=self.update_param, released=self.update_param,
                              description="Merging threshold (maximum correlation allowed before merging two components).",
                              int_values=False)
        self.add_param_slider(label_name="Components", name="num_components", minimum=1, maximum=5000,
                              value=self.controller.params()['num_components'], moved=self.update_param, num=3,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Number of components expected (if using patches, in each patch; otherwise, in the entire FOV).",
                              int_values=True)
        self.add_param_slider(label_name="HALS Iterations", name="hals_iter", minimum=1, maximum=100,
                              value=self.controller.params()['hals_iter'], moved=self.update_param, num=4, multiplier=1,
                              pressed=self.update_param, released=self.update_param,
                              description="Number of HALS iterations following initialization (default: 5).",
                              int_values=True)
        self.add_param_checkbox(label_name="Use Patches", name="use_patches", clicked=self.toggle_use_patches,
                                description="Whether to use patches when performing CNMF.", num=5,
                                related_params=['cnmf_patch_size', 'cnmf_patch_stride'])
        self.add_param_slider(label_name="Patch Size", name="cnmf_patch_size", minimum=1, maximum=100,
                              value=self.controller.params()['cnmf_patch_size'], moved=self.update_param, num=6,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Size of each patch (pixels).", int_values=True)
        self.add_param_slider(label_name="Patch Stride", name="cnmf_patch_stride", minimum=1, maximum=100,
                              value=self.controller.params()['cnmf_patch_stride'], moved=self.update_param, num=7,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Stride for each patch (pixels).", int_values=True)
        self.add_param_slider(label_name="Max Merge Area", name="max_merge_area", minimum=1, maximum=500,
                              value=self.controller.params()['max_merge_area'], moved=self.update_param, num=8,
                              multiplier=1, pressed=self.update_param, released=self.update_param,
                              description="Maximum area of merged ROI above which ROIs will not be merged (pixels).",
                              int_values=True)
        self.add_param_chooser(label_name="Initialization Method", name="init_method",
                               options=["Greedy ROI", "Sparse NMF", "PCA/ICA", "Graph NMF"],
                               callback=self.set_init_method, num=9,
                               description="Method to use to initialize ROI locations.")

        self.greedy_roi_param_widget = GreedyROIParamWidget(self.parent_widget, self.controller)
        self.sparse_nmf_param_widget = SparseNMFParamWidget(self.parent_widget, self.controller)
        self.pca_ica_param_widget = PCAICAParamWidget(self.parent_widget, self.controller)
        self.graph_nmf_param_widget = GraphNMFParamWidget(self.parent_widget, self.controller)
        self.main_layout.addWidget(self.greedy_roi_param_widget)
        self.main_layout.addWidget(self.sparse_nmf_param_widget)
        self.main_layout.addWidget(self.pca_ica_param_widget)
        self.main_layout.addWidget(self.graph_nmf_param_widget)

        self.init_param_widgets = [self.greedy_roi_param_widget, self.sparse_nmf_param_widget,
                                   self.pca_ica_param_widget, self.graph_nmf_param_widget]

        self.show_selected_init_method_params()

        self.main_layout.addStretch()

    def tab_selected(self):
        index = self.tab_widget.currentIndex()
        if index == 0:
            self.set_init_method("greedy_roi")

    def toggle_use_patches(self, boolean, checkbox, related_params=[]):
        self.controller.params()['use_patches'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())

    def toggle_use_hals(self, boolean, checkbox, related_params=[]):
        self.controller.params()['use_hals'] = boolean

        if len(related_params) > 0:
            for related_param in related_params:
                self.param_widgets[related_param].setEnabled(checkbox.isChecked())

    def set_init_method(self, i):
        methods = ['greedy_roi', 'sparse_nmf', 'pca_ica', 'graph_nmf']

        self.controller.params()['init_method'] = methods[i]

        self.show_selected_init_method_params()

    def show_selected_init_method_params(self):
        i = self.param_choosers['init_method'].currentIndex()
        print(i)
        for j in range(len(self.init_param_widgets)):
            if i == j:
                self.init_param_widgets[j].show()
            else:
                self.init_param_widgets[j].hide()
