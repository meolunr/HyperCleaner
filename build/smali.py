import os
import re
import shutil
from enum import Enum


class Method:
    class Access(Enum):
        PUBLIC = 'public'
        PROTECTED = 'protected'
        PRIVATE = 'private'

    def __init__(self):
        self.name = None
        self.access = None
        self.is_static = None
        self.is_final = None
        self.parameters = None
        self.return_type = None
        self.keywords: set[str] = set()
        self.invoke_methods: set[str] = set()


class MethodSpecifier(Method):
    def __init__(self):
        super().__init__()
        self.invoke_methods: set[MethodSpecifier] = set()


class SmaliFile:
    def __init__(self, file: str, apk):
        self.file = file
        self._apk = apk
        self._methods: dict[Method:str] = {}

    def find_method(self, specifier: MethodSpecifier) -> str:
        results = self._methods.keys()
        basic_conditions = {
            lambda x: True if specifier.name is None else x.name == specifier.name,
            lambda x: True if specifier.access is None else x.access == specifier.access,
            lambda x: True if specifier.is_static is None else x.is_static == specifier.is_static,
            lambda x: True if specifier.is_final is None else x.is_final == specifier.is_final,
            lambda x: True if specifier.parameters is None else x.parameters == specifier.parameters,
            lambda x: True if specifier.return_type is None else x.return_type == specifier.return_type
        }
        for condition in basic_conditions:
            results = set(filter(condition, results))

        if specifier.keywords:
            results = set(filter(self._filter_keyword(specifier.keywords), results))
        if specifier.invoke_methods:
            results = set(filter(self._filter_invoke_methods(specifier.invoke_methods), results))

        if len(results) == 1:
            return self._methods[results.pop()]

    def find_constructor(self, parameters: str = ''):
        results = self._methods.keys()
        basic_conditions = {
            lambda x: x.name == 'constructor',
            lambda x: x.parameters == parameters,
        }
        for condition in basic_conditions:
            results = set(filter(condition, results))

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
    .locals 0

    const/4 p0, 0x{1 if value else 0}

    return p0
.end method\
        '''
        self.method_replace(old_body, new_body)

    def add_affiliated_smali(self, file: str, name: str):
        folder = os.path.dirname(self.file)
        shutil.copy(file, f'{folder}/{name}')

    def parse_all_methods(self):
        pattern = re.compile(r'\.method.+?\n.+?\.end method', re.DOTALL)
        with open(self.file, 'r', encoding='utf-8') as f:
            content = f.read()
        for item in pattern.findall(content):
            self._add_method(item)

    def parse_method(self, content: str):
        pattern = re.compile(fr'\.method[^\n|.]+? {re.escape(content)}\n.+?\.end method', re.DOTALL)
        with open(self.file, 'r', encoding='utf-8') as f:
            content = f.read()
        method_defines = pattern.findall(content)
        self._add_method(method_defines[0])

    def parse_all_constructor(self):
        pattern = re.compile(r'(\.method.*?constructor <(?:cl)?init>\((\S*?)\)V\n.+?\.end method)', re.DOTALL)
        with open(self.file, 'r', encoding='utf-8') as f:
            content = f.read()
        for method_defines in pattern.findall(content):
            method = Method()
            method.name = 'constructor'
            method.parameters = method_defines[1]
            self._methods[method] = method_defines[0]

    def _add_method(self, content: str):
        method_pattern = re.compile(r'(\.method (public|protected|private).*?(\w+?)\((\S*?)\)(\S+))\n')
        invoke_pattern = re.compile(r'invoke-(?:direct|virtual|static) \{.*?}, L(\S+?)\n', re.DOTALL)

        method_defines = method_pattern.findall(content)
        # Skip constructor methods
        if len(method_defines) == 0:
            return
        method_defines = method_defines[0]

        method = Method()
        method.access = MethodSpecifier.Access(method_defines[1])
        method.is_static = ' static ' in method_defines[0]
        method.is_final = ' final ' in method_defines[0]
        method.name = method_defines[2]
        method.parameters = method_defines[3]
        method.return_type = method_defines[4]
        method.invoke_methods.update(invoke_pattern.findall(content))

        self._methods[method] = content

    def _filter_keyword(self, keywords):
        def condition(method: Method):
            body = self._methods[method]
            return all(x in body for x in keywords)

        return condition

    def _filter_invoke_methods(self, invoke_specifiers):
        pattern = re.compile(r'(.+?);->(.+)')

        def condition(method: Method):
            cache = {}
            for invoke_method in method.invoke_methods:
                method_defines = pattern.findall(invoke_method)[0]
                class_type_name = method_defines[0]
                method_signature = method_defines[1]

                if class_type_name in cache:
                    smali: SmaliFile = cache[class_type_name]
                else:
                    smali: SmaliFile = self._apk.open_smali(f'{class_type_name}.smali', auto_parse=False)
                    cache[class_type_name] = smali
                if not smali:
                    continue

                smali.parse_method(method_signature)
                if any(smali.find_method(specifier) for specifier in invoke_specifiers):
                    return True

            return False

        return condition
