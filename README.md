# Various OpenTrons 2 Software for Educational Purposes
## For the Ray and Stephanie Lane Computational Biology Pre-college Program @ CMU 

This repo contains software for two lesson plans for the pre-college program: Color Matching and Battleship

Color Matching automates color mixing experiments on an Opentrons OT-2 robot using a webcam for feedback. The project aims to learn dye recipes that reproduce arbitrary target colors.

Battleship automates a tournament of the game of Battleship played with water for ocean, acid for ships, and pH indicator as "missiles". Identification of the wells is done with a webcame for feedback. The project aims to pit student-submitted AIs (and instructor written historically-themed competitors) against each other in a tournament. 

## Repository structure

- **battleship/** – All files specifically related to battleship.
  `streamlit run battleship/app.py` to run this project.
- **color_matching/** – All files specifically related to color matching.
  `streamlit run color_matching/app.py` to run this project.
- **camera/** – Camera calibration utilities and example data used to measure
  plate colors.  The :class:`PlateProcessor` supports a ``virtual_mode`` that
  skips the webcam and returns an all white plate for testing. The :class:`DualPlateProcesssor`
  is specifically used in battleship to read 2 plates instead of just 1.
- **robot/** – OT-2 helper functions and argument files shared by the different
  protocols.
- **secret/** – Hidden from public facing repo, this contains robot-specific
  networking and config information.
- **tests/** – Various tests to verify functions are working. Should be expanded.

## Installation

All scripts require Python 3. Install the required packages with:

```bash
pip install -r requirements.txt
```

## Connecting to the OT-2

Both the Streamlit app and the learning pipeline connect to the OT‑2 over SSH
using `paramiko`. Edit the hostname, username and SSH key path in the scripts if
your robot uses different settings. Make sure your workstation can reach the
robot on the network and that the SSH key is stored in the `secret/` folder.

## Usage

### Streamlit interface

```bash
streamlit run color_matching/app.py
```

This launches the web UI where you can enter dye volumes and see the measured
colors, eg.
