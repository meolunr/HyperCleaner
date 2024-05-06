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


def round_to_multiple(number, size):
    remainder = number % size
    if remainder == 0:
        return number
    return number + size - remainder


class AvbDescriptor(object):
    _FORMAT_STRING = '!QQ'  # tag, num_bytes_following (descriptor header)
    _SIZE = 16

    def __init__(self, data):
        if data:
            self.data = data
            (self.tag, num_bytes_following) = struct.unpack(self._FORMAT_STRING, data[0:self._SIZE])

    def encode(self):
        num_bytes_following = len(self.data)
        nbf_with_padding = round_to_multiple(num_bytes_following, 8)
        padding_size = nbf_with_padding - num_bytes_following
        desc = struct.pack(self._FORMAT_STRING, self.tag, nbf_with_padding)
        padding = struct.pack(str(padding_size) + 'x')
        ret = desc + self.data + padding
        return bytearray(ret)


class AvbPropertyDescriptor(AvbDescriptor):
    TAG = 0
    _SIZE = 32
    _FORMAT_STRING = ('!QQ'  # tag, num_bytes_following (descriptor header)
                      'Q'  # key size (bytes)
                      'Q')  # value size (bytes)

    def __init__(self, data=None):
        super().__init__(None)
        (tag, num_bytes_following, key_size, value_size) = struct.unpack(self._FORMAT_STRING, data[0:self._SIZE])
        key_offset = self._SIZE
        value_offset = key_offset + key_size + 1
        self.key = data[key_offset:(key_offset + key_size)].decode('utf-8')
        self.value = data[value_offset:value_offset + value_size]

    def encode(self):
        key_encoded = self.key.encode('utf-8')
        num_bytes_following = (self._SIZE + len(key_encoded) + len(self.value) + 2 - 16)
        nbf_with_padding = round_to_multiple(num_bytes_following, 8)
        padding_size = nbf_with_padding - num_bytes_following
        desc = struct.pack(self._FORMAT_STRING, self.TAG, nbf_with_padding, len(key_encoded), len(self.value))
        return desc + key_encoded + b'\0' + self.value + b'\0' + padding_size * b'\0'



class VbMeta(object):
    def __init__(self, file: str):
        self.file = file
        self._image_size = os.path.getsize(file)
        self._image = open(file, 'r+b')

        self._read_header()
        aux_block_offset = AvbHeader.SIZE + self.header.authentication_data_block_size
        desc_start_offset = aux_block_offset + self.header.descriptors_offset
        self._read_descriptors(desc_start_offset, self.header.descriptors_size)

        self._image.close()

    def _read_header(self):
        data = self._image.read(AvbHeader.SIZE)
        self.header = AvbHeader(data)

    def _read_descriptors(self, offset, size):
        self._image.seek(offset)
        data = self._image.read(size)

        self.descriptors = []
        desc_offset = 0
        while desc_offset < len(data):
            tag, nb_following = struct.unpack('!2Q', data[desc_offset:desc_offset + 16])
            if tag == AvbPropertyDescriptor.TAG:
                clazz = AvbPropertyDescriptor
            else:
                clazz = AvbDescriptor
            self.descriptors.append(clazz(data[desc_offset:desc_offset + 16 + nb_following]))
            desc_offset += 16 + nb_following

    def encode(self):
        pass


def patch(file: str):
    avb = VbMeta(file)
    print(avb.header.magic)
