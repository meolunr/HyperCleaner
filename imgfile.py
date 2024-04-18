import os

FS_TYPES = [
    ('erofs', 1024, b'\xe2\xe1\xf5\xe0'),
    ('ext4', 1024 + 0x38, b'\123\357'),
    ('f2fs', 1024, b'\x10\x20\xf5\xf2')
]


def file_system(file: str) -> str:
    with open(file, 'rb') as f:
        for fs, offset, magic in FS_TYPES:
            f.seek(offset, os.SEEK_SET)
            buf = f.read(len(magic))
            if buf == magic:
                return fs
    return 'unknown'
