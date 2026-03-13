from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import Settings
from app.ports.interfaces import TokenService


class JWTTokenService(TokenService):
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expiry_days = settings.jwt_expiry_days

    def create(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=self._expiry_days)
        return jwt.encode(
            {"sub": str(user_id), "exp": expire},
            self._secret,
            algorithm=self._algorithm,
        )

    def decode(self, token: str) -> int | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            sub = payload.get("sub")
            return int(sub) if sub is not None else None
        except (JWTError, ValueError):
            return None
