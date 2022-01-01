from enum import Enum


class SmaliFile(object):
    class AccessSpecifier(Enum):
        public = 'public'
        protected = 'protected'
        private = 'private'
        default = ''

    class Method(object):
        def __init__(self):
            self.access_specifier: SmaliFile.AccessSpecifier = SmaliFile.AccessSpecifier.default
            self.is_static: bool = False
            self.name: str = ''
            self.parameters: str = ''
            self.return_type: str = ''

    def __init__(self, file: str):
        self.__path = file
        self.__methods = []
        self.__method_body = {}

    def add_method(self, method, body):
        self.__methods.append(method)
        self.__method_body[method] = body
