from typing import Annotated
from fastapi import Request, Header, HTTPException
from config import config as c
from persistence.database import session_factory
from persistence.models import UserAccount
from persistence.repository import fetch_user_account


def authorize_request(
    request: Request,
    session_token: Annotated[str | None, Header(alias=c.SESSION_TOKEN_HEADER)] = None,
):
    with session_factory() as session:
        account = (
            fetch_user_account(session, UserAccount.session_token == session_token)
            if session_token
            else None
        )
    if not account:
        raise HTTPException(401, c.SIGN_IN_REQUIRED_MESSAGE)
    area = c.AREA_BY_ROUTE[(request.method, request.scope["route"].path)]
    if area not in c.ROLE_AREA_ACCESS.get(account["role"], []):
        raise HTTPException(
            403, c.AREA_REFUSED_MESSAGE.format(role=account["role"], area=area)
        )
    return account
