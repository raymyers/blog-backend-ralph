from datetime import datetime, timedelta

from jose import jwt

from app.ports.interfaces import TokenGenerator

_SECRET_KEY = "your-secret-key-change-in-production"
_ALGORITHM = "HS256"
_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class JWTTokenGenerator(TokenGenerator):
    def __init__(
        self,
        secret_key: str = _SECRET_KEY,
        algorithm: str = _ALGORITHM,
        expire_minutes: int = _EXPIRE_MINUTES,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(self, data: dict) -> str:
        to_encode = {**data, "exp": datetime.utcnow() + timedelta(minutes=self.expire_minutes)}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
