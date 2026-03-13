"""Database adapter using SQLModel."""
from typing import Optional
from sqlmodel import Session, select

from app.domain.models import User
from app.ports.interfaces import UserRepository


class SQLModelUserRepository(UserRepository):
    """SQLModel implementation of UserRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()
    
    async def update(self, user: User) -> User:
        # Create a new session for the update operation
        from sqlmodel import Session as SQLSession
        from app.database import engine
        
        with SQLSession(engine) as session:
            db_user = session.get(User, user.id)
            if not db_user:
                return user
            
            db_user.email = user.email
            db_user.username = user.username
            db_user.password_hash = user.password_hash
            db_user.bio = user.bio
            db_user.image = user.image
            db_user.updated_at = user.updated_at
            
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            
            # Return a new object with updated values
            return User(
                id=db_user.id,
                email=db_user.email,
                username=db_user.username,
                password_hash=db_user.password_hash,
                bio=db_user.bio,
                image=db_user.image,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
