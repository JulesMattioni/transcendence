# Exemple concret pour permission_service.py :
# Ton routeur va recevoir une requête :
# GET /permissions/check?user_id=2&action=edit&org_id=5.
# Le routeur passe ces données au PermissionService.
# Le service va :

# Aller chercher le rôle du user_id 2 dans la table memberships pour l'org 5.

# Regarder dans sa logique si ce rôle a le droit de faire edit.

# Retourner True ou False au routeur.

# verif des droits

from shared.base_service import BaseService
from typing import Dict

class PermService(BaseService):