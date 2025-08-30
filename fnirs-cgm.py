import analysis
from pathlib import Path
import mne
import time # for evaluation

def main():
    graph_array = [] # for figure
    snirf_files = list(Path('data/').rglob('*.snirf'))
    alpha_value = 0.05
    low_freq, high_freq = 0.01, 0.08
    start_trim, end_trim = 0, 1
    sscreg = False
    selected_files = []
    channels_to_remove = []
    raw = analysis.load_subject_raw(snirf_files[0])
    od = mne.preprocessing.nirs.optical_density(raw)
    ch_names = (mne.preprocessing.nirs.beer_lambert_law(od)).info['ch_names']
    ch_names = [ch.split()[0] for ch in ch_names if ch.split()[1] == 'hbo']

    print('Welcome to fNIRS CGM\nType help for a list of commands')
    while True:
        inp = input('>>> ').split()
        if len(inp) < 1:
            continue
        command = inp[0]

        # LIST COMMAND
        if   command == 'list':
            count = 0
            if len(inp) < 2:
                inp.append('all')
            if inp[1] == 'all':
                gap = len(str(len(snirf_files)))
                for file in snirf_files:
                    print('[{}]{} {}'.format(count, ' '*(gap-len(str(count))), file))
                    count += 1
            elif inp[1] == 'selected':
                gap = len(str(len(selected_files)))
                for file in selected_files:
                    print('[{}]{} {}'.format(file, ' '*(gap-len(str(count))), snirf_files[file]))
                    count += 1
            elif inp[1] == 'channels':
                print(f'{len(ch_names)} fNIRS Channels:')
                count = 1
                for ch in ch_names:
                    print(f'[{count}] {ch}')
                    count += 1

        # SELECT COMMAND
        elif command == 'select':
            if len(inp) < 2:
                print('Argument required')
                continue
            if inp[1] == '*':
                files = list(range(0, len(snirf_files)))
                selected_files = list(range(0, len(snirf_files)))
            else:
                files = inp[1].split(',') 
                files = [int(file) for file in files]
                for file in files:
                    if file > len(snirf_files) or file < 0:
                        print('Invalid selection')
                        continue
                    if file not in selected_files:
                        selected_files.append(file)
                        selected_files.sort()
            print('Selected file{}:'.format('' if len(files) == 1 else 's'))
            for file in files:
                print(snirf_files[file])

        # REMOVE COMMAND
        elif command == 'remove':
            if len(inp) < 2:
                print('Argument required')
                continue
            removed_files = []
            if inp[1] == '*':
                files = list(selected_files)
                removed_files = list(selected_files)
                selected_files = []
            else:
                files = inp[1].split(',') 
                files = [int(file) for file in files]
                for file in files:
                    if file not in selected_files:
                        print('Invalid selection')
                        continue
                    if file in selected_files:
                        selected_files.remove(file)
                        removed_files.append(file)
            if len(removed_files) > 0:
                print('Removed file{}:'.format('' if len(files) == 1 else 's'))
                for file in removed_files:
                    print(snirf_files[file])

        # VIEW COMMAND
        elif command == 'view':
            if len(inp) < 3:
                print('Arguments required')
                continue
            file = int(inp[2])
            if file > len(snirf_files) or file < 0:
                print('Invalid file')
                continue
            raw = analysis.load_subject_raw(snirf_files[file])
            removed_channels = analysis.format_ch_names(channels_to_remove)
            raw.drop_channels(removed_channels)
            od = mne.preprocessing.nirs.optical_density(raw, verbose='error')
            unfiltered_od = od.get_data().copy() 
            filtered_od = od.filter(l_freq=low_freq, h_freq=high_freq, h_trans_bandwidth=0.1, verbose='error')
            haemo = mne.preprocessing.nirs.beer_lambert_law(filtered_od, ppf=0.1)
            if inp[1] == 'raw':
                data, title = raw.get_data(), 'Raw fNIRS Measurements'
            elif inp[1] == 'od':
                data, title = unfiltered_od, 'Optical Density'
            elif inp[1] == 'filtered':
                data, title = filtered_od.get_data(), 'Filtered Optical Density'
            elif inp[1] == 'haemo':
                data, title = haemo.get_data(), 'ΔHbO (μM)'
            elif inp[1] == 'aux':
                analysis.plot_aux_channels(snirf_files[file], start_trim, end_trim)
                continue
            else:
                print('Invalid option')
                continue
            trimmed_data = data[:,start_trim:-1 * end_trim]
            analysis.plot_graph(trimmed_data, title)

        # REMOVE CHANNELS COMMAND
        elif command == 'remove-channels':
            if len(inp) < 2:
                print('Argument required')
                continue
            channels = inp[1]
            if channels == '*':
                channels_to_remove = list(ch_names)
            else:
                channels = channels.split(',')
                for channel in channels:
                    if ch_names[int(channel)-1] not in channels_to_remove:
                        channels_to_remove.append(ch_names[int(channel)-1])
            print(f'Channels {channels_to_remove} will be exluded from analysis')

        # RESET CHANNELS COMMAND
        elif command == 'reset-channels':
            channels_to_remove = [] 
            print('Reset channels')

        # SET COMMAND
        elif command == 'set':
            if len(inp) < 3:
                print('Arguments required')
                continue
            if inp[1] == 'alpha':
                alpha_input = float(inp[2])
                if alpha_input >= 0 and alpha_input <= 1:
                    alpha_value = alpha_input
                    print('Alpha value set')
                else:
                    print('Invalid alpha value, must be between 0 and 1')
            elif inp[1] == 'bandpass':
                freqs = inp[2].split('-')
                if len(freqs) != 2:
                    print('Invalid frequency range')
                else:
                    low_freq = float(freqs[0])
                    high_freq = float(freqs[1])
                    print('Band-pass values set')
            elif inp[1] == 'trim':
                trims = inp[2].split('-')
                if len(trims) != 2:
                    print('Invalid argument')
                else:
                    start_trim = int(trims[0])
                    end_trim = int(trims[1])
                    print('Trim values set')
            elif inp[1] == 'sscreg':
                if inp[2] == '1':
                    sscreg = True
                else:
                    sscreg = False
                print('Sscreg value set')

        # CAUSAL DISCOVERY COMMAND
        elif command == 'pc':
            start_time = time.time()
            filenames = []
            for file in selected_files:
                filenames.append(snirf_files[file])
            if len(filenames) < 1:
                print('No files selected')
                continue
            analysis.causal_discovery(filenames, alpha_value, low_freq, high_freq, channels_to_remove, start_trim, end_trim, sscreg)
            delta_time = time.time() - start_time
            #print(f'{delta_time} seconds for {len(filenames)} subjects.')

        # HELP COMMAND
        elif command == 'help':
            print("""Commands:
  select [files]                     selects files
  list [all,selected,channels]       lists files or channels
  remove [files]                     removes files from selection  
  remove-channels [channels]         removes channels from analysis
  reset-channels                     resets channels
  set [alpha,bandpass,trim] [value]  sets parameter values
  pc                                 performs PC algorithm
  quit                               exits program
  help                               displays this screen""")

        # QUIT COMMAND
        elif command == 'quit':
            break

        else:
            print('Invalid Command')

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('An error occurred: {}'.format(e))

