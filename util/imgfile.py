import io
import os
import re
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


def sync_app_perm_and_context(partition: str):
    existing = set()
    mode_output = io.StringIO()
    context_output = io.StringIO()

    match partition:
        case 'system':
            app = f'system/{partition}/app'
            priv_app = f'system/{partition}/priv-app'
        case 'product':
            app = f'{partition}/app'
            priv_app = f'{partition}/priv-app'
            mode_output.write(f'product/UpdatedApp.json 0 0 0644\n')
            context_output.write('/product/UpdatedApp\\.json u:object_r:system_file:s0\n')
        case _:
            app = f'{partition}/app'
            priv_app = f'{partition}/priv-app'

    with open(f'config/{partition}_fs_config', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith(app) or line.startswith(priv_app):
                existing.add(line.split(' ')[0])

    for folder in (app, priv_app):
        for root, dirs, files in os.walk(folder):
            for i in dirs:
                i = os.path.join(root, i).replace('\\', '/')
                if i not in existing:
                    mode_output.write(f'{i} 0 0 0755\n')
                    context_output.write(f'/{re.escape(i)} u:object_r:system_file:s0\n')
            for i in files:
                i = os.path.join(root, i).replace('\\', '/')
                if i not in existing:
                    mode_output.write(f'{i} 0 0 0644\n')
                    context_output.write(f'/{re.escape(i)} u:object_r:system_file:s0\n')

    with open(f'config/{partition}_fs_config', 'a', encoding='utf-8') as f:
        f.write(mode_output.getvalue())
    with open(f'config/{partition}_file_contexts', 'a', encoding='utf-8') as f:
        f.write(context_output.getvalue())
