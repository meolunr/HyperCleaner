import sys
from datetime import datetime

BIN_DIR = f'{sys.path[0]}/bin'
LIB_DIR = f'{sys.path[0]}/lib'
OVERLAY_DIR = f'{sys.path[0]}/overlay'


def log(string: str):
    now = datetime.now().strftime('[%m-%d %H:%M:%S]')
    print(f'{now} {string}')
