import os

DATA_TMP_PATH = '/data/local/tmp/'


class AdbUtils(object):

    @staticmethod
    def exec(command: str):
        os.system('adb shell %s' % command)

    @staticmethod
    def exec_as_root(command: str):
        os.system('adb shell su -c %s' % command)

    @staticmethod
    def exec_with_result(command: str):
        with os.popen('adb shell %s' % command) as file:
            return file.read()

    @staticmethod
    def pull(command: str):
        os.system('adb pull %s > nul' % command)

    @staticmethod
    def push(src: str, dst: str):
        os.system('adb push %s %s' % (src, dst))

    @staticmethod
    def push_as_root(src: str, dst: str):
        file = os.path.basename(src)

        AdbUtils.push(src, DATA_TMP_PATH)
        AdbUtils.exec_as_root('cp -rf %s %s' % (os.path.join(DATA_TMP_PATH, file), dst))
        AdbUtils.exec('rm -rf %s' % os.path.join(DATA_TMP_PATH, file))

    @staticmethod
    def mount_rw(point: str):
        AdbUtils.exec_as_root('mount -o remount,rw %s' % point)
