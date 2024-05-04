import os
import struct


class AvbHeader(object):
    SIZE = 256
    FLAG_DISABLE_VERITY = 0x1
    FLAG_DISABLE_VERIFICATION = 0x2
    _MAGIC = b'AVB0'
    _RESERVED = 80
    _FORMAT_STRING = ('!4s'  # magic
                      '2L'  # avb version
                      '2Q'  # 2 * block size
                      'L'  # algorithm type
                      '2Q'  # offset, size (hash)
                      '2Q'  # offset, size (signature)
                      '2Q'  # offset, size (public key)
                      '2Q'  # offset, size (public key metadata)
                      '2Q'  # offset, size (descriptors)
                      'Q'  # rollback index
                      'L'  # flags
                      'L'  # rollback index location
                      '47sx' +  # NUL-terminated release string
                      str(_RESERVED) + 'x')  # padding for reserved bytes

    def __init__(self, data: bytes):
        (self.magic, self.avb_version_major, self.avb_version_minor,
         self.authentication_data_block_size, self.auxiliary_data_block_size,
         self.algorithm_type,
         self.hash_offset, self.hash_size,
         self.signature_offset, self.signature_size,
         self.public_key_offset, self.public_key_size,
         self.public_key_metadata_offset, self.public_key_metadata_size,
         self.descriptors_offset, self.descriptors_size,
         self.rollback_index, self.flags, self.rollback_index_location, release_string) = struct.unpack(self._FORMAT_STRING, data)
        self.release_string = release_string.rstrip(b'\0').decode('utf-8')

    def encode(self):
        release_string_encoded = self.release_string.encode('utf-8')
        return struct.pack(self._FORMAT_STRING,
                           self.magic, self.avb_version_major, self.avb_version_minor,
                           self.authentication_data_block_size, self.auxiliary_data_block_size,
                           self.algorithm_type,
                           self.hash_offset, self.hash_size,
                           self.signature_offset, self.signature_size,
                           self.public_key_offset, self.public_key_size,
                           self.public_key_metadata_offset, self.public_key_metadata_size,
                           self.descriptors_offset, self.descriptors_size,
                           self.rollback_index, self.flags, self.rollback_index_location, release_string_encoded)


class VbMeta(object):
    def __init__(self, file: str):
        self.file = file
        self._image_size = os.path.getsize(file)
        self._image = open(file, 'r+b')
        self._image.close()

    def _read_header(self):
        data = self._image.read(AvbHeader.SIZE)
        self.header = AvbHeader(data)

    def _read_descriptors(self, offset, size):
        pass

    def encode(self):
        pass


def patch(file: str):
    VbMeta(file)
