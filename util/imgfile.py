import os
from enum import Enum, auto


class FileSystem(Enum):
    BOOT = auto()
    EROFS = auto()
    EXT4 = auto()
    F2FS = auto()


_FS_TYPES = (
    (FileSystem.BOOT, 0, b'ANDROID!'),
    (FileSystem.EROFS, 1024, b'\xe2\xe1\xf5\xe0'),
    (FileSystem.EXT4, 1024 + 0x38, b'\123\357'),
    (FileSystem.F2FS, 1024, b'\x10\x20\xf5\xf2')
)


def file_system(file: str) -> FileSystem | None:
    with open(file, 'rb') as f:
        for fs, offset, magic in _FS_TYPES:
            f.seek(offset, os.SEEK_SET)
            buf = f.read(len(magic))
            if buf == magic:
                return fs
    return None
