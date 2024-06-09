import struct
from typing import BinaryIO


class Chunk:
    CHUNK_HEADER_SIZE = 8
    __FORMAT_STRING = '<2HI'  # type, header size, size (chunk)

    def __init__(self, axml: BinaryIO):
        (self.type, self.header_size, self.size) = struct.unpack(self.__FORMAT_STRING, axml.read(self.CHUNK_HEADER_SIZE))


class StringChunk(Chunk):
    __FORMAT_STRING = ('<2I'  # string count, style count
                       '2H'  # utf-8, sorted (flags)
                       '2I')  # strings start, styles start

    def __init__(self, axml: BinaryIO):
        super().__init__(axml)
        buff = axml.read(struct.calcsize(self.__FORMAT_STRING))
        (self.string_count, _, self._flag_utf8, _, self.strings_start, _) = struct.unpack(self.__FORMAT_STRING, buff)
        self.is_utf8 = self._flag_utf8 != 0

        self.string_offsets = []
        for i in range(self.string_count):
            self.string_offsets.append(struct.unpack('<I', axml.read(4))[0])

        self.string_pool = axml.read(self.size - self.strings_start)


class ManifestXml:
    def __init__(self, file: str):
        with open(file, 'rb') as f:
            f.seek(Chunk.CHUNK_HEADER_SIZE)
            self.string_chunk = StringChunk(f)
            self._string_cache = {}
