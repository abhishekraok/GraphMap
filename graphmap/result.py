SUCCESS_CODE = 0
NODE_LINK_NOT_FOUND_ERROR_CODE = 1001
NAME_ALREADY_EXISTS = 1002
WRONG_CHILDREN_COUNT = 1003


class Result:
    def __init__(self, value, code, message):
        """
        A non zero code indicates failure.

        :type value: object
        :type code: int
        :type message: str
        """
        self.value = value
        self.code = code
        self.message = message

    def is_success(self):
        return self.code == SUCCESS_CODE

    def is_fail(self):
        return self.code != SUCCESS_CODE

    def __repr__(self):
        return 'Result({0},{1},{2})'.format(str(self.value), self.code, self.message)


def good(value):
    return Result(value=value, code=0, message='')


def fail(code, message):
    return Result(value=None, code=code, message=message)


def combine(methods_list):
    """
    Combines a list of functions, by passing output of one to the next. If any fail, stops and returns failed result.
    :param methods_list:
    :return:
    """
    current_result = good(None)
    for method in methods_list:
        current_result = method(current_result.value)
        if not current_result.is_success():
            return current_result
    return current_result
