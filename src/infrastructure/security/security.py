from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import bcrypt
import jwt

#lay tu .env
SECRET_KEY = os.getenv("SK_SECURITY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:

    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
    
    return hashed_password_bytes.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire}) 
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")
            
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token đã hết hạn. Hãy đăng nhập lại.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token bị làm giả.")

security_optional = HTTPBearer(auto_error=False)

async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> str:
    """
    Biến thể "lenient" của get_current_user_id — dùng cho endpoint cho phép
    cả khách ẩn danh (vd log-view). KHÔNG BAO GIỜ raise HTTPException: thiếu
    header, token hết hạn, token sai định dạng... đều fallback "anonymous"
    thay vì chặn request.
    """
    if credentials is None:
        return "anonymous"

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        return user_id if user_id else "anonymous"
    except jwt.PyJWTError:
        return "anonymous"