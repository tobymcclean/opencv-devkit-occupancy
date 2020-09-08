import logging as log
import platform
import sys
import subprocess
from pathlib import Path

from time import time, monotonic

import consts.resource_paths
from depthai_helpers.cli_utils import PrintColors

process_watchdog_timeout = 10  # seconds


def reset_process_wd() -> None:
    global wd_cutoff
    wd_cutoff = monotonic() + process_watchdog_timeout


def get_model_files(calc_dist_to_bb, cnn_model) -> (str, str):
    cnn_model_path = f'{consts.resource_paths.nn_resource_path}{cnn_model}/{cnn_model}'
    blob_file = f'{cnn_model_path}.blob'
    suffix = ''
    if calc_dist_to_bb:
        suffix = '_depth'
    blob_file_config = f'{cnn_model_path}{suffix}.json'
    return blob_file, blob_file_config


def check_usb_rules() -> bool:
    if platform.system() == 'Linux':
        ret = subprocess.call(['grep', '-irn', 'ATTRS{idVendor}=="03e7"', '/etc/udev/rules.d'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ret != 0:
            log.warning(f'{PrintColors.WARNING.value}Usb rules not found{PrintColors.ENDC.value}')
            log.warning("\nSet rules: \n"
                        """echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' | sudo tee /etc/udev/rules.d/80-movidius.rules \n"""
                        "sudo udevadm control --reload-rules && udevadm trigger \n"
                        "Disconnect/connect usb cable on host! \n")
            return False
        return True
    return False



