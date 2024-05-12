import os
import sys
from datetime import datetime

BIN_DIR = os.path.join(sys.path[0], 'bin')
LIB_DIR = os.path.join(sys.path[0], 'lib')
OVERLAY_DIR = os.path.join(sys.path[0], 'overlay')


def log(string: str):
    now = datetime.now().strftime('[%m-%d %H:%M:%S]')
    print(f'{now} {string}')
