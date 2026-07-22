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


class Auth2faError(AuthError):
    pass


class UserNotFoundError(AuthError):
    pass


class TwoFactorAlreadyEnabledError(AuthError):
    pass


class TwoFactorNotConfiguredError(AuthError):
    pass


class InvalidOAuthStateError(AuthError):
    pass


class GoogleAuthError(AuthError):
    pass


class UserByEmailNotFoundError(AuthError):
    pass
