_AVB_MAGIC = b'AVB0'
_FLAGS_OFFSET = 0x7b
_FLAGS_TO_SET = b'\x03'


def disable_verification(file: str):
    with open(file, 'rb+') as f:
        buf = f.read(len(_AVB_MAGIC))
        if buf == _AVB_MAGIC:
            f.seek(_FLAGS_OFFSET)
            f.write(_FLAGS_TO_SET)
        else:
            print('无法修改，非验证引导文件')
