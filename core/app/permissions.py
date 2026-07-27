from fastapi import Depends, HTTPException, status
from app.clients.org_client import OrgClient
from app.get_user import get_current_user_id

ROLE_ADMIN = 1
ROLE_EDITOR = 2
ROLE_READER = 3


def get_org_client() -> OrgClient:
    """
    Provide an OrgClient for one request.

    Returns:
        A new OrgClient bound to the configured org service.
    """

    return OrgClient()


class OrgRoleChecker:
    """
    Route dependency authorising a caller against an organisation.

    Resolves the caller's role from the org service and rejects the
    request when they are not a member, or when their role is not one of
    the allowed ones. Mirrors the org service's own RoleChecker so the
    same rules apply wherever documents are reached.
    """

    def __init__(self, allowed_roles: list[int]) -> None:
        """
        Store the roles allowed to pass this check.

        Args:
            allowed_roles: Role ids authorised for the guarded routes.
        """

        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        organisation_id: int,
        user_id: int = Depends(get_current_user_id),
        org_client: OrgClient = Depends(get_org_client),
    ) -> int:
        """
        Authorise the caller for organisation_id.

        Args:
            organisation_id: Organisation the caller is acting on.
            user_id: Id of the authenticated user, resolved via auth.
            org_client: Client used to read the caller's role.

        Returns:
            The caller's user id, so routes can depend on this check and
            still receive the identity they need.

        Raises:
            HTTPException: 403 when the caller is not a member of the
            organisation or lacks an allowed role.
        """

        role_id = await org_client.get_member_role(organisation_id, user_id)
        if role_id is None or role_id not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have necessary permission",
            )
        return user_id


require_admin = OrgRoleChecker([ROLE_ADMIN])
require_editor = OrgRoleChecker([ROLE_ADMIN, ROLE_EDITOR])
require_reader = OrgRoleChecker([ROLE_ADMIN, ROLE_EDITOR, ROLE_READER])
