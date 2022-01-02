from enum import Enum


class MethodSpecifier(object):
    class Access(Enum):
        PUBLIC = 'public'
        PROTECTED = 'protected'
        PRIVATE = 'private'

    def __init__(self):
        self.access = None
        self.is_static = None
        self.name = None
        self.parameters = None
        self.return_type = None
        self.keywords: list[str] = []
