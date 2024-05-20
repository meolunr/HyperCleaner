import os

FS_TYPE_BOOT = 'boot'
FS_TYPE_EROFS = 'erofs'
FS_TYPE_EXT4 = 'ext4'
FS_TYPE_F2FS = 'f2fs'
FS_TYPE_UNKNOWN = 'unknown'

_FS_TYPES = (
    (FS_TYPE_BOOT, 0, b'ANDROID!'),
    (FS_TYPE_EROFS, 1024, b'\xe2\xe1\xf5\xe0'),
    (FS_TYPE_EXT4, 1024 + 0x38, b'\123\357'),
    (FS_TYPE_F2FS, 1024, b'\x10\x20\xf5\xf2')
)


def file_system(file: str) -> str:
    with open(file, 'rb') as f:
        for fs, offset, magic in _FS_TYPES:
            f.seek(offset, os.SEEK_SET)
            buf = f.read(len(magic))
            if buf == magic:
                return fs
    return FS_TYPE_UNKNOWN
