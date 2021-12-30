import os

DATA_TMP_PATH = '/data/local/tmp/'


class AdbUtils(object):

    @staticmethod
    def exec(command: str):
        os.system('adb shell %s' % command)

    @staticmethod
    def exec_as_root(command: str):
        os.system('adb shell su -c %s' % command)
