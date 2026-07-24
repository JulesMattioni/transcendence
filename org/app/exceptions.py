"""Domain exceptions raised by the org service."""


class OrgError(Exception):
    """Base class for all org domain errors."""


class OrgnisationCreationError(OrgError):
    """Raised when an organisation could not be created."""


class UserNotInOrganisationError(OrgError):
    """Raised when the target member does not exist in the organisation."""


class OrganisationNotFoundError(OrgError):
    """Raised when the organisation does not exist."""


class InvitedUserNotFoundError(OrgError):
    """Raised when no user matches the invited email."""


class AlreadyMemberError(OrgError):
    """Raised when the invited user is already a member."""


class InvitationAlreadyExistsError(OrgError):
    """Raised when a pending invitation already exists."""


class InvitationNotFoundError(OrgError):
    """Raised when the invitation does not exist or is not pending."""


class AuthServiceUnavailableError(OrgError):
    """Raised when the auth service cannot be reached."""
