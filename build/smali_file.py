from .method_specifier import MethodSpecifier


class SmaliFile(object):
    def __init__(self, file: str):
        self.__path = file
        self.__methods: list[MethodSpecifier] = []
        self.__method_body = {}

    def add_method(self, specifier: MethodSpecifier, body: str):
        self.__methods.append(specifier)
        self.__method_body[specifier] = body

    def find_method(self, specifier: MethodSpecifier):
        conditions = [
            lambda x: True if specifier.name is None else x.name == specifier.name,
            lambda x: True if specifier.access is None else x.access == specifier.access,
            lambda x: True if specifier.is_static is None else x.is_static == specifier.is_static,
            lambda x: True if specifier.parameters is None else x.parameters == specifier.parameters,
            lambda x: True if specifier.return_type is None else x.return_type == specifier.return_type
        ]
        results = self.__methods
        for condition in conditions:
            results = list(filter(condition, results))

        if len(results) > 1 and len(specifier.keywords) == 0:
            return

        def filter_keyword(item: MethodSpecifier):
            body = self.__method_body[item]
            return all(keyword in body for keyword in specifier.keywords)

        results = list(filter(filter_keyword, results))
        if len(results) == 1:
            return self.__method_body[results[0]]

    def method_replace(self, old_method_body: str, new_method_body: str):
        with open(self.__path, mode='r+') as file:
            text = file.read().replace(old_method_body, new_method_body)
            file.seek(0)
            file.truncate()
            file.write(text)

    def method_nop(self, specifier: MethodSpecifier):
        old_method_body = self.find_method(specifier)
        new_method_body = old_method_body.splitlines()[0] + '''
    .locals 0

    return-void
.end method\
        '''
        self.method_replace(old_method_body, new_method_body)

    def method_return0(self, specifier: MethodSpecifier):
        old_method_body = self.find_method(specifier)
        new_method_body = old_method_body.splitlines()[0] + '''
    .locals 1
    
    const/4 v0, 0x0

    return v0
.end method\
        '''
        self.method_replace(old_method_body, new_method_body)
