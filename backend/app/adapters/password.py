import bcrypt

from app.ports.interfaces import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    def hash(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except Exception:
            return False
