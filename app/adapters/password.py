from passlib.context import CryptContext

from app.ports.interfaces import PasswordHasher


class PasslibPasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._ctx.verify(plain_password, hashed_password)
