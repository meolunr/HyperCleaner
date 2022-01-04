from .method_specifier import MethodSpecifier


class SmaliFile(object):
    def __init__(self, file: str):
        self.__path = file
        self.__methods: list[MethodSpecifier] = []
        self.__method_body = {}

    def add_method(self, method: MethodSpecifier, body: str):
        self.__methods.append(method)
        self.__method_body[method] = body

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

        for item in results:
            body = self.__method_body[item]
            if all(keyword in body for keyword in specifier.keywords):
                return body

    def replace_method(self, old_method_body: str, new_method_body: str):
        with open(self.__path, mode='r+') as file:
            text = file.read().replace(old_method_body, new_method_body)
            file.seek(0)
            file.truncate()
            file.write(text)
