import os
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


class StartNamespaceChunk(Chunk):
    __FORMAT_STRING = ('<2I'  # line number, comment
                       '2I')  # prefix, uri (namespace)

    def __init__(self, axml: BinaryIO):
        super().__init__(axml)
        buff = axml.read(struct.calcsize(self.__FORMAT_STRING))
        (_, _, self.prefix, self.uri) = struct.unpack(self.__FORMAT_STRING, buff)


class StartTagChunk(Chunk):
    __FORMAT_STRING = ('<2I'  # line number, comment
                       '2I'  # namespace uri, name
                       '3H'  # start, size, count (attribute)
                       '3H')  # id index, class index, style index

    class Attribute:
        DATA_TYPE_STRING = 0x03
        __FORMAT_STRING = ('<3I'  # namespace uri, name, raw value
                           'H2BI')  # size, res0, data type, data

        def __init__(self, axml: BinaryIO):
            buff = axml.read(struct.calcsize(self.__FORMAT_STRING))
            (self.namespace_uri, self.name, _, _, _, self.data_type, self.data) = struct.unpack(self.__FORMAT_STRING, buff)

    def __init__(self, axml: BinaryIO):
        super().__init__(axml)
        buff = axml.read(struct.calcsize(self.__FORMAT_STRING))
        (_, _, self.namespace_uri, self.name, _, _, self.attribute_count, _, _, _) = struct.unpack(self.__FORMAT_STRING, buff)

        self.attributes = []
        for i in range(self.attribute_count):
            self.attributes.append(StartTagChunk.Attribute(axml))


class ManifestXml:
    def __init__(self, file: str):
        with open(file, 'rb') as f:
            f.seek(Chunk.CHUNK_HEADER_SIZE)
            self.string_chunk = StringChunk(f)
            self._string_cache = {}

            # Skip resource map chunk
            f.seek(Chunk(f).size - Chunk.CHUNK_HEADER_SIZE, os.SEEK_CUR)

            self.start_namespace_chunk = StartNamespaceChunk(f)
            self._namespace_map = {self.start_namespace_chunk.uri: self.start_namespace_chunk.prefix}

            manifest_chunk = StartTagChunk(f)
            for attribute in manifest_chunk.attributes:
                prefix = self._get_prefix(attribute.namespace_uri)
                if attribute.data_type == StartTagChunk.Attribute.DATA_TYPE_STRING:
                    attribute.data = self._get_string(attribute.data)
                print(f'{prefix}{self._get_string(attribute.name)} = {attribute.data}')

    def _get_string(self, idx: int):
        if idx in self._string_cache:
            return self._string_cache[idx]

        offset = self.string_chunk.string_offsets[idx]
        chars_start = offset + 2
        if self.string_chunk.is_utf8:
            struct_size = 1  # Skip byte length
            format_string = '<B'
            encoding = 'utf-8'
        else:
            struct_size = 2
            format_string = '<H'
            encoding = 'utf-16'
        char_num = struct.unpack(format_string, self.string_chunk.string_pool[offset: offset + struct_size])[0]
        chars = self.string_chunk.string_pool[chars_start: chars_start + char_num * struct_size].decode(encoding)
        self._string_cache[idx] = chars
        return chars

    def _get_prefix(self, uri: int):
        if uri == 0xFFFFFFFF:
            return ''
        return f'{self._get_string(self._namespace_map[uri])}:'
