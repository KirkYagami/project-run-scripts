"""The sign-in and access guard every protected endpoint sits behind."""
from fastapi import HTTPException

from config import config
from persistence import repository
from persistence.database import session_factory
from persistence.models import UserAccount


def _area_of(request):
    path = request.url.path
    if request.method == "POST" and path.endswith(config.DECISION_PATH_ENDING):
        return config.AREA_DECISION
    for start, area in config.AREA_BY_PATH_START.items():
        if path.startswith(start):
            return area
    return None


def authorize_request(request, session_token):
    """Decide who is asking and whether their role reaches that area."""
    if not session_token:
        raise HTTPException(status_code=401, detail=config.SIGN_IN_REQUIRED_MESSAGE)
    session = session_factory()
    try:
        account = repository.fetch_user_account(session, UserAccount.session_token == session_token)
    finally:
        session.close()
    if account is None:
        raise HTTPException(status_code=401, detail=config.SIGN_IN_REQUIRED_MESSAGE)
    area = _area_of(request)
    if area is not None and area not in config.ROLE_AREA_ACCESS.get(account["role"], []):
        raise HTTPException(status_code=403, detail=config.AREA_REFUSED_MESSAGE.format(
            role=account["role"], area=area))
    return account
