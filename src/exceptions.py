class ExpectedException(Exception):
    pass


class NotFoundException(ExpectedException):
    pass


class ObjAlreadyExists(ExpectedException):
    pass


class ValidateError(ExpectedException):
    pass
