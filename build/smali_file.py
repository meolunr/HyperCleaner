from build.method_specifier import MethodSpecifier


class SmaliFile(object):

    def __init__(self, file: str):
        self.__path = file
        self.__methods: list[MethodSpecifier] = []
        self.__method_body = {}

    def add_method(self, method: MethodSpecifier, body: str):
        self.__methods.append(method)
        self.__method_body[method] = body

    def find_method(self, method: MethodSpecifier):
        conditions = [
            lambda x: True if method.name is None else x.name == method.name,
            lambda x: True if method.access is None else x.access == method.access,
            lambda x: True if method.is_static is None else x.is_static == method.is_static,
            lambda x: True if method.parameters is None else x.parameters == method.parameters,
            lambda x: True if method.return_type is None else x.return_type == method.return_type
        ]
        results = self.__methods
        for condition in conditions:
            results = list(filter(condition, results))

        if len(results) > 1 and len(method.keywords) == 0:
            return

        for item in results:
            body = self.__method_body[item]
            if all(keyword in body for keyword in method.keywords):
                return body
