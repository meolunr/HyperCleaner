import sys
from datetime import datetime

LIB_DIR = f'{sys.path[0]}/lib'
MISC_DIR = f'{sys.path[0]}/misc'
UPDATED_APP_JSON = 'product/UpdatedApp.json'


def log(string: str):
    now = datetime.now().strftime('[%m-%d %H:%M:%S]')
    print(f'{now} {string}')
