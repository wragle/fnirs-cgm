# Information

* **fnirs-cgm.py** is the command-line interface tool
* **analysis.py** contains the functions I developed to conduct the analysis
* **example-output.png** is an example CGM produced by the program
* **data** is a directory containing the SPA-fNIRS data from the dataset referenced in the report

# Installation

A few libraries are required to run the program. These requirements are listed below.

## Requirements

The following Python packages are runtime requirements:
* mne           (1.9.0)
* mne-nirs      (0.7.1)
* h5py          (3.13.0)
* pydot         (3.0.4)
* matplotlib    (3.10.1)
* seaborn       (0.13.2)
* numpy         (2.2.4)
* causal-learn  (0.1.4.1)

They can be installed using pip, either globally or within a virtual environment. The program has been tested on Python 3.12.10.

## Virtual Environment (optional)

A Python virtual environment can be created to avoid the global installation of these requirements. Information on creating a virtual environment can be found here [Python Virtual Environment](https://docs.python.org/3/library/venv.html). 

# Usage

The program supports various commands and options through its command-line interface. Below are some detailed examples of common usage patterns.

### Running the Program
The following command can be run in a terminal emulator or IDE to start the program. The program must be run inside its own directory since the SNIRF files are searched for in its *data* directory. Once in the program, the user can input commands to select files, view data, remove channels, etc.

```bash
$ python fnirs-cgm.py
```

### Included Dataset
The dataset referenced in the report is included within this git repository, it includes SNIRF files for 14 subjects. The program has been testing using these files.

### Help Menu
The **help** command displays a help menu outlining the functionality of the different commands.

### Listing Files
The **list** command is used to list out all SNIRF files stored within the *data* directory. It searches recursively to include files stored within subdirectories. These files are accessible, but not yet selected. In order to run causal discovery, you must first select one or more files on which the causal discovery will be performed.

```
>>> list
[1] resting_33.snirf
[2] resting_35.snirf
[3] resting_41.snirf
...
```

The **list** command also takes an optional argument that will specify which files are listed. This argument can be either *all*, *selected*, or *channels*; *all* is the default option if no argument is provided, it outputs all SNIRF files within the *data* directory. *selected* will output only the files that you have specifically selected by previous commands.  *channels* will output the fNIRS channel names.

```
>>> list selected
[2] resting_35.snirf
```


### Selecting Files
The **select** command can be used to select one or more SNIRF files to be used in causal discovery. The command takes an argument that can be either a number in the range of the SNIRF files, a comma-separated list of numbers, or a * to select all files in the *data* directory. The selected files will be combined to produce an average CGM of all the data.

```
>>> select 1
Selected file:
resting_33.snirf

>>> select 1,3
Selected files:
resting_33.snirf
resting_41.snirf

>>> select *
Selected files:
resting_33.snirf
resting_35.snirf
resting_41.snirf
...
```

### Removing Files
The **remove** command operates in a similar way as the **select** command but removes files instead. It takes an argument in the same format as the **select** command.

```
>>> remove *
Removed files:
resting_33.snirf
resting_34.snirf
resting_35.snirf
...
```

### Viewing Plotted Data
The **view** command is used to view the various data stored within a chosen file as well as to view the data after different preprocessing stages have occurred. The options for the view command are: *raw* (raw fNIRS signals), *od* (optical density), *filtered* (filtered optical density), *haemo* (haemodynamic data), and *aux* (auxiliary data).

```
>>> view od 1

>>> view haemo 2
```

### Removing Channels
The **remove-channels** command is used to remove one or more channels from the data; these channels will be excluded from the causal discovery and graph views. The **remove-channels** command takes a 'channels' argument in the same format as previous commands (a single channel number, comma-separated list, or *). The **reset-channels** command is used to reset the selected channels, this means all the channels will be selected again.

```
>>> remove-channels 2,4,9,12
Channels [2, 4, 9, 12] will be excluded from analysis

>>> reset-channels
Channels have been reset
```

### Modifying Parameters
The **set** command takes two arguments: the first is the parameter which is to be set, the second is the new value for that parameter. The parameters which can be set are the alpha value for the conditional independence test (*alpha*), the bandpass filter frequencies (*bandpass*), and the trim value (*trim*) which determines how much of the time series should be removed from the start and end. *alpha* must be between 0 and 1, *bandpass* must be in the format `low-high`, and *trim* must be in the format `start_trim-end_trim`. *sscreg* takes a binary parameter 0 or 1, 0 by default.

```
>>> set alpha 0.03

>>> set bandpass 0.02-0.1

>>> set trim 2500-2000

>>> set sccreg 1
```

### Running PC Algorithm
The **pc** command will perform the PC algorithm on the selected files. Any channels which were previously removed will be excluded from analysis. This command generates the causal graphical model and saves it as a PNG file.

```
>>> pc
Running PC Algorithm...
```

## Producing the Output Seen in the Report
The following commands can be run to produce the CGM shown in the report.

```
>>> set trim 2000-2000
>>> remove-channels 1,4,7,12,22,32
>>> select *
>>> pc
```
