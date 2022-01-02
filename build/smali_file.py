from enum import Enum


class SmaliFile(object):
    class AccessSpecifier(Enum):
        public = 'public'
        protected = 'protected'
        private = 'private'
        default = ''

    class Method(object):
        def __init__(self):
            self.access_specifier = SmaliFile.AccessSpecifier.default
            self.is_static = False
            self.name = ''
            self.parameters = ''
            self.return_type = ''
            self.keywords: list[str] = []

    def __init__(self, file: str):
        self.__path = file
        self.__methods: list[SmaliFile.Method] = []
        self.__method_body = {}

    def add_method(self, method: Method, body: str):
        self.__methods.append(method)
        self.__method_body[method] = body

    def find_method(self, method: Method):
        for item in self.__methods:
            if item.access_specifier != method.access_specifier:
                continue
            if item.is_static != method.is_static:
                continue
            if item.name != method.name:
                continue
            if item.parameters != method.parameters:
                continue
            if item.return_type != method.return_type:
                continue

            body = self.__method_body[item]
            if all(keyword in body for keyword in method.keywords):
                return body
