class AuthError(Exception):
    pass


class EmailAlreadyExistsError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass


class TokenExpiredError(AuthError):
    pass
