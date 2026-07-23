class AuthError(Exception):
    """
    Base class for all authentication-related errors.
    """

    pass


class EmailAlreadyExistsError(AuthError):
    """
    Raised when registering with an email that is already in use.
    """

    pass


class InvalidCredentialsError(AuthError):
    """
    Raised when login credentials (email/password) are invalid.
    """

    pass


class InvalidTokenError(AuthError):
    """
    Raised when a token is malformed or of the wrong type.
    """

    pass


class TokenExpiredError(AuthError):
    """
    Raised when a token has expired.
    """

    pass


class Auth2faError(AuthError):
    """
    Raised when a 2FA TOTP code is invalid.
    """

    pass


class UserNotFoundError(AuthError):
    """
    Raised when a referenced user does not exist.
    """

    pass


class TwoFactorAlreadyEnabledError(AuthError):
    """
    Raised when trying to enable 2FA for a user that already has it enabled.
    """

    pass


class TwoFactorNotConfiguredError(AuthError):
    """
    Raised when a 2FA operation is attempted but no secret is configured.
    """

    pass


class InvalidOAuthStateError(AuthError):
    """
    Raised when an OAuth callback's state parameter doesn't match the cookie.
    """

    pass


class GoogleAuthError(AuthError):
    """
    Raised when a Google OAuth token or profile request fails.
    """

    pass


class FtAuthError(AuthError):
    """
    Raised when a 42 OAuth token or profile request fails.
    """

    pass


class UserByEmailNotFoundError(AuthError):
    """
    Raised when no user matches the given email.
    """

    pass
