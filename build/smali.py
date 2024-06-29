from enum import Enum


class MethodSpecifier:
    class Access(Enum):
        PUBLIC = 'public'
        PROTECTED = 'protected'
        PRIVATE = 'private'

    def __init__(self):
        self.access = None
        self.is_static = None
        self.is_final = None
        self.name = None
        self.parameters = None
        self.return_type = None
        self.keywords: set[str] = set()


class SmaliFile:
    def __init__(self, file: str):
        self.file = file
        self._methods: set[MethodSpecifier] = set()
        self._method_body = {}

    def add_method(self, specifier: MethodSpecifier, body: str):
        self._methods.add(specifier)
        self._method_body[specifier] = body

    def find_method(self, specifier: MethodSpecifier) -> str:
        conditions = {
            lambda x: True if specifier.name is None else x.name == specifier.name,
            lambda x: True if specifier.access is None else x.access == specifier.access,
            lambda x: True if specifier.is_static is None else x.is_static == specifier.is_static,
            lambda x: True if specifier.is_final is None else x.is_final == specifier.is_final,
            lambda x: True if specifier.parameters is None else x.parameters == specifier.parameters,
            lambda x: True if specifier.return_type is None else x.return_type == specifier.return_type
        }
        results = self._methods
        for condition in conditions:
            results = set(filter(condition, results))

        if len(results) > 1 and len(specifier.keywords) == 0:
            return ''

        def filter_keyword(item: MethodSpecifier):
            body = self._method_body[item]
            return all(keyword in body for keyword in specifier.keywords)

        results = set(filter(filter_keyword, results))
        if len(results) == 1:
            return self._method_body[results.pop()]

    def method_replace(self, old_method: str | MethodSpecifier, new_body: str):
        if type(old_method) is MethodSpecifier:
            old_method = self.find_method(old_method)
        with open(self.file, 'r+', encoding='utf-8') as file:
            text = file.read().replace(old_method, new_body)
            file.seek(0)
            file.truncate()
            file.write(text)

    def method_nop(self, specifier: MethodSpecifier):
        old_body = self.find_method(specifier)
        new_body = old_body.splitlines()[0] + '''
    .locals 0

    return-void
.end method\
        '''
        self.method_replace(old_body, new_body)

    def method_return0(self, specifier: MethodSpecifier):
        old_body = self.find_method(specifier)
        new_body = old_body.splitlines()[0] + '''
    .locals 1

    const/4 v0, 0x0

    return v0
.end method\
        '''
        self.method_replace(old_body, new_body)
