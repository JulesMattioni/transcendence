class AuthError(Exception):
    pass


class EmailAlreadyExistsError(AuthError):
    pass
