import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import tifffile
import csv
from scipy.stats.stats import pearsonr
from sklearn import linear_model
from matplotlib.widgets import Slider, CheckButtons
from scipy.signal import convolve, deconvolve
from scipy.interpolate import interp1d
from matplotlib import cm
import matplotlib.patches as mpatches
import cv2

import scipy
import os

tail_fps     = 349.0
calcium_fps  = 3
tail_calcium_offset = 0
frame_ratio  = tail_fps/calcium_fps

def get_bout_data(bout_fname, calcium_fps, n_frames, tail_calcium_offset=0):
    '''
    Given a filename containing labeled tail bouts, returns a dictionary of the format:

    {
        "bout name": [ [start frame, end frame], [start frame, end frame], ... ]
    }

    where start and end frames refer to frames in the corresponding calcium imaging recording.

    Arguments:

    bout_fname (str): The filename of a CSV containing labeled bouts. The CSV is expected
                      to be comma-delimited, to have a header row (which is skipped) and
                      one line for each labeled bout, with the following format:

                      bout name,start time,end time

                      where start and end times are in seconds.

    calcium_fps (float): The frames per second of the calcium imaging recording.

    n_frames (int): Number of frames in the calcium imaging recording.

    tail_calcium_offset (float): The offset (in calcium imaging frames) between the start of the
                                 tail recording and the start of the calcium imaging recording.
                                 (eg. a value of 1 means the tail recording started 1 frame *before*
                                 the calcium imaging recording.)

    Returns:

    bouts (dict): The dictionary of bout names and a list of their corresponding start and end frames.

    '''

    bouts = {}

    if bout_fname is not None:
        with open(bout_fname, newline='') as f:
            # extract lines from CSV file
            reader = csv.reader(f, delimiter=",")
            lines = [line.split(',') for line in f if line.strip()]

            for i in range(len(lines)):
                line = lines[i]

                # skip the first line (assuming it's a header row)
                if i > 0 and len(line) > 0:
                    bout_name = line[0]
                    if bout_name not in bouts.keys():
                        bouts[bout_name] = []
                    
                    bout_window = [float(line[1]), float(line[2])]
                    start_frame = max(0, int(round(bout_window[0]*calcium_fps)) - tail_calcium_offset)
                    end_frame   = min(n_frames-1, int(round(bout_window[1]*calcium_fps)) - tail_calcium_offset)
                    
                    bouts[bout_name].append([start_frame, end_frame])

    return bouts

def get_stimuli_data(frame_timestamp_fname, calcium_fps, n_frames, tail_calcium_offset=0):
    stimuli = {}

    if frame_timestamp_fname is not None:
        with open(frame_timestamp_fname, 'r') as f:
            data = f.readlines()

            # print(data)

            for i in range(1, len(data)):
                items = data[i].rstrip().split(',')

                # print(items)

                time        = float(items[0])
                stim_num    = int(items[1])
                stim_name   = items[2]
                stim_type   = items[3]
                stim_params = items[4].split('; ')

                # print(stim_params)


                # covert time to calcium frame
                time = int(time*calcium_fps/1000.0) + tail_calcium_offset

                if 0 <= time < n_frames and stim_type in ['Delay', 'White Flash', 'Black Flash', 'Looming Dot', 'Moving Dot', 'Combined Dots', 'Grating', 'Optomotor Grating', 'Broadband Grating']:
                    if stim_type not in stimuli.keys():
                        stimuli[stim_type] = {'time': [time]}

                        if stim_type == 'Looming Dot':
                            radius = float(stim_params[0].split('radius: ')[1])
                            stimuli[stim_type]['radius'] = [radius]
                        elif stim_type == 'Moving Dot':
                            x = float(stim_params[0].split('x: ')[1])
                            y = float(stim_params[1].split('y: ')[1])
                            stimuli[stim_type]['x'] = [x]
                            stimuli[stim_type]['y'] = [y]
                        elif stim_type == 'Combined Dots':
                            radius = float(stim_params[0].split('looming dot radius: ')[1])
                            x = float(stim_params[0].split('moving dot x: ')[1])
                            y = float(stim_params[1].split('moving dot y: ')[1])
                            stimuli[stim_type]['radius'] = [radius]
                            stimuli[stim_type]['x'] = [x]
                            stimuli[stim_type]['y'] = [y]
                        elif stim_type in ['Grating', 'Optomotor Grating', 'Broadband Grating']:
                            phase = float(stim_params[0].split('phase: ')[1])
                            stimuli[stim_type]['phase'] = [phase]
                    else:
                        if time not in stimuli[stim_type]['time']:
                            stimuli[stim_type]['time'].append(time)

                            if stim_type == 'Looming Dot':
                                radius = float(stim_params[0].split('radius: ')[1])
                                stimuli[stim_type]['radius'].append(radius)
                            elif stim_type == 'Moving Dot':
                                x = float(stim_params[0].split('x: ')[1])
                                y = float(stim_params[1].split('y: ')[1])
                                stimuli[stim_type]['x'].append(x)
                                stimuli[stim_type]['y'].append(y)
                            elif stim_type == 'Combined Dots':
                                radius = float(stim_params[0].split('looming dot radius: ')[1])
                                x = float(stim_params[0].split('moving dot x: ')[1])
                                y = float(stim_params[1].split('moving dot y: ')[1])
                                stimuli[stim_type]['radius'].append(radius)
                                stimuli[stim_type]['x'].append(x)
                                stimuli[stim_type]['y'].append(y)
                            elif stim_type in ['Grating', 'Optomotor Grating', 'Broadband Grating']:
                                phase = float(stim_params[0].split('phase: ')[1])
                                stimuli[stim_type]['phase'].append(phase)

    return stimuli

def get_behavior_start_end(bouts):
    '''
    Given a dictionary of labeled tail bouts, returns the start and end frames of
    the behavior as a whole (ie. when the first bout begins and the last bout ends),
    where start and end frames refer to frames in the corresponding calcium imaging recording.

    Arguments:

    bouts (dict): The dictionary of labeled tail bouts, of the format:

                  {
                      "bout name": [ [start frame, end frame], [start frame, end frame], ... ]
                  }

                  where start and end frames refer to frames in the corresponding calcium imaging
                  recording.

    Returns:

    behavior_start_frame (int): The frame (in the calcium imaging recording) when behavior started.

    behavior_end_frame (int) : The frame (in the calcium imaging recording) when behavior ended.

    '''

    bout_starts = []
    bout_ends   = []

    for key in bouts.keys():
        for i in range(len(bouts[key])):
            bout_starts.append(bouts[key][i][0])
            bout_ends.append(bouts[key][i][1])
    
    behavior_start_frame = min(bout_starts)
    behavior_end_frame   = max(bout_ends)

    return behavior_start_frame, behavior_end_frame

def get_tail_angles(tail_angle_fname):
    tail_angles = np.genfromtxt(tail_angle_fname, delimiter=",")[:, 1:]

    # remove baseline from tail angles
    baseline = np.mean(tail_angles[:100, :])
    tail_angles -= baseline

    return tail_angles

def get_calcium_video(calcium_video_fname):
    return tifffile.imread(calcium_video_fname)

def get_mean_images(calcium_video, invert=False):
    mean_images = np.zeros(calcium_video.shape[1:]).astype(np.uint8)

    for z in range(calcium_video.shape[1]):
        mean_image = np.mean(calcium_video[:, z, :, :], axis=0)
        mean_image -= np.amin(mean_image[100:-100, 100:-100])
        mean_image = 255.0*mean_image/np.amax(mean_image)

        if invert:
            mean_image = 255 - mean_image

        mean_images[z] = mean_image

    return mean_images

def get_roi_data(roi_data_fname):
    roi_data = np.load(roi_data_fname, allow_pickle=True)

    # extract spatial and temporal footprints, and removed ROIs
    temporal_footprints = roi_data[()]['roi_temporal_footprints']
    spatial_footprints = roi_data[()]['roi_spatial_footprints']
    try:
        removed_rois = roi_data[()]['all_removed_rois']
    except:
        removed_rois = roi_data[()]['removed_rois']

    # get rid of removed ROIs in the spatial and temporal footprints,
    # and z-score the temporal footprints
    for z in range(len(spatial_footprints)):
        kept_rois = [ i for i in range(temporal_footprints[z].shape[0]) if i not in removed_rois[z] ]

        temporal_footprints[z] = temporal_footprints[z][kept_rois]
        spatial_footprints[z]  = spatial_footprints[z][:, kept_rois]
        
        temporal_footprints[z] = (temporal_footprints[z] - np.mean(temporal_footprints[z], axis=1)[:, np.newaxis])/np.std(temporal_footprints[z], axis=1)[:, np.newaxis]

    return spatial_footprints, temporal_footprints

def get_roi_centers(spatial_footprints):
    roi_centers = [ np.zeros((spatial_footprints[z].shape[1], 2)) for z in range(len(spatial_footprints)) ]

    video_shape = int(np.sqrt(spatial_footprints[0].shape[0])), int(np.sqrt(spatial_footprints[0].shape[0]))

    for z in range(len(spatial_footprints)):
        for i in range(spatial_footprints[z].shape[1]):
            mask = (spatial_footprints[z][:, i] > 0).reshape(video_shape).toarray()

            contours = cv2.findContours(mask.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

            contour = max(contours, key=cv2.contourArea)

            M = cv2.moments(contour)
            if M["m00"] != 0:
                center_x = int(M["m10"] / M["m00"])
                center_y = int(M["m01"] / M["m00"])
            else:
                center_x = 0
                center_y = 0
            
            roi_centers[z][i] = center_x, center_y

    return roi_centers

def convolve_gcamp6f(x, calcium_fps, tau_on=0.074, tau_off=0.4):
    # create the kernel
    tau_on  *= calcium_fps  # in frames
    tau_off *= calcium_fps  # in frames
    kframes = np.arange(10 * calcium_fps)  # 10 s long kernel
    kernel  = 2 ** (-kframes / tau_off) * (1 - 2 ** (-kframes / tau_on))
    kernel  = kernel / kernel.sum()

    return convolve(x, kernel, mode='full')[:x.shape[0]]

def interpolate(x, n_frames):
    f   = interp1d(np.arange(len(x)), x)
    x_2 = np.arange(0, n_frames)*frame_ratio
    
    return f(x_2)

def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)

def create_regressors(bouts, stimuli, calcium_fps, n_frames):
    regressors = {}

    # create a regressor for each bout type
    for bout_name in bouts.keys():
        regressor = np.zeros(n_frames).astype(int)

        for bout in bouts[bout_name]:
            start_frame = bout[0]
            end_frame   = bout[1]

            regressor[start_frame:end_frame] = 1

        regressors[bout_name] = convolve_gcamp6f(regressor, calcium_fps)

    for stim_type in stimuli.keys():
        regressor = np.zeros(n_frames).astype(int)
        regressor[stimuli[stim_type]['time']] = 1

        regressors[stim_type] = convolve_gcamp6f(regressor, calcium_fps)

        if stim_type in ['Looming Dot', 'Combined Dots']:
            regressor = np.zeros(n_frames)

            for i in range(len(stimuli[stim_type]['time'])):
                time = stimuli[stim_type]['time'][i]
                radius = stimuli[stim_type]['radius'][i]

                regressor[time] = radius
            regressor -= np.amin(regressor)
            regressor /= min(100, np.amax(regressor))

            regressors['Looming Dot Radius'] = convolve_gcamp6f(regressor, calcium_fps)
        if stim_type in ['Moving Dot', 'Combined Dots']:
            regressor_x = np.zeros(n_frames)
            regressor_y = np.zeros(n_frames)

            for i in range(len(stimuli[stim_type]['time'])):
                time = stimuli[stim_type]['time'][i]
                x    = stimuli[stim_type]['x'][i]
                y    = stimuli[stim_type]['y'][i]

                regressor_x[time] = x
                regressor_y[time] = y
            regressor_x -= np.amin(regressor_x)
            regressor_x /= np.amax(regressor_x)
            regressor_y -= np.amin(regressor_y)
            regressor_y /= np.amax(regressor_y)

            regressors['Moving Dot X'] = convolve_gcamp6f(regressor_x, calcium_fps)
            regressors['Moving Dot Y'] = convolve_gcamp6f(regressor_y, calcium_fps)
        if stim_type in ['Grating', 'Optomotor Grating', 'Broadband Grating']:
            regressor = np.zeros(n_frames)

            for i in range(len(stimuli[stim_type]['time'])):
                time  = stimuli[stim_type]['time'][i]
                phase = stimuli[stim_type]['phase'][i]

                regressor[time] = phase
            regressor -= np.amin(regressor)
            regressor /= np.amax(regressor)
            regressor *= 2
            regressor -= 1

            regressors['Grating Phase'] = convolve_gcamp6f(regressor, calcium_fps)

    if len(bouts.keys()) > 0:
        behavior_start_frame, behavior_end_frame = get_behavior_start_end(bouts)

        # create a behavior start regressor
        regressor = np.zeros(n_frames).astype(int)
        regressor[behavior_start_frame] = 1
        regressors["Behavior Start"] = convolve_gcamp6f(regressor, calcium_fps)

        # create a behavior end regressor
        regressor = np.zeros(n_frames).astype(int)
        regressor[behavior_end_frame] = 1
        regressors["Behavior End"] = convolve_gcamp6f(regressor, calcium_fps)

        # create a behavior regressor
        regressor = np.zeros(n_frames).astype(int)
        regressor[behavior_start_frame:behavior_end_frame] = 1
        regressors["Behavior"] = convolve_gcamp6f(regressor, calcium_fps)

        # create a pre-behavior regressor
        regressor = np.zeros(n_frames).astype(int)
        regressor[:behavior_start_frame] = 1
        regressors["Pre-Behavior"] = convolve_gcamp6f(regressor, calcium_fps)

        # create a post-behavior regressor
        regressor = np.zeros(n_frames).astype(int)
        regressor[behavior_end_frame:] = 1
        regressors["Post-Behavior"] = convolve_gcamp6f(regressor, calcium_fps)

    # create a recording start regressor
    regressor = np.zeros(n_frames).astype(int)
    regressor[0] = 1
    regressors["Recording Start"] = convolve_gcamp6f(regressor, calcium_fps)

    return regressors

def get_correlations(regressors, temporal_footprints):
    regressor_names = list(regressors.keys())

    correlation_results = [ np.zeros((temporal_footprints[z].shape[0], len(regressor_names), 2)) for z in range(len(temporal_footprints)) ]

    for i in range(len(regressor_names)):
        for z in range(len(temporal_footprints)):
            for j in range(temporal_footprints[z].shape[0]):
                correlation_results[z][j, i] = pearsonr(regressors[regressor_names[i]], temporal_footprints[z][j])

    return correlation_results

def filter_correlation_results(correlation_results, z, regressor, max_p=0.05):
    return [ i for i in range(correlation_results[z].shape[0]) if correlation_results[z][i, regressor, 1] <= max_p ]

def multilinear_regression(regressors, temporal_footprints):
    regressor_names = list(regressors.keys())
    
    # make a 2D array containing the regressors
    X = np.zeros((temporal_footprints[0].shape[1], len(regressor_names)))
    for i in range(len(regressor_names)):
        X[:, i] = regressors[regressor_names[i]]

    regression_coefficients = [ np.zeros((temporal_footprints[z].shape[0], len(regressor_names))) for z in range(len(temporal_footprints)) ]
    regression_intercepts   = [ np.zeros((temporal_footprints[z].shape[0], 1)) for z in range(len(temporal_footprints)) ]
    regression_scores       = [ np.zeros((temporal_footprints[z].shape[0], len(regressor_names))) for z in range(len(temporal_footprints)) ]

    for z in range(len(temporal_footprints)):
        for i in range(temporal_footprints[z].shape[0]):
            clf = linear_model.LinearRegression()
            clf.fit(X, temporal_footprints[z][i])

            regression_coefficients[z][i] = clf.coef_
            regression_intercepts[z][i]   = clf.intercept_
            regression_scores[z][i]       = clf.score(X, temporal_footprints[z][i])

    return regression_coefficients, regression_intercepts, regression_scores

def get_correlation_colors(correlation_results, cmap=cm.RdBu):
    correlation_colors = [ np.zeros((correlation_results[z].shape[0], correlation_results[z].shape[1], 4)) for z in range(len(correlation_results)) ]

    for z in range(len(correlation_results)):
        for i in range(correlation_results[z].shape[0]):
            for j in range(correlation_results[z].shape[1]):
                coefficient = correlation_results[z][i, j, 0]

                if coefficient > 0:
                    correlation_colors[z][i, j] = np.array([1, 0, 0, np.abs(coefficient)])
                else:
                    correlation_colors[z][i, j] = np.array([0, 0, 1, np.abs(coefficient)])

    return correlation_colors

def get_top_regressor_colors(regression_coefficients, regression_intercepts, cmap):
    top_regressor_colors = [ np.zeros((regression_coefficients[z].shape[0], 4)) for z in range(len(regression_coefficients)) ]

    for z in range(len(regression_coefficients)):
        for i in range(regression_coefficients[z].shape[0]):

            top_regressor = np.argmax(regression_coefficients[z][i])
            largest_coefficient = regression_coefficients[z][i, top_regressor]

            if largest_coefficient < regression_intercepts[z][i]:
                top_regressor_colors[z][i] = np.array([0, 0, 0, 0])
            else:
                top_regressor_colors[z][i] = cmap(top_regressor)

    return top_regressor_colors

def get_top_regressor_rois(regression_coefficients, regressor, z):
    top_regressor_rois = []

    for i in range(regression_coefficients[z].shape[0]):
        top_regressor = np.argmax(regression_coefficients[z][i])

        if top_regressor == regressor:
            top_regressor_rois.append(i)

    return top_regressor_rois

def regressor_analysis(calcium_video_fname, roi_data_fname, bout_fname, frame_timestamp_fname, tail_calcium_offset):
    calcium_video = get_calcium_video(calcium_video_fname)

    mean_images = get_mean_images(calcium_video, invert=True)

    n_frames = calcium_video.shape[0]

    spatial_footprints, temporal_footprints = get_roi_data(roi_data_fname)
    
    roi_centers = get_roi_centers(spatial_footprints)

    bouts = get_bout_data(bout_fname, calcium_fps, n_frames, tail_calcium_offset=tail_calcium_offset)

    stimuli = get_stimuli_data(frame_timestamp_fname, calcium_fps, n_frames, tail_calcium_offset=tail_calcium_offset)

    regressors = create_regressors(bouts, stimuli, calcium_fps, n_frames)

    regression_coefficients, regression_intercepts, regression_scores = multilinear_regression(regressors, temporal_footprints)

    correlation_results = get_correlations(regressors, temporal_footprints)

    return correlation_results, regression_coefficients, regression_intercepts, regression_scores, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers

def save_data(correlation_results, regressors):
	for i in range(len(correlation_results)):
		# print('correlation results type is', type(correlation_results[i]))
		print('The value is ')
		print('length of correlation results is', len(correlation_results[i]))
		# print('The first value of the correlation results is ', correlation_results[i][0])
		if i == 2:
			np.save('correlation_test.npy', correlation_results[i])
		print(correlation_results.shape)

	# print(correlation_results)

def plot_regressor_analysis(correlation_results, regression_coefficients, regression_intercepts, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, fig=None):
    regressor_names = list(regressors.keys())

    cmap = get_cmap(len(regressor_names)+1)

    correlation_colors = get_correlation_colors(correlation_results)

    top_regressor_colors = get_top_regressor_colors(regression_coefficients, regression_intercepts, cmap)
    
    # plot results

    if fig is None:
        existing_figure = False

        fig = plt.figure(0, figsize=(8, 8))
    else:
        existing_figure = True

        plt.figure(0)

    main_plot_axis   = plt.axes([0.01, 0.5, 0.45, 0.45])
    main_plot_axis.axes.get_xaxis().set_visible(False)
    main_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    secondary_plot_axis   = plt.axes([0.54, 0.5, 0.45, 0.45])
    secondary_plot_axis.axes.get_xaxis().set_visible(False)
    secondary_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    most_correlated_roi_plot_axis = plt.axes([0.01, 0.4, 0.45, 0.05])
    most_correlated_roi_plot_axis.axes.get_xaxis().set_visible(False)
    most_correlated_roi_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    bouts_plot_axis = plt.axes([0.01, 0.3, 0.45, 0.05])
    bouts_plot_axis.axes.get_xaxis().set_visible(False)
    bouts_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    traces_plot_axis = plt.axes([0.01, 0.15, 0.45, 0.1])
    traces_plot_axis.axes.get_xaxis().set_visible(False)
    traces_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    plt.subplots_adjust(bottom=0.25)

    plt.sca(main_plot_axis)

    im = plt.imshow(mean_images[0], cmap='gray')

    # filter ROIs based on p-value
    indices = filter_correlation_results(correlation_results, z=0, regressor=0, max_p=0.05)

    scatter = plt.scatter(roi_centers[0][indices, 0], roi_centers[0][indices, 1], s=15, c=correlation_colors[0][indices, 0, :], edgecolors=None, linewidths=0)

    plt.sca(secondary_plot_axis)

    im_2 = plt.imshow(mean_images[0], cmap='gray')

    scatter_2 = plt.scatter(roi_centers[0][:, 0], roi_centers[0][:, 1], s=15, c=top_regressor_colors[0], edgecolors=None, linewidths=0)

    patches = []
    for i in range(len(regressor_names)):
        patches.append(mpatches.Patch(color=cmap(i), label=regressor_names[i]))

    plt.legend(handles=patches, fontsize='small', bbox_to_anchor=(0, -1, 1, 1))

    plt.sca(most_correlated_roi_plot_axis)
    i = np.argmax(np.abs(correlation_results[0][indices, 0, 0]))
    c = 'r' if correlation_results[0][indices[i], 0, 0] > 0 else 'b'
    most_correlated, = plt.plot(temporal_footprints[0][indices[i]], 'r')

    plt.sca(bouts_plot_axis)
    bout_array = np.zeros((1, regressors[regressor_names[0]].shape[0], 4))
    bout_array[:, :] = cmap(0)
    bout_array[:, :, -1] = regressors[regressor_names[0]]
    # bout = plt.imshow(bout_array, aspect='auto')
    bout, = plt.plot(regressors[regressor_names[0]], c=cmap(0))

    plt.sca(traces_plot_axis)

    traces = plt.imshow(temporal_footprints[0], aspect='auto', cmap='plasma')

    axcolor = 'lightgoldenrodyellow'
    
    z_slider_axis = plt.axes([0.1, 0.1, 0.35, 0.03], facecolor=axcolor)
    z_slider = Slider(z_slider_axis, 'Z', 1, calcium_video.shape[1], valinit=1, valstep=1)

    regressor_slider_axis = plt.axes([0.1, 0.05, 0.35, 0.03], facecolor=axcolor)
    regressor_slider = Slider(regressor_slider_axis, 'Regressor', 1, len(regressor_names), valinit=1, valstep=1)

    max_p_slider_axis = plt.axes([0.1, 0.01, 0.35, 0.03], facecolor=axcolor)
    max_p_slider = Slider(max_p_slider_axis, 'P-Value', 0.01, 0.5, valinit=0.05, valstep=0.01)

    main_plot_axis.set_title(regressor_names[0])
    
    secondary_plot_axis.set_title("Top Regressor")

    def update_correlations_plot(val):
        z         = int(z_slider.val)-1
        regressor = int(regressor_slider.val)-1
        max_p     = max_p_slider.val

        indices = filter_correlation_results(correlation_results, z=z, regressor=regressor, max_p=max_p)

        im.set_data(mean_images[z])
        traces.set_data(temporal_footprints[z])
        scatter.set_offsets(roi_centers[z][indices])
        scatter.set_color(correlation_colors[z][indices, regressor, :])

        indices_2 = get_top_regressor_rois(regression_coefficients, regressor, z)

        im_2.set_data(mean_images[z])
        scatter_2.set_offsets(roi_centers[z][indices_2])
        scatter_2.set_color(top_regressor_colors[z][indices_2])

        i = np.argmax(np.abs(correlation_results[z][indices, regressor, 0]))
        c = 'r' if correlation_results[z][indices[i], regressor, 0] > 0 else 'b'
        most_correlated.set_ydata(temporal_footprints[z][indices[i]])
        most_correlated.set_color(c)
        most_correlated_roi_plot_axis.relim()
        most_correlated_roi_plot_axis.autoscale_view()

        bout_array = np.zeros((1, regressors[regressor_names[regressor]].shape[0], 4))
        bout_array[:, :] = cmap(regressor)
        bout_array[:, :, -1] = regressors[regressor_names[regressor]]
        bout.set_ydata(regressors[regressor_names[regressor]])
        bout.set_color(cmap(regressor))
        bouts_plot_axis.relim()
        bouts_plot_axis.autoscale_view()

        main_plot_axis.set_title(regressor_names[regressor])

        fig.canvas.draw_idle()

    z_slider.on_changed(update_correlations_plot)
    regressor_slider.on_changed(update_correlations_plot)
    max_p_slider.on_changed(update_correlations_plot)

    if not existing_figure:
        plt.show()

def plot_correlation(correlation_results, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, z, max_p, regressor_index, fig=None):
    regressor_names = list(regressors.keys())

    cmap = get_cmap(len(regressor_names)+1)

    correlation_colors = get_correlation_colors(correlation_results)
    
    # plot results

    if fig is None:
        existing_figure = False

        fig = plt.figure(0, figsize=(8, 16))
    else:
        existing_figure = True

        plt.figure(0)

    main_plot_axis   = plt.axes([0.01, 0.5, 0.9, 0.45])
    main_plot_axis.axes.get_xaxis().set_visible(False)
    main_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    most_correlated_roi_plot_axis = plt.axes([0.01, 0.4, 0.9, 0.05])
    most_correlated_roi_plot_axis.axes.get_xaxis().set_visible(False)
    most_correlated_roi_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    regressor_axis = plt.axes([0.01, 0.3, 0.9, 0.05])
    regressor_axis.axes.get_xaxis().set_visible(False)
    regressor_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    traces_plot_axis = plt.axes([0.01, 0.15, 0.9, 0.1])
    traces_plot_axis.axes.get_xaxis().set_visible(False)
    traces_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    # plt.subplots_adjust(bottom=0.25)

    plt.sca(main_plot_axis)

    im = plt.imshow(mean_images[z], cmap='gray')

    # filter ROIs based on p-value
    indices = filter_correlation_results(correlation_results, z=z, regressor=regressor_index, max_p=max_p)

    if len(indices) > 0:
        scatter = plt.scatter(roi_centers[z][indices, 0], roi_centers[z][indices, 1], s=80*fig.dpi/72, c=correlation_colors[z][indices, regressor_index, :], edgecolors=None, linewidths=0)

        plt.sca(most_correlated_roi_plot_axis)
        i = np.argmax(np.abs(correlation_results[z][indices, regressor_index, 0]))

        c = 'r' if correlation_results[z][indices[i], regressor_index, 0] > 0 else 'b'
        most_correlated, = plt.plot(temporal_footprints[z][indices[i]], c)
        plt.xlim(0, n_frames-1)

    plt.sca(regressor_axis)
    bout_array = np.zeros((1, regressors[regressor_names[regressor_index]].shape[0], 4))
    bout_array[:, :] = cmap(0)
    bout_array[:, :, -1] = regressors[regressor_names[regressor_index]]
    # bout = plt.imshow(bout_array, aspect='auto')
    bout, = plt.plot(regressors[regressor_names[regressor_index]], c=cmap(0))
    plt.xlim(0, n_frames-1)

    plt.sca(traces_plot_axis)

    traces = plt.imshow(temporal_footprints[z], aspect='auto', cmap='plasma')

    axcolor = 'lightgoldenrodyellow'

    regressor_axis.set_title("Regressor:")
    most_correlated_roi_plot_axis.set_title("Most correlated ROI trace:")
    traces_plot_axis.set_title("All ROI traces:")
    main_plot_axis.set_title(regressor_names[regressor_index])

    if not existing_figure:
        plt.show()

def plot_multilinear_regression(regression_coefficients, regression_intercepts, regression_scores, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers, z, fig=None):
    regressor_names = list(regressors.keys())

    cmap = get_cmap(len(regressor_names)+1)

    top_regressor_colors = get_top_regressor_colors(regression_coefficients, regression_intercepts, cmap)
    
    # plot results

    if fig is None:
        existing_figure = False

        fig = plt.figure(0, figsize=(8, 16))
    else:
        existing_figure = True

        plt.figure(0)
        plt.clf()

    main_plot_axis   = plt.axes([0.01, 0.5, 0.9, 0.45])
    main_plot_axis.axes.get_xaxis().set_visible(False)
    main_plot_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    best_fit_roi_axis = plt.axes([0.01, 0.4, 0.9, 0.05])
    best_fit_roi_axis.axes.get_xaxis().set_visible(False)
    best_fit_roi_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    worst_fit_roi_axis = plt.axes([0.01, 0.3, 0.9, 0.05])
    worst_fit_roi_axis.axes.get_xaxis().set_visible(False)
    worst_fit_roi_axis.axes.get_yaxis().set_visible(False)
    plt.axis('off')

    plt.sca(main_plot_axis)

    im_2 = plt.imshow(mean_images[z], cmap='gray')

    scatter_2 = plt.scatter(roi_centers[z][:, 0], roi_centers[z][:, 1], s=80*fig.dpi/72, c=top_regressor_colors[z], edgecolors=None, linewidths=0)

    patches = []
    for i in range(len(regressor_names)):
        patches.append(mpatches.Patch(color=cmap(i), label=regressor_names[i]))

    plt.legend(handles=patches, fontsize='small', ncol=5)

    plt.sca(best_fit_roi_axis)
    i = np.argmax(regression_scores[z][:, 0])
    best_fit_roi, = plt.plot(temporal_footprints[z][i], 'r', label='ROI Trace')

    regressor_array = np.array([ regressors[key] for key in regressors.keys() ])

    fit = np.dot(regression_coefficients[z][i, :], regressor_array) + regression_intercepts[z][i, 0]
    best_fit, = plt.plot(fit, 'b', label='Fit')
    plt.xlim(0, n_frames-1)

    plt.legend()

    plt.sca(worst_fit_roi_axis)
    i = np.argmin(regression_scores[z][:, 0])
    worst_fit_roi, = plt.plot(temporal_footprints[z][i], 'r', label='ROI Trace')

    regressor_array = np.array([ regressors[key] for key in regressors.keys() ])

    fit = np.dot(regression_coefficients[z][i, :], regressor_array) + regression_intercepts[z][i, 0]
    worst_fit, = plt.plot(fit, 'b', label='Fit')
    plt.xlim(0, n_frames-1)

    main_plot_axis.set_title("Top Regressor")
    best_fit_roi_axis.set_title("Best fit:")
    worst_fit_roi_axis.set_title("Worst fit:")

    if not existing_figure:
        plt.show()

if __name__ == "__main__":
    calcium_video_fname = "/Volumes/Extra/School/Work for Tod/Videos_Regressor/May.1.19_huc6f_5dpf_PAG_lv30_1A_mc.tif"
    roi_data_fname      = "/Volumes/Extra/School/Work for Tod/Videos_Regressor/Filtered/May.1.19_huc6f_5dpf_PAG_lv30_1A_mc/roi_data.npy"
    bout_fname          = "/Volumes/Extra/School/Work for Tod/Videos_Regressor/May.1.19_1A_behaviors.csv"

    correlation_results, regression_coefficients, regression_intercepts, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers = regressor_analysis(calcium_video_fname, roi_data_fname, bout_fname, frame_timestamp_fname, tail_calcium_offset)

    plot_regressor_analysis(correlation_results, regression_coefficients, regression_intercepts, regressors, spatial_footprints, temporal_footprints, calcium_video, mean_images, n_frames, roi_centers)