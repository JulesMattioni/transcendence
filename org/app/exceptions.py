class OrgError(Exception):
    pass


class OrgnisationCreationError(OrgError):
    pass


class UserNotInOrganisationError(OrgError):
    pass


class OrganisationNotFoundError(OrgError):
    pass
