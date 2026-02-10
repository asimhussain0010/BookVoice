"""
User Management API Endpoints
Handles user profile management and user-related operations
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.dependencies import get_current_user, get_current_superuser
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    user_service = UserService(db)
    profile = user_service.get_profile(current_user.id)
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at
        },
        "profile": profile
    }

@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user_service = UserService(db)
    updated_profile = user_service.update_profile(
        current_user.id, 
        profile_data.dict(exclude_unset=True)
    )
    
    return {"profile": updated_profile}

@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile avatar"""
    image_service = ImageService()
    
    # Save avatar
    avatar_url = image_service.save_avatar(file, current_user.id)
    
    if not avatar_url:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Update profile
    user_service = UserService(db)
    
    # Delete old avatar if exists
    profile = user_service.get_profile(current_user.id)
    if profile and profile.get('avatar_url'):
        image_service.delete_avatar(profile['avatar_url'])
    
    # Save new avatar URL
    updated_profile = user_service.update_profile(
        current_user.id,
        {"avatar_url": avatar_url}
    )
    
    return {"avatar_url": avatar_url, "profile": updated_profile}
# @router.get("/me", response_model=UserResponse)
# def get_current_user_profile(
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get current user's profile
#     """
#     return current_user


# @router.put("/me", response_model=UserResponse)
# def update_current_user(
#     user_update: UserUpdate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Update current user's profile
#     """
#     # Check if email is being changed and if it's already taken
#     if user_update.email and user_update.email != current_user.email:
#         existing_user = db.query(User).filter(User.email == user_update.email).first()
#         if existing_user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email already registered"
#             )
    
#     # Check if username is being changed and if it's already taken
#     if user_update.username and user_update.username != current_user.username:
#         existing_user = db.query(User).filter(User.username == user_update.username).first()
#         if existing_user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Username already taken"
#             )
    
#     # Update user fields
#     update_data = user_update.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(current_user, field, value)
    
#     db.commit()
#     db.refresh(current_user)
    
#     return current_user


# @router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
# def delete_current_user(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Delete current user's account
#     """
#     db.delete(current_user)
#     db.commit()
#     return None


# @router.get("/", response_model=List[UserResponse])
# def get_all_users(
#     skip: int = 0,
#     limit: int = 100,
#     current_user: User = Depends(get_current_superuser),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get all users (admin only)
#     """
#     users = db.query(User).offset(skip).limit(limit).all()
#     return users


# @router.get("/{user_id}", response_model=UserResponse)
# def get_user(
#     user_id: int,
#     current_user: User = Depends(get_current_superuser),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get specific user (admin only)
#     """
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
#     return user