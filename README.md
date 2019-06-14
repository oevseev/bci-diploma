# bci-diploma
Bachelor's thesis at Chair of System Programming, St. Petersburg State University.

This repository provides a solution for a P300-based EEG-headset-assisted UI interaction.

## Prerequisites

Hardware:
- A Windows machine
- An [Emotiv EPOC+](https://www.emotiv.com/epoc/) EEG headset

Software
- Python 3.7 or later
- [Qt 5](https://www.qt.io/) (you need to install it manually if you are not using `conda` to manage dependencies)
- [CyKit](https://github.com/CymatiCorp/CyKit)

## How to install

1. Install CyKit (see [installation instructions](https://github.com/CymatiCorp/CyKit/wiki/How-to-Install-CyKIT))
2. Clone this repository (`git clone https://github.com/oevseev/bci-diploma.git`)
3. Install requirements (`pip install -r requirements.txt` or `conda install --file requirements.txt`)
3. You're good to go!

## How to run

1. Connect the device (use [official Emotiv software](https://www.emotiv.com/emotiv-bci/) to adjust the sensors)
2. Launch CyKit with `python 0.0.0.0 5151 6 openvibe+generic+nocounter+noheader+nobattery+float` (launch TCP server on port `5151` which will stream raw data from all 14 channels). You can use either remote or local machine.
3. Launch the application with `python run_app.py`
4. Use *Preferences* dialog (in the app menu, which is accessible by right clicking the app icon in the system tray) to enter IP address and port of the CyKit server.

To activate a working session, select *Enable* in the app menu.

Before you can actually interact, you need to record some training data (50-100 samples is ok). To record a train session, select *Training mode* in the app menu. Training session data is saved to `C:\Users\[your name]\.bci\models`. **Note that starting training mode again will re-record previous data.**

Feel free to experiment with the source code as it's essentially a prototype and there is some room for improvements (for example, P300 detection algorithm is very simpilistic and may be replaced with something more state-of the art. UI is very ugly too).
