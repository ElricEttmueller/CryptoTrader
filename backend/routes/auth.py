from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
import os
from dotenv import load_dotenv
from backend.database.db_config import DatabaseManager

load_dotenv()

router = APIRouter()
db = DatabaseManager()

# Use a simple API key header for authentication
API_KEY = os.getenv("API_KEY", "your-secret-api-key")  # Set this in your .env file
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

@router.get("/verify")
async def verify_auth(api_key: str = Depends(get_api_key)):
    """Verify API key is valid."""
    return {"status": "authenticated", "message": "API key is valid"}

@router.post("/register", response_model=User)
async def register_user(user: UserCreate, api_key: str = Depends(get_api_key)):
    """Register a new user."""
    # Check if user already exists
    existing_user = await db.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_data = {
        "email": user.email,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": True,
        "api_keys": [],
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    result = await db.create_user(user_data)
    user_data["_id"] = result
    return User(**user_data)

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), api_key: str = Depends(get_api_key)):
    """Login user and return access token."""
    user = await db.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    await db.update_user_login(user["_id"])
    
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api-keys", response_model=User)
async def add_api_key(api_key: APIKeyCreate, current_user: User = Depends(get_current_user), api_key_header: str = Depends(get_api_key)):
    """Add a new API key for the user."""
    encrypted_key = encrypt_api_key(api_key.api_secret)
    new_key = api_key.dict()
    new_key["api_secret"] = encrypted_key
    new_key["created_at"] = datetime.utcnow()
    new_key["last_used"] = None
    
    user = await db.add_api_key(current_user.id, new_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not add API key"
        )
    
    return user

@router.get("/api-keys", response_model=List[APIKeyCreate])
async def get_api_keys(current_user: User = Depends(get_current_user), api_key: str = Depends(get_api_key)):
    """Get all API keys for the user."""
    user = await db.get_user_by_id(current_user.id)
    return user.get("api_keys", [])
