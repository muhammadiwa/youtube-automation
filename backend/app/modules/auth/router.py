"""Authentication router for user registration, login, and token management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
    ChangePasswordRequest,
)
from app.modules.auth.jwt import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Register a new user account.
    
    **Requirements:**
    - Email must be valid and unique
    - Password must meet policy requirements (min 8 chars, uppercase, lowercase, number)
    - Name must be at least 2 characters
    - Terms of service must be accepted
    
    **Validates:** Requirements 1.1, 1.4
    """,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user.
    
    Args:
        data: Registration data including email, password, name, and terms acceptance
        db: Database session
        
    Returns:
        UserResponse: Created user profile
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    service = AuthService(db)
    
    try:
        user = await service.register(
            email=data.email,
            password=data.password,
            name=data.name,
            accept_terms=data.accept_terms,
        )
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="""
    Authenticate user and return JWT tokens.
    
    If 2FA is enabled, returns requires2FA=true and tempToken for verification.
    
    **Validates:** Requirements 1.1, 1.2
    """,
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Login user and return tokens.
    
    Args:
        data: Login credentials
        db: Database session
        
    Returns:
        LoginResponse: JWT tokens or 2FA requirement
        
    Raises:
        HTTPException: If credentials are invalid
    """
    service = AuthService(db)
    
    try:
        result = await service.login(
            email=data.email,
            password=data.password,
            remember_me=data.remember_me,
        )
        
        return LoginResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result["expires_in"],
            token_type=result["token_type"],
            requires_2fa=result.get("requires_2fa", False),
            temp_token=result.get("temp_token"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Refresh access token using refresh token.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token.
    
    Args:
        data: Refresh token
        db: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    service = AuthService(db)
    
    try:
        result = await service.refresh_token(data.refresh_token)
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logout user and invalidate tokens.",
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Logout user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
    """
    service = AuthService(db)
    await service.logout(current_user.id)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get current authenticated user profile.",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User profile
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/2fa/enable",
    response_model=TwoFactorSetupResponse,
    summary="Enable 2FA",
    description="""
    Enable two-factor authentication for current user.
    
    Returns TOTP secret and QR code for authenticator app setup.
    
    **Validates:** Requirements 1.2
    """,
)
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TwoFactorSetupResponse:
    """Enable 2FA for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TwoFactorSetupResponse: TOTP secret, QR code, and backup codes
    """
    service = AuthService(db)
    result = await service.enable_2fa(current_user.id)
    return TwoFactorSetupResponse(**result)


@router.post(
    "/2fa/verify-setup",
    summary="Verify 2FA setup",
    description="Verify 2FA code during setup to confirm configuration.",
)
async def verify_2fa_setup(
    data: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify 2FA setup.
    
    Args:
        data: TOTP code
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Backup codes
        
    Raises:
        HTTPException: If code is invalid
    """
    service = AuthService(db)
    
    try:
        result = await service.verify_2fa_setup(current_user.id, data.code)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/2fa/verify",
    response_model=TokenResponse,
    summary="Verify 2FA code",
    description="""
    Verify 2FA code during login.
    
    Requires tempToken from login response.
    
    **Validates:** Requirements 1.2
    """,
)
async def verify_2fa_login(
    data: TwoFactorVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Verify 2FA code during login.
    
    Args:
        data: TOTP code and temp token
        db: Database session
        
    Returns:
        TokenResponse: JWT tokens
        
    Raises:
        HTTPException: If code or temp token is invalid
    """
    service = AuthService(db)
    
    try:
        if not data.temp_token:
            raise ValueError("Temporary token is required")
        
        result = await service.verify_2fa_login(data.temp_token, data.code)
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/2fa/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable 2FA",
    description="Disable two-factor authentication for current user.",
)
async def disable_2fa(
    data: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Disable 2FA for current user.
    
    Args:
        data: TOTP code for verification
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If code is invalid
    """
    service = AuthService(db)
    
    try:
        await service.disable_2fa(current_user.id, data.code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/password/reset-request",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Request password reset",
    description="""
    Request password reset email.
    
    Sends secure reset link valid for 1 hour.
    
    **Validates:** Requirements 1.5
    """,
)
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Request password reset.
    
    Args:
        data: Email address
        db: Database session
    """
    service = AuthService(db)
    await service.request_password_reset(data.email)


@router.post(
    "/password/reset-confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirm password reset",
    description="Confirm password reset with token and new password.",
)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Confirm password reset.
    
    Args:
        data: Reset token and new password
        db: Database session
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    service = AuthService(db)
    
    try:
        await service.confirm_password_reset(data.token, data.new_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/password/change",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change password for authenticated user.",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Change password.
    
    Args:
        data: Current and new password
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If current password is incorrect
    """
    service = AuthService(db)
    
    try:
        await service.change_password(
            current_user.id,
            data.current_password,
            data.new_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
