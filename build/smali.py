import re
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
        self.invoke_methods: set[MethodSpecifier | str] = set()


class SmaliFile:
    def __init__(self, file: str):
        self.file = file
        self._methods: dict[MethodSpecifier:str] = {}

        with open(file, 'r', encoding='utf-8') as file:
            self._parse_method(file.read())

    def find_method(self, specifier: MethodSpecifier) -> str:
        conditions = {
            lambda x: True if specifier.name is None else x.name == specifier.name,
            lambda x: True if specifier.access is None else x.access == specifier.access,
            lambda x: True if specifier.is_static is None else x.is_static == specifier.is_static,
            lambda x: True if specifier.is_final is None else x.is_final == specifier.is_final,
            lambda x: True if specifier.parameters is None else x.parameters == specifier.parameters,
            lambda x: True if specifier.return_type is None else x.return_type == specifier.return_type
        }
        results = self._methods.keys()
        for condition in conditions:
            results = set(filter(condition, results))

        if len(results) > 1 and len(specifier.keywords) == 0:
            return ''

        def filter_keyword(item: MethodSpecifier):
            body = self._methods[item]
            return all(keyword in body for keyword in specifier.keywords)

        results = set(filter(filter_keyword, results))
        if len(results) == 1:
            return self._methods[results.pop()]

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

    def method_return_boolean(self, specifier: MethodSpecifier, value: bool):
        old_body = self.find_method(specifier)
        new_body = old_body.splitlines()[0] + f'''
    .locals 1

    const/4 v0, 0x{1 if value else 0}

    return v0
.end method\
        '''
        self.method_replace(old_body, new_body)

    def _parse_method(self, content: str):
        pattern = re.compile(r'((\.method.+?)\n.+?\.end method)', re.DOTALL)
        method_pattern = re.compile(r'\.method (public|protected|private)(?: static)?(?: final)? (\w+?)\((\S*?)\)(\S+?)')
        invoke_pattern = re.compile(r'invoke-(?:virtual|static) \{.*?}, L(.+?)\n', re.DOTALL)

        for item in pattern.findall(content):
            method_defines = method_pattern.findall(item[1])
            # Skip constructor methods
            if len(method_defines) == 0:
                continue
            method_defines = method_defines[0]

            specifier = MethodSpecifier()
            specifier.access = MethodSpecifier.Access(method_defines[0])
            specifier.is_static = ' static ' in item[1]
            specifier.is_final = ' final ' in item[1]
            specifier.name = method_defines[1]
            specifier.parameters = method_defines[2]
            specifier.return_type = method_defines[3]
            specifier.invoke_methods = set(invoke_pattern.findall(item[0]))

            self._methods[specifier] = item[0]
