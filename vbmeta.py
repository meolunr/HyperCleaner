import os


class VbMeta(object):
    def __init__(self, file: str):
        self.file = file
        self._image_size = os.path.getsize(file)
        self._image = open(file, 'r+b')
        self._image.close()

    def _read_header(self):
        pass

    def _read_descriptors(self, offset, size):
        pass

    def encode(self):
        pass


def patch(file: str):
    VbMeta(file)
