from fastapi import APIRouter, Header, HTTPException
from typing import Dict

router = APIRouter()

# curl -k -H "X-User-Id: 2" https://localhost:8443/api/org/organisation
# Utilisateur → Gateway (HTTPS + WAF) → Service org → Réponse


def get_id(user_id: str) -> int:
    try:
        return int(user_id)
    except ValueError as e:
        print(f"[Error id] {e}")
        raise HTTPException(status_code=401, detail="Ivalid Id")


@router.get("/organisation")
def jwt_mok(x_user_id: int = Header(default=1)) -> Dict[str, int]:
    user_id = get_id(x_user_id)
    return {"user_log": user_id}
