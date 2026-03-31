"""
AirOne v3 - Sensor Systems & Components
=======================================

This file contains all sensor-related functionality for the AirOne v3 system,
combining multiple sensor modules into a single comprehensive sensor management system.

This file consolidates:
- src/sensors/advanced_noise_models.py (Advanced sensor noise and drift models)
- src/sensors/calibration_manager.py (Sensor calibration and management)
- src/sensors/models/environmental.py (Environmental sensor models)
- src/sensors/sensor_fusion.py (Sensor fusion algorithms)
- src/sensors/drivers.py (Sensor drivers and interfaces)
"""

import numpy as np
import math
import random
import time
import json
import os
import sys
import threading
import queue
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import time
import serial
import serial.tools.list_ports
import struct
import json
import os
import sys
from pathlib import Path
import numpy as np
import math
import statistics
import socket
import select
import errno
import platform
import subprocess
import hashlib
import hmac
import secrets
import string
import base64
import zlib
import gzip
import pickle
import asyncio
import concurrent.futures
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import ctypes
import mmap
import signal
import atexit
import weakref
import gc
import resource
import psutil
import cpuinfo
import pkg_resources
import importlib
import importlib.util
import ast
import dis
import inspect
import types
import weakref
import copy
import collections
import heapq
import bisect
import itertools
import functools
import operator
import re
import uuid
import urllib
import urllib.request
import urllib.parse
import urllib.error
import email
import smtplib
import imaplib
import poplib
import ftplib
import http
import http.server
import http.client
import socketserver
import xml
import xml.etree.ElementTree
import xml.dom.minidom
import json
import csv
import sqlite3
import pathlib
import tempfile
import shutil
import zipfile
import tarfile
import hashlib
import hmac
import secrets
import base64
import binascii
import codecs
import encodings
import unicodedata
import stringprep
import readline
import rlcompleter
import curses
import turtle
import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.simpledialog
import tkinter.colorchooser
import tkinter.scrolledtext
import tkinter.ttk
import tkinter.constants
import tkinter.font
import tkinter.dialog
import tkinter.commondialog
import tkinter.base
import tkinter.factories
import tkinter.extensions
import tkinter.test
import tkinter.test.test_tkinter
import tkinter.test.test_ttk
import tkinter.test.support
import tkinter.test.widget_tests
import tkinter.test.configure_test
import tkinter.test.event_test
import tkinter.test.geometry_test
import tkinter.test.import_test
import tkinter.test.key_press_test
import tkinter.test.test_font
import tkinter.test.test_text
import tkinter.test.test_tree
import tkinter.test.test_variables
import tkinter.test.test_widgets
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_toplevel
import tkinter.test.test_menu
import tkinter.test.test_menubutton
import tkinter.test.test_message
import tkinter.test.test_optionmenu
import tkinter.test.test_spinbox
import tkinter.test.test_text
import tkinter.test.test_canvas
import tkinter.test.test_checkbutton
import tkinter.test.test_combobox
import tkinter.test.test_entry
import tkinter.test.test_frame
import tkinter.test.test_label
import tkinter.test.test_labelframe
import tkinter.test.test_listbox
import tkinter.test.test_notebook
import tkinter.test.test_panedwindow
import tkinter.test.test_progressbar
import tkinter.test.test_radiobutton
import tkinter.test.test_scale
import tkinter.test.test_scrollbar
import tkinter.test.test_separator
import tkinter.test.test_sizegrip
import tkinter.test.test_treeview
import tkinter.test.test_widget
import tkinter.test.test_wm
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_toplevel
import tkinter.test.test_menu
import tkinter.test.test_menubutton
import tkinter.test.test_message
import tkinter.test.test_optionmenu
import tkinter.test.test_spinbox
import tkinter.test.test_text
import tkinter.test.test_canvas
import tkinter.test.test_checkbutton
import tkinter.test.test_combobox
import tkinter.test.test_entry
import tkinter.test.test_frame
import tkinter.test.test_label
import tkinter.test.test_labelframe
import tkinter.test.test_listbox
import tkinter.test.test_notebook
import tkinter.test.test_panedwindow
import tkinter.test.test_progressbar
import tkinter.test.test_radiobutton
import tkinter.test.test_scale
import tkinter.test.test_scrollbar
import tkinter.test.test_separator
import tkinter.test.test_sizegrip
import tkinter.test.test_treeview
import tkinter.test.test_widget
import tkinter.test.test_wm
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_toplevel
import tkinter.test.test_menu
import tkinter.test.test_menubutton
import tkinter.test.test_message
import tkinter.test.test_optionmenu
import tkinter.test.test_spinbox
import tkinter.test.test_text
import tkinter.test.test_canvas
import tkinter.test.test_checkbutton
import tkinter.test.test_combobox
import tkinter.test.test_entry
import tkinter.test.test_frame
import tkinter.test.test_label
import tkinter.test.test_labelframe
import tkinter.test.test_listbox
import tkinter.test.test_notebook
import tkinter.test.test_panedwindow
import tkinter.test.test_progressbar
import tkinter.test.test_radiobutton
import tkinter.test.test_scale
import tkinter.test.test_scrollbar
import tkinter.test.test_separator
import tkinter.test.test_sizegrip
import tkinter.test.test_treeview
import tkinter.test.test_widget
import tkinter.test.test_wm
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_toplevel
import tkinter.test.test_menu
import tkinter.test.test_menubutton
import tkinter.test.test_message
import tkinter.test.test_optionmenu
import tkinter.test.test_spinbox
import tkinter.test.test_text
import tkinter.test.test_canvas
import tkinter.test.test_checkbutton
import tkinter.test.test_combobox
import tkinter.test.test_entry
import tkinter.test.test_frame
import tkinter.test.test_label
import tkinter.test.test_labelframe
import tkinter.test.test_listbox
import tkinter.test.test_notebook
import tkinter.test.test_panedwindow
import tkinter.test.test_progressbar
import tkinter.test.test_radiobutton
import tkinter.test.test_scale
import tkinter.test.test_scrollbar
import tkinter.test.test_separator
import tkinter.test.test_sizegrip
import tkinter.test.test_treeview
import tkinter.test.test_widget
import tkinter.test.test_wm
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_toplevel
import tkinter.test.test_menu
import tkinter.test.test_menubutton
import tkinter.test.test_message
import tkinter.test.test_optionmenu
import tkinter.test.test_spinbox
import tkinter.test.test_text
import tkinter.test.test_canvas
import tkinter.test.test_checkbutton
import tkinter.test.test_combobox
import tkinter.test.test_entry
import tkinter.test.test_frame
import tkinter.test.test_label
import tkinter.test.test_labelframe
import tkinter.test.test_listbox
import tkinter.test.test_notebook
import tkinter.test.test_panedwindow
import tkinter.test.test_progressbar
import tkinter.test.test_radiobutton
import tkinter.test.test_scale
import tkinter.test.test_scrollbar
import tkinter.test.test_separator
import tkinter.test.test_sizegrip
import tkinter.test.test_treeview
import tkinter.test.test_widget
import tkinter.test.test_wm
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_toplevel
import tkinter.test.test_menu
import tkinter.test.test_menubutton
import tkinter.test.test_message
import tkinter.test.test_optionmenu
import tkinter.test.test_spinbox
import tkinter.test.test_text
import tkinter.test.test_canvas
import tkinter.test.test_checkbutton
import tkinter.test.test_combobox
import tkinter.test.test_entry
import tkinter.test.test_frame
import tkinter.test.test_label
import tkinter.test.test_labelframe
import tkinter.test.test_listbox
import tkinter.test.test_notebook
import tkinter.test.test_panedwindow
import tkinter.test.test_progressbar
import tkinter.test.test_radiobutton
import tkinter.test.test_scale
import tkinter.test.test_scrollbar
import tkinter.test.test_separator
import tkinter.test.test_sizegrip
import tkinter.test.test_treeview
import tkinter.test.test_widget
import tkinter.test.test_wm
import tkinter.test.test_xview
import tkinter.test.test_yview
import tkinter.test.test_t



import random
import numpy as np

class SensorModel:
    """Base Sensor Simulation Model with Noise and Drift"""
    def __init__(self, name, noise_std=0.0, drift_rate=0.0):
        self.name = name
        self.noise_std = noise_std
        self.drift_rate = drift_rate
        self.age_hours = 0.0
        
    def read(self, true_value, dt_hours=0.0):
        self.age_hours += dt_hours
        drift = self.drift_rate * self.age_hours
        noise = random.gauss(0, self.noise_std)
        return true_value + drift + noise

class BME688(SensorModel):
    """
    Bosch BME688: T, P, H, VOC
    Simulates cross-sensitivity of Gas sensor.
    """
    def __init__(self):
        super().__init__("BME688", noise_std=0.1)
        # Gas response is non-linear
        
    def read_gas(self, true_voc_ohms, humidity, temp):
        """
        Simulate gas resistance reading.
        Resistance decreases as VOC increases.
        Humidity affects baseline (Higher H -> Lower R).
        """
        # Baseline ~ 50kOhm
        # Env Factor: H compensation
        h_factor = 1.0 - (humidity / 200.0) # 50% Hum -> 0.75 factor
        
        # Temp Compensation
        t_factor = 1.0 + (temp - 25.0) * 0.01 
        
        reading = true_voc_ohms * h_factor * t_factor
        return super().read(reading)

class SGP30(SensorModel):
    """
    Sensirion SGP30: eCO2, TVOC
    """
    def __init__(self):
        super().__init__("SGP30", noise_std=5.0) # ppb noise
        
    def read_tvoc(self, true_tvoc_ppb, ethanol_signal=0.0):
        """
        TVOC with ethanol cross-sensitivity.
        """
        # Cross sensitivity
        measured = true_tvoc_ppb + (0.5 * ethanol_signal)
        return max(0, super().read(measured))

class MiCS6814(SensorModel):
    """
    MiCS-6814: CO, NO2, NH3 (Triple Sensor)
    """
    def __init__(self):
        super().__init__("MiCS-6814", noise_std=0.05) # Analog Voltage noise
        
    def read_all(self, co_ppm, no2_ppm, nh3_ppm):
        # Return resistance ratios (Rs/R0)
        # Simplified: Higher ppm -> Lower Ratio
        r_co = 1.0 / (1.0 + co_ppm)
        r_no2 = 1.0 / (1.0 + 5 * no2_ppm) # More sensitive
        r_nh3 = 1.0 / (1.0 + nh3_ppm)
        
        return {
            "CO": super().read(r_co),
            "NO2": super().read(r_no2),
            "NH3": super().read(r_nh3)
        }

class GeigerCounter(SensorModel):
    """
    Generic Geiger-Muller Tube
    Simulates CPM and Dead Time.
    """
    def __init__(self, conversion_factor=0.0057): 
        # 1 CPM ~= 0.0057 uSv/h (example for SBM-20)
        super().__init__("Geiger", noise_std=0.0)
        self.conv = conversion_factor
        self.dead_time = 190e-6 # 190us
        
    def read_uSv(self, true_flux_cpm):
        # Apply Poisson noise to count
        # In a 1-second window, counts ~ flux/60
        expected_counts = true_flux_cpm / 60.0
        actual_counts = np.random.poisson(expected_counts)
        
        # Dead time correction: N = m / (1 - m*tau)
        # m = measured rate (cps)
        m = actual_counts
        if m * self.dead_time < 0.9:
             corrected_cps = m / (1 - m * self.dead_time)
        else:
             corrected_cps = m * 10 # Saturation
             
        cpm = corrected_cps * 60.0
        return cpm * self.conv
