class OrgError(Exception):
    pass


class OrgnisationCreationError(OrgError):
    pass


class UserNotInOrganisationError(OrgError):
    pass


class OrganisationNotFoundError(OrgError):
    pass


class InvitedUserNotFoundError(OrgError):
    pass


class AlreadyMemberError(OrgError):
    pass


class InvitationAlreadyExistsError(OrgError):
    pass


class InvitationNotFoundError(OrgError):
    pass


class AuthServiceUnavailableError(OrgError):
    pass
