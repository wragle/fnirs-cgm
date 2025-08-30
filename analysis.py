import os
import h5py
import math
from pathlib import Path
import numpy as np
import mne
import mne_nirs
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from matplotlib.gridspec import GridSpec
import pydot
from random import randint
import time
from causallearn.search.ConstraintBased.PC import pc
#from causallearn.utils.cit import kci

def plot_aux_channels(filename, start_trim, end_trim):
    aux_shape = get_aux_shapes(filename)
    PPG  = aux_shape[4]['time_series'][start_trim:-1 * end_trim]
    BP   = aux_shape[5]['time_series'][start_trim:-1 * end_trim]
    RESP = aux_shape[6]['time_series'][start_trim:-1 * end_trim]

    plt.figure(figsize=(12, 10))
    gs = GridSpec(3, 1, height_ratios=[1, 1, 1])
    time = np.arange(len(PPG))

    # plot PPG
    ax1 = plt.subplot(gs[0])
    ax1.plot(time, PPG, 'r-', linewidth=1.5)
    ax1.set_title('Photoplethysmography (PPG)', fontsize=14)
    ax1.set_ylabel('Amplitude', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, len(PPG))

    # plot BP
    ax2 = plt.subplot(gs[1], sharex=ax1)
    ax2.plot(time, BP, 'g-', linewidth=1.5)
    ax2.set_title('Blood Pressure (BP)', fontsize=14)
    ax2.set_ylabel('Amplitude', fontsize=12)
    ax2.grid(True, alpha=0.3)

    # plot RESP
    ax3 = plt.subplot(gs[2], sharex=ax1)
    ax3.plot(time, RESP, 'b-', linewidth=1.5)
    ax3.set_title('Respiration (RESP)', fontsize=14)
    ax3.set_xlabel('Time (samples)', fontsize=12)
    ax3.set_ylabel('Amplitude', fontsize=12)
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3)

    # Show the plot
    plt.show()


def add_aux_channels(hbo_data, filenames):
    count = 0
    combined_channels = []
    for file in filenames:
        aux_shapes = get_aux_shapes(file)
        PPG  = aux_shapes[4]['time_series']
        BP   = aux_shapes[5]['time_series']
        RESP = aux_shapes[6]['time_series']

        aux_channels = np.array([PPG, BP, RESP])
        combined_channels.append(np.vstack([hbo_data[count], aux_channels]))

        count += 1
    return combined_channels 

def get_aux_shapes(file_path):
    try:
        # opens snirf file
        with h5py.File(file_path, "r") as f:
            nirs_group = f["nirs/"]

            # get auxiliary channels
            aux_channels = [key for key in nirs_group.keys() if key.startswith('aux')]

            aux_shapes = []

            for aux_key in sorted(aux_channels):
                aux_group = nirs_group[aux_key]

                name = "Unknown"
                if "name" in aux_group:
                    name_data = aux_group["name"][()]
                    if isinstance(name_data, bytes):
                        name = name_data.decode('utf-8')
                    else:
                        name = str(name_data)
                shape = None
                if "dataTimeSeries" in aux_group:
                    time_series = aux_group["dataTimeSeries"][()]

                aux_shapes.append({
                    "channel": aux_key,
                    "time_series": time_series
                })

            return aux_shapes

    except Exception as e:
        return f"Error accessing file: {str(e)}"

def load_subject_raw(path):
    return mne.io.read_raw_snirf(path, verbose='error') 

def load_all_subjects_raw(path):
    print('Reading files...')
    raws = []
    subjects = [d for d in path.iterdir() if d.is_dir()]    
    for subject in subjects:
        raw = load_subject_raw(subject / 'resting.snirf')
        raws.append(raw)
    # returns an array containing the raw data from each subject
    return raws

def preprocess(raws, h_freq, l_freq, sscreg, channels_to_remove=[]):
    haemos = []
    for raw in raws:
        # drops erroneous channels
        raw.drop_channels(channels_to_remove)

        # signal intensity -> optical density
        optical_density = mne.preprocessing.nirs.optical_density(raw)

        # filter out certain frequency range
        if sscreg:
            od_ssdcorrected = mne_nirs.signal_enhancement.short_channel_regression(optical_density)
            filtered_optical_density = od_ssdcorrected.filter(l_freq=l_freq, h_freq=h_freq, h_trans_bandwidth=0.1, verbose=50)
        else:
            filtered_optical_density = optical_density.filter(l_freq=l_freq, h_freq=h_freq, h_trans_bandwidth=0.1, verbose=50)
        
        # optical density -> haemodynamic response
        haemo = mne.preprocessing.nirs.beer_lambert_law(filtered_optical_density, ppf=0.1)

        haemos.append(haemo)
    # returns an array containing the haemodynamic data from each subject after some preprocessing steps
    return haemos

def get_hbo_channels(haemo):
    channels = haemo.ch_names
    channels_to_remove = []
    for channel in channels:
        # removes HbR channels
        if channel.split(' ')[1] != 'hbo':
            channels_to_remove.append(channel)
    return haemo.drop_channels(channels_to_remove)

# graph visualisation
def plot_graph(np_array, title=''):
    plt.style.use('seaborn-v0_8-whitegrid')
    mpl.rcParams['lines.linewidth'] = 2
    mpl.rcParams['axes.labelsize'] = 12
    mpl.rcParams['xtick.labelsize'] = 10
    mpl.rcParams['ytick.labelsize'] = 10
    mpl.rcParams['figure.figsize'] = [8, 6] 

    x = np.arange(np_array.shape[1])

    # seaborn colour palette
    colors = sns.color_palette("tab10", n_colors=np_array.shape[0]) 

    for i in range(np_array.shape[0]):
        plt.plot(x[:], np_array[i, :], label=f'Row {i}', linewidth=2, color=colors[i % len(colors)])

    #plt.title(title, fontsize=14) 
    plt.xlabel('Time', fontsize=16)
    plt.ylabel(title, fontsize=16)

    plt.tight_layout()
    plt.show()

def get_adjacency_dict(graph, channel_names):
    adjacency_dict = {}
    for i in range(len(channel_names)):
        adjacency_dict[channel_names[i]] = []
        for j in range(len(channel_names)):
            if i == j:
                continue
            if graph[i][j] != 0 or graph[j][i] != 0:
                adjacency_dict[channel_names[i]].append(channel_names[j])
    return adjacency_dict

# causal discovery
def pc_discovery(data, alpha):
    print('Running PC algorithm...')
    cg = pc(data.T, alpha)
    return cg

def causal_graphical_model(channel_names, adj_matrix, ch_pos, alpha):
    scale = 280
    line_color = '#000000aa'
    node_size = 1.2
    node_style = {
        'color': line_color,
        'style': 'filled',
        'fontname': 'Helvetica-Bold',
        'fontcolor': '#222222',
        'shape': 'circle',
        'fixedsize': 'true',
        'penwidth': '6'
    }
    edge_style = {
        'color': line_color,
        'penwidth': '6',
        'arrowsize': '2',
        'fontname': 'Helvetica',
        'fontsize': '10',
    }
    count = 1
    nodes = []
    drawn_nodes = []
    drawn_edges = []
    graph = pydot.Dot(graph_type='digraph', splines='curved', layout='neato')
    graph.set
    graph.set_fontname('Helvetica')
    for ch in channel_names:
        ch_name = ch.split()[0]
        x, y = ch_pos[ch_name][0], ch_pos[ch_name][1]
        str_pos = f"{x*scale},{y*scale}!"
        if ch_name in ['PPG', 'BP', 'RESP']:
            node = pydot.Node(ch_name, fillcolor='#fb9a99', pos=str_pos, fontsize=30, width=node_size+0.5, height=node_size+0.5, **node_style)
        elif len(ch.split()) > 1:
            node = pydot.Node(str(count), fillcolor='#a6cee3', pos=str_pos, fontsize=36, width=node_size, height=node_size, **node_style)
        else:
            node = pydot.Node(str(count), fillcolor='#fdbf6f', pos=str_pos, fontsize=36, width=node_size, height=node_size, **node_style)

        graph.add_node(node)
        nodes.append(node)
        count += 1

    tested_pairs = []
    count = 0
    for i in range(len(adj_matrix)):
        for j in range(len(adj_matrix[0])):
            if (i, j) in tested_pairs:
                continue
            if adj_matrix[j][i] == 1 and adj_matrix[i][j] == -1:
                direction = 'forward'
            elif adj_matrix[i][j] == -1 and adj_matrix[j][i] == -1:
                direction = 'none'
                tested_pairs.append((i, j))
                tested_pairs.append((j, i))
            elif adj_matrix[i][j] == 1 and adj_matrix[j][i] == 1:
                direction = 'both'
                tested_pairs.append((i, j))
                tested_pairs.append((j, i))
            else:
                direction = False
            if direction:
                edge = pydot.Edge(nodes[i], nodes[j], dir=direction, **edge_style)
                graph.add_edge(edge)
                count += 1

    file_name = 'output.png'
    graph.write_png(file_name)
    print(f'Graph saved to file: \'{file_name}\'')

def format_ch_names(inp_chs):
    out_chs = []
    for ch in inp_chs:
        out_chs.append(ch + ' 830')
        out_chs.append(ch + ' 690')
    return out_chs

def causal_discovery(filenames, alpha, low_freq, high_freq, channels_to_remove, start_trim, end_trim, sscreg):

    channels_to_remove = format_ch_names(channels_to_remove)

    # get raw fNIRS data
    raws = []
    for file in filenames:
        raws.append(load_subject_raw(file))

    # converts to haemodynamic data
    haemos = preprocess(raws, high_freq, low_freq, sscreg, channels_to_remove)

    # gets hbo channels
    hbo_channels = [get_hbo_channels(haemo) for haemo in haemos]

    # gets channel names
    channel_names = hbo_channels[0].ch_names
    channel_names = [ch.split(' ')[0] for ch in channel_names]

    # gets data from channels
    hbo_data = [hbo.get_data() for hbo in hbo_channels]

    # appends aux channel names
    channel_names.append('PPG')
    channel_names.append('BP')
    channel_names.append('RESP')

    combined_data = add_aux_channels(hbo_data, filenames)

    trimmed_combined_data = []
    for c in combined_data:
        trimmed_combined_data.append(c[:, start_trim:(-1 * end_trim)])

    # constructs Virtual Typical Subject
    vts_data = np.hstack(trimmed_combined_data)

    info = raws[0].info

    points = []
    ch_pos = {}
    x_offset, y_offset = 0.005, -0.012

    ch_pos['PPG']  = (0.0044 -x_offset, -0.05  - y_offset)
    ch_pos['BP']   = (0.007  -x_offset, -0.035 - y_offset)
    ch_pos['RESP'] = (0.0236 -x_offset, -0.057 - y_offset)

    count = 0
    for ch in haemos[0].info['chs']:
        s = ch['loc'][0:2]
        d = ch['loc'][3:5]
        name = ch['ch_name'].split(' ')[0]
        midpoint = ((d[0]+s[0])/2, (d[1]+s[1])/2)
        distance = math.sqrt(((d[1]-s[1]) ** 2) + ((d[0]-s[0]) ** 2))
        if distance < 0.01:
            channel_names[count] += ' SH'
        count += 1
        ch_pos[name] = midpoint

    cg = pc_discovery(vts_data, alpha)
    labels = ['PPG','BP','RESP']

    adj_matrix = cg.G.graph

    # gets adjacency dictionary
    adjacency_dict = get_adjacency_dict(cg.G.graph, channel_names)

    causal_graphical_model(channel_names, adj_matrix, ch_pos, alpha)

