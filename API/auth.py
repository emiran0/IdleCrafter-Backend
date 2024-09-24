# API/auth.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from Database.models import User
from Database.database import AsyncSessionLocal
from sqlalchemy.future import select
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Secret key to encode and decode JWT tokens
SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_DAYS = getenv("JWT_TOKEN_EXPIRE_DAYS") 

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Utility functions for password hashing and verification
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Function to authenticate user credentials
async def authenticate_user(username: str, password: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).filter(User.Username == username)
        )
        user = result.scalar_one_or_none()
        if user and verify_password(password, user.Password):
            return user
    return None

# Function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=int(ACCESS_TOKEN_EXPIRE_DAYS)))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get the current user from the token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).filter(User.Username == username)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user