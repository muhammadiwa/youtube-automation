"""Authentication schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    """User registration request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: str = Field(..., min_length=2, max_length=100, description="User full name")
    accept_terms: bool = Field(..., alias="acceptTerms", description="Terms of service acceptance")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets policy requirements.
        
        Requirements 1.4: Password policy enforcement
        - At least 8 characters
        - Contains lowercase letter
        - Contains uppercase letter
        - Contains number
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    @field_validator("accept_terms")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        """Validate terms acceptance."""
        if not v:
            raise ValueError("You must accept the terms of service")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "name": "John Doe",
                "acceptTerms": True
            }
        }
    }


class LoginRequest(BaseModel):
    """User login request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, alias="rememberMe", description="Remember login session")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "rememberMe": False
            }
        }
    }


class TokenResponse(BaseModel):
    """Authentication token response."""
    
    access_token: str = Field(..., alias="accessToken", description="JWT access token")
    refresh_token: str = Field(..., alias="refreshToken", description="JWT refresh token")
    expires_in: int = Field(..., alias="expiresIn", description="Token expiration time in seconds")
    token_type: str = Field("bearer", alias="tokenType", description="Token type")
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expiresIn": 3600,
                "tokenType": "bearer"
            }
        }
    }


class LoginResponse(TokenResponse):
    """Login response with optional 2FA requirement."""
    
    requires_2fa: bool = Field(False, alias="requires2FA", description="Whether 2FA is required")
    temp_token: Optional[str] = Field(None, alias="tempToken", description="Temporary token for 2FA verification")
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expiresIn": 3600,
                "tokenType": "bearer",
                "requires2FA": False
            }
        }
    }


class UserResponse(BaseModel):
    """User profile response."""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User full name")
    is_2fa_enabled: bool = Field(..., alias="is2FAEnabled", description="Whether 2FA is enabled")
    created_at: datetime = Field(..., alias="createdAt", description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(None, alias="lastLoginAt", description="Last login timestamp")
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "is2FAEnabled": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "lastLoginAt": "2024-01-02T00:00:00Z"
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    
    refresh_token: str = Field(..., alias="refreshToken", description="Refresh token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    
    email: EmailStr = Field(..., description="User email address")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com"
            }
        }
    }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., alias="newPassword", min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets policy requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "abc123def456",
                "newPassword": "NewSecurePass123"
            }
        }
    }


class TwoFactorSetupResponse(BaseModel):
    """2FA setup response."""
    
    secret: str = Field(..., description="TOTP secret")
    qr_code_url: str = Field(..., alias="qrCodeUrl", description="QR code URL for authenticator app")
    backup_codes: list[str] = Field(..., alias="backupCodes", description="Backup codes")
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qrCodeUrl": "otpauth://totp/YouTube%20Automation:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=YouTube%20Automation",
                "backupCodes": ["12345678", "87654321"]
            }
        }
    }


class TwoFactorVerifyRequest(BaseModel):
    """2FA verification request."""
    
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    temp_token: Optional[str] = Field(None, alias="tempToken", description="Temporary token from login")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "123456",
                "tempToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class TwoFactorDisableRequest(BaseModel):
    """2FA disable request."""
    
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "123456"
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    
    current_password: str = Field(..., alias="currentPassword", description="Current password")
    new_password: str = Field(..., alias="newPassword", min_length=8, description="New password")
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets policy requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "currentPassword": "OldPass123",
                "newPassword": "NewSecurePass123"
            }
        }
    }
